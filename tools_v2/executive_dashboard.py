"""
Executive Dashboard Generator

Generates the single-page PE executive dashboard that serves as the landing page.
Partner gets the story in 30 seconds, clicks through for details.

Dashboard Components:
- Overall IT assessment (1-2 sentences)
- Key metrics cards (IT budget, headcount, investment needed)
- Domain highlights grid (6 cards with grade + key finding + "Deep dive →")
- Costs summary (run-rate)
- Investment summary (one-time with TSA/separation breakdown)
- Top 3 risks to consider
- Top 3 opportunities
"""

import logging
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from datetime import datetime

from tools_v2.pe_report_schemas import (
    ExecutiveDashboardData,
    DomainHighlight,
    DomainReportData,
    DealContext,
    RiskSummary,
    DOMAIN_ORDER,
    DOMAIN_DISPLAY_NAMES,
)
from tools_v2.pe_costs import (
    extract_run_rate_costs,
    extract_it_budget_summary,
    aggregate_work_item_costs,
    build_costs_report_data,
    build_investment_report_data,
)
from tools_v2.pe_narrative import generate_domain_highlight

if TYPE_CHECKING:
    from stores.fact_store import FactStore
    from tools_v2.reasoning_tools import ReasoningStore

logger = logging.getLogger(__name__)


# =============================================================================
# DASHBOARD DATA GENERATION
# =============================================================================

def generate_dashboard_data(
    fact_store: "FactStore",
    reasoning_store: "ReasoningStore",
    deal_context: Optional[DealContext] = None,
    domain_reports: Optional[Dict[str, DomainReportData]] = None,
    target_name: str = "Target Company"
) -> ExecutiveDashboardData:
    """
    Generate executive dashboard data from analysis results.

    Args:
        fact_store: Fact store with discovered facts
        reasoning_store: Reasoning store with findings
        deal_context: Optional deal context
        domain_reports: Optional pre-generated domain reports
        target_name: Name of target company

    Returns:
        ExecutiveDashboardData for rendering
    """
    # Extract budget summary
    budget_summary = extract_it_budget_summary(fact_store, deal_context)

    # Get costs data
    costs_data = build_costs_report_data(fact_store, deal_context)
    investment_data = build_investment_report_data(reasoning_store)

    # Build domain highlights
    domain_highlights = {}
    for domain in DOMAIN_ORDER:
        if domain_reports and domain in domain_reports:
            # Use pre-generated domain report
            domain_data = domain_reports[domain]
            highlight = generate_domain_highlight(domain, domain_data)
        else:
            # Generate minimal highlight from available data
            highlight = _generate_minimal_highlight(domain, fact_store, reasoning_store)

        domain_highlights[domain] = highlight

    # Get top risks
    top_risks = _extract_top_risks(reasoning_store, max_risks=3)

    # Get top opportunities
    top_opportunities = _extract_top_opportunities(reasoning_store, max_opportunities=3)

    # Calculate TSA/separation breakdown
    tsa_costs, separation_costs, integration_costs = _calculate_cost_breakdown(reasoning_store)

    # Generate overall assessment
    overall_assessment = _generate_overall_assessment(
        domain_highlights,
        costs_data,
        investment_data,
        len(reasoning_store.risks),
        len(reasoning_store.work_items)
    )

    # Determine overall grade
    overall_grade = _determine_overall_grade(domain_highlights)

    return ExecutiveDashboardData(
        target_name=target_name,
        analysis_date=datetime.now().strftime("%Y-%m-%d"),
        deal_context=deal_context,
        overall_assessment=overall_assessment,
        overall_grade=overall_grade,
        total_it_budget=costs_data.total_run_rate,
        total_investment_needed=investment_data.total_one_time,
        it_headcount=budget_summary.get("it_headcount") or 0,
        it_pct_revenue=budget_summary.get("it_pct_revenue"),
        domain_highlights=domain_highlights,
        investment_by_phase=investment_data.by_phase,
        tsa_costs=tsa_costs,
        separation_costs=separation_costs,
        integration_costs=integration_costs,
        top_risks=top_risks,
        top_opportunities=top_opportunities,
        total_work_items=len(reasoning_store.work_items),
        total_risks=len(reasoning_store.risks),
        total_facts=len(fact_store.facts),
        total_gaps=len(fact_store.gaps),
    )


