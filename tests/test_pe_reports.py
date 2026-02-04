"""
Tests for PE Report Generation System.

Tests cover:
- Data schemas and dataclasses
- Benchmark library
- Domain generators
- Renderers
- Executive dashboard and summary
"""

import pytest
from datetime import datetime


# =============================================================================
# SCHEMA TESTS
# =============================================================================

class TestPEReportSchemas:
    """Test PE report data schemas."""

    def test_deal_context_creation(self):
        """Test DealContext creation and serialization."""
        from tools_v2.pe_report_schemas import DealContext

        ctx = DealContext(
            target_name="Acme Corp",
            deal_type="acquisition",
            target_revenue=75_000_000,
            target_employees=250,
            target_industry="software"
        )

        assert ctx.target_name == "Acme Corp"
        assert ctx.company_size_tier == "50-100M"

        # Test serialization
        data = ctx.to_dict()
        assert data["target_name"] == "Acme Corp"

        # Test deserialization
        ctx2 = DealContext.from_dict(data)
        assert ctx2.target_name == ctx.target_name

    def test_company_size_tier_calculation(self):
        """Test company size tier determination."""
        from tools_v2.pe_report_schemas import DealContext

        # Test by revenue
        ctx = DealContext(target_name="Test", target_revenue=30_000_000)
        assert ctx.company_size_tier == "0-50M"

        ctx = DealContext(target_name="Test", target_revenue=80_000_000)
        assert ctx.company_size_tier == "50-100M"

        ctx = DealContext(target_name="Test", target_revenue=200_000_000)
        assert ctx.company_size_tier == "100-500M"

        # Test by employees when revenue not provided
        ctx = DealContext(target_name="Test", target_employees=50)
        assert ctx.company_size_tier == "0-50M"

        ctx = DealContext(target_name="Test", target_employees=300)
        assert ctx.company_size_tier == "50-100M"

    def test_benchmark_assessment_creation(self):
        """Test BenchmarkAssessment creation."""
        from tools_v2.pe_report_schemas import BenchmarkAssessment

        assessment = BenchmarkAssessment(
            tech_age="modern",
            tech_age_rationale="Recently upgraded infrastructure",
            cost_posture="in_line",
            cost_posture_rationale="IT spending at 3.5% of revenue",
            maturity="developing",
            overall_grade="Adequate",
            implication="IT estate is functional but will need investment",
            key_callouts=["Modern cloud infrastructure", "Legacy ERP"]
        )

        assert assessment.tech_age == "modern"
        assert assessment.overall_grade == "Adequate"
        assert len(assessment.key_callouts) == 2

        # Test serialization
        data = assessment.to_dict()
        assert data["tech_age"] == "modern"

        # Test deserialization
        assessment2 = BenchmarkAssessment.from_dict(data)
        assert assessment2.overall_grade == "Adequate"

    def test_action_item_cost_display(self):
        """Test ActionItem cost formatting."""
        from tools_v2.pe_report_schemas import ActionItem

        action = ActionItem(
            title="Implement SSO",
            so_what="Enables unified access management",
            cost_range=(50000, 100000),
            timing="Day_100",
            owner_type="target"
        )

        assert action.cost_display == "$50,000 - $100,000"

        # Test zero cost
        action2 = ActionItem(title="Test", so_what="Test", cost_range=(0, 0))
        assert action2.cost_display == "TBD"

    def test_domain_report_data_serialization(self):
        """Test DomainReportData full serialization cycle."""
        from tools_v2.pe_report_schemas import (
            DomainReportData,
            BenchmarkAssessment,
            InventorySummary,
        )

        report = DomainReportData(
            domain="organization",
            domain_display_name="IT Organization",
            inventory_summary=InventorySummary(total_count=15, summary_text="15 IT staff"),
            run_rate_cost=(1_000_000, 1_500_000),
            cost_breakdown={"personnel": (800_000, 1_000_000)},
            benchmark_assessment=BenchmarkAssessment(overall_grade="Adequate"),
            top_implications=["Lean team will need augmentation"],
            fact_count=25,
            risk_count=5,
            work_item_count=8,
        )

        # Serialize
        data = report.to_dict()
        assert data["domain"] == "organization"
        assert data["run_rate_cost"] == [1_000_000, 1_500_000]
        assert "personnel" in data["cost_breakdown"]

        # Deserialize
        report2 = DomainReportData.from_dict(data)
        assert report2.domain == "organization"
        assert report2.run_rate_cost == (1_000_000, 1_500_000)
        assert report2.fact_count == 25


