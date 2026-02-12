"""
Tests for Inventory Store (Phase 1: Foundation)

Tests:
1. InventoryItem creation and validation
2. ID generation (content-based, stable)
3. InventoryStore CRUD operations
4. Query and search functionality
5. Save/load persistence
6. Merge and re-import
"""

import pytest
import tempfile
from pathlib import Path
import json

from stores.inventory_store import InventoryStore
from stores.inventory_item import InventoryItem, MergeResult
from stores.id_generator import (
    generate_inventory_id,
    generate_fact_id,
    generate_gap_id,
    is_inventory_id,
    is_fact_id,
    is_gap_id,
    parse_id,
)
from stores.inventory_schemas import (
    INVENTORY_SCHEMAS,
    INVENTORY_PREFIXES,
    get_schema,
    get_id_fields,
    validate_inventory_type,
)


# =============================================================================
# ID Generator Tests
# =============================================================================

class TestIDGenerator:
    """Tests for content-based ID generation."""

    def test_inventory_id_format(self):
        """Test that inventory IDs have correct format."""
        item_id = generate_inventory_id(
            "application",
            {"name": "Salesforce", "vendor": "Salesforce"},
            "target"
        )
        assert item_id.startswith("I-APP-")
        assert len(item_id) == 12  # I-APP-xxxxxx (6 prefix + 6 hash)

    def test_inventory_id_stability(self):
        """Same content always produces same ID."""
        data = {"name": "Duck Creek", "vendor": "Duck Creek Technologies"}

        id1 = generate_inventory_id("application", data, "target")
        id2 = generate_inventory_id("application", data, "target")

        assert id1 == id2

    def test_inventory_id_different_entity(self):
        """Different entity produces different ID."""
        data = {"name": "Salesforce", "vendor": "Salesforce"}

        target_id = generate_inventory_id("application", data, "target")
        buyer_id = generate_inventory_id("application", data, "buyer")

        assert target_id != buyer_id

    def test_inventory_id_case_insensitive(self):
        """ID generation is case-insensitive."""
        id1 = generate_inventory_id(
            "application",
            {"name": "SALESFORCE", "vendor": "Salesforce"},
            "target"
        )
        id2 = generate_inventory_id(
            "application",
            {"name": "salesforce", "vendor": "salesforce"},
            "target"
        )

        assert id1 == id2

    def test_inventory_id_whitespace_normalized(self):
        """Whitespace is normalized in ID generation."""
        id1 = generate_inventory_id(
            "application",
            {"name": "  Salesforce  ", "vendor": "Salesforce"},
            "target"
        )
        id2 = generate_inventory_id(
            "application",
            {"name": "Salesforce", "vendor": "Salesforce"},
            "target"
        )

        assert id1 == id2

    def test_inventory_id_different_types(self):
        """Different inventory types produce different prefixes."""
        app_id = generate_inventory_id("application", {"name": "Test"}, "target")
        infra_id = generate_inventory_id("infrastructure", {"name": "Test"}, "target")
        org_id = generate_inventory_id("organization", {"role": "Test"}, "target")
        vendor_id = generate_inventory_id("vendor", {"vendor_name": "Test"}, "target")

        assert app_id.startswith("I-APP-")
        assert infra_id.startswith("I-INFRA-")
        assert org_id.startswith("I-ORG-")
        assert vendor_id.startswith("I-VENDOR-")

    def test_fact_id_format(self):
        """Test fact ID format."""
        fact_id = generate_fact_id(
            "cybersecurity",
            "MFA not enabled for admin accounts",
            "target"
        )
        assert fact_id.startswith("F-CYBER-")
        assert len(fact_id) == 14  # F-CYBER-xxxxxx (8 prefix + 6 hash)

    def test_gap_id_format(self):
        """Test gap ID format."""
        gap_id = generate_gap_id(
            "infrastructure",
            "DR plan not documented",
            "target"
        )
        assert gap_id.startswith("G-INFRA-")

    def test_id_type_detection(self):
        """Test ID type detection utilities."""
        inv_id = "I-APP-a3f291"
        fact_id = "F-CYBER-8d2a91"
        gap_id = "G-INFRA-c7b123"

        assert is_inventory_id(inv_id)
        assert not is_inventory_id(fact_id)

        assert is_fact_id(fact_id)
        assert not is_fact_id(inv_id)

        assert is_gap_id(gap_id)
        assert not is_gap_id(fact_id)

    def test_parse_id(self):
        """Test ID parsing."""
        parsed = parse_id("I-APP-a3f291")
        assert parsed["type"] == "inventory"
        assert parsed["prefix"] == "APP"
        assert parsed["hash"] == "a3f291"

        parsed = parse_id("F-CYBER-8d2a91")
        assert parsed["type"] == "fact"
        assert parsed["prefix"] == "CYBER"


