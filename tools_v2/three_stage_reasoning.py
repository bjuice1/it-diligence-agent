"""
Three-Stage Reasoning Engine

Stage 1: LLM identifies considerations from facts
Stage 2: Rule-base matches activities and applies cost anchors
Stage 3: LLM validates "does this make sense?"

This architecture combines:
- LLM strength: Interpretation, context understanding, novel situations
- Rule strength: Consistent costing, market anchors, reproducibility
- LLM validation: Catches gaps, provides confidence

Cost per full analysis: ~$0.30-0.50
- Stage 1: ~$0.15-0.20
- Stage 2: $0 (rules)
- Stage 3: ~$0.10-0.15
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime

logger = logging.getLogger(__name__)


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class IdentifiedConsideration:
    """A consideration identified by Stage 1 LLM."""
    consideration_id: str
    source_fact_ids: List[str]
    workstream: str
    finding: str           # What we found
    implication: str       # What it means
    deal_impact: str       # Why it matters for the deal
    suggested_category: str  # LLM's suggestion for matching


@dataclass
class QuantitativeContext:
    """Tracks quantities with source attribution."""
    user_count: Optional[int] = None
    user_count_source: str = "unknown"  # "extracted", "assumed", "override"

    application_count: Optional[int] = None
    application_count_source: str = "unknown"

    site_count: Optional[int] = None
    site_count_source: str = "unknown"

    server_count: Optional[int] = None
    server_count_source: str = "unknown"

    def get_with_default(self, field: str, default: int) -> Tuple[int, str]:
        """Get value with source tracking. Returns (value, source)."""
        value = getattr(self, field, None)
        source = getattr(self, f"{field}_source", "unknown")
        if value is None:
            return default, "assumed"
        return value, source


@dataclass
class MatchedActivity:
    """An activity matched from rule-base in Stage 2."""
    activity_id: str
    name: str
    description: str
    workstream: str
    triggered_by: str      # consideration_id
    activity_type: str     # "implementation", "operational", "license"

    # From rule-base
    cost_range: Tuple[float, float]
    timeline_months: Tuple[int, int]
    cost_formula: str      # How cost was calculated

    # Quantity tracking for auditability
    quantity_used: Optional[int] = None
    quantity_source: str = "unknown"  # "extracted", "assumed", "override"

    # TSA
    requires_tsa: bool = False
    tsa_duration_months: Optional[Tuple[int, int]] = None
    tsa_source: str = "rule"  # "rule" = derived from template, "negotiated" = from refinement


@dataclass
class ValidationResult:
    """Result from Stage 3 validation."""
    is_valid: bool
    confidence_score: float  # 0-1

    # Issues found
    missing_considerations: List[str]
    questionable_costs: List[Dict]
    suggested_additions: List[Dict]
    suggested_removals: List[str]

    # Recommendations
    recommendations: List[str]

    # Overall assessment
    assessment: str


@dataclass
class ThreeStageOutput:
    """Complete output from three-stage reasoning."""
    # Metadata
    deal_type: str
    facts_analyzed: int
    timestamp: str

    # Stage outputs
    considerations: List[IdentifiedConsideration]
    activities: List[MatchedActivity]
    validation: ValidationResult

    # Totals
    total_cost_range: Tuple[float, float]
    total_timeline_months: Tuple[int, int]
    tsa_services: List[Dict]

    # Quantitative context with source tracking
    quant_context: Optional[QuantitativeContext] = None

    # Breakdown by activity type
    implementation_cost_range: Optional[Tuple[float, float]] = None
    operational_runrate_range: Optional[Tuple[float, float]] = None
    license_cost_range: Optional[Tuple[float, float]] = None

    # Cost tracking
    stage1_cost: float = 0.0
    stage2_cost: float = 0.0  # Always 0
    stage3_cost: float = 0.0
    total_llm_cost: float = 0.0

    # Warnings for reviewers
    assumptions_to_verify: List[str] = field(default_factory=list)


# =============================================================================
# STAGE 1: LLM IDENTIFIES CONSIDERATIONS
# =============================================================================

STAGE1_PROMPT = """You are an expert IT M&A advisor analyzing due diligence facts.

## Deal Context
Deal Type: {deal_type}
{additional_context}

## Your Task
Read these facts and identify the KEY CONSIDERATIONS for IT due diligence.

For each consideration:
1. What does this fact MEAN for the deal?
2. What WORKSTREAM does it affect?
3. What type of ACTIVITY will be needed?

## Facts
{facts_formatted}

## Output Format
```json
{{
    "considerations": [
        {{
            "source_fact_ids": ["F-001"],
            "workstream": "identity|email|infrastructure|network|security|applications|service_desk",
            "finding": "What we found (1 clear sentence)",
            "implication": "What this means for the deal (1-2 sentences)",
            "deal_impact": "Why this matters - Day 1 risk? Cost driver? TSA need?",
            "suggested_category": "One of: parent_dependency, technology_mismatch, technical_debt, security_gap, resource_gap, license_issue, data_migration, integration_need"
        }}
    ],
    "quantitative_context": {{
        "user_count": number or null,
        "application_count": number or null,
        "site_count": number or null,
        "server_count": number or null
    }},
    "critical_day1_items": ["List of things that MUST work on Day 1"],
    "key_uncertainties": ["What we don't know that matters"]
}}
```

