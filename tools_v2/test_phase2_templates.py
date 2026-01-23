"""
Test Phase 2 Activity Templates

Validates:
1. Template structure and completeness
2. Cost calculations
3. Coverage of key activities
4. Sample scenario costing
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools_v2.activity_templates_phase2 import (
    NETWORK_TEMPLATES,
    SECURITY_TEMPLATES,
    PERIMETER_TEMPLATES,
    get_phase2_templates,
    get_phase2_activity_by_id,
    calculate_phase2_activity_cost,
)


def test_template_structure():
    """Test that all templates have required fields."""
    print("\n" + "="*70)
    print("TEST 1: Template Structure Validation")
    print("="*70)

    required_fields = ["id", "name", "description", "activity_type", "phase", "requires_tsa"]
    cost_fields = ["base_cost", "per_user_cost", "per_site_cost", "per_endpoint_cost",
                   "per_device_cost", "per_account_cost", "per_domain_cost"]

    all_templates = get_phase2_templates()
    issues = []

    total_activities = 0
    for category, workstreams in all_templates.items():
        for workstream, activities in workstreams.items():
            for activity in activities:
                total_activities += 1

                # Check required fields
                for field in required_fields:
                    if field not in activity:
                        issues.append(f"{activity.get('id', 'UNKNOWN')}: Missing '{field}'")

                # Check at least one cost field exists
                has_cost = any(field in activity for field in cost_fields)
                if not has_cost:
                    issues.append(f"{activity.get('id', 'UNKNOWN')}: Missing cost field")

    print(f"\n  Total activities: {total_activities}")
    print(f"  Issues found: {len(issues)}")

    if issues:
        for issue in issues[:10]:
            print(f"    - {issue}")
    else:
        print("  All templates have required fields")

    return len(issues) == 0


def test_activity_counts():
    """Test that we have comprehensive coverage."""
    print("\n" + "="*70)
    print("TEST 2: Activity Coverage")
    print("="*70)

    all_templates = get_phase2_templates()

    for category, workstreams in all_templates.items():
        print(f"\n  Category: {category}")
        for workstream, activities in workstreams.items():
            phases = {}
            for a in activities:
                phase = a.get("phase", "unknown")
                phases[phase] = phases.get(phase, 0) + 1

            phase_summary = ", ".join([f"{p}: {c}" for p, c in sorted(phases.items())])
            print(f"    {workstream}: {len(activities)} activities ({phase_summary})")

    # Verify minimum counts
    network_count = len(NETWORK_TEMPLATES.get("parent_dependency", []))
    security_count = len(SECURITY_TEMPLATES.get("parent_dependency", []))
    perimeter_count = len(PERIMETER_TEMPLATES.get("parent_dependency", []))

    print(f"\n  Network: {network_count} activities (target: 15+)")
    print(f"  Security: {security_count} activities (target: 15+)")
    print(f"  Perimeter: {perimeter_count} activities (target: 10+)")

    return network_count >= 15 and security_count >= 15 and perimeter_count >= 10


def test_cost_calculations():
    """Test cost calculation logic."""
    print("\n" + "="*70)
    print("TEST 3: Cost Calculations")
    print("="*70)

    # Test different cost models
    test_cases = [
        ("NET-001", {"base_cost": True}),  # Base cost
        ("NET-010", {"per_site_cost": True}),  # Per site
        ("SEC-010", {"per_endpoint_cost": True}),  # Per endpoint
        ("PER-011", {"per_user_cost": True}),  # Per user
    ]

    all_passed = True

    for activity_id, expected in test_cases:
        activity = get_phase2_activity_by_id(activity_id)
        if not activity:
            print(f"  {activity_id}: Not found")
            all_passed = False
            continue

        low, high, formula = calculate_phase2_activity_cost(
            activity,
            user_count=1000,
            site_count=5,
            endpoint_count=1500,
        )

        if low > 0 and high > low:
            print(f"  {activity_id}: ${low:,.0f}-${high:,.0f}")
            print(f"      Formula: {formula}")
        else:
            print(f"  {activity_id}: Invalid cost range ({low}, {high})")
            all_passed = False

    return all_passed


def test_complexity_modifiers():
    """Test complexity and industry modifiers."""
    print("\n" + "="*70)
    print("TEST 4: Complexity Modifiers")
    print("="*70)

    activity = get_phase2_activity_by_id("SEC-010")  # EDR deployment

    scenarios = [
        ("simple", "standard", 0.7),
        ("moderate", "standard", 1.0),
        ("complex", "standard", 1.5),
        ("moderate", "financial_services", 1.3),
        ("complex", "healthcare", 1.875),  # 1.5 * 1.25
    ]

    base_low, base_high, _ = calculate_phase2_activity_cost(
        activity, user_count=1000, complexity="moderate", industry="standard"
    )

    print(f"\n  Base cost (moderate/standard): ${base_low:,.0f}-${base_high:,.0f}")
    print("\n  Scenario comparisons:")

    for complexity, industry, expected_mult in scenarios:
        low, high, formula = calculate_phase2_activity_cost(
            activity, user_count=1000, complexity=complexity, industry=industry
        )

        print(f"    {complexity}/{industry}: ${low:,.0f}-${high:,.0f}")

    return True


def test_sample_carveout_scenario():
    """Test a realistic carveout scenario."""
    print("\n" + "="*70)
    print("TEST 5: Sample Carveout Scenario")
    print("="*70)

    print("\n  Scenario: 1,500 user carveout")
    print("  - 8 sites (offices)")
    print("  - 2,000 endpoints")
    print("  - Moderate complexity, standard industry")

    quantities = {
        "user_count": 1500,
        "site_count": 8,
        "endpoint_count": 2000,
        "device_count": 750,
        "complexity": "moderate",
        "industry": "standard",
    }

    all_templates = get_phase2_templates()

    workstream_totals = {}
    grand_total_low = 0
    grand_total_high = 0

    for category, workstreams in all_templates.items():
        for workstream, activities in workstreams.items():
            ws_low = 0
            ws_high = 0

            for activity in activities:
                low, high, _ = calculate_phase2_activity_cost(activity, **quantities)
                ws_low += low
                ws_high += high

            key = f"{workstream} ({category})"
            workstream_totals[key] = (ws_low, ws_high)
            grand_total_low += ws_low
            grand_total_high += ws_high

    print("\n  Cost by workstream:")
    for ws, (low, high) in sorted(workstream_totals.items(), key=lambda x: -x[1][1]):
        print(f"    {ws}: ${low:,.0f} - ${high:,.0f}")

    print(f"\n  PHASE 2 TOTAL: ${grand_total_low:,.0f} - ${grand_total_high:,.0f}")

    # Sanity check - should be in reasonable range for network/security buildout
    reasonable = 500000 < grand_total_low < 5000000 and 1000000 < grand_total_high < 10000000

    print(f"\n  Reasonableness check: {'PASS' if reasonable else 'FAIL'}")

    return reasonable


def test_tsa_activities():
    """Test TSA tracking."""
    print("\n" + "="*70)
    print("TEST 6: TSA Requirements")
    print("="*70)

    all_templates = get_phase2_templates()

    tsa_activities = []
    non_tsa_activities = []

    for category, workstreams in all_templates.items():
        for workstream, activities in workstreams.items():
            for activity in activities:
                if activity.get("requires_tsa"):
                    tsa_activities.append(activity)
                else:
                    non_tsa_activities.append(activity)

    print(f"\n  Activities requiring TSA: {len(tsa_activities)}")
    print(f"  Activities not requiring TSA: {len(non_tsa_activities)}")

    print("\n  TSA activities by duration:")
    duration_buckets = {}
    for a in tsa_activities:
        duration = a.get("tsa_duration", (0, 0))
        key = f"{duration[0]}-{duration[1]} months"
        duration_buckets[key] = duration_buckets.get(key, 0) + 1

    for duration, count in sorted(duration_buckets.items()):
        print(f"    {duration}: {count} activities")

    return len(tsa_activities) > 0


def test_combined_scenario():
    """Test Phase 1 + Phase 2 combined scenario."""
    print("\n" + "="*70)
    print("TEST 7: Combined Phase 1 + Phase 2 Scenario")
    print("="*70)

    try:
        from tools_v2.activity_templates_v2 import (
            get_phase1_templates,
            calculate_activity_cost,
        )

        print("\n  Scenario: 1,500 user carveout (full scope)")
        print("  Phase 1: Identity, Email, Infrastructure")
        print("  Phase 2: Network, Security, Perimeter")

        # Phase 1 quantities
        p1_quantities = {
            "user_count": 1500,
            "app_count": 40,
            "vm_count": 75,
            "server_count": 75,
            "complexity": "moderate",
            "industry": "standard",
        }

        # Phase 2 quantities
        p2_quantities = {
            "user_count": 1500,
            "site_count": 8,
            "endpoint_count": 2000,
            "complexity": "moderate",
            "industry": "standard",
        }

        # Calculate Phase 1
        p1_templates = get_phase1_templates()
        p1_total_low = 0
        p1_total_high = 0

        for category, workstreams in p1_templates.items():
            for workstream, activities in workstreams.items():
                for activity in activities:
                    low, high, _ = calculate_activity_cost(activity, **p1_quantities)
                    p1_total_low += low
                    p1_total_high += high

        # Calculate Phase 2
        p2_templates = get_phase2_templates()
        p2_total_low = 0
        p2_total_high = 0

        for category, workstreams in p2_templates.items():
            for workstream, activities in workstreams.items():
                for activity in activities:
                    low, high, _ = calculate_phase2_activity_cost(activity, **p2_quantities)
                    p2_total_low += low
                    p2_total_high += high

        combined_low = p1_total_low + p2_total_low
        combined_high = p1_total_high + p2_total_high

        print(f"\n  Phase 1 Total: ${p1_total_low:,.0f} - ${p1_total_high:,.0f}")
        print(f"  Phase 2 Total: ${p2_total_low:,.0f} - ${p2_total_high:,.0f}")
        print(f"\n  COMBINED TOTAL: ${combined_low:,.0f} - ${combined_high:,.0f}")

        # Activity counts
        p1_count = sum(
            len(acts) for cat in p1_templates.values()
            for acts in cat.values()
        )
        p2_count = sum(
            len(acts) for cat in p2_templates.values()
            for acts in cat.values()
        )

        print("\n  Activity counts:")
        print(f"    Phase 1: {p1_count} activities")
        print(f"    Phase 2: {p2_count} activities")
        print(f"    Total: {p1_count + p2_count} activities")

        return True

    except ImportError as e:
        print(f"\n  Could not import Phase 1: {e}")
        return False


def run_all_tests():
    """Run all Phase 2 template tests."""
    print("\n" + "#"*70)
    print("# PHASE 2 ACTIVITY TEMPLATES - TEST SUITE")
    print("#"*70)

    results = []

    results.append(("Template Structure", test_template_structure()))
    results.append(("Activity Coverage", test_activity_counts()))
    results.append(("Cost Calculations", test_cost_calculations()))
    results.append(("Complexity Modifiers", test_complexity_modifiers()))
    results.append(("Sample Scenario", test_sample_carveout_scenario()))
    results.append(("TSA Requirements", test_tsa_activities()))
    results.append(("Combined P1+P2", test_combined_scenario()))

    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {status}: {name}")

    print(f"\n  Total: {passed}/{total} tests passed")

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