# =============================================================================
# InventoryItem Tests
# =============================================================================

class TestInventoryItem:
    """Tests for InventoryItem dataclass."""

    def test_create_application(self):
        """Test creating an application inventory item."""
        item = InventoryItem(
            item_id="I-APP-test01",
            inventory_type="application",
            entity="target",
            data={
                "name": "Salesforce",
                "vendor": "Salesforce",
                "version": "Enterprise",
                "cost": 50000,
                "criticality": "high",
            },
            source_file="apps.xlsx",
        )

        assert item.name == "Salesforce"
        assert item.cost == 50000.0
        assert item.criticality == "high"
        assert item.is_active

    def test_create_infrastructure(self):
        """Test creating an infrastructure inventory item."""
        item = InventoryItem(
            item_id="I-INFRA-test01",
            inventory_type="infrastructure",
            entity="target",
            data={
                "name": "web-server-01",
                "type": "vm",
                "os": "Ubuntu 22.04",
                "environment": "production",
            },
            source_file="servers.csv",
        )

        assert item.name == "web-server-01"
        assert item.data["os"] == "Ubuntu 22.04"

    def test_item_validation(self):
        """Test that invalid items raise errors."""
        with pytest.raises(ValueError):
            InventoryItem(
                item_id="I-INVALID-test",
                inventory_type="invalid_type",  # Invalid
                entity="target",
                data={"name": "Test"},
                source_file="test.csv",
            )

        with pytest.raises(ValueError):
            InventoryItem(
                item_id="I-APP-test",
                inventory_type="application",
                entity="invalid_entity",  # Invalid
                data={"name": "Test"},
                source_file="test.csv",
            )

    def test_item_update(self):
        """Test updating item data."""
        item = InventoryItem(
            item_id="I-APP-test01",
            inventory_type="application",
            entity="target",
            data={"name": "Test App", "cost": 1000},
            source_file="test.xlsx",
        )

        item.update({"cost": 2000, "version": "2.0"}, modified_by="user@test.com")

        assert item.data["cost"] == 2000
        assert item.data["version"] == "2.0"
        assert item.modified_by == "user@test.com"
        assert item.modified_at != ""

    def test_item_enrichment(self):
        """Test setting enrichment data."""
        item = InventoryItem(
            item_id="I-APP-test01",
            inventory_type="application",
            entity="target",
            data={"name": "Salesforce"},
            source_file="test.xlsx",
        )

        assert not item.is_enriched

        item.set_enrichment(
            category="industry_standard",
            note="Leading CRM platform",
            confidence="high",
        )

        assert item.is_enriched
        assert item.enrichment_category == "industry_standard"
        assert not item.needs_investigation

    def test_item_remove_restore(self):
        """Test removing and restoring items."""
        item = InventoryItem(
            item_id="I-APP-test01",
            inventory_type="application",
            entity="target",
            data={"name": "Test App"},
            source_file="test.xlsx",
        )

        assert item.is_active

        item.remove("No longer used", "admin")
        assert not item.is_active
        assert item.status == "removed"
        assert item.removal_reason == "No longer used"

        item.restore()
        assert item.is_active
        assert item.removal_reason == ""

    def test_item_serialization(self):
        """Test to_dict and from_dict."""
        item = InventoryItem(
            item_id="I-APP-test01",
            inventory_type="application",
            entity="target",
            data={"name": "Test App", "cost": 5000},
            source_file="test.xlsx",
            enrichment={"category": "niche", "note": "Specialized tool"},
        )

        # Serialize
        data = item.to_dict()
        assert data["item_id"] == "I-APP-test01"
        assert data["data"]["cost"] == 5000

        # Deserialize
        restored = InventoryItem.from_dict(data)
        assert restored.item_id == item.item_id
        assert restored.data == item.data
        assert restored.enrichment == item.enrichment

    def test_cost_parsing(self):
        """Test cost parsing from various formats."""
        # Numeric cost
        item1 = InventoryItem(
            item_id="I-APP-test01",
            inventory_type="application",
            entity="target",
            data={"name": "App1", "cost": 50000},
            source_file="test.xlsx",
        )
        assert item1.cost == 50000.0

        # String cost with currency
        item2 = InventoryItem(
            item_id="I-APP-test02",
            inventory_type="application",
            entity="target",
            data={"name": "App2", "cost": "$50,000"},
            source_file="test.xlsx",
        )
        assert item2.cost == 50000.0

        # No cost
        item3 = InventoryItem(
            item_id="I-APP-test03",
            inventory_type="application",
            entity="target",
            data={"name": "App3"},
            source_file="test.xlsx",
        )
        assert item3.cost is None


