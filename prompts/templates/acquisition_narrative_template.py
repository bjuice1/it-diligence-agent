"""
Acquisition Narrative Template

For bolt-on acquisitions and platform deals where the focus is on:
- Synergy realization
- Integration into buyer's IT environment
- Day-1 operational continuity
- Value creation opportunities

Primary M&A Lenses: synergy_opportunity, day_1_continuity
Key Question: "How do we integrate?"
"""

from typing import List


# =============================================================================
# ACQUISITION EMPHASIS CONFIGURATION
# =============================================================================

ACQUISITION_EMPHASIS = {
    "primary_lenses": ["synergy_opportunity", "day_1_continuity"],
    "secondary_lenses": ["cost_driver"],
    "de_emphasized": ["tsa_exposure", "separation_complexity"],

    "executive_summary_focus": [
        "Integration complexity assessment",
        "Synergy opportunity quantification",
        "Day-1 operational readiness",
        "Key integration risks",
        "Quick wins vs. long-term initiatives"
    ],

    "team_story_emphasis": {
        "strengths": "Alignment with buyer capabilities, integration readiness",
        "constraints": "Integration blockers, skill gaps vs. buyer standards",
        "mna_implication": "Consolidation opportunity, capability gain, redundancy"
    },

    "risk_emphasis": [
        "Integration complexity risks",
        "Day-1 continuity risks",
        "Cultural/organizational risks",
        "Technical debt that complicates integration",
        "Skill gaps that affect integration timeline"
    ],

    "opportunity_emphasis": [
        "Application consolidation (eliminate duplicate systems)",
        "Infrastructure consolidation (DC, cloud rationalization)",
        "Vendor consolidation (leverage buyer contracts)",
        "Headcount synergies (eliminate redundant roles)",
        "Capability gains (acquire what buyer lacks)"
    ]
}


# =============================================================================
# ACQUISITION NARRATIVE TEMPLATE
# =============================================================================

ACQUISITION_TEMPLATE = """You are generating an IT due diligence narrative for an ACQUISITION deal.

## DEAL CONTEXT

**Deal Type**: Acquisition (bolt-on/platform)
**Key Question**: How do we integrate?
**Primary Focus**: Synergy realization and integration planning

## ACQUISITION-SPECIFIC FRAMING

For this acquisition narrative, emphasize:

1. **Synergy Opportunities** (HIGH PRIORITY)
   - Application consolidation (which systems can be retired?)
   - Infrastructure consolidation (DC/cloud rationalization)
   - Vendor consolidation (leverage buyer's contracts)
   - Headcount synergies (redundant roles)
   - Capability gains (what does target bring that buyer lacks?)

2. **Integration Complexity** (HIGH PRIORITY)
   - How difficult will integration be?
   - What are the technical integration challenges?
   - Where are the organizational/cultural friction points?
   - What's the realistic integration timeline?

3. **Day-1 Continuity** (HIGH PRIORITY)
   - What must work on Day 1 for business continuity?
   - What connectivity to buyer systems is needed immediately?
   - What are the Day-1 risks?

4. **TSA Considerations** (LOW PRIORITY for acquisitions)
   - Only if target is being carved out from a parent
   - Usually minimal for straightforward acquisitions

## EXECUTIVE SUMMARY BULLETS (5-7)

For an acquisition, include:
- Overall IT organization shape and integration readiness
- Cost/headcount concentration and synergy potential
- 2-3 key integration risks
- 2-3 key synergy opportunities with directional value
- Integration complexity assessment (simple/moderate/complex)

## SYNERGIES TABLE FORMAT

For acquisitions, use this enhanced synergies table:

| Opportunity | Category | Why it matters | Value mechanism | Estimated value | First 100 days action |
|-------------|----------|----------------|-----------------|-----------------|----------------------|

Categories:
- **Cost Elimination**: Remove duplicate spend (retire systems, reduce headcount)
- **Cost Avoidance**: Prevent future spend (leverage buyer contracts)
- **Capability Gain**: Acquire what buyer lacks (skills, tools, processes)
- **Efficiency Gain**: Do more with same resources

Value mechanisms should be specific:
- "Retire {system}, eliminate ${X}K annual license"
- "Consolidate to buyer's {tool}, avoid ${X}K future spend"
- "Reduce {N} FTEs through role consolidation"

## INTEGRATION TIMELINE SECTION

Add after M&A Lens section:

### Integration Timeline Considerations

**Day 1-30**: [Critical connectivity and access requirements]
**Day 31-100**: [Quick wins and foundation work]
**Day 100+**: [Major integration initiatives]

Include:
- Realistic timeline assessment
- Key dependencies
- Integration sequencing recommendations

## RISKS TABLE FORMAT

For acquisitions, focus risk columns on integration impact:

| Risk | Why it matters | Integration impact | Mitigation |
|------|----------------|-------------------|------------|

Integration impact should specify:
- Timeline impact (delays integration by X months)
- Cost impact (increases integration cost by $X)
- Complexity impact (requires additional workstreams)

## QUALITY CHECKLIST FOR ACQUISITIONS

Before finalizing, verify:
- [ ] Synergies table has at least 5 opportunities with value estimates
- [ ] Integration timeline section is included
- [ ] Day-1 requirements are explicitly listed
- [ ] Risks focus on integration impact, not just operational risk
- [ ] At least 3 "quick win" synergies identified (achievable in first 100 days)
- [ ] Capability gains are identified (not just cost savings)
"""


