# 💰 Complete Cost Types Audit - All Report Types

## 📊 Executive Summary

This document provides a comprehensive audit of ALL cost types tracked across Product, Listing, and Shop reports in the Etsy analytics system.

---

## 🎯 Cost Categories Overview

### 1. **Product Costs (COGS - Cost of Goods Sold)**

- ✅ **Tracked**: `total_cost`
- ✅ **Source**: `cost.csv` with SKU-specific costs by region/month
- ✅ **Fallback Strategy**: 3-level fallback (direct → sibling SKU → historical)
- ✅ **Included in**: Product, Listing, Shop reports

### 2. **Shipping Costs**

#### a. FedEx Shipping Charges

- ✅ **Tracked**: `actual_shipping_cost`
- ✅ **Source**: Zone-based pricing from `fedex_price_per_kg_for_zones.csv`
- ✅ **Calculation**: Weight (desi) × Zone rate
- ✅ **Included in**: Product, Listing, Shop reports

#### b. US Import Duties

- ✅ **Tracked**: `duty_amount`
- ✅ **Source**: `us_fedex_desi_and_price.csv` (rate or pre-calculated amount)
- ✅ **Calculation**: Item price × duty_rate (or fixed amount)
- ✅ **Included in**: Product, Listing, Shop reports

#### c. US Import Taxes

- ✅ **Tracked**: `tax_amount`
- ✅ **Source**: `us_fedex_desi_and_price.csv` (rate or pre-calculated amount)
- ✅ **Calculation**: Item price × tax_rate (or fixed amount)
- ✅ **Included in**: Product, Listing, Shop reports

#### d. FedEx Processing Fees

- ✅ **Tracked**: `fedex_processing_fee`
- ✅ **Source**: `us_fedex_desi_and_price.csv`
- ✅ **Included in**: Product, Listing, Shop reports

### 3. **Etsy Platform Fees**

#### a. Transaction Fees (6.5%)

- ✅ **Tracked**: `etsy_transaction_fees`
- ✅ **Calculation**: `gross_revenue × 0.065`
- ✅ **Included in**: Product, Listing, Shop reports

#### b. Processing Fees (3% + $0.25)

- ✅ **Tracked**: `etsy_processing_fees`
- ✅ **Calculation**: `(gross_revenue × 0.03) + 0.25`
- ✅ **Included in**: Product, Listing, Shop reports

#### c. Etsy Fees Retained on Refunds

- ✅ **Tracked**: `etsy_fees_retained_on_refunds`
- ✅ **Note**: Etsy KEEPS transaction fees when you refund, additional cost!
- ✅ **Calculation**: `total_refund_amount × 0.065`
- ✅ **Included in**: Product, Listing, Shop reports

### 4. **Advertising Spend**

#### a. Shop Level

- ✅ **Tracked**: `total_ad_spend`
- ✅ **Source**: `listing_ad_stats` table (aggregated from all listings)
- ✅ **Included in**: Shop reports

#### b. Listing Level

- ✅ **Tracked**: `total_ad_spend`
- ✅ **Source**: `listing_ad_stats` table (for specific listing)
- ✅ **Included in**: Listing reports

#### c. Product Level (Proportional Allocation)

- ❌ **NOT TRACKED** in database schema
- ✅ **Calculated** in metrics but **NOT SAVED** to database
- ⚠️ **Issue**: `ProductReport` schema missing ad spend fields
- ✅ **Allocation Logic**: Proportional by revenue contribution to parent listing

### 5. **Refund Costs**

- ✅ **Tracked**: `total_refund_amount`
- ✅ **Tracked**: `total_refund_count`
- ✅ **Tracked**: `orders_with_refunds`
- ✅ **Included in**: Product, Listing, Shop reports

---

## 📈 Profit Calculation Flow

### **Gross Revenue** (What customers pay us)

```
= Order Total (grand_total from Etsy)
= Product Price + Shipping Charged + Taxes Collected + VAT Collected + Gift Wrap
```

