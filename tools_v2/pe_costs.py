"""
PE Costs Service

Cost extraction and aggregation from facts for PE reporting.
Handles both run-rate costs (annual spending) and one-time costs (work items).

Key Principle: Costs are extracted from facts with clear attribution.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple, TYPE_CHECKING

from tools_v2.pe_report_schemas import (
    CostsReportData,
    InvestmentReportData,
    WorkItemSummary,
    DealContext,
)
from tools_v2.cost_calculator import (
    calculate_costs_from_work_items,
    COST_RANGE_VALUES,
)

if TYPE_CHECKING:
    from stores.fact_store import FactStore
    from tools_v2.reasoning_tools import ReasoningStore, WorkItem

logger = logging.getLogger(__name__)


# =============================================================================
# COST EXTRACTION FROM FACTS
# =============================================================================

def extract_run_rate_costs(
    fact_store: "FactStore",
    entity: str = "target"
) -> Dict[str, Any]:
    """
    Extract run-rate (annual) costs from facts.

    Looks for costs in:
    - fact.details.annual_cost
    - fact.details.cost
    - fact.details.spend
    - fact.details.budget
    - Facts with category="costs"

    Args:
        fact_store: Fact store with discovered facts
        entity: Entity to filter by ("target" or "buyer")

    Returns:
        Dict with costs organized by domain and category
    """
    costs = {
        "by_domain": {},
        "by_category": {
            "infrastructure": {"low": 0, "high": 0, "facts": []},
            "applications": {"low": 0, "high": 0, "facts": []},
            "personnel": {"low": 0, "high": 0, "facts": []},
            "vendors": {"low": 0, "high": 0, "facts": []},
            "network": {"low": 0, "high": 0, "facts": []},
            "security": {"low": 0, "high": 0, "facts": []},
            "other": {"low": 0, "high": 0, "facts": []},
        },
        "total": {"low": 0, "high": 0},
        "facts_cited": [],
    }

    # Initialize domain buckets
    for domain in ["organization", "applications", "infrastructure", "network", "cybersecurity", "identity_access"]:
        costs["by_domain"][domain] = {"low": 0, "high": 0, "facts": []}

    # Process facts
    for fact in fact_store.facts:
        # Filter by entity
        if getattr(fact, "entity", "target") != entity:
            continue

        details = fact.details or {}
        domain = fact.domain
        category = fact.category

        # Look for cost values in various fields
        cost_value = None
        cost_field = None

        for field in ["annual_cost", "cost", "spend", "budget", "annual_spend", "total_cost"]:
            if field in details:
                val = details[field]
                if isinstance(val, (int, float)) and val > 0:
                    cost_value = val
                    cost_field = field
                    break

        if cost_value is None:
            continue

        # Record the cost
        fact_ref = fact.fact_id
        costs["facts_cited"].append(fact_ref)

        # Add to domain bucket
        if domain in costs["by_domain"]:
            costs["by_domain"][domain]["low"] += cost_value
            costs["by_domain"][domain]["high"] += cost_value
            costs["by_domain"][domain]["facts"].append(fact_ref)

        # Add to category bucket
        cost_category = _categorize_cost(domain, category, fact.item)
        if cost_category in costs["by_category"]:
            costs["by_category"][cost_category]["low"] += cost_value
            costs["by_category"][cost_category]["high"] += cost_value
            costs["by_category"][cost_category]["facts"].append(fact_ref)

        # Add to total
        costs["total"]["low"] += cost_value
        costs["total"]["high"] += cost_value

    return costs


def _categorize_cost(domain: str, category: str, item: str) -> str:
    """Categorize a cost into standard buckets."""
    item_lower = (item or "").lower()
    category_lower = (category or "").lower()

    # Personnel costs
    if any(kw in category_lower or kw in item_lower for kw in
           ["personnel", "salary", "staff", "headcount", "fte", "team"]):
        return "personnel"

    # Vendor/MSP costs
    if any(kw in category_lower or kw in item_lower for kw in
           ["vendor", "msp", "outsource", "contract", "service provider"]):
        return "vendors"

    # Application costs
    if domain == "applications" or any(kw in category_lower for kw in
                                       ["license", "saas", "software", "application"]):
        return "applications"

    # Infrastructure costs
    if domain == "infrastructure" or any(kw in category_lower for kw in
                                         ["hosting", "cloud", "server", "storage", "compute"]):
        return "infrastructure"

    # Network costs
    if domain == "network" or any(kw in category_lower for kw in
                                  ["network", "connectivity", "bandwidth", "wan", "mpls"]):
        return "network"

    # Security costs
    if domain == "cybersecurity" or any(kw in category_lower for kw in
                                        ["security", "cyber", "firewall", "endpoint"]):
        return "security"

    return "other"


def extract_it_budget_summary(
    fact_store: "FactStore",
    deal_context: Optional[DealContext],
    entity: str = "target"
) -> Dict[str, Any]:
    """
    Extract IT budget summary from organization facts.

    Args:
        fact_store: Fact store with discovered facts
        deal_context: Deal context for company info
        entity: Entity to filter by

    Returns:
        Dict with budget summary metrics
    """
    summary = {
        "total_it_budget": None,
        "it_pct_revenue": None,
        "it_headcount": None,
        "cost_per_employee": None,
    }

    # Look for budget facts in organization domain
    org_facts = [f for f in fact_store.facts
                 if f.domain == "organization"
                 and getattr(f, "entity", "target") == entity]

    for fact in org_facts:
        details = fact.details or {}

        if "total_it_budget" in details:
            summary["total_it_budget"] = details["total_it_budget"]

        if "percent_of_revenue" in details:
            summary["it_pct_revenue"] = details["percent_of_revenue"]

        if "total_it_headcount" in details:
            summary["it_headcount"] = details["total_it_headcount"]

    # Calculate derived metrics
    if summary["total_it_budget"] and deal_context:
        if deal_context.target_employees and deal_context.target_employees > 0:
            summary["cost_per_employee"] = int(summary["total_it_budget"] / deal_context.target_employees)

        if not summary["it_pct_revenue"] and deal_context.target_revenue and deal_context.target_revenue > 0:
            summary["it_pct_revenue"] = (summary["total_it_budget"] / deal_context.target_revenue) * 100

    return summary


# =============================================================================
# WORK ITEM COST AGGREGATION
# =============================================================================

def aggregate_work_item_costs(
    reasoning_store: "ReasoningStore",
    domain_filter: Optional[str] = None
) -> Dict[str, Any]:
    """
    Aggregate one-time costs from work items.

    Args:
        reasoning_store: Reasoning store with work items
        domain_filter: Optional domain to filter by

    Returns:
        Dict with aggregated costs by phase, domain, priority, type
    """
    work_items = list(reasoning_store.work_items)

    if domain_filter:
        work_items = [wi for wi in work_items if wi.domain == domain_filter]

    # Use existing cost calculator
    breakdown = calculate_costs_from_work_items(work_items)

    # Build result structure
    result = {
        "total": {
            "low": int(breakdown.total_low),
            "high": int(breakdown.total_high),
            "count": breakdown.total_work_items,
        },
        "by_phase": {},
        "by_domain": {},
        "by_priority": {},
        "by_type": {},  # separation, integration, run, transform
        "by_owner": {},
        "work_items": [],
    }

    # Convert phase breakdown
    for phase, data in breakdown.by_phase.items():
        result["by_phase"][phase] = {
            "low": int(data.get("low", 0)),
            "high": int(data.get("high", 0)),
            "count": data.get("count", 0),
        }

    # Convert domain breakdown
    for domain, data in breakdown.by_domain.items():
        result["by_domain"][domain] = {
            "low": int(data.get("low", 0)),
            "high": int(data.get("high", 0)),
            "count": data.get("count", 0),
        }

    # Build additional aggregations
    priority_agg = {}
    type_agg = {}
    owner_agg = {}

    for wi in work_items:
        # Get cost values
        cost_estimate = getattr(wi, "cost_estimate", None)
        if not cost_estimate or cost_estimate not in COST_RANGE_VALUES:
            continue

        cost_range = COST_RANGE_VALUES[cost_estimate]
        low = cost_range["low"]
        high = cost_range["high"]

        # Aggregate by priority
        priority = getattr(wi, "priority", "medium")
        if priority not in priority_agg:
            priority_agg[priority] = {"low": 0, "high": 0, "count": 0}
        priority_agg[priority]["low"] += low
        priority_agg[priority]["high"] += high
        priority_agg[priority]["count"] += 1

        # Aggregate by type (if available)
        wi_type = getattr(wi, "type", "run")  # Default to "run"
        if wi_type not in type_agg:
            type_agg[wi_type] = {"low": 0, "high": 0, "count": 0}
        type_agg[wi_type]["low"] += low
        type_agg[wi_type]["high"] += high
        type_agg[wi_type]["count"] += 1

        # Aggregate by owner
        owner = getattr(wi, "owner_type", "target")
        if owner not in owner_agg:
            owner_agg[owner] = {"low": 0, "high": 0, "count": 0}
        owner_agg[owner]["low"] += low
        owner_agg[owner]["high"] += high
        owner_agg[owner]["count"] += 1

        # Build work item summary
        result["work_items"].append({
            "id": wi.finding_id,
            "title": wi.title,
            "domain": wi.domain,
            "phase": wi.phase,
            "priority": priority,
            "type": wi_type,
            "owner": owner,
            "cost_low": low,
            "cost_high": high,
        })

    result["by_priority"] = {k: {"low": int(v["low"]), "high": int(v["high"]), "count": v["count"]}
                            for k, v in priority_agg.items()}
    result["by_type"] = {k: {"low": int(v["low"]), "high": int(v["high"]), "count": v["count"]}
                         for k, v in type_agg.items()}
    result["by_owner"] = {k: {"low": int(v["low"]), "high": int(v["high"]), "count": v["count"]}
                          for k, v in owner_agg.items()}

    return result


# =============================================================================
# REPORT DATA BUILDERS
# =============================================================================

def build_costs_report_data(
    fact_store: "FactStore",
    deal_context: Optional[DealContext],
    entity: str = "target"
) -> CostsReportData:
    """
    Build CostsReportData from facts.

    Args:
        fact_store: Fact store with discovered facts
        deal_context: Deal context for company info
        entity: Entity to filter by

    Returns:
        CostsReportData instance
    """
    # Extract costs
    costs = extract_run_rate_costs(fact_store, entity)
    budget_summary = extract_it_budget_summary(fact_store, deal_context, entity)

    # Build by_domain tuple format
    by_domain = {}
    for domain, data in costs["by_domain"].items():
        by_domain[domain] = (data["low"], data["high"])

    # Build report data
    report = CostsReportData(
        total_run_rate=(costs["total"]["low"], costs["total"]["high"]),
        cost_per_employee=budget_summary.get("cost_per_employee"),
        it_pct_revenue=budget_summary.get("it_pct_revenue"),
        by_domain=by_domain,
        infrastructure_costs=(
            costs["by_category"]["infrastructure"]["low"],
            costs["by_category"]["infrastructure"]["high"]
        ),
        application_costs=(
            costs["by_category"]["applications"]["low"],
            costs["by_category"]["applications"]["high"]
        ),
        personnel_costs=(
            costs["by_category"]["personnel"]["low"],
            costs["by_category"]["personnel"]["high"]
        ),
        vendor_costs=(
            costs["by_category"]["vendors"]["low"],
            costs["by_category"]["vendors"]["high"]
        ),
        network_costs=(
            costs["by_category"]["network"]["low"],
            costs["by_category"]["network"]["high"]
        ),
        cost_facts_cited=costs["facts_cited"],
    )

    # Determine key cost drivers
    cost_drivers = []
    categories = costs["by_category"]

    # Sort by total cost
    sorted_cats = sorted(
        [(k, v["low"] + v["high"]) for k, v in categories.items()],
        key=lambda x: x[1],
        reverse=True
    )

    for cat, total in sorted_cats[:3]:
        if total > 0:
            cost_drivers.append(f"{cat.title()}: ${total:,.0f}")

    report.key_cost_drivers = cost_drivers

    return report


def build_investment_report_data(
    reasoning_store: "ReasoningStore"
) -> InvestmentReportData:
    """
    Build InvestmentReportData from work items.

    Args:
        reasoning_store: Reasoning store with work items

    Returns:
        InvestmentReportData instance
    """
    # Aggregate costs
    agg = aggregate_work_item_costs(reasoning_store)

    # Build work item summaries
    work_items = []
    work_items_by_domain = {}
    day_1_items = []
    day_100_items = []
    post_100_items = []

    for wi_data in agg["work_items"]:
        summary = WorkItemSummary(
            title=wi_data["title"],
            domain=wi_data["domain"],
            phase=wi_data["phase"],
            priority=wi_data["priority"],
            cost_estimate_low=wi_data["cost_low"],
            cost_estimate_high=wi_data["cost_high"],
            owner_type=wi_data["owner"],
            work_item_id=wi_data["id"],
            type=wi_data.get("type", "run"),
        )

        work_items.append(summary)

        # Organize by domain
        domain = wi_data["domain"]
        if domain not in work_items_by_domain:
            work_items_by_domain[domain] = []
        work_items_by_domain[domain].append(summary)

        # Organize by phase
        phase = wi_data["phase"]
        if phase == "Day_1":
            day_1_items.append(summary)
        elif phase == "Day_100":
            day_100_items.append(summary)
        else:
            post_100_items.append(summary)

    # Identify critical path items (critical priority or Day_1)
    critical_path = [wi.title for wi in work_items
                     if wi.priority == "critical" or wi.phase == "Day_1"]

    # Build by_phase tuple format
    by_phase = {}
    for phase, data in agg["by_phase"].items():
        by_phase[phase] = (data["low"], data["high"])

    # Build by_domain tuple format
    by_domain = {}
    for domain, data in agg["by_domain"].items():
        by_domain[domain] = (data["low"], data["high"])

    # Build by_priority tuple format
    by_priority = {}
    for priority, data in agg["by_priority"].items():
        by_priority[priority] = (data["low"], data["high"])

    # Build by_type tuple format
    by_type = {}
    for type_name, data in agg["by_type"].items():
        by_type[type_name] = (data["low"], data["high"])

    # Build phase counts
    by_phase_count = {}
    for phase, data in agg["by_phase"].items():
        by_phase_count[phase] = data["count"]

    # Build priority counts
    by_priority_count = {}
    for priority, data in agg["by_priority"].items():
        by_priority_count[priority] = data["count"]

    report = InvestmentReportData(
        total_one_time=(agg["total"]["low"], agg["total"]["high"]),
        by_phase=by_phase,
        by_domain=by_domain,
        by_priority=by_priority,
        by_type=by_type,
        work_items=work_items,
        work_items_by_domain=work_items_by_domain,
        critical_path_items=critical_path[:10],  # Top 10
        day_1_items=day_1_items,
        day_100_items=day_100_items,
        post_100_items=post_100_items,
        total_count=agg["total"]["count"],
        by_phase_count=by_phase_count,
        by_priority_count=by_priority_count,
    )

    return report


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def format_cost_range(low: int, high: int) -> str:
    """Format a cost range for display."""
    if low == 0 and high == 0:
        return "TBD"
    elif low == high:
        return f"${low:,.0f}"
    elif low == 0:
        return f"Up to ${high:,.0f}"
    else:
        return f"${low:,.0f} - ${high:,.0f}"


def get_domain_costs(
    fact_store: "FactStore",
    reasoning_store: "ReasoningStore",
    domain: str,
    entity: str = "target"
) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    """
    Get run-rate and investment costs for a specific domain.

    Args:
        fact_store: Fact store with discovered facts
        reasoning_store: Reasoning store with work items
        domain: Domain to get costs for
        entity: Entity to filter by

    Returns:
        Tuple of (run_rate_costs, investment_costs) as (low, high) tuples
    """
    # Run-rate costs from facts
    run_rate_costs = extract_run_rate_costs(fact_store, entity)
    domain_run_rate = run_rate_costs["by_domain"].get(domain, {"low": 0, "high": 0})

    # Investment costs from work items
    investment_agg = aggregate_work_item_costs(reasoning_store, domain_filter=domain)

    return (
        (domain_run_rate["low"], domain_run_rate["high"]),
        (investment_agg["total"]["low"], investment_agg["total"]["high"])
    )
