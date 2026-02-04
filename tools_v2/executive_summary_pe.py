"""
PE Executive Summary Generator

Synthesizes "things that matter" across all domains.
NOT a deal recommendation - just key things PE buyer should know.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from datetime import datetime

from tools_v2.pe_report_schemas import (
    ExecutiveSummaryData,
    DomainHighlight,
    RiskSummary,
    DomainReportData,
    DealContext,
    DOMAIN_ORDER,
    DOMAIN_DISPLAY_NAMES,
)
from tools_v2.pe_costs import (
    build_costs_report_data,
    build_investment_report_data,
    extract_it_budget_summary,
)
from tools_v2.pe_narrative import generate_domain_highlight

if TYPE_CHECKING:
    from stores.fact_store import FactStore
    from tools_v2.reasoning_tools import ReasoningStore

logger = logging.getLogger(__name__)


# =============================================================================
# EXECUTIVE SUMMARY GENERATION
# =============================================================================

def generate_executive_summary(
    fact_store: "FactStore",
    reasoning_store: "ReasoningStore",
    deal_context: Optional[DealContext] = None,
    domain_reports: Optional[Dict[str, DomainReportData]] = None,
    target_name: str = "Target Company"
) -> ExecutiveSummaryData:
    """
    Generate PE executive summary data.

    Args:
        fact_store: Fact store with discovered facts
        reasoning_store: Reasoning store with findings
        deal_context: Optional deal context
        domain_reports: Optional pre-generated domain reports
        target_name: Target company name

    Returns:
        ExecutiveSummaryData instance
    """
    # Get costs data
    costs_data = build_costs_report_data(fact_store, deal_context)
    investment_data = build_investment_report_data(reasoning_store)
    budget_summary = extract_it_budget_summary(fact_store, deal_context)

    # Build domain highlights
    domain_highlights = {}
    for domain in DOMAIN_ORDER:
        if domain_reports and domain in domain_reports:
            domain_data = domain_reports[domain]
            highlight = generate_domain_highlight(domain, domain_data)
        else:
            highlight = _generate_basic_highlight(domain, fact_store, reasoning_store)
        domain_highlights[domain] = highlight

    # Extract critical risks
    critical_risks = _extract_critical_risks(reasoning_store)

    # Extract key opportunities
    key_opportunities = _extract_key_opportunities(reasoning_store, domain_highlights)

    # Identify benchmark outliers
    benchmark_outliers = _identify_benchmark_outliers(domain_reports) if domain_reports else []

    # Identify major investments (>$500K)
    major_investments = _identify_major_investments(investment_data)

    # Generate overall narrative
    overall_narrative = _generate_overall_narrative(
        target_name,
        domain_highlights,
        critical_risks,
        costs_data,
        investment_data
    )

    return ExecutiveSummaryData(
        target_name=target_name,
        analysis_date=datetime.now().strftime("%Y-%m-%d"),
        domains_analyzed=len(domain_highlights),
        total_it_budget=costs_data.total_run_rate,
        total_investment_needed=investment_data.total_one_time,
        it_headcount=budget_summary.get("it_headcount") or 0,
        it_pct_revenue=budget_summary.get("it_pct_revenue"),
        critical_risks=critical_risks,
        key_opportunities=key_opportunities,
        benchmark_outliers=benchmark_outliers,
        major_investments=major_investments,
        domain_highlights=domain_highlights,
        overall_narrative=overall_narrative,
    )


def _generate_basic_highlight(
    domain: str,
    fact_store: "FactStore",
    reasoning_store: "ReasoningStore"
) -> DomainHighlight:
    """Generate basic domain highlight without full domain report."""
    display_name = DOMAIN_DISPLAY_NAMES.get(domain, domain.replace("_", " ").title())

    # Count facts and risks
    domain_facts = [f for f in fact_store.facts if f.domain == domain]
    domain_risks = [r for r in reasoning_store.risks if r.domain == domain]
    domain_work_items = [wi for wi in reasoning_store.work_items if wi.domain == domain]

    # Determine grade
    critical_count = len([r for r in domain_risks if r.severity == "critical"])
    high_count = len([r for r in domain_risks if r.severity == "high"])

    if critical_count > 0:
        grade = "Needs Improvement"
        key_finding = f"Critical issues identified - {critical_count} critical, {high_count} high severity risks"
    elif high_count >= 2:
        grade = "Needs Improvement"
        key_finding = f"Multiple high-severity risks requiring attention"
    elif len(domain_facts) < 3:
        grade = "Adequate"
        key_finding = "Limited data available for assessment"
    else:
        grade = "Adequate"
        key_finding = f"Baseline established with {len(domain_facts)} facts"

    # Watch items from risks
    watch_items = [r.title for r in domain_risks[:3] if r.severity in ("critical", "high")]

    return DomainHighlight(
        domain=domain,
        domain_display_name=display_name,
        overall_grade=grade,
        key_finding=key_finding,
        watch_items=watch_items,
        run_rate_cost=(0, 0),
        investment_needed=(0, 0),
        work_item_count=len(domain_work_items),
        risk_count=len(domain_risks),
    )


def _extract_critical_risks(
    reasoning_store: "ReasoningStore",
    max_risks: int = 5
) -> List[RiskSummary]:
    """Extract critical and high risks for summary."""
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}

    sorted_risks = sorted(
        reasoning_store.risks,
        key=lambda r: (severity_order.get(r.severity, 4), r.domain)
    )

    # Filter to critical and high only
    important_risks = [r for r in sorted_risks if r.severity in ("critical", "high")]

    summaries = []
    for risk in important_risks[:max_risks]:
        summaries.append(RiskSummary(
            title=risk.title,
            domain=risk.domain,
            severity=risk.severity,
            implication=risk.mna_implication or risk.description[:150],
            mitigation=risk.mitigation or "",
            finding_id=risk.finding_id,
        ))

    return summaries


def _extract_key_opportunities(
    reasoning_store: "ReasoningStore",
    domain_highlights: Dict[str, DomainHighlight],
    max_opportunities: int = 3
) -> List[str]:
    """Extract key opportunities from strategic considerations."""
    opportunities = []

    # From strategic considerations
    for sc in reasoning_store.strategic_considerations:
        if sc.lens in ("synergy", "value_creation", "synergy_opportunity"):
            if sc.implication and sc.implication not in opportunities:
                opportunities.append(sc.implication)
                if len(opportunities) >= max_opportunities:
                    break

    # From strong domains
    if len(opportunities) < max_opportunities:
        for domain, highlight in domain_highlights.items():
            if highlight.overall_grade == "Strong" and len(opportunities) < max_opportunities:
                opportunities.append(f"{highlight.domain_display_name}: {highlight.key_finding}")

    return opportunities[:max_opportunities]


def _identify_benchmark_outliers(
    domain_reports: Dict[str, DomainReportData],
    max_outliers: int = 5
) -> List[str]:
    """Identify domains significantly above/below benchmarks."""
    outliers = []

    for domain, report in domain_reports.items():
        assessment = report.benchmark_assessment

        # Check for outliers
        if assessment.cost_posture == "bloated":
            outliers.append(f"{DOMAIN_DISPLAY_NAMES.get(domain, domain)}: Cost posture above benchmarks")
        elif assessment.cost_posture == "lean":
            outliers.append(f"{DOMAIN_DISPLAY_NAMES.get(domain, domain)}: Cost posture below benchmarks - may need investment")

        if assessment.tech_age == "outdated":
            outliers.append(f"{DOMAIN_DISPLAY_NAMES.get(domain, domain)}: Technology aging/outdated")

        if assessment.maturity == "immature":
            outliers.append(f"{DOMAIN_DISPLAY_NAMES.get(domain, domain)}: Process maturity below typical")

    return outliers[:max_outliers]


def _identify_major_investments(
    investment_data: Any,
    threshold: int = 500000
) -> List[str]:
    """Identify work items with cost > threshold."""
    major = []

    for wi in investment_data.work_items:
        mid_cost = (wi.cost_estimate_low + wi.cost_estimate_high) / 2
        if mid_cost >= threshold:
            cost_display = f"${wi.cost_estimate_low:,.0f}-${wi.cost_estimate_high:,.0f}"
            major.append(f"{wi.title} ({cost_display})")

    return major[:5]


def _generate_overall_narrative(
    target_name: str,
    domain_highlights: Dict[str, DomainHighlight],
    critical_risks: List[RiskSummary],
    costs_data: Any,
    investment_data: Any
) -> str:
    """Generate 2-3 paragraph overall narrative."""
    # Count grades
    grade_counts = {"Strong": 0, "Adequate": 0, "Needs Improvement": 0}
    for highlight in domain_highlights.values():
        if highlight.overall_grade in grade_counts:
            grade_counts[highlight.overall_grade] += 1

    # Paragraph 1: Overall characterization
    total_domains = len(domain_highlights)
    strong_count = grade_counts["Strong"]
    needs_improvement_count = grade_counts["Needs Improvement"]

    if needs_improvement_count >= 3:
        overall_char = f"The IT estate at {target_name} requires significant attention, with {needs_improvement_count} of {total_domains} domains flagged for improvement."
    elif needs_improvement_count >= 1:
        problem_domains = [h.domain_display_name for h in domain_highlights.values()
                         if h.overall_grade == "Needs Improvement"]
        overall_char = f"The IT estate is generally adequate, though {', '.join(problem_domains)} require{'s' if len(problem_domains) == 1 else ''} focused attention."
    elif strong_count >= 4:
        overall_char = f"The IT estate at {target_name} is well-positioned with {strong_count} of {total_domains} domains showing strong fundamentals."
    else:
        overall_char = f"The IT estate is adequate for current operations with a typical mix of strengths and areas for improvement."

    # Paragraph 2: Key risks and costs
    run_rate_low, run_rate_high = costs_data.total_run_rate
    invest_low, invest_high = investment_data.total_one_time

    if run_rate_high > 0:
        cost_stmt = f"Current IT run-rate is ${run_rate_low:,.0f}-${run_rate_high:,.0f} annually"
    else:
        cost_stmt = "IT costs are not fully documented"

    if invest_high > 0:
        invest_stmt = f"with ${invest_low:,.0f}-${invest_high:,.0f} in identified investments"
    else:
        invest_stmt = "with investments to be determined"

    risk_stmt = ""
    if critical_risks:
        critical_count = len([r for r in critical_risks if r.severity == "critical"])
        high_count = len([r for r in critical_risks if r.severity == "high"])
        if critical_count > 0:
            risk_stmt = f" There are {critical_count} critical and {high_count} high-severity risks requiring immediate attention."
        elif high_count > 0:
            risk_stmt = f" There are {high_count} high-severity risks to address."

    cost_para = f"{cost_stmt} {invest_stmt}.{risk_stmt}"

    # Paragraph 3: Key takeaways
    takeaways = []
    if needs_improvement_count > 0:
        problem_domains = [h.domain_display_name for h in domain_highlights.values()
                         if h.overall_grade == "Needs Improvement"]
        takeaways.append(f"Focus areas: {', '.join(problem_domains)}")

    if invest_high > 1000000:
        takeaways.append("Significant investment required post-close")

    if len(critical_risks) > 0:
        takeaways.append("Critical risks should be addressed in Day 1 planning")

    takeaway_para = ""
    if takeaways:
        takeaway_para = " Key takeaways: " + "; ".join(takeaways) + "."

    return f"{overall_char}\n\n{cost_para}{takeaway_para}"


# =============================================================================
# HTML RENDERING
# =============================================================================

def render_executive_summary_html(
    summary_data: ExecutiveSummaryData
) -> str:
    """
    Render executive summary to HTML.

    Args:
        summary_data: Executive summary data

    Returns:
        Complete HTML document
    """
    # Format metrics
    budget_low, budget_high = summary_data.total_it_budget
    invest_low, invest_high = summary_data.total_investment_needed

    if budget_high > 0:
        budget_display = f"${budget_low:,.0f} - ${budget_high:,.0f}"
    else:
        budget_display = "Not documented"

    if invest_high > 0:
        invest_display = f"${invest_low:,.0f} - ${invest_high:,.0f}"
    else:
        invest_display = "TBD"

    headcount = summary_data.it_headcount if summary_data.it_headcount else "TBD"
    it_pct = f"{summary_data.it_pct_revenue:.1f}%" if summary_data.it_pct_revenue else "N/A"

    # Domain highlights
    domain_cards = ""
    for domain in DOMAIN_ORDER:
        if domain in summary_data.domain_highlights:
            h = summary_data.domain_highlights[domain]
            grade_class = h.overall_grade.lower().replace(" ", "-")
            domain_cards += f"""
            <div class="domain-card">
                <div class="card-header">
                    <span class="domain-name">{h.domain_display_name}</span>
                    <span class="grade-badge grade-{grade_class}">{h.overall_grade}</span>
                </div>
                <div class="key-finding">{h.key_finding}</div>
            </div>
            """

    # Critical risks
    risks_html = ""
    if summary_data.critical_risks:
        items = []
        for risk in summary_data.critical_risks:
            items.append(f"""
            <li class="risk-{risk.severity}">
                <strong>{risk.title}</strong>
                <span class="meta">{risk.domain.replace('_', ' ').title()} | {risk.severity.title()}</span>
                <p>{risk.implication}</p>
            </li>
            """)
        risks_html = f'<ul class="risks-list">{"".join(items)}</ul>'
    else:
        risks_html = "<p>No critical or high risks identified</p>"

    # Opportunities
    opps_html = ""
    if summary_data.key_opportunities:
        items = [f"<li>{opp}</li>" for opp in summary_data.key_opportunities]
        opps_html = f'<ul class="opps-list">{"".join(items)}</ul>'
    else:
        opps_html = "<p>No specific opportunities identified</p>"

    # Benchmark outliers
    outliers_html = ""
    if summary_data.benchmark_outliers:
        items = [f"<li>{outlier}</li>" for outlier in summary_data.benchmark_outliers]
        outliers_html = f"""
        <div class="section">
            <h2>Benchmark Outliers</h2>
            <ul class="outliers-list">{"".join(items)}</ul>
        </div>
        """

    # Major investments
    major_html = ""
    if summary_data.major_investments:
        items = [f"<li>{inv}</li>" for inv in summary_data.major_investments]
        major_html = f"""
        <div class="section">
            <h2>Major Investments (>$500K)</h2>
            <ul class="major-list">{"".join(items)}</ul>
        </div>
        """

    # Narrative with proper paragraph formatting
    narrative_html = ""
    if summary_data.overall_narrative:
        paragraphs = summary_data.overall_narrative.split("\n\n")
        narrative_html = "".join(f"<p>{p}</p>" for p in paragraphs if p.strip())

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{summary_data.target_name} - Executive Summary</title>
    <style>
        :root {{
            --primary: #2563eb;
            --success: #16a34a;
            --success-light: #dcfce7;
            --warning: #ca8a04;
            --warning-light: #fef3c7;
            --danger: #dc2626;
            --danger-light: #fecaca;
            --text: #1f2937;
            --text-muted: #6b7280;
            --bg-light: #f9fafb;
            --border: #e5e7eb;
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
            margin: 0 0 10px 0;
            color: var(--primary);
        }}

        .header .meta {{
            color: var(--text-muted);
            font-size: 14px;
        }}

        .metrics-row {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-bottom: 30px;
        }}

        .metric-card {{
            background: var(--bg-light);
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}

        .metric-card .value {{
            font-size: 24px;
            font-weight: 700;
            color: var(--primary);
            margin-bottom: 5px;
        }}

        .metric-card .label {{
            font-size: 12px;
            color: var(--text-muted);
            text-transform: uppercase;
        }}

        .narrative {{
            background: #eff6ff;
            border-left: 4px solid var(--primary);
            padding: 20px 25px;
            border-radius: 0 8px 8px 0;
            margin-bottom: 30px;
        }}

        .narrative p {{
            margin: 0 0 15px 0;
        }}

        .narrative p:last-child {{
            margin-bottom: 0;
        }}

        .section {{
            margin-bottom: 30px;
        }}

        .section h2 {{
            font-size: 18px;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .domain-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
        }}

        .domain-card {{
            background: var(--bg-light);
            padding: 15px;
            border-radius: 8px;
        }}

        .domain-card .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }}

        .domain-name {{
            font-weight: 600;
        }}

        .grade-badge {{
            font-size: 11px;
            padding: 3px 8px;
            border-radius: 10px;
            font-weight: 600;
        }}

        .grade-strong {{ background: var(--success-light); color: var(--success); }}
        .grade-adequate {{ background: var(--warning-light); color: var(--warning); }}
        .grade-needs-improvement {{ background: var(--danger-light); color: var(--danger); }}

        .key-finding {{
            font-size: 13px;
            color: var(--text-muted);
        }}

        .two-column {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 25px;
        }}

        .risks-list, .opps-list, .outliers-list, .major-list {{
            list-style: none;
            padding: 0;
            margin: 0;
        }}

        .risks-list li {{
            padding: 12px 15px;
            border-radius: 6px;
            margin-bottom: 10px;
            border-left: 3px solid var(--danger);
            background: #fef2f2;
        }}

        .risks-list li.risk-critical {{
            background: var(--danger-light);
        }}

        .risks-list li strong {{
            display: block;
            margin-bottom: 5px;
        }}

        .risks-list li .meta {{
            font-size: 11px;
            color: var(--text-muted);
            display: block;
            margin-bottom: 5px;
        }}

        .risks-list li p {{
            margin: 0;
            font-size: 13px;
        }}

        .opps-list li {{
            padding: 10px 15px;
            background: var(--success-light);
            border-left: 3px solid var(--success);
            border-radius: 6px;
            margin-bottom: 8px;
        }}

        .outliers-list li, .major-list li {{
            padding: 8px 0;
            border-bottom: 1px solid var(--border);
        }}

        @media (max-width: 800px) {{
            .metrics-row {{
                grid-template-columns: repeat(2, 1fr);
            }}

            .domain-grid {{
                grid-template-columns: 1fr;
            }}

            .two-column {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>IT Due Diligence Executive Summary</h1>
        <div class="meta">
            {summary_data.target_name} | Analysis Date: {summary_data.analysis_date} |
            {summary_data.domains_analyzed} Domains Analyzed
        </div>
    </div>

    <div class="metrics-row">
        <div class="metric-card">
            <div class="value">{budget_display}</div>
            <div class="label">Annual IT Budget</div>
        </div>
        <div class="metric-card">
            <div class="value">{invest_display}</div>
            <div class="label">Investment Needed</div>
        </div>
        <div class="metric-card">
            <div class="value">{headcount}</div>
            <div class="label">IT Headcount</div>
        </div>
        <div class="metric-card">
            <div class="value">{it_pct}</div>
            <div class="label">IT % of Revenue</div>
        </div>
    </div>

    <div class="narrative">
        {narrative_html}
    </div>

    <div class="section">
        <h2>Domain Assessment</h2>
        <div class="domain-grid">
            {domain_cards}
        </div>
    </div>

    <div class="two-column">
        <div class="section">
            <h2>Critical Risks</h2>
            {risks_html}
        </div>
        <div class="section">
            <h2>Key Opportunities</h2>
            {opps_html}
        </div>
    </div>

    {outliers_html}
    {major_html}
</body>
</html>"""

    return html


def save_executive_summary(
    summary_data: ExecutiveSummaryData,
    output_dir: Path
) -> Path:
    """
    Save executive summary to file.

    Args:
        summary_data: Executive summary data
        output_dir: Output directory

    Returns:
        Path to saved file
    """
    html = render_executive_summary_html(summary_data)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"executive_summary_{timestamp}.html"

    output_file.write_text(html)
    logger.info(f"Saved executive summary to {output_file}")

    return output_file
