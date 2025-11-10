# Zero Total Cost Investigation Guide

## Problem Statement

Reports in the database show `totalCost = 0.0` even though transactions exist and cost.csv has data.

## Root Causes Identified

### 1. Missing Cost Data in cost.csv

**Symptom:** SKU exists in database but has no cost entry for specific months

**Example:**

- Database has sales for `GeLet-Fujifilm-XT3-Black` in November 2024
- cost.csv is missing column `"US KASIM 2024"` or `"US KASIM 24"`
- Result: Cost lookup returns 0.0

**Solution:**

1. Check which SKUs/months are missing:
   ```bash
   python reportsv4_optimized.py --only-products 2>&1 | grep "Missing cost:"
   ```
2. Update cost.csv with missing data:
   - Add column: `"US KASIM 2024"` (or `"US KASIM 24"`)
   - Add cost for each missing SKU

**Prevention:**

- Ensure cost.csv is updated monthly
- Use column format: `"US {MONTH} {YEAR}"` where MONTH is Turkish (OCAK, SUBAT, MART, etc.)

---

### 2. SKU Format Mismatch

**Symptom:** SKU in transactions doesn't match SKU in cost.csv

**Example:**

- Transaction: `"OT-GeLet-Fujifilm-XT3-Black"`
- cost.csv: `"GeLet-Fujifilm-XT3-Black"`
- Result: Lookup fails, returns 0.0

**Solution:**
Already implemented! Code automatically normalizes SKUs by removing prefixes:

- `OT-`, `ZSTK-`, `DELETED-`, `ZSTK-DELETED-`, etc.

**Verify:**
Check logs for normalization:

```
→ Sample SKUs in mapping: ['GeLet-Fujifilm-XT3-Black', 'MacBag-L-Red', ...]
```

---

### 3. Cost Fallback Not Triggered

**Symptom:** Primary SKU has no cost, but sibling SKUs do (should use fallback)

**Example:**

- Listing 123 has variants:
  - `GeLet-Fujifilm-XT3-Black` (no cost)
  - `GeLet-Fujifilm-XT3-Silver` (has cost: $45.00)
- Without fallback: returns 0.0
- With fallback: returns $45.00 from sibling

**How Fallback Works:**

1. **Level 1:** Direct lookup for this SKU + date
2. **Level 2:** Check sibling SKUs in same listing for same date
3. **Level 3:** Check sibling SKUs for historical dates (up to 24 months back)
4. **Level 4:** Return 0.0 if no cost found

**Check Fallback Stats:**
At end of script run, look for:

```
Cost fallback statistics:
  Direct lookups: 85.3% (1234 items)
  Sibling same period: 10.2% (148 items)
  Sibling historical: 3.1% (45 items)
  Missing costs: 1.4% (20 items)  ← This should be LOW
```

**If "Missing costs" is high:**

- Fallback isn't working
- Check if `listing_id` is available in transactions
- Verify listings have multiple products (variants)

---

### 4. CSV Column Format Issues

**Symptom:** Cost exists but column name doesn't match expected format

**Formats Tried (in order):**

1. `"US MAYIS 2025"` (full 4-digit year)
2. `"US MART 25"` (2-digit year)
3. `"US 2024 NISAN"` (year before month)
4. `"US 25 MART"` (2-digit year before month)
5. `"US MART25"` (no space)
6. `"US25 MART"` (no space)
7. `"US MART"` (no year)

**With suffixes:**

- `"US MART 2024 CALISMA"`
- `"US MART 2024 ÇALIŞMA"`

**Common Issues:**

- Month name in English instead of Turkish
- Missing space between parts
- Wrong year format (2-digit vs 4-digit)
- Typo in month name

**Turkish Month Names:**

```python
OCAK (January)    TEMMUZ (July)
SUBAT (February)  AGUSTOS (August)
MART (March)      EYLUL (September)
NISAN (April)     EKIM (October)
MAYIS (May)       KASIM (November)
HAZIRAN (June)    ARALIK (December)
```

---

## Enhanced Logging (NEW)

Now the script logs detailed cost coverage information:

### Example Log Output:

```
WARNING: Cost coverage: 67.5% (540/800 items). Missing costs for 12 SKU instances. Period: 2024-11-01 to 2024-11-30
WARNING:   Missing cost: SKU=GeLet-Fujifilm-XT3-Black, Qty=15, Date=2024-11, ListingID=123456
WARNING:   Missing cost: SKU=MacBag-L-Red, Qty=8, Date=2024-11, ListingID=789012
WARNING:   Missing cost: SKU=Portfolio-A4-Blue, Qty=5, Date=2024-11, ListingID=345678
```

