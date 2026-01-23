"""
Tests for Phase 2-3: Unknown/N/A Handling

Run with: pytest tests/test_phase_2_3_unknown_handling.py -v
"""
import pytest
from tools.analysis_tools import (
    AnalysisStore,
    # Enums to test
    BUYER_APP_SOURCE,
    COVERAGE_STATUS,
    BUSINESS_RELEVANCE,
    QUESTION_TARGETS,
    HOSTING_MODELS,
    SUPPORT_STATUS,
    LICENSE_TYPES,
    CUSTOMIZATION_LEVELS,
    BUSINESS_CRITICALITY,
    DATA_RESIDENCY_LOCATIONS,
    OVERLAP_TYPES,
    CAPABILITY_MATURITY,
    INTEGRATION_COMPLEXITY
)


class TestEnumsHaveUnknown:
    """Test that all relevant enums include Unknown value."""

    def test_buyer_app_source_has_unknown(self):
        """Verify BUYER_APP_SOURCE includes Unknown."""
        assert "Unknown" in BUYER_APP_SOURCE

    def test_coverage_status_has_unknown(self):
        """Verify COVERAGE_STATUS includes Unknown."""
        assert "Unknown" in COVERAGE_STATUS

    def test_business_relevance_has_unknown(self):
        """Verify BUSINESS_RELEVANCE includes Unknown."""
        assert "Unknown" in BUSINESS_RELEVANCE

    def test_question_targets_has_unknown(self):
        """Verify QUESTION_TARGETS includes Unknown."""
        assert "Unknown" in QUESTION_TARGETS

    def test_hosting_models_has_unknown(self):
        """Verify HOSTING_MODELS includes Unknown."""
        assert "Unknown" in HOSTING_MODELS

    def test_support_status_has_unknown(self):
        """Verify SUPPORT_STATUS includes Unknown."""
        assert "Unknown" in SUPPORT_STATUS

    def test_license_types_has_unknown(self):
        """Verify LICENSE_TYPES includes Unknown."""
        assert "Unknown" in LICENSE_TYPES

    def test_customization_levels_has_unknown(self):
        """Verify CUSTOMIZATION_LEVELS includes Unknown."""
        assert "Unknown" in CUSTOMIZATION_LEVELS

    def test_business_criticality_has_unknown(self):
        """Verify BUSINESS_CRITICALITY includes Unknown."""
        assert "Unknown" in BUSINESS_CRITICALITY

    def test_data_residency_has_unknown(self):
        """Verify DATA_RESIDENCY_LOCATIONS includes Unknown."""
        assert "Unknown" in DATA_RESIDENCY_LOCATIONS

    def test_overlap_types_has_unknown(self):
        """Verify OVERLAP_TYPES includes Unknown."""
        assert "Unknown" in OVERLAP_TYPES

    def test_capability_maturity_has_unknown(self):
        """Verify CAPABILITY_MATURITY includes Unknown."""
        assert "Unknown" in CAPABILITY_MATURITY

    def test_integration_complexity_has_unknown(self):
        """Verify INTEGRATION_COMPLEXITY includes Unknown."""
        assert "Unknown" in INTEGRATION_COMPLEXITY


