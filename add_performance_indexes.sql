-- ============================================================================-- ============================================================================-- Performance Indexes for Reports Generation

-- PERFORMANCE INDEXES FOR ETSY REPORTS GENERATION

-- ============================================================================-- PERFORMANCE INDEXES FOR ETSY REPORTS GENERATION-- Run this to speed up queries by 10-100x

-- Created: 2025-11-10

-- Purpose: Speed up queries by 10-100x for report generation-- ============================================================================-- Safe to run multiple times (uses IF NOT EXISTS)

-- Safe to run multiple times (uses IF NOT EXISTS)

-- ============================================================================-- Created: 2025-11-10



-- 1. ORDERS TABLE - Critical for time-range queries-- Purpose: Speed up queries by 10-100x for report generation-- ============================================================

CREATE INDEX IF NOT EXISTS idx_orders_created_timestamp ON orders(created_timestamp);

CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);-- Safe to run multiple times (uses IF NOT EXISTS)-- ORDERS TABLE INDEXES

CREATE INDEX IF NOT EXISTS idx_orders_buyer_user_id ON orders(buyer_user_id);

CREATE INDEX IF NOT EXISTS idx_orders_country ON orders(country);---- ============================================================

CREATE INDEX IF NOT EXISTS idx_orders_timestamp_status ON orders(created_timestamp, status);

-- Based on actual schema analysis and query patterns in reportsv4_optimized.py

-- 2. ORDER_TRANSACTIONS TABLE - Critical for SKU/listing filtering

CREATE INDEX IF NOT EXISTS idx_order_transactions_order_id ON order_transactions(order_id);-- ============================================================================-- Index on created_timestamp for time-range queries

CREATE INDEX IF NOT EXISTS idx_order_transactions_product_id ON order_transactions(product_id);

CREATE INDEX IF NOT EXISTS idx_order_transactions_listing_id ON order_transactions(listing_id);CREATE INDEX IF NOT EXISTS idx_orders_created_timestamp 

CREATE INDEX IF NOT EXISTS idx_order_transactions_sku ON order_transactions(sku);

CREATE INDEX IF NOT EXISTS idx_order_transactions_order_product ON order_transactions(order_id, product_id);-- ============================================================================ON orders(created_timestamp);

CREATE INDEX IF NOT EXISTS idx_order_transactions_order_listing ON order_transactions(order_id, listing_id);

-- 1. ORDERS TABLE - Critical for time-range queries

-- 3. ORDER_REFUNDS TABLE

CREATE INDEX IF NOT EXISTS idx_order_refunds_order_id ON order_refunds(order_id);-- ============================================================================-- Index on status for filtering completed orders

CREATE INDEX IF NOT EXISTS idx_order_refunds_status ON order_refunds(status);

CREATE INDEX IF NOT EXISTS idx_order_refunds_created_timestamp ON order_refunds(created_timestamp);CREATE INDEX IF NOT EXISTS idx_orders_status 



-- 4. ORDER_SHIPMENTS TABLE-- Most critical: created_timestamp is used in ALL report queriesON orders(status);

CREATE INDEX IF NOT EXISTS idx_order_shipments_order_id ON order_shipments(order_id);

CREATE INDEX IF NOT EXISTS idx_order_shipments_shipped_timestamp ON order_shipments(shipped_timestamp);-- Pattern: WHERE created_timestamp BETWEEN start AND end



-- 5. LISTING_AD_STATS TABLE - Critical for ad spend queriesCREATE INDEX IF NOT EXISTS idx_orders_created_timestamp -- Composite index for time + status queries

CREATE INDEX IF NOT EXISTS idx_listing_ad_stats_listing_id ON listing_ad_stats(listing_id);

CREATE INDEX IF NOT EXISTS idx_listing_ad_stats_period_start ON listing_ad_stats(period_start);ON orders(created_timestamp);CREATE INDEX IF NOT EXISTS idx_orders_timestamp_status 

CREATE INDEX IF NOT EXISTS idx_listing_ad_stats_period_end ON listing_ad_stats(period_end);

CREATE INDEX IF NOT EXISTS idx_listing_ad_stats_listing_dates ON listing_ad_stats(listing_id, period_start, period_end);ON orders(created_timestamp, status);

