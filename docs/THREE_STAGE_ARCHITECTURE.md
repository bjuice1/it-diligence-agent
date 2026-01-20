# Three-Stage Reasoning Architecture

## Overview

The IT Due Diligence reasoning system uses a three-stage architecture that combines LLM intelligence with rule-based consistency:

```
┌─────────────────────────────────────────────────────────────────────┐
│                        DOCUMENT EXTRACTION                          │
│                    (Outside this architecture)                      │
│                                                                     │
│  PDFs/Documents ──► LLM Extraction ──► FactStore                    │
│                                                                     │
│  Cost: ~$0.50-2.00 per document                                     │
│  Frequency: Once per document                                       │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    THREE-STAGE REASONING                            │
└─────────────────────────────────────────────────────────────────────┘

    STAGE 1                 STAGE 2                 STAGE 3
    ───────                 ───────                 ───────
    LLM INTERPRETS          RULES MATCH             LLM VALIDATES

    "What do these          "What activities        "Does this make
     facts MEAN?"            apply here?"            sense?"

    Cost: ~$0.15-0.20       Cost: $0                Cost: ~$0.10-0.15
    Time: ~5-10 sec         Time: <1 sec            Time: ~5-10 sec
```

---

## Stage 1: LLM Identifies Considerations

### Purpose
Interpret raw facts and identify their implications for the deal.

### Why LLM is Required
Facts from document extraction are expressed in natural language with varied terminology:
- "Authentication via shared services agreement"
- "Users log in through corporate SSO"
- "Identity managed by parent IT organization"

All mean the same thing (parent dependency on identity), but pattern matching would miss them.

### Input
```python
facts = [
    {"fact_id": "F-001", "content": "Authentication via shared services agreement"},
    {"fact_id": "F-002", "content": "Email through parent enterprise licensing"},
    ...
]
deal_type = "carveout"
meeting_notes = "Parent wants clean separation in 12 months"
```

### Output
```python
considerations = [
    {
        "consideration_id": "C-001",
        "source_fact_ids": ["F-001"],
        "workstream": "identity",
        "finding": "Identity services provided by parent",
        "implication": "Target cannot authenticate users independently",
        "deal_impact": "Day-1 critical - business stops without identity",
        "suggested_category": "parent_dependency"
    },
    ...
]
quantitative_context = {
    "user_count": 1800,
    "application_count": 45,
    "site_count": 6
}
```

### Cost
- Model: Claude Sonnet (~$0.003/1K input, $0.015/1K output)
- Typical: ~$0.15-0.20 per analysis

---

## Stage 2: Rules Match Activities

### Purpose
Map identified considerations to specific activities with market-anchored costs.

### Why Rules Work Here
Once we know "this is an identity separation need," the activities are predictable:
1. Design identity architecture
2. Provision identity platform
3. Migrate users
4. Reconfigure SSO

The costs are formula-based using market anchors:
- User migration: $15-40 per user
- SSO reconfiguration: $2,000-8,000 per app
- Platform provisioning: $75,000-200,000 base

### Input
```python
considerations = [...]  # From Stage 1
quantitative_context = {"user_count": 1800, "application_count": 45, ...}
deal_type = "carveout"
```

### Output
```python
activities = [
    {
        "activity_id": "A-001",
        "name": "Migrate user accounts",
        "triggered_by": "C-001",
        "cost_range": (27000, 72000),  # 1800 users × $15-40
        "cost_formula": "1,800 users × $15-$40",
        "timeline_months": (2, 4),
        "requires_tsa": True,
        "tsa_duration_months": (3, 6)
    },
    ...
]
```

### Cost
- $0 (pure Python computation)
- Time: <1 second

### Activity Templates

Templates are organized by `category` → `workstream`:

