"""
Test Cost Engine Deal Type Awareness

Tests deal type multipliers and TSA cost calculations for carveout deals.
Based on spec: specs/deal-type-awareness/04-cost-engine-deal-awareness.md
"""

import pytest
from services.cost_engine.calculator import calculate_cost, calculate_deal_costs
from services.cost_engine.models import (
    get_deal_type_multiplier,
    DEAL_TYPE_MULTIPLIERS,
    WorkItemType,
    COST_MODELS,
)
from services.cost_engine.drivers import DealDrivers, TSACostDriver, OwnershipType
from stores.inventory_store import InventoryStore


class TestDealTypeMultipliers:
    """Test deal type multipliers are applied correctly."""

    def test_acquisition_baseline(self):
        """Acquisition should use 1.0 multipliers (baseline)."""
        multiplier = get_deal_type_multiplier('acquisition', 'identity')
        assert multiplier == 1.0

    def test_carveout_identity_higher(self):
        """Carve-out identity work should cost 2.5x more."""
        multiplier = get_deal_type_multiplier('carveout', 'identity')
        assert multiplier == 2.5

    def test_carveout_application_higher(self):
        """Carve-out application work should cost 1.8x more."""
        multiplier = get_deal_type_multiplier('carveout', 'application')
        assert multiplier == 1.8

    def test_divestiture_highest(self):
        """Divestiture should have highest multipliers."""
        acq_mult = get_deal_type_multiplier('acquisition', 'identity')
        carve_mult = get_deal_type_multiplier('carveout', 'identity')
        div_mult = get_deal_type_multiplier('divestiture', 'identity')

        assert div_mult > carve_mult > acq_mult
        assert div_mult == 3.0

    def test_all_deal_types_defined(self):
        """All three deal types should be defined."""
        assert 'acquisition' in DEAL_TYPE_MULTIPLIERS
        assert 'carveout' in DEAL_TYPE_MULTIPLIERS
        assert 'divestiture' in DEAL_TYPE_MULTIPLIERS

    def test_all_categories_defined(self):
        """All six categories should be defined for each deal type."""
        expected_categories = [
            'identity_separation',
            'application_migration',
            'infrastructure_consolidation',
            'network_integration',
            'cybersecurity_harmonization',
            'org_restructuring'
        ]

        for deal_type in ['acquisition', 'carveout', 'divestiture']:
            multipliers = DEAL_TYPE_MULTIPLIERS[deal_type]
            for category in expected_categories:
                assert category in multipliers, f"{category} missing for {deal_type}"

    def test_invalid_deal_type_raises_error(self):
        """Invalid deal type should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid deal_type"):
            get_deal_type_multiplier('invalid_type', 'identity')

    def test_category_mapping(self):
        """Category aliases should map correctly."""
        # Test singular vs plural
        assert get_deal_type_multiplier('acquisition', 'application') == 1.0
        assert get_deal_type_multiplier('acquisition', 'applications') == 1.0

        # Test org vs organization
        assert get_deal_type_multiplier('acquisition', 'org') == 1.0
        assert get_deal_type_multiplier('acquisition', 'organization') == 1.0


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

        # Assert
        assert carve_cost.one_time_base > acq_cost.one_time_base
        assert div_cost.one_time_base > carve_cost.one_time_base

        # Carveout should be at least 2.0x acquisition (2.5x multiplier * 0.85 scenario = 2.125x min)
        ratio_carve_acq = carve_cost.one_time_base / acq_cost.one_time_base
        assert ratio_carve_acq >= 2.0, f"Carveout should be at least 2x acquisition, got {ratio_carve_acq:.2f}x"

        # Divestiture should be at least 2.5x acquisition (3.0x multiplier)
        ratio_div_acq = div_cost.one_time_base / acq_cost.one_time_base
        assert ratio_div_acq >= 2.5, f"Divestiture should be at least 2.5x acquisition, got {ratio_div_acq:.2f}x"

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
        assert len(deal_assumptions) > 0

    def test_acquisition_no_deal_type_assumption(self):
        """Acquisition (baseline) should not mention deal type in assumptions."""
        model = COST_MODELS[WorkItemType.IDENTITY_SEPARATION]
        drivers = DealDrivers(entity="target", total_users=1000)

        acq_cost = calculate_cost(model, drivers, deal_type='acquisition')

        # Should not have deal type assumption for baseline
        deal_assumptions = [a for a in acq_cost.assumptions if 'acquisition' in a.lower()]
        # Empty or only mentions acquisition in other context (not as multiplier)
        multiplier_assumptions = [a for a in deal_assumptions if 'multiplier' in a.lower()]
        assert len(multiplier_assumptions) == 0


class TestTSACostDriver:
    """Test TSA cost calculations for carveout deals."""

    def test_tsa_cost_calculation(self):
        """TSA costs should be calculated based on shared services."""
        # Arrange
        inv_store = InventoryStore(deal_id="test-carveout")
        tsa_driver = TSACostDriver()

        # Act
        tsa_cost = tsa_driver.estimate_monthly_tsa_cost(inv_store, tsa_duration_months=12)

        # Assert
        assert tsa_cost > 0
        # Should be at least floor (50K/month * 12 = 600K)
        assert tsa_cost >= 600_000

    def test_tsa_cost_floor(self):
        """TSA costs should have minimum floor of $50K/month."""
        inv_store = InventoryStore(deal_id="test-small")
        tsa_driver = TSACostDriver()

        # Even with no shared services, should hit floor
        tsa_cost = tsa_driver.estimate_monthly_tsa_cost(inv_store, tsa_duration_months=6)

        assert tsa_cost >= 300_000  # 50K * 6 months

    def test_tsa_cost_ceiling(self):
        """TSA costs should have maximum ceiling of $500K/month."""
        inv_store = InventoryStore(deal_id="test-large")
        tsa_driver = TSACostDriver()

        # Even with many services, should cap at ceiling
        tsa_cost = tsa_driver.estimate_monthly_tsa_cost(inv_store, tsa_duration_months=12)

        assert tsa_cost <= 6_000_000  # 500K * 12 months


class TestDealCostSummaryWithDealType:
    """Test deal-level cost summary respects deal type."""

    def test_deal_costs_vary_by_type(self):
        """Same drivers should yield different costs by deal type."""
        drivers = DealDrivers(
            entity="target",
            total_users=1000,
            sites=3,
            endpoints=1200,
            identity_owned_by=OwnershipType.PARENT
        )

        acq_summary = calculate_deal_costs("test-acq", drivers, deal_type='acquisition')
        carve_summary = calculate_deal_costs("test-carve", drivers, deal_type='carveout')

        # Carveout should cost more
        assert carve_summary.total_one_time_base > acq_summary.total_one_time_base

    def test_tsa_costs_only_for_carveout(self):
        """TSA costs should only appear for carve-out deals with inventory."""
        drivers = DealDrivers(entity="target", total_users=1000)
        inv_store = InventoryStore(deal_id="test")

        acq_summary = calculate_deal_costs("test-acq", drivers, deal_type='acquisition', inventory_store=inv_store)
        carve_summary = calculate_deal_costs("test-carve", drivers, deal_type='carveout', inventory_store=inv_store)

        assert acq_summary.total_tsa_costs == 0
        assert carve_summary.total_tsa_costs > 0

    def test_carveout_without_inventory_no_tsa(self):
        """Carveout without inventory_store should not calculate TSA costs."""
        drivers = DealDrivers(entity="target", total_users=1000)

        carve_summary = calculate_deal_costs("test-carve", drivers, deal_type='carveout')

        # Should log warning but not crash
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

    def test_calculate_deal_costs_default(self):
        """calculate_deal_costs should default to acquisition."""
        drivers = DealDrivers(entity="target", total_users=1000)

        summary1 = calculate_deal_costs("test", drivers)
        summary2 = calculate_deal_costs("test", drivers, deal_type='acquisition')

        assert summary1.total_one_time_base == summary2.total_one_time_base


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
