"""
Regression tests for cost model entity awareness.

These tests ensure backward compatibility - that existing code without entity
parameters continues to work correctly with default entity="target" behavior.
"""

import pytest
from unittest.mock import patch, Mock
from services.cost_engine.drivers import DealDrivers, extract_drivers_from_facts
from services.cost_engine.calculator import calculate_deal_costs, calculate_cost
from services.cost_engine.models import get_model, WorkItemType
from web.blueprints.costs import (
    build_cost_center_data,
    _gather_headcount_costs,
    _gather_one_time_costs,
    _assess_data_quality_per_entity
)


class TestBackwardCompatibilityDefaults:
    """Test that omitting entity parameter defaults to 'target' behavior."""

    def test_deal_drivers_default_entity(self):
        """DealDrivers without entity param defaults to 'target'."""
        # Old code: no entity parameter
        drivers = DealDrivers(total_users=500, sites=3)

        # Should default to target
        assert drivers.entity == "target"

        # to_dict() should include entity
        data = drivers.to_dict()
        assert data["entity"] == "target"

    def test_deal_drivers_serialization_backward_compatible(self):
        """DealDrivers to_dict() output remains compatible."""
        drivers = DealDrivers(
            total_users=500,
            sites=3,
            endpoints=500,
            servers=25
        )

        data = drivers.to_dict()

        # All expected fields present
        assert "total_users" in data
        assert "sites" in data
        assert "endpoints" in data
        assert "servers" in data
        assert "entity" in data  # NEW, but doesn't break existing code

        # Values match
        assert data["total_users"] == 500
        assert data["sites"] == 3
        assert data["entity"] == "target"

    def test_calculate_cost_without_entity_still_works(self):
        """calculate_cost() works without entity in drivers (defaults to target)."""
        # Old-style drivers creation (no entity)
        drivers = DealDrivers(total_users=500, sites=3, endpoints=500)

        # Old-style cost calculation
        model = get_model(WorkItemType.IDENTITY_SEPARATION.value)
        estimate = calculate_cost(model, drivers)

        # Should work and default to target
        assert estimate.entity == "target"
        assert estimate.one_time_upside >= 0
        assert estimate.one_time_base >= 0
        assert estimate.one_time_stress >= 0

    def test_calculate_deal_costs_without_entity_still_works(self):
        """calculate_deal_costs() works without entity in drivers."""
        # Old-style drivers
        drivers = DealDrivers(
            total_users=500,
            sites=3,
            endpoints=500,
            servers=25,
            vms=40
        )

        # Old-style deal cost calculation
        summary = calculate_deal_costs("regression-test", drivers)

        # Should work and default to target
        assert summary.entity == "target"
        assert summary.deal_id == "regression-test"
        assert len(summary.estimates) > 0

        # All estimates should default to target
        for estimate in summary.estimates:
            assert estimate.entity == "target"

    def test_extract_drivers_without_entity_parameter(self):
        """extract_drivers_from_facts() without entity param defaults to target."""
        # Mock facts with mixed entities
        target_fact = Mock()
        target_fact.entity = "target"
        target_fact.fact_type = "organization"
        target_fact.data = {"headcount": 100}

        buyer_fact = Mock()
        buyer_fact.entity = "buyer"
        buyer_fact.fact_type = "organization"
        buyer_fact.data = {"headcount": 200}

        facts = [target_fact, buyer_fact]

        # Old-style call (no entity parameter)
        result = extract_drivers_from_facts(facts, deal_id="test")

        # Should default to target
        assert result.drivers.entity == "target"

    @patch('web.context.load_deal_context')
    @patch('web.deal_data.get_deal_data')
    @patch('flask.session', {'current_deal_id': 'regression-001'}, create=True)
    def test_gather_headcount_without_entity_parameter(self, mock_get_data, mock_load_context):
        """_gather_headcount_costs() without entity param defaults to target."""
        # Setup mock data
        target_fact = Mock()
        target_fact.entity = "target"
        target_fact.category = "engineering"
        target_fact.details = {"headcount": 50, "total_personnel_cost": 5_000_000}

        buyer_fact = Mock()
        buyer_fact.entity = "buyer"
        buyer_fact.category = "engineering"
        buyer_fact.details = {"headcount": 100, "total_personnel_cost": 10_000_000}

        mock_data = Mock()
        mock_data.get_organization.return_value = [target_fact, buyer_fact]
        mock_get_data.return_value = mock_data

        # Old-style call (no entity parameter)
        result = _gather_headcount_costs()

        # Should default to target
        assert result.name == "headcount"
        # Should only include target data ($5M, not $15M)
        assert result.total <= 5_000_000

    @patch('web.context.load_deal_context')
    @patch('web.deal_data.get_deal_data')
    @patch('flask.session', {'current_deal_id': 'regression-002'}, create=True)
    def test_gather_one_time_without_entity_parameter(self, mock_get_data, mock_load_context):
        """_gather_one_time_costs() without entity param defaults to target."""
        # Setup mock work items
        target_wi = Mock()
        target_wi.entity = "target"
        target_wi.cost_estimate = "100k_to_500k"
        target_wi.phase = "Day_1"
        target_wi.domain = "identity"

        buyer_wi = Mock()
        buyer_wi.entity = "buyer"
        buyer_wi.cost_estimate = "500k_to_1m"
        buyer_wi.phase = "Day_1"
        buyer_wi.domain = "identity"

        mock_data = Mock()
        mock_data.get_work_items.return_value = [target_wi, buyer_wi]
        mock_get_data.return_value = mock_data

        # Old-style call (no entity parameter)
        result = _gather_one_time_costs()

        # Should default to target
        # Should only include target work item (100K-500K, not both)
        assert result.total_low >= 100_000
        assert result.total_high <= 500_000

    @patch('web.context.load_deal_context')
    @patch('web.deal_data.get_deal_data')
    @patch('flask.session', {'current_deal_id': 'regression-003'}, create=True)
    @patch('web.blueprints.inventory.get_inventory_store')
    def test_build_cost_center_without_entity_parameter(
        self,
        mock_inv_store,
        mock_get_data,
        mock_load_context
    ):
        """build_cost_center_data() without entity param defaults to target."""
        # Setup minimal mocks
        mock_data = Mock()
        mock_data.get_organization.return_value = []
        mock_data.get_work_items.return_value = []
        mock_get_data.return_value = mock_data

        mock_inv = Mock()
        mock_inv.get_items.return_value = []
        mock_inv.__len__ = lambda self: 0
        mock_inv_store.return_value = mock_inv

        # Old-style call (no entity parameter)
        result = build_cost_center_data()

        # Should work and return valid structure
        assert hasattr(result, 'run_rate')
        assert hasattr(result, 'one_time')
        assert hasattr(result, 'synergies')
        assert hasattr(result, 'data_quality')


