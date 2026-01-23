# Fact Pattern Improvement Plan

## Overview

A 5-phase approach to evolving from "tool sightings" to "operational truth" in the Fact Store, enabling better downstream reasoning for M&A analysis.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         FACT PATTERN EVOLUTION                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   PHASE 1          PHASE 2          PHASE 3          PHASE 4          PHASE 5  │
│   Schema           Discovery        Gap              Asset            QA        │
│   Foundation       Enhancement      Intelligence     Rollups          Integration│
│                                                                                 │
│   ┌─────────┐      ┌─────────┐      ┌─────────┐      ┌─────────┐      ┌─────────┐
│   │ Enrich  │      │ Capture │      │ Detect  │      │ Generate│      │ Validate│
│   │ Fact    │─────▶│ Better  │─────▶│ Overlaps│─────▶│ Summary │─────▶│ Quality │
│   │ Schema  │      │ Data    │      │ & Gaps  │      │ Views   │      │ Gates   │
│   └─────────┘      └─────────┘      └─────────┘      └─────────┘      └─────────┘
│                                                                                 │
│   Week 1           Week 2           Week 3           Week 4           Week 5    │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Schema Foundation

**Goal:** Enrich the Fact and Gap schemas with M&A-relevant fields

**Duration:** ~1 week

### 1.1 Fact Schema Additions

```python
@dataclass
class Fact:
    # === EXISTING FIELDS ===
    fact_id: str              # "F-INFRA-001"
    domain: str               # "infrastructure"
    category: str             # "cloud"
    item: str                 # "AWS is primary cloud provider"
    details: dict             # {"provider": "AWS", "regions": ["us-east-1"]}
    status: str               # "documented", "inferred", "unclear"
    evidence: dict            # {exact_quote, source_section}
    entity: str               # "target" or "buyer"

    # === NEW: OPERATIONAL CONTEXT ===
    role: str = "unknown"
    # "primary" - main system for this function
    # "secondary" - backup or supplementary
    # "legacy" - being phased out
    # "unknown" - not determinable from docs

    scope: str = "unknown"
    # "enterprise" - covers whole organization
    # "business_unit" - specific BU only
    # "department" - single team
    # "unknown" - not determinable

    # === NEW: M&A RELEVANCE ===
    parent_dependency: str = "unknown"
    # "yes" - depends on or shared with parent
    # "no" - standalone/target-owned
    # "unknown" - not determinable

    tsa_candidate: str = "unknown"
    # "yes" - likely needs TSA if parent-dependent
    # "no" - can be cut over independently
    # "unknown" - need more info

    day1_critical: str = "unknown"
    # "yes" - must work on Day 1 (auth, email, etc.)
    # "no" - can migrate post-close
    # "unknown" - need more info

    # === NEW: RELATIONSHIPS ===
    related_facts: List[str] = field(default_factory=list)
    # IDs of facts that overlap, conflict, or complement this one
    # e.g., ["F-CYBER-002"] if two SIEM tools identified

    relationship_type: str = ""
    # "overlaps" - similar capability, unclear which is primary
    # "conflicts" - contradictory information
    # "complements" - works together with related fact
    # "" - no relationship
```

### 1.2 Gap Schema Additions

```python
@dataclass
class Gap:
    # === EXISTING FIELDS ===
    gap_id: str               # "G-SEC-001"
    domain: str
    category: str
    description: str
    importance: str           # "critical", "high", "medium", "low"

    # === NEW: GAP CLASSIFICATION ===
    gap_type: str = "missing_info"
    # "missing_info" - information not in docs (traditional gap)
    # "overlap" - two systems/tools, unclear which is primary
    # "conflict" - contradictory information in docs
    # "coverage_unknown" - system exists but coverage unclear
    # "ownership_unknown" - system exists but who owns/operates unclear

    # === NEW: RELATED FACTS ===
    related_facts: List[str] = field(default_factory=list)
    # Facts involved in this gap (especially for overlap/conflict)

    # === NEW: RESOLUTION GUIDANCE ===
    resolution_action: str = ""
    # Specific action to resolve: "Request SOC 2 report from target"
    # "Confirm with IT which SIEM is authoritative"

    hypothesis: str = ""
    # Best guess if we had to assume: "Likely BU-specific deployment"
    # Helps reasoning proceed while flagging uncertainty
```

