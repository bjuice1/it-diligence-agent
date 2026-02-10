"""
Executive Dashboard HTML Renderer

Renders ExecutiveDashboardData to a single-page HTML landing page.
Partner gets the story in 30 seconds, clicks through for details.

Layout:
- Header with overall assessment
- Key metrics row (4 cards)
- Domain grid (6 cards with deep-dive links)
- Two-column: Risks | Opportunities
- Investment summary with phase breakdown
"""

import logging
from datetime import datetime
from typing import Optional

from tools_v2.pe_report_schemas import (
    ExecutiveDashboardData,
    DomainHighlight,
    DOMAIN_ORDER,
)

logger = logging.getLogger(__name__)


# =============================================================================
# CSS STYLES
# =============================================================================

DASHBOARD_CSS = """
<style>
:root {
    --primary: #2563eb;
    --primary-dark: #1d4ed8;
    --success: #16a34a;
    --success-light: #dcfce7;
    --warning: #ca8a04;
    --warning-light: #fef3c7;
    --danger: #dc2626;
    --danger-light: #fecaca;
    --text: #1f2937;
    --text-muted: #6b7280;
    --bg: #f9fafb;
    --bg-white: #ffffff;
    --border: #e5e7eb;
    --shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
    --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
}

* { box-sizing: border-box; }

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
    line-height: 1.5;
    color: var(--text);
    background: var(--bg);
    margin: 0;
    padding: 0;
}

.dashboard {
    max-width: 1400px;
    margin: 0 auto;
    padding: 30px;
}

/* Header */
.header {
    background: var(--bg-white);
    border-radius: 12px;
    padding: 30px;
    margin-bottom: 25px;
    box-shadow: var(--shadow);
    border-left: 5px solid var(--primary);
}

.header h1 {
    margin: 0 0 5px 0;
    font-size: 28px;
    color: var(--text);
}

.header .subtitle {
    color: var(--text-muted);
    font-size: 14px;
    margin-bottom: 20px;
}

.overall-assessment {
    font-size: 16px;
    line-height: 1.7;
    color: var(--text);
    padding: 15px 20px;
    background: var(--bg);
    border-radius: 8px;
    border-left: 3px solid var(--primary);
}

.grade-indicator {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 16px;
    border-radius: 20px;
    font-weight: 600;
    font-size: 14px;
    float: right;
}

.grade-strong {
    background: var(--success-light);
    color: var(--success);
}

.grade-adequate {
    background: var(--warning-light);
    color: var(--warning);
}

.grade-needs-improvement {
    background: var(--danger-light);
    color: var(--danger);
}

/* Metrics Row */
.metrics-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 20px;
    margin-bottom: 25px;
}

.metric-card {
    background: var(--bg-white);
    border-radius: 10px;
    padding: 20px;
    box-shadow: var(--shadow);
    text-align: center;
}

.metric-card .icon {
    font-size: 24px;
    margin-bottom: 10px;
}

.metric-card .value {
    font-size: 24px;
    font-weight: 700;
    color: var(--primary);
    margin-bottom: 5px;
}

.metric-card .label {
    font-size: 12px;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* Domain Grid */
.domain-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
    margin-bottom: 25px;
}

.domain-card {
    background: var(--bg-white);
    border-radius: 10px;
    padding: 20px;
    box-shadow: var(--shadow);
    transition: box-shadow 0.2s, transform 0.2s;
    cursor: pointer;
    text-decoration: none;
    color: inherit;
    display: block;
}

.domain-card:hover {
    box-shadow: var(--shadow-lg);
    transform: translateY(-2px);
}

.domain-card .card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 12px;
}

.domain-card .domain-name {
    font-weight: 600;
    font-size: 16px;
    margin: 0;
}

.domain-card .grade-badge {
    font-size: 11px;
    padding: 3px 10px;
    border-radius: 12px;
    font-weight: 600;
}

.domain-card .key-finding {
    font-size: 14px;
    color: var(--text-muted);
    margin-bottom: 15px;
    min-height: 42px;
}

.domain-card .metrics {
    display: flex;
    justify-content: space-between;
    font-size: 12px;
    color: var(--text-muted);
    padding-top: 12px;
    border-top: 1px solid var(--border);
}

.domain-card .deep-dive {
    color: var(--primary);
    font-weight: 600;
    font-size: 13px;
    margin-top: 12px;
    display: inline-block;
}

/* Two Column Section */
.two-column {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    margin-bottom: 25px;
}

.column-card {
    background: var(--bg-white);
    border-radius: 10px;
    padding: 20px;
    box-shadow: var(--shadow);
}

.column-card h3 {
    margin: 0 0 15px 0;
    font-size: 16px;
    display: flex;
    align-items: center;
    gap: 8px;
}

.risk-list, .opportunity-list {
    list-style: none;
    padding: 0;
    margin: 0;
}

.risk-list li, .opportunity-list li {
    padding: 12px 15px;
    border-radius: 8px;
    margin-bottom: 10px;
    font-size: 14px;
}

.risk-list li {
    background: #fef2f2;
    border-left: 3px solid var(--danger);
}

.risk-list li.severity-critical {
    background: #fecaca;
    border-left-color: #991b1b;
}

.risk-list li.severity-high {
    background: #fed7aa;
    border-left-color: #ea580c;
}

.risk-list li .title {
    font-weight: 600;
    margin-bottom: 4px;
}

.risk-list li .meta {
    font-size: 12px;
    color: var(--text-muted);
}

.opportunity-list li {
    background: var(--success-light);
    border-left: 3px solid var(--success);
}

/* Investment Summary */
.investment-section {
    background: var(--bg-white);
    border-radius: 10px;
    padding: 25px;
    box-shadow: var(--shadow);
    margin-bottom: 25px;
}

.investment-section h3 {
    margin: 0 0 20px 0;
    font-size: 18px;
}

.investment-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 15px;
    margin-bottom: 20px;
}

.investment-card {
    text-align: center;
    padding: 15px;
    background: var(--bg);
    border-radius: 8px;
}

.investment-card .value {
    font-size: 20px;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 5px;
}

.investment-card .label {
    font-size: 12px;
    color: var(--text-muted);
}

.investment-card.highlight {
    background: #eff6ff;
    border: 2px solid var(--primary);
}

.investment-card.highlight .value {
    color: var(--primary);
}

.phase-breakdown {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 15px;
}

.phase-card {
    padding: 15px;
    border-radius: 8px;
    text-align: center;
}

.phase-card.day1 {
    background: #fef2f2;
}

.phase-card.day100 {
    background: #fef3c7;
}

.phase-card.post100 {
    background: #f0fdf4;
}

.phase-card .phase-name {
    font-weight: 600;
    font-size: 14px;
    margin-bottom: 5px;
}

.phase-card .phase-value {
    font-size: 18px;
    font-weight: 700;
}

/* Stats Row */
.stats-row {
    display: flex;
    justify-content: center;
    gap: 40px;
    padding: 20px;
    background: var(--bg-white);
    border-radius: 10px;
    box-shadow: var(--shadow);
}

.stat {
    text-align: center;
}

.stat .number {
    font-size: 28px;
    font-weight: 700;
    color: var(--primary);
}

.stat .label {
    font-size: 12px;
    color: var(--text-muted);
    text-transform: uppercase;
}

/* Footer */
.footer {
    text-align: center;
    padding: 20px;
    color: var(--text-muted);
    font-size: 12px;
}

/* Responsive */
@media (max-width: 1200px) {
    .domain-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

@media (max-width: 900px) {
    .metrics-row {
        grid-template-columns: repeat(2, 1fr);
    }

    .two-column {
        grid-template-columns: 1fr;
    }

    .investment-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

@media (max-width: 600px) {
    .dashboard {
        padding: 15px;
    }

    .metrics-row,
    .domain-grid {
        grid-template-columns: 1fr;
    }

    .phase-breakdown {
        grid-template-columns: 1fr;
    }
}

/* Print */
@media print {
    body {
        background: white;
    }

    .domain-card:hover {
        transform: none;
        box-shadow: var(--shadow);
    }
}
</style>
"""


