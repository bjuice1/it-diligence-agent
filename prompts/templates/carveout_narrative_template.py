"""
Carveout Narrative Template

For carveout deals where the target is being separated from a parent company.
Focus is on:
- TSA (Transition Service Agreement) requirements
- Separation complexity and entanglement
- Standalone readiness
- Day-1 operational independence

Primary M&A Lenses: tsa_exposure, separation_complexity
Key Question: "How do we stand alone?"
"""

from typing import Dict, List, Any


# =============================================================================
# CARVEOUT EMPHASIS CONFIGURATION
# =============================================================================

CARVEOUT_EMPHASIS = {
    "primary_lenses": ["tsa_exposure", "separation_complexity"],
    "secondary_lenses": ["day_1_continuity", "cost_driver"],
    "de_emphasized": ["synergy_opportunity"],

    "executive_summary_focus": [
        "TSA dependency assessment",
        "Standalone readiness evaluation",
        "Separation complexity rating",
        "Day-1 operational gaps",
        "Critical path to independence"
    ],

    "team_story_emphasis": {
        "strengths": "Standalone capabilities, independent operations",
        "constraints": "Parent dependencies, shared service reliance, capability gaps",
        "mna_implication": "TSA requirement, separation complexity, standalone investment needed"
    },

    "risk_emphasis": [
        "TSA duration and exit risks",
        "Separation complexity risks",
        "Standalone capability gaps",
        "Data entanglement risks",
        "Contract assignment risks",
        "Key person retention (parent employees supporting target)"
    ],

    "opportunity_emphasis": [
        "Clean separation opportunities",
        "Modernization during separation",
        "Right-sizing for standalone operations",
        "Process improvement during standup"
    ]
}


# =============================================================================
# CARVEOUT NARRATIVE TEMPLATE
# =============================================================================

CARVEOUT_TEMPLATE = """You are generating an IT due diligence narrative for a CARVEOUT deal.

## DEAL CONTEXT

**Deal Type**: Carveout (separation from parent)
**Key Question**: How do we stand alone?
**Primary Focus**: TSA requirements and standalone readiness

## CARVEOUT-SPECIFIC FRAMING

For this carveout narrative, emphasize:

1. **TSA Exposure** (CRITICAL PRIORITY)
   - Which IT services are provided by parent?
   - What's the realistic TSA duration for each service?
   - What's the exit complexity for each TSA?
   - What's the monthly cost of each TSA service?

2. **Separation Complexity** (CRITICAL PRIORITY)
   - How entangled are systems with parent?
   - What data separation is required?
   - What contract assignments are needed?
   - What's the separation effort estimate?

3. **Standalone Readiness** (HIGH PRIORITY)
   - What capabilities exist independently?
   - What must be built/acquired for standalone?
   - What's the investment required for standalone?
   - What's the timeline to full independence?

4. **Day-1 Continuity** (HIGH PRIORITY)
   - What must work on Day 1 without parent?
   - What TSAs are required for Day-1 operations?
   - What are the Day-1 risks?

5. **Synergy Opportunities** (LOW PRIORITY for carveouts)
   - Only relevant if buyer has existing operations
   - Focus on standalone first, synergy second

## EXECUTIVE SUMMARY BULLETS (5-7)

For a carveout, include:
- Overall TSA dependency level (high/medium/low)
- Estimated TSA duration range
- Standalone readiness assessment
- 2-3 critical separation risks
- Investment required for standalone operations
- Separation complexity rating (simple/moderate/complex)

## REQUIRED CARVEOUT-SPECIFIC SECTIONS

### TSA Services Inventory

| Service | Provider | Current State | TSA Duration | Monthly Cost | Exit Complexity | Exit Approach |
|---------|----------|---------------|--------------|--------------|-----------------|---------------|

Exit Complexity ratings:
- **Low**: Standard service, easy to replicate or outsource
- **Medium**: Some customization, requires planning
- **High**: Deeply integrated, significant effort to exit
- **Critical**: Core dependency, extended TSA likely

### Entanglement Assessment

| System/Service | Entanglement Level | Parent Dependencies | Separation Approach | Effort Estimate |
|----------------|-------------------|---------------------|---------------------|-----------------|

Entanglement levels:
- **None**: Fully independent, no parent dependencies
- **Low**: Minor dependencies, easily separated
- **Medium**: Moderate dependencies, requires planning
- **High**: Significant dependencies, complex separation
- **Critical**: Deeply entangled, may require rebuild

### Standalone Readiness Scorecard

| Capability | Current State | Parent Dependent? | Standalone Ready? | Gap/Investment Needed |
|------------|---------------|-------------------|-------------------|----------------------|

Key capabilities to assess:
- ERP/Financial Systems
- HR/Payroll Systems
- Email/Collaboration
- Authentication/Identity
- Network Connectivity
- Data Center/Hosting
- Security Operations
- Service Desk
- Application Support

## RISKS TABLE FORMAT

For carveouts, focus risk columns on separation impact:

| Risk | Why it matters | Separation impact | TSA implication | Mitigation |
|------|----------------|------------------|-----------------|------------|

Separation impact should specify:
- Timeline impact (extends separation by X months)
- Cost impact (increases standalone investment by $X)
- TSA impact (requires extended TSA for X service)

## QUALITY CHECKLIST FOR CARVEOUTS

Before finalizing, verify:
- [ ] TSA Services Inventory has at least 5 services identified
- [ ] Each TSA has duration estimate and exit complexity
- [ ] Entanglement Assessment covers all major systems
- [ ] Standalone Readiness Scorecard covers 8+ capabilities
- [ ] Day-1 requirements explicitly address parent dependencies
- [ ] Risks include TSA exit risks
- [ ] Separation timeline is realistic
- [ ] Investment estimate for standalone is provided
"""


