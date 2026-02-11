"""
Unit Tests for Organization Assumption Engine

Tests assumption generation logic for MISSING and PARTIAL hierarchy scenarios.
Part of adaptive organization extraction feature (spec 09).
"""

import pytest
from datetime import datetime

from stores.fact_store import FactStore
from services.org_hierarchy_detector import HierarchyPresence, HierarchyPresenceStatus
from services.org_assumption_engine import (
    generate_org_assumptions,
    OrganizationAssumption,
    _determine_industry,
    _extract_total_headcount,
    _adjust_for_company_size,
    _infer_layer_from_title,
    INDUSTRY_ORG_DEPTH
)


class TestAssumptionGeneration:
    """Test main assumption generation logic."""

    def test_generate_assumptions_full_hierarchy(self):
        """Test that FULL hierarchy generates NO assumptions."""
        # Arrange
        fact_store = FactStore(deal_id="test-deal")
        hierarchy_presence = HierarchyPresence(
            status=HierarchyPresenceStatus.FULL,
            confidence=0.9,
            has_reports_to=True,
            has_explicit_layers=True,
            has_span_data=True,
            has_org_chart=True,
            leadership_count=3,
            total_role_count=12,
            roles_with_reports_to=11,
            gaps=[],
            detection_timestamp=datetime.utcnow().isoformat(),
            fact_count=12
        )

        # Act
        assumptions = generate_org_assumptions(
            fact_store, hierarchy_presence, entity="target"
        )

        # Assert
        assert len(assumptions) == 0

    def test_generate_assumptions_missing_hierarchy(self):
        """Test MISSING hierarchy generates full structure."""
        # Arrange
        fact_store = FactStore(deal_id="test-deal")
        hierarchy_presence = HierarchyPresence(
            status=HierarchyPresenceStatus.MISSING,
            confidence=0.7,
            has_reports_to=False,
            has_explicit_layers=False,
            has_span_data=False,
            has_org_chart=False,
            leadership_count=0,
            total_role_count=3,
            roles_with_reports_to=0,
            gaps=["Reporting lines", "Layers", "Span", "Org chart"],
            detection_timestamp=datetime.utcnow().isoformat(),
            fact_count=3
        )

        company_profile = {
            'industry': 'technology',
            'headcount': 50
        }

        # Act
        assumptions = generate_org_assumptions(
            fact_store, hierarchy_presence, entity="target",
            company_profile=company_profile
        )

        # Assert
        assert len(assumptions) >= 5  # At least CIO, VPs, structure note
        assert len(assumptions) <= 15  # Not excessive
        assert all(a.entity == "target" for a in assumptions)
        assert all(0.6 <= a.confidence <= 0.8 for a in assumptions)
        assert any(a.item == "Chief Information Officer (CIO)" for a in assumptions)
        assert any("VP" in a.item for a in assumptions)

    def test_generate_assumptions_partial_hierarchy(self):
        """Test PARTIAL hierarchy generates gap-filling only."""
        # Arrange
        fact_store = FactStore(deal_id="test-deal")

        # Add some existing roles (PARTIAL data)
        for i in range(3):
            fact_store.add_fact(
                domain="organization",
                category="leadership",
                item=f"VP of Infrastructure {i}",
                details={},  # No reports_to or layer
                status="documented",
                evidence={'exact_quote': f'VP {i} exists'},
                entity="target"
            )

        hierarchy_presence = HierarchyPresence(
            status=HierarchyPresenceStatus.PARTIAL,
            confidence=0.65,
            has_reports_to=False,
            has_explicit_layers=False,
            has_span_data=False,
            has_org_chart=False,
            leadership_count=3,
            total_role_count=3,
            roles_with_reports_to=0,
            gaps=["Reporting lines", "Layers", "Span"],
            detection_timestamp=datetime.utcnow().isoformat(),
            fact_count=3
        )

        # Act
        assumptions = generate_org_assumptions(
            fact_store, hierarchy_presence, entity="target"
        )

        # Assert
        assert len(assumptions) > 0  # Should fill gaps
        assert len(assumptions) < 10  # But not full structure
        assert all(a.entity == "target" for a in assumptions)
        assert all(0.55 <= a.confidence <= 0.7 for a in assumptions)

    def test_generate_assumptions_unknown_hierarchy(self):
        """Test UNKNOWN hierarchy generates NO assumptions."""
        # Arrange
        fact_store = FactStore(deal_id="test-deal")
        hierarchy_presence = HierarchyPresence(
            status=HierarchyPresenceStatus.UNKNOWN,
            confidence=0.0,
            has_reports_to=False,
            has_explicit_layers=False,
            has_span_data=False,
            has_org_chart=False,
            leadership_count=0,
            total_role_count=0,
            roles_with_reports_to=0,
            gaps=["No data"],
            detection_timestamp=datetime.utcnow().isoformat(),
            fact_count=0
        )

        # Act
        assumptions = generate_org_assumptions(
            fact_store, hierarchy_presence, entity="target"
        )

        # Assert
        assert len(assumptions) == 0