### 1.3 Deliverables

- [ ] Updated `fact_store.py` with new Fact fields
- [ ] Updated `fact_store.py` with new Gap fields
- [ ] Migration script for existing data (default new fields to "unknown")
- [ ] Updated database schema in `database.py`
- [ ] Unit tests for new fields

---

## Phase 2: Discovery Enhancement

**Goal:** Update discovery agents to capture the new fields

**Duration:** ~1 week

### 2.1 Discovery Prompt Updates

Add to each domain's discovery prompt:

```markdown
## Extraction Requirements

For each system, tool, or capability you identify, also determine:

### Operational Context
- **Role**: Is this the PRIMARY system for its function, or SECONDARY/LEGACY?
  - Look for language like "main", "primary", "backup", "being replaced"
  - If multiple tools serve same function, try to determine which is authoritative
  - Mark "unknown" if not determinable

- **Scope**: Does this cover the ENTERPRISE or just a BUSINESS UNIT/DEPARTMENT?
  - Look for language like "company-wide", "all employees", "sales team only"
  - Mark "unknown" if not determinable

### M&A Relevance
- **Parent Dependency**: Is this SHARED WITH or DEPENDENT ON a parent company?
  - Look for: "parent's", "corporate", "shared service", "provided by"
  - Critical for carveout deals
  - Mark "unknown" if not determinable

- **TSA Candidate**: If parent-dependent, will this likely need a Transition Services Agreement?
  - Services that can't be replicated quickly = TSA candidate
  - Mark "unknown" if not determinable

- **Day 1 Critical**: Must this work on Day 1 of separation?
  - Authentication, email, core business apps = typically Day 1
  - Mark "unknown" if not determinable

### Relationships
- **Overlapping Tools**: If you identify multiple tools serving similar functions:
  - Note both in separate facts
  - Link them via related_facts field
  - Create a Gap flagging the overlap

## Example: Detecting Overlap

If document mentions both "Splunk for security monitoring" and "Elastic SIEM deployment":

Fact 1:
  fact_id: F-CYBER-001
  item: "Splunk ES for security monitoring"
  role: unknown  # can't determine primary vs secondary
  related_facts: [F-CYBER-002]
  relationship_type: overlaps

Fact 2:
  fact_id: F-CYBER-002
  item: "Elastic SIEM deployment"
  role: unknown
  related_facts: [F-CYBER-001]
  relationship_type: overlaps

Gap:
  gap_id: G-CYBER-001
  description: "Two SIEM platforms identified (Splunk, Elastic) - unclear which is primary"
  gap_type: overlap
  related_facts: [F-CYBER-001, F-CYBER-002]
  importance: high
  resolution_action: "Confirm with target security team which SIEM is authoritative for alerting"
```

### 2.2 Domain-Specific Guidance

Create guidance for common overlaps per domain:

| Domain | Common Overlaps to Detect |
|--------|--------------------------|
| Cybersecurity | Multiple SIEM, multiple EDR, overlapping security tools |
| Infrastructure | Multiple cloud providers, hybrid on-prem + cloud |
| Identity | Multiple directories (AD + Entra + Okta), SSO overlap |
| Applications | Multiple ERP instances, overlapping CRM tools |
| Network | Multiple VPN solutions, overlapping SD-WAN |

### 2.3 Deliverables

- [ ] Updated discovery prompts for all 6 domains
- [ ] Domain-specific overlap detection guidance
- [ ] Updated discovery agent output parsing
- [ ] Test cases with documents containing overlaps
- [ ] Validation that new fields are populated

---

## Phase 3: Gap Intelligence

**Goal:** Make gaps actionable and relationship-aware

**Duration:** ~1 week

### 3.1 Overlap Detection Rules

Post-processing to catch overlaps discovery might miss:

