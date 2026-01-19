# Consistency Fix Plan

## Problem Summary

The system produces inconsistent outputs across runs with the same inputs:

| Issue | Impact | Example |
|-------|--------|---------|
| Headline verdict flips | HIGH | Mid-complexity vs High-complexity |
| Cost range volatility | HIGH | $2.6M-$8.5M vs $3.5M-$10M vs $2.65M-$5.6M |
| Domain counts shift | MEDIUM | 6 facts/3 gaps vs 7 facts/2 gaps |
| Top Risks rotate | MEDIUM | Different "most important" items each run |

## Root Cause

**4 layers of implicit LLM judgment:**
1. Extract facts/gaps/work items (freeform)
2. Count and bucket them (implicit)
3. Map to cost phases (implicit)
4. Decide complexity tier (vibes-based)

If ANY layer is non-deterministic, outputs wobble.

---

## FIX PLAN

### Phase 1: Stable Evidence Layer (CRITICAL)

**Goal:** LLM produces strict JSON, not freeform text. Counts and costs come from DATA, not vibes.

#### 1.1 Evidence Card Schema

```python
@dataclass
class EvidenceCard:
    id: str                    # Hash-based, deterministic
    domain: str                # infrastructure, network, etc.
    type: str                  # fact | gap | risk | work_item
    title: str                 # Normalized title
    description: str
    source_document: str
    source_quote: str          # Exact quote (anchor to truth)
    confidence: str            # high | medium | low
    verified: bool             # Human verified?

    # For risks
    severity: str              # critical | high | medium | low
    severity_score: int        # 4=critical, 3=high, 2=medium, 1=low

    # For work items
    phase: str                 # Day_1 | Day_100 | Post_100
    cost_low: int              # Dollar amount (not range string)
    cost_high: int             # Dollar amount
    owner: str                 # buyer | target | shared
```

#### 1.2 Deduplication Map

Before any counting:
```python
dedupe_map = {
    "canonical_id": ["duplicate_id_1", "duplicate_id_2"]
}
```

Rule: If title similarity > 85% AND same domain → merge to canonical.

#### 1.3 Deterministic Counting

```python
def get_counts(evidence_cards, domain=None):
    cards = [c for c in evidence_cards if c.domain == domain] if domain else evidence_cards
    return {
        "facts": len([c for c in cards if c.type == "fact"]),
        "gaps": len([c for c in cards if c.type == "gap"]),
        "risks": len([c for c in cards if c.type == "risk"]),
        "work_items": len([c for c in cards if c.type == "work_item"])
    }
```

No LLM judgment. Just count the data.

---

### Phase 2: Rule-Based Complexity Scoring

**Goal:** Complexity tier is COMPUTED, not decided by LLM.

#### 2.1 Scoring Rules

```python
def calculate_complexity_score(evidence_cards):
    """
    Returns: (tier, score, breakdown)
    tier: "low" | "mid" | "high" | "critical"
    """
    score = 0
    breakdown = {}

    # Count by severity
    critical_risks = len([c for c in evidence_cards
                         if c.type == "risk" and c.severity == "critical"])
    high_risks = len([c for c in evidence_cards
                     if c.type == "risk" and c.severity == "high"])
    gaps = len([c for c in evidence_cards if c.type == "gap"])

    # Scoring weights
    score += critical_risks * 10
    score += high_risks * 5
    score += gaps * 2

    breakdown = {
        "critical_risks": critical_risks,
        "high_risks": high_risks,
        "gaps": gaps,
        "raw_score": score
    }

    # Tier thresholds (FIXED, not vibes)
    if score >= 50 or critical_risks >= 3:
        tier = "critical"
    elif score >= 30 or critical_risks >= 1 or high_risks >= 5:
        tier = "high"
    elif score >= 15 or high_risks >= 2:
        tier = "mid"
    else:
        tier = "low"

    return tier, score, breakdown
```

#### 2.2 Flag-Based Overrides

Certain findings ALWAYS bump complexity:

```python
COMPLEXITY_FLAGS = {
    "dual_erp": {"pattern": r"dual.*erp|two.*erp|multiple.*erp", "bump": "high"},
    "no_dr": {"pattern": r"no.*disaster.*recovery|missing.*dr", "bump": "high"},
    "identity_gap": {"pattern": r"identity.*governance|iam.*gap", "bump": "mid"},
    "legacy_system": {"pattern": r"end.of.life|eol|unsupported", "bump": "mid"},
}

def check_complexity_flags(evidence_cards):
    flags_triggered = []
    for card in evidence_cards:
        text = f"{card.title} {card.description}".lower()
        for flag_name, flag_config in COMPLEXITY_FLAGS.items():
            if re.search(flag_config["pattern"], text):
                flags_triggered.append((flag_name, flag_config["bump"]))
    return flags_triggered
```

