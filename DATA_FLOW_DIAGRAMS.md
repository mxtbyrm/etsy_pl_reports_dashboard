# Data Flow Diagram

## Current System (What You Have)

```
┌────────────────────────────────────────────────────────────────────┐
│                        PostgreSQL Database                          │
│                                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   orders    │  │  listings   │  │  products   │              │
│  │             │  │             │  │             │              │
│  │  ✓ Live     │  │  ✓ Live     │  │  ✓ Live     │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
│         ↓                 ↓                 ↓                      │
│         └─────────────────┴─────────────────┘                      │
│                          │                                         │
│                          │                                         │
│         ┏━━━━━━━━━━━━━━━━┷━━━━━━━━━━━━━━━━┓                       │
│         ┃  calculate_metrics_batch()      ┃                       │
│         ┃  (Analytics Engine)              ┃                       │
│         ┃  - Fetches orders                ┃                       │
│         ┃  - Calculates ALL metrics        ┃                       │
│         ┃  - Returns results in memory     ┃                       │
│         ┗━━━━━━━━━━━━━━┯━━━━━━━━━━━━━━━━━━┛                       │
│                        │                                           │
│         ┌──────────────┴──────────────┐                           │
│         │                              │                           │
│         ↓                              ↓                           │
│  ┌──────────────┐              ┌──────────────┐                  │
│  │  Dashboard   │              │   Reports    │                  │
│  │              │              │   Script     │                  │
│  │  ✓ Real-time │              │  ✓ Batch     │                  │
│  │  ✓ Live data │              │  ✓ Scheduled │                  │
│  │  ✓ Any range │              │  ✓ Periods   │                  │
│  └──────────────┘              └──────┬───────┘                  │
│                                        │                           │
│                                        │ Saves                    │
│                                        ↓                           │
│                          ┌──────────────────────┐                │
│                          │  shop_reports        │                │
│                          │  listing_reports     │                │
│                          │  product_reports     │                │
│                          │                      │                │
│                          │  ✗ NOT used by       │                │
│                          │    dashboard         │                │
│                          └──────────────────────┘                │
└────────────────────────────────────────────────────────────────────┘
```

## Dashboard Flow (What Happens When You View Dashboard)

```
┌─────────────────────────────────────────────────────────────────┐
│                    User Opens Dashboard                         │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Connect to Database                          │
│  - Load SKU mappings (listing_products)                         │
│  - Load inventory (product_offerings)                           │
│  ✗ Does NOT load any reports                                    │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│              User Selects Date Range                            │
│              (e.g., Last 30 Days)                               │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│           Call: calculate_metrics_batch([date_range])           │
│                                                                  │
│  This function:                                                 │
│  1. Queries orders table for date range                         │
│  2. Joins with order_transactions                               │
│  3. Joins with order_refunds                                    │
│  4. Calculates ALL metrics (revenue, profit, margins, etc.)     │
│  5. Returns results as Python dictionary                        │
│                                                                  │
│  SQL Query looks like:                                          │
│  SELECT * FROM orders o                                         │
│  WHERE o.created_timestamp BETWEEN start AND end                │
│  LEFT JOIN order_transactions ot ON ...                         │
│  LEFT JOIN order_refunds r ON ...                               │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│              Display Metrics in Dashboard                       │
│  - Revenue charts                                               │
│  - Profit breakdowns                                            │
│  - Customer metrics                                             │
│  - All calculated fresh, in real-time                           │
└─────────────────────────────────────────────────────────────────┘
```

## Reports Script Flow (Separate, Independent)

```
┌─────────────────────────────────────────────────────────────────┐
│              User Runs: python reportsv4_optimized.py           │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│              Connect to Database                                │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│         Generate Date Ranges (Daily, Weekly, Monthly, etc.)     │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│      For each date range:                                       │
│      - Call: calculate_metrics_batch([date_range])              │
│      - Get metrics dictionary                                   │
│      - Save to shop_reports table                               │
│      - Save to listing_reports table                            │
│      - Save to product_reports table                            │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│              Historical Data Saved to Database                  │
│  (Can be used for trend analysis, forecasting, etc.)            │
└─────────────────────────────────────────────────────────────────┘
```

## Key Takeaways

1. **Dashboard** = Real-time calculator (no reports needed)
2. **Reports Script** = Historical recorder (saves for later)
3. **Both use same engine** = `calculate_metrics_batch()`
4. **Both are independent** = Can run separately
5. **Dashboard NEVER reads reports tables** = Always calculates fresh

## What Gets Queried

### Dashboard Queries:

```sql
-- This is what the dashboard does
SELECT * FROM orders WHERE created_timestamp BETWEEN ? AND ?
JOIN order_transactions ON ...
JOIN order_refunds ON ...
-- Then calculates metrics in Python
```

### Reports Script Queries:

```sql
-- This is what reports script does
-- Step 1: Same as dashboard
SELECT * FROM orders WHERE created_timestamp BETWEEN ? AND ?
JOIN order_transactions ON ...
JOIN order_refunds ON ...

-- Step 2: Save results
INSERT INTO shop_reports (period_type, start_date, end_date, metrics)
VALUES ('daily', '2024-01-01', '2024-01-01', {...})
```

### Dashboard Does NOT Do:

```sql
-- Dashboard NEVER does this:
SELECT * FROM shop_reports WHERE ...
SELECT * FROM listing_reports WHERE ...
SELECT * FROM product_reports WHERE ...
```
