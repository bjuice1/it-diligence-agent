"""
PE Narrative Service

Generates PE decision-framing narratives:
- Top 3 implications ("So what?")
- Top 3 actions (with cost/timing/owner)
- Domain summaries

Key Principle: Every finding needs a "so what" for PE buyers.
"""

import logging
from typing import Dict, List, Optional, Any, TYPE_CHECKING

from tools_v2.pe_report_schemas import (
    ActionItem,
    ResourceNeed,
    DomainReportData,
    DomainHighlight,
    BenchmarkAssessment,
    DOMAIN_DISPLAY_NAMES,
)
from tools_v2.cost_calculator import COST_RANGE_VALUES

if TYPE_CHECKING:
    from stores.fact_store import FactStore
    from tools_v2.reasoning_tools import ReasoningStore, WorkItem, Risk, StrategicConsideration

logger = logging.getLogger(__name__)


# =============================================================================
# TOP 3 IMPLICATIONS
# =============================================================================

def generate_top_implications(
    domain: str,
    reasoning_store: "ReasoningStore",
    benchmark_assessment: Optional[BenchmarkAssessment] = None,
    max_implications: int = 3
) -> List[str]:
    """
    Generate top business implications for a domain.

    Sources:
    1. Benchmark assessment implication (if available)
    2. Risk M&A implications
    3. Strategic consideration implications

    Args:
        domain: Domain to generate implications for
        reasoning_store: Reasoning store with findings
        benchmark_assessment: Optional benchmark assessment
        max_implications: Maximum implications to return

    Returns:
        List of implication strings (top 3)
    """
    implications = []

    # 1. Start with benchmark implication if available
    if benchmark_assessment and benchmark_assessment.implication:
        implications.append(benchmark_assessment.implication)

    # 2. Get implications from critical/high risks
    domain_risks = [r for r in reasoning_store.risks if r.domain == domain]
    critical_risks = sorted(
        [r for r in domain_risks if r.severity in ("critical", "high")],
        key=lambda r: (0 if r.severity == "critical" else 1)
    )

    for risk in critical_risks:
        if len(implications) >= max_implications:
            break

        # Use mna_implication if available, otherwise construct from description
        if risk.mna_implication:
            imp = risk.mna_implication
        else:
            imp = f"Risk: {risk.title} - {risk.description[:100]}..."

        # Avoid duplicates
        if imp not in implications:
            implications.append(imp)

    # 3. Get implications from strategic considerations
    domain_considerations = [sc for sc in reasoning_store.strategic_considerations
                            if sc.domain == domain]

    for sc in domain_considerations:
        if len(implications) >= max_implications:
            break

        # Use implication field
        if sc.implication and sc.implication not in implications:
            implications.append(sc.implication)

    # 4. If still not enough, add callouts from benchmark
    if len(implications) < max_implications and benchmark_assessment:
        for callout in benchmark_assessment.key_callouts:
            if len(implications) >= max_implications:
                break
            if callout not in implications:
                implications.append(callout)

    return implications[:max_implications]


# =============================================================================
# TOP 3 ACTIONS
# =============================================================================

def generate_top_actions(
    domain: str,
    reasoning_store: "ReasoningStore",
    max_actions: int = 3
) -> List[ActionItem]:
    """
    Generate top action items for a domain.

    Prioritizes:
    1. Critical priority work items
    2. Day_1 phase work items
    3. High priority work items
    4. Work items triggered by critical risks

    Args:
        domain: Domain to generate actions for
        reasoning_store: Reasoning store with work items
        max_actions: Maximum actions to return

    Returns:
        List of ActionItem instances (top 3)
    """
    # Get domain work items
    domain_work_items = [wi for wi in reasoning_store.work_items if wi.domain == domain]

    if not domain_work_items:
        return []

    # Score and sort work items
    scored_items = []
    for wi in domain_work_items:
        score = _score_work_item(wi, reasoning_store)
        scored_items.append((score, wi))

    scored_items.sort(key=lambda x: x[0], reverse=True)

    # Convert top items to ActionItems
    actions = []
    for score, wi in scored_items[:max_actions]:
        action = _work_item_to_action(wi)
        actions.append(action)

    return actions