# =============================================================================
# CARVEOUT-SPECIFIC SECTION TEMPLATES
# =============================================================================

TSA_SERVICES_TEMPLATE = """
## TSA Services Inventory

The following IT services are currently provided by or shared with the parent company
and will require Transition Service Agreements (TSAs) post-close.

| Service | Provider | Current State | TSA Duration | Monthly Cost | Exit Complexity | Exit Approach |
|---------|----------|---------------|--------------|--------------|-----------------|---------------|
{tsa_rows}

### TSA Summary

- **Total TSA Services**: {total_services}
- **Estimated Monthly TSA Cost**: ${monthly_cost:,}
- **Average TSA Duration**: {avg_duration} months
- **Critical Exits** (High/Critical complexity): {critical_count}

### TSA Exit Priority

1. **Immediate** (Exit within 6 months): {immediate_exits}
2. **Near-term** (Exit within 12 months): {nearterm_exits}
3. **Extended** (12+ months): {extended_exits}
"""

ENTANGLEMENT_TEMPLATE = """
## Entanglement Assessment

This section assesses the level of entanglement between target IT systems/services
and parent company infrastructure.

| System/Service | Entanglement Level | Parent Dependencies | Separation Approach | Effort Estimate |
|----------------|-------------------|---------------------|---------------------|-----------------|
{entanglement_rows}

### Entanglement Summary

- **Total Systems Assessed**: {total_systems}
- **High/Critical Entanglement**: {high_entanglement_count} systems
- **Clean (None/Low)**: {clean_count} systems
- **Estimated Separation Effort**: {total_effort}

### Critical Entanglements

{critical_entanglements}

### Separation Sequencing Recommendations

{separation_sequence}
"""

STANDALONE_SCORECARD_TEMPLATE = """
## Standalone Readiness Scorecard

Assessment of target's readiness to operate independently from parent.

| Capability | Current State | Parent Dependent? | Standalone Ready? | Gap/Investment Needed |
|------------|---------------|-------------------|-------------------|----------------------|
{scorecard_rows}

### Readiness Summary

- **Standalone Ready**: {ready_count} capabilities
- **Requires Investment**: {investment_count} capabilities
- **Critical Gaps**: {critical_gaps}

### Overall Standalone Readiness: {overall_rating}

{readiness_narrative}

### Investment Requirements for Standalone

| Category | Investment Range | Timeline | Priority |
|----------|-----------------|----------|----------|
{investment_rows}

**Total Estimated Standalone Investment**: ${total_investment_low:,} - ${total_investment_high:,}
"""


# =============================================================================
# PROMPT ADDITIONS FOR CARVEOUT
# =============================================================================

