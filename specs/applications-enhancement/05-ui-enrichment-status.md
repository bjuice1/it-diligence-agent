# UI Enrichment Status

**Status:** Specification
**Created:** 2026-02-11
**Depends On:** 00-overview-applications-enhancement.md, 01-entity-propagation-hardening.md, 02-table-parser-robustness.md
**Enables:** 06-testing-validation.md
**Estimated Scope:** 3-4 hours

---

## Overview

**Problem:** UI currently shows application inventory without data quality indicators. Users can't tell if enrichment succeeded/failed, which apps need manual review, or trace back to source facts/documents.

**Solution:** Display enrichment status, extraction quality, source tracing, and "needs investigation" flags in application inventory UI.

**Why this exists:** Transparency builds user trust. Users need to know which data is reliable vs which needs manual validation.

---

## Architecture

### Current UI (Opaque)

```html
<table class="inventory-table">
    <tr>
        <th>Name</th>
        <th>Category</th>
        <th>Vendor</th>
        <th>Users</th>
    </tr>
    <tr>
        <td>SAP ERP</td>
        <td>ERP</td>
        <td>SAP AG</td>
        <td>5000</td>
    </tr>
</table>
```

**Missing:**
- No indication if category was enriched by LLM or deterministically matched
- No extraction quality score
- No link to source facts or documents
- No "needs investigation" flag

### Target UI (Transparent)

```html
<table class="inventory-table">
    <tr>
        <th>Name</th>
        <th>Category</th>
        <th>Vendor</th>
        <th>Users</th>
        <th>Data Quality</th>
        <th>Actions</th>
    </tr>
    <tr>
        <td>SAP ERP</td>
        <td>
            ERP
            <span class="badge badge-success" title="High confidence LLM enrichment">
                ✓ Enriched
            </span>
        </td>
        <td>SAP AG</td>
        <td>5000</td>
        <td>
            <div class="quality-indicator quality-high">
                Quality: 95%
                <span class="quality-details">
                    • Extraction: 0.98
                    • Enrichment: High confidence
                    • Entity: Validated
                </span>
            </div>
        </td>
        <td>
            <a href="/facts/F-APP-042" class="btn-sm">View Source Facts</a>
            <a href="/documents/doc_123.pdf#page=5" class="btn-sm">View Document</a>
        </td>
    </tr>
    <tr class="needs-investigation">
        <td>Custom Portal</td>
        <td>
            Unknown
            <span class="badge badge-warning" title="Enrichment failed">
                ⚠ Needs Review
            </span>
        </td>
        <td>-</td>
        <td>-</td>
        <td>
            <div class="quality-indicator quality-low">
                Quality: 45%
                <span class="quality-details">
                    • Extraction: 0.52 (low)
                    • Enrichment: Failed
                    • Entity: Inferred
                </span>
            </div>
        </td>
        <td>
            <button class="btn-warning">Manual Enrichment</button>
        </td>
    </tr>
</table>
```

**New features:**
- Enrichment status badges
- Data quality score with breakdown
- Source fact links
- Document links with page numbers
- "Needs investigation" visual highlighting
- Manual enrichment action

---

## Specification

### 1. Enrichment Status Display

**Add enrichment metadata to InventoryItem:**

```python
# stores/inventory_item.py

@dataclass
class InventoryItem:
    # ... existing fields

    # NEW: Enrichment metadata
    is_enriched: bool = False
    enrichment_confidence: str = 'none'  # none | low | medium | high
    enrichment_method: str = 'none'      # none | deterministic | llm | manual
    extraction_quality: float = 0.0      # 0.0-1.0 from parser
    needs_investigation: bool = False
```

**Populate during enrichment:**

