# Fix Plan: Entity Separation & Data Quality (v2)

## GPT Review Score: 8.5/10 for architecture direction

**Status:** Revised based on GPT feedback

---

## Problem Summary

GPT Dossier Review Score: **4.5-6/10** - "Usable shell but too many data integrity issues to trust"

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

## GPT Feedback Incorporated (v2 Changes)

| GPT Suggestion | How We Address It |
|----------------|-------------------|
| Missing entity = defect, not silent default | Phase 1B: Track `unknown_entity_count`, force yellow/red |
| Item identity needs more than name | Phase 1C: Add `canonical_key` with vendor+product+instance |
| Evidence needs source_anchor for non-page docs | Phase 3: Add `source_anchor` (heading_path, table_name, chunk_id) |
| Domain names need normalization | Phase 4B: Add `DOMAIN_ALIASES` mapping table |
| Evidence quality scoring, not just count | Phase 5B: Evidence quality score (citation + quote + numeric backing) |
| Delta view needs real diff logic | Phase 8B: Add match logic + comparison rules + diff output |
| Test for Juniper vs Check Point case | Testing: Explicit contradiction test case |
| Team-ready gate at export | Phase 9 (NEW): Export gate with blocking conditions |

---

## Phase 1: Entity-Aware Dossier Indexing (CRITICAL)

### File: `services/inventory_dossier.py`

**Problem:** Line 176 creates item key without entity
```python
# BROKEN
item_key = f"{domain}:{item.lower()}"
```

### Fix 1.1: Change item key to include entity
```python
# Line 176 - _index_facts()
entity = fact.get('entity')  # DON'T default - see 1B
if entity is None:
    entity = 'target'
    self.unknown_entity_count += 1  # Track the defect
item_key = f"{entity}:{domain}:{item.lower()}"
```

### Fix 1.2: Update build_dossier() to use entity-aware key
```python
# Line 373 - build_dossier()
def build_dossier(self, item_name: str, domain: str, entity: str = "target") -> Optional[ItemDossier]:
    item_key = f"{entity}:{domain}:{item_name.lower()}"
    item_facts = self.facts_by_item.get(item_key, [])
```

### Fix 1.3 (GPT): Track unknown_entity_count as data quality defect
```python
# In DossierBuilder.__init__()
self.unknown_entity_count = 0  # Facts missing entity field

# After indexing, log warning
if self.unknown_entity_count > 0:
    logger.warning(f"{self.unknown_entity_count} facts missing entity field - data quality defect")
```

### Fix 1.4 (GPT): Add canonical_key for robust item identity
```python
# New function to generate stable item identity
def _generate_canonical_key(self, fact: Dict) -> str:
    """
    Generate stable item identity beyond just name.

    Handles: "ADP Workforce Now" vs "ADP" vs "ADP (Payroll Instance)"
    """
    entity = fact.get('entity', 'target')
    domain = fact.get('domain', 'general')
    item = fact.get('item', '').strip().lower()

    # Extract vendor if available
    details = fact.get('details', {})
    vendor = details.get('vendor', '').strip().lower()

    # Extract instance/environment if available
    instance = details.get('instance', details.get('environment', '')).strip().lower()

    # Build canonical key
    parts = [entity, domain, item]
    if vendor and vendor not in item:
        parts.append(vendor)
    if instance:
        parts.append(instance)

    return ":".join(parts)
```

### Fix 1.5: Update build_domain_dossiers() to build separate Target/Buyer dossiers
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

    # Normalize domain name
    normalized_domain = self._normalize_domain(domain)
    domain_facts = self.facts_by_domain.get(normalized_domain, [])

    # Filter by entity if specified
    if entity:
        domain_facts = [f for f in domain_facts if f.get('entity', 'target') == entity]

    # Get unique items by canonical key
    items_by_key = {}
    for fact in domain_facts:
        canonical = self._generate_canonical_key(fact)
        fact_entity = fact.get('entity', 'target')
        item_name = fact.get('item', '').strip()
        if item_name:
            items_by_key[canonical] = (fact_entity, item_name)

    # Build dossier for each unique canonical item
    for canonical_key, (item_entity, item_name) in sorted(items_by_key.items()):
        dossier = self.build_dossier(item_name, normalized_domain, entity=item_entity)
        if dossier:
            dossier.canonical_key = canonical_key  # Store for delta matching
            dossiers.append(dossier)

    return dossiers