def _score_work_item(
    work_item: "WorkItem",
    reasoning_store: "ReasoningStore"
) -> float:
    """Score a work item for prioritization."""
    score = 0.0

    # Priority scoring
    priority_scores = {"critical": 100, "high": 50, "medium": 20, "low": 5}
    score += priority_scores.get(work_item.priority, 10)

    # Phase scoring (Day_1 is most urgent)
    phase_scores = {"Day_1": 50, "Day_100": 30, "Post_100": 10}
    score += phase_scores.get(work_item.phase, 15)

    # Boost if triggered by critical risks
    triggered_by = getattr(work_item, "triggered_by_risks", [])
    for risk_id in triggered_by:
        risk = next((r for r in reasoning_store.risks if r.finding_id == risk_id), None)
        if risk and risk.severity == "critical":
            score += 30
        elif risk and risk.severity == "high":
            score += 15

    # Boost for higher cost items (they're often more significant)
    cost_boost = {
        "over_1m": 20,
        "500k_to_1m": 15,
        "100k_to_500k": 10,
        "25k_to_100k": 5,
        "under_25k": 0,
    }
    score += cost_boost.get(work_item.cost_estimate, 0)

    return score


def _work_item_to_action(work_item: "WorkItem") -> ActionItem:
    """Convert a WorkItem to an ActionItem."""
    # Get cost range
    cost_estimate = work_item.cost_estimate or "25k_to_100k"
    cost_values = COST_RANGE_VALUES.get(cost_estimate, {"low": 25000, "high": 100000})

    # Generate "so what" from M&A implication or description
    so_what = work_item.mna_implication
    if not so_what:
        # Construct from target_action or description
        so_what = work_item.target_action or work_item.description
        if len(so_what) > 150:
            so_what = so_what[:147] + "..."

    return ActionItem(
        title=work_item.title,
        so_what=so_what,
        cost_range=(cost_values["low"], cost_values["high"]),
        timing=work_item.phase,
        owner_type=work_item.owner_type,
        priority=work_item.priority,
        domain=work_item.domain,
        work_item_id=work_item.finding_id,
    )


# =============================================================================
# RESOURCE NEEDS
# =============================================================================

def identify_resource_needs(
    domain: str,
    fact_store: "FactStore",
    reasoning_store: "ReasoningStore"
) -> List[ResourceNeed]:
    """
    Identify resource needs for a domain.

    Sources:
    1. Gap analysis from facts (missing roles)
    2. Work items requiring specific skills
    3. Explicit resource needs in findings

    Args:
        domain: Domain to analyze
        fact_store: Fact store with discovered facts
        reasoning_store: Reasoning store with findings

    Returns:
        List of ResourceNeed instances
    """
    needs = []
    seen_roles = set()

    # 1. Look for role gaps in organization facts
    if domain == "organization":
        org_facts = [f for f in fact_store.facts if f.domain == "organization"]
        for fact in org_facts:
            details = fact.details or {}

            # Check for missing roles
            if "missing_roles" in details:
                for role in details["missing_roles"]:
                    if role not in seen_roles:
                        needs.append(ResourceNeed(
                            role=role,
                            type="hire",
                            timing="Day_100",
                            rationale="Role gap identified in organization assessment"
                        ))
                        seen_roles.add(role)

    # 2. Look for skills required in work items
    domain_work_items = [wi for wi in reasoning_store.work_items if wi.domain == domain]

    for wi in domain_work_items:
        skills = getattr(wi, "skills_required", [])
        for skill in skills:
            # Map skill to potential role
            role = _skill_to_role(skill)
            if role and role not in seen_roles:
                needs.append(ResourceNeed(
                    role=role,
                    type="contract",  # Default to contract for work item skills
                    timing=wi.phase,
                    duration="project",
                    rationale=f"Required for: {wi.title}"
                ))
                seen_roles.add(role)

    # 3. Check for security-specific needs in cybersecurity domain
    if domain == "cybersecurity":
        # Check for security role gaps
        security_risks = [r for r in reasoning_store.risks
                        if r.domain == "cybersecurity" and r.severity in ("critical", "high")]

        has_security_role = any(
            "security" in (f.item or "").lower()
            for f in fact_store.facts
            if f.domain == "organization" and f.category in ("leadership", "team", "staffing")
        )

        if security_risks and not has_security_role and "Security Architect" not in seen_roles:
            needs.append(ResourceNeed(
                role="Security Architect",
                type="hire",
                timing="Day_100",
                rationale="No dedicated security role identified; critical risks present"
            ))
            seen_roles.add("Security Architect")

    return needs[:5]  # Limit to top 5


def _skill_to_role(skill: str) -> Optional[str]:
    """Map a skill name to a potential role."""
    skill_lower = skill.lower()

    skill_role_map = {
        "cloud": "Cloud Engineer",
        "aws": "AWS Engineer",
        "azure": "Azure Engineer",
        "security": "Security Engineer",
        "network": "Network Engineer",
        "sap": "SAP Consultant",
        "oracle": "Oracle Consultant",
        "erp": "ERP Consultant",
        "identity": "Identity & Access Specialist",
        "database": "Database Administrator",
        "devops": "DevOps Engineer",
        "infrastructure": "Infrastructure Engineer",
    }

    for keyword, role in skill_role_map.items():
        if keyword in skill_lower:
            return role

    return None