```python
# tools_v2/enrichment/inventory_reviewer.py

def enrich_item(item: InventoryItem) -> InventoryItem:
    """Enrich inventory item with LLM or deterministic lookup."""

    # Try deterministic lookup first
    review = _try_local_lookup(item)

    if review and review.confidence == 'confident':
        item.data['category'] = review.category
        item.data['vendor'] = review.vendor_info.get('name') if review.vendor_info else None
        item.is_enriched = True
        item.enrichment_confidence = 'high'
        item.enrichment_method = 'deterministic'
        item.needs_investigation = False
        return item

    # Fall back to LLM enrichment
    llm_review = _llm_enrich(item)

    if llm_review and llm_review.confidence in ['confident', 'probable']:
        item.data['category'] = llm_review.category
        item.data['vendor'] = llm_review.vendor_info.get('name') if llm_review.vendor_info else None
        item.is_enriched = True
        item.enrichment_confidence = llm_review.confidence
        item.enrichment_method = 'llm'
        item.needs_investigation = llm_review.confidence == 'probable'  # Flag if uncertain
        return item

    # Enrichment failed
    item.is_enriched = False
    item.enrichment_confidence = 'none'
    item.enrichment_method = 'none'
    item.needs_investigation = True
    return item
```

### 2. Data Quality Score

**Composite quality score combining extraction and enrichment:**

```python
def calculate_data_quality_score(item: InventoryItem) -> float:
    """
    Calculate overall data quality score (0.0-1.0).

    Factors:
    - Extraction quality (from parser)
    - Enrichment confidence
    - Field completeness
    - Entity validation
    """
    # Extraction quality (0.0-1.0)
    extraction_score = item.extraction_quality

    # Enrichment confidence
    enrichment_scores = {
        'none': 0.0,
        'low': 0.5,
        'medium': 0.75,
        'high': 1.0
    }
    enrichment_score = enrichment_scores.get(item.enrichment_confidence, 0.0)

    # Field completeness (% of expected fields filled)
    expected_fields = ['name', 'category', 'vendor', 'users']
    filled = sum(1 for f in expected_fields if item.data.get(f))
    completeness_score = filled / len(expected_fields)

    # Entity validation (explicit vs inferred)
    entity_score = 1.0 if item.entity_validated else 0.7

    # Weighted average
    quality = (
        extraction_score * 0.3 +
        enrichment_score * 0.4 +
        completeness_score * 0.2 +
        entity_score * 0.1
    )

    return quality
```

### 3. UI Template Updates

**Modify `web/templates/inventory.html`:**

```html
<!-- Application Inventory Table -->
<table class="table table-striped inventory-table" id="applications-table">
    <thead>
        <tr>
            <th>Name</th>
            <th>Category</th>
            <th>Vendor</th>
            <th>Users</th>
            <th>Data Quality</th>
            <th>Status</th>
            <th>Actions</th>
        </tr>
    </thead>
    <tbody>
        {% for app in applications %}
        <tr class="{{ 'table-warning' if app.needs_investigation else '' }}">
            <td>
                {{ app.data.name }}
                {% if app.needs_investigation %}
                <span class="badge badge-warning" title="Needs manual review">
                    ⚠
                </span>
                {% endif %}
            </td>
            <td>
                {{ app.data.category or 'Unknown' }}

                <!-- Enrichment status badge -->
                {% if app.is_enriched %}
                <span class="badge badge-success" title="Enriched: {{ app.enrichment_method }}">
                    ✓ {{ app.enrichment_confidence }}
                </span>
                {% else %}
                <span class="badge badge-secondary" title="Not enriched">
                    - None
                </span>
                {% endif %}
            </td>
            <td>{{ app.data.vendor or '-' }}</td>
            <td>{{ app.data.users or '-' }}</td>
            <td>
                {% set quality = calculate_quality(app) %}
                <div class="quality-indicator quality-{{ quality_class(quality) }}"
                     title="Extraction: {{ app.extraction_quality|round(2) }}, Enrichment: {{ app.enrichment_confidence }}">
                    {{ (quality * 100)|int }}%

                    <!-- Quality breakdown tooltip -->
                    <div class="quality-tooltip">
                        <strong>Quality Breakdown:</strong>
                        <ul>
                            <li>Extraction: {{ (app.extraction_quality * 100)|int }}%</li>
                            <li>Enrichment: {{ app.enrichment_confidence }}</li>
                            <li>Entity: {{ 'Validated' if app.entity_validated else 'Inferred' }}</li>
                        </ul>
                    </div>
                </div>
            </td>
            <td>
                {% if app.needs_investigation %}
                <span class="badge badge-warning">Needs Review</span>
                {% else %}
                <span class="badge badge-success">Validated</span>
                {% endif %}
            </td>
            <td>
                <!-- Source fact link -->
                {% if app.source_fact_ids %}
                <a href="{{ url_for('facts.view_fact', fact_id=app.source_fact_ids[0]) }}"
                   class="btn btn-sm btn-outline-primary"
                   title="View source fact">
                    <i class="fa fa-file-text"></i> Source
                </a>
                {% endif %}

                <!-- Manual enrichment -->
                {% if app.needs_investigation %}
                <button class="btn btn-sm btn-warning"
                        onclick="openEnrichmentModal('{{ app.item_id }}')">
                    <i class="fa fa-edit"></i> Review
                </button>
                {% endif %}

                <!-- Cost breakdown -->
                <button class="btn btn-sm btn-info"
                        onclick="showCostBreakdown('{{ app.item_id }}')">
                    <i class="fa fa-calculator"></i> Costs
                </button>
            </td>
        </tr>
        {% endfor %}
    </tbody>
</table>
```

