from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
import asyncio
import argparse
import json
import logging
import os
from functools import lru_cache

import numpy as np
import pandas as pd
from tqdm import tqdm
from tqdm.asyncio import tqdm as atqdm
from prisma import Prisma
from prisma.enums import PeriodType
import math

# --- Configuration ---
logging.basicConfig(
    level=logging.WARNING,  # Reduced to WARNING to show only errors
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# --- Data Structures ---
@dataclass
class DateRange:
    """Represents a start and end date for a time period."""
    start_date: datetime
    end_date: datetime


# --- Main Analytics Class (ULTRA OPTIMIZED) ---
class EcommerceAnalyticsOptimized:
    """
    ⚡ ULTRA-OPTIMIZED analytics engine - LIGHT SPEED MODE ⚡
    
    Optimizations:
    - Parallel processing with asyncio semaphores
    - Bulk database inserts (batched upserts)
    - Smart caching with LRU
    - Pre-computed aggregations
    - Connection pooling
    - Vectorized calculations with NumPy
    """

    def __init__(self, cost_csv_path: str, max_concurrent: int = 3, batch_size: int = 50,
                 etsy_transaction_fee_rate: float = 0.065,  # 6.5% Etsy transaction fee
                 etsy_processing_fee_rate: float = 0.03,     # 3% + $0.25 payment processing
                 etsy_processing_fee_fixed: float = 0.25,   # Fixed processing fee per order
                 desi_csv_path: str = "all_products_desi.csv",
                 fedex_zones_csv_path: str = "fedex_country_code_and_zone_number.csv",
                 fedex_pricing_csv_path: str = "fedex_price_per_kg_for_zones.csv",
                 us_fedex_csv_path: str = "us_fedex_desi_and_price.csv"):
        # Initialize Prisma with increased timeout for long queries
        self.prisma = Prisma(http={'timeout': 500.0})  # 120 seconds timeout for complex queries
        self.cost_data = self._load_cost_data(cost_csv_path)
        self.max_concurrent = max_concurrent  # Parallel operations limit
        self.batch_size = batch_size  # Bulk insert batch size
        
        # Load shipping-related CSVs
        self.desi_data = self._load_desi_data(desi_csv_path)
        self.fedex_zones_data = self._load_fedex_zones(fedex_zones_csv_path)
        self.fedex_pricing_data = self._load_fedex_pricing(fedex_pricing_csv_path)
        self.us_fedex_data = self._load_us_fedex_data(us_fedex_csv_path)
        
        # Create OTTOKOD to SKU mapping from cost.csv for lookups
        self.ottokod_to_sku = {}
        self.sku_to_ottokod = {}
        if not self.cost_data.empty and 'OTTOKOD' in self.cost_data.columns and 'SKU' in self.cost_data.columns:
            for _, row in self.cost_data.iterrows():
                ottokod = row.get('OTTOKOD')
                sku = row.get('SKU')
                if pd.notna(ottokod) and pd.notna(sku):
                    self.ottokod_to_sku[str(ottokod).strip()] = str(sku).strip()
                    self.sku_to_ottokod[str(sku).strip()] = str(ottokod).strip()
        
        # Etsy fee structure (configurable)
        self.etsy_transaction_fee_rate = etsy_transaction_fee_rate
        self.etsy_processing_fee_rate = etsy_processing_fee_rate
        self.etsy_processing_fee_fixed = etsy_processing_fee_fixed
        
        # Track data quality issues
        self._missing_cost_skus = set()
        self._currency_warnings_shown = set()
        self._cost_coverage_warnings_shown = set()  # Track incomplete cost coverage warnings
        self._cost_fallback_warnings_shown = set()  # Track when using fallback costs
        self._skipped_products_no_cost = set()  # Track SKUs skipped due to missing cost data
        self._skipped_count = 0  # Count of reports skipped due to missing costs
        
        # Cache for frequently accessed data
        self._cost_cache = {}
        self._sku_to_products = {}  # SKU -> list of product_ids
        self._listing_to_products = {}  # listing_id -> list of product_ids (for aggregating child products)
        self._listing_cache = {}  # listing_id -> listing data
        
        # Pre-computed data store
        self._aggregated_orders = None  # Will hold pre-aggregated order data
        self._inventory_cache = {}  # Inventory data cache

    def _load_cost_data(self, csv_path: str) -> pd.DataFrame:
        """Load and process cost data from the provided CSV file."""
        try:
            if not os.path.exists(csv_path):
                logger.warning(f"Cost CSV not found: {csv_path}")
                return pd.DataFrame()
            
            df = pd.read_csv(csv_path, encoding='utf-8-sig')
            df.columns = df.columns.str.strip()
            
            if 'SKU' not in df.columns:
                logger.error(f"SKU column not found in {csv_path}")
                return pd.DataFrame()
            
            df = df.dropna(subset=['SKU'])
            print(f"✓ Loaded cost data: {len(df)} SKUs")
            return df
        except Exception as e:
            logger.error(f"Error loading cost data: {e}")
            return pd.DataFrame()

    def _load_desi_data(self, csv_path: str) -> pd.DataFrame:
        """Load product weight (desi) data from CSV."""
        try:
            if not os.path.exists(csv_path):
                logger.warning(f"Desi CSV not found: {csv_path}")
                return pd.DataFrame()
            
            df = pd.read_csv(csv_path, sep=';', encoding='utf-8-sig')
            df.columns = df.columns.str.strip()
            
            # Normalize decimal separator (Turkish uses comma)
            if 'DESİ' in df.columns:
                df['DESİ'] = df['DESİ'].astype(str).str.replace(',', '.').astype(float)
            
            print(f"✓ Loaded desi data: {len(df)} products")
            return df
        except Exception as e:
            logger.error(f"Error loading desi data: {e}")
            return pd.DataFrame()

    def _load_fedex_zones(self, csv_path: str) -> pd.DataFrame:
        """Load country to FedEx zone mapping."""
        try:
            if not os.path.exists(csv_path):
                logger.warning(f"FedEx zones CSV not found: {csv_path}")
                return pd.DataFrame()
            
            df = pd.read_csv(csv_path, sep=';', encoding='utf-8-sig')
            df.columns = df.columns.str.strip()
            
            # Skip header row if first column is "FEDEX"
            if not df.empty and str(df.iloc[0, 0]).strip().upper() == 'FEDEX':
                df = df.iloc[1:].reset_index(drop=True)
            
            # Check if dataframe is empty after skipping header
            if df.empty:
                logger.warning("FedEx zones CSV is empty after skipping header")
                return pd.DataFrame()
            
            # Rename columns for easier access
            if len(df.columns) >= 3:
                df.columns = ['Country', 'Country_Code', 'Zone']
            
            print(f"✓ Loaded FedEx zones: {len(df)} countries")
            return df
        except Exception as e:
            logger.error(f"Error loading FedEx zones: {e}", exc_info=True)
            return pd.DataFrame()

    def _load_fedex_pricing(self, csv_path: str) -> pd.DataFrame:
        """Load FedEx pricing matrix (weight x zone)."""
        try:
            if not os.path.exists(csv_path):
                logger.warning(f"FedEx pricing CSV not found: {csv_path}")
                return pd.DataFrame()
            
            # Read CSV and check if first row is a title row (contains "FEDEX" in first column)
            df_check = pd.read_csv(csv_path, sep=';', encoding='utf-8-sig', nrows=1)
            skip_rows = 1 if 'FEDEX' in str(df_check.columns[0]).upper() else 0
            
            # Read the actual data with proper header
            df = pd.read_csv(csv_path, sep=';', encoding='utf-8-sig', skiprows=skip_rows)
            df.columns = df.columns.str.strip()
            
            # Check if dataframe is empty
            if df.empty:
                logger.warning("FedEx pricing CSV is empty")
                return pd.DataFrame()
            
            # Rename first column to English - check for various possible column names
            first_col = df.columns[0]
            if 'Ağırlık' in df.columns or 'ağırlık' in first_col.lower() or 'agirlik' in first_col.lower():
                df.rename(columns={first_col: 'Weight'}, inplace=True)
            elif first_col not in ['Weight', 'weight']:
                # If first column is not already named Weight, assume it's the weight column
                logger.warning(f"First column '{first_col}' doesn't match expected names, renaming to 'Weight'")
                df.rename(columns={first_col: 'Weight'}, inplace=True)
            
            # Normalize decimal separator and weight column
            if 'Weight' in df.columns:
                df['Weight'] = df['Weight'].astype(str).str.replace(',', '.').str.replace(' kg', '').str.strip().astype(float)
            else:
                logger.error("Weight column not found in FedEx pricing data after renaming")
                return pd.DataFrame()
            
            # Normalize all zone columns (1.Bölge through 15.Bölge)
            for col in df.columns:
                if 'Bölge' in col or 'Bolge' in col or col != 'Weight':
                    try:
                        df[col] = df[col].astype(str).str.replace(',', '.').str.strip().astype(float)
                    except:
                        pass  # Skip non-numeric columns
            
            print(f"✓ Loaded FedEx pricing matrix: {len(df)} weight tiers")
            return df
        except Exception as e:
            logger.error(f"Error loading FedEx pricing: {e}", exc_info=True)
            return pd.DataFrame()

    def _load_us_fedex_data(self, csv_path: str) -> pd.DataFrame:
        """Load US-specific FedEx data with duties and taxes."""
        try:
            if not os.path.exists(csv_path):
                logger.warning(f"US FedEx CSV not found: {csv_path}")
                return pd.DataFrame()
            
            df = pd.read_csv(csv_path, sep=';', encoding='utf-8-sig')
            df.columns = df.columns.str.strip()
            
            # Normalize numeric columns (Turkish uses comma for decimals)
            numeric_columns = ['DESİ-KG', 'INVOICE ÜRÜN BEDELİ', 'US FEDEX KARGO ÜCRETİ', 
                             'FEDEX İŞLEM ÜCRETİ', 'DUTY OTAN', 'DUTY', 'VERGİ ORANI', 'VERGİ']
            for col in numeric_columns:
                if col in df.columns:
                    # Handle range values like "4.5 & 8.5" by taking the first value or average
                    def parse_numeric(val):
                        val_str = str(val).replace(',', '.').replace('$', '').replace('%', '').strip()
                        if '&' in val_str:
                            # Handle range: take the average of the two values
                            parts = val_str.split('&')
                            try:
                                values = [float(p.strip()) for p in parts]
                                return sum(values) / len(values)
                            except:
                                return 0.0
                        try:
                            return float(val_str)
                        except:
                            return 0.0
                    
                    df[col] = df[col].apply(parse_numeric)
            
            print(f"✓ Loaded US FedEx data: {len(df)} products")
            return df
        except Exception as e:
            logger.error(f"Error loading US FedEx data: {e}")
            return pd.DataFrame()

    def _save_checkpoint(self, checkpoint_data: Dict):
        """Removed - not needed in ultra-fast mode."""
        pass
    
    def _load_checkpoint(self) -> Optional[Dict]:
        """Removed - not needed in ultra-fast mode."""
        return None
    
    def _clear_checkpoint(self):
        """Removed - not needed in ultra-fast mode."""
        pass

    def _sku_exists_in_cost_csv(self, sku: str) -> bool:
        """Check if SKU exists in cost CSV at all."""
        if not sku or self.cost_data.empty:
            return False
        lookup_sku = sku.replace("DELETED-", "") if sku.startswith("DELETED-") else sku
        return not self.cost_data[self.cost_data["SKU"] == lookup_sku].empty

    @lru_cache(maxsize=10000)
    def get_cost_for_sku_date(self, sku: str, year: int, month: int) -> float:
        """Get cost for a specific SKU at a specific date with LRU caching and fallback."""
        if not sku or self.cost_data.empty:
            return 0.0
            
        lookup_sku = sku.replace("DELETED-", "") if sku.startswith("DELETED-") else sku
        sku_row = self.cost_data[self.cost_data["SKU"] == lookup_sku]
        if sku_row.empty:
            return 0.0

        month_names = {
            1: "OCAK", 2: "SUBAT", 3: "MART", 4: "NISAN", 5: "MAYIS", 6: "HAZIRAN",
            7: "TEMMUZ", 8: "AGUSTOS", 9: "EYLUL", 10: "EKIM", 11: "KASIM", 12: "ARALIK",
        }
        month_name = month_names.get(month)
        if not month_name:
            return 0.0

        prefixes = ["US", "EU", "AU"]
        year_2digit = year % 100  # e.g., 2025 -> 25
        
        # Try exact date match first with ALL possible format variations
        # Your CSV has VERY inconsistent formats across different years!
        # Examples from your CSV:
        #   - "US MAYIS 2025" (full year with space)
        #   - "US MART 25" (2-digit year with space)
        #   - "US 2024 NISAN" (year first with space)
        #   - "US ARALIK 24" (2-digit year with space)
        for prefix in prefixes:
            possible_columns = [
                # Format 1: "US MAYIS 2025" (full 4-digit year after month)
                f"{prefix} {month_name} {year}",
                # Format 2: "US MART 25" (2-digit year after month with space)
                f"{prefix} {month_name} {year_2digit}",
                # Format 3: "US 2024 NISAN" (full year before month)
                f"{prefix} {year} {month_name}",
                # Format 4: "US 25 MART" (2-digit year before month)
                f"{prefix} {year_2digit} {month_name}",
                # Format 5: "US MART25" (2-digit year after month, no space)
                f"{prefix} {month_name}{year_2digit}",
                # Format 6: "US25 MART" (2-digit year after prefix, no space)
                f"{prefix}{year_2digit} {month_name}",
                # Format 7: Just month (no year at all)
                f"{prefix} {month_name}",
            ]
            
            # Try all columns with and without CALISMA/ÇALIŞMA suffix
            all_columns = []
            for col in possible_columns:
                all_columns.extend([col, f"{col} CALISMA", f"{col} ÇALIŞMA"])

            for col in all_columns:
                if col in sku_row.columns:
                    value = sku_row[col].values[0]
                    if pd.notna(value):
                        try:
                            return float(value)
                        except (ValueError, TypeError):
                            continue
        
        # FALLBACK: If exact date not found, try to find the most recent cost
        # This is especially useful for new years (e.g., 2025) where costs haven't been updated yet
        # We'll use the latest available cost from previous periods
        all_cost_columns = []
        for prefix in prefixes:
            # Look for any cost columns for this prefix
            for col in sku_row.columns:
                if col.startswith(prefix) and any(mn in col for mn in month_names.values()):
                    all_cost_columns.append(col)
        
        # Try to extract dates from column names and sort by most recent
        dated_costs = []
        for col in all_cost_columns:
            value = sku_row[col].values[0]
            if pd.notna(value):
                try:
                    cost = float(value)
                    if cost > 0:
                        # Try to extract year from column name
                        import re
                        year_match = re.search(r'\b(20\d{2}|2\d)\b', col)
                        if year_match:
                            col_year = int(year_match.group(1))
                            if col_year < 100:  # 2-digit year
                                col_year += 2000
                            dated_costs.append((col_year, cost, col))
                except (ValueError, TypeError):
                    continue
        
        # Use the most recent cost if available
        if dated_costs:
            dated_costs.sort(reverse=True)  # Sort by year, most recent first
            most_recent_cost = dated_costs[0][1]
            most_recent_col = dated_costs[0][2]
            
            # Only log fallback usage periodically to avoid spam
            fallback_key = f"{sku}_{year}_{month}"
            if fallback_key not in self._cost_fallback_warnings_shown:
                self._cost_fallback_warnings_shown.add(fallback_key)
                if len(self._cost_fallback_warnings_shown) % 50 == 1:  # Log every 50th fallback
                    logger.info(
                        f"📊 Using fallback cost for SKU {sku} ({year}/{month:02d}): "
                        f"${most_recent_cost:.2f} from column '{most_recent_col}'"
                    )
            
            return most_recent_cost

        # Track missing cost data for warnings
        if sku not in self._missing_cost_skus:
            self._missing_cost_skus.add(sku)
            # Only log first few to avoid spam
            if len(self._missing_cost_skus) <= 10:
                logger.warning(f"⚠️ No cost data found for SKU: {sku} (year: {year}, month: {month})")
        
        return 0.0

    @lru_cache(maxsize=5000)
    def get_desi_for_sku(self, sku: str) -> float:
        """Get product weight (desi) for SKU via OTTOKOD mapping."""
        if self.desi_data.empty or not sku:
            return 0.5  # Default to 0.5 kg if not found
        
        # Convert SKU to OTTOKOD
        ottokod = self.sku_to_ottokod.get(sku)
        if not ottokod:
            return 0.5  # Default weight
        
        # Look up desi by OTTOKOD
        desi_row = self.desi_data[self.desi_data['OTTOKOD'] == ottokod]
        if desi_row.empty:
            return 0.5  # Default weight
        
        try:
            return float(desi_row.iloc[0]['DESİ'])
        except:
            return 0.5

    @lru_cache(maxsize=200)
    def get_zone_for_country(self, country_code: str) -> int:
        """Get FedEx zone number for a country code."""
        if self.fedex_zones_data.empty or not country_code:
            return 8  # Default to Zone 8 (US) if not found
        
        # Match by country code using renamed column
        zone_row = self.fedex_zones_data[
            self.fedex_zones_data['Country_Code'].str.upper() == country_code.upper()
        ]
        
        if zone_row.empty:
            return 8  # Default to Zone 8
        
        try:
            return int(zone_row.iloc[0]['Zone'])
        except:
            return 8

    @lru_cache(maxsize=1000)
    def get_fedex_price(self, weight_kg: float, zone: int) -> float:
        """Get FedEx shipping price for weight and zone from pricing matrix."""
        if self.fedex_pricing_data.empty:
            return 0.0
        
        # Check if Weight column exists
        if 'Weight' not in self.fedex_pricing_data.columns:
            logger.warning("Weight column not found in FedEx pricing data")
            return 0.0
        
        # Round weight up to nearest tier
        weight_tiers = sorted(self.fedex_pricing_data['Weight'].unique())
        actual_tier = weight_kg
        for tier in weight_tiers:
            if weight_kg <= tier:
                actual_tier = tier
                break
        else:
            actual_tier = weight_tiers[-1]  # Use max tier if over
        
        # Get price for this weight tier
        price_row = self.fedex_pricing_data[
            self.fedex_pricing_data['Weight'] == actual_tier
        ]
        
        if price_row.empty:
            return 0.0
        
        # Column name for zone (e.g., "1.Bölge" for zone 1)
        zone_col = f"{zone}.Bölge"
        
        if zone_col not in price_row.columns:
            return 0.0
        
        try:
            return float(price_row.iloc[0][zone_col])
        except:
            return 0.0

    @lru_cache(maxsize=5000)
    def get_us_shipping_costs(self, sku: str) -> Dict[str, float]:
        """
        Get US-specific shipping costs including duties and taxes.
        Returns dict with: fedex_charge, processing_fee, duty_rate, duty_amount, tax_rate, tax_amount
        """
        if self.us_fedex_data.empty or not sku:
            return {
                'fedex_charge': 0.0,
                'processing_fee': 0.0,
                'duty_rate': 0.0,
                'duty_amount': 0.0,
                'tax_rate': 0.0,
                'tax_amount': 0.0
            }
        
        # Look up by SKU directly first
        us_row = self.us_fedex_data[self.us_fedex_data['SKU'] == sku]
        
        # If not found, try via OTTOKOD
        if us_row.empty:
            ottokod = self.sku_to_ottokod.get(sku)
            if ottokod:
                us_row = self.us_fedex_data[self.us_fedex_data['OTTOKOD'] == ottokod]
        
        if us_row.empty:
            return {
                'fedex_charge': 0.0,
                'processing_fee': 0.0,
                'duty_rate': 0.0,
                'duty_amount': 0.0,
                'tax_rate': 0.0,
                'tax_amount': 0.0
            }
        
        try:
            row = us_row.iloc[0]
            return {
                'fedex_charge': float(row.get('US FEDEX KARGO ÜCRETİ', 0) or 0),
                'processing_fee': float(row.get('FEDEX İŞLEM ÜCRETİ', 0) or 0),
                'duty_rate': float(row.get('DUTY OTAN', 0) or 0) / 100,  # Convert % to decimal
                'duty_amount': float(row.get('DUTY', 0) or 0),
                'tax_rate': float(row.get('VERGİ ORANI', 0) or 0) / 100,  # Convert % to decimal
                'tax_amount': float(row.get('VERGİ', 0) or 0)
            }
        except Exception as e:
            logger.error(f"Error parsing US shipping costs for SKU {sku}: {e}")
            return {
                'fedex_charge': 0.0,
                'processing_fee': 0.0,
                'duty_rate': 0.0,
                'duty_amount': 0.0,
                'tax_rate': 0.0,
                'tax_amount': 0.0
            }

    def calculate_duty_and_tax(self, invoice_price: float, duty_rate: float, tax_rate: float) -> Dict[str, float]:
        """
        Calculate duty and tax amounts based on invoice price and rates.
        
        Args:
            invoice_price: Product invoice price in USD
            duty_rate: Duty rate as decimal (e.g., 0.176 for 17.6%)
            tax_rate: Tax rate as decimal (e.g., 0.15 for 15%)
        
        Returns:
            dict with duty_amount and tax_amount
        """
        duty_amount = invoice_price * duty_rate
        tax_amount = invoice_price * tax_rate
        
        return {
            'duty_amount': duty_amount,
            'tax_amount': tax_amount
        }

    async def connect(self):
        """Connect to the Prisma database with optimized connection pool settings."""
        try:
            # Connect with connection pool limits to prevent exhausting database connections
            await self.prisma.connect()
            print("✓ Database connection established")
            # Pre-load all essential data
            await self._preload_all_data()
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    async def disconnect(self):
        """Disconnect from the Prisma database and clean up resources."""
        try:
            if self.prisma.is_connected():
                await self.prisma.disconnect()
                print("✓ Database connection closed")
        except Exception as e:
            logger.error(f"Error disconnecting from database: {e}")
    
    async def __aenter__(self):
        """Context manager entry - connect to database."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure disconnect happens."""
        await self.disconnect()
        return False

    async def clean_all_reports(self):
        """
        Delete ALL report data from database (Shop, Listing, Product reports).
        ⚠️ WARNING: This will erase all analytics but preserve orders, products, listings, etc.
        """
        print("\n" + "="*80)
        print("🗑️  CLEANING ALL REPORT DATA FROM DATABASE")
        print("="*80)
        print("⚠️  This will delete:")
        print("   - All Shop Reports (ShopReport table)")
        print("   - All Listing Reports (ListingReport table)")
        print("   - All Product Reports (ProductReport table)")
        print("\n✅ This will NOT affect:")
        print("   - Orders")
        print("   - Listings")
        print("   - Products")
        print("   - Visits")
        print("   - Any other data")
        print("="*80)
        
        try:
            # Count existing reports
            shop_count = await self.prisma.shopreport.count()
            listing_count = await self.prisma.listingreport.count()
            product_count = await self.prisma.productreport.count()
            
            print(f"\n📊 Current report counts:")
            print(f"   Shop Reports: {shop_count:,}")
            print(f"   Listing Reports: {listing_count:,}")
            print(f"   Product Reports: {product_count:,}")
            print(f"   TOTAL: {shop_count + listing_count + product_count:,} reports")
            
            if shop_count == 0 and listing_count == 0 and product_count == 0:
                print("\n✅ No reports found. Database is already clean.")
                return
            
            print("\n🗑️  Deleting all reports...")
            
            # Delete all reports in parallel
            results = await asyncio.gather(
                self.prisma.shopreport.delete_many(),
                self.prisma.listingreport.delete_many(),
                self.prisma.productreport.delete_many(),
                return_exceptions=True
            )
            
            # Check for errors
            errors = [r for r in results if isinstance(r, Exception)]
            if errors:
                logger.error(f"Errors during deletion: {errors}")
                print(f"\n⚠️  Some errors occurred during deletion")
            else:
                print(f"\n✅ Successfully deleted all report data!")
                print(f"   ✓ Deleted {shop_count:,} shop reports")
                print(f"   ✓ Deleted {listing_count:,} listing reports")
                print(f"   ✓ Deleted {product_count:,} product reports")
            
            print("="*80)
            
        except Exception as e:
            logger.error(f"Error cleaning reports: {e}")
            print(f"\n❌ Error: {e}")
            raise

    async def _preload_all_data(self):
        """Pre-load all essential data in parallel for maximum performance."""
        print("\n⚡ Pre-loading data...")
        
        # Run all pre-loading tasks in parallel
        await asyncio.gather(
            self._preload_sku_mappings(),
            self._preload_inventory_data(),
            return_exceptions=True
        )
        
        print("✅ Pre-loading complete!\n")

    async def _preload_sku_mappings(self):
        """Pre-load SKU to product_id mappings and listing to product_id mappings for faster lookups."""
        try:
            # Use raw query instead of ORM with select (not supported in Prisma Python)
            result = await self.prisma.query_raw(
                """
                SELECT sku, product_id, listing_id
                FROM listing_products
                WHERE is_deleted = false AND sku IS NOT NULL
                """
            )
            
            for row in result:
                sku = row['sku']
                product_id = row['product_id']
                listing_id = row['listing_id']
                
                # SKU to product_id mapping
                normalized_sku = sku.replace("DELETED-", "") if sku.startswith("DELETED-") else sku
                if normalized_sku not in self._sku_to_products:
                    self._sku_to_products[normalized_sku] = []
                self._sku_to_products[normalized_sku].append(product_id)
                
                # Listing to product_ids mapping (for aggregating child products)
                if listing_id not in self._listing_to_products:
                    self._listing_to_products[listing_id] = []
                self._listing_to_products[listing_id].append(product_id)
            
            print(f"  ✓ Loaded {len(self._sku_to_products)} SKU mappings")
        except Exception as e:
            logger.error(f"Error pre-loading SKU mappings: {e}")

    async def _preload_inventory_data(self):
        """Pre-load all inventory data for instant access."""
        try:
            # Get inventory by SKU
            result = await self.prisma.query_raw(
                """
                SELECT 
                    lp.sku,
                    SUM(po.quantity) as total_inventory,
                    AVG(po.price) as avg_price,
                    MAX(po.price) - MIN(po.price) as price_range,
                    COUNT(DISTINCT po.id) as active_variants
                FROM product_offerings po
                INNER JOIN listing_products lp ON po.listing_product_id = lp.id
                WHERE po.is_enabled = true 
                AND po.is_deleted = false
                AND lp.sku IS NOT NULL
                GROUP BY lp.sku
                """
            )
            
            for row in result:
                sku = row['sku']
                normalized_sku = sku.replace("DELETED-", "") if sku.startswith("DELETED-") else sku
                self._inventory_cache[f"sku_{normalized_sku}"] = {
                    "total_inventory": int(row['total_inventory'] or 0),
                    "avg_price": round(float(row['avg_price'] or 0), 2),
                    "price_range": round(float(row['price_range'] or 0), 2),
                    "active_variants": int(row['active_variants'] or 0)
                }
            
            # Get inventory by listing
            result = await self.prisma.query_raw(
                """
                SELECT 
                    lp.listing_id,
                    SUM(po.quantity) as total_inventory,
                    AVG(po.price) as avg_price,
                    MAX(po.price) - MIN(po.price) as price_range,
                    COUNT(DISTINCT po.id) as active_variants
                FROM product_offerings po
                INNER JOIN listing_products lp ON po.listing_product_id = lp.id
                WHERE po.is_enabled = true 
                AND po.is_deleted = false
                GROUP BY lp.listing_id
                """
            )
            
            for row in result:
                listing_id = row['listing_id']
                self._inventory_cache[f"listing_{listing_id}"] = {
                    "total_inventory": int(row['total_inventory'] or 0),
                    "avg_price": round(float(row['avg_price'] or 0), 2),
                    "price_range": round(float(row['price_range'] or 0), 2),
                    "active_variants": int(row['active_variants'] or 0)
                }
            
            print(f"  ✓ Loaded inventory cache")
        except Exception as e:
            logger.error(f"Error pre-loading inventory: {e}")

    async def get_date_ranges_from_database(self) -> Optional[Tuple[datetime, datetime]]:
        """Get the earliest and latest order dates using Prisma ORM (same as reportsv3)."""
        try:
            # Use Prisma ORM methods instead of raw SQL (same as reportsv3)
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
                next_month = current.month % 12 + 1
                next_year = current.year + (1 if next_month == 1 else 0)
                month_end = datetime(next_year, next_month, 1) - timedelta(seconds=1)
                month_start = max(current, start_date)
                month_end = min(month_end, end_date)
                periods["monthly"].append(DateRange(month_start, month_end))
                current = datetime(next_year, next_month, 1)
            except Exception as e:
                logger.error(f"Error generating monthly period: {e}")
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

    async def get_all_skus(self) -> List[str]:
        """Get all unique SKUs from listing_products table (same as reportsv3)."""
        # Ensure SKU mappings are loaded
        if not self._sku_to_products:
            await self._preload_sku_mappings()
        
        if self._sku_to_products:
            return list(self._sku_to_products.keys())
        
        try:
            # Use Prisma ORM instead of raw SQL (same as reportsv3)
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
            
            logger.info(f"Found {len(skus)} unique SKUs")
            return list(skus)
        except Exception as e:
            logger.error(f"Error getting SKUs: {e}")
            return []

    async def get_all_listings(self) -> List[int]:
        """Get all unique listing IDs that have transactions (using optimized raw SQL)."""
        try:
            # Use raw SQL for better performance with distinct
            result = await self.prisma.query_raw(
                """
                SELECT DISTINCT listing_id
                FROM order_transactions
                WHERE listing_id IS NOT NULL
                ORDER BY listing_id
                """
            )
            return [row['listing_id'] for row in result if row.get('listing_id')]
        except Exception as e:
            logger.error(f"Error getting listings: {e}", exc_info=True)
            return []

    async def calculate_metrics_batch(
        self, 
        date_ranges: List[DateRange],
        listing_id: Optional[int] = None,
        sku: Optional[str] = None
    ) -> Dict[str, Dict]:
        """
        ⚡ ULTRA-OPTIMIZED: Calculate metrics for multiple periods in ONE database query.
        Uses vectorized NumPy operations for maximum performance.
        """
        try:
            if not date_ranges:
                return {}
            
            # Build time range filter
            time_conditions = []
            for dr in date_ranges:
                start_ts = int(dr.start_date.timestamp())
                end_ts = int(dr.end_date.timestamp())
                time_conditions.append(f"(o.created_timestamp BETWEEN {start_ts} AND {end_ts})")
            
            time_filter = " OR ".join(time_conditions)
            
            # Build entity filter
            entity_filter = ""
            if sku:
                # For SKU: get all product_ids for this SKU
                product_ids = self._sku_to_products.get(sku, [])
                if not product_ids:
                    return {}
                product_ids_str = ','.join(str(pid) for pid in product_ids)
                entity_filter = f"AND ot.product_id IN ({product_ids_str})"
            elif listing_id:
                # For listing: get all product_ids that belong to this listing (child products)
                product_ids = self._listing_to_products.get(listing_id, [])
                if not product_ids:
                    # Fallback: if no products found, try filtering by listing_id directly
                    entity_filter = f"AND ot.listing_id = {listing_id}"
                else:
                    # Filter by all product_ids that belong to this listing
                    product_ids_str = ','.join(str(pid) for pid in product_ids)
                    entity_filter = f"AND ot.product_id IN ({product_ids_str})"
            
            # ONE MEGA-QUERY with optimized joins and aggregations
            query = f"""
                WITH order_data AS (
                    SELECT 
                        o.order_id,
                        o.created_timestamp,
                        o.grand_total,
                        o.grand_total_currency_code,
                        o.total_shipping_cost,
                        o.total_tax_cost,
                        o.total_vat_cost,
                        o.discount_amt,
                        o.gift_wrap_price,
                        o.item_count,
                        o.buyer_user_id,
                        o.is_shipped,
                        o.is_gift,
                        o.status,
                        o.payment_method,
                        o.country
                    FROM orders o
                    WHERE ({time_filter})
                    {f"AND EXISTS (SELECT 1 FROM order_transactions ot WHERE ot.order_id = o.order_id {entity_filter})" if entity_filter else ""}
                ),
                transaction_data AS (
                    SELECT 
                        ot.order_id,
                        ot.sku,
                        ot.quantity,
                        ot.price
                    FROM order_transactions ot
                    INNER JOIN order_data od ON ot.order_id = od.order_id
                    {f"WHERE {entity_filter[4:]}" if entity_filter else ""}
                ),
                refund_data AS (
                    SELECT 
                        r.order_id,
                        SUM(r.amount) as refund_amount,
                        COUNT(*) as refund_count
                    FROM order_refunds r
                    INNER JOIN order_data od ON r.order_id = od.order_id
                    GROUP BY r.order_id
                )
                SELECT 
                    od.*,
                    COALESCE(rd.refund_amount, 0) as refund_amount,
                    COALESCE(rd.refund_count, 0) as refund_count,
                    json_agg(
                        json_build_object(
                            'sku', td.sku,
                            'quantity', td.quantity,
                            'price', td.price
                        )
                    ) as transactions
                FROM order_data od
                LEFT JOIN refund_data rd ON od.order_id = rd.order_id
                LEFT JOIN transaction_data td ON od.order_id = td.order_id
                GROUP BY od.order_id, od.created_timestamp, od.grand_total, od.grand_total_currency_code,
                         od.total_shipping_cost, od.total_tax_cost, od.total_vat_cost, od.discount_amt,
                         od.gift_wrap_price, od.item_count, od.buyer_user_id, od.is_shipped, od.is_gift,
                         od.status, od.payment_method, od.country, rd.refund_amount, rd.refund_count
            """
            
            # Execute the mega-query
            try:
                raw_results = await self.prisma.query_raw(query)
            except Exception as query_error:
                logger.error(f"SQL Query failed: {query_error}")
                logger.error(f"Query was: {query[:500]}...")  # Log first 500 chars of query
                raise  # Re-raise to be caught by outer exception handler
            
            if not raw_results:
                # Return empty metrics for all periods
                empty_results = {}
                for dr in date_ranges:
                    period_key = f"{dr.start_date.strftime('%Y-%m-%d')}_to_{dr.end_date.strftime('%Y-%m-%d')}"
                    empty_results[period_key] = await self._empty_metrics(sku=sku, listing_id=listing_id, date_range=dr)
                return empty_results
            
            # Group results by period using vectorized operations
            period_results = {}
            period_keys = {}
            
            # Create period key mapping
            for dr in date_ranges:
                period_key = f"{dr.start_date.strftime('%Y-%m-%d')}_to_{dr.end_date.strftime('%Y-%m-%d')}"
                period_results[period_key] = []
                period_keys[period_key] = dr
            
            # Convert to numpy for fast filtering
            timestamps = np.array([row['created_timestamp'] for row in raw_results])
            
            for period_key, dr in period_keys.items():
                start_ts = int(dr.start_date.timestamp())
                end_ts = int(dr.end_date.timestamp())
                mask = (timestamps >= start_ts) & (timestamps <= end_ts)
                indices = np.where(mask)[0]
                period_results[period_key] = [raw_results[i] for i in indices]
            
            # Calculate metrics for each period in parallel
            tasks = []
            ordered_keys = []
            for period_key, rows in period_results.items():
                dr = period_keys[period_key]
                tasks.append(self._calculate_metrics_from_rows(rows, dr, sku, listing_id))
                ordered_keys.append(period_key)
            
            results = await asyncio.gather(*tasks)
            
            all_metrics = {}
            for period_key, metrics in zip(ordered_keys, results):
                all_metrics[period_key] = metrics
            
            return all_metrics
            
        except Exception as e:
            logger.error(f"Error in batch calculation: {e}", exc_info=True)
            # Return empty metrics for all periods on error
            empty_results = {}
            for dr in date_ranges:
                period_key = f"{dr.start_date.strftime('%Y-%m-%d')}_to_{dr.end_date.strftime('%Y-%m-%d')}"
                empty_results[period_key] = await self._empty_metrics(sku=sku, listing_id=listing_id, date_range=dr)
            return empty_results

    async def _calculate_metrics_from_rows(
        self, 
        rows: List[Dict], 
        date_range: DateRange,
        sku: Optional[str] = None,
        listing_id: Optional[int] = None
    ) -> Dict:
        """⚡ Calculate metrics from pre-fetched raw data rows using vectorized operations."""
        if not rows:
            return await self._empty_metrics(sku=sku, listing_id=listing_id, date_range=date_range)
        
        # Extract order-level data using list comprehensions (fast)
        orders_dict = {}
        for row in rows:
            order_id = row['order_id']
            if order_id not in orders_dict:
                # Parse transactions JSON
                transactions = row.get('transactions', [])
                if isinstance(transactions, str):
                    transactions = json.loads(transactions)
                
                orders_dict[order_id] = {
                    'grand_total': float(row.get('grand_total') or 0),
                    'shipping': float(row.get('total_shipping_cost') or 0),
                    'tax': float(row.get('total_tax_cost') or 0),
                    'vat': float(row.get('total_vat_cost') or 0),
                    'discount': float(row.get('discount_amt') or 0),
                    'gift_wrap': float(row.get('gift_wrap_price') or 0),
                    'item_count': int(row.get('item_count') or 0),
                    'buyer_id': row.get('buyer_user_id'),
                    'is_shipped': row.get('is_shipped', False),
                    'is_gift': row.get('is_gift', False),
                    'status': row.get('status'),
                    'payment_method': row.get('payment_method'),
                    'refund_amount': float(row.get('refund_amount') or 0),
                    'refund_count': int(row.get('refund_count') or 0),
                    'created_timestamp': row['created_timestamp'],
                    'country': row.get('country'),
                    'transactions': [t for t in transactions if t]
                }
        
        orders = list(orders_dict.values())
        
        # Vectorized filtering
        cancelled_statuses = {'cancelled', 'canceled'}
        completed_orders = [o for o in orders if o['status'] not in cancelled_statuses]
        
        if not completed_orders:
            return await self._empty_metrics(sku=sku, listing_id=listing_id, date_range=date_range)
        
        # ===== CURRENCY VALIDATION (CRITICAL FOR ACCURACY) =====
        # Check if all orders are in the same currency
        currencies_in_orders = set()
        for row in rows:
            currency = row.get('grand_total_currency_code') or 'USD'
            currencies_in_orders.add(currency)
        
        if len(currencies_in_orders) > 1:
            period_key = f"{date_range.start_date}_{date_range.end_date}"
            if period_key not in self._currency_warnings_shown:
                self._currency_warnings_shown.add(period_key)
                logger.error(f"⚠️⚠️⚠️ CRITICAL: Multiple currencies detected: {currencies_in_orders}")
                logger.error(f"⚠️⚠️⚠️ Financial calculations will be INACCURATE without currency conversion!")
                logger.error(f"⚠️⚠️⚠️ Period: {date_range.start_date} to {date_range.end_date}")
        
        # Use NumPy for fast aggregations
        grand_totals = np.array([o['grand_total'] for o in completed_orders])
        shipping_costs = np.array([o['shipping'] for o in completed_orders])
        tax_costs = np.array([o['tax'] for o in completed_orders])
        vat_costs = np.array([o['vat'] for o in completed_orders])
        discounts = np.array([o['discount'] for o in completed_orders])
        gift_wraps = np.array([o['gift_wrap'] for o in completed_orders])
        item_counts = np.array([o['item_count'] for o in completed_orders])
        
        # ===== CORRECTED ETSY FINANCIAL CALCULATIONS =====
        
        # 1. GROSS REVENUE (what buyers paid)
        gross_revenue = float(np.sum(grand_totals))
        
        # 2. REVENUE COMPONENTS (already included in grand_total)
        total_shipping_charged = float(np.sum(shipping_costs))
        total_tax_collected = float(np.sum(tax_costs))
        total_vat_collected = float(np.sum(vat_costs))
        total_discounts_given = float(np.sum(discounts))
        total_gift_wrap_revenue = float(np.sum(gift_wraps))
        
        # 3. CALCULATE ETSY FEES (these are NOT in the database, so we estimate)
        # Note: grand_total = subtotal + shipping + tax + vat + gift_wrap - discounts
        # Etsy fees are calculated on: subtotal + shipping (NOT on tax/vat)
        taxable_amount = gross_revenue - total_tax_collected - total_vat_collected
        
        # Etsy Transaction Fee: 6.5% on item price + shipping
        etsy_transaction_fees = taxable_amount * self.etsy_transaction_fee_rate
        
        # Etsy Payment Processing Fee: 3% + $0.25 per order
        etsy_processing_fees = (taxable_amount * self.etsy_processing_fee_rate) + \
                               (len(completed_orders) * self.etsy_processing_fee_fixed)
        
        # Total Etsy fees
        total_etsy_fees = etsy_transaction_fees + etsy_processing_fees
        
        # 4. NET REVENUE (what you actually receive after Etsy takes their cut)
        # Remove: Etsy fees + taxes (taxes go to government, not you)
        net_revenue_from_sales = gross_revenue - total_etsy_fees - total_tax_collected - total_vat_collected
        
        # 5. PRODUCT REVENUE (item sales only, excluding shipping/tax/fees)
        # Product revenue = net_revenue - shipping charged
        product_revenue = net_revenue_from_sales - total_shipping_charged - total_gift_wrap_revenue
        
        # Cost calculation with tracking of which items have valid cost data
        total_cost = 0.0
        total_quantity_sold = 0
        total_quantity_with_cost = 0  # Track items that have known costs
        unique_skus = set()
        
        # Pre-compute costs for all year-month combinations in this period
        year_month_set = {(date_range.start_date.year, date_range.start_date.month)}
        if date_range.end_date.year != date_range.start_date.year or date_range.end_date.month != date_range.start_date.month:
            current = date_range.start_date
            while current <= date_range.end_date:
                year_month_set.add((current.year, current.month))
                if current.month == 12:
                    current = datetime(current.year + 1, 1, 1)
                else:
                    current = datetime(current.year, current.month + 1, 1)
        
        for order in completed_orders:
            order_date = datetime.fromtimestamp(order['created_timestamp'])
            year, month = order_date.year, order_date.month
            
            for txn in order['transactions']:
                if not txn or not txn.get('sku'):
                    continue
                    
                sku_val = txn['sku']
                quantity = int(txn.get('quantity', 0))
                
                # Use LRU cached cost lookup
                cost = self.get_cost_for_sku_date(sku_val, year, month)
                if cost > 0:  # Only count items with valid cost data
                    total_cost += cost * quantity
                    total_quantity_with_cost += quantity
                
                total_quantity_sold += quantity
                
                normalized_sku = sku_val.replace("DELETED-", "") if sku_val.startswith("DELETED-") else sku_val
                unique_skus.add(normalized_sku)
        
        # Calculate average cost only for items with known costs
        avg_cost_per_item = total_cost / total_quantity_with_cost if total_quantity_with_cost > 0 else 0
        
        # ===== NEW: SHIPPING COST CALCULATIONS (FedEx + Duties/Taxes) =====
        # CRITICAL FINANCIAL CALCULATION - DO NOT MODIFY WITHOUT CAREFUL REVIEW
        # 
        # This section calculates the ACTUAL costs we pay for shipping, duties, and taxes.
        # These are EXPENSES that reduce our profit, separate from what customers pay us.
        #
        # Revenue side (already calculated above):
        #   - total_shipping_charged = what customers paid us for shipping (included in gross_revenue)
        #
        # Cost side (calculated here):
        #   - total_actual_shipping_cost = what we actually pay FedEx
        #   - total_us_import_duty = US customs duties we pay (COST to us)
        #   - total_us_import_tax = US import taxes we pay (COST to us)
        #   - total_fedex_processing_fee = FedEx processing fees
        #
        # NOTE: These are DIFFERENT from:
        #   - total_tax_collected = sales tax collected FROM customers (part of gross_revenue)
        #   - total_vat_collected = VAT collected FROM customers (part of gross_revenue)
        #
        # Shipping profit/loss = total_shipping_charged - total_actual_shipping_cost
        # (Positive = we made money on shipping, Negative = we lost money on shipping)
        
        total_actual_shipping_cost = 0.0
        total_us_import_duty = 0.0  # US customs duties (COST to us)
        total_us_import_tax = 0.0   # US import taxes (COST to us)
        total_fedex_processing_fee = 0.0
        
        for order in completed_orders:
            order_country = order.get('country', 'US')
            
            # Calculate actual FedEx shipping costs for this order
            # IMPORTANT: We process each transaction (line item) separately because:
            # 1. Each SKU may have different weight (desi)
            # 2. Each SKU may have different duty/tax rates
            # 3. Total shipping cost = sum of all items' shipping costs
            for txn in order['transactions']:
                if not txn or not txn.get('sku'):
                    continue
                
                sku_val = txn['sku']
                quantity = int(txn.get('quantity', 0))
                item_price = float(txn.get('price', 0))  # Price per unit in this order
                
                # Get product weight (desi) - this is weight per unit
                weight_per_item = self.get_desi_for_sku(sku_val)
                total_weight = weight_per_item * quantity  # Total weight for all units of this SKU
                
                # Check if this is a US order
                if order_country and order_country.upper() in ['US', 'USA', 'UNITED STATES']:
                    # US orders: Use special US pricing with duties/taxes
                    us_costs = self.get_us_shipping_costs(sku_val)
                    
                    # FedEx charges are per-item in the CSV, multiply by quantity
                    total_actual_shipping_cost += us_costs['fedex_charge'] * quantity
                    total_fedex_processing_fee += us_costs['processing_fee'] * quantity
                    
                    # Duty and tax calculations
                    # IMPORTANT: The CSV may contain either:
                    # 1. Pre-calculated amounts (already per unit) - just multiply by quantity
                    # 2. Rates (as decimals) - calculate from item_price
                    
                    # Calculate based on the actual item price in this order
                    # This is more accurate because prices can vary between orders
                    invoice_price_per_item = item_price
                    
                    # Use rates to calculate (more accurate for variable pricing)
                    if us_costs['duty_rate'] > 0:
                        duty_per_item = invoice_price_per_item * us_costs['duty_rate']
                        total_us_import_duty += duty_per_item * quantity
                    elif us_costs['duty_amount'] > 0:
                        # Fallback: use pre-calculated amount if rate is not available
                        total_us_import_duty += us_costs['duty_amount'] * quantity
                    
                    if us_costs['tax_rate'] > 0:
                        tax_per_item = invoice_price_per_item * us_costs['tax_rate']
                        total_us_import_tax += tax_per_item * quantity
                    elif us_costs['tax_amount'] > 0:
                        # Fallback: use pre-calculated amount if rate is not available
                        total_us_import_tax += us_costs['tax_amount'] * quantity
                else:
                    # International orders: Use zone-based FedEx pricing
                    # Get the FedEx zone for this country
                    zone = self.get_zone_for_country(order_country or 'US')
                    # Get price for total weight of all items
                    fedex_price = self.get_fedex_price(total_weight, zone)
                    total_actual_shipping_cost += fedex_price
        
        # Calculate shipping profit/loss
        # This shows if we make or lose money on shipping
        shipping_profit = total_shipping_charged - total_actual_shipping_cost
        
        # ===== CORRECTED PROFIT CALCULATIONS (INCLUDING SHIPPING COSTS) =====
        # CRITICAL FINANCIAL FLOW - This is the TRUE profit calculation
        #
        # Total Costs = COGS + All Shipping-Related Expenses
        # We must include ALL costs we pay out:
        #   1. total_cost (COGS from cost.csv)
        #   2. total_actual_shipping_cost (FedEx charges we pay)
        #   3. total_us_import_duty (customs duties we pay to US gov)
        #   4. total_us_import_tax (import taxes we pay to US gov)
        #   5. total_fedex_processing_fee (FedEx processing fees)
        #
        # Gross Profit = Net Revenue - Total Costs
        #   where Net Revenue = Gross Revenue - Etsy Fees - Taxes Collected (from customers)
        #
        # Net Profit = Gross Profit - Refunds - Etsy Fees on Refunds
        
        # Add shipping costs, duties, and taxes to total costs
        total_cost_with_shipping = total_cost + total_actual_shipping_cost + total_us_import_duty + total_us_import_tax + total_fedex_processing_fee
        
        # GROSS PROFIT = Net Revenue - All Costs (COGS + Shipping + Duties + Taxes)
        # (This is profit before refunds)
        gross_profit = net_revenue_from_sales - total_cost_with_shipping
        
        # For more detailed breakdown, we can also calculate contribution margin
        # (profit from product sales only, before shipping costs)
        contribution_margin = product_revenue - total_cost
        
        # Order metrics (vectorized)
        total_orders = len(completed_orders)
        total_items = int(np.sum(item_counts))
        
        # Customer metrics
        customer_ids = [o['buyer_id'] for o in completed_orders if o['buyer_id']]
        unique_customers = len(set(customer_ids))
        repeat_customers = len(customer_ids) - unique_customers
        
        # Payment methods
        payment_methods = [o['payment_method'] for o in completed_orders if o['payment_method']]
        payment_method_counts = defaultdict(int)
        for pm in payment_methods:
            payment_method_counts[pm] += 1
        
        # Operational metrics (vectorized)
        shipped_count = sum(1 for o in completed_orders if o['is_shipped'])
        shipping_rate = shipped_count / total_orders if total_orders > 0 else 0
        
        gift_order_count = sum(1 for o in completed_orders if o['is_gift'])
        gift_rate = gift_order_count / total_orders if total_orders > 0 else 0
        
        # Revenue distribution (NumPy percentiles - super fast!)
        median_order_value = float(np.median(grand_totals))
        percentile_75_order_value = float(np.percentile(grand_totals, 75))
        percentile_25_order_value = float(np.percentile(grand_totals, 25))
        order_value_std = float(np.std(grand_totals))
        
        # Time analysis
        avg_time_between_orders = 0
        if len(completed_orders) > 1:
            timestamps = np.array(sorted([o['created_timestamp'] for o in completed_orders]))
            time_diffs = np.diff(timestamps)
            avg_time_between_orders = float(np.mean(time_diffs)) / 3600
        
        # Refund metrics (vectorized)
        refund_amounts = np.array([o['refund_amount'] for o in completed_orders])
        refund_counts = np.array([o['refund_count'] for o in completed_orders])
        
        total_refund_amount = float(np.sum(refund_amounts))
        total_refund_count = int(np.sum(refund_counts))
        orders_with_refunds = int(np.sum(refund_counts > 0))
        
        # ===== ETSY FEES ON REFUNDS =====
        # IMPORTANT: When you refund an order, Etsy KEEPS the transaction fee (doesn't refund it)
        # Only the processing fee is refunded. This is an additional cost on refunds.
        etsy_fees_retained_on_refunds = total_refund_amount * self.etsy_transaction_fee_rate
        
        # ===== NET PROFIT CALCULATION =====
        # Net Profit = Gross Profit - Refunds - Etsy Fees Retained on Refunds
        # (After all costs, fees, refunds, AND the Etsy fees you can't get back)
        net_profit = gross_profit - total_refund_amount - etsy_fees_retained_on_refunds
        
        # Adjusted net revenue (after refunds)
        net_revenue_after_refunds = net_revenue_from_sales - total_refund_amount - etsy_fees_retained_on_refunds
        
        # Business metrics
        avg_customer_value = gross_revenue / unique_customers if unique_customers > 0 else 0
        customer_retention_rate = repeat_customers / unique_customers if unique_customers > 0 else 0
        estimated_clv = avg_customer_value * (1 + customer_retention_rate)
        
        customer_acquisition_cost = total_cost / unique_customers if unique_customers > 0 else 0
        
        period_days = (date_range.end_date - date_range.start_date).days + 1
        daily_profit_per_customer = (gross_profit / unique_customers) / period_days if unique_customers > 0 and period_days > 0 else 0
        payback_period_days = customer_acquisition_cost / daily_profit_per_customer if daily_profit_per_customer > 0 else 0
        
        # Price elasticity
        price_elasticity = 0
        if total_discounts_given > 0 and gross_revenue > 0 and total_items > 0:
            discount_rate = total_discounts_given / gross_revenue
            avg_price = gross_revenue / total_items
            price_change = (total_discounts_given / total_items) / avg_price if avg_price > 0 else 0
            quantity_change = total_items / total_orders if total_orders > 0 else 0
            price_elasticity = (quantity_change / price_change) if price_change != 0 else 0
        
        # Compile metrics
        metrics = {
            "period_start": date_range.start_date,
            "period_end": date_range.end_date,
            "period_days": period_days,
            
            # ===== REVENUE METRICS (CORRECTED FOR ETSY) =====
            "gross_revenue": round(gross_revenue, 2),  # What buyers paid (grand_total)
            "total_revenue": round(gross_revenue, 2),  # Alias for backwards compatibility
            "product_revenue": round(product_revenue, 2),  # Net product sales (after fees, excl shipping)
            "total_shipping_charged": round(total_shipping_charged, 2),  # Shipping charged to customers
            "total_tax_collected": round(total_tax_collected, 2),
            "total_vat_collected": round(total_vat_collected, 2),
            "total_gift_wrap_revenue": round(total_gift_wrap_revenue, 2),
            "total_discounts_given": round(total_discounts_given, 2),
            
            # ===== ETSY FEES (NEW) =====
            "etsy_transaction_fees": round(etsy_transaction_fees, 2),
            "etsy_processing_fees": round(etsy_processing_fees, 2),
            "total_etsy_fees": round(total_etsy_fees, 2),
            "etsy_fee_rate": round(total_etsy_fees / gross_revenue, 4) if gross_revenue > 0 else 0,
            
            # ===== NET REVENUE (CORRECTED) =====
            "net_revenue": round(net_revenue_from_sales, 2),  # After Etsy fees & taxes
            "net_revenue_after_refunds": round(net_revenue_after_refunds, 2),
            "take_home_rate": round(net_revenue_from_sales / gross_revenue, 4) if gross_revenue > 0 else 0,
            "discount_rate": round(total_discounts_given / gross_revenue, 4) if gross_revenue > 0 else 0,
            
            # ===== SHIPPING COST METRICS (NEW) =====
            "actual_shipping_cost": round(total_actual_shipping_cost, 2),  # Actual FedEx costs
            "shipping_profit": round(shipping_profit, 2),  # Profit/loss on shipping
            "duty_amount": round(total_us_import_duty, 2),  # US customs duties (COST to us)
            "tax_amount": round(total_us_import_tax, 2),  # US import taxes (COST to us)
            "fedex_processing_fee": round(total_fedex_processing_fee, 2),  # FedEx processing fees
            
            # ===== COST & PROFIT METRICS (CORRECTED WITH SHIPPING) =====
            "total_cost": round(total_cost, 2),  # COGS only
            "total_cost_with_shipping": round(total_cost_with_shipping, 2),  # COGS + Shipping + Duties + Taxes
            "avg_cost_per_item": round(avg_cost_per_item, 2),
            "cost_per_order": round(total_cost_with_shipping / total_orders, 2) if total_orders > 0 else 0,
            
            "contribution_margin": round(contribution_margin, 2),  # Product profit before shipping costs
            "gross_profit": round(gross_profit, 2),  # After COGS, shipping, duties, taxes & Etsy fees
            "gross_margin": round(gross_profit / gross_revenue, 4) if gross_revenue > 0 else 0,
            "net_profit": round(net_profit, 2),  # After everything including refunds
            "net_margin": round(net_profit / gross_revenue, 4) if gross_revenue > 0 else 0,
            "return_on_revenue": round(net_profit / gross_revenue, 4) if gross_revenue > 0 else 0,
            "markup_ratio": round(gross_profit / total_cost_with_shipping, 4) if total_cost_with_shipping > 0 else 0,
            
            # ===== ORDER METRICS =====
            "total_orders": total_orders,
            "total_items": total_items,
            "total_quantity_sold": total_quantity_sold,
            "unique_skus": len(unique_skus),
            "average_order_value": round(gross_revenue / total_orders, 2) if total_orders > 0 else 0,
            "median_order_value": round(median_order_value, 2),
            "percentile_75_order_value": round(percentile_75_order_value, 2),
            "percentile_25_order_value": round(percentile_25_order_value, 2),
            "order_value_std": round(order_value_std, 2),
            "items_per_order": round(total_items / total_orders, 2) if total_orders > 0 else 0,
            "revenue_per_item": round(gross_revenue / total_items, 2) if total_items > 0 else 0,
            "profit_per_item": round(gross_profit / total_items, 2) if total_items > 0 else 0,
            
            # ===== CUSTOMER METRICS =====
            "unique_customers": unique_customers,
            "repeat_customers": repeat_customers,
            "customer_retention_rate": round(customer_retention_rate, 4),
            "revenue_per_customer": round(avg_customer_value, 2),
            "orders_per_customer": round(total_orders / unique_customers, 2) if unique_customers > 0 else 0,
            "profit_per_customer": round(gross_profit / unique_customers, 2) if unique_customers > 0 else 0,
            
            # ===== OPERATIONAL METRICS =====
            "shipped_orders": shipped_count,
            "shipping_rate": round(shipping_rate, 4),
            "gift_orders": gift_order_count,
            "gift_rate": round(gift_rate, 4),
            "avg_time_between_orders_hours": round(avg_time_between_orders, 2),
            "orders_per_day": round(total_orders / period_days, 2),
            "revenue_per_day": round(gross_revenue / period_days, 2),
            
            # ===== REFUND METRICS =====
            "total_refund_amount": round(total_refund_amount, 2),
            "total_refund_count": total_refund_count,
            "orders_with_refunds": orders_with_refunds,
            "etsy_fees_retained_on_refunds": round(etsy_fees_retained_on_refunds, 2),  # NEW: Etsy keeps these!
            "refund_rate_by_order": round(total_refund_count / total_orders, 4) if total_orders > 0 else 0,
            "refund_rate_by_value": round(total_refund_amount / gross_revenue, 4) if gross_revenue > 0 else 0,
            "order_refund_rate": round(orders_with_refunds / total_orders, 4) if total_orders > 0 else 0,
            
            # ===== CANCELLATION METRICS =====
            "cancelled_orders": len(orders) - len(completed_orders),
            "cancellation_rate": round((len(orders) - len(completed_orders)) / len(orders), 4) if len(orders) > 0 else 0,
            "completion_rate": round(total_orders / len(orders), 4) if len(orders) > 0 else 0,
            
            # ===== PAYMENT METRICS =====
            "primary_payment_method": max(payment_method_counts, key=payment_method_counts.get) if payment_method_counts else None,
            "payment_method_diversity": len(payment_method_counts),
            
            # ===== BUSINESS METRICS =====
            "customer_lifetime_value": round(estimated_clv, 2),
            "payback_period_days": round(payback_period_days, 1),
            "customer_acquisition_cost": round(customer_acquisition_cost, 2),
            "price_elasticity": round(price_elasticity, 4),
            
            # ===== TEMPORAL METRICS =====
            "peak_month": None,
            "peak_day_of_week": None,
            "peak_hour": None,
            "seasonality_index": 0,
            
            # ===== INVENTORY METRICS =====
            "total_inventory": 0,
            "avg_price": 0,
            "price_range": 0,
            "active_variants": 0,
            "inventory_turnover": 0,
            "stockout_risk": 0,
        }
        
        # Get inventory from cache (instant!)
        if sku:
            cache_key = f"sku_{sku}"
            inventory_data = self._inventory_cache.get(cache_key, {
                "total_inventory": 0, "avg_price": 0, "price_range": 0, "active_variants": 0
            })
        elif listing_id:
            cache_key = f"listing_{listing_id}"
            inventory_data = self._inventory_cache.get(cache_key, {
                "total_inventory": 0, "avg_price": 0, "price_range": 0, "active_variants": 0
            })
        else:
            inventory_data = {"total_inventory": 0, "avg_price": 0, "price_range": 0, "active_variants": 0}
        
        metrics.update(inventory_data)
        
        # Calculate inventory turnover
        if inventory_data.get("total_inventory", 0) > 0:
            inventory_turnover = total_quantity_sold / inventory_data["total_inventory"]
            stockout_risk = max(0, min(1, 1 - (inventory_data["total_inventory"] / max(total_quantity_sold, 1))))
            metrics["inventory_turnover"] = round(inventory_turnover, 4)
            metrics["stockout_risk"] = round(stockout_risk, 4)
        
        # Log warning if cost data is incomplete
        if total_quantity_sold > 0 and total_quantity_with_cost < total_quantity_sold:
            cost_coverage_pct = (total_quantity_with_cost / total_quantity_sold) * 100
            period_str = f"{date_range.start_date.date()} to {date_range.end_date.date()}"
            entity_str = f"SKU={sku}" if sku else f"Listing={listing_id}" if listing_id else "Shop"
            
            # Only log periodically to avoid spam (every 10th incomplete period)
            warning_key = f"{entity_str}_{period_str}"
            if warning_key not in self._cost_coverage_warnings_shown:
                self._cost_coverage_warnings_shown.add(warning_key)
                if len(self._cost_coverage_warnings_shown) % 10 == 1:  # Log 1st, 11th, 21st, etc.
                    logger.warning(
                        f"⚠️ Incomplete cost data for {entity_str}, period {period_str}: "
                        f"{total_quantity_with_cost}/{total_quantity_sold} items have costs ({cost_coverage_pct:.1f}% coverage). "
                        f"Profit metrics may be underestimated."
                    )
        
        return metrics

    async def get_inventory_insights_by_sku(self, sku: str) -> Dict:
        """Get inventory insights for a specific SKU from cache."""
        cache_key = f"sku_{sku}"
        return self._inventory_cache.get(cache_key, {
            "total_inventory": 0, "avg_price": 0, "price_range": 0, "active_variants": 0
        })

    async def get_inventory_insights_by_listing(self, listing_id: int) -> Dict:
        """Get inventory insights for a listing from cache."""
        cache_key = f"listing_{listing_id}"
        return self._inventory_cache.get(cache_key, {
            "total_inventory": 0, "avg_price": 0, "price_range": 0, "active_variants": 0
        })

    async def _empty_metrics(self, sku: Optional[str] = None, 
                           listing_id: Optional[int] = None,
                           date_range: Optional[DateRange] = None) -> Dict:
        """Return empty metrics with corrected Etsy structure and shipping costs."""
        return {
            "period_start": date_range.start_date if date_range else None,
            "period_end": date_range.end_date if date_range else None,
            "period_days": 0,
            # Revenue
            "gross_revenue": 0, "total_revenue": 0, "product_revenue": 0, 
            "total_shipping_charged": 0, "total_tax_collected": 0, "total_vat_collected": 0, 
            "total_gift_wrap_revenue": 0, "total_discounts_given": 0,
            # Etsy fees
            "etsy_transaction_fees": 0, "etsy_processing_fees": 0, "total_etsy_fees": 0, "etsy_fee_rate": 0,
            # Net revenue
            "net_revenue": 0, "net_revenue_after_refunds": 0, "take_home_rate": 0, "discount_rate": 0,
            # Shipping costs
            "actual_shipping_cost": 0, "shipping_profit": 0, "duty_amount": 0, "tax_amount": 0, "fedex_processing_fee": 0,
            # Costs & Profit
            "total_cost": 0, "total_cost_with_shipping": 0, "avg_cost_per_item": 0, "cost_per_order": 0, 
            "contribution_margin": 0, "gross_profit": 0, "gross_margin": 0, 
            "net_profit": 0, "net_margin": 0, "return_on_revenue": 0, "markup_ratio": 0,
            # Orders
            "total_orders": 0, "total_items": 0, "total_quantity_sold": 0, "unique_skus": 0,
            "average_order_value": 0, "median_order_value": 0, "percentile_75_order_value": 0,
            "percentile_25_order_value": 0, "order_value_std": 0, "items_per_order": 0,
            "revenue_per_item": 0, "profit_per_item": 0,
            # Customers
            "unique_customers": 0, "repeat_customers": 0, "customer_retention_rate": 0,
            "revenue_per_customer": 0, "orders_per_customer": 0, "profit_per_customer": 0,
            # Operations
            "shipped_orders": 0, "shipping_rate": 0, "gift_orders": 0, "gift_rate": 0,
            "avg_time_between_orders_hours": 0, "orders_per_day": 0, "revenue_per_day": 0,
            # Refunds
            "total_refund_amount": 0, "total_refund_count": 0, "orders_with_refunds": 0,
            "etsy_fees_retained_on_refunds": 0,
            "refund_rate_by_order": 0, "refund_rate_by_value": 0, "order_refund_rate": 0,
            # Cancellations
            "cancelled_orders": 0, "cancellation_rate": 0, "completion_rate": 0,
            # Payment
            "primary_payment_method": None, "payment_method_diversity": 0,
            # Temporal
            "peak_month": None, "peak_day_of_week": None, "peak_hour": None, "seasonality_index": 0,
            # Inventory
            "total_inventory": 0, "avg_price": 0, "price_range": 0, "active_variants": 0,
            "inventory_turnover": 0, "stockout_risk": 0,
            # Business
            "customer_lifetime_value": 0, "payback_period_days": 0, "customer_acquisition_cost": 0,
            "price_elasticity": 0,
        }

    # --- SAVE METHODS (BULK OPTIMIZED) ---

    def _snake_to_camel(self, snake_str: str) -> str:
        """Convert snake_case to camelCase."""
        components = snake_str.split('_')
        return components[0] + ''.join(x.title() for x in components[1:])

    async def _bulk_save_reports(self, reports: List[Tuple[str, Dict]], report_type: str):
        """⚡ Bulk save reports using raw SQL for maximum performance."""
        if not reports:
            return
        
        try:
            # Group reports into batches
            for i in range(0, len(reports), self.batch_size):
                batch = reports[i:i + self.batch_size]
                
                if report_type == "shop":
                    await self._bulk_upsert_shop_reports(batch)
                elif report_type == "listing":
                    await self._bulk_upsert_listing_reports(batch)
                elif report_type == "product":
                    await self._bulk_upsert_product_reports(batch)
                    
        except Exception as e:
            logger.error(f"Error in bulk save: {e}")

    async def _bulk_upsert_shop_reports(self, batch: List[Tuple[str, Dict]]):
        """Bulk upsert shop reports using raw SQL."""
        try:
            # Build VALUES clause
            values = []
            for period_type, period_start, period_end, metrics in batch:
                period_type_enum = period_type.upper()
                m = metrics
                values.append(f"""(
                    '{period_type_enum}',
                    '{period_start.isoformat()}',
                    '{period_end.isoformat()}',
                    {m.get('period_days', 0)},
                    {m.get('total_revenue', 0)},
                    {m.get('product_revenue', 0)},
                    {m.get('total_shipping_revenue', 0)},
                    {m.get('total_cost', 0)},
                    {m.get('gross_profit', 0)},
                    {m.get('net_profit', 0)},
                    {m.get('total_orders', 0)},
                    {m.get('total_items', 0)},
                    {m.get('unique_customers', 0)}
                )""")
            
            # Use ON CONFLICT DO UPDATE for upsert
            query = f"""
                INSERT INTO shop_reports (
                    period_type, period_start, period_end, period_days,
                    total_revenue, product_revenue, total_shipping_revenue,
                    total_cost, gross_profit, net_profit,
                    total_orders, total_items, unique_customers
                ) VALUES {','.join(values)}
                ON CONFLICT (period_type, period_start, period_end)
                DO UPDATE SET
                    total_revenue = EXCLUDED.total_revenue,
                    product_revenue = EXCLUDED.product_revenue,
                    total_orders = EXCLUDED.total_orders,
                    updated_at = NOW()
            """
            
            await self.prisma.execute_raw(query)
        except Exception as e:
            logger.error(f"Error in bulk upsert shop reports: {e}")
            # Fallback to individual saves
            for item in batch:
                try:
                    await self.save_shop_report(*item)
                except:
                    pass

    def _clean_metric_value(self, value):
        """Clean metric values to prevent NaN, Infinity, or None issues."""
        if value is None:
            return 0
        if isinstance(value, float):
            if math.isnan(value) or math.isinf(value):
                return 0
        return value

    async def save_shop_report(self, metrics: Dict, period_type: str, 
                              period_start: datetime, period_end: datetime) -> None:
        """Save shop report to database (optimized single insert)."""
        try:
            # Map period_type string to enum (same as reportsv3.py)
            period_type_enum = {
                "yearly": PeriodType.YEARLY,
                "monthly": PeriodType.MONTHLY, 
                "weekly": PeriodType.WEEKLY
            }[period_type]
            
            # Use the same working approach as reportsv3.py - explicit field mapping
            # Clean all metrics to prevent NaN/Infinity issues
            payload = {
                "periodType": period_type_enum,
                "periodStart": period_start,
                "periodEnd": period_end,
                "periodDays": self._clean_metric_value(metrics.get("period_days", 0)),
                "grossRevenue": self._clean_metric_value(metrics.get("gross_revenue", 0)),
                "totalRevenue": self._clean_metric_value(metrics.get("total_revenue", 0)),
                "productRevenue": self._clean_metric_value(metrics.get("product_revenue", 0)),
                "totalShippingRevenue": self._clean_metric_value(metrics.get("total_shipping_revenue", 0)),
                "totalShippingCharged": self._clean_metric_value(metrics.get("total_shipping_charged", 0)),
                "actualShippingCost": self._clean_metric_value(metrics.get("actual_shipping_cost", 0)),
                "shippingProfit": self._clean_metric_value(metrics.get("shipping_profit", 0)),
                "dutyAmount": self._clean_metric_value(metrics.get("duty_amount", 0)),
                "taxAmount": self._clean_metric_value(metrics.get("tax_amount", 0)),
                "fedexProcessingFee": self._clean_metric_value(metrics.get("fedex_processing_fee", 0)),
                "totalTaxCollected": self._clean_metric_value(metrics.get("total_tax_collected", 0)),
                "totalVatCollected": self._clean_metric_value(metrics.get("total_vat_collected", 0)),
                "totalGiftWrapRevenue": self._clean_metric_value(metrics.get("total_gift_wrap_revenue", 0)),
                "totalDiscountsGiven": self._clean_metric_value(metrics.get("total_discounts_given", 0)),
                "etsyTransactionFees": self._clean_metric_value(metrics.get("etsy_transaction_fees", 0)),
                "etsyProcessingFees": self._clean_metric_value(metrics.get("etsy_processing_fees", 0)),
                "totalEtsyFees": self._clean_metric_value(metrics.get("total_etsy_fees", 0)),
                "etsyFeeRate": self._clean_metric_value(metrics.get("etsy_fee_rate", 0)),
                "netRevenue": self._clean_metric_value(metrics.get("net_revenue", 0)),
                "netRevenueAfterRefunds": self._clean_metric_value(metrics.get("net_revenue_after_refunds", 0)),
                "takeHomeRate": self._clean_metric_value(metrics.get("take_home_rate", 0)),
                "discountRate": self._clean_metric_value(metrics.get("discount_rate", 0)),
                "contributionMargin": self._clean_metric_value(metrics.get("contribution_margin", 0)),
                "totalCost": self._clean_metric_value(metrics.get("total_cost", 0)),
                "totalCostWithShipping": self._clean_metric_value(metrics.get("total_cost_with_shipping", 0)),
                "avgCostPerItem": self._clean_metric_value(metrics.get("avg_cost_per_item", 0)),
                "costPerOrder": self._clean_metric_value(metrics.get("cost_per_order", 0)),
                "grossProfit": self._clean_metric_value(metrics.get("gross_profit", 0)),
                "grossMargin": self._clean_metric_value(metrics.get("gross_margin", 0)),
                "netProfit": self._clean_metric_value(metrics.get("net_profit", 0)),
                "netMargin": self._clean_metric_value(metrics.get("net_margin", 0)),
                "returnOnRevenue": self._clean_metric_value(metrics.get("return_on_revenue", 0)),
                "markupRatio": self._clean_metric_value(metrics.get("markup_ratio", 0)),
                "totalOrders": self._clean_metric_value(metrics.get("total_orders", 0)),
                "totalItems": self._clean_metric_value(metrics.get("total_items", 0)),
                "totalQuantitySold": self._clean_metric_value(metrics.get("total_quantity_sold", 0)),
                "uniqueSkus": self._clean_metric_value(metrics.get("unique_skus", 0)),
                "averageOrderValue": self._clean_metric_value(metrics.get("average_order_value", 0)),
                "medianOrderValue": self._clean_metric_value(metrics.get("median_order_value", 0)),
                "percentile75OrderValue": self._clean_metric_value(metrics.get("percentile_75_order_value", 0)),
                "percentile25OrderValue": self._clean_metric_value(metrics.get("percentile_25_order_value", 0)),
                "orderValueStd": self._clean_metric_value(metrics.get("order_value_std", 0)),
                "itemsPerOrder": self._clean_metric_value(metrics.get("items_per_order", 0)),
                "revenuePerItem": self._clean_metric_value(metrics.get("revenue_per_item", 0)),
                "profitPerItem": self._clean_metric_value(metrics.get("profit_per_item", 0)),
                "uniqueCustomers": self._clean_metric_value(metrics.get("unique_customers", 0)),
                "repeatCustomers": self._clean_metric_value(metrics.get("repeat_customers", 0)),
                "customerRetentionRate": self._clean_metric_value(metrics.get("customer_retention_rate", 0)),
                "revenuePerCustomer": self._clean_metric_value(metrics.get("revenue_per_customer", 0)),
                "ordersPerCustomer": self._clean_metric_value(metrics.get("orders_per_customer", 0)),
                "profitPerCustomer": self._clean_metric_value(metrics.get("profit_per_customer", 0)),
                "shippedOrders": self._clean_metric_value(metrics.get("shipped_orders", 0)),
                "shippingRate": self._clean_metric_value(metrics.get("shipping_rate", 0)),
                "giftOrders": self._clean_metric_value(metrics.get("gift_orders", 0)),
                "giftRate": self._clean_metric_value(metrics.get("gift_rate", 0)),
                "avgTimeBetweenOrdersHours": self._clean_metric_value(metrics.get("avg_time_between_orders_hours", 0)),
                "ordersPerDay": self._clean_metric_value(metrics.get("orders_per_day", 0)),
                "revenuePerDay": self._clean_metric_value(metrics.get("revenue_per_day", 0)),
                "totalRefundAmount": self._clean_metric_value(metrics.get("total_refund_amount", 0)),
                "totalRefundCount": self._clean_metric_value(metrics.get("total_refund_count", 0)),
                "ordersWithRefunds": self._clean_metric_value(metrics.get("orders_with_refunds", 0)),
                "etsyFeesRetainedOnRefunds": self._clean_metric_value(metrics.get("etsy_fees_retained_on_refunds", 0)),
                "refundRateByOrder": self._clean_metric_value(metrics.get("refund_rate_by_order", 0)),
                "refundRateByValue": self._clean_metric_value(metrics.get("refund_rate_by_value", 0)),
                "orderRefundRate": self._clean_metric_value(metrics.get("order_refund_rate", 0)),
                "cancelledOrders": self._clean_metric_value(metrics.get("cancelled_orders", 0)),
                "cancellationRate": self._clean_metric_value(metrics.get("cancellation_rate", 0)),
                "completionRate": self._clean_metric_value(metrics.get("completion_rate", 0)),
                "primaryPaymentMethod": metrics.get("primary_payment_method"),
                "paymentMethodDiversity": self._clean_metric_value(metrics.get("payment_method_diversity", 0)),
                "customerLifetimeValue": self._clean_metric_value(metrics.get("customer_lifetime_value", 0)),
                "paybackPeriodDays": self._clean_metric_value(metrics.get("payback_period_days", 0)),
                "customerAcquisitionCost": self._clean_metric_value(metrics.get("customer_acquisition_cost", 0)),
                "priceElasticity": self._clean_metric_value(metrics.get("price_elasticity", 0)),
                "peakMonth": metrics.get("peak_month"),
                "peakDayOfWeek": metrics.get("peak_day_of_week"),
                "peakHour": metrics.get("peak_hour"),
                "seasonalityIndex": self._clean_metric_value(metrics.get("seasonality_index", 0)),
                "totalInventory": self._clean_metric_value(metrics.get("total_inventory", 0)),
                "avgPrice": self._clean_metric_value(metrics.get("avg_price", 0)),
                "priceRange": self._clean_metric_value(metrics.get("price_range", 0)),
                "activeVariants": self._clean_metric_value(metrics.get("active_variants", 0)),
                "inventoryTurnover": self._clean_metric_value(metrics.get("inventory_turnover", 0)),
                "stockoutRisk": self._clean_metric_value(metrics.get("stockout_risk", 0)),
            }
            
            await self.prisma.shopreport.upsert(
                where={
                    "periodType_periodStart_periodEnd": {
                        "periodType": period_type_enum,
                        "periodStart": period_start,
                        "periodEnd": period_end,
                    }
                },
                data={
                    "create": payload,
                    "update": payload
                }
            )
        except Exception as e:
            logger.error(f"Error saving shop report for {period_type} {period_start}-{period_end}: {e}", exc_info=True)
            raise  # Re-raise to see the full error

    async def save_listing_report(self, listing_id: int, metrics: Dict, period_type: str,
                                 period_start: datetime, period_end: datetime) -> None:
        """Save listing report to database."""
        try:
            # Map period_type string to enum (same as reportsv3.py)
            period_type_enum = {
                "yearly": PeriodType.YEARLY,
                "monthly": PeriodType.MONTHLY, 
                "weekly": PeriodType.WEEKLY
            }[period_type]
            
            # Use the same working approach - explicit field mapping
            # Clean all metrics to prevent NaN/Infinity issues
            payload = {
                "listingId": listing_id,
                "periodType": period_type_enum,
                "periodStart": period_start,
                "periodEnd": period_end,
                "periodDays": self._clean_metric_value(metrics.get("period_days", 0)),
                "grossRevenue": self._clean_metric_value(metrics.get("gross_revenue", 0)),
                "totalRevenue": self._clean_metric_value(metrics.get("total_revenue", 0)),
                "productRevenue": self._clean_metric_value(metrics.get("product_revenue", 0)),
                "totalShippingRevenue": self._clean_metric_value(metrics.get("total_shipping_revenue", 0)),
                "totalShippingCharged": self._clean_metric_value(metrics.get("total_shipping_charged", 0)),
                "actualShippingCost": self._clean_metric_value(metrics.get("actual_shipping_cost", 0)),
                "shippingProfit": self._clean_metric_value(metrics.get("shipping_profit", 0)),
                "dutyAmount": self._clean_metric_value(metrics.get("duty_amount", 0)),
                "taxAmount": self._clean_metric_value(metrics.get("tax_amount", 0)),
                "fedexProcessingFee": self._clean_metric_value(metrics.get("fedex_processing_fee", 0)),
                "totalTaxCollected": self._clean_metric_value(metrics.get("total_tax_collected", 0)),
                "totalVatCollected": self._clean_metric_value(metrics.get("total_vat_collected", 0)),
                "totalGiftWrapRevenue": self._clean_metric_value(metrics.get("total_gift_wrap_revenue", 0)),
                "totalDiscountsGiven": self._clean_metric_value(metrics.get("total_discounts_given", 0)),
                "etsyTransactionFees": self._clean_metric_value(metrics.get("etsy_transaction_fees", 0)),
                "etsyProcessingFees": self._clean_metric_value(metrics.get("etsy_processing_fees", 0)),
                "totalEtsyFees": self._clean_metric_value(metrics.get("total_etsy_fees", 0)),
                "etsyFeeRate": self._clean_metric_value(metrics.get("etsy_fee_rate", 0)),
                "netRevenue": self._clean_metric_value(metrics.get("net_revenue", 0)),
                "netRevenueAfterRefunds": self._clean_metric_value(metrics.get("net_revenue_after_refunds", 0)),
                "takeHomeRate": self._clean_metric_value(metrics.get("take_home_rate", 0)),
                "discountRate": self._clean_metric_value(metrics.get("discount_rate", 0)),
                "contributionMargin": self._clean_metric_value(metrics.get("contribution_margin", 0)),
                "totalCost": self._clean_metric_value(metrics.get("total_cost", 0)),
                "totalCostWithShipping": self._clean_metric_value(metrics.get("total_cost_with_shipping", 0)),
                "avgCostPerItem": self._clean_metric_value(metrics.get("avg_cost_per_item", 0)),
                "costPerOrder": self._clean_metric_value(metrics.get("cost_per_order", 0)),
                "grossProfit": self._clean_metric_value(metrics.get("gross_profit", 0)),
                "grossMargin": self._clean_metric_value(metrics.get("gross_margin", 0)),
                "netProfit": self._clean_metric_value(metrics.get("net_profit", 0)),
                "netMargin": self._clean_metric_value(metrics.get("net_margin", 0)),
                "returnOnRevenue": self._clean_metric_value(metrics.get("return_on_revenue", 0)),
                "markupRatio": self._clean_metric_value(metrics.get("markup_ratio", 0)),
                "totalOrders": self._clean_metric_value(metrics.get("total_orders", 0)),
                "totalItems": self._clean_metric_value(metrics.get("total_items", 0)),
                "totalQuantitySold": self._clean_metric_value(metrics.get("total_quantity_sold", 0)),
                "uniqueSkus": self._clean_metric_value(metrics.get("unique_skus", 0)),
                "averageOrderValue": self._clean_metric_value(metrics.get("average_order_value", 0)),
                "medianOrderValue": self._clean_metric_value(metrics.get("median_order_value", 0)),
                "percentile75OrderValue": self._clean_metric_value(metrics.get("percentile_75_order_value", 0)),
                "percentile25OrderValue": self._clean_metric_value(metrics.get("percentile_25_order_value", 0)),
                "orderValueStd": self._clean_metric_value(metrics.get("order_value_std", 0)),
                "itemsPerOrder": self._clean_metric_value(metrics.get("items_per_order", 0)),
                "revenuePerItem": self._clean_metric_value(metrics.get("revenue_per_item", 0)),
                "profitPerItem": self._clean_metric_value(metrics.get("profit_per_item", 0)),
                "uniqueCustomers": self._clean_metric_value(metrics.get("unique_customers", 0)),
                "repeatCustomers": self._clean_metric_value(metrics.get("repeat_customers", 0)),
                "customerRetentionRate": self._clean_metric_value(metrics.get("customer_retention_rate", 0)),
                "revenuePerCustomer": self._clean_metric_value(metrics.get("revenue_per_customer", 0)),
                "ordersPerCustomer": self._clean_metric_value(metrics.get("orders_per_customer", 0)),
                "profitPerCustomer": self._clean_metric_value(metrics.get("profit_per_customer", 0)),
                "shippedOrders": self._clean_metric_value(metrics.get("shipped_orders", 0)),
                "shippingRate": self._clean_metric_value(metrics.get("shipping_rate", 0)),
                "giftOrders": self._clean_metric_value(metrics.get("gift_orders", 0)),
                "giftRate": self._clean_metric_value(metrics.get("gift_rate", 0)),
                "avgTimeBetweenOrdersHours": self._clean_metric_value(metrics.get("avg_time_between_orders_hours", 0)),
                "ordersPerDay": self._clean_metric_value(metrics.get("orders_per_day", 0)),
                "revenuePerDay": self._clean_metric_value(metrics.get("revenue_per_day", 0)),
                "totalRefundAmount": self._clean_metric_value(metrics.get("total_refund_amount", 0)),
                "totalRefundCount": self._clean_metric_value(metrics.get("total_refund_count", 0)),
                "ordersWithRefunds": self._clean_metric_value(metrics.get("orders_with_refunds", 0)),
                "etsyFeesRetainedOnRefunds": self._clean_metric_value(metrics.get("etsy_fees_retained_on_refunds", 0)),
                "refundRateByOrder": self._clean_metric_value(metrics.get("refund_rate_by_order", 0)),
                "refundRateByValue": self._clean_metric_value(metrics.get("refund_rate_by_value", 0)),
                "orderRefundRate": self._clean_metric_value(metrics.get("order_refund_rate", 0)),
                "cancelledOrders": self._clean_metric_value(metrics.get("cancelled_orders", 0)),
                "cancellationRate": self._clean_metric_value(metrics.get("cancellation_rate", 0)),
                "completionRate": self._clean_metric_value(metrics.get("completion_rate", 0)),
                "primaryPaymentMethod": metrics.get("primary_payment_method"),
                "paymentMethodDiversity": self._clean_metric_value(metrics.get("payment_method_diversity", 0)),
                "customerLifetimeValue": self._clean_metric_value(metrics.get("customer_lifetime_value", 0)),
                "paybackPeriodDays": self._clean_metric_value(metrics.get("payback_period_days", 0)),
                "customerAcquisitionCost": self._clean_metric_value(metrics.get("customer_acquisition_cost", 0)),
                "priceElasticity": self._clean_metric_value(metrics.get("price_elasticity", 0)),
                "peakMonth": metrics.get("peak_month"),
                "peakDayOfWeek": metrics.get("peak_day_of_week"),
                "peakHour": metrics.get("peak_hour"),
                "seasonalityIndex": self._clean_metric_value(metrics.get("seasonality_index", 0)),
                "totalInventory": self._clean_metric_value(metrics.get("total_inventory", 0)),
                "avgPrice": self._clean_metric_value(metrics.get("avg_price", 0)),
                "priceRange": self._clean_metric_value(metrics.get("price_range", 0)),
                "activeVariants": self._clean_metric_value(metrics.get("active_variants", 0)),
                "inventoryTurnover": self._clean_metric_value(metrics.get("inventory_turnover", 0)),
                "stockoutRisk": self._clean_metric_value(metrics.get("stockout_risk", 0)),
                # Listing-specific fields
                "listingViews": self._clean_metric_value(metrics.get("listing_views", 0)),
                "listingFavorites": self._clean_metric_value(metrics.get("listing_favorites", 0)),
                "conversionRate": self._clean_metric_value(metrics.get("conversion_rate", 0)),
                "favoriteToOrderRate": self._clean_metric_value(metrics.get("favorite_to_order_rate", 0)),
                "viewToFavoriteRate": self._clean_metric_value(metrics.get("view_to_favorite_rate", 0)),
                "revenuePerView": self._clean_metric_value(metrics.get("revenue_per_view", 0)),
                "profitPerView": self._clean_metric_value(metrics.get("profit_per_view", 0)),
                "costPerAcquisition": self._clean_metric_value(metrics.get("cost_per_acquisition", 0)),
                "shopAvgViews": self._clean_metric_value(metrics.get("shop_avg_views", 0)),
                "shopAvgFavorites": self._clean_metric_value(metrics.get("shop_avg_favorites", 0)),
                "viewsVsShopAvg": self._clean_metric_value(metrics.get("views_vs_shop_avg", 0)),
                "favoritesVsShopAvg": self._clean_metric_value(metrics.get("favorites_vs_shop_avg", 0)),
            }
            
            await self.prisma.listingreport.upsert(
                where={
                    "listingId_periodType_periodStart_periodEnd": {
                        "listingId": listing_id,
                        "periodType": period_type_enum,
                        "periodStart": period_start,
                        "periodEnd": period_end,
                    }
                },
                data={
                    "create": payload,
                    "update": payload
                }
            )
        except Exception as e:
            logger.error(f"Error saving listing report for listing {listing_id}, {period_type} {period_start}-{period_end}: {e}", exc_info=True)

    async def save_product_report(self, sku: str, metrics: Dict, period_type: str,
                                 period_start: datetime, period_end: datetime) -> None:
        """Save product report to database."""
        try:
            # Map period_type string to enum (same as reportsv3.py)
            period_type_enum = {
                "yearly": PeriodType.YEARLY,
                "monthly": PeriodType.MONTHLY, 
                "weekly": PeriodType.WEEKLY
            }[period_type]
            
            # Use the same working approach - explicit field mapping
            # Clean all metrics to prevent NaN/Infinity issues
            payload = {
                "sku": sku,
                "periodType": period_type_enum,
                "periodStart": period_start,
                "periodEnd": period_end,
                "periodDays": self._clean_metric_value(metrics.get("period_days", 0)),
                "grossRevenue": self._clean_metric_value(metrics.get("gross_revenue", 0)),
                "totalRevenue": self._clean_metric_value(metrics.get("total_revenue", 0)),
                "productRevenue": self._clean_metric_value(metrics.get("product_revenue", 0)),
                "totalShippingRevenue": self._clean_metric_value(metrics.get("total_shipping_revenue", 0)),
                "totalShippingCharged": self._clean_metric_value(metrics.get("total_shipping_charged", 0)),
                "actualShippingCost": self._clean_metric_value(metrics.get("actual_shipping_cost", 0)),
                "shippingProfit": self._clean_metric_value(metrics.get("shipping_profit", 0)),
                "dutyAmount": self._clean_metric_value(metrics.get("duty_amount", 0)),
                "taxAmount": self._clean_metric_value(metrics.get("tax_amount", 0)),
                "fedexProcessingFee": self._clean_metric_value(metrics.get("fedex_processing_fee", 0)),
                "totalTaxCollected": self._clean_metric_value(metrics.get("total_tax_collected", 0)),
                "totalVatCollected": self._clean_metric_value(metrics.get("total_vat_collected", 0)),
                "totalGiftWrapRevenue": self._clean_metric_value(metrics.get("total_gift_wrap_revenue", 0)),
                "totalDiscountsGiven": self._clean_metric_value(metrics.get("total_discounts_given", 0)),
                "etsyTransactionFees": self._clean_metric_value(metrics.get("etsy_transaction_fees", 0)),
                "etsyProcessingFees": self._clean_metric_value(metrics.get("etsy_processing_fees", 0)),
                "totalEtsyFees": self._clean_metric_value(metrics.get("total_etsy_fees", 0)),
                "etsyFeeRate": self._clean_metric_value(metrics.get("etsy_fee_rate", 0)),
                "netRevenue": self._clean_metric_value(metrics.get("net_revenue", 0)),
                "netRevenueAfterRefunds": self._clean_metric_value(metrics.get("net_revenue_after_refunds", 0)),
                "takeHomeRate": self._clean_metric_value(metrics.get("take_home_rate", 0)),
                "discountRate": self._clean_metric_value(metrics.get("discount_rate", 0)),
                "contributionMargin": self._clean_metric_value(metrics.get("contribution_margin", 0)),
                "totalCost": self._clean_metric_value(metrics.get("total_cost", 0)),
                "totalCostWithShipping": self._clean_metric_value(metrics.get("total_cost_with_shipping", 0)),
                "avgCostPerItem": self._clean_metric_value(metrics.get("avg_cost_per_item", 0)),
                "costPerOrder": self._clean_metric_value(metrics.get("cost_per_order", 0)),
                "grossProfit": self._clean_metric_value(metrics.get("gross_profit", 0)),
                "grossMargin": self._clean_metric_value(metrics.get("gross_margin", 0)),
                "netProfit": self._clean_metric_value(metrics.get("net_profit", 0)),
                "netMargin": self._clean_metric_value(metrics.get("net_margin", 0)),
                "returnOnRevenue": self._clean_metric_value(metrics.get("return_on_revenue", 0)),
                "markupRatio": self._clean_metric_value(metrics.get("markup_ratio", 0)),
                "totalOrders": self._clean_metric_value(metrics.get("total_orders", 0)),
                "totalItems": self._clean_metric_value(metrics.get("total_items", 0)),
                "totalQuantitySold": self._clean_metric_value(metrics.get("total_quantity_sold", 0)),
                "uniqueSkus": self._clean_metric_value(metrics.get("unique_skus", 0)),
                "averageOrderValue": self._clean_metric_value(metrics.get("average_order_value", 0)),
                "medianOrderValue": self._clean_metric_value(metrics.get("median_order_value", 0)),
                "percentile75OrderValue": self._clean_metric_value(metrics.get("percentile_75_order_value", 0)),
                "percentile25OrderValue": self._clean_metric_value(metrics.get("percentile_25_order_value", 0)),
                "orderValueStd": self._clean_metric_value(metrics.get("order_value_std", 0)),
                "itemsPerOrder": self._clean_metric_value(metrics.get("items_per_order", 0)),
                "revenuePerItem": self._clean_metric_value(metrics.get("revenue_per_item", 0)),
                "profitPerItem": self._clean_metric_value(metrics.get("profit_per_item", 0)),
                "uniqueCustomers": self._clean_metric_value(metrics.get("unique_customers", 0)),
                "repeatCustomers": self._clean_metric_value(metrics.get("repeat_customers", 0)),
                "customerRetentionRate": self._clean_metric_value(metrics.get("customer_retention_rate", 0)),
                "revenuePerCustomer": self._clean_metric_value(metrics.get("revenue_per_customer", 0)),
                "ordersPerCustomer": self._clean_metric_value(metrics.get("orders_per_customer", 0)),
                "profitPerCustomer": self._clean_metric_value(metrics.get("profit_per_customer", 0)),
                "shippedOrders": self._clean_metric_value(metrics.get("shipped_orders", 0)),
                "shippingRate": self._clean_metric_value(metrics.get("shipping_rate", 0)),
                "giftOrders": self._clean_metric_value(metrics.get("gift_orders", 0)),
                "giftRate": self._clean_metric_value(metrics.get("gift_rate", 0)),
                "avgTimeBetweenOrdersHours": self._clean_metric_value(metrics.get("avg_time_between_orders_hours", 0)),
                "ordersPerDay": self._clean_metric_value(metrics.get("orders_per_day", 0)),
                "revenuePerDay": self._clean_metric_value(metrics.get("revenue_per_day", 0)),
                "totalRefundAmount": self._clean_metric_value(metrics.get("total_refund_amount", 0)),
                "totalRefundCount": self._clean_metric_value(metrics.get("total_refund_count", 0)),
                "ordersWithRefunds": self._clean_metric_value(metrics.get("orders_with_refunds", 0)),
                "etsyFeesRetainedOnRefunds": self._clean_metric_value(metrics.get("etsy_fees_retained_on_refunds", 0)),
                "refundRateByOrder": self._clean_metric_value(metrics.get("refund_rate_by_order", 0)),
                "refundRateByValue": self._clean_metric_value(metrics.get("refund_rate_by_value", 0)),
                "orderRefundRate": self._clean_metric_value(metrics.get("order_refund_rate", 0)),
                "cancelledOrders": self._clean_metric_value(metrics.get("cancelled_orders", 0)),
                "cancellationRate": self._clean_metric_value(metrics.get("cancellation_rate", 0)),
                "completionRate": self._clean_metric_value(metrics.get("completion_rate", 0)),
                "primaryPaymentMethod": metrics.get("primary_payment_method"),
                "paymentMethodDiversity": self._clean_metric_value(metrics.get("payment_method_diversity", 0)),
                "customerLifetimeValue": self._clean_metric_value(metrics.get("customer_lifetime_value", 0)),
                "paybackPeriodDays": self._clean_metric_value(metrics.get("payback_period_days", 0)),
                "customerAcquisitionCost": self._clean_metric_value(metrics.get("customer_acquisition_cost", 0)),
                "priceElasticity": self._clean_metric_value(metrics.get("price_elasticity", 0)),
                "peakMonth": metrics.get("peak_month"),
                "peakDayOfWeek": metrics.get("peak_day_of_week"),
                "peakHour": metrics.get("peak_hour"),
                "seasonalityIndex": self._clean_metric_value(metrics.get("seasonality_index", 0)),
                "totalInventory": self._clean_metric_value(metrics.get("total_inventory", 0)),
                "avgPrice": self._clean_metric_value(metrics.get("avg_price", 0)),
                "priceRange": self._clean_metric_value(metrics.get("price_range", 0)),
                "activeVariants": self._clean_metric_value(metrics.get("active_variants", 0)),
                "inventoryTurnover": self._clean_metric_value(metrics.get("inventory_turnover", 0)),
                "stockoutRisk": self._clean_metric_value(metrics.get("stockout_risk", 0)),
            }
            
            await self.prisma.productreport.upsert(
                where={
                    "sku_periodType_periodStart_periodEnd": {
                        "sku": sku,
                        "periodType": period_type_enum,
                        "periodStart": period_start,
                        "periodEnd": period_end,
                    }
                },
                data={
                    "create": payload,
                    "update": payload
                }
            )
        except Exception as e:
            logger.error(f"Error saving product report for SKU {sku}, {period_type} {period_start}-{period_end}: {e}", exc_info=True)
            

    async def generate_all_insights_batch(self, clean_old_data: bool = False):
        """
        ⚡ HIERARCHICAL ANALYTICS GENERATION - CORRECT DATA FLOW!
        
        Order of calculation (Bottom-Up):
        1. Product/SKU reports ← Calculate from raw transactions (BASE LEVEL)
        2. Listing reports ← Aggregate from child SKU reports  
        3. Shop reports ← Aggregate from all listings/SKUs
        
        This ensures data consistency and correct parent-child relationships!
        
        Args:
            clean_old_data: If True, DELETE all existing reports before generating new ones.
                           ⚠️ WARNING: This erases all previous analytics!
        """
        print("\n⚡⚡⚡ STARTING HIERARCHICAL ANALYTICS GENERATION ⚡⚡⚡\n")
        
        try:
            # OPTIONAL: Clean all old report data first
            if clean_old_data:
                await self.clean_all_reports()
                print("\n🔄 Starting fresh report generation...\n")
            
            # Get date ranges
            date_result = await self.get_date_ranges_from_database()
            if not date_result:
                logger.error("No orders found")
                return None
            
            start_date, end_date = date_result
            print(f"📅 Processing orders from {start_date} to {end_date}")
            
            # Generate time periods
            periods = self.generate_time_periods(start_date, end_date)
            total_periods = sum(len(p) for p in periods.values())
            print(f"⏱️  Generated {total_periods} time periods\n")
            
            # Get all SKUs and listings
            all_skus = await self.get_all_skus()
            all_listings = await self.get_all_listings()
            print(f"📦 Found {len(all_skus)} SKUs and {len(all_listings)} listings\n")
            
            # Create semaphore for controlled parallelism
            semaphore = asyncio.Semaphore(self.max_concurrent)
            
            # Storage for calculated metrics (for aggregation)
            sku_metrics_store = {}  # {sku: {period_key: metrics}}
            listing_metrics_store = {}  # {listing_id: {period_key: metrics}}
            
            # ==========================================
            # PHASE 1: PRODUCT/SKU REPORTS (BASE LEVEL)
            # ==========================================
            print("📦 PHASE 1: Product/SKU Reports (Base Level - From Transactions)")
            sku_tasks = []
            for sku in all_skus:
                task = self._process_sku_reports_with_cache(sku, periods, semaphore, sku_metrics_store)
                sku_tasks.append(task)
            
            # Process with progress bar
            chunk_size = self.max_concurrent * 2
            with tqdm(total=len(sku_tasks), desc="  Processing SKUs", unit="sku", ncols=100) as pbar:
                for i in range(0, len(sku_tasks), chunk_size):
                    chunk = sku_tasks[i:i + chunk_size]
                    await asyncio.gather(*chunk)
                    pbar.update(len(chunk))
            
            print(f"  ✅ Completed {len(all_skus)} SKUs\n")
            
            # ==========================================
            # PHASE 2: LISTING REPORTS (AGGREGATE FROM CHILD SKUs)
            # ==========================================
            print("📋 PHASE 2: Listing Reports (Aggregated from Child Products)")
            listing_tasks = []
            for listing_id in all_listings:
                task = self._process_listing_reports_aggregated(
                    listing_id, periods, semaphore, sku_metrics_store, listing_metrics_store
                )
                listing_tasks.append(task)
            
            # Process with progress bar
            with tqdm(total=len(listing_tasks), desc="  Processing Listings", unit="listing", ncols=100) as pbar:
                for i in range(0, len(listing_tasks), chunk_size):
                    chunk = listing_tasks[i:i + chunk_size]
                    await asyncio.gather(*chunk)
                    pbar.update(len(chunk))
            
            print(f"  ✅ Completed {len(all_listings)} listings\n")
            
            # ==========================================
            # PHASE 3: SHOP REPORTS (AGGREGATE FROM ALL LISTINGS)
            # ==========================================
            print("🏪 PHASE 3: Shop-Wide Reports (Aggregated from All Listings)")
            shop_tasks = []
            for period_type, date_ranges in periods.items():
                task = self._process_shop_reports_aggregated(
                    period_type, date_ranges, semaphore, listing_metrics_store
                )
                shop_tasks.append(task)
            
            # Process with progress bar
            with tqdm(total=len(shop_tasks), desc="  Processing Shop Reports", unit="type", ncols=100) as pbar:
                for task in shop_tasks:
                    await task
                    pbar.update(1)
            
            print(f"  ✅ Completed all shop reports\n")
            
            print("✅✅✅ ALL INSIGHTS GENERATED WITH CORRECT HIERARCHY! ✅✅✅\n")
            return {
                "status": "success",
                "skus": len(all_skus),
                "listings": len(all_listings),
                "periods": total_periods
            }
            
        except Exception as e:
            logger.error(f"Error in batch generation: {e}", exc_info=True)
            return None

    async def _process_shop_reports(self, period_type: str, date_ranges: List[DateRange], semaphore: asyncio.Semaphore):
        """Process all shop reports for a given period type."""
        async with semaphore:
            try:
                logger.info(f"  → Processing {period_type.upper()} shop reports...")
                all_metrics = await self.calculate_metrics_batch(date_ranges)
                
                saved_count = 0
                for period_key, metrics in all_metrics.items():
                    if metrics.get('total_orders', 0) > 0:
                        await self.save_shop_report(
                            metrics, period_type,
                            metrics['period_start'], metrics['period_end']
                        )
                        saved_count += 1
                
                logger.info(f"  ✅ {period_type.upper()}: Saved {saved_count}/{len(date_ranges)} periods")
            except Exception as e:
                logger.error(f"Error processing shop {period_type}: {e}")

    async def _process_listing_reports(self, listing_id: int, periods: Dict, semaphore: asyncio.Semaphore):
        """Process all reports for a single listing (all period types)."""
        async with semaphore:
            try:
                for period_type, date_ranges in periods.items():
                    all_metrics = await self.calculate_metrics_batch(date_ranges, listing_id=listing_id)
                    
                    for period_key, metrics in all_metrics.items():
                        if metrics.get('total_orders', 0) > 0:
                            await self.save_listing_report(
                                listing_id, metrics, period_type,
                                metrics['period_start'], metrics['period_end']
                            )
            except Exception as e:
                logger.error(f"Error processing listing {listing_id}: {e}")

    async def _process_sku_reports(self, sku: str, periods: Dict, semaphore: asyncio.Semaphore):
        """Process all reports for a single SKU (all period types)."""
        async with semaphore:
            try:
                for period_type, date_ranges in periods.items():
                    all_metrics = await self.calculate_metrics_batch(date_ranges, sku=sku)
                    
                    for period_key, metrics in all_metrics.items():
                        if metrics.get('total_orders', 0) > 0:
                            await self.save_product_report(
                                sku, metrics, period_type,
                                metrics['period_start'], metrics['period_end']
                            )
            except Exception as e:
                logger.error(f"Error processing SKU {sku}: {e}")

    # ============================================================================
    # NEW HIERARCHICAL AGGREGATION METHODS
    # ============================================================================
    
    async def _process_sku_reports_with_cache(self, sku: str, periods: Dict, semaphore: asyncio.Semaphore, cache_store: Dict):
        """Process SKU reports and cache for listing aggregation."""
        async with semaphore:
            try:
                # Check if SKU exists in cost CSV
                if not self._sku_exists_in_cost_csv(sku):
                    self._skipped_products_no_cost.add(sku)
                    self._skipped_count += 1
                    # Still initialize cache entry for aggregation purposes
                    cache_store[sku] = {}
                    return
                
                cache_store[sku] = {}
                for period_type, date_ranges in periods.items():
                    all_metrics = await self.calculate_metrics_batch(date_ranges, sku=sku)
                    
                    for period_key, metrics in all_metrics.items():
                        # Check if this SKU has cost data for this specific period
                        if metrics.get('total_cost', 0) == 0 and metrics.get('total_orders', 0) > 0:
                            # Has orders but no cost data for this period - skip
                            self._skipped_products_no_cost.add(sku)
                            self._skipped_count += 1
                            continue
                        
                        if metrics.get('total_orders', 0) > 0:
                            await self.save_product_report(sku, metrics, period_type,
                                                          metrics['period_start'], metrics['period_end'])
                            full_key = f"{period_type}_{period_key}"
                            cache_store[sku][full_key] = metrics
            except Exception as e:
                logger.error(f"Error processing SKU {sku}: {e}", exc_info=True)

    async def _process_listing_reports_aggregated(self, listing_id: int, periods: Dict, 
                                                  semaphore: asyncio.Semaphore, 
                                                  sku_metrics_store: Dict, listing_cache_store: Dict):
        """
        Listing reports - try aggregation from SKUs first, fall back to direct calculation.
        This ensures all listings get reports even if SKU aggregation fails.
        """
        async with semaphore:
            try:
                child_product_ids = self._listing_to_products.get(listing_id, [])
                child_skus = []
                
                if child_product_ids:
                    child_skus = [sku for sku, pids in self._sku_to_products.items() 
                                 if any(pid in child_product_ids for pid in pids)]
                
                # If no child SKUs found or empty, use direct calculation
                if not child_skus:
                    return await self._process_listing_reports_direct(listing_id, periods, listing_cache_store)
                
                listing_cache_store[listing_id] = {}
                
                for period_type, date_ranges in periods.items():
                    for dr in date_ranges:
                        period_key = f"{dr.start_date.isoformat()}_{dr.end_date.isoformat()}"
                        full_key = f"{period_type}_{period_key}"
                        
                        # TRY 1: Aggregate from child SKUs
                        aggregated_metrics = self._aggregate_from_skus(child_skus, full_key, sku_metrics_store, dr)
                        
                        # TRY 2: If aggregation returned nothing, calculate directly
                        if not aggregated_metrics or aggregated_metrics.get('total_orders', 0) == 0:
                            # Direct calculation for this listing
                            batch_metrics = await self.calculate_metrics_batch([dr], listing_id=listing_id)
                            if batch_metrics:
                                aggregated_metrics = batch_metrics.get(period_key)
                        
                        # Save if we have valid data
                        if aggregated_metrics and aggregated_metrics.get('total_orders', 0) > 0:
                            await self.save_listing_report(
                                listing_id, 
                                aggregated_metrics, 
                                period_type,
                                aggregated_metrics['period_start'], 
                                aggregated_metrics['period_end']
                            )
                            listing_cache_store[listing_id][full_key] = aggregated_metrics
                            
            except Exception as e:
                logger.error(f"Error processing listing {listing_id}: {e}", exc_info=True)

    async def _process_listing_reports_direct(self, listing_id: int, periods: Dict, cache_store: Dict):
        """Fallback for listings without child SKUs."""
        cache_store[listing_id] = {}
        for period_type, date_ranges in periods.items():
            all_metrics = await self.calculate_metrics_batch(date_ranges, listing_id=listing_id)
            for period_key, metrics in all_metrics.items():
                if metrics.get('total_orders', 0) > 0:
                    await self.save_listing_report(listing_id, metrics, period_type,
                                                  metrics['period_start'], metrics['period_end'])
                    cache_store[listing_id][f"{period_type}_{period_key}"] = metrics

    async def _process_shop_reports_aggregated(self, period_type: str, date_ranges: List[DateRange], 
                                               semaphore: asyncio.Semaphore, listing_metrics_store: Dict):
        """
        Shop reports - try aggregation first, fall back to direct calculation.
        This ensures shop reports are always generated even if listing cache is incomplete.
        """
        async with semaphore:
            try:
                saved_count = 0
                for dr in date_ranges:
                    # IMPORTANT: Use the same key format as calculate_metrics_batch returns
                    period_key = f"{dr.start_date.strftime('%Y-%m-%d')}_to_{dr.end_date.strftime('%Y-%m-%d')}"
                    full_key = f"{period_type}_{period_key}"
                    
                    # TRY 1: Aggregate from listings if we have data
                    aggregated_metrics = None
                    if listing_metrics_store:
                        aggregated_metrics = self._aggregate_from_listings(
                            list(listing_metrics_store.keys()), 
                            full_key, 
                            listing_metrics_store, 
                            dr
                        )
                    
                    # TRY 2: If aggregation failed or no data, calculate directly from transactions
                    if not aggregated_metrics or aggregated_metrics.get('total_orders', 0) == 0:
                        # Direct calculation for shop-level (all transactions)
                        batch_metrics = await self.calculate_metrics_batch([dr])
                        if batch_metrics:
                            # Use the same period_key format that calculate_metrics_batch returns
                            aggregated_metrics = batch_metrics.get(period_key)
                    
                    # Save if we have valid data
                    if aggregated_metrics and aggregated_metrics.get('total_orders', 0) > 0:
                        try:
                            await self.save_shop_report(
                                aggregated_metrics, 
                                period_type,
                                aggregated_metrics['period_start'], 
                                aggregated_metrics['period_end']
                            )
                            saved_count += 1
                        except Exception as save_error:
                            logger.error(f"Failed to save shop report: {save_error}", exc_info=True)
                
                print(f"📊 Shop {period_type.upper()}: Saved {saved_count}/{len(date_ranges)} periods")
                logger.info(f"Shop {period_type.upper()}: Saved {saved_count}/{len(date_ranges)} periods")
            except Exception as e:
                print(f"\n❌ ERROR in _process_shop_reports_aggregated: {e}")
                logger.error(f"Error aggregating shop {period_type}: {e}", exc_info=True)

    def _aggregate_from_skus(self, sku_list: List[str], period_key: str, 
                            sku_store: Dict, date_range: DateRange) -> Dict:
        """Aggregate metrics from SKUs."""
        agg = None
        for sku in sku_list:
            if sku in sku_store and period_key in sku_store[sku]:
                agg = sku_store[sku][period_key].copy() if agg is None else self._sum_metrics(agg, sku_store[sku][period_key])
        if agg:
            agg['period_start'], agg['period_end'] = date_range.start_date, date_range.end_date
        return agg

    def _aggregate_from_listings(self, listing_ids: List[int], period_key: str,
                                listing_store: Dict, date_range: DateRange) -> Dict:
        """Aggregate metrics from listings."""
        agg = None
        for lid in listing_ids:
            if lid in listing_store and period_key in listing_store[lid]:
                agg = listing_store[lid][period_key].copy() if agg is None else self._sum_metrics(agg, listing_store[lid][period_key])
        if agg:
            agg['period_start'], agg['period_end'] = date_range.start_date, date_range.end_date
        return agg

    def _sum_metrics(self, m1: Dict, m2: Dict) -> Dict:
        """Sum metrics for aggregation with corrected Etsy calculations and shipping costs."""
        r = m1.copy()
        
        # Sum all additive fields (including new shipping fields)
        for f in ['gross_revenue', 'total_revenue', 'product_revenue', 'total_shipping_charged', 
                 'total_tax_collected', 'total_vat_collected', 'total_gift_wrap_revenue', 
                 'total_discounts_given', 'etsy_transaction_fees', 'etsy_processing_fees', 
                 'total_etsy_fees', 'net_revenue', 'net_revenue_after_refunds',
                 'actual_shipping_cost', 'shipping_profit', 'duty_amount', 'tax_amount', 'fedex_processing_fee',
                 'total_cost', 'total_cost_with_shipping', 'contribution_margin', 'gross_profit', 'net_profit', 
                 'total_orders', 'total_items', 'total_quantity_sold', 'shipped_orders', 
                 'gift_orders', 'total_refund_amount', 'total_refund_count', 'orders_with_refunds', 
                 'etsy_fees_retained_on_refunds',
                 'cancelled_orders', 'unique_customers', 'repeat_customers', 'total_inventory', 
                 'active_variants']:
            r[f] = r.get(f, 0) + m2.get(f, 0)
        
        # Recalculate all derived metrics (rates, margins, averages)
        gross_revenue = r.get('gross_revenue', 0) or r.get('total_revenue', 0)
        total_orders = r.get('total_orders', 0)
        total_items = r.get('total_items', 0)
        unique_customers = r.get('unique_customers', 0)
        total_cost = r.get('total_cost', 0)
        total_cost_with_shipping = r.get('total_cost_with_shipping', 0)
        gross_profit = r.get('gross_profit', 0)
        net_profit = r.get('net_profit', 0)
        net_revenue = r.get('net_revenue', 0)
        total_etsy_fees = r.get('total_etsy_fees', 0)
        
        # Revenue-based rates
        if gross_revenue > 0:
            r['discount_rate'] = r.get('total_discounts_given', 0) / gross_revenue
            r['gross_margin'] = gross_profit / gross_revenue
            r['net_margin'] = net_profit / gross_revenue
            r['return_on_revenue'] = net_profit / gross_revenue
            r['etsy_fee_rate'] = total_etsy_fees / gross_revenue
            r['take_home_rate'] = net_revenue / gross_revenue
            r['refund_rate_by_value'] = r.get('total_refund_amount', 0) / gross_revenue
        
        # Cost-based ratios (use total_cost_with_shipping for accurate markup)
        if total_cost_with_shipping > 0:
            r['markup_ratio'] = gross_profit / total_cost_with_shipping
        elif total_cost > 0:
            r['markup_ratio'] = gross_profit / total_cost
        
        # Order-based averages
        if total_orders > 0:
            r['average_order_value'] = gross_revenue / total_orders
            r['items_per_order'] = total_items / total_orders
            r['cost_per_order'] = total_cost_with_shipping / total_orders if total_cost_with_shipping > 0 else total_cost / total_orders
            r['refund_rate_by_order'] = r.get('total_refund_count', 0) / total_orders
            r['order_refund_rate'] = r.get('orders_with_refunds', 0) / total_orders
        
        # Item-based averages
        if total_items > 0:
            r['revenue_per_item'] = gross_revenue / total_items
            r['profit_per_item'] = gross_profit / total_items
            r['avg_cost_per_item'] = total_cost / total_items
        
        # Customer-based metrics
        if unique_customers > 0:
            r['revenue_per_customer'] = gross_revenue / unique_customers
            r['orders_per_customer'] = total_orders / unique_customers
            r['profit_per_customer'] = gross_profit / unique_customers
        
        # Period days should stay the same
        r['period_days'] = m1.get('period_days', 0)
        
        return r


async def main():
    """Main execution function with ULTRA-OPTIMIZED batch processing."""
    parser = argparse.ArgumentParser(
        description='⚡ ULTRA-OPTIMIZED E-commerce Analytics - LIGHT SPEED MODE ⚡',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Standard run (updates existing reports)
  python reportsv4_optimized.py --cost-file cost.csv
  
  # Clean slate - delete all reports and start fresh
  python reportsv4_optimized.py --clean-reports
  
  # Fast processing with custom Etsy fees
  python reportsv4_optimized.py --max-concurrent 20 --etsy-transaction-fee 0.05
        """
    )
    
    # File arguments
    parser.add_argument('--cost-file', default='cost.csv',
                       help='Path to cost CSV file (default: cost.csv)')
    
    # Data management arguments
    parser.add_argument('--clean-reports', action='store_true',
                       help='⚠️ DELETE all existing reports before generating new ones (FRESH START)')
    
    # Performance arguments
    parser.add_argument('--max-concurrent', type=int, default=3,
                       help='Maximum concurrent operations (default: 3, safe for connection pool)')
    parser.add_argument('--batch-size', type=int, default=50,
                       help='Batch size for bulk operations (default: 50)')
    
    # Etsy fee configuration
    parser.add_argument('--etsy-transaction-fee', type=float, default=0.065,
                       help='Etsy transaction fee rate (default: 0.065 = 6.5%%)')
    parser.add_argument('--etsy-processing-fee', type=float, default=0.03,
                       help='Etsy payment processing fee rate (default: 0.03 = 3%%)')
    parser.add_argument('--etsy-processing-fixed', type=float, default=0.25,
                       help='Etsy fixed processing fee per order (default: 0.25 USD)')
    
    args = parser.parse_args()
    
    analytics = EcommerceAnalyticsOptimized(
        args.cost_file,
        max_concurrent=args.max_concurrent,
        batch_size=args.batch_size,
        etsy_transaction_fee_rate=args.etsy_transaction_fee,
        etsy_processing_fee_rate=args.etsy_processing_fee,
        etsy_processing_fee_fixed=args.etsy_processing_fixed
    )
    
    print("\n" + "="*80)
    print("⚡⚡⚡ ETSY ANALYTICS ENGINE - CORRECTED CALCULATIONS ⚡⚡⚡")
    print("="*80)
    print(f"🚀 Parallel Operations: {args.max_concurrent}")
    print(f"📦 Batch Size: {args.batch_size}")
    print(f"💰 Etsy Transaction Fee: {args.etsy_transaction_fee*100:.1f}%")
    print(f"💳 Etsy Processing Fee: {args.etsy_processing_fee*100:.1f}% + ${args.etsy_processing_fixed}")
    
    if args.clean_reports:
        print(f"🗑️  Mode: CLEAN & REGENERATE (will delete all existing reports)")
    else:
        print(f"🔄 Mode: UPDATE (will upsert existing reports)")
        
    print("💨 Optimizations: NumPy Vectorization + Parallel Processing + Smart Caching")
    print("⏱️  Expected: 5-10 minutes for 200k orders (vs 4-6 hours sequential)")
    print("\n🔧 NEW: Accurate profit calculations with Etsy fees included!")
    print("="*80 + "\n")
    
    import time
    start_time = time.time()
    
    # Use context manager to ensure connection is ALWAYS closed
    try:
        async with analytics:
            # Run the analysis with clean flag
            result = await analytics.generate_all_insights_batch(clean_old_data=args.clean_reports)
            
            elapsed_time = time.time() - start_time
            
            if result:
                print("\n" + "="*80)
                print("✅✅✅ ANALYSIS COMPLETE! ✅✅✅")
                print("="*80)
                print(f"📊 Processed {result.get('skus', 0)} SKUs")
                print(f"📦 Processed {result.get('listings', 0)} Listings")
                print(f"⏱️  Processed {result.get('periods', 0)} Time Periods")
                print(f"⚡ Total Time: {elapsed_time:.1f} seconds ({elapsed_time/60:.1f} minutes)")
                print(f"🚀 Speed: {result.get('skus', 0) * result.get('periods', 0) / elapsed_time:.1f} calculations/second")
                print("="*80)
                
                # Data Quality Report
                print("\n📋 DATA QUALITY REPORT:")
                print("="*80)
                
                # Skipped products due to missing cost data
                if analytics._skipped_products_no_cost:
                    print(f"⏭️  SKIPPED: {len(analytics._skipped_products_no_cost)} products not recorded")
                    print(f"    Reason: SKU not found in cost.csv OR no cost data for specific months")
                    print(f"    Total reports skipped: {analytics._skipped_count}")
                    if len(analytics._skipped_products_no_cost) <= 20:
                        print(f"    Skipped SKUs: {', '.join(sorted(analytics._skipped_products_no_cost))}")
                    else:
                        sample_skus = sorted(analytics._skipped_products_no_cost)[:20]
                        print(f"    Sample (first 20): {', '.join(sample_skus)}")
                    print(f"    💡 TIP: Add these SKUs to cost.csv to include them in reports")
                    print()
                
                if analytics._missing_cost_skus:
                    print(f"⚠️  WARNING: {len(analytics._missing_cost_skus)} SKUs missing cost data for some periods")
                    print(f"    These were still processed but with $0 cost (profit may be overstated)")
                    if len(analytics._missing_cost_skus) <= 20:
                        print(f"    Missing SKUs: {', '.join(sorted(analytics._missing_cost_skus))}")
                    else:
                        sample_skus = sorted(analytics._missing_cost_skus)[:20]
                        print(f"    Sample (first 20): {', '.join(sample_skus)}")
                    print()
                else:
                    print("✅ All processed SKUs have cost data")
                
                if analytics._currency_warnings_shown:
                    print(f"⚠️  CRITICAL: Multiple currencies detected in {len(analytics._currency_warnings_shown)} periods")
                    print(f"    Financial calculations may be INACCURATE without currency conversion!")
                    print()
                else:
                    print("✅ Single currency used (or no currency issues detected)")
                
                print("="*80)
                print("\n💡 TIP: Compare results with your Etsy Payment Account to verify accuracy!")
                print("="*80)
            else:
                print("❌ Analysis failed")
        
    except KeyboardInterrupt:
        print("\n⏸️  Process interrupted by user.")
        # Context manager will handle disconnect automatically
    except Exception as e:
        logger.error(f"Critical error: {e}", exc_info=True)
        print(f"❌ Error: {e}")
        # Context manager will handle disconnect automatically


if __name__ == "__main__":
    asyncio.run(main())
