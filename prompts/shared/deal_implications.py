"""
Deal-Type Specific Implications

Codified patterns that help the AI recognize and articulate deal-specific
implications. These patterns transform generic facts into actionable insights.

Example:
  Fact: "Uses parent's Microsoft Enterprise Agreement"
  + Pattern: carveout + parent_license
  = Implication: "Post-close will need standalone Microsoft licensing at
                  approximately 1.5-2x cost due to loss of volume discount.
                  Budget $X-Y for Year 1 licensing transition."
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class DealImplication:
    """A specific implication based on fact + deal type."""
    pattern_name: str
    trigger_signals: List[str]  # Keywords/phrases that trigger this pattern
    deal_types: List[str]  # Which deal types this applies to
    implication_template: str  # The insight to surface
    cost_impact: Optional[str]  # Cost range or formula
    timeline_impact: Optional[str]  # Timeline consideration
    action_required: str  # What needs to be done
    priority: str  # high, medium, low


# =============================================================================
# CARVEOUT-SPECIFIC IMPLICATIONS
# =============================================================================

CARVEOUT_IMPLICATIONS = [
    DealImplication(
        pattern_name="parent_enterprise_license",
        trigger_signals=[
            "parent enterprise agreement",
            "corporate Microsoft EA",
            "parent SAP license",
            "shared Oracle agreement",
            "volume discount through parent",
            "bundled licensing"
        ],
        deal_types=["carveout", "divestiture"],
        implication_template="""**License Cost Uplift**: Target currently benefits from parent's enterprise
agreement. Post-separation, standalone licensing will cost approximately 1.5-2x more
per seat due to loss of volume discount. For {user_count} users, expect annual
increase of ${cost_increase_low:,} - ${cost_increase_high:,}.""",
        cost_impact="$200-500 per user annual increase",
        timeline_impact="60-90 days for new agreement negotiation",
        action_required="Begin vendor negotiations immediately; consider alternative vendors; budget for Year 1 uplift",
        priority="high"
    ),

    DealImplication(
        pattern_name="parent_service_desk",
        trigger_signals=[
            "parent service desk",
            "corporate IT support",
            "shared helpdesk",
            "parent-managed tickets",
            "service desk outsourced to parent",
            "parent MSP"
        ],
        deal_types=["carveout", "divestiture"],
        implication_template="""**Service Desk Transition**: IT support currently provided through parent.
Post-separation requires new service desk capability. Options:
- New MSP contract: ${msp_cost_low:,} - ${msp_cost_high:,}/year ({cost_per_user}/user/month)
- In-house build: Higher cost, 6-12 month ramp
- Extended TSA: ${tsa_monthly:,}/month (recommend <6 months)""",
        cost_impact="$50-150 per user per month for MSP",
        timeline_impact="3-6 months to establish, TSA bridge required",
        action_required="Issue RFP for MSP services; define service levels; plan knowledge transfer",
        priority="high"
    ),

    DealImplication(
        pattern_name="parent_identity",
        trigger_signals=[
            "parent Active Directory",
            "corporate Azure AD",
            "federated identity",
            "parent Okta tenant",
            "shared identity provider",
            "corporate SSO"
        ],
        deal_types=["carveout", "divestiture"],
        implication_template="""**Identity Separation (Day-1 Critical)**: Users authenticate through parent
identity systems. This is Day-1 critical - without separation, users cannot
access systems post-close. Requires:
- New directory services (AD/Azure AD/Okta)
- User migration and credential reset
- Application SSO reconfiguration
- MFA re-enrollment

Timeline: 3-6 months; TSA bridge essential.""",
        cost_impact="$200K-800K for identity separation project",
        timeline_impact="Day-1 critical; 3-6 months to full separation",
        action_required="Begin identity architecture design immediately; plan TSA for bridge period",
        priority="high"
    ),

    DealImplication(
        pattern_name="oversized_erp",
        trigger_signals=[
            "SAP for mid-market",
            "Oracle for <$1B company",
            "enterprise ERP for SMB",
            "200+ custom objects",
            "heavily customized ERP"
        ],
        deal_types=["carveout", "acquisition"],
        implication_template="""**ERP Right-Sizing Opportunity**: Current enterprise ERP may be oversized for
standalone entity. For a ${revenue}M company, consider:
- Current ERP TCO: ~${current_tco:,}/year
- Mid-market alternative (NetSuite/Sage Intacct): ~${alt_tco:,}/year
- Potential savings: ${savings_low:,} - ${savings_high:,}/year