**CSS for quality indicators:**

```css
/* Data quality indicators */
.quality-indicator {
    display: inline-block;
    padding: 4px 8px;
    border-radius: 4px;
    font-weight: bold;
    cursor: help;
}

.quality-high {
    background-color: #d4edda;
    color: #155724;
}

.quality-medium {
    background-color: #fff3cd;
    color: #856404;
}

.quality-low {
    background-color: #f8d7da;
    color: #721c24;
}

.quality-tooltip {
    display: none;
    position: absolute;
    background: white;
    border: 1px solid #ccc;
    padding: 10px;
    border-radius: 4px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    z-index: 1000;
}

.quality-indicator:hover .quality-tooltip {
    display: block;
}

/* Needs investigation rows */
.table-warning {
    background-color: #fff3cd !important;
}
```

### 4. Source Tracing

**Link back to source facts and documents:**

```python
# web/blueprints/facts.py

@bp.route('/facts/<fact_id>')
def view_fact(fact_id: str):
    """View fact details including source document."""
    fact_store = get_fact_store()
    fact = fact_store.get_fact(fact_id)

    if not fact:
        abort(404)

    return render_template('fact_detail.html', fact=fact)
```

**Fact detail template:**

```html
<!-- web/templates/fact_detail.html -->
<div class="fact-detail">
    <h3>Fact: {{ fact.fact_id }}</h3>

    <table class="table">
        <tr>
            <th>Domain</th>
            <td>{{ fact.domain }}</td>
        </tr>
        <tr>
            <th>Entity</th>
            <td><span class="badge">{{ fact.entity }}</span></td>
        </tr>
        <tr>
            <th>Content</th>
            <td>{{ fact.content }}</td>
        </tr>
        <tr>
            <th>Confidence</th>
            <td>{{ fact.confidence }}</td>
        </tr>
        <tr>
            <th>Source Document</th>
            <td>
                <a href="{{ url_for('documents.view', doc_id=fact.source_doc_id) }}">
                    {{ fact.source_file }}
                </a>
                {% if fact.source_page %}
                (Page {{ fact.source_page }})
                {% endif %}
            </td>
        </tr>
        <tr>
            <th>Evidence</th>
            <td>
                <pre>{{ fact.evidence }}</pre>
            </td>
        </tr>
    </table>

    <h4>Linked Inventory Items</h4>
    <ul>
        {% for item in get_inventory_items_from_fact(fact.fact_id) %}
        <li>
            <a href="{{ url_for('inventory.view_item', item_id=item.item_id) }}">
                {{ item.data.name }}
            </a>
        </li>
        {% endfor %}
    </ul>
</div>
```

### 5. Manual Enrichment Modal

**Allow users to manually enrich low-quality items:**

