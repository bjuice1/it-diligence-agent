# Spec 05: Business Context UI & Report Section

**Feature Area:** Business Context
**Status:** Draft
**Dependencies:** Spec 01 (Company Profile), Spec 02 (Industry Classification), Spec 03 (Industry Templates), Spec 04 (Benchmark Engine)
**Consumed by:** End users (PE analysts, IT DD practitioners) via web UI and HTML export

---

## Overview

Render business context as the FIRST section users see -- before risks, work items, or costs. Present structured Expected/Observed/Variance data, not prose. Every assertion shows confidence + provenance. Deal-lens selector changes emphasis. This covers both the web UI page AND the HTML export report section.

The Business Context page answers the question every PE deal team asks first: *"What is this company, and how does its IT stack up against what we would expect?"* It synthesizes the outputs of Specs 01-04 into five visual sections: Company Profile Card, Benchmark Metrics Table, Expected Technology Stack, Staffing Comparison, and Deal Lens Panel. Each data point carries a confidence indicator and expandable provenance trail so analysts can verify any assertion against source documents.

This spec does NOT introduce new computation logic. It consumes the structured outputs of the four preceding specs and renders them. The rendering layer is intentionally decoupled from the data layer: if the data models change shape, only the service adapter and templates need updating.

---

## Architecture

### New Files

| File | Purpose |
|------|---------|
| `web/templates/business_context/overview.html` | Main page template -- extends `base.html`, renders all 5 sections |
| `web/templates/business_context/components/profile_card.html` | Jinja2 include -- Company Profile Card (Section 1) |
| `web/templates/business_context/components/metrics_table.html` | Jinja2 include -- Benchmark Metrics Table (Section 2) |
| `web/templates/business_context/components/system_table.html` | Jinja2 include -- Expected Technology Stack (Section 3) |
| `web/templates/business_context/components/staffing_table.html` | Jinja2 include -- Staffing Comparison (Section 4) |
| `web/templates/business_context/components/deal_lens_panel.html` | Jinja2 include -- Deal Lens Panel (Section 5) |
| `web/templates/business_context/components/provenance_panel.html` | Jinja2 include -- Expandable provenance detail (reusable) |
| `web/routes/business_context.py` | Flask blueprint -- page route + deal-lens API endpoint |
| `web/static/css/business_context.css` | Component-scoped CSS for all Business Context views |
| `web/services/business_context_service.py` | Orchestration service -- calls Specs 01-04 and assembles `BusinessContext` view model |

### Modified Files

| File | Change |
|------|--------|
| `web/templates/base.html` | Add "Business Context" nav link as first item after "Dashboard" in `.nav-links` |
| `web/templates/dashboard.html` | Add Business Context summary card as FIRST card in metrics area |
| `web/routes/__init__.py` | Register `business_context_bp` blueprint |
| `tools_v2/html_report.py` | Add `_build_business_context_section()` -- renders Section 0 before Executive Summary |

### Data Flow

```
Spec 01: ProfileExtractor ──> CompanyProfile
                                    |
Spec 02: IndustryClassifier ──> IndustryClassification
                                    |
Spec 03: IndustryTemplateStore ──> IndustryTemplate
                                    |
Spec 04: BenchmarkEngine ──> BenchmarkReport
                                    |
                                    v
              BusinessContextService.build_context(deal_id)
                                    |
                                    v
                        BusinessContext (view model)
                          /                    \
                         v                      v
            Flask route renders            html_report.py renders
            Jinja2 templates               inline-CSS HTML section
            (web UI page)                  (exported report)
```

### Integration Boundaries

- **Input:** `deal_id` from session/URL. The service uses this to load the deal's FactStore, InventoryStore, and OrganizationBridge data, then runs Specs 01-04 in sequence.
- **Output:** Rendered HTML (web page or report section). No data is written back to any store by this spec.
- **No LLM calls.** All rendering is deterministic template evaluation against pre-computed data.
- **Timing:** The page loads on demand when a user navigates to `/business-context`. The HTML report section is generated during report export. Both call the same `BusinessContextService.build_context()` method.

---

## Specification

### 1. Business Context Service

The service orchestrates all four preceding specs into a single view model. It lives at `web/services/business_context_service.py`.

```python
"""
Business Context Service

Orchestrates Specs 01-04 to produce a unified BusinessContext view model
for rendering in the web UI and HTML report.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class BusinessContext:
    """
    Unified view model consumed by templates and the report generator.

    This is NOT a persistence model. It is computed fresh on each page load
    from the current state of the deal's stores.
    """
    # Spec 01 output
    profile: Any                        # CompanyProfile instance

    # Spec 02 output
    classification: Any                 # IndustryClassification instance

    # Spec 03 output
    template: Optional[Any] = None      # IndustryTemplate instance (None if no template matched)

    # Spec 04 output
    report: Optional[Any] = None        # BenchmarkReport instance (None if insufficient data)

    # Computed summary fields for dashboard card
    industry_label: str = ""            # e.g., "P&C Insurance (Specialty)"
    industry_confidence: float = 0.0    # 0.0 - 1.0
    size_label: str = ""                # e.g., "Midmarket (~450 emp)"
    it_staff_label: str = ""            # e.g., "12 FTE + 3 MSPs"
    stack_coverage_label: str = ""      # e.g., "9/12 expected"
    metrics_in_range_label: str = ""    # e.g., "4/6 in range"

    # Metadata
    computed_at: str = ""               # ISO timestamp of computation
    previous_report: Optional[Any] = None  # Previous BenchmarkReport for diff (if exists)
    deal_lens: str = "growth"           # Active deal lens
    has_data: bool = False              # Whether any meaningful data exists

    # Source document summary
    source_documents: List[str] = field(default_factory=list)
    signal_count: int = 0               # Total classification signals


class BusinessContextService:
    """
    Orchestrates profile extraction, classification, template selection,
    and benchmark comparison into a renderable BusinessContext.
    """

    def build_context(self, deal_id: str) -> BusinessContext:
        """
        Build complete business context for a deal.

        Executes Specs 01-04 in sequence:
          1. Extract company profile (Spec 01)
          2. Classify industry (Spec 02)
          3. Load industry template (Spec 03)
          4. Compute benchmarks (Spec 04)

        Returns a BusinessContext view model ready for template rendering.
        If any step fails or produces no data, downstream steps degrade
        gracefully -- the view model always has valid (possibly empty) fields.

        Args:
            deal_id: The deal identifier to load data for

        Returns:
            BusinessContext with all available data populated
        """
        from stores.fact_store import FactStore
        from stores.inventory_store import InventoryStore
        from services.organization_bridge import OrganizationBridge
        from services.profile_extractor import ProfileExtractor
        from services.industry_classifier import IndustryClassifier
        from stores.industry_templates import IndustryTemplateStore
        from services.benchmark_engine import BenchmarkEngine

        # Load deal stores
        fact_store = self._load_fact_store(deal_id)
        inventory_store = self._load_inventory_store(deal_id)
        org_bridge = self._load_org_bridge(deal_id)
        deal_context = self._load_deal_context(deal_id)

        ctx = BusinessContext()
        ctx.computed_at = datetime.utcnow().isoformat()
        ctx.deal_lens = self._get_deal_lens(deal_id)

        # Step 1: Extract company profile (Spec 01)
        try:
            extractor = ProfileExtractor(fact_store, inventory_store, org_bridge)
            ctx.profile = extractor.extract(deal_context)
            ctx.has_data = True
        except Exception:
            ctx.profile = None

        # Step 2: Classify industry (Spec 02)
        try:
            classifier = IndustryClassifier(fact_store, inventory_store)
            ctx.classification = classifier.classify(deal_context)
        except Exception:
            ctx.classification = None

        # Step 3: Load industry template (Spec 03)
        if ctx.classification and ctx.profile:
            try:
                template_store = IndustryTemplateStore()
                size_tier = (ctx.profile.size_tier.value
                           if ctx.profile.size_tier and ctx.profile.size_tier.value
                           else "midmarket")
                ctx.template = template_store.get_template(
                    ctx.classification.primary_industry,
                    ctx.classification.sub_industry,
                    size_tier
                )
            except Exception:
                ctx.template = None

        # Step 4: Compute benchmarks (Spec 04)
        if ctx.profile and ctx.classification and ctx.template:
            try:
                engine = BenchmarkEngine(
                    ctx.profile, ctx.classification, ctx.template,
                    fact_store, inventory_store, org_bridge
                )
                ctx.report = engine.compare()
            except Exception:
                ctx.report = None

        # Load previous report for diff display
        ctx.previous_report = self._load_previous_report(deal_id)

        # Compute summary labels for dashboard card
        ctx = self._compute_summary_labels(ctx)

        return ctx

    def set_deal_lens(self, deal_id: str, lens: str) -> None:
        """
        Persist the selected deal lens for this deal.

        Valid lens values: growth, carve_out, platform_add_on, turnaround,
                          take_private, recapitalization

        The lens is stored in the deal's settings JSON column so it
        persists across sessions.

        Args:
            deal_id: The deal to update
            lens: The deal lens identifier
        """
        valid_lenses = {
            "growth", "carve_out", "platform_add_on",
            "turnaround", "take_private", "recapitalization"
        }
        if lens not in valid_lenses:
            raise ValueError(f"Invalid lens '{lens}'. Must be one of: {valid_lenses}")

        from web.services.deal_service import get_deal_service
        service = get_deal_service()
        service.update_deal(deal_id=deal_id, user_id=None, settings={
            "deal_lens": lens
        })

    def _get_deal_lens(self, deal_id: str) -> str:
        """Read persisted deal lens from deal settings. Defaults to 'growth'."""
        from web.services.deal_service import get_deal_service
        service = get_deal_service()
        deal = service.get_deal(deal_id)
        if deal and hasattr(deal, 'settings') and deal.settings:
            return deal.settings.get("deal_lens", "growth")
        return "growth"

    def _compute_summary_labels(self, ctx: BusinessContext) -> BusinessContext:
        """Populate human-readable summary labels for the dashboard card."""
        # Industry label
        if ctx.classification:
            primary = ctx.classification.primary_industry or "Unknown"
            sub = ctx.classification.sub_industry
            ctx.industry_label = f"{primary} ({sub})" if sub else primary
            ctx.industry_confidence = ctx.classification.confidence or 0.0
            ctx.signal_count = len(ctx.classification.evidence_snippets or [])

        # Size label
        if ctx.profile:
            tier = ctx.profile.size_tier.value if ctx.profile.size_tier else "Unknown"
            emp = ctx.profile.employee_count.value if ctx.profile.employee_count else None
            emp_str = f"~{emp} emp" if emp else ""
            ctx.size_label = f"{tier.title()} ({emp_str})" if emp_str else tier.title()

            # IT staff label
            it_count = (ctx.profile.it_headcount.value
                       if ctx.profile.it_headcount and ctx.profile.it_headcount.value
                       else None)
            if it_count is not None:
                ctx.it_staff_label = f"{it_count} FTE"
                # Append MSP count if available from org bridge
                # (MSP count comes from the BenchmarkReport staffing comparisons)

            # Source documents
            all_docs = set()
            for field_name in ["company_name", "revenue", "employee_count",
                             "it_headcount", "it_budget", "geography",
                             "operating_model", "size_tier"]:
                pf = getattr(ctx.profile, field_name, None)
                if pf and hasattr(pf, 'source_documents'):
                    all_docs.update(pf.source_documents)
            ctx.source_documents = sorted(all_docs)

        # Stack coverage
        if ctx.report and ctx.report.system_comparisons:
            total = len(ctx.report.system_comparisons)
            found = sum(1 for s in ctx.report.system_comparisons
                       if s.status in ("found", "partial"))
            ctx.stack_coverage_label = f"{found}/{total} expected"

        # Metrics in range
        if ctx.report and ctx.report.metric_comparisons:
            eligible = [m for m in ctx.report.metric_comparisons if m.eligible]
            in_range = sum(1 for m in eligible
                         if m.variance_category in ("within_range", "normal"))
            ctx.metrics_in_range_label = f"{in_range}/{len(eligible)} in range"

        return ctx

    def _load_fact_store(self, deal_id: str):
        """Load FactStore for the given deal."""
        # Implementation loads from deal-specific data path
        # Uses the same pattern as web/app.py get_session()
        pass

    def _load_inventory_store(self, deal_id: str):
        """Load InventoryStore for the given deal."""
        pass

    def _load_org_bridge(self, deal_id: str):
        """Load OrganizationBridge for the given deal."""
        pass

    def _load_deal_context(self, deal_id: str):
        """Load DealContext for the given deal."""
        pass

    def _load_previous_report(self, deal_id: str):
        """Load previous BenchmarkReport for diff display. Returns None if no previous."""
        pass
```