### **Net Revenue** (After Etsy takes their cut)

```
= Gross Revenue
  - Etsy Transaction Fees (6.5%)
  - Etsy Processing Fees (3% + $0.25)
  - Taxes Collected (passed to government)
```

### **Total Costs with Shipping**

```
= Product Costs (COGS from cost.csv)
  + Actual Shipping Cost (FedEx charges)
  + US Import Duties (customs fees)
  + US Import Tax (import taxes)
  + FedEx Processing Fees
```

### **Gross Profit** (Before refunds and ads)

```
= Net Revenue - Total Costs with Shipping
```

### **Net Profit** (Final bottom line)

```
= Gross Profit
  - Total Refund Amount
  - Etsy Fees Retained on Refunds
  - Advertising Spend
```

---

## 🔍 Schema Comparison

### ✅ **ShopReport** - Complete (All costs tracked)

- ✅ Product costs
- ✅ Shipping costs (all 4 types)
- ✅ Etsy fees (all 3 types)
- ✅ Ad spend (`totalAdSpend`, `adSpendRate`, `roas`)
- ✅ Refunds

### ✅ **ListingReport** - Complete (All costs tracked)

- ✅ Product costs
- ✅ Shipping costs (all 4 types)
- ✅ Etsy fees (all 3 types)
- ✅ Ad spend (`totalAdSpend`, `adSpendRate`, `roas`)
- ✅ Refunds

### ⚠️ **ProductReport** - MISSING Ad Spend Fields!

- ✅ Product costs
- ✅ Shipping costs (all 4 types)
- ✅ Etsy fees (all 3 types)
- ❌ **MISSING**: `totalAdSpend`
- ❌ **MISSING**: `adSpendRate`
- ❌ **MISSING**: `roas`
- ✅ Refunds

---

## 🚨 Critical Issues Found

### 1. **ProductReport Missing Ad Spend Fields**

**Problem**:

- Metrics are CALCULATED (lines 2588-2590 in reportsv4_optimized.py)
- But NOT SAVED to database (missing from schema & save function)
- This means product-level ad spend analysis is impossible from database

**Evidence**:

```python
# In metrics calculation (line 2588-2590):
"total_ad_spend": round(total_ad_spend, 2),
"ad_spend_rate": round(total_ad_spend / gross_revenue, 4) if gross_revenue > 0 else 0,
"roas": round(gross_revenue / total_ad_spend, 2) if total_ad_spend > 0 else 0,

# In save_product_report (lines 3522-3630):
# ❌ These fields are NOT included in payload!
```

**Impact**:

- Cannot analyze ad performance at product level
- Cannot see which products benefit most from ads
- Cannot calculate accurate product-level net profit including ad costs
- Dashboard/reports cannot show product-level ROAS

**Fix Required**:

1. Add fields to `ProductReport` schema in `prisma/schema.prisma`:

   ```prisma
   totalAdSpend    Float @default(0) @map("total_ad_spend")
   adSpendRate     Float @default(0) @map("ad_spend_rate")
   roas            Float @default(0)
   ```

2. Add fields to `save_product_report` payload (line ~3630):

   ```python
   "totalAdSpend": self._clean_metric_value(metrics.get("total_ad_spend", 0)),
   "adSpendRate": self._clean_metric_value(metrics.get("ad_spend_rate", 0)),
   "roas": self._clean_metric_value(metrics.get("roas", 0)),
   ```

3. Run migration:
   ```bash
   npx prisma migrate dev --name add_ad_spend_to_product_reports
   ```

---

## ✅ What's Working Well

### 1. **Comprehensive Cost Tracking**

- All major cost types are captured in metrics calculation
- Proper separation of revenue vs costs
- Accurate shipping cost calculations (zone-based + weight-based)

### 2. **Multi-Level Cost Fallback**

- Direct SKU cost lookup
- Sibling SKU fallback (same listing)
- Historical cost fallback (previous periods)
- Variant-aware (size/material specific)

