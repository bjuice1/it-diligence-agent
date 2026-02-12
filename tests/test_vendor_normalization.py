"""
Tests for Vendor Normalization

Validates that:
1. Vendor field is normalized using AppMapping when available
2. Empty vendor fields use sentinel value in fingerprints
3. Unmapped apps fall back to raw vendor from table
4. Fingerprints are stable across re-imports
"""

import pytest
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from stores.id_generator import generate_inventory_id
from stores.fact_store import FactStore
from stores.inventory_store import InventoryStore
from tools_v2.deterministic_parser import ParsedTable, _app_table_to_facts


class TestVendorNormalization:
    """Test vendor normalization from AppMapping."""

    def test_vendor_normalized_from_appmapping_high_confidence(self):
        """Test that vendor is normalized for known apps with high confidence match."""
        # Concur is in AppMapping with vendor="SAP"
        table = ParsedTable(
            headers=["Application", "Vendor"],
            rows=[
                {"application": "Concur", "vendor": "SomeWrongVendor"},  # Table has wrong vendor
            ]
        )

        fact_store = FactStore(deal_id="test-vendor-norm-001")
        inv_store = InventoryStore(deal_id="test-vendor-norm-001")

        _app_table_to_facts(
            table, fact_store, entity="target",
            source_document="test.pdf", inventory_store=inv_store
        )

        # Verify vendor was normalized to canonical form from AppMapping
        items = inv_store.get_items(inventory_type="application", status="active")
        assert len(items) == 1
        assert items[0].name == "Concur"
        assert items[0].data["vendor"] == "SAP", f"Expected 'SAP' (from AppMapping), got '{items[0].data['vendor']}'"

    def test_vendor_normalized_from_appmapping_medium_confidence(self):
        """Test that vendor is normalized for partial matches (medium confidence)."""
        # "SAP ERP" should partially match "SAP" in AppMapping
        table = ParsedTable(
            headers=["Application", "Vendor"],
            rows=[
                {"application": "SAP ERP", "vendor": ""},  # Empty vendor in table
            ]
        )

        fact_store = FactStore(deal_id="test-vendor-norm-002")
        inv_store = InventoryStore(deal_id="test-vendor-norm-002")

        _app_table_to_facts(
            table, fact_store, entity="target",
            source_document="test.pdf", inventory_store=inv_store
        )

        # Verify vendor was normalized to canonical form from AppMapping
        items = inv_store.get_items(inventory_type="application", status="active")
        assert len(items) == 1
        assert items[0].name == "SAP ERP"
        assert items[0].data["vendor"] == "SAP", f"Expected 'SAP', got '{items[0].data['vendor']}'"

    def test_unmapped_app_uses_raw_vendor(self):
        """Test that unmapped apps use raw vendor from table."""
        # UnknownApp not in AppMapping (avoid "custom", "internal" to prevent category match)
        table = ParsedTable(
            headers=["Application", "Vendor"],
            rows=[
                {"application": "CompletelyUnknownApp", "vendor": "In-House"},
            ]
        )

        fact_store = FactStore(deal_id="test-vendor-norm-003")
        inv_store = InventoryStore(deal_id="test-vendor-norm-003")

        _app_table_to_facts(
            table, fact_store, entity="target",
            source_document="test.pdf", inventory_store=inv_store
        )

        # Verify raw vendor was used (no mapping available)
        items = inv_store.get_items(inventory_type="application", status="active")
        assert len(items) == 1
        assert items[0].name == "CompletelyUnknownApp"
        assert items[0].data["vendor"] == "In-House", f"Expected 'In-House', got '{items[0].data['vendor']}'"

    def test_empty_vendor_no_mapping_omits_vendor_field(self):
        """Test that unmapped apps with no vendor omit vendor field (empty values removed)."""
        # UnknownApp not in AppMapping, no vendor in table (avoid "custom")
        table = ParsedTable(
            headers=["Application"],
            rows=[
                {"application": "AnotherUnknownApp"},
            ]
        )

        fact_store = FactStore(deal_id="test-vendor-norm-004")
        inv_store = InventoryStore(deal_id="test-vendor-norm-004")

        _app_table_to_facts(
            table, fact_store, entity="target",
            source_document="test.pdf", inventory_store=inv_store
        )

        # Verify vendor field is omitted (empty values are filtered out)
        items = inv_store.get_items(inventory_type="application", status="active")
        assert len(items) == 1
        assert items[0].name == "AnotherUnknownApp"
        assert "vendor" not in items[0].data, f"Expected vendor field to be omitted, but found: '{items[0].data.get('vendor', 'N/A')}'"

    def test_no_duplicates_with_inconsistent_vendor_data(self):
        """Test that apps with inconsistent vendor data don't create duplicates."""
        # BlackLine appears twice with different vendor values
        table = ParsedTable(
            headers=["Application", "Vendor"],
            rows=[
                {"application": "BlackLine", "vendor": "BlackLine"},
                {"application": "BlackLine", "vendor": ""},  # Empty vendor
            ]
        )

        fact_store = FactStore(deal_id="test-vendor-norm-005")
        inv_store = InventoryStore(deal_id="test-vendor-norm-005")

        _app_table_to_facts(
            table, fact_store, entity="target",
            source_document="test.pdf", inventory_store=inv_store
        )

        # Should create only ONE inventory item (vendor normalized to same value)
        items = inv_store.get_items(inventory_type="application", status="active")
        assert len(items) == 1, f"Expected 1 item, got {len(items)}"
        assert items[0].name == "BlackLine"
        assert items[0].data["vendor"] == "BlackLine"  # Canonical from AppMapping