```html
<!-- Enrichment modal -->
<div class="modal" id="enrichmentModal">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5>Manual Enrichment: <span id="enrichment-app-name"></span></h5>
            </div>
            <div class="modal-body">
                <form id="enrichment-form">
                    <input type="hidden" id="enrichment-item-id">

                    <div class="form-group">
                        <label>Category</label>
                        <select class="form-control" id="enrichment-category">
                            <option value="">Select category...</option>
                            <option value="erp">ERP</option>
                            <option value="crm">CRM</option>
                            <option value="collaboration">Collaboration</option>
                            <!-- ... all categories -->
                        </select>
                    </div>

                    <div class="form-group">
                        <label>Vendor</label>
                        <input type="text" class="form-control" id="enrichment-vendor">
                    </div>

                    <div class="form-group">
                        <label>Complexity</label>
                        <select class="form-control" id="enrichment-complexity">
                            <option value="simple">Simple</option>
                            <option value="medium">Medium</option>
                            <option value="complex">Complex</option>
                            <option value="critical">Critical</option>
                        </select>
                    </div>

                    <div class="form-group">
                        <label>Deployment Type</label>
                        <select class="form-control" id="enrichment-deployment">
                            <option value="saas">SaaS</option>
                            <option value="on_prem">On-Premise</option>
                            <option value="hybrid">Hybrid</option>
                            <option value="custom">Custom</option>
                        </select>
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" data-dismiss="modal">Cancel</button>
                <button class="btn btn-primary" onclick="saveEnrichment()">Save</button>
            </div>
        </div>
    </div>
</div>
```

**Backend endpoint:**

```python
# web/blueprints/inventory.py

@bp.route('/inventory/<item_id>/enrich', methods=['POST'])
def manual_enrich(item_id: str):
    """Manually enrich inventory item."""
    inv_store = get_inventory_store()
    item = inv_store.get_item(item_id)

    if not item:
        abort(404)

    # Get enrichment data from form
    data = request.json
    item.data['category'] = data.get('category')
    item.data['vendor'] = data.get('vendor')
    item.data['complexity'] = data.get('complexity')
    item.data['deployment_type'] = data.get('deployment_type')

    # Mark as manually enriched
    item.is_enriched = True
    item.enrichment_method = 'manual'
    item.enrichment_confidence = 'high'
    item.needs_investigation = False

    # Save
    inv_store.update_item(item)

    return jsonify({'success': True, 'item_id': item_id})
```

### 6. Cost Breakdown Modal

**Show per-app cost breakdown:**

```html
<!-- Cost breakdown modal -->
<div class="modal" id="costModal">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <div class="modal-header">
                <h5>Cost Breakdown: <span id="cost-app-name"></span></h5>
            </div>
            <div class="modal-body">
                <table class="table">
                    <tr>
                        <th>Base Cost</th>
                        <td>${{ cost.base_cost|format_currency }}</td>
                    </tr>
                    <tr>
                        <th>Complexity Multiplier</th>
                        <td>{{ cost.complexity }} ({{ cost.complexity_multiplier }}x)</td>
                    </tr>
                    <tr>
                        <th>Category Multiplier</th>
                        <td>{{ cost.category }} ({{ cost.category_multiplier }}x)</td>
                    </tr>
                    <tr>
                        <th>Deployment Multiplier</th>
                        <td>{{ cost.deployment_type }} ({{ cost.deployment_multiplier }}x)</td>
                    </tr>
                    <tr>
                        <th>Deal Type Multiplier</th>
                        <td>{{ deal_type }} ({{ cost.deal_multiplier }}x)</td>
                    </tr>
                    <tr class="table-info">
                        <th>One-Time Base</th>
                        <td>${{ cost.one_time_base|format_currency }}</td>
                    </tr>
                </table>

                <h6>Integration Costs</h6>
                <table class="table">
                    <tr>
                        <td>API Integrations ({{ cost.api_count }})</td>
                        <td>${{ cost.api_integration_cost|format_currency }}</td>
                    </tr>
                    <tr>
                        <td>SSO Integration</td>
                        <td>${{ cost.sso_cost|format_currency }}</td>
                    </tr>
                    <tr>
                        <td>Data Migration ({{ cost.data_volume_gb }} GB)</td>
                        <td>${{ cost.data_migration_cost|format_currency }}</td>
                    </tr>
                    <tr class="table-info">
                        <th>Total Integration</th>
                        <td>${{ cost.integration_total|format_currency }}</td>
                    </tr>
                </table>

                {% if cost.tsa_total > 0 %}
                <h6>TSA Costs (Carveout)</h6>
                <table class="table">
                    <tr>
                        <td>Monthly TSA</td>
                        <td>${{ cost.tsa_monthly|format_currency }}</td>
                    </tr>
                    <tr>
                        <td>Duration</td>
                        <td>{{ cost.tsa_duration }} months</td>
                    </tr>
                    <tr class="table-info">
                        <th>Total TSA</th>
                        <td>${{ cost.tsa_total|format_currency }}</td>
                    </tr>
                </table>
                {% endif %}

                <h5 class="mt-4">Grand Total: ${{ cost.grand_total|format_currency }}</h5>
            </div>
        </div>
    </div>
</div>
```

