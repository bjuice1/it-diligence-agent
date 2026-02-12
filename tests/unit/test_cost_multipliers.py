"""
Unit tests for deal type cost multipliers.

Tests that cost multipliers are applied correctly:
- Acquisition = 1.0x baseline
- Carve-out = 1.5-3.0x
- Divestiture = 2.0-3.5x

Based on spec: specs/deal-type-awareness/06-testing-validation.md
"""

import pytest
from services.cost_engine.calculator import calculate_cost, calculate_deal_costs
from services.cost_engine.models import (
    get_deal_type_multiplier,
    DEAL_TYPE_MULTIPLIERS,
    WorkItemType,
    COST_MODELS
)
from services.cost_engine.drivers import DealDrivers, OwnershipType
from stores.inventory_store import InventoryStore


class TestDealTypeMultipliers:
    """Test cost multiplier logic."""

    def test_acquisition_baseline_multipliers(self):
        """Test that acquisition uses 1.0 multipliers (baseline)."""
        categories = ['identity', 'application', 'infrastructure', 'network', 'cybersecurity', 'org']

        for category in categories:
            multiplier = get_deal_type_multiplier('acquisition', category)
            assert multiplier == 1.0, f"{category} should be 1.0 for acquisition, got {multiplier}"

    def test_carveout_higher_than_acquisition(self):
        """Test that carve-out multipliers are higher than acquisition."""
        categories = ['identity', 'application', 'infrastructure', 'network', 'cybersecurity', 'org']

        for category in categories:
            acq_mult = get_deal_type_multiplier('acquisition', category)
            carve_mult = get_deal_type_multiplier('carveout', category)

            assert carve_mult > acq_mult, \
                f"{category}: carveout ({carve_mult}) should be > acquisition ({acq_mult})"
            assert carve_mult >= 1.5, \
                f"{category}: carveout multiplier should be at least 1.5x, got {carve_mult}"

    def test_divestiture_highest_multipliers(self):
        """Test that divestiture has highest multipliers."""
        categories = ['identity', 'application', 'infrastructure', 'network', 'cybersecurity', 'org']

        for category in categories:
            acq_mult = get_deal_type_multiplier('acquisition', category)
            carve_mult = get_deal_type_multiplier('carveout', category)
            div_mult = get_deal_type_multiplier('divestiture', category)

            assert div_mult >= carve_mult >= acq_mult, \
                f"{category}: divestiture >= carveout >= acquisition failed. " \
                f"Got {div_mult} >= {carve_mult} >= {acq_mult}"

    def test_specific_carveout_multipliers(self):
        """Test specific carve-out multiplier values."""
        # Based on spec values
        assert get_deal_type_multiplier('carveout', 'identity') == 2.5
        assert get_deal_type_multiplier('carveout', 'application') == 1.8

    def test_specific_divestiture_multipliers(self):
        """Test specific divestiture multiplier values."""
        # Based on spec values
        assert get_deal_type_multiplier('divestiture', 'identity') == 3.0

    def test_invalid_deal_type_raises_error(self):
        """Test that invalid deal type raises ValueError."""
        with pytest.raises(ValueError, match="Invalid deal_type"):
            get_deal_type_multiplier('merger', 'identity')

    def test_invalid_category_raises_error(self):
        """Test that invalid category raises ValueError."""
        with pytest.raises(ValueError, match="Invalid category"):
            get_deal_type_multiplier('acquisition', 'invalid_category')

    def test_category_aliases(self):
        """Test that category aliases work correctly."""
        # Test singular vs plural
        assert get_deal_type_multiplier('acquisition', 'application') == \
               get_deal_type_multiplier('acquisition', 'applications')

        assert get_deal_type_multiplier('acquisition', 'infrastructure') == \
               get_deal_type_multiplier('acquisition', 'infrastructures')

        # Test org vs organization
        assert get_deal_type_multiplier('acquisition', 'org') == \
               get_deal_type_multiplier('acquisition', 'organization')


