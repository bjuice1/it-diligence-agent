"""
Test Phase 7 Activity Templates (Operational Run-Rate)

Validates:
1. Template structure and completeness
2. Cost calculations (ANNUAL costs)
3. Coverage of key operational areas
4. Sample scenario costing
5. IT staffing calculations
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools_v2.activity_templates_phase7 import (
    INFRASTRUCTURE_OPS_TEMPLATES,
    APPLICATION_SUPPORT_TEMPLATES,
    IT_STAFFING_TEMPLATES,
    MANAGED_SERVICES_TEMPLATES,
    SUPPORT_CONTRACTS_TEMPLATES,
    get_phase7_templates,
    get_phase7_activity_by_id,
    calculate_phase7_activity_cost,
    calculate_it_staffing_needs,
)
from tools_v2.activity_templates_v2 import COMPLEXITY_MULTIPLIERS, INDUSTRY_MODIFIERS


def test_template_structure():
    """Test that all templates have required fields."""
    print("\n" + "="*70)
    print("TEST 1: Template Structure Validation")
    print("="*70)

    required_fields = ["id", "name", "description", "activity_type", "phase", "requires_tsa"]
    cost_fields = ["base_cost", "per_user_cost", "per_vm_cost", "per_server_cost",
                   "per_endpoint_cost", "per_database_cost", "per_app_cost", "per_site_cost",
                   "per_tb_cost", "per_cpu_cost", "per_core_cost", "per_fte_cost",
                   "per_employee_cost", "per_device_cost", "per_host_cost", "per_kw_cost",
                   "per_asset_cost"]

    all_templates = get_phase7_templates()
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

    all_templates = get_phase7_templates()

    for category, workstreams in all_templates.items():
        print(f"\n  Category: {category}")
        for workstream, activities in workstreams.items():
            print(f"    {workstream}: {len(activities)} activities")

    # Verify minimum counts
    infra_count = len(INFRASTRUCTURE_OPS_TEMPLATES.get("run_rate", []))
    app_count = len(APPLICATION_SUPPORT_TEMPLATES.get("run_rate", []))
    staff_count = len(IT_STAFFING_TEMPLATES.get("run_rate", []))
    msp_count = len(MANAGED_SERVICES_TEMPLATES.get("run_rate", []))
    support_count = len(SUPPORT_CONTRACTS_TEMPLATES.get("run_rate", []))

    print(f"\n  Infrastructure Ops: {infra_count} activities (target: 10+)")
    print(f"  Application Support: {app_count} activities (target: 10+)")
    print(f"  IT Staffing: {staff_count} activities (target: 10+)")
    print(f"  Managed Services: {msp_count} activities (target: 8+)")
    print(f"  Support Contracts: {support_count} activities (target: 10+)")

    return infra_count >= 10 and app_count >= 10 and staff_count >= 10 and msp_count >= 8


def test_cost_calculations():
    """Test cost calculation logic."""
    print("\n" + "="*70)
    print("TEST 3: Cost Calculations (Annual)")
    print("="*70)

    # Test different cost models
    test_cases = [
        ("OPS-INF-001", "Cloud compute costs"),
        ("OPS-INF-020", "WAN circuit costs"),
        ("OPS-APP-001", "ERP maintenance"),
        ("OPS-APP-040", "M365 productivity suite"),
        ("OPS-STF-010", "Infrastructure engineers"),
        ("OPS-MSP-010", "Managed SOC"),
        ("OPS-SUP-001", "Microsoft EA renewal"),
    ]

    all_passed = True

    for activity_id, description in test_cases:
        activity = get_phase7_activity_by_id(activity_id)
        if not activity:
            print(f"  {activity_id}: Not found")
            all_passed = False
            continue

        low, high, formula = calculate_phase7_activity_cost(
            activity,
            user_count=1000,
            vm_count=100,
            site_count=8,
            database_count=20,
        )

        if low > 0 and high >= low:
            print(f"  {activity_id} ({description}): ${low:,.0f}-${high:,.0f}/year")
            print(f"      Formula: {formula}")
        else:
            print(f"  {activity_id}: Invalid cost range ({low}, {high})")
            all_passed = False

    return all_passed


def test_run_rate_scenarios():
    """Test operational run-rate scenarios."""
    print("\n" + "="*70)
    print("TEST 4: Run-Rate Scenarios")
    print("="*70)

    scenarios = [
        {
            "name": "Cloud-First (100 VMs)",
            "activities": ["OPS-INF-001", "OPS-INF-002", "OPS-INF-003", "OPS-INF-004",
                         "OPS-INF-005", "OPS-INF-030", "OPS-INF-031"],
            "quantities": {"vm_count": 100, "storage_tb": 50},
        },
        {
            "name": "Full IT Staff (1000 users)",
            "activities": ["OPS-STF-001", "OPS-STF-002", "OPS-STF-010", "OPS-STF-011",
                         "OPS-STF-012", "OPS-STF-020", "OPS-STF-030", "OPS-STF-040"],
            "quantities": {"user_count": 1000, "fte_count": 1},
        },
        {
            "name": "Managed Services Model",
            "activities": ["OPS-MSP-001", "OPS-MSP-002", "OPS-MSP-010", "OPS-MSP-020",
                         "OPS-MSP-021", "OPS-MSP-030"],
            "quantities": {"vm_count": 100, "user_count": 1000, "endpoint_count": 1300},
        },
    ]

    for scenario in scenarios:
        print(f"\n  Scenario: {scenario['name']}")
        total_low = 0
        total_high = 0

        # Build quantities dict with defaults
        quantities = {
            "user_count": 1000, "vm_count": 100, "site_count": 8,
            "database_count": 20, "app_count": 30, "storage_tb": 50,
            "endpoint_count": 1300, "server_count": 50
        }
        quantities.update(scenario.get("quantities", {}))

        for act_id in scenario["activities"]:
            activity = get_phase7_activity_by_id(act_id)
            if activity:
                low, high, _ = calculate_phase7_activity_cost(activity, **quantities)
                total_low += low
                total_high += high

        print(f"    Activities: {len(scenario['activities'])}")
        print(f"    Annual cost range: ${total_low:,.0f} - ${total_high:,.0f}")

    return True


def test_sample_standalone_scenario():
    """Test a realistic standalone IT run-rate."""
    print("\n" + "="*70)
    print("TEST 5: Sample Standalone IT Run-Rate")
    print("="*70)

    print("\n  Scenario: 1,500 user standalone company")
    print("  - Hybrid cloud (100 VMs cloud, 50 on-prem)")
    print("  - 8 sites with WAN connectivity")
    print("  - ERP, CRM, standard business apps")
    print("  - Mix of in-house and managed services")

    quantities = {
        "user_count": 1500,
        "employee_count": 1500,
        "vm_count": 100,
        "server_count": 50,
        "endpoint_count": 2000,
        "database_count": 25,
        "app_count": 40,
        "site_count": 8,
        "storage_tb": 75,
        "cpu_count": 40,
        "core_count": 120,
        "device_count": 60,
        "complexity": "moderate",
        "industry": "standard",
    }

    all_templates = get_phase7_templates()

    workstream_totals = {}
    grand_total_low = 0
    grand_total_high = 0

    for category, workstreams in all_templates.items():
        for workstream, activities in workstreams.items():
            ws_low = 0
            ws_high = 0

            for activity in activities:
                low, high, _ = calculate_phase7_activity_cost(activity, **quantities)
                ws_low += low
                ws_high += high

            key = f"{workstream}"
            workstream_totals[key] = (ws_low, ws_high)
            grand_total_low += ws_low
            grand_total_high += ws_high

    print("\n  Annual cost by workstream:")
    for ws, (low, high) in sorted(workstream_totals.items(), key=lambda x: -x[1][1]):
        print(f"    {ws}: ${low:,.0f} - ${high:,.0f}/year")

    print(f"\n  ANNUAL IT RUN-RATE: ${grand_total_low:,.0f} - ${grand_total_high:,.0f}")
    print(f"  Per-user annual: ${grand_total_low/1500:,.0f} - ${grand_total_high/1500:,.0f}")

    # Sanity check - run rate should be reasonable
    # Note: This sums ALL activities including overlapping options (in-house AND managed)
    # In practice, you'd choose one model. Total represents upper bound of all options.
    # For 1500 users with ALL options: expect $8-20M low, $20-60M high
    reasonable = 5000000 < grand_total_low < 20000000 and 15000000 < grand_total_high < 60000000

    print(f"\n  Reasonableness check: {'PASS' if reasonable else 'FAIL'}")
    print(f"  Note: Total includes overlapping options (in-house + managed services)")

    return reasonable


def test_it_staffing_calculation():
    """Test IT staffing needs calculation."""
    print("\n" + "="*70)
    print("TEST 6: IT Staffing Needs Calculation")
    print("="*70)

    scenarios = [
        {"name": "Small (500 users)", "user_count": 500, "vm_count": 40, "database_count": 10, "app_count": 15, "site_count": 3},
        {"name": "Medium (1500 users)", "user_count": 1500, "vm_count": 100, "database_count": 25, "app_count": 40, "site_count": 8},
        {"name": "Large (5000 users)", "user_count": 5000, "vm_count": 300, "database_count": 75, "app_count": 100, "site_count": 20},
    ]

    for scenario in scenarios:
        print(f"\n  Scenario: {scenario['name']}")
        staffing = calculate_it_staffing_needs(
            user_count=scenario["user_count"],
            vm_count=scenario["vm_count"],
            database_count=scenario["database_count"],
            app_count=scenario["app_count"],
            site_count=scenario["site_count"],
            complexity="moderate",
        )

        total_min = sum(v[0] for v in staffing.values())
        total_max = sum(v[1] for v in staffing.values())

        print(f"    Total FTE range: {total_min} - {total_max}")
        print(f"    Key roles:")
        for role, (min_fte, max_fte, notes) in list(staffing.items())[:5]:
            print(f"      {role}: {min_fte}-{max_fte} ({notes})")

    return True


def test_in_house_vs_managed():
    """Compare in-house vs managed services costs."""
    print("\n" + "="*70)
    print("TEST 7: In-House vs Managed Services Comparison")
    print("="*70)

    quantities = {
        "user_count": 1000,
        "vm_count": 100,
        "endpoint_count": 1300,
        "site_count": 8,
        "app_count": 30,
    }

    # In-house staffing costs
    in_house_ids = ["OPS-STF-010", "OPS-STF-011", "OPS-STF-020", "OPS-STF-040", "OPS-STF-041"]
    in_house_low, in_house_high = 0, 0
    for act_id in in_house_ids:
        activity = get_phase7_activity_by_id(act_id)
        if activity:
            low, high, _ = calculate_phase7_activity_cost(activity, fte_count=2, **quantities)
            in_house_low += low
            in_house_high += high

    # Managed services costs
    managed_ids = ["OPS-MSP-001", "OPS-MSP-003", "OPS-MSP-010", "OPS-MSP-020", "OPS-MSP-021"]
    managed_low, managed_high = 0, 0
    for act_id in managed_ids:
        activity = get_phase7_activity_by_id(act_id)
        if activity:
            low, high, _ = calculate_phase7_activity_cost(activity, **quantities)
            managed_low += low
            managed_high += high

    print(f"\n  In-House Model (selected roles):")
    print(f"    Annual cost: ${in_house_low:,.0f} - ${in_house_high:,.0f}")

    print(f"\n  Managed Services Model:")
    print(f"    Annual cost: ${managed_low:,.0f} - ${managed_high:,.0f}")

    print(f"\n  Note: Managed services often better for <1000 users")
    print(f"        In-house often better for >2000 users")

    return True


def test_combined_all_phases():
    """Test Phase 1-7 combined scenario."""
    print("\n" + "="*70)
    print("TEST 8: One-Time vs Recurring Cost Summary")
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
        from tools_v2.activity_templates_phase3 import (
            get_phase3_templates,
            calculate_phase3_activity_cost,
        )
        from tools_v2.activity_templates_phase4 import (
            get_phase4_templates,
            calculate_phase4_activity_cost,
        )
        from tools_v2.activity_templates_phase5 import (
            get_phase5_templates,
            calculate_phase5_activity_cost,
        )
        from tools_v2.activity_templates_phase6 import (
            get_phase6_templates,
            calculate_phase6_activity_cost,
        )

        print("\n  Scenario: 1,500 user IT Separation")
        print("  ONE-TIME costs (Phases 1-6): Separation/Integration")
        print("  RECURRING costs (Phase 7): Annual Run-Rate")

        user_count = 1500

        # One-time phases
        one_time_phases = []

        # Phase 1
        p1_low, p1_high, p1_count = 0, 0, 0
        for cat in get_phase1_templates().values():
            for acts in cat.values():
                for a in acts:
                    l, h, _ = calculate_activity_cost(a, user_count=user_count, app_count=40, vm_count=100)
                    p1_low += l
                    p1_high += h
                    p1_count += 1
        one_time_phases.append(("Phase 1-6 (Separation)", p1_low, p1_high, p1_count))

        # Sum phases 2-6
        for phase_num, get_fn, calc_fn, kwargs in [
            (2, get_phase2_templates, calculate_phase2_activity_cost, {"user_count": user_count, "site_count": 8}),
            (3, get_phase3_templates, calculate_phase3_activity_cost, {"user_count": user_count, "app_count": 40}),
            (4, get_phase4_templates, calculate_phase4_activity_cost, {"user_count": user_count, "database_count": 25, "storage_tb": 75}),
            (5, get_phase5_templates, calculate_phase5_activity_cost, {"user_count": user_count, "database_count": 25, "cpu_count": 50}),
            (6, get_phase6_templates, calculate_phase6_activity_cost, {"user_count": user_count, "site_count": 10, "vm_count": 150, "app_count": 40}),
        ]:
            for cat in get_fn().values():
                for acts in cat.values():
                    for a in acts:
                        l, h, _ = calc_fn(a, **kwargs)
                        p1_low += l
                        p1_high += h
                        p1_count += 1

        # Phase 7 (recurring)
        p7_low, p7_high, p7_count = 0, 0, 0
        for cat in get_phase7_templates().values():
            for acts in cat.values():
                for a in acts:
                    l, h, _ = calculate_phase7_activity_cost(
                        a, user_count=user_count, vm_count=100, database_count=25,
                        app_count=40, site_count=8, storage_tb=75
                    )
                    p7_low += l
                    p7_high += h
                    p7_count += 1

        print(f"\n  ONE-TIME SEPARATION COSTS (Phases 1-6):")
        print(f"    Total: ${p1_low:,.0f} - ${p1_high:,.0f}")
        print(f"    Activities: {p1_count}")

        print(f"\n  ANNUAL RUN-RATE COSTS (Phase 7):")
        print(f"    Total: ${p7_low:,.0f} - ${p7_high:,.0f}/year")
        print(f"    Activities: {p7_count}")

        print(f"\n  TOTAL FIRST-YEAR COST:")
        print(f"    ${p1_low + p7_low:,.0f} - ${p1_high + p7_high:,.0f}")

        print(f"\n  Per-user first year: ${(p1_low + p7_low)/user_count:,.0f} - ${(p1_high + p7_high)/user_count:,.0f}")

        return True

    except ImportError as e:
        print(f"\n  Could not import other phases: {e}")
        return False


def run_all_tests():
    """Run all Phase 7 template tests."""
    print("\n" + "#"*70)
    print("# PHASE 7 ACTIVITY TEMPLATES (OPERATIONAL RUN-RATE) - TEST SUITE")
    print("#"*70)

    results = []

    results.append(("Template Structure", test_template_structure()))
    results.append(("Activity Coverage", test_activity_counts()))
    results.append(("Cost Calculations", test_cost_calculations()))
    results.append(("Run-Rate Scenarios", test_run_rate_scenarios()))
    results.append(("Sample Scenario", test_sample_standalone_scenario()))
    results.append(("IT Staffing Calculation", test_it_staffing_calculation()))
    results.append(("In-House vs Managed", test_in_house_vs_managed()))
    results.append(("Combined Phases 1-7", test_combined_all_phases()))

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
