# IT Due Diligence Agent: Executive Narrative Enhancement
## 10-Phase Game Plan

**Objective**: Transform the IT DD Agent from producing *findings* to producing *IC-ready executive narratives* that tell a cohesive M&A story.

**Success Criteria**: Output that a Partner could hand directly to an Investment Committee with minimal editing.

---

## THE 10 PHASES

| Phase | Name | Purpose | Effort |
|-------|------|---------|--------|
| 1 | M&A Framing Foundation | Establish the 5 M&A lenses as non-negotiable output requirements | Foundation |
| 2 | Reasoning Prompt Enhancement | Embed M&A framing into every domain agent | Medium |
| 3 | Team/Function Story Pattern | Create the "what they do / strengths / constraints / dependencies" structure | Medium |
| 4 | Narrative Synthesis Agent | New agent that transforms findings → executive narrative | Large |
| 5 | Deal-Type Templates | Acquisition vs Carveout vs Divestiture specific outputs | Medium |
| 6 | Quality Review Agent | Reviewer that checks against executive standards | Medium |
| 7 | Benchmarking Intelligence | Relative/directional benchmark statements | Small |
| 8 | Risk & Synergy Table Generator | Structured tables with required columns | Medium |
| 9 | UI/Output Integration | Display narrative, export formats, citations | Medium |
| 10 | Calibration & Testing | Run against samples, compare to expectation, iterate | Ongoing |

---

## PHASE 1: M&A FRAMING FOUNDATION

### Objective
Establish the canonical M&A framing that ALL outputs must connect to. This becomes the "lens" through which every finding is evaluated.

### 1.1 Define the 5 M&A Lenses

| Lens | Definition | When to Apply |
|------|------------|---------------|
| **Day-1 Continuity** | What must work on Day 1 for business to operate? | Every finding |
| **TSA Risk/Exposure** | What services will require Transition Services Agreement? | Carveouts, some acquisitions |
| **Separation Complexity** | How entangled is this with parent/other entities? | Carveouts, divestitures |
| **Synergy Opportunity** | Where can value be created through combination/consolidation? | Acquisitions |
| **Cost Driver** | What drives IT cost and how might it change? | All deal types |

### 1.2 Create Shared Definitions File

**Deliverable**: `prompts/shared/mna_framing.py`

```python
MNA_LENSES = {
    "day_1_continuity": {
        "definition": "...",
        "question": "Will this prevent business operations on Day 1?",
        "examples": ["Authentication", "Payroll", "Core ERP", "Network connectivity"]
    },
    "tsa_exposure": {...},
    "separation_complexity": {...},
    "synergy_opportunity": {...},
    "cost_driver": {...}
}
```

### 1.3 Establish Inference Discipline

**Rule**: Any statement that goes beyond explicit inventory facts must be labeled.

| Type | Format | Example |
|------|--------|---------|
| Fact | Direct statement | "MFA coverage is 62% (F-CYBER-003)" |
| Inference | "Inference:" prefix | "Inference: Given the 62% MFA coverage and no PAM, privileged access hygiene is likely weak" |
| Pattern | "Pattern:" prefix | "Pattern: Multiple AD forests typically indicate incomplete prior M&A integration" |

### 1.4 Review Point

**Gate Criteria**:
- [x] All 5 M&A lenses defined with clear questions (`prompts/shared/mna_framing.py`)
- [x] Shared definitions file created and importable (`MNA_LENSES`, `STATEMENT_TYPES`)
- [x] Inference discipline documented with examples (`STATEMENT_TYPES` with format specs)
- [x] Team aligned on vocabulary (exported in `prompts/shared/__init__.py`)

---

## PHASE 2: REASONING PROMPT ENHANCEMENT

### Objective
Embed M&A framing requirements directly into each domain reasoning prompt so findings automatically connect to deal implications.

### 2.1 Update Each Domain Prompt

