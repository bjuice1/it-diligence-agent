# Spec 13: Organization Reporting & Dashboard Integration

**Status:** Draft
**Created:** 2026-02-11
**Complexity:** Medium
**Estimated Implementation:** 4-6 hours

---

## Overview

This specification defines how assumption metadata (detection results, confidence scores, assumption basis) surfaces in user-facing outputs: Excel workbooks, HTML reports, web dashboards, and PowerPoint presentations. The goal is **transparent communication** to M&A analysts about what organizational data is observed vs. assumed, enabling informed investment decisions.

**Why this exists:** The adaptive org feature generates valuable metadata (hierarchy detection status, assumption confidence, industry benchmarks used) that analysts need to see to trust the analysis. Without transparent reporting, assumed data looks identical to observed data → analysts can't distinguish fact from inference → undermines credibility.

**Key principle:** Transparency over perfection. Better to show "20 roles (15 observed, 5 assumed based on tech industry benchmarks)" than "20 roles" with no context.

---

## Architecture

### Component Positioning

```
Backend (Specs 08-11)
    ↓
Detection Results + Assumptions Generated
    ↓
Inventory Store (with data_source metadata)
    ↓
[THIS COMPONENT] → Reporting Integration Layer
    ├─→ Excel Exporter (add columns, new worksheet)
    ├─→ HTML Report Generator (badges, panels, tooltips)
    ├─→ Web Dashboard (data quality indicators, assumption cards)
    └─→ Presentation Generator (footnotes, quality slide)
    ↓
User sees transparent, trustworthy analysis
```

### Dependencies

**Input:**
- `HierarchyPresence` from detection (spec 08)
- `OrganizationAssumption[]` from assumption engine (spec 09)
- Inventory items with `data_source`, `confidence_score`, `assumption_basis` (spec 10)
- Bridge status (`success_with_assumptions`, etc.) (spec 11)

**Output:**
- Enhanced Excel workbook with data source columns + Assumptions worksheet
- HTML report with badges, assumption summary panel, tooltips
- Dashboard with data quality indicators, assumption breakdown
- Presentation with footnotes and data quality slide

**Integrates With:**
- `tools_v2/excel_exporter.py` (Excel workbook generation)
- `tools_v2/html_report_generator.py` (HTML report generation)
- `tools_v2/presentation.py` (PowerPoint generation)
- `web/blueprints/organization.py` (dashboard rendering)

---

## Specification

### 1. Excel Workbook Integration

**File:** `tools_v2/excel_exporter.py`

#### 1.1 Organization Inventory Sheet Enhancements

**Current Sheet Columns:**
```
| Name | Role | Team | Department | Headcount | Annual Cost | ... |
```

**Enhanced Sheet Columns (NEW):**
```
| Name | Role | Team | Department | Headcount | Annual Cost | Data Source | Confidence | Assumption Basis |
```

**Column Definitions:**

| Column | Description | Format | Example |
|--------|-------------|--------|---------|
| **Data Source** | Provenance of data | Text with icon | "🟢 Observed" / "🟡 Assumed" / "🔵 Hybrid" |
| **Confidence** | Confidence score | Percentage with color | "95%" (green) / "70%" (yellow) |
| **Assumption Basis** | Why assumed (if applicable) | Text | "Industry benchmark: tech" / "Inferred from role title" / "-" (if observed) |

**Implementation:**

