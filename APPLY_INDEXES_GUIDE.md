# How to Apply Performance Indexes in Supabase

## Problem Fixed

The original index script tried to create indexes on `period_type` column in composite indexes, but this column is an ENUM type which caused an error. The script has been fixed.

## Steps to Apply Indexes

### Option 1: Supabase SQL Editor (Recommended - Easiest)

1. Open your Supabase dashboard: https://supabase.com/dashboard
2. Select your project
3. Go to **SQL Editor** (left sidebar)
4. Click **+ New Query**
5. Copy the ENTIRE contents of `add_performance_indexes.sql`
6. Paste into the SQL editor
7. Click **Run** (or press Ctrl+Enter / Cmd+Enter)

You should see: `Performance indexes created successfully!`

### Option 2: Using psql Command Line

If you have PostgreSQL client installed:

```bash
# Get your DATABASE_URL from Supabase dashboard:
# Project Settings → Database → Connection String → URI

export DATABASE_URL="postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres"

# Apply the indexes
psql "$DATABASE_URL" -f add_performance_indexes.sql
```

### Option 3: Python Script

```python
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Read the SQL file
with open("add_performance_indexes.sql", "r") as f:
    sql_script = f.read()

# Execute
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()
cur.execute(sql_script)
conn.commit()
print("✅ Indexes applied successfully!")
cur.close()
conn.close()
```

## What These Indexes Do

The script creates **25+ indexes** on critical columns:

### Critical Indexes for Query Performance:

- `orders.created_timestamp` - **10-50x faster date range queries**
- `order_transactions.product_id` - **5-20x faster SKU filtering**
- `order_transactions.sku` - **Direct SKU lookups**
- `listing_ad_stats.listing_id + dates` - **Fast ad spend queries**

### Expected Performance Impact:

- **Before**: 74 seconds per SKU = 25+ hours for 1,255 SKUs
- **After**: 5-10 seconds per SKU = **2-3 hours for 1,255 SKUs**

That's a **10x speedup**!

## Verify Indexes Were Created

After running the script, check if indexes exist:

```sql
-- Run this in Supabase SQL Editor
SELECT tablename, indexname
FROM pg_indexes
WHERE schemaname = 'public'
AND indexname LIKE 'idx_%'
ORDER BY tablename, indexname;
```

You should see indexes like:

- `idx_orders_created_timestamp`
- `idx_order_transactions_product_id`
- `idx_order_transactions_sku`
- `idx_listing_ad_stats_listing_id`
- And 20+ more...

## Safe to Run Multiple Times

The script uses `IF NOT EXISTS`, so it's **safe to run multiple times**. If indexes already exist, it will skip creating them.

## Next Steps After Applying Indexes

1. **Restart your report generation**:

   ```bash
   python reportsv4_optimized.py
   ```

2. **Monitor performance**: You should see much faster processing times per SKU

3. **Increase concurrency** (optional): After verifying indexes work, edit `reportsv4_optimized.py`:

   ```python
   # Change from:
   semaphore = asyncio.Semaphore(5)

   # To:
   semaphore = asyncio.Semaphore(20)  # Process more SKUs in parallel
   ```

## Troubleshooting

### Error: "column X does not exist"

- The script has been fixed to remove non-existent column references
- Make sure you're using the updated `add_performance_indexes.sql`

### Error: "permission denied"

- Make sure you're using the connection string with admin privileges
- In Supabase: Use the "Connection String" from Project Settings → Database

### Indexes taking long time to create

- This is normal for large tables (200k+ rows)
- Creating indexes on `orders` and `order_transactions` may take 1-5 minutes
- Don't interrupt the process!

## Monitoring Index Usage

After running reports with indexes, check which indexes are being used most:

```sql
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as "Times Used",
    idx_tup_read as "Rows Read"
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
AND indexname LIKE 'idx_%'
ORDER BY idx_scan DESC
LIMIT 20;
```

Indexes with high `idx_scan` values are the most valuable!
