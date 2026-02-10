"""
Separation Costs Report Generator

One-time costs for IT separation/integration using driver-based cost models.
This complements the run-rate costs report with scenario-based estimates.
"""

import logging
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from stores.fact_store import FactStore

logger = logging.getLogger(__name__)


def generate_separation_costs_report(
    deal_id: str,
    fact_store: "FactStore" = None,
    deal_context = None,
) -> Dict[str, Any]:
    """
    Generate separation/integration costs report data.

    Uses the new driver-based cost engine for deterministic calculations.

    Args:
        deal_id: Deal identifier
        fact_store: Fact store with discovered facts
        deal_context: Optional deal context

    Returns:
        Dict with costs summary and estimates
    """
    from services.cost_engine import get_effective_drivers, calculate_deal_costs

    # Get drivers and calculate costs
    driver_result = get_effective_drivers(deal_id, fact_store)
    summary = calculate_deal_costs(deal_id, driver_result.drivers)

    return {
        'deal_id': deal_id,
        'summary': summary,
        'drivers': driver_result.drivers,
        'driver_stats': {
            'extracted': driver_result.drivers_extracted,
            'assumed': driver_result.drivers_assumed,
        },
        'generated_at': datetime.utcnow().isoformat(),
    }


def render_separation_costs_html(
    data: Dict[str, Any],
    target_name: str = "Target Company"
) -> str:
    """
    Render separation costs report to HTML.

    Args:
        data: Report data from generate_separation_costs_report
        target_name: Target company name

    Returns:
        Complete HTML document
    """
    summary = data['summary']
    drivers = data['drivers']
    driver_stats = data['driver_stats']

    # Tower breakdown rows
    tower_rows = ""
    for tower, costs in summary.tower_costs.items():
        tower_rows += f"""
        <tr>
            <td><strong>{tower}</strong></td>
            <td class="cost upside">${costs['one_time_upside']:,.0f}</td>
            <td class="cost base">${costs['one_time_base']:,.0f}</td>
            <td class="cost stress">${costs['one_time_stress']:,.0f}</td>
            <td class="cost">${costs['annual_licenses']:,.0f}</td>
            <td class="items">{', '.join(costs['items'])}</td>
        </tr>
        """

    # Work item rows
    work_item_rows = ""
    for est in summary.estimates:
        complexity_class = 'low' if est.complexity == 'low' else 'high' if est.complexity == 'high' else 'medium'
        work_item_rows += f"""
        <tr>
            <td><span class="tower-badge">{est.tower}</span> {est.display_name}</td>
            <td class="cost upside">${est.one_time_upside:,.0f}</td>
            <td class="cost base">${est.one_time_base:,.0f}</td>
            <td class="cost stress">${est.one_time_stress:,.0f}</td>
            <td class="cost">${est.annual_licenses:,.0f}</td>
            <td><span class="complexity-{complexity_class}">{est.complexity.title()}</span></td>
            <td>{est.estimated_months}mo</td>
        </tr>
        """

    # Driver highlights
    driver_rows = ""
    key_drivers = [
        ('total_users', 'Total Users'),
        ('sites', 'Sites'),
        ('endpoints', 'Endpoints'),
        ('erp_system', 'ERP System'),
        ('identity_provider', 'Identity Provider'),
    ]
    for field, label in key_drivers:
        value = getattr(drivers, field, None)
        if value is not None:
            source = drivers.sources.get(field)
            confidence = source.confidence.value if source else 'unknown'
            conf_class = 'high' if confidence == 'high' else 'low' if confidence == 'low' else 'medium'

            display_val = f"{value:,}" if isinstance(value, int) else str(value)
            driver_rows += f"""
            <tr>
                <td>{label}</td>
                <td><strong>{display_val}</strong></td>
                <td><span class="confidence-{conf_class}">{confidence.upper()}</span></td>
            </tr>
            """

    # Assumptions list
    assumptions_list = ""
    for assumption in summary.top_assumptions[:10]:
        assumptions_list += f"<li>{assumption}</li>"

    # Parent dependencies
    parent_deps = ""
    if drivers.shared_with_parent:
        services = ', '.join([s.title() for s in drivers.shared_with_parent])
        parent_deps = f"""
        <div class="alert alert-parent">
            <strong>Parent Dependencies Identified:</strong> {services}
            <p>These services are currently provided by/shared with the parent company.
            Separation costs include standing up independent capability.</p>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{target_name} - IT Separation Costs</title>
    <style>
        :root {{
            --primary: #2563eb;
            --text: #1f2937;
            --text-muted: #6b7280;
            --bg-light: #f9fafb;
            --border: #e5e7eb;
            --green: #16a34a;
            --red: #dc2626;
            --amber: #f59e0b;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: var(--text);
            max-width: 1100px;
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
            margin: 0 0 8px 0;
            color: var(--primary);
        }}

        .header .subtitle {{
            color: var(--text-muted);
            font-size: 14px;
        }}

        /* Executive Summary */
        .exec-summary {{
            display: flex;
            gap: 40px;
            padding: 30px;
            background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
            color: white;
            border-radius: 12px;
            margin-bottom: 30px;
        }}

        .scenario-card {{
            text-align: center;
            flex: 1;
        }}

        .scenario-label {{
            font-size: 12px;
            text-transform: uppercase;
            opacity: 0.8;
        }}

        .scenario-value {{
            font-size: 28px;
            font-weight: 700;
        }}

        .scenario-upside .scenario-value {{ color: #86efac; }}
        .scenario-base .scenario-value {{ color: white; }}
        .scenario-stress .scenario-value {{ color: #fca5a5; }}

        .licenses-summary {{
            text-align: right;
        }}

        .licenses-label {{
            font-size: 12px;
            opacity: 0.8;
        }}

        .licenses-value {{
            font-size: 22px;
            font-weight: 600;
            color: #fef08a;
        }}

        /* Tables */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 24px;
        }}

        th, td {{
            padding: 10px 12px;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }}

        th {{
            font-size: 11px;
            text-transform: uppercase;
            color: var(--text-muted);
            font-weight: 600;
            background: var(--bg-light);
        }}

        .cost {{
            text-align: right;
            font-family: 'SF Mono', Monaco, monospace;
        }}

        .cost.upside {{ color: var(--green); }}
        .cost.base {{ color: var(--primary); font-weight: 600; }}
        .cost.stress {{ color: var(--red); }}

        .items {{
            font-size: 12px;
            color: var(--text-muted);
        }}

        .total-row {{
            font-weight: 600;
            background: var(--bg-light);
        }}

        .total-row td {{
            border-top: 2px solid var(--border);
        }}

        /* Badges */
        .tower-badge {{
            display: inline-block;
            font-size: 10px;
            padding: 2px 6px;
            border-radius: 4px;
            margin-right: 6px;
            background: #e0e7ff;
            color: #4338ca;
        }}

        .complexity-low {{ color: var(--green); }}
        .complexity-medium {{ color: var(--amber); }}
        .complexity-high {{ color: var(--red); }}

        .confidence-high {{ color: var(--green); font-size: 11px; }}
        .confidence-medium {{ color: var(--amber); font-size: 11px; }}
        .confidence-low {{ color: var(--red); font-size: 11px; }}

        /* Sections */
        .section {{
            margin-bottom: 30px;
        }}

        .section h2 {{
            font-size: 18px;
            color: var(--text);
            margin: 0 0 16px 0;
            padding-bottom: 8px;
            border-bottom: 1px solid var(--border);
        }}

        /* Alert */
        .alert {{
            padding: 16px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}

        .alert-parent {{
            background: #fef2f2;
            border: 1px solid #fecaca;
            color: #991b1b;
        }}

        .alert-parent p {{
            margin: 8px 0 0 0;
            font-size: 13px;
        }}

        /* Assumptions */
        .assumptions-list {{
            columns: 2;
            padding-left: 20px;
            font-size: 13px;
        }}

        .assumptions-list li {{
            margin-bottom: 6px;
        }}

        /* Grid Layout */
        .two-col {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
        }}

        /* Driver Stats */
        .driver-stats {{
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
        }}

        .stat {{
            background: var(--bg-light);
            padding: 12px 20px;
            border-radius: 8px;
            text-align: center;
        }}

        .stat-value {{
            font-size: 24px;
            font-weight: 700;
            color: var(--primary);
        }}

        .stat-label {{
            font-size: 12px;
            color: var(--text-muted);
        }}

        /* Footer */
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid var(--border);
            color: var(--text-muted);
            font-size: 12px;
        }}

        @media print {{
            body {{ padding: 20px; }}
            .exec-summary {{ -webkit-print-color-adjust: exact; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{target_name} - IT Separation Costs</h1>
        <div class="subtitle">One-Time Costs for IT Separation/Integration | Driver-Based Estimates</div>
    </div>

    <div class="exec-summary">
        <div class="scenario-card scenario-upside">
            <div class="scenario-label">Upside</div>
            <div class="scenario-value">${summary.total_one_time_upside:,.0f}</div>
        </div>
        <div class="scenario-card scenario-base">
            <div class="scenario-label">Base Case</div>
            <div class="scenario-value">${summary.total_one_time_base:,.0f}</div>
        </div>
        <div class="scenario-card scenario-stress">
            <div class="scenario-label">Stress</div>
            <div class="scenario-value">${summary.total_one_time_stress:,.0f}</div>
        </div>
        <div class="licenses-summary">
            <div class="licenses-label">Annual Licenses</div>
            <div class="licenses-value">${summary.total_annual_licenses:,.0f}/yr</div>
        </div>
    </div>

    {parent_deps}

    <div class="section">
        <h2>Costs by Tower</h2>
        <table>
            <thead>
                <tr>
                    <th>Tower</th>
                    <th style="text-align:right">Upside</th>
                    <th style="text-align:right">Base</th>
                    <th style="text-align:right">Stress</th>
                    <th style="text-align:right">Annual</th>
                    <th>Work Items</th>
                </tr>
            </thead>
            <tbody>
                {tower_rows}
            </tbody>
            <tfoot>
                <tr class="total-row">
                    <td>TOTAL</td>
                    <td class="cost upside">${summary.total_one_time_upside:,.0f}</td>
                    <td class="cost base">${summary.total_one_time_base:,.0f}</td>
                    <td class="cost stress">${summary.total_one_time_stress:,.0f}</td>
                    <td class="cost">${summary.total_annual_licenses:,.0f}</td>
                    <td></td>
                </tr>
            </tfoot>
        </table>
    </div>

    <div class="section">
        <h2>Work Item Details</h2>
        <table>
            <thead>
                <tr>
                    <th>Work Item</th>
                    <th style="text-align:right">Upside</th>
                    <th style="text-align:right">Base</th>
                    <th style="text-align:right">Stress</th>
                    <th style="text-align:right">Annual</th>
                    <th>Complexity</th>
                    <th>Timeline</th>
                </tr>
            </thead>
            <tbody>
                {work_item_rows}
            </tbody>
        </table>
    </div>

    <div class="two-col">
        <div class="section">
            <h2>Key Drivers</h2>
            <div class="driver-stats">
                <div class="stat">
                    <div class="stat-value">{driver_stats['extracted']}</div>
                    <div class="stat-label">Extracted</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{driver_stats['assumed']}</div>
                    <div class="stat-label">Assumed</div>
                </div>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Driver</th>
                        <th>Value</th>
                        <th>Confidence</th>
                    </tr>
                </thead>
                <tbody>
                    {driver_rows}
                </tbody>
            </table>
        </div>

        <div class="section">
            <h2>Key Assumptions</h2>
            <ul class="assumptions-list">
                {assumptions_list}
            </ul>
            <p style="font-size:12px; color:var(--text-muted); margin-top:16px;">
                To tighten estimates, verify assumed driver values and provide actuals.
            </p>
        </div>
    </div>

    <div class="footer">
        <p>Generated: {data['generated_at'][:10]} | Deal ID: {data['deal_id']}</p>
        <p>Costs are based on driver-based models with scenario multipliers (Upside: 0.85x, Base: 1.0x, Stress: 1.3x)</p>
    </div>
</body>
</html>
"""

    return html