```

**Done when:**
- [ ] Same-name items in Target and Buyer create separate dossiers
- [ ] `unknown_entity_count` is tracked and logged
- [ ] Canonical key includes vendor/instance when available

---

## Phase 2: Entity Badge in HTML Output

### File: `services/inventory_dossier.py`

**Problem:** Dossier header shows name but no entity indicator

### Fix 2.1: Add entity badge CSS (after line 920)
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
.entity-badge.unknown { background: #dc3545; color: white; }  /* GPT: flag unknown */
```

### Fix 2.2: Add entity badge to dossier header (line 988)
```python
# Before:
<h3>{dossier.name}</h3>

# After:
entity_class = dossier.entity if dossier.entity in ['target', 'buyer'] else 'unknown'
<h3>
    <span class="entity-badge {entity_class}">{dossier.entity.upper()}</span>
    {dossier.name}
</h3>
```

### Fix 2.3: Add entity to data attribute for filtering
```python
# Line 986
<div class="dossier" data-status="{dossier.overall_status}" data-entity="{dossier.entity}">
```

### Fix 2.4: Add entity filter buttons (after line 946)
```python
<button class="filter-btn" onclick="filterByEntity('target')">🎯 Target Only</button>
<button class="filter-btn" onclick="filterByEntity('buyer')">🏢 Buyer Only</button>
<button class="filter-btn" onclick="filterByEntity('all')">All</button>
```

**Done when:**
- [ ] Every dossier tile shows TARGET or BUYER badge
- [ ] Unknown entities show RED "UNKNOWN" badge
- [ ] Filter buttons work to show only one entity

---

## Phase 3: Source Evidence Traceability

### File: `services/inventory_dossier.py`

**Problem:** Evidence shows only filename ("— document.pdf")

### Fix 3.1 (GPT Enhanced): Update SourceEvidence dataclass
```python
@dataclass
class SourceEvidence:
    """Evidence from source documents."""
    quote: str
    source_document: str
    source_section: str = ""
    source_page: str = ""
    source_line: str = ""
    source_anchor: str = ""      # GPT: heading_path, table_name, chunk_id
    fact_id: str = ""
    is_exact_quote: bool = True  # GPT: vs paraphrase

    def format_citation(self) -> str:
        """Format as auditable citation."""
        parts = [self.source_document]
        if self.source_section:
            parts.append(f"§{self.source_section}")
        if self.source_page:
            parts.append(f"p.{self.source_page}")
        if self.source_anchor and not self.source_page:
            # Use anchor when page not available (GPT suggestion)
            parts.append(f"@{self.source_anchor}")
        return " | ".join(parts)

    def quality_score(self) -> int:
        """GPT: Evidence quality score for status calculation."""
        score = 0
        # Has citation metadata
        if self.source_section or self.source_page or self.source_anchor:
            score += 1
        # Is exact quote (not paraphrase)
        if self.is_exact_quote:
            score += 1
        # Quote contains a number (backs a key field)
        if any(c.isdigit() for c in self.quote):
            score += 1
        return score
```

### Fix 3.2: Update evidence extraction (line 402-408)
```python
evidence = fact.get('evidence', {})
if isinstance(evidence, dict) and evidence.get('exact_quote'):
    dossier.evidence.append(SourceEvidence(
        quote=evidence['exact_quote'],
        source_document=fact.get('source_document', ''),
        source_section=evidence.get('source_section', ''),
        source_page=evidence.get('page_number', evidence.get('page', '')),
        source_line=evidence.get('line_number', ''),
        source_anchor=evidence.get('heading_path', evidence.get('table_name', evidence.get('chunk_id', ''))),
        fact_id=fact_id,
        is_exact_quote=True  # Our extraction always uses exact quotes
    ))
```

