"""
Tests for the Consistency Engine.

These tests verify that the rule-based scoring and deterministic
calculations produce stable, predictable outputs.
"""

from tools_v2.consistency_engine import (
    categorize_work_item,
    calculate_work_item_cost,
    calculate_total_costs,
    check_complexity_flags,
    calculate_complexity_score,
    score_risk,
    get_top_risks,
    calculate_confidence,
    generate_consistency_report,
    CompanyProfile,
    get_size_multiplier,
    get_industry_factor,
    get_geography_factor,
    get_maturity_factor,
    COST_TABLE,
)


class TestWorkItemCategorization:
    """Test work item categorization."""

    def test_erp_categorization(self):
        """ERP-related items should categorize as erp_integration."""
        assert categorize_work_item("SAP integration project") == "erp_integration"
        assert categorize_work_item("Oracle EBS migration") == "erp_integration"
        assert categorize_work_item("NetSuite consolidation") == "erp_integration"

    def test_identity_categorization(self):
        """Identity-related items should categorize as identity_consolidation."""
        assert categorize_work_item("SSO implementation") == "identity_consolidation"
        assert categorize_work_item("Active Directory migration") == "identity_consolidation"
        assert categorize_work_item("IAM governance setup") == "identity_consolidation"

    def test_security_categorization(self):
        """Security-related items should categorize as security_remediation."""
        assert categorize_work_item("SIEM deployment") == "security_remediation"
        assert categorize_work_item("Vulnerability remediation") == "security_remediation"
        assert categorize_work_item("Firewall configuration") == "security_remediation"

    def test_default_categorization(self):
        """Unknown items should categorize as default."""
        assert categorize_work_item("Random task") == "default"
        assert categorize_work_item("Something else entirely") == "default"


class TestCostCalculation:
    """Test deterministic cost calculation."""

    def test_cost_returns_tuple(self):
        """Cost calculation should return (low, high) tuple."""
        low, high = calculate_work_item_cost("SAP integration", "", "Day_100")
        assert isinstance(low, int)
        assert isinstance(high, int)
        assert low < high

    def test_costs_match_table(self):
        """Costs should match the lookup table."""
        low, high = calculate_work_item_cost("ERP integration", "", "Day_1")
        expected = COST_TABLE["erp_integration"]["Day_1"]
        assert (low, high) == expected

    def test_phase_normalization(self):
        """Different phase formats should normalize correctly."""
        cost1 = calculate_work_item_cost("Task", "", "Day_1")
        cost2 = calculate_work_item_cost("Task", "", "day_1")
        _ = calculate_work_item_cost("Task", "", "day1")
        # All should produce same result
        assert cost1 == cost2

    def test_total_costs_calculation(self):
        """Total costs should sum correctly."""
        work_items = [
            {"title": "SAP migration", "description": "", "phase": "Day_100"},
            {"title": "SSO setup", "description": "", "phase": "Day_1"},
        ]
        result = calculate_total_costs(work_items)

        assert "by_phase" in result
        assert "total" in result
        assert "breakdown" in result
        assert result["total"]["low"] > 0
        assert result["total"]["high"] > result["total"]["low"]

    def test_costs_are_deterministic(self):
        """Same inputs should always produce same costs."""
        work_items = [
            {"title": "ERP integration", "description": "", "phase": "Day_100"},
            {"title": "Security audit", "description": "", "phase": "Day_1"},
        ]
        result1 = calculate_total_costs(work_items)
        result2 = calculate_total_costs(work_items)

        assert result1["total"] == result2["total"]