CREATE INDEX IF NOT EXISTS idx_listing_ad_stats_period_type ON listing_ad_stats(period_type);

-- Used for filtering completed orders

-- 6. LISTING_VISIT_STATS TABLE

CREATE INDEX IF NOT EXISTS idx_listing_visit_stats_listing_id ON listing_visit_stats(listing_id);-- Pattern: WHERE status = 'completed' OR status IN (...)-- ============================================================

CREATE INDEX IF NOT EXISTS idx_listing_visit_stats_listing_dates ON listing_visit_stats(listing_id, period_start, period_end);

CREATE INDEX IF NOT EXISTS idx_orders_status -- ORDER_TRANSACTIONS TABLE INDEXES

-- 7. LISTING_PRODUCTS TABLE - Critical for SKU to product_id mapping

CREATE INDEX IF NOT EXISTS idx_listing_products_sku ON listing_products(sku);ON orders(status);-- ============================================================

CREATE INDEX IF NOT EXISTS idx_listing_products_listing_id ON listing_products(listing_id);

CREATE INDEX IF NOT EXISTS idx_listing_products_is_deleted ON listing_products(is_deleted);

CREATE INDEX IF NOT EXISTS idx_listing_products_sku_active ON listing_products(sku, is_deleted);

-- Buyer analysis queries-- Index on order_id for joins

-- 8. PRODUCT_OFFERINGS TABLE

CREATE INDEX IF NOT EXISTS idx_product_offerings_listing_product_id ON product_offerings(listing_product_id);-- Pattern: WHERE buyer_user_id = XCREATE INDEX IF NOT EXISTS idx_order_transactions_order_id 

CREATE INDEX IF NOT EXISTS idx_product_offerings_enabled_not_deleted ON product_offerings(is_enabled, is_deleted);

CREATE INDEX IF NOT EXISTS idx_orders_buyer_user_id ON order_transactions(order_id);

-- 9. LISTINGS TABLE

CREATE INDEX IF NOT EXISTS idx_listings_state ON listings(state);ON orders(buyer_user_id);

CREATE INDEX IF NOT EXISTS idx_listings_shop_id ON listings(shop_id);

-- Index on product_id for SKU/product filtering

-- 10. REVIEWS TABLE

CREATE INDEX IF NOT EXISTS idx_reviews_listing_id ON reviews(listing_id);-- Country-based shipping analysisCREATE INDEX IF NOT EXISTS idx_order_transactions_product_id 

CREATE INDEX IF NOT EXISTS idx_reviews_product_id ON reviews(product_id);

CREATE INDEX IF NOT EXISTS idx_reviews_created_timestamp ON reviews(created_timestamp);-- Pattern: WHERE country = 'US' OR country IN (...)ON order_transactions(product_id);

CREATE INDEX IF NOT EXISTS idx_reviews_rating ON reviews(rating);

CREATE INDEX IF NOT EXISTS idx_orders_country 

-- 11. PRODUCT_REPORTS TABLE

CREATE INDEX IF NOT EXISTS idx_product_reports_sku ON product_reports(sku);ON orders(country);-- Index on listing_id for listing filtering

CREATE INDEX IF NOT EXISTS idx_product_reports_period_type ON product_reports(period_type);

CREATE INDEX IF NOT EXISTS idx_product_reports_sku_dates ON product_reports(sku, period_start, period_end);CREATE INDEX IF NOT EXISTS idx_order_transactions_listing_id 

CREATE INDEX IF NOT EXISTS idx_product_reports_full ON product_reports(sku, period_type, period_start, period_end);

-- Composite index for most common query patternON order_transactions(listing_id);

-- 12. LISTING_REPORTS TABLE

CREATE INDEX IF NOT EXISTS idx_listing_reports_listing_id ON listing_reports(listing_id);-- Pattern: WHERE created_timestamp BETWEEN X AND Y AND status = 'completed'

CREATE INDEX IF NOT EXISTS idx_listing_reports_period_type ON listing_reports(period_type);