### 3. **Shipping Cost Accuracy**

- Country-specific calculations
- US orders: Separate duty/tax calculation
- International: Zone-based FedEx pricing
- Per-item weight calculations

### 4. **Etsy Fee Accuracy**

- Transaction fees (6.5%)
- Processing fees (3% + $0.25)
- Fees retained on refunds (often forgotten but critical!)

### 5. **Ad Spend Allocation**

- Shop level: Full ad spend included
- Listing level: Listing-specific ad spend
- Product level: Proportional by revenue share (calculated correctly)

---

## 📋 Cost Tracking Status Matrix

| Cost Type                 | Product Reports  | Listing Reports | Shop Reports | Source           |
| ------------------------- | ---------------- | --------------- | ------------ | ---------------- |
| **Product Costs (COGS)**  | ✅ Saved         | ✅ Saved        | ✅ Saved     | cost.csv         |
| **FedEx Shipping**        | ✅ Saved         | ✅ Saved        | ✅ Saved     | Zone pricing     |
| **US Import Duties**      | ✅ Saved         | ✅ Saved        | ✅ Saved     | US FedEx CSV     |
| **US Import Taxes**       | ✅ Saved         | ✅ Saved        | ✅ Saved     | US FedEx CSV     |
| **FedEx Processing Fees** | ✅ Saved         | ✅ Saved        | ✅ Saved     | US FedEx CSV     |
| **Etsy Transaction Fees** | ✅ Saved         | ✅ Saved        | ✅ Saved     | 6.5% calculation |
| **Etsy Processing Fees**  | ✅ Saved         | ✅ Saved        | ✅ Saved     | 3% + $0.25       |
| **Etsy Fees on Refunds**  | ✅ Saved         | ✅ Saved        | ✅ Saved     | 6.5% of refunds  |
| **Advertising Spend**     | ❌ **NOT SAVED** | ✅ Saved        | ✅ Saved     | listing_ad_stats |
| **Refunds**               | ✅ Saved         | ✅ Saved        | ✅ Saved     | order_refunds    |

---

## 🎯 Recommendations

### High Priority

1. **Add ad spend fields to ProductReport schema** - Critical for complete product profitability analysis
2. **Run Prisma migration** - Update database structure
3. **Verify product-level net profit** - Ensure it includes ad costs after fix

### Medium Priority

4. **Add ROAS benchmarks** - Define good/bad ROAS thresholds per category
5. **Create cost allocation report** - Show breakdown of all cost types
6. **Add cost trend analysis** - Track cost changes over time

### Low Priority

7. **Add cost coverage warnings** - Alert when cost data is incomplete
8. **Create cost efficiency metrics** - Cost per order, cost per customer, etc.
9. **Add cost forecasting** - Predict future costs based on trends

---

## 📝 Testing Checklist

After adding ad spend to ProductReport:

- [ ] Verify ad spend is saved to database for product reports
- [ ] Check product net profit includes ad costs
- [ ] Validate ROAS calculation at product level
- [ ] Test proportional ad allocation logic
- [ ] Verify ad spend sums correctly (product → listing → shop)
- [ ] Check dashboard displays product ad metrics
- [ ] Test edge cases (no ad spend, high ad spend, etc.)

---

## 🔗 Related Files

- **Schema**: `prisma/schema.prisma` (lines 546-640 for ProductReport)
- **Metrics Calculation**: `reportsv4_optimized.py` (lines 2240-2650)
- **Save Function**: `reportsv4_optimized.py` (lines 3522-3630)
- **Cost CSVs**:
  - `cost.csv` - Product costs
  - `us_fedex_desi_and_price.csv` - US shipping/duties/taxes
  - `fedex_price_per_kg_for_zones.csv` - International shipping
  - `fedex_country_code_and_zone_number.csv` - Zone mapping

---

**Last Updated**: November 10, 2025  
**Status**: ⚠️ Action Required - Add ad spend to ProductReport schema
