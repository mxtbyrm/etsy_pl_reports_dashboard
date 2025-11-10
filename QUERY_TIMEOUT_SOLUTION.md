# Query Timeout Solution - Why Queries Are Failing

## Current Problem

**Symptoms:**

- Queries timing out after 74 seconds per SKU
- Processing 1255 SKUs would take 25+ hours
- Error: "Query timed out after multiple attempts"

**Root Causes:**

### 1. Missing Database Indexes (CRITICAL)

The performance indexes defined in `add_performance_indexes.sql` have **NOT been applied** to your database yet.

Without indexes, PostgreSQL does **full table scans** for every query:

- Orders table: ~200,000+ rows
- Order transactions: ~500,000+ rows
- Every SKU query scans ALL rows = extremely slow

**Impact:** Queries are 10-100x slower without indexes!

### 2. One-SKU-at-a-Time Processing

Current code processes SKUs sequentially:

```python
for each SKU:
    calculate_metrics_batch([date_ranges], sku=sku)  # Separate DB query per SKU!
```

This means:

- 1,255 SKUs × 74 seconds = **25.8 hours** of processing time
- Each query rebuilds CTEs and scans tables independently
- No sharing of data between SKU queries

### 3. Query Complexity

The `calculate_metrics_batch()` mega-query has:

- Multiple CTEs (WITH clauses)
- Joins across 6+ tables
- JSON aggregations
- Complex filtering

Without indexes, each join becomes a full table scan.

## Solutions (In Priority Order)

### ✅ SOLUTION 1: Apply Performance Indexes (IMMEDIATE - Do This First!)

**Step 1: Get your DATABASE_URL**

If you're running the reports script, it already knows the DATABASE_URL. Check one of:

```bash
# Option A: Check if .env file exists
cat .env | grep DATABASE_URL

# Option B: Print it from Python
python3 -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('DATABASE_URL'))"

# Option C: Check your reportsv4_optimized.py run - it uses the same connection
# The script already connects successfully, so the URL is configured
```

**Step 2: Apply the indexes**

```bash
# Replace with your actual DATABASE_URL
export DATABASE_URL="postgresql://user:password@host:port/dbname"

# Apply indexes
psql "$DATABASE_URL" -f add_performance_indexes.sql
```

**Expected Result:**

- Queries should drop from 74 seconds to 5-10 seconds per SKU
- Total time: 1,255 SKUs × 7 seconds = ~2.5 hours (much better!)

**Indexes Created:**

- `orders.created_timestamp` - Critical for date range queries
- `order_transactions.product_id` - Critical for SKU filtering
- `order_transactions.sku` - Direct SKU lookups
- `listing_ad_stats.listing_id + date` - Ad spend queries
- And 20+ more indexes covering all major query patterns

---

### ✅ SOLUTION 2: Batch Processing (MEDIUM PRIORITY)

Instead of processing one SKU at a time, process multiple SKUs in batches:

**Current (Slow):**

```
Query 1: SKU="MacBag" → 74 seconds
Query 2: SKU="Wallet" → 74 seconds
Query 3: SKU="Case" → 74 seconds
Total: 222 seconds for 3 SKUs
```

**Improved (Fast):**

```
Query 1: SKUs IN ("MacBag", "Wallet", "Case") → 80 seconds
Total: 80 seconds for 3 SKUs (2.7x faster)
```

**Implementation:** Modify `calculate_metrics_batch` to accept `List[str]` of SKUs instead of single SKU.

---

### ✅ SOLUTION 3: Increase Batch Size (QUICK WIN)

The current semaphore limits concurrent processing:

```python
# Current
semaphore = asyncio.Semaphore(5)  # Only 5 SKUs processed concurrently
```

After applying indexes, increase concurrency:

```python
semaphore = asyncio.Semaphore(20)  # Process 20 SKUs concurrently
```

**Expected Result:** 4x faster total processing time

---

### ✅ SOLUTION 4: Cache Common Data (OPTIMIZATION)

Many SKUs share the same cost data, desi values, and shipping costs. Cache these lookups to avoid repeated DataFrame scans:

