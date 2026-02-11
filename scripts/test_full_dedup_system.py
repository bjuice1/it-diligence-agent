#!/usr/bin/env python3
"""
Full System Deduplication Test

Tests deduplication logic across ALL inventory types to ensure:
1. No duplicates exist in any inventory type
2. Fingerprint collision prevention works correctly
3. Entity scoping is properly maintained

This is the comprehensive test that should be run after the dedup fix.
"""

import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

from stores.inventory_store import InventoryStore
from stores.inventory_schemas import INVENTORY_SCHEMAS


def normalize_key(item_data: Dict, inv_type: str) -> Tuple:
    """
    Create normalized deduplication key for any inventory type.

    Uses same normalization logic as emergency dedup script.
    """
    name_field = "name" if inv_type != "vendor" else "vendor_name"
    name = item_data.get(name_field, "").lower().strip()

    # Normalize company suffixes
    name = name.replace(' inc.', '').replace(' llc', '').replace(' corp', '')
    name = name.replace('.com', '').replace('.io', '').replace(' corporation', '')

    entity = item_data.get('entity', 'target')

    return (name, entity)


def scan_for_duplicates(deal_id: str) -> Dict[str, Dict]:
    """
    Scan ALL inventory types for duplicates.

    Returns:
        Dict mapping inventory_type to duplicate findings
    """
    store = InventoryStore(deal_id=deal_id)

    results = {}

    for inv_type in INVENTORY_SCHEMAS.keys():
        items = store.get_items(inventory_type=inv_type, status="active")

        # Group by normalized key
        duplicates_map = defaultdict(list)
        for item in items:
            # Create dict for normalization
            item_dict = {
                "name": item.name,
                "vendor_name": item.data.get("vendor_name", item.name),
                "entity": item.entity
            }

            key = normalize_key(item_dict, inv_type)
            duplicates_map[key].append({
                'item_id': item.item_id,
                'name': item.name,
                'entity': item.entity,
                'data': item.data
            })

        # Filter to actual duplicates
        duplicates = {k: v for k, v in duplicates_map.items() if len(v) > 1}

        results[inv_type] = {
            'total_items': len(items),
            'duplicates_count': len(duplicates),
            'duplicates': duplicates,
            'items_to_delete': sum(len(v) - 1 for v in duplicates.values())
        }

    return results


def test_fingerprint_fields() -> Dict[str, Dict]:
    """
    Test that all id_fields are properly validated.

    Returns vulnerability assessment for each inventory type.
    """
    vulnerabilities = {}

    for inv_type, schema in INVENTORY_SCHEMAS.items():
        id_fields = schema["id_fields"]
        required = schema["required"]

        # Check if any id_field is optional
        optional_id_fields = [f for f in id_fields if f not in required]

        vulnerabilities[inv_type] = {
            'id_fields': id_fields,
            'required_fields': required,
            'vulnerable_fields': optional_id_fields,
            'is_vulnerable': len(optional_id_fields) > 0
        }

    return vulnerabilities


def test_entity_propagation(deal_id: str) -> Dict[str, int]:
    """
    Test that entity field is properly propagated.

    Checks for items with null/missing entity field.
    """
    store = InventoryStore(deal_id=deal_id)

    entity_stats = {
        'total_items': 0,
        'target_items': 0,
        'buyer_items': 0,
        'null_entity': 0,
        'invalid_entity': 0
    }

    for inv_type in INVENTORY_SCHEMAS.keys():
        items = store.get_items(inventory_type=inv_type, status="active")

        for item in items:
            entity_stats['total_items'] += 1

            if item.entity == 'target':
                entity_stats['target_items'] += 1
            elif item.entity == 'buyer':
                entity_stats['buyer_items'] += 1
            elif item.entity is None or item.entity == '':
                entity_stats['null_entity'] += 1
            else:
                entity_stats['invalid_entity'] += 1

    return entity_stats