### 2. Flask Routes

New blueprint at `web/routes/business_context.py`:

```python
"""
Business Context Routes

Flask blueprint providing the Business Context page and API endpoints.
"""

import logging
from flask import Blueprint, render_template, request, jsonify, session
from web.services.business_context_service import BusinessContextService

logger = logging.getLogger(__name__)

business_context_bp = Blueprint('business_context', __name__)


def _get_deal_id():
    """Get the active deal ID from session."""
    return session.get('current_deal_id')


def require_deal(f):
    """Decorator ensuring an active deal is selected."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        deal_id = _get_deal_id()
        if not deal_id:
            from flask import redirect, url_for
            return redirect(url_for('deals.deals_list_page'))
        kwargs['deal_id'] = deal_id
        return f(*args, **kwargs)
    return decorated


@business_context_bp.route('/business-context')
@require_deal
def overview(deal_id):
    """
    Main business context page.

    Renders the full business context view with all 5 sections:
    1. Company Profile Card
    2. Benchmark Metrics Table
    3. Expected Technology Stack
    4. Staffing Comparison
    5. Deal Lens Panel

    Gracefully degrades when data is missing -- each section
    independently checks for its required data and shows an
    appropriate empty state if unavailable.
    """
    service = BusinessContextService()
    try:
        context = service.build_context(deal_id)
    except Exception as e:
        logger.error(f"Failed to build business context for deal {deal_id}: {e}")
        context = None

    return render_template(
        'business_context/overview.html',
        context=context,
        deal_id=deal_id
    )


@business_context_bp.route('/api/business-context/deal-lens', methods=['POST'])
@require_deal
def set_deal_lens(deal_id):
    """
    Set or change the deal lens for the active deal.

    Request body:
        {"lens": "carve_out"}

    Valid lens values:
        growth, carve_out, platform_add_on, turnaround,
        take_private, recapitalization

    The lens persists in deal settings and is used to filter
    deal-lens considerations shown on the Business Context page.
    Returns the updated context for the Deal Lens Panel so the
    frontend can re-render without a full page reload.
    """
    data = request.get_json() or {}
    lens = data.get('lens', 'growth')

    service = BusinessContextService()
    try:
        service.set_deal_lens(deal_id, lens)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Failed to set deal lens: {e}")
        return jsonify({"error": "Internal error"}), 500

    return jsonify({"status": "ok", "lens": lens})
```

**Blueprint Registration** -- update `web/routes/__init__.py`:

```python
"""
Routes Package

Flask Blueprints for organized route management.
"""

from web.routes.deals import deals_bp
from web.routes.business_context import business_context_bp

__all__ = ['deals_bp', 'business_context_bp']
```

Register in the application factory (in `web/app.py` or wherever blueprints are registered):

```python
app.register_blueprint(business_context_bp)
```

### 3. Page Layout

The `/business-context` page extends `base.html` and renders five sections vertically. Each section is a Jinja2 include that receives the `context` object and renders independently.

#### 3.1 Main Template: `overview.html`

```html
{% extends "base.html" %}
{% block title %}Business Context - IT Due Diligence{% endblock %}

{% block head %}
<link rel="stylesheet" href="{{ url_for('static', filename='css/business_context.css') }}">
{% endblock %}

{% block content %}
<div class="page-header">
    <div class="bc-header-row">
        <div>
            <h1>Business Context</h1>
            <p class="text-muted">Industry benchmarks, expected technology stack, and deal-lens analysis</p>
        </div>
        <div class="bc-header-actions">
            <span class="bc-computed-at text-muted text-sm" title="Last computed">
                {% if context and context.computed_at %}
                    Computed {{ context.computed_at[:16] }}
                {% endif %}
            </span>
        </div>
    </div>
</div>

{% if not context or not context.has_data %}
<!-- ============================================================
     EMPTY STATE
     ============================================================ -->
<div class="card bc-empty-state">
    <div class="bc-empty-icon">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none"
             stroke="currentColor" stroke-width="1.5">
            <rect x="3" y="3" width="18" height="18" rx="2"/>
            <path d="M3 9h18"/>
            <path d="M9 21V9"/>
        </svg>
    </div>
    <h2>Business Context Not Available</h2>
    <p>
        Business Context will be available after running analysis.
        Upload documents and run analysis to generate company profile,
        industry benchmarks, and technology stack comparison.
    </p>
    <a href="{{ url_for('upload_documents') }}" class="btn btn-primary">
        Upload Documents
    </a>
</div>

{% else %}
<!-- ============================================================
     WHAT CHANGED SECTION (only if previous report exists)
     ============================================================ -->
{% if context.previous_report %}
<details class="bc-what-changed">
    <summary class="bc-what-changed-summary">
        What Changed Since Last Run
    </summary>
    <div class="bc-what-changed-body" id="what-changed-body">
        <!-- Populated by comparing context.report vs context.previous_report -->
        <!-- Rendered server-side by the template -->
    </div>
</details>
{% endif %}

<!-- ============================================================
     SECTION 1: COMPANY PROFILE CARD
     ============================================================ -->
{% include "business_context/components/profile_card.html" %}

<!-- ============================================================
     SECTION 2: BENCHMARK METRICS TABLE
     ============================================================ -->
{% include "business_context/components/metrics_table.html" %}

<!-- ============================================================
     SECTION 3: EXPECTED TECHNOLOGY STACK
     ============================================================ -->
{% include "business_context/components/system_table.html" %}

<!-- ============================================================
     SECTION 4: STAFFING COMPARISON
     ============================================================ -->
{% include "business_context/components/staffing_table.html" %}

<!-- ============================================================
     SECTION 5: DEAL LENS PANEL
     ============================================================ -->
{% include "business_context/components/deal_lens_panel.html" %}

{% endif %}

<!-- ============================================================
     JAVASCRIPT: Provenance expansion + Deal Lens selector
     ============================================================ -->
<script>
document.addEventListener('DOMContentLoaded', function() {
    // Provenance expansion
    document.querySelectorAll('[data-provenance-toggle]').forEach(function(el) {
        el.addEventListener('click', function(e) {
            e.preventDefault();
            var targetId = this.getAttribute('data-provenance-toggle');
            var panel = document.getElementById(targetId);
            if (panel) {
                var isExpanded = panel.style.display !== 'none';
                panel.style.display = isExpanded ? 'none' : 'block';
                this.setAttribute('aria-expanded', !isExpanded);
            }
        });
    });

    // Deal Lens selector
    var lensSelect = document.getElementById('deal-lens-select');
    if (lensSelect) {
        lensSelect.addEventListener('change', function() {
            var lens = this.value;
            fetch('/api/business-context/deal-lens', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({lens: lens})
            })
            .then(function(resp) { return resp.json(); })
            .then(function(data) {
                if (data.status === 'ok') {
                    // Reload to show updated deal lens considerations
                    window.location.reload();
                }
            })
            .catch(function(err) {
                console.error('Failed to update deal lens:', err);
            });
        });
    }
});
</script>
{% endblock %}
```