class TestComplexityFlags:
    """Test complexity flag detection."""

    def test_dual_erp_flag(self):
        """Dual ERP should trigger flag."""
        flags = check_complexity_flags(["We have dual ERP systems"])
        assert len(flags) == 1
        assert flags[0]["flag"] == "dual_erp"
        assert flags[0]["bump_to"] == "high"

    def test_no_dr_flag(self):
        """Missing DR should trigger flag."""
        flags = check_complexity_flags(["No disaster recovery plan exists"])
        assert len(flags) == 1
        assert flags[0]["flag"] == "no_disaster_recovery"

    def test_multiple_flags(self):
        """Multiple flags can trigger at once."""
        flags = check_complexity_flags([
            "Dual ERP systems",
            "Legacy EOL software"
        ])
        assert len(flags) >= 2

    def test_no_flags_for_clean_text(self):
        """Clean text should not trigger flags."""
        flags = check_complexity_flags(["Modern infrastructure with good practices"])
        assert len(flags) == 0


class TestComplexityScoring:
    """Test rule-based complexity scoring."""

    def test_low_complexity(self):
        """Few low-severity items should be low complexity."""
        result = calculate_complexity_score(
            risks=[{"severity": "low"}, {"severity": "low"}],
            gaps=[],
            work_items=[{"title": "Minor task"}]
        )
        assert result["tier"] == "low"

    def test_high_complexity_from_critical_risks(self):
        """Critical risks should push to high complexity."""
        result = calculate_complexity_score(
            risks=[
                {"severity": "critical"},
                {"severity": "critical"},
                {"severity": "high"}
            ],
            gaps=[{"importance": "high"}],
            work_items=[]
        )
        assert result["tier"] in ["high", "critical"]

    def test_flag_bumps_tier(self):
        """Complexity flags should bump tier."""
        result = calculate_complexity_score(
            risks=[{"severity": "low", "title": "Minor risk"}],
            gaps=[],
            work_items=[],
            all_texts=["We have dual ERP systems that need integration"]
        )
        # Should be bumped to high due to dual_erp flag
        assert result["tier"] == "high"
        assert len(result["flags_triggered"]) > 0

    def test_scoring_is_deterministic(self):
        """Same inputs should always produce same complexity."""
        risks = [{"severity": "high"}, {"severity": "medium"}]
        gaps = [{"importance": "high"}]
        work_items = [{"title": "Task 1"}, {"title": "Task 2"}]

        result1 = calculate_complexity_score(risks, gaps, work_items)
        result2 = calculate_complexity_score(risks, gaps, work_items)

        assert result1["tier"] == result2["tier"]
        assert result1["score"] == result2["score"]


class TestRiskScoring:
    """Test deterministic risk scoring."""

    def test_critical_scores_higher(self):
        """Critical risks should score higher than low risks."""
        critical_score = score_risk({"severity": "critical"})
        low_score = score_risk({"severity": "low"})
        assert critical_score > low_score

    def test_more_citations_higher_score(self):
        """More citations should increase score."""
        few_citations = score_risk({
            "severity": "high",
            "based_on_facts": ["F-1"]
        })
        many_citations = score_risk({
            "severity": "high",
            "based_on_facts": ["F-1", "F-2", "F-3", "F-4"]
        })
        assert many_citations > few_citations

    def test_verified_citations_boost(self):
        """Verified citations should boost score."""
        unverified = score_risk(
            {"severity": "high", "based_on_facts": ["F-1", "F-2"]},
            verified_fact_ids=[]
        )
        verified = score_risk(
            {"severity": "high", "based_on_facts": ["F-1", "F-2"]},
            verified_fact_ids=["F-1", "F-2"]
        )
        assert verified > unverified

    def test_integration_dependent_boost(self):
        """Integration-dependent risks should get boost."""
        not_dependent = score_risk({
            "severity": "high",
            "integration_dependent": False
        })
        dependent = score_risk({
            "severity": "high",
            "integration_dependent": True
        })
        assert dependent > not_dependent


