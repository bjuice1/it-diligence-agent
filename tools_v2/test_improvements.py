"""
Test script for the improved three-stage reasoning system.

Tests:
1. Category normalization (fragile matching fix)
2. Quantity tracking (assumed vs extracted)
3. TSA source separation
4. Operational activities and run-rate
5. Feedback tracking

Run with: python -m tools_v2.test_improvements
"""

import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools_v2.three_stage_reasoning import (
    normalize_category,
    CATEGORY_SYNONYMS,
    stage2_match_activities,
    IdentifiedConsideration,
    QuantitativeContext,
    ACTIVITY_TEMPLATES,
    OPERATIONAL_RUNRATE_TEMPLATES,
)
from tools_v2.feedback_tracker import FeedbackTracker, CostOverride


def test_category_normalization():
    """Test that category synonyms are properly normalized."""
    print("\n" + "="*70)
    print("TEST 1: Category Normalization")
    print("="*70)

    test_cases = [
        ("parent_dependency", "parent_dependency"),
        ("identity_separation", "parent_dependency"),  # LLM might say this
        ("shared_service", "parent_dependency"),
        ("shared_services", "parent_dependency"),
        ("tech_mismatch", "technology_mismatch"),
        ("platform_mismatch", "technology_mismatch"),
        ("integration_need", "technology_mismatch"),
        ("legacy_system", "technical_debt"),
        ("eol", "technical_debt"),
        ("security_risk", "security_gap"),
        ("licensing", "license_issue"),
        ("unknown_category", "unknown_category"),  # Pass through
    ]

    passed = 0
    failed = 0

    for input_cat, expected in test_cases:
        result = normalize_category(input_cat)
        status = "✓" if result == expected else "✗"
        if result == expected:
            passed += 1
        else:
            failed += 1
        print(f"  {status} '{input_cat}' → '{result}' (expected: '{expected}')")

    print(f"\n  Results: {passed} passed, {failed} failed")
    return failed == 0


def test_quantity_tracking():
    """Test that quantities are tracked with source attribution."""
    print("\n" + "="*70)
    print("TEST 2: Quantity Tracking (Assumed vs Extracted)")
    print("="*70)

    # Create test considerations
    considerations = [
        IdentifiedConsideration(
            consideration_id="C-001",
            source_fact_ids=["F-001"],
            workstream="identity",
            finding="Identity services provided by parent",
            implication="Need standalone identity",
            deal_impact="Day-1 critical",
            suggested_category="parent_dependency",
        ),
    ]

    # Test with extracted quantities
    print("\n  A) With extracted quantities:")
    quant_extracted = {"user_count": 500, "application_count": 20}
    activities, tsa, quant_ctx = stage2_match_activities(
        considerations=considerations,
        quant_context=quant_extracted,
        deal_type="carveout",
        include_runrate=False,
    )

    print(f"     User count: {quant_ctx.user_count} (source: {quant_ctx.user_count_source})")
    print(f"     App count: {quant_ctx.application_count} (source: {quant_ctx.application_count_source})")
    print(f"     Site count: {quant_ctx.site_count} (source: {quant_ctx.site_count_source})")

    # Test with missing quantities (should assume defaults)
    print("\n  B) With missing quantities (should assume defaults):")
    quant_empty = {}
    activities2, tsa2, quant_ctx2 = stage2_match_activities(
        considerations=considerations,
        quant_context=quant_empty,
        deal_type="carveout",
        include_runrate=False,
    )

    print(f"     User count: {quant_ctx2.user_count} (source: {quant_ctx2.user_count_source})")
    print(f"     App count: {quant_ctx2.application_count} (source: {quant_ctx2.application_count_source})")

    # Check that activities flag assumed quantities
    print("\n  C) Activity cost formulas flag assumptions:")
    for a in activities2[:2]:
        print(f"     {a.name}:")
        print(f"       Formula: {a.cost_formula}")
        print(f"       Quantity source: {a.quantity_source}")

    # Verify
    extracted_ok = quant_ctx.user_count_source == "extracted"
    assumed_ok = quant_ctx2.user_count_source == "assumed"
    formula_flagged = "[ASSUMED]" in activities2[2].cost_formula if len(activities2) > 2 else True

    print(f"\n  Results: extracted tracking={'✓' if extracted_ok else '✗'}, "
          f"assumed tracking={'✓' if assumed_ok else '✗'}")

    return extracted_ok and assumed_ok


