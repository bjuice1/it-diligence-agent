"""
Investment Report Generator

Aggregates one-time costs from work items across domains.
Shows TSA/separation/integration breakdown.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from datetime import datetime

from tools_v2.pe_report_schemas import InvestmentReportData, WorkItemSummary
from tools_v2.pe_costs import build_investment_report_data

if TYPE_CHECKING:
    from tools_v2.reasoning_tools import ReasoningStore

logger = logging.getLogger(__name__)


# =============================================================================
# INVESTMENT REPORT GENERATION
# =============================================================================

def generate_investment_report(
    reasoning_store: "ReasoningStore"
) -> InvestmentReportData:
    """
    Generate comprehensive investment report data.

    Args:
        reasoning_store: Reasoning store with work items

    Returns:
        InvestmentReportData instance
    """
    return build_investment_report_data(reasoning_store)


def render_investment_report_html(
    investment_data: InvestmentReportData,
    target_name: str = "Target Company"
) -> str:
    """
    Render investment report to HTML.

    Args:
        investment_data: Investment report data
        target_name: Target company name

    Returns:
        Complete HTML document
    """
    # Format total
    total_low, total_high = investment_data.total_one_time
    if total_high > 0:
        total_display = f"${total_low:,.0f} - ${total_high:,.0f}"
    else:
        total_display = "No investments identified"

    # Build phase cards
    phase_cards = ""
    phase_labels = [("Day_1", "Day 1"), ("Day_100", "Day 100"), ("Post_100", "Post 100")]
    for phase_key, phase_label in phase_labels:
        low, high = investment_data.by_phase.get(phase_key, (0, 0))
        count = investment_data.by_phase_count.get(phase_key, 0)

        if high > 0:
            cost_display = f"${low:,.0f} - ${high:,.0f}"
        else:
            cost_display = "$0"

        phase_cards += f"""
        <div class="phase-card phase-{phase_key.lower().replace('_', '')}">
            <div class="phase-name">{phase_label}</div>
            <div class="phase-value">{cost_display}</div>
            <div class="phase-count">{count} items</div>
        </div>
        """

    # Build domain breakdown rows
    domain_rows = ""
    for domain, (low, high) in sorted(investment_data.by_domain.items()):
        if high > 0:
            cost_display = f"${low:,.0f} - ${high:,.0f}"
            count = len([wi for wi in investment_data.work_items if wi.domain == domain])
            domain_rows += f"""
            <tr>
                <td><strong>{domain.replace('_', ' ').title()}</strong></td>
                <td class="cost">{cost_display}</td>
                <td class="count">{count}</td>
            </tr>
            """

    # Build type breakdown (TSA/Separation/Integration)
    type_rows = ""
    type_labels = {
        "tsa": "TSA / Transition",
        "separation": "Separation",
        "integration": "Integration",
        "transform": "Transformation",
        "run": "Run / Maintain",
    }

    for type_key, type_label in type_labels.items():
        low, high = investment_data.by_type.get(type_key, (0, 0))
        if high > 0:
            cost_display = f"${low:,.0f} - ${high:,.0f}"
            type_rows += f"""
            <tr>
                <td><strong>{type_label}</strong></td>
                <td class="cost">{cost_display}</td>
            </tr>
            """

    # Build priority breakdown
    priority_rows = ""
    for priority in ["critical", "high", "medium", "low"]:
        low, high = investment_data.by_priority.get(priority, (0, 0))
        count = investment_data.by_priority_count.get(priority, 0)
        if count > 0:
            cost_display = f"${low:,.0f} - ${high:,.0f}" if high > 0 else "$0"
            priority_rows += f"""
            <tr>
                <td><strong class="priority-{priority}">{priority.title()}</strong></td>
                <td class="cost">{cost_display}</td>
                <td class="count">{count}</td>
            </tr>
            """

    # Build work items table
    work_items_rows = ""
    for wi in investment_data.work_items[:20]:  # Limit to 20
        cost_display = f"${wi.cost_estimate_low:,.0f} - ${wi.cost_estimate_high:,.0f}"
        work_items_rows += f"""
        <tr>
            <td><strong>{wi.title[:50]}{'...' if len(wi.title) > 50 else ''}</strong></td>
            <td>{wi.domain.replace('_', ' ').title()}</td>
            <td>{wi.phase.replace('_', ' ')}</td>
            <td><span class="priority-{wi.priority}">{wi.priority.title()}</span></td>
            <td class="cost">{cost_display}</td>
            <td>{wi.owner_type.title()}</td>
        </tr>
        """

    # Critical path items
    critical_html = ""
    if investment_data.critical_path_items:
        items = [f"<li>{item}</li>" for item in investment_data.critical_path_items[:5]]
        critical_html = f"""
        <div class="critical-path">
            <h3>Critical Path Items</h3>
            <ul>{"".join(items)}</ul>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{target_name} - Investment Report</title>
    <style>
        :root {{
            --primary: #2563eb;
            --success: #16a34a;
            --warning: #ca8a04;
            --danger: #dc2626;
            --text: #1f2937;
            --text-muted: #6b7280;
            --bg-light: #f9fafb;
            --border: #e5e7eb;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: var(--text);
            max-width: 1200px;
            margin: 0 auto;
            padding: 30px;
            background: white;
        }}

        .header {{
            border-bottom: 3px solid var(--primary);
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}

        .header h1 {{
            margin: 0 0 10px 0;
            color: var(--primary);
        }}

        .header .meta {{
            color: var(--text-muted);
            font-size: 14px;
        }}

        .total-card {{
            background: var(--primary);
            color: white;
            padding: 25px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 25px;
        }}

        .total-card .value {{
            font-size: 36px;
            font-weight: 700;
            margin-bottom: 5px;
        }}

        .total-card .label {{
            font-size: 14px;
            opacity: 0.9;
        }}

        .phase-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            margin-bottom: 30px;
        }}

        .phase-card {{
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}

        .phase-day1 {{ background: #fef2f2; }}
        .phase-day100 {{ background: #fef3c7; }}
        .phase-post100 {{ background: #f0fdf4; }}

        .phase-name {{
            font-weight: 600;
            margin-bottom: 5px;
        }}

        .phase-value {{
            font-size: 20px;
            font-weight: 700;
            margin-bottom: 3px;
        }}

        .phase-count {{
            font-size: 12px;
            color: var(--text-muted);
        }}

        .section {{
            margin-bottom: 30px;
        }}

        .section h2 {{
            font-size: 18px;
            margin-bottom: 15px;
        }}

        .two-column {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 25px;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }}

        th, td {{
            padding: 10px 12px;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }}

        th {{
            background: var(--bg-light);
            font-weight: 600;
            font-size: 11px;
            text-transform: uppercase;
            color: var(--text-muted);
        }}

        .cost {{
            font-weight: 600;
            color: var(--primary);
        }}

        .count {{
            color: var(--text-muted);
        }}

        .priority-critical {{ color: var(--danger); font-weight: 600; }}
        .priority-high {{ color: #ea580c; font-weight: 600; }}
        .priority-medium {{ color: var(--warning); }}
        .priority-low {{ color: var(--success); }}

        .critical-path {{
            background: #fef2f2;
            border: 1px solid #fecaca;
            border-radius: 8px;
            padding: 15px 20px;
            margin-bottom: 25px;
        }}

        .critical-path h3 {{
            margin: 0 0 10px 0;
            color: var(--danger);
            font-size: 14px;
        }}

        .critical-path ul {{
            margin: 0;
            padding-left: 20px;
        }}

        .critical-path li {{
            margin-bottom: 6px;
        }}

        .work-items-section {{
            margin-top: 30px;
        }}

        @media (max-width: 800px) {{
            .two-column {{
                grid-template-columns: 1fr;
            }}

            .phase-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Investment Report</h1>
        <div class="meta">
            {target_name} | One-Time Investments | Generated {datetime.now().strftime('%B %d, %Y')}
        </div>
    </div>

    <div class="total-card">
        <div class="value">{total_display}</div>
        <div class="label">Total One-Time Investment ({investment_data.total_count} work items)</div>
    </div>

    <div class="phase-grid">
        {phase_cards}
    </div>

    {critical_html}

    <div class="two-column">
        <div class="section">
            <h2>By Domain</h2>
            <table>
                <thead>
                    <tr>
                        <th>Domain</th>
                        <th>Investment</th>
                        <th>Items</th>
                    </tr>
                </thead>
                <tbody>
                    {domain_rows if domain_rows else '<tr><td colspan="3">No domain data</td></tr>'}
                </tbody>
            </table>
        </div>

        <div class="section">
            <h2>By Type</h2>
            <table>
                <thead>
                    <tr>
                        <th>Type</th>
                        <th>Investment</th>
                    </tr>
                </thead>
                <tbody>
                    {type_rows if type_rows else '<tr><td colspan="2">No type data</td></tr>'}
                </tbody>
            </table>
        </div>
    </div>

    <div class="section">
        <h2>By Priority</h2>
        <table>
            <thead>
                <tr>
                    <th>Priority</th>
                    <th>Investment</th>
                    <th>Items</th>
                </tr>
            </thead>
            <tbody>
                {priority_rows if priority_rows else '<tr><td colspan="3">No priority data</td></tr>'}
            </tbody>
        </table>
    </div>

    <div class="section work-items-section">
        <h2>Work Items Detail</h2>
        <table>
            <thead>
                <tr>
                    <th>Work Item</th>
                    <th>Domain</th>
                    <th>Phase</th>
                    <th>Priority</th>
                    <th>Cost</th>
                    <th>Owner</th>
                </tr>
            </thead>
            <tbody>
                {work_items_rows if work_items_rows else '<tr><td colspan="6">No work items</td></tr>'}
            </tbody>
        </table>
        {f'<p style="color: var(--text-muted); margin-top: 10px;">Showing {min(20, len(investment_data.work_items))} of {len(investment_data.work_items)} work items</p>' if len(investment_data.work_items) > 20 else ''}
    </div>
</body>
</html>"""

    return html


def save_investment_report(
    investment_data: InvestmentReportData,
    output_dir: Path,
    target_name: str = "Target Company"
) -> Path:
    """
    Save investment report to file.

    Args:
        investment_data: Investment report data
        output_dir: Output directory
        target_name: Target company name

    Returns:
        Path to saved file
    """
    html = render_investment_report_html(investment_data, target_name)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"investment_report_{timestamp}.html"

    output_file.write_text(html)
    logger.info(f"Saved investment report to {output_file}")

    return output_file
