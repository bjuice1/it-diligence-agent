"""
HTML Report Generator for IT DD Synthesis.

Produces a clean, professional HTML report from SynthesisResult.
"""
from typing import Optional
from .models import SynthesisResult
from .cost_engine import format_currency


def generate_html_report(result: SynthesisResult, include_details: bool = True) -> str:
    """
    Generate complete HTML report.

    Args:
        result: SynthesisResult from synthesizer
        include_details: Include detailed appendices

    Returns:
        Complete HTML document as string
    """
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IT Due Diligence Report - {result.target_company}</title>
    <style>
        {_get_styles()}
    </style>
</head>
<body>
    <div class="container">
        {_generate_header(result)}
        {_generate_executive_summary(result)}
        {_generate_risk_summary(result)}
        {_generate_cost_summary(result)}
        {_generate_domain_summaries(result)}
        {_generate_questions_section(result) if result.questions else ''}
        {_generate_application_inventory(result) if include_details else ''}
        {_generate_risk_register(result) if include_details else ''}
        {_generate_footer(result)}
    </div>
</body>
</html>"""

    return html


def _get_styles() -> str:
    """CSS styles for the report."""
    return """
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: white;
        }
        h1 { color: #1a365d; border-bottom: 3px solid #2c5282; padding-bottom: 10px; margin-bottom: 20px; }
        h2 { color: #2c5282; margin: 30px 0 15px 0; padding-bottom: 5px; border-bottom: 1px solid #e2e8f0; }
        h3 { color: #4a5568; margin: 20px 0 10px 0; }

        .header { text-align: center; margin-bottom: 30px; }
        .header .subtitle { color: #718096; font-size: 1.1em; }
        .header .date { color: #a0aec0; font-size: 0.9em; margin-top: 5px; }

        .exec-summary {
            background: #ebf8ff;
            border-left: 4px solid #3182ce;
            padding: 20px;
            margin: 20px 0;
        }
        .exec-summary .assessment {
            font-size: 1.2em;
            font-weight: bold;
            color: #2c5282;
        }

        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .metric-card {
            background: #f7fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
        }
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            color: #2c5282;
        }
        .metric-label { color: #718096; font-size: 0.9em; }

        .risk-badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
        }
        .risk-critical { background: #fed7d7; color: #c53030; }
        .risk-high { background: #feebc8; color: #c05621; }
        .risk-medium { background: #fefcbf; color: #975a16; }
        .risk-low { background: #c6f6d5; color: #276749; }

        table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            font-size: 0.9em;
        }
        th, td {
            padding: 10px 12px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }
        th {
            background: #f7fafc;
            font-weight: 600;
            color: #4a5568;
        }
        tr:hover { background: #f7fafc; }

        .findings-list {
            list-style: none;
            padding: 0;
        }
        .findings-list li {
            padding: 8px 0;
            border-bottom: 1px solid #edf2f7;
        }
        .findings-list li:before {
            content: "•";
            color: #3182ce;
            font-weight: bold;
            margin-right: 10px;
        }

        .cost-summary {
            background: #f0fff4;
            border: 1px solid #9ae6b4;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }
        .cost-range {
            font-size: 1.5em;
            font-weight: bold;
            color: #276749;
        }

        .domain-card {
            background: #f7fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
        }
        .domain-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        .domain-name { font-weight: bold; color: #2c5282; }

        .questions-section {
            background: #fffbeb;
            border: 1px solid #fbd38d;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }

        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e2e8f0;
            text-align: center;
            color: #a0aec0;
            font-size: 0.85em;
        }

        @media print {
            body { background: white; }
            .container { max-width: 100%; }
            .no-print { display: none; }
        }
    """


def _generate_header(result: SynthesisResult) -> str:
    """Generate report header."""
    return f"""
    <div class="header">
        <h1>IT Due Diligence Report</h1>
        <div class="subtitle">{result.target_company}</div>
        <div class="date">Generated: {result.generated_at[:10]}</div>
    </div>
    """


def _generate_executive_summary(result: SynthesisResult) -> str:
    """Generate executive summary section."""
    critical_count = len([r for r in result.risks if r.severity == "Critical"])
    high_count = len([r for r in result.risks if r.severity == "High"])

    findings_html = "".join([f"<li>{f}</li>" for f in result.key_findings[:5]])

    return f"""
    <h2>Executive Summary</h2>
    <div class="exec-summary">
        <div class="assessment">{result.overall_assessment}</div>
    </div>

    <div class="metrics-grid">
        <div class="metric-card">
            <div class="metric-value">{len(result.applications)}</div>
            <div class="metric-label">Applications Identified</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{critical_count}</div>
            <div class="metric-label">Critical Risks</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{high_count}</div>
            <div class="metric-label">High Risks</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{format_currency(result.total_one_time_low)} - {format_currency(result.total_one_time_high)}</div>
            <div class="metric-label">Est. Remediation Cost</div>
        </div>
    </div>

    <h3>Key Findings</h3>
    <ul class="findings-list">
        {findings_html if findings_html else '<li>No critical or high findings identified</li>'}
    </ul>
    """


def _generate_risk_summary(result: SynthesisResult) -> str:
    """Generate risk summary section."""
    critical_risks = [r for r in result.risks if r.severity == "Critical"]
    high_risks = [r for r in result.risks if r.severity == "High"]

    critical_html = "".join([
        f'<tr><td><span class="risk-badge risk-critical">Critical</span></td><td>{r.title}</td><td>{r.domain}</td></tr>'
        for r in critical_risks
    ])

    high_html = "".join([
        f'<tr><td><span class="risk-badge risk-high">High</span></td><td>{r.title}</td><td>{r.domain}</td></tr>'
        for r in high_risks[:5]
    ])

    return f"""
    <h2>Risk Summary</h2>

    <table>
        <thead>
            <tr><th>Severity</th><th>Risk</th><th>Domain</th></tr>
        </thead>
        <tbody>
            {critical_html}
            {high_html}
        </tbody>
    </table>
    """


def _generate_cost_summary(result: SynthesisResult) -> str:
    """Generate cost summary section."""
    if not result.cost_items:
        return ""

    items_html = "".join([
        f'<tr><td>{c.description}</td><td>{c.timing}</td><td>{format_currency(c.low_estimate)} - {format_currency(c.high_estimate)}</td></tr>'
        for c in result.cost_items[:10]
    ])

    return f"""
    <h2>Cost Implications</h2>

    <div class="cost-summary">
        <div class="cost-range">Estimated Total: {format_currency(result.total_one_time_low)} - {format_currency(result.total_one_time_high)}</div>
        <p style="margin-top: 10px; color: #718096;">ROM estimates for planning purposes. Detailed scoping required.</p>
    </div>

    <table>
        <thead>
            <tr><th>Item</th><th>Timing</th><th>Estimate</th></tr>
        </thead>
        <tbody>
            {items_html}
        </tbody>
    </table>
    """


def _generate_domain_summaries(result: SynthesisResult) -> str:
    """Generate domain summary cards."""
    cards_html = ""
    for domain, summary in result.domain_summaries.items():
        risk_text = f"{summary.critical_risks} critical, {summary.risk_count} total"
        top_risks_html = "".join([f"<li>{r}</li>" for r in summary.top_risks[:3]])

        cards_html += f"""
        <div class="domain-card">
            <div class="domain-header">
                <span class="domain-name">{domain}</span>
                <span>{risk_text}</span>
            </div>
            <ul class="findings-list" style="font-size: 0.9em;">
                {top_risks_html if top_risks_html else '<li>No significant risks identified</li>'}
            </ul>
        </div>
        """

    return f"""
    <h2>Domain Summaries</h2>
    {cards_html}
    """


def _generate_questions_section(result: SynthesisResult) -> str:
    """Generate follow-up questions section."""
    must_have = [q for q in result.questions if "must" in q.priority.lower()]
    important = [q for q in result.questions if "important" in q.priority.lower()]

    must_html = "".join([f"<li><strong>{q.question}</strong><br><em>{q.why_it_matters}</em></li>" for q in must_have[:5]])
    important_html = "".join([f"<li>{q.question}</li>" for q in important[:5]])

    return f"""
    <h2>Follow-Up Questions for Management</h2>
    <div class="questions-section">
        <h3>Must Ask</h3>
        <ul class="findings-list">
            {must_html if must_html else '<li>No critical questions identified</li>'}
        </ul>

        <h3>Important</h3>
        <ul class="findings-list">
            {important_html if important_html else '<li>No additional questions</li>'}
        </ul>
    </div>
    """


def _generate_application_inventory(result: SynthesisResult) -> str:
    """Generate application inventory appendix."""
    if not result.applications:
        return ""

    rows_html = ""
    for app in result.applications:
        eol_badge = ""
        if app.eol_status == "Past_EOL":
            eol_badge = '<span class="risk-badge risk-critical">Past EOL</span>'
        elif app.eol_status == "Approaching_EOL":
            eol_badge = '<span class="risk-badge risk-high">Approaching EOL</span>'

        rows_html += f"""
        <tr>
            <td>{app.id}</td>
            <td>{app.name}</td>
            <td>{app.vendor}</td>
            <td>{app.category}</td>
            <td>{app.hosting}</td>
            <td>{app.version} {eol_badge}</td>
            <td>{app.criticality}</td>
        </tr>
        """

    return f"""
    <h2>Appendix A: Application Inventory</h2>
    <table>
        <thead>
            <tr><th>ID</th><th>Application</th><th>Vendor</th><th>Category</th><th>Hosting</th><th>Version</th><th>Criticality</th></tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>
    """


def _generate_risk_register(result: SynthesisResult) -> str:
    """Generate risk register appendix."""
    if not result.risks:
        return ""

    rows_html = ""
    for risk in result.risks:
        severity_class = f"risk-{risk.severity.lower()}"
        rows_html += f"""
        <tr>
            <td>{risk.id}</td>
            <td><span class="risk-badge {severity_class}">{risk.severity}</span></td>
            <td>{risk.title}</td>
            <td>{risk.domain}</td>
            <td>{risk.mitigation[:100]}...</td>
        </tr>
        """

    return f"""
    <h2>Appendix B: Risk Register</h2>
    <table>
        <thead>
            <tr><th>ID</th><th>Severity</th><th>Risk</th><th>Domain</th><th>Mitigation</th></tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>
    """


def _generate_footer(result: SynthesisResult) -> str:
    """Generate report footer."""
    return f"""
    <div class="footer">
        <p>IT Due Diligence Report | {result.target_company} | Generated {result.generated_at[:10]}</p>
        <p>This report is for informational purposes. Findings should be validated through management interviews.</p>
    </div>
    """
