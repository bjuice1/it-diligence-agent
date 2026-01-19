"""
M&A Framing Foundation

Canonical definitions for the 5 M&A lenses that ALL outputs must connect to.
This is the foundational vocabulary for IT due diligence analysis.

Every finding, risk, work item, and recommendation must explicitly tie to at least one lens.
"""

# =============================================================================
# THE 5 M&A LENSES
# =============================================================================

MNA_LENSES = {
    "day_1_continuity": {
        "id": "DAY1",
        "name": "Day-1 Continuity",
        "definition": "What must work on Day 1 for the business to operate? These are non-negotiable requirements that, if not met, would prevent employees from working or customers from being served.",
        "core_question": "Will this prevent business operations on Day 1?",
        "secondary_questions": [
            "Can employees authenticate and access critical systems?",
            "Can the business process transactions?",
            "Can customers be served?",
            "Can payroll run?",
            "Is there network connectivity?"
        ],
        "typical_examples": [
            "Authentication/Identity (AD, SSO, MFA)",
            "Payroll/HCM systems",
            "Core ERP transactions",
            "Network connectivity (WAN, VPN)",
            "Email/communication",
            "Customer-facing applications",
            "Payment processing"
        ],
        "when_to_apply": "Every finding - always assess Day 1 impact",
        "deal_types": ["acquisition", "carveout", "divestiture"],
        "severity_if_blocked": "CRITICAL - Deal cannot close without resolution"
    },

    "tsa_exposure": {
        "id": "TSA",
        "name": "TSA Risk/Exposure",
        "definition": "What services will require a Transition Services Agreement? TSAs are temporary arrangements where the seller continues to provide IT services to the buyer post-close, typically for 6-24 months.",
        "core_question": "Does this require transition services from the seller?",
        "secondary_questions": [
            "Is this service provided by shared/corporate IT?",
            "Does the target have standalone capability?",
            "How long would it take to stand up independently?",
            "What is the monthly cost exposure during TSA?",
            "What is the exit complexity?"
        ],
        "typical_examples": [
            "Shared data center hosting",
            "Corporate email/M365",
            "Parent company ERP instance",
            "Shared service desk",
            "Corporate network/WAN",
            "Centralized security operations (SOC)",
            "Shared identity services"
        ],
        "when_to_apply": "Carveouts primarily; some acquisitions with shared services",
        "deal_types": ["carveout", "divestiture"],
        "tsa_duration_guidance": {
            "infrastructure": "12-18 months typical",
            "applications": "12-24 months typical",
            "end_user_services": "6-12 months typical",
            "security": "12-18 months typical",
            "data_analytics": "6-12 months typical"
        },
        "severity_if_missed": "HIGH - Unexpected TSA costs, service gaps post-close"
    },

    "separation_complexity": {
        "id": "SEP",
        "name": "Separation Complexity",
        "definition": "How entangled is this system/service with the parent or other entities? Separation complexity drives cost, timeline, and risk for carveouts and divestitures.",
        "core_question": "How entangled is this and how hard is it to separate?",
        "secondary_questions": [
            "Is data commingled with other business units?",
            "Are there shared databases or applications?",
            "Do integrations cross entity boundaries?",
            "Is licensing tied to the parent entity?",
            "Are there contractual change-of-control issues?"
        ],
        "typical_examples": [
            "Shared ERP instance with intercompany transactions",
            "Commingled customer data in single CRM",
            "Parent-licensed software (Oracle, SAP, Microsoft EA)",
            "Shared identity directory (AD forest)",
            "Integrated networks with parent sites",
            "Shared security tools and policies"
        ],
        "when_to_apply": "Carveouts and divestitures - where separation is required",
        "deal_types": ["carveout", "divestiture"],
        "entanglement_levels": {
            "none": "Fully standalone - no separation needed",
            "low": "Minor dependencies - simple to separate",
            "medium": "Shared services - TSA and migration required",
            "high": "Deeply integrated - significant separation project",
            "critical": "Core systems shared - may affect deal structure"
        },
        "severity_if_underestimated": "HIGH - Timeline delays, cost overruns, operational disruption"
    },

    "synergy_opportunity": {
        "id": "SYN",
        "name": "Synergy Opportunity",
        "definition": "Where can value be created through combination or consolidation? Synergies are a key component of deal thesis for acquisitions.",
        "core_question": "Where can we create value by combining or consolidating?",
        "secondary_questions": [
            "Can we consolidate to a single platform/tool?",
            "Can we eliminate duplicate spend?",
            "Can we achieve economies of scale?",
            "Can we leverage target capabilities buyer lacks?",
            "Can we enable new revenue through integration?"
        ],
        "typical_examples": [
            "Application consolidation (two ERPs → one)",
            "License rationalization (eliminate duplicate tools)",
            "Infrastructure consolidation (data center, cloud)",
            "Team consolidation (combined IT org)",
            "Vendor consolidation (volume discounts)",
            "Capability acquisition (target has skills buyer needs)"
        ],
        "when_to_apply": "Acquisitions primarily - where combination creates value",
        "deal_types": ["acquisition"],
        "synergy_types": {
            "cost_elimination": "Remove duplicate spend entirely",
            "cost_avoidance": "Prevent future spend (e.g., avoid planned upgrade)",
            "efficiency_gain": "Do more with same resources",
            "capability_gain": "Acquire capability buyer lacks",
            "revenue_enablement": "Enable new revenue streams"
        },
        "caution": "Synergies often overestimated - require realistic timeline and investment to achieve"
    },

    "cost_driver": {
        "id": "COST",
        "name": "Cost Driver",
        "definition": "What drives IT cost and how might it change? Understanding cost drivers enables accurate budgeting and identifies optimization opportunities.",
        "core_question": "What drives the cost and how will the deal change it?",
        "secondary_questions": [
            "What are the major IT cost categories?",
            "Are costs fixed or variable?",
            "What contracts are coming up for renewal?",
            "Are there technical debt items that will require investment?",
            "What integration/separation costs should be budgeted?"
        ],
        "typical_examples": [
            "Headcount costs (internal IT team)",
            "Outsourcing/MSP costs",
            "Software licensing (perpetual, subscription)",
            "Infrastructure hosting (DC, cloud)",
            "Network/telecom costs",
            "Security tool stack",
            "Maintenance and support contracts"
        ],
        "when_to_apply": "All deal types - cost is always relevant",
        "deal_types": ["acquisition", "carveout", "divestiture"],
        "cost_categories": {
            "run_the_business": "Ongoing operational costs",
            "grow_the_business": "Investment in new capabilities",
            "transform_the_business": "Major change initiatives",
            "integration_separation": "One-time deal-related costs"
        },
        "severity_if_missed": "MEDIUM - Budget surprises, investment thesis affected"
    }
}


