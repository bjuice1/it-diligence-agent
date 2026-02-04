"""
PE Benchmarking Service

LLM-based benchmark assessment with sourced benchmark context.
Provides contextualized assessment combining:
1. Benchmark data (objective, sourced)
2. LLM interpretation (context-specific reasoning)
3. Full transparency (both shown to user)

Key Principle: Benchmark provides baseline, LLM provides context.
"""

import json
import logging
from typing import Dict, List, Optional, Any, TYPE_CHECKING

from tools_v2.pe_report_schemas import (
    BenchmarkAssessment,
    DealContext,
)
from tools_v2.benchmark_library import (
    get_benchmark,
    get_benchmark_context_string,
    assess_against_benchmark,
    BenchmarkData,
)

if TYPE_CHECKING:
    from stores.fact_store import FactStore
    from tools_v2.reasoning_tools import ReasoningStore

logger = logging.getLogger(__name__)


# =============================================================================
# ASSESSMENT PROMPTS
# =============================================================================

ORGANIZATION_ASSESSMENT_PROMPT = """Analyze this IT organization for a PE buyer.

Company Context:
- Company: {company_name}
- Industry: {industry}
- Size: {company_size} ({employee_count} employees, ${revenue}M revenue)

IT Organization Facts:
- Total IT headcount: {it_headcount}
- IT staff ratio: {it_staff_ratio} per 100 employees
- IT budget: ${it_budget:,.0f}
- IT % of revenue: {it_pct_revenue}%
- Outsourced percentage: {outsourced_pct}%

Benchmark Context:
{benchmark_context}

Additional Organization Facts:
{org_facts}

Assess (be specific and cite facts):
1. SIZE: Is the IT organization lean, bloated, or in-line for this company size/industry?
2. COST EFFICIENCY: Is IT spending appropriate vs benchmarks?
3. OUTSOURCING MIX: Is the outsourcing balance appropriate? Over/under-leveraged?
4. KEY GAPS: What capabilities or roles are notably missing?

Return valid JSON (no markdown):
{{
    "tech_age": "modern|mixed|outdated",
    "tech_age_rationale": "...",
    "cost_posture": "lean|in_line|bloated",
    "cost_posture_rationale": "...",
    "maturity": "mature|developing|immature",
    "maturity_rationale": "...",
    "implication": "Business consequence in 1-2 sentences - the 'so what'",
    "triggered_actions": ["Action 1", "Action 2"],
    "overall_grade": "Strong|Adequate|Needs Improvement",
    "key_callouts": ["Specific observation 1", "Specific observation 2", "Specific observation 3"],
    "confidence": "high|medium|low",
    "confidence_rationale": "Why this confidence level"
}}
"""

APPLICATIONS_ASSESSMENT_PROMPT = """Analyze this application portfolio for a PE buyer.

Company Context:
- Company: {company_name}
- Industry: {industry}
- Size: {company_size} ({employee_count} employees)

Application Portfolio:
- Total applications: {app_count}
- Apps per 100 employees: {app_ratio}
- Custom applications: {custom_app_count}

Key Systems:
{key_systems}

Benchmark Context:
{benchmark_context}

Additional Application Facts:
{app_facts}

Assess (be specific and cite facts):
1. ERP ASSESSMENT: Is the ERP modern and appropriate for company size?
2. TECH DEBT: Where is there significant technical debt?
3. MODERNIZATION: What is their modernization direction/roadmap?
4. DATA MANAGEMENT: How mature is data management (centralized, fragmented)?
5. APP RATIONALIZATION: Are there obvious consolidation opportunities?

Return valid JSON (no markdown):
{{
    "tech_age": "modern|mixed|outdated",
    "tech_age_rationale": "...",
    "cost_posture": "lean|in_line|bloated",
    "cost_posture_rationale": "...",
    "maturity": "mature|developing|immature",
    "maturity_rationale": "...",
    "implication": "Business consequence in 1-2 sentences",
    "triggered_actions": ["Action 1", "Action 2"],
    "overall_grade": "Strong|Adequate|Needs Improvement",
    "key_callouts": ["Specific observation 1", "Specific observation 2"],
    "confidence": "high|medium|low",
    "confidence_rationale": "Why this confidence level"
}}
"""