### Fix 3.3: Update HTML rendering (line 956)
```python
citation = ev.format_citation() if hasattr(ev, 'format_citation') else ev.source_document
quality = ev.quality_score() if hasattr(ev, 'quality_score') else 0
quality_indicator = "⭐" * quality if quality > 0 else "⚠️"

evidence_html += f'''
<div class="evidence">
    "{quote[:250]}{"..." if len(quote) > 250 else ""}"
    <div class="source">
        <span class="fact-id">[{ev.fact_id}]</span>
        <span class="quality">{quality_indicator}</span>
        — {citation}
    </div>
</div>'''
```

**Done when:**
- [ ] Evidence shows doc + section/page OR anchor
- [ ] Evidence quality score (0-3 stars) is visible
- [ ] Non-page-addressable docs use heading_path or chunk_id

---

## Phase 4: Promote not_stated to Gaps + Domain Normalization

### File: `services/inventory_dossier.py`

**Problem:** `not_stated` attributes sit as dead data; domain names inconsistent

### Fix 4.1 (GPT): Add domain normalization mapping
```python
# Domain name normalization (GPT suggestion)
DOMAIN_ALIASES = {
    'identity & access': 'identity_access',
    'identity and access': 'identity_access',
    'iam': 'identity_access',
    'security': 'cybersecurity',
    'cyber': 'cybersecurity',
    'infra': 'infrastructure',
    'apps': 'applications',
    'network & connectivity': 'network',
    'org': 'organization',
    'people': 'organization',
}

def _normalize_domain(self, domain: str) -> str:
    """Normalize domain name to canonical form."""
    normalized = domain.lower().strip()
    return DOMAIN_ALIASES.get(normalized, normalized)
```

### Fix 4.2: Add gap generation with normalized domains (after line 423)
```python
# Critical fields by NORMALIZED domain name
CRITICAL_FIELDS = {
    'applications': ['user_count', 'vendor', 'version', 'criticality', 'annual_cost'],
    'infrastructure': ['location', 'capacity', 'age', 'annual_cost'],
    'cybersecurity': ['coverage', 'deployment_scope', 'last_assessment'],
    'identity_access': ['user_count', 'mfa_coverage', 'sso_enabled'],
    'network': ['bandwidth', 'redundancy', 'vendor'],
    'organization': ['headcount', 'reporting_to', 'tenure'],
}

# Normalize domain before lookup
normalized_domain = self._normalize_domain(domain)
missing_critical = []
domain_critical = CRITICAL_FIELDS.get(normalized_domain, [])

for field in domain_critical:
    value = dossier.attributes.get(field)
    if not value or str(value).lower() in ['not_stated', 'not_specified', 'unknown', 'n/a', 'none', '']:
        missing_critical.append(field)

if missing_critical:
    dossier.data_gaps = missing_critical
    dossier.data_completeness = 1 - (len(missing_critical) / max(len(domain_critical), 1))
else:
    dossier.data_completeness = 1.0
```

### Fix 4.3: Add data_gaps field to ItemDossier (after line 108)
```python
# Data completeness tracking
data_gaps: List[str] = field(default_factory=list)  # Missing critical fields
data_completeness: float = 1.0  # 0.0 to 1.0
canonical_key: str = ""  # GPT: For delta matching
```

