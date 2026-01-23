"""
Organization Domain Data Models

Models for IT organization analysis including:
- Staff census data (roles, compensation, tenure)
- MSP/outsourcing relationships
- Shared services dependencies
- Benchmark profiles for comparison
- TSA and staffing needs

These models support the four Organization analysis views:
1. Staffing Census Tree - Role-level drill-down with compensation
2. Benchmark Comparison - Actual vs. expected staffing
3. MSP Dependency Analysis - Outsourced work and risk
4. Shared Services Analysis - Hidden headcount from parent/shared services
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import date
import json


# =============================================================================
# ENUMS
# =============================================================================

class EmploymentType(Enum):
    """Type of employment for a staff member."""
    FTE = "fte"
    CONTRACTOR = "contractor"
    MSP = "msp"
    TEMP = "temp"
    INTERN = "intern"

    @classmethod
    def from_string(cls, value: str) -> 'EmploymentType':
        """Convert string to EmploymentType, with fuzzy matching."""
        value_lower = value.lower().strip()
        mappings = {
            'fte': cls.FTE,
            'full-time': cls.FTE,
            'full time': cls.FTE,
            'employee': cls.FTE,
            'w2': cls.FTE,
            'contractor': cls.CONTRACTOR,
            'contract': cls.CONTRACTOR,
            '1099': cls.CONTRACTOR,
            'consultant': cls.CONTRACTOR,
            'msp': cls.MSP,
            'managed service': cls.MSP,
            'vendor': cls.MSP,
            'outsourced': cls.MSP,
            'temp': cls.TEMP,
            'temporary': cls.TEMP,
            'intern': cls.INTERN,
            'internship': cls.INTERN
        }
        return mappings.get(value_lower, cls.FTE)


class RoleCategory(Enum):
    """Functional category for IT roles."""
    LEADERSHIP = "leadership"
    INFRASTRUCTURE = "infrastructure"
    APPLICATIONS = "applications"
    SECURITY = "security"
    SERVICE_DESK = "service_desk"
    DATA = "data"
    PROJECT_MANAGEMENT = "project_management"
    OTHER = "other"

    @classmethod
    def from_string(cls, value: str) -> 'RoleCategory':
        """Convert string to RoleCategory."""
        value_lower = value.lower().strip()
        mappings = {
            'leadership': cls.LEADERSHIP,
            'executive': cls.LEADERSHIP,
            'management': cls.LEADERSHIP,
            'infrastructure': cls.INFRASTRUCTURE,
            'infra': cls.INFRASTRUCTURE,
            'network': cls.INFRASTRUCTURE,
            'systems': cls.INFRASTRUCTURE,
            'applications': cls.APPLICATIONS,
            'apps': cls.APPLICATIONS,
            'development': cls.APPLICATIONS,
            'software': cls.APPLICATIONS,
            'security': cls.SECURITY,
            'cybersecurity': cls.SECURITY,
            'infosec': cls.SECURITY,
            'service_desk': cls.SERVICE_DESK,
            'service desk': cls.SERVICE_DESK,
            'help desk': cls.SERVICE_DESK,
            'helpdesk': cls.SERVICE_DESK,
            'support': cls.SERVICE_DESK,
            'data': cls.DATA,
            'database': cls.DATA,
            'analytics': cls.DATA,
            'bi': cls.DATA,
            'project_management': cls.PROJECT_MANAGEMENT,
            'project management': cls.PROJECT_MANAGEMENT,
            'pmo': cls.PROJECT_MANAGEMENT
        }
        return mappings.get(value_lower, cls.OTHER)

    @property
    def display_name(self) -> str:
        """Human-readable display name."""
        names = {
            self.LEADERSHIP: "Leadership",
            self.INFRASTRUCTURE: "Infrastructure",
            self.APPLICATIONS: "Applications",
            self.SECURITY: "Security",
            self.SERVICE_DESK: "Service Desk",
            self.DATA: "Data & Analytics",
            self.PROJECT_MANAGEMENT: "Project Management",
            self.OTHER: "Other"
        }
        return names.get(self, "Other")


class DependencyLevel(Enum):
    """Level of dependency on an external provider."""
    FULL = "full"              # Entirely dependent on this provider
    PARTIAL = "partial"        # Mix of internal + external
    SUPPLEMENTAL = "supplemental"  # Internal capability exists, external augments

    @property
    def display_name(self) -> str:
        names = {
            self.FULL: "Full Dependency",
            self.PARTIAL: "Partial Dependency",
            self.SUPPLEMENTAL: "Supplemental"
        }
        return names.get(self, "Unknown")

    @property
    def risk_level(self) -> str:
        """Associated risk level."""
        levels = {
            self.FULL: "high",
            self.PARTIAL: "medium",
            self.SUPPLEMENTAL: "low"
        }
        return levels.get(self, "medium")


# =============================================================================
# CENSUS / STAFFING MODELS
# =============================================================================

@dataclass
class StaffMember:
    """
    Individual person from census data.

    Represents a single IT staff member with their role, compensation,
    and organizational attributes.
    """
    id: str
    name: str
    role_title: str
    role_category: RoleCategory
    department: str
    employment_type: EmploymentType
    base_compensation: float
    total_compensation: Optional[float] = None  # Including bonus/equity
    location: str = "Unknown"
    tenure_years: Optional[float] = None
    hire_date: Optional[str] = None
    reports_to: Optional[str] = None
    entity: str = "target"  # target | buyer | parent
    skills: List[str] = field(default_factory=list)
    is_key_person: bool = False
    key_person_reason: Optional[str] = None
    notes: Optional[str] = None

    def __post_init__(self):
        """Ensure total_compensation defaults to base if not provided."""
        if self.total_compensation is None:
            self.total_compensation = self.base_compensation

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'id': self.id,
            'name': self.name,
            'role_title': self.role_title,
            'role_category': self.role_category.value,
            'department': self.department,
            'employment_type': self.employment_type.value,
            'base_compensation': self.base_compensation,
            'total_compensation': self.total_compensation,
            'location': self.location,
            'tenure_years': self.tenure_years,
            'hire_date': self.hire_date,
            'reports_to': self.reports_to,
            'entity': self.entity,
            'skills': self.skills,
            'is_key_person': self.is_key_person,
            'key_person_reason': self.key_person_reason,
            'notes': self.notes
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StaffMember':
        """Create from dictionary."""
        return cls(
            id=data['id'],
            name=data['name'],
            role_title=data['role_title'],
            role_category=RoleCategory(data['role_category']),
            department=data['department'],
            employment_type=EmploymentType(data['employment_type']),
            base_compensation=data['base_compensation'],
            total_compensation=data.get('total_compensation'),
            location=data.get('location', 'Unknown'),
            tenure_years=data.get('tenure_years'),
            hire_date=data.get('hire_date'),
            reports_to=data.get('reports_to'),
            entity=data.get('entity', 'target'),
            skills=data.get('skills', []),
            is_key_person=data.get('is_key_person', False),
            key_person_reason=data.get('key_person_reason'),
            notes=data.get('notes')
        )


@dataclass
class RoleSummary:
    """
    Aggregated view of a role type.

    Groups staff members with the same role title and provides
    summary statistics.
    """
    role_title: str
    role_category: RoleCategory
    headcount: int
    total_compensation: float
    avg_compensation: float
    avg_tenure: Optional[float] = None
    min_compensation: float = 0.0
    max_compensation: float = 0.0
    members: List[StaffMember] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'role_title': self.role_title,
            'role_category': self.role_category.value,
            'headcount': self.headcount,
            'total_compensation': self.total_compensation,
            'avg_compensation': self.avg_compensation,
            'avg_tenure': self.avg_tenure,
            'min_compensation': self.min_compensation,
            'max_compensation': self.max_compensation,
            'member_ids': [m.id for m in self.members]
        }


@dataclass
class CategorySummary:
    """
    Aggregated view of a category (Infrastructure, Apps, etc.).

    Groups roles within a functional category and provides
    summary statistics.
    """
    category: RoleCategory
    total_headcount: int
    total_compensation: float
    avg_compensation: float = 0.0
    roles: List[RoleSummary] = field(default_factory=list)
    fte_count: int = 0
    contractor_count: int = 0
    msp_count: int = 0

    @property
    def display_name(self) -> str:
        return self.category.display_name

    def to_dict(self) -> Dict[str, Any]:
        return {
            'category': self.category.value,
            'display_name': self.display_name,
            'total_headcount': self.total_headcount,
            'total_compensation': self.total_compensation,
            'avg_compensation': self.avg_compensation,
            'fte_count': self.fte_count,
            'contractor_count': self.contractor_count,
            'msp_count': self.msp_count,
            'roles': [r.to_dict() for r in self.roles]
        }


# =============================================================================
# MSP / OUTSOURCING MODELS
# =============================================================================

@dataclass
class MSPService:
    """
    A specific service provided by an MSP.

    Represents one service line within an MSP relationship,
    with its FTE equivalent and criticality.
    """
    service_name: str
    fte_equivalent: float
    coverage: str = "business_hours"  # "24x7" | "business_hours" | "on_call"
    criticality: str = "medium"  # "critical" | "high" | "medium" | "low"
    internal_backup: bool = False
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'service_name': self.service_name,
            'fte_equivalent': self.fte_equivalent,
            'coverage': self.coverage,
            'criticality': self.criticality,
            'internal_backup': self.internal_backup,
            'description': self.description
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MSPService':
        return cls(
            service_name=data['service_name'],
            fte_equivalent=data['fte_equivalent'],
            coverage=data.get('coverage', 'business_hours'),
            criticality=data.get('criticality', 'medium'),
            internal_backup=data.get('internal_backup', False),
            description=data.get('description')
        )


@dataclass
class MSPRelationship:
    """
    Complete MSP/vendor relationship.

    Represents the full relationship with an MSP including all services,
    contract terms, and risk assessment.
    """
    id: str
    vendor_name: str
    services: List[MSPService]
    contract_value_annual: float
    contract_start: Optional[str] = None
    contract_expiry: Optional[str] = None
    notice_period_days: int = 30
    dependency_level: DependencyLevel = DependencyLevel.PARTIAL
    entity: str = "target"
    notes: Optional[str] = None

    # Calculated fields
    total_fte_equivalent: float = field(init=False)
    replacement_cost_estimate: float = field(init=False)

    def __post_init__(self):
        """Calculate derived fields."""
        self.total_fte_equivalent = sum(s.fte_equivalent for s in self.services)
        # Rough estimate: $100K fully loaded cost per FTE
        self.replacement_cost_estimate = self.total_fte_equivalent * 100000

    @property
    def has_critical_services(self) -> bool:
        """Check if any services are critical."""
        return any(s.criticality == 'critical' for s in self.services)

    @property
    def services_without_backup(self) -> List[MSPService]:
        """Get services that have no internal backup."""
        return [s for s in self.services if not s.internal_backup]

    @property
    def risk_level(self) -> str:
        """Calculate overall risk level."""
        if self.dependency_level == DependencyLevel.FULL and self.has_critical_services:
            return "critical"
        elif self.dependency_level == DependencyLevel.FULL or self.has_critical_services:
            return "high"
        elif len(self.services_without_backup) > len(self.services) / 2:
            return "medium"
        return "low"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'vendor_name': self.vendor_name,
            'services': [s.to_dict() for s in self.services],
            'contract_value_annual': self.contract_value_annual,
            'contract_start': self.contract_start,
            'contract_expiry': self.contract_expiry,
            'notice_period_days': self.notice_period_days,
            'dependency_level': self.dependency_level.value,
            'total_fte_equivalent': self.total_fte_equivalent,
            'replacement_cost_estimate': self.replacement_cost_estimate,
            'risk_level': self.risk_level,
            'entity': self.entity,
            'notes': self.notes
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MSPRelationship':
        return cls(
            id=data['id'],
            vendor_name=data['vendor_name'],
            services=[MSPService.from_dict(s) for s in data['services']],
            contract_value_annual=data['contract_value_annual'],
            contract_start=data.get('contract_start'),
            contract_expiry=data.get('contract_expiry'),
            notice_period_days=data.get('notice_period_days', 30),
            dependency_level=DependencyLevel(data.get('dependency_level', 'partial')),
            entity=data.get('entity', 'target'),
            notes=data.get('notes')
        )


# =============================================================================
# SHARED SERVICES / PARENT DEPENDENCY MODELS
# =============================================================================

@dataclass
class SharedServiceDependency:
    """
    Service provided by parent/shared services that target relies on.

    Represents a service that the target company receives from a parent
    company or shared services center, which may create hidden headcount
    needs post-close.
    """
    id: str
    service_name: str
    provider: str  # "Parent IT", "Shared Services Center", etc.
    fte_equivalent: float
    will_transfer: bool = False  # Will this service transfer in the deal?
    criticality: str = "medium"  # "critical" | "high" | "medium" | "low"
    tsa_candidate: bool = True  # Should this be in a TSA?
    tsa_duration_months: int = 12
    description: Optional[str] = None

    # Calculated fields for replacement planning
    replacement_cost_annual: float = field(init=False)
    replacement_fte_need: float = field(init=False)

    def __post_init__(self):
        """Calculate replacement needs."""
        if not self.will_transfer:
            self.replacement_fte_need = self.fte_equivalent
            # Rough estimate: $100K fully loaded cost per FTE
            self.replacement_cost_annual = self.fte_equivalent * 100000
        else:
            self.replacement_fte_need = 0
            self.replacement_cost_annual = 0

    @property
    def urgency(self) -> str:
        """Determine urgency of addressing this dependency."""
        if self.criticality == 'critical' and not self.will_transfer:
            return "immediate"
        elif self.criticality == 'high' and not self.will_transfer:
            return "day_100"
        else:
            return "year_1"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'service_name': self.service_name,
            'provider': self.provider,
            'fte_equivalent': self.fte_equivalent,
            'will_transfer': self.will_transfer,
            'criticality': self.criticality,
            'tsa_candidate': self.tsa_candidate,
            'tsa_duration_months': self.tsa_duration_months,
            'replacement_cost_annual': self.replacement_cost_annual,
            'replacement_fte_need': self.replacement_fte_need,
            'urgency': self.urgency,
            'description': self.description
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SharedServiceDependency':
        return cls(
            id=data['id'],
            service_name=data['service_name'],
            provider=data['provider'],
            fte_equivalent=data['fte_equivalent'],
            will_transfer=data.get('will_transfer', False),
            criticality=data.get('criticality', 'medium'),
            tsa_candidate=data.get('tsa_candidate', True),
            tsa_duration_months=data.get('tsa_duration_months', 12),
            description=data.get('description')
        )


# =============================================================================
# BENCHMARK MODELS
# =============================================================================

@dataclass
class BenchmarkRange:
    """
    Min/typical/max range for a metric.

    Used for staffing counts, ratios, and other benchmark comparisons.
    """
    min_value: float
    typical_value: float
    max_value: float

    def contains(self, value: float) -> bool:
        """Check if value falls within the range."""
        return self.min_value <= value <= self.max_value

    def variance_from_typical(self, value: float) -> float:
        """Calculate variance from typical (positive = over, negative = under)."""
        return value - self.typical_value

    def status(self, value: float) -> str:
        """Determine status based on value."""
        if value < self.min_value:
            return "understaffed"
        elif value > self.max_value:
            return "overstaffed"
        return "in_range"

    def to_dict(self) -> Dict[str, float]:
        return {
            'min': self.min_value,
            'typical': self.typical_value,
            'max': self.max_value
        }

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> 'BenchmarkRange':
        return cls(
            min_value=data['min'],
            typical_value=data['typical'],
            max_value=data['max']
        )


@dataclass
class ExpectedRole:
    """
    A role that should exist based on benchmarks.

    Represents a specific role that companies of a certain profile
    are expected to have.
    """
    role_title: str
    category: RoleCategory
    importance: str = "medium"  # "critical" | "high" | "medium" | "low"
    typical_count: int = 1
    description: Optional[str] = None
    alternatives: List[str] = field(default_factory=list)  # Alternative titles that satisfy this

    def to_dict(self) -> Dict[str, Any]:
        return {
            'role_title': self.role_title,
            'category': self.category.value,
            'importance': self.importance,
            'typical_count': self.typical_count,
            'description': self.description,
            'alternatives': self.alternatives
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExpectedRole':
        return cls(
            role_title=data['role_title'],
            category=RoleCategory(data['category']),
            importance=data.get('importance', 'medium'),
            typical_count=data.get('typical_count', 1),
            description=data.get('description'),
            alternatives=data.get('alternatives', [])
        )


@dataclass
class BenchmarkProfile:
    """
    Benchmark profile for comparison.

    Defines expected IT staffing for companies matching certain
    characteristics (revenue, size, industry).
    """
    profile_id: str
    profile_name: str
    description: str

    # Company characteristics this applies to
    revenue_range_min: float
    revenue_range_max: float
    employee_range_min: int
    employee_range_max: int
    industries: List[str]

    # Expected headcounts by category
    expected_staffing: Dict[str, BenchmarkRange] = field(default_factory=dict)

    # Expected specific roles
    expected_roles: List[ExpectedRole] = field(default_factory=list)

    # Key ratios
    it_to_employee_ratio: Optional[BenchmarkRange] = None
    apps_per_developer_ratio: Optional[BenchmarkRange] = None

    notes: Optional[str] = None

    def matches_company(self, revenue: float, employees: int, industry: str) -> bool:
        """Check if this profile matches a company's characteristics."""
        revenue_match = self.revenue_range_min <= revenue <= self.revenue_range_max
        employee_match = self.employee_range_min <= employees <= self.employee_range_max
        industry_match = industry.lower() in [i.lower() for i in self.industries] or 'general' in self.industries
        return revenue_match and employee_match and industry_match

    def match_score(self, revenue: float, employees: int, industry: str) -> int:
        """Calculate how well this profile matches (higher = better match)."""
        score = 0

        # Revenue in range
        if self.revenue_range_min <= revenue <= self.revenue_range_max:
            score += 10
            # Bonus for being in middle of range
            mid_revenue = (self.revenue_range_min + self.revenue_range_max) / 2
            if abs(revenue - mid_revenue) < mid_revenue * 0.3:
                score += 5

        # Employees in range
        if self.employee_range_min <= employees <= self.employee_range_max:
            score += 10
            mid_emp = (self.employee_range_min + self.employee_range_max) / 2
            if abs(employees - mid_emp) < mid_emp * 0.3:
                score += 5

        # Industry match
        if industry.lower() in [i.lower() for i in self.industries]:
            score += 20  # Strong bonus for exact industry match
        elif 'general' in self.industries:
            score += 5

        return score

    def get_expected_staffing_for_category(self, category: str) -> Optional[BenchmarkRange]:
        """Get expected staffing range for a category."""
        return self.expected_staffing.get(category)

    def get_critical_roles(self) -> List[ExpectedRole]:
        """Get roles marked as critical."""
        return [r for r in self.expected_roles if r.importance == 'critical']

    def to_dict(self) -> Dict[str, Any]:
        return {
            'profile_id': self.profile_id,
            'profile_name': self.profile_name,
            'description': self.description,
            'revenue_range_min': self.revenue_range_min,
            'revenue_range_max': self.revenue_range_max,
            'employee_range_min': self.employee_range_min,
            'employee_range_max': self.employee_range_max,
            'industries': self.industries,
            'expected_staffing': {k: v.to_dict() for k, v in self.expected_staffing.items()},
            'expected_roles': [r.to_dict() for r in self.expected_roles],
            'it_to_employee_ratio': self.it_to_employee_ratio.to_dict() if self.it_to_employee_ratio else None,
            'apps_per_developer_ratio': self.apps_per_developer_ratio.to_dict() if self.apps_per_developer_ratio else None,
            'notes': self.notes
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BenchmarkProfile':
        expected_staffing = {}
        for k, v in data.get('expected_staffing', {}).items():
            expected_staffing[k] = BenchmarkRange.from_dict(v)

        expected_roles = [ExpectedRole.from_dict(r) for r in data.get('expected_roles', [])]

        it_ratio = None
        if data.get('it_to_employee_ratio'):
            it_ratio = BenchmarkRange.from_dict(data['it_to_employee_ratio'])

        apps_ratio = None
        if data.get('apps_per_developer_ratio'):
            apps_ratio = BenchmarkRange.from_dict(data['apps_per_developer_ratio'])

        return cls(
            profile_id=data['profile_id'],
            profile_name=data['profile_name'],
            description=data['description'],
            revenue_range_min=data['revenue_range_min'],
            revenue_range_max=data['revenue_range_max'],
            employee_range_min=data['employee_range_min'],
            employee_range_max=data['employee_range_max'],
            industries=data['industries'],
            expected_staffing=expected_staffing,
            expected_roles=expected_roles,
            it_to_employee_ratio=it_ratio,
            apps_per_developer_ratio=apps_ratio,
            notes=data.get('notes')
        )


# =============================================================================
# TSA AND STAFFING NEEDS
# =============================================================================

@dataclass
class TSAItem:
    """
    Transition Services Agreement line item.

    Represents a service that should be included in the TSA
    to cover shared service dependencies during transition.
    """
    id: str
    service: str
    provider: str
    duration_months: int
    estimated_monthly_cost: float
    exit_criteria: str
    replacement_plan: str
    related_dependency_id: Optional[str] = None

    @property
    def total_cost(self) -> float:
        return self.duration_months * self.estimated_monthly_cost

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'service': self.service,
            'provider': self.provider,
            'duration_months': self.duration_months,
            'estimated_monthly_cost': self.estimated_monthly_cost,
            'total_cost': self.total_cost,
            'exit_criteria': self.exit_criteria,
            'replacement_plan': self.replacement_plan,
            'related_dependency_id': self.related_dependency_id
        }


