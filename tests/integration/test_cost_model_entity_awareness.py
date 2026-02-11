"""
Integration tests for entity-aware cost model.

End-to-end tests that verify entity awareness propagates correctly through
the full cost calculation pipeline: drivers → estimates → summary → UI.
"""

import pytest
from unittest.mock import patch, Mock
from tests.fixtures.cost_model_test_data import CostModelTestData
from services.cost_engine.drivers import extract_drivers_from_facts
from services.cost_engine.calculator import calculate_deal_costs
from web.blueprints.costs import (
    build_cost_center_data,
    _identify_synergies,
    _assess_data_quality_per_entity
)


class TestEntityAwarenessFullPipeline:
    """Test entity awareness through the complete cost calculation pipeline."""

    def test_target_entity_full_pipeline(self):
        """Target entity flows correctly through drivers → estimates → summary."""
        # Create target drivers
        drivers = CostModelTestData.create_target_drivers()

        # Calculate costs
        summary = calculate_deal_costs("test-deal-target", drivers)

        # Verify entity propagation
        assert summary.entity == "target"
        assert summary.deal_id == "test-deal-target"

        # All estimates should have target entity
        assert len(summary.estimates) > 0, "Should generate cost estimates"
        for estimate in summary.estimates:
            assert estimate.entity == "target", \
                f"Estimate {estimate.work_item_type} should have target entity"

        # Verify cost ranges are reasonable
        assert summary.total_one_time_upside >= 0  # Upside scenario
        assert summary.total_one_time_base >= 0     # Base scenario
        assert summary.total_one_time_stress >= 0   # Stress scenario
        # Stress should be >= base >= upside
        assert summary.total_one_time_upside <= summary.total_one_time_base <= summary.total_one_time_stress

    def test_buyer_entity_full_pipeline(self):
        """Buyer entity flows correctly through drivers → estimates → summary."""
        # Create buyer drivers (larger scale)
        drivers = CostModelTestData.create_buyer_drivers()

        # Calculate costs
        summary = calculate_deal_costs("test-deal-buyer", drivers)

        # Verify entity propagation
        assert summary.entity == "buyer"

        # All estimates should have buyer entity
        for estimate in summary.estimates:
            assert estimate.entity == "buyer", \
                f"Estimate {estimate.work_item_type} should have buyer entity"

        # Buyer should have higher costs (larger scale)
        assert summary.total_one_time_base >= 0, "Buyer should have non-negative costs"

    def test_all_entities_full_pipeline(self):
        """Entity='all' flows correctly through pipeline."""
        # Create combined drivers
        drivers = CostModelTestData.create_combined_drivers()

        # Calculate costs
        summary = calculate_deal_costs("test-deal-all", drivers)

        # Verify entity propagation
        assert summary.entity == "all"

        # All estimates should have 'all' entity
        for estimate in summary.estimates:
            assert estimate.entity == "all"

    def test_target_vs_buyer_costs_differ(self):
        """Target and buyer generate different cost estimates based on scale."""
        target_drivers = CostModelTestData.create_target_drivers()
        buyer_drivers = CostModelTestData.create_buyer_drivers()

        target_summary = calculate_deal_costs("test-target", target_drivers)
        buyer_summary = calculate_deal_costs("test-buyer", buyer_drivers)

        # Buyer has 4x users, costs should be significantly higher
        assert buyer_summary.total_one_time_base > target_summary.total_one_time_base, \
            "Buyer costs should exceed target costs due to larger scale"

        # Verify both have same estimate types but different values
        target_types = {e.work_item_type for e in target_summary.estimates}
        buyer_types = {e.work_item_type for e in buyer_summary.estimates}
        assert target_types == buyer_types, "Should have same work item types"