INFRASTRUCTURE_ASSESSMENT_PROMPT = """Analyze this IT infrastructure for a PE buyer.

Company Context:
- Company: {company_name}
- Industry: {industry}
- Size: {company_size}

Infrastructure Overview:
{infra_overview}

Cloud Adoption: {cloud_pct}% of workloads in cloud

Benchmark Context:
{benchmark_context}

Additional Infrastructure Facts:
{infra_facts}

Assess (be specific and cite facts):
1. HOSTING/COMPUTE: Is infrastructure modern and right-sized?
2. CLOUD READINESS: Where are they on cloud journey?
3. DR/BACKUP: Is disaster recovery adequate?
4. TECHNICAL DEBT: What infrastructure needs refresh?
5. MODERNIZATION PATH: What's the sensible next step?

Return valid JSON (no markdown):
{{
    "tech_age": "modern|mixed|outdated",
    "tech_age_rationale": "...",
    "cost_posture": "lean|in_line|bloated",
    "cost_posture_rationale": "...",
    "maturity": "mature|developing|immature",
    "maturity_rationale": "...",
    "implication": "Business consequence in 1-2 sentences",
    "triggered_actions": ["Action 1", "Action 2"],
    "overall_grade": "Strong|Adequate|Needs Improvement",
    "key_callouts": ["Specific observation 1", "Specific observation 2"],
    "confidence": "high|medium|low",
    "confidence_rationale": "Why this confidence level"
}}
"""

NETWORK_ASSESSMENT_PROMPT = """Analyze this network infrastructure for a PE buyer.

Company Context:
- Company: {company_name}
- Industry: {industry}
- Size: {company_size}
- Sites/Locations: {site_count}

Network Overview:
{network_overview}

Benchmark Context:
{benchmark_context}

Additional Network Facts:
{network_facts}

Assess (be specific and cite facts):
1. ARCHITECTURE: Is network architecture sound and scalable?
2. CONNECTIVITY: Are sites properly connected? Bandwidth adequate?
3. SECURITY: Is network security (firewall, segmentation) appropriate?
4. REMOTE ACCESS: Is remote work infrastructure adequate?
5. MODERNIZATION: What are the gaps vs modern standards?

Return valid JSON (no markdown):
{{
    "tech_age": "modern|mixed|outdated",
    "tech_age_rationale": "...",
    "cost_posture": "lean|in_line|bloated",
    "cost_posture_rationale": "...",
    "maturity": "mature|developing|immature",
    "maturity_rationale": "...",
    "implication": "Business consequence in 1-2 sentences",
    "triggered_actions": ["Action 1", "Action 2"],
    "overall_grade": "Strong|Adequate|Needs Improvement",
    "key_callouts": ["Specific observation 1", "Specific observation 2"],
    "confidence": "high|medium|low",
    "confidence_rationale": "Why this confidence level"
}}
"""

CYBERSECURITY_ASSESSMENT_PROMPT = """Analyze this cybersecurity posture for a PE buyer.

Company Context:
- Company: {company_name}
- Industry: {industry}
- Size: {company_size}

Security Overview:
{security_overview}

Security spending as % of IT: {security_pct}%

Benchmark Context:
{benchmark_context}

Additional Security Facts:
{security_facts}

Assess (be specific and cite facts):
1. CONTROLS INVENTORY: What security controls are in place?
2. MATURITY: How mature is the security program vs frameworks (NIST, ISO)?
3. GAP ANALYSIS: What critical controls are missing?
4. INCIDENT RESPONSE: Do they have IR capability?
5. COMPLIANCE: What compliance requirements apply and are they met?

Return valid JSON (no markdown):
{{
    "tech_age": "modern|mixed|outdated",
    "tech_age_rationale": "...",
    "cost_posture": "lean|in_line|bloated",
    "cost_posture_rationale": "...",
    "maturity": "mature|developing|immature",
    "maturity_rationale": "...",
    "implication": "Business consequence in 1-2 sentences",
    "triggered_actions": ["Action 1", "Action 2"],
    "overall_grade": "Strong|Adequate|Needs Improvement",
    "key_callouts": ["Specific observation 1", "Specific observation 2"],
    "confidence": "high|medium|low",
    "confidence_rationale": "Why this confidence level"
}}
"""

