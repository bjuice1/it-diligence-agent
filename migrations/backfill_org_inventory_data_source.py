"""
Migration: Backfill data_source field for existing organization inventory items

This script backfills the data_source field for existing organization inventory
items to prepare for the new fingerprinting logic (spec 10).

CRITICAL: Run this migration BEFORE deploying code with updated id_fields.
Otherwise, existing items will have different fingerprints and appear duplicated.

Usage:
    python -m migrations.backfill_org_inventory_data_source

    Or from code:
    from migrations.backfill_org_inventory_data_source import backfill_existing_org_inventory
    backfill_existing_org_inventory()

Status: Part of spec 10 (P0 fix #1 - Fingerprint Breaking Change)
"""

import logging
import sys
import os
from pathlib import Path

# Add parent directory to path so we can import from stores/
sys.path.insert(0, str(Path(__file__).parent.parent))

from stores.inventory_store import InventoryStore
from stores.fact_store import FactStore
from web.database import SessionLocal, Deal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def backfill_existing_org_inventory(dry_run: bool = False):
    """
    Backfill data_source field for existing organization inventory items.

    Algorithm:
        1. For each deal in database
        2. Load InventoryStore for that deal
        3. Find all organization items
        4. Add data_source='observed' to items missing the field
        5. Add entity='target' if missing (per CLAUDE.md requirement)
        6. Add confidence_score=1.0 if missing (observed data is high confidence)
        7. Save updated store

    Args:
        dry_run: If True, log changes but don't save. Default False.

    Returns:
        dict with stats: {
            'deals_processed': int,
            'items_updated': int,
            'items_skipped': int (already had data_source)
        }
    """
    stats = {
        'deals_processed': 0,
        'items_updated': 0,
        'items_skipped': 0,
        'errors': []
    }

    logger.info("Starting backfill for organization inventory data_source field")
    if dry_run:
        logger.info("DRY RUN MODE - no changes will be saved")

    # Get all deals from database
    db = SessionLocal()
    try:
        deals = db.query(Deal).filter(Deal.deleted_at.is_(None)).all()
        logger.info(f"Found {len(deals)} active deals")

        for deal in deals:
            deal_id = deal.deal_id
            logger.info(f"Processing deal: {deal_id} ({deal.target_name})")

            try:
                # Load inventory store for this deal
                store = InventoryStore(deal_id=deal_id)

                # Get all organization items
                org_items = [
                    item for item in store._items.values()
                    if item.inventory_type == "organization"
                ]

                logger.info(f"  Found {len(org_items)} organization items")

                items_updated_this_deal = 0
                for item in org_items:
                    # Check if data_source already exists
                    if 'data_source' in item.data and item.data['data_source']:
                        stats['items_skipped'] += 1
                        continue

                    # Backfill data_source
                    item.data['data_source'] = 'observed'

                    # Backfill confidence_score if missing
                    if 'confidence_score' not in item.data:
                        item.data['confidence_score'] = 1.0

                    # Backfill entity if missing (CRITICAL per CLAUDE.md)
                    if 'entity' not in item.data or not item.data.get('entity'):
                        # Try to infer from item context or default to target
                        item.data['entity'] = item.entity if hasattr(item, 'entity') and item.entity else 'target'
                        logger.warning(
                            f"  Item {item.item_id} missing entity field, "
                            f"defaulted to {item.data['entity']}"
                        )

                    stats['items_updated'] += 1
                    items_updated_this_deal += 1

                    logger.debug(
                        f"  Updated item {item.item_id}: "
                        f"data_source=observed, entity={item.data.get('entity')}"
                    )

                # Save updated store (unless dry run)
                if not dry_run and items_updated_this_deal > 0:
                    store.save()
                    logger.info(f"  Saved {items_updated_this_deal} updated items for deal {deal_id}")

                stats['deals_processed'] += 1

            except Exception as e:
                logger.error(f"  Error processing deal {deal_id}: {e}")
                stats['errors'].append({'deal_id': deal_id, 'error': str(e)})
                continue

    finally:
        db.close()

    # Log summary
    logger.info("=" * 60)
    logger.info("BACKFILL SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Deals processed:    {stats['deals_processed']}")
    logger.info(f"Items updated:      {stats['items_updated']}")
    logger.info(f"Items skipped:      {stats['items_skipped']}")
    logger.info(f"Errors:             {len(stats['errors'])}")

    if stats['errors']:
        logger.error("\nErrors encountered:")
        for err in stats['errors']:
            logger.error(f"  Deal {err['deal_id']}: {err['error']}")

    if dry_run:
        logger.info("\nDRY RUN - No changes were saved")
    else:
        logger.info("\nBackfill complete")

    return stats


def verify_backfill():
    """
    Verify that all organization items now have data_source field.

    Returns:
        dict with verification results: {
            'total_items': int,
            'items_with_data_source': int,
            'items_missing_data_source': List[str] (item IDs)
        }
    """
    logger.info("Verifying backfill...")

    verification = {
        'total_items': 0,
        'items_with_data_source': 0,
        'items_missing_data_source': []
    }

    db = SessionLocal()
    try:
        deals = db.query(Deal).filter(Deal.deleted_at.is_(None)).all()

        for deal in deals:
            store = InventoryStore(deal_id=deal.deal_id)
            org_items = [
                item for item in store._items.values()
                if item.inventory_type == "organization"
            ]

            for item in org_items:
                verification['total_items'] += 1

                if 'data_source' in item.data and item.data['data_source']:
                    verification['items_with_data_source'] += 1
                else:
                    verification['items_missing_data_source'].append(item.item_id)

    finally:
        db.close()

    # Log results
    logger.info("=" * 60)
    logger.info("VERIFICATION RESULTS")
    logger.info("=" * 60)
    logger.info(f"Total org items:           {verification['total_items']}")
    logger.info(f"Items with data_source:    {verification['items_with_data_source']}")
    logger.info(f"Items missing data_source: {len(verification['items_missing_data_source'])}")

    if verification['items_missing_data_source']:
        logger.warning("\nItems still missing data_source:")
        for item_id in verification['items_missing_data_source'][:10]:
            logger.warning(f"  {item_id}")
        if len(verification['items_missing_data_source']) > 10:
            logger.warning(f"  ... and {len(verification['items_missing_data_source']) - 10} more")

    success = len(verification['items_missing_data_source']) == 0
    if success:
        logger.info("\n✅ Verification PASSED - all items have data_source")
    else:
        logger.error("\n❌ Verification FAILED - some items missing data_source")

    return verification


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Backfill data_source field for organization inventory (spec 10)"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Log changes but don't save (default: False)"
    )
    parser.add_argument(
        '--verify',
        action='store_true',
        help="Verify backfill after running (default: False)"
    )

    args = parser.parse_args()

    # Run backfill
    stats = backfill_existing_org_inventory(dry_run=args.dry_run)

    # Run verification if requested
    if args.verify and not args.dry_run:
        print("\n")
        verify_backfill()

    # Exit with error code if there were errors
    if stats['errors']:
        sys.exit(1)