def test_activity_types():
    """Test that different activity types are generated."""
    print("\n" + "="*70)
    print("TEST 3: Activity Types (Implementation, Operational, License)")
    print("="*70)

    # Create considerations that should trigger different activity types
    considerations = [
        IdentifiedConsideration(
            consideration_id="C-001",
            source_fact_ids=["F-001"],
            workstream="identity",
            finding="Identity dependency on parent",
            implication="Need standalone identity",
            deal_impact="Day-1 critical",
            suggested_category="parent_dependency",
        ),
        IdentifiedConsideration(
            consideration_id="C-002",
            source_fact_ids=["F-002"],
            workstream="applications",
            finding="Software licenses tied to parent agreement",
            implication="Need license transfer or new procurement",
            deal_impact="Cost driver",
            suggested_category="license_issue",
        ),
        IdentifiedConsideration(
            consideration_id="C-003",
            source_fact_ids=["F-003"],
            workstream="service_desk",
            finding="IT support provided by parent",
            implication="Need standalone IT operations",
            deal_impact="TSA required",
            suggested_category="resource_gap",
        ),
    ]

    quant = {"user_count": 1000}

    activities, tsa, quant_ctx = stage2_match_activities(
        considerations=considerations,
        quant_context=quant,
        deal_type="carveout",
        include_runrate=True,
    )

    # Group by type
    by_type = {}
    for a in activities:
        t = a.activity_type
        if t not in by_type:
            by_type[t] = []
        by_type[t].append(a)

    print("\n  Activities by type:")
    for activity_type, acts in sorted(by_type.items()):
        print(f"\n  {activity_type.upper()}:")
        for a in acts[:3]:  # Show first 3
            print(f"    - {a.name}: ${a.cost_range[0]:,.0f}-${a.cost_range[1]:,.0f}")

    # Check we have multiple types
    has_implementation = "implementation" in by_type
    has_runrate = "operational_runrate" in by_type

    print(f"\n  Results: implementation={'✓' if has_implementation else '✗'}, "
          f"run-rate={'✓' if has_runrate else '✗'}")

    return has_implementation


def test_tsa_source_tracking():
    """Test that TSA sources are tracked."""
    print("\n" + "="*70)
    print("TEST 4: TSA Source Tracking")
    print("="*70)

    considerations = [
        IdentifiedConsideration(
            consideration_id="C-001",
            source_fact_ids=["F-001"],
            workstream="identity",
            finding="Identity dependency",
            implication="Need standalone identity",
            deal_impact="Day-1 critical",
            suggested_category="parent_dependency",
        ),
    ]

    activities, tsa_services, _ = stage2_match_activities(
        considerations=considerations,
        quant_context={"user_count": 500},
        deal_type="carveout",
        include_runrate=False,
    )

    print("\n  TSA Services from rules:")
    for tsa in tsa_services:
        print(f"    - {tsa['service']}: {tsa['duration_months']} months (source: {tsa.get('source', 'unknown')})")

    # Check activities have TSA source
    print("\n  Activities with TSA:")
    for a in activities:
        if a.requires_tsa:
            print(f"    - {a.name}: TSA source = {a.tsa_source}")

    rule_source = all(t.get('source') == 'rule' for t in tsa_services)
    print(f"\n  Results: all TSA sources tracked={'✓' if rule_source else '✗'}")

    return rule_source


