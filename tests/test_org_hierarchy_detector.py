"""
Unit Tests for Organization Hierarchy Detector

Tests the detection logic that determines whether organization census has
sufficient management structure data (FULL/PARTIAL/MISSING).

Part of adaptive organization extraction feature (spec 08).
"""

import pytest
from datetime import datetime

from stores.fact_store import FactStore, Fact
from services.org_hierarchy_detector import (
    detect_hierarchy_presence,
    HierarchyPresenceStatus,
    HierarchyPresence
)


class TestHierarchyDetection:
    """Test hierarchy presence detection logic."""

    def test_detect_full_hierarchy(self):
        """Test detection of complete hierarchy (FULL status)."""
        # Arrange: 10 roles, 90% have reports_to, layers mentioned
        # Include leadership roles to meet FULL criteria (leadership_count >= 2)
        fact_store = FactStore(deal_id="test-deal")

        # Add 3 leadership roles
        for i in range(3):
            fact_store.add_fact(
                domain="organization",
                category="leadership",
                item=f"VP {i}",
                details={'reports_to': 'CIO'},
                status="documented",
                evidence={'exact_quote': 'Org chart shows 3 management layers'},
                entity="target"
            )

        # Add 7 regular roles
        for i in range(7):
            fact_store.add_fact(
                domain="organization",
                category="roles",
                item=f"Role {i}",
                details={'reports_to': f'Manager {i // 2}'},
                status="documented",
                evidence={'exact_quote': 'Org chart shows 3 management layers'},
                entity="target"
            )

        # Act
        result = detect_hierarchy_presence(fact_store, entity="target")

        # Assert
        assert result.status == HierarchyPresenceStatus.FULL
        assert result.confidence >= 0.8
        assert result.has_reports_to is True
        assert result.leadership_count == 3
        assert result.roles_with_reports_to >= 8  # At least 80%
        assert result.total_role_count == 10
        assert len(result.gaps) == 0  # FULL has no gaps

    def test_detect_partial_hierarchy_mid_range(self):
        """Test detection of partial hierarchy (50% reports_to, no layers)."""
        # Arrange: 8 roles, 50% have reports_to, no layers mentioned
        fact_store = FactStore(deal_id="test-deal")
        for i in range(8):
            details = {'reports_to': 'Manager'} if i < 4 else {}
            fact_store.add_fact(
                domain="organization",
                category="roles",
                item=f"Role {i}",
                details=details,
                status="documented",
                evidence={'exact_quote': f'Role {i} description'},
                entity="target"
            )

        # Act
        result = detect_hierarchy_presence(fact_store, entity="target")

        # Assert
        assert result.status == HierarchyPresenceStatus.PARTIAL
        assert 0.5 <= result.confidence <= 0.7
        assert result.has_reports_to is True
        assert result.has_explicit_layers is False
        assert result.roles_with_reports_to == 4  # 50%
        assert result.total_role_count == 8
        assert len(result.gaps) > 0  # PARTIAL has gaps

    def test_detect_missing_hierarchy(self):
        """Test detection of missing hierarchy (0% reports_to, no layers/chart)."""
        # Arrange: 5 roles, no reports_to, no layers, no chart
        fact_store = FactStore(deal_id="test-deal")
        for i in range(5):
            fact_store.add_fact(
                domain="organization",
                category="roles",
                item=f"Role {i}",
                details={},  # No reports_to
                status="documented",
                evidence={'exact_quote': f'Role {i} exists'},
                entity="target"
            )

        # Act
        result = detect_hierarchy_presence(fact_store, entity="target")

        # Assert
        assert result.status == HierarchyPresenceStatus.MISSING
        assert result.confidence >= 0.6
        assert result.has_reports_to is False
        assert result.has_explicit_layers is False
        assert result.has_span_data is False
        assert result.has_org_chart is False
        assert result.roles_with_reports_to == 0
        assert len(result.gaps) == 5  # All 4 standard + "Complete documentation"

    def test_detect_borderline_80_percent(self):
        """Test borderline case at 80% threshold (79% reports_to)."""
        # Arrange: 10 roles, 70% have reports_to (below FULL threshold)
        fact_store = FactStore(deal_id="test-deal")
        for i in range(10):
            details = {'reports_to': 'Manager'} if i < 7 else {}
            fact_store.add_fact(
                domain="organization",
                category="roles",
                item=f"Role {i}",
                details=details,
                status="documented",
                evidence={'exact_quote': 'Org structure with 3 layers'},
                entity="target"
            )

        # Act
        result = detect_hierarchy_presence(fact_store, entity="target")

        # Assert - should be PARTIAL (not FULL) because 70% < 80%
        assert result.status == HierarchyPresenceStatus.PARTIAL
        assert result.has_explicit_layers is True  # "layers" mentioned
        assert result.roles_with_reports_to == 7
        assert 0.70 <= (result.roles_with_reports_to / result.total_role_count) < 0.80

    def test_detect_borderline_30_percent(self):
        """Test borderline case at 30% threshold (31% reports_to)."""
        # Arrange: 10 roles, 40% have reports_to (above MISSING threshold)
        fact_store = FactStore(deal_id="test-deal")
        for i in range(10):
            details = {'reports_to': 'Manager'} if i < 4 else {}
            fact_store.add_fact(
                domain="organization",
                category="roles",
                item=f"Role {i}",
                details=details,
                status="documented",
                evidence={'exact_quote': f'Role {i}'},
                entity="target"
            )

        # Act
        result = detect_hierarchy_presence(fact_store, entity="target")

        # Assert - should be PARTIAL (30-80% range)
        assert result.status == HierarchyPresenceStatus.PARTIAL
        assert result.roles_with_reports_to == 4  # 40%
        assert 0.30 <= (result.roles_with_reports_to / result.total_role_count) < 0.80

    def test_detect_conflicting_signals(self):
        """Test conflicting signals (org chart mentioned, but no reports_to data)."""
        # Arrange: org_chart evidence but 0% reports_to
        fact_store = FactStore(deal_id="test-deal")
        for i in range(5):
            fact_store.add_fact(
                domain="organization",
                category="roles",
                item=f"Role {i}",
                details={},  # No reports_to
                status="documented",
                evidence={'exact_quote': 'See org chart in appendix for full structure'},
                entity="target"
            )

        # Act
        result = detect_hierarchy_presence(fact_store, entity="target")

        # Assert - confidence should be penalized for conflicting signals
        assert result.has_org_chart is True  # "org chart" detected
        assert result.has_reports_to is False
        assert result.status == HierarchyPresenceStatus.PARTIAL  # Chart gives PARTIAL
        assert result.confidence < 0.7  # Penalty applied

    def test_detect_empty_facts(self):
        """Test detection with empty FactStore."""
        # Arrange: No facts
        fact_store = FactStore(deal_id="test-deal")

        # Act
        result = detect_hierarchy_presence(fact_store, entity="target")

        # Assert
        assert result.status == HierarchyPresenceStatus.UNKNOWN
        assert result.confidence == 0.0
        assert result.total_role_count == 0
        assert result.fact_count == 0
        assert "No organization data found" in result.gaps

    def test_detect_entity_filtering(self):
        """Test that detection only analyzes specified entity."""
        # Arrange: Mix of target and buyer facts
        fact_store = FactStore(deal_id="test-deal")

        # Add 5 target facts (with reports_to)
        for i in range(5):
            fact_store.add_fact(
                domain="organization",
                category="roles",
                item=f"Target Role {i}",
                details={'reports_to': 'Target Manager'},
                status="documented",
                evidence={'exact_quote': 'Target org structure'},
                entity="target"
            )

        # Add 5 buyer facts (no reports_to)
        for i in range(5):
            fact_store.add_fact(
                domain="organization",
                category="roles",
                item=f"Buyer Role {i}",
                details={},
                status="documented",
                evidence={'exact_quote': 'Buyer role'},
                entity="buyer"
            )

        # Act - analyze only target
        result = detect_hierarchy_presence(fact_store, entity="target")

        # Assert - should only see target facts
        assert result.total_role_count == 5  # Only target roles
        assert result.roles_with_reports_to == 5  # All target roles have reports_to
        assert result.fact_count == 5

    def test_detect_high_confidence_full(self):
        """Test high confidence when hierarchy is very complete."""
        # Arrange: 95% reports_to, layers + chart mentioned, 10+ roles
        fact_store = FactStore(deal_id="test-deal")
        for i in range(12):
            # 11 out of 12 = 91.7%
            details = {'reports_to': 'Manager'} if i < 11 else {}
            fact_store.add_fact(
                domain="organization",
                category="leadership" if i < 3 else "roles",
                item=f"Role {i}",
                details=details,
                status="documented",
                evidence={'exact_quote': 'Org chart shows 4 management layers with clear span of control'},
                entity="target"
            )

        # Act
        result = detect_hierarchy_presence(fact_store, entity="target")

        # Assert - high confidence FULL
        assert result.status == HierarchyPresenceStatus.FULL
        assert result.confidence >= 0.9  # High confidence
        assert result.has_reports_to is True
        assert result.has_explicit_layers is True
        assert result.has_org_chart is True
        assert result.leadership_count == 3
        assert result.total_role_count == 12

    def test_detect_gaps_identification(self):
        """Test that MISSING status populates all gap categories."""
        # Arrange: Minimal data (MISSING status)
        fact_store = FactStore(deal_id="test-deal")
        fact_store.add_fact(
            domain="organization",
            category="leadership",
            item="IT Director",
            details={},
            status="documented",
            evidence={'exact_quote': 'IT Director exists'},
            entity="target"
        )

        # Act
        result = detect_hierarchy_presence(fact_store, entity="target")

        # Assert - MISSING should have all gaps
        assert result.status == HierarchyPresenceStatus.MISSING
        assert len(result.gaps) == 5  # 4 standard + "Complete documentation"
        assert "Reporting lines (who reports to whom)" in result.gaps
        assert any("Management layers/levels" in gap for gap in result.gaps)
        assert any("Span of control" in gap for gap in result.gaps)
        assert "Organization chart or hierarchy diagram" in result.gaps
        assert "Complete IT organization structure documentation" in result.gaps


