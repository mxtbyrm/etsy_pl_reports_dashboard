-- CreateTable
CREATE TABLE "listing_ad_stats" (
    "id" BIGSERIAL NOT NULL,
    "listing_id" BIGINT NOT NULL,
    "period_start" TIMESTAMP(3) NOT NULL,
    "period_end" TIMESTAMP(3) NOT NULL,
    "impressions" BIGINT,
    "clicks" BIGINT,
    "orders" BIGINT,
    "revenue" DOUBLE PRECISION,
    "revenue_divisor" INTEGER,
    "revenue_currency_code" TEXT,
    "spend" DOUBLE PRECISION,
    "spend_divisor" INTEGER,
    "spend_currency_code" TEXT,
    "raw_stats" TEXT,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "listing_ad_stats_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "listing_visit_stats" (
    "id" BIGSERIAL NOT NULL,
    "listing_id" BIGINT NOT NULL,
    "periodType" "PeriodType" NOT NULL,
    "period_start" TIMESTAMP(3) NOT NULL,
    "period_end" TIMESTAMP(3) NOT NULL,
    "visits" BIGINT,
    "views" BIGINT,
    "orders" BIGINT,
    "revenue" DOUBLE PRECISION,
    "raw_response" TEXT,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "listing_visit_stats_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "listing_ad_stats_listing_id_period_start_period_end_key" ON "listing_ad_stats"("listing_id", "period_start", "period_end");

-- CreateIndex
CREATE UNIQUE INDEX "listing_visit_stats_listing_id_periodType_period_start_peri_key" ON "listing_visit_stats"("listing_id", "periodType", "period_start", "period_end");

-- AddForeignKey
ALTER TABLE "listing_ad_stats" ADD CONSTRAINT "listing_ad_stats_listing_id_fkey" FOREIGN KEY ("listing_id") REFERENCES "listings"("listing_id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "listing_visit_stats" ADD CONSTRAINT "listing_visit_stats_listing_id_fkey" FOREIGN KEY ("listing_id") REFERENCES "listings"("listing_id") ON DELETE CASCADE ON UPDATE CASCADE;