def _generate_minimal_highlight(
    domain: str,
    fact_store: "FactStore",
    reasoning_store: "ReasoningStore"
) -> DomainHighlight:
    """Generate a minimal domain highlight without full domain report."""
    display_name = DOMAIN_DISPLAY_NAMES.get(domain, domain.replace("_", " ").title())

    # Count facts and risks for this domain
    domain_facts = [f for f in fact_store.facts if f.domain == domain]
    domain_risks = [r for r in reasoning_store.risks if r.domain == domain]
    domain_work_items = [wi for wi in reasoning_store.work_items if wi.domain == domain]

    fact_count = len(domain_facts)
    risk_count = len(domain_risks)
    work_item_count = len(domain_work_items)

    # Determine grade based on risk severity
    critical_count = len([r for r in domain_risks if r.severity == "critical"])
    high_count = len([r for r in domain_risks if r.severity == "high"])

    if critical_count > 0:
        grade = "Needs Improvement"
    elif high_count >= 2:
        grade = "Needs Improvement"
    elif high_count > 0 or risk_count >= 3:
        grade = "Adequate"
    elif fact_count >= 5:
        grade = "Adequate"
    else:
        grade = "Adequate"  # Default

    # Generate key finding
    if critical_count > 0:
        critical_risk = next((r for r in domain_risks if r.severity == "critical"), None)
        key_finding = f"Critical: {critical_risk.title}" if critical_risk else "Critical issues identified"
    elif high_count > 0:
        key_finding = f"{risk_count} risks to address, {work_item_count} work items planned"
    elif fact_count == 0:
        key_finding = "Limited data available for assessment"
    else:
        key_finding = f"Baseline established with {fact_count} facts"

    # Get watch items from risks
    watch_items = [r.title for r in domain_risks[:3] if r.severity in ("critical", "high")]

    # Calculate costs
    from tools_v2.pe_costs import get_domain_costs
    run_rate, investment = get_domain_costs(fact_store, reasoning_store, domain)

    return DomainHighlight(
        domain=domain,
        domain_display_name=display_name,
        overall_grade=grade,
        key_finding=key_finding,
        watch_items=watch_items,
        run_rate_cost=run_rate,
        investment_needed=investment,
        work_item_count=work_item_count,
        risk_count=risk_count,
    )


def _extract_top_risks(
    reasoning_store: "ReasoningStore",
    max_risks: int = 3
) -> List[Dict[str, str]]:
    """Extract top risks for dashboard display."""
    # Sort by severity
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}

    sorted_risks = sorted(
        reasoning_store.risks,
        key=lambda r: (severity_order.get(r.severity, 4), r.domain)
    )

    top_risks = []
    for risk in sorted_risks[:max_risks]:
        top_risks.append({
            "title": risk.title,
            "severity": risk.severity,
            "domain": risk.domain,
            "implication": risk.mna_implication or risk.description[:100] + "...",
        })

    return top_risks


def _extract_top_opportunities(
    reasoning_store: "ReasoningStore",
    max_opportunities: int = 3
) -> List[str]:
    """Extract top opportunities/value creation areas."""
    opportunities = []

    # Get synergy opportunities from strategic considerations
    synergy_considerations = [
        sc for sc in reasoning_store.strategic_considerations
        if sc.lens in ("synergy", "value_creation", "synergy_opportunity")
    ]

    for sc in synergy_considerations[:max_opportunities]:
        opportunities.append(sc.implication or sc.title)

    # If not enough, look for positive aspects
    if len(opportunities) < max_opportunities:
        # Look for low-risk domains or positive findings
        for sc in reasoning_store.strategic_considerations:
            if len(opportunities) >= max_opportunities:
                break
            if "opportunity" in sc.title.lower() or "strength" in sc.title.lower():
                if sc.implication and sc.implication not in opportunities:
                    opportunities.append(sc.implication)

    return opportunities[:max_opportunities]


def _calculate_cost_breakdown(
    reasoning_store: "ReasoningStore"
) -> tuple:
    """Calculate TSA/separation/integration cost breakdown."""
    tsa_low, tsa_high = 0, 0
    separation_low, separation_high = 0, 0
    integration_low, integration_high = 0, 0

    from tools_v2.cost_calculator import COST_RANGE_VALUES

    for wi in reasoning_store.work_items:
        cost_estimate = getattr(wi, "cost_estimate", None)
        if not cost_estimate or cost_estimate not in COST_RANGE_VALUES:
            continue

        cost_range = COST_RANGE_VALUES[cost_estimate]
        low = cost_range["low"]
        high = cost_range["high"]

        # Classify by type (if available) or infer from title/description
        wi_type = getattr(wi, "type", None)

        if not wi_type:
            # Infer from title/description
            title_lower = wi.title.lower()
            desc_lower = (wi.description or "").lower()

            if "tsa" in title_lower or "tsa" in desc_lower or "transition" in title_lower:
                wi_type = "tsa"
            elif "separat" in title_lower or "standalone" in title_lower:
                wi_type = "separation"
            elif "integrat" in title_lower or "consolid" in title_lower or "harmoni" in title_lower:
                wi_type = "integration"
            else:
                wi_type = "run"

        # Add to appropriate bucket
        if wi_type == "tsa":
            tsa_low += low
            tsa_high += high
        elif wi_type == "separation":
            separation_low += low
            separation_high += high
        elif wi_type == "integration":
            integration_low += low
            integration_high += high

    return (
        (tsa_low, tsa_high),
        (separation_low, separation_high),
        (integration_low, integration_high)
    )


