-- CreateEnum
CREATE TYPE "PeriodType" AS ENUM ('YEARLY', 'MONTHLY', 'WEEKLY');

-- CreateTable
CREATE TABLE "orders" (
    "order_id" BIGINT NOT NULL,
    "created_timestamp" BIGINT NOT NULL,
    "created_datetime" TIMESTAMP(3),
    "buyer_user_id" BIGINT,
    "buyer_email" TEXT NOT NULL,
    "grand_total" DOUBLE PRECISION,
    "grand_total_divisor" DOUBLE PRECISION,
    "grand_total_currency_code" TEXT,
    "subtotal" DOUBLE PRECISION,
    "subtotal_divisor" DOUBLE PRECISION,
    "subtotal_currency_code" TEXT,
    "total_price" DOUBLE PRECISION NOT NULL,
    "total_price_divisor" DOUBLE PRECISION,
    "total_price_currency_code" TEXT NOT NULL,
    "total_shipping_cost" DOUBLE PRECISION,
    "shipping_divisor" DOUBLE PRECISION,
    "shipping_currency_code" TEXT,
    "total_tax_cost" DOUBLE PRECISION,
    "tax_divisor" DOUBLE PRECISION,
    "tax_currency_code" TEXT,
    "total_vat_cost" DOUBLE PRECISION,
    "vat_divisor" DOUBLE PRECISION,
    "vat_currency_code" TEXT,
    "discount_amt" DOUBLE PRECISION,
    "discount_divisor" DOUBLE PRECISION,
    "discount_currency_code" TEXT,
    "gift_wrap_price" DOUBLE PRECISION,
    "gift_wrap_divisor" DOUBLE PRECISION,
    "gift_wrap_currency_code" TEXT,
    "item_count" BIGINT NOT NULL,
    "is_paid" BOOLEAN NOT NULL,
    "is_shipped" BOOLEAN NOT NULL,
    "is_gift" BOOLEAN,
    "status" TEXT,
    "payment_method" TEXT,
    "raw_transactions" TEXT,
    "raw_shipments" TEXT,
    "raw_refunds" TEXT,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "orders_pkey" PRIMARY KEY ("order_id")
);

