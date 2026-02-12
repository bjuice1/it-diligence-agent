#!/usr/bin/env python3
"""
Quick test script to validate synergy engine branching logic.

Tests that:
1. Acquisition deals return consolidation synergies
2. Carveout deals return separation costs (NO consolidation)
3. Deal type branching works correctly
"""

import sys
from stores.inventory_store import InventoryStore
from web.blueprints.costs import _identify_synergies

print("=" * 80)
print("SYNERGY ENGINE BRANCHING TEST")
print("=" * 80)
print()

# Create test inventory with overlapping systems
print("Setting up test inventory...")
print("- Shared ERP system (parent datacenter)")
print("- Shared CRM system (parent datacenter)")
print("- Overlapping Salesforce instances (buyer + target)")
print()

inv_store = InventoryStore(deal_id="test-synergy-engine")

# Add buyer applications (for acquisition scenario - consolidation opportunity)
inv_store.add_item(
    inventory_type='application',
    entity='buyer',
    data={
        'name': 'Salesforce CRM',
        'category': 'CRM',
        'hosting': 'aws',
        'users': 1000,
        'annual_cost': 120000,
        'criticality': 'high'
    }
)

# Add target applications
inv_store.add_item(
    inventory_type='application',
    entity='target',
    data={
        'name': 'Salesforce CRM',  # Same as buyer - consolidation opportunity
        'category': 'CRM',
        'hosting': 'parent_datacenter',  # Hosted by parent (separation needed)
        'users': 500,
        'annual_cost': 60000,
        'criticality': 'high'
    }
)

inv_store.add_item(
    inventory_type='application',
    entity='target',
    data={
        'name': 'SAP ERP',
        'category': 'ERP',
        'hosting': 'parent_datacenter',  # Shared with parent
        'users': 800,
        'annual_cost': 500000,
        'criticality': 'critical',
        'notes': 'Shared ERP instance with parent company'
    }
)

inv_store.add_item(
    inventory_type='application',
    entity='target',
    data={
        'name': 'Workday HCM',
        'category': 'HCM',
        'hosting': 'parent_datacenter',
        'users': 1000,
        'annual_cost': 200000,
        'criticality': 'high',
        'notes': 'Parent-owned HCM system'
    }
)

print(f"Created inventory with {len(inv_store._items)} applications")
print()

# ============================================================================
# TEST 1: ACQUISITION - Should return consolidation synergies
# ============================================================================

print("=" * 80)
print("TEST 1: ACQUISITION DEAL")
print("=" * 80)
print()
print("Calling: _identify_synergies(inv_store, deal_type='acquisition')")
print()

try:
    acquisition_results = _identify_synergies(inv_store, deal_type='acquisition')

    print(f"✅ Returned {len(acquisition_results)} results")
    print()

    if acquisition_results:
        print("Results:")
        print("-" * 80)
        for i, result in enumerate(acquisition_results, 1):
            print(f"{i}. {result.title}")
            print(f"   Type: {type(result).__name__}")

            # Check if it's a SynergyOpportunity (consolidation)
            if hasattr(result, 'annual_savings'):
                print(f"   💰 Annual Savings: ${result.annual_savings:,.0f}")
                print(f"   Description: {result.description[:100]}...")
                if 'consolidat' in result.description.lower():
                    print("   ✅ Contains 'consolidate' - CORRECT for acquisition")

            # Check if it's a SeparationCost (should NOT be for acquisition)
            if hasattr(result, 'setup_cost_low'):
                print(f"   ⚠️ WARNING: Returned SeparationCost for acquisition (unexpected)")

            print()
    else:
        print("⚠️ No results returned")

except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print()

# ============================================================================
# TEST 2: CARVEOUT - Should return separation costs (NO consolidation)
# ============================================================================

print("=" * 80)
print("TEST 2: CARVEOUT DEAL")
print("=" * 80)
print()
print("Calling: _identify_synergies(inv_store, deal_type='carveout')")
print()

try:
    carveout_results = _identify_synergies(inv_store, deal_type='carveout')

    print(f"✅ Returned {len(carveout_results)} results")
    print()

    if carveout_results:
        print("Results:")
        print("-" * 80)
        for i, result in enumerate(carveout_results, 1):
            print(f"{i}. {result.title}")
            print(f"   Type: {type(result).__name__}")

            # Check if it's a SeparationCost (expected for carveout)
            if hasattr(result, 'setup_cost_low'):
                print(f"   💵 Setup Cost Range: ${result.setup_cost_low:,.0f} - ${result.setup_cost_high:,.0f}")
                if hasattr(result, 'tsa_required') and result.tsa_required:
                    print(f"   📋 TSA Required: {result.tsa_duration_months} months @ ${result.tsa_monthly_cost:,.0f}/month")
                    total_cost = result.total_cost_high
                    print(f"   💰 Total Cost (Setup + TSA): ${total_cost:,.0f}")
                print(f"   Description: {result.description[:100]}...")

                # Verify NO consolidation language
                if 'consolidat' in result.description.lower():
                    print("   ❌ CRITICAL BUG: Contains 'consolidate' - WRONG for carveout!")
                elif 'separat' in result.description.lower() or 'standalone' in result.description.lower():
                    print("   ✅ Contains 'separate/standalone' - CORRECT for carveout")

            # Check if it's a SynergyOpportunity (should NOT be for carveout)
            if hasattr(result, 'annual_savings'):
                print(f"   ❌ CRITICAL BUG: Returned SynergyOpportunity for carveout!")
                print(f"      (Should return SeparationCost, not consolidation synergies)")

            print()
    else:
        print("⚠️ No results returned")