```python
# In excel_exporter.py, _write_organization_sheet()

def _write_organization_sheet(workbook, org_store, detection_results):
    """
    Write organization inventory to Excel with assumption metadata.

    NEW: Includes data_source, confidence, assumption_basis columns
    to show users what's observed vs. assumed.
    """
    ws = workbook.create_sheet("Organization Inventory")

    # Header row (extended with new columns)
    headers = [
        "Name", "Role", "Team", "Department", "Headcount",
        "Annual Cost", "Reports To",
        "Data Source",         # NEW
        "Confidence",          # NEW
        "Assumption Basis"     # NEW
    ]
    ws.append(headers)

    # Style header
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="366092", fill_type="solid")
        cell.font = Font(color="FFFFFF", bold=True)

    # Data rows
    for staff in org_store.staff_members:
        # Determine data source display
        data_source = staff.data_source if hasattr(staff, 'data_source') else 'observed'
        data_source_display = {
            'observed': '🟢 Observed',
            'assumed': '🟡 Assumed',
            'hybrid': '🔵 Hybrid'
        }.get(data_source, '🟢 Observed')

        # Confidence score
        confidence = staff.confidence_score if hasattr(staff, 'confidence_score') else 1.0
        confidence_pct = f"{int(confidence * 100)}%"

        # Assumption basis
        assumption_basis = ""
        if data_source in ['assumed', 'hybrid'] and hasattr(staff, 'assumption_basis'):
            assumption_basis = staff.assumption_basis or ""

        row = [
            staff.name or "",
            staff.role,
            staff.team or "",
            staff.department or "",
            staff.headcount,
            f"${staff.annual_cost:,.0f}" if staff.annual_cost else "",
            staff.reports_to or "",
            data_source_display,   # NEW
            confidence_pct,         # NEW
            assumption_basis        # NEW
        ]
        ws.append(row)

        # Color-code confidence cell
        row_num = ws.max_row
        confidence_cell = ws.cell(row=row_num, column=8)  # Confidence column

        if confidence >= 0.9:
            confidence_cell.fill = PatternFill(start_color="C6EFCE", fill_type="solid")  # Green
        elif confidence >= 0.7:
            confidence_cell.fill = PatternFill(start_color="FFEB9C", fill_type="solid")  # Yellow
        else:
            confidence_cell.fill = PatternFill(start_color="FFC7CE", fill_type="solid")  # Red

    # Auto-size columns
    for column in ws.columns:
        ws.column_dimensions[column[0].column_letter].width = 15
```

#### 1.2 New Worksheet: "Assumptions Summary"

**Purpose:** Dedicated sheet showing all assumptions generated, detection results, and gaps.

**Sheet Structure:**

