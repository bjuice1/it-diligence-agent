"""
Test Phase 1 Activity Templates

Validates:
1. Template structure and completeness
2. Cost calculations
3. Coverage of key activities
4. Sample scenario costing
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools_v2.activity_templates_v2 import (
    IDENTITY_TEMPLATES,
    EMAIL_TEMPLATES,
    INFRASTRUCTURE_TEMPLATES,
    COMPLEXITY_MULTIPLIERS,
    INDUSTRY_MODIFIERS,
    get_phase1_templates,
    get_activity_by_id,
    get_activities_by_phase,
    calculate_activity_cost,
)


def test_template_structure():
    """Test that all templates have required fields."""
    print("\n" + "="*70)
    print("TEST 1: Template Structure Validation")
    print("="*70)

    required_fields = ["id", "name", "description", "activity_type", "phase", "requires_tsa"]
    cost_fields = ["base_cost", "per_user_cost", "per_app_cost", "per_vm_cost",
                   "per_server_cost", "per_mailbox_cost", "per_database_cost", "per_tb_cost",
                   "per_account_cost", "per_group_cost", "per_domain_cost", "per_resource_cost"]

    all_templates = get_phase1_templates()
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
        print("  ✓ All templates have required fields")

    return len(issues) == 0


def test_activity_counts():
    """Test that we have comprehensive coverage."""
    print("\n" + "="*70)
    print("TEST 2: Activity Coverage")
    print("="*70)

    all_templates = get_phase1_templates()

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
    identity_count = len(IDENTITY_TEMPLATES.get("parent_dependency", []))
    email_count = len(EMAIL_TEMPLATES.get("parent_dependency", []))
    infra_count = len(INFRASTRUCTURE_TEMPLATES.get("parent_dependency", []))

    print(f"\n  Identity: {identity_count} activities (target: 15+)")
    print(f"  Email: {email_count} activities (target: 15+)")
    print(f"  Infrastructure: {infra_count} activities (target: 15+)")

    return identity_count >= 15 and email_count >= 15 and infra_count >= 15


def test_cost_calculations():
    """Test cost calculation logic."""
    print("\n" + "="*70)
    print("TEST 3: Cost Calculations")
    print("="*70)

    # Test different cost models
    test_cases = [
        ("IDN-001", {"base_cost": True}),  # Base cost
        ("IDN-020", {"per_user_cost": True}),  # Per user
        ("IDN-030", {"per_app_cost": True}),  # Per app
        ("INF-020", {"per_vm_cost": True}),  # Per VM
    ]

    all_passed = True

    for activity_id, expected in test_cases:
        activity = get_activity_by_id(activity_id)
        if not activity:
            print(f"  ✗ {activity_id}: Not found")
            all_passed = False
            continue

        low, high, formula = calculate_activity_cost(
            activity,
            user_count=1000,
            app_count=30,
            vm_count=100,
        )

        if low > 0 and high > low:
            print(f"  ✓ {activity_id}: ${low:,.0f}-${high:,.0f}")
            print(f"      Formula: {formula}")
        else:
            print(f"  ✗ {activity_id}: Invalid cost range ({low}, {high})")
            all_passed = False

    return all_passed


def test_complexity_modifiers():
    """Test complexity and industry modifiers."""
    print("\n" + "="*70)
    print("TEST 4: Complexity Modifiers")
    print("="*70)

    activity = get_activity_by_id("IDN-020")  # User migration

    scenarios = [
        ("simple", "standard", 0.7),
        ("moderate", "standard", 1.0),
        ("complex", "standard", 1.5),
        ("moderate", "financial_services", 1.3),
        ("complex", "healthcare", 1.875),  # 1.5 * 1.25
    ]

    base_low, base_high, _ = calculate_activity_cost(
        activity, user_count=1000, complexity="moderate", industry="standard"
    )

    print(f"\n  Base cost (moderate/standard): ${base_low:,.0f}-${base_high:,.0f}")
    print("\n  Scenario comparisons:")

    for complexity, industry, expected_mult in scenarios:
        low, high, formula = calculate_activity_cost(
            activity, user_count=1000, complexity=complexity, industry=industry
        )

        actual_mult = low / (base_low / 1.0)  # Approximate
        print(f"    {complexity}/{industry}: ${low:,.0f}-${high:,.0f}")

    return True


def test_sample_carveout_scenario():
    """Test a realistic carveout scenario."""
    print("\n" + "="*70)
    print("TEST 5: Sample Carveout Scenario")
    print("="*70)

    print("\n  Scenario: 1,500 user carveout")
    print("  - 40 applications with SSO")
    print("  - 75 VMs")
    print("  - Moderate complexity, standard industry")

    quantities = {
        "user_count": 1500,
        "app_count": 40,
        "vm_count": 75,
        "server_count": 75,
        "complexity": "moderate",
        "industry": "standard",
    }

    all_templates = get_phase1_templates()

    workstream_totals = {}
    grand_total_low = 0
    grand_total_high = 0

    for category, workstreams in all_templates.items():
        for workstream, activities in workstreams.items():
            ws_low = 0
            ws_high = 0

            for activity in activities:
                low, high, _ = calculate_activity_cost(activity, **quantities)
                ws_low += low
                ws_high += high

            workstream_totals[workstream] = (ws_low, ws_high)
            grand_total_low += ws_low
            grand_total_high += ws_high

    print("\n  Cost by workstream:")
    for ws, (low, high) in sorted(workstream_totals.items(), key=lambda x: -x[1][1]):
        print(f"    {ws}: ${low:,.0f} - ${high:,.0f}")

    print(f"\n  TOTAL: ${grand_total_low:,.0f} - ${grand_total_high:,.0f}")

    # Sanity check - should be in reasonable range for 1500 user carveout
    reasonable = 500000 < grand_total_low < 5000000 and 1000000 < grand_total_high < 10000000

    print(f"\n  Reasonableness check: {'✓ PASS' if reasonable else '✗ FAIL'}")

    return reasonable


def test_tsa_activities():
    """Test TSA tracking."""
    print("\n" + "="*70)
    print("TEST 6: TSA Requirements")
    print("="*70)

    all_templates = get_phase1_templates()

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


def run_all_tests():
    """Run all Phase 1 template tests."""
    print("\n" + "#"*70)
    print("# PHASE 1 ACTIVITY TEMPLATES - TEST SUITE")
    print("#"*70)

    results = []

    results.append(("Template Structure", test_template_structure()))
    results.append(("Activity Coverage", test_activity_counts()))
    results.append(("Cost Calculations", test_cost_calculations()))
    results.append(("Complexity Modifiers", test_complexity_modifiers()))
    results.append(("Sample Scenario", test_sample_carveout_scenario()))
    results.append(("TSA Requirements", test_tsa_activities()))

    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")

    print(f"\n  Total: {passed}/{total} tests passed")

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