IDENTITY_ASSESSMENT_PROMPT = """Analyze this identity and access management for a PE buyer.

Company Context:
- Company: {company_name}
- Industry: {industry}
- Size: {company_size} ({employee_count} employees)

Identity Overview:
{identity_overview}

Benchmark Context:
{benchmark_context}

Additional Identity Facts:
{identity_facts}

Assess (be specific and cite facts):
1. IAM PLATFORM: Is the identity platform modern and capable?
2. MFA COVERAGE: How comprehensive is multi-factor authentication?
3. PAM: Is privileged access management in place?
4. ACCESS GOVERNANCE: How mature is access review/certification?
5. LIFECYCLE: How well is joiner/mover/leaver handled?

Return valid JSON (no markdown):
{{
    "tech_age": "modern|mixed|outdated",
    "tech_age_rationale": "...",
    "cost_posture": "lean|in_line|bloated",
    "cost_posture_rationale": "...",
    "maturity": "mature|developing|immature",
    "maturity_rationale": "...",
    "implication": "Business consequence in 1-2 sentences",
    "triggered_actions": ["Action 1", "Action 2"],
    "overall_grade": "Strong|Adequate|Needs Improvement",
    "key_callouts": ["Specific observation 1", "Specific observation 2"],
    "confidence": "high|medium|low",
    "confidence_rationale": "Why this confidence level"
}}
"""

DOMAIN_PROMPTS = {
    "organization": ORGANIZATION_ASSESSMENT_PROMPT,
    "applications": APPLICATIONS_ASSESSMENT_PROMPT,
    "infrastructure": INFRASTRUCTURE_ASSESSMENT_PROMPT,
    "network": NETWORK_ASSESSMENT_PROMPT,
    "cybersecurity": CYBERSECURITY_ASSESSMENT_PROMPT,
    "identity_access": IDENTITY_ASSESSMENT_PROMPT,
}


# =============================================================================
# BENCHMARK ASSESSMENT FUNCTIONS
# =============================================================================

def build_benchmark_context(
    domain: str,
    deal_context: Optional[DealContext],
    metrics: Dict[str, float]
) -> str:
    """
    Build benchmark context string for LLM prompt.

    Args:
        domain: Domain being assessed
        deal_context: Deal context with company info
        metrics: Actual metrics to compare (e.g., {"it_pct_revenue": 3.5})

    Returns:
        Formatted benchmark context string
    """
    if not deal_context:
        return "No company context available for benchmark comparison."

    industry = deal_context.target_industry or "general"
    size_tier = deal_context.company_size_tier

    context_parts = []

    for metric_name, actual_value in metrics.items():
        if actual_value is not None:
            context = get_benchmark_context_string(
                metric=metric_name,
                industry=industry,
                company_size=size_tier,
                actual_value=actual_value
            )
            context_parts.append(context)

    if not context_parts:
        return "No benchmark metrics available for comparison."

    return "\n".join(context_parts)


def extract_domain_metrics(
    domain: str,
    fact_store: "FactStore",
    deal_context: Optional[DealContext]
) -> Dict[str, Optional[float]]:
    """
    Extract relevant metrics from facts for benchmark comparison.

    Args:
        domain: Domain to extract metrics for
        fact_store: Fact store with discovered facts
        deal_context: Deal context

    Returns:
        Dict of metric name -> value (or None if not found)
    """
    metrics = {}

    # Get facts for this domain
    domain_facts = [f for f in fact_store.facts if f.domain == domain]

    if domain == "organization":
        # Extract IT budget and headcount metrics
        for fact in domain_facts:
            details = fact.details or {}

            if "total_it_budget" in details and deal_context and deal_context.target_revenue:
                budget = details["total_it_budget"]
                if isinstance(budget, (int, float)) and deal_context.target_revenue > 0:
                    metrics["it_pct_revenue"] = (budget / deal_context.target_revenue) * 100

            if "total_it_headcount" in details and deal_context and deal_context.target_employees:
                headcount = details["total_it_headcount"]
                if isinstance(headcount, (int, float)) and deal_context.target_employees > 0:
                    metrics["it_staff_ratio"] = (headcount / deal_context.target_employees) * 100

            if "outsourced_percentage" in details:
                metrics["outsourcing_pct"] = details["outsourced_percentage"]

    elif domain == "applications":
        app_facts = [f for f in domain_facts if f.category not in ("costs", "budget")]
        app_count = len(app_facts)
        if app_count > 0 and deal_context and deal_context.target_employees:
            metrics["app_count_ratio"] = (app_count / deal_context.target_employees) * 100

    elif domain == "infrastructure":
        for fact in domain_facts:
            details = fact.details or {}
            if "cloud_percentage" in details:
                metrics["cloud_adoption_pct"] = details["cloud_percentage"]
            if "cloud_adoption" in details:
                # Try to parse percentage from string
                cloud_str = str(details["cloud_adoption"])
                if "%" in cloud_str:
                    try:
                        metrics["cloud_adoption_pct"] = float(cloud_str.replace("%", "").strip())
                    except ValueError:
                        pass

    elif domain == "cybersecurity":
        for fact in domain_facts:
            details = fact.details or {}
            if "security_budget_pct" in details:
                metrics["security_pct_it"] = details["security_budget_pct"]

    return metrics