```
┌─────────────────────────────────────────────────────────────────────┐
│ ORGANIZATION ASSUMPTIONS SUMMARY                                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ Detection Results                                                   │
│ ─────────────────                                                   │
│ Hierarchy Status:        PARTIAL                                    │
│ Detection Confidence:    72%                                        │
│ Roles Analyzed:          25                                         │
│ Roles with Reports-To:   12 (48%)                                   │
│                                                                     │
│ Data Breakdown                                                      │
│ ──────────────                                                      │
│ Observed Items:          18                                         │
│ Assumed Items:           7                                          │
│ Hybrid Items:            0                                          │
│ Total:                   25                                         │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ Assumptions Generated                                               │
│                                                                     │
│ Item              | Category    | Confidence | Basis               │
│ ─────────────────────────────────────────────────────────────────  │
│ Chief Information Officer | leadership | 80% | Standard leadership  │
│ VP of Infrastructure     | leadership | 75% | Industry: tech      │
│ VP of Applications       | leadership | 75% | Industry: tech      │
│ Infrastructure Manager   | roles      | 65% | Team structure      │
│ Applications Manager     | roles      | 65% | Team structure      │
│ Org Depth: 3 layers     | skills     | 70% | Industry: tech      │
│ Span of Control: 6      | skills     | 65% | Industry average    │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ Identified Gaps (for VDR Follow-up)                                │
│                                                                     │
│ 1. Reporting lines (who reports to whom)                           │
│ 2. Span of control (number of direct reports per manager)          │
│ 3. Organization chart or hierarchy diagram                          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Implementation:**

```python
def _write_assumptions_summary_sheet(workbook, detection_results, assumptions, org_store):
    """
    Create dedicated worksheet showing assumption metadata.

    Helps analysts understand:
    - What hierarchy data was found vs missing
    - What assumptions were made and why
    - What gaps to follow up on in VDR
    """
    ws = workbook.create_sheet("Assumptions Summary")

    # Title
    ws.merge_cells('A1:D1')
    title_cell = ws['A1']
    title_cell.value = "ORGANIZATION ASSUMPTIONS SUMMARY"
    title_cell.font = Font(size=14, bold=True)
    title_cell.alignment = Alignment(horizontal='center')

    row = 3

    # Section 1: Detection Results
    ws[f'A{row}'] = "Detection Results"
    ws[f'A{row}'].font = Font(bold=True, size=12)
    row += 1

    ws[f'A{row}'] = "Hierarchy Status:"
    ws[f'B{row}'] = detection_results.status.value.upper()
    row += 1

    ws[f'A{row}'] = "Detection Confidence:"
    ws[f'B{row}'] = f"{int(detection_results.confidence * 100)}%"
    row += 1

    ws[f'A{row}'] = "Roles Analyzed:"
    ws[f'B{row}'] = detection_results.total_role_count
    row += 1

    ws[f'A{row}'] = "Roles with Reports-To:"
    reports_to_pct = (detection_results.roles_with_reports_to /
                      detection_results.total_role_count * 100) if detection_results.total_role_count > 0 else 0
    ws[f'B{row}'] = f"{detection_results.roles_with_reports_to} ({int(reports_to_pct)}%)"
    row += 2

    # Section 2: Data Breakdown
    ws[f'A{row}'] = "Data Breakdown"
    ws[f'A{row}'].font = Font(bold=True, size=12)
    row += 1

    # Count by data source
    observed_count = sum(1 for s in org_store.staff_members if getattr(s, 'data_source', 'observed') == 'observed')
    assumed_count = sum(1 for s in org_store.staff_members if getattr(s, 'data_source', 'observed') == 'assumed')
    hybrid_count = sum(1 for s in org_store.staff_members if getattr(s, 'data_source', 'observed') == 'hybrid')

    ws[f'A{row}'] = "Observed Items:"
    ws[f'B{row}'] = observed_count
    row += 1

    ws[f'A{row}'] = "Assumed Items:"
    ws[f'B{row}'] = assumed_count
    row += 1

    ws[f'A{row}'] = "Hybrid Items:"
    ws[f'B{row}'] = hybrid_count
    row += 1

    ws[f'A{row}'] = "Total:"
    ws[f'B{row}'] = len(org_store.staff_members)
    ws[f'B{row}'].font = Font(bold=True)
    row += 2

    # Section 3: Assumptions Generated
    if assumptions:
        ws[f'A{row}'] = "Assumptions Generated"
        ws[f'A{row}'].font = Font(bold=True, size=12)
        row += 2

        # Table header
        headers = ['Item', 'Category', 'Confidence', 'Basis']
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col_num)
            cell.value = header
            cell.font = Font(bold=True)
        row += 1

        # Assumption rows
        for assumption in assumptions:
            ws.cell(row=row, column=1).value = assumption.item
            ws.cell(row=row, column=2).value = assumption.category
            ws.cell(row=row, column=3).value = f"{int(assumption.confidence * 100)}%"
            ws.cell(row=row, column=4).value = assumption.assumption_basis
            row += 1

        row += 1

    # Section 4: Gaps Identified
    if detection_results.gaps:
        ws[f'A{row}'] = "Identified Gaps (for VDR Follow-up)"
        ws[f'A{row}'].font = Font(bold=True, size=12)
        row += 2

        for i, gap in enumerate(detection_results.gaps, 1):
            ws[f'A{row}'] = f"{i}. {gap}"
            row += 1

    # Auto-size columns
    ws.column_dimensions['A'].width = 30
    ws.column_dimensions['B'].width = 20
    ws.column_dimensions['C'].width = 15
    ws.column_dimensions['D'].width = 30
```

#### 1.3 Integration Point

**Modify:** `tools_v2/excel_exporter.py` main export function

```python
def generate_excel_report(
    fact_store,
    org_store,
    detection_results,  # NEW parameter
    assumptions,        # NEW parameter
    output_path
):
    """Generate Excel workbook with assumption transparency."""

    workbook = Workbook()

    # ... existing sheets (Executive Summary, Applications, etc.) ...

    # Enhanced Organization sheet
    _write_organization_sheet(workbook, org_store, detection_results)

    # NEW: Assumptions Summary sheet
    _write_assumptions_summary_sheet(workbook, detection_results, assumptions, org_store)

    # ... rest of export ...

    workbook.save(output_path)
