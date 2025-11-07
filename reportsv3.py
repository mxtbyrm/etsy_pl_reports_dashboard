import asyncio
import calendar
import json
import logging
import os
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from prisma import Prisma
from prisma.enums import PeriodType

# --- Configuration ---
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# --- Data Structures ---
@dataclass
class DateRange:
    """Represents a start and end date for a time period."""
    start_date: datetime
    end_date: datetime


# --- Main Analytics Class ---
class EcommerceAnalytics:
    """
    A comprehensive analytics engine for calculating financial metrics
    from a Prisma database and saving results back to database tables.
    """

    def __init__(self, cost_csv_path: str, resume_from_checkpoint: bool = True):
        self.prisma = Prisma()
        self.cost_data = self._load_cost_data(cost_csv_path)
        self.resume_from_checkpoint = resume_from_checkpoint
        self.checkpoint_file = "analytics_checkpoint.json"

    def _load_cost_data(self, csv_path: str) -> pd.DataFrame:
        """Load and process cost data from the provided CSV file."""
        try:
            if not os.path.exists(csv_path):
                logger.error(f"Cost data file not found at '{csv_path}'.")
                return pd.DataFrame()
            
            df = pd.read_csv(csv_path, encoding='utf-8-sig')  # Handle BOM
            df.columns = df.columns.str.strip()
            
            # Ensure SKU column exists
            if 'SKU' not in df.columns:
                logger.error("SKU column not found in cost data CSV")
                return pd.DataFrame()
            
            # Remove rows with null SKUs
            df = df.dropna(subset=['SKU'])
            
            logger.info(f"Successfully loaded cost data with {len(df)} rows")
            return df
        except Exception as e:
            logger.error(f"Error loading cost data: {e}")
            return pd.DataFrame()

    def _save_checkpoint(self, checkpoint_data: Dict):
        """Save progress checkpoint to disk."""
        try:
            with open(self.checkpoint_file, 'w') as f:
                json.dump(checkpoint_data, f, default=str, indent=2)
            logger.info(f"Checkpoint saved: {checkpoint_data.get('current_stage', 'unknown')}")
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
    
    def _load_checkpoint(self) -> Optional[Dict]:
        """Load progress checkpoint from disk."""
        try:
            if os.path.exists(self.checkpoint_file):
                with open(self.checkpoint_file, 'r') as f:
                    checkpoint = json.load(f)
                logger.info(f"Checkpoint loaded: {checkpoint.get('current_stage', 'unknown')}")
                return checkpoint
            return None
        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            return None
    
    def _clear_checkpoint(self):
        """Remove checkpoint file after successful completion."""
        try:
            if os.path.exists(self.checkpoint_file):
                os.remove(self.checkpoint_file)
                logger.info("Checkpoint cleared after successful completion")
        except Exception as e:
            logger.error(f"Failed to clear checkpoint: {e}")

    def get_cost_for_sku_date(self, sku: str, date: datetime) -> float:
        """Get cost for a specific SKU at a specific date."""
        if not sku or self.cost_data.empty:
            return 0.0
            
        # Handle DELETED- prefix
        lookup_sku = sku.replace("DELETED-", "") if sku.startswith("DELETED-") else sku

        sku_row = self.cost_data[self.cost_data["SKU"] == lookup_sku]
        if sku_row.empty:
            return 0.0

        year = date.year
        month = date.month

        # Turkish month names
        month_names = {
            1: "OCAK", 2: "SUBAT", 3: "MART", 4: "NISAN", 5: "MAYIS", 6: "HAZIRAN",
            7: "TEMMUZ", 8: "AGUSTOS", 9: "EYLUL", 10: "EKIM", 11: "KASIM", 12: "ARALIK",
        }
        month_name = month_names.get(month)
        if not month_name:
            return 0.0

        # Region prefixes
        prefixes = ["US", "EU", "AU"]
        
        # Column name patterns
        for prefix in prefixes:
            possible_columns = [
                f"{prefix} {month_name} {year}",
                f"{prefix} {year} {month_name}",
                f"{prefix} {month_name} {year % 100}",
                f"{prefix} {month_name}",
            ]
            
            # Add CALISMA/ÇALIŞMA variations
            all_columns = []
            for col in possible_columns:
                all_columns.extend([col, f"{col} CALISMA", f"{col} ÇALIŞMA"])

            for col in all_columns:
                if col in sku_row.columns:
                    try:
                        cost_value = sku_row[col].iloc[0]
                        if pd.notna(cost_value) and str(cost_value).strip():
                            return float(cost_value)
                    except (ValueError, TypeError, IndexError):
                        continue

        return 0.0

    async def connect(self):
        """Connect to the Prisma database."""
        try:
            await self.prisma.connect()
            logger.info("Database connection established.")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    async def disconnect(self):
        """Disconnect from the Prisma database."""
        try:
            await self.prisma.disconnect()
            logger.info("Database connection closed.")
        except Exception as e:
            logger.error(f"Error disconnecting from database: {e}")

    async def get_date_ranges_from_database(self) -> Optional[Tuple[datetime, datetime]]:
        """Get the earliest and latest order dates."""
        try:
            earliest_order = await self.prisma.order.find_first(
                order={"createdTimestamp": "asc"}
            )
            latest_order = await self.prisma.order.find_first(
                order={"createdTimestamp": "desc"}
            )

            if not earliest_order or not latest_order:
                logger.warning("No orders found in the database.")
                return None

            start_date = datetime.fromtimestamp(earliest_order.createdTimestamp)
            end_date = datetime.fromtimestamp(latest_order.createdTimestamp)
            return start_date, end_date
        except Exception as e:
            logger.error(f"Error getting date ranges: {e}")
            return None

    def generate_time_periods(self, start_date: datetime, end_date: datetime) -> Dict[str, List[DateRange]]:
        """Generate yearly, monthly, and weekly periods."""
        periods = {"yearly": [], "monthly": [], "weekly": []}
        
        # Yearly periods
        for year in range(start_date.year, end_date.year + 1):
            year_start = max(datetime(year, 1, 1), start_date)
            year_end = min(datetime(year, 12, 31, 23, 59, 59), end_date)
            periods["yearly"].append(DateRange(year_start, year_end))
        
        # Monthly periods
        current = datetime(start_date.year, start_date.month, 1)
        while current <= end_date:
            try:
                _, last_day = calendar.monthrange(current.year, current.month)
                month_end = datetime(current.year, current.month, last_day, 23, 59, 59)
                month_start = max(current, start_date)
                month_end = min(month_end, end_date)
                periods["monthly"].append(DateRange(month_start, month_end))
                
                # Move to next month
                if current.month == 12:
                    current = current.replace(year=current.year + 1, month=1)
                else:
                    current = current.replace(month=current.month + 1)
            except Exception as e:
                logger.error(f"Error generating monthly period for {current}: {e}")
                break
        
        # Weekly periods
        current = start_date - timedelta(days=start_date.weekday())
        while current <= end_date:
            week_end = current + timedelta(days=6, hours=23, minutes=59, seconds=59)
            week_start = max(current, start_date)
            week_end = min(week_end, end_date)
            periods["weekly"].append(DateRange(week_start, week_end))
            current += timedelta(weeks=1)
            
        return periods

    async def get_orders_in_range_by_sku(self, date_range: DateRange, sku: Optional[str] = None, 
                                        listing_id: Optional[int] = None) -> List:
        """Fetch orders within a date range filtered by SKU or listing using proper relationships."""
        try:
            start_ts = int(date_range.start_date.timestamp())
            end_ts = int(date_range.end_date.timestamp())

            where_clause = {
                "createdTimestamp": {"gte": start_ts, "lte": end_ts}
            }
            
            if sku:
                # Find listing_products with this SKU (normalized)
                listing_products = await self.prisma.listingproduct.find_many(
                    where={
                        "OR": [
                            {"sku": sku},
                            {"sku": f"DELETED-{sku}"}
                        ],
                        "isDeleted": False
                    }
                )
                
                if not listing_products:
                    return []
                
                product_ids = [lp.productId for lp in listing_products]
                where_clause["transactions"] = {
                    "some": {
                        "productId": {"in": product_ids}
                    }
                }
                
            elif listing_id:
                where_clause["transactions"] = {
                    "some": {
                        "listingId": listing_id
                    }
                }
            
            orders = await self.prisma.order.find_many(
                where=where_clause,
                include={
                    "transactions": {
                        "include": {
                            "listing": True,
                            "listingProduct": True
                        }
                    },
                    "shipments": True,
                    "refunds": True
                }
            )
            
            return orders
            
        except Exception as e:
            logger.error(f"Error fetching orders by SKU: {e}")
            return []

    async def get_all_skus(self) -> List[str]:
        """Get all unique SKUs from listing_products table."""
        try:
            listing_products = await self.prisma.listingproduct.find_many(
                where={
                    "sku": {"not": None},
                    "isDeleted": False
                },
                distinct=["sku"]
            )
            
            # Normalize SKUs by removing DELETED- prefix for grouping
            skus = set()
            for lp in listing_products:
                if lp.sku:
                    # Remove DELETED- prefix to get the base SKU
                    base_sku = lp.sku.replace("DELETED-", "") if lp.sku.startswith("DELETED-") else lp.sku
                    skus.add(base_sku)
            
            return list(skus)
        except Exception as e:
            logger.error(f"Error getting SKUs: {e}")
            return []

    async def get_all_listings(self) -> List[int]:
        """Get all unique listing IDs that have transactions."""
        try:
            transactions = await self.prisma.ordertransaction.find_many(
                where={"listingId": {"not": None}},
                distinct=["listingId"]
            )
            return [t.listingId for t in transactions if t.listingId]
        except Exception as e:
            logger.error(f"Error getting listings: {e}")
            return []

    async def get_seasonal_patterns(self, orders: List) -> Dict:
        """Analyze seasonal patterns in order data."""
        if not orders:
            return {
                "peak_month": None, "peak_day_of_week": None, 
                "peak_hour": None, "seasonality_index": 0
            }
        
        try:
            order_dates = [datetime.fromtimestamp(o.createdTimestamp) for o in orders]
            
            # Monthly analysis
            monthly_counts = defaultdict(int)
            for date in order_dates:
                monthly_counts[date.month] += 1
            
            peak_month = max(monthly_counts, key=monthly_counts.get) if monthly_counts else None
            
            # Day of week analysis
            daily_counts = defaultdict(int)
            for date in order_dates:
                daily_counts[date.weekday()] += 1
            
            peak_day_of_week = max(daily_counts, key=daily_counts.get) if daily_counts else None
            
            # Hour analysis
            hourly_counts = defaultdict(int)
            for date in order_dates:
                hourly_counts[date.hour] += 1
            
            peak_hour = max(hourly_counts, key=hourly_counts.get) if hourly_counts else None
            
            # Seasonality index
            seasonality_index = 0
            if len(monthly_counts) > 1:
                monthly_values = list(monthly_counts.values())
                mean_val = np.mean(monthly_values)
                if mean_val > 0:
                    seasonality_index = np.std(monthly_values) / mean_val
            
            return {
                "peak_month": peak_month,
                "peak_day_of_week": peak_day_of_week,
                "peak_hour": peak_hour,
                "seasonality_index": round(seasonality_index, 4)
            }
        except Exception as e:
            logger.error(f"Error analyzing seasonal patterns: {e}")
            return {
                "peak_month": None, "peak_day_of_week": None,
                "peak_hour": None, "seasonality_index": 0
            }

    async def get_inventory_insights_by_sku(self, sku: str) -> Dict:
        """Get inventory insights for a specific SKU across all its variations."""
        try:
            # Find all listing products that have this SKU
            listing_products = await self.prisma.listingproduct.find_many(
                where={
                    "OR": [
                        {"sku": sku},
                        {"sku": f"DELETED-{sku}"}
                    ],
                    "isDeleted": False
                },
                include={"offerings": True}
            )
            
            if not listing_products:
                return {"total_inventory": 0, "avg_price": 0, "price_range": 0, "active_variants": 0}
            
            total_inventory = 0
            prices = []
            active_variants = 0
            
            for product in listing_products:
                active_variants += 1
                for offering in product.offerings:
                    if offering.isEnabled and not offering.isDeleted:
                        total_inventory += offering.quantity or 0
                        if offering.price:
                            prices.append(float(offering.price))
            
            avg_price = np.mean(prices) if prices else 0
            price_range = max(prices) - min(prices) if len(prices) > 1 else 0
            
            return {
                "total_inventory": total_inventory,
                "avg_price": round(avg_price, 2),
                "price_range": round(price_range, 2),
                "active_variants": active_variants
            }
            
        except Exception as e:
            logger.error(f"Error getting inventory insights for SKU {sku}: {e}")
            return {"total_inventory": 0, "avg_price": 0, "price_range": 0, "active_variants": 0}

    async def get_inventory_insights_by_listing(self, listing_id: int) -> Dict:
        """Get inventory insights for all products in a listing."""
        try:
            listing = await self.prisma.listing.find_unique(
                where={"listingId": listing_id},
                include={
                    "products": {
                        "include": {"offerings": True}
                    }
                }
            )
            
            if not listing:
                return {"total_inventory": 0, "avg_price": 0, "price_range": 0, "active_variants": 0}
            
            total_inventory = 0
            prices = []
            active_variants = 0
            
            for product in listing.products:
                if not product.isDeleted:
                    active_variants += 1
                    for offering in product.offerings:
                        if offering.isEnabled and not offering.isDeleted:
                            total_inventory += offering.quantity or 0
                            if offering.price:
                                prices.append(float(offering.price))
            
            avg_price = np.mean(prices) if prices else 0
            price_range = max(prices) - min(prices) if len(prices) > 1 else 0
            
            return {
                "total_inventory": total_inventory,
                "avg_price": round(avg_price, 2),
                "price_range": round(price_range, 2),
                "active_variants": active_variants
            }
            
        except Exception as e:
            logger.error(f"Error getting inventory insights for listing {listing_id}: {e}")
            return {"total_inventory": 0, "avg_price": 0, "price_range": 0, "active_variants": 0}

    async def get_internal_benchmarks(self, listing_id: int) -> Dict:
        """Get internal benchmarking data comparing listing to shop averages."""
        try:
            all_listings = await self.prisma.listing.find_many()
            
            if len(all_listings) < 2:
                return {
                    "shop_avg_views": 0, "shop_avg_favorites": 0, 
                    "views_vs_shop_avg": 0, "favorites_vs_shop_avg": 0
                }
            
            # Calculate shop averages
            all_views = [l.views or 0 for l in all_listings]
            all_favorites = [l.numFavorers or 0 for l in all_listings]
            
            shop_avg_views = np.mean(all_views) if all_views else 0
            shop_avg_favorites = np.mean(all_favorites) if all_favorites else 0
            
            # Get current listing's performance
            current_listing = next((l for l in all_listings if l.listingId == listing_id), None)
            current_views = current_listing.views or 0 if current_listing else 0
            current_favorites = current_listing.numFavorers or 0 if current_listing else 0
            
            views_vs_shop = current_views / shop_avg_views if shop_avg_views > 0 else 0
            favorites_vs_shop = current_favorites / shop_avg_favorites if shop_avg_favorites > 0 else 0
            
            return {
                "shop_avg_views": round(shop_avg_views, 2),
                "shop_avg_favorites": round(shop_avg_favorites, 2),
                "views_vs_shop_avg": round(views_vs_shop, 4),
                "favorites_vs_shop_avg": round(favorites_vs_shop, 4)
            }
        except Exception as e:
            logger.error(f"Error getting internal benchmarks: {e}")
            return {
                "shop_avg_views": 0, "shop_avg_favorites": 0,
                "views_vs_shop_avg": 0, "favorites_vs_shop_avg": 0
            }

    async def calculate_financial_metrics(self, orders: List, date_range: DateRange, 
                                        sku: Optional[str] = None,
                                        listing_id: Optional[int] = None) -> Dict:
        """Calculate comprehensive financial and performance metrics."""
        if not orders:
            return await self._empty_metrics(sku, listing_id)

        cancelled_statuses = {"cancelled", "canceled"}
        completed_orders = [o for o in orders if o.status not in cancelled_statuses]
        cancelled_orders_count = len(orders) - len(completed_orders)

        if not completed_orders:
            metrics = await self._empty_metrics(sku, listing_id)
            metrics.update({
                "cancelled_orders": cancelled_orders_count,
                "cancellation_rate": 1.0 if cancelled_orders_count > 0 else 0.0,
                "period_start": date_range.start_date.strftime("%Y-%m-%d"),
                "period_end": date_range.end_date.strftime("%Y-%m-%d"),
                "period_days": (date_range.end_date - date_range.start_date).days + 1,
            })
            return metrics

        # Basic financial metrics
        total_revenue = sum(float(o.grandTotal or 0) for o in completed_orders)
        total_shipping_revenue = sum(float(o.totalShippingCost or 0) for o in completed_orders)
        total_tax_collected = sum(float(o.totalTaxCost or 0) for o in completed_orders)
        total_vat_collected = sum(float(o.totalVatCost or 0) for o in completed_orders)
        total_discounts_given = sum(float(o.discountAmt or 0) for o in completed_orders)
        total_gift_wrap_revenue = sum(float(o.giftWrapPrice or 0) for o in completed_orders)
        product_revenue = total_revenue - total_shipping_revenue - total_tax_collected - total_gift_wrap_revenue
        
        # Cost calculation and item analysis - CORRECTED FOR PROPER DATABASE RELATIONSHIPS
        total_cost = 0
        total_quantity_sold = 0
        unique_skus = set()
        
        for order in completed_orders:
            order_date = datetime.fromtimestamp(order.createdTimestamp)
            for trx in order.transactions:
                if not trx.productId:
                    continue
                
                # Get the SKU from the listing_product relationship
                transaction_sku = None
                if trx.listingProduct and trx.listingProduct.sku:
                    transaction_sku = trx.listingProduct.sku
                elif hasattr(trx, 'sku') and trx.sku:  # Fallback to transaction SKU if available
                    transaction_sku = trx.sku
                
                if not transaction_sku:
                    continue
                
                # Normalize the SKU (remove DELETED- prefix for cost lookup)
                base_sku = transaction_sku.replace("DELETED-", "") if transaction_sku.startswith("DELETED-") else transaction_sku
                
                # Filter transactions based on scope
                should_include = True
                if sku and base_sku != sku:
                    # For SKU analysis, only include transactions with matching base SKU
                    should_include = False
                elif listing_id and trx.listingId != listing_id:
                    # For listing analysis, only include transactions from this listing
                    should_include = False
                
                if should_include:
                    # Use the base SKU (without DELETED-) for cost lookup
                    cost = self.get_cost_for_sku_date(base_sku, order_date)
                    total_cost += cost * (trx.quantity or 0)
                    total_quantity_sold += trx.quantity or 0
                    unique_skus.add(base_sku)

        avg_cost_per_item = total_cost / total_quantity_sold if total_quantity_sold > 0 else 0
        gross_profit = total_revenue - total_cost
        
        # Order and item metrics
        total_orders = len(completed_orders)
        total_items = sum(o.itemCount or 0 for o in completed_orders)
        
        # Customer metrics
        customer_ids = [o.buyerUserId for o in completed_orders if o.buyerUserId]
        unique_customers = len(set(customer_ids))
        repeat_customers = len(customer_ids) - unique_customers
        
        # Payment method analysis
        payment_methods = [o.paymentMethod for o in completed_orders if o.paymentMethod]
        payment_method_counts = defaultdict(int)
        for pm in payment_methods:
            payment_method_counts[pm] += 1
        
        # Operational metrics
        shipped_orders = [o for o in completed_orders if o.isShipped]
        shipped_count = len(shipped_orders)
        shipping_rate = shipped_count / total_orders if total_orders > 0 else 0
        
        gift_orders = [o for o in completed_orders if o.isGift]
        gift_order_count = len(gift_orders)
        gift_rate = gift_order_count / total_orders if total_orders > 0 else 0
        
        # Revenue distribution
        order_values = [float(o.grandTotal or 0) for o in completed_orders]
        median_order_value = float(np.median(order_values)) if order_values else 0
        percentile_75_order_value = float(np.percentile(order_values, 75)) if order_values else 0
        percentile_25_order_value = float(np.percentile(order_values, 25)) if order_values else 0
        order_value_std = float(np.std(order_values)) if order_values else 0
        
        # Time analysis
        avg_time_between_orders = 0
        if len(completed_orders) > 1:
            order_timestamps = sorted([o.createdTimestamp for o in completed_orders])
            time_diffs = [
                (order_timestamps[i] - order_timestamps[i-1]) / 3600 
                for i in range(1, len(order_timestamps))
            ]
            avg_time_between_orders = np.mean(time_diffs) if time_diffs else 0
        
        # Refund metrics
        total_refund_amount = sum(float(r.amount or 0) for o in completed_orders for r in o.refunds)
        total_refund_count = sum(len(o.refunds) for o in completed_orders)
        orders_with_refunds = len([o for o in completed_orders if o.refunds])
        
        # Net calculations
        net_revenue = total_revenue - total_refund_amount
        net_profit = gross_profit - total_refund_amount
        
        # Business Intelligence Metrics
        avg_customer_value = total_revenue / unique_customers if unique_customers > 0 else 0
        customer_retention_rate = repeat_customers / unique_customers if unique_customers > 0 else 0
        estimated_clv = avg_customer_value * (1 + customer_retention_rate)
        
        customer_acquisition_cost = total_cost / unique_customers if unique_customers > 0 else 0
        
        period_days = (date_range.end_date - date_range.start_date).days + 1
        daily_profit_per_customer = (gross_profit / unique_customers) / period_days if unique_customers > 0 and period_days > 0 else 0
        payback_period_days = customer_acquisition_cost / daily_profit_per_customer if daily_profit_per_customer > 0 else 0
        
        # Price elasticity estimation
        price_elasticity = 0
        if total_discounts_given > 0 and total_revenue > 0 and total_items > 0:
            discount_percentage = total_discounts_given / (total_revenue + total_discounts_given)
            if discount_percentage > 0:
                estimated_quantity_increase = total_items * 0.1
                price_elasticity = (estimated_quantity_increase / total_items) / discount_percentage

        # Compile all metrics
        metrics = {
            # Time period
            "period_start": date_range.start_date.strftime("%Y-%m-%d"),
            "period_end": date_range.end_date.strftime("%Y-%m-%d"),
            "period_days": period_days,
            
            # Revenue breakdown
            "total_revenue": round(total_revenue, 2),
            "product_revenue": round(product_revenue, 2),
            "total_shipping_revenue": round(total_shipping_revenue, 2),
            "total_tax_collected": round(total_tax_collected, 2),
            "total_vat_collected": round(total_vat_collected, 2),
            "total_gift_wrap_revenue": round(total_gift_wrap_revenue, 2),
            "total_discounts_given": round(total_discounts_given, 2),
            "net_revenue": round(net_revenue, 2),
            "discount_rate": round(total_discounts_given / total_revenue, 4) if total_revenue > 0 else 0,
            
            # Cost and profit metrics
            "total_cost": round(total_cost, 2),
            "avg_cost_per_item": round(avg_cost_per_item, 2),
            "cost_per_order": round(total_cost / total_orders, 2) if total_orders > 0 else 0,
            "gross_profit": round(gross_profit, 2),
            "gross_margin": round(gross_profit / total_revenue, 4) if total_revenue > 0 else 0,
            "net_profit": round(net_profit, 2),
            "net_margin": round(net_profit / total_revenue, 4) if total_revenue > 0 else 0,
            "return_on_revenue": round(net_profit / total_revenue, 4) if total_revenue > 0 else 0,
            "markup_ratio": round(gross_profit / total_cost, 4) if total_cost > 0 else 0,
            
            # Order metrics
            "total_orders": total_orders,
            "total_items": total_items,
            "total_quantity_sold": total_quantity_sold,
            "unique_skus": len(unique_skus),
            "average_order_value": round(total_revenue / total_orders, 2) if total_orders > 0 else 0,
            "median_order_value": round(median_order_value, 2),
            "percentile_75_order_value": round(percentile_75_order_value, 2),
            "percentile_25_order_value": round(percentile_25_order_value, 2),
            "order_value_std": round(order_value_std, 2),
            "items_per_order": round(total_items / total_orders, 2) if total_orders > 0 else 0,
            "revenue_per_item": round(total_revenue / total_items, 2) if total_items > 0 else 0,
            "profit_per_item": round(gross_profit / total_items, 2) if total_items > 0 else 0,
            
            # Customer metrics
            "unique_customers": unique_customers,
            "repeat_customers": repeat_customers,
            "customer_retention_rate": round(customer_retention_rate, 4),
            "revenue_per_customer": round(avg_customer_value, 2),
            "orders_per_customer": round(total_orders / unique_customers, 2) if unique_customers > 0 else 0,
            "profit_per_customer": round(gross_profit / unique_customers, 2) if unique_customers > 0 else 0,
            
            # Operational metrics
            "shipped_orders": shipped_count,
            "shipping_rate": round(shipping_rate, 4),
            "gift_orders": gift_order_count,
            "gift_rate": round(gift_rate, 4),
            "avg_time_between_orders_hours": round(avg_time_between_orders, 2),
            "orders_per_day": round(total_orders / period_days, 2),
            "revenue_per_day": round(total_revenue / period_days, 2),
            
            # Refund metrics
            "total_refund_amount": round(total_refund_amount, 2),
            "total_refund_count": total_refund_count,
            "orders_with_refunds": orders_with_refunds,
            "refund_rate_by_order": round(total_refund_count / total_orders, 4) if total_orders > 0 else 0,
            "refund_rate_by_value": round(total_refund_amount / total_revenue, 4) if total_revenue > 0 else 0,
            "order_refund_rate": round(orders_with_refunds / total_orders, 4) if total_orders > 0 else 0,
            
            # Cancellation metrics
            "cancelled_orders": cancelled_orders_count,
            "cancellation_rate": round(cancelled_orders_count / len(orders), 4) if len(orders) > 0 else 0,
            "completion_rate": round(total_orders / len(orders), 4) if len(orders) > 0 else 0,
            
            # Payment methods
            "primary_payment_method": max(payment_method_counts, key=payment_method_counts.get) if payment_method_counts else None,
            "payment_method_diversity": len(payment_method_counts),
            
            # Business intelligence
            "customer_lifetime_value": round(estimated_clv, 2),
            "payback_period_days": round(payback_period_days, 1),
            "customer_acquisition_cost": round(customer_acquisition_cost, 2),
            "price_elasticity": round(price_elasticity, 4),
        }

        # Add seasonal patterns
        seasonal_data = await self.get_seasonal_patterns(completed_orders)
        metrics.update(seasonal_data)
        
        # Add inventory insights based on analysis type
        if sku:
            # For SKU analysis, get inventory for this specific SKU via product lookup
            inventory_data = await self.get_inventory_insights_by_sku(sku)
        elif listing_id:
            # For listing analysis, get aggregated inventory for all products in listing
            inventory_data = await self.get_inventory_insights_by_listing(listing_id)
        else:
            # For shop analysis, get overall inventory
            inventory_data = {"total_inventory": 0, "avg_price": 0, "price_range": 0, "active_variants": 0}
        
        metrics.update(inventory_data)
        
        # Calculate inventory turnover
        inventory_turnover = total_quantity_sold / inventory_data.get("total_inventory", 1) if inventory_data.get("total_inventory", 0) > 0 else 0
        stockout_risk = max(0, min(1, 1 - (inventory_data.get("total_inventory", 0) / max(total_quantity_sold, 1))))
        
        metrics.update({
            "inventory_turnover": round(inventory_turnover, 4),
            "stockout_risk": round(stockout_risk, 4),
        })

        # Add listing-specific metrics
        if listing_id:
            try:
                listing = await self.prisma.listing.find_unique(
                    where={"listingId": listing_id}
                )
                
                views = listing.views or 0 if listing else 0
                favorites = listing.numFavorers or 0 if listing else 0
                
                # Get internal benchmarks
                benchmark_data = await self.get_internal_benchmarks(listing_id)
                
                listing_metrics = {
                    "listing_views": views,
                    "listing_favorites": favorites,
                    "conversion_rate": round(total_orders / views, 6) if views > 0 else 0,
                    "favorite_to_order_rate": round(total_orders / favorites, 4) if favorites > 0 else 0,
                    "view_to_favorite_rate": round(favorites / views, 4) if views > 0 else 0,
                    "revenue_per_view": round(total_revenue / views, 4) if views > 0 else 0,
                    "profit_per_view": round(gross_profit / views, 4) if views > 0 else 0,
                    "cost_per_acquisition": round(total_cost / total_orders, 2) if total_orders > 0 else 0,
                }
                listing_metrics.update(benchmark_data)
                metrics.update(listing_metrics)
            except Exception as e:
                logger.error(f"Error adding listing metrics: {e}")

        return metrics

    async def _empty_metrics(self, sku: Optional[str] = None, 
                           listing_id: Optional[int] = None) -> Dict:
        """Return empty metrics with async operations."""
        base_metrics = {
            # Time period (will be filled by caller)
            "period_days": 0,
            
            # Revenue breakdown
            "total_revenue": 0, "product_revenue": 0, "total_shipping_revenue": 0, 
            "total_tax_collected": 0, "total_vat_collected": 0, "total_gift_wrap_revenue": 0,
            "total_discounts_given": 0, "net_revenue": 0, "discount_rate": 0,
            
            # Cost and profit
            "total_cost": 0, "avg_cost_per_item": 0, "cost_per_order": 0, "gross_profit": 0, 
            "gross_margin": 0, "net_profit": 0, "net_margin": 0, "return_on_revenue": 0, "markup_ratio": 0,
            
            # Orders and items
            "total_orders": 0, "total_items": 0, "total_quantity_sold": 0, "unique_skus": 0,
            "average_order_value": 0, "median_order_value": 0, "percentile_75_order_value": 0,
            "percentile_25_order_value": 0, "order_value_std": 0, "items_per_order": 0,
            "revenue_per_item": 0, "profit_per_item": 0,
            
            # Customer metrics
            "unique_customers": 0, "repeat_customers": 0, "customer_retention_rate": 0,
            "revenue_per_customer": 0, "orders_per_customer": 0, "profit_per_customer": 0,
            
            # Operational metrics
            "shipped_orders": 0, "shipping_rate": 0, "gift_orders": 0, "gift_rate": 0,
            "avg_time_between_orders_hours": 0, "orders_per_day": 0, "revenue_per_day": 0,
            
            # Refund metrics
            "total_refund_amount": 0, "total_refund_count": 0, "orders_with_refunds": 0,
            "refund_rate_by_order": 0, "refund_rate_by_value": 0, "order_refund_rate": 0,
            
            # Cancellation metrics
            "cancelled_orders": 0, "cancellation_rate": 0, "completion_rate": 0,
            
            # Payment methods
            "primary_payment_method": None, "payment_method_diversity": 0,
            
            # Seasonal patterns
            "peak_month": None, "peak_day_of_week": None, "peak_hour": None, "seasonality_index": 0,
            
            # Inventory insights
            "total_inventory": 0, "avg_price": 0, "price_range": 0, "active_variants": 0,
            "inventory_turnover": 0, "stockout_risk": 0,
            
            # Business intelligence
            "customer_lifetime_value": 0, "payback_period_days": 0, "customer_acquisition_cost": 0,
            "price_elasticity": 0,
        }
        
        # Add seasonal patterns (empty)
        seasonal_data = await self.get_seasonal_patterns([])
        base_metrics.update(seasonal_data)
        
        # Add inventory insights based on analysis type
        if sku:
            inventory_data = await self.get_inventory_insights_by_sku(sku)
        elif listing_id:
            inventory_data = await self.get_inventory_insights_by_listing(listing_id)
        else:
            inventory_data = {"total_inventory": 0, "avg_price": 0, "price_range": 0, "active_variants": 0}
        
        base_metrics.update(inventory_data)
        
        # Add listing-specific empty metrics
        if listing_id:
            benchmark_data = await self.get_internal_benchmarks(listing_id)
            listing_metrics = {
                "listing_views": 0, "listing_favorites": 0, "conversion_rate": 0, 
                "favorite_to_order_rate": 0, "view_to_favorite_rate": 0, 
                "revenue_per_view": 0, "profit_per_view": 0, "cost_per_acquisition": 0,
            }
            listing_metrics.update(benchmark_data)
            base_metrics.update(listing_metrics)
        
        return base_metrics

    # --- DATABASE OPERATIONS ---

    async def save_shop_report(self, metrics: Dict, period_type: str, 
                              period_start: datetime, period_end: datetime) -> None:
        """Save shop report to database."""
        try:
            # Map period_type string to enum
            period_type_enum = {
                "yearly": PeriodType.YEARLY,
                "monthly": PeriodType.MONTHLY, 
                "weekly": PeriodType.WEEKLY
            }[period_type]
            
            payload={
                    "periodType": period_type_enum,
                    "periodStart": period_start,
                    "periodEnd": period_end,
                    "periodDays": metrics.get("period_days", 0),
                    "totalRevenue": metrics.get("total_revenue", 0),
                    "productRevenue": metrics.get("product_revenue", 0),
                    "totalShippingRevenue": metrics.get("total_shipping_revenue", 0),
                    "totalTaxCollected": metrics.get("total_tax_collected", 0),
                    "totalVatCollected": metrics.get("total_vat_collected", 0),
                    "totalGiftWrapRevenue": metrics.get("total_gift_wrap_revenue", 0),
                    "totalDiscountsGiven": metrics.get("total_discounts_given", 0),
                    "netRevenue": metrics.get("net_revenue", 0),
                    "discountRate": metrics.get("discount_rate", 0),
                    "totalCost": metrics.get("total_cost", 0),
                    "avgCostPerItem": metrics.get("avg_cost_per_item", 0),
                    "costPerOrder": metrics.get("cost_per_order", 0),
                    "grossProfit": metrics.get("gross_profit", 0),
                    "grossMargin": metrics.get("gross_margin", 0),
                    "netProfit": metrics.get("net_profit", 0),
                    "netMargin": metrics.get("net_margin", 0),
                    "returnOnRevenue": metrics.get("return_on_revenue", 0),
                    "markupRatio": metrics.get("markup_ratio", 0),
                    "totalOrders": metrics.get("total_orders", 0),
                    "totalItems": metrics.get("total_items", 0),
                    "totalQuantitySold": metrics.get("total_quantity_sold", 0),
                    "uniqueSkus": metrics.get("unique_skus", 0),
                    "averageOrderValue": metrics.get("average_order_value", 0),
                    "medianOrderValue": metrics.get("median_order_value", 0),
                    "percentile75OrderValue": metrics.get("percentile_75_order_value", 0),
                    "percentile25OrderValue": metrics.get("percentile_25_order_value", 0),
                    "orderValueStd": metrics.get("order_value_std", 0),
                    "itemsPerOrder": metrics.get("items_per_order", 0),
                    "revenuePerItem": metrics.get("revenue_per_item", 0),
                    "profitPerItem": metrics.get("profit_per_item", 0),
                    "uniqueCustomers": metrics.get("unique_customers", 0),
                    "repeatCustomers": metrics.get("repeat_customers", 0),
                    "customerRetentionRate": metrics.get("customer_retention_rate", 0),
                    "revenuePerCustomer": metrics.get("revenue_per_customer", 0),
                    "ordersPerCustomer": metrics.get("orders_per_customer", 0),
                    "profitPerCustomer": metrics.get("profit_per_customer", 0),
                    "shippedOrders": metrics.get("shipped_orders", 0),
                    "shippingRate": metrics.get("shipping_rate", 0),
                    "giftOrders": metrics.get("gift_orders", 0),
                    "giftRate": metrics.get("gift_rate", 0),
                    "avgTimeBetweenOrdersHours": metrics.get("avg_time_between_orders_hours", 0),
                    "ordersPerDay": metrics.get("orders_per_day", 0),
                    "revenuePerDay": metrics.get("revenue_per_day", 0),
                    "totalRefundAmount": metrics.get("total_refund_amount", 0),
                    "totalRefundCount": metrics.get("total_refund_count", 0),
                    "ordersWithRefunds": metrics.get("orders_with_refunds", 0),
                    "refundRateByOrder": metrics.get("refund_rate_by_order", 0),
                    "refundRateByValue": metrics.get("refund_rate_by_value", 0),
                    "orderRefundRate": metrics.get("order_refund_rate", 0),
                    "cancelledOrders": metrics.get("cancelled_orders", 0),
                    "cancellationRate": metrics.get("cancellation_rate", 0),
                    "completionRate": metrics.get("completion_rate", 0),
                    "primaryPaymentMethod": metrics.get("primary_payment_method"),
                    "paymentMethodDiversity": metrics.get("payment_method_diversity", 0),
                    "customerLifetimeValue": metrics.get("customer_lifetime_value", 0),
                    "paybackPeriodDays": metrics.get("payback_period_days", 0),
                    "customerAcquisitionCost": metrics.get("customer_acquisition_cost", 0),
                    "priceElasticity": metrics.get("price_elasticity", 0),
                    "peakMonth": metrics.get("peak_month"),
                    "peakDayOfWeek": metrics.get("peak_day_of_week"),
                    "peakHour": metrics.get("peak_hour"),
                    "seasonalityIndex": metrics.get("seasonality_index", 0),
                    "totalInventory": metrics.get("total_inventory", 0),
                    "avgPrice": metrics.get("avg_price", 0),
                    "priceRange": metrics.get("price_range", 0),
                    "activeVariants": metrics.get("active_variants", 0),
                    "inventoryTurnover": metrics.get("inventory_turnover", 0),
                    "stockoutRisk": metrics.get("stockout_risk", 0),
                }
            
            # Create or update report
            await self.prisma.shopreport.upsert(
                where={
                    "periodType_periodStart_periodEnd": {
                        "periodType": period_type_enum,
                        "periodStart": period_start,
                        "periodEnd": period_end
                    }
                },
                data={
                    'create': payload,
                    'update': payload
                }
            )
            
        except Exception as e:
            logger.error(f"Error saving product report: {e}")
            raise

    async def _generate_insights_db(
        self,
        insight_type: str,
        date_periods: Dict[str, List[DateRange]],
        ids: Optional[List[Union[str, int]]] = None,
        checkpoint: Optional[Dict] = None
    ):
        """Generate insights with checkpoint support and save directly to database."""
        
        # Determine starting point from checkpoint
        start_period_type = checkpoint.get("current_period_type", None) if checkpoint else None
        start_period_key = checkpoint.get("current_period_key", None) if checkpoint else None
        start_item_id = checkpoint.get("current_item_id", None) if checkpoint else None
        completed_items = set(checkpoint.get("completed_items", [])) if checkpoint else set()
        
        skip_until_resume_point = bool(checkpoint and start_period_type)
        
        for period_type, periods in date_periods.items():
            # Skip periods until we reach the resume point
            if skip_until_resume_point and period_type != start_period_type:
                continue
            elif period_type == start_period_type:
                skip_until_resume_point = False
            
            logger.info(f"--> Calculating {period_type.upper()} {insight_type.upper()} insights...")
            
            for date_range in periods:
                period_key = f"{date_range.start_date.strftime('%Y-%m-%d')}_to_{date_range.end_date.strftime('%Y-%m-%d')}"
                
                # Skip periods until we reach the resume point
                if start_period_key and period_key != start_period_key and period_type == start_period_type:
                    continue
                elif period_key == start_period_key:
                    start_period_key = None  # Clear after reaching resume point
                
                items_to_process = ids if ids else [None]
                for item_id in items_to_process:
                    # Skip completed items if resuming
                    item_key = f"{insight_type}_{period_type}_{period_key}_{item_id}"
                    if item_key in completed_items:
                        continue
                    
                    try:
                        # Use the correct method based on insight type
                        if insight_type == "sku":
                            orders = await self.get_orders_in_range_by_sku(
                                date_range, sku=item_id
                            )
                            metrics = await self.calculate_financial_metrics(
                                orders, date_range, sku=item_id
                            )
                        elif insight_type == "listing":
                            orders = await self.get_orders_in_range_by_sku(
                                date_range, listing_id=item_id
                            )
                            metrics = await self.calculate_financial_metrics(
                                orders, date_range, listing_id=item_id
                            )
                        else:  # shop-wide
                            orders = await self.get_orders_in_range_by_sku(date_range)
                            metrics = await self.calculate_financial_metrics(
                                orders, date_range
                            )
                        
                        # Skip empty periods unless there were cancellations
                        if not orders and metrics.get('cancelled_orders', 0) == 0:
                            completed_items.add(item_key)
                            continue

                        # Save to database based on insight type
                        if insight_type == "sku":
                            await self.save_product_report(
                                item_id, metrics, period_type,
                                date_range.start_date, date_range.end_date
                            )
                        elif insight_type == "listing":
                            await self.save_listing_report(
                                item_id, metrics, period_type,
                                date_range.start_date, date_range.end_date
                            )
                        else:  # shop-wide
                            await self.save_shop_report(
                                metrics, period_type,
                                date_range.start_date, date_range.end_date
                            )
                        
                        id_str = f"ID: {item_id:<15}" if item_id else " " * 19
                        revenue = metrics.get('total_revenue', 0)
                        print(f"  ✅ {insight_type.upper():<15} | {period_type.upper():<7} | {period_key} | {id_str} | Revenue: ${revenue:>8.2f} | 💾 SAVED TO DB")
                        
                        # Mark as completed and save checkpoint periodically
                        completed_items.add(item_key)
                        if len(completed_items) % 10 == 0:  # Save checkpoint every 10 items
                            checkpoint_data = {
                                "current_stage": f"{insight_type}_insights",
                                "current_period_type": period_type,
                                "current_period_key": period_key,
                                "current_item_id": item_id,
                                "completed_items": list(completed_items),
                                "timestamp": datetime.now().isoformat()
                            }
                            self._save_checkpoint(checkpoint_data)
                            
                    except Exception as e:
                        logger.error(f"Error processing {insight_type} {item_id} for period {period_key}: {e}")
                        continue

    async def generate_executive_summary_db(self) -> Dict:
        """Generate executive summary using data from database tables."""
        try:
            summary = {
                "report_date": datetime.now().isoformat(),
                "key_metrics": {},
                "top_performers": {},
                "areas_for_improvement": [],
                "recommendations": [],
                "risk_factors": [],
                "opportunities": []
            }
            
            # Get latest shop metrics from database
            latest_shop_report = await self.prisma.shopreport.find_first(
                order={"periodEnd": "desc"}
            )
            
            if latest_shop_report:
                summary["key_metrics"] = {
                    "total_revenue": float(latest_shop_report.totalRevenue),
                    "gross_profit": float(latest_shop_report.grossProfit),
                    "gross_margin": float(latest_shop_report.grossMargin),
                    "total_orders": latest_shop_report.totalOrders,
                    "unique_customers": latest_shop_report.uniqueCustomers,
                    "customer_lifetime_value": float(latest_shop_report.customerLifetimeValue)
                }
            
            # Find top performing listings from database
            top_listings = await self.prisma.listingreport.find_many(
                where={"periodType": PeriodType.MONTHLY},
                order={"totalRevenue": "desc"},
                take=5
            )
            
            summary["top_performers"]["by_revenue"] = [
                {
                    "listing_id": report.listingId,
                    "revenue": float(report.totalRevenue)
                }
                for report in top_listings if report.totalRevenue > 0
            ]
            
            # Generate recommendations based on metrics
            if latest_shop_report:
                gross_margin = float(latest_shop_report.grossMargin)
                clv = float(latest_shop_report.customerLifetimeValue)
                
                if gross_margin < 0.3:
                    summary["areas_for_improvement"].append("Low profit margins")
                    summary["recommendations"].append("Review pricing strategy and optimize costs")
                
                if clv > 0:
                    revenue = float(latest_shop_report.totalRevenue)
                    customers = latest_shop_report.uniqueCustomers or 1
                    cac = revenue / customers
                    clv_cac_ratio = clv / max(cac, 1)
                    
                    if clv_cac_ratio < 3:
                        summary["risk_factors"].append("Low CLV to CAC ratio")
                        summary["recommendations"].append("Focus on customer retention strategies")
                
                if gross_margin > 0.5:
                    summary["opportunities"].append("Strong margins - consider scaling successful products")
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating executive summary: {e}")
            return {"error": f"Failed to generate executive summary: {str(e)}"}

    async def clean_old_reports(self, keep_latest_n: int = 5):
        """Clean old report data to prevent database bloat."""
        try:
            logger.info(f"Cleaning old reports, keeping latest {keep_latest_n} for each type...")
            
            # Clean shop reports (keep latest N by period end)
            shop_reports = await self.prisma.shopreport.find_many(
                order={"periodEnd": "desc"},
                skip=keep_latest_n
            )
            if shop_reports:
                report_ids = [r.id for r in shop_reports]
                deleted_count = await self.prisma.shopreport.delete_many(
                    where={"id": {"in": report_ids}}
                )
                logger.info(f"Cleaned {deleted_count} old shop reports")
            
            # Clean listing reports (keep latest N per listing)
            listings = await self.prisma.listingreport.find_many(
                distinct=["listingId"]
            )
            
            for listing in listings:
                old_reports = await self.prisma.listingreport.find_many(
                    where={"listingId": listing.listingId},
                    order={"periodEnd": "desc"},
                    skip=keep_latest_n
                )
                if old_reports:
                    report_ids = [r.id for r in old_reports]
                    await self.prisma.listingreport.delete_many(
                        where={"id": {"in": report_ids}}
                    )
            
            # Clean product reports (keep latest N per SKU)
            skus = await self.prisma.productreport.find_many(
                distinct=["sku"]
            )
            
            for sku_report in skus:
                old_reports = await self.prisma.productreport.find_many(
                    where={"sku": sku_report.sku},
                    order={"periodEnd": "desc"},
                    skip=keep_latest_n
                )
                if old_reports:
                    report_ids = [r.id for r in old_reports]
                    await self.prisma.productreport.delete_many(
                        where={"id": {"in": report_ids}}
                    )
                    
            logger.info("Report cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during report cleanup: {e}")
    
    

    async def save_listing_report(self, listing_id: int, metrics: Dict, period_type: str,
                                 period_start: datetime, period_end: datetime) -> None:
        """Save listing report to database."""
        try:
            # Map period_type string to enum
            period_type_enum = {
                "yearly": PeriodType.YEARLY,
                "monthly": PeriodType.MONTHLY,
                "weekly": PeriodType.WEEKLY
            }[period_type]
            
            payload = {
                    "listingId": listing_id,
                    "periodType": period_type_enum,
                    "periodStart": period_start,
                    "periodEnd": period_end,
                    "periodDays": metrics.get("period_days", 0),
                    "totalRevenue": metrics.get("total_revenue", 0),
                    "productRevenue": metrics.get("product_revenue", 0),
                    "totalShippingRevenue": metrics.get("total_shipping_revenue", 0),
                    "totalTaxCollected": metrics.get("total_tax_collected", 0),
                    "totalVatCollected": metrics.get("total_vat_collected", 0),
                    "totalGiftWrapRevenue": metrics.get("total_gift_wrap_revenue", 0),
                    "totalDiscountsGiven": metrics.get("total_discounts_given", 0),
                    "netRevenue": metrics.get("net_revenue", 0),
                    "discountRate": metrics.get("discount_rate", 0),
                    "totalCost": metrics.get("total_cost", 0),
                    "avgCostPerItem": metrics.get("avg_cost_per_item", 0),
                    "costPerOrder": metrics.get("cost_per_order", 0),
                    "grossProfit": metrics.get("gross_profit", 0),
                    "grossMargin": metrics.get("gross_margin", 0),
                    "netProfit": metrics.get("net_profit", 0),
                    "netMargin": metrics.get("net_margin", 0),
                    "returnOnRevenue": metrics.get("return_on_revenue", 0),
                    "markupRatio": metrics.get("markup_ratio", 0),
                    "totalOrders": metrics.get("total_orders", 0),
                    "totalItems": metrics.get("total_items", 0),
                    "totalQuantitySold": metrics.get("total_quantity_sold", 0),
                    "uniqueSkus": metrics.get("unique_skus", 0),
                    "averageOrderValue": metrics.get("average_order_value", 0),
                    "medianOrderValue": metrics.get("median_order_value", 0),
                    "percentile75OrderValue": metrics.get("percentile_75_order_value", 0),
                    "percentile25OrderValue": metrics.get("percentile_25_order_value", 0),
                    "orderValueStd": metrics.get("order_value_std", 0),
                    "itemsPerOrder": metrics.get("items_per_order", 0),
                    "revenuePerItem": metrics.get("revenue_per_item", 0),
                    "profitPerItem": metrics.get("profit_per_item", 0),
                    "uniqueCustomers": metrics.get("unique_customers", 0),
                    "repeatCustomers": metrics.get("repeat_customers", 0),
                    "customerRetentionRate": metrics.get("customer_retention_rate", 0),
                    "revenuePerCustomer": metrics.get("revenue_per_customer", 0),
                    "ordersPerCustomer": metrics.get("orders_per_customer", 0),
                    "profitPerCustomer": metrics.get("profit_per_customer", 0),
                    "shippedOrders": metrics.get("shipped_orders", 0),
                    "shippingRate": metrics.get("shipping_rate", 0),
                    "giftOrders": metrics.get("gift_orders", 0),
                    "giftRate": metrics.get("gift_rate", 0),
                    "avgTimeBetweenOrdersHours": metrics.get("avg_time_between_orders_hours", 0),
                    "ordersPerDay": metrics.get("orders_per_day", 0),
                    "revenuePerDay": metrics.get("revenue_per_day", 0),
                    "totalRefundAmount": metrics.get("total_refund_amount", 0),
                    "totalRefundCount": metrics.get("total_refund_count", 0),
                    "ordersWithRefunds": metrics.get("orders_with_refunds", 0),
                    "refundRateByOrder": metrics.get("refund_rate_by_order", 0),
                    "refundRateByValue": metrics.get("refund_rate_by_value", 0),
                    "orderRefundRate": metrics.get("order_refund_rate", 0),
                    "cancelledOrders": metrics.get("cancelled_orders", 0),
                    "cancellationRate": metrics.get("cancellation_rate", 0),
                    "completionRate": metrics.get("completion_rate", 0),
                    "primaryPaymentMethod": metrics.get("primary_payment_method"),
                    "paymentMethodDiversity": metrics.get("payment_method_diversity", 0),
                    "customerLifetimeValue": metrics.get("customer_lifetime_value", 0),
                    "paybackPeriodDays": metrics.get("payback_period_days", 0),
                    "customerAcquisitionCost": metrics.get("customer_acquisition_cost", 0),
                    "priceElasticity": metrics.get("price_elasticity", 0),
                    "peakMonth": metrics.get("peak_month"),
                    "peakDayOfWeek": metrics.get("peak_day_of_week"),
                    "peakHour": metrics.get("peak_hour"),
                    "seasonalityIndex": metrics.get("seasonality_index", 0),
                    "totalInventory": metrics.get("total_inventory", 0),
                    "avgPrice": metrics.get("avg_price", 0),
                    "priceRange": metrics.get("price_range", 0),
                    "activeVariants": metrics.get("active_variants", 0),
                    "inventoryTurnover": metrics.get("inventory_turnover", 0),
                    "stockoutRisk": metrics.get("stockout_risk", 0),
                    # Listing-specific fields
                    "listingViews": metrics.get("listing_views", 0),
                    "listingFavorites": metrics.get("listing_favorites", 0),
                    "conversionRate": metrics.get("conversion_rate", 0),
                    "favoriteToOrderRate": metrics.get("favorite_to_order_rate", 0),
                    "viewToFavoriteRate": metrics.get("view_to_favorite_rate", 0),
                    "revenuePerView": metrics.get("revenue_per_view", 0),
                    "profitPerView": metrics.get("profit_per_view", 0),
                    "costPerAcquisition": metrics.get("cost_per_acquisition", 0),
                    "shopAvgViews": metrics.get("shop_avg_views", 0),
                    "shopAvgFavorites": metrics.get("shop_avg_favorites", 0),
                    "viewsVsShopAvg": metrics.get("views_vs_shop_avg", 0),
                    "favoritesVsShopAvg": metrics.get("favorites_vs_shop_avg", 0),
                }
            
            # Create or update report
            await self.prisma.listingreport.upsert(
                where={
                    "listingId_periodType_periodStart_periodEnd": {
                        "listingId": listing_id,
                        "periodType": period_type_enum,
                        "periodStart": period_start,
                        "periodEnd": period_end
                    }
                },
                data={
                    'create': payload,
                    'update': payload
                },
            )
            
        except Exception as e:
            logger.error(f"Error saving listing report: {e}")
            raise

    async def save_product_report(self, sku: str, metrics: Dict, period_type: str,
                                 period_start: datetime, period_end: datetime) -> None:
        """Save product report to database."""
        try:
            # Map period_type string to enum
            period_type_enum = {
                "yearly": PeriodType.YEARLY,
                "monthly": PeriodType.MONTHLY,
                "weekly": PeriodType.WEEKLY
            }[period_type]
            
            payload = {
                    "sku": sku,
                    "periodType": period_type_enum,
                    "periodStart": period_start,
                    "periodEnd": period_end,
                    "periodDays": metrics.get("period_days", 0),
                    "totalRevenue": metrics.get("total_revenue", 0),
                    "productRevenue": metrics.get("product_revenue", 0),
                    "totalShippingRevenue": metrics.get("total_shipping_revenue", 0),
                    "totalTaxCollected": metrics.get("total_tax_collected", 0),
                    "totalVatCollected": metrics.get("total_vat_collected", 0),
                    "totalGiftWrapRevenue": metrics.get("total_gift_wrap_revenue", 0),
                    "totalDiscountsGiven": metrics.get("total_discounts_given", 0),
                    "netRevenue": metrics.get("net_revenue", 0),
                    "discountRate": metrics.get("discount_rate", 0),
                    "totalCost": metrics.get("total_cost", 0),
                    "avgCostPerItem": metrics.get("avg_cost_per_item", 0),
                    "costPerOrder": metrics.get("cost_per_order", 0),
                    "grossProfit": metrics.get("gross_profit", 0),
                    "grossMargin": metrics.get("gross_margin", 0),
                    "netProfit": metrics.get("net_profit", 0),
                    "netMargin": metrics.get("net_margin", 0),
                    "returnOnRevenue": metrics.get("return_on_revenue", 0),
                    "markupRatio": metrics.get("markup_ratio", 0),
                    "totalOrders": metrics.get("total_orders", 0),
                    "totalItems": metrics.get("total_items", 0),
                    "totalQuantitySold": metrics.get("total_quantity_sold", 0),
                    "uniqueSkus": metrics.get("unique_skus", 0),
                    "averageOrderValue": metrics.get("average_order_value", 0),
                    "medianOrderValue": metrics.get("median_order_value", 0),
                    "percentile75OrderValue": metrics.get("percentile_75_order_value", 0),
                    "percentile25OrderValue": metrics.get("percentile_25_order_value", 0),
                    "orderValueStd": metrics.get("order_value_std", 0),
                    "itemsPerOrder": metrics.get("items_per_order", 0),
                    "revenuePerItem": metrics.get("revenue_per_item", 0),
                    "profitPerItem": metrics.get("profit_per_item", 0),
                    "uniqueCustomers": metrics.get("unique_customers", 0),
                    "repeatCustomers": metrics.get("repeat_customers", 0),
                    "customerRetentionRate": metrics.get("customer_retention_rate", 0),
                    "revenuePerCustomer": metrics.get("revenue_per_customer", 0),
                    "ordersPerCustomer": metrics.get("orders_per_customer", 0),
                    "profitPerCustomer": metrics.get("profit_per_customer", 0),
                    "shippedOrders": metrics.get("shipped_orders", 0),
                    "shippingRate": metrics.get("shipping_rate", 0),
                    "giftOrders": metrics.get("gift_orders", 0),
                    "giftRate": metrics.get("gift_rate", 0),
                    "avgTimeBetweenOrdersHours": metrics.get("avg_time_between_orders_hours", 0),
                    "ordersPerDay": metrics.get("orders_per_day", 0),
                    "revenuePerDay": metrics.get("revenue_per_day", 0),
                    "totalRefundAmount": metrics.get("total_refund_amount", 0),
                    "totalRefundCount": metrics.get("total_refund_count", 0),
                    "ordersWithRefunds": metrics.get("orders_with_refunds", 0),
                    "refundRateByOrder": metrics.get("refund_rate_by_order", 0),
                    "refundRateByValue": metrics.get("refund_rate_by_value", 0),
                    "orderRefundRate": metrics.get("order_refund_rate", 0),
                    "cancelledOrders": metrics.get("cancelled_orders", 0),
                    "cancellationRate": metrics.get("cancellation_rate", 0),
                    "completionRate": metrics.get("completion_rate", 0),
                    "primaryPaymentMethod": metrics.get("primary_payment_method"),
                    "paymentMethodDiversity": metrics.get("payment_method_diversity", 0),
                    "customerLifetimeValue": metrics.get("customer_lifetime_value", 0),
                    "paybackPeriodDays": metrics.get("payback_period_days", 0),
                    "customerAcquisitionCost": metrics.get("customer_acquisition_cost", 0),
                    "priceElasticity": metrics.get("price_elasticity", 0),
                    "peakMonth": metrics.get("peak_month"),
                    "peakDayOfWeek": metrics.get("peak_day_of_week"),
                    "peakHour": metrics.get("peak_hour"),
                    "seasonalityIndex": metrics.get("seasonality_index", 0),
                    "totalInventory": metrics.get("total_inventory", 0),
                    "avgPrice": metrics.get("avg_price", 0),
                    "priceRange": metrics.get("price_range", 0),
                    "activeVariants": metrics.get("active_variants", 0),
                    "inventoryTurnover": metrics.get("inventory_turnover", 0),
                    "stockoutRisk": metrics.get("stockout_risk", 0),
                }
            
            # Create or update report
            await self.prisma.productreport.upsert(
                where={
                    "sku_periodType_periodStart_periodEnd": {
                        "sku": sku,
                        "periodType": period_type_enum,
                        "periodStart": period_start,
                        "periodEnd": period_end
                    }
                },
                data={
                    'create': payload,
                    'update': payload
                }
            )
            
        except Exception as e:
            logger.error(f"Error saving shop report: {e}")
            raise

    async def generate_all_insights_comprehensive_db(self, clean_old_data: bool = True):
        """Generate comprehensive insights with database storage and resume capability."""
        logger.info("Starting comprehensive insights generation with database storage...")
        
        # Check for existing checkpoint
        checkpoint = None
        if self.resume_from_checkpoint:
            checkpoint = self._load_checkpoint()
            if checkpoint:
                logger.info(f"Resuming from checkpoint: {checkpoint.get('current_stage', 'unknown')}")
        
        try:
            date_range_tuple = await self.get_date_ranges_from_database()
            if not date_range_tuple:
                logger.error("Could not get date ranges from database.")
                return None
                
            start_date, end_date = date_range_tuple
            logger.info(f"Data range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
            
            date_periods = self.generate_time_periods(start_date, end_date)
            
            # Optional: Clean old reports before generating new ones
            if clean_old_data:
                await self.clean_old_reports(keep_latest_n=10)

            try:
                # Determine which stage to start from
                current_stage = checkpoint.get("current_stage", "sku_insights") if checkpoint else "sku_insights"
                
                # Generate SKU insights
                if current_stage in ["sku_insights"]:
                    skus = await self.get_all_skus()
                    logger.info(f"\n=== GENERATING INSIGHTS FOR {len(skus)} UNIQUE SKUs ===")
                    
                    stage_checkpoint = checkpoint if current_stage == "sku_insights" else None
                    await self._generate_insights_db(
                        "sku", date_periods, skus, stage_checkpoint
                    )
                    
                    # Save checkpoint after completing SKUs
                    self._save_checkpoint({
                        "current_stage": "listing_insights",
                        "completed_stages": ["sku_insights"],
                        "timestamp": datetime.now().isoformat()
                    })
                
                # Generate listing insights
                if current_stage in ["sku_insights", "listing_insights"]:
                    listing_ids = await self.get_all_listings()
                    logger.info(f"\n=== GENERATING INSIGHTS FOR {len(listing_ids)} LISTINGS ===")
                    
                    stage_checkpoint = checkpoint if current_stage == "listing_insights" else None
                    await self._generate_insights_db(
                        "listing", date_periods, listing_ids, stage_checkpoint
                    )
                    
                    # Save checkpoint after completing listings
                    self._save_checkpoint({
                        "current_stage": "shop_insights",
                        "completed_stages": ["sku_insights", "listing_insights"],
                        "timestamp": datetime.now().isoformat()
                    })
                
                # Generate shop-wide insights
                if current_stage in ["sku_insights", "listing_insights", "shop_insights"]:
                    logger.info(f"\n=== GENERATING SHOP-WIDE INSIGHTS ===")
                    
                    stage_checkpoint = checkpoint if current_stage == "shop_insights" else None
                    await self._generate_insights_db(
                        "shop", date_periods, checkpoint=stage_checkpoint
                    )
                
                # Generate executive summary
                logger.info("\n=== GENERATING EXECUTIVE SUMMARY ===")
                executive_summary = await self.generate_executive_summary_db()
                
                # Save executive summary to a JSON file for easy access
                output_dir = "insights_output"
                os.makedirs(output_dir, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                summary_path = os.path.join(output_dir, f"executive_summary_db_{timestamp}.json")
                with open(summary_path, "w", encoding='utf-8') as f:
                    json.dump(executive_summary, f, indent=2, default=str, ensure_ascii=False)
                
                # Clear checkpoint after successful completion
                self._clear_checkpoint()
                
                logger.info("=== COMPREHENSIVE INSIGHTS GENERATION WITH DATABASE STORAGE COMPLETED ===")
                
                # Return summary of what was saved
                return {
                    "status": "completed",
                    "resumed_from_checkpoint": bool(checkpoint),
                    "data_range": {
                        "start_date": start_date.isoformat(), 
                        "end_date": end_date.isoformat()
                    },
                    "executive_summary": executive_summary,
                    "database_tables_populated": [
                        "shop_reports", "listing_reports", "product_reports"
                    ],
                    "summary_file": summary_path
                }
                
            except Exception as e:
                logger.error(f"Error in insights generation: {e}", exc_info=True)
                return None
                
        except Exception as e:
            logger.error(f"Critical error in insights generation: {e}", exc_info=True)
            # Save error checkpoint for debugging
            error_checkpoint = {
                "error": str(e),
                "error_timestamp": datetime.now().isoformat(),
                "current_stage": checkpoint.get("current_stage", "unknown") if checkpoint else "startup"
            }
            self._save_checkpoint(error_checkpoint)
            return None


async def main():
    """Main execution function with database storage and resume capability."""
    import argparse
    
    parser = argparse.ArgumentParser(description='E-commerce Analytics Engine with Database Storage')
    parser.add_argument('--no-resume', action='store_true', 
                       help='Start fresh without loading checkpoint')
    parser.add_argument('--cost-file', default='cost.csv',
                       help='Path to cost CSV file (default: cost.csv)')
    parser.add_argument('--no-cleanup', action='store_true',
                       help='Skip cleaning old report data')
    
    args = parser.parse_args()
    
    resume_enabled = not args.no_resume
    cleanup_enabled = not args.no_cleanup
    analytics = EcommerceAnalytics(args.cost_file, resume_from_checkpoint=resume_enabled)
    
    if resume_enabled and os.path.exists("analytics_checkpoint.json"):
        print("🔄 Found existing checkpoint. Resuming from previous session...")
    elif resume_enabled:
        print("🚀 Starting fresh analytics generation with checkpoint support...")
    else:
        print("🆕 Starting fresh analytics generation (checkpoints disabled)...")
    
    try:
        await analytics.connect()
        result = await analytics.generate_all_insights_comprehensive_db(clean_old_data=cleanup_enabled)
        
        if result:
            print("\n" + "="*80)
            print("      COMPREHENSIVE E-COMMERCE ANALYTICS WITH DATABASE STORAGE COMPLETE")
            print("="*80)
            print("Generated comprehensive insights directly in database tables:")
            print("• shop_reports - Business-wide metrics (yearly, monthly, weekly)")
            print("• listing_reports - Product family metrics (yearly, monthly, weekly)")  
            print("• product_reports - Individual SKU metrics (yearly, monthly, weekly)")
            print()
            print("All data is now stored in your database and can be queried with Prisma or SQL")
            print()
            print("Database Benefits:")
            print("• Fast queries with proper indexing")
            print("• Relational data integrity")
            print("• Easy integration with dashboards/BI tools")
            print("• Automatic data validation")
            print("• Concurrent access support")
            print()
            print("Key Features Maintained:")
            print("• SKU-based cost calculation with DELETED- prefix handling")
            print("• Proper P&L calculation using cost.csv SKU lookup")
            print("• Listing insights aggregate child SKU performance")
            print("• Resume capability - interrupted jobs continue where they left off")
            print("• Automatic cleanup of old report data")
            print()
            print(f"Executive summary saved to: {result.get('summary_file', 'N/A')}")
            
            if result.get("resumed_from_checkpoint"):
                print("\n✅ Successfully resumed from previous checkpoint")
                
            # Show some quick stats
            try:
                shop_count = await analytics.prisma.shopreport.count()
                listing_count = await analytics.prisma.listingreport.count()
                product_count = await analytics.prisma.productreport.count()
                
                print(f"\n📊 Database Report Counts:")
                print(f"• Shop Reports: {shop_count}")
                print(f"• Listing Reports: {listing_count}")
                print(f"• Product Reports: {product_count}")
                print(f"• Total Reports: {shop_count + listing_count + product_count}")
                
            except Exception as e:
                logger.warning(f"Could not fetch report counts: {e}")
                
        else:
            print("❌ Analytics generation failed. Check logs for details.")
        
    except KeyboardInterrupt:
        print("\n⏸️  Process interrupted by user. Progress saved to checkpoint.")
        print("Run the script again to resume from where it left off.")
    except Exception as e:
        logger.error(f"Critical error in main execution: {e}", exc_info=True)
        print(f"❌ Error: {e}")
        print("Progress has been saved. You can resume by running the script again.")
    finally:
        await analytics.disconnect()


if __name__ == "__main__":
    asyncio.run(main())