### What This Tells You:

- **67.5% coverage:** 540 items have costs, 260 items don't
- **12 SKU instances:** 12 different SKU-date combinations are missing
- **Specific examples:** Shows first 3 missing SKUs with details

---

## Diagnostic Steps

### Step 1: Run Report Generation

```bash
python reportsv4_optimized.py --only-products 2>&1 | tee report_log.txt
```

### Step 2: Check Logs for Warnings

```bash
grep "Cost coverage:" report_log.txt
grep "Missing cost:" report_log.txt
```

### Step 3: Verify Database Results

```python
# In Python shell or script:
from prisma import Prisma
import asyncio

async def check_costs():
    prisma = Prisma()
    await prisma.connect()

    # Find reports with zero cost
    zero_cost_reports = await prisma.productreport.find_many(
        where={"totalCost": 0.0},
        take=10
    )

    for report in zero_cost_reports:
        print(f"SKU: {report.sku}, Period: {report.periodStart} to {report.periodEnd}")

    await prisma.disconnect()

asyncio.run(check_costs())
```

### Step 4: Check cost.csv for Missing Data

```python
import pandas as pd

# Load cost.csv
df = pd.read_csv('cost.csv')

# Check if SKU exists
sku = "GeLet-Fujifilm-XT3-Black"
if sku in df['SKU'].values:
    print(f"✅ SKU '{sku}' found in cost.csv")

    # Check for specific month
    month_col = "US KASIM 2024"
    if month_col in df.columns:
        cost = df[df['SKU'] == sku][month_col].iloc[0]
        print(f"✅ Cost for {month_col}: ${cost}")
    else:
        print(f"❌ Column '{month_col}' not found")
        print(f"Available columns: {[c for c in df.columns if 'KASIM' in c or '2024' in c]}")
else:
    print(f"❌ SKU '{sku}' not found in cost.csv")
```

### Step 5: Verify Fallback Logic

```bash
# Look for fallback usage in logs
grep "sibling" report_log.txt
grep "historical" report_log.txt
```

---

## Solutions Checklist

- [ ] **Update cost.csv**

  - [ ] Add missing month columns
  - [ ] Use correct format: `"US {TURKISH_MONTH} {YEAR}"`
  - [ ] Fill in costs for all SKUs
  - [ ] Remove duplicate/typo columns

- [ ] **Verify SKU Names**

  - [ ] Check SKUs in cost.csv match database (after normalization)
  - [ ] Remove unnecessary prefixes from cost.csv if present

- [ ] **Enable Fallback**

  - [ ] Ensure listings have `listing_id` in transactions
  - [ ] Verify variants exist for products
  - [ ] Check sibling SKUs have costs

- [ ] **Monitor Coverage**
  - [ ] Run with new logging
  - [ ] Target: >95% cost coverage
  - [ ] Fix remaining missing costs manually

---

## Quick Fix for Immediate Results

If you need reports NOW and can't update cost.csv:

### Option 1: Use Last Known Cost

If a product had cost $50 in October but no cost in November, the fallback should find October's cost.

**Check:** Is historical fallback working?

```bash
grep "sibling_historical" report_log.txt
```

### Option 2: Add Generic Month Columns

If specific months are missing, try adding generic columns:

- `"US COST"` (no month/year)
- Copy from most recent month

### Option 3: Skip Cost Validation (NOT RECOMMENDED)

Only if absolutely necessary for testing:

```python
# In _calculate_metrics_from_rows(), line ~1850
# Change:
if cost > 0:
    total_cost += cost * quantity

# To:
# Accept any cost, even 0 (NOT RECOMMENDED FOR PRODUCTION)
total_cost += cost * quantity  # Remove the if check
```

---

## Expected Results After Fixes

### Before:

```
Cost coverage: 45.2% (120/265 items). Missing costs for 145 SKU instances.
Total cost: $1,234.56
Reports with zero cost: 45 out of 100
```

### After:

```
Cost coverage: 98.7% (262/265 items). Missing costs for 3 SKU instances.
Total cost: $12,456.78
Reports with zero cost: 0 out of 100
```

---

## Support

If costs are still zero after following this guide:

1. Share the log output: `grep -A 5 "Cost coverage:" report_log.txt`
2. Share cost.csv column headers: `head -1 cost.csv`
3. Share specific missing SKU example
4. Run diagnostic script above and share results
