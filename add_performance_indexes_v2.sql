-- ============================================================================
-- PERFORMANCE INDEXES FOR ETSY REPORTS GENERATION v2
-- ============================================================================
-- Created: 2025-11-10
-- Purpose: Speed up queries by 10-100x for report generation
-- Safe to run multiple times (uses IF NOT EXISTS)
-- ============================================================================

-- 1. ORDERS TABLE
CREATE INDEX IF NOT EXISTS idx_orders_created_timestamp ON orders(created_timestamp);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_buyer_user_id ON orders(buyer_user_id);
CREATE INDEX IF NOT EXISTS idx_orders_country ON orders(country);
CREATE INDEX IF NOT EXISTS idx_orders_timestamp_status ON orders(created_timestamp, status);

-- 2. ORDER_TRANSACTIONS TABLE
CREATE INDEX IF NOT EXISTS idx_order_transactions_order_id ON order_transactions(order_id);
CREATE INDEX IF NOT EXISTS idx_order_transactions_product_id ON order_transactions(product_id);
CREATE INDEX IF NOT EXISTS idx_order_transactions_listing_id ON order_transactions(listing_id);
CREATE INDEX IF NOT EXISTS idx_order_transactions_sku ON order_transactions(sku);
CREATE INDEX IF NOT EXISTS idx_order_transactions_order_product ON order_transactions(order_id, product_id);
CREATE INDEX IF NOT EXISTS idx_order_transactions_order_listing ON order_transactions(order_id, listing_id);

-- 3. ORDER_REFUNDS TABLE
CREATE INDEX IF NOT EXISTS idx_order_refunds_order_id ON order_refunds(order_id);
CREATE INDEX IF NOT EXISTS idx_order_refunds_status ON order_refunds(status);
CREATE INDEX IF NOT EXISTS idx_order_refunds_created_timestamp ON order_refunds(created_timestamp);

-- 4. ORDER_SHIPMENTS TABLE
CREATE INDEX IF NOT EXISTS idx_order_shipments_order_id ON order_shipments(order_id);
CREATE INDEX IF NOT EXISTS idx_order_shipments_shipped_timestamp ON order_shipments(shipped_timestamp);

-- 5. LISTING_AD_STATS TABLE
CREATE INDEX IF NOT EXISTS idx_listing_ad_stats_listing_id ON listing_ad_stats(listing_id);
CREATE INDEX IF NOT EXISTS idx_listing_ad_stats_period_start ON listing_ad_stats(period_start);
CREATE INDEX IF NOT EXISTS idx_listing_ad_stats_period_end ON listing_ad_stats(period_end);
CREATE INDEX IF NOT EXISTS idx_listing_ad_stats_listing_dates ON listing_ad_stats(listing_id, period_start, period_end);

-- 6. LISTING_VISIT_STATS TABLE
CREATE INDEX IF NOT EXISTS idx_listing_visit_stats_listing_id ON listing_visit_stats(listing_id);
CREATE INDEX IF NOT EXISTS idx_listing_visit_stats_listing_dates ON listing_visit_stats(listing_id, period_start, period_end);

-- 7. LISTING_PRODUCTS TABLE
CREATE INDEX IF NOT EXISTS idx_listing_products_sku ON listing_products(sku);
CREATE INDEX IF NOT EXISTS idx_listing_products_listing_id ON listing_products(listing_id);
CREATE INDEX IF NOT EXISTS idx_listing_products_is_deleted ON listing_products(is_deleted);
CREATE INDEX IF NOT EXISTS idx_listing_products_sku_active ON listing_products(sku, is_deleted);

-- 8. PRODUCT_OFFERINGS TABLE
CREATE INDEX IF NOT EXISTS idx_product_offerings_listing_product_id ON product_offerings(listing_product_id);
CREATE INDEX IF NOT EXISTS idx_product_offerings_enabled_not_deleted ON product_offerings(is_enabled, is_deleted);

-- 9. LISTINGS TABLE
CREATE INDEX IF NOT EXISTS idx_listings_state ON listings(state);
CREATE INDEX IF NOT EXISTS idx_listings_shop_id ON listings(shop_id);

-- 10. REVIEWS TABLE
CREATE INDEX IF NOT EXISTS idx_reviews_listing_id ON reviews(listing_id);
CREATE INDEX IF NOT EXISTS idx_reviews_product_id ON reviews(product_id);
CREATE INDEX IF NOT EXISTS idx_reviews_created_timestamp ON reviews(created_timestamp);
CREATE INDEX IF NOT EXISTS idx_reviews_rating ON reviews(rating);

-- 11. PRODUCT_REPORTS TABLE
CREATE INDEX IF NOT EXISTS idx_product_reports_sku ON product_reports(sku);
CREATE INDEX IF NOT EXISTS idx_product_reports_sku_dates ON product_reports(sku, period_start, period_end);

-- 12. LISTING_REPORTS TABLE
CREATE INDEX IF NOT EXISTS idx_listing_reports_listing_id ON listing_reports(listing_id);
CREATE INDEX IF NOT EXISTS idx_listing_reports_listing_dates ON listing_reports(listing_id, period_start, period_end);

-- 13. SHOP_REPORTS TABLE
CREATE INDEX IF NOT EXISTS idx_shop_reports_dates ON shop_reports(period_start, period_end);

-- 14. LEDGER_ENTRIES TABLE
CREATE INDEX IF NOT EXISTS idx_ledger_entries_created_timestamp ON ledger_entries(created_timestamp);
CREATE INDEX IF NOT EXISTS idx_ledger_entries_ledger_type ON ledger_entries(ledger_type);
CREATE INDEX IF NOT EXISTS idx_ledger_entries_related_payment_id ON ledger_entries(related_payment_id);

-- Update table statistics
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

-- Success message
SELECT 
    'Performance indexes created successfully!' as status,
    COUNT(*) as total_indexes
FROM pg_indexes 
WHERE schemaname = 'public' 
AND indexname LIKE 'idx_%';