# =============================================================================
# INFERENCE DISCIPLINE
# =============================================================================

STATEMENT_TYPES = {
    "fact": {
        "definition": "Direct statement supported by explicit evidence in the inventory",
        "format": "Statement with citation: '[statement] (F-XXX-###)'",
        "example": "MFA coverage is 62% (F-CYBER-003)",
        "requirements": [
            "Must cite specific fact ID",
            "Must be directly stated in inventory",
            "No interpretation added"
        ]
    },
    "inference": {
        "definition": "Logical conclusion drawn from facts that requires interpretation",
        "format": "Prefix with 'Inference:' - '[Inference: statement based on facts]'",
        "example": "Inference: Given the 62% MFA coverage (F-CYBER-003) and no PAM documented (GAP-IAM-005), privileged access hygiene is likely weak across the environment.",
        "requirements": [
            "Must be prefixed with 'Inference:'",
            "Must cite the facts it's based on",
            "Must be reasonable/defensible",
            "Should not overreach beyond evidence"
        ]
    },
    "pattern": {
        "definition": "Recognition of a common M&A pattern based on evidence signals",
        "format": "Prefix with 'Pattern:' - '[Pattern: recognized pattern and what it typically indicates]'",
        "example": "Pattern: Multiple AD forests (F-IAM-001, F-IAM-002) typically indicate incomplete integration from prior M&A activity.",
        "requirements": [
            "Must be prefixed with 'Pattern:'",
            "Must cite triggering evidence",
            "Must explain what the pattern typically indicates",
            "Based on M&A experience/playbook knowledge"
        ]
    },
    "gap_flag": {
        "definition": "Explicit acknowledgment of missing information",
        "format": "'[Topic] not documented (GAP). [Why this matters].'",
        "example": "Disaster recovery capability not documented (GAP). Critical to validate given single data center deployment.",
        "requirements": [
            "Must explicitly state '(GAP)'",
            "Must explain why the gap matters",
            "Must NOT assume capability exists",
            "Should recommend investigation"
        ]
    }
}


# =============================================================================
# M&A LENS SELECTION GUIDANCE
# =============================================================================