def format_facts_for_prompt(
    facts: List[Any],
    max_facts: int = 15
) -> str:
    """Format facts for inclusion in LLM prompt."""
    if not facts:
        return "No additional facts available."

    lines = []
    for i, fact in enumerate(facts[:max_facts]):
        item = fact.item
        details = fact.details or {}
        status = fact.status

        # Format key details
        detail_strs = []
        for key, value in details.items():
            if key not in ("evidence", "source") and value is not None:
                detail_strs.append(f"{key}: {value}")

        detail_str = "; ".join(detail_strs[:5])  # Limit details
        lines.append(f"- {item}: {detail_str} [{status}]")

    if len(facts) > max_facts:
        lines.append(f"... and {len(facts) - max_facts} more facts")

    return "\n".join(lines)


async def assess_domain_with_llm(
    domain: str,
    fact_store: "FactStore",
    deal_context: Optional[DealContext],
    llm_client: Any,
    model: str = "claude-sonnet-4-20250514"
) -> BenchmarkAssessment:
    """
    Generate benchmark assessment for a domain using LLM.

    Args:
        domain: Domain to assess
        fact_store: Fact store with discovered facts
        deal_context: Deal context with company info
        llm_client: Anthropic client for LLM calls
        model: Model to use for assessment

    Returns:
        BenchmarkAssessment with contextualized assessment
    """
    # Get domain facts
    domain_facts = [f for f in fact_store.facts if f.domain == domain]

    if not domain_facts:
        logger.warning(f"No facts found for domain {domain}")
        return BenchmarkAssessment(
            overall_grade="Unknown",
            key_callouts=["No data available for this domain"],
            confidence="low",
            confidence_rationale="No facts discovered for assessment"
        )

    # Extract metrics for benchmark comparison
    metrics = extract_domain_metrics(domain, fact_store, deal_context)

    # Build benchmark context
    benchmark_context = build_benchmark_context(domain, deal_context, metrics)

    # Get the appropriate prompt template
    prompt_template = DOMAIN_PROMPTS.get(domain)
    if not prompt_template:
        logger.warning(f"No prompt template for domain {domain}")
        return BenchmarkAssessment(
            overall_grade="Unknown",
            key_callouts=["Assessment not available for this domain"],
            confidence="low"
        )

    # Build prompt context
    company_name = deal_context.target_name if deal_context else "Target Company"
    industry = deal_context.target_industry if deal_context else "general"
    company_size = deal_context.company_size_tier if deal_context else "50-100M"
    employee_count = deal_context.target_employees if deal_context else 0
    revenue = (deal_context.target_revenue / 1_000_000) if deal_context and deal_context.target_revenue else 0

    # Format facts for prompt
    facts_str = format_facts_for_prompt(domain_facts)

    # Build domain-specific context
    prompt_vars = {
        "company_name": company_name,
        "industry": industry,
        "company_size": company_size,
        "employee_count": employee_count,
        "revenue": revenue,
        "benchmark_context": benchmark_context,
    }

    # Add domain-specific variables
    if domain == "organization":
        it_headcount = 0
        it_budget = 0
        outsourced_pct = 0
        for fact in domain_facts:
            details = fact.details or {}
            if "total_it_headcount" in details:
                it_headcount = details["total_it_headcount"]
            if "total_it_budget" in details:
                it_budget = details["total_it_budget"]
            if "outsourced_percentage" in details:
                outsourced_pct = details["outsourced_percentage"]

        it_staff_ratio = (it_headcount / employee_count * 100) if employee_count > 0 else 0
        it_pct_revenue = (it_budget / (revenue * 1_000_000) * 100) if revenue > 0 else 0

        prompt_vars.update({
            "it_headcount": it_headcount,
            "it_staff_ratio": f"{it_staff_ratio:.1f}",
            "it_budget": it_budget,
            "it_pct_revenue": f"{it_pct_revenue:.1f}",
            "outsourced_pct": outsourced_pct,
            "org_facts": facts_str,
        })

    elif domain == "applications":
        app_facts = [f for f in domain_facts if f.category not in ("costs", "budget")]
        app_count = len(app_facts)
        custom_count = len([f for f in app_facts if f.category == "custom"])
        app_ratio = (app_count / employee_count * 100) if employee_count > 0 else 0

        # Extract key systems
        key_systems = []
        for fact in domain_facts:
            if fact.category in ("erp", "crm", "hcm"):
                key_systems.append(f"- {fact.category.upper()}: {fact.item}")

        prompt_vars.update({
            "app_count": app_count,
            "app_ratio": f"{app_ratio:.1f}",
            "custom_app_count": custom_count,
            "key_systems": "\n".join(key_systems) if key_systems else "No key systems documented",
            "app_facts": facts_str,
        })

    elif domain == "infrastructure":
        cloud_pct = metrics.get("cloud_adoption_pct", "Unknown")

        # Build overview
        infra_categories = {}
        for fact in domain_facts:
            cat = fact.category
            if cat not in infra_categories:
                infra_categories[cat] = []
            infra_categories[cat].append(fact.item)

        overview_lines = []
        for cat, items in infra_categories.items():
            overview_lines.append(f"- {cat}: {', '.join(items[:3])}")

        prompt_vars.update({
            "infra_overview": "\n".join(overview_lines) if overview_lines else "No infrastructure documented",
            "cloud_pct": cloud_pct,
            "infra_facts": facts_str,
        })

    elif domain == "network":
        site_count = 0
        for fact in domain_facts:
            if "site_count" in (fact.details or {}):
                site_count = fact.details["site_count"]
            if "locations" in (fact.details or {}):
                site_count = fact.details["locations"]

        # Build overview
        network_items = [f.item for f in domain_facts[:5]]

        prompt_vars.update({
            "site_count": site_count or "Unknown",
            "network_overview": ", ".join(network_items) if network_items else "No network details documented",
            "network_facts": facts_str,
        })

    elif domain == "cybersecurity":
        security_pct = metrics.get("security_pct_it", "Unknown")

        # Build overview
        security_items = [f.item for f in domain_facts[:5]]

        prompt_vars.update({
            "security_overview": ", ".join(security_items) if security_items else "No security controls documented",
            "security_pct": security_pct,
            "security_facts": facts_str,
        })

    elif domain == "identity_access":
        # Build overview
        identity_items = [f.item for f in domain_facts[:5]]

        prompt_vars.update({
            "identity_overview": ", ".join(identity_items) if identity_items else "No identity systems documented",
            "identity_facts": facts_str,
        })

    # Format prompt
    try:
        prompt = prompt_template.format(**prompt_vars)
    except KeyError as e:
        logger.error(f"Missing prompt variable for {domain}: {e}")
        return BenchmarkAssessment(
            overall_grade="Unknown",
            key_callouts=["Assessment failed due to missing data"],
            confidence="low"
        )

    # Call LLM
    try:
        response = await llm_client.messages.create(
            model=model,
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = response.content[0].text.strip()

        # Parse JSON response
        # Handle potential markdown code blocks
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()

        result = json.loads(response_text)

        # Build BenchmarkAssessment from result
        assessment = BenchmarkAssessment(
            tech_age=result.get("tech_age", "mixed"),
            tech_age_rationale=result.get("tech_age_rationale", ""),
            tech_age_benchmark_source=benchmark_context.split("\n")[0] if benchmark_context else "",
            cost_posture=result.get("cost_posture", "in_line"),
            cost_posture_rationale=result.get("cost_posture_rationale", ""),
            cost_benchmark_source=benchmark_context,
            maturity=result.get("maturity", "developing"),
            maturity_rationale=result.get("maturity_rationale", ""),
            implication=result.get("implication", ""),
            triggered_actions=result.get("triggered_actions", []),
            overall_grade=result.get("overall_grade", "Adequate"),
            key_callouts=result.get("key_callouts", []),
            confidence=result.get("confidence", "medium"),
            confidence_rationale=result.get("confidence_rationale", ""),
        )

        return assessment

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON for {domain}: {e}")
        return BenchmarkAssessment(
            overall_grade="Unknown",
            key_callouts=["Assessment response was not valid JSON"],
            confidence="low"
        )
    except Exception as e:
        logger.error(f"LLM call failed for {domain} assessment: {e}")
        return BenchmarkAssessment(
            overall_grade="Unknown",
            key_callouts=[f"Assessment failed: {str(e)}"],
            confidence="low"
        )


def assess_domain_without_llm(
    domain: str,
    fact_store: "FactStore",
    deal_context: Optional[DealContext]
) -> BenchmarkAssessment:
    """
    Generate a basic benchmark assessment without LLM.

    Uses benchmark data directly for rule-based assessment.
    Useful for quick assessments or when LLM is not available.

    Args:
        domain: Domain to assess
        fact_store: Fact store with discovered facts
        deal_context: Deal context with company info

    Returns:
        BenchmarkAssessment with basic assessment
    """
    # Extract metrics
    metrics = extract_domain_metrics(domain, fact_store, deal_context)

    industry = deal_context.target_industry if deal_context else "general"
    size_tier = deal_context.company_size_tier if deal_context else "50-100M"

    # Default assessment
    assessment = BenchmarkAssessment(
        tech_age="mixed",
        cost_posture="in_line",
        maturity="developing",
        overall_grade="Adequate",
        confidence="low",
        confidence_rationale="Rule-based assessment without LLM analysis"
    )

    callouts = []

    # Assess based on available metrics
    if "it_pct_revenue" in metrics:
        result = assess_against_benchmark("it_pct_revenue", industry, size_tier, metrics["it_pct_revenue"])
        if result["found"]:
            if result["assessment"] == "below_typical":
                assessment.cost_posture = "lean"
                assessment.cost_posture_rationale = f"IT spending at {metrics['it_pct_revenue']:.1f}% is below typical range"
                callouts.append(f"IT spending below typical at {metrics['it_pct_revenue']:.1f}% of revenue")
            elif result["assessment"] == "above_typical":
                assessment.cost_posture = "bloated"
                assessment.cost_posture_rationale = f"IT spending at {metrics['it_pct_revenue']:.1f}% is above typical range"
                callouts.append(f"IT spending above typical at {metrics['it_pct_revenue']:.1f}% of revenue")
            assessment.cost_benchmark_source = result["context"]

    if "it_staff_ratio" in metrics:
        result = assess_against_benchmark("it_staff_ratio", industry, size_tier, metrics["it_staff_ratio"])
        if result["found"]:
            if result["assessment"] == "below_typical":
                callouts.append("IT staffing level is lean")
            elif result["assessment"] == "above_typical":
                callouts.append("IT staffing level is heavy")

    if "outsourcing_pct" in metrics:
        result = assess_against_benchmark("outsourcing_pct", industry, size_tier, metrics["outsourcing_pct"])
        if result["found"]:
            if result["assessment"] == "above_typical":
                callouts.append(f"High outsourcing at {metrics['outsourcing_pct']}%")

    # Get domain facts for additional context
    domain_facts = [f for f in fact_store.facts if f.domain == domain]

    # Set confidence based on data availability
    if len(domain_facts) >= 10 and len(metrics) >= 2:
        assessment.confidence = "medium"
        assessment.confidence_rationale = f"Based on {len(domain_facts)} facts and {len(metrics)} metrics"
    elif len(domain_facts) >= 5:
        assessment.confidence = "low"
        assessment.confidence_rationale = f"Limited data: {len(domain_facts)} facts"
    else:
        assessment.confidence = "low"
        assessment.confidence_rationale = "Insufficient data for assessment"

    if not callouts:
        callouts.append("Limited data available for detailed assessment")

    assessment.key_callouts = callouts[:4]

    return assessment