except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print()

# ============================================================================
# TEST 3: DIVESTITURE - Should return separation costs (higher than carveout)
# ============================================================================

print("=" * 80)
print("TEST 3: DIVESTITURE DEAL")
print("=" * 80)
print()
print("Calling: _identify_synergies(inv_store, deal_type='divestiture')")
print()

try:
    divestiture_results = _identify_synergies(inv_store, deal_type='divestiture')

    print(f"✅ Returned {len(divestiture_results)} results")
    print()

    if divestiture_results:
        print("Results:")
        print("-" * 80)
        for i, result in enumerate(divestiture_results, 1):
            print(f"{i}. {result.title}")
            print(f"   Type: {type(result).__name__}")

            if hasattr(result, 'setup_cost_low'):
                print(f"   💵 Setup Cost Range: ${result.setup_cost_low:,.0f} - ${result.setup_cost_high:,.0f}")
                if hasattr(result, 'tsa_required') and result.tsa_required:
                    print(f"   📋 TSA Required: {result.tsa_duration_months} months @ ${result.tsa_monthly_cost:,.0f}/month")
                print(f"   Criticality: {result.criticality}")
            print()
    else:
        print("⚠️ No results returned")

except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print()

# ============================================================================
# SUMMARY
# ============================================================================

print("=" * 80)
print("SUMMARY")
print("=" * 80)
print()

print("Test Results:")
print(f"  Acquisition:  {len(acquisition_results) if 'acquisition_results' in locals() else 0} results")
print(f"  Carveout:     {len(carveout_results) if 'carveout_results' in locals() else 0} results")
print(f"  Divestiture:  {len(divestiture_results) if 'divestiture_results' in locals() else 0} results")
print()

# Validation checks
checks_passed = 0
checks_total = 0

print("Validation Checks:")

# Check 1: Acquisition returns results
checks_total += 1
if 'acquisition_results' in locals() and len(acquisition_results) > 0:
    print("  ✅ Acquisition returns results")
    checks_passed += 1
else:
    print("  ❌ Acquisition returns no results")

# Check 2: Carveout returns results
checks_total += 1
if 'carveout_results' in locals() and len(carveout_results) > 0:
    print("  ✅ Carveout returns results")
    checks_passed += 1
else:
    print("  ❌ Carveout returns no results")

# Check 3: Acquisition returns SynergyOpportunity
checks_total += 1
if 'acquisition_results' in locals() and acquisition_results:
    if any(hasattr(r, 'annual_savings') for r in acquisition_results):
        print("  ✅ Acquisition returns SynergyOpportunity (consolidation)")
        checks_passed += 1
    else:
        print("  ❌ Acquisition does NOT return SynergyOpportunity")
else:
    print("  ⚠️ Cannot check (no acquisition results)")

# Check 4: Carveout returns SeparationCost
checks_total += 1
if 'carveout_results' in locals() and carveout_results:
    if any(hasattr(r, 'setup_cost_low') for r in carveout_results):
        print("  ✅ Carveout returns SeparationCost (NOT consolidation)")
        checks_passed += 1
    else:
        print("  ❌ Carveout does NOT return SeparationCost")
else:
    print("  ⚠️ Cannot check (no carveout results)")

# Check 5: Carveout does NOT return consolidation synergies
checks_total += 1
if 'carveout_results' in locals() and carveout_results:
    if not any(hasattr(r, 'annual_savings') for r in carveout_results):
        print("  ✅ Carveout does NOT return consolidation synergies (CRITICAL)")
        checks_passed += 1
    else:
        print("  ❌ CRITICAL BUG: Carveout returns consolidation synergies!")
else:
    print("  ⚠️ Cannot check (no carveout results)")

print()
print(f"Checks Passed: {checks_passed}/{checks_total}")

if checks_passed == checks_total:
    print()
    print("🎉 ALL CHECKS PASSED - Synergy engine branching works correctly!")
    sys.exit(0)
else:
    print()
    print("⚠️ SOME CHECKS FAILED - Review output above")
    sys.exit(1)
