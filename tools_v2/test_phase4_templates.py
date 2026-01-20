"""
Test Phase 4 Activity Templates (Data & Migration)

Validates:
1. Template structure and completeness
2. Cost calculations
3. Coverage of key activities
4. Sample scenario costing
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools_v2.activity_templates_phase4 import (
    DATABASE_TEMPLATES,
    FILE_DATA_TEMPLATES,
    ARCHIVAL_TEMPLATES,
    MIGRATION_TOOLING_TEMPLATES,
    get_phase4_templates,
    get_phase4_activity_by_id,
    calculate_phase4_activity_cost,
)
from tools_v2.activity_templates_v2 import COMPLEXITY_MULTIPLIERS, INDUSTRY_MODIFIERS


def test_template_structure():
    """Test that all templates have required fields."""
    print("\n" + "="*70)
    print("TEST 1: Template Structure Validation")
    print("="*70)

    required_fields = ["id", "name", "description", "activity_type", "phase", "requires_tsa"]
    cost_fields = ["base_cost", "per_user_cost", "per_database_cost", "per_tb_cost", "per_site_cost"]

    all_templates = get_phase4_templates()
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

    all_templates = get_phase4_templates()

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
    db_count = len(DATABASE_TEMPLATES.get("parent_dependency", []))
    file_count = len(FILE_DATA_TEMPLATES.get("parent_dependency", []))
    archive_count = len(ARCHIVAL_TEMPLATES.get("parent_dependency", []))
    tooling_count = len(MIGRATION_TOOLING_TEMPLATES.get("parent_dependency", []))

    print(f"\n  Database: {db_count} activities (target: 15+)")
    print(f"  File Data: {file_count} activities (target: 12+)")
    print(f"  Archival: {archive_count} activities (target: 8+)")
    print(f"  Migration Tooling: {tooling_count} activities (target: 10+)")

    return db_count >= 15 and file_count >= 12 and archive_count >= 8 and tooling_count >= 10


def test_cost_calculations():
    """Test cost calculation logic."""
    print("\n" + "="*70)
    print("TEST 3: Cost Calculations")
    print("="*70)

    # Test different cost models
    test_cases = [
        ("DAT-001", "Database assessment"),
        ("DAT-011", "SQL Server complex migration"),
        ("FIL-010", "File share migration"),
        ("FIL-021", "SharePoint migration"),
        ("ARC-011", "Email archive migration"),
        ("MIG-020", "Migration wave planning"),
    ]

    all_passed = True

    for activity_id, description in test_cases:
        activity = get_phase4_activity_by_id(activity_id)
        if not activity:
            print(f"  {activity_id}: Not found")
            all_passed = False
            continue

        low, high, formula = calculate_phase4_activity_cost(
            activity,
            user_count=1000,
            database_count=20,
            storage_tb=50,
            site_count=25,
        )

        if low > 0 and high >= low:
            print(f"  {activity_id} ({description}): ${low:,.0f}-${high:,.0f}")
            print(f"      Formula: {formula}")
        else:
            print(f"  {activity_id}: Invalid cost range ({low}, {high})")
            all_passed = False

    return all_passed


def test_database_scenarios():
    """Test database-specific scenarios."""
    print("\n" + "="*70)
    print("TEST 4: Database Migration Scenarios")
    print("="*70)

    scenarios = [
        {
            "name": "SQL Server to Azure (10 databases)",
            "activities": ["DAT-001", "DAT-002", "DAT-003", "DAT-005", "DAT-013", "DAT-050", "DAT-051"],
            "quantities": {"database_count": 10},
        },
        {
            "name": "Oracle Migration (5 complex DBs)",
            "activities": ["DAT-001", "DAT-002", "DAT-004", "DAT-005", "DAT-021", "DAT-050", "DAT-051"],
            "quantities": {"database_count": 5},
        },
        {
            "name": "Data Warehouse Migration (100TB)",
            "activities": ["DAT-001", "DAT-040", "DAT-041", "DAT-050"],
            "quantities": {"database_count": 3, "storage_tb": 100},
        },
    ]

    for scenario in scenarios:
        print(f"\n  Scenario: {scenario['name']}")
        total_low = 0
        total_high = 0

        for act_id in scenario["activities"]:
            activity = get_phase4_activity_by_id(act_id)
            if activity:
                low, high, _ = calculate_phase4_activity_cost(
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

    print("\n  Scenario: 1,500 user carveout")
    print("  - 25 databases (mix of SQL Server, Oracle)")
    print("  - 75 TB file data")
    print("  - 40 SharePoint sites")
    print("  - Email archive migration")

    quantities = {
        "user_count": 1500,
        "database_count": 25,
        "storage_tb": 75,
        "site_count": 40,
        "complexity": "moderate",
        "industry": "standard",
    }

    all_templates = get_phase4_templates()

    workstream_totals = {}
    grand_total_low = 0
    grand_total_high = 0

    for category, workstreams in all_templates.items():
        for workstream, activities in workstreams.items():
            ws_low = 0
            ws_high = 0

            for activity in activities:
                low, high, _ = calculate_phase4_activity_cost(activity, **quantities)
                ws_low += low
                ws_high += high

            key = f"{workstream} ({category})"
            workstream_totals[key] = (ws_low, ws_high)
            grand_total_low += ws_low
            grand_total_high += ws_high

    print("\n  Cost by workstream:")
    for ws, (low, high) in sorted(workstream_totals.items(), key=lambda x: -x[1][1]):
        print(f"    {ws}: ${low:,.0f} - ${high:,.0f}")

    print(f"\n  PHASE 4 TOTAL: ${grand_total_low:,.0f} - ${grand_total_high:,.0f}")

    # Sanity check
    reasonable = 500000 < grand_total_low < 5000000 and 1000000 < grand_total_high < 15000000

    print(f"\n  Reasonableness check: {'PASS' if reasonable else 'FAIL'}")

    return reasonable


def test_tsa_activities():
    """Test TSA tracking."""
    print("\n" + "="*70)
    print("TEST 6: TSA Requirements")
    print("="*70)

    all_templates = get_phase4_templates()

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
    """Test Phase 1-4 combined scenario."""
    print("\n" + "="*70)
    print("TEST 7: Combined Phases 1-4 Scenario")
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

        print("\n  Scenario: 1,500 user carveout (FULL SCOPE)")
        print("  Phase 1: Identity, Email, Infrastructure")
        print("  Phase 2: Network, Security, Perimeter")
        print("  Phase 3: ERP, CRM, HCM, Apps, SaaS")
        print("  Phase 4: Database, Files, Archive, Tooling")

        # Common quantities
        user_count = 1500

        # Phase 1
        p1_templates = get_phase1_templates()
        p1_total_low, p1_total_high, p1_count = 0, 0, 0
        for cat in p1_templates.values():
            for acts in cat.values():
                for activity in acts:
                    low, high, _ = calculate_activity_cost(activity, user_count=user_count, app_count=40, vm_count=75)
                    p1_total_low += low
                    p1_total_high += high
                    p1_count += 1

        # Phase 2
        p2_templates = get_phase2_templates()
        p2_total_low, p2_total_high, p2_count = 0, 0, 0
        for cat in p2_templates.values():
            for acts in cat.values():
                for activity in acts:
                    low, high, _ = calculate_phase2_activity_cost(activity, user_count=user_count, site_count=8)
                    p2_total_low += low
                    p2_total_high += high
                    p2_count += 1

        # Phase 3
        p3_templates = get_phase3_templates()
        p3_total_low, p3_total_high, p3_count = 0, 0, 0
        for cat in p3_templates.values():
            for acts in cat.values():
                for activity in acts:
                    low, high, _ = calculate_phase3_activity_cost(activity, user_count=user_count, app_count=25)
                    p3_total_low += low
                    p3_total_high += high
                    p3_count += 1

        # Phase 4
        p4_templates = get_phase4_templates()
        p4_total_low, p4_total_high, p4_count = 0, 0, 0
        for cat in p4_templates.values():
            for acts in cat.values():
                for activity in acts:
                    low, high, _ = calculate_phase4_activity_cost(activity, user_count=user_count, database_count=25, storage_tb=75)
                    p4_total_low += low
                    p4_total_high += high
                    p4_count += 1

        combined_low = p1_total_low + p2_total_low + p3_total_low + p4_total_low
        combined_high = p1_total_high + p2_total_high + p3_total_high + p4_total_high
        total_activities = p1_count + p2_count + p3_count + p4_count

        print(f"\n  Phase 1 (Core Infrastructure): ${p1_total_low:,.0f} - ${p1_total_high:,.0f}")
        print(f"  Phase 2 (Network & Security): ${p2_total_low:,.0f} - ${p2_total_high:,.0f}")
        print(f"  Phase 3 (Applications): ${p3_total_low:,.0f} - ${p3_total_high:,.0f}")
        print(f"  Phase 4 (Data & Migration): ${p4_total_low:,.0f} - ${p4_total_high:,.0f}")
        print(f"\n  COMBINED TOTAL: ${combined_low:,.0f} - ${combined_high:,.0f}")

        print(f"\n  Activity counts:")
        print(f"    Phase 1: {p1_count} activities")
        print(f"    Phase 2: {p2_count} activities")
        print(f"    Phase 3: {p3_count} activities")
        print(f"    Phase 4: {p4_count} activities")
        print(f"    Total: {total_activities} activities")

        return True

    except ImportError as e:
        print(f"\n  Could not import other phases: {e}")
        return False


def run_all_tests():
    """Run all Phase 4 template tests."""
    print("\n" + "#"*70)
    print("# PHASE 4 ACTIVITY TEMPLATES (DATA & MIGRATION) - TEST SUITE")
    print("#"*70)

    results = []

    results.append(("Template Structure", test_template_structure()))
    results.append(("Activity Coverage", test_activity_counts()))
    results.append(("Cost Calculations", test_cost_calculations()))
    results.append(("Database Scenarios", test_database_scenarios()))
    results.append(("Sample Scenario", test_sample_carveout_scenario()))
    results.append(("TSA Requirements", test_tsa_activities()))
    results.append(("Combined Phases 1-4", test_combined_all_phases()))

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