class TestIndustryMapping:
    """Test industry determination logic."""

    def test_determine_industry_from_profile_tech(self):
        """Test industry determined from company_profile."""
        # Arrange
        fact_store = FactStore(deal_id="test-deal")
        company_profile = {'industry': 'software'}

        # Act
        industry = _determine_industry(company_profile, fact_store, "target")

        # Assert
        assert industry == "technology"

    def test_determine_industry_from_profile_manufacturing(self):
        """Test manufacturing industry detection."""
        # Arrange
        fact_store = FactStore(deal_id="test-deal")
        company_profile = {'industry': 'industrial production'}

        # Act
        industry = _determine_industry(company_profile, fact_store, "target")

        # Assert
        assert industry == "manufacturing"

    def test_determine_industry_from_facts(self):
        """Test industry determined from business_context facts."""
        # Arrange
        fact_store = FactStore(deal_id="test-deal")
        fact_store.add_fact(
            domain="organization",
            category="business_context",
            item="Company Overview",
            details={'industry': 'retail e-commerce'},
            status="documented",
            evidence={'exact_quote': 'Leading retail e-commerce company'},
            entity="target"
        )

        # Act
        industry = _determine_industry(None, fact_store, "target")

        # Assert
        assert industry == "retail"

    def test_determine_industry_default(self):
        """Test fallback to default industry."""
        # Arrange
        fact_store = FactStore(deal_id="test-deal")

        # Act
        industry = _determine_industry(None, fact_store, "target")

        # Assert
        assert industry == "default"


class TestHeadcountExtraction:
    """Test headcount extraction logic."""

    def test_extract_headcount_from_profile(self):
        """Test headcount from company_profile."""
        # Arrange
        fact_store = FactStore(deal_id="test-deal")
        company_profile = {'headcount': 150}

        # Act
        headcount = _extract_total_headcount(company_profile, fact_store, "target")

        # Assert
        assert headcount == 150

    def test_extract_headcount_from_profile_employee_count(self):
        """Test headcount from employee_count field."""
        # Arrange
        fact_store = FactStore(deal_id="test-deal")
        company_profile = {'employee_count': 200}

        # Act
        headcount = _extract_total_headcount(company_profile, fact_store, "target")

        # Assert
        assert headcount == 200

    def test_extract_headcount_from_facts(self):
        """Test headcount from fact details."""
        # Arrange
        fact_store = FactStore(deal_id="test-deal")
        fact_store.add_fact(
            domain="organization",
            category="leadership",
            item="IT Organization",
            details={'total_headcount': 75},
            status="documented",
            evidence={'exact_quote': '75 IT employees'},
            entity="target"
        )

        # Act
        headcount = _extract_total_headcount(None, fact_store, "target")

        # Assert
        assert headcount == 75

    def test_extract_headcount_default(self):
        """Test default headcount when not found."""
        # Arrange
        fact_store = FactStore(deal_id="test-deal")

        # Act
        headcount = _extract_total_headcount(None, fact_store, "target")

        # Assert
        assert headcount == 50  # Default


class TestCompanySizeAdjustment:
    """Test org structure adjustment by company size."""

    def test_adjust_for_very_small_company(self):
        """Test very small company (<20 employees) → flat structure."""
        # Arrange
        benchmarks = INDUSTRY_ORG_DEPTH['technology'].copy()

        # Act
        adjusted = _adjust_for_company_size(benchmarks, 15)

        # Assert
        assert adjusted['typical_layers'] == 2  # Flat
        assert adjusted['span_leadership'] >= 8  # Wide span

    def test_adjust_for_small_company(self):
        """Test small company (20-50) → minimal hierarchy."""
        # Arrange
        benchmarks = INDUSTRY_ORG_DEPTH['technology'].copy()

        # Act
        adjusted = _adjust_for_company_size(benchmarks, 35)

        # Assert
        assert adjusted['typical_layers'] == 3

    def test_adjust_for_medium_company(self):
        """Test medium company (50-150) → use benchmarks as-is."""
        # Arrange
        benchmarks = INDUSTRY_ORG_DEPTH['manufacturing'].copy()
        original_layers = benchmarks['typical_layers']

        # Act
        adjusted = _adjust_for_company_size(benchmarks, 100)

        # Assert
        assert adjusted['typical_layers'] == original_layers

    def test_adjust_for_large_company(self):
        """Test large company (150-500) → add layer."""
        # Arrange
        benchmarks = INDUSTRY_ORG_DEPTH['technology'].copy()
        original_layers = benchmarks['typical_layers']

        # Act
        adjusted = _adjust_for_company_size(benchmarks, 300)

        # Assert
        assert adjusted['typical_layers'] == original_layers + 1
        assert adjusted['span_leadership'] < benchmarks['span_leadership']

    def test_adjust_for_very_large_company(self):
        """Test very large company (500+) → add 2 layers."""
        # Arrange
        benchmarks = INDUSTRY_ORG_DEPTH['technology'].copy()
        original_layers = benchmarks['typical_layers']

        # Act
        adjusted = _adjust_for_company_size(benchmarks, 600)

        # Assert
        assert adjusted['typical_layers'] == original_layers + 2