def _generate_overall_assessment(
    domain_highlights: Dict[str, DomainHighlight],
    costs_data: Any,
    investment_data: Any,
    risk_count: int,
    work_item_count: int
) -> str:
    """Generate 1-2 sentence overall IT assessment."""
    # Count grades
    grade_counts = {"Strong": 0, "Adequate": 0, "Needs Improvement": 0}
    for highlight in domain_highlights.values():
        grade = highlight.overall_grade
        if grade in grade_counts:
            grade_counts[grade] += 1

    # Determine overall characterization
    if grade_counts["Needs Improvement"] >= 3:
        overall_char = "requires significant attention"
    elif grade_counts["Needs Improvement"] >= 1:
        overall_char = "has areas requiring attention"
    elif grade_counts["Strong"] >= 4:
        overall_char = "is well-positioned"
    else:
        overall_char = "is adequate for current operations"

    # Format cost info
    run_rate_low, run_rate_high = costs_data.total_run_rate
    investment_low, investment_high = investment_data.total_one_time

    if run_rate_high > 0:
        cost_phrase = f"Current IT run-rate is ${run_rate_low:,.0f}-${run_rate_high:,.0f}"
    else:
        cost_phrase = "IT costs not fully documented"

    if investment_high > 0:
        investment_phrase = f"with ${investment_low:,.0f}-${investment_high:,.0f} in planned investments"
    else:
        investment_phrase = ""

    # Build assessment
    assessment = f"The IT estate {overall_char}. "
    assessment += f"{cost_phrase}"
    if investment_phrase:
        assessment += f" {investment_phrase}"
    assessment += f" across {work_item_count} work items."

    return assessment


def _determine_overall_grade(
    domain_highlights: Dict[str, DomainHighlight]
) -> str:
    """Determine overall grade from domain grades."""
    grade_scores = {"Strong": 3, "Adequate": 2, "Needs Improvement": 1}

    total_score = sum(
        grade_scores.get(h.overall_grade, 2)
        for h in domain_highlights.values()
    )

    avg_score = total_score / len(domain_highlights) if domain_highlights else 2

    if avg_score >= 2.5:
        return "Strong"
    elif avg_score >= 1.5:
        return "Adequate"
    else:
        return "Needs Improvement"


# =============================================================================
# LLM-ENHANCED ASSESSMENT (OPTIONAL)
# =============================================================================

async def generate_dashboard_data_with_llm(
    fact_store: "FactStore",
    reasoning_store: "ReasoningStore",
    llm_client: Any,
    deal_context: Optional[DealContext] = None,
    domain_reports: Optional[Dict[str, DomainReportData]] = None,
    target_name: str = "Target Company",
    model: str = "claude-sonnet-4-20250514"
) -> ExecutiveDashboardData:
    """
    Generate executive dashboard with LLM-enhanced assessment.

    Uses LLM to generate:
    - Overall assessment narrative
    - Top opportunities synthesis

    Args:
        fact_store: Fact store
        reasoning_store: Reasoning store
        llm_client: Anthropic client
        deal_context: Deal context
        domain_reports: Pre-generated domain reports
        target_name: Target company name
        model: Model to use

    Returns:
        ExecutiveDashboardData with enhanced narratives
    """
    # Start with base dashboard data
    dashboard = generate_dashboard_data(
        fact_store=fact_store,
        reasoning_store=reasoning_store,
        deal_context=deal_context,
        domain_reports=domain_reports,
        target_name=target_name
    )

    # Build context for LLM
    domain_summaries = []
    for domain, highlight in dashboard.domain_highlights.items():
        domain_summaries.append(
            f"- {highlight.domain_display_name}: {highlight.overall_grade} - {highlight.key_finding}"
        )

    risk_summaries = [f"- {r['title']} ({r['severity']})" for r in dashboard.top_risks]

    prompt = f"""Generate a concise executive summary for a PE buyer reviewing this IT due diligence.

Target: {target_name}

Domain Assessments:
{chr(10).join(domain_summaries)}

Key Risks:
{chr(10).join(risk_summaries) if risk_summaries else 'No critical risks identified'}

IT Budget: ${dashboard.total_it_budget[0]:,.0f} - ${dashboard.total_it_budget[1]:,.0f} (annual)
Investment Needed: ${dashboard.total_investment_needed[0]:,.0f} - ${dashboard.total_investment_needed[1]:,.0f}
Work Items: {dashboard.total_work_items}

Write a 2-3 sentence overall assessment that:
1. Characterizes the IT estate (solid/adequate/needs attention)
2. Highlights the most significant finding
3. Frames the investment required

Tone: Candid, partner-level, focused on what matters for the deal.
"""

    try:
        response = await llm_client.messages.create(
            model=model,
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )

        dashboard.overall_assessment = response.content[0].text.strip()

    except Exception as e:
        logger.warning(f"LLM enhancement failed, using rule-based assessment: {e}")

    return dashboard