# =============================================================================
# ACQUISITION-SPECIFIC SECTION TEMPLATES
# =============================================================================

INTEGRATION_TIMELINE_TEMPLATE = """
### Integration Timeline Considerations

**Phase 1: Day 1-30 (Foundation)**
{day_1_30_items}

**Phase 2: Day 31-100 (Quick Wins)**
{day_31_100_items}

**Phase 3: Day 100+ (Major Initiatives)**
{day_100_plus_items}

**Key Dependencies**:
{dependencies}

**Recommended Sequencing**:
{sequencing}
"""

SYNERGY_DEEP_DIVE_TEMPLATE = """
### Synergy Analysis

**Total Addressable Synergies**: ${total_low:,} - ${total_high:,} annually

#### By Category

| Category | Opportunity Count | Value Range | Realization Timeline |
|----------|------------------|-------------|---------------------|
| Cost Elimination | {cost_elim_count} | ${cost_elim_range} | {cost_elim_timeline} |
| Cost Avoidance | {cost_avoid_count} | ${cost_avoid_range} | {cost_avoid_timeline} |
| Capability Gain | {cap_gain_count} | {cap_gain_value} | {cap_gain_timeline} |
| Efficiency Gain | {eff_gain_count} | ${eff_gain_range} | {eff_gain_timeline} |

#### Quick Wins (First 100 Days)
{quick_wins}

#### Major Initiatives (100+ Days)
{major_initiatives}
"""


# =============================================================================
# PROMPT ADDITIONS FOR ACQUISITION
# =============================================================================

def get_acquisition_prompt_additions() -> str:
    """Get acquisition-specific prompt additions to inject into synthesis."""
    return """
## ACQUISITION-SPECIFIC REQUIREMENTS

### Synergy Identification Guidelines

When identifying synergies, categorize each as:

1. **Cost Elimination** (highest confidence)
   - Duplicate applications that can be retired
   - Redundant infrastructure (DCs, cloud accounts)
   - Overlapping vendor contracts
   - Redundant roles/positions

2. **Cost Avoidance** (medium confidence)
   - Leverage buyer's volume discounts
   - Avoid planned target investments
   - Consolidate to buyer's enterprise agreements

3. **Capability Gain** (strategic value)
   - Skills/expertise buyer lacks
   - Tools/platforms buyer wants
   - Processes/methodologies to adopt
   - Customer/market knowledge

4. **Efficiency Gain** (operational value)
   - Shared services opportunities
   - Process standardization
   - Automation opportunities

### Integration Complexity Assessment

Rate overall integration complexity as:

- **Simple**: <3 major systems, aligned technology stack, minimal customization
- **Moderate**: 3-7 major systems, some technology gaps, moderate customization
- **Complex**: >7 major systems, significant technology gaps, heavy customization

Factors that increase complexity:
- Multiple ERP instances
- Heavy customization of core systems
- Legacy technology requiring modernization
- Multiple data centers requiring consolidation
- Significant organizational change required

### Day-1 Requirements

Explicitly list what MUST work on Day 1:
- Authentication/access (can employees log in?)
- Core business applications (can business operate?)
- Communication systems (email, collaboration)
- Financial systems (can we pay people/vendors?)
- Customer-facing systems (can customers transact?)

For each, specify: current state, Day-1 approach, risk level.
"""


def get_acquisition_risk_prompts() -> List[str]:
    """Get acquisition-specific risk identification prompts."""
    return [
        "What technical debt could delay or complicate integration?",
        "What organizational/cultural factors could impede integration?",
        "What skill gaps exist relative to buyer's standards?",
        "What vendor contracts could complicate consolidation?",
        "What data quality issues could affect integration?",
        "What compliance gaps need remediation before integration?",
        "What key person dependencies could affect integration?"
    ]


def get_acquisition_synergy_prompts() -> List[str]:
    """Get acquisition-specific synergy identification prompts."""
    return [
        "What applications duplicate buyer capabilities and can be retired?",
        "What infrastructure can be consolidated with buyer's environment?",
        "What vendor contracts overlap with buyer's enterprise agreements?",
        "What roles/positions are redundant with buyer's organization?",
        "What capabilities does target have that buyer lacks?",
        "What process improvements could be adopted from either side?",
        "What quick wins can be achieved in the first 100 days?"
    ]


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'ACQUISITION_TEMPLATE',
    'ACQUISITION_EMPHASIS',
    'INTEGRATION_TIMELINE_TEMPLATE',
    'SYNERGY_DEEP_DIVE_TEMPLATE',
    'get_acquisition_prompt_additions',
    'get_acquisition_risk_prompts',
    'get_acquisition_synergy_prompts'
]