class TestNoBreakingChanges:
    """Test that new entity feature doesn't break existing data structures."""

    def test_deal_drivers_fields_unchanged(self):
        """DealDrivers retains all original fields."""
        drivers = DealDrivers(
            total_users=500,
            it_headcount=25,
            sites=3,
            countries=2,
            endpoints=500,
            servers=30,
            vms=50,
            total_apps=40
        )

        # All original fields still accessible
        assert drivers.total_users == 500
        assert drivers.it_headcount == 25
        assert drivers.sites == 3
        assert drivers.countries == 2
        assert drivers.endpoints == 500
        assert drivers.servers == 30
        assert drivers.vms == 50
        assert drivers.total_apps == 40

        # New field added but doesn't break existing access patterns
        assert drivers.entity == "target"

    def test_cost_estimate_structure_unchanged(self):
        """CostEstimate structure retains all original fields."""
        drivers = DealDrivers(total_users=500, sites=3, endpoints=500)
        model = get_model(WorkItemType.IDENTITY_SEPARATION.value)
        estimate = calculate_cost(model, drivers)

        # All original fields present
        assert hasattr(estimate, 'work_item_type')
        assert hasattr(estimate, 'display_name')
        assert hasattr(estimate, 'tower')
        assert hasattr(estimate, 'one_time_upside')
        assert hasattr(estimate, 'one_time_base')
        assert hasattr(estimate, 'one_time_stress')
        assert hasattr(estimate, 'annual_licenses')
        assert hasattr(estimate, 'complexity')
        assert hasattr(estimate, 'assumptions')

        # New field added
        assert hasattr(estimate, 'entity')
        assert estimate.entity == "target"

    def test_deal_cost_summary_structure_unchanged(self):
        """DealCostSummary structure retains all original fields."""
        drivers = DealDrivers(total_users=500, sites=3, endpoints=500, servers=25, vms=40)
        summary = calculate_deal_costs("backward-compat-test", drivers)

        # All original fields present
        assert hasattr(summary, 'deal_id')
        assert hasattr(summary, 'total_one_time_upside')
        assert hasattr(summary, 'total_one_time_base')
        assert hasattr(summary, 'total_one_time_stress')
        assert hasattr(summary, 'total_annual_licenses')
        assert hasattr(summary, 'total_run_rate_delta')
        assert hasattr(summary, 'tower_costs')
        assert hasattr(summary, 'estimates')

        # New field added
        assert hasattr(summary, 'entity')
        assert summary.entity == "target"

    def test_cost_category_structure_unchanged(self):
        """CostCategory structure remains unchanged."""
        from web.blueprints.costs import CostCategory

        # Old-style creation
        category = CostCategory(name="test", display_name="Test", icon="📊")

        # All fields accessible
        assert category.name == "test"
        assert category.display_name == "Test"
        assert category.icon == "📊"
        assert hasattr(category, 'items')
        assert hasattr(category, 'total')

    def test_one_time_costs_structure_unchanged(self):
        """OneTimeCosts structure remains unchanged."""
        from web.blueprints.costs import OneTimeCosts

        # Old-style creation
        one_time = OneTimeCosts()

        # All fields accessible
        assert hasattr(one_time, 'total_low')
        assert hasattr(one_time, 'total_mid')
        assert hasattr(one_time, 'total_high')
        assert hasattr(one_time, 'by_phase')
        assert hasattr(one_time, 'by_category')
        assert isinstance(one_time.by_phase, dict)
        assert isinstance(one_time.by_category, dict)


