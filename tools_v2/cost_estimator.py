"""
Cost Estimator Module

Provides functions to create detailed cost build-ups with full transparency.
Links work items to specific cost anchors from the cost model.

Usage:
    from tools_v2.cost_estimator import estimate_cost, get_anchor_info

    # Create a detailed cost estimate
    buildup = estimate_cost(
        anchor_key="identity_separation",
        quantity=1500,
        size_tier="medium",
        source_facts=["F-001", "F-023"],
        assumptions=["Using Azure AD", "Clean migration path"]
    )

    # The buildup contains full transparency:
    # - anchor_name: "Identity Separation"
    # - estimation_method: "fixed_by_size"
    # - unit_cost_low/high: from COST_ANCHORS
    # - total_low/high: calculated
    # - assumptions and source_facts preserved
"""

import logging
from typing import List, Optional, Dict, Any, Tuple

from tools_v2.cost_model import COST_ANCHORS, RUN_RATE_ANCHORS, ACQUISITION_COSTS
from tools_v2.reasoning_tools import CostBuildUp

logger = logging.getLogger(__name__)


# Combine all anchors for lookup
ALL_ANCHORS = {**COST_ANCHORS, **RUN_RATE_ANCHORS, **ACQUISITION_COSTS}


# Unit labels for different estimation methods
UNIT_LABELS = {
    "per_user": "users",
    "per_user_annual": "users",
    "per_app": "applications",
    "per_site": "sites",
    "per_site_annual": "sites",
    "per_server": "servers",
    "per_server_annual": "servers",
    "per_dc": "data centers",
    "per_tb": "TB",
    "per_vendor": "vendors",
    "per_tool": "tools",
    "per_fte": "FTEs",
    "fixed": "organization",
    "fixed_by_size": "organization",
    "fixed_by_complexity": "organization",
    "fixed_by_gaps": "organization",
    "fixed_plus_per_user": "users",
    "percentage": "of total",
}


def get_anchor_info(anchor_key: str) -> Optional[Dict[str, Any]]:
    """
    Get information about a cost anchor.

    Args:
        anchor_key: Key from COST_ANCHORS (e.g., "identity_separation")

    Returns:
        Dict with anchor details or None if not found
    """
    return ALL_ANCHORS.get(anchor_key)


def list_anchors(category: str = None) -> List[Dict[str, Any]]:
    """
    List available cost anchors, optionally filtered by category.

    Args:
        category: Optional filter - "one_time", "run_rate", "acquisition", "tsa_exit"

    Returns:
        List of anchor info dicts with keys included
    """
    result = []

    for key, anchor in ALL_ANCHORS.items():
        anchor_info = {"key": key, **anchor}

        # Categorize
        if key.startswith("runrate_"):
            anchor_info["category"] = "run_rate"
        elif key.startswith("tsa_exit_"):
            anchor_info["category"] = "tsa_exit"
        elif key.startswith("integration_"):
            anchor_info["category"] = "acquisition"
        else:
            anchor_info["category"] = "one_time"

        if category is None or anchor_info["category"] == category:
            result.append(anchor_info)

    return result


