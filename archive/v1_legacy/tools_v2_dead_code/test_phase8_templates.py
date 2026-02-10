"""
Test Phase 8 Activity Templates (Compliance & Regulatory)

Validates:
1. Template structure and completeness
2. Cost calculations
3. Coverage of key compliance areas
4. Regulatory requirement mapping
5. Sample scenario costing
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools_v2.activity_templates_phase8 import (
    DATA_PRIVACY_TEMPLATES,
    INDUSTRY_REGULATION_TEMPLATES,
    SECURITY_COMPLIANCE_TEMPLATES,
    AUDIT_READINESS_TEMPLATES,
    POLICY_TEMPLATES,
    get_phase8_templates,
    get_phase8_activity_by_id,
    calculate_phase8_activity_cost,
    get_regulatory_requirements,
)


def test_template_structure():
    """Test that all templates have required fields."""
    print("\n" + "="*70)
    print("TEST 1: Template Structure Validation")
    print("="*70)

    required_fields = ["id", "name", "description", "activity_type", "phase", "requires_tsa"]
    cost_fields = ["base_cost", "per_user_cost", "per_system_cost", "per_vendor_cost",
                   "per_site_cost", "per_control_cost", "per_module_cost"]

    all_templates = get_phase8_templates()
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

    all_templates = get_phase8_templates()

    for category, workstreams in all_templates.items():
        print(f"\n  Category: {category}")
        for workstream, activities in workstreams.items():
            print(f"    {workstream}: {len(activities)} activities")

    # Verify minimum counts
    privacy_count = len(DATA_PRIVACY_TEMPLATES.get("compliance", []))
    industry_count = len(INDUSTRY_REGULATION_TEMPLATES.get("compliance", []))
    security_count = len(SECURITY_COMPLIANCE_TEMPLATES.get("compliance", []))
    audit_count = len(AUDIT_READINESS_TEMPLATES.get("compliance", []))
    policy_count = len(POLICY_TEMPLATES.get("compliance", []))

    print(f"\n  Data Privacy: {privacy_count} activities (target: 10+)")
    print(f"  Industry Regulations: {industry_count} activities (target: 10+)")
    print(f"  Security Compliance: {security_count} activities (target: 10+)")
    print(f"  Audit Readiness: {audit_count} activities (target: 8+)")
    print(f"  Policy/Procedures: {policy_count} activities (target: 10+)")

    return privacy_count >= 10 and industry_count >= 10 and security_count >= 10


def test_cost_calculations():
    """Test cost calculation logic."""
    print("\n" + "="*70)
    print("TEST 3: Cost Calculations")
    print("="*70)

    # Test different cost models
    test_cases = [
        ("CMP-PRV-001", "Privacy program assessment"),
        ("CMP-PRV-011", "GDPR remediation"),
        ("CMP-SOX-002", "SOX ITGC remediation"),
        ("CMP-HIP-002", "HIPAA remediation"),
        ("CMP-SOC-002", "SOC 2 implementation"),
        ("CMP-ISO-002", "ISO 27001 ISMS"),
        ("CMP-POL-010", "Security policy suite"),
    ]

    all_passed = True

    for activity_id, description in test_cases:
        activity = get_phase8_activity_by_id(activity_id)
        if not activity:
            print(f"  {activity_id}: Not found")
            all_passed = False
            continue

        low, high, formula = calculate_phase8_activity_cost(
            activity,
            user_count=1000,
            system_count=30,
            vendor_count=50,
        )

        if low > 0 and high >= low:
            print(f"  {activity_id} ({description}): ${low:,.0f}-${high:,.0f}")
            print(f"      Formula: {formula}")
        else:
            print(f"  {activity_id}: Invalid cost range ({low}, {high})")
            all_passed = False

    return all_passed


def test_regulatory_requirements():
    """Test regulatory requirement mapping."""
    print("\n" + "="*70)
    print("TEST 4: Regulatory Requirement Mapping")
    print("="*70)

    scenarios = [
        {
            "name": "Healthcare company",
            "industries": ["healthcare"],
            "data_types": ["phi", "pii"],
            "geographies": ["california"],
        },
        {
            "name": "Financial services",
            "industries": ["financial_services"],
            "data_types": ["pii", "financial", "payment_card"],
            "geographies": ["new_york_financial"],
        },
        {
            "name": "Tech company with EU customers",
            "industries": ["technology"],
            "data_types": ["pii"],
            "geographies": ["eu", "california"],
        },
        {
            "name": "Government contractor",
            "industries": ["government"],
            "data_types": ["pii"],
            "geographies": ["federal_us"],
        },
    ]

    for scenario in scenarios:
        reqs = get_regulatory_requirements(
            industries=scenario.get("industries"),
            data_types=scenario.get("data_types"),
            geographies=scenario.get("geographies"),
        )
        print(f"\n  {scenario['name']}:")
        print(f"    Requirements: {', '.join(reqs)}")

    return True


def test_compliance_scenarios():
    """Test compliance-specific scenarios."""
    print("\n" + "="*70)
    print("TEST 5: Compliance Scenarios")
    print("="*70)

    scenarios = [
        {
            "name": "GDPR Compliance Program",
            "activities": ["CMP-PRV-010", "CMP-PRV-011", "CMP-PRV-012", "CMP-PRV-014",
                         "CMP-PRV-030", "CMP-PRV-031"],
            "quantities": {"user_count": 1000, "site_count": 5},
        },
        {
            "name": "SOC 2 Type II Certification",
            "activities": ["CMP-SOC-001", "CMP-SOC-002", "CMP-SOC-003", "CMP-SOC-004",
                         "CMP-POL-010", "CMP-POL-012"],
            "quantities": {"system_count": 30, "control_count": 80},
        },
        {
            "name": "Healthcare Compliance (HIPAA + HITRUST)",
            "activities": ["CMP-HIP-001", "CMP-HIP-002", "CMP-HIP-003", "CMP-CRT-001",
                         "CMP-POL-010", "CMP-POL-012"],
            "quantities": {"vendor_count": 40},
        },
        {
            "name": "Financial Services (SOX + PCI)",
            "activities": ["CMP-SOX-001", "CMP-SOX-002", "CMP-SOX-003", "CMP-SOX-004",
                         "CMP-PCI-001", "CMP-PCI-002", "CMP-PCI-003"],
            "quantities": {"system_count": 25},
        },
    ]

    for scenario in scenarios:
        print(f"\n  Scenario: {scenario['name']}")
        total_low = 0
        total_high = 0

        # Build quantities dict with defaults
        quantities = {
            "user_count": 1000, "system_count": 30, "vendor_count": 50,
            "site_count": 8, "control_count": 100, "module_count": 3
        }
        quantities.update(scenario.get("quantities", {}))

        for act_id in scenario["activities"]:
            activity = get_phase8_activity_by_id(act_id)
            if activity:
                low, high, _ = calculate_phase8_activity_cost(activity, **quantities)
                total_low += low
                total_high += high

        print(f"    Activities: {len(scenario['activities'])}")
        print(f"    Cost range: ${total_low:,.0f} - ${total_high:,.0f}")

    return True


def test_sample_compliance_scenario():
    """Test a comprehensive compliance scenario."""
    print("\n" + "="*70)
    print("TEST 6: Sample Comprehensive Compliance Scenario")
    print("="*70)

    print("\n  Scenario: 1,500 user financial services carveout")
    print("  - GDPR (EU operations)")
    print("  - SOX (public company)")
    print("  - PCI-DSS (payment processing)")
    print("  - SOC 2 (customer requirements)")
    print("  - Full policy suite needed")

    quantities = {
        "user_count": 1500,
        "system_count": 40,
        "vendor_count": 75,
        "site_count": 10,
        "control_count": 150,
        "module_count": 4,
        "complexity": "moderate",
        "industry": "financial_services",
    }

    all_templates = get_phase8_templates()

    workstream_totals = {}
    grand_total_low = 0
    grand_total_high = 0

    for category, workstreams in all_templates.items():
        for workstream, activities in workstreams.items():
            ws_low = 0
            ws_high = 0

            for activity in activities:
                low, high, _ = calculate_phase8_activity_cost(activity, **quantities)
                ws_low += low
                ws_high += high

            key = f"{workstream}"
            workstream_totals[key] = (ws_low, ws_high)
            grand_total_low += ws_low
            grand_total_high += ws_high

    print("\n  Cost by workstream:")
    for ws, (low, high) in sorted(workstream_totals.items(), key=lambda x: -x[1][1]):
        print(f"    {ws}: ${low:,.0f} - ${high:,.0f}")

    print(f"\n  PHASE 8 TOTAL: ${grand_total_low:,.0f} - ${grand_total_high:,.0f}")

    # Sanity check - compliance costs with financial services modifier
    reasonable = 1500000 < grand_total_low < 8000000 and 4000000 < grand_total_high < 20000000

    print(f"\n  Reasonableness check: {'PASS' if reasonable else 'FAIL'}")

    return reasonable


def test_regulatory_drivers():
    """Test regulatory driver coverage."""
    print("\n" + "="*70)
    print("TEST 7: Regulatory Driver Coverage")
    print("="*70)

    all_templates = get_phase8_templates()

    reg_drivers = {}

    for category, workstreams in all_templates.items():
        for workstream, activities in workstreams.items():
            for activity in activities:
                drivers = activity.get("regulatory_driver", [])
                if isinstance(drivers, str):
                    drivers = [drivers]
                for driver in drivers:
                    if driver not in reg_drivers:
                        reg_drivers[driver] = []
                    reg_drivers[driver].append(activity["id"])

    print(f"\n  Regulatory drivers covered: {len(reg_drivers)}")
    for driver in sorted(reg_drivers.keys()):
        print(f"    {driver}: {len(reg_drivers[driver])} activities")

    # Should cover key regulations
    key_regs = ["GDPR", "CCPA", "SOX", "HIPAA", "PCI-DSS", "SOC 2", "ISO 27001"]
    missing = [r for r in key_regs if r not in reg_drivers]

    if missing:
        print(f"\n  Missing key regulations: {missing}")
        return False

    print("\n  All key regulations covered")
    return True


def test_combined_all_phases():
    """Test Phase 1-8 combined scenario."""
    print("\n" + "="*70)
    print("TEST 8: Combined Phases 1-8 Scenario")
    print("="*70)

    try:
        from tools_v2.activity_templates_v2 import (
            get_phase1_templates,
        )
        from tools_v2.activity_templates_phase2 import (
            get_phase2_templates,
        )
        from tools_v2.activity_templates_phase3 import (
            get_phase3_templates,
        )
        from tools_v2.activity_templates_phase4 import (
            get_phase4_templates,
        )
        from tools_v2.activity_templates_phase5 import (
            get_phase5_templates,
        )
        from tools_v2.activity_templates_phase6 import (
            get_phase6_templates,
        )
        from tools_v2.activity_templates_phase7 import (
            get_phase7_templates,
        )

        print("\n  Scenario: 1,500 user IT Separation (Financial Services)")
        print("  Phases 1-6: Separation/Integration")
        print("  Phase 7: Annual Run-Rate")
        print("  Phase 8: Compliance & Regulatory")

        user_count = 1500

        # Phase 8 (compliance)
        p8_low, p8_high, p8_count = 0, 0, 0
        for cat in get_phase8_templates().values():
            for acts in cat.values():
                for a in acts:
                    l, h, _ = calculate_phase8_activity_cost(
                        a, user_count=user_count, system_count=40, vendor_count=75,
                        complexity="moderate", industry="financial_services"
                    )
                    p8_low += l
                    p8_high += h
                    p8_count += 1

        print("\n  PHASE 8 COMPLIANCE COSTS:")
        print(f"    Total: ${p8_low:,.0f} - ${p8_high:,.0f}")
        print(f"    Activities: {p8_count}")

        # Quick totals from other phases
        total_activities = p8_count

        # Count activities from other phases
        for get_fn in [get_phase1_templates, get_phase2_templates, get_phase3_templates,
                       get_phase4_templates, get_phase5_templates, get_phase6_templates,
                       get_phase7_templates]:
            for cat in get_fn().values():
                for acts in cat.values():
                    total_activities += len(acts)

        print(f"\n  TOTAL ACTIVITIES (Phases 1-8): {total_activities}")

        return True

    except ImportError as e:
        print(f"\n  Could not import other phases: {e}")
        return False


def run_all_tests():
    """Run all Phase 8 template tests."""
    print("\n" + "#"*70)
    print("# PHASE 8 ACTIVITY TEMPLATES (COMPLIANCE & REGULATORY) - TEST SUITE")
    print("#"*70)

    results = []

    results.append(("Template Structure", test_template_structure()))
    results.append(("Activity Coverage", test_activity_counts()))
    results.append(("Cost Calculations", test_cost_calculations()))
    results.append(("Regulatory Requirements", test_regulatory_requirements()))
    results.append(("Compliance Scenarios", test_compliance_scenarios()))
    results.append(("Sample Scenario", test_sample_compliance_scenario()))
    results.append(("Regulatory Drivers", test_regulatory_drivers()))
    results.append(("Combined Phases 1-8", test_combined_all_phases()))

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
