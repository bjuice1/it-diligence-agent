"""
Tests for Phase 4: Inventory Integration

Tests:
1. Get inventory for domain
2. Format inventory for agents
3. Sync inventory to facts
4. Link findings to inventory
5. Inventory summary
"""

import pytest
from stores.inventory_store import InventoryStore
from stores.fact_store import FactStore
from tools_v2.inventory_integration import (
    get_inventory_for_domain,
    format_inventory_for_agent,
    sync_inventory_to_facts,
    link_finding_to_inventory,
    get_inventory_summary,
    INVENTORY_TO_DOMAIN,
    DOMAIN_TO_INVENTORY,
)


class TestInventoryToDomain:
    """Tests for inventory-domain mapping."""

    def test_application_maps_to_applications_domain(self):
        """Application inventory maps to applications domain."""
        assert INVENTORY_TO_DOMAIN["application"] == "applications"

    def test_infrastructure_maps_to_infrastructure_domain(self):
        """Infrastructure inventory maps to infrastructure domain."""
        assert INVENTORY_TO_DOMAIN["infrastructure"] == "infrastructure"

    def test_applications_domain_includes_both_types(self):
        """Applications domain includes both application and vendor."""
        assert "application" in DOMAIN_TO_INVENTORY["applications"]
        assert "vendor" in DOMAIN_TO_INVENTORY["applications"]


class TestGetInventoryForDomain:
    """Tests for getting inventory by domain."""

    def test_get_applications_domain(self):
        """Should get application and vendor inventory for applications domain."""
        store = InventoryStore()

        # Add application
        store.add_item(
            inventory_type="application",
            data={"name": "Salesforce", "vendor": "Salesforce"},
            entity="target",
            source_file="test.xlsx",
        )

        # Add vendor
        store.add_item(
            inventory_type="vendor",
            data={"name": "AWS Contract", "vendor_name": "Amazon"},
            entity="target",
            source_file="test.xlsx",
        )

        # Add infrastructure (should not be included)
        store.add_item(
            inventory_type="infrastructure",
            data={"name": "web-01", "os": "Ubuntu"},
            entity="target",
            source_file="test.xlsx",
        )

        context = get_inventory_for_domain(store, "applications", "target")

        assert context.item_count == 2
        assert context.domain == "applications"

    def test_get_infrastructure_domain(self):
        """Should get infrastructure inventory."""
        store = InventoryStore()

        store.add_item(
            inventory_type="infrastructure",
            data={"name": "db-01", "os": "RHEL"},
            entity="target",
            source_file="test.xlsx",
        )

        context = get_inventory_for_domain(store, "infrastructure", "target")

        assert context.item_count == 1

    def test_empty_domain(self):
        """Should handle empty inventory gracefully."""
        store = InventoryStore()

        context = get_inventory_for_domain(store, "applications", "target")

        assert context.item_count == 0
        assert "No applications inventory items" in context.formatted_text


class TestFormatInventoryForAgent:
    """Tests for formatting inventory text."""

    def test_format_includes_item_id(self):
        """Formatted text should include item IDs for citation."""
        store = InventoryStore()

        item_id = store.add_item(
            inventory_type="application",
            data={"name": "SAP ERP", "vendor": "SAP", "version": "S/4HANA"},
            entity="target",
            source_file="test.xlsx",
        )

        item = store.get_item(item_id)
        text = format_inventory_for_agent([item], "applications")

        assert item_id in text
        assert "SAP ERP" in text
        assert "S/4HANA" in text

    def test_format_includes_enrichment(self):
        """Formatted text should include enrichment notes."""
        store = InventoryStore()

        item_id = store.add_item(
            inventory_type="application",
            data={"name": "Duck Creek"},
            entity="target",
            source_file="test.xlsx",
        )

        item = store.get_item(item_id)
        item.set_enrichment(
            category="industry_standard",
            note="Insurance policy administration platform",
            confidence="high",
        )

        text = format_inventory_for_agent([item], "applications")

        assert "Insurance policy administration" in text

    def test_format_flags_investigation(self):
        """Flagged items should be marked."""
        store = InventoryStore()

        item_id = store.add_item(
            inventory_type="application",
            data={"name": "Custom Tool"},
            entity="target",
            source_file="test.xlsx",
        )

        item = store.get_item(item_id)
        item.set_enrichment(
            category="unknown",
            note="Unknown application",
            confidence="low",
            flag="investigate",
        )

        text = format_inventory_for_agent([item], "applications")

        assert "FLAGGED" in text or "investigation" in text.lower()