This is a Year 2+ optimization - stabilize first, then rationalize.""",
        cost_impact="Potential 40-60% TCO reduction",
        timeline_impact="12-24 month migration if pursued",
        action_required="Assess ERP requirements for standalone; build business case for migration vs. stay",
        priority="medium"
    ),

    DealImplication(
        pattern_name="shared_infrastructure",
        trigger_signals=[
            "parent data center",
            "shared hosting",
            "corporate network",
            "parent WAN",
            "shared infrastructure"
        ],
        deal_types=["carveout", "divestiture"],
        implication_template="""**Infrastructure Separation**: Target systems hosted in parent infrastructure.
Separation options:
1. **Lift & Shift to Cloud**: ${cloud_cost:,}/month, 3-6 months
2. **New Colocation**: ${colo_cost:,}/month, 6-9 months
3. **Extended TSA**: ${tsa_cost:,}/month (not recommended >12 months)

Recommendation: Cloud-first for agility unless regulatory constraints.""",
        cost_impact="$500K-2M migration + ongoing hosting delta",
        timeline_impact="3-12 months depending on approach",
        action_required="Define target state architecture; plan migration waves; establish TSA for bridge",
        priority="high"
    ),

    DealImplication(
        pattern_name="dc_lease_constraint",
        trigger_signals=[
            "non-cancellable lease",
            "lease expiry",
            "owned facility",
            "long-term commitment",
            "colocation contract"
        ],
        deal_types=["carveout", "divestiture", "acquisition"],
        implication_template="""**Stranded Cost Risk**: Data center lease obligations may continue
post-separation even if services are migrated.
- Remaining lease term: {lease_months} months
- Monthly obligation: ${monthly_cost:,}
- Total exposure: ${total_exposure:,}

Mitigation options: sublease, early termination negotiation, assignment to buyer.""",
        cost_impact="Stranded cost = remaining lease value",
        timeline_impact="Lease term constrains migration timeline",
        action_required="Review lease terms; negotiate exit or assignment; factor into deal model",
        priority="medium"
    ),

    DealImplication(
        pattern_name="tool_overlap",
        trigger_signals=[
            "multiple tools",
            "overlapping capabilities",
            "dual vendors",
            "both CrowdStrike and",
            "both Splunk and",
            "redundant tools"
        ],
        deal_types=["carveout", "acquisition"],
        implication_template="""**Tool Rationalization Opportunity**: Multiple overlapping tools identified.
Post-transaction, consolidation can yield:
- License savings: 30-50% of category spend
- Operational efficiency: reduced complexity
- Security improvement: unified visibility

This is Year 1-2 optimization - don't disrupt during separation.""",
        cost_impact="20-40% savings on consolidated categories",
        timeline_impact="6-18 months to rationalize",
        action_required="Inventory overlapping tools; build rationalization roadmap for post-Day-100",
        priority="low"
    ),

    DealImplication(
        pattern_name="high_outsourcing",
        trigger_signals=[
            "outsourced",
            "managed by MSP",
            "contractor",
            "third-party managed",
            ">30% outsourced"
        ],
        deal_types=["carveout", "divestiture"],
        implication_template="""**MSP Contract Transition**: Significant IT functions outsourced to MSPs
that may have contracts through parent:
- Contracts may not be assignable
- Parent pricing may not transfer
- Knowledge concentrated in vendor

Actions: Review contract assignment rights; negotiate new terms; plan knowledge transfer.""",
        cost_impact="New contracts may be 10-20% higher",
        timeline_impact="60-90 days for contract transition",
        action_required="Audit MSP contracts; assess assignability; begin negotiations early",
        priority="high"
    ),
]


# =============================================================================
# ACQUISITION-SPECIFIC IMPLICATIONS
# =============================================================================