CREATE INDEX IF NOT EXISTS idx_listing_reports_listing_dates ON listing_reports(listing_id, period_start, period_end);CREATE INDEX IF NOT EXISTS idx_orders_timestamp_status -- Index on SKU for direct SKU lookups

CREATE INDEX IF NOT EXISTS idx_listing_reports_full ON listing_reports(listing_id, period_type, period_start, period_end);

ON orders(created_timestamp, status);CREATE INDEX IF NOT EXISTS idx_order_transactions_sku 

-- 13. SHOP_REPORTS TABLE

CREATE INDEX IF NOT EXISTS idx_shop_reports_period_type ON shop_reports(period_type);ON order_transactions(sku);

CREATE INDEX IF NOT EXISTS idx_shop_reports_dates ON shop_reports(period_start, period_end);

CREATE INDEX IF NOT EXISTS idx_shop_reports_full ON shop_reports(period_type, period_start, period_end);-- Order ID (Primary key, already indexed but explicitly for joins)



-- 14. LEDGER_ENTRIES TABLE-- Pattern: JOIN orders ON order_id = X-- Composite index for order + product queries

CREATE INDEX IF NOT EXISTS idx_ledger_entries_created_timestamp ON ledger_entries(created_timestamp);

CREATE INDEX IF NOT EXISTS idx_ledger_entries_ledger_type ON ledger_entries(ledger_type);CREATE INDEX IF NOT EXISTS idx_order_transactions_order_product 

CREATE INDEX IF NOT EXISTS idx_ledger_entries_related_payment_id ON ledger_entries(related_payment_id);

-- ============================================================================ON order_transactions(order_id, product_id);

-- Update table statistics for query planner

ANALYZE orders;-- 2. ORDER_TRANSACTIONS TABLE - Critical for SKU/listing filtering

ANALYZE order_transactions;

ANALYZE order_refunds;-- ============================================================================-- ============================================================

ANALYZE order_shipments;

ANALYZE listing_ad_stats;-- ORDER_REFUNDS TABLE INDEXES

ANALYZE listing_visit_stats;

ANALYZE listing_products;-- Most critical: order_id for joins-- ============================================================

ANALYZE product_offerings;

ANALYZE listings;-- Pattern: JOIN order_transactions ON order_id = orders.order_id

ANALYZE reviews;

ANALYZE product_reports;CREATE INDEX IF NOT EXISTS idx_order_transactions_order_id -- Index on order_id for refund lookups

ANALYZE listing_reports;

ANALYZE shop_reports;ON order_transactions(order_id);CREATE INDEX IF NOT EXISTS idx_order_refunds_order_id 

ANALYZE ledger_entries;

ON order_refunds(order_id);

-- Success message

SELECT '✅ Performance indexes created successfully!' as status,-- Critical: product_id for SKU filtering

       COUNT(*) as total_indexes

FROM pg_indexes -- Pattern: WHERE product_id IN (list_of_product_ids)-- ============================================================

WHERE schemaname = 'public' 

AND indexname LIKE 'idx_%';CREATE INDEX IF NOT EXISTS idx_order_transactions_product_id -- LISTING_AD_STATS TABLE INDEXES


ON order_transactions(product_id);-- ============================================================



-- Critical: listing_id for listing reports-- Index on listing_id for ad spend queries

-- Pattern: WHERE listing_id = X OR listing_id IN (...)CREATE INDEX IF NOT EXISTS idx_listing_ad_stats_listing_id 

CREATE INDEX IF NOT EXISTS idx_order_transactions_listing_id ON listing_ad_stats(listing_id);

ON order_transactions(listing_id);

-- Index on period dates for time-range queries

-- Critical: SKU for direct SKU lookupsCREATE INDEX IF NOT EXISTS idx_listing_ad_stats_period_start 

-- Pattern: WHERE sku = 'MacBag' OR sku IN (...)ON listing_ad_stats(period_start);

CREATE INDEX IF NOT EXISTS idx_order_transactions_sku 

ON order_transactions(sku);CREATE INDEX IF NOT EXISTS idx_listing_ad_stats_period_end 

ON listing_ad_stats(period_end);

-- Transaction ID (Already unique, but used in Review joins)