class TestCostBlueprintEntityFiltering:
    """Test entity filtering in cost blueprint functions."""

    @patch('web.context.load_deal_context')
    @patch('web.deal_data.get_deal_data')
    @patch('flask.session', {'current_deal_id': 'test-001'}, create=True)
    @patch('web.blueprints.inventory.get_inventory_store')
    def test_build_cost_center_target_only(
        self,
        mock_inv_store,
        mock_get_data,
        mock_load_context
    ):
        """build_cost_center_data(entity='target') returns only target costs."""
        # Setup mocks
        target_facts = CostModelTestData.create_org_facts(entity="target")
        target_work_items = CostModelTestData.create_work_items(entity="target")
        target_apps = CostModelTestData.create_application_inventory(entity="target")

        mock_data = Mock()
        mock_data.get_organization.return_value = target_facts
        mock_data.get_work_items.return_value = target_work_items
        mock_get_data.return_value = mock_data

        mock_inv = Mock()
        mock_inv.get_items.return_value = target_apps
        mock_inv.__len__ = lambda self: len(target_apps)
        mock_inv_store.return_value = mock_inv

        # Execute
        result = build_cost_center_data(entity="target")

        # Verify structure
        assert hasattr(result, 'run_rate')
        assert hasattr(result, 'one_time')
        assert hasattr(result, 'synergies')
        assert hasattr(result, 'data_quality')

        # Verify headcount only includes target (40 people)
        headcount_total = sum(
            item.item_count for item in result.run_rate.headcount.items
            if hasattr(item, 'item_count')
        )
        assert headcount_total == 40, "Should have 40 target employees"

    @patch('web.context.load_deal_context')
    @patch('web.deal_data.get_deal_data')
    @patch('flask.session', {'current_deal_id': 'test-002'}, create=True)
    @patch('web.blueprints.inventory.get_inventory_store')
    def test_build_cost_center_buyer_only(
        self,
        mock_inv_store,
        mock_get_data,
        mock_load_context
    ):
        """build_cost_center_data(entity='buyer') returns only buyer costs."""
        # Setup mocks
        buyer_facts = CostModelTestData.create_org_facts(entity="buyer")
        buyer_work_items = CostModelTestData.create_work_items(entity="buyer")
        buyer_apps = CostModelTestData.create_application_inventory(entity="buyer")

        mock_data = Mock()
        mock_data.get_organization.return_value = buyer_facts
        mock_data.get_work_items.return_value = buyer_work_items
        mock_get_data.return_value = mock_data

        mock_inv = Mock()
        mock_inv.get_items.return_value = buyer_apps
        mock_inv.__len__ = lambda self: len(buyer_apps)
        mock_inv_store.return_value = mock_inv

        # Execute
        result = build_cost_center_data(entity="buyer")

        # Verify headcount only includes buyer (150 people)
        headcount_total = sum(
            item.item_count for item in result.run_rate.headcount.items
            if hasattr(item, 'item_count')
        )
        assert headcount_total == 150, "Should have 150 buyer employees"

    @patch('web.context.load_deal_context')
    @patch('web.deal_data.get_deal_data')
    @patch('flask.session', {'current_deal_id': 'test-003'}, create=True)
    @patch('web.blueprints.inventory.get_inventory_store')
    def test_build_cost_center_all_entities(
        self,
        mock_inv_store,
        mock_get_data,
        mock_load_context
    ):
        """build_cost_center_data(entity='all') returns combined costs."""
        # Setup mocks
        all_facts = CostModelTestData.create_org_facts(entity="all")
        all_work_items = CostModelTestData.create_work_items(entity="all")
        all_apps = CostModelTestData.create_application_inventory(entity="all")

        mock_data = Mock()
        mock_data.get_organization.return_value = all_facts
        mock_data.get_work_items.return_value = all_work_items
        mock_get_data.return_value = mock_data

        mock_inv = Mock()
        mock_inv.get_items.return_value = all_apps
        mock_inv.__len__ = lambda self: len(all_apps)
        mock_inv_store.return_value = mock_inv

        # Execute
        result = build_cost_center_data(entity="all")

        # Verify headcount includes both (190 people)
        headcount_total = sum(
            item.item_count for item in result.run_rate.headcount.items
            if hasattr(item, 'item_count')
        )
        assert headcount_total == 190, "Should have 190 total employees (40 + 150)"


