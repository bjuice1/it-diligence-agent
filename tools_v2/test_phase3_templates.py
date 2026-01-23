"""
Test Phase 3 Activity Templates (Applications)

Validates:
1. Template structure and completeness
2. Cost calculations
3. Coverage of key activities
4. Sample scenario costing
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools_v2.activity_templates_phase3 import (
    ERP_TEMPLATES,
    CRM_TEMPLATES,
    HRHCM_TEMPLATES,
    CUSTOM_APP_TEMPLATES,
    SAAS_TEMPLATES,
    get_phase3_templates,
    get_phase3_activity_by_id,
    calculate_phase3_activity_cost,
)


def test_template_structure():
    """Test that all templates have required fields."""
    print("\n" + "="*70)
    print("TEST 1: Template Structure Validation")
    print("="*70)

    required_fields = ["id", "name", "description", "activity_type", "phase", "requires_tsa"]
    cost_fields = ["base_cost", "per_user_cost", "per_employee_cost", "per_app_cost",
                   "per_integration_cost", "per_contract_cost", "per_record_cost"]

    all_templates = get_phase3_templates()
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

    all_templates = get_phase3_templates()

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
    erp_count = len(ERP_TEMPLATES.get("parent_dependency", []))
    crm_count = len(CRM_TEMPLATES.get("parent_dependency", []))
    hcm_count = len(HRHCM_TEMPLATES.get("parent_dependency", []))
    app_count = len(CUSTOM_APP_TEMPLATES.get("parent_dependency", []))
    saas_count = len(SAAS_TEMPLATES.get("parent_dependency", []))

    print(f"\n  ERP: {erp_count} activities (target: 15+)")
    print(f"  CRM: {crm_count} activities (target: 10+)")
    print(f"  HR/HCM: {hcm_count} activities (target: 15+)")
    print(f"  Custom Apps: {app_count} activities (target: 10+)")
    print(f"  SaaS: {saas_count} activities (target: 15+)")

    return erp_count >= 15 and crm_count >= 10 and hcm_count >= 15 and app_count >= 10 and saas_count >= 15


def test_cost_calculations():
    """Test cost calculation logic."""
    print("\n" + "="*70)
    print("TEST 3: Cost Calculations")
    print("="*70)

    # Test different cost models
    test_cases = [
        ("ERP-001", "ERP assessment"),
        ("ERP-010", "SAP system copy"),
        ("CRM-012", "Salesforce data migration"),
        ("HCM-012", "Workday data migration"),
        ("APP-011", "Moderate app migration"),
        ("SAS-012", "SaaS user provisioning"),
    ]

    all_passed = True

    for activity_id, description in test_cases:
        activity = get_phase3_activity_by_id(activity_id)
        if not activity:
            print(f"  {activity_id}: Not found")
            all_passed = False
            continue

        low, high, formula = calculate_phase3_activity_cost(
            activity,
            user_count=1000,
            employee_count=1000,
            app_count=30,
            integration_count=20,
        )

        if low > 0 and high >= low:
            print(f"  {activity_id} ({description}): ${low:,.0f}-${high:,.0f}")
            print(f"      Formula: {formula}")
        else:
            print(f"  {activity_id}: Invalid cost range ({low}, {high})")
            all_passed = False

    return all_passed


def test_erp_scenarios():
    """Test ERP-specific scenarios."""
    print("\n" + "="*70)
    print("TEST 4: ERP Separation Scenarios")
    print("="*70)

    scenarios = [
        {
            "name": "SAP S/4HANA Carveout",
            "activities": ["ERP-001", "ERP-002", "ERP-003", "ERP-004", "ERP-006",
                         "ERP-010", "ERP-012", "ERP-013", "ERP-014",
                         "ERP-040", "ERP-041", "ERP-044", "ERP-045"],
            "quantities": {"integration_count": 30},
        },
        {
            "name": "NetSuite Separation",
            "activities": ["ERP-001", "ERP-002", "ERP-006", "ERP-030",
                         "ERP-040", "ERP-043", "ERP-044"],
            "quantities": {"integration_count": 15},
        },
    ]

    for scenario in scenarios:
        print(f"\n  Scenario: {scenario['name']}")
        total_low = 0
        total_high = 0

        for act_id in scenario["activities"]:
            activity = get_phase3_activity_by_id(act_id)
            if activity:
                low, high, _ = calculate_phase3_activity_cost(
                    activity,
                    user_count=1000,
                    **scenario.get("quantities", {})
                )
                total_low += low
                total_high += high

        print(f"    Activities: {len(scenario['activities'])}")
        print(f"    Cost range: ${total_low:,.0f} - ${total_high:,.0f}")

    return True


def test_sample_carveout_scenario():
    """Test a realistic carveout scenario."""
    print("\n" + "="*70)
    print("TEST 5: Sample Carveout Scenario")
    print("="*70)

    print("\n  Scenario: 1,500 employee carveout")
    print("  - SAP ERP (clone approach)")
    print("  - Salesforce CRM")
    print("  - Workday HCM")
    print("  - 25 custom applications")
    print("  - 75 SaaS applications")

    quantities = {
        "user_count": 1500,
        "employee_count": 1500,
        "app_count": 25,
        "integration_count": 40,
        "contract_count": 75,
        "complexity": "moderate",
        "industry": "standard",
    }

    all_templates = get_phase3_templates()

    workstream_totals = {}
    grand_total_low = 0
    grand_total_high = 0

    for category, workstreams in all_templates.items():
        for workstream, activities in workstreams.items():
            ws_low = 0
            ws_high = 0

            for activity in activities:
                low, high, _ = calculate_phase3_activity_cost(activity, **quantities)
                ws_low += low
                ws_high += high

            key = f"{workstream} ({category})"
            workstream_totals[key] = (ws_low, ws_high)
            grand_total_low += ws_low
            grand_total_high += ws_high

    print("\n  Cost by workstream:")
    for ws, (low, high) in sorted(workstream_totals.items(), key=lambda x: -x[1][1]):
        print(f"    {ws}: ${low:,.0f} - ${high:,.0f}")

    print(f"\n  PHASE 3 TOTAL: ${grand_total_low:,.0f} - ${grand_total_high:,.0f}")

    # Sanity check - applications are typically the largest cost driver
    reasonable = 2000000 < grand_total_low < 15000000 and 5000000 < grand_total_high < 40000000

    print(f"\n  Reasonableness check: {'PASS' if reasonable else 'FAIL'}")

    return reasonable


def test_tsa_activities():
    """Test TSA tracking."""
    print("\n" + "="*70)
    print("TEST 6: TSA Requirements")
    print("="*70)

    all_templates = get_phase3_templates()

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

    # ERP/HCM typically need longer TSAs
    long_tsa = sum(1 for a in tsa_activities if a.get("tsa_duration", (0,0))[1] >= 12)
    print(f"\n  Activities with 12+ month TSA: {long_tsa}")

    return len(tsa_activities) > 0


def test_combined_all_phases():
    """Test Phase 1 + Phase 2 + Phase 3 combined scenario."""
    print("\n" + "="*70)
    print("TEST 7: Combined All Phases Scenario")
    print("="*70)

    try:
        from tools_v2.activity_templates_v2 import (
            get_phase1_templates,
            calculate_activity_cost,
        )
        from tools_v2.activity_templates_phase2 import (
            get_phase2_templates,
            calculate_phase2_activity_cost,
        )

        print("\n  Scenario: 1,500 user carveout (FULL SCOPE)")
        print("  Phase 1: Identity, Email, Infrastructure")
        print("  Phase 2: Network, Security, Perimeter")
        print("  Phase 3: ERP, CRM, HCM, Custom Apps, SaaS")

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

        # Phase 3 quantities
        p3_quantities = {
            "user_count": 1500,
            "employee_count": 1500,
            "app_count": 25,
            "integration_count": 40,
            "contract_count": 75,
            "complexity": "moderate",
            "industry": "standard",
        }

        # Calculate Phase 1
        p1_templates = get_phase1_templates()
        p1_total_low = 0
        p1_total_high = 0
        p1_count = 0

        for category, workstreams in p1_templates.items():
            for workstream, activities in workstreams.items():
                for activity in activities:
                    low, high, _ = calculate_activity_cost(activity, **p1_quantities)
                    p1_total_low += low
                    p1_total_high += high
                    p1_count += 1

        # Calculate Phase 2
        p2_templates = get_phase2_templates()
        p2_total_low = 0
        p2_total_high = 0
        p2_count = 0

        for category, workstreams in p2_templates.items():
            for workstream, activities in workstreams.items():
                for activity in activities:
                    low, high, _ = calculate_phase2_activity_cost(activity, **p2_quantities)
                    p2_total_low += low
                    p2_total_high += high
                    p2_count += 1

        # Calculate Phase 3
        p3_templates = get_phase3_templates()
        p3_total_low = 0
        p3_total_high = 0
        p3_count = 0

        for category, workstreams in p3_templates.items():
            for workstream, activities in workstreams.items():
                for activity in activities:
                    low, high, _ = calculate_phase3_activity_cost(activity, **p3_quantities)
                    p3_total_low += low
                    p3_total_high += high
                    p3_count += 1

        combined_low = p1_total_low + p2_total_low + p3_total_low
        combined_high = p1_total_high + p2_total_high + p3_total_high

        print(f"\n  Phase 1 (Core Infrastructure): ${p1_total_low:,.0f} - ${p1_total_high:,.0f}")
        print(f"  Phase 2 (Network & Security): ${p2_total_low:,.0f} - ${p2_total_high:,.0f}")
        print(f"  Phase 3 (Applications): ${p3_total_low:,.0f} - ${p3_total_high:,.0f}")
        print(f"\n  COMBINED TOTAL: ${combined_low:,.0f} - ${combined_high:,.0f}")

        print("\n  Activity counts:")
        print(f"    Phase 1: {p1_count} activities")
        print(f"    Phase 2: {p2_count} activities")
        print(f"    Phase 3: {p3_count} activities")
        print(f"    Total: {p1_count + p2_count + p3_count} activities")

        # Phase 3 should be largest cost driver
        p3_pct_low = (p3_total_low / combined_low) * 100 if combined_low > 0 else 0
        p3_pct_high = (p3_total_high / combined_high) * 100 if combined_high > 0 else 0
        print(f"\n  Phase 3 (Apps) as % of total: {p3_pct_low:.0f}%-{p3_pct_high:.0f}%")

        return True

    except ImportError as e:
        print(f"\n  Could not import other phases: {e}")
        return False


def run_all_tests():
    """Run all Phase 3 template tests."""
    print("\n" + "#"*70)
    print("# PHASE 3 ACTIVITY TEMPLATES (APPLICATIONS) - TEST SUITE")
    print("#"*70)

    results = []

    results.append(("Template Structure", test_template_structure()))
    results.append(("Activity Coverage", test_activity_counts()))
    results.append(("Cost Calculations", test_cost_calculations()))
    results.append(("ERP Scenarios", test_erp_scenarios()))
    results.append(("Sample Scenario", test_sample_carveout_scenario()))
    results.append(("TSA Requirements", test_tsa_activities()))
    results.append(("Combined All Phases", test_combined_all_phases()))

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
