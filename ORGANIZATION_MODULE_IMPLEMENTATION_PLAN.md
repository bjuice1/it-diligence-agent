# Organization Module Enhancement - 10 Phase Implementation Plan

## Overview

This plan covers the implementation of four interconnected analytical views for the Organization domain:

1. **Staffing Census Tree** - Role-level drill-down with compensation
2. **Benchmark Comparison** - Actual vs. expected staffing analysis
3. **MSP Dependency Analysis** - Understanding outsourced work and risk
4. **Shared Services Analysis** - Hidden headcount from parent/shared services

---

## Phase 1: Data Models & Schema Foundation

### Objective
Define all data structures that will hold census, benchmark, MSP, and shared services information.

### Deliverables

**1.1 Create `models/organization_models.py`**

```python
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum

class EmploymentType(Enum):
    FTE = "fte"
    CONTRACTOR = "contractor"
    MSP = "msp"
    TEMP = "temp"

class RoleCategory(Enum):
    LEADERSHIP = "leadership"
    INFRASTRUCTURE = "infrastructure"
    APPLICATIONS = "applications"
    SECURITY = "security"
    SERVICE_DESK = "service_desk"
    DATA = "data"
    PROJECT_MANAGEMENT = "project_management"
    OTHER = "other"

class DependencyLevel(Enum):
    FULL = "full"           # Entirely dependent on this provider
    PARTIAL = "partial"     # Mix of internal + external
    SUPPLEMENTAL = "supplemental"  # Internal capability exists, external augments

@dataclass
class StaffMember:
    """Individual person from census data."""
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
    reports_to: Optional[str] = None
    entity: str = "target"  # target | buyer | parent
    skills: List[str] = field(default_factory=list)
    is_key_person: bool = False
    notes: Optional[str] = None

@dataclass
class RoleSummary:
    """Aggregated view of a role type."""
    role_title: str
    role_category: RoleCategory
    headcount: int
    total_compensation: float
    avg_compensation: float
    avg_tenure: Optional[float]
    members: List[StaffMember] = field(default_factory=list)

@dataclass
class CategorySummary:
    """Aggregated view of a category (Infrastructure, Apps, etc.)."""
    category: RoleCategory
    total_headcount: int
    total_compensation: float
    roles: List[RoleSummary] = field(default_factory=list)
    fte_count: int = 0
    contractor_count: int = 0

@dataclass
class MSPService:
    """A specific service provided by an MSP."""
    service_name: str
    fte_equivalent: float
    coverage: str  # "24/7" | "business_hours" | "on_call"
    criticality: str  # "critical" | "high" | "medium" | "low"
    internal_backup: bool = False
    description: Optional[str] = None

@dataclass
class MSPRelationship:
    """Complete MSP/vendor relationship."""
    id: str
    vendor_name: str
    services: List[MSPService]
    contract_value_annual: float
    contract_start: Optional[str] = None
    contract_expiry: Optional[str] = None
    notice_period_days: int = 30
    dependency_level: DependencyLevel = DependencyLevel.PARTIAL
    total_fte_equivalent: float = 0.0
    replacement_cost_estimate: float = 0.0
    entity: str = "target"
    notes: Optional[str] = None

@dataclass
class SharedServiceDependency:
    """Service provided by parent/shared services that target relies on."""
    id: str
    service_name: str
    provider: str  # "Parent Corp IT" | "Shared Services Center"
    fte_equivalent: float
    will_transfer: bool  # Will this come over in the deal?
    replacement_cost_annual: float = 0.0
    replacement_fte_need: float = 0.0
    criticality: str = "medium"
    tsa_candidate: bool = True  # Should this be in TSA?
    tsa_duration_months: int = 12
    description: Optional[str] = None

@dataclass
class BenchmarkRange:
    """Min/typical/max range for a metric."""
    min_value: float
    typical_value: float
    max_value: float

@dataclass
class ExpectedRole:
    """A role that should exist based on benchmarks."""
    role_title: str
    category: RoleCategory
    importance: str  # "critical" | "high" | "medium" | "low"
    typical_count: int = 1
    description: Optional[str] = None

@dataclass
class BenchmarkProfile:
    """Benchmark profile for comparison."""
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
    it_to_employee_ratio: BenchmarkRange = None
    apps_per_developer_ratio: BenchmarkRange = None

    notes: Optional[str] = None
```

**1.2 Create `models/organization_stores.py`**

```python
@dataclass
class OrganizationDataStore:
    """Central store for all organization-related data."""

    # Census data
    staff_members: List[StaffMember] = field(default_factory=list)
    category_summaries: Dict[str, CategorySummary] = field(default_factory=dict)

    # MSP/Outsourcing
    msp_relationships: List[MSPRelationship] = field(default_factory=list)

    # Shared services
    shared_service_dependencies: List[SharedServiceDependency] = field(default_factory=list)

    # Benchmark comparison results
    active_benchmark: Optional[BenchmarkProfile] = None
    benchmark_comparison_results: Dict = field(default_factory=dict)

    # Calculated totals
    total_internal_fte: int = 0
    total_contractor: int = 0
    total_msp_fte_equivalent: float = 0.0
    total_shared_services_fte: float = 0.0
    total_compensation: float = 0.0
    hidden_headcount_need: float = 0.0
```

### Acceptance Criteria
- [ ] All dataclasses defined with proper typing
- [ ] Enums cover all expected values
- [ ] Models support both target and buyer entity distinction
- [ ] Store can be serialized to/from JSON

---

## Phase 2: Benchmark Framework & Test Data

### Objective
Create the benchmark framework with realistic test data that can later be replaced with real benchmark data.

### Deliverables

**2.1 Create `data/benchmarks/benchmark_profiles.json`**