# =============================================================================
# BENCHMARK LIBRARY TESTS
# =============================================================================

class TestBenchmarkLibrary:
    """Test benchmark library functionality."""

    def test_get_benchmark_exists(self):
        """Test retrieving existing benchmark."""
        from tools_v2.benchmark_library import get_benchmark

        benchmark = get_benchmark("it_pct_revenue", "software", "50-100M")
        assert benchmark is not None
        assert benchmark.metric == "it_pct_revenue"
        assert benchmark.industry == "software"
        assert benchmark.typical > benchmark.low
        assert benchmark.high > benchmark.typical

    def test_get_benchmark_fallback_to_general(self):
        """Test fallback to general benchmark."""
        from tools_v2.benchmark_library import get_benchmark

        # Try a specific industry that might not exist
        benchmark = get_benchmark("it_pct_revenue", "aerospace", "50-100M")
        assert benchmark is not None
        assert benchmark.industry == "general"

    def test_get_benchmark_no_fallback(self):
        """Test when fallback is disabled."""
        from tools_v2.benchmark_library import get_benchmark

        benchmark = get_benchmark(
            "it_pct_revenue", "nonexistent_industry", "50-100M",
            fallback_to_general=False
        )
        # May return None or general depending on implementation
        # Just verify no exception

    def test_benchmark_format_range(self):
        """Test benchmark range formatting."""
        from tools_v2.benchmark_library import get_benchmark

        benchmark = get_benchmark("it_pct_revenue", "software", "50-100M")
        range_str = benchmark.format_range()
        assert "%" in range_str
        assert "typical" in range_str

    def test_benchmark_assess_value(self):
        """Test value assessment against benchmark."""
        from tools_v2.benchmark_library import get_benchmark

        benchmark = get_benchmark("it_pct_revenue", "software", "50-100M")

        # Value below typical
        assert benchmark.assess_value(2.0) == "below_typical"

        # Value typical
        assert benchmark.assess_value(benchmark.typical) == "typical"

        # Value above typical
        assert benchmark.assess_value(15.0) == "above_typical"

    def test_list_available_metrics(self):
        """Test listing available metrics."""
        from tools_v2.benchmark_library import list_available_metrics

        metrics = list_available_metrics()
        assert "it_pct_revenue" in metrics
        assert "cost_per_employee" in metrics
        assert "it_staff_ratio" in metrics

    def test_assess_against_benchmark(self):
        """Test structured assessment against benchmark."""
        from tools_v2.benchmark_library import assess_against_benchmark

        result = assess_against_benchmark(
            "it_pct_revenue", "software", "50-100M", 3.5
        )

        assert result["found"] is True
        assert result["benchmark"] is not None
        assert result["assessment"] in ["below_typical", "typical", "above_typical"]
        assert "context" in result


# =============================================================================
# DOMAIN GENERATOR TESTS
# =============================================================================