def _get_anchor_range(anchor: Dict, size_tier: str = None) -> Tuple[float, float]:
    """
    Get the low/high range from an anchor, handling different unit types.

    Args:
        anchor: The anchor dict from COST_ANCHORS
        size_tier: For fixed_by_size anchors: "small", "medium", "large"

    Returns:
        Tuple of (low, high) costs
    """
    unit = anchor.get("unit", "fixed")

    # Handle fixed_by_size anchors
    if unit == "fixed_by_size":
        tier = size_tier or "medium"
        tier_key = f"anchor_{tier}"
        if tier_key in anchor:
            return anchor[tier_key]
        # Fallback to medium if tier not found
        return anchor.get("anchor_medium", anchor.get("anchor", (0, 0)))

    # Handle fixed_by_complexity
    if unit == "fixed_by_complexity":
        tier = size_tier or "moderate"
        tier_key = f"anchor_{tier}"
        if tier_key in anchor:
            return anchor[tier_key]
        return anchor.get("anchor_moderate", anchor.get("anchor", (0, 0)))

    # Handle fixed_by_gaps
    if unit == "fixed_by_gaps":
        tier = size_tier or "moderate"
        tier_key = f"anchor_{tier}"
        if tier_key in anchor:
            return anchor[tier_key]
        return anchor.get("anchor_moderate", anchor.get("anchor", (0, 0)))

    # Handle tiered run-rate anchors (e.g., anchor_e3, anchor_e5)
    if size_tier and f"anchor_{size_tier}" in anchor:
        return anchor[f"anchor_{size_tier}"]

    # Standard anchor
    if "anchor" in anchor:
        return anchor["anchor"]

    # Try first anchor_ prefix found
    for key, val in anchor.items():
        if key.startswith("anchor") and isinstance(val, tuple):
            return val

    return (0, 0)


def estimate_cost(
    anchor_key: str,
    quantity: int = 1,
    size_tier: str = None,
    source_facts: List[str] = None,
    assumptions: List[str] = None,
    notes: str = "",
    estimation_source: str = "benchmark",
    source_details: str = "",
    confidence: str = "medium",
    scale_factor: float = 1.0
) -> Optional[CostBuildUp]:
    """
    Create a detailed cost estimate with full transparency.

    Args:
        anchor_key: Key from COST_ANCHORS (e.g., "identity_separation", "license_microsoft")
        quantity: Number of units (users, apps, sites). Use 1 for fixed costs.
        size_tier: For tiered anchors - "small", "medium", "large", "e3", "e5", etc.
        source_facts: Fact IDs that informed this estimate
        assumptions: List of assumptions made in the estimate
        notes: Additional context

    Returns:
        CostBuildUp with full calculation transparency, or None if anchor not found

    Example:
        # Per-user cost (e.g., license transition)
        buildup = estimate_cost(
            anchor_key="license_microsoft",
            quantity=1500,  # users
            source_facts=["F-001"],
            assumptions=["Losing EA discount", "Moving to E3 tier"]
        )
        # Result: 1500 users × $180-$400 = $270,000 - $600,000

        # Fixed-by-size cost (e.g., identity separation)
        buildup = estimate_cost(
            anchor_key="identity_separation",
            quantity=1,
            size_tier="medium",  # 1000-5000 users
            assumptions=["Azure AD migration", "Clean separation"]
        )
        # Result: 1 medium org × $300,000-$800,000 = $300,000 - $800,000
    """
    anchor = get_anchor_info(anchor_key)
    if not anchor:
        logger.warning(f"Unknown cost anchor: {anchor_key}")
        return None

    # Get the cost range
    unit_cost_low, unit_cost_high = _get_anchor_range(anchor, size_tier)

    # Get estimation method (unit type)
    estimation_method = anchor.get("unit", "fixed")

    # Get unit label
    unit_label = UNIT_LABELS.get(estimation_method, "units")

    # For fixed costs, quantity is always 1
    if estimation_method in ("fixed", "fixed_by_size", "fixed_by_complexity", "fixed_by_gaps"):
        quantity = 1
        if size_tier:
            unit_label = f"{size_tier} organization"

    # Calculate totals with scale factor
    total_low = quantity * unit_cost_low * scale_factor
    total_high = quantity * unit_cost_high * scale_factor

    return CostBuildUp(
        anchor_key=anchor_key,
        anchor_name=anchor.get("name", anchor_key),
        estimation_method=estimation_method,
        quantity=quantity,
        unit_label=unit_label,
        unit_cost_low=unit_cost_low,
        unit_cost_high=unit_cost_high,
        total_low=total_low,
        total_high=total_high,
        assumptions=assumptions or [],
        source_facts=source_facts or [],
        notes=notes,
        size_tier=size_tier or "",
        estimation_source=estimation_source,
        source_details=source_details,
        confidence=confidence,
        scale_factor=scale_factor
    )