```
parent_dependency/
├── identity/
│   ├── Design standalone identity architecture
│   ├── Provision identity platform
│   ├── Migrate user accounts
│   └── Reconfigure application SSO
├── email/
│   ├── Provision email platform
│   └── Migrate mailboxes
├── infrastructure/
│   ├── Design target infrastructure
│   ├── Provision infrastructure
│   └── Migrate workloads
├── network/
│   ├── Design network architecture
│   └── Implement WAN connectivity
└── security/
    ├── Design security architecture
    └── Implement security tooling

technology_mismatch/
├── identity/
│   └── Integrate identity platforms
├── email/
│   └── Migrate to buyer email platform
└── applications/
    └── Consolidate to buyer ERP
```

---

## Stage 3: LLM Validates

### Purpose
Review the matched activities and costs to catch:
- Missing considerations (facts mentioned but not addressed)
- Incorrect costs (too high or too low)
- Gaps in logic

### Why LLM is Required
Rules can't catch novel situations or subtle errors:
- "The facts mention 6 locations but you only have 3 site migrations"
- "The timeline seems aggressive given the legacy systems mentioned"

### Input
- Original facts
- Identified considerations (Stage 1)
- Matched activities (Stage 2)
- Total cost estimate

### Output
```python
validation = {
    "is_valid": True,
    "confidence_score": 0.85,
    "missing_considerations": [
        "Facts mention legacy AS/400 but no remediation activity"
    ],
    "questionable_costs": [],
    "suggested_additions": [
        {
            "activity": "Legacy system assessment",
            "reason": "AS/400 mentioned in facts",
            "estimated_cost": [50000, 150000]
        }
    ],
    "recommendations": [
        "Verify TSA duration with seller - 6 months may be tight"
    ],
    "assessment": "Analysis covers major dependencies. Consider legacy system risk."
}
```

### Cost
- Model: Claude Sonnet
- Typical: ~$0.10-0.15 per validation

---

## Cost Summary

| Operation | LLM Cost | When to Use |
|-----------|----------|-------------|
| Full Analysis (1+2+3) | ~$0.30-0.40 | Initial analysis, final output |
| Fast Analysis (1+2) | ~$0.15-0.20 | During refinement iterations |
| Re-validation (3 only) | ~$0.10-0.15 | After major refinements |
| Quantitative only | $0 | Changing user count, site count |

### Example: Typical Deal Workflow

```
Initial analysis:           $0.35
5 refinement iterations:    $0.75  (fast mode)
Pre-client validation:      $0.15
Final enhanced output:      $0.40
────────────────────────────────────
Total:                      $1.65
```

---

## Refinement Flow

The system supports iterative refinement as team members provide input:

```
                    INITIAL ANALYSIS
                          │
                          ▼
        ┌─────────────────────────────────┐
        │      REFINEMENT LOOP            │
        │                                 │
        │  Team Input ──► Apply ──► Fast  │
        │       │         Analysis        │
        │       ▼              │          │
        │  Track Change ◄──────┘          │
        │                                 │
        └─────────────────────────────────┘
                          │
                          ▼
                 FINAL VALIDATION
                          │
                          ▼
                   CLIENT OUTPUT
```

### Refinement Types

| Type | Source | Effect |
|------|--------|--------|
| `tsa_requirement` | Seller | Adds TSA service |
| `activity_override` | Team | Changes cost/timeline |
| `quantitative` | Team | Updates user count, etc. |
| `timeline_constraint` | Buyer | Constrains schedule |
| `note` | Any | Adds context for re-analysis |

### Example Refinement

```python
# Seller says they need to provide email TSA
session.add_tsa_requirement(
    service="Email Services",
    workstream="email",
    duration_months=(3, 6),
    source="seller",
    reason="Complex data migration requires extended transition"
)

# Re-analyze (fast mode)
result = orchestrator.analyze_fast(session.fact_store, session.deal_type)
```

---

## Files

| File | Purpose |
|------|---------|
| `analysis_pipeline.py` | **Main entry point** - `analyze_deal()` |
| `three_stage_reasoning.py` | Core three-stage logic (Stage 1, 2, 3) |
| `three_stage_refinement.py` | Refinement session with three-stage integration |
| `reasoning_orchestrator.py` | Coordination and convenience functions |
| `refinement_engine.py` | Base refinement input types |
| `quality_modes.py` | Fast/validated/enhanced modes |