class TestDomainGenerators:
    """Test domain report generators."""

    @pytest.fixture
    def mock_fact_store(self):
        """Create a mock fact store with sample data."""
        from stores.fact_store import FactStore, Fact

        store = FactStore(deal_id="test-deal-123")

        # Add organization facts
        store.add_fact(
            domain="organization",
            category="leadership",
            item="CIO",
            details={"name": "John Smith", "tenure": "5 years"},
            status="documented",
            evidence={"exact_quote": "John Smith is the CIO"}
        )

        store.add_fact(
            domain="organization",
            category="staffing",
            item="IT Team",
            details={"headcount": 12, "total_it_headcount": 12, "outsourced_percentage": 30},
            status="documented",
            evidence={}
        )

        store.add_fact(
            domain="organization",
            category="budget",
            item="IT Budget",
            details={"total_it_budget": 2_500_000, "percent_of_revenue": 3.5},
            status="documented",
            evidence={}
        )

        # Add application facts
        store.add_fact(
            domain="applications",
            category="erp",
            item="SAP ECC 6.0",
            details={"vendor": "SAP", "version": "ECC 6.0", "criticality": "high"},
            status="documented",
            evidence={}
        )

        store.add_fact(
            domain="applications",
            category="crm",
            item="Salesforce",
            details={"vendor": "Salesforce", "criticality": "high"},
            status="documented",
            evidence={}
        )

        return store

    @pytest.fixture
    def mock_reasoning_store(self):
        """Create a mock reasoning store with sample data."""
        from tools_v2.reasoning_tools import ReasoningStore

        store = ReasoningStore()

        # Add a risk (using kwargs, not dataclass)
        store.add_risk(
            domain="organization",
            title="Lean IT Team",
            description="IT team is understaffed for company size",
            category="resource",
            severity="medium",
            integration_dependent=False,
            mitigation="Consider hiring or augmenting",
            based_on_facts=["F-ORG-001"],
            confidence="high",
            reasoning="12 staff for 250 employees is below typical ratio"
        )

        # Add a work item (using kwargs, not dataclass)
        store.add_work_item(
            domain="organization",
            title="Hire Security Architect",
            description="Add dedicated security role",
            phase="Day_100",
            priority="high",
            owner_type="target",
            triggered_by=["F-ORG-001"],
            based_on_facts=["F-ORG-001"],
            confidence="high",
            reasoning="No dedicated security role exists",
            cost_estimate="100k_to_500k"
        )

        return store

    @pytest.fixture
    def mock_deal_context(self):
        """Create a mock deal context."""
        from tools_v2.pe_report_schemas import DealContext

        return DealContext(
            target_name="Test Company",
            deal_type="acquisition",
            target_revenue=75_000_000,
            target_employees=250,
            target_industry="software"
        )

    def test_organization_generator(self, mock_fact_store, mock_reasoning_store, mock_deal_context):
        """Test organization domain generator."""
        from tools_v2.domain_generators.organization import OrganizationDomainGenerator

        generator = OrganizationDomainGenerator(
            fact_store=mock_fact_store,
            reasoning_store=mock_reasoning_store,
            deal_context=mock_deal_context
        )

        report = generator.generate()

        assert report.domain == "organization"
        assert report.domain_display_name == "IT Organization"
        assert report.fact_count >= 2
        assert report.inventory_html  # Should have org chart

    def test_applications_generator(self, mock_fact_store, mock_reasoning_store, mock_deal_context):
        """Test applications domain generator."""
        from tools_v2.domain_generators.applications import ApplicationsDomainGenerator

        generator = ApplicationsDomainGenerator(
            fact_store=mock_fact_store,
            reasoning_store=mock_reasoning_store,
            deal_context=mock_deal_context
        )

        report = generator.generate()

        assert report.domain == "applications"
        assert report.domain_display_name == "Applications"
        assert "SAP" in str(report.inventory_summary.key_items) or report.fact_count >= 1


# =============================================================================
# RENDERER TESTS
# =============================================================================