def estimate_from_facts(
    anchor_key: str,
    facts: List[Any],
    quantity_fact_pattern: str = None,
    size_tier: str = None,
    additional_assumptions: List[str] = None
) -> Optional[CostBuildUp]:
    """
    Create a cost estimate using facts to determine quantity.

    Args:
        anchor_key: Key from COST_ANCHORS
        facts: List of Fact objects to search
        quantity_fact_pattern: Pattern to find quantity fact (e.g., "user count", "total users")
        size_tier: For tiered anchors
        additional_assumptions: Extra assumptions beyond fact-derived ones

    Returns:
        CostBuildUp with facts linked as sources
    """
    source_facts = []
    quantity = 1
    assumptions = additional_assumptions or []

    # Try to find quantity from facts
    if quantity_fact_pattern and facts:
        for fact in facts:
            fact_text = getattr(fact, 'value', str(fact)).lower()
            if quantity_fact_pattern.lower() in fact_text:
                # Try to extract number
                import re
                numbers = re.findall(r'[\d,]+', fact_text)
                if numbers:
                    try:
                        quantity = int(numbers[0].replace(',', ''))
                        source_facts.append(getattr(fact, 'fact_id', str(fact)))
                        assumptions.append(f"Quantity from: {fact_text[:100]}")
                        break
                    except ValueError:
                        pass

    # Add fact IDs as sources
    for fact in facts[:5]:  # Limit to first 5 facts
        fact_id = getattr(fact, 'fact_id', None)
        if fact_id and fact_id not in source_facts:
            source_facts.append(fact_id)

    return estimate_cost(
        anchor_key=anchor_key,
        quantity=quantity,
        size_tier=size_tier,
        source_facts=source_facts,
        assumptions=assumptions
    )


def create_buildup_summary(buildups: List[CostBuildUp]) -> Dict[str, Any]:
    """
    Create a summary of multiple cost build-ups.

    Args:
        buildups: List of CostBuildUp objects

    Returns:
        Summary dict with totals by phase, domain, and overall
    """
    total_low = sum(b.total_low for b in buildups)
    total_high = sum(b.total_high for b in buildups)

    # Group by estimation method
    by_method = {}
    for b in buildups:
        method = b.estimation_method
        if method not in by_method:
            by_method[method] = {"count": 0, "total_low": 0, "total_high": 0}
        by_method[method]["count"] += 1
        by_method[method]["total_low"] += b.total_low
        by_method[method]["total_high"] += b.total_high

    # All assumptions
    all_assumptions = []
    for b in buildups:
        all_assumptions.extend(b.assumptions)

    return {
        "total_low": total_low,
        "total_high": total_high,
        "total_mid": (total_low + total_high) / 2,
        "count": len(buildups),
        "by_method": by_method,
        "all_assumptions": list(set(all_assumptions)),  # Dedupe
    }


# Common estimation shortcuts
def estimate_identity_separation(user_count: int, **kwargs) -> CostBuildUp:
    """Estimate identity separation cost based on user count."""
    if user_count < 1000:
        size_tier = "small"
    elif user_count < 5000:
        size_tier = "medium"
    else:
        size_tier = "large"

    kwargs.setdefault("assumptions", []).append(f"{user_count:,} users → {size_tier} tier")
    return estimate_cost("identity_separation", size_tier=size_tier, **kwargs)


def estimate_license_transition(user_count: int, license_type: str = "microsoft", **kwargs) -> CostBuildUp:
    """Estimate license transition cost."""
    anchor_key = f"license_{license_type}"
    kwargs.setdefault("assumptions", []).append(f"Standalone licensing for {user_count:,} users")
    return estimate_cost(anchor_key, quantity=user_count, **kwargs)