### Fix 4.4: Display data gaps in HTML
```python
gaps_html = ""
if dossier.data_gaps:
    completeness_class = "red" if dossier.data_completeness < 0.5 else "yellow"
    gaps_html = f'''
    <div class="section data-gaps {completeness_class}">
        <h4>⚠️ Data Gaps ({len(dossier.data_gaps)} critical fields missing)</h4>
        <ul class="gap-list">
            {''.join(f'<li>{g.replace("_", " ").title()}</li>' for g in dossier.data_gaps)}
        </ul>
        <p class="completeness">Data completeness: {dossier.data_completeness:.0%}</p>
        <p class="action">These should be added to VDR request list.</p>
    </div>'''
```

**Done when:**
- [ ] Domain names normalized before CRITICAL_FIELDS lookup
- [ ] `not_stated` fields appear in Data Gaps section
- [ ] Data completeness percentage is calculated and shown

---

## Phase 5: Evidence-Based Status Rating (GPT Enhanced)

### File: `services/inventory_dossier.py`

**Problem:** Green = "no risks" instead of "verified good"

### Fix 5.1 (GPT): Replace _calculate_status() with quality-aware logic
```python
def _calculate_status(self, risks: List[Dict], dossier: ItemDossier = None) -> str:
    """
    Calculate status based on risks AND evidence quality (GPT enhanced).

    Status criteria:
    - RED: Critical/high risks OR <25% data completeness OR unknown entity
    - YELLOW: Medium risks OR <50% data completeness OR evidence quality < 3
    - GREEN: No significant risks AND >75% completeness AND evidence quality >= 3
    """
    # Check risk severity
    severities = [r.get('severity', 'medium').lower() for r in risks]
    has_critical = 'critical' in severities
    has_high = 'high' in severities
    has_medium = 'medium' in severities

    if dossier:
        completeness = getattr(dossier, 'data_completeness', 1.0)

        # GPT: Calculate total evidence quality score
        evidence_quality = sum(
            ev.quality_score() if hasattr(ev, 'quality_score') else 1
            for ev in dossier.evidence
        )

        # GPT: Unknown entity is a RED flag
        if dossier.entity not in ['target', 'buyer']:
            return "red"

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
        if evidence_quality < 3:  # GPT: Quality threshold, not just count
            return "yellow"
        if dossier.has_conflicts:  # Conflicts require review
            return "yellow"

        # GREEN requires actual quality evidence
        if completeness >= 0.75 and evidence_quality >= 3:
            return "green"

        return "yellow"  # Default to yellow if uncertain

    # Fallback: risk-only logic
    if has_critical or has_high:
        return "red"
    elif has_medium:
        return "yellow"
    return "yellow"  # GPT: Default to yellow, not green
```

### Fix 5.2: Update status calculation call (line 473)
```python
# Before:
dossier.overall_status = self._calculate_status(related_risks)

# After:
dossier.overall_status = self._calculate_status(related_risks, dossier)
```

**Done when:**
- [ ] Evidence quality score (not just count) drives status
- [ ] Unknown entity forces RED status
- [ ] Conflicts force YELLOW status
- [ ] Default is YELLOW, not GREEN

---

## Phase 6: Conflict Detection for Duplicate Items

### File: `services/inventory_dossier.py`

**Problem:** First value wins silently when attributes conflict

### Fix 6.1: Add conflict tracking to ItemDossier (after line 108)
```python
# Conflict tracking
attribute_conflicts: Dict[str, List[Any]] = field(default_factory=dict)
has_conflicts: bool = False
conflict_count: int = 0
```

### Fix 6.2: Update attribute extraction with conflict detection (line 419-423)
```python
# Extract attributes from details WITH conflict detection
details = fact.get('details', {})
for key, value in details.items():
    if value and str(value).lower() not in ['not_stated', 'not_specified', 'unknown', 'n/a']:
        if key in dossier.attributes:
            existing = dossier.attributes[key]
            # Normalize for comparison
            existing_norm = str(existing).lower().strip()
            value_norm = str(value).lower().strip()
            if existing_norm != value_norm:
                # Conflict detected
                if key not in dossier.attribute_conflicts:
                    dossier.attribute_conflicts[key] = [existing]
                if value not in dossier.attribute_conflicts[key]:
                    dossier.attribute_conflicts[key].append(value)
                dossier.has_conflicts = True
                dossier.conflict_count += 1
        else:
            dossier.attributes[key] = value
```