## Guidelines
- Focus on MATERIAL considerations (things that drive cost, risk, or timeline)
- Be specific - "identity dependency" not "IT dependency"
- For carveouts: Focus on parent dependencies and standalone readiness
- For acquisitions: Focus on technology mismatches and integration needs
- Don't list generic IT activities - only what the FACTS support
"""


def stage1_identify_considerations(
    facts: List[Dict],
    deal_type: str,
    additional_context: str = "",
    model: str = "claude-sonnet-4-20250514",
) -> Tuple[List[IdentifiedConsideration], Dict, float]:
    """
    Stage 1: Use LLM to identify considerations from facts.

    Returns:
        Tuple of (considerations, quantitative_context, llm_cost)
    """
    import anthropic
    import os

    # Format facts
    facts_formatted = "\n".join([
        f"[{f.get('fact_id', 'N/A')}] {f.get('category', '')}: {f.get('content', '')}"
        for f in facts
    ])

    prompt = STAGE1_PROMPT.format(
        deal_type=deal_type,
        additional_context=additional_context or "None provided",
        facts_formatted=facts_formatted,
    )

    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    response = client.messages.create(
        model=model,
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}]
    )

    # Calculate cost
    input_tokens = response.usage.input_tokens
    output_tokens = response.usage.output_tokens
    if "sonnet" in model:
        cost = (input_tokens * 0.003 + output_tokens * 0.015) / 1000
    elif "haiku" in model:
        cost = (input_tokens * 0.00025 + output_tokens * 0.00125) / 1000
    else:
        cost = (input_tokens * 0.015 + output_tokens * 0.075) / 1000

    # Parse response
    response_text = response.content[0].text

    import re
    json_match = re.search(r'\{[\s\S]*\}', response_text)
    if not json_match:
        logger.error("Failed to parse Stage 1 response")
        return [], {}, cost

    data = json.loads(json_match.group())

    considerations = []
    for i, c in enumerate(data.get('considerations', [])):
        considerations.append(IdentifiedConsideration(
            consideration_id=f"C-{i+1:03d}",
            source_fact_ids=c.get('source_fact_ids', []),
            workstream=c.get('workstream', 'general'),
            finding=c.get('finding', ''),
            implication=c.get('implication', ''),
            deal_impact=c.get('deal_impact', ''),
            suggested_category=c.get('suggested_category', 'general'),
        ))

    quant_context = data.get('quantitative_context', {})

    logger.info(f"Stage 1: Identified {len(considerations)} considerations (${cost:.4f})")

    return considerations, quant_context, cost


# =============================================================================
# STAGE 2: RULE-BASE MATCHES ACTIVITIES
# =============================================================================

# Category normalization - maps LLM variations to canonical categories
CATEGORY_SYNONYMS = {
    # Parent dependency variations
    "parent_dependency": "parent_dependency",
    "parent_dependent": "parent_dependency",
    "shared_service": "parent_dependency",
    "shared_services": "parent_dependency",
    "dependency": "parent_dependency",
    "separation": "parent_dependency",
    "carveout_dependency": "parent_dependency",
    "identity_separation": "parent_dependency",
    "email_separation": "parent_dependency",
    "infrastructure_separation": "parent_dependency",

    # Technology mismatch variations
    "technology_mismatch": "technology_mismatch",
    "tech_mismatch": "technology_mismatch",
    "platform_mismatch": "technology_mismatch",
    "integration_need": "technology_mismatch",
    "integration": "technology_mismatch",
    "consolidation": "technology_mismatch",

    # Technical debt variations
    "technical_debt": "technical_debt",
    "tech_debt": "technical_debt",
    "legacy_system": "technical_debt",
    "legacy": "technical_debt",
    "eol": "technical_debt",
    "end_of_life": "technical_debt",
    "modernization": "technical_debt",

    # Security variations
    "security_gap": "security_gap",
    "security": "security_gap",
    "compliance_gap": "security_gap",
    "security_risk": "security_gap",

    # Resource variations
    "resource_gap": "resource_gap",
    "staffing": "resource_gap",
    "headcount": "resource_gap",

    # License variations
    "license_issue": "license_issue",
    "licensing": "license_issue",
    "license": "license_issue",
    "software_license": "license_issue",

    # Data variations
    "data_migration": "data_migration",
    "data": "data_migration",
}


def normalize_category(category: str) -> str:
    """Normalize LLM category to canonical form."""
    # Clean up the category string
    cleaned = category.lower().strip().replace(" ", "_").replace("-", "_")
    return CATEGORY_SYNONYMS.get(cleaned, cleaned)


# Activity templates by category
# Each activity has:
#   - activity_type: "implementation" (one-time), "operational" (ongoing), "license" (licensing)
#   - cost model: base_cost, per_user_cost, per_app_cost, etc.
#   - TSA: requires_tsa and tsa_duration

ACTIVITY_TEMPLATES = {
    "parent_dependency": {
        "identity": [
            {
                "name": "Design standalone identity architecture",
                "description": "Design target-state identity platform and migration approach",
                "base_cost": (50000, 120000),
                "timeline_months": (1, 2),
                "requires_tsa": False,
                "activity_type": "implementation",
            },
            {
                "name": "Provision identity platform",
                "description": "Stand up new identity infrastructure (Azure AD, Okta, etc.)",
                "base_cost": (75000, 200000),
                "timeline_months": (1, 3),
                "requires_tsa": True,
                "tsa_duration": (3, 6),
                "activity_type": "implementation",
            },
            {
                "name": "Migrate user accounts",
                "description": "Migrate users to new identity platform",
                "per_user_cost": (15, 40),
                "timeline_months": (2, 4),
                "requires_tsa": True,
                "tsa_duration": (3, 6),
                "activity_type": "implementation",
            },
            {
                "name": "Reconfigure application SSO",
                "description": "Update applications to use new identity provider",
                "per_app_cost": (2000, 8000),
                "timeline_months": (2, 4),
                "requires_tsa": True,
                "tsa_duration": (3, 6),
                "activity_type": "implementation",
            },
        ],
        "email": [
            {
                "name": "Provision email platform",
                "description": "Stand up standalone email environment",
                "base_cost": (30000, 80000),
                "timeline_months": (1, 2),
                "requires_tsa": True,
                "tsa_duration": (2, 4),
                "activity_type": "implementation",
            },
            {
                "name": "Migrate mailboxes",
                "description": "Migrate email, calendar, contacts to new platform",
                "per_user_cost": (20, 50),
                "timeline_months": (2, 4),
                "requires_tsa": True,
                "tsa_duration": (2, 4),
                "activity_type": "implementation",
            },
        ],
        "infrastructure": [
            {
                "name": "Design target infrastructure",
                "description": "Design standalone hosting environment",
                "base_cost": (40000, 100000),
                "timeline_months": (1, 2),
                "requires_tsa": False,
                "activity_type": "implementation",
            },
            {
                "name": "Provision infrastructure",
                "description": "Build out hosting environment (cloud or colo)",
                "base_cost": (100000, 300000),
                "timeline_months": (2, 4),
                "requires_tsa": True,
                "tsa_duration": (3, 6),
                "activity_type": "implementation",
            },
            {
                "name": "Migrate workloads",
                "description": "Migrate servers/applications to new infrastructure",
                "per_server_cost": (500, 2000),
                "timeline_months": (3, 6),
                "requires_tsa": True,
                "tsa_duration": (3, 6),
                "activity_type": "implementation",
            },
        ],
        "network": [
            {
                "name": "Design network architecture",
                "description": "Design standalone network topology",
                "base_cost": (30000, 75000),
                "timeline_months": (1, 2),
                "requires_tsa": False,
                "activity_type": "implementation",
            },
            {
                "name": "Implement WAN connectivity",
                "description": "Establish standalone WAN (MPLS, SD-WAN)",
                "per_site_cost": (15000, 50000),
                "timeline_months": (2, 4),
                "requires_tsa": True,
                "tsa_duration": (3, 6),
                "activity_type": "implementation",
            },
        ],
        "security": [
            {
                "name": "Design security architecture",
                "description": "Design standalone security stack",
                "base_cost": (40000, 100000),
                "timeline_months": (1, 2),
                "requires_tsa": False,
                "activity_type": "implementation",
            },
            {
                "name": "Implement security tooling",
                "description": "Deploy endpoint, network, and monitoring tools",
                "base_cost": (75000, 200000),
                "timeline_months": (2, 4),
                "requires_tsa": True,
                "tsa_duration": (2, 4),
                "activity_type": "implementation",
            },
        ],
        "service_desk": [
            {
                "name": "Establish IT support function",
                "description": "Stand up help desk and support processes",
                "base_cost": (50000, 150000),
                "timeline_months": (1, 3),
                "requires_tsa": True,
                "tsa_duration": (3, 6),
                "activity_type": "implementation",
            },
        ],
    },
    "technology_mismatch": {
        "identity": [
            {
                "name": "Integrate identity platforms",
                "description": "Integrate target identity into buyer's platform",
                "per_user_cost": (10, 30),
                "timeline_months": (2, 4),
                "requires_tsa": False,
                "activity_type": "implementation",
            },
        ],
        "email": [
            {
                "name": "Migrate to buyer email platform",
                "description": "Migrate target email to buyer's platform",
                "per_user_cost": (25, 60),
                "timeline_months": (2, 4),
                "requires_tsa": False,
                "activity_type": "implementation",
            },
        ],
        "applications": [
            {
                "name": "Consolidate to buyer ERP",
                "description": "Migrate target to buyer's ERP platform",
                "base_cost": (500000, 2000000),
                "timeline_months": (12, 24),
                "requires_tsa": False,
                "activity_type": "implementation",
            },
        ],
    },
    "technical_debt": {
        "infrastructure": [
            {
                "name": "Remediate technical debt",
                "description": "Address legacy systems and EOL components",
                "base_cost": (100000, 500000),
                "timeline_months": (3, 12),
                "requires_tsa": False,
                "activity_type": "implementation",
            },
        ],
    },
    "security_gap": {
        "security": [
            {
                "name": "Remediate security gaps",
                "description": "Address identified security deficiencies",
                "base_cost": (50000, 200000),
                "timeline_months": (2, 6),
                "requires_tsa": False,
                "activity_type": "implementation",
            },
        ],
    },
    # =========================================================================
    # LICENSE ACTIVITIES - Software licensing considerations
    # =========================================================================
    "license_issue": {
        "applications": [
            {
                "name": "License transfer negotiation",
                "description": "Negotiate transfer of existing software licenses to new entity",
                "base_cost": (25000, 75000),
                "timeline_months": (1, 3),
                "requires_tsa": False,
                "activity_type": "license",
            },
            {
                "name": "New license procurement",
                "description": "Procure new software licenses (when transfer not possible)",
                "per_user_cost": (50, 200),  # Varies widely by software
                "timeline_months": (1, 2),
                "requires_tsa": False,
                "activity_type": "license",
            },
        ],
        "infrastructure": [
            {
                "name": "Infrastructure license separation",
                "description": "Separate/transfer infrastructure licenses (VMware, Windows Server, etc.)",
                "per_server_cost": (500, 2000),
                "timeline_months": (1, 2),
                "requires_tsa": False,
                "activity_type": "license",
            },
        ],
    },
    # =========================================================================
    # RESOURCE/OPERATIONAL ACTIVITIES - Ongoing operational needs
    # =========================================================================
    "resource_gap": {
        "service_desk": [
            {
                "name": "IT operations staffing",
                "description": "Hire/contract IT staff for standalone operations",
                "base_cost": (150000, 400000),  # Annual cost, Year 1
                "timeline_months": (2, 4),
                "requires_tsa": True,
                "tsa_duration": (3, 6),
                "activity_type": "operational",
                "note": "Represents Year 1 staffing cost; ongoing run-rate",
            },
            {
                "name": "Managed services contract",
                "description": "Contract managed services provider for IT operations",
                "per_user_cost": (30, 80),  # Per user per month, annualized
                "timeline_months": (1, 2),
                "requires_tsa": True,
                "tsa_duration": (2, 4),
                "activity_type": "operational",
                "note": "Annual managed services cost",
            },
        ],
        "security": [
            {
                "name": "Security operations staffing",
                "description": "Security analyst/engineer for standalone operations",
                "base_cost": (120000, 250000),  # Annual cost
                "timeline_months": (2, 4),
                "requires_tsa": True,
                "tsa_duration": (3, 6),
                "activity_type": "operational",
            },
        ],
    },
}

# =========================================================================
# OPERATIONAL RUN-RATE TEMPLATES - Post-separation ongoing costs
# These are NOT implementation activities but ongoing operational costs
# =========================================================================
OPERATIONAL_RUNRATE_TEMPLATES = {
    "identity": {
        "name": "Identity platform run-rate",
        "description": "Annual cost for standalone identity platform (Azure AD, Okta)",
        "per_user_annual": (3, 8),  # Per user per year
        "activity_type": "operational_runrate",
    },
    "email": {
        "name": "Email platform run-rate",
        "description": "Annual cost for standalone email (M365, Google Workspace)",
        "per_user_annual": (120, 300),  # Per user per year
        "activity_type": "operational_runrate",
    },
    "infrastructure": {
        "name": "Infrastructure run-rate",
        "description": "Annual infrastructure hosting costs",
        "per_server_annual": (2000, 8000),  # Per server per year
        "activity_type": "operational_runrate",
    },
    "security": {
        "name": "Security tooling run-rate",
        "description": "Annual security tool licensing and operations",
        "per_user_annual": (20, 60),  # Per user per year
        "activity_type": "operational_runrate",
    },
    "service_desk": {
        "name": "IT support run-rate",
        "description": "Annual IT support/helpdesk costs",
        "per_user_annual": (200, 500),  # Per user per year
        "activity_type": "operational_runrate",
    },
}


def stage2_match_activities(
    considerations: List[IdentifiedConsideration],
    quant_context: Dict,
    deal_type: str,
    include_runrate: bool = True,
) -> Tuple[List[MatchedActivity], List[Dict], QuantitativeContext]:
    """
    Stage 2: Match considerations to activity templates and calculate costs.

    Args:
        considerations: Identified considerations from Stage 1
        quant_context: Quantitative context from Stage 1
        deal_type: Type of deal
        include_runrate: Whether to include operational run-rate estimates

    Returns:
        Tuple of (matched_activities, tsa_services, quant_with_sources)
    """
    activities = []
    tsa_services = []
    activity_counter = 0

    # Track quantities with source attribution
    quant_tracked = QuantitativeContext()

    # Get quantities - track whether extracted or assumed
    if quant_context.get('user_count'):
        quant_tracked.user_count = quant_context['user_count']
        quant_tracked.user_count_source = "extracted"
    else:
        quant_tracked.user_count = 1000
        quant_tracked.user_count_source = "assumed"

    if quant_context.get('application_count'):
        quant_tracked.application_count = quant_context['application_count']
        quant_tracked.application_count_source = "extracted"
    else:
        quant_tracked.application_count = 30
        quant_tracked.application_count_source = "assumed"

    if quant_context.get('site_count'):
        quant_tracked.site_count = quant_context['site_count']
        quant_tracked.site_count_source = "extracted"
    else:
        quant_tracked.site_count = 5
        quant_tracked.site_count_source = "assumed"

    if quant_context.get('server_count'):
        quant_tracked.server_count = quant_context['server_count']
        quant_tracked.server_count_source = "extracted"
    else:
        quant_tracked.server_count = 50
        quant_tracked.server_count_source = "assumed"

    # Use tracked values
    user_count = quant_tracked.user_count
    app_count = quant_tracked.application_count
    site_count = quant_tracked.site_count
    server_count = quant_tracked.server_count

    # Track which workstreams have activities (for run-rate)
    workstreams_with_activities = set()

    for consideration in considerations:
        # NORMALIZE the category to handle LLM variations
        raw_category = consideration.suggested_category
        category = normalize_category(raw_category)
        workstream = consideration.workstream

        # Find matching templates
        templates = ACTIVITY_TEMPLATES.get(category, {}).get(workstream, [])

        if not templates:
            # Try parent_dependency as fallback for carveouts
            if deal_type == "carveout":
                templates = ACTIVITY_TEMPLATES.get("parent_dependency", {}).get(workstream, [])

        # Still no match? Try workstream-only matching across all categories
        if not templates:
            for cat_templates in ACTIVITY_TEMPLATES.values():
                if workstream in cat_templates:
                    templates = cat_templates[workstream]
                    logger.info(f"Fallback match: {raw_category}/{workstream} → found via workstream")
                    break

        for template in templates:
            activity_counter += 1

            # Calculate cost with source tracking
            quantity_used = None
            quantity_source = None

            if 'base_cost' in template:
                cost_low, cost_high = template['base_cost']
                cost_formula = f"Base: ${cost_low:,.0f}-${cost_high:,.0f}"
            elif 'per_user_cost' in template:
                per_user_low, per_user_high = template['per_user_cost']
                cost_low = per_user_low * user_count
                cost_high = per_user_high * user_count
                cost_formula = f"{user_count:,} users × ${per_user_low}-${per_user_high}"
                quantity_used = user_count
                quantity_source = quant_tracked.user_count_source
            elif 'per_app_cost' in template:
                per_app_low, per_app_high = template['per_app_cost']
                cost_low = per_app_low * app_count
                cost_high = per_app_high * app_count
                cost_formula = f"{app_count} apps × ${per_app_low:,}-${per_app_high:,}"
                quantity_used = app_count
                quantity_source = quant_tracked.application_count_source
            elif 'per_site_cost' in template:
                per_site_low, per_site_high = template['per_site_cost']
                cost_low = per_site_low * site_count
                cost_high = per_site_high * site_count
                cost_formula = f"{site_count} sites × ${per_site_low:,}-${per_site_high:,}"
                quantity_used = site_count
                quantity_source = quant_tracked.site_count_source
            elif 'per_server_cost' in template:
                per_server_low, per_server_high = template['per_server_cost']
                cost_low = per_server_low * server_count
                cost_high = per_server_high * server_count
                cost_formula = f"{server_count} servers × ${per_server_low:,}-${per_server_high:,}"
                quantity_used = server_count
                quantity_source = quant_tracked.server_count_source
            else:
                cost_low, cost_high = 0, 0
                cost_formula = "Unknown"

            # Flag assumed quantities in the formula
            if quantity_source == "assumed":
                cost_formula += " [ASSUMED]"

            activity = MatchedActivity(
                activity_id=f"A-{activity_counter:03d}",
                name=template['name'],
                description=template['description'],
                workstream=workstream,
                triggered_by=consideration.consideration_id,
                activity_type=template.get('activity_type', 'implementation'),
                cost_range=(cost_low, cost_high),
                timeline_months=template['timeline_months'],
                cost_formula=cost_formula,
                quantity_used=quantity_used,
                quantity_source=quantity_source or "n/a",
                requires_tsa=template.get('requires_tsa', False),
                tsa_duration_months=template.get('tsa_duration'),
                tsa_source="rule",
            )

            activities.append(activity)
            workstreams_with_activities.add(workstream)

            # Track TSA with source
            if activity.requires_tsa:
                tsa_services.append({
                    'service': activity.name,
                    'workstream': workstream,
                    'duration_months': activity.tsa_duration_months,
                    'triggered_by': consideration.consideration_id,
                    'source': 'rule',  # Distinguished from 'negotiated'
                })

    # Add operational run-rate estimates if requested
    if include_runrate and workstreams_with_activities:
        runrate_activities = _calculate_runrate(
            workstreams_with_activities,
            quant_tracked,
            activity_counter,
        )
        activities.extend(runrate_activities)

    logger.info(f"Stage 2: Matched {len(activities)} activities from {len(considerations)} considerations")

    return activities, tsa_services, quant_tracked


def _calculate_runrate(
    workstreams: set,
    quant: QuantitativeContext,
    start_counter: int,
) -> List[MatchedActivity]:
    """Calculate operational run-rate activities for relevant workstreams."""
    activities = []
    counter = start_counter

    for workstream in workstreams:
        if workstream not in OPERATIONAL_RUNRATE_TEMPLATES:
            continue

        template = OPERATIONAL_RUNRATE_TEMPLATES[workstream]
        counter += 1

        # Calculate annual cost
        if 'per_user_annual' in template:
            low, high = template['per_user_annual']
            cost_low = low * quant.user_count
            cost_high = high * quant.user_count
            formula = f"{quant.user_count:,} users × ${low}-${high}/yr"
            if quant.user_count_source == "assumed":
                formula += " [ASSUMED]"
        elif 'per_server_annual' in template:
            low, high = template['per_server_annual']
            cost_low = low * quant.server_count
            cost_high = high * quant.server_count
            formula = f"{quant.server_count:,} servers × ${low:,}-${high:,}/yr"
            if quant.server_count_source == "assumed":
                formula += " [ASSUMED]"
        else:
            continue

        activity = MatchedActivity(
            activity_id=f"A-{counter:03d}",
            name=template['name'],
            description=template['description'],
            workstream=workstream,
            triggered_by="runrate",
            activity_type="operational_runrate",
            cost_range=(cost_low, cost_high),
            timeline_months=(12, 12),  # Annual
            cost_formula=formula,
            requires_tsa=False,
        )

        activities.append(activity)

    return activities


# =============================================================================
# STAGE 3: LLM VALIDATES
# =============================================================================

STAGE3_PROMPT = """You are an expert IT M&A advisor reviewing an automated analysis.