```python
def detect_overlaps(facts: List[Fact]) -> List[Gap]:
    """
    Analyze facts to detect potential overlaps not caught by discovery.
    """
    overlaps = []

    # Group facts by domain + category
    by_category = group_by(facts, key=lambda f: (f.domain, f.category))

    for (domain, category), category_facts in by_category.items():
        # If multiple facts in same category, check for overlap signals
        if len(category_facts) > 1:
            # Check if any are marked as primary
            primaries = [f for f in category_facts if f.role == "primary"]
            unknowns = [f for f in category_facts if f.role == "unknown"]

            # Multiple unknowns in same category = potential overlap
            if len(unknowns) > 1:
                overlaps.append(Gap(
                    gap_id=generate_gap_id(domain),
                    domain=domain,
                    category=category,
                    description=f"Multiple {category} tools identified - unclear which is primary",
                    importance="high",
                    gap_type="overlap",
                    related_facts=[f.fact_id for f in unknowns],
                    resolution_action=f"Confirm primary {category} system with target"
                ))

    return overlaps
```

### 3.2 Gap Enrichment Rules

Automatically enrich gaps with resolution guidance:

```python
RESOLUTION_TEMPLATES = {
    "overlap": {
        "siem": "Confirm with security team which SIEM is authoritative for alerting",
        "edr": "Confirm endpoint coverage split between tools",
        "identity": "Confirm which directory is source of truth for user provisioning",
        "cloud": "Confirm primary vs secondary cloud strategy",
    },
    "missing_info": {
        "compliance": "Request compliance certifications (SOC 2, ISO 27001, etc.)",
        "dr": "Request DR/BC documentation and RTO/RPO targets",
        "contracts": "Request vendor contract list with renewal dates",
    },
    "coverage_unknown": {
        "endpoint": "Request endpoint inventory with coverage percentages",
        "network": "Request network diagram with site connectivity",
        "identity": "Request user count by directory/IdP",
    }
}

def enrich_gap(gap: Gap) -> Gap:
    """Add resolution guidance based on gap type and category."""
    templates = RESOLUTION_TEMPLATES.get(gap.gap_type, {})
    if gap.category in templates and not gap.resolution_action:
        gap.resolution_action = templates[gap.category]
    return gap
```

### 3.3 Conflict Detection

Detect when facts contradict each other:

```python
def detect_conflicts(facts: List[Fact]) -> List[Gap]:
    """
    Detect contradictory information in facts.
    """
    conflicts = []

    # Example: Different user counts mentioned
    user_counts = [f for f in facts if "user" in f.item.lower() and any(c.isdigit() for c in f.item)]
    if len(set(extract_numbers(f.item) for f in user_counts)) > 1:
        conflicts.append(Gap(
            gap_id=generate_gap_id("general"),
            domain="organization",
            category="scope",
            description="Conflicting user counts in documentation",
            importance="high",
            gap_type="conflict",
            related_facts=[f.fact_id for f in user_counts],
            resolution_action="Confirm actual user count with target"
        ))

    return conflicts
```

### 3.4 Deliverables

- [ ] `gap_intelligence.py` module with detection rules
- [ ] Overlap detection for all domains
- [ ] Conflict detection rules
- [ ] Resolution guidance templates
- [ ] Integration into discovery pipeline
- [ ] Test cases for overlap/conflict scenarios

---

## Phase 4: Asset Rollups

**Goal:** Generate summary views for reporting and reasoning

**Duration:** ~1 week

### 4.1 Asset Summary Generator