LENS_SELECTION_MATRIX = """
## How to Select the Primary M&A Lens

Each finding should connect to at least one M&A lens. Use this matrix to select the primary lens:

| If the finding is about... | Primary Lens | Secondary Lens |
|---------------------------|--------------|----------------|
| Something that must work Day 1 | Day-1 Continuity | Cost Driver |
| A shared service from parent | TSA Exposure | Separation Complexity |
| Commingled data/systems | Separation Complexity | TSA Exposure |
| Duplicate tools/platforms | Synergy Opportunity | Cost Driver |
| Technical debt requiring investment | Cost Driver | Day-1 Continuity |
| Missing capability buyer needs | Synergy Opportunity | Cost Driver |
| Contract with change-of-control | Separation Complexity | Cost Driver |
| Staffing/key person issues | Cost Driver | TSA Exposure |

## Deal Type Emphasis

| Deal Type | Primary Lenses | Secondary Lenses |
|-----------|---------------|------------------|
| **Acquisition** | Synergy, Day-1, Cost | TSA (if shared services) |
| **Carveout** | TSA, Separation, Day-1 | Cost |
| **Divestiture** | Separation, Cost, Day-1 | N/A |
"""


# =============================================================================
# PROMPT INJECTION BLOCK
# =============================================================================

MNA_FRAMING_PROMPT_BLOCK = """
## M&A FRAMING REQUIREMENTS

Every finding you produce MUST explicitly connect to at least one M&A lens. This is non-negotiable - findings without M&A framing are not IC-ready.

### The 5 M&A Lenses

| Lens | Core Question | Apply When |
|------|---------------|------------|
| **Day-1 Continuity** | Will this prevent business operations on Day 1? | Always |
| **TSA Exposure** | Does this require transition services? | Carveouts, shared services |
| **Separation Complexity** | How entangled is this? | Carveouts, divestitures |
| **Synergy Opportunity** | Where's the value creation potential? | Acquisitions |
| **Cost Driver** | What drives cost and how will deal change it? | Always |

### Required Output Format

In your reasoning field, you MUST explicitly state:
```
M&A Lens: [LENS_NAME]
Why: [1-2 sentences explaining why this lens applies to this finding]
Deal Impact: [Specific impact on this deal - timeline, cost, risk, or value]
```

### Inference Discipline

- **FACT**: Direct statement with citation → "MFA coverage is 62% (F-CYBER-003)"
- **INFERENCE**: Logical conclusion → "Inference: Given [facts], [conclusion]"
- **PATTERN**: Recognized M&A pattern → "Pattern: [evidence] typically indicates [implication]"
- **GAP**: Missing information → "[Topic] not documented (GAP). [Why it matters]."

NEVER state inferences as facts. ALWAYS label when you go beyond explicit evidence.
"""


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_mna_framing_prompt() -> str:
    """Return the M&A framing prompt block for injection into agent prompts."""
    return MNA_FRAMING_PROMPT_BLOCK


def get_lens_definition(lens_id: str) -> dict:
    """Get the full definition for a specific M&A lens."""
    return MNA_LENSES.get(lens_id, {})


def get_all_lens_ids() -> list:
    """Return list of all valid M&A lens IDs."""
    return list(MNA_LENSES.keys())


def get_lens_for_deal_type(deal_type: str) -> list:
    """Return recommended lenses for a deal type, in priority order."""
    lens_priority = {
        "acquisition": ["synergy_opportunity", "day_1_continuity", "cost_driver", "tsa_exposure"],
        "carveout": ["tsa_exposure", "separation_complexity", "day_1_continuity", "cost_driver"],
        "divestiture": ["separation_complexity", "cost_driver", "day_1_continuity"]
    }
    return lens_priority.get(deal_type.lower(), list(MNA_LENSES.keys()))


def validate_mna_lens(lens: str) -> bool:
    """Validate that a lens ID is valid."""
    return lens in MNA_LENSES


def get_statement_type_guidance() -> dict:
    """Return the statement type guidance for inference discipline."""
    return STATEMENT_TYPES


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'MNA_LENSES',
    'STATEMENT_TYPES',
    'LENS_SELECTION_MATRIX',
    'MNA_FRAMING_PROMPT_BLOCK',
    'get_mna_framing_prompt',
    'get_lens_definition',
    'get_all_lens_ids',
    'get_lens_for_deal_type',
    'validate_mna_lens',
    'get_statement_type_guidance'
]