class TestTopRisks:
    """Test stable top risks selection."""

    def test_returns_n_risks(self):
        """Should return exactly N risks."""
        risks = [
            {"severity": "high", "title": "Risk 1"},
            {"severity": "medium", "title": "Risk 2"},
            {"severity": "low", "title": "Risk 3"},
        ]
        top = get_top_risks(risks, n=2)
        assert len(top) == 2

    def test_sorted_by_score(self):
        """Top risks should be sorted by score descending."""
        risks = [
            {"severity": "low", "title": "Low Risk"},
            {"severity": "critical", "title": "Critical Risk"},
            {"severity": "medium", "title": "Medium Risk"},
        ]
        top = get_top_risks(risks, n=3)

        # Critical should be first
        assert top[0]["severity"] == "critical"
        # Low should be last
        assert top[2]["severity"] == "low"

    def test_selection_is_deterministic(self):
        """Same risks should always produce same top selection."""
        risks = [
            {"severity": "high", "title": "Risk A", "domain": "infrastructure"},
            {"severity": "high", "title": "Risk B", "domain": "cybersecurity"},
            {"severity": "medium", "title": "Risk C", "domain": "applications"},
        ]

        top1 = get_top_risks(risks, n=2)
        top2 = get_top_risks(risks, n=2)

        # Same titles should be selected
        titles1 = [r["title"] for r in top1]
        titles2 = [r["title"] for r in top2]
        assert titles1 == titles2


class TestConfidence:
    """Test confidence calculation."""

    def test_high_confidence(self):
        """High verification rate should produce high confidence."""
        result = calculate_confidence(
            total_facts=100,
            verified_facts=95,
            gap_count=0,
            source_count=5
        )
        assert result["label"] == "High"
        assert result["score"] >= 0.7

    def test_low_confidence(self):
        """Low verification and many gaps should produce low confidence."""
        result = calculate_confidence(
            total_facts=100,
            verified_facts=10,
            gap_count=20,
            source_count=1
        )
        assert result["label"] == "Low"
        assert result["score"] < 0.4

    def test_no_facts_is_low_confidence(self):
        """No facts should be low confidence."""
        result = calculate_confidence(
            total_facts=0,
            verified_facts=0,
            gap_count=0,
            source_count=0
        )
        assert result["label"] == "Low"
        assert result["score"] == 0.0


class TestConsistencyReport:
    """Test the main consistency report generation."""

    def test_report_structure(self):
        """Report should have expected structure."""
        report = generate_consistency_report(
            facts=[{"item": "VMware"}],
            gaps=[{"description": "Missing DR", "importance": "high"}],
            risks=[{"severity": "high", "title": "EOL Risk", "description": ""}],
            work_items=[{"title": "Migration", "description": "", "phase": "Day_100"}]
        )

        assert "complexity" in report
        assert "costs" in report
        assert "top_risks" in report
        assert "confidence" in report
        assert "counts" in report
        assert "generated_at" in report

    def test_report_is_deterministic(self):
        """Same inputs should always produce same report."""
        facts = [{"item": "VMware"}]
        gaps = [{"description": "Missing DR", "importance": "high"}]
        risks = [{"severity": "high", "title": "EOL Risk", "description": ""}]
        work_items = [{"title": "Migration", "description": "", "phase": "Day_100"}]

        report1 = generate_consistency_report(facts, gaps, risks, work_items)
        report2 = generate_consistency_report(facts, gaps, risks, work_items)

        assert report1["complexity"]["tier"] == report2["complexity"]["tier"]
        assert report1["costs"]["total"] == report2["costs"]["total"]
        assert report1["counts"] == report2["counts"]