```python
@dataclass
class AssetSummary:
    """
    Rolled-up view of an asset category for reporting.
    Generated at report time, not stored.
    """
    domain: str
    category: str

    # Tools/systems in this category
    primary_system: Optional[str]        # The main tool if known
    secondary_systems: List[str]         # Backup/supplementary tools
    legacy_systems: List[str]            # Being phased out
    unknown_role_systems: List[str]      # Role not determined

    # Coverage assessment
    coverage_known: bool
    coverage_summary: str                # "Enterprise-wide" or "Unknown - BU split possible"

    # M&A implications
    parent_dependencies: List[str]       # Facts flagged as parent-dependent
    tsa_candidates: List[str]            # Likely TSA items
    day1_critical_items: List[str]       # Must work Day 1

    # Open questions
    overlaps: List[str]                  # Gap IDs for overlaps
    conflicts: List[str]                 # Gap IDs for conflicts
    missing_info: List[str]              # Gap IDs for missing info

    # Confidence
    confidence_score: float              # 0-1 based on unknowns
    confidence_factors: List[str]        # What's driving confidence up/down


def generate_asset_summary(
    facts: List[Fact],
    gaps: List[Gap],
    domain: str,
    category: str
) -> AssetSummary:
    """
    Generate a summary view for an asset category.
    """
    category_facts = [f for f in facts if f.domain == domain and f.category == category]
    category_gaps = [g for g in gaps if g.domain == domain and g.category == category]

    # Classify systems by role
    primary = [f.item for f in category_facts if f.role == "primary"]
    secondary = [f.item for f in category_facts if f.role == "secondary"]
    legacy = [f.item for f in category_facts if f.role == "legacy"]
    unknown = [f.item for f in category_facts if f.role == "unknown"]

    # M&A implications
    parent_deps = [f.item for f in category_facts if f.parent_dependency == "yes"]
    tsa = [f.item for f in category_facts if f.tsa_candidate == "yes"]
    day1 = [f.item for f in category_facts if f.day1_critical == "yes"]

    # Gaps by type
    overlaps = [g.gap_id for g in category_gaps if g.gap_type == "overlap"]
    conflicts = [g.gap_id for g in category_gaps if g.gap_type == "conflict"]
    missing = [g.gap_id for g in category_gaps if g.gap_type == "missing_info"]

    # Calculate confidence
    total_facts = len(category_facts)
    unknown_count = len(unknown) + len([f for f in category_facts if f.scope == "unknown"])
    confidence = 1.0 - (unknown_count / max(total_facts * 2, 1))

    confidence_factors = []
    if len(primary) == 0 and len(unknown) > 1:
        confidence_factors.append("Multiple systems, none confirmed as primary")
    if len(overlaps) > 0:
        confidence_factors.append(f"{len(overlaps)} unresolved overlaps")
    if len(parent_deps) > 0:
        confidence_factors.append(f"{len(parent_deps)} parent dependencies identified")

    return AssetSummary(
        domain=domain,
        category=category,
        primary_system=primary[0] if primary else None,
        secondary_systems=secondary,
        legacy_systems=legacy,
        unknown_role_systems=unknown,
        coverage_known=any(f.scope != "unknown" for f in category_facts),
        coverage_summary=_summarize_coverage(category_facts),
        parent_dependencies=parent_deps,
        tsa_candidates=tsa,
        day1_critical_items=day1,
        overlaps=overlaps,
        conflicts=conflicts,
        missing_info=missing,
        confidence_score=confidence,
        confidence_factors=confidence_factors
    )
```

### 4.2 Domain Summary View

Roll up all categories in a domain:

```python
def generate_domain_summary(
    facts: List[Fact],
    gaps: List[Gap],
    domain: str
) -> Dict:
    """
    Generate summary for an entire domain.
    """
    domain_facts = [f for f in facts if f.domain == domain]
    domain_gaps = [g for g in gaps if g.domain == domain]

    # Get unique categories
    categories = set(f.category for f in domain_facts)

    # Generate summary for each category
    category_summaries = [
        generate_asset_summary(facts, gaps, domain, cat)
        for cat in categories
    ]

    # Domain-level stats
    total_parent_deps = sum(len(s.parent_dependencies) for s in category_summaries)
    total_overlaps = sum(len(s.overlaps) for s in category_summaries)
    avg_confidence = sum(s.confidence_score for s in category_summaries) / max(len(category_summaries), 1)

    return {
        "domain": domain,
        "categories": category_summaries,
        "stats": {
            "total_facts": len(domain_facts),
            "total_gaps": len(domain_gaps),
            "parent_dependencies": total_parent_deps,
            "unresolved_overlaps": total_overlaps,
            "average_confidence": avg_confidence
        },
        "key_concerns": _identify_key_concerns(category_summaries)
    }
```

