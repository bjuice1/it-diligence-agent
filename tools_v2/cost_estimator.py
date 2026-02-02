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

from tools_v2.cost_model import (
    COST_ANCHORS, RUN_RATE_ANCHORS, ACQUISITION_COSTS,
    get_volume_discount, get_regional_multiplier, get_blended_rate_multiplier,
    REGIONAL_MULTIPLIERS, VOLUME_DISCOUNT_CURVES
)
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
    scale_factor: float = 1.0,
    # NEW: Volume discount and regional adjustments
    apply_volume_discount: bool = True,
    region: str = None,
    work_type: str = None,  # For blended regional rates
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
        estimation_source: Where the estimate came from (benchmark, vendor_quote, etc.)
        source_details: Details about the source
        confidence: high, medium, low
        scale_factor: Manual adjustment factor
        apply_volume_discount: Auto-apply volume discounts based on quantity (default: True)
        region: Region code for labor cost adjustment (e.g., "us_east", "india", "uk")
        work_type: Work type for blended rates (e.g., "development", "migration")

    Returns:
        CostBuildUp with full calculation transparency, or None if anchor not found

    Example:
        # Per-user cost with volume discount and regional adjustment
        buildup = estimate_cost(
            anchor_key="license_microsoft",
            quantity=1500,
            region="india",  # 35% of US cost
            apply_volume_discount=True,  # Auto 25% discount at 1000+ users
            assumptions=["Offshore delivery", "Volume pricing"]
        )
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

    # Initialize assumptions list
    assumptions = assumptions or []

    # For fixed costs, quantity is always 1
    is_fixed = estimation_method in ("fixed", "fixed_by_size", "fixed_by_complexity", "fixed_by_gaps")
    if is_fixed:
        quantity = 1
        if size_tier:
            unit_label = f"{size_tier} organization"

    # Apply volume discount for per-unit costs
    volume_discount = 1.0
    if apply_volume_discount and not is_fixed and quantity > 1:
        # Map estimation method to volume curve type
        volume_type_map = {
            "per_user": "per_user",
            "per_user_annual": "per_user",
            "per_app": "per_app",
            "per_app_retired": "per_app",
            "per_site": "per_site",
            "per_site_annual": "per_site",
            "per_server": "per_server",
            "per_server_annual": "per_server",
            "per_vendor": "per_vendor",
        }
        volume_type = volume_type_map.get(estimation_method)
        if volume_type:
            volume_discount = get_volume_discount(volume_type, quantity)
            if volume_discount < 1.0:
                discount_pct = (1 - volume_discount) * 100
                assumptions.append(f"Volume discount: {discount_pct:.0f}% at {quantity:,} {unit_label}")

    # Apply regional multiplier
    regional_mult = 1.0
    if region:
        if work_type:
            # Use blended rate based on work type
            regional_mult = get_blended_rate_multiplier(work_type, onshore_region="us_east", offshore_region=region)
            assumptions.append(f"Blended rate ({work_type}): {regional_mult:.0%} of US base")
        else:
            regional_mult = get_regional_multiplier(region)
            if regional_mult != 1.0:
                region_display = region.replace("_", " ").title()
                assumptions.append(f"Regional adjustment ({region_display}): {regional_mult:.0%} of US base")

    # Combine all multipliers
    combined_multiplier = scale_factor * volume_discount * regional_mult

    # Calculate totals
    total_low = quantity * unit_cost_low * combined_multiplier
    total_high = quantity * unit_cost_high * combined_multiplier

    return CostBuildUp(
        anchor_key=anchor_key,
        anchor_name=anchor.get("name", anchor_key),
        estimation_method=estimation_method,
        quantity=quantity,
        unit_label=unit_label,
        unit_cost_low=unit_cost_low * volume_discount * regional_mult,  # Adjusted unit cost
        unit_cost_high=unit_cost_high * volume_discount * regional_mult,
        total_low=total_low,
        total_high=total_high,
        assumptions=assumptions,
        source_facts=source_facts or [],
        notes=notes,
        size_tier=size_tier or "",
        estimation_source=estimation_source,
        source_details=source_details,
        confidence=confidence,
        scale_factor=combined_multiplier  # Store combined multiplier
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


# =============================================================================
# VENDOR QUOTE IMPORT
# =============================================================================

import csv
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from datetime import datetime


@dataclass
class VendorQuote:
    """A vendor quote for cost estimation."""
    quote_id: str
    vendor_name: str
    activity_name: str
    description: str
    amount_low: float
    amount_high: float
    quantity: int = 1
    unit: str = "item"
    valid_until: str = ""  # ISO date
    quote_date: str = ""
    contact_name: str = ""
    contact_email: str = ""
    notes: str = ""
    tags: List[str] = field(default_factory=list)  # e.g., ["identity", "migration"]

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "VendorQuote":
        return cls(**data)

    def to_cost_buildup(self, **kwargs) -> CostBuildUp:
        """Convert vendor quote to CostBuildUp."""
        return estimate_from_vendor_quote(
            activity_name=self.activity_name,
            vendor_name=self.vendor_name,
            quoted_low=self.amount_low,
            quoted_high=self.amount_high,
            quantity=self.quantity,
            unit_label=self.unit,
            notes=self.notes,
            **kwargs
        )


class VendorQuoteStore:
    """
    Store and manage vendor quotes for cost estimation.

    Supports:
    - Import from CSV/JSON
    - Search by activity/vendor/tags
    - Export to file
    """

    def __init__(self):
        self.quotes: Dict[str, VendorQuote] = {}
        self._next_id = 1

    def add_quote(self, quote: VendorQuote) -> str:
        """Add a quote to the store."""
        if not quote.quote_id:
            quote.quote_id = f"VQ-{self._next_id:04d}"
            self._next_id += 1
        self.quotes[quote.quote_id] = quote
        return quote.quote_id

    def get_quote(self, quote_id: str) -> Optional[VendorQuote]:
        """Get a quote by ID."""
        return self.quotes.get(quote_id)

    def search_quotes(
        self,
        activity_pattern: str = None,
        vendor_name: str = None,
        tags: List[str] = None,
        min_amount: float = None,
        max_amount: float = None
    ) -> List[VendorQuote]:
        """Search quotes by various criteria."""
        results = []

        for quote in self.quotes.values():
            # Activity pattern match
            if activity_pattern:
                if activity_pattern.lower() not in quote.activity_name.lower():
                    continue

            # Vendor name match
            if vendor_name:
                if vendor_name.lower() not in quote.vendor_name.lower():
                    continue

            # Tags match (any tag)
            if tags:
                if not any(t in quote.tags for t in tags):
                    continue

            # Amount range
            if min_amount and quote.amount_high < min_amount:
                continue
            if max_amount and quote.amount_low > max_amount:
                continue

            results.append(quote)

        return results

    def import_from_csv(self, file_path: str) -> int:
        """
        Import vendor quotes from CSV file.

        Expected columns:
        - vendor_name (required)
        - activity_name (required)
        - amount_low (required)
        - amount_high (optional, defaults to amount_low * 1.2)
        - description
        - quantity
        - unit
        - valid_until
        - quote_date
        - contact_name
        - contact_email
        - notes
        - tags (comma-separated)

        Returns:
            Number of quotes imported
        """
        count = 0
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")

        with open(path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                try:
                    # Required fields
                    vendor_name = row.get('vendor_name', '').strip()
                    activity_name = row.get('activity_name', '').strip()
                    amount_low_str = row.get('amount_low', row.get('amount', '')).strip()

                    if not vendor_name or not activity_name or not amount_low_str:
                        logger.warning(f"Skipping row - missing required fields: {row}")
                        continue

                    # Parse amounts (handle currency symbols and commas)
                    amount_low = float(amount_low_str.replace('$', '').replace(',', ''))
                    amount_high_str = row.get('amount_high', '').strip()
                    if amount_high_str:
                        amount_high = float(amount_high_str.replace('$', '').replace(',', ''))
                    else:
                        amount_high = amount_low * 1.2  # Default 20% buffer

                    # Optional fields
                    quantity = int(row.get('quantity', '1') or '1')
                    unit = row.get('unit', 'item').strip() or 'item'
                    tags_str = row.get('tags', '').strip()
                    tags = [t.strip() for t in tags_str.split(',') if t.strip()]

                    quote = VendorQuote(
                        quote_id="",  # Will be auto-generated
                        vendor_name=vendor_name,
                        activity_name=activity_name,
                        description=row.get('description', '').strip(),
                        amount_low=amount_low,
                        amount_high=amount_high,
                        quantity=quantity,
                        unit=unit,
                        valid_until=row.get('valid_until', '').strip(),
                        quote_date=row.get('quote_date', '').strip(),
                        contact_name=row.get('contact_name', '').strip(),
                        contact_email=row.get('contact_email', '').strip(),
                        notes=row.get('notes', '').strip(),
                        tags=tags
                    )

                    self.add_quote(quote)
                    count += 1

                except Exception as e:
                    logger.warning(f"Error parsing row {row}: {e}")
                    continue

        logger.info(f"Imported {count} vendor quotes from {file_path}")
        return count

    def import_from_json(self, file_path: str) -> int:
        """Import vendor quotes from JSON file."""
        count = 0
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"JSON file not found: {file_path}")

        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        quotes_data = data if isinstance(data, list) else data.get('quotes', [])

        for item in quotes_data:
            try:
                quote = VendorQuote.from_dict(item)
                self.add_quote(quote)
                count += 1
            except Exception as e:
                logger.warning(f"Error parsing quote {item}: {e}")
                continue

        logger.info(f"Imported {count} vendor quotes from {file_path}")
        return count

    def export_to_json(self, file_path: str) -> int:
        """Export all quotes to JSON file."""
        path = Path(file_path)
        quotes_list = [q.to_dict() for q in self.quotes.values()]

        with open(path, 'w', encoding='utf-8') as f:
            json.dump({"quotes": quotes_list, "exported_at": datetime.now().isoformat()}, f, indent=2)

        return len(quotes_list)

    def export_to_csv(self, file_path: str) -> int:
        """Export all quotes to CSV file."""
        path = Path(file_path)

        if not self.quotes:
            return 0

        fieldnames = [
            'quote_id', 'vendor_name', 'activity_name', 'description',
            'amount_low', 'amount_high', 'quantity', 'unit',
            'valid_until', 'quote_date', 'contact_name', 'contact_email',
            'notes', 'tags'
        ]

        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for quote in self.quotes.values():
                row = quote.to_dict()
                row['tags'] = ','.join(row['tags'])  # Convert list to comma-separated
                writer.writerow(row)

        return len(self.quotes)

    def get_best_quote_for_activity(
        self,
        activity_pattern: str,
        prefer_recent: bool = True
    ) -> Optional[VendorQuote]:
        """
        Find the best matching quote for an activity.

        Args:
            activity_pattern: Pattern to match activity name
            prefer_recent: Prefer more recent quotes

        Returns:
            Best matching VendorQuote or None
        """
        matches = self.search_quotes(activity_pattern=activity_pattern)

        if not matches:
            return None

        if len(matches) == 1:
            return matches[0]

        # Sort by recency if we have dates
        if prefer_recent:
            dated_matches = [m for m in matches if m.quote_date]
            if dated_matches:
                dated_matches.sort(key=lambda q: q.quote_date, reverse=True)
                return dated_matches[0]

        # Otherwise return the one with lowest cost (conservative)
        return min(matches, key=lambda q: q.amount_low)


# Global vendor quote store
vendor_quote_store = VendorQuoteStore()


def import_vendor_quotes(file_path: str) -> int:
    """
    Import vendor quotes from file (CSV or JSON).

    Args:
        file_path: Path to CSV or JSON file

    Returns:
        Number of quotes imported
    """
    path = Path(file_path)

    if path.suffix.lower() == '.csv':
        return vendor_quote_store.import_from_csv(file_path)
    elif path.suffix.lower() == '.json':
        return vendor_quote_store.import_from_json(file_path)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}. Use .csv or .json")


def get_vendor_quote_estimate(
    activity_pattern: str,
    fallback_anchor: str = None,
    **kwargs
) -> Optional[CostBuildUp]:
    """
    Get cost estimate from vendor quotes, with optional benchmark fallback.

    Args:
        activity_pattern: Pattern to match activity name
        fallback_anchor: Anchor key to use if no vendor quote found
        **kwargs: Additional arguments for CostBuildUp

    Returns:
        CostBuildUp from vendor quote or fallback benchmark
    """
    quote = vendor_quote_store.get_best_quote_for_activity(activity_pattern)

    if quote:
        return quote.to_cost_buildup(**kwargs)

    if fallback_anchor:
        logger.info(f"No vendor quote for '{activity_pattern}', using benchmark: {fallback_anchor}")
        return estimate_cost(fallback_anchor, **kwargs)

    return None
