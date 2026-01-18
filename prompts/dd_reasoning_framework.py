"""
IT Due Diligence Reasoning Framework

Defines the four-lens reasoning methodology that ALL domain agents must follow.
This ensures consistent, comprehensive analysis that separates:
- What exists (Current State)
- What could go wrong (Risks)
- What it means for the deal (Strategic Implications)
- What needs to be done (Integration Actions)

Import this into domain prompts to ensure consistent reasoning.

Version 2.0 - Enhanced with Anti-Hallucination Measures
- Mandatory source_evidence on all findings
- Confidence calibration guidance
- Gap-over-guess principle
- Evidence requirements
"""

# Import shared anti-hallucination components
from prompts.shared import (
    get_evidence_requirements,
    get_hallucination_guardrails,
    get_gap_over_guess,
    get_confidence_calibration,
    get_all_shared_guidance
)

# =============================================================================
# FOUR-LENS FRAMEWORK DEFINITION
# =============================================================================

DD_FOUR_LENS_FRAMEWORK = """
## MANDATORY FOUR-LENS REASONING FRAMEWORK

You MUST analyze through four distinct lenses, IN ORDER. Each lens must be completed
independently before moving to the next. DO NOT let integration assumptions influence
your current-state observations.

### LENS 1: CURRENT STATE ASSESSMENT
**Question to answer:** "What exists today?"

**Purpose:** Describe the IT environment as-is, creating a neutral baseline of what
the buyer would be acquiring. This description must be:
- Factual and defensible
- Understandable without knowing the buyer
- Independent of any integration assumptions

**What to capture:**
- Inventory of systems, tools, and platforms
- Architecture and design patterns
- Maturity level (not just existence)
- Standalone viability assessment

**Tool to use:** `create_current_state_entry` for each major finding

**Key rule:** Describe what exists BEFORE recommending change.

---

### LENS 2: RISK IDENTIFICATION
**Question to answer:** "What could go wrong, even if nothing changes?"

**Purpose:** Identify risks that exist INDEPENDENT of integration. These are risks
the target company faces today, regardless of the deal outcome.

**Types of standalone risks to identify:**
- Technical debt exposure (EOL systems, unsupported platforms)
- Security gaps relative to industry standards
- Compliance deficiencies
- Key person dependencies
- Vendor/licensing constraints
- Scalability and resilience concerns
- Business continuity gaps

**Tool to use:** `identify_risk` with `integration_dependent: false` where applicable

**Key rule:** Risks may exist even if no integration occurs. A risk is NOT just
"something that creates integration work."

---

### LENS 3: STRATEGIC IMPLICATIONS
**Question to answer:** "What does this mean for the deal?"

**Purpose:** Surface deal-relevant implications that inform negotiation, structure,
and planning—WITHOUT doing financial modeling.

**What to capture:**
- Alignment with buyer's IT standards (aligned/partial/misaligned)
- Barriers to synergy realization
- Standalone vs. integrated complexity differences
- TSA or carve-out implications
- Deal structure considerations

**Tool to use:** `create_strategic_consideration`

**Key rule:** This is deal LOGIC, not deal MATH. Focus on implications, not costs.

---

### LENS 4: INTEGRATION ACTIONS
**Question to answer:** "What needs to be done post-close?"

**Purpose:** Define specific, phased work items for integration execution.

**Phase definitions:**
- **Day 1:** Business continuity, legal/compliance must-haves, basic connectivity
- **Day 100:** Stabilization, quick wins, foundation for larger work
- **Post-100:** Optimization, transformation, full integration
- **Optional:** Nice-to-have improvements, not on critical path

**Tools to use:**
- `create_work_item` with phase tagging
- `create_recommendation` for strategic guidance

**Key rule:** Integration is DOWNSTREAM from understanding. The quality of Lens 4
depends on the thoroughness of Lenses 1-3.

---

## CRITICAL REASONING RULES

### Rule 1: Sequential Independence
Complete each lens before starting the next. Do not jump ahead to integration
recommendations while still documenting current state.

### Rule 2: Category Separation
- **Observations** describe reality (facts about what exists)
- **Risks** describe potential negative outcomes (what could go wrong)
- **Recommendations** describe optional actions (what could be done)

If you find yourself blurring these categories, stop and categorize correctly.

### Rule 3: Integration Isolation
Your current-state conclusions must NOT be influenced by integration logic.
Ask yourself: "Would this description change if there were no buyer?"
If yes, you're injecting integration bias.

### Rule 4: Non-Integration Risk Mandate
For EACH domain area you analyze, you MUST explicitly consider:
"What risks exist here even if we never integrate?"

If you find no standalone risks in an area, explicitly state why:
"No standalone risks identified for [area] because [reasoning]."

### Rule 5: Investment Committee Standard
Assume your findings will be reviewed by an Investment Committee.
They need:
- Clear facts, not speculation
- Risks with impact quantification
- Strategic implications that inform decisions
- Defensible conclusions

---

## OUTPUT SEQUENCING

Your analysis should flow in this order:

1. **Extract facts** from the documents
2. **Apply Lens 1** → Create current_state entries
3. **Apply Lens 2** → Identify risks (flag integration_dependent correctly)
4. **Apply Lens 3** → Create strategic_considerations
5. **Apply Lens 4** → Create work_items and recommendations
6. **Complete analysis** with domain summary

Do NOT batch all findings at the end. Record findings as you identify them
through each lens.
"""

# =============================================================================
# LENS-SPECIFIC GUIDANCE (for import into domain prompts)
# =============================================================================