-- Pattern: JOIN reviews ON transaction_id = X-- Composite index for listing + date range queries

CREATE INDEX IF NOT EXISTS idx_listing_ad_stats_listing_dates 

-- Composite index for the most common join + filter patternON listing_ad_stats(listing_id, period_start, period_end);

-- Pattern: JOIN transactions WHERE order_id = X AND product_id = Y

CREATE INDEX IF NOT EXISTS idx_order_transactions_order_product -- ============================================================

ON order_transactions(order_id, product_id);-- LISTING_PRODUCTS TABLE INDEXES

-- ============================================================

-- Composite for listing reports

-- Pattern: JOIN transactions WHERE order_id = X AND listing_id = Y  -- Index on SKU for product-to-listing lookups

CREATE INDEX IF NOT EXISTS idx_order_transactions_order_listing CREATE INDEX IF NOT EXISTS idx_listing_products_sku 

ON order_transactions(order_id, listing_id);ON listing_products(sku);



-- ============================================================================-- Index on is_deleted for active product filtering

-- 3. ORDER_REFUNDS TABLE - For refund analysisCREATE INDEX IF NOT EXISTS idx_listing_products_deleted 

-- ============================================================================ON listing_products(is_deleted);



-- Critical: order_id for joining refunds to orders-- Composite index for SKU + active status

-- Pattern: LEFT JOIN order_refunds ON order_id = orders.order_idCREATE INDEX IF NOT EXISTS idx_listing_products_sku_active 

CREATE INDEX IF NOT EXISTS idx_order_refunds_order_id ON listing_products(sku, is_deleted);

ON order_refunds(order_id);

-- ============================================================

-- Refund status filtering-- PRODUCT_REPORTS TABLE INDEXES

-- Pattern: WHERE status = 'approved' OR status IN (...)-- ============================================================

CREATE INDEX IF NOT EXISTS idx_order_refunds_status 

ON order_refunds(status);-- Index on SKU for product report lookups

CREATE INDEX IF NOT EXISTS idx_product_reports_sku 

-- Refund timestamp for time-based analysisON product_reports(sku);

-- Pattern: WHERE created_timestamp BETWEEN X AND Y

CREATE INDEX IF NOT EXISTS idx_order_refunds_created_timestamp -- Composite index for SKU + period queries (includes period_type, period_start, period_end)

ON order_refunds(created_timestamp);CREATE INDEX IF NOT EXISTS idx_product_reports_sku_period 

ON product_reports(sku, period_start, period_end);

-- ============================================================================

-- 4. ORDER_SHIPMENTS TABLE - For shipping analysis-- ============================================================

-- ============================================================================-- LISTING_REPORTS TABLE INDEXES

-- ============================================================

-- Order ID for joins

-- Pattern: LEFT JOIN order_shipments ON order_id = orders.order_id-- Index on listing_id for listing report lookups

CREATE INDEX IF NOT EXISTS idx_order_shipments_order_id CREATE INDEX IF NOT EXISTS idx_listing_reports_listing_id 

ON order_shipments(order_id);ON listing_reports(listing_id);



-- Shipped timestamp for time-based shipping analysis-- Composite index for listing + period queries (includes period_start, period_end)

-- Pattern: WHERE shipped_timestamp BETWEEN X AND YCREATE INDEX IF NOT EXISTS idx_listing_reports_listing_period 

CREATE INDEX IF NOT EXISTS idx_order_shipments_shipped_timestamp ON listing_reports(listing_id, period_start, period_end);

ON order_shipments(shipped_timestamp);

-- ============================================================

-- ============================================================================-- SHOP_REPORTS TABLE INDEXES

-- 5. LISTING_AD_STATS TABLE - Critical for ad spend queries-- ============================================================

-- ============================================================================

-- Composite index for shop report time queries (includes period_start, period_end)

-- Most critical: listing_id for ad spend lookupsCREATE INDEX IF NOT EXISTS idx_shop_reports_period 

-- Pattern: WHERE listing_id = XON shop_reports(period_start, period_end);

CREATE INDEX IF NOT EXISTS idx_listing_ad_stats_listing_id 

ON listing_ad_stats(listing_id);-- ============================================================