-- CreateTable
CREATE TABLE "order_transactions" (
    "id" BIGSERIAL NOT NULL,
    "order_id" BIGINT NOT NULL,
    "transaction_id" BIGINT NOT NULL,
    "listing_id" BIGINT,
    "product_id" BIGINT,
    "sku" TEXT,
    "quantity" INTEGER NOT NULL,
    "price" DOUBLE PRECISION NOT NULL,
    "price_divisor" DOUBLE PRECISION,
    "currency_code" TEXT NOT NULL,
    "shipping_cost" DOUBLE PRECISION,
    "tax_cost" DOUBLE PRECISION,
    "variation_data" TEXT,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "order_transactions_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "order_shipments" (
    "id" BIGSERIAL NOT NULL,
    "order_id" BIGINT NOT NULL,
    "shipment_id" BIGINT,
    "carrier_name" TEXT,
    "tracking_code" TEXT,
    "tracking_url" TEXT,
    "shipped_timestamp" BIGINT,
    "note" TEXT,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "order_shipments_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "order_refunds" (
    "id" BIGSERIAL NOT NULL,
    "order_id" BIGINT NOT NULL,
    "refund_id" BIGINT,
    "amount" DOUBLE PRECISION NOT NULL,
    "amount_divisor" DOUBLE PRECISION,
    "currency_code" TEXT NOT NULL,
    "reason" TEXT,
    "note" TEXT,
    "status" TEXT,
    "created_timestamp" BIGINT,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "order_refunds_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ledger_entries" (
    "entry_id" BIGINT NOT NULL,
    "ledger_type" TEXT NOT NULL,
    "amount" DOUBLE PRECISION NOT NULL,
    "currency" TEXT NOT NULL,
    "created_timestamp" BIGINT NOT NULL,
    "description" TEXT NOT NULL,
    "related_payment_id" BIGINT,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "ledger_entries_pkey" PRIMARY KEY ("entry_id")
);

-- CreateTable
CREATE TABLE "reviews" (
    "id" BIGSERIAL NOT NULL,
    "transaction_id" BIGINT NOT NULL,
    "shop_id" BIGINT,
    "listing_id" BIGINT,
    "product_id" BIGINT,
    "buyer_user_id" BIGINT,
    "rating" BIGINT NOT NULL DEFAULT 0,
    "review_message" TEXT NOT NULL DEFAULT '',
    "language" TEXT NOT NULL DEFAULT '',
    "image_url_fullxfull" TEXT NOT NULL DEFAULT '',
    "created_timestamp" BIGINT,
    "updated_timestamp" BIGINT,
    "created_datetime" TIMESTAMP(3),
    "updated_datetime" TIMESTAMP(3),

    CONSTRAINT "reviews_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "listings" (
    "listing_id" BIGINT NOT NULL,
    "user_id" BIGINT,
    "shop_id" BIGINT,
    "title" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "tags" TEXT NOT NULL,
    "materials" TEXT,
    "state" TEXT NOT NULL,
    "price" DOUBLE PRECISION NOT NULL,
    "currency_code" TEXT NOT NULL,
    "quantity" BIGINT NOT NULL,
    "views" BIGINT,
    "num_favorers" BIGINT,
    "creation_timestamp" BIGINT NOT NULL,
    "creation_datetime" TIMESTAMP(3),
    "created_timestamp" BIGINT,
    "created_datetime" TIMESTAMP(3),
    "ending_timestamp" BIGINT,
    "original_creation_timestamp" BIGINT,
    "last_modified_timestamp" BIGINT,
    "last_modified_datetime" TIMESTAMP(3),
    "updated_timestamp" BIGINT,
    "updated_datetime" TIMESTAMP(3),
    "state_timestamp" BIGINT,
    "url" TEXT NOT NULL,
    "shop_section_id" BIGINT,
    "featured_rank" INTEGER,
    "non_taxable" BOOLEAN,
    "is_taxable" BOOLEAN,
    "is_customizable" BOOLEAN,
    "is_personalizable" BOOLEAN,
    "personalization_is_required" BOOLEAN,
    "personalization_char_count_max" INTEGER,
    "personalization_instructions" TEXT,
    "listing_type" TEXT,
    "shipping_profile_id" BIGINT,
    "return_policy_id" BIGINT,
    "processing_min" INTEGER,
    "processing_max" INTEGER,
    "who_made" TEXT,
    "when_made" TEXT,
    "is_supply" BOOLEAN,
    "item_weight" DOUBLE PRECISION,
    "item_weight_unit" TEXT,
    "item_length" DOUBLE PRECISION,
    "item_width" DOUBLE PRECISION,
    "item_height" DOUBLE PRECISION,
    "item_dimensions_unit" TEXT,
    "is_private" BOOLEAN,
    "style" TEXT,
    "file_data" TEXT,
    "has_variations" BOOLEAN,
    "should_auto_renew" BOOLEAN,
    "language" TEXT,
    "taxonomy_id" BIGINT,
    "readiness_state_id" BIGINT,
    "price_on_property" TEXT,
    "quantity_on_property" TEXT,
    "sku_on_property" TEXT,
    "readiness_state_on_property" TEXT,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "listings_pkey" PRIMARY KEY ("listing_id")
);

-- CreateTable
CREATE TABLE "listing_products" (
    "id" BIGSERIAL NOT NULL,
    "listing_id" BIGINT NOT NULL,
    "product_id" BIGINT NOT NULL,
    "sku" TEXT,
    "is_deleted" BOOLEAN NOT NULL DEFAULT false,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "listing_products_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "product_offerings" (
    "id" BIGSERIAL NOT NULL,
    "listing_product_id" BIGINT NOT NULL,
    "offering_id" BIGINT,
    "price" DOUBLE PRECISION NOT NULL,
    "price_divisor" DOUBLE PRECISION,
    "currency_code" TEXT NOT NULL,
    "quantity" INTEGER NOT NULL,
    "is_enabled" BOOLEAN NOT NULL DEFAULT true,
    "is_deleted" BOOLEAN NOT NULL DEFAULT false,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "product_offerings_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "product_property_values" (
    "id" BIGSERIAL NOT NULL,
    "listing_product_id" BIGINT NOT NULL,
    "property_id" BIGINT NOT NULL,
    "property_name" TEXT,
    "scale_id" BIGINT,
    "scale_name" TEXT,
    "value_ids" TEXT,
    "values" TEXT,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "product_property_values_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "shop_reports" (
    "id" BIGSERIAL NOT NULL,
    "periodType" "PeriodType" NOT NULL,
    "periodStart" TIMESTAMP(3) NOT NULL,
    "periodEnd" TIMESTAMP(3) NOT NULL,
    "periodDays" INTEGER NOT NULL DEFAULT 0,
    "totalRevenue" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "productRevenue" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "totalShippingRevenue" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "totalTaxCollected" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "totalVatCollected" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "totalGiftWrapRevenue" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "totalDiscountsGiven" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "netRevenue" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "discountRate" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "totalCost" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "avgCostPerItem" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "costPerOrder" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "grossProfit" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "grossMargin" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "netProfit" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "netMargin" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "returnOnRevenue" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "markupRatio" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "totalOrders" INTEGER NOT NULL DEFAULT 0,
    "totalItems" INTEGER NOT NULL DEFAULT 0,
    "totalQuantitySold" INTEGER NOT NULL DEFAULT 0,
    "uniqueSkus" INTEGER NOT NULL DEFAULT 0,
    "averageOrderValue" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "medianOrderValue" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "percentile_75_order_value" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "percentile_25_order_value" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "orderValueStd" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "itemsPerOrder" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "revenuePerItem" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "profitPerItem" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "uniqueCustomers" INTEGER NOT NULL DEFAULT 0,
    "repeatCustomers" INTEGER NOT NULL DEFAULT 0,
    "customerRetentionRate" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "revenuePerCustomer" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "ordersPerCustomer" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "profitPerCustomer" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "shippedOrders" INTEGER NOT NULL DEFAULT 0,
    "shippingRate" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "giftOrders" INTEGER NOT NULL DEFAULT 0,
    "giftRate" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "avgTimeBetweenOrdersHours" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "ordersPerDay" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "revenuePerDay" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "totalRefundAmount" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "totalRefundCount" INTEGER NOT NULL DEFAULT 0,
    "ordersWithRefunds" INTEGER NOT NULL DEFAULT 0,
    "refundRateByOrder" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "refundRateByValue" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "orderRefundRate" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "cancelledOrders" INTEGER NOT NULL DEFAULT 0,
    "cancellationRate" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "completionRate" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "primaryPaymentMethod" TEXT,
    "paymentMethodDiversity" INTEGER NOT NULL DEFAULT 0,
    "customerLifetimeValue" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "paybackPeriodDays" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "customerAcquisitionCost" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "priceElasticity" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "peakMonth" INTEGER,
    "peakDayOfWeek" INTEGER,
    "peakHour" INTEGER,
    "seasonalityIndex" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "totalInventory" INTEGER NOT NULL DEFAULT 0,
    "avgPrice" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "priceRange" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "activeVariants" INTEGER NOT NULL DEFAULT 0,
    "inventoryTurnover" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "stockoutRisk" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "shop_reports_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "listing_reports" (
    "id" BIGSERIAL NOT NULL,
    "listingId" BIGINT NOT NULL,
    "periodType" "PeriodType" NOT NULL,
    "periodStart" TIMESTAMP(3) NOT NULL,
    "periodEnd" TIMESTAMP(3) NOT NULL,
    "periodDays" INTEGER NOT NULL DEFAULT 0,
    "totalRevenue" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "productRevenue" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "totalShippingRevenue" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "totalTaxCollected" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "totalVatCollected" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "totalGiftWrapRevenue" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "totalDiscountsGiven" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "netRevenue" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "discountRate" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "totalCost" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "avgCostPerItem" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "costPerOrder" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "grossProfit" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "grossMargin" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "netProfit" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "netMargin" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "returnOnRevenue" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "markupRatio" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "totalOrders" INTEGER NOT NULL DEFAULT 0,
    "totalItems" INTEGER NOT NULL DEFAULT 0,
    "totalQuantitySold" INTEGER NOT NULL DEFAULT 0,
    "uniqueSkus" INTEGER NOT NULL DEFAULT 0,
    "averageOrderValue" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "medianOrderValue" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "percentile_75_order_value" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "percentile_25_order_value" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "orderValueStd" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "itemsPerOrder" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "revenuePerItem" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "profitPerItem" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "uniqueCustomers" INTEGER NOT NULL DEFAULT 0,
    "repeatCustomers" INTEGER NOT NULL DEFAULT 0,
    "customerRetentionRate" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "revenuePerCustomer" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "ordersPerCustomer" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "profitPerCustomer" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "shippedOrders" INTEGER NOT NULL DEFAULT 0,
    "shippingRate" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "giftOrders" INTEGER NOT NULL DEFAULT 0,
    "giftRate" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "avgTimeBetweenOrdersHours" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "ordersPerDay" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "revenuePerDay" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "totalRefundAmount" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "totalRefundCount" INTEGER NOT NULL DEFAULT 0,
    "ordersWithRefunds" INTEGER NOT NULL DEFAULT 0,
    "refundRateByOrder" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "refundRateByValue" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "orderRefundRate" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "cancelledOrders" INTEGER NOT NULL DEFAULT 0,
    "cancellationRate" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "completionRate" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "primaryPaymentMethod" TEXT,
    "paymentMethodDiversity" INTEGER NOT NULL DEFAULT 0,
    "customerLifetimeValue" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "paybackPeriodDays" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "customerAcquisitionCost" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "priceElasticity" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "peakMonth" INTEGER,
    "peakDayOfWeek" INTEGER,
    "peakHour" INTEGER,
    "seasonalityIndex" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "totalInventory" INTEGER NOT NULL DEFAULT 0,
    "avgPrice" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "priceRange" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "activeVariants" INTEGER NOT NULL DEFAULT 0,
    "inventoryTurnover" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "stockoutRisk" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "listingViews" INTEGER DEFAULT 0,
    "listingFavorites" INTEGER DEFAULT 0,
    "conversionRate" DOUBLE PRECISION DEFAULT 0,
    "favoriteToOrderRate" DOUBLE PRECISION DEFAULT 0,
    "viewToFavoriteRate" DOUBLE PRECISION DEFAULT 0,
    "revenuePerView" DOUBLE PRECISION DEFAULT 0,
    "profitPerView" DOUBLE PRECISION DEFAULT 0,
    "costPerAcquisition" DOUBLE PRECISION DEFAULT 0,
    "shopAvgViews" DOUBLE PRECISION DEFAULT 0,
    "shopAvgFavorites" DOUBLE PRECISION DEFAULT 0,
    "viewsVsShopAvg" DOUBLE PRECISION DEFAULT 0,
    "favoritesVsShopAvg" DOUBLE PRECISION DEFAULT 0,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "listing_reports_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "product_reports" (
    "id" BIGSERIAL NOT NULL,
    "sku" TEXT NOT NULL,
    "periodType" "PeriodType" NOT NULL,
    "periodStart" TIMESTAMP(3) NOT NULL,
    "periodEnd" TIMESTAMP(3) NOT NULL,
    "periodDays" INTEGER NOT NULL DEFAULT 0,
    "totalRevenue" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "productRevenue" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "totalShippingRevenue" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "totalTaxCollected" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "totalVatCollected" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "totalGiftWrapRevenue" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "totalDiscountsGiven" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "netRevenue" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "discountRate" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "totalCost" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "avgCostPerItem" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "costPerOrder" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "grossProfit" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "grossMargin" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "netProfit" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "netMargin" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "returnOnRevenue" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "markupRatio" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "totalOrders" INTEGER NOT NULL DEFAULT 0,
    "totalItems" INTEGER NOT NULL DEFAULT 0,
    "totalQuantitySold" INTEGER NOT NULL DEFAULT 0,
    "uniqueSkus" INTEGER NOT NULL DEFAULT 0,
    "averageOrderValue" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "medianOrderValue" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "percentile_75_order_value" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "percentile_25_order_value" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "orderValueStd" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "itemsPerOrder" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "revenuePerItem" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "profitPerItem" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "uniqueCustomers" INTEGER NOT NULL DEFAULT 0,
    "repeatCustomers" INTEGER NOT NULL DEFAULT 0,
    "customerRetentionRate" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "revenuePerCustomer" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "ordersPerCustomer" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "profitPerCustomer" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "shippedOrders" INTEGER NOT NULL DEFAULT 0,
    "shippingRate" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "giftOrders" INTEGER NOT NULL DEFAULT 0,
    "giftRate" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "avgTimeBetweenOrdersHours" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "ordersPerDay" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "revenuePerDay" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "totalRefundAmount" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "totalRefundCount" INTEGER NOT NULL DEFAULT 0,
    "ordersWithRefunds" INTEGER NOT NULL DEFAULT 0,
    "refundRateByOrder" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "refundRateByValue" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "orderRefundRate" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "cancelledOrders" INTEGER NOT NULL DEFAULT 0,
    "cancellationRate" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "completionRate" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "primaryPaymentMethod" TEXT,
    "paymentMethodDiversity" INTEGER NOT NULL DEFAULT 0,
    "customerLifetimeValue" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "paybackPeriodDays" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "customerAcquisitionCost" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "priceElasticity" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "peakMonth" INTEGER,
    "peakDayOfWeek" INTEGER,
    "peakHour" INTEGER,
    "seasonalityIndex" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "totalInventory" INTEGER NOT NULL DEFAULT 0,
    "avgPrice" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "priceRange" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "activeVariants" INTEGER NOT NULL DEFAULT 0,
    "inventoryTurnover" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "stockoutRisk" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "product_reports_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "order_transactions_transaction_id_key" ON "order_transactions"("transaction_id");

-- CreateIndex
CREATE UNIQUE INDEX "reviews_transaction_id_key" ON "reviews"("transaction_id");

-- CreateIndex
CREATE UNIQUE INDEX "listing_products_product_id_key" ON "listing_products"("product_id");

-- CreateIndex
CREATE UNIQUE INDEX "listing_products_listing_id_product_id_key" ON "listing_products"("listing_id", "product_id");

-- CreateIndex
CREATE UNIQUE INDEX "product_offerings_listing_product_id_offering_id_key" ON "product_offerings"("listing_product_id", "offering_id");

-- CreateIndex
CREATE UNIQUE INDEX "product_property_values_listing_product_id_property_id_key" ON "product_property_values"("listing_product_id", "property_id");

-- CreateIndex
CREATE UNIQUE INDEX "shop_reports_periodType_periodStart_periodEnd_key" ON "shop_reports"("periodType", "periodStart", "periodEnd");

-- CreateIndex
CREATE UNIQUE INDEX "listing_reports_listingId_periodType_periodStart_periodEnd_key" ON "listing_reports"("listingId", "periodType", "periodStart", "periodEnd");

-- CreateIndex
CREATE UNIQUE INDEX "product_reports_sku_periodType_periodStart_periodEnd_key" ON "product_reports"("sku", "periodType", "periodStart", "periodEnd");

-- AddForeignKey
ALTER TABLE "order_transactions" ADD CONSTRAINT "order_transactions_listing_id_fkey" FOREIGN KEY ("listing_id") REFERENCES "listings"("listing_id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "order_transactions" ADD CONSTRAINT "order_transactions_order_id_fkey" FOREIGN KEY ("order_id") REFERENCES "orders"("order_id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "order_transactions" ADD CONSTRAINT "order_transactions_product_id_fkey" FOREIGN KEY ("product_id") REFERENCES "listing_products"("product_id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "order_shipments" ADD CONSTRAINT "order_shipments_order_id_fkey" FOREIGN KEY ("order_id") REFERENCES "orders"("order_id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "order_refunds" ADD CONSTRAINT "order_refunds_order_id_fkey" FOREIGN KEY ("order_id") REFERENCES "orders"("order_id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "reviews" ADD CONSTRAINT "reviews_listing_id_fkey" FOREIGN KEY ("listing_id") REFERENCES "listings"("listing_id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "reviews" ADD CONSTRAINT "reviews_product_id_fkey" FOREIGN KEY ("product_id") REFERENCES "listing_products"("product_id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "reviews" ADD CONSTRAINT "reviews_transaction_id_fkey" FOREIGN KEY ("transaction_id") REFERENCES "order_transactions"("transaction_id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "listing_products" ADD CONSTRAINT "listing_products_listing_id_fkey" FOREIGN KEY ("listing_id") REFERENCES "listings"("listing_id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "product_offerings" ADD CONSTRAINT "product_offerings_listing_product_id_fkey" FOREIGN KEY ("listing_product_id") REFERENCES "listing_products"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "product_property_values" ADD CONSTRAINT "product_property_values_listing_product_id_fkey" FOREIGN KEY ("listing_product_id") REFERENCES "listing_products"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "listing_reports" ADD CONSTRAINT "listing_reports_listingId_fkey" FOREIGN KEY ("listingId") REFERENCES "listings"("listing_id") ON DELETE CASCADE ON UPDATE CASCADE;

