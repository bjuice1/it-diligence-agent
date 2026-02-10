"""
Tests for Phase 7-8: Business Context Profile

Run with: pytest tests/test_phase_7_8_business_context.py -v
"""
import pytest
from tools.analysis_tools import (
    AnalysisStore,
    INDUSTRY_TYPES,
    BUSINESS_MODELS,
    COMPANY_SIZE_RANGES,
    REVENUE_RANGES,
    GEOGRAPHIC_PRESENCE,
    BUSINESS_CONTEXT_SOURCE
)


class TestBusinessContextEnums:
    """Test that business context enums exist and have correct values."""

    def test_industry_types_has_values(self):
        """Verify INDUSTRY_TYPES has expected values."""
        assert "Manufacturing" in INDUSTRY_TYPES
        assert "Technology_Software" in INDUSTRY_TYPES
        assert "Healthcare" in INDUSTRY_TYPES
        assert "Financial_Services" in INDUSTRY_TYPES
        assert "Unknown" in INDUSTRY_TYPES

    def test_business_models_has_values(self):
        """Verify BUSINESS_MODELS has expected values."""
        assert "B2B" in BUSINESS_MODELS
        assert "B2C" in BUSINESS_MODELS
        assert "Subscription_SaaS" in BUSINESS_MODELS
        assert "Unknown" in BUSINESS_MODELS

    def test_company_size_ranges_has_values(self):
        """Verify COMPANY_SIZE_RANGES has expected values."""
        assert "Small_Under_100" in COMPANY_SIZE_RANGES
        assert "Enterprise_Over_10000" in COMPANY_SIZE_RANGES
        assert "Unknown" in COMPANY_SIZE_RANGES

    def test_revenue_ranges_has_values(self):
        """Verify REVENUE_RANGES has expected values."""
        assert "Under_10M" in REVENUE_RANGES
        assert "Over_1B" in REVENUE_RANGES
        assert "Unknown" in REVENUE_RANGES

    def test_geographic_presence_has_values(self):
        """Verify GEOGRAPHIC_PRESENCE has expected values."""
        assert "Single_Country" in GEOGRAPHIC_PRESENCE
        assert "Global" in GEOGRAPHIC_PRESENCE
        assert "Unknown" in GEOGRAPHIC_PRESENCE

    def test_business_context_source_has_values(self):
        """Verify BUSINESS_CONTEXT_SOURCE has expected values."""
        assert "Public_Filings_SEC" in BUSINESS_CONTEXT_SOURCE
        assert "Seller_Provided" in BUSINESS_CONTEXT_SOURCE
        assert "Unknown" in BUSINESS_CONTEXT_SOURCE


class TestRecordBusinessContext:
    """Test the record_business_context tool."""

    @pytest.fixture
    def store(self):
        """Fresh AnalysisStore for each test."""
        return AnalysisStore()

    def test_record_business_context_basic(self, store):
        """Test recording basic business context."""
        result = store.execute_tool("record_business_context", {
            "company_name": "Acme Corp",
            "industry": "Manufacturing",
            "business_model": "B2B",
            "employee_count_range": "Medium_100_500",
            "information_source": "Seller_Provided"
        })

        assert result["status"] == "recorded"
        assert result["id"] == "BC-001"
        assert result["type"] == "business_context"

        # Verify stored correctly
        ctx = store.get_business_context()
        assert ctx is not None
        assert ctx["company_name"] == "Acme Corp"
        assert ctx["industry"] == "Manufacturing"

    def test_record_business_context_full(self, store):
        """Test recording full business context with all fields."""
        result = store.execute_tool("record_business_context", {
            "company_name": "TechCo Inc",
            "industry": "Technology_Software",
            "industry_details": "Enterprise SaaS for HR",
            "business_model": "Subscription_SaaS",
            "business_model_details": "Monthly recurring revenue from SMB",
            "employee_count_range": "Large_500_2000",
            "employee_count_actual": "1,200",
            "revenue_range": "100M_500M",
            "geographic_presence": "Multi_Region",
            "geographic_details": "US, UK, Germany, Australia",
            "key_business_processes": ["Customer onboarding", "Subscription billing", "Support"],
            "regulatory_requirements": ["SOC 2", "GDPR"],
            "is_public_company": False,
            "information_source": "Seller_Provided",
            "notes": "High growth company"
        })

        assert result["status"] == "recorded"

        ctx = store.get_business_context()
        assert ctx["industry_details"] == "Enterprise SaaS for HR"
        assert ctx["key_business_processes"] == ["Customer onboarding", "Subscription billing", "Support"]
        assert ctx["regulatory_requirements"] == ["SOC 2", "GDPR"]

    def test_record_business_context_singleton(self, store):
        """Test that only one business context can be recorded."""
        # First record
        store.execute_tool("record_business_context", {
            "company_name": "First Corp",
            "industry": "Manufacturing",
            "business_model": "B2B",
            "employee_count_range": "Medium_100_500",
            "information_source": "Seller_Provided"
        })

        # Second attempt should fail
        result = store.execute_tool("record_business_context", {
            "company_name": "Second Corp",
            "industry": "Technology_Software",
            "business_model": "Subscription_SaaS",
            "employee_count_range": "Small_Under_100",
            "information_source": "Assumption"
        })

        assert result["status"] == "already_exists"

        # Verify original still exists
        ctx = store.get_business_context()
        assert ctx["company_name"] == "First Corp"

    def test_record_business_context_defaults(self, store):
        """Test that default arrays are added."""
        store.execute_tool("record_business_context", {
            "company_name": "Minimal Corp",
            "industry": "Other",
            "business_model": "Unknown",
            "employee_count_range": "Unknown",
            "information_source": "Assumption"
        })

        ctx = store.get_business_context()
        assert ctx["key_business_processes"] == []
        assert ctx["regulatory_requirements"] == []


