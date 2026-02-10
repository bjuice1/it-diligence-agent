# Fix Plan: Entity Separation & Data Quality

## Problem Summary

GPT Review Score: **4.5-6/10** - "Usable shell but too many data integrity issues to trust"

### Critical Issues Identified

| Issue | Impact | Root Cause |
|-------|--------|------------|
| Target/Buyer data mixing | Fatal - readers can't tell which company | Dossier indexes by `domain:item` without entity |
| Internal contradictions | Destroys trust | Same-name items merged across entities |
| No entity label in output | Can't identify source | HTML renderer doesn't show entity field |
| not_stated = dead attribute | Useless for DD | No promotion to Gap items |
| Source evidence unauditable | Can't verify claims | Only shows filename, no section/line |
| Green = false confidence | Misleading | Based only on risk count, not evidence quality |
| Duplicate app rows | Wrong cost analysis | First-value-wins, no conflict detection |

---

## Phase 1: Entity-Aware Dossier Indexing (CRITICAL)

### File: `services/inventory_dossier.py`

**Problem:** Line 176 creates item key without entity
```python
# BROKEN
item_key = f"{domain}:{item.lower()}"
```

**Fix 1.1: Change item key to include entity**
```python
# Line 176 - _index_facts()
entity = fact.get('entity', 'target')
item_key = f"{entity}:{domain}:{item.lower()}"
```

**Fix 1.2: Update build_dossier() to use entity-aware key**
```python
# Line 373 - build_dossier()
def build_dossier(self, item_name: str, domain: str, entity: str = "target") -> Optional[ItemDossier]:
    item_key = f"{entity}:{domain}:{item_name.lower()}"
    item_facts = self.facts_by_item.get(item_key, [])
```

**Fix 1.3: Update build_domain_dossiers() to build separate Target/Buyer dossiers**
```python
# Line 494 - build_domain_dossiers()
def build_domain_dossiers(self, domain: str, entity: str = None) -> List[ItemDossier]:
    """
    Build dossiers for all items in a domain.

    Args:
        domain: Domain to process
        entity: If None, build for both entities separately
    """
    dossiers = []
    domain_facts = self.facts_by_domain.get(domain, [])

    # Filter by entity if specified
    if entity:
        domain_facts = [f for f in domain_facts if f.get('entity', 'target') == entity]

    # Get unique item names WITH entity
    item_keys = set()
    for fact in domain_facts:
        item = fact.get('item', '').strip()
        fact_entity = fact.get('entity', 'target')
        if item:
            item_keys.add((fact_entity, item))

    # Build dossier for each unique entity:item
    for item_entity, item_name in sorted(item_keys):
        dossier = self.build_dossier(item_name, domain, entity=item_entity)
        if dossier:
            dossiers.append(dossier)

    return dossiers
```

---

## Phase 2: Entity Badge in HTML Output

### File: `services/inventory_dossier.py`

**Problem:** Dossier header shows name but no entity indicator

**Fix 2.1: Add entity badge CSS (after line 920)**
```css
.entity-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 3px;
    font-size: 0.75em;
    font-weight: 600;
    text-transform: uppercase;
    margin-right: 10px;
}
.entity-badge.target { background: #007bff; color: white; }
.entity-badge.buyer { background: #6f42c1; color: white; }
```

**Fix 2.2: Add entity badge to dossier header (line 988)**
```python
# Before:
<h3>{dossier.name}</h3>

# After:
<h3>
    <span class="entity-badge {dossier.entity}">{dossier.entity.upper()}</span>
    {dossier.name}
</h3>
```

**Fix 2.3: Add entity to data attribute for filtering**
```python
# Line 986
<div class="dossier" data-status="{dossier.overall_status}" data-entity="{dossier.entity}">
```

**Fix 2.4: Add entity filter buttons (after line 946)**
```python
<button class="filter-btn" onclick="filterByEntity('target')">🎯 Target Only</button>
<button class="filter-btn" onclick="filterByEntity('buyer')">🏢 Buyer Only</button>
```