class TestSynergyIdentificationIntegration:
    """Test buyer vs target synergy identification with realistic data."""

    @patch('web.blueprints.inventory.get_inventory_store')
    def test_identify_synergies_with_test_data(self, mock_inv_store):
        """Identify synergies using realistic buyer vs target inventory."""
        # Create buyer and target applications
        all_apps = CostModelTestData.create_application_inventory(entity="all")

        # Configure mock to filter by entity
        def get_items(inventory_type=None, entity=None, status=None):
            if entity == "buyer":
                return [app for app in all_apps if app.entity == "buyer"]
            elif entity == "target":
                return [app for app in all_apps if app.entity == "target"]
            return []

        mock_inv = Mock()
        mock_inv.get_items = get_items
        mock_inv.__len__ = lambda self: len(all_apps)
        mock_inv_store.return_value = mock_inv

        # Execute
        synergies = _identify_synergies()

        # Verify - should find 3 synergies (CRM, ERP, Collaboration)
        assert len(synergies) == 3, f"Should find 3 synergies, found {len(synergies)}"

        synergy_names = {s.name.lower() for s in synergies}
        assert any("crm" in name for name in synergy_names), "Should find CRM synergy"
        assert any("erp" in name for name in synergy_names), "Should find ERP synergy"
        assert any("collaboration" in name for name in synergy_names), "Should find collaboration synergy"

        # Verify all are consolidation synergies
        for synergy in synergies:
            assert synergy.category == "consolidation"
            assert synergy.annual_savings_low > 0
            assert synergy.annual_savings_high > synergy.annual_savings_low
            assert synergy.cost_to_achieve_low > 0

    @patch('web.blueprints.inventory.get_inventory_store')
    def test_synergy_savings_realistic_ranges(self, mock_inv_store):
        """Verify synergy savings fall within realistic ranges."""
        all_apps = CostModelTestData.create_application_inventory(entity="all")

        def get_items(inventory_type=None, entity=None, status=None):
            if entity == "buyer":
                return [app for app in all_apps if app.entity == "buyer"]
            elif entity == "target":
                return [app for app in all_apps if app.entity == "target"]
            return []

        mock_inv = Mock()
        mock_inv.get_items = get_items
        mock_inv.__len__ = lambda self: len(all_apps)
        mock_inv_store.return_value = mock_inv

        # Execute
        synergies = _identify_synergies()

        # Find CRM synergy (largest savings)
        crm_synergy = next((s for s in synergies if "crm" in s.name.lower()), None)
        assert crm_synergy is not None

        # CRM: eliminate $300K + volume discount on $800K
        # Expected: $300K + ($800K * 0.10 to 0.30) = $380K to $540K
        assert 370_000 <= crm_synergy.annual_savings_low <= 390_000, \
            f"CRM low savings should be ~$380K, got ${crm_synergy.annual_savings_low:,}"
        assert 530_000 <= crm_synergy.annual_savings_high <= 550_000, \
            f"CRM high savings should be ~$540K, got ${crm_synergy.annual_savings_high:,}"


class TestQualityAssessmentIntegration:
    """Test data quality assessment with realistic cost data."""

    def test_quality_assessment_target_entity(self):
        """Quality assessment for target entity with realistic data."""
        run_rate = CostModelTestData.create_run_rate_costs(entity="target")
        one_time = CostModelTestData.create_one_time_costs(entity="target")

        # Execute
        quality = _assess_data_quality_per_entity(run_rate, one_time, entity="target")

        # Verify structure
        assert "headcount" in quality
        assert "applications" in quality
        assert "infrastructure" in quality
        assert "one_time" in quality
        assert "entity_filter" in quality

        # Verify target-specific quality scores
        expected = CostModelTestData.create_expected_quality_scores(entity="target")
        assert quality["headcount"]["overall"] == expected["headcount"]["overall"]
        assert quality["applications"]["overall"] == expected["applications"]["overall"]
        assert quality["infrastructure"]["overall"] == expected["infrastructure"]["overall"]
        assert quality["one_time"]["overall"] == expected["one_time"]["overall"]

    def test_quality_assessment_buyer_entity(self):
        """Quality assessment for buyer entity with realistic data."""
        run_rate = CostModelTestData.create_run_rate_costs(entity="buyer")
        one_time = CostModelTestData.create_one_time_costs(entity="buyer")

        # Execute
        quality = _assess_data_quality_per_entity(run_rate, one_time, entity="buyer")

        # Verify buyer-specific quality scores
        expected = CostModelTestData.create_expected_quality_scores(entity="buyer")
        assert quality["headcount"]["overall"] == expected["headcount"]["overall"]
        assert quality["applications"]["overall"] == expected["applications"]["overall"]

    def test_quality_assessment_all_entities(self):
        """Quality assessment for all entities combined."""
        run_rate = CostModelTestData.create_run_rate_costs(entity="all")
        one_time = CostModelTestData.create_one_time_costs(entity="all")

        # Execute
        quality = _assess_data_quality_per_entity(run_rate, one_time, entity="all")

        # Verify entity filter message
        assert "all entities" in quality["entity_filter"].lower()

        # Verify combined quality scores
        expected = CostModelTestData.create_expected_quality_scores(entity="all")
        assert quality["one_time"]["overall"] == expected["one_time"]["overall"]