### Fix 6.3: Display conflicts in HTML (add warning box)
```python
conflict_html = ""
if dossier.has_conflicts:
    conflict_html = f'''
    <div class="section conflicts-warning" style="background: #fff3cd; border-left: 4px solid #ffc107;">
        <h4>⚠️ Data Conflicts Detected ({dossier.conflict_count})</h4>
        <p>Multiple values found for the same attribute. Review source documents to resolve:</p>
        <table class="conflict-table">
            <tr><th>Attribute</th><th>Conflicting Values</th></tr>
            {''.join(f'<tr><td><strong>{k}</strong></td><td>{" vs ".join(str(v) for v in vals)}</td></tr>'
                     for k, vals in dossier.attribute_conflicts.items())}
        </table>
    </div>'''
```

**Done when:**
- [ ] Multiple values for same attribute are detected
- [ ] Conflicts shown in yellow warning box
- [ ] Conflict count visible in dossier

---

## Phase 7: PE Reports Entity Separation

### Files: `tools_v2/domain_generators/*.py`, `tools_v2/pe_costs.py`

**Problem:** PE reports pull from FactStore without entity filtering

### Fix 7.1: Update BaseDomainGenerator to filter by entity
```python
# tools_v2/domain_generators/base.py

def __init__(self, fact_store, reasoning_store, deal_context, entity: str = "target"):
    self.fact_store = fact_store
    self.reasoning_store = reasoning_store
    self.deal_context = deal_context
    self.entity = entity

def _get_domain_facts(self) -> List[Dict]:
    """Get facts for this domain filtered by entity."""
    return [
        f.to_dict() for f in self.fact_store.get_entity_facts(self.entity, self.domain)
    ]
```

### Fix 7.2: Update PE dashboard to show entity context
```python
# tools_v2/executive_dashboard.py

@dataclass
class ExecutiveDashboardData:
    # ... existing fields ...
    entity: str = "target"

# In render, add header:
<div class="entity-banner {data.entity}">
    {'🎯 TARGET ENVIRONMENT' if data.entity == 'target' else '🏢 BUYER REFERENCE'}
</div>
```

### Fix 7.3: Add buyer comparison view option
```python
# web/blueprints/pe_reports.py

@pe_reports_bp.route('/dashboard')
@pe_reports_bp.route('/dashboard/<entity>')
def dashboard(entity: str = "target"):
    if entity not in ["target", "buyer", "comparison"]:
        entity = "target"

    dashboard_data = generate_dashboard_data(
        fact_store=fact_store,
        reasoning_store=reasoning_store,
        deal_context=deal_context,
        entity=entity
    )
```

**Done when:**
- [ ] PE dashboard shows which entity it represents
- [ ] Routes support /dashboard/target and /dashboard/buyer
- [ ] No fact mixing between entity views

---

## Phase 8: Three-View Dossier Export with Delta Logic (GPT Enhanced)

### File: `web/app.py`, NEW: `services/delta_comparator.py`

**Problem:** No real diff logic for integration delta view

