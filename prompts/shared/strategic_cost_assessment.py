"""
Strategic Cost Assessment Framework

Provides top-down AI-driven cost assessment based on company profile
and deal characteristics, complementing bottom-up inventory costing.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum


class DealComplexity(Enum):
    """Deal complexity levels affecting cost multipliers."""
    LOW = "low"          # Clean acquisition, modern stack
    MEDIUM = "medium"    # Some legacy, manageable separation
    HIGH = "high"        # Significant entanglement, legacy debt
    VERY_HIGH = "very_high"  # Complex carveout, heavy shared services


@dataclass
class CompanyProfile:
    """Target company profile for cost estimation."""
    revenue: float  # Annual revenue in USD
    employees: int
    it_headcount: int
    app_count: int
    dc_count: int
    cloud_percentage: float  # 0-100
    outsourcing_percentage: float  # 0-100
    erp_count: int  # Number of ERP systems


@dataclass
class DealProfile:
    """Deal characteristics affecting cost."""
    deal_type: str  # acquisition, carveout, divestiture
    shared_services_dependency: bool
    parent_licenses: bool  # Using parent's enterprise licenses
    tsa_required: bool
    target_integration_timeline_months: int


# =============================================================================
# COST DRIVER PATTERNS
# =============================================================================

COST_DRIVER_PATTERNS = {
    # License & Vendor Patterns
    "parent_enterprise_license": {
        "signals": [
            "parent enterprise agreement",
            "shared Microsoft EA",
            "corporate SAP license",
            "parent volume discount",
            "bundled under parent"
        ],
        "carveout_implication": "Must establish standalone vendor relationships. Enterprise licenses (Microsoft EA, SAP, Oracle) typically cost 1.5-2x more per seat without parent's volume discount.",
        "cost_impact": "high",
        "typical_range_pct": (0.15, 0.25),  # 15-25% of total separation
        "work_item": "Negotiate standalone enterprise agreements; consider alternative vendors for cost optimization"
    },

    "shared_identity": {
        "signals": [
            "parent Active Directory",
            "corporate Okta tenant",
            "shared Azure AD",
            "federated with parent",
            "parent-managed identity"
        ],
        "carveout_implication": "Identity separation is Day-1 critical. Requires new directory, SSO reconfiguration, and user migration. TSA typically 3-6 months.",
        "cost_impact": "high",
        "typical_range": (200_000, 800_000),
        "work_item": "Plan identity separation; establish new directory services; migrate users"
    },

    "shared_service_desk": {
        "signals": [
            "parent service desk",
            "corporate helpdesk",
            "shared ITSM",
            "parent-managed tickets",
            "outsourced to parent MSP"
        ],
        "carveout_implication": "Need standalone service desk capability. Options: new MSP contract ($50-150/user/month), in-house build, or extended TSA.",
        "cost_impact": "medium",
        "typical_range_per_user": (50, 150),  # Monthly
        "work_item": "Evaluate MSP options; plan service desk transition"
    },

    "oversized_erp": {
        "signals": [
            "SAP S/4HANA for <$500M company",
            "Oracle ERP for mid-market",
            "enterprise ERP",
            "complex ERP customizations"
        ],
        "carveout_implication": "Consider right-sizing to mid-market ERP (NetSuite, Sage Intacct, Acumatica). Can reduce TCO by 40-60% for companies <$500M revenue.",
        "cost_impact": "medium",
        "synergy_range": (500_000, 2_000_000),  # Annual savings
        "work_item": "Assess ERP right-sizing opportunity; compare TCO of current vs. alternatives"
    },

    "dual_tools": {
        "signals": [
            "overlapping tools",
            "duplicate capabilities",
            "both SentinelOne and CrowdStrike",
            "multiple SIEM",
            "redundant security tools"
        ],
        "carveout_implication": "Tool rationalization opportunity. Consolidating duplicate tools can save 30-50% in that category.",
        "cost_impact": "low",
        "synergy_range": (100_000, 500_000),
        "work_item": "Inventory overlapping tools; plan rationalization roadmap"
    },

    "dc_lease_constraint": {
        "signals": [
            "non-cancellable lease",
            "owned data center",
            "long-term colocation",
            "lease expiry >12 months"
        ],
        "carveout_implication": "Stranded cost risk. If DC services not needed post-separation, lease obligations continue. Consider sublease or early termination negotiation.",
        "cost_impact": "medium",
        "risk_range": (500_000, 2_000_000),
        "work_item": "Review DC lease terms; assess migration timeline vs. lease obligations"
    },

    "legacy_systems": {
        "signals": [
            "end of support",
            "ECC 6.0",
            "Windows Server 2012",
            "unsupported version",
            "10+ years old"
        ],
        "carveout_implication": "Technical debt requires remediation. Legacy systems increase separation complexity and ongoing risk.",
        "cost_impact": "high",
        "typical_range": (1_000_000, 5_000_000),
        "work_item": "Assess legacy system remediation; plan upgrade or replacement"
    },

    "high_outsourcing": {
        "signals": [
            ">30% outsourced",
            "MSP dependency",
            "managed services",
            "contractor-heavy"
        ],
        "carveout_implication": "MSP contracts may need renegotiation or replacement. Parent MSP relationships may not transfer.",
        "cost_impact": "medium",
        "work_item": "Review MSP contracts; assess transferability; plan new MSP relationships"
    },
}


# =============================================================================
# DEAL TYPE SPECIFIC CONSIDERATIONS
# =============================================================================

DEAL_TYPE_CONSIDERATIONS = {
    "carveout": {
        "primary_concerns": [
            "TSA scope and duration",
            "Shared services untangling",
            "License portability",
            "Identity separation",
            "Data segregation"
        ],
        "cost_multiplier": 1.3,  # Carveouts typically 30% more complex
        "typical_timeline_months": (12, 24),
        "key_questions": [
            "What services are provided by parent today?",
            "Which licenses are under parent enterprise agreements?",
            "How is identity/authentication managed?",
            "What data needs to be segregated?",
            "What is the TSA exit timeline?"
        ],
        "strategic_considerations": [
            "TSA costs can be $200-500K/month for complex separations",
            "Identity separation is Day-1 critical - plan 3-6 months",
            "License renegotiation should start immediately - lead times are 60-90 days",
            "Consider 'lift and shift' for Day-1, optimize in Year 2",
            "Right-sizing opportunity: smaller company may not need enterprise tools"
        ]
    },

    "acquisition": {
        "primary_concerns": [
            "Integration complexity",
            "System consolidation",
            "Synergy capture",
            "Culture/process alignment",
            "Redundancy elimination"
        ],
        "cost_multiplier": 1.0,  # Baseline
        "typical_timeline_months": (6, 18),
        "key_questions": [
            "What systems overlap with buyer?",
            "Which target systems should be retained vs. retired?",
            "What is the integration vs. standalone strategy?",
            "Where are synergy opportunities?",
            "What is the Day-1 vs. Day-100 plan?"
        ],
        "strategic_considerations": [
            "Integration synergies typically 15-30% of combined IT spend",
            "ERP consolidation is usually the largest single initiative",
            "Quick wins: email migration, identity federation",
            "Don't rush integration - stabilize first (90 days)",
            "Retain key IT talent during transition"
        ]
    },

    "divestiture": {
        "primary_concerns": [
            "Clean separation",
            "Buyer readiness",
            "TSA provision",
            "Data segregation",
            "Ongoing obligations"
        ],
        "cost_multiplier": 1.1,
        "typical_timeline_months": (6, 12),
        "key_questions": [
            "What must be separated vs. can remain shared?",
            "What TSA services will seller provide?",
            "What is the data segregation requirement?",
            "What contracts need assignment or replacement?",
            "What knowledge transfer is needed?"
        ],
        "strategic_considerations": [
            "TSA pricing should cover fully-loaded costs plus margin (10-15%)",
            "Plan for TSA extension requests - build in flexibility",
            "Data segregation is often underestimated - start early",
            "Document everything for clean handoff",
            "Consider impact on retained business"
        ]
    }
}


# =============================================================================
# STRATEGIC ASSESSMENT GENERATION
# =============================================================================

def calculate_complexity_score(
    company: CompanyProfile,
    deal: DealProfile
) -> Tuple[DealComplexity, Dict[str, any]]:
    """Calculate deal complexity based on profile factors."""

    score = 0
    factors = []

    # Company size factors
    if company.employees > 5000:
        score += 2
        factors.append("Large employee base (>5000)")
    elif company.employees > 1000:
        score += 1
        factors.append("Mid-size employee base (1000-5000)")

    # Application complexity
    if company.app_count > 50:
        score += 2
        factors.append("Large application portfolio (>50 apps)")
    elif company.app_count > 25:
        score += 1
        factors.append("Moderate application portfolio (25-50 apps)")

    # ERP complexity
    if company.erp_count > 1:
        score += 2
        factors.append(f"Multiple ERP systems ({company.erp_count})")

    # Infrastructure complexity
    if company.dc_count > 2:
        score += 1
        factors.append(f"Multiple data centers ({company.dc_count})")

    # Cloud maturity (lower = more complex separation)
    if company.cloud_percentage < 30:
        score += 2
        factors.append("Low cloud adoption (<30%) - heavy on-prem")
    elif company.cloud_percentage < 60:
        score += 1
        factors.append("Moderate cloud adoption (30-60%)")

    # Deal-specific factors
    if deal.deal_type == "carveout":
        score += 2
        factors.append("Carveout deal type (inherent complexity)")

    if deal.shared_services_dependency:
        score += 2
        factors.append("Shared services dependency with parent")

    if deal.parent_licenses:
        score += 1
        factors.append("Parent enterprise licenses in use")

    # Determine complexity level
    if score >= 10:
        complexity = DealComplexity.VERY_HIGH
    elif score >= 7:
        complexity = DealComplexity.HIGH
    elif score >= 4:
        complexity = DealComplexity.MEDIUM
    else:
        complexity = DealComplexity.LOW

    return complexity, {
        "score": score,
        "factors": factors,
        "complexity": complexity.value
    }


def estimate_total_separation_cost(
    company: CompanyProfile,
    deal: DealProfile,
    complexity: DealComplexity
) -> Dict[str, any]:
    """Estimate total IT separation cost based on profile."""

    # Base cost per employee (industry benchmarks)
    base_cost_per_employee = {
        DealComplexity.LOW: (1000, 2000),
        DealComplexity.MEDIUM: (2000, 4000),
        DealComplexity.HIGH: (4000, 7000),
        DealComplexity.VERY_HIGH: (7000, 12000),
    }

    low, high = base_cost_per_employee[complexity]

    # Apply deal type multiplier
    multiplier = DEAL_TYPE_CONSIDERATIONS[deal.deal_type]["cost_multiplier"]

    base_low = company.employees * low * multiplier
    base_high = company.employees * high * multiplier

    # Adjust for specific factors
    adjustments = []

    if deal.shared_services_dependency:
        # Add TSA exit costs
        tsa_low = company.employees * 100 * 12  # $100/user/month for 12 months
        tsa_high = company.employees * 200 * 18  # $200/user/month for 18 months
        base_low += tsa_low
        base_high += tsa_high
        adjustments.append(f"TSA exit costs: ${tsa_low/1e6:.1f}M - ${tsa_high/1e6:.1f}M")

    if deal.parent_licenses:
        # License transition costs
        license_low = company.employees * 200  # $200/user one-time
        license_high = company.employees * 500  # $500/user one-time
        base_low += license_low
        base_high += license_high
        adjustments.append(f"License transition: ${license_low/1e6:.1f}M - ${license_high/1e6:.1f}M")

    if company.erp_count > 1:
        # ERP complexity
        erp_add = 1_000_000 * (company.erp_count - 1)
        base_low += erp_add
        base_high += erp_add * 2
        adjustments.append(f"Multi-ERP complexity: ${erp_add/1e6:.1f}M - ${erp_add*2/1e6:.1f}M")

    return {
        "total_low": round(base_low, -5),  # Round to nearest 100K
        "total_high": round(base_high, -5),
        "total_mid": round((base_low + base_high) / 2, -5),
        "adjustments": adjustments,
        "timeline_months": DEAL_TYPE_CONSIDERATIONS[deal.deal_type]["typical_timeline_months"],
        "annual_run_rate_change": estimate_run_rate_change(company, deal)
    }


def estimate_run_rate_change(
    company: CompanyProfile,
    deal: DealProfile
) -> Dict[str, any]:
    """Estimate ongoing IT cost change post-separation."""

    # Baseline IT spend estimate (3-5% of revenue is typical)
    estimated_it_spend = company.revenue * 0.04

    if deal.deal_type == "carveout":
        # Carveouts typically see 10-30% cost increase initially
        # due to loss of scale, then opportunity to optimize
        year1_change = (0.10, 0.30)  # 10-30% increase
        year2_change = (-0.05, 0.15)  # -5% to +15% (optimization kicks in)
    elif deal.deal_type == "acquisition":
        # Acquisitions have synergy opportunity
        year1_change = (-0.05, 0.10)  # -5% to +10%
        year2_change = (-0.20, -0.05)  # 5-20% savings from synergies
    else:  # divestiture
        year1_change = (0.05, 0.15)
        year2_change = (0.00, 0.10)

    return {
        "estimated_current_it_spend": estimated_it_spend,
        "year1_change_pct": year1_change,
        "year1_change_usd": (
            estimated_it_spend * year1_change[0],
            estimated_it_spend * year1_change[1]
        ),
        "year2_change_pct": year2_change,
        "year2_change_usd": (
            estimated_it_spend * year2_change[0],
            estimated_it_spend * year2_change[1]
        )
    }


def identify_cost_drivers(
    facts: List[Dict],
    deal: DealProfile
) -> List[Dict]:
    """Identify key cost drivers from extracted facts."""

    identified_drivers = []

    for pattern_name, pattern in COST_DRIVER_PATTERNS.items():
        # Check if any facts match this pattern's signals
        matching_facts = []
        for fact in facts:
            content = fact.get("content", "").lower()
            for signal in pattern["signals"]:
                if signal.lower() in content:
                    matching_facts.append(fact)
                    break

        if matching_facts:
            driver = {
                "pattern": pattern_name,
                "implication": pattern.get(f"{deal.deal_type}_implication", pattern.get("carveout_implication")),
                "cost_impact": pattern["cost_impact"],
                "matching_facts": [f.get("fact_id") for f in matching_facts],
                "work_item": pattern.get("work_item")
            }

            # Add cost/synergy ranges if available
            if "typical_range" in pattern:
                driver["cost_range"] = pattern["typical_range"]
            if "synergy_range" in pattern:
                driver["synergy_range"] = pattern["synergy_range"]

            identified_drivers.append(driver)

    # Sort by impact
    impact_order = {"high": 0, "medium": 1, "low": 2}
    identified_drivers.sort(key=lambda x: impact_order.get(x["cost_impact"], 99))

    return identified_drivers


def generate_strategic_assessment(
    company: CompanyProfile,
    deal: DealProfile,
    facts: List[Dict]
) -> Dict[str, any]:
    """Generate complete strategic cost assessment."""

    # Calculate complexity
    complexity, complexity_details = calculate_complexity_score(company, deal)

    # Estimate total cost
    cost_estimate = estimate_total_separation_cost(company, deal, complexity)

    # Identify specific cost drivers
    cost_drivers = identify_cost_drivers(facts, deal)

    # Get deal-type specific considerations
    deal_considerations = DEAL_TYPE_CONSIDERATIONS[deal.deal_type]

    return {
        "summary": {
            "deal_type": deal.deal_type,
            "complexity": complexity.value,
            "total_cost_range": (cost_estimate["total_low"], cost_estimate["total_high"]),
            "total_cost_mid": cost_estimate["total_mid"],
            "timeline_months": cost_estimate["timeline_months"]
        },
        "complexity_analysis": complexity_details,
        "cost_estimate": cost_estimate,
        "cost_drivers": cost_drivers,
        "deal_considerations": {
            "primary_concerns": deal_considerations["primary_concerns"],
            "key_questions": deal_considerations["key_questions"],
            "strategic_considerations": deal_considerations["strategic_considerations"]
        },
        "run_rate_impact": cost_estimate["annual_run_rate_change"]
    }


# =============================================================================
# PROMPT GENERATION FOR AI SYNTHESIS
# =============================================================================

def get_strategic_assessment_prompt(
    company: CompanyProfile,
    deal: DealProfile,
    facts_summary: str
) -> str:
    """Generate prompt for AI strategic cost assessment."""

    deal_context = DEAL_TYPE_CONSIDERATIONS[deal.deal_type]

    return f"""You are an IT M&A expert providing a strategic cost assessment for a {deal.deal_type}.

