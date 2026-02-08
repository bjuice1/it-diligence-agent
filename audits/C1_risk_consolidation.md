# Audit C1: Risk Consolidation/Deduplication

## Status: PARTIALLY IMPLEMENTED
## Priority: MEDIUM (Tier 3 - Feature Improvement) → **Tier 1 if client-facing**
## Complexity: Deep
## Review Score: 8.4/10 (GPT review, Feb 8 2026)
## Implementation Date: Feb 8, 2026

---

## 1. Problem Statement

**Symptom:** Multiple related or duplicate risks appear separately instead of being grouped into consolidated findings.

**User Impact:**
- Redundant content in reports
- Harder to prioritize (same issue appears 3x)
- Looks unprofessional
- Inflates risk count artificially

**Expected Behavior:** Related risks should be grouped and presented as a single consolidated finding with all supporting evidence.

**Tier Note:** If partner/client-facing → Tier 1 (perception = trust)

---

## 2. Critical Constraint: Post-Classification Only (GPT FEEDBACK)

### Rule: Only consolidate items with classification='risk'

**DO NOT consolidate:**
- Gaps (even if phrased similarly)
- Observations (if you add them per B3)
- Cross-entity items (target + buyer)

**Why:** Accidentally merging gaps phrased like risks makes consolidation untrustworthy.

### Pre-condition:
```python
def get_consolidation_candidates(deal_id: str, entity: str) -> List[Risk]:
    """Only return validated risks for consolidation."""
    return Risk.query.filter_by(
        deal_id=deal_id,
        entity=entity,
        classification='risk',  # NOT gap, NOT observation
        validated=True          # Passed B3 validation
    ).all()
```

---

## 3. Evidence Provenance Requirement (GPT FEEDBACK)

### Rule: Consolidated descriptions MUST cite child evidence

Each ConsolidatedRisk must include:
- `child_risk_ids` — original risks
- `supporting_facts` — union of all child facts
- `field_provenance` — which child contributed which claims

### Validation:
```python
def validate_consolidated_risk(consolidated: ConsolidatedRisk, children: List[Risk]) -> bool:
    """Ensure consolidated risk doesn't introduce new claims."""

    # Extract system names from consolidated description
    consolidated_systems = extract_system_names(consolidated.description)

    # Extract system names from all children
    child_systems = set()
    for child in children:
        child_systems.update(extract_system_names(child.description))
        child_systems.update(child.key_systems or [])

    # Flag any new systems not in children
    new_systems = consolidated_systems - child_systems
    if new_systems:
        logger.warning(f"Consolidated risk introduces new systems: {new_systems}")
        return False

    return True
```

**Hard rule:** Consolidated descriptions must not introduce new claims not supported by child facts.

---

## 4. Graph-Based Clustering (GPT FEEDBACK)

### Problem with Pairwise Threshold:
Pairwise "cosine > 0.8" creates weirdness: A~B, B~C, but A not~C

### Solution: Treat as graph clustering

```python
import networkx as nx

def cluster_related_risks(risks: List[Risk]) -> List[List[Risk]]:
    """
    Cluster risks using connected components.

    1. Build graph: nodes = risks, edges = should_group pairs
    2. Find connected components
    3. Return groups
    """
    G = nx.Graph()

    # Add all risks as nodes
    for risk in risks:
        G.add_node(risk.id, risk=risk)

    # Add edges for related risks
    for i, risk_a in enumerate(risks):
        for risk_b in risks[i+1:]:
            if should_group(risk_a, risk_b):
                G.add_edge(risk_a.id, risk_b.id)

    # Find connected components
    groups = []
    for component in nx.connected_components(G):
        group = [G.nodes[node_id]['risk'] for node_id in component]
        groups.append(group)

    return groups
```

---

## 5. Cross-Domain Policy (GPT FEEDBACK)

### Decision: Consolidate within domain first