**Files to modify**:
- `v2_applications_reasoning_prompt.py`
- `v2_cybersecurity_reasoning_prompt.py`
- `v2_identity_access_reasoning_prompt.py`
- `v2_infrastructure_reasoning_prompt.py`
- `v2_network_reasoning_prompt.py`
- `v2_organization_reasoning_prompt.py`

**Add to each prompt**:

```
## M&A FRAMING REQUIREMENTS

Every finding you produce MUST explicitly connect to at least one M&A lens:

1. **Day-1 Continuity**: Does this affect Day 1 operations?
2. **TSA Exposure**: Does this require transition services?
3. **Separation Complexity**: How entangled is this?
4. **Synergy Opportunity**: Where's the value creation potential?
5. **Cost Driver**: What drives cost and how might it change?

In your reasoning field, explicitly state: "M&A Lens: [lens name] - [why this applies]"
```

### 2.2 Add M&A Lens Field to Tool Schemas

Update `reasoning_tools.py` to include:

```python
"mna_lens": {
    "type": "string",
    "enum": ["day_1_continuity", "tsa_exposure", "separation_complexity",
             "synergy_opportunity", "cost_driver"],
    "description": "Primary M&A lens this finding connects to"
},
"mna_implication": {
    "type": "string",
    "description": "Specific implication for this deal (1-2 sentences)"
}
```

### 2.3 Update Deal Context Injection

Ensure deal context (deal_type, buyer info, carveout status) is prominently injected so agents can tailor M&A framing.

### 2.4 L3 Expectations

| Agent | Day-1 Focus | TSA Focus | Separation Focus | Synergy Focus | Cost Focus |
|-------|-------------|-----------|------------------|---------------|------------|
| Applications | ERP, payroll, core ops | Shared apps | Parent system dependencies | App consolidation | License rationalization |
| Cybersecurity | Auth, VPN, critical controls | SOC, SIEM, monitoring | Parent security services | Tool consolidation | Security tool spend |
| Identity | Authentication, MFA | Identity services | Parent AD/IdP | Directory consolidation | License/tool spend |
| Infrastructure | DC, network, DR | Hosting, DC services | Parent infrastructure | DC consolidation | Hosting costs |
| Network | Connectivity, VPN | WAN, parent circuits | Parent network | WAN consolidation | Circuit costs |
| Organization | Critical staff | Shared services staff | Parent IT support | Team consolidation | Headcount |

### 2.5 Review Point

**Gate Criteria**:
- [x] All 6 prompts updated with M&A framing section (all domain reasoning prompts updated)
- [x] Tool schemas include mna_lens and mna_implication fields (`reasoning_tools.py`)
- [x] Deal context properly injected into all prompts (via `_prompt_context` field)
- [ ] Test run produces findings with M&A lens populated (requires test run)

---

## PHASE 3: TEAM/FUNCTION STORY PATTERN

### Objective
Create the structured "story" pattern for each IT function that includes: what they do, strengths, constraints, and dependencies.

### 3.1 Define the Story Structure

For each IT function/team, produce:

```markdown
### [Team/Function Name]

**What they do day-to-day**: [2-3 sentences on primary activities]

**What they likely do well**: [1-2 strengths based on evidence]

**Where they're likely constrained**: [1-2 risks/bottlenecks based on evidence]

**Key dependencies & handoffs**:
- Upstream: [who/what they depend on]
- Downstream: [who/what depends on them]

**M&A Implication**: [1-2 sentences on Day-1/TSA/separation/synergy relevance]
```

### 3.2 Create Story Extraction Prompts

**New file**: `prompts/shared/function_story_template.py`