```json
{
  "profiles": [
    {
      "profile_id": "smb_general",
      "profile_name": "SMB General",
      "description": "Small business under $25M revenue",
      "revenue_range_min": 0,
      "revenue_range_max": 25000000,
      "employee_range_min": 0,
      "employee_range_max": 100,
      "industries": ["general"],
      "expected_staffing": {
        "leadership": {"min": 1, "typical": 1, "max": 1},
        "infrastructure": {"min": 1, "typical": 2, "max": 4},
        "applications": {"min": 0, "typical": 1, "max": 2},
        "security": {"min": 0, "typical": 0, "max": 1},
        "service_desk": {"min": 1, "typical": 1, "max": 2}
      },
      "expected_roles": [
        {"role": "IT Manager/Director", "category": "leadership", "importance": "critical"},
        {"role": "Systems Administrator", "category": "infrastructure", "importance": "high"},
        {"role": "Help Desk Technician", "category": "service_desk", "importance": "high"}
      ],
      "it_to_employee_ratio": {"min": 0.02, "typical": 0.04, "max": 0.08}
    },
    {
      "profile_id": "midmarket_manufacturing",
      "profile_name": "Mid-Market Manufacturing",
      "description": "Manufacturing company $25M-$200M revenue",
      "revenue_range_min": 25000000,
      "revenue_range_max": 200000000,
      "employee_range_min": 100,
      "employee_range_max": 1000,
      "industries": ["manufacturing", "industrial"],
      "expected_staffing": {
        "leadership": {"min": 1, "typical": 2, "max": 3},
        "infrastructure": {"min": 4, "typical": 8, "max": 14},
        "applications": {"min": 2, "typical": 5, "max": 10},
        "security": {"min": 1, "typical": 2, "max": 4},
        "service_desk": {"min": 2, "typical": 4, "max": 8},
        "data": {"min": 0, "typical": 1, "max": 3}
      },
      "expected_roles": [
        {"role": "CIO/IT Director", "category": "leadership", "importance": "critical"},
        {"role": "IT Manager", "category": "leadership", "importance": "high"},
        {"role": "Network Administrator", "category": "infrastructure", "importance": "critical"},
        {"role": "Systems Administrator", "category": "infrastructure", "importance": "critical"},
        {"role": "DBA", "category": "data", "importance": "high"},
        {"role": "ERP Administrator", "category": "applications", "importance": "critical"},
        {"role": "Security Analyst", "category": "security", "importance": "high"},
        {"role": "Help Desk Lead", "category": "service_desk", "importance": "high"},
        {"role": "Help Desk Technician", "category": "service_desk", "importance": "medium"}
      ],
      "it_to_employee_ratio": {"min": 0.02, "typical": 0.035, "max": 0.05}
    },
    {
      "profile_id": "midmarket_professional_services",
      "profile_name": "Mid-Market Professional Services",
      "description": "Professional services firm $25M-$200M revenue",
      "revenue_range_min": 25000000,
      "revenue_range_max": 200000000,
      "employee_range_min": 100,
      "employee_range_max": 500,
      "industries": ["professional_services", "consulting", "legal", "accounting"],
      "expected_staffing": {
        "leadership": {"min": 1, "typical": 2, "max": 3},
        "infrastructure": {"min": 3, "typical": 5, "max": 8},
        "applications": {"min": 3, "typical": 6, "max": 12},
        "security": {"min": 1, "typical": 2, "max": 4},
        "service_desk": {"min": 2, "typical": 4, "max": 6}
      },
      "expected_roles": [
        {"role": "CIO/IT Director", "category": "leadership", "importance": "critical"},
        {"role": "Applications Manager", "category": "leadership", "importance": "high"},
        {"role": "Network Administrator", "category": "infrastructure", "importance": "high"},
        {"role": "Cloud Engineer", "category": "infrastructure", "importance": "high"},
        {"role": "Business Analyst", "category": "applications", "importance": "high"},
        {"role": "Developer", "category": "applications", "importance": "medium"},
        {"role": "Security Analyst", "category": "security", "importance": "high"}
      ],
      "it_to_employee_ratio": {"min": 0.03, "typical": 0.05, "max": 0.08}
    },
    {
      "profile_id": "midmarket_healthcare",
      "profile_name": "Mid-Market Healthcare",
      "description": "Healthcare organization $50M-$500M revenue",
      "revenue_range_min": 50000000,
      "revenue_range_max": 500000000,
      "employee_range_min": 200,
      "employee_range_max": 2000,
      "industries": ["healthcare", "medical"],
      "expected_staffing": {
        "leadership": {"min": 2, "typical": 3, "max": 5},
        "infrastructure": {"min": 6, "typical": 12, "max": 20},
        "applications": {"min": 4, "typical": 10, "max": 18},
        "security": {"min": 2, "typical": 4, "max": 8},
        "service_desk": {"min": 4, "typical": 8, "max": 15},
        "data": {"min": 1, "typical": 3, "max": 6}
      },
      "expected_roles": [
        {"role": "CIO", "category": "leadership", "importance": "critical"},
        {"role": "CISO", "category": "leadership", "importance": "critical"},
        {"role": "IT Director", "category": "leadership", "importance": "high"},
        {"role": "Network Engineer", "category": "infrastructure", "importance": "critical"},
        {"role": "Systems Administrator", "category": "infrastructure", "importance": "critical"},
        {"role": "Clinical Applications Analyst", "category": "applications", "importance": "critical"},
        {"role": "EHR Administrator", "category": "applications", "importance": "critical"},
        {"role": "Security Analyst", "category": "security", "importance": "critical"},
        {"role": "Compliance Analyst", "category": "security", "importance": "high"},
        {"role": "Data Analyst", "category": "data", "importance": "high"}
      ],
      "it_to_employee_ratio": {"min": 0.03, "typical": 0.045, "max": 0.06}
    },
    {
      "profile_id": "enterprise_general",
      "profile_name": "Enterprise General",
      "description": "Large enterprise $200M+ revenue",
      "revenue_range_min": 200000000,
      "revenue_range_max": 10000000000,
      "employee_range_min": 1000,
      "employee_range_max": 50000,
      "industries": ["general"],
      "expected_staffing": {
        "leadership": {"min": 4, "typical": 8, "max": 15},
        "infrastructure": {"min": 15, "typical": 30, "max": 60},
        "applications": {"min": 10, "typical": 25, "max": 50},
        "security": {"min": 5, "typical": 12, "max": 25},
        "service_desk": {"min": 10, "typical": 20, "max": 40},
        "data": {"min": 3, "typical": 8, "max": 15},
        "project_management": {"min": 2, "typical": 5, "max": 10}
      },
      "expected_roles": [
        {"role": "CIO", "category": "leadership", "importance": "critical"},
        {"role": "CISO", "category": "leadership", "importance": "critical"},
        {"role": "VP Infrastructure", "category": "leadership", "importance": "high"},
        {"role": "VP Applications", "category": "leadership", "importance": "high"},
        {"role": "Enterprise Architect", "category": "leadership", "importance": "high"}
      ],
      "it_to_employee_ratio": {"min": 0.025, "typical": 0.04, "max": 0.06}
    }
  ]
}
```

**2.2 Create `data/benchmarks/role_compensation_benchmarks.json`**

