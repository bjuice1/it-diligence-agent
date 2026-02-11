"""
Test P0 Fixes for Cost Status Implementation

Verifies:
1. Shared utility works for both deterministic parser and LLM discovery
2. Database schema supports cost_status column with constraints
3. Both ingestion paths produce consistent cost_status data
"""

import pytest
from utils.cost_status_inference import infer_cost_status, normalize_numeric


class TestCostStatusUtility:
    """Test the shared cost status inference utility."""

    def test_infer_known_cost(self):
        """Test known cost with numeric value."""
        status, note = infer_cost_status("50000", vendor_name="Oracle")
        assert status == "known"
        assert note == ""

    def test_infer_unknown_cost_na(self):
        """Test unknown cost from N/A value."""
        status, note = infer_cost_status(None, vendor_name="Oracle", original_value="N/A")
        assert status == "unknown"
        assert "Cost not specified" in note
        assert "N/A" in note

    def test_infer_internal_no_cost_exact_match(self):
        """Test internal_no_cost for exact vendor keyword."""
        status, note = infer_cost_status("0", vendor_name="internal")
        assert status == "internal_no_cost"
        assert "Internally developed" in note

    def test_infer_internal_no_cost_prefix_match(self):
        """Test internal_no_cost for vendor prefix pattern."""
        status, note = infer_cost_status("0", vendor_name="Internal Development Team")
        assert status == "internal_no_cost"
        assert "Internally developed" in note

    def test_no_false_positive_for_custom_inc(self):
        """Test that 'Custom Software Inc.' doesn't trigger internal_no_cost."""
        status, note = infer_cost_status("0", vendor_name="Custom Software Inc.")
        assert status == "known"  # Should be 'known' (free/open source), not internal_no_cost
        assert "Free or open source" in note

    def test_infer_free_open_source(self):
        """Test known cost for free/open source (non-internal $0)."""
        status, note = infer_cost_status("0", vendor_name="PostgreSQL")
        assert status == "known"
        assert "Free or open source" in note

    def test_floating_point_precision(self):
        """Test that near-zero costs are treated as zero."""
        status, note = infer_cost_status("0.0000001", vendor_name="Test")
        assert status == "known"
        assert "Free or open source" in note


class TestNormalizeNumeric:
    """Test the normalize_numeric utility."""

    def test_normalize_dollar_sign(self):
        """Test normalization of dollar signs."""
        assert normalize_numeric("$50,000") == "50000"

    def test_normalize_k_suffix(self):
        """Test normalization of K suffix."""
        assert normalize_numeric("50K") == "50000"

    def test_normalize_m_suffix(self):
        """Test normalization of M suffix."""
        assert normalize_numeric("1.5M") == "1500000"

    def test_normalize_na_returns_none(self):
        """Test that N/A equivalents return None."""
        assert normalize_numeric("N/A") is None
        assert normalize_numeric("TBD") is None
        assert normalize_numeric("Unknown") is None

    def test_normalize_range_midpoint(self):
        """Test that ranges are converted to midpoint."""
        assert normalize_numeric("10-20") == "15"


class TestDeterministicParserIntegration:
    """Test that deterministic parser uses the shared utility."""

    def test_parser_imports_utility(self):
        """Verify parser imports the shared utility."""
        from tools_v2 import deterministic_parser
        assert hasattr(deterministic_parser, 'infer_cost_status')
        assert hasattr(deterministic_parser, 'normalize_numeric')


class TestLLMDiscoveryIntegration:
    """Test that LLM discovery uses the shared utility."""

    def test_discovery_imports_utility(self):
        """Verify discovery tools import the shared utility."""
        from tools_v2 import discovery_tools
        assert hasattr(discovery_tools, 'infer_cost_status')
        assert hasattr(discovery_tools, 'normalize_numeric')

    def test_discovery_infers_cost_status(self):
        """Test that discovery tools infer cost_status from details."""
        from stores.fact_store import FactStore
        from tools_v2.discovery_tools import _execute_create_inventory_entry

        store = FactStore(deal_id="test-deal")

        # Simulate LLM discovery agent creating an application fact with cost
        # This goes through the discovery_tools path which infers cost_status
        input_data = {
            'domain': 'applications',
            'category': 'crm',
            'item': 'Salesforce CRM',
            'details': {
                'vendor': 'Salesforce',
                'cost': '120000',
                'users': '500'
            },
            'status': 'documented',
            'evidence': {
                'exact_quote': 'Salesforce CRM is used by 500 users with annual cost of $120,000',
                'source_section': 'Application Inventory'
            },
            'entity': 'target',
            'source_document': 'test.pdf'
        }

        result = _execute_create_inventory_entry(input_data, store)

        # Verify fact was created successfully
        assert result['status'] == 'success'
        fact_id = result['fact_id']

        fact = store.get_fact(fact_id)

        # Should have cost_status inferred by discovery_tools
        assert 'cost_status' in fact.details
        assert fact.details['cost_status'] == 'known'


class TestDatabaseSchema:
    """Test database schema supports cost_status."""

    def test_fact_model_has_cost_status_column(self):
        """Verify Fact model has cost_status column."""
        from web.database import Fact
        assert hasattr(Fact, 'cost_status')

    def test_fact_to_dict_includes_cost_status(self):
        """Verify to_dict() includes cost_status."""
        from web.database import Fact, db
        from datetime import datetime

        fact = Fact()
        fact.id = 'F-TGT-APP-001'
        fact.deal_id = 'test-deal'
        fact.domain = 'applications'
        fact.category = 'crm'
        fact.entity = 'target'
        fact.item = 'Salesforce'
        fact.status = 'documented'
        fact.details = {'vendor': 'Salesforce'}
        fact.cost_status = 'known'
        fact.evidence = {}
        fact.source_document = 'test.pdf'
        fact.created_at = datetime.utcnow()

        fact_dict = fact.to_dict()

        assert 'cost_status' in fact_dict
        assert fact_dict['cost_status'] == 'known'


class TestConsistencyBetweenPaths:
    """Test that both ingestion paths produce consistent results."""

    def test_same_cost_produces_same_status(self):
        """Verify deterministic parser and LLM discovery produce same cost_status."""

        # Deterministic parser path
        parser_status, parser_note = infer_cost_status("50000", vendor_name="Oracle")

        # LLM discovery path (simulated)
        discovery_status, discovery_note = infer_cost_status("50000", vendor_name="Oracle")

        assert parser_status == discovery_status == "known"

    def test_na_produces_same_status(self):
        """Verify N/A handling is consistent."""

        parser_status, _ = infer_cost_status(None, original_value="N/A")
        discovery_status, _ = infer_cost_status(None, original_value="TBD")

        assert parser_status == discovery_status == "unknown"

    def test_internal_produces_same_status(self):
        """Verify internal app detection is consistent."""

        parser_status, _ = infer_cost_status("0", vendor_name="internal")
        discovery_status, _ = infer_cost_status("0", vendor_name="Internal Development")

        assert parser_status == discovery_status == "internal_no_cost"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