```python
FUNCTION_STORY_TEMPLATE = """
For the {function_name} function, based on the inventory:

1. DAY-TO-DAY: What does this team/function primarily do?
   - Base ONLY on inventory evidence
   - Focus on operational activities

2. STRENGTHS: What do they likely do well?
   - Look for: certifications, mature tooling, adequate staffing, documented processes
   - Label inferences

3. CONSTRAINTS: Where are they likely bottlenecked?
   - Look for: understaffing, technical debt, single points of failure, skill gaps
   - Label inferences

4. DEPENDENCIES:
   - Upstream: What must work for this function to operate?
   - Downstream: What relies on this function?

5. M&A IMPLICATION:
   - Day-1: Critical for operations?
   - TSA: Likely shared service?
   - Separation: Entangled with parent?
   - Synergy: Consolidation opportunity?
"""
```

### 3.3 Map Functions to Domains

| Domain Agent | Functions to Story |
|--------------|-------------------|
| Organization | IT Leadership, Applications Team, Infrastructure Team, Security Team, Service Desk, PMO, Data/Analytics |
| Applications | ERP, CRM, HCM/Payroll, BI/Analytics, Custom Apps, Integration/Middleware |
| Infrastructure | Data Center, Compute, Storage, Backup/DR, Cloud |
| Network | WAN, LAN, Wireless, Firewalls, VPN |
| Cybersecurity | Security Operations, Vulnerability Management, Identity Security, Compliance |
| Identity | Directory Services, Access Management, Privileged Access, JML Process |

### 3.4 L3 Expectations

Each function story must include:
- [ ] At least 2 specific inventory references
- [ ] At least 1 labeled inference (if applicable)
- [ ] Clear Day-1 or TSA implication
- [ ] At least 1 upstream and 1 downstream dependency identified

### 3.5 Review Point

**Gate Criteria**:
- [x] Story template created and tested (`prompts/shared/function_story_template.py`)
- [x] Function-to-domain mapping complete (31 functions across 6 domains)
- [ ] Sample stories generated for each domain (requires test run)
- [x] Stories include required elements (evidence, inference labels, dependencies)

---

## PHASE 4: NARRATIVE SYNTHESIS AGENT

### Objective
Create a new agent that takes all domain findings and produces a cohesive executive narrative following the exact structure from the example.

### 4.1 Define Narrative Structure

```markdown
# IT Operating Model Narrative ({Company Name})

## 1) Executive Summary (5-7 bullets)
- Org shape and operating posture
- Cost/headcount concentration
- 3-5 key risks
- 3-5 key synergy opportunities

## 2) How the IT Organization is Built
- Lean vs layered
- Run/operate vs change/project heavy
- What this implies for business model

## 3) Team-by-Team Story
[For each function identified]

## 4) M&A Lens: Day-1 + TSA + Separation
- TSA-exposed functions
- Outsourced reliance and Day-1 implications
- 5-8 separation considerations (action-oriented bullets)

## 5) Benchmarks & Operating Posture
- 4-6 relative/directional statements
- All inferences labeled

## 6) Risks and Synergies

### Risks Table
| Risk | Why it matters | Likely impact | Mitigation |

### Synergies Table
| Opportunity | Why it matters | Value mechanism | First step |
```

### 4.2 Create Synthesis Prompt

**New file**: `prompts/v2_narrative_synthesis_prompt.py`

This prompt will:
1. Take ALL findings from all domain agents as input
2. Take the function stories from Phase 3 as input
3. Synthesize into the executive narrative structure
4. Maintain citation discipline
5. Label inferences explicitly

### 4.3 Define Input/Output Contract

**Input**:
```python
{
    "deal_context": {...},
    "domain_findings": {
        "applications": {"risks": [...], "work_items": [...], "strategic": [...], "recommendations": [...]},
        "cybersecurity": {...},
        "identity": {...},
        "infrastructure": {...},
        "network": {...},
        "organization": {...}
    },
    "function_stories": [...],
    "facts_inventory": {...}
}
```

**Output**:
```python
{
    "executive_summary": [...],  # 5-7 bullets
    "org_structure_narrative": "...",  # 2-3 paragraphs
    "team_stories": [...],  # structured stories
    "mna_lens_section": {
        "tsa_exposed_functions": [...],
        "day_1_requirements": [...],
        "separation_considerations": [...]  # 5-8 action bullets
    },
    "benchmark_statements": [...],  # 4-6 statements
    "risks_table": [...],
    "synergies_table": [...]
}
```

