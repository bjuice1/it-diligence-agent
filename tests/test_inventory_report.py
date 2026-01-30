"""
Tests for Phase 5: Inventory Report Generation

Tests:
1. Inventory section building
2. Application table formatting
3. Infrastructure table formatting
4. Flagged items section
5. Stat cards and navigation
"""

import pytest
from stores.inventory_store import InventoryStore
from tools_v2.inventory_report import (
    build_inventory_section,
    build_inventory_nav_link,
    build_inventory_stat_card,
    _build_applications_table,
    _build_infrastructure_table,
    _build_flagged_section,
    _criticality_badge,
    _environment_badge,
    get_inventory_styles,
)


class TestInventoryNavigation:
    """Tests for navigation elements."""

    def test_nav_link_shows_count(self):
        """Nav link should show total inventory count."""
        store = InventoryStore()
        store.add_item(
            inventory_type="application",
            data={"name": "App1"},
            entity="target",
            source_file="test.xlsx",
        )
        store.add_item(
            inventory_type="application",
            data={"name": "App2"},
            entity="target",
            source_file="test.xlsx",
        )

        nav_html = build_inventory_nav_link(store)

        assert "Inventory (2)" in nav_html
        assert 'href="#inventory"' in nav_html

    def test_stat_card_shows_counts(self):
        """Stat card should show item count and flagged count."""
        store = InventoryStore()

        # Add regular item
        store.add_item(
            inventory_type="application",
            data={"name": "App1"},
            entity="target",
            source_file="test.xlsx",
        )

        # Add flagged item
        item_id = store.add_item(
            inventory_type="application",
            data={"name": "Unknown App"},
            entity="target",
            source_file="test.xlsx",
        )
        item = store.get_item(item_id)
        item.set_enrichment(
            category="unknown",
            note="Cannot identify",
            confidence="low",
            flag="investigate",
        )

        stat_html = build_inventory_stat_card(store)

        assert "2" in stat_html  # Total count
        assert "flagged" in stat_html.lower()


class TestApplicationsTable:
    """Tests for applications table generation."""

    def test_table_includes_item_id(self):
        """Table should include item ID for reference."""
        store = InventoryStore()
        item_id = store.add_item(
            inventory_type="application",
            data={"name": "Salesforce", "vendor": "Salesforce"},
            entity="target",
            source_file="test.xlsx",
        )

        items = store.get_items(inventory_type="application")
        html = _build_applications_table(items)

        assert item_id in html
        assert "Salesforce" in html

    def test_table_shows_cost(self):
        """Table should format costs correctly."""
        store = InventoryStore()
        store.add_item(
            inventory_type="application",
            data={"name": "SAP", "cost": 150000},
            entity="target",
            source_file="test.xlsx",
        )

        items = store.get_items(inventory_type="application")
        html = _build_applications_table(items)

        assert "$150,000" in html

    def test_table_shows_enrichment_indicator(self):
        """Enriched items should show info indicator."""
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

        items = store.get_items(inventory_type="application")
        html = _build_applications_table(items)

        assert "ℹ️" in html or "tooltip" in html

    def test_table_shows_investigate_badge(self):
        """Flagged items should show investigate badge."""
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
            note="Unknown",
            confidence="low",
            flag="investigate",
        )

        items = store.get_items(inventory_type="application")
        html = _build_applications_table(items)

        assert "Investigate" in html


class TestInfrastructureTable:
    """Tests for infrastructure table generation."""

    def test_table_includes_fields(self):
        """Table should include key infrastructure fields."""
        store = InventoryStore()
        store.add_item(
            inventory_type="infrastructure",
            data={
                "name": "web-01",
                "type": "Web Server",
                "os": "Ubuntu 22.04",
                "environment": "production",
                "location": "AWS us-east-1",
            },
            entity="target",
            source_file="test.xlsx",
        )

        items = store.get_items(inventory_type="infrastructure")
        html = _build_infrastructure_table(items)

        assert "web-01" in html
        assert "Ubuntu" in html
        assert "production" in html

    def test_environment_badge_colors(self):
        """Environment badges should be color-coded."""
        # Production - green
        prod_badge = _environment_badge("production")
        assert "#166534" in prod_badge or "green" in prod_badge.lower()

        # Dev - blue
        dev_badge = _environment_badge("development")
        assert "#1e40af" in dev_badge or "blue" in dev_badge.lower()


class TestFlaggedSection:
    """Tests for flagged items section."""

    def test_flagged_section_lists_items(self):
        """Flagged section should list all flagged items."""
        store = InventoryStore()

        for i in range(3):
            item_id = store.add_item(
                inventory_type="application",
                data={"name": f"Unknown App {i}"},
                entity="target",
                source_file="test.xlsx",
            )
            item = store.get_item(item_id)
            item.set_enrichment(
                category="unknown",
                note="Cannot identify",
                confidence="low",
                flag="investigate",
            )

        flagged = [i for i in store.get_items() if i.needs_investigation]
        html = _build_flagged_section(flagged)

        assert "Unknown App 0" in html
        assert "Unknown App 1" in html
        assert "Unknown App 2" in html
        assert "3" in html  # Count

    def test_empty_flagged_returns_empty(self):
        """Empty flagged list should return empty string."""
        html = _build_flagged_section([])
        assert html == ""


class TestCriticalityBadge:
    """Tests for criticality badge generation."""

    def test_critical_badge_is_red(self):
        """Critical badge should be red."""
        badge = _criticality_badge("critical")
        assert "#dc2626" in badge  # Red color

    def test_high_badge_is_orange(self):
        """High badge should be orange."""
        badge = _criticality_badge("high")
        assert "#ea580c" in badge  # Orange color

    def test_empty_returns_dash(self):
        """Empty criticality should return dash."""
        badge = _criticality_badge("")
        assert badge == "—"


class TestFullInventorySection:
    """Tests for complete inventory section."""

    def test_section_has_all_subsections(self):
        """Section should include all inventory types."""
        store = InventoryStore()

        store.add_item(
            inventory_type="application",
            data={"name": "App1"},
            entity="target",
            source_file="test.xlsx",
        )
        store.add_item(
            inventory_type="infrastructure",
            data={"name": "Server1"},
            entity="target",
            source_file="test.xlsx",
        )

        html = build_inventory_section(store, "target")

        assert "Applications" in html
        assert "Infrastructure" in html
        assert "Organization" in html
        assert "Vendor Contracts" in html
        assert 'id="inventory"' in html

    def test_section_shows_summary_stats(self):
        """Section should show summary statistics."""
        store = InventoryStore()

        for i in range(5):
            store.add_item(
                inventory_type="application",
                data={"name": f"App{i}", "cost": 10000},
                entity="target",
                source_file="test.xlsx",
            )

        html = build_inventory_section(store, "target")

        assert "5" in html  # App count
        assert "$50,000" in html  # Total cost

    def test_styles_include_required_classes(self):
        """CSS styles should include all required classes."""
        styles = get_inventory_styles()

        assert ".mini-stat" in styles
        assert ".badge" in styles
        assert ".tooltip" in styles


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
