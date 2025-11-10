#!/usr/bin/env python3
"""
Test SKU normalization and OTTOKOD mapping to diagnose why shipping costs are zero.

This script:
1. Shows how SKU normalization works
2. Tests SKU -> OTTOKOD -> Desi lookup chain
3. Verifies CSV data is loaded correctly
4. Shows example lookups with different SKU formats
"""

import pandas as pd
from pathlib import Path

def normalize_sku(sku: str) -> str:
    """Normalize SKU by removing common prefixes (same logic as in reportsv4_optimized.py)"""
    if not sku:
        return sku
    
    prefixes_to_remove = [
        "DELETED-", "OT-", "ZSTK-", "MG-", "LND-",
        "EU-", "US-", "UK-", "CA-", "AU-", "JP-",
    ]
    
    normalized_sku = sku.strip()
    
    # Keep stripping prefixes until none match
    changed = True
    while changed:
        changed = False
        for prefix in prefixes_to_remove:
            if normalized_sku.upper().startswith(prefix):
                normalized_sku = normalized_sku[len(prefix):]
                changed = True
                break
    
    return normalized_sku.lower()

def test_normalization():
    """Test the normalization function with various SKU formats."""
    print("\n" + "="*80)
    print("SKU NORMALIZATION TEST")
    print("="*80)
    
    test_cases = [
        "MacBag",
        "OT-MacBag",
        "OT-ZSTK-MacBag",
        "DELETED-OT-MacBag",
        "US-MacBag",
        "ot-macbag",  # lowercase
        "Remote-Organizer",
        "OT-Remote-Organizer",
    ]
    
    print("\nShowing how different SKU formats normalize to the same value:\n")
    for sku in test_cases:
        normalized = normalize_sku(sku)
        print(f"  {sku:35s} → {normalized}")
    
    print("\n✓ All variants of the same product should normalize to the same value")
    print("  This allows matching even when prefixes differ between database and CSV\n")

def test_sku_to_ottokod_mapping():
    """Test SKU to OTTOKOD mapping from cost.csv"""
    print("\n" + "="*80)
    print("SKU → OTTOKOD MAPPING TEST (from cost.csv)")
    print("="*80)
    
    cost_csv = Path("cost.csv")
    if not cost_csv.exists():
        print(f"\n❌ ERROR: {cost_csv} not found!")
        return None, None
    
    # Load cost.csv
    try:
        cost_data = pd.read_csv(cost_csv, encoding='utf-8')
        print(f"\n✓ Loaded cost.csv: {len(cost_data)} rows")
        print(f"  Columns: {list(cost_data.columns)}\n")
    except Exception as e:
        print(f"\n❌ ERROR loading cost.csv: {e}")
        return None, None
    
    # Check required columns
    if 'SKU' not in cost_data.columns or 'OTTOKOD' not in cost_data.columns:
        print(f"❌ ERROR: cost.csv missing required columns!")
        print(f"   Expected: 'SKU' and 'OTTOKOD'")
        print(f"   Found: {list(cost_data.columns)}")
        return None, None
    
    # Build mappings (both raw and normalized)
    sku_to_ottokod = {}
    sku_to_ottokod_normalized = {}
    
    for _, row in cost_data.iterrows():
        sku = row.get('SKU')
        ottokod = row.get('OTTOKOD')
        
        if pd.notna(sku) and pd.notna(ottokod):
            sku_clean = str(sku).strip()
            ottokod_clean = str(ottokod).strip()
            
            # Raw mapping
            sku_to_ottokod[sku_clean] = ottokod_clean
            
            # Normalized mapping
            normalized = normalize_sku(sku_clean)
            if normalized:
                sku_to_ottokod_normalized[normalized] = ottokod_clean
    
    print(f"✓ Built SKU → OTTOKOD mapping:")
    print(f"  Raw mappings: {len(sku_to_ottokod)}")
    print(f"  Normalized mappings: {len(sku_to_ottokod_normalized)}")
    
    # Show first 10 examples
    print(f"\n  First 10 mappings (showing both raw and normalized):")
    for i, (sku, ottokod) in enumerate(list(sku_to_ottokod.items())[:10]):
        normalized = normalize_sku(sku)
        print(f"    {sku:30s} → {ottokod:15s} (normalized: {normalized})")
    
    return sku_to_ottokod, sku_to_ottokod_normalized

