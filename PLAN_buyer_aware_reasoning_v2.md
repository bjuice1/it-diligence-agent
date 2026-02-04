# Plan: PE-Grade Buyer-Aware Reasoning (v2)

## Objective
Enable reasoning agents to produce PE-client-grade outputs by:
1. Making overlap analysis a **first-class structured artifact**
2. Enforcing entity separation at **runtime** (not just prompt guidance)
3. Separating **target actions** from **integration options**
4. Organizing output into a **3-layer stack** for clarity
5. Using **Migration Hypothesis** as the organizing spine

---

## Architecture Overview

### New Reasoning Flow (3 Phases)

```
┌──────────────────────────────────────────────────────────────┐
│  PHASE A: OVERLAP MAPPING (New)                              │
│  - Structured comparison of TARGET vs BUYER by category      │
│  - Produces overlap_candidates[] with confidence & questions │
│  - This happens BEFORE any findings are generated            │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│  PHASE B: FINDINGS GENERATION (Enhanced)                     │
│  Layer 1: Target Standalone (no buyer references)            │
│  Layer 2: Overlap Findings (must cite both entities)         │
│  Layer 3: Integration Workplan (target actions + options)    │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│  PHASE C: VALIDATION (New)                                   │
│  - Reject findings that cite BUYER without TARGET            │
│  - Reject "Buyer should..." language unless framed correctly │
│  - Auto-tag integration_related based on citations           │
└──────────────────────────────────────────────────────────────┘
```

---

## New Data Structures

### 1. OverlapCandidate (First-Class Object)

```python
@dataclass
class OverlapCandidate:
    """
    Structured comparison between TARGET and BUYER systems.
    Generated BEFORE findings - forces the model to "show its work".
    """
    overlap_id: str                      # OC-001, OC-002, etc.
    overlap_type: str                    # See OVERLAP_TYPES below
    target_fact_ids: List[str]           # F-TGT-xxx IDs
    buyer_fact_ids: List[str]            # F-BYR-xxx IDs

    # What we're comparing
    target_summary: str                  # "SAP ECC 6.0 with 247 custom objects"
    buyer_summary: str                   # "Oracle Cloud ERP, enterprise license"

    # Analysis
    why_it_matters: str                  # Integration implication explanation
    confidence: float                    # 0.0-1.0

    # Gaps that need filling
    missing_info_questions: List[str]   # Questions to resolve uncertainty

    # Downstream linking
    migration_scenarios: List[str]       # Which scenarios this affects

    created_at: str = field(default_factory=_generate_timestamp)


OVERLAP_TYPES = [
    "platform_mismatch",        # Different vendors/platforms (SAP vs Oracle)
    "platform_alignment",       # Same platforms (AWS + AWS)
    "version_gap",              # Same platform, different versions
    "capability_gap",           # Target lacks something buyer has
    "capability_overlap",       # Both have same capability (consolidation opportunity)
    "integration_complexity",   # Different integration patterns/middleware
    "data_model_mismatch",      # Incompatible data structures
    "licensing_conflict",       # License terms that conflict
    "security_gap",             # Security posture differences
    "process_divergence",       # Business process differences
]
```

### 2. MigrationHypothesis (Organizing Spine)

```python
@dataclass
class MigrationHypothesis:
    """
    A scenario for how integration could proceed.
    Findings and work items link to one or more scenarios.
    """
    scenario_id: str                     # MS-001
    scenario_name: str                   # "Absorb into Buyer Stack"
    description: str

    # Effort estimate per scenario
    effort_level: str                    # "low", "medium", "high", "very_high"
    effort_rationale: str
    timeline_estimate: str               # "12-18 months"

    # Cost range for this scenario
    cost_range: str                      # "500k_to_1m", "over_1m", etc.

    # Key decision points
    decision_gates: List[Dict]           # {"decision": str, "deadline": str, "owner": str}

    # What must be true for this scenario
    assumptions: List[str]

    # What would invalidate this scenario
    blockers: List[str]


STANDARD_SCENARIOS = [
    {
        "id": "MS-ABSORB",
        "name": "Absorb into Buyer Stack",
        "description": "Full migration of target systems to buyer platforms"
    },
    {
        "id": "MS-STANDALONE",
        "name": "Run Standalone with Interfaces",
        "description": "Target systems remain separate, connected via APIs/integrations"
    },
    {
        "id": "MS-HYBRID",
        "name": "Hybrid Integration",
        "description": "Selective migration - some systems absorbed, others interfaced"
    },
    {
        "id": "MS-PLATFORM",
        "name": "Platform Consolidation",
        "description": "Buyer migrates to target's platform (target has better system)"
    }
]
```