#### 3.2 Section 1: Company Profile Card

Template: `web/templates/business_context/components/profile_card.html`

Renders a two-column grid of profile fields, each with a confidence dot and hover tooltip. An expandable footer shows classification evidence snippets from Spec 02.

```
+---------------------------------------------------------+
|  COMPANY PROFILE                     [N] signals        |
+--------------------------+------------------------------+
|  Company:  Acme Ins      |  Industry:  P&C Insurance .G |
|  Revenue:  ~$200M    .Y  |  Sub:       Specialty     .G |
|  Employees: ~450     .G  |  Secondary: Technology    .Y |
|  IT Staff:  12 FTE   .G  |  Geography: US (3 sites) .Y |
|  IT Budget: ~$8M     .Y  |  Model:     Hybrid       .G |
|  Size Tier: Midmkt       |  Confidence: 0.87            |
+--------------------------+------------------------------+
|  Sources: org-chart.pdf, budget-2025.xlsx, ...          |
|  Classification: 14 evidence signals (expand)           |
+---------------------------------------------------------+

.G = green confidence dot (document_sourced)
.Y = yellow confidence dot (inferred)
.R = gray confidence dot (default/template)
```

Each field cell is structured as:

```html
<div class="bc-profile-field"
     data-provenance-toggle="prov-{{ field_key }}"
     role="button" tabindex="0"
     aria-expanded="false"
     title="Click for provenance details">
    <span class="bc-profile-label">{{ label }}</span>
    <span class="bc-profile-value">{{ value }}</span>
    <span class="bc-confidence-dot bc-confidence-{{ confidence_class }}"
          aria-label="{{ confidence_label }}">
    </span>
</div>
<div class="bc-provenance-panel" id="prov-{{ field_key }}"
     style="display: none;" role="region" aria-label="Provenance for {{ label }}">
    {% include "business_context/components/provenance_panel.html" %}
</div>
```

**Confidence dot mapping** (from `ProfileField.provenance`):

| Provenance | CSS Class | Visual | Aria Label |
|------------|-----------|--------|------------|
| `document_sourced` | `bc-confidence-high` | Green filled circle | "Document-sourced (high confidence)" |
| `user_specified` | `bc-confidence-high` | Green filled circle | "User-specified (high confidence)" |
| `inferred` | `bc-confidence-medium` | Yellow/amber filled circle | "Inferred (medium confidence)" |
| `default` | `bc-confidence-low` | Gray filled circle | "Default value (low confidence)" |

**Profile fields rendered** (in order, two-column layout):

| Column 1 | Column 2 |
|----------|----------|
| `company_name` -- "Company" | `industry` (from classification) -- "Industry" |
| `revenue` -- "Revenue" | `sub_industry` -- "Sub-Industry" |
| `employee_count` -- "Employees" | `secondary_industries` -- "Secondary" |
| `it_headcount` -- "IT Staff" | `geography` -- "Geography" |
| `it_budget` -- "IT Budget" | `operating_model` -- "Model" |
| `size_tier` -- "Size Tier" | Classification `confidence` -- "Confidence" |

**Expandable classification evidence section:**

When the user clicks "Classification: N evidence signals (expand)", a `<details>` element opens showing the `evidence_snippets` list from `IndustryClassification` (Spec 02). Each snippet shows:

- The evidence text (truncated to 200 chars)
- The signal type (e.g., "industry_vertical_app", "regulatory_keyword", "trigger_word")
- The source fact ID and document

The `signal_breakdown` dict from Spec 02 is rendered as a mini bar chart showing relative signal weights per industry considered.

#### 3.3 Section 2: Benchmark Metrics Table

Template: `web/templates/business_context/components/metrics_table.html`

Renders a table of all `MetricComparison` objects from `BenchmarkReport.metric_comparisons`. Eligible metrics are shown in the main table. Ineligible metrics are shown in a collapsed section below.

**Table columns:**

| Column | Source Field | Width |
|--------|-------------|-------|
| Metric | `metric_label` | 20% |
| Industry Range | `expected_low` -- `expected_high` (with `unit`) | 15% |
| Observed | `observed_formatted` | 12% |
| Variance | `variance_category` (rendered as colored dot + label) | 12% |
| Implication | `implication` | 30% |
| Confidence | `confidence` (rendered as dot) | 6% |

**Variance indicator colors:**

| `variance_category` Value | CSS Class | Color | Dot + Label |
|--------------------------|-----------|-------|-------------|
| `within_range` or `normal` | `bc-variance-within` | `#16a34a` (green-600) | Green dot + "Normal" |
| `low_end` or `high_end` | `bc-variance-edge` | `#ca8a04` (yellow-600) | Yellow dot + "Low"/"High" |
| `below_range` or `above_range` | `bc-variance-outside` | `#ea580c` (orange-600) | Orange dot + "Below"/"Above" |
| `far_below` or `far_above` | `bc-variance-far-outside` | `#dc2626` (red-600) | Red dot + "Significantly Below"/"Significantly Above" |
| `insufficient_data` | `bc-variance-no-data` | `#9ca3af` (gray-400) | Gray dot + "Insufficient Data" |

Each row is clickable (via `data-provenance-toggle`) to expand a provenance panel below the row. The provenance panel for a metric shows:

```
Provenance: {{ metric_label }}
---------------------------------------------
Expected: {{ expected_low }} - {{ expected_high }} {{ unit }}
  Source: {{ provenance.expected_source }}
  Template: {{ template_id }} v{{ version }}

Observed: {{ observed_formatted }}
  Computation: {{ provenance.computation_description }}
  Sources: {{ provenance.source_fact_ids | join(", ") }}
  Documents: {{ provenance.source_documents | join(", ") }}

Confidence: {{ confidence | upper }}
  Rationale: {{ provenance.confidence_rationale }}
```

**Ineligible metrics section:**

Below the main table, a `<details>` element shows ineligible metrics:

```html
<details class="bc-ineligible-metrics">
    <summary>
        Ineligible Metrics ({{ ineligible_count }})
    </summary>
    <div class="bc-ineligible-list">
        {% for metric in ineligible_metrics %}
        <div class="bc-ineligible-item">
            <span class="bc-ineligible-label">{{ metric.metric_label }}</span>
            <span class="bc-ineligible-reason">{{ metric.ineligibility_reason }}</span>
        </div>
        {% endfor %}
    </div>
</details>
```

**Empty state:** If no metrics are available (no `BenchmarkReport` or empty `metric_comparisons`):

```html
<div class="bc-section-empty">
    <p>Benchmark metrics will appear after industry classification and profile extraction complete.</p>
</div>
```

#### 3.4 Section 3: Expected Technology Stack

Template: `web/templates/business_context/components/system_table.html`

Renders `BenchmarkReport.system_comparisons` in two sub-sections: Industry-Critical Systems and General Enterprise Systems. Systems are split based on `expected_criticality` ("critical" = industry-critical, everything else = general enterprise).

**Table columns:**

| Column | Source Field | Width |
|--------|-------------|-------|
| Expected System | `category` + `description` | 22% |
| Status | `status` (badge) | 12% |
| Observed | `observed_system` + `observed_vendor` | 20% |
| Notes | `notes` | 40% |

**Status badges:**

| `status` Value | CSS Class | Visual | Label |
|---------------|-----------|--------|-------|
| `found` | `bc-status-found` | Green filled dot | "Found" |
| `partial` | `bc-status-partial` | Yellow filled dot | "Partial" |
| `not_found` | `bc-status-not-found` | Gray open circle | "Not Found" |