```

---

### 2. HTML Report Integration

**File:** `tools_v2/html_report_generator.py`

#### 2.1 Organization Section Enhancements

**Add Assumption Summary Panel:**

```html
<!-- NEW: Assumption Summary Panel (appears if assumptions were used) -->
{% if org_analysis.has_assumptions %}
<div class="assumption-summary-panel">
    <h3>📊 Organization Data Quality</h3>

    <div class="detection-status">
        <div class="status-badge status-{{ detection_results.status.value }}">
            {{ detection_results.status.display_name }}
        </div>
        <span class="confidence-score">
            {{ (detection_results.confidence * 100)|int }}% confidence
        </span>
    </div>

    <div class="data-breakdown">
        <div class="breakdown-item">
            <span class="label">Observed:</span>
            <span class="value">{{ observed_count }} items</span>
            <div class="bar" style="width: {{ (observed_count / total_count * 100)|int }}%; background: #28a745;"></div>
        </div>
        <div class="breakdown-item">
            <span class="label">Assumed:</span>
            <span class="value">{{ assumed_count }} items</span>
            <div class="bar" style="width: {{ (assumed_count / total_count * 100)|int }}%; background: #ffc107;"></div>
        </div>
    </div>

    {% if detection_results.gaps %}
    <div class="gaps-section">
        <h4>📋 Data Gaps for VDR Follow-up</h4>
        <ul>
        {% for gap in detection_results.gaps %}
            <li>{{ gap }}</li>
        {% endfor %}
        </ul>
    </div>
    {% endif %}

    <details class="assumptions-detail">
        <summary>View {{ assumed_count }} Assumptions Generated</summary>
        <table class="assumptions-table">
            <thead>
                <tr>
                    <th>Item</th>
                    <th>Category</th>
                    <th>Confidence</th>
                    <th>Basis</th>
                </tr>
            </thead>
            <tbody>
            {% for assumption in assumptions %}
                <tr>
                    <td>{{ assumption.item }}</td>
                    <td>{{ assumption.category }}</td>
                    <td>{{ (assumption.confidence * 100)|int }}%</td>
                    <td>{{ assumption.assumption_basis }}</td>
                </tr>
            {% endfor %}
            </tbody>
        </table>
    </details>
</div>
{% endif %}

<!-- Organization Inventory Table (enhanced) -->
<table class="org-inventory-table">
    <thead>
        <tr>
            <th>Role</th>
            <th>Team</th>
            <th>Headcount</th>
            <th>Annual Cost</th>
            <th>Data Source</th> <!-- NEW -->
        </tr>
    </thead>
    <tbody>
    {% for staff in org_store.staff_members %}
        <tr class="data-source-{{ staff.data_source }}">
            <td>
                {{ staff.role }}
                {% if staff.data_source == 'assumed' %}
                <span class="badge badge-warning"
                      title="Assumed based on {{ staff.assumption_basis }}">
                    Assumed
                </span>
                {% elif staff.data_source == 'hybrid' %}
                <span class="badge badge-info"
                      title="Partially assumed">
                    Partial
                </span>
                {% endif %}
            </td>
            <td>{{ staff.team }}</td>
            <td>{{ staff.headcount }}</td>
            <td>${{ staff.annual_cost|number_format }}</td>
            <td>
                <span class="confidence-indicator"
                      style="background: {{ get_confidence_color(staff.confidence_score) }}">
                    {{ (staff.confidence_score * 100)|int }}%
                </span>
            </td>
        </tr>
    {% endfor %}
    </tbody>
</table>
```

#### 2.2 CSS Styling

```css
/* Assumption Summary Panel */
.assumption-summary-panel {
    background: #f8f9fa;
    border-left: 4px solid #ffc107;
    padding: 20px;
    margin: 20px 0;
    border-radius: 4px;
}

.detection-status {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 15px;
}

.status-badge {
    padding: 8px 16px;
    border-radius: 20px;
    font-weight: bold;
    font-size: 14px;
}

.status-badge.status-full {
    background: #d4edda;
    color: #155724;
}

.status-badge.status-partial {
    background: #fff3cd;
    color: #856404;
}

.status-badge.status-missing {
    background: #f8d7da;
    color: #721c24;
}

.confidence-score {
    font-size: 14px;
    color: #6c757d;
}

/* Data Breakdown Bars */
.data-breakdown {
    margin: 20px 0;
}

.breakdown-item {
    margin-bottom: 10px;
}

.breakdown-item .label {
    display: inline-block;
    width: 100px;
    font-weight: 600;
}

.breakdown-item .value {
    display: inline-block;
    width: 80px;
}

.breakdown-item .bar {
    height: 20px;
    border-radius: 3px;
    margin-top: 5px;
}

/* Gaps Section */
.gaps-section {
    background: #fff;
    border: 1px solid #dee2e6;
    padding: 15px;
    margin-top: 15px;
    border-radius: 4px;
}