```json
{
  "compensation_benchmarks": {
    "leadership": {
      "CIO": {"p25": 180000, "p50": 225000, "p75": 300000},
      "CISO": {"p25": 165000, "p50": 200000, "p75": 260000},
      "VP IT": {"p25": 150000, "p50": 185000, "p75": 240000},
      "IT Director": {"p25": 130000, "p50": 160000, "p75": 200000},
      "IT Manager": {"p25": 95000, "p50": 115000, "p75": 140000}
    },
    "infrastructure": {
      "Infrastructure Manager": {"p25": 110000, "p50": 130000, "p75": 155000},
      "Sr Network Engineer": {"p25": 95000, "p50": 115000, "p75": 135000},
      "Network Administrator": {"p25": 70000, "p50": 85000, "p75": 100000},
      "Sr Systems Administrator": {"p25": 90000, "p50": 105000, "p75": 125000},
      "Systems Administrator": {"p25": 65000, "p50": 80000, "p75": 95000},
      "Cloud Engineer": {"p25": 100000, "p50": 125000, "p75": 150000},
      "DevOps Engineer": {"p25": 105000, "p50": 130000, "p75": 160000}
    },
    "applications": {
      "Applications Manager": {"p25": 115000, "p50": 135000, "p75": 160000},
      "ERP Administrator": {"p25": 85000, "p50": 105000, "p75": 130000},
      "Sr Developer": {"p25": 110000, "p50": 135000, "p75": 165000},
      "Developer": {"p25": 75000, "p50": 95000, "p75": 120000},
      "Business Analyst": {"p25": 70000, "p50": 85000, "p75": 105000},
      "QA Engineer": {"p25": 65000, "p50": 80000, "p75": 100000}
    },
    "security": {
      "Security Manager": {"p25": 125000, "p50": 150000, "p75": 180000},
      "Sr Security Analyst": {"p25": 100000, "p50": 120000, "p75": 145000},
      "Security Analyst": {"p25": 75000, "p50": 95000, "p75": 115000},
      "Security Engineer": {"p25": 105000, "p50": 130000, "p75": 160000},
      "Compliance Analyst": {"p25": 70000, "p50": 85000, "p75": 105000}
    },
    "service_desk": {
      "Service Desk Manager": {"p25": 70000, "p50": 85000, "p75": 100000},
      "Help Desk Lead": {"p25": 55000, "p50": 65000, "p75": 78000},
      "Help Desk Technician": {"p25": 40000, "p50": 50000, "p75": 62000},
      "Desktop Support": {"p25": 45000, "p50": 55000, "p75": 68000}
    },
    "data": {
      "Data Manager": {"p25": 115000, "p50": 140000, "p75": 170000},
      "Sr DBA": {"p25": 105000, "p50": 125000, "p75": 150000},
      "DBA": {"p25": 80000, "p50": 100000, "p75": 120000},
      "Data Analyst": {"p25": 65000, "p50": 80000, "p75": 100000},
      "Data Engineer": {"p25": 100000, "p50": 125000, "p75": 155000}
    }
  },
  "location_adjustments": {
    "high_cost": 1.25,
    "medium_cost": 1.0,
    "low_cost": 0.80,
    "offshore": 0.40
  }
}
```

**2.3 Create `services/benchmark_service.py`**

```python
class BenchmarkService:
    """Service for loading and matching benchmark profiles."""

    def load_profiles(self) -> List[BenchmarkProfile]
    def match_profile(self, revenue: float, employees: int, industry: str) -> BenchmarkProfile
    def compare_staffing(self, actual: CategorySummary, benchmark: BenchmarkProfile) -> ComparisonResult
    def identify_missing_roles(self, staff: List[StaffMember], benchmark: BenchmarkProfile) -> List[str]
    def calculate_ratios(self, staff_count: int, company_employees: int) -> Dict
```

### Acceptance Criteria
- [ ] At least 5 benchmark profiles covering SMB to Enterprise
- [ ] Compensation benchmarks for all role categories
- [ ] BenchmarkService can match company to appropriate profile
- [ ] Test data generates realistic comparisons

---

## Phase 3: Census Data Parser

### Objective
Build the parser that reads Excel/CSV census files and populates the StaffMember model.

### Deliverables

**3.1 Create `parsers/census_parser.py`**

```python
class CensusParser:
    """Parses HR census data from Excel/CSV into StaffMember objects."""

    # Column mapping configuration
    COLUMN_MAPPINGS = {
        "name": ["name", "employee_name", "full_name", "employee"],
        "role": ["title", "job_title", "role", "position"],
        "department": ["department", "dept", "team", "group"],
        "salary": ["salary", "base_salary", "compensation", "base_pay", "annual_salary"],
        "total_comp": ["total_comp", "total_compensation", "tc", "ote"],
        "location": ["location", "office", "site", "work_location"],
        "hire_date": ["hire_date", "start_date", "date_hired"],
        "manager": ["manager", "reports_to", "supervisor"]
    }

    # Role category classification rules
    ROLE_CATEGORY_RULES = {
        "leadership": ["cio", "ciso", "vp", "vice president", "director", "chief"],
        "infrastructure": ["network", "systems", "infrastructure", "cloud", "devops", "server"],
        "applications": ["developer", "programmer", "erp", "crm", "application", "software"],
        "security": ["security", "compliance", "risk", "audit"],
        "service_desk": ["help desk", "service desk", "support", "desktop"],
        "data": ["dba", "database", "data analyst", "data engineer", "bi "]
    }

    def parse_file(self, file_path: str, entity: str = "target") -> List[StaffMember]
    def detect_columns(self, df: DataFrame) -> Dict[str, str]
    def classify_role(self, role_title: str) -> RoleCategory
    def calculate_tenure(self, hire_date: str) -> float
    def aggregate_by_category(self, staff: List[StaffMember]) -> Dict[str, CategorySummary]
    def aggregate_by_role(self, staff: List[StaffMember]) -> Dict[str, RoleSummary]
```

**3.2 Create `parsers/census_validator.py`**

```python
class CensusValidator:
    """Validates census data quality and flags issues."""

    def validate_completeness(self, staff: List[StaffMember]) -> List[ValidationIssue]
    def validate_compensation_ranges(self, staff: List[StaffMember]) -> List[ValidationIssue]
    def detect_duplicates(self, staff: List[StaffMember]) -> List[ValidationIssue]
    def flag_missing_managers(self, staff: List[StaffMember]) -> List[ValidationIssue]
```

**3.3 Create sample test census file `data/test/sample_census.csv`**

```csv
name,title,department,base_salary,total_comp,location,hire_date,reports_to
Michael Johnson,IT Director,IT,165000,185000,HQ,2018-03-15,CFO
Sarah Chen,Sr Network Administrator,IT - Infrastructure,105000,115000,HQ,2019-06-01,Michael Johnson
James Wilson,Systems Administrator,IT - Infrastructure,82000,90000,HQ,2021-02-15,Sarah Chen
...
```

### Acceptance Criteria
- [ ] Parser handles both Excel (.xlsx) and CSV formats
- [ ] Auto-detects column mappings with fuzzy matching
- [ ] Correctly classifies roles into categories
- [ ] Calculates tenure from hire dates
- [ ] Validator catches common data quality issues

---

## Phase 4: MSP & Outsourcing Data Capture

### Objective
Extend the discovery process to capture detailed MSP/outsourcing information and calculate FTE equivalents.

### Deliverables

**4.1 Update `prompts/v2_organization_discovery_prompt.py`**