---

## Phase 3: Source Evidence Traceability

### File: `services/inventory_dossier.py`

**Problem:** Evidence shows only filename ("— document.pdf")

**Fix 3.1: Update SourceEvidence dataclass (line 31)**
```python
@dataclass
class SourceEvidence:
    """Evidence from source documents."""
    quote: str
    source_document: str
    source_section: str = ""
    source_page: str = ""      # NEW
    source_line: str = ""      # NEW
    fact_id: str = ""

    def format_citation(self) -> str:
        """Format as auditable citation."""
        parts = [self.source_document]
        if self.source_section:
            parts.append(f"§{self.source_section}")
        if self.source_page:
            parts.append(f"p.{self.source_page}")
        return " | ".join(parts)
```

**Fix 3.2: Update evidence extraction (line 402-408)**
```python
evidence = fact.get('evidence', {})
if isinstance(evidence, dict) and evidence.get('exact_quote'):
    dossier.evidence.append(SourceEvidence(
        quote=evidence['exact_quote'],
        source_document=fact.get('source_document', ''),
        source_section=evidence.get('source_section', ''),
        source_page=evidence.get('page_number', evidence.get('page', '')),
        source_line=evidence.get('line_number', ''),
        fact_id=fact_id
    ))
```

**Fix 3.3: Update HTML rendering (line 956)**
```python
# Before:
evidence_html += f'...<div class="source">— {source}</div></div>'

# After:
citation = ev.format_citation() if hasattr(ev, 'format_citation') else ev.source_document
evidence_html += f'''
<div class="evidence">
    "{quote[:250]}{"..." if len(quote) > 250 else ""}"
    <div class="source">
        <span class="fact-id">[{ev.fact_id}]</span> — {citation}
    </div>
</div>'''
```

---

## Phase 4: Promote not_stated to Gaps

### File: `services/inventory_dossier.py`

**Problem:** `not_stated` attributes sit as dead data

**Fix 4.1: Add gap generation in build_dossier() (after line 423)**
```python
# After extracting attributes, check for critical missing fields
CRITICAL_FIELDS = {
    'applications': ['user_count', 'vendor', 'version', 'criticality', 'annual_cost'],
    'infrastructure': ['location', 'capacity', 'age', 'annual_cost'],
    'cybersecurity': ['coverage', 'deployment_scope', 'last_assessment'],
    'identity_access': ['user_count', 'mfa_coverage', 'sso_enabled'],
    'network': ['bandwidth', 'redundancy', 'vendor'],
    'organization': ['headcount', 'reporting_to', 'tenure'],
}

missing_critical = []
domain_critical = CRITICAL_FIELDS.get(domain, [])
for field in domain_critical:
    value = dossier.attributes.get(field)
    if not value or value in ['not_stated', 'not_specified', 'unknown', 'N/A']:
        missing_critical.append(field)

if missing_critical:
    dossier.data_gaps = missing_critical  # NEW field
    dossier.data_completeness = 1 - (len(missing_critical) / len(domain_critical))
```

**Fix 4.2: Add data_gaps field to ItemDossier (after line 108)**
```python
# Data completeness tracking
data_gaps: List[str] = field(default_factory=list)  # Missing critical fields
data_completeness: float = 1.0  # 0.0 to 1.0
```

**Fix 4.3: Display data gaps in HTML (add section after line 1005)**
```python
# Add data gaps section
gaps_html = ""
if dossier.data_gaps:
    gaps_html = f'''
    <div class="section data-gaps">
        <h4>⚠️ Data Gaps ({len(dossier.data_gaps)} missing)</h4>
        <ul class="gap-list">
            {''.join(f'<li>{g.replace("_", " ").title()}</li>' for g in dossier.data_gaps)}
        </ul>
        <p class="completeness">Data completeness: {dossier.data_completeness:.0%}</p>
    </div>'''
```

---

## Phase 5: Evidence-Based Status Rating

### File: `services/inventory_dossier.py`

**Problem:** Green = "no risks" instead of "verified good"