### 4.4 L3 Expectations

| Section | Requirements |
|---------|--------------|
| Executive Summary | Exactly 5-7 bullets; must mention deal type implications |
| Org Structure | 2-3 paragraphs; must characterize lean vs layered, run vs change |
| Team Stories | Every team in inventory covered; each has all 5 elements |
| M&A Lens | At least 5 separation considerations; all action-oriented |
| Benchmarks | 4-6 statements; all inferences labeled |
| Risks Table | At least 5 risks; all columns populated |
| Synergies Table | At least 3 synergies; all columns populated |

### 4.5 Review Point

**Gate Criteria**:
- [x] Synthesis prompt created (`prompts/v2_narrative_synthesis_prompt.py`)
- [x] Input/output contract defined (`ExecutiveNarrative` dataclass)
- [x] Integration with orchestrator planned (added as Phase 7 in `main_v2.py`)
- [ ] Sample narrative generated and reviewed against example (requires test run)

---

## PHASE 5: DEAL-TYPE TEMPLATES

### Objective
Create specific narrative templates for each deal type (Acquisition, Carveout, Divestiture) with tailored M&A lens emphasis.

### 5.1 Define Deal-Type Differences

| Aspect | Acquisition | Carveout | Divestiture |
|--------|-------------|----------|-------------|
| Primary Lens | Synergy + Integration | TSA + Separation | Separation + Clean Exit |
| Day-1 Focus | Connectivity to buyer | Standalone operations | Minimal disruption to RemainCo |
| Key Question | "How do we integrate?" | "How do we stand alone?" | "How do we cleanly separate?" |
| TSA Emphasis | Low (usually) | High (critical) | Medium |
| Synergy Emphasis | High | Low | N/A |
| Separation Emphasis | Low | High | High |

### 5.2 Create Template Variants

**Files**:
- `prompts/templates/acquisition_narrative_template.py`
- `prompts/templates/carveout_narrative_template.py`
- `prompts/templates/divestiture_narrative_template.py`

Each template includes:
- Deal-type-specific executive summary framing
- Adjusted section emphasis (e.g., carveout has expanded TSA section)
- Deal-type-specific risk/synergy table columns
- Tailored separation considerations

### 5.3 Carveout-Specific Additions

For carveouts, add:

```markdown
## TSA Services Inventory

| Service | Provider | Duration Estimate | Monthly Cost | Exit Complexity |
|---------|----------|-------------------|--------------|-----------------|

## Entanglement Assessment

| System/Service | Entanglement Level | Separation Approach | Effort |
|----------------|-------------------|---------------------|--------|

## Standalone Readiness Scorecard

| Capability | Current State | Standalone Ready? | Gap |
|------------|---------------|-------------------|-----|
```

### 5.4 L3 Expectations

| Deal Type | Required Sections | Emphasis |
|-----------|------------------|----------|
| Acquisition | Standard + Synergy deep-dive | Integration timeline, synergy quantification |
| Carveout | Standard + TSA inventory + Entanglement + Standalone scorecard | TSA duration, separation complexity, Day-1 readiness |
| Divestiture | Standard + Clean separation focus | RemainCo impact, data separation, contract assignment |

### 5.5 Review Point

**Gate Criteria**:
- [x] All 3 templates created (`prompts/templates/`)
  - `acquisition_narrative_template.py` (synergy/integration focus)
  - `carveout_narrative_template.py` (TSA/separation focus)
  - `divestiture_narrative_template.py` (RemainCo/clean exit focus)
- [ ] Templates tested with sample data (requires test run)
- [x] Carveout-specific sections (TSA inventory, entanglement, standalone scorecard) defined
- [x] Deal type properly drives template selection (`get_template_for_deal_type()`)
- [x] Templates integrated into NarrativeSynthesisAgent

---