def estimate_app_migration(app_count: int, complexity: str = "moderate", **kwargs) -> CostBuildUp:
    """Estimate application migration cost."""
    anchor_key = f"app_migration_{complexity}"
    kwargs.setdefault("assumptions", []).append(f"{app_count} {complexity} applications")
    return estimate_cost(anchor_key, quantity=app_count, **kwargs)


def estimate_network_separation(site_count: int, complexity: str = "moderate", **kwargs) -> CostBuildUp:
    """Estimate network separation cost."""
    # Fixed base cost for network separation
    base = estimate_cost("network_separation", size_tier=complexity, **kwargs)

    # Per-site WAN setup
    if site_count > 1:
        per_site = estimate_cost("wan_setup", quantity=site_count, **kwargs)
        if base and per_site:
            # Combine into single buildup
            base.total_low += per_site.total_low
            base.total_high += per_site.total_high
            base.notes = f"Base separation + {site_count} site WAN setup"

    return base


# =============================================================================
# ESTIMATION SOURCE HELPERS
# =============================================================================

def estimate_from_inventory(
    anchor_key: str,
    inventory_items: List[Any],
    quantity_field: str = None,
    **kwargs
) -> Optional[CostBuildUp]:
    """
    Create cost estimate from actual inventory data.

    Higher confidence because quantity is based on real data, not estimates.

    Args:
        anchor_key: Cost anchor to use
        inventory_items: List of inventory items (apps, servers, etc.)
        quantity_field: Field name to sum for quantity (default: count items)
    """
    if quantity_field:
        quantity = sum(getattr(item, quantity_field, 1) for item in inventory_items)
    else:
        quantity = len(inventory_items)

    # Extract source facts from inventory if available
    source_facts = []
    for item in inventory_items[:10]:  # Limit to first 10
        item_id = getattr(item, 'id', None) or getattr(item, 'inventory_id', None)
        if item_id:
            source_facts.append(str(item_id))

    assumptions = kwargs.pop('assumptions', [])
    assumptions.append(f"Based on {quantity} items from inventory")

    return estimate_cost(
        anchor_key=anchor_key,
        quantity=quantity,
        estimation_source="inventory",
        confidence="high",  # Higher confidence from real data
        source_details=f"Inventory count: {len(inventory_items)} items",
        source_facts=source_facts,
        assumptions=assumptions,
        **kwargs
    )


def estimate_from_vendor_quote(
    activity_name: str,
    vendor_name: str,
    quoted_low: float,
    quoted_high: float = None,
    quantity: int = 1,
    unit_label: str = "item",
    **kwargs
) -> CostBuildUp:
    """
    Create cost estimate from an actual vendor quote.

    Highest confidence because it's based on real pricing.

    Args:
        activity_name: Description of the work
        vendor_name: Name of the vendor who provided quote
        quoted_low: Low end of quote (or single quote amount)
        quoted_high: High end (optional, defaults to low + 20%)
        quantity: Number of units quoted
        unit_label: What the units are
    """
    if quoted_high is None:
        quoted_high = quoted_low * 1.2  # Add 20% buffer if single quote

    unit_cost_low = quoted_low / quantity if quantity > 1 else quoted_low
    unit_cost_high = quoted_high / quantity if quantity > 1 else quoted_high

    assumptions = kwargs.pop('assumptions', [])
    assumptions.append(f"Vendor quote from {vendor_name}")

    return CostBuildUp(
        anchor_key="vendor_quote",
        anchor_name=activity_name,
        estimation_method="vendor_quote",
        quantity=quantity,
        unit_label=unit_label,
        unit_cost_low=unit_cost_low,
        unit_cost_high=unit_cost_high,
        total_low=quoted_low,
        total_high=quoted_high,
        estimation_source="vendor_quote",
        source_details=f"Quote from: {vendor_name}",
        confidence="high",
        assumptions=assumptions,
        **kwargs
    )