---

### Phase 3: Deterministic Cost Calculation

**Goal:** Costs come from a LOOKUP TABLE, not LLM estimation.

#### 3.1 Cost Table

```python
COST_TABLE = {
    # Work item category -> (low, high) per phase
    "erp_integration": {
        "Day_1": (50000, 150000),
        "Day_100": (200000, 500000),
        "Post_100": (100000, 300000)
    },
    "identity_consolidation": {
        "Day_1": (25000, 75000),
        "Day_100": (100000, 250000),
        "Post_100": (50000, 150000)
    },
    "infrastructure_migration": {
        "Day_1": (25000, 100000),
        "Day_100": (150000, 400000),
        "Post_100": (75000, 200000)
    },
    "security_remediation": {
        "Day_1": (50000, 150000),
        "Day_100": (100000, 300000),
        "Post_100": (50000, 150000)
    },
    "application_rationalization": {
        "Day_1": (10000, 50000),
        "Day_100": (100000, 300000),
        "Post_100": (200000, 500000)
    },
    "default": {
        "Day_1": (25000, 100000),
        "Day_100": (50000, 200000),
        "Post_100": (25000, 100000)
    }
}
```

#### 3.2 Work Item → Category Mapping

```python
def categorize_work_item(work_item):
    """Map work item to cost category based on keywords."""
    title_lower = work_item.title.lower()

    if any(k in title_lower for k in ["erp", "sap", "oracle", "netsuite"]):
        return "erp_integration"
    elif any(k in title_lower for k in ["identity", "iam", "sso", "active directory"]):
        return "identity_consolidation"
    elif any(k in title_lower for k in ["migrate", "infrastructure", "datacenter", "cloud"]):
        return "infrastructure_migration"
    elif any(k in title_lower for k in ["security", "vulnerability", "compliance"]):
        return "security_remediation"
    elif any(k in title_lower for k in ["application", "rationalize", "consolidate"]):
        return "application_rationalization"
    else:
        return "default"
```

#### 3.3 Total Cost Calculation

```python
def calculate_total_costs(work_items):
    totals = {
        "Day_1": {"low": 0, "high": 0},
        "Day_100": {"low": 0, "high": 0},
        "Post_100": {"low": 0, "high": 0}
    }

    for wi in work_items:
        category = categorize_work_item(wi)
        phase = wi.phase
        costs = COST_TABLE.get(category, COST_TABLE["default"])
        phase_costs = costs.get(phase, costs["Day_100"])

        totals[phase]["low"] += phase_costs[0]
        totals[phase]["high"] += phase_costs[1]

    grand_total = {
        "low": sum(t["low"] for t in totals.values()),
        "high": sum(t["high"] for t in totals.values())
    }

    return totals, grand_total
```

---

### Phase 4: Stable Top Risks Selection

**Goal:** "Top Risks" are selected by SCORE, not LLM preference.

#### 4.1 Risk Scoring

```python
def score_risk(risk, evidence_cards):
    """
    Score a risk deterministically.
    Higher score = more important = more likely to be "Top Risk"
    """
    score = 0

    # Base severity score
    severity_scores = {"critical": 100, "high": 75, "medium": 50, "low": 25}
    score += severity_scores.get(risk.severity, 50)

    # Evidence strength (more citations = stronger)
    citation_count = len(risk.based_on_facts)
    score += citation_count * 10

    # Verified citations boost
    verified_citations = sum(1 for fid in risk.based_on_facts
                            if any(c.id == fid and c.verified for c in evidence_cards))
    score += verified_citations * 15

    # Integration-dependent risks get boost (PE cares about these)
    if risk.integration_dependent:
        score += 20

    # Domain priority boost
    domain_priority = {
        "cybersecurity": 15,
        "infrastructure": 10,
        "applications": 10,
        "organization": 5
    }
    score += domain_priority.get(risk.domain, 0)

    return score

def get_top_risks(risks, evidence_cards, n=5):
    """Get top N risks by deterministic score."""
    scored = [(r, score_risk(r, evidence_cards)) for r in risks]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [r for r, s in scored[:n]]
```

---

### Phase 5: HTML Report Improvements

#### 5.1 Deal Readout (1-page summary)

