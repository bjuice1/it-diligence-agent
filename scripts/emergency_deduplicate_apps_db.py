#!/usr/bin/env python3
"""
Emergency Deduplication Script for Application Inventory (Database Version)

Works with PostgreSQL database used by web interface.
This version connects directly to the database instead of using file-based InventoryStore.

USAGE:
    python scripts/emergency_deduplicate_apps_db.py <deal_id>

EXAMPLE:
    python scripts/emergency_deduplicate_apps_db.py bca38f6d-73d3-455f-8aa1-3575b511fef9

SAFETY:
    - Creates backup before modification
    - Dry-run mode available with --dry-run flag
    - Logs all actions for audit trail
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Flask app setup
from flask import Flask
from web.database import db, Deal
from web.app import app  # Use existing Flask app

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DeduplicationReport:
    """Track deduplication actions for reporting."""

    def __init__(self):
        self.duplicates_found: List[Dict] = []
        self.items_deleted: List[str] = []
        self.facts_merged: List[Tuple[str, str]] = []
        self.errors: List[str] = []

    def add_duplicate(self, original_id: str, duplicate_id: str, app_name: str, entity: str):
        self.duplicates_found.append({
            'app_name': app_name,
            'entity': entity,
            'original_id': original_id,
            'duplicate_id': duplicate_id
        })

    def add_deletion(self, item_id: str, app_name: str):
        self.items_deleted.append(item_id)
        logger.info(f"  Deleted duplicate: {item_id} ({app_name})")

    def add_fact_merge(self, from_id: str, to_id: str):
        self.facts_merged.append((from_id, to_id))

    def add_error(self, error: str):
        self.errors.append(error)
        logger.error(f"  ERROR: {error}")

    def summary(self) -> str:
        lines = [
            "\n" + "=" * 80,
            "DEDUPLICATION SUMMARY",
            "=" * 80,
            f"Duplicates found: {len(self.duplicates_found)}",
            f"Items deleted: {len(self.items_deleted)}",
            f"Fact links merged: {len(self.facts_merged)}",
            f"Errors: {len(self.errors)}",
            "=" * 80,
        ]

        if self.duplicates_found:
            lines.append("\nDUPLICATES DETECTED:")
            by_app = defaultdict(list)
            for dup in self.duplicates_found:
                key = (dup['app_name'], dup['entity'])
                by_app[key].append(dup)

            for (app_name, entity), dups in sorted(by_app.items()):
                lines.append(f"\n  {app_name} ({entity}): {len(dups) + 1} copies")
                for dup in dups:
                    lines.append(f"    - {dup['duplicate_id']} (duplicate of {dup['original_id']})")

        if self.errors:
            lines.append("\nERRORS:")
            for err in self.errors:
                lines.append(f"  - {err}")

        return "\n".join(lines)


def normalize_app_key(item_data: Dict) -> Tuple[str, str]:
    """
    Create normalized deduplication key for an application.

    Args:
        item_data: Dict with 'name' and 'entity' keys

    Returns:
        Tuple of (normalized_name, entity) for deduplication
    """
    # Normalize name: lowercase, strip whitespace, remove special chars
    name = item_data['name'].lower().strip()
    # Remove common suffixes that don't affect identity
    name = name.replace(' inc.', '').replace(' llc', '').replace(' corp', '')
    name = name.replace('.com', '').replace('.io', '')

    return (name, item_data.get('entity', 'target'))


def backup_inventory_data(deal_id: str) -> Path:
    """
    Create backup of inventory data before modification.

    Args:
        deal_id: Deal ID for naming

    Returns:
        Path to backup file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = Path(f"output/deals/{deal_id}/backups")
    backup_dir.mkdir(parents=True, exist_ok=True)

    backup_path = backup_dir / f"inventory_db_backup_{timestamp}.json"

    # Query all inventory items for this deal
    with app.app_context():
        # Import here to avoid circular imports
        from stores.inventory_store import InventoryStore
        store = InventoryStore(deal_id=deal_id)

        backup_data = {
            'deal_id': deal_id,
            'timestamp': timestamp,
            'items': []
        }

        # Get all items
        all_items = store.get_items(status="active")
        for item in all_items:
            backup_data['items'].append({
                'item_id': item.item_id,
                'inventory_type': item.inventory_type,
                'name': item.name,
                'entity': item.entity,
                'data': item.data,
                'source_fact_ids': item.source_fact_ids
            })

        # Save backup
        with open(backup_path, 'w') as f:
            json.dump(backup_data, f, indent=2)

    logger.info(f"✅ Created backup: {backup_path} ({len(backup_data['items'])} items)")
    return backup_path