def get_carveout_prompt_additions() -> str:
    """Get carveout-specific prompt additions to inject into synthesis."""
    return """
## CARVEOUT-SPECIFIC REQUIREMENTS

### TSA Identification Guidelines

For each IT service, determine:

1. **Is this provided by parent?**
   - Shared infrastructure (DC, network, cloud)
   - Shared applications (ERP, email, collaboration)
   - Shared services (service desk, security operations)
   - Parent-employed staff supporting target

2. **TSA Duration Estimation**
   - **3-6 months**: Simple services, easy to replicate
   - **6-12 months**: Moderate complexity, requires planning
   - **12-18 months**: Complex services, significant build
   - **18+ months**: Critical/deeply integrated services

3. **Exit Complexity Assessment**
   - **Low**: Commodity service, multiple alternatives
   - **Medium**: Some customization, planning required
   - **High**: Significant dependencies, complex migration
   - **Critical**: Core to operations, extended TSA likely

4. **Monthly Cost Estimation**
   - Include: licensing, hosting, support labor, overhead
   - Use market rates if parent costs unknown
   - Flag if cost seems below market (hidden subsidy)

### Entanglement Assessment Guidelines

For each major system, assess:

1. **Data Entanglement**
   - Shared databases?
   - Commingled data?
   - Data separation effort?

2. **Integration Entanglement**
   - APIs to parent systems?
   - Shared middleware?
   - Integration rewrite needed?

3. **Infrastructure Entanglement**
   - Shared servers/VMs?
   - Shared network segments?
   - Shared security perimeter?

4. **Organizational Entanglement**
   - Parent staff supporting target?
   - Shared support processes?
   - Knowledge transfer needed?

### Standalone Readiness Assessment

For each capability, determine:

1. **Current State**
   - Fully in place at target
   - Partially in place
   - Provided by parent
   - Does not exist

2. **Standalone Readiness**
   - Ready (no changes needed)
   - Minor gaps (easy to address)
   - Significant gaps (investment needed)
   - Critical gaps (major build required)

3. **Investment Needed**
   - Be specific: "Implement standalone email ($50K-$100K)"
   - Include: software, implementation, training
   - Distinguish one-time vs. recurring costs

### Day-1 Carveout Requirements

For Day 1 of a carveout, explicitly address:

1. **Can employees work?**
   - Authentication (AD, SSO) - parent dependent?
   - Email access - parent dependent?
   - Core application access - parent dependent?

2. **Can business operate?**
   - ERP/financial systems - parent dependent?
   - Customer-facing systems - parent dependent?
   - Supply chain systems - parent dependent?

3. **Is data protected?**
   - Security monitoring - parent dependent?
   - Backup/recovery - parent dependent?
   - Incident response - parent dependent?

For each, specify: current dependency, Day-1 approach (TSA vs. standalone), risk level.
"""


def get_carveout_risk_prompts() -> List[str]:
    """Get carveout-specific risk identification prompts."""
    return [
        "What TSA services have highest exit complexity?",
        "What systems have deepest parent entanglement?",
        "What standalone capabilities are missing entirely?",
        "What data separation challenges exist?",
        "What contracts require assignment or renegotiation?",
        "What key staff are parent employees supporting target?",
        "What compliance gaps emerge in standalone state?",
        "What hidden parent subsidies will become real costs?"
    ]


def get_carveout_tsa_categories() -> List[Dict[str, str]]:
    """Get standard TSA service categories for carveouts."""
    return [
        {"category": "Infrastructure", "services": ["Data Center Hosting", "Cloud Services", "Backup/DR", "Network/WAN"]},
        {"category": "Applications", "services": ["ERP", "Email/Collaboration", "HR/Payroll", "CRM", "Custom Apps"]},
        {"category": "Security", "services": ["SOC/Monitoring", "Identity/Access", "Endpoint Protection", "Compliance"]},
        {"category": "Support", "services": ["Service Desk", "Desktop Support", "Application Support", "DBA Services"]},
        {"category": "Other", "services": ["Telecom", "Printing", "Facilities IT", "Procurement"]}
    ]


def get_standalone_capabilities() -> List[str]:
    """Get standard capabilities to assess for standalone readiness."""
    return [
        "ERP/Financial Systems",
        "HR/Payroll Systems",
        "Email & Collaboration",
        "Authentication & Identity",
        "Network Connectivity (WAN/LAN)",
        "Data Center/Cloud Hosting",
        "Backup & Disaster Recovery",
        "Security Operations (SOC)",
        "Endpoint Protection",
        "Service Desk",
        "Application Development",
        "Data & Analytics",
        "Compliance & Audit",
        "IT Governance & PMO"
    ]


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'CARVEOUT_TEMPLATE',
    'CARVEOUT_EMPHASIS',
    'TSA_SERVICES_TEMPLATE',
    'ENTANGLEMENT_TEMPLATE',
    'STANDALONE_SCORECARD_TEMPLATE',
    'get_carveout_prompt_additions',
    'get_carveout_risk_prompts',
    'get_carveout_tsa_categories',
    'get_standalone_capabilities'
]
