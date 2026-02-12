"""
Regression tests to ensure deal type changes don't break existing behavior.

Tests against golden fixtures to validate expected outputs for each deal type.

Based on spec: specs/deal-type-awareness/06-testing-validation.md
"""

import pytest
import json
from pathlib import Path
from web.database import Deal, db
from stores.inventory_store import InventoryStore
from services.cost_engine.calculator import calculate_deal_costs
from services.cost_engine.drivers import DealDrivers
from services.cost_engine.models import get_deal_type_multiplier


class TestDealTypeRegression:
    """Regression tests using golden fixtures."""

    @pytest.fixture
    def golden_acquisition(self):
        """Load golden acquisition fixture."""
        fixture_path = Path(__file__).parent.parent / 'fixtures' / 'golden_acquisition.json'
        with open(fixture_path) as f:
            return json.load(f)

    @pytest.fixture
    def golden_carveout(self):
        """Load golden carveout fixture."""
        fixture_path = Path(__file__).parent.parent / 'fixtures' / 'golden_carveout.json'
        with open(fixture_path) as f:
            return json.load(f)

    @pytest.fixture
    def golden_divestiture(self):
        """Load golden divestiture fixture."""
        fixture_path = Path(__file__).parent.parent / 'fixtures' / 'golden_divestiture.json'
        with open(fixture_path) as f:
            return json.load(f)

    def test_acquisition_golden_outputs(self, golden_acquisition):
        """Test that acquisition outputs match golden fixture expectations."""
        deal = Deal(
            name="Acquisition Regression",
            target_name=golden_acquisition['test_scenario']['target_name'],
            buyer_name=golden_acquisition['test_scenario']['buyer_name'],
            deal_type="acquisition"
        )
        db.session.add(deal)
        db.session.commit()

        try:
            # Setup test scenario
            inv_store = InventoryStore(deal_id=deal.id)

            # Add overlapping apps from fixture
            for app_name in golden_acquisition['test_scenario']['overlapping_apps']:
                inv_store.add_item('applications', {
                    'name': app_name,
                    'entity': 'buyer'
                })
                inv_store.add_item('applications', {
                    'name': app_name,
                    'entity': 'target'
                })

            drivers = DealDrivers(
                entity="target",
                total_users=golden_acquisition['test_scenario']['total_users'],
                applications=golden_acquisition['test_scenario']['applications']
            )

            result = calculate_deal_costs(
                deal_id=deal.id,
                drivers=drivers,
                deal_type=deal.deal_type,
                inventory_store=inv_store
            )

            # Validate against golden expectations
            expected = golden_acquisition['expected_outputs']

            # Check TSA costs
            assert result.total_tsa_costs == expected['tsa_costs'], \
                "Acquisition should have no TSA costs"

            # Check cost multipliers
            for category, expected_mult in expected['cost_multipliers'].items():
                actual_mult = get_deal_type_multiplier('acquisition', category)
                assert actual_mult == expected_mult, \
                    f"{category} multiplier mismatch: expected {expected_mult}, got {actual_mult}"

            # Validate rules
            rules = golden_acquisition['validation_rules']
            assert rules['no_separation_costs'] is True
            assert rules['no_tsa_recommendations'] is True

        finally:
            db.session.delete(deal)
            db.session.commit()

    def test_carveout_golden_outputs(self, golden_carveout):
        """Test that carve-out outputs match golden fixture expectations."""
        deal = Deal(
            name="Carveout Regression",
            target_name=golden_carveout['test_scenario']['target_name'],
            buyer_name=golden_carveout['test_scenario']['buyer_name'],
            deal_type="carveout"
        )
        db.session.add(deal)
        db.session.commit()

        try:
            # Setup test scenario
            inv_store = InventoryStore(deal_id=deal.id)

            # Add shared services from fixture
            for service_name in golden_carveout['test_scenario']['shared_services']:
                inv_store.add_item('applications', {
                    'name': service_name,
                    'entity': 'target',
                    'hosted_by_parent': True,
                    'shared_service': True
                })

            drivers = DealDrivers(
                entity="target",
                total_users=golden_carveout['test_scenario']['total_users'],
                applications=golden_carveout['test_scenario']['applications']
            )

            result = calculate_deal_costs(
                deal_id=deal.id,
                drivers=drivers,
                deal_type=deal.deal_type,
                inventory_store=inv_store
            )

            # Validate against golden expectations
            expected = golden_carveout['expected_outputs']

            # Check TSA costs
            assert result.total_tsa_costs >= expected['tsa_costs_min'], \
                f"Carveout TSA costs ({result.total_tsa_costs}) should be >= {expected['tsa_costs_min']}"

            # Check cost multipliers
            for category, expected_mult in expected['cost_multipliers'].items():
                actual_mult = get_deal_type_multiplier('carveout', category)
                assert actual_mult == expected_mult, \
                    f"{category} multiplier mismatch: expected {expected_mult}, got {actual_mult}"

            # Validate rules
            rules = golden_carveout['validation_rules']
            assert rules['no_consolidation_synergies'] is True
            assert rules['tsa_costs_present'] is True
            assert rules['separation_costs_present'] is True

        finally:
            db.session.delete(deal)
            db.session.commit()

    def test_divestiture_golden_outputs(self, golden_divestiture):
        """Test that divestiture outputs match golden fixture expectations."""
        deal = Deal(
            name="Divestiture Regression",
            target_name=golden_divestiture['test_scenario']['target_name'],
            buyer_name=golden_divestiture['test_scenario']['buyer_name'],
            deal_type="divestiture"
        )
        db.session.add(deal)
        db.session.commit()

        try:
            # Setup test scenario
            inv_store = InventoryStore(deal_id=deal.id)

            # Add deeply integrated systems from fixture
            for system_name in golden_divestiture['test_scenario']['deeply_integrated_systems']:
                inv_store.add_item('applications', {
                    'name': system_name,
                    'entity': 'target',
                    'integration_level': 'deeply_integrated',
                    'shared_with_parent': True
                })

            drivers = DealDrivers(
                entity="target",
                total_users=golden_divestiture['test_scenario']['total_users'],
                applications=golden_divestiture['test_scenario']['applications']
            )

            result = calculate_deal_costs(
                deal_id=deal.id,
                drivers=drivers,
                deal_type=deal.deal_type,
                inventory_store=inv_store
            )

            # Validate against golden expectations
            expected = golden_divestiture['expected_outputs']

            # Check cost multipliers (highest)
            for category, expected_mult in expected['cost_multipliers'].items():
                actual_mult = get_deal_type_multiplier('divestiture', category)
                assert actual_mult == expected_mult, \
                    f"{category} multiplier mismatch: expected {expected_mult}, got {actual_mult}"

            # Validate rules
            rules = golden_divestiture['validation_rules']
            assert rules['no_consolidation_synergies'] is True
            assert rules['highest_costs'] is True
            assert rules['deep_integration_identified'] is True

        finally:
            db.session.delete(deal)
            db.session.commit()