def find_duplicates(deal_id: str) -> Dict[Tuple[str, str], List[Dict]]:
    """
    Find duplicate applications by normalized (name, entity).

    Args:
        deal_id: Deal ID to analyze

    Returns:
        Dict mapping (normalized_name, entity) to list of item dicts
    """
    duplicates_map: Dict[Tuple[str, str], List[Dict]] = defaultdict(list)

    with app.app_context():
        from stores.inventory_store import InventoryStore
        store = InventoryStore(deal_id=deal_id)

        # Get all application items
        app_items = store.get_items(inventory_type="application", status="active")

        for item in app_items:
            item_dict = {
                'item_id': item.item_id,
                'name': item.name,
                'entity': item.entity,
                'data': item.data,
                'source_fact_ids': item.source_fact_ids,
                'item_obj': item
            }
            key = normalize_app_key({'name': item.name, 'entity': item.entity})
            duplicates_map[key].append(item_dict)

    # Filter to only keys with duplicates
    return {k: v for k, v in duplicates_map.items() if len(v) > 1}


def deduplicate_applications(
    deal_id: str,
    dry_run: bool = False
) -> DeduplicationReport:
    """
    Remove duplicate applications from database.

    Strategy:
    1. Group apps by normalized (name, entity)
    2. For each group with >1 item:
        a. Keep first item as "canonical"
        b. Merge source_fact_ids from duplicates into canonical
        c. Delete duplicate items

    Args:
        deal_id: Deal ID to deduplicate
        dry_run: If True, report duplicates but don't modify

    Returns:
        DeduplicationReport with results
    """
    report = DeduplicationReport()

    logger.info(f"🔍 Scanning for duplicates (dry_run={dry_run})...")

    duplicates_map = find_duplicates(deal_id)

    if not duplicates_map:
        logger.info("✅ No duplicates found!")
        return report

    logger.info(f"⚠️  Found {len(duplicates_map)} applications with duplicates")

    with app.app_context():
        from stores.inventory_store import InventoryStore
        store = InventoryStore(deal_id=deal_id)

        for (normalized_name, entity), items in duplicates_map.items():
            # Sort by item_id for deterministic ordering
            items = sorted(items, key=lambda x: x['item_id'])

            canonical = items[0]
            duplicates = items[1:]

            logger.info(f"\n📦 Processing: {canonical['name']} ({entity})")
            logger.info(f"  Canonical ID: {canonical['item_id']}")
            logger.info(f"  Duplicates: {len(duplicates)}")

            for dup in duplicates:
                report.add_duplicate(
                    original_id=canonical['item_id'],
                    duplicate_id=dup['item_id'],
                    app_name=canonical['name'],
                    entity=entity
                )

                if not dry_run:
                    try:
                        # Merge fact links into canonical
                        canonical_item = canonical['item_obj']
                        for fact_id in dup['source_fact_ids']:
                            if fact_id not in canonical_item.source_fact_ids:
                                canonical_item.source_fact_ids.append(fact_id)
                                report.add_fact_merge(dup['item_id'], canonical['item_id'])

                        # Delete duplicate
                        store.remove_item(dup['item_id'])
                        report.add_deletion(dup['item_id'], dup['name'])

                    except Exception as e:
                        error_msg = f"Failed to merge {dup['item_id']}: {e}"
                        report.add_error(error_msg)

        # Save changes if not dry-run
        if not dry_run and report.duplicates_found:
            store.save()

    return report


def verify_deduplication(deal_id: str) -> bool:
    """
    Verify no duplicates remain after deduplication.

    Args:
        deal_id: Deal ID to verify

    Returns:
        True if clean, False if duplicates still exist
    """
    logger.info("\n🔍 Verifying deduplication...")

    duplicates_map = find_duplicates(deal_id)

    if duplicates_map:
        logger.error(f"❌ VERIFICATION FAILED: {len(duplicates_map)} duplicates still exist!")
        for (name, entity), items in duplicates_map.items():
            logger.error(f"  - {name} ({entity}): {len(items)} copies")
        return False

    logger.info("✅ Verification passed: No duplicates found")
    return True


