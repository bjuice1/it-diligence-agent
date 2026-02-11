"""
Unit tests for buyer vs target synergy matching.

Tests that _identify_synergies() correctly matches buyer and target applications
by category and calculates consolidation synergies.
"""

import pytest
from unittest.mock import Mock, patch
from web.blueprints.costs import _identify_synergies, SynergyOpportunity


class TestSynergyMatching:
    """Test buyer vs target synergy identification."""

    @patch('web.blueprints.inventory.get_inventory_store')
    def test_identify_synergies_buyer_target_overlap(self, mock_get_inv_store):
        """Identify synergies from buyer vs target category overlap."""
        # Setup mock inventory store
        mock_inv_store = Mock()

        # Buyer has Salesforce (CRM)
        buyer_app = Mock()
        buyer_app.name = "Salesforce (Buyer)"
        buyer_app.data = {"category": "crm"}
        buyer_app.cost = 500_000

        # Target has Salesforce (CRM)
        target_app = Mock()
        target_app.name = "Salesforce (Target)"
        target_app.data = {"category": "crm"}
        target_app.cost = 300_000

        # Configure mock to return apps based on entity
        def get_items(inventory_type=None, entity=None, status=None):
            if entity == "buyer":
                return [buyer_app]
            elif entity == "target":
                return [target_app]
            return []

        mock_inv_store.get_items = get_items
        mock_inv_store.__len__ = lambda self: 2  # Has items
        mock_get_inv_store.return_value = mock_inv_store

        # Execute
        synergies = _identify_synergies()

        # Verify
        assert len(synergies) > 0, "Should find at least one synergy"

        # Find CRM synergy
        crm_synergy = next((s for s in synergies if "Crm" in s.name or "CRM" in s.name.upper()), None)
        assert crm_synergy is not None, "Should find CRM consolidation synergy"

        # Verify synergy properties
        assert crm_synergy.category == "consolidation"
        assert crm_synergy.annual_savings_low > 0, "Should have positive savings (low)"
        assert crm_synergy.annual_savings_high > 0, "Should have positive savings (high)"
        assert crm_synergy.annual_savings_high > crm_synergy.annual_savings_low, "High savings should exceed low"
        assert crm_synergy.cost_to_achieve_low > 0, "Should have cost to achieve"
        assert "buyer" in crm_synergy.notes.lower() or "target" in crm_synergy.notes.lower(), "Notes should mention entities"

    @patch('web.blueprints.inventory.get_inventory_store')
    def test_identify_synergies_no_overlap(self, mock_get_inv_store):
        """No synergies when buyer and target have different categories."""
        # Setup mock inventory store
        mock_inv_store = Mock()

        # Buyer has CRM
        buyer_app = Mock()
        buyer_app.name = "Salesforce"
        buyer_app.data = {"category": "crm"}
        buyer_app.cost = 500_000

        # Target has ERP (different category)
        target_app = Mock()
        target_app.name = "NetSuite"
        target_app.data = {"category": "erp"}
        target_app.cost = 300_000

        def get_items(inventory_type=None, entity=None, status=None):
            if entity == "buyer":
                return [buyer_app]
            elif entity == "target":
                return [target_app]
            return []

        mock_inv_store.get_items = get_items
        mock_inv_store.__len__ = lambda self: 2
        mock_get_inv_store.return_value = mock_inv_store

        # Execute
        synergies = _identify_synergies()

        # Verify - should find no synergies (no category overlap)
        assert len(synergies) == 0, "Should find no synergies when categories don't overlap"

    @patch('web.blueprints.inventory.get_inventory_store')
    def test_synergy_savings_calculation(self, mock_get_inv_store):
        """Verify synergy savings calculation logic."""
        # Setup mock inventory store
        mock_inv_store = Mock()

        # Buyer has expensive app in category
        buyer_app = Mock()
        buyer_app.name = "App A (Buyer)"
        buyer_app.data = {"category": "productivity"}
        buyer_app.cost = 600_000  # Larger

        # Target has cheaper app in same category
        target_app = Mock()
        target_app.name = "App B (Target)"
        target_app.data = {"category": "productivity"}
        target_app.cost = 200_000  # Smaller

        def get_items(inventory_type=None, entity=None, status=None):
            if entity == "buyer":
                return [buyer_app]
            elif entity == "target":
                return [target_app]
            return []

        mock_inv_store.get_items = get_items
        mock_inv_store.__len__ = lambda self: 2
        mock_get_inv_store.return_value = mock_inv_store

        # Execute
        synergies = _identify_synergies()

        # Verify
        assert len(synergies) == 1, "Should find one synergy"

        synergy = synergies[0]

        # Savings model: eliminate smaller ($200K) + volume discount on larger (10-30% of $600K)
        # Low: $200K + ($600K * 0.10) = $200K + $60K = $260K
        # High: $200K + ($600K * 0.30) = $200K + $180K = $380K

        expected_savings_low = 200_000 + (600_000 * 0.10)  # $260K
        expected_savings_high = 200_000 + (600_000 * 0.30)  # $380K

        # Allow for rounding (to nearest $1K)
        assert abs(synergy.annual_savings_low - expected_savings_low) < 1_000, \
            f"Low savings should be ~${expected_savings_low:,.0f}, got ${synergy.annual_savings_low:,.0f}"
        assert abs(synergy.annual_savings_high - expected_savings_high) < 1_000, \
            f"High savings should be ~${expected_savings_high:,.0f}, got ${synergy.annual_savings_high:,.0f}"

        # Cost to achieve: 50-200% of smaller ($200K)
        expected_cost_low = 200_000 * 0.5  # $100K
        expected_cost_high = 200_000 * 2.0  # $400K

        assert abs(synergy.cost_to_achieve_low - expected_cost_low) < 1_000, \
            f"Low cost should be ~${expected_cost_low:,.0f}"
        assert abs(synergy.cost_to_achieve_high - expected_cost_high) < 1_000, \
            f"High cost should be ~${expected_cost_high:,.0f}"

    @patch('web.blueprints.inventory.get_inventory_store')
    def test_multiple_category_overlaps(self, mock_get_inv_store):
        """Identify multiple synergies across different categories."""
        # Setup mock inventory store
        mock_inv_store = Mock()

        # Buyer has CRM and ERP
        buyer_crm = Mock()
        buyer_crm.name = "Salesforce"
        buyer_crm.data = {"category": "crm"}
        buyer_crm.cost = 400_000

        buyer_erp = Mock()
        buyer_erp.name = "SAP"
        buyer_erp.data = {"category": "erp"}
        buyer_erp.cost = 800_000

        # Target has CRM and ERP
        target_crm = Mock()
        target_crm.name = "HubSpot"
        target_crm.data = {"category": "crm"}
        target_crm.cost = 200_000

        target_erp = Mock()
        target_erp.name = "NetSuite"
        target_erp.data = {"category": "erp"}
        target_erp.cost = 300_000

        def get_items(inventory_type=None, entity=None, status=None):
            if entity == "buyer":
                return [buyer_crm, buyer_erp]
            elif entity == "target":
                return [target_crm, target_erp]
            return []

        mock_inv_store.get_items = get_items
        mock_inv_store.__len__ = lambda self: 4
        mock_get_inv_store.return_value = mock_inv_store

        # Execute
        synergies = _identify_synergies()

        # Verify - should find 2 synergies (CRM + ERP)
        assert len(synergies) == 2, f"Should find 2 synergies (CRM and ERP), found {len(synergies)}"

        synergy_names = {s.name for s in synergies}
        assert any("crm" in name.lower() for name in synergy_names), "Should have CRM synergy"
        assert any("erp" in name.lower() for name in synergy_names), "Should have ERP synergy"

    @patch('web.blueprints.inventory.get_inventory_store')
    def test_skip_low_cost_synergies(self, mock_get_inv_store):
        """Skip synergies when combined cost is below threshold."""
        # Setup mock inventory store
        mock_inv_store = Mock()

        # Buyer and target both have low-cost app in same category
        buyer_app = Mock()
        buyer_app.name = "Small Tool (Buyer)"
        buyer_app.data = {"category": "utilities"}
        buyer_app.cost = 30_000

        target_app = Mock()
        target_app.name = "Small Tool (Target)"
        target_app.data = {"category": "utilities"}
        target_app.cost = 40_000

        # Combined cost = $70K (below $100K threshold)

        def get_items(inventory_type=None, entity=None, status=None):
            if entity == "buyer":
                return [buyer_app]
            elif entity == "target":
                return [target_app]
            return []

        mock_inv_store.get_items = get_items
        mock_inv_store.__len__ = lambda self: 2
        mock_get_inv_store.return_value = mock_inv_store

        # Execute
        synergies = _identify_synergies()

        # Verify - should skip due to low combined cost
        assert len(synergies) == 0, "Should skip synergies below $100K combined cost"

    @patch('web.blueprints.inventory.get_inventory_store')
    def test_critical_vs_non_critical_timeframes(self, mock_get_inv_store):
        """Critical systems have longer timeframes than non-critical."""
        # Setup mock inventory store
        mock_inv_store = Mock()

        # Critical CRM
        buyer_crm = Mock()
        buyer_crm.name = "Salesforce"
        buyer_crm.data = {"category": "crm"}  # Critical
        buyer_crm.cost = 300_000

        target_crm = Mock()
        target_crm.name = "HubSpot"
        target_crm.data = {"category": "crm"}
        target_crm.cost = 200_000

        # Non-critical collaboration tool
        buyer_collab = Mock()
        buyer_collab.name = "Slack"
        buyer_collab.data = {"category": "collaboration"}  # Non-critical
        buyer_collab.cost = 100_000

        target_collab = Mock()
        target_collab.name = "Teams"
        target_collab.data = {"category": "collaboration"}
        target_collab.cost = 80_000

        def get_items(inventory_type=None, entity=None, status=None):
            if entity == "buyer":
                return [buyer_crm, buyer_collab]
            elif entity == "target":
                return [target_crm, target_collab]
            return []

        mock_inv_store.get_items = get_items
        mock_inv_store.__len__ = lambda self: 4
        mock_get_inv_store.return_value = mock_inv_store

        # Execute
        synergies = _identify_synergies()

        # Verify
        assert len(synergies) == 2, "Should find 2 synergies"

        crm_synergy = next((s for s in synergies if "crm" in s.name.lower()), None)
        collab_synergy = next((s for s in synergies if "collaboration" in s.name.lower()), None)

        assert crm_synergy is not None, "Should find CRM synergy"
        assert collab_synergy is not None, "Should find collaboration synergy"

        # Critical systems take longer
        assert crm_synergy.timeframe == "12-18 months", "CRM should have 12-18 month timeframe"
        assert crm_synergy.confidence == "medium", "CRM should have medium confidence"

        # Non-critical systems are faster
        assert collab_synergy.timeframe == "6-12 months", "Collaboration should have 6-12 month timeframe"
        assert collab_synergy.confidence == "high", "Collaboration should have high confidence"