Add enhanced MSP extraction section:
```python
ENHANCED_MSP_EXTRACTION = """
**4. OUTSOURCING & MSP - ENHANCED**

For each MSP/vendor, capture:

| Field | Description |
|-------|-------------|
| vendor_name | Company name |
| services | List of specific services provided |
| fte_equivalent | Estimated FTE equivalent for each service |
| coverage | 24/7, business hours, on-call |
| contract_value | Annual contract value if stated |
| contract_expiry | When contract ends |
| notice_period | Termination notice required |
| criticality | How critical is this to operations |
| internal_backup | Does internal staff exist as backup? |

**FTE EQUIVALENT GUIDANCE:**
- 24/7 Help Desk: Typically 3-5 FTEs
- 24/7 Infrastructure Monitoring: 1.5-3 FTEs
- Security Operations (SOC): 2-4 FTEs
- Managed Desktop: 1 FTE per 150-200 users
- Application Support: Varies by complexity
"""
```

**4.2 Create `parsers/msp_parser.py`**

```python
class MSPParser:
    """Parses MSP/vendor information from various sources."""

    # Standard service FTE equivalents (defaults)
    SERVICE_FTE_DEFAULTS = {
        "24x7_helpdesk": 4.0,
        "business_hours_helpdesk": 1.5,
        "infrastructure_monitoring_24x7": 2.0,
        "security_operations": 3.0,
        "managed_backup": 0.5,
        "managed_patching": 0.5,
        "managed_desktop": 0.005,  # Per user
        "managed_network": 1.0,
        "erp_support": 1.5
    }

    def parse_from_facts(self, facts: List[Fact]) -> List[MSPRelationship]
    def calculate_fte_equivalent(self, services: List[MSPService]) -> float
    def estimate_replacement_cost(self, msp: MSPRelationship) -> float
    def assess_dependency_risk(self, msp: MSPRelationship) -> str
```

**4.3 Create `services/msp_analysis_service.py`**

```python
class MSPAnalysisService:
    """Analyzes MSP dependencies and calculates impact."""

    def calculate_total_outsourced_fte(self, msps: List[MSPRelationship]) -> float
    def identify_high_risk_dependencies(self, msps: List[MSPRelationship]) -> List[MSPRelationship]
    def calculate_exit_cost(self, msp: MSPRelationship) -> Dict
    def generate_msp_summary(self, msps: List[MSPRelationship]) -> MSPSummary
```

### Acceptance Criteria
- [ ] Discovery prompt captures detailed MSP information
- [ ] FTE equivalents calculated for standard services
- [ ] Replacement cost estimates generated
- [ ] High-risk dependencies flagged automatically

---

## Phase 5: Shared Services / Parent Dependency Capture

### Objective
Build the capability to capture and analyze services provided by parent company or shared services that create hidden headcount needs.

### Deliverables

**5.1 Update `prompts/v2_organization_discovery_prompt.py`**

Add shared services extraction:
```python
SHARED_SERVICES_EXTRACTION = """
**9. SHARED SERVICES / PARENT DEPENDENCIES**

Identify IT services provided by parent company or shared services center:

| Field | Description |
|-------|-------------|
| service_name | What service is provided |
| provider | Who provides it (Parent IT, Shared Services, etc.) |
| fte_equivalent | Estimated FTE equivalent |
| will_transfer | Will this service transfer in the deal? |
| criticality | How critical to target operations |
| tsa_candidate | Should this be in a TSA? |

**LOOK FOR INDICATORS:**
- References to "corporate IT" or "parent company"
- Shared ERP/financial systems
- Centralized security operations
- Corporate network/WAN management
- Shared help desk services
- "Provided by headquarters"
"""
```

**5.2 Create `services/shared_services_analyzer.py`**

```python
class SharedServicesAnalyzer:
    """Analyzes shared service dependencies and calculates hidden needs."""

    def identify_dependencies(self, facts: List[Fact]) -> List[SharedServiceDependency]
    def calculate_hidden_headcount(self, deps: List[SharedServiceDependency]) -> float
    def calculate_replacement_cost(self, deps: List[SharedServiceDependency]) -> float
    def generate_tsa_recommendations(self, deps: List[SharedServiceDependency]) -> List[TSAItem]
    def generate_day1_staffing_needs(self, deps: List[SharedServiceDependency]) -> List[StaffingNeed]
```

**5.3 Create `models/tsa_models.py`**

```python
@dataclass
class TSAItem:
    """Transition Services Agreement line item."""
    service: str
    provider: str
    duration_months: int
    estimated_monthly_cost: float
    exit_criteria: str
    replacement_plan: str

@dataclass
class StaffingNeed:
    """Post-close staffing need."""
    role: str
    category: RoleCategory
    fte_count: float
    urgency: str  # "immediate" | "day_100" | "year_1"
    reason: str
    estimated_salary: float
```

### Acceptance Criteria
- [ ] Discovery identifies parent/shared service dependencies
- [ ] Hidden headcount needs calculated automatically
- [ ] TSA recommendations generated
- [ ] Clear distinction between what transfers and what doesn't

---

## Phase 6: Benchmark Comparison Engine

### Objective
Build the comparison engine that evaluates actual staffing against benchmarks and identifies gaps/overages.

### Deliverables

**6.1 Create `services/staffing_comparison_service.py`**

```python
class StaffingComparisonService:
    """Compares actual staffing to benchmarks."""

    def compare_to_benchmark(
        self,
        actual: OrganizationDataStore,
        benchmark: BenchmarkProfile,
        company_info: CompanyInfo
    ) -> StaffingComparisonResult

    def compare_category_headcount(
        self,
        category: str,
        actual_count: int,
        benchmark_range: BenchmarkRange
    ) -> CategoryComparison

    def identify_missing_roles(
        self,
        actual_roles: List[str],
        expected_roles: List[ExpectedRole]
    ) -> List[MissingRole]

    def identify_overstaffed_areas(
        self,
        actual: Dict[str, int],
        benchmark: Dict[str, BenchmarkRange]
    ) -> List[OverstaffedArea]

    def calculate_ratio_comparison(
        self,
        it_headcount: int,
        company_employees: int,
        benchmark_ratio: BenchmarkRange
    ) -> RatioComparison
```

**6.2 Create `models/comparison_models.py`**

```python
@dataclass
class CategoryComparison:
    category: str
    actual_count: int
    benchmark_min: int
    benchmark_typical: int
    benchmark_max: int
    variance: int  # Positive = over, Negative = under
    status: str  # "in_range" | "understaffed" | "overstaffed"
    analysis: str

@dataclass
class MissingRole:
    role_title: str
    category: RoleCategory
    importance: str
    impact: str
    recommendation: str

@dataclass
class StaffingComparisonResult:
    benchmark_used: str
    overall_status: str
    category_comparisons: List[CategoryComparison]
    missing_roles: List[MissingRole]
    overstaffed_areas: List[OverstaffedArea]
    ratio_comparisons: Dict[str, RatioComparison]
    key_findings: List[str]
    recommendations: List[str]
```

