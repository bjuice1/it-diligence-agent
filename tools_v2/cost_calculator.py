"""
Centralized Cost Calculation for IT Due Diligence

This module provides a single source of truth for cost calculations.
All cost rollups MUST use this module to ensure consistency.

CRITICAL: Costs are ONLY computed from work items, never from ad-hoc prose.
"""

from typing import Dict, List, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# COST RANGE DEFINITIONS (Single Source of Truth)
# =============================================================================

# These values MUST match the reasoning tools cost estimates
COST_RANGE_VALUES = {
    "under_25k": {"low": 0, "high": 25_000, "label": "<$25K"},
    "25k_to_100k": {"low": 25_000, "high": 100_000, "label": "$25K-$100K"},
    "100k_to_250k": {"low": 100_000, "high": 250_000, "label": "$100K-$250K"},
    "250k_to_500k": {"low": 250_000, "high": 500_000, "label": "$250K-$500K"},
    "500k_to_1m": {"low": 500_000, "high": 1_000_000, "label": "$500K-$1M"},
    "over_1m": {"low": 1_000_000, "high": 2_500_000, "label": ">$1M"},
}

# Phase labels for display
PHASE_LABELS = {
    "Day_1": "Day 1",
    "Day_100": "Day 100",
    "Post_100": "Post 100",
}

# Owner type labels for display
OWNER_LABELS = {
    "target": "Target",
    "buyer": "Buyer",
    "combined": "Combined",
}


@dataclass
class CostBreakdown:
    """Structured cost breakdown computed from work items."""

    # Totals
    total_low: float = 0.0
    total_high: float = 0.0
    total_work_items: int = 0

    # By phase
    by_phase: Dict[str, Dict[str, Any]] = None

    # By domain
    by_domain: Dict[str, Dict[str, Any]] = None

    # By owner
    by_owner: Dict[str, Dict[str, Any]] = None

    # Work item details (for traceability)
    work_item_costs: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.by_phase is None:
            self.by_phase = {}
        if self.by_domain is None:
            self.by_domain = {}
        if self.by_owner is None:
            self.by_owner = {}
        if self.work_item_costs is None:
            self.work_item_costs = []


def calculate_costs_from_work_items(work_items: List[Any]) -> CostBreakdown:
    """
    Calculate cost breakdown from work items, preferring CostBuildUp when available.

    Priority:
    1. CostBuildUp (precise, anchor-based) - if work_item.cost_buildup exists
    2. cost_estimate string (vague range) - fallback

    This is the ONLY function that should be used for cost calculations
    to ensure consistency across the system.

    Args:
        work_items: List of WorkItem objects from ReasoningStore

    Returns:
        CostBreakdown with all cost aggregations
    """
    breakdown = CostBreakdown()

    # Initialize phase buckets
    for phase in PHASE_LABELS:
        breakdown.by_phase[phase] = {"low": 0, "high": 0, "count": 0, "items": []}

    # Process each work item
    for wi in work_items:
        # Get attributes
        wi_id = getattr(wi, 'finding_id', 'unknown')
        phase = getattr(wi, 'phase', 'Day_100')
        domain = getattr(wi, 'domain', 'unknown')
        owner = getattr(wi, 'owner_type', 'combined')
        title = getattr(wi, 'title', '')
        cost_estimate = getattr(wi, 'cost_estimate', None)

        # Prefer CostBuildUp for precise estimates
        cost_buildup = getattr(wi, 'cost_buildup', None)
        if cost_buildup is not None:
            low = cost_buildup.total_low
            high = cost_buildup.total_high
            estimation_source = "cost_buildup"
            anchor_key = cost_buildup.anchor_key
        else:
            # Fallback to vague range from cost_estimate string
            if not cost_estimate:
                logger.warning(f"Work item {wi_id} has no cost_estimate")
                continue

            cost_range = COST_RANGE_VALUES.get(cost_estimate)
            if not cost_range:
                logger.warning(f"Unknown cost_estimate '{cost_estimate}' for work item {wi_id}")
                continue

            low = cost_range['low']
            high = cost_range['high']
            estimation_source = "cost_range"
            anchor_key = None

        # Record individual work item cost
        wi_cost = {
            "id": wi_id,
            "title": title,
            "phase": phase,
            "domain": domain,
            "owner": owner,
            "cost_estimate": cost_estimate,
            "low": low,
            "high": high,
            "estimation_source": estimation_source,
            "anchor_key": anchor_key,
        }
        breakdown.work_item_costs.append(wi_cost)

        # Aggregate totals
        breakdown.total_low += low
        breakdown.total_high += high
        breakdown.total_work_items += 1

        # Aggregate by phase
        if phase in breakdown.by_phase:
            breakdown.by_phase[phase]["low"] += low
            breakdown.by_phase[phase]["high"] += high
            breakdown.by_phase[phase]["count"] += 1
            breakdown.by_phase[phase]["items"].append(wi_id)

        # Aggregate by domain
        if domain not in breakdown.by_domain:
            breakdown.by_domain[domain] = {"low": 0, "high": 0, "count": 0, "items": []}
        breakdown.by_domain[domain]["low"] += low
        breakdown.by_domain[domain]["high"] += high
        breakdown.by_domain[domain]["count"] += 1
        breakdown.by_domain[domain]["items"].append(wi_id)

        # Aggregate by owner
        if owner not in breakdown.by_owner:
            breakdown.by_owner[owner] = {"low": 0, "high": 0, "count": 0, "items": []}
        breakdown.by_owner[owner]["low"] += low
        breakdown.by_owner[owner]["high"] += high
        breakdown.by_owner[owner]["count"] += 1
        breakdown.by_owner[owner]["items"].append(wi_id)

    logger.info(
        f"Computed costs from {breakdown.total_work_items} work items: "
        f"${breakdown.total_low:,.0f} - ${breakdown.total_high:,.0f}"
    )

    return breakdown


