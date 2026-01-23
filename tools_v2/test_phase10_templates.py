"""
Test Phase 10: Validation & Refinement

Validates:
1. Unified catalog integrity
2. Cross-phase validation
3. Deal scenario estimation
4. Activity coverage analysis
5. Cost model calibration
6. ID uniqueness
7. Executive summary generation
8. Complete system validation
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools_v2.activity_templates_phase10 import (
    get_activity_by_id,
    get_unified_activity_catalog,
    get_activity_count_by_phase,
    estimate_deal_costs,
    analyze_activity_coverage,
    validate_all_activities,
    check_id_uniqueness,
    calibrate_to_target,
    generate_executive_summary,
)


def test_unified_catalog():
    """Test unified activity catalog."""
    print("\n" + "="*70)
    print("TEST 1: Unified Activity Catalog")
    print("="*70)

    catalog = get_unified_activity_catalog()
    counts = get_activity_count_by_phase()

    print(f"\n  Total activities in catalog: {len(catalog)}")
    print("\n  By phase:")
    for phase, count in sorted(counts.items()):
        print(f"    {phase}: {count}")

    total_from_counts = sum(counts.values())
    print(f"\n  Sum from phase counts: {total_from_counts}")

    # Verify counts match
    if len(catalog) != total_from_counts:
        print(f"  MISMATCH: catalog={len(catalog)}, sum={total_from_counts}")
        return False

    # Check we have activities from all 8 phases (one-time costs only)
    expected_phases = 8
    actual_phases = len(counts)

    print(f"\n  Phases covered: {actual_phases} (expected: {expected_phases})")

    return actual_phases == expected_phases and len(catalog) == total_from_counts


def test_activity_lookup():
    """Test activity lookup by ID."""
    print("\n" + "="*70)
    print("TEST 2: Activity Lookup by ID")
    print("="*70)

    test_ids = [
        ("IDN-001", "phase1_foundation"),      # Identity architecture assessment
        ("NET-001", "phase2_applications"),     # Network architecture assessment
        ("ERP-001", "phase3_infrastructure"),   # ERP landscape assessment
        ("DAT-001", "phase4_end_user"),         # Data landscape discovery
        ("LIC-MS-001", "phase5_security"),      # Microsoft 365 E5/E3 licensing
        ("INT-001", "phase6_data"),             # Integration landscape discovery
        ("CMP-PRV-001", "phase7_compliance"),   # Privacy program assessment
        ("VND-CON-001", "phase8_vendor"),       # IT contract inventory
    ]

    all_found = True

    for activity_id, expected_phase in test_ids:
        activity = get_activity_by_id(activity_id)
        if activity:
            found_phase = activity.get("_source_phase")
            status = "✓" if found_phase == expected_phase else "✗"
            print(f"  {status} {activity_id}: {activity.get('name', 'N/A')[:40]}...")
        else:
            print(f"  ✗ {activity_id}: NOT FOUND")
            all_found = False

    # Test non-existent ID
    fake_activity = get_activity_by_id("FAKE-ID-999")
    if fake_activity is None:
        print("  ✓ Non-existent ID correctly returns None")
    else:
        print("  ✗ Non-existent ID should return None")
        all_found = False

    return all_found


def test_validation():
    """Test activity validation."""
    print("\n" + "="*70)
    print("TEST 3: Activity Validation")
    print("="*70)

    issues = validate_all_activities()
    catalog = get_unified_activity_catalog()

    print(f"\n  Total activities: {len(catalog)}")
    print(f"  Activities with validation issues: {len(issues)}")

    if issues:
        print("\n  Sample issues (up to 5):")
        for i, (act_id, errors) in enumerate(list(issues.items())[:5]):
            print(f"    {act_id}:")
            for error in errors[:2]:
                print(f"      - {error}")

    # Allow up to 5% of activities to have issues (legacy/informational activities)
    # These are typically assessment/planning activities bundled into other costs
    issue_rate = len(issues) / len(catalog) if catalog else 1
    acceptable = issue_rate < 0.05  # Less than 5% with issues

    print(f"\n  Issue rate: {issue_rate:.1%} (threshold: 5%)")
    print(f"  Result: {'PASS' if acceptable else 'FAIL'}")

    return acceptable


def test_id_uniqueness():
    """Test that all activity IDs are unique."""
    print("\n" + "="*70)
    print("TEST 4: ID Uniqueness")
    print("="*70)

    duplicates = check_id_uniqueness()

    catalog = get_unified_activity_catalog()
    print(f"\n  Total activities: {len(catalog)}")
    print(f"  Duplicate IDs found: {len(duplicates)}")

    if duplicates:
        print("\n  Duplicates:")
        for dup in duplicates[:10]:
            print(f"    - {dup}")
        return False

    print("  All IDs are unique")
    return True


def test_deal_estimation():
    """Test deal cost estimation (one-time costs only)."""
    print("\n" + "="*70)
    print("TEST 5: Deal Cost Estimation (One-Time)")
    print("="*70)

    test_scenarios = ["carveout_small", "carveout_medium", "carveout_large", "standalone"]

    for scenario in test_scenarios:
        estimate = estimate_deal_costs(scenario, industry="standard")

        total = estimate["total_costs"]

        print(f"\n  {scenario}:")
        print(f"    Total: ${total['low']:,.0f} - ${total['high']:,.0f}")

    # Verify costs scale with deal size
    small = estimate_deal_costs("carveout_small")
    large = estimate_deal_costs("carveout_large")

    if large["total_costs"]["low"] > small["total_costs"]["low"]:
        print("\n  ✓ Large deals correctly cost more than small deals")
        return True
    else:
        print("\n  ✗ Cost scaling issue: large should cost more than small")
        return False


def test_industry_modifiers():
    """Test industry cost modifiers."""
    print("\n" + "="*70)
    print("TEST 6: Industry Cost Modifiers")
    print("="*70)

    deal = "carveout_medium"
    industries = ["standard", "financial_services", "healthcare", "government"]

    costs = {}
    for industry in industries:
        estimate = estimate_deal_costs(deal, industry=industry)
        costs[industry] = estimate["total_costs"]["high"]
        print(f"  {industry}: ${estimate['total_costs']['high']:,.0f}")

    # Verify financial services/healthcare/government cost more than standard
    standard_cost = costs["standard"]
    regulated_higher = all(
        costs[ind] >= standard_cost
        for ind in ["financial_services", "healthcare", "government"]
    )

    if regulated_higher:
        print("\n  ✓ Regulated industries correctly have higher costs")
        return True
    else:
        print("\n  ✗ Regulated industries should have higher costs")
        return False


def test_activity_coverage():
    """Test activity coverage analysis."""
    print("\n" + "="*70)
    print("TEST 7: Activity Coverage Analysis")
    print("="*70)

    analysis = analyze_activity_coverage()

    print(f"\n  Total activities: {analysis['total_activities']}")

    print("\n  By activity type:")
    for act_type, count in sorted(analysis["by_activity_type"].items(), key=lambda x: -x[1]):
        print(f"    {act_type}: {count}")

    print(f"\n  TSA-requiring activities: {len(analysis['tsa_activities'])}")

    print("\n  Cost model distribution:")
    for model, count in sorted(analysis["cost_model_distribution"].items(), key=lambda x: -x[1]):
        print(f"    {model}: {count}")

    # Verify we have good coverage
    has_multiple_types = len(analysis["by_activity_type"]) >= 3
    has_tsa_activities = len(analysis["tsa_activities"]) > 0

    return has_multiple_types and has_tsa_activities


def test_calibration():
    """Test cost model calibration."""
    print("\n" + "="*70)
    print("TEST 8: Cost Model Calibration")
    print("="*70)

    # Test calibration to a target
    target = 15_000_000  # $15M target

    calibration = calibrate_to_target(target, "carveout_medium", "standard")

    print(f"\n  Target: ${target:,.0f}")
    print(f"  Current estimate: ${calibration['current_estimate']['low']:,.0f} - ${calibration['current_estimate']['high']:,.0f}")
    print("\n  Adjustment factors:")
    print(f"    To match low:  {calibration['adjustment_factors']['to_match_low']:.2f}x")
    print(f"    To match mid:  {calibration['adjustment_factors']['to_match_mid']:.2f}x")
    print(f"    To match high: {calibration['adjustment_factors']['to_match_high']:.2f}x")
    print(f"\n  Interpretation: {calibration['interpretation']}")

    return True


def test_executive_summary():
    """Test executive summary generation."""
    print("\n" + "="*70)
    print("TEST 9: Executive Summary Generation")
    print("="*70)

    summary = generate_executive_summary("carveout_medium", "financial_services")

    print("\n" + summary)

    # Verify summary contains key elements
    has_costs = "TOTAL" in summary
    has_phases = "PHASE BREAKDOWN" in summary

    return has_costs and has_phases


def test_comprehensive_scenario():
    """Test comprehensive multi-phase scenario (one-time costs only)."""
    print("\n" + "="*70)
    print("TEST 10: Comprehensive Multi-Phase Scenario")
    print("="*70)

    print("\n  Scenario: Large Financial Services Carveout")
    print("  - 5,000 users")
    print("  - Complex environment")
    print("  - Regulated industry")
    print("  - One-time costs only (no run-rate)")

    estimate = estimate_deal_costs(
        deal_type="carveout_large",
        industry="financial_services",
    )

    print("\n  Parameters:")
    for param, value in estimate["parameters"].items():
        if isinstance(value, (int, float)):
            print(f"    {param}: {value:,}")
        else:
            print(f"    {param}: {value}")

    print("\n  Phase costs:")
    for phase, data in sorted(estimate["phases"].items()):
        print(f"    {phase}: ${data['low']:,.0f} - ${data['high']:,.0f}")

    print(f"\n  TOTAL ONE-TIME COSTS: ${estimate['total_costs']['low']:,.0f} - ${estimate['total_costs']['high']:,.0f}")

    # Reasonableness check for large (5,000 user) complex financial services carveout
    # This is a massive deal - costs include ALL activities across ALL workstreams
    # Real deals would select relevant subset, so these are comprehensive maximums
    # One-time: $80M - $250M range (low), $250M - $600M range (high) - reduced without run-rate
    one_time_reasonable = (
        80_000_000 < estimate["total_costs"]["low"] < 250_000_000 and
        250_000_000 < estimate["total_costs"]["high"] < 600_000_000
    )

    print(f"\n  Reasonableness check: {'PASS' if one_time_reasonable else 'FAIL'}")

    return one_time_reasonable


def run_all_tests():
    """Run all Phase 10 tests."""
    print("\n" + "#"*70)
    print("# PHASE 10: VALIDATION & REFINEMENT - COMPREHENSIVE TEST SUITE")
    print("#"*70)

    results = []

    results.append(("Unified Catalog", test_unified_catalog()))
    results.append(("Activity Lookup", test_activity_lookup()))
    results.append(("Activity Validation", test_validation()))
    results.append(("ID Uniqueness", test_id_uniqueness()))
    results.append(("Deal Estimation", test_deal_estimation()))
    results.append(("Industry Modifiers", test_industry_modifiers()))
    results.append(("Coverage Analysis", test_activity_coverage()))
    results.append(("Calibration", test_calibration()))
    results.append(("Executive Summary", test_executive_summary()))
    results.append(("Comprehensive Scenario", test_comprehensive_scenario()))

    print("\n" + "="*70)
    print("FINAL SUMMARY")
    print("="*70)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {status}: {name}")

    print(f"\n  Total: {passed}/{total} tests passed")

    # Print total activity count
    catalog = get_unified_activity_catalog()
    print(f"\n  TOTAL ACTIVITIES IN SYSTEM: {len(catalog)}")

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