# =============================================================================
# InventoryStore Tests
# =============================================================================

class TestInventoryStore:
    """Tests for InventoryStore class."""

    def test_add_item(self):
        """Test adding items to store."""
        store = InventoryStore(deal_id="test-deal")

        item_id = store.add_item(
            inventory_type="application",
            data={"name": "Salesforce", "vendor": "Salesforce"},
            entity="target",
            source_file="apps.xlsx",
        )

        assert item_id.startswith("I-APP-")
        assert store.exists(item_id)
        assert len(store) == 1

    def test_add_duplicate_returns_existing(self):
        """Adding duplicate item returns existing ID."""
        store = InventoryStore(deal_id="test-deal")

        id1 = store.add_item(
            inventory_type="application",
            data={"name": "Salesforce", "vendor": "Salesforce"},
            entity="target",
        )

        id2 = store.add_item(
            inventory_type="application",
            data={"name": "Salesforce", "vendor": "Salesforce"},
            entity="target",
        )

        assert id1 == id2
        assert len(store) == 1

    def test_get_item(self):
        """Test retrieving items."""
        store = InventoryStore(deal_id="test-deal")

        item_id = store.add_item(
            inventory_type="application",
            data={"name": "Test App", "cost": 10000},
            entity="target",
        )

        item = store.get_item(item_id)
        assert item is not None
        assert item.name == "Test App"
        assert item.cost == 10000.0

        # Non-existent item
        assert store.get_item("I-APP-nonexistent") is None

    def test_update_item(self):
        """Test updating items."""
        store = InventoryStore(deal_id="test-deal")

        item_id = store.add_item(
            inventory_type="application",
            data={"name": "Test App", "cost": 10000},
            entity="target",
        )

        result = store.update_item(item_id, {"cost": 20000}, modified_by="user")
        assert result is True

        item = store.get_item(item_id)
        assert item.data["cost"] == 20000

        # Update non-existent
        result = store.update_item("I-APP-nonexistent", {"cost": 0})
        assert result is False

    def test_remove_item(self):
        """Test removing items."""
        store = InventoryStore(deal_id="test-deal")

        item_id = store.add_item(
            inventory_type="application",
            data={"name": "Test App"},
            entity="target",
        )

        assert len(store) == 1

        result = store.remove_item(item_id, "No longer needed", "admin")
        assert result is True

        # Item still exists but is not active
        assert store.exists(item_id)
        assert not store.exists_active(item_id)
        assert len(store) == 0  # len() counts only active

    def test_entity_validation(self):
        """Test that entity field is validated and cannot be None or empty."""
        import pytest
        store = InventoryStore(deal_id="test-deal")

        # Test add_item() rejects None entity
        with pytest.raises(ValueError, match="entity is required"):
            store.add_item(
                inventory_type="application",
                data={"name": "Test App"},
                entity=None
            )

        # Test add_item() rejects empty string entity
        with pytest.raises(ValueError, match="entity is required"):
            store.add_item(
                inventory_type="application",
                data={"name": "Test App"},
                entity=""
            )

        # Test add_item() rejects whitespace-only entity
        with pytest.raises(ValueError, match="entity is required"):
            store.add_item(
                inventory_type="application",
                data={"name": "Test App"},
                entity="   "
            )

        # Test add_from_table() rejects None entity
        with pytest.raises(ValueError, match="entity is required"):
            store.add_from_table(
                inventory_type="application",
                rows=[{"name": "App1"}, {"name": "App2"}],
                entity=None
            )

        # Test add_from_table() rejects empty string entity
        with pytest.raises(ValueError, match="entity is required"):
            store.add_from_table(
                inventory_type="application",
                rows=[{"name": "App1"}, {"name": "App2"}],
                entity=""
            )

        # Verify valid entity values work correctly
        item_id = store.add_item(
            inventory_type="application",
            data={"name": "Valid App"},
            entity="target"
        )
        assert item_id is not None
        item = store.get_item(item_id)
        assert item.entity == "target"

        # Verify buyer entity also works
        item_id2 = store.add_item(
            inventory_type="application",
            data={"name": "Buyer App"},
            entity="buyer"
        )
        assert item_id2 is not None
        item2 = store.get_item(item_id2)
        assert item2.entity == "buyer"

    def test_get_items_by_type(self):
        """Test filtering by inventory type."""
        store = InventoryStore(deal_id="test-deal")

        store.add_item("application", {"name": "App1"}, "target")
        store.add_item("application", {"name": "App2"}, "target")
        store.add_item("infrastructure", {"name": "Server1"}, "target")

        apps = store.get_items(inventory_type="application")
        assert len(apps) == 2

        infra = store.get_items(inventory_type="infrastructure")
        assert len(infra) == 1

    def test_get_items_by_entity(self):
        """Test filtering by entity."""
        store = InventoryStore(deal_id="test-deal")

        store.add_item("application", {"name": "App1"}, "target")
        store.add_item("application", {"name": "App2"}, "buyer")

        target_apps = store.get_items(entity="target")
        assert len(target_apps) == 1

        buyer_apps = store.get_items(entity="buyer")
        assert len(buyer_apps) == 1

    def test_find_by_name(self):
        """Test finding items by name."""
        store = InventoryStore(deal_id="test-deal")

        store.add_item("application", {"name": "Salesforce CRM", "vendor": "Salesforce"}, "target")
        store.add_item("application", {"name": "SAP ERP", "vendor": "SAP"}, "target")

        # Partial match
        item = store.find_by_name("salesforce")
        assert item is not None
        assert "Salesforce" in item.name

        # Exact match
        item = store.find_by_name("SAP ERP", exact=True)
        assert item is not None

        # No match
        item = store.find_by_name("Oracle")
        assert item is None

    def test_search(self):
        """Test text search."""
        store = InventoryStore(deal_id="test-deal")

        store.add_item("application", {"name": "Salesforce", "vendor": "Salesforce", "notes": "CRM system"}, "target")
        store.add_item("application", {"name": "SAP", "vendor": "SAP", "notes": "ERP system"}, "target")

        # Search by name
        results = store.search("sales")
        assert len(results) == 1

        # Search by notes
        results = store.search("CRM")
        assert len(results) == 1

    def test_count_and_sum(self):
        """Test aggregation methods."""
        store = InventoryStore(deal_id="test-deal")

        store.add_item("application", {"name": "App1", "cost": 10000}, "target")
        store.add_item("application", {"name": "App2", "cost": 20000}, "target")
        store.add_item("infrastructure", {"name": "Server1", "cost": 5000}, "target")

        assert store.count() == 3
        assert store.count(inventory_type="application") == 2
        assert store.sum_costs() == 35000.0
        assert store.sum_costs(inventory_type="application") == 30000.0

    def test_get_summary(self):
        """Test summary generation."""
        store = InventoryStore(deal_id="test-deal")

        store.add_item("application", {"name": "App1", "cost": 10000}, "target")
        store.add_item("application", {"name": "App2", "cost": 20000}, "target")
        store.add_item("infrastructure", {"name": "Server1"}, "target")

        summary = store.get_summary()

        assert summary["total_items"] == 3
        assert summary["active_items"] == 3
        assert summary["total_cost"] == 30000.0
        assert summary["by_type"]["application"]["count"] == 2

    def test_save_and_load(self):
        """Test persistence."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "inventory.json"

            # Create and save
            store1 = InventoryStore(deal_id="test-deal")
            store1.add_item("application", {"name": "App1", "cost": 10000}, "target")
            store1.add_item("application", {"name": "App2", "cost": 20000}, "target")
            store1.save(path)

            # Load into new store
            store2 = InventoryStore(deal_id="test-deal")
            store2.load_from_file(path)

            assert len(store2) == 2
            assert store2.sum_costs() == 30000.0

            # Verify IDs are preserved
            items1 = {item.item_id for item in store1}
            items2 = {item.item_id for item in store2}
            assert items1 == items2

    def test_save_load_with_storage_path(self):
        """Test auto-load from storage_path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "inventory.json"

            # Create and save
            store1 = InventoryStore(deal_id="test-deal", storage_path=path)
            store1.add_item("application", {"name": "App1"}, "target")
            store1.save()

            # Create new store with same path - should auto-load
            store2 = InventoryStore(deal_id="test-deal", storage_path=path)
            assert len(store2) == 1

    def test_merge_add_new(self):
        """Test merge with add_new strategy."""
        store1 = InventoryStore(deal_id="test-deal")
        store1.add_item("application", {"name": "App1"}, "target")

        store2 = InventoryStore(deal_id="test-deal")
        store2.add_item("application", {"name": "App1"}, "target")  # Same
        store2.add_item("application", {"name": "App2"}, "target")  # New

        result = store1.merge_from(store2, strategy="add_new")

        assert result.added == 1
        assert result.unchanged == 1
        assert len(store1) == 2

    def test_merge_update(self):
        """Test merge with update strategy."""
        store1 = InventoryStore(deal_id="test-deal")
        store1.add_item("application", {"name": "App1", "cost": 1000}, "target")

        store2 = InventoryStore(deal_id="test-deal")
        store2.add_item("application", {"name": "App1", "cost": 2000}, "target")  # Updated cost

        result = store1.merge_from(store2, strategy="update")

        assert result.updated == 1
        item = store1.find_by_name("App1")
        assert item.data["cost"] == 2000

    def test_add_from_table(self):
        """Test bulk add from table data."""
        store = InventoryStore(deal_id="test-deal")

        rows = [
            {"name": "App1", "vendor": "Vendor1", "cost": 10000},
            {"name": "App2", "vendor": "Vendor2", "cost": 20000},
            {"name": "App3", "vendor": "Vendor3", "cost": 30000},
        ]

        result = store.add_from_table(
            inventory_type="application",
            rows=rows,
            entity="target",
            source_file="apps.xlsx"
        )

        assert result.added == 3
        assert len(store) == 3
        assert store.sum_costs() == 60000.0


