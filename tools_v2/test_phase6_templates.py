"""
Test Phase 6 Activity Templates (Acquisition & Integration)

Validates:
1. Template structure and completeness
2. Cost calculations
3. Coverage of key activities
4. Sample scenario costing
5. Day 1 critical activities
6. Synergy tracking
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools_v2.activity_templates_phase6 import (
    INTEGRATION_PLANNING_TEMPLATES,
    TECHNOLOGY_INTEGRATION_TEMPLATES,
    SYNERGY_TEMPLATES,
    DAY1_TEMPLATES,
    TSA_MANAGEMENT_TEMPLATES,
    get_phase6_templates,
    get_phase6_activity_by_id,
    calculate_phase6_activity_cost,
)


def test_template_structure():
    """Test that all templates have required fields."""
    print("\n" + "="*70)
    print("TEST 1: Template Structure Validation")
    print("="*70)

    required_fields = ["id", "name", "description", "activity_type", "phase", "requires_tsa"]
    cost_fields = ["base_cost", "per_user_cost", "per_site_cost", "per_vm_cost",
                   "per_app_cost", "per_domain_cost"]

    all_templates = get_phase6_templates()
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

    all_templates = get_phase6_templates()

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
    planning_count = len(INTEGRATION_PLANNING_TEMPLATES.get("integration_planning", []))
    tech_count = len(TECHNOLOGY_INTEGRATION_TEMPLATES.get("integration_planning", []))
    synergy_count = len(SYNERGY_TEMPLATES.get("integration_planning", []))
    day1_count = len(DAY1_TEMPLATES.get("integration_planning", []))
    tsa_count = len(TSA_MANAGEMENT_TEMPLATES.get("integration_planning", []))

    print(f"\n  Integration Planning: {planning_count} activities (target: 5+)")
    print(f"  Technology Integration: {tech_count} activities (target: 10+)")
    print(f"  Synergy: {synergy_count} activities (target: 8+)")
    print(f"  Day 1: {day1_count} activities (target: 10+)")
    print(f"  TSA Management: {tsa_count} activities (target: 4+)")

    return planning_count >= 5 and tech_count >= 10 and synergy_count >= 8 and day1_count >= 10


def test_cost_calculations():
    """Test cost calculation logic."""
    print("\n" + "="*70)
    print("TEST 3: Cost Calculations")
    print("="*70)

    # Test different cost models
    test_cases = [
        ("INT-001", "IT integration assessment"),
        ("INT-012", "User migration to buyer identity"),
        ("INT-031", "Workload migration to buyer platform"),
        ("INT-041", "ERP integration/consolidation"),
        ("SYN-004", "Infrastructure consolidation"),
        ("D1-020", "Day 1 access provisioning"),
    ]

    all_passed = True

    for activity_id, description in test_cases:
        activity = get_phase6_activity_by_id(activity_id)
        if not activity:
            print(f"  {activity_id}: Not found")
            all_passed = False
            continue

        low, high, formula = calculate_phase6_activity_cost(
            activity,
            user_count=1000,
            site_count=8,
            vm_count=100,
            app_count=30,
        )

        if low > 0 and high >= low:
            print(f"  {activity_id} ({description}): ${low:,.0f}-${high:,.0f}")
            print(f"      Formula: {formula}")
        else:
            print(f"  {activity_id}: Invalid cost range ({low}, {high})")
            all_passed = False

    return all_passed


def test_integration_scenarios():
    """Test integration-specific scenarios."""
    print("\n" + "="*70)
    print("TEST 4: Integration Scenarios")
    print("="*70)

    scenarios = [
        {
            "name": "Bolt-on Integration (500 users)",
            "activities": ["INT-001", "INT-002", "INT-005", "INT-010", "INT-011",
                         "INT-012", "INT-020", "INT-021", "INT-022", "D1-001",
                         "D1-002", "D1-003", "D1-032"],
            "quantities": {"user_count": 500, "site_count": 3, "app_count": 15},
        },
        {
            "name": "Platform Acquisition (2000 users)",
            "activities": ["INT-001", "INT-002", "INT-003", "INT-004", "INT-005",
                         "INT-006", "INT-040", "INT-041", "SYN-001", "SYN-002",
                         "SYN-004", "SYN-005"],
            "quantities": {"user_count": 2000, "site_count": 12, "app_count": 50, "vm_count": 200},
        },
        {
            "name": "Day 1 Readiness Focus",
            "activities": ["D1-001", "D1-002", "D1-003", "D1-010", "D1-011",
                         "D1-020", "D1-021", "D1-030", "D1-031", "D1-032"],
            "quantities": {"user_count": 1000},
        },
    ]

    for scenario in scenarios:
        print(f"\n  Scenario: {scenario['name']}")
        total_low = 0
        total_high = 0

        # Build quantities dict with defaults
        quantities = {"user_count": 1000, "site_count": 5, "vm_count": 100, "app_count": 30, "domain_count": 3}
        quantities.update(scenario.get("quantities", {}))

        for act_id in scenario["activities"]:
            activity = get_phase6_activity_by_id(act_id)
            if activity:
                low, high, _ = calculate_phase6_activity_cost(activity, **quantities)
                total_low += low
                total_high += high

        print(f"    Activities: {len(scenario['activities'])}")
        print(f"    Cost range: ${total_low:,.0f} - ${total_high:,.0f}")

    return True


def test_sample_acquisition_scenario():
    """Test a realistic acquisition scenario."""
    print("\n" + "="*70)
    print("TEST 5: Sample Acquisition Scenario")
    print("="*70)

    print("\n  Scenario: Mid-market acquisition - 1,500 users")
    print("  - Target company being absorbed into buyer platform")
    print("  - Full identity and email migration")
    print("  - Infrastructure consolidation")
    print("  - 40 applications to rationalize")
    print("  - Cost synergies expected")

    quantities = {
        "user_count": 1500,
        "site_count": 10,
        "vm_count": 150,
        "app_count": 40,
        "domain_count": 5,
        "complexity": "moderate",
        "industry": "standard",
    }

    all_templates = get_phase6_templates()

    workstream_totals = {}
    grand_total_low = 0
    grand_total_high = 0

    for category, workstreams in all_templates.items():
        for workstream, activities in workstreams.items():
            ws_low = 0
            ws_high = 0

            for activity in activities:
                low, high, _ = calculate_phase6_activity_cost(activity, **quantities)
                ws_low += low
                ws_high += high

            key = f"{workstream} ({category})"
            workstream_totals[key] = (ws_low, ws_high)
            grand_total_low += ws_low
            grand_total_high += ws_high

    print("\n  Cost by workstream:")
    for ws, (low, high) in sorted(workstream_totals.items(), key=lambda x: -x[1][1]):
        print(f"    {ws}: ${low:,.0f} - ${high:,.0f}")

    print(f"\n  PHASE 6 TOTAL: ${grand_total_low:,.0f} - ${grand_total_high:,.0f}")

    # Sanity check - integration costs should be significant
    reasonable = 500000 < grand_total_low < 5000000 and 1000000 < grand_total_high < 15000000

    print(f"\n  Reasonableness check: {'PASS' if reasonable else 'FAIL'}")

    return reasonable


def test_day1_critical_activities():
    """Test Day 1 critical activity tracking."""
    print("\n" + "="*70)
    print("TEST 6: Day 1 Critical Activities")
    print("="*70)

    all_templates = get_phase6_templates()

    day1_critical = []
    not_day1_critical = []

    for category, workstreams in all_templates.items():
        for workstream, activities in workstreams.items():
            for activity in activities:
                if activity.get("day1_critical"):
                    day1_critical.append(activity)
                else:
                    not_day1_critical.append(activity)

    print(f"\n  Day 1 critical activities: {len(day1_critical)}")
    print(f"  Non Day 1 critical activities: {len(not_day1_critical)}")

    print("\n  Day 1 critical activities:")
    for a in day1_critical:
        print(f"    - {a['id']}: {a['name']}")

    # Verify we have Day 1 critical coverage across key areas
    critical_ids = [a['id'] for a in day1_critical]
    has_identity = any('INT-011' in id for id in critical_ids)  # Directory trust
    has_email = any('INT-021' in id for id in critical_ids)  # Mail flow
    has_network = any('INT-030' in id or 'D1-010' in id for id in critical_ids)  # Connectivity
    has_access = any('D1-020' in id for id in critical_ids)  # Access provisioning

    print("\n  Critical area coverage:")
    print(f"    Identity (INT-011): {'Yes' if has_identity else 'No'}")
    print(f"    Email (INT-021): {'Yes' if has_email else 'No'}")
    print(f"    Network (INT-030/D1-010): {'Yes' if has_network else 'No'}")
    print(f"    Access (D1-020): {'Yes' if has_access else 'No'}")

    return len(day1_critical) >= 5 and has_identity and has_email and has_network


def test_synergy_tracking():
    """Test synergy type tracking."""
    print("\n" + "="*70)
    print("TEST 7: Synergy Tracking")
    print("="*70)

    all_templates = get_phase6_templates()

    synergy_types = {"cost": [], "revenue": [], "capability": [], "none": []}

    for category, workstreams in all_templates.items():
        for workstream, activities in workstreams.items():
            for activity in activities:
                synergy_type = activity.get("synergy_type", "none")
                if synergy_type not in synergy_types:
                    synergy_types[synergy_type] = []
                synergy_types[synergy_type].append(activity)

    print("\n  Activities by synergy type:")
    for stype, activities in synergy_types.items():
        if activities:
            print(f"    {stype}: {len(activities)} activities")
            if stype != "none":
                for a in activities[:3]:
                    print(f"      - {a['id']}: {a['name']}")
                if len(activities) > 3:
                    print(f"      ... and {len(activities) - 3} more")

    # Should have cost synergies defined
    return len(synergy_types.get("cost", [])) >= 3


def test_combined_all_phases():
    """Test Phase 1-6 combined scenario."""
    print("\n" + "="*70)
    print("TEST 8: Combined Phases 1-6 Scenario")
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

        print("\n  Scenario: Full M&A IT Scope (1,500 users)")
        print("  Phases 1-4: Carveout/Separation (Seller)")
        print("  Phase 5: Licensing")
        print("  Phase 6: Integration (Buyer)")

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

        # Phase 6
        p6_low, p6_high, p6_count = 0, 0, 0
        for cat in get_phase6_templates().values():
            for acts in cat.values():
                for a in acts:
                    l, h, _ = calculate_phase6_activity_cost(a, user_count=user_count, site_count=10, vm_count=150, app_count=40)
                    p6_low += l
                    p6_high += h
                    p6_count += 1
        phases.append(("Phase 6 (Integration)", p6_low, p6_high, p6_count))

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
    """Run all Phase 6 template tests."""
    print("\n" + "#"*70)
    print("# PHASE 6 ACTIVITY TEMPLATES (ACQUISITION & INTEGRATION) - TEST SUITE")
    print("#"*70)

    results = []

    results.append(("Template Structure", test_template_structure()))
    results.append(("Activity Coverage", test_activity_counts()))
    results.append(("Cost Calculations", test_cost_calculations()))
    results.append(("Integration Scenarios", test_integration_scenarios()))
    results.append(("Sample Scenario", test_sample_acquisition_scenario()))
    results.append(("Day 1 Critical", test_day1_critical_activities()))
    results.append(("Synergy Tracking", test_synergy_tracking()))
    results.append(("Combined Phases 1-6", test_combined_all_phases()))

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