**6.3 Create reasoning integration `agents_v2/reasoning/organization_benchmark_reasoning.py`**

```python
class OrganizationBenchmarkReasoning:
    """Generates findings from benchmark comparisons."""

    def generate_staffing_findings(self, comparison: StaffingComparisonResult) -> List[Finding]
    def generate_missing_role_risks(self, missing: List[MissingRole]) -> List[Risk]
    def generate_overstaffing_observations(self, over: List[OverstaffedArea]) -> List[Finding]
    def generate_recommendations(self, comparison: StaffingComparisonResult) -> List[Recommendation]
```

### Acceptance Criteria
- [ ] Comparison runs against any benchmark profile
- [ ] Clear understaffed/overstaffed identification
- [ ] Missing critical roles flagged as risks
- [ ] Ratio analysis (IT:employee) included
- [ ] Findings auto-generated with proper citations

---

## Phase 7: Organization Reasoning Integration

### Objective
Integrate all organization analysis (census, benchmarks, MSP, shared services) into the reasoning engine to produce cohesive findings.

### Deliverables

**7.1 Update `agents_v2/reasoning/organization_reasoning.py`**

```python
class EnhancedOrganizationReasoning:
    """
    Enhanced organization reasoning that combines:
    - Census analysis
    - Benchmark comparison
    - MSP dependency analysis
    - Shared services analysis
    """

    def analyze_complete_organization(
        self,
        org_store: OrganizationDataStore,
        company_info: CompanyInfo
    ) -> OrganizationAnalysisResult

    def generate_key_person_risks(self, staff: List[StaffMember]) -> List[Risk]
    def generate_compensation_findings(self, staff: List[StaffMember]) -> List[Finding]
    def generate_msp_risks(self, msps: List[MSPRelationship]) -> List[Risk]
    def generate_hidden_headcount_risks(self, deps: List[SharedServiceDependency]) -> List[Risk]
    def generate_integration_work_items(self, org_store: OrganizationDataStore) -> List[WorkItem]

    def calculate_total_it_cost(
        self,
        internal_staff: List[StaffMember],
        msps: List[MSPRelationship],
        shared_services: List[SharedServiceDependency]
    ) -> TotalITCostSummary
```

**7.2 Create `models/organization_analysis_result.py`**

```python
@dataclass
class OrganizationAnalysisResult:
    """Complete organization analysis output."""

    # Summaries
    staffing_summary: StaffingSummary
    benchmark_comparison: StaffingComparisonResult
    msp_summary: MSPSummary
    shared_services_summary: SharedServicesSummary

    # Findings
    risks: List[Risk]
    gaps: List[Gap]
    observations: List[Finding]

    # Recommendations
    work_items: List[WorkItem]
    tsa_recommendations: List[TSAItem]
    hiring_recommendations: List[StaffingNeed]

    # Financials
    total_it_cost: TotalITCostSummary
    hidden_costs: float
    post_close_staffing_cost: float
```

**7.3 Update finding templates**

```python
ORGANIZATION_FINDING_TEMPLATES = {
    "understaffed_category": """
        {category} team appears understaffed with {actual} FTEs vs benchmark of {typical}.
        This may indicate: (a) heavy MSP reliance, (b) shared services dependency,
        or (c) operational strain. Recommend investigation.
    """,
    "missing_critical_role": """
        No {role} identified in the organization. This is typically a {importance}
        role for companies of this size. Current coverage: {current_coverage}.
    """,
    "high_msp_dependency": """
        {vendor} provides {services} representing {fte_equiv} FTE equivalent.
        Contract expires {expiry}. No internal backup capability identified.
        Exit risk: {exit_risk}
    """,
    "hidden_headcount": """
        Target relies on {provider} for {service} (~{fte} FTE equivalent).
        This service will not transfer in the deal. Post-close need: {need}.
    """
}
```

### Acceptance Criteria
- [ ] All four analysis types feed into unified reasoning
- [ ] Risks properly categorized and severity-rated
- [ ] Work items generated for identified gaps
- [ ] Total IT cost calculated including hidden costs
- [ ] Findings cite supporting facts

---

## Phase 8: Tree View UI Component

### Objective
Build the expandable tree view component for the staffing census visualization.

### Deliverables

**8.1 Create `web/templates/organization/staffing_tree.html`**

```html
{% extends "base.html" %}
{% block content %}
<div class="staffing-tree-container">
    <div class="tree-header">
        <h2>IT Staffing by Function</h2>
        <div class="tree-controls">
            <button id="expand-all">Expand All</button>
            <button id="collapse-all">Collapse All</button>
            <select id="entity-filter">
                <option value="all">All Entities</option>
                <option value="target">Target Only</option>
                <option value="buyer">Buyer Only</option>
            </select>
        </div>
        <div class="tree-summary">
            <span class="total-headcount">Total: {{ total_headcount }} FTEs</span>
            <span class="total-comp">Total Comp: ${{ total_compensation|format_currency }}</span>
        </div>
    </div>

    <div class="staffing-tree" id="staffing-tree">
        {% for category in categories %}
        <div class="tree-category" data-category="{{ category.name }}">
            <div class="category-header" onclick="toggleCategory('{{ category.name }}')">
                <span class="expand-icon">▶</span>
                <span class="category-name">{{ category.display_name }}</span>
                <span class="category-count">({{ category.headcount }})</span>
                <span class="category-comp">${{ category.total_comp|format_currency }}</span>
            </div>
            <div class="category-content" id="content-{{ category.name }}" style="display: none;">
                {% for role in category.roles %}
                <div class="tree-role" data-role="{{ role.title }}">
                    <div class="role-header" onclick="toggleRole('{{ category.name }}', '{{ role.title }}')">
                        <span class="expand-icon">▶</span>
                        <span class="role-title">{{ role.title }}</span>
                        {% if role.headcount > 1 %}
                        <span class="role-count">({{ role.headcount }})</span>
                        {% endif %}
                        <span class="role-comp">${{ role.avg_comp|format_currency }} avg</span>
                    </div>
                    <div class="role-content" id="content-{{ category.name }}-{{ role.title|slugify }}" style="display: none;">
                        {% for person in role.members %}
                        <div class="tree-person {% if person.is_key_person %}key-person{% endif %}">
                            <span class="person-name">{{ person.name }}</span>
                            <span class="person-comp">${{ person.compensation|format_currency }}</span>
                            <span class="person-tenure">{{ person.tenure_years }} yrs</span>
                            <span class="person-type {{ person.employment_type }}">{{ person.employment_type }}</span>
                            {% if person.is_key_person %}
                            <span class="key-person-badge" title="Key Person Risk">⚠</span>
                            {% endif %}
                        </div>
                        {% endfor %}
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        {% endfor %}
    </div>
</div>
{% endblock %}
```

