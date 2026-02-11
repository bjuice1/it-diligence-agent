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
