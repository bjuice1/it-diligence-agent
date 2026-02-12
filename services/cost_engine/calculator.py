"""
Cost Calculator

Driver-based cost calculations with scenario support.
Takes DealDrivers + CostModel → CostEstimate

Key features:
- Deterministic: same inputs = same outputs
- Traceable: shows which drivers fed which calculations
- Scenario-aware: upside/base/stress multipliers
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

from .drivers import DealDrivers, DriverConfidence, OwnershipType
from .models import (
    CostModel,
    CostEstimate,
    CostScenario,
    Complexity,
    WorkItemType,
    COST_MODELS,
    SCENARIO_MULTIPLIERS,
    get_model,
    get_deal_type_multiplier,
)

logger = logging.getLogger(__name__)


# =============================================================================
# COMPLEXITY ASSESSMENT
# =============================================================================

def assess_complexity(work_item_type: WorkItemType, drivers: DealDrivers) -> Complexity:
    """
    Determine complexity level based on driver values.

    This is heuristic-based. Each work item type has its own rules.
    """

    if work_item_type == WorkItemType.IDENTITY_SEPARATION:
        users = drivers.total_users or 0
        if users < 500:
            return Complexity.LOW
        elif users > 2000:
            return Complexity.HIGH
        return Complexity.MEDIUM

    elif work_item_type == WorkItemType.EMAIL_MIGRATION:
        users = drivers.total_users or 0
        if users < 300:
            return Complexity.LOW
        elif users > 1500:
            return Complexity.HIGH
        return Complexity.MEDIUM

    elif work_item_type == WorkItemType.WAN_SEPARATION:
        sites = drivers.sites or 0
        if sites <= 3:
            return Complexity.LOW
        elif sites > 10:
            return Complexity.HIGH
        return Complexity.MEDIUM

    elif work_item_type == WorkItemType.ENDPOINT_EDR:
        endpoints = drivers.endpoints or 0
        if endpoints < 200:
            return Complexity.LOW
        elif endpoints > 1000:
            return Complexity.HIGH
        return Complexity.MEDIUM

    elif work_item_type == WorkItemType.SECURITY_OPS:
        users = drivers.total_users or 0
        if users < 500:
            return Complexity.LOW
        elif users > 2000:
            return Complexity.HIGH
        return Complexity.MEDIUM

    elif work_item_type == WorkItemType.ERP_STANDALONE:
        erp = (drivers.erp_system or '').lower()
        if 'netsuite' in erp or 'quickbooks' in erp:
            return Complexity.LOW
        elif 'sap' in erp:
            return Complexity.HIGH
        return Complexity.MEDIUM

    elif work_item_type == WorkItemType.DC_HOSTING_EXIT:
        servers = drivers.servers or 0
        vms = drivers.vms or 0
        total = servers + vms
        if total < 20:
            return Complexity.LOW
        elif total > 100:
            return Complexity.HIGH
        return Complexity.MEDIUM

    elif work_item_type == WorkItemType.PMO_TRANSITION:
        sites = drivers.sites or 0
        users = drivers.total_users or 0
        if sites <= 3 and users < 500:
            return Complexity.LOW
        elif sites > 10 or users > 2000:
            return Complexity.HIGH
        return Complexity.MEDIUM

    return Complexity.MEDIUM


# =============================================================================
# COST CALCULATION
# =============================================================================

def calculate_cost(
    model: CostModel,
    drivers: DealDrivers,
    complexity_override: Optional[Complexity] = None,
    deal_type: str = "acquisition"
) -> CostEstimate:
    """
    Calculate cost estimate for a single work item type.

    Args:
        model: The cost model definition
        drivers: Deal drivers (extracted values)
        complexity_override: Optional complexity override (else auto-assessed)
        deal_type: One of ['acquisition', 'carveout', 'divestiture']

    Returns:
        CostEstimate with all three scenarios
    """

    # Determine complexity
    if complexity_override:
        complexity = complexity_override
    else:
        complexity = assess_complexity(model.work_item_type, drivers)

    complexity_multiplier = model.complexity_multipliers.get(
        complexity.value, 1.0
    )

    # Get driver values with defaults
    users = drivers.total_users or 0
    sites = drivers.sites or 1
    servers = (drivers.servers or 0) + (drivers.vms or 0)
    endpoints = drivers.endpoints or users  # Default to user count

    # Calculate base one-time cost
    base_cost = model.base_services_cost

    # Add per-unit costs
    if model.per_user_cost > 0:
        base_cost += model.per_user_cost * users

    if model.per_site_cost > 0:
        base_cost += model.per_site_cost * sites

    if model.per_server_cost > 0:
        base_cost += model.per_server_cost * servers

    if model.per_app_cost > 0:
        apps = drivers.total_apps or 0
        base_cost += model.per_app_cost * apps

    # Apply complexity
    adjusted_cost = base_cost * complexity_multiplier

    # Apply deal type multiplier
    # Map work item type to domain category
    domain_mapping = {
        WorkItemType.IDENTITY_SEPARATION: 'identity',
        WorkItemType.EMAIL_MIGRATION: 'application',
        WorkItemType.WAN_SEPARATION: 'network',
        WorkItemType.ENDPOINT_EDR: 'infrastructure',
        WorkItemType.SECURITY_OPS: 'cybersecurity',
        WorkItemType.ERP_STANDALONE: 'application',
        WorkItemType.DC_HOSTING_EXIT: 'infrastructure',
        WorkItemType.PMO_TRANSITION: 'org',
    }

    domain = domain_mapping.get(model.work_item_type, 'infrastructure')
    deal_multiplier = get_deal_type_multiplier(deal_type, domain)

    adjusted_cost = adjusted_cost * deal_multiplier

    # Calculate scenarios
    one_time_upside = adjusted_cost * SCENARIO_MULTIPLIERS[CostScenario.UPSIDE]
    one_time_base = adjusted_cost * SCENARIO_MULTIPLIERS[CostScenario.BASE]
    one_time_stress = adjusted_cost * SCENARIO_MULTIPLIERS[CostScenario.STRESS]

    # Calculate annual licenses
    annual_licenses = 0.0
    for lic in model.licenses:
        annual_licenses += lic.calculate(users=users, devices=endpoints)

    # Run rate delta (new licenses as ongoing cost)
    run_rate_delta = annual_licenses

    # Build cost breakdown
    breakdown = {
        'base_services': model.base_services_cost,
        'per_user': model.per_user_cost * users if model.per_user_cost else 0,
        'per_site': model.per_site_cost * sites if model.per_site_cost else 0,
        'per_server': model.per_server_cost * servers if model.per_server_cost else 0,
        'complexity_multiplier': complexity_multiplier,
        'deal_type_multiplier': deal_multiplier,
        'annual_licenses': annual_licenses,
    }

    # Build assumptions list
    assumptions = list(model.assumptions)

    # Add driver-based assumptions
    if users > 0:
        assumptions.append(f"User count: {users:,}")
    if sites > 1:
        assumptions.append(f"Site count: {sites}")
    if complexity != Complexity.MEDIUM:
        assumptions.append(f"Complexity: {complexity.value}")
    if deal_type != 'acquisition' and deal_multiplier != 1.0:
        assumptions.append(f"Deal type: {deal_type} ({deal_multiplier}x multiplier)")

    # Track drivers used
    drivers_used = {
        'total_users': users,
        'sites': sites,
        'servers': servers,
        'endpoints': endpoints,
    }

    return CostEstimate(
        work_item_type=model.work_item_type.value,
        display_name=model.display_name,
        tower=model.tower,
        entity=drivers.entity,  # Propagate entity from drivers
        one_time_upside=round(one_time_upside, -3),  # Round to nearest $1000
        one_time_base=round(one_time_base, -3),
        one_time_stress=round(one_time_stress, -3),
        annual_licenses=round(annual_licenses, -2),  # Round to nearest $100
        run_rate_delta=round(run_rate_delta, -2),
        cost_breakdown=breakdown,
        assumptions=assumptions,
        drivers_used=drivers_used,
        complexity=complexity.value,
        estimated_months=model.typical_months,
    )


def calculate_work_item_cost(
    work_item_type: str,
    drivers: DealDrivers,
    complexity_override: Optional[str] = None,
    deal_type: str = "acquisition"
) -> Optional[CostEstimate]:
    """
    Calculate cost for a work item type by name.

    Args:
        work_item_type: Work item type string (e.g., "identity_separation")
        drivers: Deal drivers
        complexity_override: Optional complexity string ("low", "medium", "high")
        deal_type: One of ['acquisition', 'carveout', 'divestiture']

    Returns:
        CostEstimate or None if model not found
    """
    model = get_model(work_item_type)
    if not model:
        logger.warning(f"No cost model found for: {work_item_type}")
        return None

    complexity = None
    if complexity_override:
        try:
            complexity = Complexity(complexity_override)
        except ValueError:
            logger.warning(f"Invalid complexity: {complexity_override}")

    return calculate_cost(model, drivers, complexity, deal_type)


# =============================================================================
# DEAL-LEVEL AGGREGATION
# =============================================================================

@dataclass
class DealCostSummary:
    """Aggregated cost summary for a deal."""
    deal_id: str

    # Entity dimension
    entity: str = "target"

    # Totals by scenario
    total_one_time_upside: float = 0.0
    total_one_time_base: float = 0.0
    total_one_time_stress: float = 0.0
    total_annual_licenses: float = 0.0
    total_run_rate_delta: float = 0.0
    total_tsa_costs: float = 0.0

    # By tower
    tower_costs: Dict[str, Dict] = field(default_factory=dict)

    # Individual estimates
    estimates: List[CostEstimate] = field(default_factory=list)

    # Top assumptions
    top_assumptions: List[str] = field(default_factory=list)

    # Missing/assumed drivers
    drivers_missing: List[str] = field(default_factory=list)
    drivers_assumed: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            'deal_id': self.deal_id,
            'entity': self.entity,
            'totals': {
                'one_time': {
                    'upside': self.total_one_time_upside,
                    'base': self.total_one_time_base,
                    'stress': self.total_one_time_stress,
                },
                'annual_licenses': self.total_annual_licenses,
                'run_rate_delta': self.total_run_rate_delta,
                'tsa_costs': self.total_tsa_costs,
            },
            'tower_costs': self.tower_costs,
            'estimates': [e.to_dict() for e in self.estimates],
            'top_assumptions': self.top_assumptions,
            'drivers_missing': self.drivers_missing,
            'drivers_assumed': self.drivers_assumed,
        }


def calculate_deal_costs(
    deal_id: str,
    drivers: DealDrivers,
    work_item_types: Optional[List[str]] = None,
    deal_type: str = "acquisition",
    inventory_store: Optional[Any] = None
) -> DealCostSummary:
    """
    Calculate costs for all applicable work items in a deal.

    Args:
        deal_id: The deal ID
        drivers: Deal drivers (entity is read from drivers.entity)
        work_item_types: Optional list of work item types to include
                        (if None, calculates all that have required drivers)
        deal_type: One of ['acquisition', 'carveout', 'divestiture']
        inventory_store: Optional InventoryStore for TSA cost calculation

    Returns:
        DealCostSummary with all costs aggregated (entity-aware)
    """
    summary = DealCostSummary(deal_id=deal_id, entity=drivers.entity)

    # Determine which work items to calculate
    if work_item_types:
        types_to_calc = work_item_types
    else:
        # Auto-detect based on available drivers
        types_to_calc = _determine_applicable_work_items(drivers)

    # Calculate each work item
    for wit_str in types_to_calc:
        estimate = calculate_work_item_cost(wit_str, drivers, deal_type=deal_type)
        if estimate:
            summary.estimates.append(estimate)

            # Add to totals
            summary.total_one_time_upside += estimate.one_time_upside
            summary.total_one_time_base += estimate.one_time_base
            summary.total_one_time_stress += estimate.one_time_stress
            summary.total_annual_licenses += estimate.annual_licenses
            summary.total_run_rate_delta += estimate.run_rate_delta

            # Add to tower costs
            tower = estimate.tower
            if tower not in summary.tower_costs:
                summary.tower_costs[tower] = {
                    'one_time_upside': 0,
                    'one_time_base': 0,
                    'one_time_stress': 0,
                    'annual_licenses': 0,
                    'items': [],
                }
            summary.tower_costs[tower]['one_time_upside'] += estimate.one_time_upside
            summary.tower_costs[tower]['one_time_base'] += estimate.one_time_base
            summary.tower_costs[tower]['one_time_stress'] += estimate.one_time_stress
            summary.tower_costs[tower]['annual_licenses'] += estimate.annual_licenses
            summary.tower_costs[tower]['items'].append(estimate.display_name)

    # Add TSA costs for carveout deals
    if deal_type == 'carveout' and inventory_store is not None:
        from .drivers import TSACostDriver
        tsa_driver = TSACostDriver()
        tsa_duration = drivers.tsa_months_assumed or 12
        tsa_cost = tsa_driver.estimate_monthly_tsa_cost(
            inventory_store=inventory_store,
            tsa_duration_months=tsa_duration
        )
        summary.total_tsa_costs = tsa_cost
        summary.top_assumptions.insert(0, f"TSA costs: ${tsa_cost:,.0f} over {tsa_duration} months")
        logger.info(f"Deal {deal_id} carveout TSA costs: ${tsa_cost:,.0f}")
    elif deal_type == 'carveout':
        logger.warning(f"Deal {deal_id} is carveout but no inventory_store provided - TSA costs not calculated")

    # Collect top assumptions
    all_assumptions = []
    for est in summary.estimates:
        all_assumptions.extend(est.assumptions)
    # Dedupe and take top 10
    seen = set()
    for a in all_assumptions:
        if a not in seen:
            seen.add(a)
            summary.top_assumptions.append(a)
            if len(summary.top_assumptions) >= 10:
                break

    # Track driver issues
    summary.drivers_missing = drivers.get_missing_drivers([
        'total_users', 'sites', 'endpoints'
    ])
    summary.drivers_assumed = drivers.get_assumed_drivers()

    logger.info(
        f"Deal {deal_id} costs for entity={drivers.entity}, deal_type={deal_type}: "
        f"${summary.total_one_time_base:,.0f} base, "
        f"${summary.total_annual_licenses:,.0f}/yr licenses, "
        f"{len(summary.estimates)} work items"
    )

    return summary


def _determine_applicable_work_items(drivers: DealDrivers) -> List[str]:
    """
    Determine which work items apply based on drivers.

    Returns list of work item type strings.
    """
    applicable = []

    # Identity - always needed in carveout/standalone
    if drivers.identity_owned_by == OwnershipType.PARENT or drivers.total_users:
        applicable.append(WorkItemType.IDENTITY_SEPARATION.value)

    # Email - usually goes with identity
    if drivers.total_users:
        applicable.append(WorkItemType.EMAIL_MIGRATION.value)

    # WAN - if multiple sites or parent-owned WAN
    if (drivers.sites and drivers.sites > 1) or drivers.wan_owned_by == OwnershipType.PARENT:
        applicable.append(WorkItemType.WAN_SEPARATION.value)

    # Endpoint/EDR - if endpoints exist
    if drivers.endpoints or drivers.total_users:
        applicable.append(WorkItemType.ENDPOINT_EDR.value)

    # Security Ops - if parent-owned SOC or significant user base
    if drivers.soc_owned_by == OwnershipType.PARENT or (drivers.total_users and drivers.total_users > 200):
        applicable.append(WorkItemType.SECURITY_OPS.value)

    # ERP - if ERP exists and is parent-owned
    if drivers.erp_system and drivers.erp_owned_by == OwnershipType.PARENT:
        applicable.append(WorkItemType.ERP_STANDALONE.value)

    # DC Exit - if parent-owned DC or significant servers
    if drivers.dc_owned_by == OwnershipType.PARENT or (drivers.servers and drivers.servers > 10):
        applicable.append(WorkItemType.DC_HOSTING_EXIT.value)

    # PMO - always if anything else is applicable
    if len(applicable) >= 2:
        applicable.append(WorkItemType.PMO_TRANSITION.value)

    return applicable


# =============================================================================
# VOLUME DISCOUNT INTEGRATION
# =============================================================================

# Volume discount curves from existing cost_model.py
VOLUME_DISCOUNT_CURVES = {
    'per_user': [
        (0, 1.0),
        (500, 0.95),
        (1000, 0.90),
        (2500, 0.85),
        (5000, 0.80),
        (10000, 0.75),
    ],
    'per_site': [
        (0, 1.0),
        (5, 0.95),
        (10, 0.90),
        (25, 0.85),
        (50, 0.80),
    ],
    'per_server': [
        (0, 1.0),
        (20, 0.95),
        (50, 0.90),
        (100, 0.85),
        (200, 0.80),
    ],
}


def get_volume_discount(quantity: int, discount_type: str) -> float:
    """
    Get volume discount factor for a quantity.

    Returns multiplier (e.g., 0.85 for 15% discount).
    """
    curve = VOLUME_DISCOUNT_CURVES.get(discount_type, [(0, 1.0)])

    for threshold, factor in reversed(curve):
        if quantity >= threshold:
            return factor

    return 1.0


def calculate_cost_with_volume_discount(
    model: CostModel,
    drivers: DealDrivers,
    apply_volume_discounts: bool = True,
    deal_type: str = "acquisition"
) -> CostEstimate:
    """
    Calculate cost with volume discounts applied.

    Same as calculate_cost but applies volume discount curves to per-unit costs.
    """
    estimate = calculate_cost(model, drivers, deal_type=deal_type)

    if not apply_volume_discounts:
        return estimate

    # Apply volume discounts to one-time costs
    users = drivers.total_users or 0
    sites = drivers.sites or 1
    servers = (drivers.servers or 0) + (drivers.vms or 0)

    user_discount = get_volume_discount(users, 'per_user')
    site_discount = get_volume_discount(sites, 'per_site')
    server_discount = get_volume_discount(servers, 'per_server')

    # Weighted average discount based on cost breakdown
    breakdown = estimate.cost_breakdown
    user_cost = breakdown.get('per_user', 0)
    site_cost = breakdown.get('per_site', 0)
    server_cost = breakdown.get('per_server', 0)
    base_cost = breakdown.get('base_services', 0)

    total_variable = user_cost + site_cost + server_cost
    if total_variable > 0:
        weighted_discount = (
            (user_cost * user_discount +
             site_cost * site_discount +
             server_cost * server_discount) / total_variable
        )
    else:
        weighted_discount = 1.0

    # Recalculate with discount
    discounted_variable = total_variable * weighted_discount
    discounted_total = base_cost + discounted_variable

    # Apply to all scenarios
    ratio = discounted_total / (base_cost + total_variable) if (base_cost + total_variable) > 0 else 1.0

    estimate.one_time_upside = round(estimate.one_time_upside * ratio, -3)
    estimate.one_time_base = round(estimate.one_time_base * ratio, -3)
    estimate.one_time_stress = round(estimate.one_time_stress * ratio, -3)

    # Add volume discount to assumptions
    if ratio < 0.99:
        discount_pct = (1 - ratio) * 100
        estimate.assumptions.append(f"Volume discount: {discount_pct:.0f}%")

    return estimate
