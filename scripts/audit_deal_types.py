#!/usr/bin/env python3
"""
Audit existing deal_type values in database.

Reports:
- NULL deal_type count
- Invalid deal_type values
- Deal type distribution
- Detailed list of problematic deals

Usage:
    python scripts/audit_deal_types.py [--json]
"""

import sys
import os
import argparse
import json
from collections import Counter
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from web.database import init_db, Deal

# Valid deal types
VALID_DEAL_TYPES = ['acquisition', 'carveout', 'divestiture']


def audit_deal_types(output_json: bool = False):
    """
    Audit deal_type field across all deals.

    Args:
        output_json: If True, output results as JSON instead of formatted text

    Returns:
        dict: Audit results
    """
    # Initialize database
    try:
        from web.app import app
        with app.app_context():
            return _run_audit(output_json)
    except Exception as e:
        print(f"Failed to initialize app context: {e}", file=sys.stderr)
        print("Trying direct database initialization...", file=sys.stderr)
        init_db()
        return _run_audit(output_json)


def _run_audit(output_json: bool = False):
    """Run audit within database context."""

    # Query all deals (including soft-deleted)
    all_deals = Deal.query.all()
    active_deals = Deal.query.filter(Deal.deleted_at.is_(None)).all()

    # Count NULL values
    null_count = sum(1 for d in active_deals if d.deal_type is None or d.deal_type == '')

    # Count invalid values (not in valid set)
    invalid_deals = [
        d for d in active_deals
        if d.deal_type not in VALID_DEAL_TYPES and d.deal_type is not None and d.deal_type != ''
    ]
    invalid_count = len(invalid_deals)

    # Distribution of deal types
    deal_type_dist = Counter(
        d.deal_type if d.deal_type else 'NULL'
        for d in active_deals
    )

    # Build results
    results = {
        'audit_timestamp': datetime.utcnow().isoformat(),
        'total_deals': len(all_deals),
        'active_deals': len(active_deals),
        'deleted_deals': len(all_deals) - len(active_deals),
        'null_count': null_count,
        'invalid_count': invalid_count,
        'distribution': dict(deal_type_dist),
        'invalid_deals': [
            {
                'id': d.id,
                'name': d.name,
                'deal_type': d.deal_type,
                'created_at': d.created_at.isoformat() if d.created_at else None
            }
            for d in invalid_deals
        ],
        'null_deals': [
            {
                'id': d.id,
                'name': d.name,
                'created_at': d.created_at.isoformat() if d.created_at else None
            }
            for d in active_deals
            if d.deal_type is None or d.deal_type == ''
        ]
    }

    # Calculate health score
    if len(active_deals) > 0:
        valid_count = len(active_deals) - null_count - invalid_count
        health_pct = (valid_count / len(active_deals)) * 100
        results['health_score'] = {
            'valid_deals': valid_count,
            'percentage': round(health_pct, 1),
            'status': 'HEALTHY' if health_pct >= 90 else 'NEEDS_ATTENTION' if health_pct >= 70 else 'CRITICAL'
        }
    else:
        results['health_score'] = {
            'valid_deals': 0,
            'percentage': 0,
            'status': 'NO_DATA'
        }

    # Output results
    if output_json:
        print(json.dumps(results, indent=2))
    else:
        _print_formatted_results(results)

    return results


def _print_formatted_results(results: dict):
    """Print results in human-readable format."""

    print("\n" + "="*60)
    print("DEAL TYPE AUDIT REPORT")
    print("="*60)
    print(f"Audit Date: {results['audit_timestamp']}")
    print()

    print("SUMMARY")
    print("-"*60)
    print(f"Total deals (all):       {results['total_deals']}")
    print(f"Active deals:            {results['active_deals']}")
    print(f"Deleted deals:           {results['deleted_deals']}")
    print(f"NULL deal_type:          {results['null_count']}")
    print(f"Invalid deal_type:       {results['invalid_count']}")
    print()

    print("HEALTH SCORE")
    print("-"*60)
    health = results['health_score']
    print(f"Valid deals:             {health['valid_deals']}/{results['active_deals']}")
    print(f"Percentage:              {health['percentage']}%")
    print(f"Status:                  {health['status']}")
    print()

    print("DISTRIBUTION")
    print("-"*60)
    for deal_type, count in sorted(results['distribution'].items(), key=lambda x: -x[1]):
        pct = (count / results['active_deals'] * 100) if results['active_deals'] > 0 else 0
        status_icon = "✓" if deal_type in VALID_DEAL_TYPES else "⚠" if deal_type == "NULL" else "✗"
        print(f"  {status_icon} {deal_type:20s} {count:4d} ({pct:5.1f}%)")
    print()

    # List NULL deals
    if results['null_count'] > 0:
        print("NULL DEAL_TYPE DEALS (will be backfilled to 'acquisition')")
        print("-"*60)
        for deal in results['null_deals'][:10]:  # Show first 10
            print(f"  - {deal['name']} (ID: {deal['id']})")
        if len(results['null_deals']) > 10:
            print(f"  ... and {len(results['null_deals']) - 10} more")
        print()

    # List invalid deals
    if results['invalid_count'] > 0:
        print("INVALID DEAL_TYPE DEALS (will be normalized to 'acquisition')")
        print("-"*60)
        for deal in results['invalid_deals']:
            print(f"  - {deal['name']} (ID: {deal['id']}): deal_type='{deal['deal_type']}'")
        print()

    # Migration recommendation
    print("MIGRATION RECOMMENDATION")
    print("-"*60)
    if results['null_count'] > 0 or results['invalid_count'] > 0:
        print(f"⚠ Action required: {results['null_count'] + results['invalid_count']} deals need normalization")
        print()
        print("Run migration to:")
        print("  1. Backfill NULL values to 'acquisition'")
        print("  2. Normalize invalid values to 'acquisition'")
        print("  3. Add NOT NULL constraint")
        print("  4. Add CHECK constraint")
        print()
        print("Command:")
        print("  flask db upgrade")
    else:
        print("✓ All deals have valid deal_type values")
        print("  Migration can proceed safely")

    print("="*60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Audit deal_type values in database'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results as JSON'
    )

    args = parser.parse_args()

    try:
        results = audit_deal_types(output_json=args.json)

        # Exit with error code if health score is critical
        if results['health_score']['status'] == 'CRITICAL':
            sys.exit(1)
        else:
            sys.exit(0)

    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
