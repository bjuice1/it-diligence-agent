"""Tests for category mapping: vertical categories, default fallback, provenance.

Spec 02: Validates categorize_app, categorize_app_simple, vertical mappings,
default fallback behavior, and confidence/source tracking.
"""
import pytest

from stores.app_category_mappings import (
    categorize_app,
    categorize_app_simple,
    lookup_app,
    normalize_app_name,
)


class TestVerticalMappings:
    """Verify new vertical/industry applications resolve correctly."""

    @pytest.mark.parametrize("app_name,expected_category", [
        # Insurance
        ("Duck Creek", "industry_vertical"),
        ("Guidewire", "industry_vertical"),
        ("Majesco", "industry_vertical"),
        ("Vertafore AMS360", "industry_vertical"),
        ("Applied Epic", "industry_vertical"),
        ("Sapiens", "industry_vertical"),
        # Healthcare
        ("Epic", "industry_vertical"),
        ("Cerner", "industry_vertical"),
        ("eClinicalWorks", "industry_vertical"),
        ("NextGen Healthcare", "industry_vertical"),
        # Manufacturing
        ("Rockwell Automation", "industry_vertical"),
        ("AVEVA", "industry_vertical"),
        ("Plex", "industry_vertical"),
        # Retail
        ("Manhattan Associates", "industry_vertical"),
        ("Blue Yonder", "industry_vertical"),
    ])
    def test_vertical_app_categorization(self, app_name, expected_category):
        cat, mapping, conf, src = categorize_app(app_name)
        assert cat == expected_category, f"{app_name} should be {expected_category}, got {cat}"
        assert conf in ("high", "medium"), f"{app_name} confidence should be high/medium, got {conf}"

    def test_existing_mappings_unchanged(self):
        """Regression: existing ERP, CRM, etc. mappings still work."""
        assert categorize_app("SAP")[0] == "erp"
        assert categorize_app("Salesforce")[0] == "crm"
        assert categorize_app("Workday")[0] == "hcm"
        assert categorize_app("Okta")[0] == "security"
        assert categorize_app("AWS")[0] == "infrastructure"


class TestDefaultFallback:
    """Verify unmapped apps default to 'unknown', not 'saas'."""

    def test_unmapped_app_is_unknown(self):
        cat, mapping, conf, src = categorize_app("Totally Custom Internal Tool XYZ123")
        assert cat == "unknown"
        assert mapping is None
        assert conf == "none"
        assert src == "default"

    def test_saas_not_default(self):
        """No app should get 'saas' unless explicitly mapped."""
        cat, _, _, _ = categorize_app("RandomUnknownApp987654")
        assert cat != "saas"


class TestCategoryProvenance:
    """Verify confidence and source tracking."""

    def test_exact_match_high_confidence(self):
        """Direct key match in APP_MAPPINGS should be high confidence."""
        cat, mapping, conf, src = categorize_app("Oracle Database")
        assert conf == "high"
        assert src in ("mapping_exact", "mapping_alias")

    def test_alias_match_high_confidence(self):
        """Alias match should also be high confidence."""
        cat, mapping, conf, src = categorize_app("Oracle EBS")
        assert conf == "high"
        assert src == "mapping_alias"

    def test_partial_match_medium_confidence(self):
        """Partial match should yield medium confidence."""
        cat, mapping, conf, src = categorize_app("Oracle Database Enterprise 19c")
        assert conf == "medium"
        assert src == "mapping_partial"

    def test_no_match_none_confidence(self):
        """No match should yield none confidence and default source."""
        cat, mapping, conf, src = categorize_app("XYZCorp Proprietary Tool v3.2")
        assert conf == "none"
        assert src == "default"


class TestBackwardsCompatibility:
    """Verify categorize_app_simple() wrapper works for legacy callers."""

    def test_simple_returns_two_values(self):
        cat, mapping = categorize_app_simple("SAP")
        assert cat == "erp"
        assert mapping is not None

    def test_simple_unknown_returns_none_mapping(self):
        cat, mapping = categorize_app_simple("UnknownApp123")
        assert cat == "unknown"
        assert mapping is None

    def test_categorize_app_returns_four_values(self):
        """Full categorize_app should return 4 values (category, mapping, confidence, source)."""
        result = categorize_app("SAP")
        assert len(result) == 4
        cat, mapping, conf, src = result
        assert isinstance(cat, str)
        assert conf in ("high", "medium", "low", "none")
        assert src in ("mapping_exact", "mapping_alias", "mapping_partial", "keyword_inference", "default")


class TestNormalizeAppName:
    """Verify app name normalization for consistent matching."""

    def test_lowercase(self):
        assert normalize_app_name("SAP") == "sap"

    def test_strip_version(self):
        """Version numbers at the end should be stripped."""
        assert normalize_app_name("SAP 7.5") == "sap"

    def test_strip_company_suffix(self):
        assert normalize_app_name("Oracle Corp") == "oracle"

    def test_strip_year(self):
        assert normalize_app_name("Office 2019") == "office"

    def test_empty_string(self):
        assert normalize_app_name("") == ""
