#!/usr/bin/env python3
"""Test script for SKU normalization logic."""

def normalize_sku_for_comparison(sku: str) -> str:
    """
    Normalize SKU for comparison by removing common prefixes and converting to lowercase.
    """
    if not sku:
        return sku
    
    prefixes_to_remove = [
        "DELETED-",
        "OT-",
        "ZSTK-",
        "MG-",
        "LND-",
        "EU-",
        "US-",
        "UK-",
        "CA-",
        "AU-",
        "JP-",
    ]
    
    normalized_sku = sku.strip()
    
    # Keep stripping prefixes until none match (handles multiple prefixes)
    # Compare case-insensitively by checking uppercase version
    changed = True
    while changed:
        changed = False
        for prefix in prefixes_to_remove:
            if normalized_sku.upper().startswith(prefix):
                normalized_sku = normalized_sku[len(prefix):]
                changed = True
                break
    
    # Convert to lowercase for case-insensitive comparison
    return normalized_sku.lower()


# Test cases
test_cases = [
    ("OT-WAL-Passport-Wallet-Black", "WAL-Passport-Wallet-Black"),
    ("WAL-Passport-Wallet-Black", "OT-WAL-Passport-Wallet-Black"),
    ("OT-Remote-Organizer-L.Brown", "Remote-Organizer-L.Brown"),
    ("Remote-Organizer-L.Brown", "OT-Remote-Organizer-L.Brown"),
    ("DELETED-OT-Some-SKU", "Some-SKU"),
    ("DELETED-US-Another-SKU", "Another-SKU"),
    ("EU-Product-Name", "US-Product-Name"),  # Should NOT match
    ("ot-test-sku", "OT-Test-SKU"),  # Case insensitive
]

print("Testing SKU Normalization Logic")
print("=" * 80)

for db_sku, csv_sku in test_cases:
    normalized_db = normalize_sku_for_comparison(db_sku)
    normalized_csv = normalize_sku_for_comparison(csv_sku)
    match = normalized_db == normalized_csv
    
    print(f"\nDB SKU:  '{db_sku}' → '{normalized_db}'")
    print(f"CSV SKU: '{csv_sku}' → '{normalized_csv}'")
    print(f"Match:   {'✅ YES' if match else '❌ NO'}")

print("\n" + "=" * 80)
print("✅ All test cases completed!")
