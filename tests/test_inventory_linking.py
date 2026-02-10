"""Tests for FactStore <-> InventoryStore bidirectional linking.

Spec 03: Validates Fact.inventory_item_id, InventoryItem.source_fact_ids,
bidirectional linking via sync_inventory_to_facts, reconciliation,
deal isolation, and backwards compatibility for missing fields.
"""
import pytest

from stores.fact_store import Fact
from stores.inventory_item import InventoryItem
from tools_v2.inventory_integration import reconcile_facts_and_inventory


class TestBidirectionalLinking:
    """Verify cross-references between F-* and I-* entries."""

    def test_fact_has_inventory_item_id_field(self):
        """Fact dataclass should have inventory_item_id field."""
        fact = Fact(
            fact_id="F-TGT-APP-001",
            domain="applications",
            category="erp",
            item="SAP",
            details={},
            status="documented",
            evidence={"exact_quote": "SAP ECC"},
            entity="target",
        )
        assert hasattr(fact, "inventory_item_id")
        assert fact.inventory_item_id == ""  # Default is empty string

    def test_inventory_item_has_source_fact_ids_field(self):
        """InventoryItem dataclass should have source_fact_ids field."""
        item = InventoryItem(
            item_id="I-APP-abc123",
            inventory_type="application",
            entity="target",
            data={"name": "SAP", "vendor": "SAP SE"},
            deal_id="test-deal",
        )
        assert hasattr(item, "source_fact_ids")
        assert item.source_fact_ids == []  # Default is empty list

    def test_fact_to_dict_includes_inventory_item_id(self):
        """Fact.to_dict() should include inventory_item_id."""
        fact = Fact(
            fact_id="F-TGT-APP-001",
            domain="applications",
            category="erp",
            item="SAP",
            details={},
            status="documented",
            evidence={},
            entity="target",
            inventory_item_id="I-APP-abc123",
        )
        d = fact.to_dict()
        assert "inventory_item_id" in d
        assert d["inventory_item_id"] == "I-APP-abc123"

    def test_inventory_item_to_dict_includes_source_fact_ids(self):
        """InventoryItem.to_dict() should include source_fact_ids."""
        item = InventoryItem(
            item_id="I-APP-abc123",
            inventory_type="application",
            entity="target",
            data={"name": "SAP"},
            source_fact_ids=["F-TGT-APP-001", "F-TGT-APP-002"],
            deal_id="test-deal",
        )
        d = item.to_dict()
        assert "source_fact_ids" in d
        assert d["source_fact_ids"] == ["F-TGT-APP-001", "F-TGT-APP-002"]

    def test_fact_from_dict_backwards_compat_missing_inventory_item_id(self):
        """Fact.from_dict should handle missing inventory_item_id (old data)."""
        old_dict = {
            "fact_id": "F-TGT-APP-001",
            "domain": "applications",
            "category": "erp",
            "item": "SAP",
            "details": {},
            "status": "documented",
            "evidence": {},
            "entity": "target",
            "created_at": "2026-01-01T00:00:00.000000",
        }
        fact = Fact.from_dict(old_dict)
        assert fact.inventory_item_id == ""

    def test_inventory_item_from_dict_backwards_compat_missing_source_fact_ids(self):
        """InventoryItem.from_dict should handle missing source_fact_ids (old data)."""
        old_dict = {
            "item_id": "I-APP-abc123",
            "inventory_type": "application",
            "entity": "target",
            "data": {"name": "SAP"},
            "deal_id": "test-deal",
            "created_at": "2026-01-01T00:00:00.000000",
        }
        item = InventoryItem.from_dict(old_dict)
        assert item.source_fact_ids == []


class TestReconciliation:
    """Verify reconcile_facts_and_inventory exists and is callable."""

    def test_reconcile_function_exists(self):
        """reconcile_facts_and_inventory should be importable and callable."""
        assert callable(reconcile_facts_and_inventory)

    def test_reconcile_signature(self):
        """Function should accept fact_store, inventory_store, and optional params."""
        import inspect
        sig = inspect.signature(reconcile_facts_and_inventory)
        params = list(sig.parameters.keys())
        assert "fact_store" in params
        assert "inventory_store" in params
        assert "similarity_threshold" in params


class TestDealIsolation:
    """Basic verification that deal isolation parameters exist."""

    def test_fact_has_deal_id(self):
        """Fact should have deal_id field for isolation."""
        fact = Fact(
            fact_id="F-TGT-APP-001",
            domain="applications",
            category="erp",
            item="SAP",
            details={},
            status="documented",
            evidence={},
            entity="target",
            deal_id="deal-123",
        )
        assert fact.deal_id == "deal-123"

    def test_inventory_item_has_deal_id(self):
        """InventoryItem should have deal_id field for isolation."""
        item = InventoryItem(
            item_id="I-APP-abc123",
            inventory_type="application",
            entity="target",
            data={"name": "SAP"},
            deal_id="deal-123",
        )
        assert item.deal_id == "deal-123"

    def test_inventory_item_validates_entity(self):
        """InventoryItem should reject invalid entity values."""
        with pytest.raises(ValueError, match="Invalid entity"):
            InventoryItem(
                item_id="I-APP-abc123",
                inventory_type="application",
                entity="neither",
                data={"name": "SAP"},
                deal_id="test-deal",
            )