-- ANALYSIS: Check index usage

-- Period dates for time-range queries-- ============================================================

-- Pattern: WHERE period_start >= X AND period_end <= Y

CREATE INDEX IF NOT EXISTS idx_listing_ad_stats_period_start -- Run this query AFTER running reports to see which indexes are being used:

ON listing_ad_stats(period_start);-- 

-- SELECT 

CREATE INDEX IF NOT EXISTS idx_listing_ad_stats_period_end --     schemaname,

ON listing_ad_stats(period_end);--     tablename,

--     indexname,

-- Composite index for the most common query pattern--     idx_scan as "Times Used",

-- Pattern: WHERE listing_id = X AND period_start >= Y AND period_end <= Z--     idx_tup_read as "Rows Read",

CREATE INDEX IF NOT EXISTS idx_listing_ad_stats_listing_dates --     idx_tup_fetch as "Rows Fetched"

ON listing_ad_stats(listing_id, period_start, period_end);-- FROM pg_stat_user_indexes

-- WHERE schemaname = 'public'

-- Period type for filtering (ENUM type, but useful for filtering)-- ORDER BY idx_scan DESC;

-- Pattern: WHERE period_type = 'MONTHLY'

CREATE INDEX IF NOT EXISTS idx_listing_ad_stats_period_type ANALYZE orders;

ON listing_ad_stats(period_type);ANALYZE order_transactions;

ANALYZE order_refunds;

-- ============================================================================ANALYZE listing_ad_stats;

-- 6. LISTING_VISIT_STATS TABLE - For visit analyticsANALYZE listing_products;

-- ============================================================================ANALYZE product_reports;

ANALYZE listing_reports;

-- Listing ID for joinsANALYZE shop_reports;

-- Pattern: WHERE listing_id = X

CREATE INDEX IF NOT EXISTS idx_listing_visit_stats_listing_id -- Success message

ON listing_visit_stats(listing_id);SELECT 'Performance indexes created successfully!' as status;


-- Composite for common query pattern
-- Pattern: WHERE listing_id = X AND period_start >= Y AND period_end <= Z
CREATE INDEX IF NOT EXISTS idx_listing_visit_stats_listing_dates 
ON listing_visit_stats(listing_id, period_start, period_end);

-- ============================================================================
-- 7. LISTING_PRODUCTS TABLE - Critical for SKU to product_id mapping
-- ============================================================================

-- Most critical: SKU for product-to-listing lookups
-- Pattern: WHERE sku = 'MacBag' (Query: get_listing_id_for_sku)
CREATE INDEX IF NOT EXISTS idx_listing_products_sku 
ON listing_products(sku);

-- Listing ID for finding all products in a listing
-- Pattern: WHERE listing_id = X
CREATE INDEX IF NOT EXISTS idx_listing_products_listing_id 
ON listing_products(listing_id);

-- is_deleted for filtering active products
-- Pattern: WHERE is_deleted = false AND sku IS NOT NULL
CREATE INDEX IF NOT EXISTS idx_listing_products_is_deleted 
ON listing_products(is_deleted);

-- Composite index for active SKU lookups (most common pattern)
-- Pattern: WHERE sku = X AND is_deleted = FALSE
CREATE INDEX IF NOT EXISTS idx_listing_products_sku_active 
ON listing_products(sku, is_deleted);

-- Product ID (Already unique, used in joins)
-- Pattern: JOIN listing_products ON product_id = X

-- ============================================================================
-- 8. PRODUCT_OFFERINGS TABLE - For inventory and pricing
-- ============================================================================

-- Listing product ID for joins
-- Pattern: JOIN product_offerings ON listing_product_id = X
CREATE INDEX IF NOT EXISTS idx_product_offerings_listing_product_id 
ON product_offerings(listing_product_id);

-- Composite for active offerings
-- Pattern: WHERE is_enabled = true AND is_deleted = false
CREATE INDEX IF NOT EXISTS idx_product_offerings_enabled_not_deleted 
ON product_offerings(is_enabled, is_deleted);

-- ============================================================================
-- 9. LISTINGS TABLE - For listing metadata
-- ============================================================================