class TestCapabilityRelevance:
    """Test capability relevance based on business context."""

    @pytest.fixture
    def store(self):
        """Fresh AnalysisStore for each test."""
        return AnalysisStore()

    def test_relevance_without_context(self, store):
        """Test default relevance when no context is recorded."""
        relevance = store.get_expected_capability_relevance()

        # Should return defaults
        assert relevance["finance_accounting"] == "Critical"
        assert relevance["human_resources"] == "Critical"
        assert relevance["identity_security"] == "Critical"

    def test_relevance_manufacturing(self, store):
        """Test relevance for manufacturing company."""
        store.execute_tool("record_business_context", {
            "company_name": "ManufactureCo",
            "industry": "Manufacturing",
            "business_model": "B2B",
            "employee_count_range": "Large_500_2000",
            "information_source": "Seller_Provided"
        })

        relevance = store.get_expected_capability_relevance()

        assert relevance["operations_supply_chain"] == "Critical"
        assert relevance["ecommerce_digital"] == "Low"

    def test_relevance_ecommerce(self, store):
        """Test relevance for e-commerce company."""
        store.execute_tool("record_business_context", {
            "company_name": "OnlineStore",
            "industry": "E_Commerce",
            "business_model": "B2C",
            "employee_count_range": "Medium_100_500",
            "information_source": "Company_Website"
        })

        relevance = store.get_expected_capability_relevance()

        assert relevance["ecommerce_digital"] == "Critical"
        assert relevance["customer_service"] == "High"
        assert relevance["marketing"] == "High"

    def test_relevance_professional_services(self, store):
        """Test relevance for professional services company."""
        store.execute_tool("record_business_context", {
            "company_name": "ConsultingFirm",
            "industry": "Professional_Services",
            "business_model": "Professional_Services",
            "employee_count_range": "Small_Under_100",
            "information_source": "Seller_Provided"
        })

        relevance = store.get_expected_capability_relevance()

        assert relevance["operations_supply_chain"] == "Not_Applicable"
        assert relevance["ecommerce_digital"] == "Low"

    def test_relevance_saas(self, store):
        """Test relevance for SaaS company."""
        store.execute_tool("record_business_context", {
            "company_name": "SaaSCo",
            "industry": "Technology_Software",
            "business_model": "Subscription_SaaS",
            "employee_count_range": "Medium_100_500",
            "information_source": "Seller_Provided"
        })

        relevance = store.get_expected_capability_relevance()

        assert relevance["data_analytics"] == "High"
        assert relevance["customer_service"] == "High"
        assert relevance["operations_supply_chain"] == "Low"


class TestBusinessContextSummary:
    """Test business context summary generation."""

    @pytest.fixture
    def store(self):
        """Fresh AnalysisStore for each test."""
        return AnalysisStore()

    def test_summary_no_context(self, store):
        """Test summary when no context is recorded."""
        summary = store.get_business_context_summary()

        assert "No business context recorded" in summary

    def test_summary_with_context(self, store):
        """Test summary with recorded context."""
        store.execute_tool("record_business_context", {
            "company_name": "Acme Corp",
            "industry": "Manufacturing",
            "industry_details": "Industrial equipment",
            "business_model": "B2B",
            "business_model_details": "Direct sales to enterprises",
            "employee_count_range": "Large_500_2000",
            "revenue_range": "100M_500M",
            "geographic_presence": "Multi_Region",
            "geographic_details": "North America, Europe",
            "key_business_processes": ["Manufacturing", "Distribution"],
            "regulatory_requirements": ["ISO 9001", "SOX"],
            "is_public_company": True,
            "ticker_symbol": "ACME",
            "information_source": "Public_Filings_SEC"
        })

        summary = store.get_business_context_summary()

        assert "Acme Corp" in summary
        assert "Manufacturing" in summary
        assert "Industrial equipment" in summary
        assert "100M_500M" in summary
        assert "Manufacturing, Distribution" in summary
        assert "ISO 9001, SOX" in summary
        assert "ACME" in summary