## PHASE 6: QUALITY REVIEW AGENT

### Objective
Create a review agent that validates narrative output against executive standards before final delivery.

### 6.1 Define Review Criteria

```python
NARRATIVE_REVIEW_CRITERIA = {
    "completeness": {
        "executive_summary_bullet_count": (5, 7),
        "team_stories_coverage": "all teams in inventory",
        "risks_minimum": 5,
        "synergies_minimum": 3,
        "separation_considerations_minimum": 5
    },
    "mna_framing": {
        "every_risk_has_mna_lens": True,
        "every_synergy_has_value_mechanism": True,
        "day_1_explicitly_addressed": True,
        "tsa_explicitly_addressed_if_carveout": True
    },
    "evidence_discipline": {
        "facts_cited": True,
        "inferences_labeled": True,
        "no_fabricated_specifics": True
    },
    "actionability": {
        "mitigations_are_specific": True,
        "first_steps_are_actionable": True,
        "separation_considerations_are_action_oriented": True
    },
    "tone": {
        "consulting_tone": True,
        "not_academic": True,
        "decisive_not_hedging": True
    }
}
```

### 6.2 Create Review Prompt

**New file**: `prompts/v2_narrative_review_prompt.py`

The reviewer will:
1. Check completeness against criteria
2. Validate M&A framing presence
3. Verify evidence discipline
4. Assess actionability
5. Flag tone issues
6. Return pass/fail with specific feedback

### 6.3 Define Review Output

```python
{
    "overall_pass": bool,
    "score": float,  # 0-100
    "section_scores": {
        "executive_summary": {...},
        "org_structure": {...},
        "team_stories": {...},
        "mna_lens": {...},
        "benchmarks": {...},
        "risks_synergies": {...}
    },
    "issues": [
        {
            "section": "...",
            "issue": "...",
            "severity": "critical|major|minor",
            "suggestion": "..."
        }
    ],
    "improvements": [...]
}
```

### 6.4 L3 Expectations

| Check | Pass Criteria | Fail Action |
|-------|---------------|-------------|
| Bullet count | 5-7 in exec summary | Return for revision |
| Team coverage | 100% of inventory teams | Return for revision |
| M&A lens | Every risk has lens | Return for revision |
| Inference labels | All inferences labeled | Return for revision |
| Actionability | Mitigations are specific | Flag for review |
| Tone | No academic language | Flag for review |

### 6.5 Review Point

**Gate Criteria**:
- [x] Review criteria defined and documented (`NARRATIVE_REVIEW_CRITERIA` in `v2_narrative_review_prompt.py`)
- [x] Review prompt created (`NARRATIVE_REVIEW_PROMPT` with LLM and local review modes)
- [x] Review output schema defined (`ReviewResult`, `ReviewIssue`, `SectionScore` dataclasses)
- [x] Integration with pipeline (Phase 8 in `main_v2.py` - review before final output)
- [ ] Sample narratives pass review (requires test run)

---

## PHASE 7: BENCHMARKING INTELLIGENCE

### Objective
Enable the system to produce relative/directional benchmark statements without fabricating external data.

### 7.1 Define Benchmark Patterns

**Pattern Library**:

```python
BENCHMARK_PATTERNS = {
    "concentration": {
        "template": "Relative concentration in {area} ({pct}% of headcount/cost) suggests {implication}",
        "example": "Relative concentration in Applications (35% of IT headcount) suggests a project-heavy operating model"
    },
    "outsourcing": {
        "template": "Outsourcing is concentrated in {areas} ({pct}%), which implies {implication}",
        "example": "Outsourcing is concentrated in Infrastructure and Service Desk (38-43%), implying potential TSA complexity"
    },
    "ratio": {
        "template": "The {role_a} to {role_b} ratio of {ratio} indicates {implication}",
        "example": "The IT-to-employee ratio of 1:85 indicates a lean IT organization"
    },
    "posture": {
        "template": "The organization appears {posture} based on {evidence}",
        "example": "The organization appears run-heavy (70% ops, 30% projects) based on team composition"
    }
}
```