# =============================================================================
# Schema Tests
# =============================================================================

class TestSchemas:
    """Tests for inventory schemas."""

    def test_all_types_have_schemas(self):
        """All inventory types have defined schemas."""
        for inv_type in ["application", "infrastructure", "organization", "vendor"]:
            schema = get_schema(inv_type)
            assert "required" in schema
            assert "optional" in schema
            assert "id_fields" in schema

    def test_validate_inventory_type(self):
        """Test inventory type validation."""
        assert validate_inventory_type("application")
        assert validate_inventory_type("infrastructure")
        assert not validate_inventory_type("invalid")

    def test_id_fields_exist_in_schema(self):
        """ID fields should be in required or optional."""
        for inv_type, schema in INVENTORY_SCHEMAS.items():
            all_fields = schema["required"] + schema["optional"]
            for id_field in schema["id_fields"]:
                assert id_field in all_fields, f"{id_field} not in {inv_type} schema"


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests combining multiple components."""

    def test_full_workflow(self):
        """Test complete workflow: create, update, save, load, verify."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "inventory.json"

            # Create store and add items
            store = InventoryStore(deal_id="test-deal")

            app_id = store.add_item(
                "application",
                {
                    "name": "Duck Creek Policy",
                    "vendor": "Duck Creek Technologies",
                    "version": "12",
                    "cost": 546257,
                    "criticality": "critical",
                },
                "target",
                source_file="ToltIQ_Apps.xlsx"
            )

            infra_id = store.add_item(
                "infrastructure",
                {
                    "name": "prod-db-01",
                    "type": "vm",
                    "os": "RHEL 8",
                    "environment": "production",
                },
                "target",
                source_file="servers.csv"
            )

            # Update with enrichment
            app = store.get_item(app_id)
            app.set_enrichment(
                category="vertical_specific",
                note="Insurance policy administration system",
                confidence="high"
            )

            # Save
            store.save(path)

            # Load into new store
            store2 = InventoryStore(deal_id="test-deal")
            store2.load_from_file(path)

            # Verify
            assert len(store2) == 2

            app2 = store2.get_item(app_id)
            assert app2.name == "Duck Creek Policy"
            assert app2.cost == 546257.0
            assert app2.enrichment_category == "vertical_specific"

            infra2 = store2.get_item(infra_id)
            assert infra2.name == "prod-db-01"
            assert infra2.data["environment"] == "production"

    def test_reimport_workflow(self):
        """Test re-importing updated data."""
        store = InventoryStore(deal_id="test-deal")

        # Initial import
        rows_v1 = [
            {"name": "App1", "vendor": "Vendor1", "cost": 10000},
            {"name": "App2", "vendor": "Vendor2", "cost": 20000},
        ]
        store.add_from_table("application", rows_v1, "target", source_file="v1.xlsx")

        assert len(store) == 2

        # Updated import (App1 cost changed, App3 added)
        rows_v2 = [
            {"name": "App1", "vendor": "Vendor1", "cost": 15000},
            {"name": "App2", "vendor": "Vendor2", "cost": 20000},
            {"name": "App3", "vendor": "Vendor3", "cost": 30000},
        ]

        # Create new store for merge
        store2 = InventoryStore(deal_id="test-deal")
        store2.add_from_table("application", rows_v2, "target", source_file="v2.xlsx")

        # Merge with update strategy
        result = store.merge_from(store2, strategy="update")

        assert result.added == 1  # App3
        assert result.updated == 1  # App1 cost changed
        assert result.unchanged == 1  # App2

        assert len(store) == 3
        assert store.sum_costs() == 65000.0  # 15000 + 20000 + 30000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