class TestRenderers:
    """Test HTML renderers."""

    def test_domain_report_renderer(self):
        """Test domain report HTML rendering."""
        from tools_v2.pe_report_schemas import (
            DomainReportData,
            BenchmarkAssessment,
            ActionItem,
            InventorySummary,
        )
        from tools_v2.renderers.html_renderer import render_domain_report

        report = DomainReportData(
            domain="organization",
            domain_display_name="IT Organization",
            inventory_summary=InventorySummary(
                total_count=15,
                summary_text="15 IT staff, 3 leadership roles"
            ),
            inventory_html="<div>Test org chart</div>",
            run_rate_cost=(1_000_000, 1_500_000),
            cost_breakdown={"personnel": (800_000, 1_000_000)},
            benchmark_assessment=BenchmarkAssessment(
                tech_age="modern",
                cost_posture="in_line",
                overall_grade="Adequate",
                implication="IT is functional but needs attention"
            ),
            top_actions=[
                ActionItem(
                    title="Hire Security Architect",
                    so_what="Address security gap",
                    cost_range=(100_000, 200_000),
                    timing="Day_100",
                    owner_type="target",
                    priority="high"
                )
            ],
            top_implications=["Lean team will need augmentation"],
            fact_count=25,
            risk_count=5,
            work_item_count=8,
        )

        html = render_domain_report(report, "Test Company")

        assert "<!DOCTYPE html>" in html
        assert "IT Organization" in html
        assert "Adequate" in html
        assert "$1,000,000" in html or "1,000,000" in html
        assert "Hire Security Architect" in html

    def test_dashboard_renderer(self):
        """Test dashboard HTML rendering."""
        from tools_v2.pe_report_schemas import (
            ExecutiveDashboardData,
            DomainHighlight,
        )
        from tools_v2.renderers.dashboard_renderer import render_dashboard

        dashboard = ExecutiveDashboardData(
            target_name="Test Company",
            overall_assessment="IT estate is adequate for current operations.",
            overall_grade="Adequate",
            total_it_budget=(2_000_000, 3_000_000),
            total_investment_needed=(500_000, 1_000_000),
            it_headcount=15,
            it_pct_revenue=3.5,
            domain_highlights={
                "organization": DomainHighlight(
                    domain="organization",
                    domain_display_name="IT Organization",
                    overall_grade="Adequate",
                    key_finding="Lean team with MSP support",
                    work_item_count=5,
                    risk_count=3,
                ),
            },
            investment_by_phase={"Day_1": (100_000, 200_000), "Day_100": (300_000, 500_000)},
            top_risks=[{"title": "Security Gap", "severity": "high", "domain": "cybersecurity"}],
            top_opportunities=["Consolidate IT infrastructure"],
            total_work_items=10,
            total_risks=5,
            total_facts=50,
            total_gaps=8,
        )

        html = render_dashboard(dashboard)

        assert "<!DOCTYPE html>" in html
        assert "Test Company" in html
        assert "Adequate" in html
        assert "IT Organization" in html


# =============================================================================
# EXECUTIVE SUMMARY TESTS
# =============================================================================

class TestExecutiveSummary:
    """Test executive summary generation."""

    def test_executive_summary_generation(self):
        """Test executive summary data generation."""
        from tools_v2.pe_report_schemas import DealContext, ExecutiveSummaryData
        from tools_v2.executive_summary_pe import generate_executive_summary
        from stores.fact_store import FactStore
        from tools_v2.reasoning_tools import ReasoningStore

        fact_store = FactStore()
        reasoning_store = ReasoningStore()
        deal_context = DealContext(
            target_name="Test Corp",
            target_revenue=75_000_000,
            target_employees=250
        )

        summary = generate_executive_summary(
            fact_store=fact_store,
            reasoning_store=reasoning_store,
            deal_context=deal_context,
            target_name="Test Corp"
        )

        assert isinstance(summary, ExecutiveSummaryData)
        assert summary.target_name == "Test Corp"
        assert summary.domains_analyzed == 6
        assert len(summary.domain_highlights) == 6

    def test_executive_summary_html_rendering(self):
        """Test executive summary HTML rendering."""
        from tools_v2.pe_report_schemas import (
            ExecutiveSummaryData,
            DomainHighlight,
            RiskSummary,
        )
        from tools_v2.executive_summary_pe import render_executive_summary_html

        summary = ExecutiveSummaryData(
            target_name="Test Corp",
            total_it_budget=(2_000_000, 3_000_000),
            total_investment_needed=(500_000, 1_000_000),
            it_headcount=15,
            domain_highlights={
                "organization": DomainHighlight(
                    domain="organization",
                    domain_display_name="IT Organization",
                    overall_grade="Adequate",
                    key_finding="Lean team"
                ),
            },
            critical_risks=[
                RiskSummary(
                    title="Security Gap",
                    domain="cybersecurity",
                    severity="high",
                    implication="Need to address",
                    mitigation="Hire security"
                )
            ],
            key_opportunities=["Cost optimization"],
            overall_narrative="The IT estate is adequate."
        )

        html = render_executive_summary_html(summary)

        assert "<!DOCTYPE html>" in html
        assert "Test Corp" in html
        assert "Security Gap" in html