def calculate_user_count_impact(
    deal_id: str,
    before_count: int
) -> Dict[str, int]:
    """
    Calculate impact of deduplication on user counts.

    Args:
        deal_id: Deal ID
        before_count: Total user count before deduplication

    Returns:
        Dict with before/after/reduction stats
    """
    with app.app_context():
        from stores.inventory_store import InventoryStore
        store = InventoryStore(deal_id=deal_id)

        app_items = store.get_items(inventory_type="application", status="active")

        after_count = 0
        for item in app_items:
            # Parse user count from data
            user_count = item.data.get('users', 0)
            if isinstance(user_count, str):
                # Try to parse numeric
                import re
                match = re.search(r'(\d+)', user_count.replace(',', ''))
                if match:
                    user_count = int(match.group(1))
                else:
                    user_count = 0
            after_count += int(user_count or 0)

    reduction = before_count - after_count

    return {
        'before': before_count,
        'after': after_count,
        'reduction': reduction,
        'reduction_pct': (reduction / before_count * 100) if before_count > 0 else 0
    }


def main():
    """Main execution."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Emergency deduplication for application inventory (database version)"
    )
    parser.add_argument(
        'deal_id',
        help='Deal ID to deduplicate (e.g., bca38f6d-73d3-455f-8aa1-3575b511fef9)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Report duplicates but do not modify data'
    )
    parser.add_argument(
        '--skip-backup',
        action='store_true',
        help='Skip backup creation (not recommended)'
    )

    args = parser.parse_args()

    deal_id = args.deal_id
    dry_run = args.dry_run

    logger.info("=" * 80)
    logger.info("EMERGENCY APPLICATION DEDUPLICATION (DATABASE VERSION)")
    logger.info("=" * 80)
    logger.info(f"Deal ID: {deal_id}")
    logger.info(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    logger.info("=" * 80)

    # Get before stats
    with app.app_context():
        from stores.inventory_store import InventoryStore
        store = InventoryStore(deal_id=deal_id)

        app_items_before = store.get_items(inventory_type="application", status="active")
        total_users_before = 0
        for item in app_items_before:
            user_count = item.data.get('users', 0)
            if isinstance(user_count, str):
                import re
                match = re.search(r'(\d+)', user_count.replace(',', ''))
                if match:
                    user_count = int(match.group(1))
                else:
                    user_count = 0
            total_users_before += int(user_count or 0)

        logger.info(f"\nBEFORE DEDUPLICATION:")
        logger.info(f"  Applications: {len(app_items_before)}")
        logger.info(f"  Total Users: {total_users_before:,}")

    # Create backup
    if not dry_run and not args.skip_backup:
        try:
            backup_path = backup_inventory_data(deal_id)
        except Exception as e:
            logger.error(f"❌ Backup failed: {e}")
            return 1

    # Run deduplication
    report = deduplicate_applications(deal_id, dry_run=dry_run)

    # Verify
    if not dry_run and report.duplicates_found:
        if not verify_deduplication(deal_id):
            return 1

    # Get after stats
    if not dry_run and report.duplicates_found:
        impact = calculate_user_count_impact(deal_id, total_users_before)

        logger.info(f"\nAFTER DEDUPLICATION:")
        with app.app_context():
            from stores.inventory_store import InventoryStore
            store = InventoryStore(deal_id=deal_id)
            app_items_after = store.get_items(inventory_type="application", status="active")
            logger.info(f"  Applications: {len(app_items_after)}")
        logger.info(f"  Total Users: {impact['after']:,}")
        logger.info(f"  REDUCTION: {impact['reduction']:,} users ({impact['reduction_pct']:.1f}%)")

    # Print summary
    print(report.summary())

    if dry_run:
        logger.info("\n⚠️  DRY RUN MODE - No changes were made")
        logger.info("Run without --dry-run to apply deduplication")

    return 0 if not report.errors else 1


if __name__ == "__main__":
    sys.exit(main())