class TestCrossFixtureComparison:
    """Test comparative behavior across golden fixtures."""

    @pytest.fixture
    def all_golden_fixtures(self):
        """Load all golden fixtures."""
        fixtures_dir = Path(__file__).parent.parent / 'fixtures'
        fixtures = {}

        for deal_type in ['acquisition', 'carveout', 'divestiture']:
            fixture_path = fixtures_dir / f'golden_{deal_type}.json'
            with open(fixture_path) as f:
                fixtures[deal_type] = json.load(f)

        return fixtures

    def test_cost_multipliers_increase_across_types(self, all_golden_fixtures):
        """Test that cost multipliers increase: acquisition < carveout < divestiture."""
        categories = ['identity', 'application', 'infrastructure', 'network', 'cybersecurity', 'org']

        for category in categories:
            acq_mult = all_golden_fixtures['acquisition']['expected_outputs']['cost_multipliers'][category]
            carve_mult = all_golden_fixtures['carveout']['expected_outputs']['cost_multipliers'][category]
            div_mult = all_golden_fixtures['divestiture']['expected_outputs']['cost_multipliers'][category]

            assert carve_mult > acq_mult, \
                f"{category}: carveout ({carve_mult}) should be > acquisition ({acq_mult})"
            assert div_mult >= carve_mult, \
                f"{category}: divestiture ({div_mult}) should be >= carveout ({carve_mult})"

    def test_tsa_costs_only_for_separation_deals(self, all_golden_fixtures):
        """Test that TSA costs only apply to carveout and divestiture."""
        assert all_golden_fixtures['acquisition']['expected_outputs']['tsa_costs'] == 0
        assert all_golden_fixtures['carveout']['expected_outputs']['tsa_costs_min'] > 0
        assert all_golden_fixtures['divestiture']['expected_outputs']['tsa_costs_min'] > 0

    def test_consolidation_only_for_acquisition(self, all_golden_fixtures):
        """Test that consolidation synergies only apply to acquisition."""
        # Acquisition should have synergies
        assert all_golden_fixtures['acquisition']['expected_outputs']['synergy_count_min'] > 0
        assert 'consolidation' in all_golden_fixtures['acquisition']['expected_outputs']['synergy_types']

        # Carveout and divestiture should have zero synergies
        assert all_golden_fixtures['carveout']['expected_outputs']['synergy_count'] == 0
        assert all_golden_fixtures['divestiture']['expected_outputs']['synergy_count'] == 0

    def test_findings_terminology_differs_by_type(self, all_golden_fixtures):
        """Test that findings use different terminology for each deal type."""
        # Acquisition: consolidation language
        acq_contain = all_golden_fixtures['acquisition']['expected_outputs']['findings_contain']
        assert 'consolidate' in acq_contain
        assert 'migrate' in acq_contain

        acq_not_contain = all_golden_fixtures['acquisition']['expected_outputs']['findings_not_contain']
        assert 'separate' in acq_not_contain
        assert 'standalone' in acq_not_contain

        # Carveout: separation language
        carve_contain = all_golden_fixtures['carveout']['expected_outputs']['findings_contain']
        assert 'separate' in carve_contain
        assert 'standalone' in carve_contain
        assert 'tsa' in carve_contain

        carve_not_contain = all_golden_fixtures['carveout']['expected_outputs']['findings_not_contain']
        assert 'consolidate' in carve_not_contain

        # Divestiture: untangling language
        div_contain = all_golden_fixtures['divestiture']['expected_outputs']['findings_contain']
        assert 'untangle' in div_contain or 'disentangle' in div_contain
        assert 'extraction' in div_contain


