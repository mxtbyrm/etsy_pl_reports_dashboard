#!/usr/bin/env python3
"""
Diagnostic script to check all CSV files are loaded correctly and show data samples.
"""
import pandas as pd
import os

def check_csv(file_path, separator=',', expected_columns=None, encoding='utf-8-sig'):
    """Check if CSV exists and show first few rows."""
    print(f"\n{'='*80}")
    print(f"📄 Checking: {file_path}")
    print(f"{'='*80}")
    
    if not os.path.exists(file_path):
        print(f"❌ FILE NOT FOUND: {file_path}")
        return False
    
    file_size = os.path.getsize(file_path)
    print(f"✓ File exists, size: {file_size:,} bytes")
    
    try:
        # Try to read the CSV
        df = pd.read_csv(file_path, sep=separator, encoding=encoding, nrows=5)
        df.columns = df.columns.str.strip()
        
        print(f"✓ Loaded successfully")
        print(f"📊 Shape: {len(df)} rows (showing first 5) x {len(df.columns)} columns")
        print(f"\n📋 Columns: {list(df.columns)}")
        
        if expected_columns:
            missing = set(expected_columns) - set(df.columns)
            if missing:
                print(f"\n⚠️  Missing expected columns: {missing}")
            else:
                print(f"✓ All expected columns present")
        
        print(f"\n📝 First 5 rows:")
        print(df.to_string(index=False))
        
        # Check for empty values
        empty_counts = df.isnull().sum()
        if empty_counts.any():
            print(f"\n⚠️  Empty/null values per column:")
            for col, count in empty_counts[empty_counts > 0].items():
                print(f"  - {col}: {count}/{len(df)} empty")
        
        # Load full file to get actual count
        df_full = pd.read_csv(file_path, sep=separator, encoding=encoding)
        print(f"\n✓ Full file: {len(df_full):,} total rows")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR reading file: {e}")
        return False

def main():
    print("\n" + "="*80)
    print("🔍 CSV DATA VERIFICATION TOOL")
    print("="*80)
    
    csv_files = [
        {
            'path': 'cost.csv',
            'sep': ',',
            'expected': ['SKU', 'OTTOKOD'],
            'description': 'Product cost data (COGS)'
        },
        {
            'path': 'all_products_desi.csv',
            'sep': ';',
            'expected': ['SKU', 'DESİ'],
            'description': 'Product weights (desi)'
        },
        {
            'path': 'fedex_country_code_and_zone_number.csv',
            'sep': ';',
            'expected': None,
            'description': 'Country to FedEx zone mapping'
        },
        {
            'path': 'fedex_price_per_kg_for_zones.csv',
            'sep': ';',
            'expected': None,
            'description': 'FedEx pricing matrix (weight x zone)'
        },
        {
            'path': 'us_fedex_desi_and_price.csv',
            'sep': ';',
            'expected': ['SKU', 'US FEDEX KARGO ÜCRETİ'],
            'description': 'US-specific shipping costs with duties/taxes'
        }
    ]
    
    results = {}
    for csv_info in csv_files:
        print(f"\n\n📦 {csv_info['description']}")
        success = check_csv(
            csv_info['path'], 
            separator=csv_info['sep'],
            expected_columns=csv_info['expected']
        )
        results[csv_info['path']] = success
    
    # Summary
    print(f"\n\n{'='*80}")
    print("📊 SUMMARY")
    print(f"{'='*80}")
    
    for file_path, success in results.items():
        status = "✅ OK" if success else "❌ FAILED"
        print(f"{status} - {file_path}")
    
    all_ok = all(results.values())
    if all_ok:
        print(f"\n✅ ALL CSV FILES ARE LOADED CORRECTLY!")
    else:
        print(f"\n⚠️  SOME CSV FILES HAVE ISSUES - CHECK ABOVE FOR DETAILS")
        print(f"\nℹ️  Missing or problematic CSV files will cause:")
        print(f"  - Missing cost data → Zero-cost reports")
        print(f"  - Missing shipping data → Zero shipping costs in reports")
        print(f"  - Missing zone/pricing data → Incorrect international shipping calculations")
    
    print(f"\n{'='*80}\n")

if __name__ == "__main__":
    main()