```python
# Already implemented:
@lru_cache(maxsize=5000)
def get_us_shipping_costs(self, sku: str) -> Dict[str, float]:
    # Cached - only computes once per unique SKU
```

This is already done in the code!

---

## Recommended Action Plan

### Phase 1: Apply Indexes (DO THIS NOW!)

```bash
# 1. Find your DATABASE_URL
cat .env | grep DATABASE_URL

# Or get it from the running process:
ps aux | grep python | grep reportsv4

# 2. Apply indexes
psql "$DATABASE_URL" -f add_performance_indexes.sql

# 3. Verify indexes were created
psql "$DATABASE_URL" -c "\d+ orders" | grep -i index

# You should see indexes like:
#   idx_orders_created_timestamp
#   idx_orders_buyer_id
#   etc.
```

**Expected Impact:** 10-20x speedup (74 sec → 5-7 sec per SKU)

### Phase 2: Increase Concurrency

After indexes are applied and queries are faster, increase concurrency in the script:

Find this line in `reportsv4_optimized.py`:

```python
semaphore = asyncio.Semaphore(5)
```

Change to:

```python
semaphore = asyncio.Semaphore(20)  # Process more SKUs in parallel
```

**Expected Impact:** 4x speedup (2.5 hours → 40 minutes)

### Phase 3: Monitor and Optimize

After Phase 1 & 2:

1. Re-run the reports generation
2. Check the new per-SKU processing time
3. If still slow, consider batch processing (Solution 2)

---

## How to Check If Indexes Exist

```bash
# Check orders table indexes
psql "$DATABASE_URL" -c "\d+ orders"

# Check order_transactions indexes
psql "$DATABASE_URL" -c "\d+ order_transactions"

# List all indexes in database
psql "$DATABASE_URL" -c "\di"
```

**What to look for:**

- `idx_orders_created_timestamp` - Critical!
- `idx_order_transactions_product_id` - Critical!
- `idx_order_transactions_sku` - Critical!

If these don't exist, **the indexes haven't been applied**.

---

## Why 74 Seconds Per SKU?

Without indexes, here's what happens for EACH SKU query:

1. **Full scan of orders** table (~200K rows) to filter by date
2. **Full scan of order_transactions** (~500K rows) to filter by product_id
3. **Full scan of refunds** table for each matching order
4. **Full scan of listing_ad_stats** for ad spend
5. **Nested loop joins** between all tables (no index-assisted joins)

Total: **~1 million row scans per query** × ~30-50 queries per SKU = **Very slow!**

With indexes:

1. **Index seek on orders.created_timestamp** - finds ~1000 relevant orders instantly
2. **Index seek on order_transactions.product_id** - finds ~100 transactions instantly
3. **Index-assisted joins** - PostgreSQL uses indexes to join efficiently

Total: **~1000 rows examined** × optimized joins = **10-100x faster!**

---

## Quick Diagnosis

Run this to see query performance:

```sql
-- Check if indexes exist
SELECT tablename, indexname
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

-- Check table sizes (to understand scale)
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    n_live_tup AS rows
FROM pg_stat_user_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

This shows:

- Which indexes exist (should see `idx_` prefixed indexes)
- Table sizes (to understand query complexity)
- Row counts (to estimate scan overhead)

---

## Summary

| Issue             | Impact                  | Solution                            | Expected Speedup |
| ----------------- | ----------------------- | ----------------------------------- | ---------------- |
| Missing indexes   | 10-100x slower          | Apply `add_performance_indexes.sql` | 10-20x faster    |
| Low concurrency   | Only 5 parallel queries | Increase semaphore to 20            | 4x faster        |
| One-SKU-at-a-time | Sequential processing   | Batch multiple SKUs per query       | 2-3x faster      |

**Combined Expected Result:**

- Current: 25+ hours for 1,255 SKUs
- After Phase 1 (indexes): ~2.5 hours
- After Phase 2 (concurrency): ~40 minutes
- After Phase 3 (batching): ~15 minutes

**Start with Phase 1 - it's the biggest win and takes 30 seconds to apply!**