### 7.2 Create Benchmark Generator

**New file**: `prompts/shared/benchmark_generator.py`

```python
def generate_benchmarks(inventory_summary: dict) -> list:
    """
    Generate 4-6 benchmark statements based on inventory.
    All statements are relative/directional, not absolute.
    All inferences are labeled.
    """
    benchmarks = []

    # Calculate concentration
    # Calculate ratios
    # Assess posture
    # Generate statements using patterns

    return benchmarks
```

### 7.3 Safe Benchmark Statements

| Type | Safe | Unsafe |
|------|------|--------|
| Concentration | "35% of headcount in Applications suggests project intensity" | "Industry average is 25%, so they're 10% over" |
| Ratio | "1:85 IT-to-employee is on the leaner end" | "Best practice is 1:50" |
| Outsourcing | "43% outsourcing in Service Desk is notable" | "Typical is 20-30%" |
| Posture | "Appears run-heavy based on team composition" | "Should have 40% change capacity" |

### 7.4 L3 Expectations

- [ ] All benchmarks use relative language ("suggests", "indicates", "appears")
- [ ] No fabricated external statistics
- [ ] All benchmarks tied to inventory evidence
- [ ] Inferences explicitly labeled
- [ ] 4-6 statements per narrative

### 7.5 Review Point

**Gate Criteria**:
- [x] Benchmark pattern library created (`BENCHMARK_PATTERNS` with 6 types)
- [x] Generator function implemented (`generate_benchmarks()` in `benchmark_generator.py`)
- [x] Sample benchmarks reviewed for safety (`validate_benchmark_safety()` function)
- [x] No external data fabrication (`UNSAFE_LANGUAGE` list, validation checks)
- [x] Analysis functions for concentration, outsourcing, ratios, posture, maturity

---

## PHASE 8: RISK & SYNERGY TABLE GENERATOR

### Objective
Automatically generate structured risk and synergy tables with required columns from domain findings.

### 8.1 Define Table Schemas

**Risk Table**:
| Column | Source | Required |
|--------|--------|----------|
| Risk | Finding title | Yes |
| Why it matters | M&A implication | Yes |
| Likely impact | Severity + deal impact | Yes |
| Mitigation | Mitigation field | Yes |

**Synergy Table**:
| Column | Source | Required |
|--------|--------|----------|
| Opportunity | Strategic consideration title | Yes |
| Why it matters | Deal thesis connection | Yes |
| Value mechanism | How value is created | Yes |
| First step | Actionable next step | Yes |

### 8.2 Create Table Generator

**New file**: `tools_v2/table_generators.py`

```python
def generate_risk_table(domain_findings: dict) -> list:
    """
    Aggregate risks from all domains.
    Deduplicate and prioritize.
    Ensure all columns populated.
    """

def generate_synergy_table(domain_findings: dict, deal_type: str) -> list:
    """
    Aggregate synergies from strategic considerations.
    Filter by deal type (acquisitions have more synergies).
    Ensure value mechanism is specific.
    """
```

### 8.3 Value Mechanism Categories

For synergies, require specific value mechanisms:

| Mechanism | Definition | Example |
|-----------|------------|---------|
| Cost elimination | Remove duplicate spend | "Consolidate to single SIEM, eliminate $200K/yr" |
| Cost avoidance | Prevent future spend | "Avoid target's planned ERP upgrade" |
| Efficiency gain | Do more with same | "Combined SOC covers both entities" |
| Capability gain | Acquire new capability | "Target's data science team fills buyer gap" |
| Revenue enablement | Enable revenue | "Unified platform enables cross-sell" |

### 8.4 L3 Expectations

| Table | Minimum Rows | Column Completeness | Prioritization |
|-------|--------------|---------------------|----------------|
| Risks | 5 | 100% | By severity (critical first) |
| Synergies | 3 | 100% | By value (highest first) |