**Rule:**
1. Primary consolidation: within same domain (Applications, Infra, Cyber, etc.)
2. If risk truly spans domains: create "Cross-Domain / Strategic" consolidated risk
3. Keep domain-level children intact (don't delete, link to them)

**Why:** One mega-risk swallowing everything loses report structure.

```python
def consolidate_by_domain(risks: List[Risk]) -> Dict[str, List[ConsolidatedRisk]]:
    """Consolidate within each domain, then identify cross-domain."""

    # Group by domain
    by_domain = defaultdict(list)
    for risk in risks:
        by_domain[risk.domain].append(risk)

    consolidated = {}
    for domain, domain_risks in by_domain.items():
        consolidated[domain] = consolidate_risks(domain_risks)

    # Optional: identify cross-domain themes
    # consolidated['cross_domain'] = find_cross_domain_themes(consolidated)

    return consolidated
```

---

## 6. Examples of Fragmentation

### Example 1: ERP Environment
Current output (fragmented):
- Risk 1: "Multiple ERP systems create integration complexity"
- Risk 2: "SAP and Oracle running in parallel"
- Risk 3: "ERP consolidation needed post-acquisition"

Should be consolidated to:
- **Consolidated Risk:** "Multiple ERP Environment"
  - Description: Target runs SAP S/4HANA and NetSuite in parallel, creating integration complexity and consolidation needs
  - Supporting facts: [links to all 3 original findings]
  - key_systems: ["SAP S/4HANA", "NetSuite"]

### Example 2: Security Tools
Current output (fragmented):
- Risk 4: "Dual EDR platforms (SentinelOne + CrowdStrike)"
- Risk 5: "SIEM overlap (Elastic + Splunk)"
- Risk 6: "Security tool rationalization needed"

Should be consolidated to:
- **Consolidated Risk:** "Security Tool Overlap"
  - Description: Multiple overlapping security tools across EDR and SIEM require rationalization
  - Supporting facts: [links to all 3 original findings]
  - key_systems: ["SentinelOne", "CrowdStrike", "Elastic", "Splunk"]

---

## 7. Consolidation Approach (Hybrid - Recommended)

### Approach D: Rule-Based + LLM Summary (GPT FEEDBACK Tightened)

```
1. Rule-based candidate grouping (fast, cheap)
   - Same primary_system / vendor
   - Same keyword families
   - Shared supporting facts

2. Optional semantic step for ambiguous leftovers
   - Embeddings only within domain
   - Only for items not already grouped

3. LLM consolidation ONLY after grouping
   - Summarize + title + key systems
   - MUST cite child evidence
   - No new claims allowed

4. Validator
   - No new systems introduced
   - Severity = max(children)
   - Title length + style rules
```

---

## 8. Data Model

### ConsolidatedRisk Model (Updated with GPT FEEDBACK):

```python
@dataclass
class ConsolidatedRisk:
    """Consolidated risk grouping related findings."""

    id: str
    deal_id: str
    domain: str
    title: str                    # "Multiple ERP Environment"
    description: str              # Consolidated summary
    severity: str                 # High/Medium/Low (max of children)

    # Evidence & provenance (GPT FEEDBACK)
    child_risk_ids: List[str]     # Original risk IDs
    supporting_facts: List[str]   # Union of all child facts
    key_systems: List[str]        # Systems mentioned (GPT FEEDBACK)
    field_provenance: Dict        # Which child contributed what

    # Metadata
    consolidation_method: str     # "rule_based" | "llm" | "manual"
    grouping_confidence: float    # 0.0 - 1.0 (GPT FEEDBACK)
    version: int                  # Increment when children change (GPT FEEDBACK)

    created_at: datetime
    updated_at: datetime
```

### Database Table:

```sql
CREATE TABLE consolidated_risks (
    id VARCHAR PRIMARY KEY,
    deal_id VARCHAR NOT NULL,
    domain VARCHAR,
    title VARCHAR,
    description TEXT,
    severity VARCHAR,
    child_risk_ids JSONB,
    supporting_facts JSONB,
    key_systems JSONB,
    field_provenance JSONB,
    consolidation_method VARCHAR,
    grouping_confidence FLOAT,
    version INT DEFAULT 1,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (deal_id) REFERENCES deals(id)
);
```

---

## 9. Storage vs Display Time (GPT FEEDBACK)

### Decision: Both, with specific rules

**Storage-time (primary):**
- Generate ConsolidatedRisk objects after reasoning phase
- Cache results for reproducibility
- Used for reports and exports

**Display-time (secondary):**
- Allow "raw view" toggle in UI
- Small re-clustering only as UI convenience
- Never overwrite stored consolidations

**Why:** Reports and exports must be stable and reviewable.

---

## 10. Files to Create/Modify

### New Files:
| File | Purpose |
|------|---------|
| `agents_v2/risk_consolidation_agent.py` | Consolidation logic |
| `prompts/risk_consolidation_prompt.py` | LLM prompt for consolidation |

### Modified Files:
| File | Changes |
|------|---------|
| `web/database.py` | Add ConsolidatedRisk model |
| `web/tasks/analysis_tasks.py` | Add consolidation step after reasoning |
| `web/app.py` | Display consolidated risks in UI |
| `tools_v2/presentation.py` | Render consolidated risks in reports |

---

## 11. Audit Steps

### Phase 1: Analyze Current State
- [ ] 1.1 Query all risks for test deal
- [ ] 1.2 Manually identify duplicate/related risks
- [ ] 1.3 Count how many could be consolidated
- [ ] 1.4 Document patterns in duplication

### Phase 2: Design Grouping Logic
- [ ] 2.1 Define grouping rules (same app, keywords, etc.)
- [ ] 2.2 Implement graph-based clustering
- [ ] 2.3 Test rules against sample data
- [ ] 2.4 Calculate precision/recall of grouping

### Phase 3: Implement Consolidation
- [ ] 3.1 Create `risk_consolidation_agent.py`
- [ ] 3.2 Add ConsolidatedRisk model
- [ ] 3.3 Add consolidation step to pipeline
- [ ] 3.4 Add evidence provenance validation

### Phase 4: UI Integration
- [ ] 4.1 Update UI to show consolidated view (default)
- [ ] 4.2 Add expand/collapse for child risks
- [ ] 4.3 Add "raw view" toggle
- [ ] 4.4 Update report generation

### Phase 5: Test & Refine
- [ ] 5.1 Run consolidation on test deal
- [ ] 5.2 Review consolidated outputs
- [ ] 5.3 Verify no new claims introduced
- [ ] 5.4 Adjust thresholds/prompts as needed

---

## 12. Consolidation Prompt

```python
RISK_CONSOLIDATION_PROMPT = """
You are consolidating related IT due diligence risks into unified findings.

## Input Risks to Consolidate:
{risks_json}

## Instructions:
1. These risks have been grouped because they relate to the same theme/system
2. Create a SINGLE consolidated risk that captures all concerns
3. The consolidated description MUST:
   - Summarize the core issue
   - Reference ONLY systems mentioned in the child risks
   - Combine the business impact from all child risks
   - NOT introduce any new claims or systems
4. Severity = HIGHEST of any child risk
5. key_systems = all systems mentioned across children

## Output Format:
{{
    "title": "Short title for consolidated risk (under 50 chars)",
    "description": "Comprehensive description combining all related risks",
    "severity": "High|Medium|Low",
    "key_systems": ["list", "of", "affected", "systems"]
}}

## IMPORTANT:
- Do NOT mention any system not explicitly named in the input risks
- Do NOT add new concerns not present in the input risks
"""
```

---

## 13. Definition of Done (GPT FEEDBACK)

### Must have:
- [ ] Related risks grouped (no obvious duplicates)
- [ ] Consolidated summaries are coherent
- [ ] Child risks accessible from consolidated view
- [ ] Risk count feels accurate (not inflated)
- [ ] Report looks professional
- [ ] **0 consolidated risks without supporting facts**
- [ ] **0 new systems introduced** (validation passes)

### Quantitative Metrics (GPT FEEDBACK):
- [ ] **Duplicate risk rate:** % of risks sharing key system/keyword drops by >50%
- [ ] **Over-consolidation rate:** Manual review finds "lost nuance" in <5%

### Tests:
- [ ] Unit test: Grouping rules identify related risks
- [ ] Unit test: Validator catches new systems
- [ ] Unit test: Severity = max of children
- [ ] Integration test: Full consolidation pipeline

---

## 14. Success Criteria

- [ ] Related risks grouped (no obvious duplicates)
- [ ] Consolidated summaries are coherent and cite evidence
- [ ] Child risks accessible from consolidated view
- [ ] Risk count feels accurate (not inflated)
- [ ] Report looks professional
- [ ] Consolidation only happens for validated risks

---

## 15. Questions Resolved

| Question | Decision |
|----------|----------|
| Storage-time vs display-time? | **Both** - storage for stability, display for toggle |
| Manual group/ungroup? | Future (admin-only) |
| Cross-domain risks? | Separate "Cross-Domain" category, keep domain children |
| Version when children change? | **Yes** - increment version field |
| Show both consolidated and raw? | **Yes** - toggle in UI |

---

## 16. Dependencies

- B3 (Risks vs Gaps) - ensures we're consolidating actual risks, not gaps

## 17. Blocks

- Professional report output
- Accurate risk prioritization

---

## 18. GPT Review Notes (Feb 8, 2026)

**Score: 8.4/10**

**Strengths:**
- Clear user pain and examples
- Hybrid approach is right call
- Data model is smart and auditable
- UI expand/collapse behavior included

**Improvements made based on feedback:**
1. Added "Post-Classification Only" rule (risks only, not gaps/observations)
2. Added "Evidence Provenance Requirement" (no new claims)
3. Changed to **graph-based clustering** (connected components)
4. Added **cross-domain policy** (consolidate within domain first)
5. Added `key_systems`, `grouping_confidence`, `version` to model
6. Added "Storage vs Display Time" decision (both, with rules)
7. Added quantitative success metrics (duplicate rate, over-consolidation rate)
8. Added validator to catch new systems

---

## 20. Implementation Notes (Feb 8, 2026)

### Files Created/Modified:

**New Files:**
- `services/risk_consolidation.py` - Main consolidation service with:
  - `RiskConsolidator` class for graph-based clustering
  - networkx connected components for grouping
  - Union-find fallback if networkx unavailable
  - Rule-based grouping (shared facts, systems, keywords, category)
  - Evidence provenance tracking
  - Validation to prevent new claims

- `web/database.py` - Added `ConsolidatedRisk` model with:
  - `child_risk_ids` (JSON array of finding IDs)
  - `supporting_facts` (union of all child facts)
  - `key_systems` (systems mentioned across children)
  - `field_provenance` (which child contributed what)
  - `grouping_confidence` and `version` fields

### Key Implementation Details:

1. **Graph-Based Clustering**: Uses networkx connected components when available, falls back to union-find algorithm.

2. **Grouping Rules**:
   - Shared supporting facts (highest confidence: 0.9)
   - Same key systems mentioned (0.85)
   - Same keyword families (0.7)
   - Same risk category (0.6)

3. **Domain-First**: Consolidation happens within domain first, as recommended.

4. **Validation**: `_validate_consolidated()` checks that no new systems are introduced.

### Remaining Work:
- [ ] Integration into analysis pipeline (call after reasoning phase)
- [ ] UI display of consolidated vs raw view toggle
- [ ] Report generation updates
- [ ] LLM summarization option for consolidated descriptions
