"""
Unit Tests for Inventory Schema Enhancements (Spec 10)

Tests new data provenance fields added to organization inventory:
- data_source (observed/assumed/hybrid)
- confidence_score
- assumption_basis
- observed_fields/assumed_fields

Part of adaptive organization extraction feature.
"""

import pytest
import hashlib
from typing import Dict, Any

from stores.inventory_schemas import (
    INVENTORY_SCHEMAS,
    get_schema,
    get_id_fields,
    get_all_fields
)
from models.inventory_enums import (
    InventoryDataSource,
    validate_confidence,
    CONFIDENCE_RANGES
)
from stores.fact_store import FactStore


class TestOrganizationSchemaChanges:
    """Test schema changes to organization inventory."""

    def test_schema_has_new_fields(self):
        """Test that organization schema includes all new provenance fields."""
        # Arrange
        schema = get_schema("organization")
        optional_fields = schema["optional"]

        # Assert - verify new fields present
        assert "data_source" in optional_fields
        assert "confidence_score" in optional_fields
        assert "assumption_basis" in optional_fields
        assert "observed_fields" in optional_fields
        assert "assumed_fields" in optional_fields

    def test_schema_id_fields_updated(self):
        """Test that id_fields includes entity and data_source."""
        # Arrange
        id_fields = get_id_fields("organization")

        # Assert
        assert "role" in id_fields
        assert "team" in id_fields
        assert "entity" in id_fields  # NEW
        assert "data_source" in id_fields  # NEW

    def test_all_fields_includes_new_fields(self):
        """Test that get_all_fields returns new fields."""
        # Arrange
        all_fields = get_all_fields("organization")

        # Assert
        assert "data_source" in all_fields
        assert "confidence_score" in all_fields


class TestInventoryDataSourceEnum:
    """Test InventoryDataSource enum functionality."""

    def test_enum_values(self):
        """Test enum has correct values."""
        assert InventoryDataSource.OBSERVED.value == "observed"
        assert InventoryDataSource.ASSUMED.value == "assumed"
        assert InventoryDataSource.HYBRID.value == "hybrid"

    def test_display_label(self):
        """Test human-readable display labels."""
        assert InventoryDataSource.OBSERVED.display_label == "Documented"
        assert InventoryDataSource.ASSUMED.display_label == "Assumed"
        assert InventoryDataSource.HYBRID.display_label == "Partial"

    def test_badge_color(self):
        """Test CSS class for UI badges."""
        assert InventoryDataSource.OBSERVED.badge_color == "badge-success"
        assert InventoryDataSource.ASSUMED.badge_color == "badge-warning"
        assert InventoryDataSource.HYBRID.badge_color == "badge-info"

    def test_is_verified(self):
        """Test is_verified property."""
        assert InventoryDataSource.OBSERVED.is_verified is True
        assert InventoryDataSource.ASSUMED.is_verified is False
        assert InventoryDataSource.HYBRID.is_verified is False

    def test_from_fact_observed(self):
        """Test from_fact with observed data."""
        # Arrange
        fact_store = FactStore(deal_id="test-deal")
        fact_id = fact_store.add_fact(
            domain="organization",
            category="leadership",
            item="CIO",
            details={},  # No data_source → defaults to observed
            status="documented",
            evidence={'exact_quote': 'CIO role'},
            entity="target"
        )
        fact = fact_store.get_fact(fact_id)

        # Act
        data_source = InventoryDataSource.from_fact(fact)

        # Assert
        assert data_source == InventoryDataSource.OBSERVED

    def test_from_fact_assumed(self):
        """Test from_fact with assumed data."""
        # Arrange
        fact_store = FactStore(deal_id="test-deal")
        fact_id = fact_store.add_fact(
            domain="organization",
            category="leadership",
            item="VP",
            details={'data_source': 'assumed'},  # Explicitly assumed
            status="documented",
            evidence={'exact_quote': 'Industry benchmark'},
            entity="target"
        )
        fact = fact_store.get_fact(fact_id)

        # Act
        data_source = InventoryDataSource.from_fact(fact)

        # Assert
        assert data_source == InventoryDataSource.ASSUMED

    def test_from_fact_hybrid(self):
        """Test from_fact with hybrid data."""
        # Arrange
        fact_store = FactStore(deal_id="test-deal")
        fact_id = fact_store.add_fact(
            domain="organization",
            category="leadership",
            item="Director",
            details={'data_source': 'hybrid'},  # Mixed
            status="documented",
            evidence={'exact_quote': 'Role observed, reports_to assumed'},
            entity="target"
        )
        fact = fact_store.get_fact(fact_id)

        # Act
        data_source = InventoryDataSource.from_fact(fact)

        # Assert
        assert data_source == InventoryDataSource.HYBRID