Industry-critical systems are marked with a star indicator in the "Expected System" column.

**Summary line** below the table:

```
Summary: {{ found_count }} of {{ total_count }} expected systems found,
         {{ partial_count }} partial, {{ not_found_count }} not found in data room
```

Note: "Not Found" means "not found in data room" -- NOT "missing." The system may be outsourced, undocumented, or handled by a parent company. The UI never uses the word "missing" for `not_found` systems.

**Empty state:** If no system comparisons exist:

```html
<div class="bc-section-empty">
    <p>Technology stack comparison requires an industry template.
       Run analysis with documents to enable industry classification.</p>
</div>
```

#### 3.5 Section 4: Staffing Comparison

Template: `web/templates/business_context/components/staffing_table.html`

Renders `BenchmarkReport.staffing_comparisons`. Only shown if organization data is available.

**Table columns:**

| Column | Source Field | Width |
|--------|-------------|-------|
| Role Category | `category` | 18% |
| Expected | `expected_label` or `expected_count` | 12% |
| Observed | `observed_count` | 10% |
| Status | `variance` (rendered as colored label) | 12% |
| Staff | `observed_names` (truncated, with tooltip for full list) | 40% |

**Variance status labels:**

| `variance` Value | CSS Class | Label |
|-----------------|-----------|-------|
| `match` | `bc-staffing-match` | "Match" (green) |
| `over` | `bc-staffing-over` | "Over" (blue) |
| `lean` | `bc-staffing-lean` | "Lean" (yellow) |
| `none` | `bc-staffing-none` | "None" (red) |
| `msp` | `bc-staffing-msp` | "MSP" (purple) |
| `unknown` | `bc-staffing-unknown` | "Unknown" (gray) |

**Summary line** below the table:

```
Total IT Staff: {{ total_it_fte }} FTE
{% if msp_count > 0 %} + {{ msp_count }} MSP relationships{% endif %}
```

**Empty state:** If no staffing comparisons or no organization data:

```html
<div class="bc-section-empty">
    <p>Staffing comparison requires organization data.
       Upload org charts or staffing documents to enable this section.</p>
</div>
```

#### 3.6 Section 5: Deal Lens Panel

Template: `web/templates/business_context/components/deal_lens_panel.html`

A dropdown selector for deal thesis plus the relevant considerations from the industry template (`IndustryTemplate.deal_lens_considerations`).

**Lens selector:**

```html
<div class="bc-deal-lens-header">
    <h2>Deal Lens</h2>
    <div class="bc-deal-lens-select-wrapper">
        <label for="deal-lens-select" class="sr-only">Select deal lens</label>
        <select id="deal-lens-select" class="bc-deal-lens-select">
            <option value="growth"
                {{ 'selected' if context.deal_lens == 'growth' }}>
                Growth / Buy-and-Build
            </option>
            <option value="carve_out"
                {{ 'selected' if context.deal_lens == 'carve_out' }}>
                Carve-Out / Divestiture
            </option>
            <option value="platform_add_on"
                {{ 'selected' if context.deal_lens == 'platform_add_on' }}>
                Platform + Add-On
            </option>
            <option value="turnaround"
                {{ 'selected' if context.deal_lens == 'turnaround' }}>
                Turnaround / Operational Improvement
            </option>
            <option value="take_private"
                {{ 'selected' if context.deal_lens == 'take_private' }}>
                Take-Private
            </option>
            <option value="recapitalization"
                {{ 'selected' if context.deal_lens == 'recapitalization' }}>
                Recapitalization
            </option>
        </select>
    </div>
</div>
```

**Considerations list:**

The template filters `IndustryTemplate.deal_lens_considerations` by the active lens and renders each consideration as a list item. If a consideration matches against actual inventory/findings, an annotation is added.

Annotation logic:
1. For each consideration text, search the deal's inventory and facts for keywords mentioned in the consideration.
2. If a match is found, append an annotation line (`->` prefix) with the specific finding.
3. If no match is found, show the consideration without annotation.

```html
<div class="bc-deal-lens-considerations">
    <h3>Key Considerations for {{ lens_display_name }}</h3>
    <ul class="bc-considerations-list">
        {% for item in considerations %}
        <li class="bc-consideration-item">
            <span class="bc-consideration-text">{{ item.consideration }}</span>
            {% if item.annotations %}
            <ul class="bc-consideration-annotations">
                {% for annotation in item.annotations %}
                <li class="bc-annotation">
                    <span class="bc-annotation-arrow" aria-hidden="true">&rarr;</span>
                    {{ annotation }}
                </li>
                {% endfor %}
            </ul>
            {% endif %}
        </li>
        {% endfor %}
    </ul>
</div>
```

Annotations are generated server-side by `BusinessContextService` -- they ONLY reference confirmed inventory items and extracted facts. The service never speculates or infers connections that are not grounded in data. Unmatched considerations are shown without annotations.

**Empty state:** If no template loaded or no deal lens considerations for the selected lens:

```html
<div class="bc-section-empty">
    <p>Deal lens considerations require an industry template.
       Ensure industry classification has completed successfully.</p>
</div>
```

#### 3.7 Provenance Panel (Reusable Component)

Template: `web/templates/business_context/components/provenance_panel.html`

A generic expandable panel used by Sections 1, 2, and 3 to show provenance details for any data point.

```html
{#
   Expected context variables:
   - prov_label: str (e.g., "IT Staff Ratio")
   - prov_expected: str (e.g., "2.0 - 5.5 per 100 employees")
   - prov_expected_source: str (e.g., "Gartner IT Key Metrics 2025 -- Insurance")
   - prov_template_ref: str (e.g., "insurance_p_and_c_midmarket v1.0")
   - prov_observed: str (e.g., "2.7 per 100 employees")
   - prov_computation: str (e.g., "12 IT FTE / 450 total employees x 100")
   - prov_source_facts: list of str (e.g., ["F-TGT-ORG-003 (org-chart.pdf)"])
   - prov_confidence: str (e.g., "HIGH")
   - prov_confidence_rationale: str
#}
<div class="bc-provenance-content">
    <h4 class="bc-provenance-title">Provenance: {{ prov_label }}</h4>
    <div class="bc-provenance-section">
        <div class="bc-provenance-heading">Expected</div>
        <div class="bc-provenance-detail">{{ prov_expected }}</div>
        {% if prov_expected_source %}
        <div class="bc-provenance-source">Source: {{ prov_expected_source }}</div>
        {% endif %}
        {% if prov_template_ref %}
        <div class="bc-provenance-source">Template: {{ prov_template_ref }}</div>
        {% endif %}
    </div>
    <div class="bc-provenance-section">
        <div class="bc-provenance-heading">Observed</div>
        <div class="bc-provenance-detail">{{ prov_observed }}</div>
        {% if prov_computation %}
        <div class="bc-provenance-source">Computation: {{ prov_computation }}</div>
        {% endif %}
        {% for fact_ref in prov_source_facts %}
        <div class="bc-provenance-source">Source: {{ fact_ref }}</div>
        {% endfor %}
    </div>
    <div class="bc-provenance-section">
        <div class="bc-provenance-heading">Confidence: {{ prov_confidence }}</div>
        {% if prov_confidence_rationale %}
        <div class="bc-provenance-detail">{{ prov_confidence_rationale }}</div>
        {% endif %}
    </div>
</div>
```

### 4. CSS Specification

File: `web/static/css/business_context.css`

All classes are prefixed with `bc-` to avoid collisions with the global design system. The stylesheet uses design tokens from `tokens.css` wherever possible.

