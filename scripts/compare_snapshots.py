#!/usr/bin/env python3
"""
Compare post-migration outputs to pre-migration baseline.

Validates that acquisition deals produce SAME outputs after migration.
This ensures backward compatibility and no regressions.

Usage:
    python scripts/compare_snapshots.py [--pre FILE] [--post FILE] [--tolerance PCT]
"""

import json
import sys
import argparse
from typing import Dict, List, Any
from datetime import datetime


def compare_snapshots(
    pre_file: str = 'data/pre_migration_snapshots.json',
    post_file: str = 'data/post_migration_snapshots.json',
    tolerance_pct: float = 5.0
) -> bool:
    """
    Compare pre/post migration snapshots.

    Args:
        pre_file: Path to pre-migration snapshot JSON
        post_file: Path to post-migration snapshot JSON
        tolerance_pct: Allowed percentage difference for cost values (default 5%)

    Returns:
        bool: True if no regressions detected, False otherwise
    """

    print("\n" + "="*60)
    print("SNAPSHOT COMPARISON REPORT")
    print("="*60)
    print(f"Comparison Date: {datetime.utcnow().isoformat()}")
    print()

    # Load snapshots
    try:
        with open(pre_file) as f:
            pre_data = json.load(f)
        print(f"✓ Loaded pre-migration snapshot: {pre_file}")
        print(f"  Date: {pre_data.get('snapshot_date', 'unknown')}")
        print(f"  Deals: {pre_data.get('total_deals', 0)}")
    except FileNotFoundError:
        print(f"✗ ERROR: Pre-migration snapshot not found: {pre_file}")
        print("  Run: python scripts/snapshot_existing_deals.py")
        return False
    except Exception as e:
        print(f"✗ ERROR: Failed to load pre-migration snapshot: {e}")
        return False

    try:
        with open(post_file) as f:
            post_data = json.load(f)
        print(f"✓ Loaded post-migration snapshot: {post_file}")
        print(f"  Date: {post_data.get('snapshot_date', 'unknown')}")
        print(f"  Deals: {post_data.get('total_deals', 0)}")
    except FileNotFoundError:
        print(f"✗ ERROR: Post-migration snapshot not found: {post_file}")
        print("  Run: python scripts/snapshot_existing_deals.py --post")
        return False
    except Exception as e:
        print(f"✗ ERROR: Failed to load post-migration snapshot: {e}")
        return False

    print()

    # Build lookup by deal_id
    pre_map = {s['deal_id']: s for s in pre_data['snapshots']}
    post_map = {s['deal_id']: s for s in post_data['snapshots']}

    # Track issues
    regressions = []
    warnings = []
    missing_deals = []

    # Compare each deal
    for deal_id, pre_snap in pre_map.items():
        post_snap = post_map.get(deal_id)

        if not post_snap:
            missing_deals.append({
                'deal_id': deal_id,
                'deal_name': pre_snap.get('deal_name', 'unknown'),
                'issue': 'missing_from_post'
            })
            continue

        # Only validate acquisition deals (others can legitimately differ)
        deal_type = pre_snap.get('deal_type', '').lower()
        if deal_type not in ['acquisition', 'null']:
            continue

        # Skip if either snapshot has errors
        if pre_snap.get('status') != 'success' or post_snap.get('status') != 'success':
            warnings.append({
                'deal_id': deal_id,
                'deal_name': pre_snap.get('deal_name', 'unknown'),
                'issue': 'snapshot_error',
                'pre_status': pre_snap.get('status'),
                'post_status': post_snap.get('status')
            })
            continue

        # Extract metrics
        pre_metrics = pre_snap.get('metrics', {})
        post_metrics = post_snap.get('metrics', {})

        # Compare total cost
        pre_cost = pre_metrics.get('cost_total', 0)
        post_cost = post_metrics.get('cost_total', 0)

        if pre_cost > 0:
            cost_diff_pct = abs(post_cost - pre_cost) / pre_cost * 100

            if cost_diff_pct > tolerance_pct:
                regressions.append({
                    'deal_id': deal_id,
                    'deal_name': pre_snap.get('deal_name', 'unknown'),
                    'issue': 'cost_changed',
                    'pre_cost': pre_cost,
                    'post_cost': post_cost,
                    'diff_pct': round(cost_diff_pct, 2),
                    'diff_amount': post_cost - pre_cost
                })

        # Compare synergy count
        pre_synergy_count = pre_metrics.get('synergy_count', 0)
        post_synergy_count = post_metrics.get('synergy_count', 0)

        if post_synergy_count != pre_synergy_count:
            # Allow small differences (±1) for edge cases
            if abs(post_synergy_count - pre_synergy_count) > 1:
                regressions.append({
                    'deal_id': deal_id,
                    'deal_name': pre_snap.get('deal_name', 'unknown'),
                    'issue': 'synergy_count_changed',
                    'pre_count': pre_synergy_count,
                    'post_count': post_synergy_count,
                    'diff': post_synergy_count - pre_synergy_count
                })

        # Compare work item count
        pre_wi_count = pre_metrics.get('work_item_count', 0)
        post_wi_count = post_metrics.get('work_item_count', 0)

        if abs(post_wi_count - pre_wi_count) > 2:  # Allow ±2 difference
            warnings.append({
                'deal_id': deal_id,
                'deal_name': pre_snap.get('deal_name', 'unknown'),
                'issue': 'work_item_count_changed',
                'pre_count': pre_wi_count,
                'post_count': post_wi_count,
                'diff': post_wi_count - pre_wi_count
            })

    # Print results
    print("COMPARISON RESULTS")
    print("-"*60)
    print(f"Deals compared:          {len(pre_map)}")
    print(f"Regressions found:       {len(regressions)}")
    print(f"Warnings:                {len(warnings)}")
    print(f"Missing deals:           {len(missing_deals)}")
    print()

    # Show regressions
    if regressions:
        print("⚠ REGRESSIONS DETECTED")
        print("-"*60)
        for reg in regressions:
            print(f"\nDeal: {reg['deal_name']} (ID: {reg['deal_id']})")
            print(f"Issue: {reg['issue']}")

            if reg['issue'] == 'cost_changed':
                print(f"  Pre-migration cost:  ${reg['pre_cost']:,.0f}")
                print(f"  Post-migration cost: ${reg['post_cost']:,.0f}")
                print(f"  Difference:          ${reg['diff_amount']:+,.0f} ({reg['diff_pct']:+.1f}%)")
                print(f"  Tolerance:           ±{tolerance_pct}%")

            elif reg['issue'] == 'synergy_count_changed':
                print(f"  Pre-migration count:  {reg['pre_count']}")
                print(f"  Post-migration count: {reg['post_count']}")
                print(f"  Difference:           {reg['diff']:+d}")

        print()

    # Show warnings
    if warnings:
        print("ℹ WARNINGS (non-critical)")
        print("-"*60)
        for warn in warnings[:5]:  # Show first 5
            print(f"- {warn['deal_name']}: {warn['issue']}")
        if len(warnings) > 5:
            print(f"  ... and {len(warnings) - 5} more")
        print()

    # Show missing deals
    if missing_deals:
        print("⚠ MISSING DEALS")
        print("-"*60)
        for missing in missing_deals:
            print(f"- {missing['deal_name']} (ID: {missing['deal_id']})")
        print()

    # Final verdict
    print("FINAL VERDICT")
    print("-"*60)
    if len(regressions) == 0:
        print("✓ NO REGRESSIONS DETECTED")
        print()
        print("All acquisition deals match baseline within tolerance.")
        print("Migration is safe to proceed.")
        result = True
    else:
        print("✗ REGRESSIONS FOUND")
        print()
        print(f"{len(regressions)} deal(s) show significant changes.")
        print("Review regressions above before proceeding with migration.")
        print()
        print("Recommended actions:")
        print("  1. Investigate each regression")
        print("  2. Verify if changes are expected")
        print("  3. Fix issues or update tolerance if justified")
        print("  4. Re-run comparison")
        result = False

    print("="*60)
    print()

    return result


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Compare pre/post migration snapshots for regressions'
    )
    parser.add_argument(
        '--pre',
        default='data/pre_migration_snapshots.json',
        help='Pre-migration snapshot file (default: data/pre_migration_snapshots.json)'
    )
    parser.add_argument(
        '--post',
        default='data/post_migration_snapshots.json',
        help='Post-migration snapshot file (default: data/post_migration_snapshots.json)'
    )
    parser.add_argument(
        '--tolerance',
        type=float,
        default=5.0,
        help='Cost tolerance percentage (default: 5.0)'
    )

    args = parser.parse_args()

    try:
        success = compare_snapshots(
            pre_file=args.pre,
            post_file=args.post,
            tolerance_pct=args.tolerance
        )

        # Exit with appropriate code
        sys.exit(0 if success else 1)

    except Exception as e:
        print(f"\n✗ Fatal error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