class TestCostCalculationByDealType:
    """Test end-to-end cost calculation respects deal type."""

    def test_same_work_item_different_costs_by_deal_type(self):
        """Same work items should yield different costs for different deal types."""
        # Arrange
        model = COST_MODELS[WorkItemType.IDENTITY_SEPARATION]
        drivers = DealDrivers(
            entity="target",
            total_users=1000,
            sites=5,
            endpoints=1200
        )

        # Act
        acq_cost = calculate_cost(model, drivers, deal_type='acquisition')
        carve_cost = calculate_cost(model, drivers, deal_type='carveout')
        div_cost = calculate_cost(model, drivers, deal_type='divestiture')

        # Assert - costs should increase
        assert carve_cost.one_time_base > acq_cost.one_time_base, \
            f"Carveout ({carve_cost.one_time_base}) should be > acquisition ({acq_cost.one_time_base})"
        assert div_cost.one_time_base > carve_cost.one_time_base, \
            f"Divestiture ({div_cost.one_time_base}) should be > carveout ({carve_cost.one_time_base})"

        # Carveout should be at least 2.0x acquisition (2.5x multiplier accounting for other factors)
        ratio_carve_acq = carve_cost.one_time_base / acq_cost.one_time_base
        assert ratio_carve_acq >= 2.0, \
            f"Carveout should be at least 2x acquisition, got {ratio_carve_acq:.2f}x"

        # Divestiture should be at least 2.5x acquisition (3.0x multiplier)
        ratio_div_acq = div_cost.one_time_base / acq_cost.one_time_base
        assert ratio_div_acq >= 2.5, \
            f"Divestiture should be at least 2.5x acquisition, got {ratio_div_acq:.2f}x"

    def test_application_migration_costs_by_deal_type(self):
        """Test application migration costs vary by deal type."""
        model = COST_MODELS[WorkItemType.APPLICATION_MIGRATION]
        drivers = DealDrivers(
            entity="target",
            applications=50,
            total_users=800
        )

        acq_cost = calculate_cost(model, drivers, deal_type='acquisition')
        carve_cost = calculate_cost(model, drivers, deal_type='carveout')
        div_cost = calculate_cost(model, drivers, deal_type='divestiture')

        # Verify increasing costs
        assert div_cost.one_time_base > carve_cost.one_time_base > acq_cost.one_time_base

    def test_cost_breakdown_includes_deal_multiplier(self):
        """Cost breakdown should include deal type multiplier."""
        model = COST_MODELS[WorkItemType.IDENTITY_SEPARATION]
        drivers = DealDrivers(entity="target", total_users=1000)

        carve_cost = calculate_cost(model, drivers, deal_type='carveout')

        assert 'deal_type_multiplier' in carve_cost.cost_breakdown
        assert carve_cost.cost_breakdown['deal_type_multiplier'] == 2.5

    def test_assumptions_include_deal_type(self):
        """Assumptions should mention deal type if not acquisition."""
        model = COST_MODELS[WorkItemType.IDENTITY_SEPARATION]
        drivers = DealDrivers(entity="target", total_users=1000)

        carve_cost = calculate_cost(model, drivers, deal_type='carveout')

        # Should have an assumption about deal type
        deal_assumptions = [a for a in carve_cost.assumptions if 'carveout' in a.lower()]
        assert len(deal_assumptions) > 0, "Should have carveout-specific assumptions"

    def test_acquisition_no_deal_type_assumption(self):
        """Acquisition (baseline) should not mention deal type multiplier in assumptions."""
        model = COST_MODELS[WorkItemType.IDENTITY_SEPARATION]
        drivers = DealDrivers(entity="target", total_users=1000)

        acq_cost = calculate_cost(model, drivers, deal_type='acquisition')

        # Should not have deal type multiplier assumption for baseline
        multiplier_assumptions = [a for a in acq_cost.assumptions if 'multiplier' in a.lower() and 'deal' in a.lower()]
        assert len(multiplier_assumptions) == 0, \
            "Acquisition should not mention deal type multipliers"


