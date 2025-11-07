#!/usr/bin/env python3
"""
Quick test script to verify cost lookup for 2025 dates
"""
import pandas as pd
import os

def test_cost_lookup():
    csv_path = "cost.csv"
    
    if not os.path.exists(csv_path):
        print(f"❌ Cost CSV not found: {csv_path}")
        return
    
    # Load the CSV
    df = pd.read_csv(csv_path, encoding='utf-8-sig')
    df.columns = df.columns.str.strip()
    
    print(f"✅ Loaded cost.csv with {len(df)} SKUs")
    print(f"📊 Total columns: {len(df.columns)}")
    
    # Test with first SKU that has data
    if df.empty or 'SKU' not in df.columns:
        print("❌ No SKUs found in CSV")
        return
    
    test_sku = df[df['SKU'].notna()]['SKU'].iloc[0]
    print(f"\n🔍 Testing with SKU: {test_sku}")
    
    sku_row = df[df['SKU'] == test_sku]
    
    # Test 2025 months
    test_dates = [
        (2025, 1, "OCAK"),   # January
        (2025, 2, "SUBAT"),  # February
        (2025, 3, "MART"),   # March
        (2025, 4, "NISAN"),  # April
        (2025, 5, "MAYIS"),  # May
    ]
    
    print("\n" + "="*80)
    print("Testing 2025 cost lookups:")
    print("="*80)
    
    for year, month, month_name in test_dates:
        year_2digit = year % 100
        
        # All possible column formats
        possible_cols = [
            f"US {month_name} {year}",      # US MAYIS 2025
            f"US {month_name} {year_2digit}",  # US MART 25
            f"US {year} {month_name}",      # US 2025 MART
            f"US {year_2digit} {month_name}",  # US 25 MART
        ]
        
        found = False
        for col in possible_cols:
            if col in sku_row.columns:
                value = sku_row[col].values[0]
                if pd.notna(value):
                    try:
                        cost = float(value)
                        print(f"✅ {year}/{month:02d} ({month_name:8s}): ${cost:7.2f} (column: '{col}')")
                        found = True
                        break
                    except:
                        pass
        
        if not found:
            print(f"❌ {year}/{month:02d} ({month_name:8s}): NOT FOUND")
            print(f"   Tried columns: {possible_cols}")
    
    # Show available 2025 columns
    print("\n" + "="*80)
    print("Available 2025 columns in CSV:")
    print("="*80)
    cols_2025 = [col for col in df.columns if '2025' in col or ' 25' in col]
    for col in sorted(cols_2025)[:20]:  # Show first 20
        print(f"  - {col}")
    
    if len(cols_2025) > 20:
        print(f"  ... and {len(cols_2025) - 20} more")

if __name__ == "__main__":
    test_cost_lookup()
