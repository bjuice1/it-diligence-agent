"""
Tests for Phase 3: App Ingestion & Category Mapping

Tests:
- App category mappings (lookup, categorize)
- Auto-categorization in file_router
- Category validation and normalization in enrichment
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


# =============================================================================
# APP CATEGORY MAPPINGS TESTS
# =============================================================================

class TestAppCategoryMappings:
    """Tests for stores/app_category_mappings.py"""

    def test_lookup_known_app_exact(self):
        """Known apps should be found with exact match."""
        from stores.app_category_mappings import lookup_app

        mapping = lookup_app("salesforce")
        assert mapping is not None
        assert mapping.category == "crm"
        assert mapping.vendor == "Salesforce"

    def test_lookup_known_app_case_insensitive(self):
        """Lookup should be case insensitive."""
        from stores.app_category_mappings import lookup_app

        mapping1 = lookup_app("SALESFORCE")
        mapping2 = lookup_app("SalesForce")
        mapping3 = lookup_app("salesforce")

        assert mapping1 is not None
        assert mapping2 is not None
        assert mapping3 is not None
        assert mapping1.category == mapping2.category == mapping3.category

    def test_lookup_by_alias(self):
        """Apps should be found by their aliases."""
        from stores.app_category_mappings import lookup_app

        # Office 365 is an alias for Microsoft 365
        mapping = lookup_app("office 365")
        assert mapping is not None
        assert mapping.category == "productivity"
        assert mapping.vendor == "Microsoft"

    def test_lookup_partial_match(self):
        """Partial matches should work."""
        from stores.app_category_mappings import lookup_app

        # "SAP ERP" starts with "sap"
        mapping = lookup_app("sap erp")
        assert mapping is not None
        assert mapping.category == "erp"

    def test_lookup_unknown_app(self):
        """Unknown apps without matches should return None."""
        from stores.app_category_mappings import lookup_app

        # Test with app that truly has no match (not "custom")
        mapping = lookup_app("CompleteLyUnknownApp123")
        assert mapping is None

        # Apps with "custom" in name should match the "custom" category (feature)
        custom_mapping = lookup_app("CustomInternalApp123")
        assert custom_mapping is not None
        assert custom_mapping.category == "custom"

    def test_categorize_known_app(self):
        """Known apps should return correct category."""
        from stores.app_category_mappings import categorize_app_simple

        category, mapping = categorize_app_simple("Workday")
        assert category == "hcm"
        assert mapping is not None
        assert mapping.vendor == "Workday"

    def test_categorize_unknown_app(self):
        """Unknown apps should return 'unknown' category, unless they match 'custom'."""
        from stores.app_category_mappings import categorize_app_simple

        # Truly unknown app (no matches at all)
        category, mapping = categorize_app_simple("CompletelyUnknownApp")
        assert category == "unknown"
        assert mapping is None

        # Apps with "custom" in name should match "custom" category (feature)
        category, mapping = categorize_app_simple("MyCustomApp")
        assert category == "custom"
        assert mapping is not None
        assert mapping.vendor == "Internal"

    def test_normalize_app_name_removes_version(self):
        """Version numbers should be stripped from app names."""
        from stores.app_category_mappings import normalize_app_name

        assert normalize_app_name("SAP 7.5") == "sap"
        assert normalize_app_name("Office 2019") == "office"
        assert normalize_app_name("App v2.1.0") == "app"

    def test_normalize_app_name_removes_company_suffixes(self):
        """Company suffixes should be removed."""
        from stores.app_category_mappings import normalize_app_name

        assert normalize_app_name("Acme Inc") == "acme"
        assert normalize_app_name("Company LLC") == "company"
        assert normalize_app_name("Corp Ltd") == "corp"

    def test_category_definitions_exist(self):
        """All categories should have definitions."""
        from stores.app_category_mappings import CATEGORY_DEFINITIONS, APP_MAPPINGS

        # Check that all categories in mappings are defined
        categories_used = set(m.category for m in APP_MAPPINGS.values())
        for cat in categories_used:
            assert cat in CATEGORY_DEFINITIONS, f"Category '{cat}' has no definition"

    def test_list_apps_by_category(self):
        """Should return apps filtered by category."""
        from stores.app_category_mappings import list_apps_by_category

        erp_apps = list_apps_by_category("erp")
        assert len(erp_apps) > 0
        assert "sap" in erp_apps

        crm_apps = list_apps_by_category("crm")
        assert len(crm_apps) > 0
        assert "salesforce" in crm_apps

    def test_get_all_known_apps(self):
        """Should return list of all known app names."""
        from stores.app_category_mappings import get_all_known_apps

        apps = get_all_known_apps()
        assert len(apps) > 100  # We have 106+ mappings
        assert "salesforce" in apps
        assert "sap" in apps

    def test_erp_category_apps(self):
        """ERP category should include expected apps."""
        from stores.app_category_mappings import lookup_app

        erp_apps = ["sap", "netsuite", "oracle e-business suite", "epicor"]
        for app in erp_apps:
            mapping = lookup_app(app)
            assert mapping is not None, f"{app} not found"
            assert mapping.category == "erp", f"{app} should be ERP"

    def test_crm_category_apps(self):
        """CRM category should include expected apps."""
        from stores.app_category_mappings import lookup_app

        crm_apps = ["salesforce", "hubspot", "zoho crm", "pipedrive"]
        for app in crm_apps:
            mapping = lookup_app(app)
            assert mapping is not None, f"{app} not found"
            assert mapping.category == "crm", f"{app} should be CRM"

    def test_security_category_apps(self):
        """Security category should include expected apps."""
        from stores.app_category_mappings import lookup_app

        security_apps = ["okta", "crowdstrike", "zscaler", "cyberark"]
        for app in security_apps:
            mapping = lookup_app(app)
            assert mapping is not None, f"{app} not found"
            assert mapping.category == "security", f"{app} should be Security"


# =============================================================================
# FILE ROUTER AUTO-CATEGORIZATION TESTS
# =============================================================================

class TestFileRouterAutoCategorization:
    """Tests for auto-categorization in tools_v2/file_router.py"""

    def test_auto_categorize_known_app(self):
        """Known apps should be auto-categorized."""
        from tools_v2.file_router import _auto_categorize_app

        data = {"name": "Salesforce", "users": "500"}
        updated, was_categorized = _auto_categorize_app(data)

        assert was_categorized is True
        assert updated["category"] == "crm"
        assert updated["vendor"] == "Salesforce"
        assert updated["_auto_categorized"] is True

    def test_auto_categorize_unknown_app(self):
        """Unknown apps should not be categorized."""
        from tools_v2.file_router import _auto_categorize_app

        data = {"name": "MyCustomApp", "users": "50"}
        updated, was_categorized = _auto_categorize_app(data)

        assert was_categorized is False
        assert "category" not in updated or updated.get("category") is None

    def test_auto_categorize_preserves_existing_category(self):
        """Existing category should not be overwritten."""
        from tools_v2.file_router import _auto_categorize_app

        data = {"name": "Salesforce", "category": "custom_crm"}
        updated, was_categorized = _auto_categorize_app(data)

        # Should still mark as categorized (vendor might be added)
        # But category should remain as provided
        assert updated["category"] == "custom_crm"

    def test_auto_categorize_preserves_existing_vendor(self):
        """Existing vendor should not be overwritten."""
        from tools_v2.file_router import _auto_categorize_app

        data = {"name": "Salesforce", "vendor": "Custom Vendor"}
        updated, was_categorized = _auto_categorize_app(data)

        assert updated["vendor"] == "Custom Vendor"

    def test_auto_categorize_empty_name(self):
        """Empty name should not cause errors."""
        from tools_v2.file_router import _auto_categorize_app

        data = {"name": "", "users": "50"}
        updated, was_categorized = _auto_categorize_app(data)

        assert was_categorized is False

    def test_auto_categorize_missing_name(self):
        """Missing name field should not cause errors."""
        from tools_v2.file_router import _auto_categorize_app

        data = {"users": "50"}
        updated, was_categorized = _auto_categorize_app(data)

        assert was_categorized is False


# =============================================================================
# ENRICHMENT CATEGORY VALIDATION TESTS
# =============================================================================

class TestEnrichmentCategoryValidation:
    """Tests for category validation in tools_v2/enrichment/inventory_reviewer.py"""

    def test_validate_category_valid(self):
        """Valid categories should return True."""
        from tools_v2.enrichment.inventory_reviewer import validate_category

        valid_categories = ["erp", "crm", "hcm", "security", "infrastructure"]
        for cat in valid_categories:
            assert validate_category(cat) is True, f"{cat} should be valid"

    def test_validate_category_case_insensitive(self):
        """Validation should be case insensitive."""
        from tools_v2.enrichment.inventory_reviewer import validate_category

        assert validate_category("ERP") is True
        assert validate_category("Crm") is True
        assert validate_category("SECURITY") is True

    def test_validate_category_invalid(self):
        """Invalid categories should return False."""
        from tools_v2.enrichment.inventory_reviewer import validate_category

        assert validate_category("invalid_category") is False
        assert validate_category("not_a_category") is False

    def test_validate_category_empty(self):
        """Empty/None categories should return False."""
        from tools_v2.enrichment.inventory_reviewer import validate_category

        assert validate_category("") is False
        assert validate_category(None) is False

    def test_normalize_category_direct_match(self):
        """Direct matches should be normalized to lowercase."""
        from tools_v2.enrichment.inventory_reviewer import normalize_category

        assert normalize_category("ERP") == "erp"
        assert normalize_category("CRM") == "crm"

    def test_normalize_category_aliases(self):
        """Category aliases should be normalized."""
        from tools_v2.enrichment.inventory_reviewer import normalize_category

        # HR variants -> hcm
        assert normalize_category("HR") == "hcm"
        assert normalize_category("human resources") == "hcm"
        assert normalize_category("payroll") == "hcm"

        # Finance variants -> finance
        assert normalize_category("accounting") == "finance"
        assert normalize_category("accounts payable") == "finance"

        # Cloud variants -> infrastructure
        assert normalize_category("cloud") == "infrastructure"

    def test_normalize_category_unknown(self):
        """Unknown categories should normalize to 'unknown'."""
        from tools_v2.enrichment.inventory_reviewer import normalize_category

        assert normalize_category("random_string") == "unknown"
        assert normalize_category("not_a_category") == "unknown"

    def test_normalize_category_empty(self):
        """Empty categories should normalize to 'unknown'."""
        from tools_v2.enrichment.inventory_reviewer import normalize_category

        assert normalize_category("") == "unknown"
        assert normalize_category(None) == "unknown"

    def test_suggest_category_known_app(self):
        """Known apps should get category suggestions."""
        from tools_v2.enrichment.inventory_reviewer import suggest_category

        assert suggest_category("Salesforce") == "crm"
        assert suggest_category("SAP") == "erp"
        assert suggest_category("Workday") == "hcm"

    def test_suggest_category_unknown_app(self):
        """Truly unknown apps should return None, but 'custom' apps should match."""
        from tools_v2.enrichment.inventory_reviewer import suggest_category

        # Truly unknown app
        assert suggest_category("CompletelyUnknownApp") is None

        # Apps with "custom" should match the "custom" category (feature)
        category = suggest_category("MyCustomApp")
        assert category == "custom"


# =============================================================================
# ENRICHMENT LOCAL LOOKUP TESTS
# =============================================================================

class TestEnrichmentLocalLookup:
    """Tests for local lookup in enrichment."""

    def test_try_local_lookup_known_app(self):
        """Known apps should be enriched from local mappings."""
        from tools_v2.enrichment.inventory_reviewer import _try_local_lookup
        from stores.inventory_item import InventoryItem

        item = InventoryItem(
            item_id="APP-001",
            inventory_type="application",
            entity="target",
            data={"name": "Salesforce", "users": "500"},
        )

        review = _try_local_lookup(item)

        assert review is not None
        assert review.item_id == "APP-001"
        assert review.category == "crm"
        assert review.vendor_info == "Salesforce"
        assert review.is_confident is True
        assert review.needs_investigation is False

    def test_try_local_lookup_unknown_app(self):
        """Unknown apps should return None from local lookup."""
        from tools_v2.enrichment.inventory_reviewer import _try_local_lookup
        from stores.inventory_item import InventoryItem

        item = InventoryItem(
            item_id="APP-002",
            inventory_type="application",
            entity="target",
            data={"name": "CustomInternalTool", "users": "50"},
        )

        review = _try_local_lookup(item)

        assert review is None

    def test_try_local_lookup_empty_name(self):
        """Items with empty names should return None."""
        from tools_v2.enrichment.inventory_reviewer import _try_local_lookup
        from stores.inventory_item import InventoryItem

        item = InventoryItem(
            item_id="APP-003",
            inventory_type="application",
            entity="target",
            data={"users": "50"},  # No name field
        )

        review = _try_local_lookup(item)

        assert review is None


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestAppCategorizationIntegration:
    """Integration tests for app categorization flow."""

    def test_full_categorization_flow(self):
        """Test complete flow: lookup -> categorize -> validate."""
        from stores.app_category_mappings import lookup_app, categorize_app_simple
        from tools_v2.enrichment.inventory_reviewer import validate_category

        # Lookup known app
        mapping = lookup_app("Microsoft Teams")
        assert mapping is not None

        # Get category
        category, _ = categorize_app_simple("Microsoft Teams")
        assert category == "collaboration"

        # Validate category
        assert validate_category(category) is True

    def test_categorization_coverage(self):
        """Common enterprise apps should all be categorized."""
        from stores.app_category_mappings import lookup_app

        # Common enterprise apps that should be in the mappings
        common_apps = [
            "Salesforce", "SAP", "Workday", "Microsoft 365",
            "Slack", "Zoom", "Okta", "ServiceNow", "Jira",
            "AWS", "Azure", "VMware", "Oracle", "SQL Server",
        ]

        for app in common_apps:
            mapping = lookup_app(app)
            assert mapping is not None, f"Common app '{app}' should be in mappings"

    def test_vendor_variety(self):
        """Mappings should cover major vendors."""
        from stores.app_category_mappings import APP_MAPPINGS

        vendors = set(m.vendor for m in APP_MAPPINGS.values())

        major_vendors = [
            "Microsoft", "Salesforce", "Oracle", "SAP",
            "Google", "Amazon", "VMware", "Atlassian",
        ]

        for vendor in major_vendors:
            assert vendor in vendors, f"Major vendor '{vendor}' should be represented"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