.gaps-section h4 {
    margin-top: 0;
    color: #6c757d;
}

.gaps-section ul {
    margin: 10px 0 0 20px;
}

/* Assumptions Detail (Expandable) */
.assumptions-detail {
    margin-top: 20px;
}

.assumptions-detail summary {
    cursor: pointer;
    font-weight: 600;
    padding: 10px;
    background: #e9ecef;
    border-radius: 4px;
}

.assumptions-detail summary:hover {
    background: #dee2e6;
}

.assumptions-table {
    width: 100%;
    margin-top: 10px;
    border-collapse: collapse;
}

.assumptions-table th,
.assumptions-table td {
    padding: 8px;
    border: 1px solid #dee2e6;
    text-align: left;
}

.assumptions-table th {
    background: #f8f9fa;
    font-weight: 600;
}

/* Confidence Indicator */
.confidence-indicator {
    display: inline-block;
    padding: 4px 8px;
    border-radius: 3px;
    color: #fff;
    font-size: 12px;
    font-weight: 600;
}

/* Helper function in template context */
/* get_confidence_color(score):
   - >0.9: #28a745 (green)
   - 0.7-0.9: #ffc107 (yellow)
   - <0.7: #dc3545 (red)
*/
```

#### 2.3 Implementation

```python
# In html_report_generator.py

def generate_org_section(org_store, detection_results, assumptions):
    """
    Generate organization section HTML with assumption transparency.

    NEW: Includes assumption summary panel, badges, confidence indicators.
    """
    # Count by data source
    observed_count = sum(1 for s in org_store.staff_members
                        if getattr(s, 'data_source', 'observed') == 'observed')
    assumed_count = sum(1 for s in org_store.staff_members
                       if getattr(s, 'data_source', 'observed') == 'assumed')
    total_count = len(org_store.staff_members)

    # Check if assumptions were used
    has_assumptions = assumed_count > 0

    # Render template
    template = env.get_template('organization_section.html')
    html = template.render(
        org_store=org_store,
        detection_results=detection_results,
        assumptions=assumptions,
        observed_count=observed_count,
        assumed_count=assumed_count,
        total_count=total_count,
        has_assumptions=has_assumptions,
        get_confidence_color=_get_confidence_color
    )

    return html


def _get_confidence_color(score):
    """Return color hex for confidence score."""
    if score >= 0.9:
        return '#28a745'  # Green
    elif score >= 0.7:
        return '#ffc107'  # Yellow
    else:
        return '#dc3545'  # Red
```

---

### 3. Web Dashboard Integration

**File:** `web/blueprints/organization.py`

#### 3.1 Organization Dashboard Card Enhancement

**Add Data Quality Indicator:**

```html
<!-- Organization Card on Dashboard -->
<div class="card org-card">
    <div class="card-header">
        <h3>Organization</h3>
        <!-- NEW: Data Quality Indicator -->
        <div class="data-quality-badge {{ quality_level }}">
            {{ quality_label }}
        </div>
    </div>

    <div class="card-body">
        <div class="metric">
            <span class="label">Total IT Staff:</span>
            <span class="value">{{ total_staff }}</span>
        </div>

        <div class="metric">
            <span class="label">Annual Personnel Cost:</span>
            <span class="value">${{ total_cost|number_format }}</span>
        </div>

        <!-- NEW: Data Source Breakdown -->
        <div class="data-source-breakdown">
            <div class="breakdown-bar">
                <div class="observed" style="width: {{ observed_pct }}%"></div>
                <div class="assumed" style="width: {{ assumed_pct }}%"></div>
            </div>
            <div class="breakdown-legend">
                <span class="observed-legend">🟢 {{ observed_count }} Observed</span>
                <span class="assumed-legend">🟡 {{ assumed_count }} Assumed</span>
            </div>
        </div>

        <!-- NEW: Expandable Assumptions Section -->
        {% if has_assumptions %}
        <details class="assumptions-expand">
            <summary>View Assumptions Used ({{ assumed_count }})</summary>
            <div class="assumptions-content">
                <div class="detection-info">
                    <strong>Detection:</strong> {{ detection_status }}
                    <span class="confidence">({{ detection_confidence }}% confidence)</span>
                </div>

                <ul class="assumption-list">
                {% for assumption in assumptions[:5] %}
                    <li>
                        <strong>{{ assumption.item }}</strong>
                        <span class="basis">{{ assumption.assumption_basis }}</span>
                    </li>
                {% endfor %}
                </ul>

                {% if assumed_count > 5 %}
                <a href="/organization/assumptions" class="view-all-link">
                    View all {{ assumed_count }} assumptions →
                </a>
                {% endif %}
            </div>
        </details>
        {% endif %}
    </div>