class TestCompanyProfile:
    """Test company profile and multiplier calculations."""

    def test_size_multiplier_micro(self):
        """Micro companies (<50 employees) should get 0.4x multiplier."""
        mult, label = get_size_multiplier(30)
        assert mult == 0.4
        assert "50" in label

    def test_size_multiplier_midmarket(self):
        """Mid-market companies (250-500) should get 1.0x multiplier."""
        mult, label = get_size_multiplier(300)
        assert mult == 1.0

    def test_size_multiplier_enterprise(self):
        """Enterprise companies (5000+) should get 4.0x multiplier."""
        mult, label = get_size_multiplier(10000)
        assert mult == 4.0

    def test_industry_factor_healthcare(self):
        """Healthcare should get 1.4x factor."""
        factor, reason = get_industry_factor("healthcare")
        assert factor == 1.4
        assert "HIPAA" in reason

    def test_industry_factor_financial(self):
        """Financial services should get 1.5x factor."""
        factor, reason = get_industry_factor("financial_services")
        assert factor == 1.5

    def test_industry_factor_default(self):
        """Unknown industry should get 1.0x default."""
        factor, reason = get_industry_factor("unknown_industry")
        assert factor == 1.0

    def test_geography_global(self):
        """Global geography should get 1.6x factor."""
        factor, reason = get_geography_factor("global")
        assert factor == 1.6

    def test_maturity_minimal(self):
        """Minimal IT maturity should get 1.6x factor."""
        factor, reason = get_maturity_factor("minimal")
        assert factor == 1.6

    def test_company_profile_total_multiplier(self):
        """Company profile should calculate combined multiplier."""
        profile = CompanyProfile(
            employee_count=300,  # 1.0x
            industry="technology",  # 1.0x
            geography="single_country",  # 1.0x
            it_maturity="standard"  # 1.0x
        )
        total, breakdown = profile.get_total_multiplier()
        assert total == 1.0

    def test_company_profile_large_healthcare(self):
        """Large healthcare company should have high multiplier."""
        profile = CompanyProfile(
            employee_count=3000,  # 3.0x
            industry="healthcare",  # 1.4x
            geography="multi_region",  # 1.4x
            it_maturity="basic"  # 1.3x
        )
        total, breakdown = profile.get_total_multiplier()
        # 3.0 * 1.4 * 1.4 * 1.3 = 7.644
        assert total > 7.0
        assert "size" in breakdown
        assert "industry" in breakdown

    def test_cost_with_profile(self):
        """Costs should scale with company profile."""
        # Base cost (mid-market)
        base_low, base_high = calculate_work_item_cost("ERP integration", "", "Day_100")

        # Large enterprise profile
        large_profile = CompanyProfile(employee_count=6000)  # 4.0x
        large_low, large_high = calculate_work_item_cost(
            "ERP integration", "", "Day_100", large_profile
        )

        # Large should be approximately 4x the base
        assert large_low > base_low * 3.5
        assert large_low < base_low * 4.5

    def test_total_costs_with_profile(self):
        """Total costs should include methodology breakdown."""
        profile = CompanyProfile(
            employee_count=1500,
            industry="financial_services",
            geography="multi_region"
        )
        work_items = [
            {"title": "SAP migration", "description": "", "phase": "Day_100"},
            {"title": "SSO setup", "description": "", "phase": "Day_1"},
        ]
        result = calculate_total_costs(work_items, profile)

        assert "methodology" in result
        assert "multiplier_applied" in result
        assert result["multiplier_applied"] > 1.0  # Should be elevated
        assert "base_total" in result
        assert result["total"]["low"] > result["base_total"]["low"]

    def test_report_includes_company_profile(self):
        """Consistency report should include company profile details."""
        profile = CompanyProfile(
            employee_count=500,
            industry="manufacturing"
        )
        report = generate_consistency_report(
            facts=[{"item": "VMware"}],
            gaps=[],
            risks=[{"severity": "medium", "title": "Risk", "description": ""}],
            work_items=[{"title": "Task", "description": "", "phase": "Day_100"}],
            company_profile=profile
        )

        assert "company_profile" in report
        assert "methodology_summary" in report
        assert report["company_profile"]["employee_count"] == 500
        assert report["company_profile"]["industry"] == "manufacturing"

    def test_multipliers_are_deterministic(self):
        """Same profile should always produce same multiplier."""
        profile = CompanyProfile(
            employee_count=750,
            industry="healthcare",
            geography="global",
            it_maturity="basic"
        )

        mult1, _ = profile.get_total_multiplier()
        mult2, _ = profile.get_total_multiplier()

        assert mult1 == mult2