### Fix 8.1 (GPT): Create delta comparator service
```python
# NEW FILE: services/delta_comparator.py

@dataclass
class DeltaResult:
    """Result of comparing target vs buyer item."""
    target_item: Optional[ItemDossier]
    buyer_item: Optional[ItemDossier]
    match_type: str  # "matched", "target_only", "buyer_only"
    attribute_diffs: Dict[str, Tuple[Any, Any]]  # field -> (target_val, buyer_val)
    is_vendor_mismatch: bool
    is_version_mismatch: bool
    integration_notes: List[str]

class DeltaComparator:
    """GPT: Real diff engine for Target vs Buyer comparison."""

    # Attributes where mismatch is meaningful
    MEANINGFUL_DIFF_FIELDS = ['vendor', 'version', 'platform', 'hosting', 'region']

    # Attributes where mismatch is just scale
    SCALE_DIFF_FIELDS = ['user_count', 'cost', 'headcount', 'capacity']

    def match_items(self, target_dossiers: List[ItemDossier],
                    buyer_dossiers: List[ItemDossier]) -> List[DeltaResult]:
        """Match target items to buyer items and compute deltas."""
        results = []

        # Index buyer items by canonical key and name
        buyer_by_key = {d.canonical_key: d for d in buyer_dossiers}
        buyer_by_name = {d.name.lower(): d for d in buyer_dossiers}
        matched_buyer_keys = set()

        for target in target_dossiers:
            # Try canonical key match first
            buyer = buyer_by_key.get(target.canonical_key)
            if not buyer:
                # Fall back to name match
                buyer = buyer_by_name.get(target.name.lower())

            if buyer:
                matched_buyer_keys.add(buyer.canonical_key)
                delta = self._compute_delta(target, buyer)
                results.append(delta)
            else:
                # Target only
                results.append(DeltaResult(
                    target_item=target,
                    buyer_item=None,
                    match_type="target_only",
                    attribute_diffs={},
                    is_vendor_mismatch=False,
                    is_version_mismatch=False,
                    integration_notes=["No matching buyer system found"]
                ))

        # Add buyer-only items
        for buyer in buyer_dossiers:
            if buyer.canonical_key not in matched_buyer_keys:
                results.append(DeltaResult(
                    target_item=None,
                    buyer_item=buyer,
                    match_type="buyer_only",
                    attribute_diffs={},
                    is_vendor_mismatch=False,
                    is_version_mismatch=False,
                    integration_notes=["Buyer system with no target equivalent"]
                ))

        return results

    def _compute_delta(self, target: ItemDossier, buyer: ItemDossier) -> DeltaResult:
        """Compute attribute differences between matched items."""
        diffs = {}
        notes = []

        all_keys = set(target.attributes.keys()) | set(buyer.attributes.keys())

        for key in all_keys:
            t_val = target.attributes.get(key)
            b_val = buyer.attributes.get(key)

            if t_val != b_val:
                diffs[key] = (t_val, b_val)

                if key in self.MEANINGFUL_DIFF_FIELDS:
                    notes.append(f"{key}: Target={t_val} vs Buyer={b_val}")

        is_vendor_mismatch = 'vendor' in diffs
        is_version_mismatch = 'version' in diffs

        if is_vendor_mismatch:
            notes.insert(0, "⚠️ VENDOR MISMATCH - Integration complexity HIGH")

        return DeltaResult(
            target_item=target,
            buyer_item=buyer,
            match_type="matched",
            attribute_diffs=diffs,
            is_vendor_mismatch=is_vendor_mismatch,
            is_version_mismatch=is_version_mismatch,
            integration_notes=notes
        )
```

### Fix 8.2: Add entity parameter to dossier export
```python
@app.route('/api/export/dossiers/<domain>')
@app.route('/api/export/dossiers/<domain>/<entity>')
def export_dossiers(domain, entity=None):
    """Export dossiers with optional entity filter or comparison view."""
    if entity == "comparison":
        # Use delta comparator
        target_dossiers = builder.build_domain_dossiers(domain, entity="target")
        buyer_dossiers = builder.build_domain_dossiers(domain, entity="buyer")
        deltas = DeltaComparator().match_items(target_dossiers, buyer_dossiers)
        return render_delta_view(deltas, domain)
    elif entity:
        dossiers = builder.build_domain_dossiers(domain, entity=entity)
    else:
        # Default: show both with clear separation
        dossiers = builder.build_domain_dossiers(domain)
```

