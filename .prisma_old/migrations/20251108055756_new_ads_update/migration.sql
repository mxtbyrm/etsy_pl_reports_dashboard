/*
  Warnings:

  - A unique constraint covering the columns `[listing_id,periodType,period_start,period_end]` on the table `listing_ad_stats` will be added. If there are existing duplicate values, this will fail.

*/
-- DropIndex
DROP INDEX "listing_ad_stats_listing_id_period_start_period_end_key";

-- AlterTable
ALTER TABLE "listing_ad_stats" ADD COLUMN     "periodType" "PeriodType" NOT NULL DEFAULT 'MONTHLY';

-- AlterTable
ALTER TABLE "listing_reports" ADD COLUMN     "ad_spend_rate" DOUBLE PRECISION NOT NULL DEFAULT 0,
ADD COLUMN     "roas" DOUBLE PRECISION NOT NULL DEFAULT 0,
ADD COLUMN     "total_ad_spend" DOUBLE PRECISION NOT NULL DEFAULT 0;

-- AlterTable
ALTER TABLE "shop_reports" ADD COLUMN     "ad_spend_rate" DOUBLE PRECISION NOT NULL DEFAULT 0,
ADD COLUMN     "roas" DOUBLE PRECISION NOT NULL DEFAULT 0,
ADD COLUMN     "total_ad_spend" DOUBLE PRECISION NOT NULL DEFAULT 0;

-- CreateIndex
CREATE UNIQUE INDEX "listing_ad_stats_listing_id_periodType_period_start_period__key" ON "listing_ad_stats"("listing_id", "periodType", "period_start", "period_end");