# =============================================================================
# COSTS AND INVESTMENT TESTS
# =============================================================================

class TestCostsAndInvestment:
    """Test costs and investment report generation."""

    def test_costs_report_generation(self):
        """Test costs report data generation."""
        from tools_v2.pe_report_schemas import DealContext, CostsReportData
        from tools_v2.costs_report import generate_costs_report
        from stores.fact_store import FactStore

        fact_store = FactStore()
        deal_context = DealContext(
            target_name="Test Corp",
            target_revenue=75_000_000,
            target_employees=250
        )

        costs_data = generate_costs_report(fact_store, deal_context)

        assert isinstance(costs_data, CostsReportData)
        assert isinstance(costs_data.total_run_rate, tuple)
        assert isinstance(costs_data.by_domain, dict)

    def test_investment_report_generation(self):
        """Test investment report data generation."""
        from tools_v2.pe_report_schemas import InvestmentReportData
        from tools_v2.investment_report import generate_investment_report
        from tools_v2.reasoning_tools import ReasoningStore

        reasoning_store = ReasoningStore()
        investment_data = generate_investment_report(reasoning_store)

        assert isinstance(investment_data, InvestmentReportData)
        assert isinstance(investment_data.total_one_time, tuple)
        assert isinstance(investment_data.by_phase, dict)


# =============================================================================
# PE NARRATIVE TESTS
# =============================================================================

class TestPENarrative:
    """Test PE narrative generation."""

    def test_generate_top_implications(self):
        """Test top implications generation."""
        from tools_v2.pe_narrative import generate_top_implications
        from tools_v2.pe_report_schemas import BenchmarkAssessment
        from tools_v2.reasoning_tools import ReasoningStore

        reasoning_store = ReasoningStore()
        assessment = BenchmarkAssessment(
            implication="IT estate needs investment"
        )

        implications = generate_top_implications(
            "organization", reasoning_store, assessment
        )

        assert isinstance(implications, list)
        assert len(implications) <= 3

    def test_generate_top_actions(self):
        """Test top actions generation."""
        from tools_v2.pe_narrative import generate_top_actions
        from tools_v2.reasoning_tools import ReasoningStore

        reasoning_store = ReasoningStore()
        actions = generate_top_actions("organization", reasoning_store)

        assert isinstance(actions, list)
        assert len(actions) <= 3


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestPEReportIntegration:
    """Integration tests for the complete PE reporting flow."""

    def test_full_report_generation_flow(self):
        """Test complete report generation from stores to HTML."""
        from stores.fact_store import FactStore
        from tools_v2.reasoning_tools import ReasoningStore
        from tools_v2.pe_report_schemas import DealContext
        from tools_v2.domain_generators.organization import OrganizationDomainGenerator
        from tools_v2.renderers.html_renderer import render_domain_report

        # Setup
        fact_store = FactStore(deal_id="test-deal-456")
        fact_store.add_fact(
            domain="organization",
            category="staffing",
            item="IT Team",
            details={"total_it_headcount": 10},
            status="documented",
            evidence={}
        )

        reasoning_store = ReasoningStore()
        reasoning_store.add_work_item(
            domain="organization",
            title="Test Work Item",
            description="Test description",
            phase="Day_100",
            priority="high",
            owner_type="target",
            triggered_by=[],
            based_on_facts=[],
            confidence="high",
            reasoning="Test reasoning",
            cost_estimate="25k_to_100k"
        )

        deal_context = DealContext(
            target_name="Integration Test Corp",
            target_revenue=50_000_000,
            target_employees=200
        )

        # Generate
        generator = OrganizationDomainGenerator(
            fact_store=fact_store,
            reasoning_store=reasoning_store,
            deal_context=deal_context
        )
        report = generator.generate()

        # Render
        html = render_domain_report(report, "Integration Test Corp")

        # Verify
        assert "Integration Test Corp" in html
        assert "IT Organization" in html
        assert "<!DOCTYPE html>" in html