def format_cost_range(low: float, high: float) -> str:
    """Format a cost range for display."""
    if low == 0 and high == 0:
        return "TBD"
    elif low == high:
        return f"${low:,.0f}"
    else:
        return f"${low:,.0f} - ${high:,.0f}"


def format_cost_summary(breakdown: CostBreakdown) -> Dict[str, Any]:
    """
    Format cost breakdown for presentation/JSON output.

    Returns a structured dictionary suitable for templates and JSON export.
    """
    return {
        "total": {
            "low": breakdown.total_low,
            "high": breakdown.total_high,
            "formatted": format_cost_range(breakdown.total_low, breakdown.total_high),
            "work_item_count": breakdown.total_work_items
        },
        "by_phase": {
            phase: {
                "low": data["low"],
                "high": data["high"],
                "formatted": format_cost_range(data["low"], data["high"]),
                "count": data["count"],
                "label": PHASE_LABELS.get(phase, phase)
            }
            for phase, data in breakdown.by_phase.items()
            if data["count"] > 0
        },
        "by_domain": {
            domain: {
                "low": data["low"],
                "high": data["high"],
                "formatted": format_cost_range(data["low"], data["high"]),
                "count": data["count"]
            }
            for domain, data in breakdown.by_domain.items()
        },
        "by_owner": {
            owner: {
                "low": data["low"],
                "high": data["high"],
                "formatted": format_cost_range(data["low"], data["high"]),
                "count": data["count"],
                "label": OWNER_LABELS.get(owner, owner)
            }
            for owner, data in breakdown.by_owner.items()
        },
        "work_items": breakdown.work_item_costs,
        "_source": "calculated_from_work_items",  # Traceability marker
        "_work_item_count": breakdown.total_work_items
    }


def get_cost_statement(breakdown: CostBreakdown, total_gaps: int = 0) -> str:
    """
    Generate a cost statement from computed costs.

    This ensures cost statements are ALWAYS derived from work items.
    """
    if breakdown.total_work_items == 0:
        return "No cost estimates available - work items required for pricing."

    cost_str = format_cost_range(breakdown.total_low, breakdown.total_high)
    statement = f"Expected integration cost: {cost_str} (based on {breakdown.total_work_items} work items)"

    if total_gaps >= 10:
        statement += f". Note: {total_gaps} information gaps remain - estimates may shift."
    elif total_gaps >= 5:
        statement += f". {total_gaps} gaps should be resolved before finalizing."

    return statement


def validate_cost_consistency(
    stated_low: float,
    stated_high: float,
    computed_breakdown: CostBreakdown,
    tolerance: float = 0.05
) -> Dict[str, Any]:
    """
    Validate that stated costs match computed costs.

    Use this to catch any prose-based cost statements that don't match
    the actual work item totals.

    Args:
        stated_low: Low end of stated cost range
        stated_high: High end of stated cost range
        computed_breakdown: Breakdown computed from work items
        tolerance: Acceptable variance (default 5%)

    Returns:
        Dict with validation results
    """
    computed_low = computed_breakdown.total_low
    computed_high = computed_breakdown.total_high

    # Calculate variance
    low_variance = abs(stated_low - computed_low) / max(computed_low, 1)
    high_variance = abs(stated_high - computed_high) / max(computed_high, 1)

    is_consistent = low_variance <= tolerance and high_variance <= tolerance

    return {
        "is_consistent": is_consistent,
        "stated": {"low": stated_low, "high": stated_high},
        "computed": {"low": computed_low, "high": computed_high},
        "variance": {
            "low": f"{low_variance:.1%}",
            "high": f"{high_variance:.1%}"
        },
        "tolerance": f"{tolerance:.1%}",
        "message": (
            "Costs are consistent with work items" if is_consistent
            else f"WARNING: Stated costs differ from computed work item totals by more than {tolerance:.0%}"
        )
    }