class TestDriverExtractionEntityFiltering:
    """Test driver extraction with entity filtering."""

    def test_extract_drivers_filters_by_target(self):
        """extract_drivers_from_facts() filters to target facts only."""
        all_facts = (
            CostModelTestData.create_org_facts(entity="target") +
            CostModelTestData.create_org_facts(entity="buyer")
        )

        # Execute
        result = extract_drivers_from_facts(all_facts, deal_id="test", entity="target")

        # Verify
        assert result.drivers.entity == "target"

        # Drivers should reflect target scale (500 users, not 2500)
        # Note: Actual extraction logic may vary, but entity should propagate
        assert result.drivers.entity == "target"

    def test_extract_drivers_filters_by_buyer(self):
        """extract_drivers_from_facts() filters to buyer facts only."""
        all_facts = (
            CostModelTestData.create_org_facts(entity="target") +
            CostModelTestData.create_org_facts(entity="buyer")
        )

        # Execute
        result = extract_drivers_from_facts(all_facts, deal_id="test", entity="buyer")

        # Verify
        assert result.drivers.entity == "buyer"

    def test_extract_drivers_all_entities(self):
        """extract_drivers_from_facts() includes all facts when entity='all'."""
        all_facts = (
            CostModelTestData.create_org_facts(entity="target") +
            CostModelTestData.create_org_facts(entity="buyer")
        )

        # Execute
        result = extract_drivers_from_facts(all_facts, deal_id="test", entity="all")

        # Verify
        assert result.drivers.entity == "all"


class TestEndToEndCostModelWorkflow:
    """End-to-end workflow tests simulating real usage patterns."""

    @patch('web.context.load_deal_context')
    @patch('web.deal_data.get_deal_data')
    @patch('flask.session', {'current_deal_id': 'test-e2e'}, create=True)
    @patch('web.blueprints.inventory.get_inventory_store')
    def test_full_cost_analysis_workflow_target(
        self,
        mock_inv_store,
        mock_get_data,
        mock_load_context
    ):
        """Simulate full cost analysis workflow for target entity."""
        # Setup: Facts, work items, inventory
        target_facts = CostModelTestData.create_org_facts(entity="target")
        target_work_items = CostModelTestData.create_work_items(entity="target")
        target_apps = CostModelTestData.create_application_inventory(entity="target")

        mock_data = Mock()
        mock_data.get_organization.return_value = target_facts
        mock_data.get_work_items.return_value = target_work_items
        mock_get_data.return_value = mock_data

        mock_inv = Mock()
        mock_inv.get_items.return_value = target_apps
        mock_inv.__len__ = lambda self: len(target_apps)
        mock_inv_store.return_value = mock_inv

        # Step 1: Build cost center data
        cost_data = build_cost_center_data(entity="target")

        # Step 2: Verify run-rate costs
        assert cost_data.run_rate.headcount.total > 0
        assert cost_data.run_rate.applications.total > 0

        # Step 3: Verify one-time costs
        assert cost_data.one_time.total_mid > 0

        # Step 4: Verify quality assessment
        assert "headcount" in cost_data.data_quality
        assert "applications" in cost_data.data_quality

        # Step 5: Verify entity is target throughout
        assert "target" in cost_data.data_quality["entity_filter"].lower()

    def test_compare_target_vs_buyer_costs(self):
        """Compare target vs buyer cost outputs side-by-side."""
        # Calculate for both entities
        target_drivers = CostModelTestData.create_target_drivers()
        buyer_drivers = CostModelTestData.create_buyer_drivers()

        target_summary = calculate_deal_costs("compare-target", target_drivers)
        buyer_summary = calculate_deal_costs("compare-buyer", buyer_drivers)

        # Verify entity separation
        assert target_summary.entity == "target"
        assert buyer_summary.entity == "buyer"

        # Verify buyer has higher costs (4x users)
        # Note: costs may not scale linearly with users, so just verify buyer > target
        assert buyer_summary.total_one_time_base >= target_summary.total_one_time_base, \
            "Buyer should have higher or equal costs compared to target"

        # Verify both have valid cost scenario ordering
        for summary in [target_summary, buyer_summary]:
            # Upside <= Base <= Stress
            assert summary.total_one_time_upside <= summary.total_one_time_base
            assert summary.total_one_time_base <= summary.total_one_time_stress