### Fix 8.3: Create three-view HTML template
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
    <div class="delta-summary">
        <span class="matched">✓ {matched_count} Matched</span>
        <span class="target-only">→ {target_only_count} Target Only</span>
        <span class="buyer-only">← {buyer_only_count} Buyer Only</span>
        <span class="vendor-mismatch">⚠️ {vendor_mismatch_count} Vendor Mismatches</span>
    </div>
    <!-- Delta items with diff highlighting -->
</div>
```

**Done when:**
- [ ] Delta view shows matched/target-only/buyer-only
- [ ] Vendor mismatches highlighted prominently
- [ ] Attribute diffs shown in table format

---

## Phase 9 (NEW - GPT): Team-Ready Export Gate

### File: `services/inventory_dossier.py`, `web/app.py`

**Problem:** Exports go out even with data quality issues

### Fix 9.1: Add export readiness checker
```python
@dataclass
class ExportReadiness:
    """Result of team-ready gate check."""
    is_ready: bool
    blocking_issues: List[str]
    warnings: List[str]
    unknown_entity_count: int
    unresolved_conflicts: int
    low_completeness_domains: List[str]

class ExportGate:
    """GPT: Block exports that aren't team-ready."""

    def check_readiness(self, dossiers: Dict[str, List[ItemDossier]]) -> ExportReadiness:
        blocking = []
        warnings = []
        unknown_count = 0
        conflict_count = 0
        low_completeness = []

        for domain, domain_dossiers in dossiers.items():
            domain_completeness = []

            for d in domain_dossiers:
                # Check for unknown entities
                if d.entity not in ['target', 'buyer']:
                    unknown_count += 1

                # Check for unresolved conflicts
                if d.has_conflicts:
                    conflict_count += d.conflict_count

                domain_completeness.append(d.data_completeness)

            # Check domain-level completeness
            avg_completeness = sum(domain_completeness) / len(domain_completeness) if domain_completeness else 0
            if avg_completeness < 0.5:
                low_completeness.append(f"{domain}: {avg_completeness:.0%}")

        # Determine blocking issues
        if unknown_count > 0:
            blocking.append(f"{unknown_count} facts with unknown entity - CANNOT EXPORT")

        if conflict_count > 10:
            blocking.append(f"{conflict_count} unresolved conflicts - REVIEW REQUIRED")
        elif conflict_count > 0:
            warnings.append(f"{conflict_count} conflicts need resolution")

        if low_completeness:
            warnings.append(f"Low completeness domains: {', '.join(low_completeness)}")

        return ExportReadiness(
            is_ready=len(blocking) == 0,
            blocking_issues=blocking,
            warnings=warnings,
            unknown_entity_count=unknown_count,
            unresolved_conflicts=conflict_count,
            low_completeness_domains=low_completeness
        )
```

### Fix 9.2: Add gate check to export routes
```python
@app.route('/api/export/dossiers/<domain>')
def export_dossiers(domain):
    dossiers = builder.build_all_dossiers()

    # Check export readiness
    gate = ExportGate()
    readiness = gate.check_readiness(dossiers)

    if not readiness.is_ready:
        return jsonify({
            "error": "Export blocked - data quality issues",
            "blocking_issues": readiness.blocking_issues,
            "warnings": readiness.warnings
        }), 400

    # Proceed with export, include warnings in header
    # ...
```

### Fix 9.3: Add readiness banner to HTML exports
```python
def _render_readiness_banner(readiness: ExportReadiness) -> str:
    if readiness.blocking_issues:
        return f'''
        <div class="readiness-banner blocking">
            <h3>🚫 NOT READY FOR TEAM DISTRIBUTION</h3>
            <ul>{''.join(f'<li>{i}</li>' for i in readiness.blocking_issues)}</ul>
        </div>'''
    elif readiness.warnings:
        return f'''
        <div class="readiness-banner warning">
            <h3>⚠️ REVIEW RECOMMENDED</h3>
            <ul>{''.join(f'<li>{w}</li>' for w in readiness.warnings)}</ul>
        </div>'''
    else:
        return '<div class="readiness-banner ready"><h3>✅ TEAM READY</h3></div>'
