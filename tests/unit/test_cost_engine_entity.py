"""
Unit tests for entity-aware cost engine.

Tests that entity field is properly added to dataclasses and propagates
through the cost calculation chain: drivers → estimates → summary.
"""

import pytest
from services.cost_engine.drivers import DealDrivers, DriverExtractionResult, extract_drivers_from_facts
from services.cost_engine.models import CostEstimate, WorkItemType, get_model
from services.cost_engine.calculator import DealCostSummary, calculate_cost, calculate_deal_costs


class TestEntityField:
    """Test entity field on DealDrivers, CostEstimate, and DealCostSummary."""

    def test_deal_drivers_entity_field_default(self):
        """DealDrivers has entity field with default='target'."""
        drivers = DealDrivers(total_users=500)
        assert drivers.entity == "target"

    def test_deal_drivers_entity_field_explicit(self):
        """DealDrivers entity field can be set explicitly."""
        drivers = DealDrivers(total_users=500, entity="buyer")
        assert drivers.entity == "buyer"

        drivers_all = DealDrivers(total_users=1200, entity="all")
        assert drivers_all.entity == "all"

    def test_deal_drivers_entity_validation(self):
        """DealDrivers validates entity values via __post_init__."""
        with pytest.raises(ValueError, match="entity must be one of"):
            DealDrivers(entity="invalid")

        with pytest.raises(ValueError, match="entity must be one of"):
            DealDrivers(entity="TARGET")  # Case-sensitive

    def test_deal_drivers_to_dict_includes_entity(self):
        """DealDrivers.to_dict() includes entity field."""
        drivers = DealDrivers(total_users=400, entity="buyer")
        data = drivers.to_dict()
        assert "entity" in data
        assert data["entity"] == "buyer"


class TestCostEstimateEntity:
    """Test entity field on CostEstimate."""

    def test_cost_estimate_includes_entity(self):
        """CostEstimate includes entity field."""
        model = get_model(WorkItemType.IDENTITY_SEPARATION.value)
        drivers = DealDrivers(total_users=500, sites=3, entity="buyer")

        estimate = calculate_cost(model, drivers)

        assert hasattr(estimate, "entity")
        assert estimate.entity == "buyer"

    def test_cost_estimate_to_dict_includes_entity(self):
        """CostEstimate.to_dict() includes entity field."""
        model = get_model(WorkItemType.EMAIL_MIGRATION.value)
        drivers = DealDrivers(total_users=300, entity="target")

        estimate = calculate_cost(model, drivers)
        data = estimate.to_dict()

        assert "entity" in data
        assert data["entity"] == "target"


class TestDealCostSummaryEntity:
    """Test entity field on DealCostSummary."""

    def test_deal_cost_summary_includes_entity(self):
        """DealCostSummary includes entity field."""
        drivers = DealDrivers(total_users=500, sites=2, endpoints=500, entity="target")
        summary = calculate_deal_costs("test-deal-001", drivers)

        assert hasattr(summary, "entity")
        assert summary.entity == "target"

    def test_deal_cost_summary_to_dict_includes_entity(self):
        """DealCostSummary.to_dict() includes entity field."""
        drivers = DealDrivers(total_users=400, sites=3, entity="buyer")
        summary = calculate_deal_costs("test-deal-002", drivers)

        data = summary.to_dict()
        assert "entity" in data
        assert data["entity"] == "buyer"


class TestEntityPropagation:
    """Test that entity propagates through the cost calculation chain."""

    def test_entity_propagates_from_drivers_to_estimates(self):
        """Entity propagates from drivers → estimates."""
        drivers = DealDrivers(
            total_users=400,
            sites=2,
            endpoints=400,
            entity="buyer"
        )

        # Get a single estimate
        model = get_model(WorkItemType.IDENTITY_SEPARATION.value)
        estimate = calculate_cost(model, drivers)

        # Estimate should have buyer entity
        assert estimate.entity == "buyer"

    def test_entity_propagates_through_full_calculation(self):
        """Entity propagates from drivers → estimates → summary."""
        drivers = DealDrivers(
            total_users=600,
            sites=4,
            endpoints=600,
            servers=20,
            vms=30,
            entity="buyer"
        )

        summary = calculate_deal_costs("test-deal-003", drivers)

        # Summary has buyer entity
        assert summary.entity == "buyer"

        # All estimates have buyer entity
        assert len(summary.estimates) > 0, "Should have at least one estimate"
        for estimate in summary.estimates:
            assert estimate.entity == "buyer", f"Estimate {estimate.work_item_type} should have buyer entity"

    def test_default_entity_target_propagates(self):
        """Default entity='target' propagates through calculations."""
        drivers = DealDrivers(
            total_users=300,
            sites=2,
            endpoints=300
            # entity defaults to "target"
        )

        summary = calculate_deal_costs("test-deal-004", drivers)

        # Summary defaults to target
        assert summary.entity == "target"

        # All estimates default to target
        for estimate in summary.estimates:
            assert estimate.entity == "target"


class TestExtractDriversEntityFiltering:
    """Test entity filtering in extract_drivers_from_facts()."""

    def test_extract_drivers_accepts_entity_parameter(self):
        """extract_drivers_from_facts() accepts entity parameter."""
        # Create mock fact objects
        facts = []

        # Should not raise
        result = extract_drivers_from_facts(facts, deal_id="test", entity="target")
        assert result.drivers.entity == "target"

        result = extract_drivers_from_facts(facts, deal_id="test", entity="buyer")
        assert result.drivers.entity == "buyer"

        result = extract_drivers_from_facts(facts, deal_id="test", entity="all")
        assert result.drivers.entity == "all"

    def test_extract_drivers_entity_validation(self):
        """extract_drivers_from_facts() validates entity parameter."""
        facts = []

        with pytest.raises(ValueError, match="Invalid entity"):
            extract_drivers_from_facts(facts, deal_id="test", entity="invalid")

    def test_extract_drivers_default_entity_target(self):
        """extract_drivers_from_facts() defaults to entity='target'."""
        facts = []
        result = extract_drivers_from_facts(facts, deal_id="test")  # No entity param
        assert result.drivers.entity == "target"
