#!/usr/bin/env python3
"""
Snapshot existing deal outputs for regression comparison.

Captures:
- Cost estimates
- Synergy recommendations
- Narrative excerpts

For comparison after migration to ensure backward compatibility.

Usage:
    python scripts/snapshot_existing_deals.py [--output FILE]

Output file defaults to: data/pre_migration_snapshots.json
                    (or data/post_migration_snapshots.json if --post flag used)
"""

import json
import os
import sys
import argparse
import logging
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from web.database import init_db, Deal, db, AnalysisRun
from stores.inventory_store import InventoryStore
from stores.fact_store import FactStore
from services.cost_service import calculate_all_costs

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def snapshot_deal_outputs(output_file: str = None):
    """
    Snapshot outputs for all existing deals.

    Args:
        output_file: Path to save snapshot JSON. If None, uses default.

    Returns:
        dict: Snapshot results with success/error counts
    """
    logger.info("Starting deal output snapshot process...")

    # Initialize database connection
    try:
        from web.app import app
        with app.app_context():
            _run_snapshot(output_file)
    except Exception as e:
        logger.error(f"Failed to initialize app context: {e}")
        logger.info("Trying direct database initialization...")
        init_db()
        _run_snapshot(output_file)


def _run_snapshot(output_file: str = None):
    """Run snapshot within database context."""

    # Query all non-deleted deals
    deals = Deal.query.filter(Deal.deleted_at.is_(None)).all()

    logger.info(f"Found {len(deals)} deals to snapshot")

    if len(deals) == 0:
        logger.warning("No deals found in database!")
        return

    snapshots = []
    success_count = 0
    error_count = 0

    for i, deal in enumerate(deals, 1):
        logger.info(f"[{i}/{len(deals)}] Snapshotting deal: {deal.name} (ID: {deal.id})")

        try:
            # Get the most recent successful analysis run
            latest_run = AnalysisRun.query.filter(
                AnalysisRun.deal_id == deal.id,
                AnalysisRun.status == 'completed'
            ).order_by(AnalysisRun.completed_at.desc()).first()

            if not latest_run:
                logger.warning(f"  No completed analysis runs found for {deal.name}")
                snapshots.append({
                    'deal_id': deal.id,
                    'deal_name': deal.name,
                    'deal_type': deal.deal_type,
                    'status': 'no_analysis_run',
                    'error': 'No completed analysis runs found'
                })
                error_count += 1
                continue

            # Load inventory store from latest run
            inv_store = InventoryStore(deal_id=deal.id)

            # Load fact store
            fact_store = FactStore(deal_id=deal.id)

            # Calculate costs
            cost_result = calculate_all_costs(
                inv_store=inv_store,
                fact_store=fact_store,
                deal_type=deal.deal_type or 'acquisition'
            )

            # Extract synergies from cost result
            synergies = cost_result.get('synergies', [])

            # Build snapshot
            snapshot = {
                'deal_id': deal.id,
                'deal_name': deal.name,
                'deal_type': deal.deal_type or 'NULL',
                'status': 'success',
                'timestamp': datetime.utcnow().isoformat(),
                'analysis_run_id': latest_run.id,
                'metrics': {
                    'cost_total': cost_result.get('total_cost', 0),
                    'cost_by_phase': cost_result.get('by_phase', {}),
                    'synergy_count': len(synergies),
                    'synergy_types': list(set(s.get('type', 'unknown') for s in synergies)),
                    'work_item_count': len(cost_result.get('work_items', [])),
                    'inventory_counts': {
                        'applications': len(inv_store.get_all_items('application')),
                        'infrastructure': len(inv_store.get_all_items('infrastructure')),
                        'network': len(inv_store.get_all_items('network')),
                        'cybersecurity': len(inv_store.get_all_items('cybersecurity')),
                        'identity': len(inv_store.get_all_items('identity'))
                    },
                    'fact_count': len(fact_store.get_all_facts())
                }
            }

            # Add sample synergies (first 3)
            if synergies:
                snapshot['sample_synergies'] = synergies[:3]

            snapshots.append(snapshot)
            success_count += 1
            logger.info(f"  ✓ Snapshotted successfully (cost: ${snapshot['metrics']['cost_total']:,.0f})")

        except Exception as e:
            logger.error(f"  ✗ Failed to snapshot {deal.name}: {e}")
            snapshots.append({
                'deal_id': deal.id,
                'deal_name': deal.name,
                'deal_type': deal.deal_type,
                'status': 'error',
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e)
            })
            error_count += 1

    # Determine output file
    if not output_file:
        output_file = 'data/pre_migration_snapshots.json'

    # Ensure directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Save to file
    output_data = {
        'snapshot_date': datetime.utcnow().isoformat(),
        'total_deals': len(deals),
        'success_count': success_count,
        'error_count': error_count,
        'snapshots': snapshots
    }

    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)

    # Print summary
    logger.info("\n" + "="*60)
    logger.info("SNAPSHOT COMPLETE")
    logger.info("="*60)
    logger.info(f"Total deals: {len(deals)}")
    logger.info(f"Successful: {success_count}")
    logger.info(f"Errors: {error_count}")
    logger.info(f"Output saved to: {output_file}")
    logger.info("="*60)

    return output_data


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Snapshot deal outputs for migration regression testing'
    )
    parser.add_argument(
        '--output', '-o',
        help='Output file path (default: data/pre_migration_snapshots.json)'
    )
    parser.add_argument(
        '--post',
        action='store_true',
        help='Use post-migration default filename'
    )

    args = parser.parse_args()

    # Determine output file
    if args.output:
        output_file = args.output
    elif args.post:
        output_file = 'data/post_migration_snapshots.json'
    else:
        output_file = 'data/pre_migration_snapshots.json'

    try:
        result = snapshot_deal_outputs(output_file)

        # Exit with error code if any snapshots failed
        if result['error_count'] > 0:
            sys.exit(1)
        else:
            sys.exit(0)

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