### 3. Enhanced WorkItem (Split Actions)

```python
@dataclass
class WorkItem:
    """Enhanced work item with separated target vs integration actions."""
    finding_id: str
    domain: str
    title: str
    description: str
    phase: str                           # Day_1, Day_100, Post_100
    priority: str
    owner_type: str                      # buyer, target, shared, vendor

    # === NEW: Separated Actions ===
    target_action: str                   # What TARGET must do (always required)
    integration_option: Optional[str]    # Optional path depending on buyer strategy

    # === NEW: Scenario Linking ===
    applicable_scenarios: List[str]      # ["MS-ABSORB", "MS-HYBRID"]
    scenario_specific_notes: Dict[str, str]  # {"MS-ABSORB": "Add 3 months if...", ...}

    # === NEW: Entity Tracking ===
    integration_related: bool            # True if depends on buyer context
    target_facts_cited: List[str]        # F-TGT-xxx
    buyer_facts_cited: List[str]         # F-BYR-xxx (empty if standalone)
    overlap_id: Optional[str]            # Link to OverlapCandidate if relevant

    # Existing fields
    triggered_by: List[str]
    based_on_facts: List[str]            # Combined list (for backwards compatibility)
    cost_estimate: str
    cost_buildup: Optional[CostBuildUp]
    triggered_by_risks: List[str]
    mna_lens: str
    mna_implication: str
    dependencies: List[str]
    confidence: str
    reasoning: str
    created_at: str
```

### 4. Enhanced Risk (Entity Tracking)

```python
@dataclass
class Risk:
    """Enhanced risk with entity separation."""
    finding_id: str
    domain: str
    title: str
    description: str
    category: str
    severity: str

    # === NEW: Risk Classification ===
    risk_scope: str                      # "target_standalone" | "integration_dependent"

    # === NEW: Entity Tracking ===
    target_facts_cited: List[str]        # F-TGT-xxx (always required)
    buyer_facts_cited: List[str]         # F-BYR-xxx (only if integration_dependent)
    overlap_id: Optional[str]            # Link to OverlapCandidate if relevant

    # === NEW: Scenario Impact ===
    scenario_impacts: Dict[str, str]     # {"MS-ABSORB": "Critical - blocks migration", ...}

    # Existing fields
    integration_dependent: bool          # Kept for backwards compatibility
    mitigation: str
    based_on_facts: List[str]            # Combined list (backwards compat)
    confidence: str
    reasoning: str
    mna_lens: str
    mna_implication: str
    timeline: Optional[str]
    created_at: str
```

---

## New Tool: generate_overlap_map

Add to REASONING_TOOLS:

```python
{
    "name": "generate_overlap_map",
    "description": """MUST be called FIRST, before creating any findings.

    Analyzes TARGET and BUYER inventories to identify overlap candidates.
    This structures your thinking and ensures all findings are grounded
    in explicit comparisons.

    For each category where both entities have data, produce an overlap candidate.

    Returns a list of overlap candidate IDs.""",
    "input_schema": {
        "type": "object",
        "properties": {
            "overlap_candidates": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "overlap_type": {
                            "type": "string",
                            "enum": OVERLAP_TYPES,
                            "description": "Type of overlap/mismatch"
                        },
                        "target_fact_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "TARGET fact IDs (F-TGT-xxx)"
                        },
                        "buyer_fact_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "BUYER fact IDs (F-BYR-xxx)"
                        },
                        "target_summary": {
                            "type": "string",
                            "description": "Brief summary of target's position"
                        },
                        "buyer_summary": {
                            "type": "string",
                            "description": "Brief summary of buyer's position"
                        },
                        "why_it_matters": {
                            "type": "string",
                            "description": "Why this overlap matters for integration"
                        },
                        "confidence": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1,
                            "description": "Confidence in this assessment (0.0-1.0)"
                        },
                        "missing_info_questions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Questions that would improve confidence"
                        }
                    },
                    "required": ["overlap_type", "target_fact_ids", "buyer_fact_ids",
                                "target_summary", "buyer_summary", "why_it_matters",
                                "confidence"]
                }
            }
        },
        "required": ["overlap_candidates"]
    }
}
```

---

## Runtime Validation Rules

Add to `execute_reasoning_tool()`:

```python
def validate_finding_entity_rules(tool_name: str, tool_input: dict) -> List[str]:
    """
    Enforce entity separation rules at runtime.
    Returns list of validation errors (empty = valid).
    """
    errors = []

    # Get fact citations
    based_on = tool_input.get("based_on_facts", [])
    target_facts = tool_input.get("target_facts_cited", [])
    buyer_facts = tool_input.get("buyer_facts_cited", [])

    # If using new fields, validate them
    if buyer_facts or target_facts:
        # Rule 1: Buyer facts require target facts
        if buyer_facts and not target_facts:
            errors.append(
                f"ENTITY_VIOLATION: Finding cites buyer facts {buyer_facts} "
                f"but no target facts. All findings must anchor in target."
            )

    # If using legacy based_on_facts, check those
    elif based_on:
        buyer_refs = [f for f in based_on if "BYR" in f or "BUYER" in f.upper()]
        target_refs = [f for f in based_on if "TGT" in f or "TARGET" in f.upper()]

        # Rule 1: Buyer facts require target facts
        if buyer_refs and not target_refs:
            errors.append(
                f"ENTITY_VIOLATION: Finding cites buyer facts {buyer_refs} "
                f"but no target facts. All findings must anchor in target."
            )

    # Rule 2: Check for "Buyer should..." language in descriptions
    description = tool_input.get("description", "")
    target_action = tool_input.get("target_action", "")
    integration_option = tool_input.get("integration_option", "")

    buyer_action_patterns = [
        r"buyer\s+should",
        r"buyer\s+must",
        r"buyer\s+needs\s+to",
        r"recommend.*buyer",
    ]

    for pattern in buyer_action_patterns:
        # Allow in integration_option field, block elsewhere
        if re.search(pattern, description, re.IGNORECASE):
            errors.append(
                f"SCOPE_VIOLATION: Description contains buyer-action language "
                f"('{pattern}'). Reframe as target-side action or move to "
                f"integration_option field."
            )
        if re.search(pattern, target_action, re.IGNORECASE):
            errors.append(
                f"SCOPE_VIOLATION: target_action contains buyer-action language. "
                f"target_action must describe what TARGET does, not buyer."
            )

    # Rule 3: Work items must have target_action
    if tool_name == "create_work_item":
        if not target_action and not tool_input.get("description"):
            errors.append(
                "MISSING_TARGET_ACTION: Work items must specify target_action."
            )

    return errors


def execute_reasoning_tool(tool_name: str, tool_input: dict, reasoning_store) -> dict:
    """Execute a reasoning tool with validation."""

    # === NEW: Pre-execution validation ===
    validation_errors = validate_finding_entity_rules(tool_name, tool_input)

    if validation_errors:
        # Log but don't block - return warning to model
        logger.warning(f"Validation warnings for {tool_name}: {validation_errors}")
        return {
            "status": "warning",
            "message": "Finding accepted with warnings",
            "warnings": validation_errors,
            "guidance": "Please ensure findings anchor in target facts and avoid buyer-action language."
        }

    # ... rest of existing execution logic ...
```

---

## 3-Layer Output Structure

Update reasoning prompts to require this structure:

```markdown
## OUTPUT STRUCTURE (Required)

You MUST organize your outputs into three distinct layers:

### LAYER 1: TARGET STANDALONE FINDINGS
Findings about the target that exist **regardless of who the buyer is**.
- Risk: "SAP ECC 6.0 reaches EOL 2027" (standalone, no buyer reference)
- Risk: "Single developer maintains 247 custom ABAP programs" (key person risk)
- These would matter even if target remained independent.

**Rules:**
- Do NOT reference buyer facts
- based_on_facts: Only F-TGT-xxx IDs
- risk_scope: "target_standalone"

### LAYER 2: OVERLAP FINDINGS
Findings that **depend on buyer context** for meaning.
- Strategic Consideration: "ERP Platform Mismatch - SAP vs Oracle"
- Risk: "Data model incompatibility between SAP and Oracle ERP"
- These require knowing both entities to identify.

**Rules:**
- MUST reference both target AND buyer facts
- based_on_facts: Both F-TGT-xxx and F-BYR-xxx IDs
- MUST link to an overlap_id from your overlap map
- risk_scope: "integration_dependent"

### LAYER 3: INTEGRATION WORKPLAN
Work items organized by scenario with separated actions.

**Structure each work item as:**
```json
{
  "title": "Migrate SAP master data to Oracle Cloud",
  "target_action": "Inventory SAP custom objects; estimate conversion/remediation effort; engage SAP licensing for migration terms",
  "integration_option": "If buyer insists on Oracle harmonization, plan for ETL + process redesign (add 6 months)",
  "applicable_scenarios": ["MS-ABSORB", "MS-HYBRID"],
  "scenario_specific_notes": {
    "MS-ABSORB": "Full data migration required",
    "MS-STANDALONE": "Interface-only, no migration needed"
  }
}
```
```

---

## Tone Control Prompt