---

## Verification Strategy

### Unit Tests

```python
# tests/unit/test_ui_enrichment_status.py

def test_calculate_quality_score_high():
    """High-quality item (extracted well, enriched, complete) scores >0.8."""
    item = InventoryItem(
        item_id="APP-001",
        inventory_type="application",
        entity="target",
        data={'name': 'SAP', 'category': 'erp', 'vendor': 'SAP AG', 'users': '1000'},
        extraction_quality=0.95,
        is_enriched=True,
        enrichment_confidence='high',
        entity_validated=True
    )

    quality = calculate_data_quality_score(item)
    assert quality > 0.8

def test_calculate_quality_score_low():
    """Low-quality item (poor extraction, not enriched) scores <0.5."""
    item = InventoryItem(
        item_id="APP-002",
        inventory_type="application",
        entity="target",
        data={'name': 'Unknown'},
        extraction_quality=0.4,
        is_enriched=False,
        enrichment_confidence='none',
        entity_validated=False
    )

    quality = calculate_data_quality_score(item)
    assert quality < 0.5
```

### Manual Verification

**UI test scenarios:**

1. **View inventory with high-quality apps**
   - ✅ Quality scores >80% shown in green
   - ✅ Enrichment badges show "✓ high"
   - ✅ No "Needs Review" flags

2. **View inventory with low-quality apps**
   - ✅ Quality scores <50% shown in red
   - ✅ Rows highlighted in yellow
   - ✅ "⚠ Needs Review" badges visible

3. **Click "View Source" link**
   - ✅ Opens fact detail page
   - ✅ Shows source document link
   - ✅ Shows evidence snippet

4. **Click "Manual Review" button**
   - ✅ Opens enrichment modal
   - ✅ Pre-fills existing values
   - ✅ Saves updates to inventory

5. **Click "Costs" button**
   - ✅ Opens cost breakdown modal
   - ✅ Shows all multipliers
   - ✅ Shows integration costs

---

## Benefits

### User Trust
- **Transparency:** Users see exactly how confident the system is
- **Traceability:** Can trace data back to source documents
- **Control:** Manual enrichment when automated enrichment fails

### Data Quality
- **Visual flags:** Low-quality data highlighted immediately
- **Actionable:** "Needs Review" items have clear next action
- **Audit trail:** Enrichment method logged (deterministic/LLM/manual)

### Cost Visibility
- **Per-app breakdown:** Users understand why SAP costs $500K and Slack costs $8K
- **Transparency:** All multipliers and drivers shown
- **Defensibility:** Can explain costs to stakeholders

---

## Expectations

### Success Criteria

- [ ] Enrichment status badges displayed for all apps
- [ ] Data quality score calculated and shown
- [ ] "Needs investigation" rows visually highlighted
- [ ] Source fact links functional
- [ ] Manual enrichment modal works
- [ ] Cost breakdown modal shows all multipliers
- [ ] UI tested with 5 users (usability validation)

---

## Results Criteria

### Acceptance Criteria

1. **InventoryItem metadata fields** added (is_enriched, enrichment_confidence, etc.)
2. **Data quality score** calculated and displayed
3. **UI template updated** with badges, quality indicators, action buttons
4. **Manual enrichment modal** functional
5. **Cost breakdown modal** shows per-app costs
6. **Source tracing** links to facts and documents

---

## Related Documents

- **00-overview-applications-enhancement.md** - Architecture overview
- **02-table-parser-robustness.md** - Extraction quality score (input)
- **04-cost-engine-inventory-integration.md** - Cost breakdown data (input)

---

**Document Status:** ✅ Complete
**Last Updated:** 2026-02-11
**Next Document:** 06-testing-validation.md
