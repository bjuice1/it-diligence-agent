"""
Domain Report HTML Renderer

Renders DomainReportData to HTML following the 5-section PE framework:
1. What You're Getting (Inventory)
2. What It Costs Today (Run-Rate)
3. How It Compares (Benchmark Assessment)
4. What Needs to Happen (Actions/Work Items)
5. Team Implications (Resources)
"""

import logging
from typing import Optional
from datetime import datetime

from tools_v2.pe_report_schemas import (
    DomainReportData,
    BenchmarkAssessment,
    ActionItem,
    ResourceNeed,
    WorkItemTaxonomy,
    DOMAIN_DISPLAY_NAMES,
    DOMAIN_ICONS,
)

logger = logging.getLogger(__name__)


# =============================================================================
# CSS STYLES
# =============================================================================

DOMAIN_REPORT_CSS = """
<style>
:root {
    --primary: #2563eb;
    --primary-light: #3b82f6;
    --success: #16a34a;
    --warning: #ca8a04;
    --danger: #dc2626;
    --danger-light: #fecaca;
    --info: #0891b2;
    --text: #1f2937;
    --text-muted: #6b7280;
    --bg-light: #f9fafb;
    --border: #e5e7eb;
    --border-dark: #d1d5db;
}

* {
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
    line-height: 1.6;
    color: var(--text);
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
    background: white;
}

.report-header {
    border-bottom: 3px solid var(--primary);
    padding-bottom: 20px;
    margin-bottom: 30px;
}

.report-header h1 {
    margin: 0 0 10px 0;
    color: var(--primary);
    font-size: 28px;
}

.report-header .meta {
    color: var(--text-muted);
    font-size: 14px;
}

.grade-badge {
    display: inline-block;
    padding: 6px 16px;
    border-radius: 20px;
    font-weight: 600;
    font-size: 14px;
    margin-left: 15px;
}

.grade-strong {
    background: #dcfce7;
    color: var(--success);
}

.grade-adequate {
    background: #fef3c7;
    color: var(--warning);
}

.grade-needs-improvement {
    background: var(--danger-light);
    color: var(--danger);
}

.section {
    margin-bottom: 35px;
    padding: 25px;
    background: var(--bg-light);
    border-radius: 10px;
    border: 1px solid var(--border);
}

.section-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 20px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--border);
}

.section-header h2 {
    margin: 0;
    font-size: 18px;
    color: var(--text);
}

.section-number {
    width: 28px;
    height: 28px;
    background: var(--primary);
    color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    font-weight: 600;
}

/* Cost cards */
.cost-summary {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 15px;
    margin-bottom: 20px;
}

.cost-card {
    background: white;
    padding: 15px;
    border-radius: 8px;
    border: 1px solid var(--border);
    text-align: center;
}

.cost-card .label {
    font-size: 12px;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 5px;
}

.cost-card .value {
    font-size: 24px;
    font-weight: 700;
    color: var(--primary);
}

.cost-card.secondary .value {
    color: var(--text);
    font-size: 20px;
}

/* Benchmark assessment */
.benchmark-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 20px;
}

.benchmark-item {
    background: white;
    padding: 18px;
    border-radius: 8px;
    border: 1px solid var(--border);
}

.benchmark-item .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}

.benchmark-item .header strong {
    font-size: 14px;
}

.benchmark-item .badge {
    font-size: 12px;
    padding: 3px 10px;
    border-radius: 12px;
    font-weight: 600;
}

.badge-modern, .badge-lean, .badge-mature {
    background: #dcfce7;
    color: var(--success);
}

.badge-mixed, .badge-in_line, .badge-developing {
    background: #fef3c7;
    color: var(--warning);
}

.badge-outdated, .badge-bloated, .badge-immature {
    background: var(--danger-light);
    color: var(--danger);
}

.benchmark-item .rationale {
    font-size: 13px;
    color: var(--text-muted);
    margin-bottom: 8px;
}

.benchmark-item .source {
    font-size: 11px;
    color: var(--text-muted);
    font-style: italic;
}

.so-what-box {
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    border-radius: 8px;
    padding: 15px 18px;
    margin-top: 20px;
}

.so-what-box strong {
    color: var(--primary);
}

/* Action items */
.action-list {
    display: flex;
    flex-direction: column;
    gap: 15px;
}

.action-item {
    background: white;
    padding: 18px;
    border-radius: 8px;
    border: 1px solid var(--border);
    border-left: 4px solid var(--primary);
}

.action-item.priority-critical {
    border-left-color: var(--danger);
}

.action-item.priority-high {
    border-left-color: #ea580c;
}

.action-item .action-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 10px;
}

.action-item .title {
    font-weight: 600;
    font-size: 15px;
    margin: 0;
}

.action-item .cost {
    font-size: 14px;
    font-weight: 600;
    color: var(--primary);
    white-space: nowrap;
}

.action-item .so-what {
    font-size: 13px;
    color: var(--text-muted);
    margin-bottom: 10px;
}

.action-meta {
    display: flex;
    gap: 15px;
    font-size: 12px;
}

.action-meta span {
    display: flex;
    align-items: center;
    gap: 4px;
    color: var(--text-muted);
}

/* Implications list */
.implications-list {
    list-style: none;
    padding: 0;
    margin: 0;
}

.implications-list li {
    padding: 12px 15px;
    background: white;
    border: 1px solid var(--border);
    border-radius: 6px;
    margin-bottom: 10px;
    position: relative;
    padding-left: 35px;
}

.implications-list li::before {
    content: "→";
    position: absolute;
    left: 12px;
    color: var(--primary);
    font-weight: bold;
}

/* Resource needs */
.resource-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.resource-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 15px;
    background: white;
    border: 1px solid var(--border);
    border-radius: 6px;
}

.resource-item .role {
    font-weight: 600;
    font-size: 14px;
}

.resource-item .details {
    display: flex;
    gap: 10px;
    font-size: 12px;
    color: var(--text-muted);
}

/* Tables */
table {
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
}

th, td {
    padding: 10px 12px;
    text-align: left;
    border-bottom: 1px solid var(--border);
}

th {
    background: var(--bg-light);
    font-weight: 600;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--text-muted);
}

tr:hover td {
    background: #f3f4f6;
}

/* Key callouts */
.callouts {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 15px;
}

.callout {
    background: #fef3c7;
    padding: 8px 14px;
    border-radius: 6px;
    font-size: 13px;
    border: 1px solid #fcd34d;
}

/* Integration box */
.integration-box {
    background: #f0fdf4;
    border: 1px solid #86efac;
    border-radius: 8px;
    padding: 15px 18px;
    margin-top: 20px;
}

.integration-box h4 {
    margin: 0 0 10px 0;
    color: var(--success);
    font-size: 14px;
}

.integration-box ul {
    margin: 0;
    padding-left: 20px;
}

.integration-box li {
    margin-bottom: 6px;
    font-size: 13px;
}

/* Inventory section content (org chart, app landscape) */
.inventory-content {
    background: white;
    border-radius: 8px;
    padding: 15px;
    border: 1px solid var(--border);
}

/* Responsive */
@media (max-width: 768px) {
    .section {
        padding: 15px;
    }

    .cost-summary {
        grid-template-columns: 1fr;
    }

    .benchmark-grid {
        grid-template-columns: 1fr;
    }
}

/* Print styles */
@media print {
    body {
        padding: 0;
    }

    .section {
        page-break-inside: avoid;
    }
}
</style>
"""