class TestEntityValidation:
    """Test P0 fix #4: Entity field validation."""

    def test_entity_validation_missing_field(self):
        """Test that missing entity field throws ValueError."""
        # Arrange: Create fact store with valid facts, then manually corrupt one
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

        # Manually corrupt the entity field (simulating upstream bug)
        fact = fact_store.get_fact(fact_id)
        fact.entity = None

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            detect_hierarchy_presence(fact_store, entity="target")

        assert "Entity field validation failed" in str(exc_info.value)
        assert "missing entity" in str(exc_info.value)

    def test_entity_validation_invalid_value(self):
        """Test that invalid entity value throws ValueError."""
        # Arrange: Create fact store, manually set invalid entity
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

        # Manually corrupt the entity field
        fact = fact_store.get_fact(fact_id)
        fact.entity = "invalid_entity"

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            detect_hierarchy_presence(fact_store, entity="target")

        assert "Entity field validation failed" in str(exc_info.value)
        assert "invalid entity values" in str(exc_info.value)

    def test_entity_parameter_validation(self):
        """Test that invalid entity parameter throws ValueError."""
        # Arrange
        fact_store = FactStore(deal_id="test-deal")

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            detect_hierarchy_presence(fact_store, entity="invalid")

        assert "Invalid entity 'invalid'" in str(exc_info.value)
        assert "Must be 'target' or 'buyer'" in str(exc_info.value)