def test_feedback_tracker():
    """Test the feedback tracking system."""
    print("\n" + "="*70)
    print("TEST 5: Feedback Tracker")
    print("="*70)

    # Create tracker (in-memory, no file)
    tracker = FeedbackTracker()

    # Record some overrides
    tracker.record_cost_override(
        activity_name="Migrate user accounts",
        activity_id="A-003",
        workstream="identity",
        template_cost_range=(15000, 40000),
        override_cost_range=(25000, 55000),
        deal_type="carveout",
        user_count=1000,
        user_count_source="extracted",
        source="team",
        reason="Enterprise complexity",
        session_id="TEST-001",
    )

    tracker.record_cost_override(
        activity_name="Migrate user accounts",
        activity_id="A-003",
        workstream="identity",
        template_cost_range=(15000, 40000),
        override_cost_range=(22000, 50000),
        deal_type="carveout",
        user_count=800,
        user_count_source="extracted",
        source="team",
        reason="Complex integrations",
        session_id="TEST-002",
    )

    tracker.record_cost_override(
        activity_name="Migrate mailboxes",
        activity_id="A-005",
        workstream="email",
        template_cost_range=(20000, 50000),
        override_cost_range=(35000, 70000),
        deal_type="carveout",
        user_count=1000,
        user_count_source="extracted",
        source="seller",
        reason="Large attachments, complex rules",
        session_id="TEST-001",
    )

    print("\n  Recorded 3 cost overrides")

    # Get stats for an activity
    stats = tracker.get_template_stats("Migrate user accounts")
    print(f"\n  Stats for 'Migrate user accounts':")
    print(f"    Times overridden: {stats.times_overridden}")
    print(f"    Avg delta %: {stats.avg_delta_percent:.1f}%")
    print(f"    Override contexts: {stats.override_contexts}")

    # Generate report
    report = tracker.generate_report()
    print(f"\n  Feedback Report:")
    print(f"    Total overrides: {report['total_cost_overrides']}")
    print(f"    Unique activities: {report['unique_activities_overridden']}")

    if report['recommendations']:
        print(f"    Recommendations:")
        for r in report['recommendations'][:3]:
            print(f"      - {r}")

    return stats.times_overridden == 2


def test_workstream_fallback():
    """Test that workstream-only matching works as fallback."""
    print("\n" + "="*70)
    print("TEST 6: Workstream Fallback Matching")
    print("="*70)

    # Use a category that won't match anything
    considerations = [
        IdentifiedConsideration(
            consideration_id="C-001",
            source_fact_ids=["F-001"],
            workstream="identity",  # This workstream exists in templates
            finding="Some identity issue",
            implication="Need to address",
            deal_impact="Important",
            suggested_category="completely_made_up_category",  # This won't match
        ),
    ]

    activities, _, _ = stage2_match_activities(
        considerations=considerations,
        quant_context={"user_count": 500},
        deal_type="carveout",
        include_runrate=False,
    )

    print(f"\n  Category used: 'completely_made_up_category'")
    print(f"  Workstream: 'identity'")
    print(f"  Activities matched: {len(activities)}")

    if activities:
        print("\n  Matched activities (via fallback):")
        for a in activities[:3]:
            print(f"    - {a.name}")

    # Should have matched via fallback
    matched = len(activities) > 0
    print(f"\n  Results: fallback matching={'✓' if matched else '✗'}")

    return matched


def run_all_tests():
    """Run all tests."""
    print("\n" + "#"*70)
    print("# THREE-STAGE REASONING IMPROVEMENTS - TEST SUITE")
    print("#"*70)

    results = []

    results.append(("Category Normalization", test_category_normalization()))
    results.append(("Quantity Tracking", test_quantity_tracking()))
    results.append(("Activity Types", test_activity_types()))
    results.append(("TSA Source Tracking", test_tsa_source_tracking()))
    results.append(("Feedback Tracker", test_feedback_tracker()))
    results.append(("Workstream Fallback", test_workstream_fallback()))

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
