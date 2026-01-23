"""
Test Phase 5 Activity Templates (Licensing)

Validates:
1. Template structure and completeness
2. Cost calculations
3. Coverage of key activities
4. Sample scenario costing
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools_v2.activity_templates_phase5 import (
    MICROSOFT_LICENSE_TEMPLATES,
    DATABASE_LICENSE_TEMPLATES,
    INFRASTRUCTURE_LICENSE_TEMPLATES,
    APPLICATION_LICENSE_TEMPLATES,
    LICENSE_COMPLIANCE_TEMPLATES,
    get_phase5_templates,
    get_phase5_activity_by_id,
    calculate_phase5_activity_cost,
)


def test_template_structure():
    """Test that all templates have required fields."""
    print("\n" + "="*70)
    print("TEST 1: Template Structure Validation")
    print("="*70)

    required_fields = ["id", "name", "description", "activity_type", "phase", "requires_tsa"]
    cost_fields = ["base_cost", "per_user_cost", "per_server_cost", "per_database_cost",
                   "per_cpu_cost", "per_core_cost", "per_vm_cost", "per_app_cost",
                   "per_endpoint_cost", "per_device_cost", "per_developer_cost"]

    all_templates = get_phase5_templates()
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

    all_templates = get_phase5_templates()

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
    ms_count = len(MICROSOFT_LICENSE_TEMPLATES.get("license_issue", []))
    db_count = len(DATABASE_LICENSE_TEMPLATES.get("license_issue", []))
    infra_count = len(INFRASTRUCTURE_LICENSE_TEMPLATES.get("license_issue", []))
    app_count = len(APPLICATION_LICENSE_TEMPLATES.get("license_issue", []))
    compliance_count = len(LICENSE_COMPLIANCE_TEMPLATES.get("license_issue", []))

    print(f"\n  Microsoft: {ms_count} activities (target: 12+)")
    print(f"  Database: {db_count} activities (target: 10+)")
    print(f"  Infrastructure: {infra_count} activities (target: 8+)")
    print(f"  Applications: {app_count} activities (target: 10+)")
    print(f"  Compliance: {compliance_count} activities (target: 4+)")

    return ms_count >= 12 and db_count >= 10 and infra_count >= 8 and app_count >= 10


def test_cost_calculations():
    """Test cost calculation logic."""
    print("\n" + "="*70)
    print("TEST 3: Cost Calculations")
    print("="*70)

    # Test different cost models
    test_cases = [
        ("LIC-MS-001", "Microsoft licensing assessment"),
        ("LIC-MS-011", "M365 license procurement"),
        ("LIC-DB-001", "Oracle licensing assessment"),
        ("LIC-DB-011", "SQL Server license procurement"),
        ("LIC-INF-002", "VMware license procurement"),
        ("LIC-APP-011", "Salesforce license procurement"),
    ]

    all_passed = True

    for activity_id, description in test_cases:
        activity = get_phase5_activity_by_id(activity_id)
        if not activity:
            print(f"  {activity_id}: Not found")
            all_passed = False
            continue

        low, high, formula = calculate_phase5_activity_cost(
            activity,
            user_count=1000,
            server_count=50,
            database_count=20,
            cpu_count=30,
            core_count=100,
        )

        if low > 0 and high >= low:
            print(f"  {activity_id} ({description}): ${low:,.0f}-${high:,.0f}")
            print(f"      Formula: {formula}")
        else:
            print(f"  {activity_id}: Invalid cost range ({low}, {high})")
            all_passed = False

    return all_passed


def test_licensing_scenarios():
    """Test licensing-specific scenarios."""
    print("\n" + "="*70)
    print("TEST 4: Licensing Scenarios")
    print("="*70)

    scenarios = [
        {
            "name": "Microsoft Stack (1000 users)",
            "activities": ["LIC-MS-001", "LIC-MS-002", "LIC-MS-010", "LIC-MS-011",
                         "LIC-MS-012", "LIC-MS-030", "LIC-MS-031", "LIC-MS-032"],
            "quantities": {"user_count": 1000, "server_count": 30},
        },
        {
            "name": "Oracle Environment (15 databases)",
            "activities": ["LIC-DB-001", "LIC-DB-002", "LIC-DB-003", "LIC-DB-004", "LIC-DB-005"],
            "quantities": {"database_count": 15},
        },
        {
            "name": "VMware Infrastructure (40 hosts)",
            "activities": ["LIC-INF-001", "LIC-INF-002", "LIC-INF-010", "LIC-INF-011"],
            "quantities": {"cpu_count": 80, "vm_count": 200},
        },
    ]

    for scenario in scenarios:
        print(f"\n  Scenario: {scenario['name']}")
        total_low = 0
        total_high = 0

        # Build quantities dict with defaults
        quantities = {"user_count": 1000, "server_count": 50, "database_count": 20, "cpu_count": 30, "vm_count": 100}
        quantities.update(scenario.get("quantities", {}))

        for act_id in scenario["activities"]:
            activity = get_phase5_activity_by_id(act_id)
            if activity:
                low, high, _ = calculate_phase5_activity_cost(activity, **quantities)
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

    print("\n  Scenario: 1,500 user carveout - Licensing")
    print("  - Full Microsoft stack (M365, Azure, Windows)")
    print("  - Oracle databases (10)")
    print("  - SQL Server databases (15)")
    print("  - VMware infrastructure (50 CPU sockets)")
    print("  - Salesforce CRM")

    quantities = {
        "user_count": 1500,
        "server_count": 75,
        "database_count": 25,
        "cpu_count": 50,
        "core_count": 150,
        "vm_count": 150,
        "endpoint_count": 2000,
        "app_count": 30,
        "complexity": "moderate",
        "industry": "standard",
    }

    all_templates = get_phase5_templates()

    workstream_totals = {}
    grand_total_low = 0
    grand_total_high = 0

    for category, workstreams in all_templates.items():
        for workstream, activities in workstreams.items():
            ws_low = 0
            ws_high = 0

            for activity in activities:
                low, high, _ = calculate_phase5_activity_cost(activity, **quantities)
                ws_low += low
                ws_high += high

            key = f"{workstream} ({category})"
            workstream_totals[key] = (ws_low, ws_high)
            grand_total_low += ws_low
            grand_total_high += ws_high

    print("\n  Cost by workstream:")
    for ws, (low, high) in sorted(workstream_totals.items(), key=lambda x: -x[1][1]):
        print(f"    {ws}: ${low:,.0f} - ${high:,.0f}")

    print(f"\n  PHASE 5 TOTAL: ${grand_total_low:,.0f} - ${grand_total_high:,.0f}")

    # Sanity check - licensing costs should be significant but not astronomical
    reasonable = 500000 < grand_total_low < 5000000 and 1000000 < grand_total_high < 15000000

    print(f"\n  Reasonableness check: {'PASS' if reasonable else 'FAIL'}")

    return reasonable


def test_tsa_activities():
    """Test TSA tracking."""
    print("\n" + "="*70)
    print("TEST 6: TSA Requirements")
    print("="*70)

    all_templates = get_phase5_templates()

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


def test_combined_all_phases():
    """Test Phase 1-5 combined scenario."""
    print("\n" + "="*70)
    print("TEST 7: Combined Phases 1-5 Scenario")
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

        print("\n  Scenario: 1,500 user carveout (FULL SCOPE)")
        print("  Phases 1-4: Infrastructure, Apps, Data")
        print("  Phase 5: Licensing")

        user_count = 1500

        # Calculate each phase
        phases = []

        # Phase 1
        p1_low, p1_high, p1_count = 0, 0, 0
        for cat in get_phase1_templates().values():
            for acts in cat.values():
                for a in acts:
                    l, h, _ = calculate_activity_cost(a, user_count=user_count, app_count=40, vm_count=100)
                    p1_low += l
                    p1_high += h
                    p1_count += 1
        phases.append(("Phase 1 (Core Infra)", p1_low, p1_high, p1_count))

        # Phase 2
        p2_low, p2_high, p2_count = 0, 0, 0
        for cat in get_phase2_templates().values():
            for acts in cat.values():
                for a in acts:
                    l, h, _ = calculate_phase2_activity_cost(a, user_count=user_count, site_count=8)
                    p2_low += l
                    p2_high += h
                    p2_count += 1
        phases.append(("Phase 2 (Network/Security)", p2_low, p2_high, p2_count))

        # Phase 3
        p3_low, p3_high, p3_count = 0, 0, 0
        for cat in get_phase3_templates().values():
            for acts in cat.values():
                for a in acts:
                    l, h, _ = calculate_phase3_activity_cost(a, user_count=user_count, app_count=25)
                    p3_low += l
                    p3_high += h
                    p3_count += 1
        phases.append(("Phase 3 (Applications)", p3_low, p3_high, p3_count))

        # Phase 4
        p4_low, p4_high, p4_count = 0, 0, 0
        for cat in get_phase4_templates().values():
            for acts in cat.values():
                for a in acts:
                    l, h, _ = calculate_phase4_activity_cost(a, user_count=user_count, database_count=25, storage_tb=75)
                    p4_low += l
                    p4_high += h
                    p4_count += 1
        phases.append(("Phase 4 (Data/Migration)", p4_low, p4_high, p4_count))

        # Phase 5
        p5_low, p5_high, p5_count = 0, 0, 0
        for cat in get_phase5_templates().values():
            for acts in cat.values():
                for a in acts:
                    l, h, _ = calculate_phase5_activity_cost(a, user_count=user_count, database_count=25, cpu_count=50)
                    p5_low += l
                    p5_high += h
                    p5_count += 1
        phases.append(("Phase 5 (Licensing)", p5_low, p5_high, p5_count))

        # Print results
        combined_low = sum(p[1] for p in phases)
        combined_high = sum(p[2] for p in phases)
        total_activities = sum(p[3] for p in phases)

        for name, low, high, count in phases:
            print(f"  {name}: ${low:,.0f} - ${high:,.0f}")

        print(f"\n  COMBINED TOTAL: ${combined_low:,.0f} - ${combined_high:,.0f}")

        print("\n  Activity counts:")
        for name, _, _, count in phases:
            print(f"    {name}: {count} activities")
        print(f"    Total: {total_activities} activities")

        return True

    except ImportError as e:
        print(f"\n  Could not import other phases: {e}")
        return False


def run_all_tests():
    """Run all Phase 5 template tests."""
    print("\n" + "#"*70)
    print("# PHASE 5 ACTIVITY TEMPLATES (LICENSING) - TEST SUITE")
    print("#"*70)

    results = []

    results.append(("Template Structure", test_template_structure()))
    results.append(("Activity Coverage", test_activity_counts()))
    results.append(("Cost Calculations", test_cost_calculations()))
    results.append(("Licensing Scenarios", test_licensing_scenarios()))
    results.append(("Sample Scenario", test_sample_carveout_scenario()))
    results.append(("TSA Requirements", test_tsa_activities()))
    results.append(("Combined Phases 1-5", test_combined_all_phases()))

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
