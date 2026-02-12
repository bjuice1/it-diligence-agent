#!/usr/bin/env python3
"""
Backfill missing entity values in InventoryStore.

This migration script fixes existing inventory items that have:
- entity = "" (empty string)
- entity = None (null)

Strategy:
1. Load all inventory stores from data/inventory_store.json
2. For each item with missing entity, infer from context:
   - If deal_id exists, get deal's primary entity (target)
   - If source_file contains "target" or "buyer", use that
   - Default to "target" if no other signals
3. Save updated inventory
4. Create audit log of changes

Run before deploying applications-enhancement Phase 1 to avoid EntityValidationError.

Usage:
    python migrations/backfill_inventory_entity.py [--dry-run] [--deal-id DEAL_ID]

Options:
    --dry-run    Show what would change without modifying data
    --deal-id    Only process specific deal (default: all deals)
"""

import sys
import os
import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from stores.inventory_store import InventoryStore
from stores.inventory_item import InventoryItem


def infer_entity(item: InventoryItem, deal_id: str = None) -> str:
    """
    Infer entity from context when missing.

    Priority:
    1. Check source_file for "target" or "buyer" keywords
    2. Default to "target" (most common)

    Args:
        item: InventoryItem with missing entity
        deal_id: Deal ID if known

    Returns:
        Inferred entity ("target" or "buyer")
    """
    # Check source file
    if item.source_file:
        source_lower = item.source_file.lower()
        if "buyer" in source_lower or "acquirer" in source_lower or "parent" in source_lower:
            return "buyer"
        if "target" in source_lower or "seller" in source_lower:
            return "target"

    # Check data fields for clues
    if item.data:
        # Check if any field contains entity hints
        for value in item.data.values():
            if isinstance(value, str):
                value_lower = value.lower()
                if "buyer" in value_lower or "acquirer" in value_lower:
                    return "buyer"

    # Default to target (most common in M&A diligence)
    return "target"


def backfill_inventory_entity(
    inventory_store: InventoryStore,
    deal_id: str,
    dry_run: bool = False
) -> Tuple[int, List[Dict]]:
    """
    Backfill missing entity values in inventory store.

    Args:
        inventory_store: InventoryStore instance
        deal_id: Deal ID being processed
        dry_run: If True, don't save changes

    Returns:
        (count_updated, audit_log)
    """
    updated_count = 0
    audit_log = []

    # Get all items
    all_items = inventory_store.get_items(status="active")

    for item in all_items:
        # Check if entity is missing or empty
        if not item.entity or item.entity.strip() == "":
            # Infer entity
            inferred_entity = infer_entity(item, deal_id)

            # Create audit entry
            audit_entry = {
                "item_id": item.item_id,
                "inventory_type": item.inventory_type,
                "name": item.name,
                "old_entity": item.entity or "(empty)",
                "new_entity": inferred_entity,
                "source_file": item.source_file,
                "inference_method": "source_file" if item.source_file else "default",
                "timestamp": datetime.utcnow().isoformat(),
            }
            audit_log.append(audit_entry)

            # Update entity
            if not dry_run:
                item.entity = inferred_entity
                inventory_store.update_item(item)

            updated_count += 1

    return updated_count, audit_log


def main():
    """Main migration execution."""
    parser = argparse.ArgumentParser(description="Backfill missing inventory entity values")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without applying")
    parser.add_argument("--deal-id", type=str, help="Only process specific deal ID")
    args = parser.parse_args()

    print("=" * 80)
    print("INVENTORY ENTITY BACKFILL MIGRATION")
    print("=" * 80)
    print()

    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be saved")
        print()

    # Find all inventory store files
    data_dir = Path(__file__).parent.parent / "data"
    inventory_files = list(data_dir.glob("**/inventory_store.json"))

    if not inventory_files:
        print("❌ No inventory_store.json files found")
        return

    print(f"Found {len(inventory_files)} inventory store file(s)")
    print()

    total_updated = 0
    all_audit_logs = []

    for inv_file in inventory_files:
        # Try to infer deal_id from path
        deal_id = None
        if "sessions" in str(inv_file):
            # Extract from path like: data/sessions/DEAL_ID/inventory_store.json
            parts = inv_file.parts
            if "sessions" in parts:
                idx = parts.index("sessions")
                if idx + 1 < len(parts):
                    deal_id = parts[idx + 1]

        # Skip if filtering by deal_id
        if args.deal_id and deal_id != args.deal_id:
            continue

        print(f"Processing: {inv_file}")
        print(f"  Deal ID: {deal_id or 'unknown'}")

        # Load inventory store
        try:
            inv_store = InventoryStore(deal_id=deal_id or "migration")
            # Load from file
            if inv_file.exists():
                with open(inv_file, 'r') as f:
                    data = json.load(f)
                    # Manually load items to avoid automatic validation
                    for item_data in data.get("items", []):
                        try:
                            item = InventoryItem.from_dict(item_data)
                            inv_store._items[item.item_id] = item
                        except Exception as e:
                            print(f"    ⚠️  Skipping invalid item: {e}")

            # Backfill
            updated, audit_log = backfill_inventory_entity(inv_store, deal_id, args.dry_run)

            print(f"  ✅ Updated {updated} item(s)")

            if updated > 0 and not args.dry_run:
                # Save updated inventory
                inv_store.save(str(inv_file))
                print(f"  💾 Saved to {inv_file}")

            total_updated += updated
            all_audit_logs.extend(audit_log)

        except Exception as e:
            print(f"  ❌ Error processing {inv_file}: {e}")
            import traceback
            traceback.print_exc()

        print()

    # Save audit log
    if all_audit_logs:
        audit_file = data_dir / f"inventory_entity_backfill_audit_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(audit_file, 'w') as f:
            json.dump(all_audit_logs, f, indent=2)
        print(f"📋 Audit log saved to: {audit_file}")
        print()

    print("=" * 80)
    print("MIGRATION COMPLETE")
    print("=" * 80)
    print()
    print(f"Total items updated: {total_updated}")

    if args.dry_run:
        print()
        print("⚠️  This was a DRY RUN - no changes were saved")
        print("   Run without --dry-run to apply changes")
    else:
        print()
        print("✅ Changes saved to inventory files")
        print("   Review audit log for details of what changed")

    print()

    # Show summary of changes
    if all_audit_logs:
        print("Summary of changes:")
        entity_counts = {"target": 0, "buyer": 0}
        for entry in all_audit_logs:
            entity_counts[entry["new_entity"]] += 1

        print(f"  - Set to 'target': {entity_counts['target']}")
        print(f"  - Set to 'buyer': {entity_counts['buyer']}")
        print()


if __name__ == "__main__":
    main()
