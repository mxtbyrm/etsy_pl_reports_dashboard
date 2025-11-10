#!/usr/bin/env python3
"""
Quick script to check for zero-cost reports in the database.
"""
import asyncio
from prisma import Prisma

async def check_zero_costs():
    prisma = Prisma()
    await prisma.connect()
    
    try:
        print("🔍 Checking for zero-cost reports...\n")
        
        # Check product reports
        zero_cost_products = await prisma.productreport.count(
            where={"totalCost": 0}
        )
        total_products = await prisma.productreport.count()
        print(f"📦 Product Reports:")
        print(f"   Total: {total_products}")
        print(f"   Zero-cost: {zero_cost_products}")
        print(f"   Status: {'✅ GOOD' if zero_cost_products == 0 else '❌ BAD'}\n")
        
        # Check listing reports
        zero_cost_listings = await prisma.listingreport.count(
            where={"totalCost": 0}
        )
        total_listings = await prisma.listingreport.count()
        print(f"📋 Listing Reports:")
        print(f"   Total: {total_listings}")
        print(f"   Zero-cost: {zero_cost_listings}")
        print(f"   Status: {'✅ GOOD' if zero_cost_listings == 0 else '❌ BAD'}\n")
        
        # Check shop reports
        zero_cost_shops = await prisma.shopreport.count(
            where={"totalCost": 0}
        )
        total_shops = await prisma.shopreport.count()
        print(f"🏪 Shop Reports:")
        print(f"   Total: {total_shops}")
        print(f"   Zero-cost: {zero_cost_shops}")
        print(f"   Status: {'✅ GOOD' if zero_cost_shops == 0 else '❌ BAD'}\n")
        
        # Overall summary
        total_zero = zero_cost_products + zero_cost_listings + zero_cost_shops
        total_all = total_products + total_listings + total_shops
        
        print("=" * 50)
        print(f"📊 Overall Summary:")
        print(f"   Total reports: {total_all}")
        print(f"   Zero-cost reports: {total_zero}")
        
        if total_zero == 0:
            print(f"\n✅ SUCCESS! No zero-cost reports found!")
            print(f"   All {total_all} reports have valid cost data.")
        else:
            print(f"\n❌ WARNING! Found {total_zero} zero-cost reports.")
            print(f"   This indicates the validation may not be working correctly.")
            
            # Show some examples
            if zero_cost_products > 0:
                examples = await prisma.productreport.find_many(
                    where={"totalCost": 0},
                    take=5
                )
                print(f"\n   Example zero-cost products:")
                for ex in examples:
                    print(f"   - SKU: {ex.sku}, Period: {ex.periodType}, Orders: {ex.totalOrders}")
        
    finally:
        await prisma.disconnect()

if __name__ == "__main__":
    asyncio.run(check_zero_costs())
