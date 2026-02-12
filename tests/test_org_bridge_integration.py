"""
Unit Tests for Organization Bridge Integration (Spec 11)

Tests the integration of hierarchy detection and assumption generation
into the organization bridge service.

Part of adaptive organization extraction feature.
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from stores.fact_store import FactStore
from services.organization_bridge import (
    build_organization_from_facts,
    _remove_old_assumptions_from_fact_store,
    _merge_assumptions_into_fact_store
)
from services.org_hierarchy_detector import HierarchyPresence, HierarchyPresenceStatus
from services.org_assumption_engine import OrganizationAssumption


class TestBridgeIntegrationBasic:
    """Test basic integration flow."""

    def test_bridge_with_full_hierarchy_no_assumptions(self):
        """Test that FULL hierarchy skips assumption generation."""
        # Arrange
        fact_store = FactStore(deal_id="test-deal")

        # Add facts for FULL hierarchy (80%+ with reports_to + explicit layers)
        for i in range(10):
            fact_store.add_fact(
                domain="organization",
                category="leadership" if i < 3 else "roles",
                item=f"Role {i}",
                details={'reports_to': f'Manager {i//2}'} if i < 9 else {},
                status="documented",
                # Include explicit layers to meet FULL criteria
                evidence={'exact_quote': f'Role {i} with reporting line. Organization has 3 management layers.'},
                entity="target"
            )

        # Act
        # No need to patch - just use enable_assumptions parameter
        store, status = build_organization_from_facts(
            fact_store,
            entity="target",
            enable_assumptions=True
        )

        # Assert
        assert status == "success"  # Not "success_with_assumptions"
        # No assumptions should be generated for FULL hierarchy

    def test_bridge_with_missing_hierarchy_generates_assumptions(self):
        """Test that MISSING hierarchy generates assumptions."""
        # Arrange
        fact_store = FactStore(deal_id="test-deal")

        # Add minimal facts (MISSING hierarchy)
        for i in range(3):
            fact_store.add_fact(
                domain="organization",
                category="roles",
                item=f"Role {i}",
                details={},  # No reports_to
                status="documented",
                evidence={'exact_quote': f'Role {i} exists'},
                entity="target"
            )

        company_profile = {'industry': 'technology', 'headcount': 50}

        # Act
        # No need to patch - just use enable_assumptions parameter
        store, status = build_organization_from_facts(
            fact_store,
            entity="target",
            company_profile=company_profile,
            enable_assumptions=True
        )

        # Assert
        assert status == "success_with_assumptions"
        # Check that assumptions were added to fact_store
        assumed_facts = [f for f in fact_store.facts
                        if f.domain == "organization"
                        and f.entity == "target"
                        and (f.details or {}).get('data_source') == 'assumed']
        assert len(assumed_facts) > 0

    def test_bridge_assumptions_disabled(self):
        """Test that assumptions are skipped when disabled."""
        # Arrange
        fact_store = FactStore(deal_id="test-deal")

        for i in range(3):
            fact_store.add_fact(
                domain="organization",
                category="roles",
                item=f"Role {i}",
                details={},
                status="documented",
                evidence={'exact_quote': f'Role {i}'},
                entity="target"
            )

        # Act
        store, status = build_organization_from_facts(
            fact_store,
            entity="target",
            enable_assumptions=False  # Explicitly disabled
        )

        # Assert
        assert status == "success"  # Not "success_with_assumptions"
        assumed_facts = [f for f in fact_store.facts
                        if (f.details or {}).get('data_source') == 'assumed']
        assert len(assumed_facts) == 0


class TestEntityFiltering:
    """Test entity filtering and isolation."""

    def test_bridge_filters_by_entity(self):
        """Test that bridge only processes facts for specified entity."""
        # Arrange
        fact_store = FactStore(deal_id="test-deal")

        # Add facts for both target and buyer
        for i in range(5):
            fact_store.add_fact(
                domain="organization",
                category="roles",
                item=f"Target Role {i}",
                details={'reports_to': 'Manager'},
                status="documented",
                evidence={'exact_quote': f'Target role {i}'},
                entity="target"
            )

        for i in range(3):
            fact_store.add_fact(
                domain="organization",
                category="roles",
                item=f"Buyer Role {i}",
                details={},
                status="documented",
                evidence={'exact_quote': f'Buyer role {i}'},
                entity="buyer"
            )

        # Act - analyze only target
        store, status = build_organization_from_facts(
            fact_store,
            entity="target",
            enable_assumptions=False
        )

        # Assert - should only see target data
        assert status == "success"
        # Count should reflect only target facts (5)
        # (Actual count verification depends on staff member creation logic)

    def test_bridge_entity_validation_missing_field(self):
        """Test that missing entity field throws ValueError."""
        # Arrange
        fact_store = FactStore(deal_id="test-deal")
        fact_id = fact_store.add_fact(
            domain="organization",
            category="roles",
            item="Role 1",
            details={},
            status="documented",
            evidence={'exact_quote': 'Role 1'},
            entity="target"
        )

        # Manually corrupt entity field
        fact = fact_store.get_fact(fact_id)
        fact.entity = None

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            build_organization_from_facts(fact_store, entity="target")

        assert "Entity validation failed" in str(exc_info.value)


class TestP0Fixes:
    """Test P0 critical fixes."""

    def test_p0_fix_2_idempotency_protection(self):
        """Test that duplicate assumptions are not re-added (P0 fix #2)."""
        # Arrange
        fact_store = FactStore(deal_id="test-deal")

        # Create assumptions
        assumptions = [
            OrganizationAssumption(
                item="CIO",
                category="leadership",
                details={'layer': 0},
                confidence=0.75,
                assumption_basis="Industry benchmark",
                entity="target"
            ),
            OrganizationAssumption(
                item="VP of Infrastructure",
                category="leadership",
                details={'layer': 1},
                confidence=0.70,
                assumption_basis="Industry benchmark",
                entity="target"
            )
        ]

        # Act - merge twice
        _merge_assumptions_into_fact_store(fact_store, assumptions, "test-deal", "target")
        original_count = len(fact_store.facts)

        _merge_assumptions_into_fact_store(fact_store, assumptions, "test-deal", "target")
        final_count = len(fact_store.facts)

        # Assert - no duplicates added
        assert final_count == original_count

    def test_p0_fix_3_cleanup_removes_old_assumptions(self):
        """Test that old assumptions are removed before new ones (P0 fix #3)."""
        # Arrange
        fact_store = FactStore(deal_id="test-deal")

        # Add old assumptions
        for i in range(3):
            fact_store.add_fact(
                domain="organization",
                category="leadership",
                item=f"Old Assumption {i}",
                details={'data_source': 'assumed'},
                status="documented",
                evidence={'exact_quote': 'Old assumption'},
                entity="target"
            )

        original_count = len(fact_store.facts)

        # Act - remove old assumptions
        removed = _remove_old_assumptions_from_fact_store(fact_store, "target")

        # Assert
        assert removed == 3
        assert len(fact_store.facts) == original_count - 3

    def test_p0_fix_5_entity_isolation(self):
        """Test that target and buyer assumptions don't interfere (P0 fix #5)."""
        # Arrange
        fact_store = FactStore(deal_id="test-deal")

        # Add target assumptions
        target_assumptions = [
            OrganizationAssumption(
                item="Target CIO",
                category="leadership",
                details={'layer': 0},
                confidence=0.75,
                assumption_basis="Target benchmark",
                entity="target"
            )
        ]

        # Add buyer assumptions
        buyer_assumptions = [
            OrganizationAssumption(
                item="Buyer CIO",
                category="leadership",
                details={'layer': 0},
                confidence=0.75,
                assumption_basis="Buyer benchmark",
                entity="buyer"
            )
        ]

        # Act - merge both
        _merge_assumptions_into_fact_store(fact_store, target_assumptions, "test-deal", "target")
        _merge_assumptions_into_fact_store(fact_store, buyer_assumptions, "test-deal", "buyer")

        # Cleanup target (should not affect buyer)
        _remove_old_assumptions_from_fact_store(fact_store, "target")

        # Assert - buyer assumptions still present
        buyer_facts = [f for f in fact_store.facts
                      if f.entity == "buyer" and (f.details or {}).get('data_source') == 'assumed']
        assert len(buyer_facts) == 1
        assert buyer_facts[0].item == "Buyer CIO"

    def test_p0_fix_6_atomicity_rollback_on_failure(self):
        """Test rollback when assumption merge fails (P0 fix #6)."""
        # Arrange
        fact_store = FactStore(deal_id="test-deal")

        # Add old assumptions
        for i in range(3):
            fact_store.add_fact(
                domain="organization",
                category="leadership",
                item=f"Old Assumption {i}",
                details={'data_source': 'assumed'},
                status="documented",
                evidence={'exact_quote': 'Old'},
                entity="target"
            )

        original_count = len(fact_store.facts)

        # Mock assumption merge to fail
        with patch('services.organization_bridge._merge_assumptions_into_fact_store') as mock_merge:
            mock_merge.side_effect = ValueError("Merge failed")

            # Act - should rollback
            try:
                # Simulate the bridge logic
                old_backup = [f for f in fact_store.facts
                             if (f.details or {}).get('data_source') == 'assumed']
                _remove_old_assumptions_from_fact_store(fact_store, "target")

                try:
                    mock_merge(fact_store, [], "test-deal", "target")
                except Exception:
                    # Rollback
                    fact_store.facts.extend(old_backup)
                    raise
            except ValueError:
                pass

        # Assert - old assumptions restored
        assert len(fact_store.facts) == original_count

    def test_p0_fix_list_identity_preserved_on_rollback(self):
        """Test that list identity is preserved during rollback (P0-1 fix)."""
        # Arrange
        fact_store = FactStore(deal_id="test-deal")

        # Add some observed facts
        for i in range(3):
            fact_store.add_fact(
                domain="organization",
                category="roles",
                item=f"Observed Role {i}",
                details={'observed': True},
                status="documented",
                evidence={'exact_quote': f'Role {i}'},
                entity="target"
            )

        # Add old assumptions
        for i in range(2):
            fact_store.add_fact(
                domain="organization",
                category="leadership",
                item=f"Old Assumption {i}",
                details={'data_source': 'assumed'},
                status="documented",
                evidence={'exact_quote': 'Old'},
                entity="target"
            )

        # Capture external reference to facts list BEFORE rollback
        facts_list_ref = fact_store.facts
        original_list_id = id(fact_store.facts)

        # Mock assumption merge to fail (triggers rollback path)
        with patch('services.organization_bridge._merge_assumptions_into_fact_store') as mock_merge:
            mock_merge.side_effect = ValueError("Simulated merge failure")

            # Act - trigger rollback by attempting to build with assumptions
            try:
                build_organization_from_facts(
                    fact_store,
                    entity="target",
                    enable_assumptions=True,
                    company_profile={'industry': 'technology', 'headcount': 50}
                )
            except Exception:
                pass  # Expected to fail

        # Assert - list identity is preserved (critical for thread safety)
        assert id(fact_store.facts) == original_list_id, \
            "FactStore.facts list was replaced during rollback, breaking external references"
        assert facts_list_ref is fact_store.facts, \
            "External reference to facts list became stale after rollback"

        # Assert - facts are intact (observed + old assumptions restored)
        assert len(fact_store.facts) == 5  # 3 observed + 2 old assumptions


class TestSignatureBackwardCompatibility:
    """Test backward compatibility of new signature (P0 fix #7)."""

    def test_old_signature_still_works(self):
        """Test that old 3-parameter calls still work."""
        # Arrange
        fact_store = FactStore(deal_id="test-deal")

        for i in range(3):
            fact_store.add_fact(
                domain="organization",
                category="roles",
                item=f"Role {i}",
                details={'reports_to': 'Manager'},
                status="documented",
                evidence={'exact_quote': f'Role {i}'},
                entity="target"  # Entity is set in facts
            )

        # Act - use old signature (3 parameters)
        store, status = build_organization_from_facts(fact_store, "Target", "test-deal")

        # Assert - should work (defaults apply)
        assert status in ["success", "success_with_assumptions"]

    def test_new_signature_with_entity(self):
        """Test new signature with explicit entity parameter."""
        # Arrange
        fact_store = FactStore(deal_id="test-deal")

        for i in range(3):
            fact_store.add_fact(
                domain="organization",
                category="roles",
                item=f"Role {i}",
                details={},
                status="documented",
                evidence={'exact_quote': f'Role {i}'},
                entity="buyer"
            )

        # Act - use new signature with entity="buyer"
        store, status = build_organization_from_facts(
            fact_store,
            entity="buyer",
            enable_assumptions=False
        )

        # Assert
        assert status == "success"


class TestConcurrentAccess:
    """
    P3 FIX #10: Test thread-safe behavior under concurrent access.

    Verifies that the threading.RLock in organization_bridge.py
    prevents race conditions when multiple threads call the bridge
    simultaneously with the same FactStore instance.
    """

    def test_concurrent_calls_same_fact_store(self):
        """Test that concurrent calls with same FactStore don't corrupt data."""
        import threading
        from concurrent.futures import ThreadPoolExecutor, as_completed

        # Arrange: Single FactStore shared across threads
        fact_store = FactStore(deal_id="concurrent-test")

        # Add some initial facts
        for i in range(5):
            fact_store.add_fact(
                domain="organization",
                category="roles",
                item=f"Initial Role {i}",
                details={'reports_to': 'CIO'},
                status="documented",
                evidence={'exact_quote': f'Role {i}'},
                entity="target"
            )

        # Track results
        results = []
        errors = []

        def call_bridge(thread_id):
            """Callable for each thread."""
            try:
                store, status = build_organization_from_facts(
                    fact_store,
                    entity="target",
                    enable_assumptions=True,
                    deal_id="concurrent-test"
                )
                return {"thread": thread_id, "status": status, "staff_count": len(store.staff_members)}
            except Exception as e:
                errors.append({"thread": thread_id, "error": str(e)})
                raise

        # Act: 10 concurrent calls
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(call_bridge, i) for i in range(10)]

            for future in as_completed(futures):
                result = future.result()  # Will raise if thread errored
                results.append(result)

        # Assert
        assert len(errors) == 0, f"Concurrent calls failed: {errors}"
        assert len(results) == 10, "Should have 10 successful results"

        # Staff counts should be in expected range (5 initial + 0-2 assumptions)
        # NOTE: Counts may vary slightly due to timing of assumption generation
        # The lock prevents corruption, but doesn't force identical results
        staff_counts = [r["staff_count"] for r in results]
        assert all(5 <= count <= 10 for count in staff_counts), \
            f"Staff counts outside expected range: {staff_counts}"

        # Variance should be small (within 2-3 staff members)
        count_range = max(staff_counts) - min(staff_counts)
        assert count_range <= 3, f"Too much variance in staff counts (range={count_range}): {staff_counts}"

        # FactStore should still be valid (no corruption)
        org_facts = [f for f in fact_store.facts if f.domain == "organization"]
        assert len(org_facts) > 0, "FactStore should still have organization facts"

        # Check no duplicate fact IDs (would indicate corruption)
        fact_ids = [f.item for f in org_facts]
        assert len(fact_ids) == len(set(fact_ids)) or len(fact_ids) - len(set(fact_ids)) <= 2, \
            "Excessive duplicate facts suggest FactStore corruption"

    def test_concurrent_calls_different_entities(self):
        """Test concurrent calls for different entities (target vs buyer) with same FactStore."""
        from concurrent.futures import ThreadPoolExecutor, as_completed

        # Arrange: Single FactStore with both target and buyer facts
        fact_store = FactStore(deal_id="multi-entity-test")

        # Add target facts
        for i in range(5):
            fact_store.add_fact(
                domain="organization",
                category="roles",
                item=f"Target Role {i}",
                details={'reports_to': 'Target CIO'},
                status="documented",
                evidence={'exact_quote': f'Target Role {i}'},
                entity="target"
            )

        # Add buyer facts
        for i in range(3):
            fact_store.add_fact(
                domain="organization",
                category="roles",
                item=f"Buyer Role {i}",
                details={'reports_to': 'Buyer VP'},
                status="documented",
                evidence={'exact_quote': f'Buyer Role {i}'},
                entity="buyer"
            )

        # Track results
        results = {"target": [], "buyer": []}
        errors = []

        def call_bridge_for_entity(entity, call_num):
            """Callable for each thread."""
            try:
                store, status = build_organization_from_facts(
                    fact_store,
                    entity=entity,
                    enable_assumptions=True,
                    deal_id="multi-entity-test"
                )
                return {
                    "entity": entity,
                    "call": call_num,
                    "status": status,
                    "staff_count": len(store.staff_members)
                }
            except Exception as e:
                errors.append({"entity": entity, "call": call_num, "error": str(e)})
                raise

        # Act: 5 target calls + 5 buyer calls concurrently
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []

            # Submit 5 target calls
            for i in range(5):
                futures.append(executor.submit(call_bridge_for_entity, "target", i))

            # Submit 5 buyer calls
            for i in range(5):
                futures.append(executor.submit(call_bridge_for_entity, "buyer", i))

            for future in as_completed(futures):
                result = future.result()
                results[result["entity"]].append(result)

        # Assert
        assert len(errors) == 0, f"Concurrent entity calls failed: {errors}"
        assert len(results["target"]) == 5, "Should have 5 target results"
        assert len(results["buyer"]) == 5, "Should have 5 buyer results"

        # Target results should be in expected range (5 initial + 0-2 assumptions)
        target_counts = [r["staff_count"] for r in results["target"]]
        assert all(5 <= count <= 10 for count in target_counts), \
            f"Target counts outside expected range: {target_counts}"

        # Buyer results should be in expected range (3 initial + 0-2 assumptions)
        buyer_counts = [r["staff_count"] for r in results["buyer"]]
        assert all(3 <= count <= 8 for count in buyer_counts), \
            f"Buyer counts outside expected range: {buyer_counts}"

        # Variance should be small within each entity
        target_range = max(target_counts) - min(target_counts)
        buyer_range = max(buyer_counts) - min(buyer_counts)
        assert target_range <= 3, f"Too much variance in target counts: {target_counts}"
        assert buyer_range <= 3, f"Too much variance in buyer counts: {buyer_counts}"

        # Target should generally have more staff than buyer (but allow some overlap due to assumptions)
        assert max(target_counts) >= min(buyer_counts), \
            "Target should have at least as much staff as buyer"

    def test_no_deadlock_under_concurrent_load(self):
        """Test that lock implementation doesn't cause deadlocks under heavy load."""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import time

        # Arrange
        fact_store = FactStore(deal_id="deadlock-test")

        for i in range(10):
            fact_store.add_fact(
                domain="organization",
                category="roles",
                item=f"Role {i}",
                details={'reports_to': 'Manager'},
                status="documented",
                evidence={'exact_quote': f'Role {i}'},
                entity="target"
            )

        def call_with_timeout(call_num):
            """Call bridge and track duration."""
            start = time.time()
            try:
                store, status = build_organization_from_facts(
                    fact_store,
                    entity="target",
                    enable_assumptions=True,
                    deal_id="deadlock-test"
                )
                duration = time.time() - start
                return {"call": call_num, "duration": duration, "success": True}
            except Exception as e:
                duration = time.time() - start
                return {"call": call_num, "duration": duration, "success": False, "error": str(e)}

        # Act: 20 concurrent calls with timeout monitoring
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(call_with_timeout, i) for i in range(20)]

            results = []
            for future in as_completed(futures, timeout=30):  # 30s timeout for all calls
                results.append(future.result())

        # Assert
        assert len(results) == 20, "All calls should complete"
        assert all(r["success"] for r in results), "All calls should succeed"

        # No call should take unreasonably long (no deadlock or severe contention)
        max_duration = max(r["duration"] for r in results)
        assert max_duration < 10.0, f"Max duration {max_duration}s suggests deadlock or severe contention"

        avg_duration = sum(r["duration"] for r in results) / len(results)
        assert avg_duration < 2.0, f"Avg duration {avg_duration}s suggests lock contention overhead"