## Deal Context
Deal Type: {deal_type}
User Count: {user_count:,}

## Original Facts
{facts_summary}

## Considerations Identified (Stage 1)
{considerations_summary}

## Activities Matched (Stage 2)
{activities_summary}

## Total Estimates
Cost Range: ${total_low:,.0f} - ${total_high:,.0f}
TSA Services: {tsa_count}

## Your Task
Review this analysis and answer:
1. Does this make sense given the facts?
2. Are there obvious GAPS (things the facts mention but we didn't address)?
3. Are any costs clearly WRONG (too high or too low)?
4. What's your confidence in this estimate?

## Output Format
```json
{{
    "is_valid": true/false,
    "confidence_score": 0.0-1.0,
    "missing_considerations": [
        "Things mentioned in facts but not addressed"
    ],
    "questionable_costs": [
        {{
            "activity": "Activity name",
            "issue": "Why it seems wrong",
            "suggested_adjustment": "What it should be"
        }}
    ],
    "suggested_additions": [
        {{
            "activity": "What's missing",
            "reason": "Why it's needed based on facts",
            "estimated_cost": [low, high]
        }}
    ],
    "suggested_removals": ["Activity IDs that shouldn't be included"],
    "recommendations": [
        "Specific actionable recommendations"
    ],
    "assessment": "2-3 sentence overall assessment"
}}
```

Be specific. If something is wrong, say exactly what and why.
If everything looks good, say so with high confidence.
"""


def stage3_validate(
    facts: List[Dict],
    considerations: List[IdentifiedConsideration],
    activities: List[MatchedActivity],
    tsa_services: List[Dict],
    deal_type: str,
    quant_context: Dict,
    model: str = "claude-sonnet-4-20250514",
) -> Tuple[ValidationResult, float]:
    """
    Stage 3: Use LLM to validate the matched activities.

    Returns:
        Tuple of (validation_result, llm_cost)
    """
    import anthropic
    import os

    # Summarize inputs for prompt
    facts_summary = "\n".join([
        f"- {f.get('content', '')[:150]}"
        for f in facts[:15]  # Limit to keep prompt manageable
    ])

    considerations_summary = "\n".join([
        f"- [{c.workstream}] {c.finding} → {c.implication}"
        for c in considerations
    ])

    activities_summary = "\n".join([
        f"- {a.name}: ${a.cost_range[0]:,.0f}-${a.cost_range[1]:,.0f} ({a.cost_formula})"
        for a in activities
    ])

    total_low = sum(a.cost_range[0] for a in activities)
    total_high = sum(a.cost_range[1] for a in activities)

    prompt = STAGE3_PROMPT.format(
        deal_type=deal_type,
        user_count=quant_context.get('user_count', 1000),
        facts_summary=facts_summary,
        considerations_summary=considerations_summary,
        activities_summary=activities_summary,
        total_low=total_low,
        total_high=total_high,
        tsa_count=len(tsa_services),
    )

    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    response = client.messages.create(
        model=model,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    # Calculate cost
    input_tokens = response.usage.input_tokens
    output_tokens = response.usage.output_tokens
    if "sonnet" in model:
        cost = (input_tokens * 0.003 + output_tokens * 0.015) / 1000
    elif "haiku" in model:
        cost = (input_tokens * 0.00025 + output_tokens * 0.00125) / 1000
    else:
        cost = (input_tokens * 0.015 + output_tokens * 0.075) / 1000

    # Parse response
    response_text = response.content[0].text

    import re
    json_match = re.search(r'\{[\s\S]*\}', response_text)

    if json_match:
        data = json.loads(json_match.group())

        validation = ValidationResult(
            is_valid=data.get('is_valid', True),
            confidence_score=data.get('confidence_score', 0.7),
            missing_considerations=data.get('missing_considerations', []),
            questionable_costs=data.get('questionable_costs', []),
            suggested_additions=data.get('suggested_additions', []),
            suggested_removals=data.get('suggested_removals', []),
            recommendations=data.get('recommendations', []),
            assessment=data.get('assessment', 'Review complete'),
        )
    else:
        validation = ValidationResult(
            is_valid=True,
            confidence_score=0.5,
            missing_considerations=[],
            questionable_costs=[],
            suggested_additions=[],
            suggested_removals=[],
            recommendations=["Could not parse validation response - manual review recommended"],
            assessment="Validation parsing failed",
        )

    logger.info(f"Stage 3: Validation complete, confidence={validation.confidence_score:.0%} (${cost:.4f})")

    return validation, cost


# =============================================================================
# STRUCTURED DOMAIN VALIDATORS (Alternative to one-shot validation)
# =============================================================================

DOMAIN_VALIDATION_CHECKS = {
    "identity": [
        "Are all identity dependencies addressed (SSO, directory, MFA)?",
        "Is user migration scoped correctly for the user count?",
        "Are application SSO reconfigurations accounted for?",
    ],
    "email": [
        "Is email migration scoped for all users?",
        "Are shared mailboxes and distribution lists considered?",
        "Is email archival/retention addressed?",
    ],
    "infrastructure": [
        "Are all servers/VMs accounted for in migration?",
        "Is disaster recovery addressed?",
        "Are storage and backup systems included?",
    ],
    "network": [
        "Are all sites covered in network separation?",
        "Is WAN connectivity addressed for each location?",
        "Are firewall rules and network security considered?",
    ],
    "security": [
        "Are endpoint security tools addressed?",
        "Is SIEM/logging separation considered?",
        "Are compliance requirements (SOC2, etc.) factored in?",
    ],
    "applications": [
        "Are all business-critical applications identified?",
        "Are integration points with parent systems addressed?",
        "Are license transfers vs new procurement considered?",
    ],
}


def run_structured_validation(
    facts: List[Dict],
    considerations: List[IdentifiedConsideration],
    activities: List[MatchedActivity],
    deal_type: str,
    quant_context: Dict,
    model: str = "claude-sonnet-4-20250514",
) -> Tuple[Dict[str, Dict], float]:
    """
    Run structured domain-by-domain validation.

    More thorough than one-shot validation for complex deals.

    Returns:
        Tuple of (domain_results, total_cost)
    """
    import anthropic
    import os

    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    total_cost = 0.0

    # Identify which workstreams have activities
    workstreams_covered = set(a.workstream for a in activities)

    results = {}

    for domain, checks in DOMAIN_VALIDATION_CHECKS.items():
        if domain not in workstreams_covered:
            continue

        # Get domain-specific facts and activities
        domain_considerations = [c for c in considerations if c.workstream == domain]
        domain_activities = [a for a in activities if a.workstream == domain]

        if not domain_activities:
            continue

        # Build focused prompt
        prompt = f"""Review the {domain.upper()} workstream analysis:

## Considerations Identified
{chr(10).join([f'- {c.finding}' for c in domain_considerations])}

## Activities Planned
{chr(10).join([f'- {a.name}: ${a.cost_range[0]:,.0f}-${a.cost_range[1]:,.0f}' for a in domain_activities])}

## Validation Checklist
{chr(10).join([f'{i+1}. {check}' for i, check in enumerate(checks)])}

For each checklist item, respond with:
- "PASS" if adequately addressed
- "GAP" if missing or incomplete
- Brief explanation

Format as JSON:
```json
{{
    "domain": "{domain}",
    "checks": [
        {{"question": "...", "status": "PASS|GAP", "explanation": "..."}}
    ],
    "overall_status": "PASS|NEEDS_ATTENTION",
    "gaps_found": ["list of gaps"],
    "suggestions": ["list of suggestions"]
}}
```
"""

        response = client.messages.create(
            model="claude-3-5-haiku-20241022",  # Use faster model for each domain
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        )

        # Calculate cost
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        cost = (input_tokens * 0.00025 + output_tokens * 0.00125) / 1000
        total_cost += cost

        # Parse response
        import re
        response_text = response.content[0].text
        json_match = re.search(r'\{[\s\S]*\}', response_text)

        if json_match:
            try:
                result = json.loads(json_match.group())
                results[domain] = result
            except:
                results[domain] = {"status": "parse_error", "raw": response_text}
        else:
            results[domain] = {"status": "parse_error", "raw": response_text}

    return results, total_cost


def aggregate_structured_validation(
    domain_results: Dict[str, Dict]
) -> ValidationResult:
    """Convert structured validation results to ValidationResult."""

    all_gaps = []
    all_suggestions = []
    domains_with_issues = []

    for domain, result in domain_results.items():
        gaps = result.get('gaps_found', [])
        suggestions = result.get('suggestions', [])

        if gaps:
            all_gaps.extend([f"[{domain}] {g}" for g in gaps])
            domains_with_issues.append(domain)

        if suggestions:
            all_suggestions.extend([f"[{domain}] {s}" for s in suggestions])

    # Calculate confidence based on gaps
    total_domains = len(domain_results)
    domains_passing = total_domains - len(domains_with_issues)
    confidence = domains_passing / max(total_domains, 1)

    return ValidationResult(
        is_valid=len(all_gaps) == 0,
        confidence_score=confidence,
        missing_considerations=all_gaps,
        questionable_costs=[],
        suggested_additions=[{"activity": s, "reason": "Domain validation"} for s in all_suggestions[:5]],
        suggested_removals=[],
        recommendations=all_suggestions[:5] if all_suggestions else ["All domains validated successfully"],
        assessment=f"Validated {total_domains} domains. {len(all_gaps)} gaps found across {len(domains_with_issues)} domains."
    )


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def run_three_stage_analysis(
    fact_store: Any,
    deal_type: str,
    meeting_notes: str = "",
    model: str = "claude-sonnet-4-20250514",
    include_runrate: bool = True,
) -> ThreeStageOutput:
    """
    Run complete three-stage reasoning analysis.

    Args:
        fact_store: FactStore with extracted facts
        deal_type: "carveout", "acquisition", etc.
        meeting_notes: Additional context
        model: Which Claude model to use
        include_runrate: Whether to include operational run-rate estimates

    Returns:
        ThreeStageOutput with full analysis
    """
    from tools_v2.reasoning_integration import factstore_to_reasoning_format

    # Convert facts
    facts = factstore_to_reasoning_format(fact_store)

    logger.info(f"Starting three-stage analysis: {len(facts)} facts, deal_type={deal_type}")

    # STAGE 1: Identify considerations
    considerations, quant_context_raw, stage1_cost = stage1_identify_considerations(
        facts=facts,
        deal_type=deal_type,
        additional_context=meeting_notes,
        model=model,
    )

    # STAGE 2: Match activities (rules - no LLM cost)
    activities, tsa_services, quant_tracked = stage2_match_activities(
        considerations=considerations,
        quant_context=quant_context_raw,
        deal_type=deal_type,
        include_runrate=include_runrate,
    )

    # STAGE 3: Validate (pass raw dict for compatibility)
    quant_for_validation = {
        'user_count': quant_tracked.user_count,
        'application_count': quant_tracked.application_count,
        'site_count': quant_tracked.site_count,
        'server_count': quant_tracked.server_count,
    }

    validation, stage3_cost = stage3_validate(
        facts=facts,
        considerations=considerations,
        activities=activities,
        tsa_services=tsa_services,
        deal_type=deal_type,
        quant_context=quant_for_validation,
        model=model,
    )

    # Calculate totals by activity type
    impl_activities = [a for a in activities if a.activity_type == 'implementation']
    runrate_activities = [a for a in activities if a.activity_type == 'operational_runrate']
    license_activities = [a for a in activities if a.activity_type == 'license']
    operational_activities = [a for a in activities if a.activity_type == 'operational']

    impl_low = sum(a.cost_range[0] for a in impl_activities)
    impl_high = sum(a.cost_range[1] for a in impl_activities)

    runrate_low = sum(a.cost_range[0] for a in runrate_activities)
    runrate_high = sum(a.cost_range[1] for a in runrate_activities)

    license_low = sum(a.cost_range[0] for a in license_activities)
    license_high = sum(a.cost_range[1] for a in license_activities)

    operational_low = sum(a.cost_range[0] for a in operational_activities)
    operational_high = sum(a.cost_range[1] for a in operational_activities)

    # Total implementation cost (one-time)
    total_impl_low = impl_low + license_low + operational_low
    total_impl_high = impl_high + license_high + operational_high

    # Total cost including run-rate
    total_low = total_impl_low + runrate_low
    total_high = total_impl_high + runrate_high

    # Timeline (implementation activities only)
    timeline_low = min((a.timeline_months[0] for a in impl_activities), default=0)
    timeline_high = max((a.timeline_months[1] for a in impl_activities), default=0)

    # Build assumptions to verify
    assumptions = []
    if quant_tracked.user_count_source == "assumed":
        assumptions.append(f"User count ASSUMED at {quant_tracked.user_count:,} - verify with target")
    if quant_tracked.application_count_source == "assumed":
        assumptions.append(f"Application count ASSUMED at {quant_tracked.application_count} - verify with target")
    if quant_tracked.site_count_source == "assumed":
        assumptions.append(f"Site count ASSUMED at {quant_tracked.site_count} - verify with target")
    if quant_tracked.server_count_source == "assumed":
        assumptions.append(f"Server count ASSUMED at {quant_tracked.server_count} - verify with target")

    output = ThreeStageOutput(
        deal_type=deal_type,
        facts_analyzed=len(facts),
        timestamp=datetime.now().isoformat(),
        considerations=considerations,
        activities=activities,
        validation=validation,
        total_cost_range=(total_impl_low, total_impl_high),  # Implementation only
        total_timeline_months=(timeline_low, timeline_high),
        tsa_services=tsa_services,
        quant_context=quant_tracked,
        implementation_cost_range=(impl_low, impl_high),
        operational_runrate_range=(runrate_low, runrate_high),
        license_cost_range=(license_low, license_high),
        stage1_cost=stage1_cost,
        stage2_cost=0.0,
        stage3_cost=stage3_cost,
        total_llm_cost=stage1_cost + stage3_cost,
        assumptions_to_verify=assumptions,
    )

    logger.info(f"Three-stage analysis complete: ${total_impl_low:,.0f}-${total_impl_high:,.0f} impl, "
                f"${runrate_low:,.0f}-${runrate_high:,.0f}/yr run-rate, LLM cost=${output.total_llm_cost:.4f}")

    return output


def format_three_stage_output(output: ThreeStageOutput) -> str:
    """Format output for display."""
    lines = []

    lines.append("=" * 70)
    lines.append("THREE-STAGE REASONING ANALYSIS")
    lines.append("=" * 70)

    lines.append(f"\nDeal Type: {output.deal_type}")
    lines.append(f"Facts Analyzed: {output.facts_analyzed}")
    lines.append(f"LLM Cost: ${output.total_llm_cost:.4f}")

    # Show assumptions to verify prominently
    if output.assumptions_to_verify:
        lines.append(f"\n{'!'*70}")
        lines.append("ASSUMPTIONS TO VERIFY")
        lines.append("!" * 70)
        for assumption in output.assumptions_to_verify:
            lines.append(f"  ⚠ {assumption}")

    # Quantitative context
    if output.quant_context:
        lines.append(f"\n{'-'*70}")
        lines.append("QUANTITATIVE INPUTS")
        lines.append("-" * 70)
        qc = output.quant_context
        lines.append(f"  Users: {qc.user_count:,} ({qc.user_count_source})")
        lines.append(f"  Applications: {qc.application_count} ({qc.application_count_source})")
        lines.append(f"  Sites: {qc.site_count} ({qc.site_count_source})")
        lines.append(f"  Servers: {qc.server_count} ({qc.server_count_source})")

    lines.append(f"\n{'='*70}")
    lines.append("STAGE 1: CONSIDERATIONS IDENTIFIED")
    lines.append("=" * 70)

    for c in output.considerations:
        lines.append(f"\n[{c.consideration_id}] {c.workstream.upper()}")
        lines.append(f"  Finding: {c.finding}")
        lines.append(f"  Implication: {c.implication}")
        lines.append(f"  Deal Impact: {c.deal_impact}")

    lines.append(f"\n{'='*70}")
    lines.append("STAGE 2: ACTIVITIES MATCHED")
    lines.append("=" * 70)

    # Group by activity type
    impl_activities = [a for a in output.activities if a.activity_type == 'implementation']
    license_activities = [a for a in output.activities if a.activity_type == 'license']
    operational_activities = [a for a in output.activities if a.activity_type == 'operational']
    runrate_activities = [a for a in output.activities if a.activity_type == 'operational_runrate']

    if impl_activities:
        lines.append("\n--- Implementation Activities (One-Time) ---")
        for a in impl_activities:
            lines.append(f"\n[{a.activity_id}] {a.name}")
            lines.append(f"  Cost: ${a.cost_range[0]:,.0f} - ${a.cost_range[1]:,.0f}")
            lines.append(f"  Formula: {a.cost_formula}")
            lines.append(f"  Timeline: {a.timeline_months[0]}-{a.timeline_months[1]} months")
            if a.requires_tsa:
                tsa_source = f" [{a.tsa_source}]" if hasattr(a, 'tsa_source') else ""
                lines.append(f"  TSA: Yes ({a.tsa_duration_months[0]}-{a.tsa_duration_months[1]} months){tsa_source}")

    if license_activities:
        lines.append("\n--- License Activities ---")
        for a in license_activities:
            lines.append(f"\n[{a.activity_id}] {a.name}")
            lines.append(f"  Cost: ${a.cost_range[0]:,.0f} - ${a.cost_range[1]:,.0f}")
            lines.append(f"  Formula: {a.cost_formula}")

    if operational_activities:
        lines.append("\n--- Operational Setup (One-Time) ---")
        for a in operational_activities:
            lines.append(f"\n[{a.activity_id}] {a.name}")
            lines.append(f"  Cost: ${a.cost_range[0]:,.0f} - ${a.cost_range[1]:,.0f}")
            lines.append(f"  Formula: {a.cost_formula}")

    if runrate_activities:
        lines.append("\n--- Operational Run-Rate (Annual) ---")
        for a in runrate_activities:
            lines.append(f"\n[{a.activity_id}] {a.name}")
            lines.append(f"  Annual Cost: ${a.cost_range[0]:,.0f} - ${a.cost_range[1]:,.0f}/year")
            lines.append(f"  Formula: {a.cost_formula}")

    lines.append(f"\n{'='*70}")
    lines.append("STAGE 3: VALIDATION")
    lines.append("=" * 70)

    v = output.validation
    lines.append(f"\nConfidence: {v.confidence_score:.0%}")
    lines.append(f"Valid: {'Yes' if v.is_valid else 'No'}")
    lines.append(f"\nAssessment: {v.assessment}")

    if v.missing_considerations:
        lines.append("\nMissing Considerations:")
        for m in v.missing_considerations:
            lines.append(f"  - {m}")

    if v.suggested_additions:
        lines.append("\nSuggested Additions:")
        for s in v.suggested_additions:
            lines.append(f"  - {s.get('activity')}: {s.get('reason')}")

    if v.recommendations:
        lines.append("\nRecommendations:")
        for r in v.recommendations:
            lines.append(f"  - {r}")

    lines.append(f"\n{'='*70}")
    lines.append("COST SUMMARY")
    lines.append("=" * 70)

    lines.append(f"\nImplementation (One-Time):")
    lines.append(f"  Total: ${output.total_cost_range[0]:,.0f} - ${output.total_cost_range[1]:,.0f}")

    if output.implementation_cost_range:
        lines.append(f"    - Core Implementation: ${output.implementation_cost_range[0]:,.0f} - ${output.implementation_cost_range[1]:,.0f}")
    if output.license_cost_range and output.license_cost_range[1] > 0:
        lines.append(f"    - Licensing: ${output.license_cost_range[0]:,.0f} - ${output.license_cost_range[1]:,.0f}")

    if output.operational_runrate_range and output.operational_runrate_range[1] > 0:
        lines.append(f"\nOperational Run-Rate (Annual):")
        lines.append(f"  ${output.operational_runrate_range[0]:,.0f} - ${output.operational_runrate_range[1]:,.0f}/year")

    lines.append(f"\nTimeline: {output.total_timeline_months[0]}-{output.total_timeline_months[1]} months")
    lines.append(f"TSA Services: {len(output.tsa_services)}")

    # Show TSA breakdown by source
    rule_tsa = [t for t in output.tsa_services if t.get('source') == 'rule']
    negotiated_tsa = [t for t in output.tsa_services if t.get('source') == 'negotiated']

    if rule_tsa:
        lines.append(f"  - Rule-derived: {len(rule_tsa)}")
    if negotiated_tsa:
        lines.append(f"  - Negotiated: {len(negotiated_tsa)}")

    return "\n".join(lines)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'run_three_stage_analysis',
    'format_three_stage_output',
    'ThreeStageOutput',
    'IdentifiedConsideration',
    'MatchedActivity',
    'ValidationResult',
    'QuantitativeContext',
    'stage1_identify_considerations',
    'stage2_match_activities',
    'stage3_validate',
    'run_structured_validation',
    'aggregate_structured_validation',
    'normalize_category',
    'CATEGORY_SYNONYMS',
    'ACTIVITY_TEMPLATES',
    'OPERATIONAL_RUNRATE_TEMPLATES',
]