def test_desi_lookup(sku_to_ottokod, sku_to_ottokod_normalized):
    """Test OTTOKOD → Desi lookup from all_products_desi.csv"""
    print("\n" + "="*80)
    print("OTTOKOD → DESI LOOKUP TEST (from all_products_desi.csv)")
    print("="*80)
    
    desi_csv = Path("all_products_desi.csv")
    if not desi_csv.exists():
        print(f"\n❌ ERROR: {desi_csv} not found!")
        return
    
    # Load desi CSV
    try:
        desi_data = pd.read_csv(desi_csv, encoding='utf-8', decimal=',')
        print(f"\n✓ Loaded all_products_desi.csv: {len(desi_data)} rows")
        print(f"  Columns: {list(desi_data.columns)}\n")
    except Exception as e:
        print(f"\n❌ ERROR loading all_products_desi.csv: {e}")
        return
    
    # Check if it has OTTOKOD column
    if 'OTTOKOD' not in desi_data.columns:
        print(f"❌ ERROR: all_products_desi.csv missing 'OTTOKOD' column!")
        print(f"   Found columns: {list(desi_data.columns)}")
        return
    
    if 'DESİ' not in desi_data.columns and 'DESI' not in desi_data.columns:
        print(f"❌ ERROR: all_products_desi.csv missing 'DESİ' or 'DESI' column!")
        print(f"   Found columns: {list(desi_data.columns)}")
        return
    
    # Normalize column names
    desi_col = 'DESİ' if 'DESİ' in desi_data.columns else 'DESI'
    
    print(f"✓ CSV structure is correct:")
    print(f"  - Has OTTOKOD column: ✓")
    print(f"  - Has {desi_col} column: ✓")
    
    # Show first 10 rows
    print(f"\n  First 10 rows:")
    for i, row in desi_data.head(10).iterrows():
        ottokod = row.get('OTTOKOD', 'N/A')
        desi = row.get(desi_col, 'N/A')
        print(f"    OTTOKOD: {ottokod:20s} → {desi_col}: {desi}")
    
    # Test full lookup chain: SKU → OTTOKOD → Desi
    print(f"\n" + "="*80)
    print("FULL LOOKUP CHAIN TEST: SKU → OTTOKOD → DESI")
    print("="*80)
    
    if not sku_to_ottokod:
        print("\n⚠️  No SKU mappings available (cost.csv issue)")
        return
    
    # Test with first 5 SKUs from cost.csv
    test_skus = list(sku_to_ottokod.keys())[:5]
    
    print(f"\nTesting lookup chain with {len(test_skus)} SKUs:\n")
    
    for sku in test_skus:
        print(f"  SKU: {sku}")
        
        # Step 1: Exact lookup
        ottokod = sku_to_ottokod.get(sku)
        print(f"    ├─ Exact SKU → OTTOKOD: {ottokod}")
        
        # Step 2: Normalized lookup
        normalized = normalize_sku(sku)
        ottokod_normalized = sku_to_ottokod_normalized.get(normalized)
        print(f"    ├─ Normalized '{normalized}' → OTTOKOD: {ottokod_normalized}")
        
        # Step 3: OTTOKOD → Desi lookup
        if ottokod:
            desi_row = desi_data[desi_data['OTTOKOD'].str.strip() == str(ottokod).strip()]
            if not desi_row.empty:
                desi_value = desi_row.iloc[0][desi_col]
                print(f"    └─ OTTOKOD '{ottokod}' → Desi: {desi_value} kg ✓")
            else:
                print(f"    └─ OTTOKOD '{ottokod}' NOT FOUND in desi CSV ❌")
        else:
            print(f"    └─ No OTTOKOD found ❌")
        print()

