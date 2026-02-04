"""
Costs Report Generator

Consolidates all run-rate spending across domains.
Provides the "What It Costs Today" aggregate view.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from datetime import datetime

from tools_v2.pe_report_schemas import CostsReportData, DealContext
from tools_v2.pe_costs import build_costs_report_data

if TYPE_CHECKING:
    from stores.fact_store import FactStore
    from tools_v2.reasoning_tools import ReasoningStore

logger = logging.getLogger(__name__)


# =============================================================================
# COSTS REPORT GENERATION
# =============================================================================

def generate_costs_report(
    fact_store: "FactStore",
    deal_context: Optional[DealContext] = None,
    entity: str = "target"
) -> CostsReportData:
    """
    Generate comprehensive costs report data.

    Args:
        fact_store: Fact store with discovered facts
        deal_context: Optional deal context
        entity: Entity to filter by

    Returns:
        CostsReportData instance
    """
    return build_costs_report_data(fact_store, deal_context, entity)


def render_costs_report_html(
    costs_data: CostsReportData,
    target_name: str = "Target Company"
) -> str:
    """
    Render costs report to HTML.

    Args:
        costs_data: Costs report data
        target_name: Target company name

    Returns:
        Complete HTML document
    """
    # Format total
    total_low, total_high = costs_data.total_run_rate
    if total_high > 0:
        total_display = f"${total_low:,.0f} - ${total_high:,.0f}"
    else:
        total_display = "Not documented"

    # Format per-employee
    if costs_data.cost_per_employee:
        per_emp_display = f"${costs_data.cost_per_employee:,.0f}"
    else:
        per_emp_display = "N/A"

    # Format IT % revenue
    if costs_data.it_pct_revenue:
        pct_display = f"{costs_data.it_pct_revenue:.1f}%"
    else:
        pct_display = "N/A"

    # Build domain breakdown rows
    domain_rows = ""
    for domain, (low, high) in sorted(costs_data.by_domain.items()):
        if high > 0:
            cost_display = f"${low:,.0f} - ${high:,.0f}"
            pct_of_total = ((low + high) / 2 / ((total_low + total_high) / 2) * 100) if total_high > 0 else 0
            domain_rows += f"""
            <tr>
                <td><strong>{domain.replace('_', ' ').title()}</strong></td>
                <td class="cost">{cost_display}</td>
                <td class="pct">{pct_of_total:.1f}%</td>
            </tr>
            """

    # Build category breakdown rows
    category_rows = ""
    category_costs = [
        ("Infrastructure", costs_data.infrastructure_costs),
        ("Applications", costs_data.application_costs),
        ("Personnel", costs_data.personnel_costs),
        ("Vendors/MSP", costs_data.vendor_costs),
        ("Network", costs_data.network_costs),
    ]

    for cat_name, (low, high) in category_costs:
        if high > 0:
            cost_display = f"${low:,.0f} - ${high:,.0f}"
            pct_of_total = ((low + high) / 2 / ((total_low + total_high) / 2) * 100) if total_high > 0 else 0
            category_rows += f"""
            <tr>
                <td><strong>{cat_name}</strong></td>
                <td class="cost">{cost_display}</td>
                <td class="pct">{pct_of_total:.1f}%</td>
            </tr>
            """

    # Key cost drivers
    drivers_html = ""
    if costs_data.key_cost_drivers:
        items = [f"<li>{d}</li>" for d in costs_data.key_cost_drivers]
        drivers_html = f'<ul class="drivers-list">{"".join(items)}</ul>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{target_name} - IT Costs Report</title>
    <style>
        :root {{
            --primary: #2563eb;
            --text: #1f2937;
            --text-muted: #6b7280;
            --bg-light: #f9fafb;
            --border: #e5e7eb;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: var(--text);
            max-width: 1000px;
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

        .summary-cards {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-bottom: 30px;
        }}

        .summary-card {{
            background: var(--bg-light);
            padding: 25px;
            border-radius: 10px;
            text-align: center;
        }}

        .summary-card .value {{
            font-size: 28px;
            font-weight: 700;
            color: var(--primary);
            margin-bottom: 5px;
        }}

        .summary-card .label {{
            font-size: 13px;
            color: var(--text-muted);
            text-transform: uppercase;
        }}

        .section {{
            margin-bottom: 30px;
        }}

        .section h2 {{
            font-size: 18px;
            margin-bottom: 15px;
            color: var(--text);
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
        }}

        th, td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }}

        th {{
            background: var(--bg-light);
            font-weight: 600;
            font-size: 12px;
            text-transform: uppercase;
            color: var(--text-muted);
        }}

        .cost {{
            font-weight: 600;
            color: var(--primary);
        }}

        .pct {{
            color: var(--text-muted);
        }}

        .drivers-list {{
            margin: 0;
            padding-left: 20px;
        }}

        .drivers-list li {{
            margin-bottom: 8px;
        }}

        .benchmark-box {{
            background: #eff6ff;
            border: 1px solid #bfdbfe;
            border-radius: 8px;
            padding: 15px 20px;
            margin-top: 20px;
        }}

        .facts-cited {{
            font-size: 12px;
            color: var(--text-muted);
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>IT Costs Report</h1>
        <div class="meta">
            {target_name} | Run-Rate Analysis | Generated {datetime.now().strftime('%B %d, %Y')}
        </div>
    </div>

    <div class="summary-cards">
        <div class="summary-card">
            <div class="value">{total_display}</div>
            <div class="label">Total Annual IT Budget</div>
        </div>
        <div class="summary-card">
            <div class="value">{per_emp_display}</div>
            <div class="label">Cost per Employee</div>
        </div>
        <div class="summary-card">
            <div class="value">{pct_display}</div>
            <div class="label">IT % of Revenue</div>
        </div>
    </div>

    <div class="section">
        <h2>Costs by Domain</h2>
        <table>
            <thead>
                <tr>
                    <th>Domain</th>
                    <th>Annual Cost</th>
                    <th>% of Total</th>
                </tr>
            </thead>
            <tbody>
                {domain_rows if domain_rows else '<tr><td colspan="3">No domain costs documented</td></tr>'}
            </tbody>
        </table>
    </div>

    <div class="section">
        <h2>Costs by Category</h2>
        <table>
            <thead>
                <tr>
                    <th>Category</th>
                    <th>Annual Cost</th>
                    <th>% of Total</th>
                </tr>
            </thead>
            <tbody>
                {category_rows if category_rows else '<tr><td colspan="3">No category costs documented</td></tr>'}
            </tbody>
        </table>
    </div>

    <div class="section">
        <h2>Key Cost Drivers</h2>
        {drivers_html if drivers_html else '<p>No key cost drivers identified</p>'}

        {f'<div class="benchmark-box"><strong>Benchmark Assessment:</strong> {costs_data.benchmark_assessment}</div>' if costs_data.benchmark_assessment else ''}
    </div>

    <div class="facts-cited">
        Based on: {', '.join(costs_data.cost_facts_cited[:10])}{'...' if len(costs_data.cost_facts_cited) > 10 else ''}
    </div>
</body>
</html>"""

    return html


def save_costs_report(
    costs_data: CostsReportData,
    output_dir: Path,
    target_name: str = "Target Company"
) -> Path:
    """
    Save costs report to file.

    Args:
        costs_data: Costs report data
        output_dir: Output directory
        target_name: Target company name

    Returns:
        Path to saved file
    """
    html = render_costs_report_html(costs_data, target_name)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"costs_report_{timestamp}.html"

    output_file.write_text(html)
    logger.info(f"Saved costs report to {output_file}")

    return output_file