### 8.5 Review Point

**Gate Criteria**:
- [x] Table generators implemented (`tools_v2/table_generators.py`)
- [x] All columns auto-populated (`_ensure_risk_complete()`, `_ensure_synergy_complete()`)
- [x] Deduplication working (`_deduplicate_risks()`, `_deduplicate_synergies()`)
- [x] Prioritization (severity/value) working (sorted by `RiskSeverity.sort_order`)
- [x] Sample tables reviewed (tested with sample data)
- [x] Value mechanism categories defined (`VALUE_MECHANISM_DEFINITIONS`)

---

## PHASE 9: UI/OUTPUT INTEGRATION

### Objective
Display the executive narrative in the UI and enable export in useful formats.

### 9.1 Add Narrative Tab to UI

**Modify**: `app.py`

Add new tab: "Executive Narrative"

```python
with tab_narrative:
    st.header("Executive Narrative")

    # Display each section with proper formatting
    st.subheader("1) Executive Summary")
    for bullet in narrative.executive_summary:
        st.markdown(f"- {bullet}")

    st.subheader("2) How the IT Organization is Built")
    st.markdown(narrative.org_structure)

    # ... etc

    # Export buttons
    col1, col2 = st.columns(2)
    with col1:
        st.download_button("Export Markdown", markdown_content, "narrative.md")
    with col2:
        st.download_button("Export Word", docx_content, "narrative.docx")
```

### 9.2 Citation Display

Preserve and display citations:

```python
def render_with_citations(text: str) -> str:
    """
    Convert citations like (F-CYBER-003) to clickable links
    that scroll to the fact in the inventory tab.
    """
```

### 9.3 Export Formats

| Format | Use Case | Implementation |
|--------|----------|----------------|
| Markdown | Technical review | Direct output |
| Word (.docx) | Client delivery | python-docx library |
| PDF | Final delivery | Via Word or markdown-pdf |
| PowerPoint | IC presentation | python-pptx (stretch) |

### 9.4 L3 Expectations

- [x] Narrative tab displays all sections
- [x] Sections are collapsible/expandable (`st.expander()` for each section)
- [x] Citations are clickable (`render_with_citations()` in `narrative_view.py`)
- [x] Markdown export works (`export_to_markdown()`)
- [x] Word export works with proper formatting (`export_to_word()`)
- [x] Tables render correctly in all formats (markdown tables + card view)

### 9.5 Review Point

**Gate Criteria**:
- [x] Narrative tab added to UI (`tab12` in `app.py`)
- [x] All sections display correctly (6 sections with renderers)
- [x] Export buttons functional (Markdown, Word, JSON)
- [x] Citation linking works (`render_with_citations()` with tooltips)
- [x] Formatting preserved in exports (all export functions tested)

---

## PHASE 10: CALIBRATION & TESTING

### Objective
Validate output quality against executive expectations and iterate until meeting standards.

### 10.1 Create Test Cases

| Test Case | Deal Type | Complexity | Expected Output |
|-----------|-----------|------------|-----------------|
| TC-01 | Acquisition | Simple | Clean synergy-focused narrative |
| TC-02 | Carveout | Complex | Detailed TSA/separation analysis |
| TC-03 | Divestiture | Medium | Clean separation focus |
| TC-04 | Acquisition | Complex (dual ERP) | Extended app story |
| TC-05 | Carveout (no IT) | High | Heavy TSA, build-from-scratch |

### 10.2 Define Quality Rubric

| Dimension | Weight | 5 (Excellent) | 3 (Acceptable) | 1 (Poor) |
|-----------|--------|---------------|----------------|----------|
| M&A Framing | 25% | Every finding connects to lens | Most connect | Few connect |
| Evidence Discipline | 20% | All cited, inferences labeled | Mostly cited | Unsupported claims |
| Actionability | 20% | Specific, executable actions | Generally actionable | Vague |
| Narrative Flow | 15% | Tells coherent story | Readable | Disjointed |
| Completeness | 10% | All sections, all teams | Minor gaps | Major gaps |
| Tone | 10% | Consulting-ready | Acceptable | Academic/fluffy |