def test_us_shipping_lookup():
    """Test US shipping costs lookup from us_fedex_desi_and_price.csv"""
    print("\n" + "="*80)
    print("US SHIPPING COSTS LOOKUP TEST (from us_fedex_desi_and_price.csv)")
    print("="*80)
    
    us_csv = Path("us_fedex_desi_and_price.csv")
    if not us_csv.exists():
        print(f"\n❌ ERROR: {us_csv} not found!")
        return
    
    # Load US shipping CSV
    try:
        us_data = pd.read_csv(us_csv, encoding='utf-8')
        print(f"\n✓ Loaded us_fedex_desi_and_price.csv: {len(us_data)} rows")
        print(f"  Columns: {list(us_data.columns)}\n")
    except Exception as e:
        print(f"\n❌ ERROR loading us_fedex_desi_and_price.csv: {e}")
        return
    
    # Check which identifier column it has
    has_sku = 'SKU' in us_data.columns
    has_ottokod = 'OTTOKOD' in us_data.columns
    
    print(f"✓ CSV identifier columns:")
    print(f"  - Has SKU column: {'✓' if has_sku else '❌'}")
    print(f"  - Has OTTOKOD column: {'✓' if has_ottokod else '❌'}")
    
    if not has_sku and not has_ottokod:
        print(f"\n❌ ERROR: CSV has neither SKU nor OTTOKOD column!")
        print(f"   Cannot identify products!")
        return
    
    # Check for cost columns
    expected_columns = [
        'US FEDEX KARGO ÜCRETİ',
        'FEDEX İŞLEM ÜCRETİ',
        'DUTY',
        'DUTY OTAN',
        'VERGİ',
        'VERGİ ORANI'
    ]
    
    print(f"\n  Checking cost columns:")
    for col in expected_columns:
        exists = col in us_data.columns
        print(f"    - {col:30s}: {'✓' if exists else '❌ MISSING'}")
    
    # Show first 5 rows
    print(f"\n  First 5 rows:")
    identifier_col = 'SKU' if has_sku else 'OTTOKOD'
    for i, row in us_data.head(5).iterrows():
        identifier = row.get(identifier_col, 'N/A')
        fedex = row.get('US FEDEX KARGO ÜCRETİ', 0)
        duty = row.get('DUTY', 0)
        tax = row.get('VERGİ', 0)
        print(f"    {identifier_col}: {identifier:20s} → FedEx: ${fedex:6.2f}, Duty: ${duty:6.2f}, Tax: ${tax:6.2f}")

def main():
    """Run all diagnostic tests."""
    print("\n" + "="*80)
    print("SKU NORMALIZATION & MAPPING DIAGNOSTIC")
    print("="*80)
    print("\nThis script tests the full lookup chain:")
    print("  1. SKU normalization (removes prefixes)")
    print("  2. SKU → OTTOKOD mapping (from cost.csv)")
    print("  3. OTTOKOD → Desi lookup (from all_products_desi.csv)")
    print("  4. SKU/OTTOKOD → US shipping costs (from us_fedex_desi_and_price.csv)")
    
    # Test 1: Normalization
    test_normalization()
    
    # Test 2: SKU → OTTOKOD mapping
    sku_to_ottokod, sku_to_ottokod_normalized = test_sku_to_ottokod_mapping()
    
    # Test 3: OTTOKOD → Desi lookup
    test_desi_lookup(sku_to_ottokod, sku_to_ottokod_normalized)
    
    # Test 4: US shipping lookup
    test_us_shipping_lookup()
    
    print("\n" + "="*80)
    print("DIAGNOSTIC COMPLETE")
    print("="*80)
    print("\nKey findings to check:")
    print("  1. Are SKUs normalizing correctly?")
    print("  2. Does cost.csv have SKU → OTTOKOD mappings?")
    print("  3. Can we find OTTOKOD in all_products_desi.csv?")
    print("  4. Does us_fedex_desi_and_price.csv have cost data?")
    print("\nIf any step fails, shipping costs will be zero!\n")

if __name__ == "__main__":
    main()