CURRENT_STATE_GUIDANCE = """
### CURRENT STATE TOOL USAGE

Use `create_current_state_entry` for each significant observation:

```
{
  "domain": "your_domain",
  "category": "specific_area",  // e.g., "cloud_presence", "wan_connectivity", "iam_posture"
  "summary": "Plain-English description of what exists",
  "maturity": "low | medium | high",
  "key_characteristics": ["Notable attribute 1", "Notable attribute 2"],
  "standalone_viability": "viable | constrained | high_risk",
  "evidence": "What in the document supports this observation"
}
```

**Maturity Levels:**
- **Low:** Basic/minimal capability, significant gaps, reactive approach
- **Medium:** Functional capability, some gaps, defined processes
- **High:** Robust capability, few gaps, proactive/optimized approach

**Standalone Viability:**
- **Viable:** Could operate independently without major issues
- **Constrained:** Some dependencies or limitations that create challenges
- **High Risk:** Significant issues that threaten standalone operation
"""

RISK_IDENTIFICATION_GUIDANCE = """
### RISK TOOL USAGE (Enhanced)

Use `identify_risk` with the new fields:

```
{
  "risk": "Description of the risk",
  "trigger": "What would cause this risk to materialize",
  "domain": "your_domain",
  "severity": "critical | high | medium | low",
  "likelihood": "high | medium | low",
  "risk_type": "technical_debt | security | vendor | organization | scalability | compliance | integration",
  "integration_dependent": true | false,  // KEY FIELD
  "standalone_exposure": "What happens if this risk materializes without any deal",
  "deal_impact": ["value_leakage", "execution_risk", "timeline_risk", "cost_exposure"],
  "mitigation": "Recommended actions to address this risk"
}
```

**Risk Types:**
- **technical_debt:** EOL systems, unsupported platforms, outdated architecture
- **security:** Vulnerabilities, gaps in controls, compliance failures
- **vendor:** Contract risks, licensing issues, supplier dependencies
- **organization:** Key person risk, skill gaps, understaffing
- **scalability:** Capacity constraints, performance limitations
- **compliance:** Regulatory exposure, audit failures, certification gaps
- **integration:** Risks that only exist in context of integration

**Integration Dependent Flag:**
- `false` = Risk exists TODAY, regardless of deal (e.g., EOL Windows 2012)
- `true` = Risk only exists because of integration (e.g., cloud platform mismatch)
"""

STRATEGIC_CONSIDERATION_GUIDANCE = """
### STRATEGIC CONSIDERATION TOOL USAGE

Use `create_strategic_consideration` for deal-relevant insights:

```
{
  "theme": "Short theme name",  // e.g., "Cloud Platform Mismatch"
  "observation": "Neutral statement of fact",
  "implication": "What this means for the deal",
  "deal_relevance": ["integration_risk", "value_leakage", "tsa_dependency", "execution_risk", "synergy_barrier"],
  "buyer_alignment": "aligned | partial | misaligned | unknown",
  "confidence": "high | medium | low",
  "domain": "your_domain"
}
```

**Deal Relevance Categories:**
- **integration_risk:** Creates complexity or risk in integration execution
- **value_leakage:** Could erode deal value if not addressed
- **tsa_dependency:** Likely requires Transition Services Agreement
- **execution_risk:** Could cause delays or failures in integration
- **synergy_barrier:** Impedes realization of expected synergies

**Buyer Alignment:**
- **aligned:** Target approach matches buyer standards
- **partial:** Some alignment, some gaps
- **misaligned:** Fundamentally different approaches
- **unknown:** Insufficient information to assess
"""

WORK_ITEM_GUIDANCE = """
### WORK ITEM TOOL USAGE (Enhanced)

Use `create_work_item` with phase tagging:

```
{
  "title": "Short descriptive title",
  "description": "Detailed description of work required",
  "domain": "your_domain",
  "category": "migration | integration | remediation | assessment | decommission | security | compliance",
  "phase": "Day_1 | Day_100 | Post_100 | Optional",
  "phase_rationale": "Why this timing",
  "effort_estimate": "e.g., '2-4 weeks' or '200-400 hours'",
  "cost_estimate_range": "e.g., '$50K-$100K'",
  "depends_on": ["WI-XXX"],  // Optional dependencies
  "skills_required": ["cloud_engineer", "network_engineer"]
}
```

**Phase Definitions:**
- **Day_1:** Must be done for business continuity, legal/compliance, or basic operations
- **Day_100:** Stabilization work, quick wins, enabling foundation
- **Post_100:** Full integration, optimization, transformation
- **Optional:** Improvements that aren't critical path
"""

# =============================================================================
# COMBINED FRAMEWORK FOR IMPORT
# =============================================================================

def get_framework_prompt() -> str:
    """Return the complete four-lens framework for embedding in domain prompts"""
    return DD_FOUR_LENS_FRAMEWORK


def get_full_guidance() -> str:
    """Return framework plus all tool guidance"""
    return "\n\n".join([
        DD_FOUR_LENS_FRAMEWORK,
        CURRENT_STATE_GUIDANCE,
        RISK_IDENTIFICATION_GUIDANCE,
        STRATEGIC_CONSIDERATION_GUIDANCE,
        WORK_ITEM_GUIDANCE
    ])


def get_full_guidance_with_anti_hallucination() -> str:
    """
    Return the complete framework including anti-hallucination measures.
    This is the recommended function for domain agents in v2.0+.
    """
    return "\n\n".join([
        # Core framework
        DD_FOUR_LENS_FRAMEWORK,
        # Anti-hallucination guidance (from shared components)
        get_evidence_requirements(),
        get_hallucination_guardrails(),
        get_gap_over_guess(),
        get_confidence_calibration(),
        # Tool-specific guidance
        CURRENT_STATE_GUIDANCE,
        RISK_IDENTIFICATION_GUIDANCE,
        STRATEGIC_CONSIDERATION_GUIDANCE,
        WORK_ITEM_GUIDANCE
    ])