</div>
```

**Quality Level Logic:**

```python
# In organization.py blueprint

def get_data_quality_level(observed_count, assumed_count):
    """
    Determine data quality level based on assumption percentage.

    Returns:
        tuple: (quality_level, quality_label)
        - quality_level: 'high' | 'medium' | 'low'
        - quality_label: 'Mostly Observed' | 'Mixed Data' | 'Mostly Assumed'
    """
    total = observed_count + assumed_count
    if total == 0:
        return 'high', 'No Data'

    assumed_pct = assumed_count / total

    if assumed_pct < 0.1:
        return 'high', 'Mostly Observed'
    elif assumed_pct < 0.4:
        return 'medium', 'Mixed Data'
    else:
        return 'low', 'Mostly Assumed'
```

#### 3.2 New Route: Assumptions Detail Page

```python
# In web/blueprints/organization.py

@org_bp.route('/assumptions')
def view_assumptions():
    """
    Display full assumptions detail page.

    Shows detection results, all assumptions generated,
    gaps identified, and assumption basis explanations.
    """
    # Get current deal
    deal_id = get_current_deal_id()

    # Load org analysis data
    org_store = load_org_store(deal_id)
    detection_results = load_detection_results(deal_id)
    assumptions = load_assumptions(deal_id)

    # Count by data source
    observed_count = sum(1 for s in org_store.staff_members
                        if getattr(s, 'data_source', 'observed') == 'observed')
    assumed_count = sum(1 for s in org_store.staff_members
                       if getattr(s, 'data_source', 'observed') == 'assumed')

    return render_template(
        'organization/assumptions_detail.html',
        detection_results=detection_results,
        assumptions=assumptions,
        observed_count=observed_count,
        assumed_count=assumed_count,
        org_store=org_store
    )
```

**Template:** `web/templates/organization/assumptions_detail.html`

```html
{% extends "base.html" %}

{% block content %}
<div class="assumptions-detail-page">
    <h1>Organization Assumptions</h1>

    <div class="detection-summary">
        <h2>Detection Results</h2>
        <table class="detection-table">
            <tr>
                <th>Hierarchy Status</th>
                <td>
                    <span class="status-badge status-{{ detection_results.status.value }}">
                        {{ detection_results.status.display_name }}
                    </span>
                </td>
            </tr>
            <tr>
                <th>Detection Confidence</th>
                <td>{{ (detection_results.confidence * 100)|int }}%</td>
            </tr>
            <tr>
                <th>Roles Analyzed</th>
                <td>{{ detection_results.total_role_count }}</td>
            </tr>
            <tr>
                <th>Roles with Reporting Lines</th>
                <td>
                    {{ detection_results.roles_with_reports_to }}
                    ({{ (detection_results.roles_with_reports_to / detection_results.total_role_count * 100)|int }}%)
                </td>
            </tr>
        </table>
    </div>

    <div class="data-summary">
        <h2>Data Breakdown</h2>
        <div class="pie-chart">
            <!-- Simple CSS pie chart or use Chart.js -->
            <div class="chart-legend">
                <div class="legend-item">
                    <span class="color-box observed"></span>
                    Observed: {{ observed_count }} items
                </div>
                <div class="legend-item">
                    <span class="color-box assumed"></span>
                    Assumed: {{ assumed_count }} items
                </div>
            </div>
        </div>
    </div>

    <div class="assumptions-list">
        <h2>Assumptions Generated ({{ assumptions|length }})</h2>
        <table class="assumptions-table">
            <thead>
                <tr>
                    <th>Item</th>
                    <th>Category</th>
                    <th>Confidence</th>
                    <th>Assumption Basis</th>
                </tr>
            </thead>
            <tbody>
            {% for assumption in assumptions %}
                <tr>
                    <td>{{ assumption.item }}</td>
                    <td>{{ assumption.category }}</td>
                    <td>
                        <span class="confidence-indicator"
                              style="background: {{ get_confidence_color(assumption.confidence) }}">
                            {{ (assumption.confidence * 100)|int }}%
                        </span>
                    </td>
                    <td>{{ assumption.assumption_basis }}</td>
                </tr>
            {% endfor %}
            </tbody>
        </table>
    </div>

    {% if detection_results.gaps %}
    <div class="gaps-section">
        <h2>Identified Gaps for VDR Follow-up</h2>
        <ul class="gaps-list">
        {% for gap in detection_results.gaps %}
            <li>{{ gap }}</li>
        {% endfor %}
        </ul>
    </div>
    {% endif %}

    <div class="methodology">
        <h2>Methodology</h2>
        <p>
            Assumptions are generated using industry benchmarks and company size heuristics
            when organizational structure data is incomplete in source documents.
        </p>
        <ul>
            <li><strong>Industry Benchmarks:</strong> Tech companies typically have 3-4 management layers with flatter structures</li>
            <li><strong>Company Size:</strong> Adjustments based on total IT headcount (<20 = very flat, 500+ = deeper hierarchy)</li>
            <li><strong>Role Inference:</strong> Management layers inferred from role titles (VP → Director → Manager → IC)</li>
        </ul>
        <p>
            All assumptions are labeled and can be replaced with observed data when complete
            organizational documentation is provided.
        </p>
    </div>