class TestSyncInventoryToFacts:
    """Tests for syncing inventory to fact store."""

    def test_sync_creates_facts(self):
        """Sync should create facts from inventory items."""
        inventory = InventoryStore()
        facts = FactStore()

        inventory.add_item(
            inventory_type="application",
            data={"name": "Workday", "vendor": "Workday"},
            entity="target",
            source_file="test.xlsx",
        )

        stats = sync_inventory_to_facts(inventory, facts, entity="target")

        assert stats["synced"] == 1
        # Check facts were created
        all_facts = facts.get_entity_facts("target")
        assert len(all_facts) > 0

    def test_sync_includes_inventory_id_in_evidence(self):
        """Synced facts should reference inventory ID."""
        inventory = InventoryStore()
        facts = FactStore()

        item_id = inventory.add_item(
            inventory_type="application",
            data={"name": "ServiceNow"},
            entity="target",
            source_file="test.xlsx",
        )

        sync_inventory_to_facts(inventory, facts, entity="target")

        # Find the created fact by searching all facts
        all_facts = facts.get_entity_facts("target")
        service_now_fact = None
        for fact in all_facts:
            if fact.item == "ServiceNow":
                service_now_fact = fact
                break

        assert service_now_fact is not None
        assert service_now_fact.evidence.get("inventory_id") == item_id

    def test_sync_skips_duplicates(self):
        """Sync should skip items already in fact store."""
        inventory = InventoryStore()
        facts = FactStore()

        inventory.add_item(
            inventory_type="application",
            data={"name": "Jira"},
            entity="target",
            source_file="test.xlsx",
        )

        # First sync
        stats1 = sync_inventory_to_facts(inventory, facts, entity="target")
        assert stats1["synced"] == 1

        # Second sync should skip
        stats2 = sync_inventory_to_facts(inventory, facts, entity="target")
        assert stats2["skipped"] == 1
        assert stats2["synced"] == 0


class TestLinkFindingToInventory:
    """Tests for linking findings to inventory items."""

    def test_link_by_item_id(self):
        """Should link finding that mentions item ID."""
        store = InventoryStore()

        item_id = store.add_item(
            inventory_type="application",
            data={"name": "Legacy App"},
            entity="target",
            source_file="test.xlsx",
        )

        finding = {
            "description": f"The application {item_id} needs to be migrated."
        }

        linked = link_finding_to_inventory(finding, store)

        assert "inventory_links" in linked
        assert len(linked["inventory_links"]) == 1
        assert linked["inventory_links"][0]["item_id"] == item_id

    def test_link_by_name(self):
        """Should link finding that mentions item name."""
        store = InventoryStore()

        store.add_item(
            inventory_type="application",
            data={"name": "Salesforce CRM"},
            entity="target",
            source_file="test.xlsx",
        )

        finding = {
            "description": "Salesforce CRM integration requires attention."
        }

        linked = link_finding_to_inventory(finding, store)

        assert "inventory_links" in linked
        assert len(linked["inventory_links"]) == 1

    def test_no_links_when_no_match(self):
        """Should not add links when no inventory matches."""
        store = InventoryStore()

        store.add_item(
            inventory_type="application",
            data={"name": "App1"},
            entity="target",
            source_file="test.xlsx",
        )

        finding = {
            "description": "Generic finding about something else."
        }

        linked = link_finding_to_inventory(finding, store)

        assert "inventory_links" not in linked


class TestGetInventorySummary:
    """Tests for inventory summary generation."""

    def test_summary_includes_counts(self):
        """Summary should include item counts by type."""
        store = InventoryStore()

        for i in range(3):
            store.add_item(
                inventory_type="application",
                data={"name": f"App{i}"},
                entity="target",
                source_file="test.xlsx",
            )

        store.add_item(
            inventory_type="infrastructure",
            data={"name": "Server1"},
            entity="target",
            source_file="test.xlsx",
        )

        summary = get_inventory_summary(store, entity="target")

        assert summary["totals"]["application"]["count"] == 3
        assert summary["totals"]["infrastructure"]["count"] == 1

    def test_summary_highlights_high_cost(self):
        """Summary should highlight high-cost applications."""
        store = InventoryStore()

        store.add_item(
            inventory_type="application",
            data={"name": "SAP ERP", "cost": 200000},
            entity="target",
            source_file="test.xlsx",
        )

        summary = get_inventory_summary(store, entity="target")

        # Check for high-cost highlight
        highlight_text = " ".join(summary["highlights"])
        assert "SAP ERP" in highlight_text or "High-cost" in highlight_text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
