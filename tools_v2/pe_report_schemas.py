"""
PE Report Data Schemas

Structured data contracts for PE-grade executive reporting.
Separates data from rendering - these dataclasses contain NO HTML.

Key Principle: Every PE report section follows the 5-part framework:
1. What You're Getting (Inventory)
2. What It Costs Today (Run-Rate)
3. How It Compares (Benchmark Assessment)
4. What Needs to Happen (Actions/Work Items)
5. Team Implications (Resources/Organization Impact)
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime


# =============================================================================
# DEAL CONTEXT
# =============================================================================

@dataclass
class DealContext:
    """
    Formalized structure for deal context information.

    Previously unstructured Dict - now typed for reliability.
    """
    target_name: str
    deal_type: str = "acquisition"  # acquisition, carveout, merger

    # Target company details
    target_revenue: Optional[float] = None  # Annual revenue in USD
    target_employees: Optional[int] = None
    target_industry: Optional[str] = None
    target_it_budget: Optional[float] = None
    target_it_headcount: Optional[int] = None

    # Buyer details (if applicable)
    buyer_name: Optional[str] = None
    buyer_revenue: Optional[float] = None
    buyer_employees: Optional[int] = None
    buyer_industry: Optional[str] = None
    buyer_it_budget: Optional[float] = None

    # Deal specifics
    deal_value: Optional[float] = None
    expected_close_date: Optional[str] = None
    tsa_required: bool = False
    tsa_duration_months: Optional[int] = None

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "DealContext":
        # Filter to only known fields
        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known_fields}
        return cls(**filtered)

    @property
    def company_size_tier(self) -> str:
        """Determine company size tier for benchmark selection."""
        if self.target_revenue:
            if self.target_revenue < 50_000_000:
                return "0-50M"
            elif self.target_revenue < 100_000_000:
                return "50-100M"
            elif self.target_revenue < 500_000_000:
                return "100-500M"
            else:
                return "500M+"
        elif self.target_employees:
            if self.target_employees < 100:
                return "0-50M"  # Approximate
            elif self.target_employees < 500:
                return "50-100M"
            elif self.target_employees < 2000:
                return "100-500M"
            else:
                return "500M+"
        return "50-100M"  # Default to mid-market


# =============================================================================
# BENCHMARK ASSESSMENT
# =============================================================================

@dataclass
class BenchmarkAssessment:
    """
    Assessment of a domain against industry benchmarks.

    Every assessment MUST include:
    - The assessment value (modern/outdated, lean/bloated, etc.)
    - Rationale explaining the assessment
    - Benchmark source citation (NO fake authority)
    - Business implication ("So what?")
    """
    # Technology modernization assessment
    tech_age: str = "mixed"  # modern, mixed, outdated
    tech_age_rationale: str = ""
    tech_age_benchmark_source: str = ""  # e.g., "Industry average: 5-7 year refresh cycle (Gartner 2025)"

    # Cost efficiency assessment
    cost_posture: str = "in_line"  # lean, in_line, bloated
    cost_posture_rationale: str = ""
    cost_benchmark_source: str = ""  # e.g., "IT % revenue: 3-5% typical for $50-100M companies"

    # Process/capability maturity
    maturity: str = "developing"  # mature, developing, immature
    maturity_rationale: str = ""
    maturity_benchmark_source: str = ""

    # PE DECISION FRAMING
    implication: str = ""  # Business consequence - "So what?"
    triggered_actions: List[str] = field(default_factory=list)  # Top 1-3 work item titles this drives

    # Overall assessment
    overall_grade: str = "Adequate"  # Strong, Adequate, Needs Improvement
    key_callouts: List[str] = field(default_factory=list)  # 2-4 specific things to note

    # Confidence in assessment
    confidence: str = "medium"  # high, medium, low
    confidence_rationale: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "BenchmarkAssessment":
        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known_fields}
        # Handle list fields that might come as None
        if 'triggered_actions' not in filtered or filtered.get('triggered_actions') is None:
            filtered['triggered_actions'] = []
        if 'key_callouts' not in filtered or filtered.get('key_callouts') is None:
            filtered['key_callouts'] = []
        return cls(**filtered)


# =============================================================================
# ACTION ITEMS
# =============================================================================

@dataclass
class ActionItem:
    """
    Top action item with PE decision framing.

    These are the "top 3 actions" shown on each domain report.
    """
    title: str
    so_what: str  # Business implication - why this matters
    cost_range: Tuple[int, int] = (0, 0)  # (low, high) in USD
    timing: str = "Day_100"  # Day_1, Day_100, Post_100
    owner_type: str = "target"  # target, buyer, shared, vendor, msp
    priority: str = "high"  # critical, high, medium
    domain: str = ""

    # Link to work item for traceability
    work_item_id: Optional[str] = None

    # Additional context
    dependencies: List[str] = field(default_factory=list)
    skills_required: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        result = asdict(self)
        # Convert tuple to list for JSON serialization
        result['cost_range'] = list(self.cost_range)
        return result

    @classmethod
    def from_dict(cls, data: Dict) -> "ActionItem":
        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known_fields}
        # Convert list back to tuple for cost_range
        if 'cost_range' in filtered and isinstance(filtered['cost_range'], list):
            filtered['cost_range'] = tuple(filtered['cost_range'])
        return cls(**filtered)

    @property
    def cost_display(self) -> str:
        """Format cost range for display."""
        low, high = self.cost_range
        if low == 0 and high == 0:
            return "TBD"
        elif low == high:
            return f"${low:,.0f}"
        else:
            return f"${low:,.0f} - ${high:,.0f}"


# =============================================================================
# WORK ITEM TAXONOMY
# =============================================================================

@dataclass
class WorkItemTaxonomy:
    """
    Extended taxonomy for work items supporting TSA/separation views.

    Extends the base WorkItem with PE-specific classification.
    """
    work_item_id: str
    title: str

    # Classification
    type: str = "run"  # separation, integration, run, transform
    phase: str = "Day_100"  # Day_1, Day_100, Post_100
    priority: str = "high"  # critical, high, medium, low
    owner_type: str = "target"  # target, buyer, shared, vendor, msp

    # TSA tracking (for carve-outs)
    tsa_dependent: bool = False  # True if requires parent company services
    parent_service: str = ""  # e.g., "HR payroll", "Data center hosting"
    tsa_duration_needed: str = ""  # e.g., "6 months", "12 months"
    standalone_alternative: str = ""  # e.g., "Hire internal", "Outsource to vendor"

    # Cost
    cost_estimate_low: int = 0
    cost_estimate_high: int = 0

    # Domain
    domain: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "WorkItemTaxonomy":
        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known_fields}
        return cls(**filtered)


# =============================================================================
# RESOURCE NEEDS
# =============================================================================

@dataclass
class ResourceNeed:
    """Resource requirement identified for a domain."""
    role: str  # e.g., "Security Architect", "Cloud Engineer"
    type: str = "hire"  # hire, contract, outsource, train
    timing: str = "Day_100"  # When needed
    duration: str = "permanent"  # permanent, 6_months, 12_months, project
    estimated_cost: Optional[int] = None  # Annual cost if known
    rationale: str = ""  # Why this resource is needed

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "ResourceNeed":
        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known_fields}
        return cls(**filtered)


# =============================================================================
# INVENTORY SUMMARY
# =============================================================================

@dataclass
class InventorySummary:
    """Summary of inventory items for a domain."""
    total_count: int = 0
    by_category: Dict[str, int] = field(default_factory=dict)
    by_criticality: Dict[str, int] = field(default_factory=dict)
    key_items: List[str] = field(default_factory=list)  # Names of most important items
    summary_text: str = ""  # e.g., "15 applications, 3 core systems..."

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "InventorySummary":
        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known_fields}
        return cls(**filtered)


# =============================================================================
# DOMAIN REPORT DATA
# =============================================================================

@dataclass
class DomainReportData:
    """
    Structured data (NO HTML) for a domain analysis.

    This is the core data structure for each of the 6 domain reports.
    Follows the 5-section PE framework:
    1. What You're Getting (inventory)
    2. What It Costs Today (costs)
    3. How It Compares (benchmark)
    4. What Needs to Happen (actions)
    5. Team Implications (resources)
    """
    domain: str  # organization, applications, infrastructure, network, cybersecurity, identity_access
    domain_display_name: str = ""  # Human-readable name

    # Section 1: What You're Getting
    inventory_summary: InventorySummary = field(default_factory=InventorySummary)
    inventory_html: str = ""  # Pre-rendered HTML from existing builders (org chart, app landscape)
    inventory_facts: List[Dict] = field(default_factory=list)  # Raw fact data for custom rendering

    # Section 2: What It Costs Today
    run_rate_cost: Tuple[int, int] = (0, 0)  # (low, high) annual run-rate
    cost_breakdown: Dict[str, Tuple[int, int]] = field(default_factory=dict)  # category -> (low, high)
    cost_facts_cited: List[str] = field(default_factory=list)  # Fact IDs supporting costs

    # Section 3: How It Compares
    benchmark_assessment: BenchmarkAssessment = field(default_factory=BenchmarkAssessment)

    # Section 4: What Needs to Happen
    top_actions: List[ActionItem] = field(default_factory=list)  # Top 3 actions
    work_items: List[WorkItemTaxonomy] = field(default_factory=list)  # All work items for domain
    work_item_count: int = 0
    total_investment: Tuple[int, int] = (0, 0)  # (low, high) one-time investment

    # Section 5: Team Implications
    top_implications: List[str] = field(default_factory=list)  # Top 3 business implications
    resource_needs: List[ResourceNeed] = field(default_factory=list)

    # Integration considerations (if buyer context exists)
    integration_considerations: List[str] = field(default_factory=list)
    overlap_ids: List[str] = field(default_factory=list)  # Links to OverlapCandidate IDs

    # Risks for this domain
    risk_count: int = 0
    critical_risks: List[str] = field(default_factory=list)  # Titles of critical/high risks

    # Metadata
    fact_count: int = 0
    gap_count: int = 0
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        result = asdict(self)
        # Convert tuples to lists for JSON serialization
        result['run_rate_cost'] = list(self.run_rate_cost)
        result['total_investment'] = list(self.total_investment)
        result['cost_breakdown'] = {k: list(v) for k, v in self.cost_breakdown.items()}
        # Convert nested dataclasses
        result['inventory_summary'] = self.inventory_summary.to_dict()
        result['benchmark_assessment'] = self.benchmark_assessment.to_dict()
        result['top_actions'] = [a.to_dict() for a in self.top_actions]
        result['work_items'] = [w.to_dict() for w in self.work_items]
        result['resource_needs'] = [r.to_dict() for r in self.resource_needs]
        return result

    @classmethod
    def from_dict(cls, data: Dict) -> "DomainReportData":
        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known_fields}

        # Convert lists back to tuples
        if 'run_rate_cost' in filtered and isinstance(filtered['run_rate_cost'], list):
            filtered['run_rate_cost'] = tuple(filtered['run_rate_cost'])
        if 'total_investment' in filtered and isinstance(filtered['total_investment'], list):
            filtered['total_investment'] = tuple(filtered['total_investment'])
        if 'cost_breakdown' in filtered:
            filtered['cost_breakdown'] = {k: tuple(v) for k, v in filtered['cost_breakdown'].items()}

        # Convert nested dataclasses
        if 'inventory_summary' in filtered and isinstance(filtered['inventory_summary'], dict):
            filtered['inventory_summary'] = InventorySummary.from_dict(filtered['inventory_summary'])
        if 'benchmark_assessment' in filtered and isinstance(filtered['benchmark_assessment'], dict):
            filtered['benchmark_assessment'] = BenchmarkAssessment.from_dict(filtered['benchmark_assessment'])
        if 'top_actions' in filtered:
            filtered['top_actions'] = [ActionItem.from_dict(a) if isinstance(a, dict) else a
                                       for a in filtered['top_actions']]
        if 'work_items' in filtered:
            filtered['work_items'] = [WorkItemTaxonomy.from_dict(w) if isinstance(w, dict) else w
                                      for w in filtered['work_items']]
        if 'resource_needs' in filtered:
            filtered['resource_needs'] = [ResourceNeed.from_dict(r) if isinstance(r, dict) else r
                                          for r in filtered['resource_needs']]

        return cls(**filtered)


# =============================================================================
# DOMAIN HIGHLIGHT (for Executive Dashboard)
# =============================================================================

@dataclass
class DomainHighlight:
    """Summary highlight for a domain shown on executive dashboard."""
    domain: str
    domain_display_name: str
    overall_grade: str  # Strong, Adequate, Needs Improvement
    key_finding: str  # One-sentence summary
    watch_items: List[str] = field(default_factory=list)  # 2-3 things to watch
    run_rate_cost: Tuple[int, int] = (0, 0)
    investment_needed: Tuple[int, int] = (0, 0)
    work_item_count: int = 0
    risk_count: int = 0

    def to_dict(self) -> Dict:
        result = asdict(self)
        result['run_rate_cost'] = list(self.run_rate_cost)
        result['investment_needed'] = list(self.investment_needed)
        return result

    @classmethod
    def from_dict(cls, data: Dict) -> "DomainHighlight":
        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known_fields}
        if 'run_rate_cost' in filtered and isinstance(filtered['run_rate_cost'], list):
            filtered['run_rate_cost'] = tuple(filtered['run_rate_cost'])
        if 'investment_needed' in filtered and isinstance(filtered['investment_needed'], list):
            filtered['investment_needed'] = tuple(filtered['investment_needed'])
        return cls(**filtered)


# =============================================================================
# EXECUTIVE DASHBOARD DATA
# =============================================================================

@dataclass
class ExecutiveDashboardData:
    """
    Data for the executive dashboard landing page.

    Partner gets the story in 30 seconds, clicks through for details.
    """
    # Deal info
    target_name: str
    analysis_date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    deal_context: Optional[DealContext] = None

    # Overall assessment
    overall_assessment: str = ""  # 1-2 sentence IT estate assessment
    overall_grade: str = "Adequate"  # Strong, Adequate, Needs Improvement

    # Key metrics
    total_it_budget: Tuple[int, int] = (0, 0)  # Run-rate (low, high)
    total_investment_needed: Tuple[int, int] = (0, 0)  # One-time (low, high)
    it_headcount: int = 0
    it_pct_revenue: Optional[float] = None

    # Domain highlights (6 cards)
    domain_highlights: Dict[str, DomainHighlight] = field(default_factory=dict)

    # Summary by phase (for investment)
    investment_by_phase: Dict[str, Tuple[int, int]] = field(default_factory=dict)  # Day_1, Day_100, Post_100

    # TSA/Separation breakdown (if applicable)
    tsa_costs: Tuple[int, int] = (0, 0)
    separation_costs: Tuple[int, int] = (0, 0)
    integration_costs: Tuple[int, int] = (0, 0)

    # Top items
    top_risks: List[Dict[str, str]] = field(default_factory=list)  # Top 3 risks with title, severity, domain
    top_opportunities: List[str] = field(default_factory=list)  # Top 3 opportunities

    # Counts
    total_work_items: int = 0
    total_risks: int = 0
    total_facts: int = 0
    total_gaps: int = 0

    def to_dict(self) -> Dict:
        result = asdict(self)
        # Convert tuples to lists
        result['total_it_budget'] = list(self.total_it_budget)
        result['total_investment_needed'] = list(self.total_investment_needed)
        result['tsa_costs'] = list(self.tsa_costs)
        result['separation_costs'] = list(self.separation_costs)
        result['integration_costs'] = list(self.integration_costs)
        result['investment_by_phase'] = {k: list(v) for k, v in self.investment_by_phase.items()}
        # Convert nested dataclasses
        if self.deal_context:
            result['deal_context'] = self.deal_context.to_dict()
        result['domain_highlights'] = {k: v.to_dict() for k, v in self.domain_highlights.items()}
        return result

    @classmethod
    def from_dict(cls, data: Dict) -> "ExecutiveDashboardData":
        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known_fields}

        # Convert lists to tuples
        for field_name in ['total_it_budget', 'total_investment_needed', 'tsa_costs',
                          'separation_costs', 'integration_costs']:
            if field_name in filtered and isinstance(filtered[field_name], list):
                filtered[field_name] = tuple(filtered[field_name])

        if 'investment_by_phase' in filtered:
            filtered['investment_by_phase'] = {k: tuple(v) for k, v in filtered['investment_by_phase'].items()}

        # Convert nested dataclasses
        if 'deal_context' in filtered and isinstance(filtered['deal_context'], dict):
            filtered['deal_context'] = DealContext.from_dict(filtered['deal_context'])
        if 'domain_highlights' in filtered:
            filtered['domain_highlights'] = {
                k: DomainHighlight.from_dict(v) if isinstance(v, dict) else v
                for k, v in filtered['domain_highlights'].items()
            }

        return cls(**filtered)


# =============================================================================
# COSTS REPORT DATA
# =============================================================================

@dataclass
class CostsReportData:
    """
    Aggregated run-rate spending data across all domains.
    """
    # Overall summary
    total_run_rate: Tuple[int, int] = (0, 0)  # Annual (low, high)
    cost_per_employee: Optional[int] = None
    it_pct_revenue: Optional[float] = None

    # By domain
    by_domain: Dict[str, Tuple[int, int]] = field(default_factory=dict)

    # By category
    infrastructure_costs: Tuple[int, int] = (0, 0)  # Hosting, cloud, DR
    application_costs: Tuple[int, int] = (0, 0)  # Licenses, SaaS
    personnel_costs: Tuple[int, int] = (0, 0)  # IT staff, loaded costs
    vendor_costs: Tuple[int, int] = (0, 0)  # MSP, outsourcing
    network_costs: Tuple[int, int] = (0, 0)  # Connectivity, security

    # Benchmark comparison
    benchmark_assessment: str = ""  # LLM-based: "In-line", "Above average", "Below average"
    key_cost_drivers: List[str] = field(default_factory=list)

    # Source facts
    cost_facts_cited: List[str] = field(default_factory=list)

    # Metadata
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        result = asdict(self)
        # Convert tuples to lists
        tuple_fields = ['total_run_rate', 'infrastructure_costs', 'application_costs',
                       'personnel_costs', 'vendor_costs', 'network_costs']
        for f in tuple_fields:
            if f in result:
                result[f] = list(result[f])
        result['by_domain'] = {k: list(v) for k, v in self.by_domain.items()}
        return result

    @classmethod
    def from_dict(cls, data: Dict) -> "CostsReportData":
        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known_fields}

        # Convert lists to tuples
        tuple_fields = ['total_run_rate', 'infrastructure_costs', 'application_costs',
                       'personnel_costs', 'vendor_costs', 'network_costs']
        for f in tuple_fields:
            if f in filtered and isinstance(filtered[f], list):
                filtered[f] = tuple(filtered[f])

        if 'by_domain' in filtered:
            filtered['by_domain'] = {k: tuple(v) for k, v in filtered['by_domain'].items()}

        return cls(**filtered)


# =============================================================================
# INVESTMENT REPORT DATA
# =============================================================================

@dataclass
class WorkItemSummary:
    """Summary of a work item for the investment report."""
    title: str
    domain: str
    phase: str  # Day_1, Day_100, Post_100
    priority: str
    cost_estimate_low: int = 0
    cost_estimate_high: int = 0
    owner_type: str = "target"
    work_item_id: str = ""
    type: str = "run"  # separation, integration, run, transform

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "WorkItemSummary":
        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known_fields}
        return cls(**filtered)


@dataclass
class InvestmentReportData:
    """
    Aggregated one-time investment data across all domains.
    """
    # Cost summary
    total_one_time: Tuple[int, int] = (0, 0)  # All work items aggregated
    by_phase: Dict[str, Tuple[int, int]] = field(default_factory=dict)  # Day_1, Day_100, Post_100
    by_domain: Dict[str, Tuple[int, int]] = field(default_factory=dict)
    by_priority: Dict[str, Tuple[int, int]] = field(default_factory=dict)  # critical, high, medium
    by_type: Dict[str, Tuple[int, int]] = field(default_factory=dict)  # separation, integration, run, transform

    # Work items summary
    work_items: List[WorkItemSummary] = field(default_factory=list)
    work_items_by_domain: Dict[str, List[WorkItemSummary]] = field(default_factory=dict)
    critical_path_items: List[str] = field(default_factory=list)  # Must-do item titles

    # Timeline
    day_1_items: List[WorkItemSummary] = field(default_factory=list)
    day_100_items: List[WorkItemSummary] = field(default_factory=list)
    post_100_items: List[WorkItemSummary] = field(default_factory=list)

    # Counts
    total_count: int = 0
    by_phase_count: Dict[str, int] = field(default_factory=dict)
    by_priority_count: Dict[str, int] = field(default_factory=dict)

    # Metadata
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        result = asdict(self)
        # Convert tuples to lists
        result['total_one_time'] = list(self.total_one_time)
        result['by_phase'] = {k: list(v) for k, v in self.by_phase.items()}
        result['by_domain'] = {k: list(v) for k, v in self.by_domain.items()}
        result['by_priority'] = {k: list(v) for k, v in self.by_priority.items()}
        result['by_type'] = {k: list(v) for k, v in self.by_type.items()}
        # Convert work items
        result['work_items'] = [w.to_dict() for w in self.work_items]
        result['work_items_by_domain'] = {
            k: [w.to_dict() for w in v] for k, v in self.work_items_by_domain.items()
        }
        result['day_1_items'] = [w.to_dict() for w in self.day_1_items]
        result['day_100_items'] = [w.to_dict() for w in self.day_100_items]
        result['post_100_items'] = [w.to_dict() for w in self.post_100_items]
        return result

    @classmethod
    def from_dict(cls, data: Dict) -> "InvestmentReportData":
        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known_fields}

        # Convert lists to tuples
        if 'total_one_time' in filtered and isinstance(filtered['total_one_time'], list):
            filtered['total_one_time'] = tuple(filtered['total_one_time'])

        for dict_field in ['by_phase', 'by_domain', 'by_priority', 'by_type']:
            if dict_field in filtered:
                filtered[dict_field] = {k: tuple(v) for k, v in filtered[dict_field].items()}

        # Convert work items
        list_fields = ['work_items', 'day_1_items', 'day_100_items', 'post_100_items']
        for f in list_fields:
            if f in filtered:
                filtered[f] = [WorkItemSummary.from_dict(w) if isinstance(w, dict) else w
                              for w in filtered[f]]

        if 'work_items_by_domain' in filtered:
            filtered['work_items_by_domain'] = {
                k: [WorkItemSummary.from_dict(w) if isinstance(w, dict) else w for w in v]
                for k, v in filtered['work_items_by_domain'].items()
            }

        return cls(**filtered)


# =============================================================================
# EXECUTIVE SUMMARY DATA
# =============================================================================

@dataclass
class RiskSummary:
    """Summary of a risk for executive reporting."""
    title: str
    domain: str
    severity: str
    implication: str  # Business impact
    mitigation: str
    finding_id: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "RiskSummary":
        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known_fields}
        return cls(**filtered)


@dataclass
class ExecutiveSummaryData:
    """
    Data for the PE executive summary.

    Brings together "things that matter" - NOT a deal recommendation.
    """
    # Overall snapshot
    target_name: str
    analysis_date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    domains_analyzed: int = 6

    # Key metrics
    total_it_budget: Tuple[int, int] = (0, 0)
    total_investment_needed: Tuple[int, int] = (0, 0)
    it_headcount: int = 0
    it_pct_revenue: Optional[float] = None

    # Things that matter
    critical_risks: List[RiskSummary] = field(default_factory=list)  # Not deal-breakers, just risks to consider
    key_opportunities: List[str] = field(default_factory=list)  # Where value can be created
    benchmark_outliers: List[str] = field(default_factory=list)  # Things significantly above/below normal
    major_investments: List[str] = field(default_factory=list)  # Large cost items (>$500K)

    # By domain highlights
    domain_highlights: Dict[str, DomainHighlight] = field(default_factory=dict)

    # Overall assessment narrative
    overall_narrative: str = ""  # 2-3 paragraph assessment

    # Metadata
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        result = asdict(self)
        result['total_it_budget'] = list(self.total_it_budget)
        result['total_investment_needed'] = list(self.total_investment_needed)
        result['critical_risks'] = [r.to_dict() for r in self.critical_risks]
        result['domain_highlights'] = {k: v.to_dict() for k, v in self.domain_highlights.items()}
        return result

    @classmethod
    def from_dict(cls, data: Dict) -> "ExecutiveSummaryData":
        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known_fields}

        if 'total_it_budget' in filtered and isinstance(filtered['total_it_budget'], list):
            filtered['total_it_budget'] = tuple(filtered['total_it_budget'])
        if 'total_investment_needed' in filtered and isinstance(filtered['total_investment_needed'], list):
            filtered['total_investment_needed'] = tuple(filtered['total_investment_needed'])

        if 'critical_risks' in filtered:
            filtered['critical_risks'] = [RiskSummary.from_dict(r) if isinstance(r, dict) else r
                                          for r in filtered['critical_risks']]
        if 'domain_highlights' in filtered:
            filtered['domain_highlights'] = {
                k: DomainHighlight.from_dict(v) if isinstance(v, dict) else v
                for k, v in filtered['domain_highlights'].items()
            }

        return cls(**filtered)


# =============================================================================
# DOMAIN DISPLAY CONFIGURATION
# =============================================================================

DOMAIN_DISPLAY_NAMES = {
    "organization": "IT Organization",
    "applications": "Applications",
    "infrastructure": "Infrastructure",
    "network": "Network",
    "cybersecurity": "Cybersecurity",
    "identity_access": "Identity & Access",
}

DOMAIN_ICONS = {
    "organization": "users",
    "applications": "grid",
    "infrastructure": "server",
    "network": "globe",
    "cybersecurity": "shield",
    "identity_access": "key",
}

DOMAIN_ORDER = [
    "organization",
    "applications",
    "infrastructure",
    "network",
    "cybersecurity",
    "identity_access",
]