</div>
{% endblock %}
```

---

### 4. Presentation (PowerPoint) Integration

**File:** `tools_v2/presentation.py`

#### 4.1 Organization Slide Footnote

**Add Footnote to Org Summary Slide:**

```python
# In presentation.py, _create_organization_slide()

def _create_organization_slide(prs, org_store, detection_results, assumptions):
    """
    Create organization summary slide with assumption transparency.

    NEW: Adds footnote if assumptions were used.
    """
    slide = prs.slides.add_slide(prs.slide_layouts[1])  # Title and Content

    title = slide.shapes.title
    title.text = "IT Organization Summary"

    # ... existing slide content (org chart, headcount, cost) ...

    # NEW: Add footnote if assumptions were used
    assumed_count = sum(1 for s in org_store.staff_members
                       if getattr(s, 'data_source', 'observed') == 'assumed')

    if assumed_count > 0:
        # Add text box at bottom of slide
        left = Inches(0.5)
        top = Inches(7.0)
        width = Inches(9.0)
        height = Inches(0.5)

        textbox = slide.shapes.add_textbox(left, top, width, height)
        text_frame = textbox.text_frame

        p = text_frame.paragraphs[0]
        p.text = f"* Includes {assumed_count} assumed roles based on industry benchmarks and company size heuristics"
        p.font.size = Pt(10)
        p.font.italic = True
        p.font.color.rgb = RGBColor(128, 128, 128)  # Gray