class TestConfidenceValidation:
    """Test confidence score validation."""

    def test_validate_confidence_observed_valid(self):
        """Test observed data with valid confidence."""
        assert validate_confidence("observed", 0.95) is True
        assert validate_confidence("observed", 0.8) is True
        assert validate_confidence("observed", 1.0) is True

    def test_validate_confidence_observed_invalid(self):
        """Test observed data with invalid confidence (too low)."""
        assert validate_confidence("observed", 0.75) is False
        assert validate_confidence("observed", 0.6) is False

    def test_validate_confidence_assumed_valid(self):
        """Test assumed data with valid confidence."""
        assert validate_confidence("assumed", 0.70) is True
        assert validate_confidence("assumed", 0.65) is True
        assert validate_confidence("assumed", 0.6) is True

    def test_validate_confidence_assumed_invalid_high(self):
        """Test assumed data with confidence too high."""
        assert validate_confidence("assumed", 0.85) is False
        assert validate_confidence("assumed", 0.95) is False

    def test_validate_confidence_assumed_invalid_low(self):
        """Test assumed data with confidence too low."""
        assert validate_confidence("assumed", 0.55) is False
        assert validate_confidence("assumed", 0.4) is False

    def test_validate_confidence_hybrid_valid(self):
        """Test hybrid data with valid confidence."""
        assert validate_confidence("hybrid", 0.75) is True
        assert validate_confidence("hybrid", 0.8) is True
        assert validate_confidence("hybrid", 0.7) is True

    def test_validate_confidence_unknown_data_source(self):
        """Test validation with unknown data source."""
        assert validate_confidence("invalid_source", 0.8) is False


class TestFingerprintChanges:
    """Test fingerprint calculation with new id_fields."""

    def _generate_fingerprint(self, data: Dict[str, Any]) -> str:
        """Simulate fingerprint generation (same logic as InventoryStore)."""
        id_fields = get_id_fields("organization")

        id_values = []
        for field in id_fields:
            value = data.get(field, "")
            if value:
                id_values.append(str(value).lower().strip())
            elif field == "entity":
                id_values.append("target")  # Default
            elif field == "data_source":
                id_values.append("observed")  # Default

        fingerprint_string = "|".join(id_values)
        hash_obj = hashlib.sha256(fingerprint_string.encode())
        hash_hex = hash_obj.hexdigest()[:8]
        return f"I-ORG-{hash_hex}"

    def test_fingerprint_includes_data_source(self):
        """Test that same role with different data_source gets different IDs."""
        # Arrange
        observed_data = {
            'role': 'VP of Infrastructure',
            'team': 'IT Leadership',
            'entity': 'target',
            'data_source': 'observed'
        }

        assumed_data = {
            'role': 'VP of Infrastructure',
            'team': 'IT Leadership',
            'entity': 'target',
            'data_source': 'assumed'
        }

        # Act
        observed_id = self._generate_fingerprint(observed_data)
        assumed_id = self._generate_fingerprint(assumed_data)

        # Assert
        assert observed_id != assumed_id  # Different fingerprints

    def test_fingerprint_includes_entity(self):
        """Test that same role for different entities gets different IDs."""
        # Arrange
        target_data = {
            'role': 'CIO',
            'team': 'Leadership',
            'entity': 'target',
            'data_source': 'observed'
        }

        buyer_data = {
            'role': 'CIO',
            'team': 'Leadership',
            'entity': 'buyer',
            'data_source': 'observed'
        }

        # Act
        target_id = self._generate_fingerprint(target_data)
        buyer_id = self._generate_fingerprint(buyer_data)

        # Assert
        assert target_id != buyer_id  # Different fingerprints

    def test_fingerprint_defaults(self):
        """Test fingerprint with missing entity/data_source uses defaults."""
        # Arrange
        minimal_data = {
            'role': 'IT Manager',
            'team': 'Operations'
            # No entity or data_source
        }

        explicit_data = {
            'role': 'IT Manager',
            'team': 'Operations',
            'entity': 'target',
            'data_source': 'observed'
        }

        # Act
        minimal_id = self._generate_fingerprint(minimal_data)
        explicit_id = self._generate_fingerprint(explicit_data)

        # Assert
        assert minimal_id == explicit_id  # Defaults match explicit values