**Fix 5.1: Replace _calculate_status() (around line 340)**
```python
def _calculate_status(self, risks: List[Dict], dossier: ItemDossier = None) -> str:
    """
    Calculate status based on BOTH risks AND evidence quality.

    Status criteria:
    - RED: Critical/high risks OR <25% data completeness
    - YELLOW: Medium risks OR <50% data completeness OR thin evidence
    - GREEN: No significant risks AND >75% completeness AND adequate evidence
    """
    # Check risk severity
    severities = [r.get('severity', 'medium').lower() for r in risks]
    has_critical = 'critical' in severities
    has_high = 'high' in severities
    has_medium = 'medium' in severities

    # Check evidence quality (if dossier provided)
    if dossier:
        completeness = getattr(dossier, 'data_completeness', 1.0)
        evidence_count = len(dossier.evidence)

        # RED conditions
        if has_critical or has_high:
            return "red"
        if completeness < 0.25:
            return "red"

        # YELLOW conditions
        if has_medium:
            return "yellow"
        if completeness < 0.50:
            return "yellow"
        if evidence_count < 2:  # Thin evidence
            return "yellow"

        # GREEN requires actual evidence
        if completeness >= 0.75 and evidence_count >= 2:
            return "green"

        return "yellow"  # Default to yellow if uncertain

    # Fallback: risk-only logic
    if has_critical or has_high:
        return "red"
    elif has_medium:
        return "yellow"
    return "green"
```

**Fix 5.2: Update status calculation call (line 473)**
```python
# Before:
dossier.overall_status = self._calculate_status(related_risks)

# After:
dossier.overall_status = self._calculate_status(related_risks, dossier)
```

---

## Phase 6: Conflict Detection for Duplicate Items

### File: `services/inventory_dossier.py`

**Problem:** First value wins silently when attributes conflict

**Fix 6.1: Add conflict tracking to ItemDossier (after line 108)**
```python
# Conflict tracking
attribute_conflicts: Dict[str, List[Any]] = field(default_factory=dict)  # field -> [values]
has_conflicts: bool = False
```

**Fix 6.2: Update attribute extraction with conflict detection (line 419-423)**
```python
# Extract attributes from details WITH conflict detection
details = fact.get('details', {})
for key, value in details.items():
    if value:
        if key in dossier.attributes:
            existing = dossier.attributes[key]
            if str(existing).lower() != str(value).lower():
                # Conflict detected
                if key not in dossier.attribute_conflicts:
                    dossier.attribute_conflicts[key] = [existing]
                dossier.attribute_conflicts[key].append(value)
                dossier.has_conflicts = True
        else:
            dossier.attributes[key] = value
```

**Fix 6.3: Display conflicts in HTML (add warning box)**
```python
# Add conflict warning if present
conflict_html = ""
if dossier.has_conflicts:
    conflict_html = f'''
    <div class="section conflicts-warning">
        <h4>⚠️ Data Conflicts Detected</h4>
        <p>Multiple values found for the same attribute:</p>
        <ul>
            {''.join(f'<li><strong>{k}</strong>: {", ".join(str(v) for v in vals)}</li>'
                     for k, vals in dossier.attribute_conflicts.items())}
        </ul>
        <p class="warning-note">Review source documents to resolve.</p>
    </div>'''
```

---

## Phase 7: PE Reports Entity Separation

### Files: `tools_v2/domain_generators/*.py`, `tools_v2/pe_costs.py`

**Problem:** PE reports pull from FactStore without entity filtering

**Fix 7.1: Update BaseDomainGenerator to filter by entity**
```python
# tools_v2/domain_generators/base.py

def __init__(self, fact_store, reasoning_store, deal_context, entity: str = "target"):
    self.fact_store = fact_store
    self.reasoning_store = reasoning_store
    self.deal_context = deal_context
    self.entity = entity  # NEW

def _get_domain_facts(self) -> List[Dict]:
    """Get facts for this domain filtered by entity."""
    return [
        f.to_dict() for f in self.fact_store.get_entity_facts(self.entity, self.domain)
    ]
```

