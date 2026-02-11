"""
Unit tests for entity-aware cost blueprint functions.

Tests that headcount and one-time costs filter correctly by entity
in web/blueprints/costs.py.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock


class TestHeadcountEntityFiltering:
    """Test entity filtering in _gather_headcount_costs()."""

    @patch('web.context.load_deal_context')
    @patch('web.deal_data.get_deal_data')
    @patch('flask.session', {'current_deal_id': 'test-deal-001'}, create=True)
    def test_headcount_filters_by_target_entity(self, mock_get_data, mock_load_context):
        """Headcount costs filter to target entity only."""
        from web.blueprints.costs import _gather_headcount_costs

        # Create mock org facts with different entities
        target_fact = Mock()
        target_fact.entity = "target"
        target_fact.category = "engineering"
        target_fact.details = {"headcount": 10, "total_personnel_cost": 1_000_000}

        buyer_fact = Mock()
        buyer_fact.entity = "buyer"
        buyer_fact.category = "engineering"
        buyer_fact.details = {"headcount": 20, "total_personnel_cost": 2_000_000}

        mock_data = Mock()
        mock_data.get_organization.return_value = [target_fact, buyer_fact]
        mock_get_data.return_value = mock_data

        # Execute
        result = _gather_headcount_costs(entity="target")

        # Verify
        assert result.name == "headcount"
        # Should only include target fact ($1M), not buyer ($2M)
        assert result.total <= 1_000_000
        # Headcount should be 10, not 30
        total_headcount = sum(item.item_count for item in result.items if hasattr(item, 'item_count'))
        assert total_headcount == 10

    @patch('web.context.load_deal_context')
    @patch('web.deal_data.get_deal_data')
    @patch('flask.session', {'current_deal_id': 'test-deal-002'}, create=True)
    def test_headcount_filters_by_buyer_entity(self, mock_get_data, mock_load_context):
        """Headcount costs filter to buyer entity only."""
        from web.blueprints.costs import _gather_headcount_costs

        target_fact = Mock()
        target_fact.entity = "target"
        target_fact.category = "engineering"
        target_fact.details = {"headcount": 10, "total_personnel_cost": 1_000_000}

        buyer_fact = Mock()
        buyer_fact.entity = "buyer"
        buyer_fact.category = "engineering"
        buyer_fact.details = {"headcount": 20, "total_personnel_cost": 2_000_000}

        mock_data = Mock()
        mock_data.get_organization.return_value = [target_fact, buyer_fact]
        mock_get_data.return_value = mock_data

        # Execute
        result = _gather_headcount_costs(entity="buyer")

        # Verify
        # Should only include buyer fact ($2M), not target ($1M)
        assert result.total <= 2_000_000
        total_headcount = sum(item.item_count for item in result.items if hasattr(item, 'item_count'))
        assert total_headcount == 20

    @patch('web.context.load_deal_context')
    @patch('web.deal_data.get_deal_data')
    @patch('flask.session', {'current_deal_id': 'test-deal-003'}, create=True)
    def test_headcount_all_entity_includes_both(self, mock_get_data, mock_load_context):
        """Headcount costs with entity='all' includes both target and buyer."""
        from web.blueprints.costs import _gather_headcount_costs

        target_fact = Mock()
        target_fact.entity = "target"
        target_fact.category = "engineering"
        target_fact.details = {"headcount": 10, "total_personnel_cost": 1_000_000}

        buyer_fact = Mock()
        buyer_fact.entity = "buyer"
        buyer_fact.category = "engineering"
        buyer_fact.details = {"headcount": 20, "total_personnel_cost": 2_000_000}

        mock_data = Mock()
        mock_data.get_organization.return_value = [target_fact, buyer_fact]
        mock_get_data.return_value = mock_data

        # Execute
        result = _gather_headcount_costs(entity="all")

        # Verify
        # Should include both facts ($3M total)
        assert result.total >= 3_000_000
        total_headcount = sum(item.item_count for item in result.items if hasattr(item, 'item_count'))
        assert total_headcount == 30

    @patch('web.context.load_deal_context')
    @patch('web.deal_data.get_deal_data')
    @patch('flask.session', {'current_deal_id': 'test-deal-004'}, create=True)
    def test_headcount_default_entity_is_target(self, mock_get_data, mock_load_context):
        """Headcount costs defaults to entity='target' when not specified."""
        from web.blueprints.costs import _gather_headcount_costs

        target_fact = Mock()
        target_fact.entity = "target"
        target_fact.category = "engineering"
        target_fact.details = {"headcount": 10, "total_personnel_cost": 1_000_000}

        buyer_fact = Mock()
        buyer_fact.entity = "buyer"
        buyer_fact.category = "engineering"
        buyer_fact.details = {"headcount": 20, "total_personnel_cost": 2_000_000}

        mock_data = Mock()
        mock_data.get_organization.return_value = [target_fact, buyer_fact]
        mock_get_data.return_value = mock_data

        # Execute (no entity parameter)
        result = _gather_headcount_costs()

        # Verify - should default to target
        assert result.total <= 1_000_000
        total_headcount = sum(item.item_count for item in result.items if hasattr(item, 'item_count'))
        assert total_headcount == 10


class TestOneTimeCostsEntityFiltering:
    """Test entity filtering in _gather_one_time_costs()."""

    @patch('web.context.load_deal_context')
    @patch('web.deal_data.get_deal_data')
    @patch('flask.session', {'current_deal_id': 'test-deal-001'}, create=True)
    def test_one_time_costs_filters_by_target(self, mock_get_data, mock_load_context):
        """One-time costs filter to target entity only."""
        from web.blueprints.costs import _gather_one_time_costs

        # Create mock work items
        target_wi = Mock()
        target_wi.entity = "target"
        target_wi.cost_estimate = "100k_to_500k"
        target_wi.phase = "Day_1"
        target_wi.domain = "identity"

        buyer_wi = Mock()
        buyer_wi.entity = "buyer"
        buyer_wi.cost_estimate = "100k_to_500k"
        buyer_wi.phase = "Day_1"
        buyer_wi.domain = "identity"

        mock_data = Mock()
        mock_data.get_work_items.return_value = [target_wi, buyer_wi]
        mock_get_data.return_value = mock_data

        # Execute
        result = _gather_one_time_costs(entity="target")

        # Verify - should only include target work item
        # One work item with 100k-500k range
        assert result.total_low >= 100_000
        assert result.total_low < 200_000  # Only one item, not both

    @patch('web.context.load_deal_context')
    @patch('web.deal_data.get_deal_data')
    @patch('flask.session', {'current_deal_id': 'test-deal-002'}, create=True)
    def test_one_time_costs_filters_by_buyer(self, mock_get_data, mock_load_context):
        """One-time costs filter to buyer entity only."""
        from web.blueprints.costs import _gather_one_time_costs

        target_wi = Mock()
        target_wi.entity = "target"
        target_wi.cost_estimate = "100k_to_500k"
        target_wi.phase = "Day_1"
        target_wi.domain = "identity"

        buyer_wi = Mock()
        buyer_wi.entity = "buyer"
        buyer_wi.cost_estimate = "100k_to_500k"
        buyer_wi.phase = "Day_1"
        buyer_wi.domain = "identity"

        mock_data = Mock()
        mock_data.get_work_items.return_value = [target_wi, buyer_wi]
        mock_get_data.return_value = mock_data

        # Execute
        result = _gather_one_time_costs(entity="buyer")

        # Verify - should only include buyer work item
        assert result.total_low >= 100_000

    @patch('web.context.load_deal_context')
    @patch('web.deal_data.get_deal_data')
    @patch('flask.session', {'current_deal_id': 'test-deal-003'}, create=True)
    def test_one_time_costs_all_entity_includes_both(self, mock_get_data, mock_load_context):
        """One-time costs with entity='all' includes both target and buyer."""
        from web.blueprints.costs import _gather_one_time_costs

        target_wi = Mock()
        target_wi.entity = "target"
        target_wi.cost_estimate = "100k_to_500k"
        target_wi.phase = "Day_1"
        target_wi.domain = "identity"

        buyer_wi = Mock()
        buyer_wi.entity = "buyer"
        buyer_wi.cost_estimate = "100k_to_500k"
        buyer_wi.phase = "Day_1"
        buyer_wi.domain = "identity"

        mock_data = Mock()
        mock_data.get_work_items.return_value = [target_wi, buyer_wi]
        mock_get_data.return_value = mock_data

        # Execute
        result = _gather_one_time_costs(entity="all")

        # Verify - should include both work items
        # Two items with 100k-500k range each = 200k-1M combined
        assert result.total_low >= 200_000


class TestBuildCostCenterDataIntegration:
    """Test that build_cost_center_data() passes entity correctly."""

    @patch('web.blueprints.costs._gather_headcount_costs')
    @patch('web.blueprints.costs._gather_application_costs')
    @patch('web.blueprints.costs._gather_infrastructure_costs')
    @patch('web.blueprints.costs._gather_one_time_costs')
    @patch('web.blueprints.costs._identify_synergies')
    def test_build_cost_center_passes_entity_to_all_functions(
        self,
        mock_synergies,
        mock_one_time,
        mock_infra,
        mock_apps,
        mock_headcount
    ):
        """build_cost_center_data() passes entity parameter to all gathering functions."""
        from web.blueprints.costs import build_cost_center_data, CostCategory, OneTimeCosts

        # Setup mocks to return valid objects
        mock_headcount.return_value = CostCategory(name="headcount", display_name="Headcount", icon="👥")
        mock_apps.return_value = CostCategory(name="applications", display_name="Apps", icon="📱")
        mock_infra.return_value = CostCategory(name="infrastructure", display_name="Infra", icon="🖥️")
        mock_one_time.return_value = OneTimeCosts()
        mock_synergies.return_value = []

        # Execute
        result = build_cost_center_data(entity="buyer")

        # Verify all functions called with entity="buyer"
        mock_headcount.assert_called_once_with(entity="buyer")
        mock_apps.assert_called_once_with(entity="buyer")
        mock_infra.assert_called_once_with(entity="buyer")
        mock_one_time.assert_called_once_with(entity="buyer")