# =============================================================================
# RENDERER CLASS
# =============================================================================

class DashboardRenderer:
    """Renders ExecutiveDashboardData to HTML."""

    def __init__(self, include_styles: bool = True, entity: str = "target"):
        self.include_styles = include_styles
        self.entity = entity  # Phase 7 - Entity context

    def render(self, data: ExecutiveDashboardData) -> str:
        """
        Render dashboard data to HTML.

        Args:
            data: Dashboard data

        Returns:
            Complete HTML document
        """
        content = f"""
        <div class="dashboard">
            {self._render_header(data)}
            {self._render_metrics_row(data)}
            {self._render_domain_grid(data)}
            {self._render_two_column(data)}
            {self._render_investment_section(data)}
            {self._render_stats_row(data)}
            {self._render_footer(data)}
        </div>
        """

        return self._wrap_in_document(content, data.target_name)

    def _wrap_in_document(self, content: str, title: str) -> str:
        """Wrap content in HTML document."""
        styles = DASHBOARD_CSS if self.include_styles else ""

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - IT Due Diligence Dashboard</title>
    {styles}
</head>
<body>
    {content}
</body>
</html>"""

    def _render_header(self, data: ExecutiveDashboardData) -> str:
        """Render dashboard header with entity banner (Phase 7)."""
        grade_class = data.overall_grade.lower().replace(" ", "-")

        # Entity banner (Phase 7 - Entity Separation)
        entity_banner = ""
        if self.entity == "target":
            entity_banner = """
            <div style="background: #007bff; color: white; padding: 8px 15px; border-radius: 4px;
                        display: inline-block; font-weight: 600; font-size: 14px; margin-bottom: 15px;">
                🎯 TARGET ENVIRONMENT
            </div>
            """
        elif self.entity == "buyer":
            entity_banner = """
            <div style="background: #6f42c1; color: white; padding: 8px 15px; border-radius: 4px;
                        display: inline-block; font-weight: 600; font-size: 14px; margin-bottom: 15px;">
                🏢 BUYER REFERENCE
            </div>
            """

        # Entity view links
        entity_links = f"""
        <div style="margin-bottom: 15px; font-size: 13px;">
            <span style="color: #666;">View:</span>
            <a href="?entity=target" style="margin-left: 10px; color: {'#007bff' if self.entity != 'target' else '#333'}; font-weight: {'normal' if self.entity != 'target' else 'bold'};">Target</a>
            <a href="?entity=buyer" style="margin-left: 10px; color: {'#6f42c1' if self.entity != 'buyer' else '#333'}; font-weight: {'normal' if self.entity != 'buyer' else 'bold'};">Buyer</a>
        </div>
        """

        return f"""
        <div class="header">
            {entity_banner}
            <div class="grade-indicator grade-{grade_class}">
                Overall: {data.overall_grade}
            </div>
            <h1>{data.target_name}</h1>
            <div class="subtitle">
                IT Due Diligence Dashboard | Analysis Date: {data.analysis_date}
            </div>
            {entity_links}
            <div class="overall-assessment">
                {data.overall_assessment or 'No overall assessment available.'}
            </div>
        </div>
        """

    def _render_metrics_row(self, data: ExecutiveDashboardData) -> str:
        """Render key metrics cards."""
        # Format values
        budget_low, budget_high = data.total_it_budget
        if budget_high > 0:
            budget_display = f"${budget_low/1000000:.1f}M - ${budget_high/1000000:.1f}M"
        else:
            budget_display = "TBD"

        invest_low, invest_high = data.total_investment_needed
        if invest_high > 0:
            invest_display = f"${invest_low/1000000:.1f}M - ${invest_high/1000000:.1f}M"
        else:
            invest_display = "TBD"

        headcount = data.it_headcount if data.it_headcount else "TBD"

        it_pct = f"{data.it_pct_revenue:.1f}%" if data.it_pct_revenue else "TBD"

        return f"""
        <div class="metrics-row">
            <div class="metric-card">
                <div class="icon">💰</div>
                <div class="value">{budget_display}</div>
                <div class="label">Annual IT Budget</div>
            </div>
            <div class="metric-card">
                <div class="icon">📊</div>
                <div class="value">{invest_display}</div>
                <div class="label">Investment Needed</div>
            </div>
            <div class="metric-card">
                <div class="icon">👥</div>
                <div class="value">{headcount}</div>
                <div class="label">IT Headcount</div>
            </div>
            <div class="metric-card">
                <div class="icon">📈</div>
                <div class="value">{it_pct}</div>
                <div class="label">IT % of Revenue</div>
            </div>
        </div>
        """

    def _render_domain_grid(self, data: ExecutiveDashboardData) -> str:
        """Render domain cards grid."""
        cards = []

        for domain in DOMAIN_ORDER:
            highlight = data.domain_highlights.get(domain)
            if highlight:
                cards.append(self._render_domain_card(highlight))

        return f"""
        <div class="domain-grid">
            {''.join(cards)}
        </div>
        """

    def _render_domain_card(self, highlight: DomainHighlight) -> str:
        """Render a single domain card."""
        grade = highlight.overall_grade
        grade_class = grade.lower().replace(" ", "-")

        # Format costs
        run_low, run_high = highlight.run_rate_cost
        if run_high > 0:
            run_display = f"${run_low/1000:.0f}K - ${run_high/1000:.0f}K"
        else:
            run_display = "TBD"

        inv_low, inv_high = highlight.investment_needed
        if inv_high > 0:
            inv_display = f"${inv_low/1000:.0f}K - ${inv_high/1000:.0f}K"
        else:
            inv_display = "TBD"

        return f"""
        <a href="/reports/{highlight.domain}" class="domain-card">
            <div class="card-header">
                <h4 class="domain-name">{highlight.domain_display_name}</h4>
                <span class="grade-badge grade-{grade_class}">{grade}</span>
            </div>
            <div class="key-finding">{highlight.key_finding}</div>
            <div class="metrics">
                <span>Run-rate: {run_display}</span>
                <span>Investment: {inv_display}</span>
            </div>
            <span class="deep-dive">Deep dive →</span>
        </a>
        """

    def _render_two_column(self, data: ExecutiveDashboardData) -> str:
        """Render risks and opportunities columns."""
        # Risks
        risks_html = ""
        if data.top_risks:
            items = []
            for risk in data.top_risks:
                severity = risk.get("severity", "medium")
                items.append(f"""
                <li class="severity-{severity}">
                    <div class="title">{risk.get('title', 'Unnamed Risk')}</div>
                    <div class="meta">{risk.get('domain', '').replace('_', ' ').title()} | {severity.title()}</div>
                </li>
                """)
            risks_html = f'<ul class="risk-list">{"".join(items)}</ul>'
        else:
            risks_html = '<p style="color: var(--text-muted);">No critical risks identified</p>'

        # Opportunities
        opps_html = ""
        if data.top_opportunities:
            items = [f'<li>{opp}</li>' for opp in data.top_opportunities]
            opps_html = f'<ul class="opportunity-list">{"".join(items)}</ul>'
        else:
            opps_html = '<p style="color: var(--text-muted);">No specific opportunities identified</p>'

        return f"""
        <div class="two-column">
            <div class="column-card">
                <h3>⚠️ Top Risks to Consider</h3>
                {risks_html}
            </div>
            <div class="column-card">
                <h3>✨ Top Opportunities</h3>
                {opps_html}
            </div>
        </div>
        """

    def _render_investment_section(self, data: ExecutiveDashboardData) -> str:
        """Render investment summary section."""
        # Total investment
        total_low, total_high = data.total_investment_needed
        total_display = f"${total_low:,.0f} - ${total_high:,.0f}" if total_high > 0 else "TBD"

        # TSA/Separation/Integration breakdown
        tsa_low, tsa_high = data.tsa_costs
        sep_low, sep_high = data.separation_costs
        int_low, int_high = data.integration_costs

        def format_cost(low, high):
            if high > 0:
                return f"${low:,.0f} - ${high:,.0f}"
            return "$0"

        # Phase breakdown
        phase_cards = ""
        phases = [
            ("Day 1", "day1", data.investment_by_phase.get("Day_1", (0, 0))),
            ("Day 100", "day100", data.investment_by_phase.get("Day_100", (0, 0))),
            ("Post 100", "post100", data.investment_by_phase.get("Post_100", (0, 0))),
        ]

        for name, css_class, (low, high) in phases:
            value = f"${low:,.0f} - ${high:,.0f}" if high > 0 else "$0"
            phase_cards += f"""
            <div class="phase-card {css_class}">
                <div class="phase-name">{name}</div>
                <div class="phase-value">{value}</div>
            </div>
            """

        return f"""
        <div class="investment-section">
            <h3>Investment Summary</h3>

            <div class="investment-grid">
                <div class="investment-card highlight">
                    <div class="value">{total_display}</div>
                    <div class="label">Total Investment</div>
                </div>
                <div class="investment-card">
                    <div class="value">{format_cost(tsa_low, tsa_high)}</div>
                    <div class="label">TSA / Transition</div>
                </div>
                <div class="investment-card">
                    <div class="value">{format_cost(sep_low, sep_high)}</div>
                    <div class="label">Separation</div>
                </div>
                <div class="investment-card">
                    <div class="value">{format_cost(int_low, int_high)}</div>
                    <div class="label">Integration</div>
                </div>
            </div>

            <h4 style="font-size: 14px; margin-bottom: 15px; color: var(--text-muted);">By Phase</h4>
            <div class="phase-breakdown">
                {phase_cards}
            </div>
        </div>
        """

    def _render_stats_row(self, data: ExecutiveDashboardData) -> str:
        """Render bottom stats row."""
        return f"""
        <div class="stats-row">
            <div class="stat">
                <div class="number">{data.total_facts}</div>
                <div class="label">Facts Discovered</div>
            </div>
            <div class="stat">
                <div class="number">{data.total_risks}</div>
                <div class="label">Risks Identified</div>
            </div>
            <div class="stat">
                <div class="number">{data.total_work_items}</div>
                <div class="label">Work Items</div>
            </div>
            <div class="stat">
                <div class="number">{data.total_gaps}</div>
                <div class="label">Information Gaps</div>
            </div>
        </div>
        """

    def _render_footer(self, data: ExecutiveDashboardData) -> str:
        """Render footer."""
        return f"""
        <div class="footer">
            Generated {datetime.now().strftime('%B %d, %Y at %I:%M %p')} |
            IT Due Diligence Agent
        </div>
        """


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def render_dashboard(
    data: ExecutiveDashboardData,
    include_styles: bool = True,
    entity: str = "target"
) -> str:
    """
    Render executive dashboard to HTML.

    Args:
        data: Dashboard data
        include_styles: Whether to include CSS
        entity: Entity being displayed ("target" or "buyer")

    Returns:
        Complete HTML document
    """
    renderer = DashboardRenderer(include_styles=include_styles, entity=entity)
    return renderer.render(data)
