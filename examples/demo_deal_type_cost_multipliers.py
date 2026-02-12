#!/usr/bin/env python3
"""
Demo: Deal Type Cost Multipliers

Shows how carveout and divestiture deals cost significantly more than
acquisitions due to the need to build standalone systems vs simple integration.

Run: python examples/demo_deal_type_cost_multipliers.py
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.cost_engine.calculator import calculate_cost, calculate_deal_costs
from services.cost_engine.models import COST_MODELS, WorkItemType, get_deal_type_multiplier
from services.cost_engine.drivers import DealDrivers, OwnershipType
from stores.inventory_store import InventoryStore


def demo_multipliers():
    """Show multiplier values for all deal types."""
    print("\n" + "=" * 80)
    print("DEAL TYPE COST MULTIPLIERS")
    print("=" * 80)
    print("\nMultipliers by deal type (1.0 = acquisition baseline):\n")

    categories = [
        'identity',
        'application',
        'infrastructure',
        'network',
        'cybersecurity',
        'organization'
    ]

    deal_types = ['acquisition', 'carveout', 'divestiture']

    # Print header
    print(f"{'Category':<25} {'Acquisition':<15} {'Carveout':<15} {'Divestiture':<15}")
    print("-" * 70)

    # Print multipliers
    for category in categories:
        row = f"{category.title():<25}"
        for deal_type in deal_types:
            mult = get_deal_type_multiplier(deal_type, category)
            row += f"{mult:.1f}x{'':<12}"
        print(row)

    print("\n")


def demo_identity_separation():
    """Show identity separation costs across deal types."""
    print("=" * 80)
    print("EXAMPLE: Identity Separation for 1,000 User Company")
    print("=" * 80)
    print("\nScenario: Target company has 1,000 users and 5 sites")
    print("Identity systems are owned by parent company\n")

    model = COST_MODELS[WorkItemType.IDENTITY_SEPARATION]
    drivers = DealDrivers(
        entity="target",
        total_users=1000,
        sites=5,
        identity_owned_by=OwnershipType.PARENT
    )

    results = {}
    for deal_type in ['acquisition', 'carveout', 'divestiture']:
        cost = calculate_cost(model, drivers, deal_type=deal_type)
        results[deal_type] = cost

    # Print comparison
    print(f"{'Deal Type':<15} {'One-Time Cost':<20} {'Annual Licenses':<20} {'Multiplier'}")
    print("-" * 70)

    for deal_type in ['acquisition', 'carveout', 'divestiture']:
        cost = results[deal_type]
        multiplier = cost.cost_breakdown.get('deal_type_multiplier', 1.0)
        print(f"{deal_type.title():<15} ${cost.one_time_base:>15,.0f}   ${cost.annual_licenses:>15,.0f}   {multiplier:.1f}x")

    # Show the delta
    acq_cost = results['acquisition'].one_time_base
    carve_cost = results['carveout'].one_time_base
    div_cost = results['divestiture'].one_time_base

    print(f"\n{'Comparison to Acquisition:':<25}")
    print(f"  Carveout:     ${carve_cost - acq_cost:>12,.0f} more ({carve_cost / acq_cost:.1f}x)")
    print(f"  Divestiture:  ${div_cost - acq_cost:>12,.0f} more ({div_cost / acq_cost:.1f}x)")

    print("\nWhy the difference?")
    print("  Acquisition:  Extend existing buyer IAM systems (simpler)")
    print("  Carveout:     Build NEW standalone IAM from scratch (complex)")
    print("  Divestiture:  Extract identity from deeply entangled shared systems (most complex)")
    print("\n")


def demo_full_deal_costs():
    """Show full deal costs across all work items."""
    print("=" * 80)
    print("EXAMPLE: Full Deal Cost Estimate")
    print("=" * 80)
    print("\nScenario: Mid-size company with IT services owned by parent\n")

    drivers = DealDrivers(
        entity="target",
        total_users=1000,
        sites=5,
        endpoints=1200,
        identity_owned_by=OwnershipType.PARENT,
        wan_owned_by=OwnershipType.PARENT,
        soc_owned_by=OwnershipType.PARENT
    )

    results = {}
    for deal_type in ['acquisition', 'carveout', 'divestiture']:
        summary = calculate_deal_costs("demo", drivers, deal_type=deal_type)
        results[deal_type] = summary

    # Print comparison
    print(f"{'Deal Type':<15} {'Work Items':<12} {'One-Time Base':<20} {'Annual Licenses':<20}")
    print("-" * 75)

    for deal_type in ['acquisition', 'carveout', 'divestiture']:
        summary = results[deal_type]
        print(
            f"{deal_type.title():<15} "
            f"{len(summary.estimates):<12} "
            f"${summary.total_one_time_base:>15,.0f}   "
            f"${summary.total_annual_licenses:>15,.0f}"
        )

    # Show breakdown by tower for carveout
    print(f"\n{'Carveout Cost Breakdown by Tower:'}")
    print(f"{'Tower':<20} {'One-Time Cost':<20}")
    print("-" * 40)
    carve_summary = results['carveout']
    for tower, costs in sorted(carve_summary.tower_costs.items()):
        print(f"{tower:<20} ${costs['one_time_base']:>15,.0f}")

    print("\n")


def demo_tsa_costs():
    """Show TSA costs for carveout deals."""
    print("=" * 80)
    print("EXAMPLE: TSA (Transition Service Agreement) Costs")
    print("=" * 80)
    print("\nTSA = Parent provides services to carved-out entity during separation")
    print("Typical duration: 6-24 months\n")

    from services.cost_engine.drivers import TSACostDriver

    inv_store = InventoryStore(deal_id="demo")
    tsa_driver = TSACostDriver()

    for duration in [6, 12, 18, 24]:
        tsa_cost = tsa_driver.estimate_monthly_tsa_cost(inv_store, duration)
        monthly = tsa_cost / duration
        print(f"  {duration:2d} months: ${tsa_cost:>10,.0f} (${monthly:>7,.0f}/month)")

    print("\nNote: TSA costs apply ONLY to carveout deals, not acquisitions")
    print("      In acquisitions, the buyer provides services from day 1\n")


def main():
    """Run all demos."""
    print("\n" + "=" * 80)
    print("DEAL TYPE COST MULTIPLIERS DEMO")
    print("=" * 80)
    print("\nShowing how deal structure affects IT separation/integration costs")
    print("Based on: specs/deal-type-awareness/04-cost-engine-deal-awareness.md")

    demo_multipliers()
    demo_identity_separation()
    demo_full_deal_costs()
    demo_tsa_costs()

    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("\nKey Takeaways:")
    print("  1. Carveouts cost 1.5-2.5x more than acquisitions (need to build standalone)")
    print("  2. Divestitures cost 2.0-3.0x more (need to untangle from shared systems)")
    print("  3. Identity separation has highest multiplier (2.5-3.0x)")
    print("  4. TSA costs add $600K-$6M depending on complexity and duration")
    print("  5. Total carveout costs often exceed acquisition by $1-3M\n")


if __name__ == "__main__":
    main()