**8.2 Create `web/static/css/staffing_tree.css`**

```css
.staffing-tree-container {
    max-width: 900px;
    margin: 0 auto;
    padding: 20px;
}

.tree-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding-bottom: 15px;
    border-bottom: 2px solid #e0e0e0;
}

.tree-category {
    margin-bottom: 8px;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
}

.category-header {
    display: flex;
    align-items: center;
    padding: 12px 15px;
    background: #f5f5f5;
    cursor: pointer;
    font-weight: 600;
}

.category-header:hover {
    background: #ebebeb;
}

.expand-icon {
    margin-right: 10px;
    transition: transform 0.2s;
}

.expanded .expand-icon {
    transform: rotate(90deg);
}

.category-count, .role-count {
    color: #666;
    margin-left: 8px;
}

.category-comp, .role-comp {
    margin-left: auto;
    color: #2e7d32;
}

.tree-role {
    margin-left: 20px;
    border-left: 2px solid #e0e0e0;
}

.role-header {
    display: flex;
    align-items: center;
    padding: 8px 15px;
    cursor: pointer;
}

.role-header:hover {
    background: #fafafa;
}

.tree-person {
    display: flex;
    align-items: center;
    padding: 6px 15px 6px 40px;
    border-bottom: 1px solid #f0f0f0;
}

.tree-person:hover {
    background: #f9f9f9;
}

.person-name {
    flex: 1;
}

.person-comp {
    width: 100px;
    text-align: right;
    color: #2e7d32;
}

.person-tenure {
    width: 60px;
    text-align: right;
    color: #666;
}

.person-type {
    width: 80px;
    text-align: center;
    padding: 2px 8px;
    border-radius: 3px;
    font-size: 0.85em;
    margin-left: 10px;
}

.person-type.fte { background: #e3f2fd; color: #1565c0; }
.person-type.contractor { background: #fff3e0; color: #e65100; }
.person-type.msp { background: #fce4ec; color: #c2185b; }

.key-person {
    background: #fff8e1;
}

.key-person-badge {
    color: #f57c00;
    margin-left: 8px;
}
```

**8.3 Create `web/static/js/staffing_tree.js`**

```javascript
function toggleCategory(categoryName) {
    const content = document.getElementById(`content-${categoryName}`);
    const header = content.previousElementSibling;

    if (content.style.display === 'none') {
        content.style.display = 'block';
        header.classList.add('expanded');
    } else {
        content.style.display = 'none';
        header.classList.remove('expanded');
    }
}

function toggleRole(categoryName, roleTitle) {
    const slug = roleTitle.toLowerCase().replace(/\s+/g, '-');
    const content = document.getElementById(`content-${categoryName}-${slug}`);
    const header = content.previousElementSibling;

    if (content.style.display === 'none') {
        content.style.display = 'block';
        header.classList.add('expanded');
    } else {
        content.style.display = 'none';
        header.classList.remove('expanded');
    }
}

function expandAll() {
    document.querySelectorAll('.category-content, .role-content').forEach(el => {
        el.style.display = 'block';
        el.previousElementSibling.classList.add('expanded');
    });
}

function collapseAll() {
    document.querySelectorAll('.category-content, .role-content').forEach(el => {
        el.style.display = 'none';
        el.previousElementSibling.classList.remove('expanded');
    });
}

function filterByEntity(entity) {
    document.querySelectorAll('.tree-person').forEach(el => {
        if (entity === 'all' || el.dataset.entity === entity) {
            el.style.display = 'flex';
        } else {
            el.style.display = 'none';
        }
    });
    updateCounts();
}
```

### Acceptance Criteria
- [ ] Tree expands/collapses at category and role level
- [ ] Individual person details visible on expansion
- [ ] Compensation and tenure displayed
- [ ] Key person flag visible
- [ ] Employment type color-coded
- [ ] Entity filter works correctly

---

## Phase 9: Dashboard Views (Benchmark, MSP, Shared Services)

### Objective
Build the three additional dashboard views for benchmark comparison, MSP analysis, and shared services.

### Deliverables

**9.1 Create `web/templates/organization/benchmark_comparison.html`**

```html
{% extends "base.html" %}
{% block content %}
<div class="benchmark-container">
    <div class="benchmark-header">
        <h2>Staffing vs Benchmark</h2>
        <div class="benchmark-profile">
            <label>Profile:</label>
            <select id="benchmark-selector" onchange="changeBenchmark(this.value)">
                {% for profile in profiles %}
                <option value="{{ profile.id }}" {% if profile.id == active_profile %}selected{% endif %}>
                    {{ profile.name }}
                </option>
                {% endfor %}
            </select>
        </div>
    </div>

    <div class="company-context">
        <span>{{ company_name }}</span> |
        <span>Revenue: ${{ revenue|format_currency }}</span> |
        <span>Employees: {{ employee_count }}</span>
    </div>

    <!-- Category Comparison Table -->
    <div class="comparison-table">
        <table>
            <thead>
                <tr>
                    <th>Function</th>
                    <th>Actual</th>
                    <th>Expected Range</th>
                    <th>Variance</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                {% for comp in category_comparisons %}
                <tr class="{{ comp.status }}">
                    <td>{{ comp.category }}</td>
                    <td>{{ comp.actual_count }}</td>
                    <td>{{ comp.benchmark_min }} - {{ comp.benchmark_max }}</td>
                    <td>
                        {% if comp.variance > 0 %}+{% endif %}{{ comp.variance }}
                    </td>
                    <td>
                        <span class="status-badge {{ comp.status }}">
                            {% if comp.status == 'in_range' %}✓ In Range
                            {% elif comp.status == 'understaffed' %}⚠ Under
                            {% else %}⚠ Over
                            {% endif %}
                        </span>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
            <tfoot>
                <tr>
                    <td><strong>TOTAL</strong></td>
                    <td><strong>{{ total_actual }}</strong></td>
                    <td><strong>{{ total_expected_min }} - {{ total_expected_max }}</strong></td>
                    <td></td>
                    <td></td>
                </tr>
            </tfoot>
        </table>
    </div>

    <!-- Ratio Analysis -->
    <div class="ratio-analysis">
        <h3>Key Ratios</h3>
        <div class="ratio-cards">
            <div class="ratio-card {{ it_ratio.status }}">
                <div class="ratio-label">IT : Employee</div>
                <div class="ratio-value">{{ it_ratio.actual }}%</div>
                <div class="ratio-benchmark">Benchmark: {{ it_ratio.typical }}%</div>
            </div>
        </div>
    </div>

    <!-- Missing Roles -->
    <div class="missing-roles">
        <h3>Missing/Gap Roles</h3>
        {% if missing_roles %}
        <ul>
            {% for role in missing_roles %}
            <li class="missing-role {{ role.importance }}">
                <span class="role-name">{{ role.role_title }}</span>
                <span class="importance-badge">{{ role.importance }}</span>
                <span class="role-note">{{ role.recommendation }}</span>
            </li>
            {% endfor %}
        </ul>
        {% else %}
        <p class="no-gaps">No critical role gaps identified.</p>
        {% endif %}
    </div>
</div>
{% endblock %}
```