def estimate_from_historical(
    activity_name: str,
    historical_cost: float,
    historical_context: str,
    adjustment_factor: float = 1.0,
    variance_percent: float = 0.25,
    **kwargs
) -> CostBuildUp:
    """
    Create cost estimate from historical project costs.

    Medium-high confidence based on actual past project data.

    Args:
        activity_name: Description of the work
        historical_cost: Cost from past similar project
        historical_context: Description of the historical project
        adjustment_factor: Factor to adjust for differences (1.0 = same, 1.2 = 20% more complex)
        variance_percent: Uncertainty range (0.25 = ±25%)
    """
    adjusted_cost = historical_cost * adjustment_factor
    total_low = adjusted_cost * (1 - variance_percent)
    total_high = adjusted_cost * (1 + variance_percent)

    assumptions = kwargs.pop('assumptions', [])
    assumptions.append(f"Based on: {historical_context}")
    if adjustment_factor != 1.0:
        assumptions.append(f"Adjusted by {adjustment_factor:.0%} for scope differences")

    return CostBuildUp(
        anchor_key="historical",
        anchor_name=activity_name,
        estimation_method="historical",
        quantity=1,
        unit_label="project",
        unit_cost_low=total_low,
        unit_cost_high=total_high,
        total_low=total_low,
        total_high=total_high,
        estimation_source="historical",
        source_details=historical_context,
        confidence="medium",
        assumptions=assumptions,
        **kwargs
    )


def create_hybrid_estimate(
    activity_name: str,
    estimates: List[CostBuildUp],
    weighting: str = "average"
) -> CostBuildUp:
    """
    Create a hybrid estimate combining multiple estimation sources.

    Useful when you have benchmark + vendor quote + historical data.

    Args:
        activity_name: Description of the work
        estimates: List of CostBuildUp from different sources
        weighting: "average", "conservative" (use lowest), "aggressive" (use highest),
                  "confidence_weighted" (weight by confidence)
    """
    if not estimates:
        raise ValueError("At least one estimate required")

    if len(estimates) == 1:
        return estimates[0]

    # Combine based on weighting strategy
    if weighting == "conservative":
        total_low = min(e.total_low for e in estimates)
        total_high = min(e.total_high for e in estimates)
    elif weighting == "aggressive":
        total_low = max(e.total_low for e in estimates)
        total_high = max(e.total_high for e in estimates)
    elif weighting == "confidence_weighted":
        # Weight by confidence: high=3, medium=2, low=1
        conf_weights = {"high": 3, "medium": 2, "low": 1}
        total_weight = sum(conf_weights.get(e.confidence, 2) for e in estimates)
        total_low = sum(e.total_low * conf_weights.get(e.confidence, 2) for e in estimates) / total_weight
        total_high = sum(e.total_high * conf_weights.get(e.confidence, 2) for e in estimates) / total_weight
    else:  # average
        total_low = sum(e.total_low for e in estimates) / len(estimates)
        total_high = sum(e.total_high for e in estimates) / len(estimates)

    # Combine sources
    sources = [e.estimation_source for e in estimates]
    source_details = " + ".join(set(sources))

    # Combine assumptions
    all_assumptions = []
    for e in estimates:
        all_assumptions.extend(e.assumptions)
    all_assumptions.append(f"Hybrid estimate ({weighting}) from {len(estimates)} sources")

    # Combine source facts
    all_facts = []
    for e in estimates:
        all_facts.extend(e.source_facts)

    # Confidence is based on having multiple sources
    confidence = "high" if len(estimates) >= 3 else "medium"

    return CostBuildUp(
        anchor_key="hybrid",
        anchor_name=activity_name,
        estimation_method="hybrid",
        quantity=1,
        unit_label="estimate",
        unit_cost_low=total_low,
        unit_cost_high=total_high,
        total_low=total_low,
        total_high=total_high,
        estimation_source="hybrid",
        source_details=source_details,
        confidence=confidence,
        assumptions=list(set(all_assumptions)),  # Dedupe
        source_facts=list(set(all_facts)),
    )