class TestFieldsNotDocumented:
    """Test the fields_not_documented pattern in record_application."""

    @pytest.fixture
    def store(self):
        """Fresh AnalysisStore for each test."""
        return AnalysisStore()

    def test_record_application_with_fields_not_documented(self, store):
        """Test recording an application with explicit fields_not_documented."""
        result = store.execute_tool("record_application", {
            "application_name": "Test App",
            "application_category": "CRM",
            "vendor": "TestVendor",
            "hosting_model": "SaaS",
            "business_criticality": "High",
            "discovery_source": "App_Inventory_Document",
            "source_evidence": {
                "exact_quote": "Test App is a CRM system",
                "evidence_type": "direct_statement",
                "confidence_level": "high"
            },
            "fields_not_documented": ["version", "user_count", "license_type"]
        })

        assert result["status"] == "recorded"

        # Verify fields_not_documented is stored
        apps = store.get_application_inventory()
        assert len(apps) == 1
        assert apps[0]["fields_not_documented"] == ["version", "user_count", "license_type"]

    def test_record_application_defaults_empty_fields_not_documented(self, store):
        """Test that fields_not_documented defaults to empty list."""
        result = store.execute_tool("record_application", {
            "application_name": "Another App",
            "application_category": "ERP",
            "vendor": "AnotherVendor",
            "hosting_model": "On_Premise",
            "business_criticality": "Critical",
            "discovery_source": "App_Inventory_Document",
            "source_evidence": {
                "exact_quote": "Another App is the ERP",
                "evidence_type": "direct_statement",
                "confidence_level": "high"
            }
        })

        assert result["status"] == "recorded"

        apps = store.get_application_inventory()
        assert len(apps) == 1
        assert apps[0]["fields_not_documented"] == []

    def test_record_application_with_unknown_values(self, store):
        """Test recording an application with Unknown enum values."""
        result = store.execute_tool("record_application", {
            "application_name": "Partial Info App",
            "application_category": "Other",
            "vendor": "SomeVendor",
            "hosting_model": "Unknown",
            "business_criticality": "Unknown",
            "support_status": "Unknown",
            "customization_level": "Unknown",
            "discovery_source": "Mentioned_In_Passing",
            "source_evidence": {
                "exact_quote": "data flows from Partial Info App",
                "evidence_type": "direct_statement",
                "confidence_level": "medium"
            },
            "fields_not_documented": ["version", "user_count", "license_type", "contract_expiry"]
        })

        assert result["status"] == "recorded"

        apps = store.get_application_inventory()
        assert len(apps) == 1
        assert apps[0]["hosting_model"] == "Unknown"
        assert apps[0]["business_criticality"] == "Unknown"


class TestCompletenessMetrics:
    """Test the application completeness metrics."""

    @pytest.fixture
    def store(self):
        """Fresh AnalysisStore for each test."""
        return AnalysisStore()

    def test_completeness_metrics_no_apps(self, store):
        """Test metrics when no applications recorded."""
        metrics = store.get_application_completeness_metrics()

        assert metrics["status"] == "no_applications"
        assert metrics["total_applications"] == 0
        assert metrics["completeness_score"] == 0.0

    def test_completeness_metrics_with_documented_fields(self, store):
        """Test metrics with well-documented application."""
        store.execute_tool("record_application", {
            "application_name": "Well Documented App",
            "application_category": "ERP",
            "vendor": "SAP",
            "hosting_model": "On_Premise",
            "business_criticality": "Critical",
            "discovery_source": "App_Inventory_Document",
            "version": "ECC 6.0",
            "user_count": "500",
            "license_type": "Perpetual",
            "support_status": "Extended_Support",
            "customization_level": "Heavily_Customized",
            "source_evidence": {
                "exact_quote": "SAP ECC 6.0 with 500 users",
                "evidence_type": "direct_statement",
                "confidence_level": "high"
            }
        })

        metrics = store.get_application_completeness_metrics()

        assert metrics["status"] == "analyzed"
        assert metrics["total_applications"] == 1
        assert metrics["completeness_score"] > 0

    def test_completeness_metrics_with_undocumented_fields(self, store):
        """Test metrics with application missing many fields."""
        store.execute_tool("record_application", {
            "application_name": "Minimal App",
            "application_category": "Other",
            "vendor": "Unknown Vendor",
            "hosting_model": "Unknown",
            "business_criticality": "Unknown",
            "discovery_source": "Mentioned_In_Passing",
            "source_evidence": {
                "exact_quote": "uses Minimal App",
                "evidence_type": "logical_inference",
                "confidence_level": "low"
            },
            "fields_not_documented": [
                "version", "user_count", "license_type", "contract_expiry",
                "license_count", "integration_count", "technology_stack"
            ]
        })

        metrics = store.get_application_completeness_metrics()

        assert metrics["status"] == "analyzed"
        assert metrics["total_applications"] == 1
        assert metrics["apps_with_missing_fields"] == 1
        assert "unknown_value_counts" in metrics
        assert metrics["unknown_value_counts"]["hosting_model"] == 1
        assert metrics["unknown_value_counts"]["business_criticality"] == 1

    def test_completeness_metrics_multiple_apps(self, store):
        """Test metrics with mix of well-documented and minimal apps."""
        # Well documented app
        store.execute_tool("record_application", {
            "application_name": "Good App",
            "application_category": "ERP",
            "vendor": "SAP",
            "hosting_model": "On_Premise",
            "business_criticality": "Critical",
            "discovery_source": "App_Inventory_Document",
            "version": "S/4HANA",
            "user_count": "1000",
            "license_type": "Subscription_Term",
            "source_evidence": {
                "exact_quote": "SAP S/4HANA with 1000 users",
                "evidence_type": "direct_statement",
                "confidence_level": "high"
            }
        })

        # Minimal app
        store.execute_tool("record_application", {
            "application_name": "Poor App",
            "application_category": "Other",
            "vendor": "Unknown",
            "hosting_model": "Unknown",
            "business_criticality": "Unknown",
            "discovery_source": "Mentioned_In_Passing",
            "source_evidence": {
                "exact_quote": "Poor App mentioned",
                "evidence_type": "logical_inference",
                "confidence_level": "low"
            },
            "fields_not_documented": ["version", "user_count", "license_type"]
        })

        metrics = store.get_application_completeness_metrics()

        assert metrics["total_applications"] == 2
        assert metrics["apps_with_missing_fields"] == 1