Add this paragraph to ALL domain reasoning prompts:

```markdown
## BUYER CONTEXT USAGE (Critical)

Buyer facts describe **one possible destination state**, not a standard.

Use buyer context ONLY to:
- Explain integration complexity (what makes migration hard/easy)
- Identify sequencing dependencies (what must happen first)
- Surface optional paths (scenarios, not mandates)

All actions MUST be framed as **target-side diligence outputs**:
- What to **verify** (gaps, unknowns)
- What to **size** (effort, cost, timeline)
- What to **remediate** (technical debt, risks)
- What to **migrate** (data, systems, processes)
- What to **interface** (integration points)
- What to **TSA** (transition services needed)

❌ WRONG: "Buyer should upgrade their Oracle instance"
✅ RIGHT: "Target SAP migration to buyer Oracle blocked until Oracle version confirmed"

❌ WRONG: "Recommend buyer implement SSO"
✅ RIGHT: "Target SSO integration requires buyer IdP details (GAP-003)"
```

---

## Implementation Sequence

### Week 1: Foundation
1. **Fact ID Convention** - Update ID generation to F-TGT-xxx / F-BYR-xxx
2. **OverlapCandidate dataclass** - Add to reasoning_tools.py
3. **generate_overlap_map tool** - Add to REASONING_TOOLS

### Week 2: Enhanced Schema
4. **Update WorkItem** - Add target_action, integration_option, scenario fields
5. **Update Risk** - Add risk_scope, entity tracking fields
6. **MigrationHypothesis dataclass** - Add scenario support

### Week 3: Validation & Prompts
7. **Runtime validation** - Add validate_finding_entity_rules()
8. **Update all 6 domain prompts** - Add 3-layer structure, tone control
9. **Update base_reasoning_agent** - Enforce overlap map generation first

### Week 4: Testing & Refinement
10. **Test with target-only docs** - Verify backwards compatibility
11. **Test with target+buyer docs** - Verify overlap detection
12. **Test validation rules** - Verify rejection of bad patterns
13. **Refine prompts based on output quality**

---

## Files to Modify

| File | Changes | Priority |
|------|---------|----------|
| `stores/fact_store.py` | F-TGT/F-BYR ID generation | P1 |
| `tools_v2/reasoning_tools.py` | OverlapCandidate, MigrationHypothesis, enhanced WorkItem/Risk, generate_overlap_map tool, validation | P1 |
| `agents_v2/base_reasoning_agent.py` | Enforce overlap map first, use enhanced formatter | P2 |
| `prompts/v2_*_reasoning_prompt.py` (all 6) | 3-layer structure, tone control, overlap map instructions | P2 |

---

## Sample Output: What PE-Grade Looks Like

### Before (Generic)
```json
{
  "title": "ERP Migration Required",
  "description": "Target uses SAP, buyer uses Oracle. Will need to migrate.",
  "based_on_facts": ["F-001"],
  "cost_estimate": "over_1m"
}
```

### After (PE-Grade)
```json
{
  "title": "SAP-to-Oracle ERP Data Migration",
  "target_action": "Inventory SAP custom objects (247 Z-programs per F-TGT-APP-001); assess data model gaps; engage SAP licensing re: migration terms",
  "integration_option": "If buyer confirms Oracle Cloud as target state, plan ETL buildout + UAT (adds 6-9 months to timeline)",
  "applicable_scenarios": ["MS-ABSORB", "MS-HYBRID"],
  "scenario_specific_notes": {
    "MS-ABSORB": "Full migration - critical path item",
    "MS-STANDALONE": "Interface-only via iPaaS - lower effort but ongoing maintenance"
  },
  "target_facts_cited": ["F-TGT-APP-001", "F-TGT-APP-012"],
  "buyer_facts_cited": ["F-BYR-APP-001"],
  "overlap_id": "OC-001",
  "cost_estimate": "over_1m",
  "cost_buildup": {
    "anchor_name": "ERP Data Migration",
    "estimation_method": "fixed_by_size",
    "size_tier": "large",
    "total_low": 1200000,
    "total_high": 2500000,
    "assumptions": [
      "247 custom objects require remediation",
      "12-18 month migration timeline",
      "Parallel run period of 3 months"
    ],
    "source_facts": ["F-TGT-APP-001", "F-TGT-APP-012"]
  }
}
```

---

## Quick Win: If We Only Do 2 Things

1. **Generate Overlap Map first** (structured, with confidence and missing questions)
2. **Runtime validation** (buyer-cited findings must include target facts + work items must be target actions)

These two changes will materially improve consistency and eliminate the weird edge cases where the model drifts into "buyer consulting" mode.