```html
<div class="deal-readout">
    <h1>Deal Readout: {company_name}</h1>

    <div class="verdict-box">
        <span class="complexity-badge {tier}">{tier}-COMPLEXITY</span>
        <span class="cost-range">${total_low}M - ${total_high}M</span>
    </div>

    <div class="key-metrics">
        <div class="metric">
            <span class="label">Day 1 Items</span>
            <span class="value">{day1_count}</span>
        </div>
        <div class="metric">
            <span class="label">TSA Flags</span>
            <span class="value">{tsa_count}</span>
        </div>
        <div class="metric">
            <span class="label">Critical Risks</span>
            <span class="value">{critical_risk_count}</span>
        </div>
        <div class="metric">
            <span class="label">Info Gaps</span>
            <span class="value">{gap_count}</span>
        </div>
    </div>

    <div class="top-risks">
        <h3>Top 5 Risks</h3>
        <!-- Deterministically selected, not LLM-chosen -->
    </div>

    <div class="confidence-meter">
        <h3>Data Confidence</h3>
        <div class="meter" style="width: {confidence_pct}%"></div>
        <span>{verified_facts}/{total_facts} facts verified</span>
    </div>
</div>
```

#### 5.2 Infrastructure Inventory Panel

```html
<div class="inventory-panel">
    <h3>Infrastructure Inventory</h3>
    <table>
        <tr><th>Category</th><th>Item</th><th>Status</th><th>Source</th></tr>
        <tr><td>Compute</td><td>{compute_items}</td><td>✓</td><td>Doc 1</td></tr>
        <tr><td>Storage</td><td>{storage_items}</td><td>✓</td><td>Doc 2</td></tr>
        <tr><td>Network</td><td>{network_items}</td><td>✓</td><td>Doc 1</td></tr>
        <tr><td>EUC</td><td>???</td><td class="missing">MISSING</td><td>-</td></tr>
        <tr><td>DR/Backup</td><td>{dr_items}</td><td>⚠️</td><td>Doc 3</td></tr>
        <tr><td>Monitoring</td><td>???</td><td class="missing">MISSING</td><td>-</td></tr>
    </table>
</div>
```

#### 5.3 Confidence Meter

```python
def calculate_confidence(fact_store, reasoning_store):
    """Calculate overall data confidence."""
    stats = fact_store.get_verification_stats()

    # Factors
    verification_rate = stats["verification_rate"]
    source_coverage = len(fact_store.get_source_documents()) / expected_sources
    gap_penalty = min(len(fact_store.gaps) * 0.05, 0.3)  # Max 30% penalty

    confidence = (verification_rate * 0.5 + source_coverage * 0.3) - gap_penalty
    confidence = max(0, min(1, confidence))  # Clamp 0-1

    return {
        "score": confidence,
        "label": "High" if confidence > 0.7 else "Medium" if confidence > 0.4 else "Low",
        "factors": {
            "verified_facts": f"{stats['verified_count']}/{stats['total_facts']}",
            "source_documents": len(fact_store.get_source_documents()),
            "gaps": len(fact_store.gaps)
        }
    }
```

---

## Implementation Order

### Sprint 1: Core Consistency (NOW)
1. ✅ Hash-based IDs (DONE)
2. ✅ Verification system (DONE)
3. ⬜ Rule-based complexity scorer (BUILD THIS)
4. ⬜ Deterministic cost table (BUILD THIS)
5. ⬜ Stable top risks selection (BUILD THIS)

### Sprint 2: Report Improvements
6. ⬜ Deal Readout 1-pager
7. ⬜ Infrastructure Inventory panel
8. ⬜ Confidence meter
9. ⬜ Better org visualization (STARTED)

### Sprint 3: Polish
10. ⬜ Deduplication at extraction time
11. ⬜ Source traceability improvements
12. ⬜ Print-friendly CSS

---

## Success Metrics

After implementation, running the same inputs 5 times should produce:

| Metric | Target |
|--------|--------|
| Complexity tier | IDENTICAL across all runs |
| Total cost range | Within 5% variance |
| Top 5 risks | Same 5 items (order may vary) |
| Fact/gap/risk counts | IDENTICAL |
| Domain mini-metrics | IDENTICAL |

---

## Files to Create/Modify

1. `tools_v2/consistency_engine.py` - NEW: Rule-based scoring + costs
2. `tools_v2/cost_calculator.py` - MODIFY: Use lookup table
3. `tools_v2/complexity_scorer.py` - MODIFY: Use rules not vibes
4. `report_generator.py` - MODIFY: Use deterministic selections
5. `ui/deal_readout.py` - NEW: 1-page summary view
6. `ui/inventory_panel.py` - NEW: Infrastructure inventory
7. `templates/report_template.html` - MODIFY: Add new sections