# =============================================================================
# DOMAIN SUMMARY GENERATION
# =============================================================================

def generate_domain_highlight(
    domain: str,
    domain_data: DomainReportData
) -> DomainHighlight:
    """
    Generate a DomainHighlight from DomainReportData.

    Used for the executive dashboard domain cards.

    Args:
        domain: Domain name
        domain_data: Full domain report data

    Returns:
        DomainHighlight for dashboard display
    """
    # Get display name
    display_name = DOMAIN_DISPLAY_NAMES.get(domain, domain.replace("_", " ").title())

    # Extract key finding from benchmark assessment
    assessment = domain_data.benchmark_assessment
    key_finding = assessment.implication

    if not key_finding:
        # Construct from grade and top implication
        if domain_data.top_implications:
            key_finding = domain_data.top_implications[0]
        else:
            key_finding = f"{assessment.overall_grade} - Limited data available"

    # Get watch items from callouts and implications
    watch_items = []
    if assessment.key_callouts:
        watch_items.extend(assessment.key_callouts[:2])
    if domain_data.top_implications:
        for imp in domain_data.top_implications:
            if imp not in watch_items and len(watch_items) < 3:
                watch_items.append(imp)

    return DomainHighlight(
        domain=domain,
        domain_display_name=display_name,
        overall_grade=assessment.overall_grade,
        key_finding=key_finding,
        watch_items=watch_items[:3],
        run_rate_cost=domain_data.run_rate_cost,
        investment_needed=domain_data.total_investment,
        work_item_count=domain_data.work_item_count,
        risk_count=domain_data.risk_count,
    )


def generate_key_finding_sentence(
    domain: str,
    assessment: BenchmarkAssessment,
    risk_count: int,
    work_item_count: int
) -> str:
    """
    Generate a one-sentence key finding for a domain.

    Args:
        domain: Domain name
        assessment: Benchmark assessment
        risk_count: Number of risks in domain
        work_item_count: Number of work items in domain

    Returns:
        One-sentence summary
    """
    grade = assessment.overall_grade
    tech_age = assessment.tech_age
    cost_posture = assessment.cost_posture

    # Build sentence based on grade
    if grade == "Strong":
        base = f"Solid {DOMAIN_DISPLAY_NAMES.get(domain, domain)} posture"
        if tech_age == "modern":
            base += " with modern technology stack"
    elif grade == "Needs Improvement":
        base = f"{DOMAIN_DISPLAY_NAMES.get(domain, domain)} requires attention"
        if tech_age == "outdated":
            base += " due to aging technology"
        elif cost_posture == "bloated":
            base += " with spending above benchmarks"
    else:
        base = f"{DOMAIN_DISPLAY_NAMES.get(domain, domain)} is adequate"

    # Add risk context
    if risk_count > 3:
        base += f"; {risk_count} items to address"
    elif work_item_count > 5:
        base += f"; {work_item_count} work items planned"

    return base + "."


# =============================================================================
# INTEGRATION CONSIDERATIONS
# =============================================================================

def extract_integration_considerations(
    domain: str,
    reasoning_store: "ReasoningStore",
    max_items: int = 3
) -> List[str]:
    """
    Extract integration considerations for a domain.

    Pulls from OverlapCandidates and integration-related findings.

    Args:
        domain: Domain to analyze
        reasoning_store: Reasoning store with findings
        max_items: Maximum considerations to return

    Returns:
        List of integration consideration strings
    """
    considerations = []

    # 1. Get overlap candidates for this domain
    overlaps = [oc for oc in reasoning_store.overlap_candidates if oc.domain == domain]

    for overlap in overlaps:
        consideration = f"{overlap.overlap_type.replace('_', ' ').title()}: {overlap.why_it_matters}"
        if consideration not in considerations:
            considerations.append(consideration)

    # 2. Get integration-related risks
    domain_risks = [r for r in reasoning_store.risks
                   if r.domain == domain and r.integration_related]

    for risk in domain_risks:
        if len(considerations) >= max_items:
            break
        consideration = f"{risk.title}: {risk.mna_implication or risk.description[:100]}"
        if consideration not in considerations:
            considerations.append(consideration)

    # 3. Get integration-related strategic considerations
    domain_sc = [sc for sc in reasoning_store.strategic_considerations
                if sc.domain == domain and sc.integration_related]

    for sc in domain_sc:
        if len(considerations) >= max_items:
            break
        if sc.implication and sc.implication not in considerations:
            considerations.append(sc.implication)

    return considerations[:max_items]


def get_overlap_ids(
    domain: str,
    reasoning_store: "ReasoningStore"
) -> List[str]:
    """Get overlap IDs for a domain."""
    return [oc.overlap_id for oc in reasoning_store.overlap_candidates if oc.domain == domain]
