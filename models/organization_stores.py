"""
Organization Data Stores and Result Models

Contains:
- OrganizationDataStore: Central store for all organization data
- Comparison result models for benchmark analysis
- Summary models for MSP and shared services
- Complete analysis result container
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
import json

from models.organization_models import (
    StaffMember,
    CategorySummary,
    RoleSummary,
    MSPRelationship,
    SharedServiceDependency,
    BenchmarkProfile,
    BenchmarkRange,
    RoleCategory,
    TSAItem,
    StaffingNeed,
    ExpectedRole
)


# =============================================================================
# COMPARISON RESULT MODELS
# =============================================================================

@dataclass
class CategoryComparison:
    """
    Comparison result for a single category.

    Shows how actual staffing compares to benchmark for one
    functional category (e.g., Infrastructure, Applications).
    """
    category: str
    category_display: str
    actual_count: int
    benchmark_min: int
    benchmark_typical: int
    benchmark_max: int
    variance: int  # Positive = over, Negative = under
    status: str  # "in_range" | "understaffed" | "overstaffed"
    analysis: str = ""

    @property
    def variance_percentage(self) -> float:
        """Variance as percentage of typical."""
        if self.benchmark_typical == 0:
            return 0.0
        return (self.variance / self.benchmark_typical) * 100

    def to_dict(self) -> Dict[str, Any]:
        return {
            'category': self.category,
            'category_display': self.category_display,
            'actual_count': self.actual_count,
            'benchmark_min': self.benchmark_min,
            'benchmark_typical': self.benchmark_typical,
            'benchmark_max': self.benchmark_max,
            'variance': self.variance,
            'variance_percentage': round(self.variance_percentage, 1),
            'status': self.status,
            'analysis': self.analysis
        }


@dataclass
class MissingRole:
    """
    A role that is expected but not found.

    Identifies gaps where a benchmark expects a role that
    doesn't exist in the actual organization.
    """
    role_title: str
    category: RoleCategory
    importance: str  # "critical" | "high" | "medium" | "low"
    impact: str  # Description of impact of missing this role
    recommendation: str  # What to do about it
    current_coverage: str = "None identified"  # How this is currently handled
    alternatives_checked: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'role_title': self.role_title,
            'category': self.category.value,
            'importance': self.importance,
            'impact': self.impact,
            'recommendation': self.recommendation,
            'current_coverage': self.current_coverage,
            'alternatives_checked': self.alternatives_checked
        }


@dataclass
class OverstaffedArea:
    """
    An area that appears overstaffed relative to benchmarks.

    May indicate inefficiency, or may have valid reasons
    (complex environment, growth plans, etc.).
    """
    category: str
    actual_count: int
    expected_max: int
    overage: int
    potential_reasons: List[str] = field(default_factory=list)
    recommendation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            'category': self.category,
            'actual_count': self.actual_count,
            'expected_max': self.expected_max,
            'overage': self.overage,
            'potential_reasons': self.potential_reasons,
            'recommendation': self.recommendation
        }


@dataclass
class RatioComparison:
    """
    Comparison of a key ratio against benchmark.

    E.g., IT headcount to total employees ratio.
    """
    ratio_name: str
    actual_value: float
    benchmark_min: float
    benchmark_typical: float
    benchmark_max: float
    status: str  # "in_range" | "below" | "above"
    analysis: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            'ratio_name': self.ratio_name,
            'actual_value': round(self.actual_value, 3),
            'benchmark_min': self.benchmark_min,
            'benchmark_typical': self.benchmark_typical,
            'benchmark_max': self.benchmark_max,
            'status': self.status,
            'analysis': self.analysis
        }


@dataclass
class StaffingComparisonResult:
    """
    Complete result of staffing vs benchmark comparison.

    Contains all category comparisons, missing roles,
    overstaffed areas, and ratio analysis.
    """
    benchmark_profile_id: str
    benchmark_profile_name: str
    comparison_date: str
    overall_status: str  # "aligned" | "understaffed" | "overstaffed" | "mixed"

    # Totals
    total_actual: int = 0
    total_expected_min: int = 0
    total_expected_typical: int = 0
    total_expected_max: int = 0

    # Detailed comparisons
    category_comparisons: List[CategoryComparison] = field(default_factory=list)
    missing_roles: List[MissingRole] = field(default_factory=list)
    overstaffed_areas: List[OverstaffedArea] = field(default_factory=list)
    ratio_comparisons: List[RatioComparison] = field(default_factory=list)

    # Summary
    key_findings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def get_critical_missing_roles(self) -> List[MissingRole]:
        """Get roles that are critical and missing."""
        return [r for r in self.missing_roles if r.importance == 'critical']

    def get_understaffed_categories(self) -> List[CategoryComparison]:
        """Get categories that are understaffed."""
        return [c for c in self.category_comparisons if c.status == 'understaffed']

    def to_dict(self) -> Dict[str, Any]:
        return {
            'benchmark_profile_id': self.benchmark_profile_id,
            'benchmark_profile_name': self.benchmark_profile_name,
            'comparison_date': self.comparison_date,
            'overall_status': self.overall_status,
            'total_actual': self.total_actual,
            'total_expected_min': self.total_expected_min,
            'total_expected_typical': self.total_expected_typical,
            'total_expected_max': self.total_expected_max,
            'category_comparisons': [c.to_dict() for c in self.category_comparisons],
            'missing_roles': [r.to_dict() for r in self.missing_roles],
            'overstaffed_areas': [o.to_dict() for o in self.overstaffed_areas],
            'ratio_comparisons': [r.to_dict() for r in self.ratio_comparisons],
            'key_findings': self.key_findings,
            'recommendations': self.recommendations
        }


# =============================================================================
# SUMMARY MODELS
# =============================================================================

@dataclass
class MSPSummary:
    """
    Summary of all MSP/outsourcing relationships.

    Aggregates data across all MSP relationships for
    dashboard display.
    """
    total_msp_count: int = 0
    total_fte_equivalent: float = 0.0
    total_annual_cost: float = 0.0
    total_replacement_cost: float = 0.0
    high_risk_count: int = 0
    critical_services_count: int = 0
    services_without_backup: int = 0
    earliest_expiry: Optional[str] = None
    key_risks: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_msp_count': self.total_msp_count,
            'total_fte_equivalent': self.total_fte_equivalent,
            'total_annual_cost': self.total_annual_cost,
            'total_replacement_cost': self.total_replacement_cost,
            'high_risk_count': self.high_risk_count,
            'critical_services_count': self.critical_services_count,
            'services_without_backup': self.services_without_backup,
            'earliest_expiry': self.earliest_expiry,
            'key_risks': self.key_risks
        }


@dataclass
class SharedServicesSummary:
    """
    Summary of shared services dependencies.

    Aggregates hidden headcount needs and TSA recommendations.
    """
    total_dependencies: int = 0
    total_fte_equivalent: float = 0.0
    transferring_fte: float = 0.0
    non_transferring_fte: float = 0.0
    hidden_headcount_need: float = 0.0
    hidden_cost_annual: float = 0.0
    tsa_candidate_count: int = 0
    critical_dependencies: int = 0
    key_concerns: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_dependencies': self.total_dependencies,
            'total_fte_equivalent': self.total_fte_equivalent,
            'transferring_fte': self.transferring_fte,
            'non_transferring_fte': self.non_transferring_fte,
            'hidden_headcount_need': self.hidden_headcount_need,
            'hidden_cost_annual': self.hidden_cost_annual,
            'tsa_candidate_count': self.tsa_candidate_count,
            'critical_dependencies': self.critical_dependencies,
            'key_concerns': self.key_concerns
        }


@dataclass
class TotalITCostSummary:
    """
    Complete IT cost picture including hidden costs.

    Shows visible costs (internal staff, MSPs) plus hidden
    costs (shared services that need replacement).
    """
    # Visible costs
    internal_staff_cost: float = 0.0
    internal_fte_count: int = 0
    contractor_cost: float = 0.0
    contractor_count: int = 0
    msp_cost: float = 0.0
    msp_fte_equivalent: float = 0.0

    # Hidden costs
    shared_services_hidden_cost: float = 0.0
    shared_services_fte: float = 0.0

    # Totals
    total_visible_cost: float = 0.0
    total_true_cost: float = 0.0  # Including hidden
    total_fte_equivalent: float = 0.0

    def calculate_totals(self):
        """Calculate total fields."""
        self.total_visible_cost = self.internal_staff_cost + self.contractor_cost + self.msp_cost
        self.total_true_cost = self.total_visible_cost + self.shared_services_hidden_cost
        self.total_fte_equivalent = (
            self.internal_fte_count +
            self.contractor_count +
            self.msp_fte_equivalent +
            self.shared_services_fte
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'internal_staff_cost': self.internal_staff_cost,
            'internal_fte_count': self.internal_fte_count,
            'contractor_cost': self.contractor_cost,
            'contractor_count': self.contractor_count,
            'msp_cost': self.msp_cost,
            'msp_fte_equivalent': self.msp_fte_equivalent,
            'shared_services_hidden_cost': self.shared_services_hidden_cost,
            'shared_services_fte': self.shared_services_fte,
            'total_visible_cost': self.total_visible_cost,
            'total_true_cost': self.total_true_cost,
            'total_fte_equivalent': self.total_fte_equivalent
        }


# =============================================================================
# MAIN DATA STORE
# =============================================================================

@dataclass
class OrganizationDataStore:
    """
    Central store for all organization-related data.

    Holds census data, MSP relationships, shared service dependencies,
    benchmark comparison results, and calculated summaries.
    """

    # Census data
    staff_members: List[StaffMember] = field(default_factory=list)
    category_summaries: Dict[str, CategorySummary] = field(default_factory=dict)
    role_summaries: Dict[str, RoleSummary] = field(default_factory=dict)

    # MSP/Outsourcing
    msp_relationships: List[MSPRelationship] = field(default_factory=list)

    # Shared services
    shared_service_dependencies: List[SharedServiceDependency] = field(default_factory=list)

    # Benchmark comparison
    active_benchmark: Optional[BenchmarkProfile] = None
    benchmark_comparison: Optional[StaffingComparisonResult] = None

    # Calculated totals
    total_internal_fte: int = 0
    total_contractor: int = 0
    total_msp_fte_equivalent: float = 0.0
    total_shared_services_fte: float = 0.0
    total_compensation: float = 0.0
    hidden_headcount_need: float = 0.0

    # Authoritative headcount from IT Budget fact (when available)
    # This takes precedence over len(staff_members) since it's the stated official count
    authoritative_headcount: Optional[int] = None

    # Summaries
    msp_summary: Optional[MSPSummary] = None
    shared_services_summary: Optional[SharedServicesSummary] = None
    cost_summary: Optional[TotalITCostSummary] = None

    # Metadata
    last_updated: Optional[str] = None
    data_sources: List[str] = field(default_factory=list)

    def add_staff_member(self, member: StaffMember):
        """Add a staff member and update counts."""
        self.staff_members.append(member)
        self._update_counts()

    def add_msp_relationship(self, msp: MSPRelationship):
        """Add an MSP relationship and update summaries."""
        self.msp_relationships.append(msp)
        self._update_msp_summary()

    def add_shared_service(self, dep: SharedServiceDependency):
        """Add a shared service dependency and update summaries."""
        self.shared_service_dependencies.append(dep)
        self._update_shared_services_summary()

    def _update_counts(self):
        """Recalculate staff counts."""
        from models.organization_models import EmploymentType

        self.total_internal_fte = sum(
            1 for s in self.staff_members
            if s.employment_type == EmploymentType.FTE and s.entity == 'target'
        )
        self.total_contractor = sum(
            1 for s in self.staff_members
            if s.employment_type == EmploymentType.CONTRACTOR and s.entity == 'target'
        )
        self.total_compensation = sum(
            s.total_compensation for s in self.staff_members
            if s.entity == 'target' and s.total_compensation
        )

    def _update_msp_summary(self):
        """Recalculate MSP summary."""
        target_msps = [m for m in self.msp_relationships if m.entity == 'target']

        self.msp_summary = MSPSummary(
            total_msp_count=len(target_msps),
            total_fte_equivalent=sum(m.total_fte_equivalent for m in target_msps),
            total_annual_cost=sum(m.contract_value_annual for m in target_msps),
            total_replacement_cost=sum(m.replacement_cost_estimate for m in target_msps),
            high_risk_count=sum(1 for m in target_msps if m.risk_level in ['critical', 'high']),
            critical_services_count=sum(
                1 for m in target_msps
                for s in m.services if s.criticality == 'critical'
            ),
            services_without_backup=sum(
                len(m.services_without_backup) for m in target_msps
            )
        )
        self.total_msp_fte_equivalent = self.msp_summary.total_fte_equivalent

    def _update_shared_services_summary(self):
        """Recalculate shared services summary."""
        deps = self.shared_service_dependencies

        self.shared_services_summary = SharedServicesSummary(
            total_dependencies=len(deps),
            total_fte_equivalent=sum(d.fte_equivalent for d in deps),
            transferring_fte=sum(d.fte_equivalent for d in deps if d.will_transfer),
            non_transferring_fte=sum(d.fte_equivalent for d in deps if not d.will_transfer),
            hidden_headcount_need=sum(d.replacement_fte_need for d in deps),
            hidden_cost_annual=sum(d.replacement_cost_annual for d in deps),
            tsa_candidate_count=sum(1 for d in deps if d.tsa_candidate),
            critical_dependencies=sum(1 for d in deps if d.criticality == 'critical')
        )
        self.total_shared_services_fte = self.shared_services_summary.total_fte_equivalent
        self.hidden_headcount_need = self.shared_services_summary.hidden_headcount_need

    def calculate_cost_summary(self) -> TotalITCostSummary:
        """Calculate complete IT cost summary."""
        self.cost_summary = TotalITCostSummary(
            internal_staff_cost=sum(
                s.total_compensation for s in self.staff_members
                if s.employment_type.value == 'fte' and s.entity == 'target'
            ),
            internal_fte_count=self.total_internal_fte,
            contractor_cost=sum(
                s.total_compensation for s in self.staff_members
                if s.employment_type.value == 'contractor' and s.entity == 'target'
            ),
            contractor_count=self.total_contractor,
            msp_cost=sum(m.contract_value_annual for m in self.msp_relationships if m.entity == 'target'),
            msp_fte_equivalent=self.total_msp_fte_equivalent,
            shared_services_hidden_cost=self.shared_services_summary.hidden_cost_annual if self.shared_services_summary else 0,
            shared_services_fte=self.total_shared_services_fte
        )
        self.cost_summary.calculate_totals()
        return self.cost_summary

    def get_staff_by_category(self, category: RoleCategory) -> List[StaffMember]:
        """Get all staff in a category."""
        return [s for s in self.staff_members if s.role_category == category]

    def get_staff_by_entity(self, entity: str) -> List[StaffMember]:
        """Get all staff for an entity (target/buyer)."""
        return [s for s in self.staff_members if s.entity == entity]

    def get_key_persons(self) -> List[StaffMember]:
        """Get all staff flagged as key persons."""
        return [s for s in self.staff_members if s.is_key_person]

    def get_target_headcount(self) -> int:
        """Get total headcount for target entity.

        Uses authoritative_headcount from IT Budget fact if available,
        otherwise falls back to counting staff_members.
        """
        if self.authoritative_headcount is not None:
            return self.authoritative_headcount
        return sum(1 for s in self.staff_members if s.entity == 'target')

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'staff_members': [s.to_dict() for s in self.staff_members],
            'category_summaries': {k: v.to_dict() for k, v in self.category_summaries.items()},
            'msp_relationships': [m.to_dict() for m in self.msp_relationships],
            'shared_service_dependencies': [d.to_dict() for d in self.shared_service_dependencies],
            'active_benchmark': self.active_benchmark.to_dict() if self.active_benchmark else None,
            'benchmark_comparison': self.benchmark_comparison.to_dict() if self.benchmark_comparison else None,
            'total_internal_fte': self.total_internal_fte,
            'total_contractor': self.total_contractor,
            'total_msp_fte_equivalent': self.total_msp_fte_equivalent,
            'total_shared_services_fte': self.total_shared_services_fte,
            'total_compensation': self.total_compensation,
            'hidden_headcount_need': self.hidden_headcount_need,
            'msp_summary': self.msp_summary.to_dict() if self.msp_summary else None,
            'shared_services_summary': self.shared_services_summary.to_dict() if self.shared_services_summary else None,
            'cost_summary': self.cost_summary.to_dict() if self.cost_summary else None,
            'last_updated': self.last_updated,
            'data_sources': self.data_sources
        }

    def save_to_file(self, filepath: str):
        """Save store to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_from_file(cls, filepath: str) -> 'OrganizationDataStore':
        """Load store from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OrganizationDataStore':
        """Create from dictionary."""
        store = cls()

        # Load staff members
        for s in data.get('staff_members', []):
            store.staff_members.append(StaffMember.from_dict(s))

        # Load MSP relationships
        for m in data.get('msp_relationships', []):
            store.msp_relationships.append(MSPRelationship.from_dict(m))

        # Load shared services
        for d in data.get('shared_service_dependencies', []):
            store.shared_service_dependencies.append(SharedServiceDependency.from_dict(d))

        # Load benchmark
        if data.get('active_benchmark'):
            store.active_benchmark = BenchmarkProfile.from_dict(data['active_benchmark'])

        # Set counts
        store.total_internal_fte = data.get('total_internal_fte', 0)
        store.total_contractor = data.get('total_contractor', 0)
        store.total_msp_fte_equivalent = data.get('total_msp_fte_equivalent', 0)
        store.total_shared_services_fte = data.get('total_shared_services_fte', 0)
        store.total_compensation = data.get('total_compensation', 0)
        store.hidden_headcount_need = data.get('hidden_headcount_need', 0)
        store.last_updated = data.get('last_updated')
        store.data_sources = data.get('data_sources', [])

        return store


# =============================================================================
# COMPLETE ANALYSIS RESULT
# =============================================================================

@dataclass
class OrganizationAnalysisResult:
    """
    Complete organization analysis output.

    Contains all summaries, findings, risks, and recommendations
    from the organization analysis pipeline.
    """

    # Summaries
    staffing_summary: Dict[str, Any] = field(default_factory=dict)
    benchmark_comparison: Optional[StaffingComparisonResult] = None
    msp_summary: Optional[MSPSummary] = None
    shared_services_summary: Optional[SharedServicesSummary] = None
    cost_summary: Optional[TotalITCostSummary] = None

    # Findings (these integrate with the main reasoning engine)
    risks: List[Dict[str, Any]] = field(default_factory=list)
    gaps: List[Dict[str, Any]] = field(default_factory=list)
    observations: List[Dict[str, Any]] = field(default_factory=list)

    # Recommendations
    work_items: List[Dict[str, Any]] = field(default_factory=list)
    tsa_recommendations: List[TSAItem] = field(default_factory=list)
    hiring_recommendations: List[StaffingNeed] = field(default_factory=list)

    # Key metrics
    total_it_headcount: int = 0
    total_it_cost: float = 0.0
    hidden_headcount_need: float = 0.0
    post_close_staffing_cost: float = 0.0

    # Metadata
    analysis_date: str = field(default_factory=lambda: datetime.now().isoformat())
    data_sources: List[str] = field(default_factory=list)

    def get_critical_risks(self) -> List[Dict[str, Any]]:
        """Get risks rated as critical."""
        return [r for r in self.risks if r.get('severity') == 'critical']

    def get_immediate_hiring_needs(self) -> List[StaffingNeed]:
        """Get hiring needs marked as immediate."""
        return [h for h in self.hiring_recommendations if h.urgency == 'immediate']

    def to_dict(self) -> Dict[str, Any]:
        return {
            'staffing_summary': self.staffing_summary,
            'benchmark_comparison': self.benchmark_comparison.to_dict() if self.benchmark_comparison else None,
            'msp_summary': self.msp_summary.to_dict() if self.msp_summary else None,
            'shared_services_summary': self.shared_services_summary.to_dict() if self.shared_services_summary else None,
            'cost_summary': self.cost_summary.to_dict() if self.cost_summary else None,
            'risks': self.risks,
            'gaps': self.gaps,
            'observations': self.observations,
            'work_items': self.work_items,
            'tsa_recommendations': [t.to_dict() for t in self.tsa_recommendations],
            'hiring_recommendations': [h.to_dict() for h in self.hiring_recommendations],
            'total_it_headcount': self.total_it_headcount,
            'total_it_cost': self.total_it_cost,
            'hidden_headcount_need': self.hidden_headcount_need,
            'post_close_staffing_cost': self.post_close_staffing_cost,
            'analysis_date': self.analysis_date,
            'data_sources': self.data_sources
        }

    def save_to_file(self, filepath: str):
        """Save result to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
