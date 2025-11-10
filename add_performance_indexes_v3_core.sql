-- ============================================================================
-- PERFORMANCE INDEXES FOR ETSY REPORTS GENERATION v3 - CORE TABLES ONLY
-- ============================================================================
-- Created: 2025-11-10
-- Purpose: Speed up queries by 10-100x for report generation
-- Safe to run multiple times (uses IF NOT EXISTS)
-- Only indexes tables that definitely exist in your database
-- ============================================================================

-- 1. ORDERS TABLE - CRITICAL FOR ALL QUERIES
CREATE INDEX IF NOT EXISTS idx_orders_created_timestamp ON orders(created_timestamp);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_buyer_user_id ON orders(buyer_user_id);
CREATE INDEX IF NOT EXISTS idx_orders_country ON orders(country);
CREATE INDEX IF NOT EXISTS idx_orders_timestamp_status ON orders(created_timestamp, status);

-- 2. ORDER_TRANSACTIONS TABLE - CRITICAL FOR SKU/LISTING FILTERING
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

-- 5. LISTING_PRODUCTS TABLE - CRITICAL FOR SKU TO PRODUCT_ID MAPPING
CREATE INDEX IF NOT EXISTS idx_listing_products_sku ON listing_products(sku);
CREATE INDEX IF NOT EXISTS idx_listing_products_listing_id ON listing_products(listing_id);
CREATE INDEX IF NOT EXISTS idx_listing_products_is_deleted ON listing_products(is_deleted);
CREATE INDEX IF NOT EXISTS idx_listing_products_sku_active ON listing_products(sku, is_deleted);

-- 6. PRODUCT_OFFERINGS TABLE
CREATE INDEX IF NOT EXISTS idx_product_offerings_listing_product_id ON product_offerings(listing_product_id);
CREATE INDEX IF NOT EXISTS idx_product_offerings_enabled_not_deleted ON product_offerings(is_enabled, is_deleted);

-- 7. LISTINGS TABLE
CREATE INDEX IF NOT EXISTS idx_listings_state ON listings(state);
CREATE INDEX IF NOT EXISTS idx_listings_shop_id ON listings(shop_id);

-- 8. REVIEWS TABLE
CREATE INDEX IF NOT EXISTS idx_reviews_listing_id ON reviews(listing_id);
CREATE INDEX IF NOT EXISTS idx_reviews_product_id ON reviews(product_id);
CREATE INDEX IF NOT EXISTS idx_reviews_created_timestamp ON reviews(created_timestamp);
CREATE INDEX IF NOT EXISTS idx_reviews_rating ON reviews(rating);

-- 9. LEDGER_ENTRIES TABLE
CREATE INDEX IF NOT EXISTS idx_ledger_entries_created_timestamp ON ledger_entries(created_timestamp);
CREATE INDEX IF NOT EXISTS idx_ledger_entries_ledger_type ON ledger_entries(ledger_type);
CREATE INDEX IF NOT EXISTS idx_ledger_entries_related_payment_id ON ledger_entries(related_payment_id);

-- Update table statistics
ANALYZE orders;
ANALYZE order_transactions;
ANALYZE order_refunds;
ANALYZE order_shipments;
ANALYZE listing_products;
ANALYZE product_offerings;
ANALYZE listings;
ANALYZE reviews;
ANALYZE ledger_entries;

-- Success message
SELECT 
    'Core performance indexes created successfully!' as status,
    COUNT(*) as total_indexes
FROM pg_indexes 
WHERE schemaname = 'public' 
AND indexname LIKE 'idx_%';