class TestEmptyFieldSentinel:
    """Test that empty optional fields use sentinel value in fingerprints."""

    def test_empty_vendor_uses_sentinel_in_fingerprint(self):
        """Test that empty vendor gets 'unspecified' in fingerprint hash."""
        # Two apps with empty vendor should generate same fingerprint
        id1 = generate_inventory_id(
            "application",
            {"name": "CustomApp", "vendor": ""},
            entity="target",
            deal_id="deal-123"
        )

        id2 = generate_inventory_id(
            "application",
            {"name": "CustomApp", "vendor": None},
            entity="target",
            deal_id="deal-123"
        )

        # Both should produce same ID (sentinel value "unspecified" used)
        assert id1 == id2, f"Expected same ID for empty vendor, got {id1} vs {id2}"

    def test_empty_vs_populated_vendor_different_fingerprints(self):
        """Test that empty and populated vendor create different fingerprints."""
        id_empty = generate_inventory_id(
            "application",
            {"name": "CustomApp", "vendor": ""},
            entity="target",
            deal_id="deal-123"
        )

        id_populated = generate_inventory_id(
            "application",
            {"name": "CustomApp", "vendor": "SomeVendor"},
            entity="target",
            deal_id="deal-123"
        )

        # Should be different (empty → "unspecified", populated → "somevendor")
        assert id_empty != id_populated, f"Expected different IDs, got {id_empty} and {id_populated}"

    def test_fingerprint_stability_across_reimport(self):
        """Test that same data always generates same fingerprint."""
        # Generate ID multiple times with same data
        ids = []
        for _ in range(5):
            item_id = generate_inventory_id(
                "application",
                {"name": "Salesforce", "vendor": "Salesforce"},
                entity="target",
                deal_id="deal-456"
            )
            ids.append(item_id)

        # All IDs should be identical
        assert len(set(ids)) == 1, f"Expected all IDs to be same, got {ids}"

    def test_sentinel_value_for_all_inventory_types(self):
        """Test that sentinel value works for all inventory types."""
        # Test each inventory type with empty optional field
        test_cases = [
            ("application", {"name": "App", "vendor": ""}),
            ("infrastructure", {"name": "Server", "environment": ""}),
            ("organization", {"role": "CTO", "team": ""}),
            ("vendor", {"vendor_name": "Acme", "contract_type": ""}),
        ]

        for inv_type, data in test_cases:
            id1 = generate_inventory_id(inv_type, data, entity="target", deal_id="test")
            id2 = generate_inventory_id(inv_type, data, entity="target", deal_id="test")

            assert id1 == id2, f"Sentinel failed for {inv_type}: {id1} vs {id2}"


class TestFingerprintStability:
    """Test that fingerprints remain stable across various scenarios."""

    def test_same_app_different_documents_same_id(self):
        """Test that same app from different docs gets same ID."""
        fact_store = FactStore(deal_id="test-stability-001")
        inv_store = InventoryStore(deal_id="test-stability-001")

        # First document
        table1 = ParsedTable(
            headers=["Application", "Vendor"],
            rows=[{"application": "Salesforce", "vendor": "Salesforce"}]
        )
        _app_table_to_facts(table1, fact_store, entity="target",
                           source_document="doc1.pdf", inventory_store=inv_store)

        # Second document with same app
        table2 = ParsedTable(
            headers=["Application", "Vendor"],
            rows=[{"application": "Salesforce", "vendor": "Salesforce"}]
        )
        _app_table_to_facts(table2, fact_store, entity="target",
                           source_document="doc2.pdf", inventory_store=inv_store)

        # Should create only ONE inventory item (same fingerprint)
        items = inv_store.get_items(inventory_type="application", status="active")
        assert len(items) == 1, f"Expected 1 item, got {len(items)}"

    def test_case_insensitive_fingerprints(self):
        """Test that fingerprints are case-insensitive."""
        id1 = generate_inventory_id(
            "application",
            {"name": "Salesforce", "vendor": "Salesforce"},
            entity="target", deal_id="test"
        )

        id2 = generate_inventory_id(
            "application",
            {"name": "SALESFORCE", "vendor": "SALESFORCE"},
            entity="target", deal_id="test"
        )

        # Should be same ID (normalized to lowercase)
        assert id1 == id2, f"Expected case-insensitive match, got {id1} vs {id2}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