```

#### 4.2 New Slide: Organization Data Quality

**Add Dedicated Quality Slide (if assumptions >20% of data):**

```python
def _create_org_quality_slide(prs, detection_results, assumptions, org_store):
    """
    Create organization data quality slide.

    Shows detection results, assumption breakdown, gaps.
    Only included if significant assumptions were made (>20%).
    """
    observed_count = sum(1 for s in org_store.staff_members
                        if getattr(s, 'data_source', 'observed') == 'observed')
    assumed_count = sum(1 for s in org_store.staff_members
                       if getattr(s, 'data_source', 'observed') == 'assumed')
    total = observed_count + assumed_count

    # Only create this slide if >20% assumed
    if assumed_count / total < 0.2:
        return

    slide = prs.slides.add_slide(prs.slide_layouts[1])

    title = slide.shapes.title
    title.text = "Organization Data Quality"

    # Detection Results Box
    left = Inches(1.0)
    top = Inches(1.5)
    width = Inches(3.5)
    height = Inches(2.0)

    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        left, top, width, height
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = RGBColor(255, 243, 205)  # Light yellow

    text_frame = shape.text_frame
    text_frame.text = "Detection Results"
    text_frame.paragraphs[0].font.bold = True
    text_frame.paragraphs[0].font.size = Pt(14)

    # Add detection details
    p = text_frame.add_paragraph()
    p.text = f"Status: {detection_results.status.value.upper()}"
    p.level = 1

    p = text_frame.add_paragraph()
    p.text = f"Confidence: {int(detection_results.confidence * 100)}%"
    p.level = 1

    # Data Breakdown Box
    left = Inches(5.0)
    top = Inches(1.5)

    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        left, top, width, height
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = RGBColor(212, 237, 218)  # Light green

    text_frame = shape.text_frame
    text_frame.text = "Data Breakdown"
    text_frame.paragraphs[0].font.bold = True
    text_frame.paragraphs[0].font.size = Pt(14)

    p = text_frame.add_paragraph()
    p.text = f"Observed: {observed_count}"
    p.level = 1

    p = text_frame.add_paragraph()
    p.text = f"Assumed: {assumed_count}"
    p.level = 1

    p = text_frame.add_paragraph()
    p.text = f"Total: {total}"
    p.level = 1
    p.font.bold = True

    # Gaps section (bottom of slide)
    if detection_results.gaps:
        left = Inches(1.0)
        top = Inches(4.0)
        width = Inches(7.5)
        height = Inches(2.5)

        textbox = slide.shapes.add_textbox(left, top, width, height)
        text_frame = textbox.text_frame

        p = text_frame.paragraphs[0]
        p.text = "Identified Gaps for VDR Follow-up:"
        p.font.bold = True
        p.font.size = Pt(12)

        for gap in detection_results.gaps:
            p = text_frame.add_paragraph()
            p.text = f"• {gap}"
            p.level = 1
            p.font.size = Pt(11)
```

---

## Verification Strategy

### Unit Tests

**File:** `tests/test_reporting_integration.py`

**Test Cases:**

1. **test_excel_data_source_columns**
   - Generate Excel with mixed observed/assumed data
   - Verify Data Source, Confidence, Assumption Basis columns present
   - Verify color coding on confidence cells

2. **test_excel_assumptions_worksheet**
   - Generate Excel with assumptions
   - Verify "Assumptions Summary" sheet exists
   - Verify detection results, breakdown, assumption table populated

3. **test_html_assumption_panel**
   - Generate HTML report with assumptions
   - Verify assumption-summary-panel present
   - Verify badges, breakdown bars, gaps list rendered

4. **test_dashboard_quality_indicator**
   - Load dashboard with mixed data
   - Verify data-quality-badge matches assumed percentage
   - Verify breakdown bar widths correct

5. **test_presentation_footnote**
   - Generate presentation with assumptions
   - Verify footnote on org slide with assumed count

6. **test_presentation_quality_slide**
   - Generate presentation with >20% assumed
   - Verify quality slide created
   - Generate with <20% assumed, verify NO quality slide

---

## Benefits

### Why This Approach

**Transparent labeling** provides:
- **Trust:** Analysts see exactly what's real vs inferred
- **Actionable insights:** Gap list directly feeds VDR requests
- **Defensible analysis:** Can show PE partners "based on industry benchmarks"
- **Quality awareness:** Analysts know when to dig deeper

**Multi-format integration** ensures:
- **Consistency:** Same metadata shown in Excel, HTML, Dashboard, PowerPoint
- **Accessibility:** Different stakeholders use different formats (analysts=Excel, partners=PowerPoint)
- **Discoverability:** Expandable sections prevent overwhelming users with detail

---

## Expectations

### Success Metrics

**Transparency:**
- 100% of assumed items labeled in all outputs
- Assumption basis shown for every assumed item
- Detection results visible in all reports

**Usability:**
- Gap list used in 80%+ of VDR follow-up requests
- Analysts correctly interpret assumed vs observed in user testing
- No confusion between data sources (verified via feedback)

---

## Results Criteria

### Acceptance Criteria

- [ ] Excel: Data Source, Confidence, Assumption Basis columns added
- [ ] Excel: Assumptions Summary worksheet created
- [ ] HTML: Assumption summary panel renders when assumptions used
- [ ] HTML: Badges on assumed items with tooltips
- [ ] Dashboard: Data quality indicator shows on org card
- [ ] Dashboard: Assumptions detail page accessible
- [ ] Presentation: Footnote on org slide when assumptions used
- [ ] Presentation: Quality slide created when >20% assumed
- [ ] All formats consistent (same counts, same labels)

---

**Estimated Implementation Time:** 4-6 hours
**Confidence:** High (UI integration, straightforward)