```

**Done when:**
- [ ] Unknown entity facts block export
- [ ] High conflict count blocks export
- [ ] Warnings shown but don't block
- [ ] Banner shows readiness status

---

## Implementation Order (Updated)

| Phase | Priority | Effort | Files Changed |
|-------|----------|--------|---------------|
| 1. Entity-aware indexing + canonical key | CRITICAL | 3h | inventory_dossier.py |
| 2. Entity badge in HTML | HIGH | 1h | inventory_dossier.py |
| 3. Source traceability + quality score | HIGH | 2h | inventory_dossier.py |
| 4. not_stated → Gaps + domain normalization | MEDIUM | 2h | inventory_dossier.py |
| 5. Evidence-based status (quality score) | HIGH | 1h | inventory_dossier.py |
| 6. Conflict detection | MEDIUM | 2h | inventory_dossier.py |
| 7. PE reports entity | HIGH | 3h | domain_generators/, pe_costs.py |
| 8. Three-view export + delta comparator | MEDIUM | 4h | web/app.py, delta_comparator.py |
| 9. Team-ready export gate | HIGH | 2h | inventory_dossier.py, web/app.py |

**Total Effort: ~20 hours**

---

## Acceptance Criteria (GPT's Rubric - Updated)

Before any dossier is team-ready:

- [ ] Every tile has explicit `TARGET` or `BUYER` badge
- [ ] Unknown entity facts tracked as defects and block export
- [ ] Same-name items NOT merged across entities (canonical key)
- [ ] Source evidence includes doc + section/page OR anchor
- [ ] Evidence quality score (0-3) visible on each quote
- [ ] `not_stated` fields appear in Data Gaps section
- [ ] GREEN status requires quality >= 3, completeness >= 75%
- [ ] Conflicts flagged visually with all conflicting values
- [ ] PE dashboard clearly labeled by entity
- [ ] Delta view shows matched/target-only/buyer-only with diff logic
- [ ] Export gate blocks on unknown entities or high conflicts

---

## Testing Checklist

### 1. Entity Separation Test
- Upload docs for both Target and Buyer
- Verify same-name apps (e.g., "ADP") create TWO separate dossiers
- Verify each dossier shows correct entity badge
- Verify canonical key handles vendor/instance variants

### 2. Contradiction Test (GPT's Juniper vs Check Point case)
- Create Target firewall fact: vendor=Juniper
- Create Buyer firewall fact: vendor=Check Point
- Verify Target dossier shows ONLY Juniper
- Verify Buyer dossier shows ONLY Check Point
- Verify Delta view shows "VENDOR MISMATCH" flag

### 3. Conflict Detection Test
- Create two facts for same item with different user_count
- Verify conflict warning appears
- Verify both values shown in conflict table

### 4. Data Completeness Test
- Create dossier with minimal attributes
- Verify status is YELLOW (not GREEN)
- Verify data gaps section lists missing fields

### 5. Export Gate Test
- Create facts with unknown entity
- Attempt export
- Verify export is BLOCKED with error message

### 6. PE Reports Test
- Generate dashboard for Target entity
- Generate dashboard for Buyer entity
- Verify no data mixing between views

---

## Summary of Changes from v1

| Area | v1 | v2 (GPT Enhanced) |
|------|----|--------------------|
| Missing entity | Silent default to "target" | Track as defect, block export |
| Item identity | name only | canonical_key (vendor+instance) |
| Evidence source | page/line only | + source_anchor for non-page docs |
| Evidence quality | count >= 2 | quality score >= 3 |
| Domain names | raw strings | normalized via DOMAIN_ALIASES |
| Delta view | template only | real diff engine with match logic |
| Default status | green | yellow (conservative) |
| Export | always allowed | gated on data quality |