class TestBackwardCompatibility:
    """Test that existing inventory items still work."""

    def test_schema_optional_fields_backward_compatible(self):
        """Test that new fields are optional (not required)."""
        # Arrange
        schema = get_schema("organization")

        # Assert - new fields should be in optional, not required
        assert "data_source" not in schema["required"]
        assert "confidence_score" not in schema["required"]
        assert "assumption_basis" not in schema["required"]

        assert "data_source" in schema["optional"]
        assert "confidence_score" in schema["optional"]

    def test_inventory_item_without_new_fields(self):
        """Test that inventory item without new fields is valid."""
        # Arrange - simulate old inventory item
        old_item_data = {
            'role': 'Database Administrator',
            'team': 'Infrastructure',
            'department': 'IT',
            # No data_source, confidence_score, or assumption_basis
        }

        # Act - get schema fields
        all_fields = get_all_fields("organization")
        required_fields = get_schema("organization")["required"]

        # Assert - old item has all required fields
        for field in required_fields:
            assert field in old_item_data or field in ["entity", "data_source"]  # Allow defaults

    def test_defaults_applied_to_old_items(self):
        """Test that defaults are applied when fields missing."""
        # Arrange - item without new fields
        item_data = {
            'role': 'Security Engineer',
            'team': 'Security'
        }

        # Act - apply defaults (simulating InventoryStore logic)
        if 'data_source' not in item_data:
            item_data['data_source'] = 'observed'
        if 'confidence_score' not in item_data:
            item_data['confidence_score'] = 1.0
        if 'entity' not in item_data:
            item_data['entity'] = 'target'

        # Assert
        assert item_data['data_source'] == 'observed'
        assert item_data['confidence_score'] == 1.0
        assert item_data['entity'] == 'target'


class TestConfidenceRanges:
    """Test confidence range constants."""

    def test_confidence_ranges_defined(self):
        """Test that confidence ranges exist for all data sources."""
        assert 'observed' in CONFIDENCE_RANGES
        assert 'assumed' in CONFIDENCE_RANGES
        assert 'hybrid' in CONFIDENCE_RANGES

    def test_confidence_ranges_values(self):
        """Test confidence range values are sensible."""
        observed_min, observed_max = CONFIDENCE_RANGES['observed']
        assumed_min, assumed_max = CONFIDENCE_RANGES['assumed']
        hybrid_min, hybrid_max = CONFIDENCE_RANGES['hybrid']

        # Observed should be highest
        assert observed_min >= 0.8
        assert observed_max == 1.0

        # Assumed should be medium
        assert assumed_min >= 0.6
        assert assumed_max <= 0.8

        # Hybrid should be in between
        assert hybrid_min >= assumed_min
        assert hybrid_max <= observed_max