```css
/* =============================================================================
   Business Context -- Component Styles

   Prefix: bc-
   Design tokens: references tokens.css via var(--*)
   ============================================================================= */

/* ----- Layout ----- */

.bc-header-row {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: var(--space-4);
}

.bc-header-actions {
    flex-shrink: 0;
    text-align: right;
}

.bc-computed-at {
    font-size: var(--text-xs);
    color: var(--text-muted);
}

/* ----- Empty State ----- */

.bc-empty-state {
    text-align: center;
    padding: 60px 40px;
}

.bc-empty-icon {
    color: var(--text-muted);
    margin-bottom: var(--space-4);
}

.bc-empty-state h2 {
    margin-bottom: var(--space-2);
    font-size: var(--text-xl);
    color: var(--text-primary);
}

.bc-empty-state p {
    color: var(--text-muted);
    max-width: 480px;
    margin: 0 auto var(--space-6);
    line-height: var(--leading-relaxed);
}

.bc-section-empty {
    padding: var(--space-6);
    text-align: center;
    color: var(--text-muted);
    font-size: var(--text-sm);
    background: var(--bg-surface-sunken);
    border-radius: var(--radius-lg);
    margin-top: var(--space-3);
}

/* ----- What Changed ----- */

.bc-what-changed {
    background: var(--info-bg);
    border: 1px solid #bae6fd;
    border-radius: var(--radius-lg);
    margin-bottom: var(--space-6);
    overflow: hidden;
}

.bc-what-changed-summary {
    padding: var(--space-3) var(--space-4);
    font-weight: var(--font-semibold);
    font-size: var(--text-sm);
    color: var(--info);
    cursor: pointer;
    list-style: none;
    display: flex;
    align-items: center;
    gap: var(--space-2);
}

.bc-what-changed-summary::-webkit-details-marker {
    display: none;
}

.bc-what-changed-summary::before {
    content: "\25B6";
    font-size: 0.7em;
    transition: transform var(--transition-fast);
}

.bc-what-changed[open] .bc-what-changed-summary::before {
    transform: rotate(90deg);
}

.bc-what-changed-body {
    padding: 0 var(--space-4) var(--space-4);
    font-size: var(--text-sm);
    color: var(--text-secondary);
}

.bc-what-changed-body ul {
    list-style: disc;
    padding-left: var(--space-6);
}

.bc-what-changed-body li {
    margin-bottom: var(--space-1);
}

/* ----- Section Cards ----- */

.bc-section {
    background: var(--bg-surface);
    border: 1px solid var(--border-default);
    border-radius: var(--radius-lg);
    margin-bottom: var(--space-6);
    overflow: hidden;
}

.bc-section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--space-4) var(--space-5);
    border-bottom: 1px solid var(--border-default);
}

.bc-section-header h2 {
    font-size: var(--text-lg);
    font-weight: var(--font-semibold);
    color: var(--text-primary);
    margin: 0;
}

.bc-section-badge {
    font-size: var(--text-xs);
    font-weight: var(--font-medium);
    color: var(--text-muted);
    background: var(--bg-surface-sunken);
    padding: var(--space-1) var(--space-2);
    border-radius: var(--radius-full);
}

.bc-section-body {
    padding: var(--space-4) var(--space-5);
}

/* ----- Profile Card (Section 1) ----- */

.bc-profile-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--space-1) var(--space-8);
}

.bc-profile-field {
    display: flex;
    align-items: baseline;
    gap: var(--space-2);
    padding: var(--space-2) var(--space-2);
    border-radius: var(--radius-md);
    cursor: pointer;
    transition: background var(--transition-fast);
}

.bc-profile-field:hover {
    background: var(--bg-surface-sunken);
}

.bc-profile-label {
    font-size: var(--text-sm);
    color: var(--text-muted);
    min-width: 100px;
    flex-shrink: 0;
}

.bc-profile-value {
    font-size: var(--text-sm);
    font-weight: var(--font-medium);
    color: var(--text-primary);
    flex: 1;
}

/* Confidence Dots */

.bc-confidence-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
    flex-shrink: 0;
    margin-left: var(--space-1);
    position: relative;
    top: -1px;
}

.bc-confidence-high {
    background-color: #16a34a;  /* green-600 */
}

.bc-confidence-medium {
    background-color: #ca8a04;  /* yellow-600 */
}

.bc-confidence-low {
    background-color: #9ca3af;  /* gray-400 */
}

/* Profile Footer */

.bc-profile-footer {
    padding: var(--space-3) var(--space-5);
    border-top: 1px solid var(--border-default);
    font-size: var(--text-xs);
    color: var(--text-muted);
}

.bc-profile-sources {
    margin-bottom: var(--space-2);
}

.bc-profile-sources strong {
    font-weight: var(--font-semibold);
}

.bc-evidence-toggle {
    cursor: pointer;
    color: var(--accent);
    font-weight: var(--font-medium);
}

.bc-evidence-toggle:hover {
    text-decoration: underline;
}

.bc-evidence-panel {
    margin-top: var(--space-3);
    padding: var(--space-3);
    background: var(--bg-surface-sunken);
    border-radius: var(--radius-md);
}

.bc-evidence-snippet {
    padding: var(--space-2) 0;
    border-bottom: 1px solid var(--border-default);
    font-size: var(--text-xs);
}

.bc-evidence-snippet:last-child {
    border-bottom: none;
}

.bc-evidence-type {
    display: inline-block;
    font-size: 0.65rem;
    font-weight: var(--font-semibold);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--accent);
    background: var(--accent-subtle);
    padding: 1px 6px;
    border-radius: var(--radius-sm);
    margin-right: var(--space-2);
}

/* ----- Metrics Table (Section 2) ----- */

.bc-metrics-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    font-size: var(--text-sm);
}

.bc-metrics-table thead th {
    text-align: left;
    padding: var(--space-2) var(--space-3);
    font-weight: var(--font-semibold);
    font-size: var(--text-xs);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-muted);
    background: var(--bg-surface-sunken);
    border-bottom: 1px solid var(--border-default);
    position: sticky;
    top: 0;
}

.bc-metrics-table tbody td {
    padding: var(--space-3);
    border-bottom: 1px solid var(--border-default);
    vertical-align: top;
}

.bc-metrics-table tbody tr {
    cursor: pointer;
    transition: background var(--transition-fast);
}

.bc-metrics-table tbody tr:hover {
    background: var(--bg-surface-sunken);
}

.bc-metric-label {
    font-weight: var(--font-medium);
    color: var(--text-primary);
}

.bc-metric-range {
    color: var(--text-secondary);
    white-space: nowrap;
}

.bc-metric-observed {
    font-weight: var(--font-semibold);
    color: var(--text-primary);
}

/* Variance indicators */

.bc-variance {
    display: flex;
    align-items: center;
    gap: var(--space-1);
    white-space: nowrap;
}

.bc-variance-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
}

.bc-variance-within .bc-variance-dot   { background-color: #16a34a; }
.bc-variance-edge .bc-variance-dot     { background-color: #ca8a04; }
.bc-variance-outside .bc-variance-dot  { background-color: #ea580c; }
.bc-variance-far-outside .bc-variance-dot { background-color: #dc2626; }
.bc-variance-no-data .bc-variance-dot  { background-color: #9ca3af; }

.bc-variance-within .bc-variance-label   { color: #16a34a; }
.bc-variance-edge .bc-variance-label     { color: #ca8a04; }
.bc-variance-outside .bc-variance-label  { color: #ea580c; }
.bc-variance-far-outside .bc-variance-label { color: #dc2626; }
.bc-variance-no-data .bc-variance-label  { color: #9ca3af; }

.bc-metric-implication {
    color: var(--text-secondary);
    font-size: var(--text-xs);
    line-height: var(--leading-normal);
}

/* Ineligible metrics */

.bc-ineligible-metrics {
    margin-top: var(--space-3);
    font-size: var(--text-sm);
}

.bc-ineligible-metrics summary {
    cursor: pointer;
    color: var(--text-muted);
    font-weight: var(--font-medium);
    padding: var(--space-2) 0;
    list-style: none;
}

.bc-ineligible-metrics summary::-webkit-details-marker {
    display: none;
}

.bc-ineligible-metrics summary::before {
    content: "\25B6 ";
    font-size: 0.7em;
    transition: transform var(--transition-fast);
}

.bc-ineligible-metrics[open] summary::before {
    content: "\25BC ";
}

.bc-ineligible-item {
    display: flex;
    gap: var(--space-3);
    padding: var(--space-2) var(--space-3);
    font-size: var(--text-xs);
    color: var(--text-muted);
}

.bc-ineligible-label {
    font-weight: var(--font-medium);
    min-width: 160px;
    flex-shrink: 0;
}

.bc-ineligible-reason {
    font-style: italic;
}

/* ----- System Table (Section 3) ----- */

.bc-system-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    font-size: var(--text-sm);
}

.bc-system-table thead th {
    text-align: left;
    padding: var(--space-2) var(--space-3);
    font-weight: var(--font-semibold);
    font-size: var(--text-xs);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-muted);
    background: var(--bg-surface-sunken);
    border-bottom: 1px solid var(--border-default);
}

.bc-system-table tbody td {
    padding: var(--space-3);
    border-bottom: 1px solid var(--border-default);
    vertical-align: top;
}

.bc-system-critical-star {
    color: var(--accent);
    font-weight: var(--font-bold);
    margin-left: var(--space-1);
    font-size: var(--text-xs);
}

.bc-system-divider td {
    padding: var(--space-2) var(--space-3);
    background: var(--bg-surface-sunken);
    font-weight: var(--font-semibold);
    font-size: var(--text-xs);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-muted);
    border-bottom: 1px solid var(--border-default);
}

/* Status badges */

.bc-status-badge {
    display: inline-flex;
    align-items: center;
    gap: var(--space-1);
    padding: 2px 8px;
    border-radius: var(--radius-full);
    font-size: var(--text-xs);
    font-weight: var(--font-semibold);
    white-space: nowrap;
}

.bc-status-found {
    color: #16a34a;
    background: #f0fdf4;
}

.bc-status-partial {
    color: #ca8a04;
    background: #fefce8;
}

.bc-status-not-found {
    color: #9ca3af;
    background: #f9fafb;
}

.bc-system-observed {
    font-weight: var(--font-medium);
    color: var(--text-primary);
}

.bc-system-notes {
    color: var(--text-secondary);
    font-size: var(--text-xs);
}

.bc-system-summary {
    padding: var(--space-3) var(--space-5);
    border-top: 1px solid var(--border-default);
    font-size: var(--text-sm);
    color: var(--text-secondary);
    background: var(--bg-surface-sunken);
}

/* ----- Staffing Table (Section 4) ----- */

.bc-staffing-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    font-size: var(--text-sm);
}

.bc-staffing-table thead th {
    text-align: left;
    padding: var(--space-2) var(--space-3);
    font-weight: var(--font-semibold);
    font-size: var(--text-xs);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-muted);
    background: var(--bg-surface-sunken);
    border-bottom: 1px solid var(--border-default);
}

.bc-staffing-table tbody td {
    padding: var(--space-3);
    border-bottom: 1px solid var(--border-default);
    vertical-align: top;
}

.bc-staffing-status {
    display: inline-block;
    padding: 2px 8px;
    border-radius: var(--radius-full);
    font-size: var(--text-xs);
    font-weight: var(--font-semibold);
}

.bc-staffing-match   { color: #16a34a; background: #f0fdf4; }
.bc-staffing-over    { color: #2563eb; background: #eff6ff; }
.bc-staffing-lean    { color: #ca8a04; background: #fefce8; }
.bc-staffing-none    { color: #dc2626; background: #fef2f2; }
.bc-staffing-msp     { color: #7c3aed; background: #f5f3ff; }
.bc-staffing-unknown { color: #9ca3af; background: #f9fafb; }

.bc-staffing-names {
    color: var(--text-secondary);
    font-size: var(--text-xs);
}

.bc-staffing-summary {
    padding: var(--space-3) var(--space-5);
    border-top: 1px solid var(--border-default);
    font-size: var(--text-sm);
    color: var(--text-secondary);
    background: var(--bg-surface-sunken);
}

/* ----- Deal Lens Panel (Section 5) ----- */

.bc-deal-lens-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.bc-deal-lens-select-wrapper {
    flex-shrink: 0;
}

.bc-deal-lens-select {
    padding: var(--space-2) var(--space-3);
    border: 1px solid var(--border-default);
    border-radius: var(--radius-md);
    font-size: var(--text-sm);
    color: var(--text-primary);
    background: var(--bg-surface);
    cursor: pointer;
    transition: border-color var(--transition-fast);
    min-width: 200px;
}

.bc-deal-lens-select:hover {
    border-color: var(--accent);
}

.bc-deal-lens-select:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px var(--accent-subtle);
    outline: none;
}

.bc-considerations-list {
    list-style: none;
    padding: 0;
    margin: var(--space-3) 0 0 0;
}

.bc-consideration-item {
    padding: var(--space-3) 0;
    border-bottom: 1px solid var(--border-default);
}

.bc-consideration-item:last-child {
    border-bottom: none;
}

.bc-consideration-text {
    font-size: var(--text-sm);
    color: var(--text-primary);
    font-weight: var(--font-medium);
}

.bc-consideration-text::before {
    content: "\2022";
    color: var(--accent);
    margin-right: var(--space-2);
    font-weight: var(--font-bold);
}

.bc-consideration-annotations {
    list-style: none;
    padding: 0;
    margin: var(--space-2) 0 0 var(--space-5);
}

.bc-annotation {
    display: flex;
    gap: var(--space-2);
    padding: var(--space-1) 0;
    font-size: var(--text-xs);
    color: var(--text-secondary);
}

.bc-annotation-arrow {
    color: var(--accent);
    flex-shrink: 0;
}

/* ----- Provenance Panel (Reusable) ----- */

.bc-provenance-panel {
    overflow: hidden;
}

.bc-provenance-content {
    margin: var(--space-2) 0;
    padding: var(--space-4);
    background: var(--bg-surface-sunken);
    border-radius: var(--radius-md);
    border-left: 3px solid var(--accent);
    font-size: var(--text-xs);
}

.bc-provenance-title {
    font-size: var(--text-sm);
    font-weight: var(--font-semibold);
    color: var(--text-primary);
    margin-bottom: var(--space-3);
    padding-bottom: var(--space-2);
    border-bottom: 1px solid var(--border-default);
}

.bc-provenance-section {
    margin-bottom: var(--space-3);
}

.bc-provenance-section:last-child {
    margin-bottom: 0;
}

.bc-provenance-heading {
    font-weight: var(--font-semibold);
    color: var(--text-secondary);
    margin-bottom: var(--space-1);
}

.bc-provenance-detail {
    color: var(--text-primary);
    margin-bottom: var(--space-1);
}

.bc-provenance-source {
    color: var(--text-muted);
    font-style: italic;
}

/* ----- Loading State ----- */

.bc-loading {
    padding: var(--space-8);
    text-align: center;
}

.bc-loading-steps {
    list-style: none;
    padding: 0;
    display: inline-block;
    text-align: left;
    font-size: var(--text-sm);
}

.bc-loading-step {
    padding: var(--space-1) 0;
    color: var(--text-muted);
}

.bc-loading-step.done {
    color: #16a34a;
}

.bc-loading-step.active {
    color: var(--text-primary);
    font-weight: var(--font-medium);
}

.bc-loading-step::before {
    content: "\25CB ";
    margin-right: var(--space-2);
}

.bc-loading-step.done::before {
    content: "\2713 ";
    color: #16a34a;
}

.bc-loading-step.active::before {
    content: "\25CF ";
    color: var(--accent);
}

/* ----- Responsive Design ----- */

/* Tablet: 768-1024px */
@media (max-width: 1024px) {
    .bc-profile-grid {
        grid-template-columns: 1fr;
    }

    .bc-metrics-table,
    .bc-system-table,
    .bc-staffing-table {
        display: block;
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
    }

    .bc-deal-lens-header {
        flex-direction: column;
        align-items: flex-start;
        gap: var(--space-3);
    }

    .bc-deal-lens-select {
        width: 100%;
    }
}

/* Mobile: <768px */
@media (max-width: 768px) {
    .bc-header-row {
        flex-direction: column;
    }

    .bc-section-body {
        padding: var(--space-3);
    }

    /* Convert tables to card layout on mobile */
    .bc-metrics-table thead,
    .bc-system-table thead,
    .bc-staffing-table thead {
        display: none;
    }

    .bc-metrics-table tbody tr,
    .bc-system-table tbody tr,
    .bc-staffing-table tbody tr {
        display: block;
        padding: var(--space-3);
        margin-bottom: var(--space-2);
        border: 1px solid var(--border-default);
        border-radius: var(--radius-md);
    }

    .bc-metrics-table tbody td,
    .bc-system-table tbody td,
    .bc-staffing-table tbody td {
        display: block;
        padding: var(--space-1) 0;
        border-bottom: none;
        text-align: left;
    }

    .bc-metrics-table tbody td::before,
    .bc-system-table tbody td::before,
    .bc-staffing-table tbody td::before {
        content: attr(data-label);
        font-weight: var(--font-semibold);
        font-size: var(--text-xs);
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        display: block;
        margin-bottom: 2px;
    }

    .bc-profile-label {
        min-width: 80px;
    }
}
```