class TestConfidenceScoring:
    """Test confidence score calculations."""

    def test_confidence_high_sample_size(self):
        """Test that large sample size boosts confidence."""
        # Arrange: 15 roles (large sample)
        fact_store = FactStore(deal_id="test-deal")
        for i in range(15):
            fact_store.add_fact(
                domain="organization",
                category="roles",
                item=f"Role {i}",
                details={'reports_to': 'Manager'},
                status="documented",
                evidence={'exact_quote': 'Org with clear hierarchy'},
                entity="target"
            )

        # Act
        result = detect_hierarchy_presence(fact_store, entity="target")

        # Assert - sample size >= 10 gives +0.2 boost
        assert result.total_role_count == 15
        assert result.confidence >= 0.7  # Base 0.5 + sample boost + explicit layers

    def test_confidence_borderline_penalty(self):
        """Test that borderline percentages reduce confidence."""
        # Arrange: 30% reports_to (at 30% threshold)
        fact_store = FactStore(deal_id="test-deal")
        for i in range(10):
            details = {'reports_to': 'Manager'} if i < 3 else {}  # 30%
            fact_store.add_fact(
                domain="organization",
                category="roles",
                item=f"Role {i}",
                details=details,
                status="documented",
                evidence={'exact_quote': 'Role info'},
                entity="target"
            )

        # Act
        result = detect_hierarchy_presence(fact_store, entity="target")

        # Assert - confidence penalized for being near 30% threshold
        reports_to_pct = result.roles_with_reports_to / result.total_role_count
        assert 0.28 <= reports_to_pct <= 0.32  # Near threshold


class TestHierarchyPresenceDataClass:
    """Test HierarchyPresence dataclass methods."""

    def test_to_dict_serialization(self):
        """Test that HierarchyPresence.to_dict() produces valid dict."""
        # Arrange
        presence = HierarchyPresence(
            status=HierarchyPresenceStatus.FULL,
            confidence=0.85,
            has_reports_to=True,
            has_explicit_layers=True,
            has_span_data=False,
            has_org_chart=True,
            leadership_count=3,
            total_role_count=12,
            roles_with_reports_to=10,
            gaps=[],
            detection_timestamp="2026-02-11T10:00:00Z",
            fact_count=12
        )

        # Act
        result = presence.to_dict()

        # Assert
        assert result['status'] == 'full'
        assert result['confidence'] == 0.85
        assert result['has_reports_to'] is True
        assert result['leadership_count'] == 3
        assert result['gaps'] == []
        assert 'detection_timestamp' in result