**9.2 Create `web/templates/organization/msp_analysis.html`**

```html
{% extends "base.html" %}
{% block content %}
<div class="msp-container">
    <div class="msp-header">
        <h2>MSP / Outsourcing Analysis</h2>
        <div class="msp-summary-stats">
            <div class="stat">
                <span class="stat-value">{{ total_msp_fte }}</span>
                <span class="stat-label">FTE Equivalent</span>
            </div>
            <div class="stat">
                <span class="stat-value">${{ total_msp_cost|format_currency }}</span>
                <span class="stat-label">Annual Cost</span>
            </div>
            <div class="stat {{ 'high-risk' if high_risk_count > 0 }}">
                <span class="stat-value">{{ high_risk_count }}</span>
                <span class="stat-label">High Risk Dependencies</span>
            </div>
        </div>
    </div>

    {% for msp in msp_relationships %}
    <div class="msp-card {{ msp.dependency_level }}">
        <div class="msp-card-header" onclick="toggleMSP('{{ msp.id }}')">
            <span class="expand-icon">▶</span>
            <span class="msp-name">{{ msp.vendor_name }}</span>
            <span class="msp-fte">{{ msp.total_fte_equivalent }} FTE eq.</span>
            <span class="msp-cost">${{ msp.contract_value_annual|format_currency }}/yr</span>
            <span class="dependency-badge {{ msp.dependency_level }}">{{ msp.dependency_level }}</span>
        </div>

        <div class="msp-card-content" id="msp-{{ msp.id }}" style="display: none;">
            <div class="msp-contract-info">
                <span>Contract Expires: {{ msp.contract_expiry }}</span>
                <span>Notice Period: {{ msp.notice_period_days }} days</span>
            </div>

            <table class="services-table">
                <thead>
                    <tr>
                        <th>Service</th>
                        <th>FTE Eq.</th>
                        <th>Coverage</th>
                        <th>Criticality</th>
                        <th>Internal Backup?</th>
                    </tr>
                </thead>
                <tbody>
                    {% for svc in msp.services %}
                    <tr>
                        <td>{{ svc.service_name }}</td>
                        <td>{{ svc.fte_equivalent }}</td>
                        <td>{{ svc.coverage }}</td>
                        <td><span class="criticality-badge {{ svc.criticality }}">{{ svc.criticality }}</span></td>
                        <td>
                            {% if svc.internal_backup %}
                            <span class="backup-yes">✓ Yes</span>
                            {% else %}
                            <span class="backup-no">✗ No</span>
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>

            <div class="msp-risk-section">
                <h4>Risk Assessment</h4>
                <p>{{ msp.risk_assessment }}</p>
                <div class="exit-cost">
                    <strong>If MSP exits:</strong> Estimated {{ msp.replacement_fte }} FTE needed |
                    ${{ msp.replacement_cost_estimate|format_currency }}/yr additional headcount cost
                </div>
            </div>
        </div>
    </div>
    {% endfor %}
</div>
{% endblock %}
```

**9.3 Create `web/templates/organization/shared_services.html`**

```html
{% extends "base.html" %}
{% block content %}
<div class="shared-services-container">
    <div class="ss-header">
        <h2>Shared Services / Parent Dependencies</h2>
        <div class="ss-alert">
            <strong>⚠ Hidden Headcount Need:</strong>
            {{ total_hidden_fte }} FTE equivalent |
            Est. ${{ total_hidden_cost|format_currency }}/yr
        </div>
    </div>

    <div class="ss-explanation">
        <p>These services are currently provided by the parent company or shared services
        and will need to be addressed post-close through TSA, hiring, or outsourcing.</p>
    </div>

    <table class="ss-table">
        <thead>
            <tr>
                <th>Service</th>
                <th>Provider</th>
                <th>FTE Equivalent</th>
                <th>Transferring?</th>
                <th>Criticality</th>
                <th>TSA Candidate?</th>
                <th>Post-Close Need</th>
            </tr>
        </thead>
        <tbody>
            {% for dep in dependencies %}
            <tr class="{{ 'not-transferring' if not dep.will_transfer }}">
                <td>{{ dep.service_name }}</td>
                <td>{{ dep.provider }}</td>
                <td>{{ dep.fte_equivalent }}</td>
                <td>
                    {% if dep.will_transfer %}
                    <span class="transfer-yes">✓ Yes</span>
                    {% else %}
                    <span class="transfer-no">✗ No</span>
                    {% endif %}
                </td>
                <td><span class="criticality-badge {{ dep.criticality }}">{{ dep.criticality }}</span></td>
                <td>
                    {% if dep.tsa_candidate %}
                    <span class="tsa-yes">Yes ({{ dep.tsa_duration_months }}mo)</span>
                    {% else %}
                    <span class="tsa-no">No</span>
                    {% endif %}
                </td>
                <td>
                    {% if not dep.will_transfer %}
                    +{{ dep.replacement_fte_need }} FTE | ${{ dep.replacement_cost_annual|format_currency }}
                    {% else %}
                    —
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
        </tbody>
        <tfoot>
            <tr>
                <td colspan="2"><strong>TOTAL HIDDEN NEED</strong></td>
                <td><strong>{{ total_hidden_fte }}</strong></td>
                <td colspan="3"></td>
                <td><strong>${{ total_hidden_cost|format_currency }}/yr</strong></td>
            </tr>
        </tfoot>
    </table>

    <div class="tsa-recommendations">
        <h3>TSA Recommendations</h3>
        <ul>
            {% for tsa in tsa_items %}
            <li>
                <strong>{{ tsa.service }}</strong> from {{ tsa.provider }}
                for {{ tsa.duration_months }} months
                (~${{ tsa.estimated_monthly_cost|format_currency }}/mo)
            </li>
            {% endfor %}
        </ul>
    </div>

    <div class="hiring-recommendations">
        <h3>Post-Close Staffing Needs</h3>
        <ul>
            {% for need in staffing_needs %}
            <li class="urgency-{{ need.urgency }}">
                <strong>{{ need.role }}</strong> ({{ need.fte_count }} FTE) - {{ need.urgency }}
                <br><small>{{ need.reason }}</small>
            </li>
            {% endfor %}
        </ul>
    </div>
</div>
{% endblock %}
```

**9.4 Add routes to `web/app.py`**