# =============================================================================
# RENDERER CLASS
# =============================================================================

class DomainReportRenderer:
    """Renders DomainReportData to HTML."""

    def __init__(self, include_styles: bool = True):
        """
        Initialize renderer.

        Args:
            include_styles: Whether to include CSS in output
        """
        self.include_styles = include_styles

    def render(self, data: DomainReportData, target_name: str = "Target Company") -> str:
        """
        Render DomainReportData to complete HTML document.

        Args:
            data: Domain report data
            target_name: Name of target company

        Returns:
            Complete HTML document string
        """
        sections = [
            self._render_section_1_inventory(data),
            self._render_section_2_costs(data),
            self._render_section_3_benchmark(data),
            self._render_section_4_actions(data),
            self._render_section_5_implications(data),
        ]

        body_content = f"""
        {self._render_header(data, target_name)}
        {''.join(sections)}
        """

        return self._wrap_in_document(body_content, data.domain_display_name or data.domain)

    def _wrap_in_document(self, content: str, title: str) -> str:
        """Wrap content in HTML document structure."""
        styles = DOMAIN_REPORT_CSS if self.include_styles else ""

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - PE Domain Report</title>
    {styles}
</head>
<body>
    {content}
</body>
</html>"""

    def _render_header(self, data: DomainReportData, target_name: str) -> str:
        """Render report header."""
        display_name = data.domain_display_name or DOMAIN_DISPLAY_NAMES.get(data.domain, data.domain)
        grade = data.benchmark_assessment.overall_grade
        grade_class = grade.lower().replace(" ", "-")

        return f"""
        <div class="report-header">
            <h1>
                {display_name}
                <span class="grade-badge grade-{grade_class}">{grade}</span>
            </h1>
            <div class="meta">
                {target_name} | Generated {datetime.now().strftime('%B %d, %Y')} |
                {data.fact_count} facts | {data.work_item_count} work items | {data.risk_count} risks
            </div>
        </div>
        """

    def _render_section_1_inventory(self, data: DomainReportData) -> str:
        """Render Section 1: What You're Getting."""
        # Use pre-rendered inventory HTML if available
        inventory_html = data.inventory_html

        if not inventory_html:
            # Fallback to summary
            summary = data.inventory_summary
            inventory_html = f"""
            <div class="inventory-content">
                <p><strong>Summary:</strong> {summary.summary_text or 'No inventory summary available'}</p>
                <p><strong>Total Items:</strong> {summary.total_count}</p>
            </div>
            """

        return f"""
        <div class="section" id="section-1">
            <div class="section-header">
                <span class="section-number">1</span>
                <h2>What You're Getting</h2>
            </div>
            {inventory_html}
        </div>
        """

    def _render_section_2_costs(self, data: DomainReportData) -> str:
        """Render Section 2: What It Costs Today."""
        run_rate_low, run_rate_high = data.run_rate_cost

        # Format cost display
        if run_rate_low == 0 and run_rate_high == 0:
            run_rate_display = "Not documented"
        elif run_rate_low == run_rate_high:
            run_rate_display = f"${run_rate_low:,.0f}"
        else:
            run_rate_display = f"${run_rate_low:,.0f} - ${run_rate_high:,.0f}"

        # Build cost breakdown cards
        breakdown_cards = []
        for category, (low, high) in data.cost_breakdown.items():
            if low > 0 or high > 0:
                if low == high:
                    value = f"${low:,.0f}"
                else:
                    value = f"${low:,.0f}-${high:,.0f}"

                breakdown_cards.append(f"""
                <div class="cost-card secondary">
                    <div class="label">{category.replace('_', ' ').title()}</div>
                    <div class="value">{value}</div>
                </div>
                """)

        breakdown_html = ''.join(breakdown_cards) if breakdown_cards else ""

        return f"""
        <div class="section" id="section-2">
            <div class="section-header">
                <span class="section-number">2</span>
                <h2>What It Costs Today</h2>
            </div>

            <div class="cost-summary">
                <div class="cost-card">
                    <div class="label">Annual Run-Rate</div>
                    <div class="value">{run_rate_display}</div>
                </div>
                {breakdown_html}
            </div>

            {self._render_cost_facts(data.cost_facts_cited) if data.cost_facts_cited else ''}
        </div>
        """

    def _render_cost_facts(self, fact_ids: list) -> str:
        """Render cost fact citations."""
        if not fact_ids:
            return ""

        return f"""
        <div style="font-size: 12px; color: var(--text-muted); margin-top: 10px;">
            Based on: {', '.join(fact_ids[:5])}{'...' if len(fact_ids) > 5 else ''}
        </div>
        """

    def _render_section_3_benchmark(self, data: DomainReportData) -> str:
        """Render Section 3: How It Compares."""
        assessment = data.benchmark_assessment

        return f"""
        <div class="section" id="section-3">
            <div class="section-header">
                <span class="section-number">3</span>
                <h2>How It Compares</h2>
            </div>

            <div class="benchmark-grid">
                {self._render_benchmark_item('Technology Age', assessment.tech_age,
                                              assessment.tech_age_rationale, assessment.tech_age_benchmark_source)}
                {self._render_benchmark_item('Cost Posture', assessment.cost_posture,
                                              assessment.cost_posture_rationale, assessment.cost_benchmark_source)}
                {self._render_benchmark_item('Maturity', assessment.maturity,
                                              assessment.maturity_rationale, assessment.maturity_benchmark_source)}
            </div>

            {self._render_so_what(assessment.implication)}

            {self._render_callouts(assessment.key_callouts)}
        </div>
        """

    def _render_benchmark_item(self, label: str, value: str, rationale: str, source: str) -> str:
        """Render a single benchmark assessment item."""
        badge_class = f"badge-{value.lower().replace(' ', '_')}"

        return f"""
        <div class="benchmark-item">
            <div class="header">
                <strong>{label}</strong>
                <span class="badge {badge_class}">{value.replace('_', ' ').title()}</span>
            </div>
            <div class="rationale">{rationale or 'No rationale provided'}</div>
            <div class="source">{source or 'Source not specified'}</div>
        </div>
        """

    def _render_so_what(self, implication: str) -> str:
        """Render the 'So What?' box."""
        if not implication:
            return ""

        return f"""
        <div class="so-what-box">
            <strong>So What?</strong> {implication}
        </div>
        """

    def _render_callouts(self, callouts: list) -> str:
        """Render key callouts."""
        if not callouts:
            return ""

        callout_html = ''.join(f'<span class="callout">{c}</span>' for c in callouts)
        return f'<div class="callouts">{callout_html}</div>'

    def _render_section_4_actions(self, data: DomainReportData) -> str:
        """Render Section 4: What Needs to Happen."""
        # Render top 3 actions
        actions_html = ""
        for action in data.top_actions[:3]:
            actions_html += self._render_action_item(action)

        # Render work items summary
        work_items_summary = ""
        if data.work_items:
            # Group by phase
            by_phase = {}
            for wi in data.work_items:
                phase = wi.phase
                if phase not in by_phase:
                    by_phase[phase] = []
                by_phase[phase].append(wi)

            work_items_summary = f"""
            <div style="margin-top: 20px;">
                <h4 style="margin-bottom: 10px; font-size: 14px;">All Work Items by Phase</h4>
                {self._render_work_items_table(data.work_items)}
            </div>
            """

        # Investment total
        inv_low, inv_high = data.total_investment
        if inv_low > 0 or inv_high > 0:
            inv_display = f"${inv_low:,.0f} - ${inv_high:,.0f}"
            investment_box = f"""
            <div style="margin-top: 20px; padding: 12px; background: #eff6ff; border-radius: 6px;">
                <strong>Total Investment Needed:</strong> {inv_display}
            </div>
            """
        else:
            investment_box = ""

        return f"""
        <div class="section" id="section-4">
            <div class="section-header">
                <span class="section-number">4</span>
                <h2>What Needs to Happen</h2>
            </div>

            <h4 style="margin-bottom: 15px; font-size: 14px; color: var(--text-muted);">Top Actions</h4>
            <div class="action-list">
                {actions_html or '<p>No actions identified</p>'}
            </div>

            {investment_box}
            {work_items_summary}
        </div>
        """

    def _render_action_item(self, action: ActionItem) -> str:
        """Render a single action item."""
        priority_class = f"priority-{action.priority}"

        return f"""
        <div class="action-item {priority_class}">
            <div class="action-header">
                <h4 class="title">{action.title}</h4>
                <span class="cost">{action.cost_display}</span>
            </div>
            <div class="so-what">{action.so_what}</div>
            <div class="action-meta">
                <span>📅 {action.timing.replace('_', ' ')}</span>
                <span>👤 {action.owner_type.title()}</span>
                <span>⚡ {action.priority.title()}</span>
            </div>
        </div>
        """

    def _render_work_items_table(self, work_items: list) -> str:
        """Render work items as a table."""
        rows = ""
        for wi in work_items[:10]:  # Limit to 10
            cost_display = f"${wi.cost_estimate_low:,.0f}-${wi.cost_estimate_high:,.0f}"
            rows += f"""
            <tr>
                <td>{wi.title}</td>
                <td>{wi.phase.replace('_', ' ')}</td>
                <td>{wi.priority.title()}</td>
                <td>{cost_display}</td>
                <td>{wi.owner_type.title()}</td>
            </tr>
            """

        return f"""
        <table>
            <thead>
                <tr>
                    <th>Work Item</th>
                    <th>Phase</th>
                    <th>Priority</th>
                    <th>Cost</th>
                    <th>Owner</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
        """

    def _render_section_5_implications(self, data: DomainReportData) -> str:
        """Render Section 5: Team Implications."""
        # Top implications
        implications_html = ""
        if data.top_implications:
            items = ''.join(f'<li>{imp}</li>' for imp in data.top_implications[:3])
            implications_html = f'<ul class="implications-list">{items}</ul>'
        else:
            implications_html = "<p>No specific implications identified</p>"

        # Resource needs
        resources_html = ""
        if data.resource_needs:
            resources_html = '<div class="resource-list">'
            for resource in data.resource_needs:
                resources_html += f"""
                <div class="resource-item">
                    <span class="role">{resource.role}</span>
                    <div class="details">
                        <span>{resource.type.title()}</span>
                        <span>{resource.timing.replace('_', ' ')}</span>
                        <span>{resource.duration.replace('_', ' ').title()}</span>
                    </div>
                </div>
                """
            resources_html += '</div>'

        # Integration considerations
        integration_html = ""
        if data.integration_considerations:
            items = ''.join(f'<li>{cons}</li>' for cons in data.integration_considerations[:3])
            integration_html = f"""
            <div class="integration-box">
                <h4>Integration Considerations</h4>
                <ul>{items}</ul>
            </div>
            """

        return f"""
        <div class="section" id="section-5">
            <div class="section-header">
                <span class="section-number">5</span>
                <h2>Team Implications</h2>
            </div>

            <h4 style="margin-bottom: 10px; font-size: 14px;">Key Business Implications</h4>
            {implications_html}

            {f'<h4 style="margin: 20px 0 10px 0; font-size: 14px;">Resource Needs</h4>{resources_html}' if resources_html else ''}

            {integration_html}
        </div>
        """


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def render_domain_report(
    data: DomainReportData,
    target_name: str = "Target Company",
    include_styles: bool = True
) -> str:
    """
    Render a domain report to HTML.

    Args:
        data: Domain report data
        target_name: Name of target company
        include_styles: Whether to include CSS

    Returns:
        Complete HTML document
    """
    renderer = DomainReportRenderer(include_styles=include_styles)
    return renderer.render(data, target_name)