class TestUnknownValuesInCapabilityCoverage:
    """Test Unknown values in capability coverage tool."""

    @pytest.fixture
    def store(self):
        """Fresh AnalysisStore for each test."""
        return AnalysisStore()

    def test_capability_coverage_with_unknown_status(self, store):
        """Test recording capability coverage with Unknown status."""
        result = store.execute_tool("record_capability_coverage", {
            "capability_area": "finance_accounting",
            "coverage_status": "Unknown",
            "business_relevance": "Unknown",
            "relevance_reasoning": "Cannot determine relevance from available docs",
            "confidence_level": "low"
        })

        assert result["status"] == "recorded"

        summary = store.get_capability_summary()
        assert "Unknown" in summary["coverage_by_status"]


class TestUnknownValuesInBuyerComparison:
    """Test Unknown values in buyer comparison tools."""

    @pytest.fixture
    def store(self):
        """Fresh AnalysisStore for each test."""
        return AnalysisStore()

    def test_buyer_app_with_unknown_source(self, store):
        """Test recording buyer app with Unknown source."""
        result = store.execute_tool("record_buyer_application", {
            "application_name": "Buyer CRM",
            "vendor": "Salesforce",
            "application_category": "CRM",
            "capability_areas_covered": ["sales_crm"],
            "information_source": "Unknown"
        })

        assert result["status"] == "recorded"

        apps = store.get_buyer_applications()
        assert len(apps) == 1
        assert apps[0]["information_source"] == "Unknown"

    def test_overlap_with_unknown_type(self, store):
        """Test recording overlap with Unknown type."""
        # First record target app
        store.execute_tool("record_application", {
            "application_name": "Target App",
            "application_category": "CRM",
            "vendor": "Microsoft",
            "hosting_model": "SaaS",
            "business_criticality": "High",
            "discovery_source": "App_Inventory_Document",
            "source_evidence": {
                "exact_quote": "Using Target App for CRM",
                "evidence_type": "direct_statement",
                "confidence_level": "high"
            }
        })

        # Record overlap with Unknown type
        result = store.execute_tool("record_application_overlap", {
            "target_app_name": "Target App",
            "target_app_category": "CRM",
            "overlap_type": "Unknown",
            "considerations": "Need more information about buyer's CRM landscape",
            "follow_up_questions": [
                {
                    "question": "What CRM does the buyer use?",
                    "target": "Buyer_IT"
                }
            ]
        })

        assert result["status"] == "recorded"

        overlaps = store.get_application_overlaps()
        assert len(overlaps) == 1
        assert overlaps[0]["overlap_type"] == "Unknown"