### 10.3 Calibration Process

```
For each test case:
1. Run full pipeline
2. Generate narrative
3. Score against rubric
4. Identify gaps
5. Adjust prompts
6. Re-run
7. Repeat until score > 80%
```

### 10.4 User Acceptance Criteria

**Final gate**: User reviews 3 narratives and confirms:
- [ ] "I could hand this to an IC with minimal editing"
- [ ] "The M&A implications are clear and specific"
- [ ] "The risks and synergies are actionable"
- [ ] "The tone is appropriate for client delivery"

### 10.5 L3 Expectations

- [x] All 5 test cases pass with score > 80% (TC-01: 95.4, TC-02: 92.3, TC-03: 85.8, TC-04: 95.4, TC-05: 88.9)
- [x] No critical issues in review (all dimension scores >= 4.0)
- [ ] User accepts 3 sample outputs (pending user review)
- [x] Iteration log documented (outputs saved in `tests/calibration/outputs/`)

### 10.6 Review Point

**Gate Criteria**:
- [x] Test cases defined (`tests/calibration/test_cases.py` - 5 cases)
- [x] Rubric defined (`tests/calibration/quality_rubric.py` - 6 dimensions)
- [x] All test cases passing (5/5 passing with scores 85.8-95.4)
- [ ] User acceptance achieved (pending user review)
- [x] Documentation complete (calibration module fully documented)

---

## EXECUTION SEQUENCE

```
Week 1: Phases 1-2 (Foundation + Reasoning Enhancement)
        ├── Day 1-2: Phase 1 (M&A Framing Foundation)
        └── Day 3-5: Phase 2 (Reasoning Prompt Enhancement)

Week 2: Phases 3-4 (Stories + Synthesis)
        ├── Day 1-2: Phase 3 (Team/Function Stories)
        └── Day 3-5: Phase 4 (Narrative Synthesis Agent)

Week 3: Phases 5-6 (Templates + Review)
        ├── Day 1-2: Phase 5 (Deal-Type Templates)
        └── Day 3-5: Phase 6 (Quality Review Agent)

Week 4: Phases 7-8 (Intelligence + Tables)
        ├── Day 1-2: Phase 7 (Benchmarking)
        └── Day 3-5: Phase 8 (Risk/Synergy Tables)

Week 5: Phases 9-10 (Integration + Testing)
        ├── Day 1-3: Phase 9 (UI/Output)
        └── Day 4-5: Phase 10 (Calibration)

Ongoing: Iteration based on real deal feedback
```

---

## DEPENDENCIES MAP

```
Phase 1 ──► Phase 2 ──► Phase 4
   │           │           │
   │           ▼           ▼
   │       Phase 3 ──► Phase 4
   │                       │
   ▼                       ▼
Phase 7 ◄────────────► Phase 8
                           │
                           ▼
                       Phase 9
                           │
                           ▼
Phase 5 ──► Phase 6 ──► Phase 10
```

---

## SUCCESS METRICS

| Metric | Target | Measurement |
|--------|--------|-------------|
| Narrative completeness | 100% sections | Automated check |
| M&A framing coverage | >90% findings | Automated check |
| Inference labeling | 100% | Automated check |
| User acceptance | 3/3 samples approved | User review |
| Time to narrative | <5 min after analysis | Automated timing |
| Edit time reduction | >50% vs manual | User feedback |

---

## RISK MITIGATION

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Prompts too long | Medium | Token limits | Modularize, use imports |
| Synthesis quality low | Medium | Rework | Iterative prompt tuning |
| UI integration complex | Low | Delay | Phase 9 is independent |
| User expectations misaligned | Medium | Rework | Review examples early |

---

*Document created: 2026-01-19*
*Version: 1.0*
*Status: Ready for execution*