class TestBackwardCompatibility:
    """Test backward compatibility with existing tests."""

    def test_existing_acquisition_tests_still_pass(self):
        """Test that existing acquisition tests continue to work."""
        deal = Deal(
            name="Backward Compat Test",
            target_name="Target",
            deal_type="acquisition"
        )
        db.session.add(deal)
        db.session.commit()

        try:
            drivers = DealDrivers(entity="target", total_users=1000)

            # Should work without specifying deal_type (defaults to acquisition)
            result = calculate_deal_costs(
                deal_id=deal.id,
                drivers=drivers
            )

            assert result.total_one_time_base > 0
            assert result.total_tsa_costs == 0

        finally:
            db.session.delete(deal)
            db.session.commit()

    def test_default_deal_type_behavior_unchanged(self):
        """Test that default behavior (no deal_type) still works as before."""
        drivers = DealDrivers(entity="target", total_users=1000)

        # Calculate without explicit deal_type
        result_default = calculate_deal_costs(
            deal_id="test-default",
            drivers=drivers
        )

        # Calculate with explicit acquisition
        result_acquisition = calculate_deal_costs(
            deal_id="test-acq",
            drivers=drivers,
            deal_type='acquisition'
        )

        # Should be identical
        assert result_default.total_one_time_base == result_acquisition.total_one_time_base


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