@dataclass
class StaffingNeed:
    """
    Post-close staffing need.

    Represents a hiring need identified through gap analysis,
    MSP exit planning, or shared services replacement.
    """
    id: str
    role: str
    category: RoleCategory
    fte_count: float
    urgency: str  # "immediate" | "day_100" | "year_1"
    reason: str
    estimated_salary: float
    source: str  # "benchmark_gap" | "msp_exit" | "shared_services" | "key_person"

    @property
    def estimated_total_cost(self) -> float:
        """Estimate total cost including benefits (~1.3x base)."""
        return self.fte_count * self.estimated_salary * 1.3

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'role': self.role,
            'category': self.category.value,
            'fte_count': self.fte_count,
            'urgency': self.urgency,
            'reason': self.reason,
            'estimated_salary': self.estimated_salary,
            'estimated_total_cost': self.estimated_total_cost,
            'source': self.source
        }


# =============================================================================
# COMPANY INFO (for context)
# =============================================================================

@dataclass
class CompanyInfo:
    """
    Basic company information for benchmark matching.

    Used to select appropriate benchmark profile and provide
    context for analysis.
    """
    name: str
    revenue: float  # Annual revenue
    employee_count: int
    industry: str
    entity: str = "target"  # target | buyer
    headquarters_location: Optional[str] = None
    it_budget: Optional[float] = None
    fiscal_year_end: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'revenue': self.revenue,
            'employee_count': self.employee_count,
            'industry': self.industry,
            'entity': self.entity,
            'headquarters_location': self.headquarters_location,
            'it_budget': self.it_budget,
            'fiscal_year_end': self.fiscal_year_end
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CompanyInfo':
        return cls(
            name=data['name'],
            revenue=data['revenue'],
            employee_count=data['employee_count'],
            industry=data['industry'],
            entity=data.get('entity', 'target'),
            headquarters_location=data.get('headquarters_location'),
            it_budget=data.get('it_budget'),
            fiscal_year_end=data.get('fiscal_year_end')
        )