def print_report(deal_id: str):
    """Generate comprehensive deduplication test report."""

    print("=" * 80)
    print("FULL SYSTEM DEDUPLICATION TEST REPORT")
    print("=" * 80)
    print(f"Deal ID: {deal_id}")
    print()

    # TEST 1: Fingerprint Vulnerability Assessment
    print("TEST 1: FINGERPRINT VULNERABILITY ASSESSMENT")
    print("-" * 80)

    vulnerabilities = test_fingerprint_fields()
    total_vulnerable = sum(1 for v in vulnerabilities.values() if v['is_vulnerable'])

    for inv_type, vuln in vulnerabilities.items():
        status = "⚠️  VULNERABLE" if vuln['is_vulnerable'] else "✅ SAFE"
        print(f"{status} - {inv_type.upper()}")
        print(f"         ID Fields: {vuln['id_fields']}")
        print(f"         Required: {vuln['required_fields']}")
        if vuln['vulnerable_fields']:
            print(f"         🔴 Optional but used for ID: {vuln['vulnerable_fields']}")
        print()

    print(f"SUMMARY: {total_vulnerable}/4 inventory types vulnerable to fingerprint collision")
    print()

    # TEST 2: Duplicate Scan
    print("TEST 2: DUPLICATE DETECTION ACROSS ALL INVENTORY TYPES")
    print("-" * 80)

    dup_results = scan_for_duplicates(deal_id)

    total_duplicates = sum(r['duplicates_count'] for r in dup_results.values())
    total_to_delete = sum(r['items_to_delete'] for r in dup_results.values())

    for inv_type, result in dup_results.items():
        if result['duplicates_count'] > 0:
            print(f"⚠️  {inv_type.upper()}: {result['duplicates_count']} apps with duplicates")
            print(f"   Total items: {result['total_items']}")
            print(f"   Items to delete: {result['items_to_delete']}")

            # Show first 5 duplicates
            for (name, entity), dups in list(result['duplicates'].items())[:5]:
                print(f"   → {name} ({entity}): {len(dups)} copies")
                for dup in dups[:3]:  # Show first 3 IDs
                    print(f"      - {dup['item_id']}")

            if result['duplicates_count'] > 5:
                print(f"   ... and {result['duplicates_count'] - 5} more")
            print()
        else:
            print(f"✅ {inv_type.upper()}: No duplicates ({result['total_items']} items)")

    print()
    print(f"SUMMARY: {total_duplicates} unique items with duplicates, {total_to_delete} items to delete")
    print()

    # TEST 3: Entity Propagation
    print("TEST 3: ENTITY PROPAGATION VALIDATION")
    print("-" * 80)

    entity_stats = test_entity_propagation(deal_id)

    print(f"Total items: {entity_stats['total_items']}")
    print(f"Target items: {entity_stats['target_items']}")
    print(f"Buyer items: {entity_stats['buyer_items']}")

    if entity_stats['null_entity'] > 0:
        print(f"⚠️  NULL ENTITY: {entity_stats['null_entity']} items with null/empty entity!")
    else:
        print(f"✅ No null entities")

    if entity_stats['invalid_entity'] > 0:
        print(f"⚠️  INVALID ENTITY: {entity_stats['invalid_entity']} items with invalid entity!")
    else:
        print(f"✅ No invalid entities")

    print()

    # FINAL VERDICT
    print("=" * 80)
    print("FINAL VERDICT")
    print("=" * 80)

    all_passed = (
        total_duplicates == 0 and
        entity_stats['null_entity'] == 0 and
        entity_stats['invalid_entity'] == 0
    )

    if all_passed:
        print("✅ ALL TESTS PASSED - System is clean")
        print()
        print("However, note that 4/4 inventory types are vulnerable to")
        print("fingerprint collision if source data has corrupt optional fields.")
        print()
        print("Recommendation: Add validation to ensure id_fields are never empty.")
    else:
        print("❌ TESTS FAILED - Issues detected")
        print()
        if total_duplicates > 0:
            print(f"  🔴 {total_duplicates} items have duplicates - run deduplication")
        if entity_stats['null_entity'] > 0:
            print(f"  🔴 {entity_stats['null_entity']} items missing entity field")
        if entity_stats['invalid_entity'] > 0:
            print(f"  🔴 {entity_stats['invalid_entity']} items have invalid entity")

    print("=" * 80)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Test deduplication system across all inventory types"
    )
    parser.add_argument(
        'deal_id',
        help='Deal ID to test'
    )

    args = parser.parse_args()
    print_report(args.deal_id)


if __name__ == "__main__":
    main()