### 5. Dashboard Integration

Add a Business Context summary card as the FIRST card on the dashboard, before the existing metrics row.

**Location in `web/templates/dashboard.html`:** Insert immediately after the `{% else %}` branch (line ~97 in current codebase, after the empty/pending states), before the `<!-- Metrics Row -->` comment.

**Card HTML:**

```html
<!-- Business Context Summary Card -->
{% if business_context and business_context.has_data %}
<div class="card bc-dashboard-card" style="margin-bottom: var(--space-6); border-left: 4px solid var(--accent);">
    <div class="card-body" style="padding: var(--space-5);">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div>
                <h3 style="font-size: var(--text-lg); font-weight: var(--font-semibold); margin-bottom: var(--space-3); color: var(--text-primary);">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
                         stroke="currentColor" stroke-width="2"
                         style="vertical-align: text-bottom; margin-right: 4px;">
                        <rect x="3" y="3" width="18" height="18" rx="2"/>
                        <path d="M3 9h18"/>
                        <path d="M9 21V9"/>
                    </svg>
                    Business Context
                </h3>
                <div style="display: grid; grid-template-columns: auto auto; gap: var(--space-1) var(--space-6); font-size: var(--text-sm);">
                    <span style="color: var(--text-muted);">Industry:</span>
                    <span style="font-weight: var(--font-medium);">
                        {{ business_context.industry_label }}
                        <span style="color: var(--text-muted);">({{ "%.2f"|format(business_context.industry_confidence) }})</span>
                    </span>

                    <span style="color: var(--text-muted);">Size:</span>
                    <span style="font-weight: var(--font-medium);">{{ business_context.size_label }}</span>

                    <span style="color: var(--text-muted);">IT Staff:</span>
                    <span style="font-weight: var(--font-medium);">{{ business_context.it_staff_label }}</span>

                    <span style="color: var(--text-muted);">Stack Coverage:</span>
                    <span style="font-weight: var(--font-medium);">{{ business_context.stack_coverage_label or 'N/A' }}</span>

                    <span style="color: var(--text-muted);">Metrics:</span>
                    <span style="font-weight: var(--font-medium);">{{ business_context.metrics_in_range_label or 'N/A' }}</span>
                </div>
            </div>
            <a href="{{ url_for('business_context.overview') }}"
               class="btn btn-secondary btn-sm"
               style="white-space: nowrap;">
                View Full Context &rarr;
            </a>
        </div>
    </div>
</div>
{% endif %}
```