COMPANY PROFILE:
- Revenue: ${company.revenue/1e6:.0f}M
- Employees: {company.employees:,}
- IT Headcount: {company.it_headcount}
- Applications: {company.app_count}
- Data Centers: {company.dc_count}
- Cloud Adoption: {company.cloud_percentage:.0f}%
- Outsourcing: {company.outsourcing_percentage:.0f}%
- ERP Systems: {company.erp_count}

DEAL CHARACTERISTICS:
- Deal Type: {deal.deal_type}
- Shared Services Dependency: {deal.shared_services_dependency}
- Parent Enterprise Licenses: {deal.parent_licenses}
- TSA Required: {deal.tsa_required}
- Target Timeline: {deal.target_integration_timeline_months} months

KEY FACTS FROM DISCOVERY:
{facts_summary}

PRIMARY CONCERNS FOR {deal.deal_type.upper()}:
{chr(10).join(f"- {c}" for c in deal_context["primary_concerns"])}

Provide a strategic IT cost assessment that includes:

1. **Executive Summary** (2-3 sentences on overall IT posture and deal implications)

2. **Total Separation Cost Estimate** with breakdown:
   - TSA/Transition Costs
   - Infrastructure Separation
   - Application Migration/Licensing
   - Organization/People Costs
   - Contingency

3. **Top 5 Cost Drivers** (ranked by impact):
   - What is it?
   - Why does it matter for this deal?
   - Estimated cost range
   - Recommended action

4. **Synergy/Optimization Opportunities**:
   - Quick wins (0-6 months)
   - Medium-term (6-18 months)
   - Strategic (18+ months)

5. **Key Risks to Cost Estimate**:
   - What could make this more expensive?
   - What assumptions are we making?

6. **Strategic Observations**:
   - What should the IC/deal team know?
   - What makes this deal different?

Use specific numbers where facts support them. Flag estimates vs. facts clearly.
Format with clear headers and bullet points.
"""


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'DealComplexity',
    'CompanyProfile',
    'DealProfile',
    'COST_DRIVER_PATTERNS',
    'DEAL_TYPE_CONSIDERATIONS',
    'calculate_complexity_score',
    'estimate_total_separation_cost',
    'identify_cost_drivers',
    'generate_strategic_assessment',
    'get_strategic_assessment_prompt',
]
