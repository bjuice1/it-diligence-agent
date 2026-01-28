"""
Test Two-Phase Analysis Implementation.

Validates that:
1. Documents are properly separated by entity (TARGET vs BUYER)
2. TARGET facts are locked after Phase 1
3. BUYER analysis receives TARGET context
4. Entity enforcement prevents cross-contamination
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools_v2.fact_store import FactStore


def test_entity_locking():
    """Test that entity facts can be locked and prevented from modification."""
    print("\n=== Test: Entity Locking ===")

    store = FactStore()

    # Add some TARGET facts
    store.add_fact(
        domain="infrastructure",
        category="data_center",
        item="Target has 2 data centers",
        details={"count": 2, "locations": ["Chicago", "Dallas"]},
        status="documented",
        evidence={"exact_quote": "We operate 2 data centers", "source_section": "Infrastructure"},
        entity="target",
        analysis_phase="target_extraction"
    )
    store.add_fact(
        domain="applications",
        category="erp",
        item="Target uses SAP ERP",
        details={"vendor": "SAP", "version": "S/4HANA"},
        status="documented",
        evidence={"exact_quote": "Our ERP is SAP S/4HANA", "source_section": "Applications"},
        entity="target",
        analysis_phase="target_extraction"
    )

    print(f"  Added 2 TARGET facts")

    # Lock TARGET facts
    locked_count = store.lock_entity_facts("target")
    print(f"  Locked {locked_count} TARGET facts")

    # Verify lock status
    assert store.is_entity_locked("target"), "TARGET should be locked"
    assert not store.is_entity_locked("buyer"), "BUYER should not be locked"
    print(f"  Lock status verified: TARGET=locked, BUYER=unlocked")

    # Try to add another TARGET fact (should fail)
    try:
        store.add_fact(
            domain="infrastructure",
            category="cloud",
            item="Target uses AWS",
            details={"provider": "AWS"},
            status="documented",
            evidence={"exact_quote": "We use AWS", "source_section": "Cloud"},
            entity="target",
            analysis_phase="target_extraction"
        )
        print("  ERROR: Should have raised ValueError for locked entity")
        return False
    except ValueError as e:
        print(f"  Correctly rejected new TARGET fact: {e}")

    # Add a BUYER fact (should succeed)
    store.add_fact(
        domain="infrastructure",
        category="data_center",
        item="Buyer has 3 data centers",
        details={"count": 3},
        status="documented",
        evidence={"exact_quote": "We operate 3 data centers", "source_section": "Infrastructure"},
        entity="buyer",
        analysis_phase="buyer_extraction"
    )
    print(f"  Successfully added BUYER fact after TARGET lock")

    # Verify counts
    target_facts = [f for f in store.facts if f.entity == "target"]
    buyer_facts = [f for f in store.facts if f.entity == "buyer"]

    assert len(target_facts) == 2, f"Expected 2 TARGET facts, got {len(target_facts)}"
    assert len(buyer_facts) == 1, f"Expected 1 BUYER fact, got {len(buyer_facts)}"
    print(f"  Final counts: TARGET={len(target_facts)}, BUYER={len(buyer_facts)}")

    print("  ✓ Entity locking test PASSED")
    return True


def test_snapshot_creation():
    """Test that snapshots provide read-only context."""
    print("\n=== Test: Snapshot Creation ===")

    store = FactStore()

    # Add TARGET facts
    store.add_fact(
        domain="infrastructure",
        category="data_center",
        item="Target operates 2 data centers in Chicago and Dallas",
        details={"count": 2, "locations": ["Chicago", "Dallas"]},
        status="documented",
        evidence={"exact_quote": "Our 2 data centers are in Chicago and Dallas", "source_section": "Infra"},
        entity="target",
        source_document="Target Company Profile.pdf"
    )
    store.add_fact(
        domain="applications",
        category="erp",
        item="Target uses Oracle EBS as primary ERP",
        details={"vendor": "Oracle", "product": "EBS"},
        status="documented",
        evidence={"exact_quote": "We use Oracle EBS for all ERP needs", "source_section": "Apps"},
        entity="target",
        source_document="Target Company Profile.pdf"
    )

    # Lock and create snapshot
    store.lock_entity_facts("target")
    snapshot = store.create_snapshot("target")

    print(f"  Created snapshot with {len(snapshot.facts)} facts")

    # Verify snapshot content
    assert len(snapshot.facts) == 2, "Snapshot should have 2 facts"

    # Get context string
    context = snapshot.to_context_string()
    print(f"  Context string length: {len(context)} characters")

    # Verify context contains key info
    assert "data center" in context.lower(), "Context should mention data centers"
    assert "oracle" in context.lower() or "erp" in context.lower(), "Context should mention ERP"

    print(f"  Context preview:\n{context[:500]}...")
    print("  ✓ Snapshot creation test PASSED")
    return True


def test_integration_insights():
    """Test that integration insights can reference both entities."""
    print("\n=== Test: Integration Insights ===")

    store = FactStore()

    # Add TARGET fact
    store.add_fact(
        domain="infrastructure",
        category="cloud",
        item="Target uses AWS as primary cloud",
        details={"provider": "AWS"},
        status="documented",
        evidence={"exact_quote": "AWS is our primary cloud provider", "source_section": "Cloud"},
        entity="target"
    )

    # Lock TARGET
    store.lock_entity_facts("target")

    # Add BUYER fact
    store.add_fact(
        domain="infrastructure",
        category="cloud",
        item="Buyer uses Azure as primary cloud",
        details={"provider": "Azure"},
        status="documented",
        evidence={"exact_quote": "Azure is our primary cloud provider", "source_section": "Cloud"},
        entity="buyer"
    )

    # Add integration insight
    store.add_integration_insight(
        domain="infrastructure",
        category="cloud",
        item="Cloud platform mismatch: Target uses AWS while Buyer uses Azure - will require integration strategy",
        details={"target_cloud": "AWS", "buyer_cloud": "Azure"},
        evidence={"exact_quote": "Integration analysis reveals cloud mismatch", "source_section": "Integration Analysis"},
        target_fact_ids=["F-INFRA-001"],
        buyer_fact_ids=["F-INFRA-002"]
    )

    # Get integration insights
    insights = store.get_integration_insights()
    print(f"  Created {len(insights)} integration insight(s)")

    assert len(insights) == 1, "Should have 1 integration insight"
    assert insights[0].is_integration_insight, "Should be marked as integration insight"

    print(f"  Integration insight: {insights[0].item}")
    print("  ✓ Integration insights test PASSED")
    return True


def test_phase_summary():
    """Test that phase summary correctly categorizes facts."""
    print("\n=== Test: Phase Summary ===")

    store = FactStore()

    # Add facts from different phases
    store.add_fact(
        domain="infrastructure",
        category="compute",
        item="Target fact 1",
        details={},
        status="documented",
        evidence={"exact_quote": "Fact 1", "source_section": "Test"},
        entity="target",
        analysis_phase="target_extraction"
    )
    store.add_fact(
        domain="applications",
        category="erp",
        item="Target fact 2",
        details={},
        status="documented",
        evidence={"exact_quote": "Fact 2", "source_section": "Test"},
        entity="target",
        analysis_phase="target_extraction"
    )

    store.lock_entity_facts("target")

    store.add_fact(
        domain="infrastructure",
        category="compute",
        item="Buyer fact 1",
        details={},
        status="documented",
        evidence={"exact_quote": "Buyer Fact 1", "source_section": "Test"},
        entity="buyer",
        analysis_phase="buyer_extraction"
    )

    # Get phase summary
    summary = store.get_phase_summary()

    print(f"  Phase summary: {summary}")

    assert summary["target"]["fact_count"] == 2, "Should have 2 TARGET facts"
    assert summary["target"]["locked"] == True, "TARGET should be locked"
    assert summary["buyer"]["fact_count"] == 1, "Should have 1 BUYER fact"
    assert summary["buyer"]["locked"] == False, "BUYER should not be locked"

    print("  ✓ Phase summary test PASSED")
    return True


def test_document_separation():
    """Test that document separation logic works correctly."""
    print("\n=== Test: Document Separation ===")

    # Simulate the _separate_documents_by_entity function logic
    documents = [
        {"filename": "Target Company Profile.pdf", "entity": "target", "content": "Target content..."},
        {"filename": "Buyer Company Profile.pdf", "entity": "buyer", "content": "Buyer content..."},
        {"filename": "General Doc.pdf", "content": "General content..."},  # No entity specified
    ]

    deal_context = {
        "target_name": "National Mutual",
        "buyer_name": "Atlantic International"
    }

    # Separate by entity
    target_docs = []
    buyer_docs = []

    for doc in documents:
        entity = doc.get("entity", "").lower()
        filename = doc.get("filename", "").lower()

        if entity == "target" or "target" in filename:
            target_docs.append(doc)
        elif entity == "buyer" or "buyer" in filename:
            buyer_docs.append(doc)
        else:
            # Default to target if unspecified
            target_docs.append(doc)

    print(f"  Target documents: {len(target_docs)}")
    print(f"  Buyer documents: {len(buyer_docs)}")

    assert len(target_docs) == 2, "Should have 2 target docs (including default)"
    assert len(buyer_docs) == 1, "Should have 1 buyer doc"

    print("  ✓ Document separation test PASSED")
    return True


def run_all_tests():
    """Run all two-phase analysis tests."""
    print("=" * 60)
    print("TWO-PHASE ANALYSIS TEST SUITE")
    print("=" * 60)

    results = []

    results.append(("Entity Locking", test_entity_locking()))
    results.append(("Snapshot Creation", test_snapshot_creation()))
    results.append(("Integration Insights", test_integration_insights()))
    results.append(("Phase Summary", test_phase_summary()))
    results.append(("Document Separation", test_document_separation()))

    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"  {name}: {status}")

    print(f"\n  Total: {passed}/{total} tests passed")
    print("=" * 60)

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