The dashboard route must compute the `business_context` summary and pass it to the template. This requires the dashboard route handler to call `BusinessContextService().build_context(deal_id)` and pass the result as `business_context`. If the service fails or no deal is active, `business_context` is `None` and the card is not shown.

### 6. Sidebar Navigation

Update `web/templates/base.html` to add "Business Context" as the first nav link after "Dashboard."

**Current nav-links section** (lines 1316-1329):

```html
<div class="nav-links">
    <a href="{{ url_for('dashboard') }}" class="nav-link ...">Dashboard</a>
    <a href="{{ url_for('risks') }}" class="nav-link ...">Risks</a>
    ...
```

**Updated nav-links section:**

```html
<div class="nav-links">
    <a href="{{ url_for('dashboard') }}" class="nav-link {{ 'active' if request.endpoint == 'dashboard' }}" {% if request.endpoint == 'dashboard' %}aria-current="page"{% endif %}>Dashboard</a>
    <a href="{{ url_for('business_context.overview') }}" class="nav-link {{ 'active' if request.endpoint and 'business_context' in request.endpoint }}" {% if request.endpoint and 'business_context' in request.endpoint %}aria-current="page"{% endif %}>Business Context</a>
    <a href="{{ url_for('risks') }}" class="nav-link {{ 'active' if request.endpoint in ['risks', 'risk_detail'] }}" {% if request.endpoint in ['risks', 'risk_detail'] %}aria-current="page"{% endif %}>Risks</a>
    <!-- ... rest unchanged ... -->
```

### 7. HTML Report Section

Update `tools_v2/html_report.py` to add "Section 0: Business Context" before the existing Executive Summary section. This renders the same data as the web UI but with inline CSS (self-contained, no external stylesheets).

**New function:** `_build_business_context_section()`

This function accepts a `BusinessContext` object (the same view model used by the web templates) and returns an HTML string with all inline styles.

```python
def _build_business_context_section(business_context) -> str:
    """
    Build the Business Context section for the HTML report.

    Renders inline-CSS HTML matching the web UI's Business Context page.
    Uses the same BusinessContext view model but with self-contained styles
    instead of external CSS references.

    Args:
        business_context: BusinessContext view model from BusinessContextService

    Returns:
        HTML string for the Business Context report section.
        Returns empty string if business_context is None or has no data.
    """
    if not business_context or not business_context.has_data:
        return ""

    ctx = business_context

    # --- Profile Card ---
    profile_html = _build_report_profile_card(ctx)

    # --- Metrics Table ---
    metrics_html = _build_report_metrics_table(ctx)

    # --- System Table ---
    systems_html = _build_report_system_table(ctx)

    # --- Staffing Table ---
    staffing_html = _build_report_staffing_table(ctx)

    # --- Deal Lens ---
    deal_lens_html = _build_report_deal_lens(ctx)

    return f'''
    <section id="business-context">
        <h2>Business Context</h2>
        {profile_html}
        {metrics_html}
        {systems_html}
        {staffing_html}
        {deal_lens_html}
    </section>
    '''
```

**Inline style constants** used within the report section (matching the web UI colors):

```python
# Report inline style constants (for _build_business_context_section and its helpers)
_REPORT_STYLES = {
    "confidence_high": "color: #16a34a;",
    "confidence_medium": "color: #ca8a04;",
    "confidence_low": "color: #9ca3af;",
    "variance_within": "color: #16a34a;",
    "variance_edge": "color: #ca8a04;",
    "variance_outside": "color: #ea580c;",
    "variance_far_outside": "color: #dc2626;",
    "variance_no_data": "color: #9ca3af;",
    "status_found": "color: #16a34a; background: #f0fdf4; padding: 2px 8px; border-radius: 999px; font-size: 0.75rem; font-weight: 600;",
    "status_partial": "color: #ca8a04; background: #fefce8; padding: 2px 8px; border-radius: 999px; font-size: 0.75rem; font-weight: 600;",
    "status_not_found": "color: #9ca3af; background: #f9fafb; padding: 2px 8px; border-radius: 999px; font-size: 0.75rem; font-weight: 600;",
    "table": "width: 100%; border-collapse: collapse; font-size: 0.9rem; margin-bottom: 1rem;",
    "th": "text-align: left; padding: 8px 12px; font-weight: 600; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; color: #64748b; background: #f8fafc; border-bottom: 1px solid #e2e8f0;",
    "td": "padding: 10px 12px; border-bottom: 1px solid #e2e8f0; vertical-align: top;",
    "subsection": "margin: 1.5rem 0; padding: 1rem; background: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0;",
    "subsection_title": "font-size: 1rem; font-weight: 600; margin-bottom: 0.75rem; color: #1e293b;",
}
```

**Integration point in `_build_html()`:**

Insert the business context section into the report HTML between the nav and the summary section. Update the nav to include a "Business Context" link:

```python
# In _build_html(), update the nav:
<nav class="nav">
    <a href="#business-context">Business Context</a>
    <a href="#summary">Summary</a>
    <a href="#risks">Risks ({total_risks})</a>
    <a href="#work-items">Work Items ({total_work_items})</a>
    <a href="#facts">Facts ({total_facts})</a>
    <a href="#gaps">Gaps ({total_gaps})</a>
</nav>

# Insert business_context_html before the summary section:
{business_context_html}

<section id="summary">
    <h2>Executive Summary</h2>
    ...
```

The `generate_html_report()` function signature gains an optional `business_context` parameter:

```python
def generate_html_report(
    fact_store: FactStore,
    reasoning_store: ReasoningStore,
    output_dir: Path,
    timestamp: str = None,
    target_name: str = None,
    company_profile: CompanyProfile = None,
    business_context=None  # NEW: BusinessContext from BusinessContextService
) -> Path:
```

If `business_context` is `None`, the section is omitted and the report renders exactly as before (backward compatible).

### 8. Loading State

While the Business Context page is computing (expected <2 seconds), the page initially renders with a loading indicator that is replaced by the actual content once the server response arrives. Since the Flask route is synchronous (computes before rendering), the loading state is only visible if client-side fetching is used. For the initial implementation, the page is server-rendered and the loading state is not shown (the browser shows its standard loading indicator). If page load time exceeds 3 seconds in practice, a future enhancement can add client-side progressive loading via AJAX.

For reference, the loading state design if progressive loading is implemented:

```html
<div class="bc-loading" id="bc-loading">
    <h2 style="margin-bottom: var(--space-4);">Building business context...</h2>
    <ul class="bc-loading-steps">
        <li class="bc-loading-step done">Extracting company profile</li>
        <li class="bc-loading-step done">Classifying industry</li>
        <li class="bc-loading-step done">Loading industry template</li>
        <li class="bc-loading-step active">Computing benchmarks</li>
    </ul>
</div>
```

### 9. What Changed Section (Re-run Diffing)

If this is not the first analysis run for a deal, the page shows a collapsed section at the top comparing the current `BenchmarkReport` against the previous one stored for this deal.

**Diff logic** (implemented in `BusinessContextService`):

The service compares `context.report` against `context.previous_report` and generates a list of change descriptions:

1. **New documents:** Count documents in current source_documents not in previous
2. **Classification change:** Compare primary_industry and confidence
3. **Profile field changes:** Compare each ProfileField value between runs
4. **New/removed systems:** Compare system_comparisons status changes
5. **Metric eligibility changes:** Compare which metrics became eligible/ineligible
6. **Metric value changes:** Compare observed values that shifted

Each change is rendered as a bullet in the What Changed panel:

```html
{% if changes %}
<details class="bc-what-changed">
    <summary class="bc-what-changed-summary">
        What Changed Since Last Run
    </summary>
    <div class="bc-what-changed-body">
        <ul>
            {% for change in changes %}
            <li>{{ change }}</li>
            {% endfor %}
        </ul>
    </div>
</details>
{% endif %}
```

If no previous report exists, the section is not rendered.

### 10. Responsive Design Specification

Three breakpoints match the existing design system:

**Desktop (>1024px):**
- Profile card: 2-column grid
- Tables: Full-width with all columns visible
- Deal lens: Header and select on same row
- Provenance panels: Inline expansion below rows

**Tablet (768px - 1024px):**
- Profile card: Single column (stacked fields)
- Tables: Horizontal scroll wrapper with `-webkit-overflow-scrolling: touch`
- Deal lens: Select stacks below header
- Section padding reduced from `space-5` to `space-4`

**Mobile (<768px):**
- Profile card: Single column, reduced label width
- Tables: Card layout (each row becomes a stacked card with `data-label` pseudo-elements)
- Deal lens: Full-width select
- All sections single column
- Section body padding reduced to `space-3`

