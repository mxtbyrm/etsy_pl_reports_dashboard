-- ============================================================================
-- PERFORMANCE INDEXES FOR REPORT TABLES - OPTIONAL
-- ============================================================================
-- Created: 2025-11-10
-- Purpose: Indexes for report aggregation tables (apply AFTER core indexes)
-- ONLY RUN THIS IF THESE TABLES EXIST IN YOUR DATABASE
-- Check first: SELECT tablename FROM pg_tables WHERE schemaname = 'public';
-- ============================================================================

-- 1. LISTING_AD_STATS TABLE (only if exists)
CREATE INDEX IF NOT EXISTS idx_listing_ad_stats_listing_id ON listing_ad_stats(listing_id);
CREATE INDEX IF NOT EXISTS idx_listing_ad_stats_period_start ON listing_ad_stats(period_start);
CREATE INDEX IF NOT EXISTS idx_listing_ad_stats_period_end ON listing_ad_stats(period_end);
CREATE INDEX IF NOT EXISTS idx_listing_ad_stats_listing_period ON listing_ad_stats(listing_id, period_start, period_end);

-- 2. LISTING_VISIT_STATS TABLE (only if exists)
CREATE INDEX IF NOT EXISTS idx_listing_visit_stats_listing_id ON listing_visit_stats(listing_id);
CREATE INDEX IF NOT EXISTS idx_listing_visit_stats_period_start ON listing_visit_stats(period_start);
CREATE INDEX IF NOT EXISTS idx_listing_visit_stats_period_end ON listing_visit_stats(period_end);
CREATE INDEX IF NOT EXISTS idx_listing_visit_stats_listing_period ON listing_visit_stats(listing_id, period_start, period_end);

-- 3. PRODUCT_REPORTS TABLE (only if exists)
-- Note: These tables use camelCase column names (no @map directives)
CREATE INDEX IF NOT EXISTS idx_product_reports_sku ON product_reports(sku);
CREATE INDEX IF NOT EXISTS idx_product_reports_sku_dates ON product_reports(sku, "periodStart", "periodEnd");

-- 4. LISTING_REPORTS TABLE (only if exists)
CREATE INDEX IF NOT EXISTS idx_listing_reports_listing_id ON listing_reports("listingId");
CREATE INDEX IF NOT EXISTS idx_listing_reports_listing_dates ON listing_reports("listingId", "periodStart", "periodEnd");

-- 5. SHOP_REPORTS TABLE (only if exists)
CREATE INDEX IF NOT EXISTS idx_shop_reports_dates ON shop_reports("periodStart", "periodEnd");

-- Update table statistics (only for tables that exist)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'listing_ad_stats') THEN
        EXECUTE 'ANALYZE listing_ad_stats';
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'listing_visit_stats') THEN
        EXECUTE 'ANALYZE listing_visit_stats';
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'product_reports') THEN
        EXECUTE 'ANALYZE product_reports';
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'listing_reports') THEN
        EXECUTE 'ANALYZE listing_reports';
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'shop_reports') THEN
        EXECUTE 'ANALYZE shop_reports';
    END IF;
END $$;

-- Success message
SELECT 
    'Report table indexes created successfully!' as status,
    COUNT(*) as total_indexes
FROM pg_indexes 
WHERE schemaname = 'public' 
AND indexname LIKE 'idx_%';