class TestDealCostSummaryWithDealType:
    """Test deal-level cost summary respects deal type."""

    def test_deal_costs_vary_by_type(self):
        """Same drivers should yield different costs by deal type."""
        drivers = DealDrivers(
            entity="target",
            total_users=1000,
            sites=3,
            endpoints=1200,
            identity_owned_by=OwnershipType.TARGET
        )

        acq_summary = calculate_deal_costs("test-acq", drivers, deal_type='acquisition')
        carve_summary = calculate_deal_costs("test-carve", drivers, deal_type='carveout')
        div_summary = calculate_deal_costs("test-div", drivers, deal_type='divestiture')

        # Costs should increase
        assert carve_summary.total_one_time_base > acq_summary.total_one_time_base
        assert div_summary.total_one_time_base > carve_summary.total_one_time_base

    def test_tsa_costs_only_for_carveout(self):
        """TSA costs should only appear for carve-out deals with inventory."""
        drivers = DealDrivers(entity="target", total_users=1000)
        inv_store = InventoryStore(deal_id="test-tsa")

        # Add some shared services to trigger TSA calculation
        inv_store.add_item('applications', {
            'name': 'Shared ERP',
            'entity': 'target',
            'hosted_by_parent': True
        })

        acq_summary = calculate_deal_costs(
            "test-acq",
            drivers,
            deal_type='acquisition',
            inventory_store=inv_store
        )
        carve_summary = calculate_deal_costs(
            "test-carve",
            drivers,
            deal_type='carveout',
            inventory_store=inv_store
        )

        assert acq_summary.total_tsa_costs == 0, "Acquisition should have no TSA costs"
        assert carve_summary.total_tsa_costs > 0, "Carveout should have TSA costs"

    def test_carveout_without_inventory_no_tsa(self):
        """Carveout without inventory_store should not calculate TSA costs."""
        drivers = DealDrivers(entity="target", total_users=1000)

        carve_summary = calculate_deal_costs("test-carve-no-inv", drivers, deal_type='carveout')

        # Should not crash, TSA costs should be 0
        assert carve_summary.total_tsa_costs == 0


class TestBackwardCompatibility:
    """Test backward compatibility with existing code."""

    def test_default_deal_type_is_acquisition(self):
        """Functions should default to acquisition if deal_type not specified."""
        model = COST_MODELS[WorkItemType.IDENTITY_SEPARATION]
        drivers = DealDrivers(entity="target", total_users=1000)

        # Call without deal_type parameter
        cost1 = calculate_cost(model, drivers)
        cost2 = calculate_cost(model, drivers, deal_type='acquisition')

        # Should be identical
        assert cost1.one_time_base == cost2.one_time_base
        assert cost1.total_cost == cost2.total_cost

    def test_calculate_deal_costs_default(self):
        """calculate_deal_costs should default to acquisition."""
        drivers = DealDrivers(entity="target", total_users=1000)

        summary1 = calculate_deal_costs("test-default", drivers)
        summary2 = calculate_deal_costs("test-acq", drivers, deal_type='acquisition')

        assert summary1.total_one_time_base == summary2.total_one_time_base

    def test_multiplier_dict_structure(self):
        """Test that DEAL_TYPE_MULTIPLIERS has correct structure."""
        assert isinstance(DEAL_TYPE_MULTIPLIERS, dict)

        # Check all 3 deal types exist
        assert 'acquisition' in DEAL_TYPE_MULTIPLIERS
        assert 'carveout' in DEAL_TYPE_MULTIPLIERS
        assert 'divestiture' in DEAL_TYPE_MULTIPLIERS

        # Check each deal type has all categories
        expected_categories = [
            'identity_separation',
            'application_migration',
            'infrastructure_consolidation',
            'network_integration',
            'cybersecurity_harmonization',
            'org_restructuring'
        ]

        for deal_type in ['acquisition', 'carveout', 'divestiture']:
            for category in expected_categories:
                assert category in DEAL_TYPE_MULTIPLIERS[deal_type], \
                    f"{category} missing from {deal_type}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