**Fix 7.2: Update PE dashboard to show entity context**
```python
# tools_v2/executive_dashboard.py

@dataclass
class ExecutiveDashboardData:
    # ... existing fields ...
    entity: str = "target"  # NEW - which company this dashboard represents

# In render, add header badge:
<span class="entity-indicator">{data.entity.upper()} ENVIRONMENT</span>
```

**Fix 7.3: Add buyer comparison view option**
```python
# web/blueprints/pe_reports.py

@pe_reports_bp.route('/dashboard')
@pe_reports_bp.route('/dashboard/<entity>')  # NEW route
def dashboard(entity: str = "target"):
    # Validate entity
    if entity not in ["target", "buyer", "comparison"]:
        entity = "target"

    # Generate for specific entity
    dashboard_data = generate_dashboard_data(
        fact_store=fact_store,
        reasoning_store=reasoning_store,
        deal_context=deal_context,
        entity=entity  # Pass through
    )
```

---

## Phase 8: Three-View Dossier Export

### File: `web/app.py` (export routes)

**Fix 8.1: Add entity parameter to dossier export**
```python
@app.route('/api/export/dossiers/<domain>')
@app.route('/api/export/dossiers/<domain>/<entity>')  # NEW
def export_dossiers(domain, entity=None):
    """Export dossiers with optional entity filter."""
    # If entity specified, filter to that entity only
    # If not specified, create three-section output
```

**Fix 8.2: Create three-view HTML template**
```html
<div class="entity-section target-section">
    <h2>🎯 Target Environment</h2>
    <!-- Target dossiers -->
</div>

<div class="entity-section buyer-section">
    <h2>🏢 Buyer Reference</h2>
    <!-- Buyer dossiers -->
</div>

<div class="entity-section delta-section">
    <h2>⚡ Integration Delta</h2>
    <!-- Items that exist in both with differences -->
</div>
```

---

## Implementation Order

| Phase | Priority | Effort | Files Changed |
|-------|----------|--------|---------------|
| 1. Entity-aware indexing | CRITICAL | 2h | inventory_dossier.py |
| 2. Entity badge in HTML | HIGH | 1h | inventory_dossier.py |
| 3. Source traceability | HIGH | 2h | inventory_dossier.py |
| 4. not_stated → Gaps | MEDIUM | 2h | inventory_dossier.py |
| 5. Evidence-based status | HIGH | 1h | inventory_dossier.py |
| 6. Conflict detection | MEDIUM | 2h | inventory_dossier.py |
| 7. PE reports entity | HIGH | 3h | domain_generators/, pe_costs.py |
| 8. Three-view export | MEDIUM | 3h | web/app.py |

**Total Effort: ~16 hours**

---

## Acceptance Criteria (GPT's Rubric)

Before any dossier is team-ready:

- [ ] Every tile has explicit `TARGET` or `BUYER` badge
- [ ] No same-name items merged across entities
- [ ] Source evidence includes doc + section (not just filename)
- [ ] `not_stated` fields generate Gap items with owner/timeline
- [ ] GREEN status requires >75% data completeness + 2+ evidence items
- [ ] Conflicts flagged visually with all conflicting values shown
- [ ] PE dashboard clearly labeled as "Target Environment" or "Buyer Reference"
- [ ] Export options include Target-only, Buyer-only, and Comparison views

---

## Testing Checklist

1. **Entity Separation Test**
   - Upload docs for both Target and Buyer
   - Verify same-name apps (e.g., "ADP") create TWO separate dossiers
   - Verify each dossier shows correct entity badge

2. **Conflict Detection Test**
   - Create facts with conflicting user_count for same item
   - Verify conflict warning appears in dossier

3. **Data Completeness Test**
   - Create dossier with minimal attributes
   - Verify status is YELLOW (not GREEN)
   - Verify data gaps section lists missing fields

4. **PE Reports Test**
   - Generate dashboard for Target entity
   - Generate dashboard for Buyer entity
   - Verify no data mixing between views