The responsive CSS is included in the full `business_context.css` specification above.

### 11. Accessibility

- All interactive elements (confidence dots, provenance toggles, deal lens select) have appropriate `aria-label` attributes
- Provenance panels use `aria-expanded` and `role="region"` for screen reader compatibility
- Color is never the sole indicator -- confidence dots have text labels on hover/focus, variance indicators include text labels alongside colored dots
- Tables use proper `<thead>`, `<tbody>`, `<th scope="col">` markup
- The deal lens select uses a `<label>` with `for` attribute (visually hidden with `.sr-only`)
- Focus states follow the global `*:focus-visible` style from `tokens.css`
- Keyboard navigation: all provenance toggles are `tabindex="0"` and respond to Enter/Space

---

## Benefits

- **Business context FIRST** -- answers "what is this company?" before diving into findings, matching how PE deal teams actually read reports
- **Structured tables, not prose** -- PE teams can scan Expected/Observed/Variance in seconds without reading paragraphs
- **Confidence visible on every assertion** -- green/yellow/gray dots build trust by distinguishing "we know" from "we inferred" from "we defaulted"
- **Deal lens makes it PE-native** -- not a generic industry wiki; considerations are filtered and annotated for the specific deal thesis
- **Provenance expandable** -- clean summary view by default, detailed evidence chain for those who want to verify
- **HTML report integration** -- same structured view appears in exported reports, not just the web UI
- **Graceful degradation** -- each section independently handles missing data with clear empty states, so partial analysis still provides value

---

## Expectations

### Performance
- Page renders in <3 seconds including all 4 spec computations (profile extraction + classification + template load + benchmark comparison)
- `BusinessContextService.build_context()` completes in <2 seconds for a typical deal with ~200 facts
- Template rendering adds <100ms
- Dashboard card adds <500ms to dashboard load (can be cached)

### Functionality
- Business Context card appears as first item on dashboard (before metrics row)
- At least company profile + tech stack table render even with sparse data (missing revenue, missing org data)
- Deal lens persists per deal across sessions (stored in deal settings)
- HTML report includes business context section in exported files when `business_context` parameter is provided
- Changing deal lens via dropdown updates without full page reload (AJAX POST + reload)

### Data Integrity
- Every data point shown on the page traces back to a specific `ProfileField`, `MetricComparison`, `SystemComparison`, or `StaffingComparison` from Specs 01-04
- No data is fabricated or extrapolated by the UI layer
- Confidence dots accurately reflect the `provenance` field from `ProfileField` (Spec 01) or the `confidence` field from comparisons (Spec 04)

---

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Too much information overwhelms the reader | Users skip the page | Medium | Collapsed sections for provenance, ineligible metrics, evidence. Default view is a clean summary with 5 scannable sections. |
| Low confidence on many fields undermines trust | Users distrust all data | Medium | Clearly distinguish "we know" (green) from "we inferred" (yellow) from "we don't know" (gray). Show provenance on click so users can verify. |
| Deal lens annotations are incorrect | Wrong conclusions drawn | Low | Annotations ONLY match against confirmed inventory/findings, never speculate. Unmatched considerations shown without annotation. |
| Page breaks with no data | 500 errors or blank page | Medium | Empty states for every component. `BusinessContextService.build_context()` wraps each step in try/except and degrades gracefully. |
| Performance regression on dashboard | Dashboard loads slowly | Low | Dashboard card computation can be cached per deal. Only recompute when analysis data changes. |
| HTML report grows too large | Export files unwieldy | Low | Business context section adds ~20-40KB of HTML. Manageable alongside existing report sections. |
| Spec 01-04 data model changes break rendering | Template errors | Medium | The `BusinessContextService` acts as an adapter layer. Data model changes are isolated to the service; templates consume the stable `BusinessContext` view model. |

---

## Results Criteria

The following must be true for this spec to be considered complete:

1. **Profile card renders** with all available fields + confidence dots. Clicking any field expands its provenance panel.
2. **Metrics table shows** eligible metrics with Expected/Observed/Variance columns. Variance dots use the correct color for each category.
3. **Ineligible metrics** appear in a collapsed section with human-readable reasons.
4. **Tech stack table** shows Found/Not Found/Partial for all expected systems. Industry-critical systems are marked with a star. Summary line shows counts.
5. **Staffing table** shows role categories with Expected/Observed/Status when organization data is available. Not shown when no org data exists.
6. **Deal lens dropdown** changes displayed considerations without full page reload. Selected lens persists across sessions for the deal.
7. **Provenance expands** on click showing source facts, documents, computation method, and confidence rationale.
8. **Dashboard card** shows industry, size, IT staff, stack coverage, and metrics summary with "View Full Context" link. Card appears as first item before the metrics row.
9. **Sidebar nav** includes "Business Context" as the first item after "Dashboard."
10. **HTML report** export includes a "Business Context" section before the Executive Summary when business context data is available.
11. **Empty state** renders correctly when no analysis exists for the deal.
12. **Responsive layout** works correctly at 1024px (tablet), 768px (small tablet), and 375px (mobile) widths.
13. **No regressions** -- existing pages (dashboard, risks, work items, etc.) continue to function identically.

---

## Appendix A: File Tree (New + Modified)

```
web/
  routes/
    __init__.py                          # MODIFIED - register business_context_bp
    business_context.py                  # NEW - Flask blueprint
  services/
    business_context_service.py          # NEW - orchestration service
  templates/
    base.html                            # MODIFIED - add nav link
    dashboard.html                       # MODIFIED - add summary card
    business_context/
      overview.html                      # NEW - main page
      components/
        profile_card.html                # NEW - Section 1
        metrics_table.html               # NEW - Section 2
        system_table.html                # NEW - Section 3
        staffing_table.html              # NEW - Section 4
        deal_lens_panel.html             # NEW - Section 5
        provenance_panel.html            # NEW - reusable provenance expansion
  static/
    css/
      business_context.css               # NEW - component styles

tools_v2/
  html_report.py                         # MODIFIED - add business context section
```

## Appendix B: Data Model Cross-Reference

This spec consumes the following data models from Specs 01-04. The table shows which UI section uses each model.

| Data Model | Source Spec | UI Section(s) |
|------------|------------|----------------|
| `CompanyProfile` | Spec 01 | Section 1 (Profile Card), Dashboard Card |
| `ProfileField` | Spec 01 | Section 1 (confidence dots, provenance panels) |
| `IndustryClassification` | Spec 02 | Section 1 (industry fields, evidence snippets, signal breakdown) |
| `IndustryTemplate` | Spec 03 | Section 3 (expected systems), Section 4 (expected staffing), Section 5 (deal lens considerations) |
| `BenchmarkReport` | Spec 04 | Sections 2-4 (all comparison tables) |
| `MetricComparison` | Spec 04 | Section 2 (Benchmark Metrics Table) |
| `SystemComparison` | Spec 04 | Section 3 (Expected Technology Stack) |
| `StaffingComparison` | Spec 04 | Section 4 (Staffing Comparison) |

## Appendix C: Deal Lens Identifiers

| Lens ID | Display Name | Description |
|---------|-------------|-------------|
| `growth` | Growth / Buy-and-Build | Organic growth acceleration, scalability assessment |
| `carve_out` | Carve-Out / Divestiture | TSA planning, shared service separation, standalone readiness |
| `platform_add_on` | Platform + Add-On | Integration synergies, system consolidation, migration planning |
| `turnaround` | Turnaround / Operational Improvement | Cost reduction, efficiency gains, technical debt remediation |
| `take_private` | Take-Private | Compliance readiness, reporting changes, IT governance gaps |
| `recapitalization` | Recapitalization | Minimal disruption assessment, contractual risk review |

## Appendix D: Variance Category Mapping

The `variance_category` field on `MetricComparison` (Spec 04) maps to UI indicators as follows:

| `variance_category` | Dot Color | CSS Class | Display Label | Threshold Logic (Spec 04) |
|---------------------|-----------|-----------|---------------|---------------------------|
| `within_range` | `#16a34a` green | `bc-variance-within` | "Normal" | Observed is between `expected_low` and `expected_high` |
| `low_end` | `#ca8a04` yellow | `bc-variance-edge` | "Low" | Observed is within 10% below `expected_low` |
| `high_end` | `#ca8a04` yellow | `bc-variance-edge` | "High" | Observed is within 10% above `expected_high` |
| `below_range` | `#ea580c` orange | `bc-variance-outside` | "Below" | Observed is 10-30% below `expected_low` |
| `above_range` | `#ea580c` orange | `bc-variance-outside` | "Above" | Observed is 10-30% above `expected_high` |
| `far_below` | `#dc2626` red | `bc-variance-far-outside` | "Significantly Below" | Observed is >30% below `expected_low` |
| `far_above` | `#dc2626` red | `bc-variance-far-outside` | "Significantly Above" | Observed is >30% above `expected_high` |
| `insufficient_data` | `#9ca3af` gray | `bc-variance-no-data` | "Insufficient Data" | One or both values missing |