ACQUISITION_IMPLICATIONS = [
    DealImplication(
        pattern_name="dual_erp",
        trigger_signals=[
            "multiple ERP",
            "SAP and Oracle",
            "NetSuite and SAP",
            "two ERP systems",
            "dual ERP"
        ],
        deal_types=["acquisition"],
        implication_template="""**ERP Consolidation Opportunity**: Combined entity will have multiple ERPs.
Consolidation typically yields:
- 15-25% reduction in ERP TCO
- Simplified reporting and analytics
- Reduced IT support overhead

Recommendation: Stabilize both (90 days), then build consolidation roadmap.""",
        cost_impact="15-25% ERP cost reduction post-consolidation",
        timeline_impact="18-36 months for full consolidation",
        action_required="Assess which ERP to retain; build migration plan; budget for integration",
        priority="medium"
    ),

    DealImplication(
        pattern_name="email_consolidation",
        trigger_signals=[
            "different email systems",
            "Google Workspace and Microsoft",
            "separate email domains",
            "multiple collaboration platforms"
        ],
        deal_types=["acquisition"],
        implication_template="""**Email/Collaboration Quick Win**: Different email platforms create friction.
Migration to single platform is a quick win:
- Timeline: 30-60 days
- Cost: $10-30 per user migration
- Benefits: unified directory, simplified collaboration

This should be a Day 30-60 priority.""",
        cost_impact="Low cost, high value",
        timeline_impact="30-60 days",
        action_required="Choose target platform; plan migration; communicate to users",
        priority="medium"
    ),

    DealImplication(
        pattern_name="security_tool_synergy",
        trigger_signals=[
            "different security tools",
            "target uses CrowdStrike, buyer uses",
            "separate SIEM",
            "different endpoint protection"
        ],
        deal_types=["acquisition"],
        implication_template="""**Security Stack Synergy**: Combined entity can consolidate security tools:
- Single EDR platform: unified threat visibility
- Consolidated SIEM: centralized monitoring
- Shared SOC: operational efficiency

Synergy potential: 20-40% reduction in security tool spend.""",
        cost_impact="20-40% security tool consolidation",
        timeline_impact="6-12 months for consolidation",
        action_required="Inventory both security stacks; plan consolidation; retain best-of-breed",
        priority="medium"
    ),
]


# =============================================================================
# PATTERN MATCHING ENGINE
# =============================================================================

def get_implications_for_deal_type(deal_type: str) -> List[DealImplication]:
    """Get all relevant implications for a deal type."""
    all_implications = CARVEOUT_IMPLICATIONS + ACQUISITION_IMPLICATIONS

    return [
        impl for impl in all_implications
        if deal_type in impl.deal_types
    ]


def match_facts_to_implications(
    facts: List[Dict],
    deal_type: str
) -> List[Dict]:
    """
    Match extracted facts to implication patterns.

    Returns list of triggered implications with supporting facts.
    """
    implications = get_implications_for_deal_type(deal_type)
    triggered = []

    for impl in implications:
        matching_facts = []

        for fact in facts:
            content = fact.get("content", "").lower()

            # Check if any trigger signal matches
            for signal in impl.trigger_signals:
                if signal.lower() in content:
                    matching_facts.append(fact)
                    break

        if matching_facts:
            triggered.append({
                "pattern": impl.pattern_name,
                "implication": impl.implication_template,
                "cost_impact": impl.cost_impact,
                "timeline_impact": impl.timeline_impact,
                "action_required": impl.action_required,
                "priority": impl.priority,
                "supporting_facts": [f.get("fact_id") for f in matching_facts]
            })

    # Sort by priority
    priority_order = {"high": 0, "medium": 1, "low": 2}
    triggered.sort(key=lambda x: priority_order.get(x["priority"], 99))

    return triggered


def get_implication_prompt_injection(deal_type: str) -> str:
    """
    Generate prompt text to inject into reasoning prompts.

    This teaches the AI what patterns to look for and what implications to draw.
    """
    implications = get_implications_for_deal_type(deal_type)

    prompt_lines = [
        f"\n## {deal_type.upper()}-SPECIFIC CONSIDERATIONS",
        "",
        "When analyzing facts, look for these patterns and call out their implications:",
        ""
    ]

    for impl in implications:
        prompt_lines.extend([
            f"### {impl.pattern_name.replace('_', ' ').title()}",
            f"**Triggers**: {', '.join(impl.trigger_signals[:3])}...",
            f"**Implication**: {impl.implication_template[:200]}...",
            f"**Cost Impact**: {impl.cost_impact}",
            f"**Action**: {impl.action_required}",
            ""
        ])

    prompt_lines.extend([
        "",
        "For EACH relevant pattern you identify:",
        "1. State the specific fact that triggers it",
        "2. Explain the implication for THIS deal",
        "3. Quantify the cost/timeline impact",
        "4. Recommend specific action",
        ""
    ])

    return "\n".join(prompt_lines)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'DealImplication',
    'CARVEOUT_IMPLICATIONS',
    'ACQUISITION_IMPLICATIONS',
    'get_implications_for_deal_type',
    'match_facts_to_implications',
    'get_implication_prompt_injection',
]