class TestEntityValidationRegressions:
    """Test that entity validation doesn't break valid use cases."""

    def test_valid_entity_values_accepted(self):
        """All valid entity values work correctly."""
        # Target (default)
        target_drivers = DealDrivers(total_users=500)
        assert target_drivers.entity == "target"

        # Explicit target
        explicit_target = DealDrivers(total_users=500, entity="target")
        assert explicit_target.entity == "target"

        # Buyer
        buyer_drivers = DealDrivers(total_users=2000, entity="buyer")
        assert buyer_drivers.entity == "buyer"

        # All
        all_drivers = DealDrivers(total_users=2500, entity="all")
        assert all_drivers.entity == "all"

    def test_invalid_entity_raises_error(self):
        """Invalid entity values raise clear errors."""
        with pytest.raises(ValueError, match="entity must be one of"):
            DealDrivers(total_users=500, entity="invalid")

        with pytest.raises(ValueError, match="entity must be one of"):
            DealDrivers(total_users=500, entity="Target")  # Case-sensitive

        with pytest.raises(ValueError, match="entity must be one of"):
            DealDrivers(total_users=500, entity="")  # Empty string

    def test_extract_drivers_entity_validation(self):
        """extract_drivers_from_facts() validates entity parameter."""
        facts = []

        # Valid values work
        for entity in ["target", "buyer", "all"]:
            result = extract_drivers_from_facts(facts, deal_id="test", entity=entity)
            assert result.drivers.entity == entity

        # Invalid value raises error
        with pytest.raises(ValueError, match="Invalid entity"):
            extract_drivers_from_facts(facts, deal_id="test", entity="invalid")