### 4.3 Integration with Deal Readout

Update Deal Readout to show asset summaries:

```python
def render_asset_inventory(facts: List[Fact], gaps: List[Gap]):
    """Render asset summaries in the Deal Readout."""

    st.markdown("### Asset Inventory")

    for domain in DOMAINS:
        summary = generate_domain_summary(facts, gaps, domain)

        with st.expander(f"{domain.title()} ({summary['stats']['total_facts']} items)"):
            # Show confidence meter
            conf = summary['stats']['average_confidence']
            st.progress(conf, text=f"Confidence: {conf:.0%}")

            # Show categories
            for cat_summary in summary['categories']:
                st.markdown(f"**{cat_summary.category.title()}**")

                if cat_summary.primary_system:
                    st.markdown(f"- Primary: {cat_summary.primary_system}")
                if cat_summary.unknown_role_systems:
                    st.warning(f"⚠️ Unclear primary: {', '.join(cat_summary.unknown_role_systems)}")
                if cat_summary.parent_dependencies:
                    st.info(f"🔗 Parent dependencies: {', '.join(cat_summary.parent_dependencies)}")
```

### 4.4 Deliverables

- [ ] `asset_summary.py` module with generators
- [ ] AssetSummary dataclass
- [ ] Domain summary generator
- [ ] Integration with Deal Readout UI
- [ ] Confidence scoring logic
- [ ] Test cases for summary generation

---

## Phase 5: QA Integration

**Goal:** Use enriched data for quality validation

**Duration:** ~1 week

### 5.1 Quality Rules Engine

```python
@dataclass
class QualityCheck:
    check_id: str
    name: str
    severity: str           # "error", "warning", "info"
    passed: bool
    message: str
    affected_items: List[str]


def run_quality_checks(
    facts: List[Fact],
    gaps: List[Gap],
    deal_type: str
) -> List[QualityCheck]:
    """
    Run quality checks on enriched facts and gaps.
    """
    checks = []

    # CHECK 1: Carveout without parent dependency assessment
    if deal_type == "carveout":
        parent_unknown = [f for f in facts if f.parent_dependency == "unknown"]
        if len(parent_unknown) > len(facts) * 0.5:
            checks.append(QualityCheck(
                check_id="QC-001",
                name="Parent Dependency Assessment",
                severity="warning",
                passed=False,
                message=f"{len(parent_unknown)} of {len(facts)} facts have unknown parent dependency status. For carveouts, this should be assessed.",
                affected_items=[f.fact_id for f in parent_unknown[:5]]
            ))

    # CHECK 2: Unresolved overlaps
    overlap_gaps = [g for g in gaps if g.gap_type == "overlap"]
    if overlap_gaps:
        checks.append(QualityCheck(
            check_id="QC-002",
            name="System Overlaps",
            severity="warning",
            passed=False,
            message=f"{len(overlap_gaps)} potential system overlaps detected. Primary systems should be confirmed.",
            affected_items=[g.gap_id for g in overlap_gaps]
        ))

    # CHECK 3: Day 1 critical items without TSA assessment
    day1_items = [f for f in facts if f.day1_critical == "yes"]
    day1_no_tsa = [f for f in day1_items if f.parent_dependency == "yes" and f.tsa_candidate == "unknown"]
    if day1_no_tsa:
        checks.append(QualityCheck(
            check_id="QC-003",
            name="Day 1 TSA Assessment",
            severity="error",
            passed=False,
            message=f"{len(day1_no_tsa)} Day 1 critical items are parent-dependent but TSA candidacy not assessed.",
            affected_items=[f.fact_id for f in day1_no_tsa]
        ))

    # CHECK 4: Low confidence domains
    for domain in DOMAINS:
        domain_summary = generate_domain_summary(facts, gaps, domain)
        if domain_summary['stats']['average_confidence'] < 0.5:
            checks.append(QualityCheck(
                check_id=f"QC-CONF-{domain.upper()}",
                name=f"{domain.title()} Confidence",
                severity="warning",
                passed=False,
                message=f"{domain.title()} domain has low confidence ({domain_summary['stats']['average_confidence']:.0%}). Consider additional discovery.",
                affected_items=[]
            ))

    return checks
```