-- Listing ID (Primary key, already indexed)

-- State for filtering active listings
-- Pattern: WHERE state = 'active'
CREATE INDEX IF NOT EXISTS idx_listings_state 
ON listings(state);

-- Shop ID for shop-level queries
-- Pattern: WHERE shop_id = X
CREATE INDEX IF NOT EXISTS idx_listings_shop_id 
ON listings(shop_id);

-- ============================================================================
-- 10. REVIEWS TABLE - For review analysis
-- ============================================================================

-- Transaction ID (Already unique, used in joins)
-- Pattern: JOIN reviews ON transaction_id = X

-- Listing ID for listing reviews
-- Pattern: WHERE listing_id = X
CREATE INDEX IF NOT EXISTS idx_reviews_listing_id 
ON reviews(listing_id);

-- Product ID for product reviews
-- Pattern: WHERE product_id = X
CREATE INDEX IF NOT EXISTS idx_reviews_product_id 
ON reviews(product_id);

-- Created timestamp for time-based analysis
-- Pattern: WHERE created_timestamp BETWEEN X AND Y
CREATE INDEX IF NOT EXISTS idx_reviews_created_timestamp 
ON reviews(created_timestamp);

-- Rating for analysis
-- Pattern: WHERE rating >= X
CREATE INDEX IF NOT EXISTS idx_reviews_rating 
ON reviews(rating);

-- ============================================================================
-- 11. PRODUCT_REPORTS TABLE - For caching and lookups
-- ============================================================================

-- SKU for product report lookups
-- Pattern: WHERE sku = X
CREATE INDEX IF NOT EXISTS idx_product_reports_sku 
ON product_reports(sku);

-- Period type for filtering
-- Pattern: WHERE period_type = 'MONTHLY'
CREATE INDEX IF NOT EXISTS idx_product_reports_period_type 
ON product_reports(period_type);

-- Composite for most common query pattern
-- Pattern: WHERE sku = X AND period_start >= Y AND period_end <= Z
CREATE INDEX IF NOT EXISTS idx_product_reports_sku_dates 
ON product_reports(sku, period_start, period_end);

-- Full composite with period_type (covers unique constraint)
-- Pattern: WHERE sku = X AND period_type = Y AND period_start = Z AND period_end = W
-- Note: This matches the @@unique constraint, PostgreSQL may already optimize this
CREATE INDEX IF NOT EXISTS idx_product_reports_full 
ON product_reports(sku, period_type, period_start, period_end);

-- ============================================================================
-- 12. LISTING_REPORTS TABLE - For caching and lookups
-- ============================================================================

-- Listing ID for report lookups
-- Pattern: WHERE listing_id = X
CREATE INDEX IF NOT EXISTS idx_listing_reports_listing_id 
ON listing_reports(listing_id);

-- Period type for filtering
-- Pattern: WHERE period_type = 'MONTHLY'
CREATE INDEX IF NOT EXISTS idx_listing_reports_period_type 
ON listing_reports(period_type);

-- Composite for common query pattern
-- Pattern: WHERE listing_id = X AND period_start >= Y AND period_end <= Z
CREATE INDEX IF NOT EXISTS idx_listing_reports_listing_dates 
ON listing_reports(listing_id, period_start, period_end);

-- Full composite (covers unique constraint)
-- Pattern: WHERE listing_id = X AND period_type = Y AND period_start = Z AND period_end = W
CREATE INDEX IF NOT EXISTS idx_listing_reports_full 
ON listing_reports(listing_id, period_type, period_start, period_end);

-- ============================================================================
-- 13. SHOP_REPORTS TABLE - For shop-level caching
-- ============================================================================

-- Period type for filtering
-- Pattern: WHERE period_type = 'YEARLY'
CREATE INDEX IF NOT EXISTS idx_shop_reports_period_type 
ON shop_reports(period_type);

-- Composite for time-based queries
-- Pattern: WHERE period_start >= X AND period_end <= Y
CREATE INDEX IF NOT EXISTS idx_shop_reports_dates 
ON shop_reports(period_start, period_end);