---

## Quick Start

### Simple Analysis

```python
from tools_v2 import analyze_deal, AnalysisMode

# Full validated analysis
result = analyze_deal(
    fact_store=my_facts,
    deal_type="carveout",
    mode=AnalysisMode.VALIDATED,
)

print(result.summary)
# {'total_cost': '$610,500 - $1,867,000', 'confidence': '85%', ...}

print(result.formatted_text)
# Full formatted output
```

### With Refinement Session

```python
from tools_v2 import create_analysis_session

# Create session
session = create_analysis_session(fact_store, "carveout")

# Initial analysis
result = session.run_initial_analysis()

# Team provides clarification
session.add_tsa_requirement(
    service="Email Services",
    workstream="email",
    duration_months=(3, 6),
    source="seller",
    reason="Complex data migration",
)

# Fast re-analysis
result = session.apply_refinements_fast()

# Pre-client validation
final = session.run_full_validation()
```

---

## Analysis Modes

| Mode | Stages | Cost | Use Case |
|------|--------|------|----------|
| `FAST` | 1 + 2 | ~$0.15-0.20 | Quick iterations during exploration |
| `VALIDATED` | 1 + 2 + 3 | ~$0.30-0.50 | Standard analysis with validation |
| `ENHANCED` | 1 + 2 + 3 + summary | ~$0.50-0.70 | Client-ready with executive summary |

```python
from tools_v2 import analyze_deal, AnalysisMode

# Fast mode - during exploration
quick = analyze_deal(facts, "carveout", mode=AnalysisMode.FAST)

# Validated mode - standard analysis
standard = analyze_deal(facts, "carveout", mode=AnalysisMode.VALIDATED)

# Enhanced mode - client delivery
final = analyze_deal(facts, "carveout", mode=AnalysisMode.ENHANCED)
```

---

## Integration Points

### From FactStore
```python
from tools_v2 import analyze_deal, AnalysisMode

# Simple one-shot analysis
result = analyze_deal(fact_store, "carveout")

# Access results
print(result.total_cost_range)  # (610500, 1867000)
print(result.summary)           # Quick summary dict
print(result.formatted_text)    # Full formatted output
```

### From DDSession
```python
from tools_v2 import analyze_deal
from tools_v2.session import DDSession

session = DDSession.load("my_session")
result = analyze_deal(
    session.fact_store,
    session.state.deal_context.deal_type,
    meeting_notes=session.meeting_notes,
)
```

### With Refinement Session
```python
from tools_v2 import create_analysis_session

# Create refinement session
session = create_analysis_session(fact_store, "carveout")

# Run initial analysis
initial = session.run_initial_analysis()

# Seller provides TSA details
session.add_tsa_requirement(
    service="Email Services",
    workstream="email",
    duration_months=(3, 6),
    source="seller",
)

# Buyer updates user count
session.add_quantitative_update(
    field="user_count",
    value=2500,
    source="buyer",
)

# Team overrides activity cost
session.add_activity_override(
    activity_id="A-003",
    cost_override=(50000, 100000),
    reason="Known vendor quote",
)

# Fast re-analysis (Stage 1+2 only)
updated = session.apply_refinements_fast()

# Final validation before client
final = session.run_full_validation()

# Check what changed
print(session.get_change_summary())
```

---

## Quality Assurance

### Traceability
Every cost traces back through the chain:
```
$27,000-72,000 (activity cost)
    ↑
1,800 users × $15-40 (formula)
    ↑
C-001: Identity dependency (consideration)
    ↑
F-001: "Authentication via shared services" (fact)
    ↑
Page 3, paragraph 2 of IT_Overview.pdf (source)
```

### Validation Checks
Stage 3 validation catches:
- Facts mentioned but not addressed
- Costs that seem unreasonable
- Missing activities for identified dependencies
- Timeline inconsistencies

### Reproducibility
- Same facts + same deal type = same output
- Changes only happen when inputs change
- Full audit trail of refinements