```python
@app.route('/organization')
def organization_dashboard():
    """Organization domain overview."""
    ...

@app.route('/organization/staffing')
def organization_staffing():
    """Staffing tree view."""
    ...

@app.route('/organization/benchmark')
def organization_benchmark():
    """Benchmark comparison view."""
    ...

@app.route('/organization/msp')
def organization_msp():
    """MSP analysis view."""
    ...

@app.route('/organization/shared-services')
def organization_shared_services():
    """Shared services analysis view."""
    ...
```

### Acceptance Criteria
- [ ] All four views accessible via navigation
- [ ] Benchmark comparison shows variance clearly
- [ ] MSP view expands to show service details
- [ ] Shared services shows hidden headcount prominently
- [ ] TSA and hiring recommendations generated

---

## Phase 10: Integration, Testing & Documentation

### Objective
Integrate all components, create comprehensive tests, and document the module.

### Deliverables

**10.1 Create integration pipeline `services/organization_pipeline.py`**

```python
class OrganizationAnalysisPipeline:
    """
    Orchestrates the complete organization analysis flow.
    """

    def __init__(self):
        self.census_parser = CensusParser()
        self.msp_parser = MSPParser()
        self.benchmark_service = BenchmarkService()
        self.shared_services_analyzer = SharedServicesAnalyzer()
        self.comparison_service = StaffingComparisonService()
        self.reasoning_engine = EnhancedOrganizationReasoning()

    def run_full_analysis(
        self,
        census_file: str,
        facts: List[Fact],
        company_info: CompanyInfo
    ) -> OrganizationAnalysisResult:
        """
        Run complete organization analysis:
        1. Parse census data
        2. Extract MSP information from facts
        3. Identify shared service dependencies
        4. Match to appropriate benchmark
        5. Run comparisons
        6. Generate findings and recommendations
        """

        # Step 1: Parse census
        staff = self.census_parser.parse_file(census_file)
        org_store = OrganizationDataStore(staff_members=staff)

        # Step 2: Aggregate staffing data
        org_store.category_summaries = self.census_parser.aggregate_by_category(staff)

        # Step 3: Extract MSP relationships from facts
        org_store.msp_relationships = self.msp_parser.parse_from_facts(facts)

        # Step 4: Identify shared service dependencies
        org_store.shared_service_dependencies = self.shared_services_analyzer.identify_dependencies(facts)

        # Step 5: Match benchmark profile
        benchmark = self.benchmark_service.match_profile(
            company_info.revenue,
            company_info.employee_count,
            company_info.industry
        )
        org_store.active_benchmark = benchmark

        # Step 6: Run benchmark comparison
        comparison = self.comparison_service.compare_to_benchmark(
            org_store, benchmark, company_info
        )
        org_store.benchmark_comparison_results = comparison

        # Step 7: Calculate totals
        org_store.total_internal_fte = sum(1 for s in staff if s.employment_type == EmploymentType.FTE)
        org_store.total_msp_fte_equivalent = sum(m.total_fte_equivalent for m in org_store.msp_relationships)
        org_store.total_shared_services_fte = sum(d.fte_equivalent for d in org_store.shared_service_dependencies)
        org_store.hidden_headcount_need = self.shared_services_analyzer.calculate_hidden_headcount(
            org_store.shared_service_dependencies
        )

        # Step 8: Generate findings
        result = self.reasoning_engine.analyze_complete_organization(org_store, company_info)

        return result
```

**10.2 Create test suite `tests/test_organization_module.py`**

```python
class TestCensusParser:
    def test_parse_csv_file(self)
    def test_role_classification(self)
    def test_tenure_calculation(self)
    def test_missing_columns_handling(self)

class TestBenchmarkService:
    def test_profile_matching(self)
    def test_comparison_in_range(self)
    def test_comparison_understaffed(self)
    def test_comparison_overstaffed(self)
    def test_missing_role_detection(self)

class TestMSPAnalysis:
    def test_fte_equivalent_calculation(self)
    def test_replacement_cost_estimate(self)
    def test_high_risk_identification(self)

class TestSharedServicesAnalysis:
    def test_dependency_identification(self)
    def test_hidden_headcount_calculation(self)
    def test_tsa_recommendation_generation(self)

class TestOrganizationPipeline:
    def test_full_analysis_flow(self)
    def test_finding_generation(self)
    def test_work_item_generation(self)
```

**10.3 Create test data generator `tests/fixtures/organization_fixtures.py`**

```python
def generate_sample_census(size: str = "medium") -> str:
    """Generate sample census CSV for testing."""
    ...

def generate_sample_msp_facts() -> List[Fact]:
    """Generate sample MSP-related facts."""
    ...

def generate_sample_shared_services_facts() -> List[Fact]:
    """Generate sample shared services facts."""
    ...
```

**10.4 Create documentation `docs/organization_module.md`**

```markdown
# Organization Module Documentation

## Overview
The Organization module provides comprehensive analysis of IT staffing...

## Data Inputs
### Census File Format
...

## Analysis Views
### 1. Staffing Tree View
### 2. Benchmark Comparison
### 3. MSP Analysis
### 4. Shared Services Analysis

## Benchmark Framework
### Available Profiles
### Customizing Benchmarks
### Adding New Profiles

## Integration with Reasoning Engine
...

## API Reference
...
```

### Acceptance Criteria
- [ ] Full pipeline runs end-to-end
- [ ] All unit tests passing
- [ ] Integration tests with sample data passing
- [ ] Documentation complete
- [ ] Sample data generators working

---

## Summary: Phase Dependencies

```
Phase 1: Data Models ──────────────────────┐
                                           │
Phase 2: Benchmark Framework ──────────────┼───┐
                                           │   │
Phase 3: Census Parser ────────────────────┤   │
                                           │   │
Phase 4: MSP Data Capture ─────────────────┤   │
                                           │   │
Phase 5: Shared Services Capture ──────────┤   │
                                           │   │
                                           ▼   ▼
Phase 6: Benchmark Comparison Engine ──────────┤
                                               │
Phase 7: Organization Reasoning ───────────────┤
                                               │
Phase 8: Tree View UI ─────────────────────────┤
                                               │
Phase 9: Dashboard Views ──────────────────────┤
                                               │
                                               ▼
Phase 10: Integration & Testing ───────────────┘
```

## Estimated Deliverables per Phase

| Phase | New Files | Modified Files | Key Output |
|-------|-----------|----------------|------------|
| 1 | 2 | 0 | Data models |
| 2 | 3 | 0 | Benchmark data + service |
| 3 | 3 | 0 | Census parser |
| 4 | 2 | 1 | MSP parser + prompt update |
| 5 | 2 | 1 | Shared services analyzer |
| 6 | 2 | 0 | Comparison engine |
| 7 | 2 | 1 | Enhanced reasoning |
| 8 | 3 | 0 | Tree view UI |
| 9 | 3 | 1 | Dashboard views |
| 10 | 4 | 1 | Tests + docs + pipeline |

**Total: ~27 new files, ~5 modified files**