### 5.2 QA Dashboard in UI

```python
def render_qa_dashboard(facts: List[Fact], gaps: List[Gap], deal_type: str):
    """Render QA checks in the UI."""

    st.markdown("### Quality Assurance")

    checks = run_quality_checks(facts, gaps, deal_type)

    errors = [c for c in checks if c.severity == "error" and not c.passed]
    warnings = [c for c in checks if c.severity == "warning" and not c.passed]
    passed = [c for c in checks if c.passed]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Errors", len(errors), delta=None)
    with col2:
        st.metric("Warnings", len(warnings), delta=None)
    with col3:
        st.metric("Passed", len(passed), delta=None)

    if errors:
        st.error("**Errors (must resolve):**")
        for check in errors:
            st.markdown(f"- **{check.name}**: {check.message}")

    if warnings:
        st.warning("**Warnings (should review):**")
        for check in warnings:
            st.markdown(f"- **{check.name}**: {check.message}")
```

### 5.3 Stage 1 Reasoning Enhancement

Update Stage 1 (LLM interprets facts) to use enriched data:

```python
STAGE1_PROMPT_ADDITION = """
## Enriched Fact Context

The facts below include operational context:
- **role**: primary/secondary/legacy/unknown
- **parent_dependency**: whether shared with parent company
- **day1_critical**: whether must work on Day 1

When identifying considerations:
1. Pay special attention to facts with parent_dependency="yes" - these need separation planning
2. Facts with day1_critical="yes" are higher priority
3. Facts with role="unknown" in overlapping categories indicate uncertainty - flag as open questions
4. Use the gap_type to understand what kind of information is missing

Do not hallucinate specifics (coverage %, user counts) if marked as "unknown" in the facts.
"""
```

### 5.4 Deliverables

- [ ] `quality_checks.py` module with rules engine
- [ ] QA dashboard component in UI
- [ ] Integration with Deal Readout
- [ ] Stage 1 prompt updates for enriched context
- [ ] Test cases for quality checks
- [ ] Documentation of all quality rules

---

## Implementation Timeline

```
Week 1: Phase 1 - Schema Foundation
├── Day 1-2: Update Fact dataclass
├── Day 3-4: Update Gap dataclass
├── Day 5: Database migration + tests

Week 2: Phase 2 - Discovery Enhancement
├── Day 1-2: Update discovery prompts (all 6 domains)
├── Day 3-4: Update output parsing
├── Day 5: Test with sample documents

Week 3: Phase 3 - Gap Intelligence
├── Day 1-2: Overlap detection rules
├── Day 3-4: Conflict detection + resolution templates
├── Day 5: Integration + tests

Week 4: Phase 4 - Asset Rollups
├── Day 1-2: AssetSummary generator
├── Day 3-4: Domain summary + UI integration
├── Day 5: Deal Readout updates

Week 5: Phase 5 - QA Integration
├── Day 1-2: Quality rules engine
├── Day 3-4: QA dashboard + Stage 1 updates
├── Day 5: Final testing + documentation
```

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Facts with role identified | ~0% | >60% |
| Facts with parent_dependency assessed | ~0% | >80% (for carveouts) |
| Overlaps explicitly flagged | ~0% | 100% |
| Gaps with resolution guidance | ~20% | >90% |
| Average domain confidence score | N/A | >70% |
| QA checks passing | N/A | >80% |

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Discovery prompts get too long | Test token usage; split into focused sub-prompts if needed |
| Too many "unknown" values | Acceptable initially; track and improve over time |
| Schema changes break existing data | Migration script with defaults; backward compatible |
| Quality checks too strict | Start with warnings, promote to errors after tuning |
| Performance impact | Asset summaries generated on-demand, not stored |