class TestExistingCodePatterns:
    """Test that common existing code patterns still work."""

    def test_driver_creation_from_facts_pattern(self):
        """Common pattern: create drivers from facts."""
        # Mock facts
        facts = [
            Mock(entity="target", fact_type="organization", data={"headcount": 100}),
            Mock(entity="target", fact_type="infrastructure", data={"servers": 25})
        ]

        # Pattern: extract drivers then calculate
        result = extract_drivers_from_facts(facts, deal_id="pattern-test")
        drivers = result.drivers

        # Should work
        assert drivers.entity == "target"

        # Pattern: use drivers for cost calculation
        summary = calculate_deal_costs("pattern-test", drivers)
        assert summary.entity == "target"

    def test_cost_calculation_pipeline_pattern(self):
        """Common pattern: create drivers → calculate → analyze."""
        # Step 1: Create drivers
        drivers = DealDrivers(
            total_users=500,
            sites=3,
            endpoints=500,
            servers=25,
            vms=40
        )

        # Step 2: Calculate costs
        summary = calculate_deal_costs("pipeline-test", drivers)

        # Step 3: Analyze estimates
        identity_estimates = [
            e for e in summary.estimates
            if "identity" in e.work_item_type.lower()
        ]

        # Should all work
        assert len(summary.estimates) > 0
        assert all(e.entity == "target" for e in summary.estimates)

    def test_estimate_filtering_pattern(self):
        """Common pattern: filter estimates by tower/type."""
        drivers = DealDrivers(
            total_users=500,
            sites=3,
            endpoints=500,
            servers=25
        )
        summary = calculate_deal_costs("filter-test", drivers)

        # Pattern: group by tower
        by_tower = {}
        for estimate in summary.estimates:
            tower = estimate.tower
            if tower not in by_tower:
                by_tower[tower] = []
            by_tower[tower].append(estimate)

        # Should work - all estimates have tower
        assert len(by_tower) > 0
        for tower, estimates in by_tower.items():
            assert all(e.tower == tower for e in estimates)
            assert all(e.entity == "target" for e in estimates)  # NEW: entity consistent

    @patch('web.context.load_deal_context')
    @patch('web.deal_data.get_deal_data')
    @patch('flask.session', {'current_deal_id': 'pattern-cost-center'}, create=True)
    @patch('web.blueprints.inventory.get_inventory_store')
    def test_cost_center_data_access_pattern(
        self,
        mock_inv_store,
        mock_get_data,
        mock_load_context
    ):
        """Common pattern: build cost center data and access components."""
        # Setup minimal mocks
        mock_data = Mock()
        mock_data.get_organization.return_value = []
        mock_data.get_work_items.return_value = []
        mock_get_data.return_value = mock_data

        mock_inv = Mock()
        mock_inv.get_items.return_value = []
        mock_inv.__len__ = lambda self: 0
        mock_inv_store.return_value = mock_inv

        # Pattern: build and access
        cost_data = build_cost_center_data()

        # Pattern: access run-rate costs
        headcount_total = cost_data.run_rate.headcount.total
        apps_total = cost_data.run_rate.applications.total
        infra_total = cost_data.run_rate.infrastructure.total

        # Pattern: access one-time costs
        one_time_low = cost_data.one_time.total_low
        one_time_mid = cost_data.one_time.total_mid
        one_time_high = cost_data.one_time.total_high

        # Pattern: access synergies
        synergy_count = len(cost_data.synergies)

        # All patterns should work
        assert isinstance(headcount_total, (int, float))
        assert isinstance(apps_total, (int, float))
        assert isinstance(one_time_mid, (int, float))
        assert isinstance(synergy_count, int)


class TestQualityAssessmentRegressions:
    """Test that quality assessment doesn't break with new entity field."""

    def test_quality_assessment_basic_structure(self):
        """Quality assessment returns expected structure."""
        from web.blueprints.costs import CostCategory, RunRateCosts, OneTimeCosts

        # Create minimal cost data
        run_rate = RunRateCosts(
            headcount=CostCategory(name="headcount", display_name="Headcount", icon="👥"),
            applications=CostCategory(name="applications", display_name="Apps", icon="📱"),
            infrastructure=CostCategory(name="infrastructure", display_name="Infra", icon="🖥️"),
            vendors_msp=CostCategory(name="vendors_msp", display_name="Vendors", icon="🤝")
        )
        run_rate.headcount.total = 1_000_000

        one_time = OneTimeCosts()
        one_time.total_mid = 500_000

        # Assess quality (defaults to target)
        quality = _assess_data_quality_per_entity(run_rate, one_time, entity="target")

        # Should have all expected keys
        assert "headcount" in quality
        assert "applications" in quality
        assert "infrastructure" in quality
        assert "one_time" in quality
        assert "entity_filter" in quality

        # Each should have overall and note
        for key in ["headcount", "applications", "infrastructure", "one_time"]:
            assert "overall" in quality[key]
            assert "note" in quality[key]

    def test_quality_level_thresholds_unchanged(self):
        """Quality level thresholds work as before."""
        from web.blueprints.costs import _quality_level

        # Test unchanged threshold behavior
        assert _quality_level(0, [100, 500, 1000]) == "none"
        assert _quality_level(50, [100, 500, 1000]) == "low"
        assert _quality_level(300, [100, 500, 1000]) == "medium"
        assert _quality_level(750, [100, 500, 1000]) == "high"
        assert _quality_level(2000, [100, 500, 1000]) == "very_high"

        # Edge cases
        assert _quality_level(100, [100, 500, 1000]) == "medium"  # Exactly at threshold
        assert _quality_level(500, [100, 500, 1000]) == "high"    # Exactly at threshold
        assert _quality_level(1000, [100, 500, 1000]) == "very_high"  # Exactly at threshold
