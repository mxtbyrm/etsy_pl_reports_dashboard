# Analytics System Architecture

## Overview

This project consists of two independent but complementary components:

## 1. 📊 **Dashboard** (`dashboard.py`)

### Purpose: Real-time Analytics Interface

**What it does:**

- Provides interactive web interface for viewing analytics
- Calculates metrics **on-the-fly** from live database data
- Shows always up-to-date, real-time information

**Data Sources:**

- ✅ Fetches `orders` table (transactions data)
- ✅ Fetches `listing_products` table (SKU mappings)
- ✅ Fetches `product_offerings` table (inventory data)
- ✅ Fetches `order_refunds` table (refund data)
- ❌ Does NOT fetch `shop_reports`, `listing_reports`, or `product_reports`

**How it works:**

1. User selects a date range
2. Dashboard queries orders from database for that date range
3. Analytics engine calculates all metrics in memory
4. Results displayed immediately

**Performance:**

- Uses optimized SQL queries
- Parallel processing with asyncio
- LRU caching for frequently accessed data
- Typically fast enough for interactive use

**Use when:**

- You need to see latest data immediately
- You want to explore different date ranges interactively
- You need custom time periods not in pre-generated reports

---

## 2. 📝 **Reports Script** (`reportsv4_optimized.py`)

### Purpose: Batch Report Generation & Historical Storage

**What it does:**

- Generates comprehensive reports for predefined time periods
- Saves calculated metrics to database for historical tracking
- Runs on a schedule (e.g., nightly) to build historical data

**Data Flow:**

1. Fetches orders data from database
2. Calculates metrics for all time periods (daily, weekly, monthly, quarterly, yearly)
3. Saves results to `shop_reports`, `listing_reports`, `product_reports` tables
4. Historical data can be queried for trend analysis

**Output Tables:**

- `shop_reports` - Shop-wide metrics by time period
- `listing_reports` - Per-listing metrics by time period
- `product_reports` - Per-SKU metrics by time period

**Use when:**

- You need to track historical performance over time
- You want pre-calculated metrics for fast querying
- You're building trend reports or forecasting models
- You need to preserve point-in-time snapshots

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     PostgreSQL Database                      │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   orders     │  │   listings   │  │   products   │     │
│  │              │  │              │  │              │     │
│  │  (Raw Data)  │  │  (Raw Data)  │  │  (Raw Data)  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│         │                  │                  │             │
│         └──────────────────┴──────────────────┘             │
│                          │                                  │
│                          │ Fetched by both                 │
│                          ▼                                  │
│         ┌────────────────────────────────┐                 │
│         │  Analytics Engine (Shared)     │                 │
│         │  calculate_metrics_batch()     │                 │
│         └────────────────────────────────┘                 │
│                    │            │                           │
│        Used by     │            │   Saves to               │
│        Dashboard   │            │   Reports Script         │
│                    ▼            ▼                           │
│         ┌──────────────┐  ┌──────────────┐               │
│         │  Dashboard   │  │   Reports    │               │
│         │  (Real-time) │  │  (Historical)│               │
│         └──────────────┘  └──────────────┘               │
│                                  │                          │
│                                  │ Saves                   │
│                                  ▼                          │
│                    ┌──────────────────────┐               │
│                    │  shop_reports        │               │
│                    │  listing_reports     │               │
│                    │  product_reports     │               │
│                    └──────────────────────┘               │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Differences

| Feature          | Dashboard               | Reports Script      |
| ---------------- | ----------------------- | ------------------- |
| **Data Source**  | Orders (live)           | Orders (live)       |
| **Calculation**  | Real-time               | Batch/scheduled     |
| **Storage**      | None (in-memory)        | Database tables     |
| **Speed**        | Fast (< 5 sec)          | Slow (minutes)      |
| **Flexibility**  | Any date range          | Predefined periods  |
| **Use Case**     | Interactive exploration | Historical tracking |
| **Dependencies** | None                    | None (independent)  |

---

## Usage Recommendations

### Use Dashboard When:

- ✅ You need to check today's performance
- ✅ You want to analyze a custom date range
- ✅ You need immediate answers
- ✅ You're exploring data interactively

### Use Reports Script When:

- ✅ You need to build historical database
- ✅ You want to preserve point-in-time metrics
- ✅ You're doing trend analysis
- ✅ You need consistent period definitions
- ✅ You want to reduce calculation overhead for common queries

### Use Both:

The systems complement each other:

1. **Run reports script nightly** to build historical data
2. **Use dashboard during the day** for real-time insights
3. **Query report tables** for historical analysis
4. **Use dashboard** for custom date ranges not in reports

---

## Shared Components

Both systems use:

- **Same analytics engine** (`EcommerceAnalyticsOptimized`)
- **Same calculation logic** (`calculate_metrics_batch()`)
- **Same CSV files** (cost.csv, desi.csv, fedex data, etc.)
- **Same database connection** (Prisma client)

This ensures consistency - metrics calculated by dashboard match those saved by reports script.

---

## Performance Notes

### Dashboard Performance:

- Optimized for interactive use
- Uses connection pooling
- Caches frequently accessed data
- Parallel query execution
- Typical response: 2-5 seconds for 30-day period

### Reports Script Performance:

- Optimized for batch processing
- Processes multiple periods in parallel
- Bulk database inserts
- Progress tracking with tqdm
- Typical runtime: 5-15 minutes for all reports

---

## Data Independence

**Important:** Both systems are **independent**:

- Dashboard does NOT require reports script to have run
- Reports script does NOT affect dashboard functionality
- Either can be used standalone
- No coupling between them

They simply share the same underlying data (orders, listings) and calculation engine.