class TestRoleTitleInference:
    """Test layer inference from role titles."""

    def test_infer_layer_cio(self):
        """Test C-suite detection."""
        assert _infer_layer_from_title("Chief Information Officer") == 0
        assert _infer_layer_from_title("CIO") == 0
        assert _infer_layer_from_title("CTO") == 0

    def test_infer_layer_vp(self):
        """Test VP detection."""
        assert _infer_layer_from_title("VP of Infrastructure") == 1
        assert _infer_layer_from_title("Vice President of IT") == 1
        assert _infer_layer_from_title("Senior Vice President") == 1

    def test_infer_layer_director(self):
        """Test Director detection."""
        assert _infer_layer_from_title("Director of IT Services") == 2
        assert _infer_layer_from_title("Senior Director") == 2

    def test_infer_layer_manager(self):
        """Test Manager detection."""
        assert _infer_layer_from_title("IT Manager") == 3
        assert _infer_layer_from_title("Senior Manager") == 3
        assert _infer_layer_from_title("Team Lead") == 3

    def test_infer_layer_ic(self):
        """Test IC (individual contributor) detection."""
        assert _infer_layer_from_title("Senior Engineer") == 4
        assert _infer_layer_from_title("IT Analyst") == 4
        assert _infer_layer_from_title("Systems Administrator") == 4

    def test_infer_layer_ambiguous(self):
        """Test ambiguous titles return None."""
        assert _infer_layer_from_title("IT Staff") is None
        assert _infer_layer_from_title("Technical Resource") is None


class TestAssumptionDataClass:
    """Test OrganizationAssumption dataclass."""

    def test_assumption_to_fact_conversion(self):
        """Test conversion to fact dict."""
        # Arrange
        assumption = OrganizationAssumption(
            item="VP of Infrastructure",
            category="leadership",
            details={'reports_to': 'CIO', 'layer': 1},
            confidence=0.70,
            assumption_basis="Industry benchmark (technology)",
            entity="target"
        )

        # Act
        fact_dict = assumption.to_fact(deal_id="test-deal")

        # Assert
        assert fact_dict['domain'] == 'organization'
        assert fact_dict['category'] == 'leadership'
        assert fact_dict['item'] == 'VP of Infrastructure'
        assert fact_dict['details']['data_source'] == 'assumed'
        assert fact_dict['details']['reports_to'] == 'CIO'
        assert fact_dict['entity'] == 'target'
        assert fact_dict['evidence']['confidence'] == 0.70
        assert 'Industry benchmark' in fact_dict['evidence']['exact_quote']

    def test_assumption_confidence_range(self):
        """Test assumptions have confidence in 0.6-0.8 range."""
        # Arrange
        fact_store = FactStore(deal_id="test-deal")
        hierarchy_presence = HierarchyPresence(
            status=HierarchyPresenceStatus.MISSING,
            confidence=0.7,
            has_reports_to=False,
            has_explicit_layers=False,
            has_span_data=False,
            has_org_chart=False,
            leadership_count=0,
            total_role_count=2,
            roles_with_reports_to=0,
            gaps=["All"],
            detection_timestamp=datetime.utcnow().isoformat(),
            fact_count=2
        )

        # Act
        assumptions = generate_org_assumptions(
            fact_store, hierarchy_presence, entity="target",
            company_profile={'industry': 'technology', 'headcount': 50}
        )

        # Assert
        for assumption in assumptions:
            assert 0.6 <= assumption.confidence <= 0.8


class TestEntityPropagation:
    """Test entity field propagation."""

    def test_assumptions_entity_target(self):
        """Test all assumptions inherit entity=target."""
        # Arrange
        fact_store = FactStore(deal_id="test-deal")
        hierarchy_presence = HierarchyPresence(
            status=HierarchyPresenceStatus.MISSING,
            confidence=0.7,
            has_reports_to=False,
            has_explicit_layers=False,
            has_span_data=False,
            has_org_chart=False,
            leadership_count=0,
            total_role_count=2,
            roles_with_reports_to=0,
            gaps=["All"],
            detection_timestamp=datetime.utcnow().isoformat(),
            fact_count=2
        )

        # Act
        assumptions = generate_org_assumptions(
            fact_store, hierarchy_presence, entity="target"
        )

        # Assert
        assert all(a.entity == "target" for a in assumptions)

    def test_assumptions_entity_buyer(self):
        """Test all assumptions inherit entity=buyer."""
        # Arrange
        fact_store = FactStore(deal_id="test-deal")
        hierarchy_presence = HierarchyPresence(
            status=HierarchyPresenceStatus.MISSING,
            confidence=0.7,
            has_reports_to=False,
            has_explicit_layers=False,
            has_span_data=False,
            has_org_chart=False,
            leadership_count=0,
            total_role_count=2,
            roles_with_reports_to=0,
            gaps=["All"],
            detection_timestamp=datetime.utcnow().isoformat(),
            fact_count=2
        )

        # Act
        assumptions = generate_org_assumptions(
            fact_store, hierarchy_presence, entity="buyer"
        )

        # Assert
        assert all(a.entity == "buyer" for a in assumptions)