-- Full composite (covers unique constraint)
-- Pattern: WHERE period_type = X AND period_start = Y AND period_end = Z
CREATE INDEX IF NOT EXISTS idx_shop_reports_full 
ON shop_reports(period_type, period_start, period_end);

-- ============================================================================
-- 14. LEDGER_ENTRIES TABLE - For financial analysis
-- ============================================================================

-- Created timestamp for time-based queries
-- Pattern: WHERE created_timestamp BETWEEN X AND Y
CREATE INDEX IF NOT EXISTS idx_ledger_entries_created_timestamp 
ON ledger_entries(created_timestamp);

-- Ledger type for filtering
-- Pattern: WHERE ledger_type = 'payment'
CREATE INDEX IF NOT EXISTS idx_ledger_entries_ledger_type 
ON ledger_entries(ledger_type);

-- Related payment ID for joins
-- Pattern: WHERE related_payment_id = X
CREATE INDEX IF NOT EXISTS idx_ledger_entries_related_payment_id 
ON ledger_entries(related_payment_id);

-- ============================================================================
-- ANALYZE TABLES - Update statistics for query planner
-- ============================================================================

ANALYZE orders;
ANALYZE order_transactions;
ANALYZE order_refunds;
ANALYZE order_shipments;
ANALYZE listing_ad_stats;
ANALYZE listing_visit_stats;
ANALYZE listing_products;
ANALYZE product_offerings;
ANALYZE listings;
ANALYZE reviews;
ANALYZE product_reports;
ANALYZE listing_reports;
ANALYZE shop_reports;
ANALYZE ledger_entries;

-- ============================================================================
-- SUCCESS MESSAGE
-- ============================================================================

SELECT 
    '✅ Performance indexes created successfully!' as status,
    COUNT(*) as total_indexes_created
FROM pg_indexes 
WHERE schemaname = 'public' 
AND indexname LIKE 'idx_%';

-- ============================================================================
-- VERIFICATION QUERIES (Run these after creating indexes)
-- ============================================================================

-- 1. List all indexes created by this script
-- SELECT tablename, indexname 
-- FROM pg_indexes 
-- WHERE schemaname = 'public' 
-- AND indexname LIKE 'idx_%'
-- ORDER BY tablename, indexname;

-- 2. Check table sizes (helps understand query complexity)
-- SELECT 
--     schemaname,
--     tablename,
--     pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
--     n_live_tup AS estimated_rows
-- FROM pg_stat_user_tables
-- ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- 3. Check index usage after running reports (run this AFTER generating reports)
-- SELECT 
--     schemaname,
--     tablename,
--     indexname,
--     idx_scan as times_used,
--     idx_tup_read as rows_read,
--     idx_tup_fetch as rows_fetched,
--     pg_size_pretty(pg_relation_size(indexrelid)) as index_size
-- FROM pg_stat_user_indexes
-- WHERE schemaname = 'public'
-- AND indexname LIKE 'idx_%'
-- ORDER BY idx_scan DESC;

-- 4. Find unused indexes (run this after reports have been running for a while)
-- SELECT 
--     schemaname,
--     tablename,
--     indexname,
--     pg_size_pretty(pg_relation_size(indexrelid)) as index_size
-- FROM pg_stat_user_indexes
-- WHERE schemaname = 'public'
-- AND indexname LIKE 'idx_%'
-- AND idx_scan = 0
-- ORDER BY pg_relation_size(indexrelid) DESC;

-- ============================================================================
-- EXPECTED PERFORMANCE IMPROVEMENTS
-- ============================================================================
-- 
-- Before indexes:
--   - 74 seconds per SKU query
--   - 1,255 SKUs × 74 sec = 25+ hours total
--
-- After indexes:
--   - 5-10 seconds per SKU query (10-15x faster!)
--   - 1,255 SKUs × 7 sec = ~2.5 hours total
--
-- Key indexes that provide biggest speedup:
--   1. idx_orders_created_timestamp (10-50x faster date queries)
--   2. idx_order_transactions_product_id (5-20x faster SKU filtering)
--   3. idx_order_transactions_order_id (5-10x faster joins)
--   4. idx_listing_ad_stats_listing_dates (10x faster ad spend queries)
--
-- ============================================================================
