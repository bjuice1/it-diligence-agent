"""
Cost Center Blueprint

Finance-focused view of IT costs for deal modeling:
1. Run-Rate Costs (annual recurring)
2. One-Time Costs (integration/separation)
3. Synergy Opportunities
4. Cost Commentary & Insights

Designed for PE/M&A deal teams to quickly understand cost implications.
"""

import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple, Union
from dataclasses import dataclass, field
from flask import Blueprint, render_template, request, jsonify

logger = logging.getLogger(__name__)

costs_bp = Blueprint('costs', __name__, url_prefix='/costs')


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class CostLineItem:
    """Individual cost line item."""
    category: str
    name: str
    amount: float
    amount_low: float = 0.0
    amount_high: float = 0.0
    unit: str = "annual"  # annual, one-time, monthly
    confidence: str = "medium"  # high, medium, low
    source: str = ""  # Where this number came from
    notes: str = ""
    item_count: int = 0  # Number of items (apps, FTEs, etc.)


@dataclass
class CostCategory:
    """Category of costs with subtotals."""
    name: str
    display_name: str
    items: List[CostLineItem] = field(default_factory=list)
    total: float = 0.0
    total_low: float = 0.0
    total_high: float = 0.0
    icon: str = ""

    def calculate_totals(self):
        self.total = sum(item.amount for item in self.items)
        self.total_low = sum(item.amount_low or item.amount for item in self.items)
        self.total_high = sum(item.amount_high or item.amount for item in self.items)


@dataclass
class RunRateCosts:
    """Annual recurring costs."""
    headcount: CostCategory = None
    applications: CostCategory = None
    infrastructure: CostCategory = None
    vendors_msp: CostCategory = None
    total: float = 0.0

    def calculate_total(self):
        cats = [self.headcount, self.applications, self.infrastructure, self.vendors_msp]
        self.total = sum(c.total for c in cats if c)


@dataclass
class OneTimeCosts:
    """Integration/separation costs."""
    by_phase: Dict[str, CostCategory] = field(default_factory=dict)
    by_category: Dict[str, CostCategory] = field(default_factory=dict)
    total_low: float = 0.0
    total_mid: float = 0.0
    total_high: float = 0.0


@dataclass
class SynergyOpportunity:
    """Potential cost savings opportunity."""
    name: str
    category: str  # consolidation, optimization, renegotiation
    annual_savings_low: float
    annual_savings_high: float
    cost_to_achieve_low: float
    cost_to_achieve_high: float
    timeframe: str  # 6-12 months, 12-18 months, etc.
    confidence: str
    notes: str = ""
    affected_items: List[str] = field(default_factory=list)

    @property
    def net_benefit_low(self) -> float:
        """3-year net benefit (conservative)."""
        return (self.annual_savings_low * 3) - self.cost_to_achieve_high

    @property
    def net_benefit_high(self) -> float:
        """3-year net benefit (optimistic)."""
        return (self.annual_savings_high * 3) - self.cost_to_achieve_low


@dataclass
class SeparationCost:
    """Separation/standup cost for carveouts and divestitures.

    See: specs/deal-type-awareness/02-synergy-engine-conditional-logic.md
    """
    name: str
    category: str  # "standup", "tsa_service", "data_separation"
    setup_cost_low: float
    setup_cost_high: float
    tsa_required: bool
    tsa_duration_months: int
    tsa_monthly_cost: float
    timeframe: str
    criticality: str  # "critical", "high", "medium", "low"
    notes: str
    affected_systems: List[str] = field(default_factory=list)
    alternative_approaches: List[str] = field(default_factory=list)

    @property
    def total_cost_low(self) -> float:
        """Total cost including setup + TSA fees."""
        return self.setup_cost_low + (self.tsa_monthly_cost * self.tsa_duration_months)

    @property
    def total_cost_high(self) -> float:
        """Total cost including setup + TSA fees."""
        return self.setup_cost_high + (self.tsa_monthly_cost * self.tsa_duration_months)


@dataclass
class CostInsight:
    """Commentary/insight about costs."""
    category: str  # concern, opportunity, observation
    title: str
    description: str
    impact: str  # $X or X%
    priority: str  # high, medium, low
    related_costs: List[str] = field(default_factory=list)


@dataclass
class CostCenterData:
    """Complete cost center data.

    Note: synergies field can contain either SynergyOpportunity (acquisitions)
    or SeparationCost (carveouts/divestitures) objects.

    See: specs/deal-type-awareness/02-synergy-engine-conditional-logic.md
    """
    run_rate: RunRateCosts = None
    one_time: OneTimeCosts = None
    synergies: List[Union[SynergyOpportunity, SeparationCost]] = field(default_factory=list)
    insights: List[CostInsight] = field(default_factory=list)
    data_quality: Dict[str, str] = field(default_factory=dict)


# =============================================================================
# DATA GATHERING
# =============================================================================

def _gather_headcount_costs(entity: str = "target") -> CostCategory:
    """Gather headcount costs from organization analysis.

    Args:
        entity: Entity filter ("target", "buyer", or "all")

    Phase 2+: Database-first implementation using DealData.
    """
    from flask import session as flask_session
    from web.deal_data import get_deal_data
    from web.context import load_deal_context

    category = CostCategory(
        name="headcount",
        display_name="IT Headcount",
        icon="👥"
    )

    try:
        # Get current deal context
        current_deal_id = flask_session.get('current_deal_id')
        if not current_deal_id:
            return category

        load_deal_context(current_deal_id)
        data = get_deal_data()

        # Get organization facts from database
        org_facts_all = data.get_organization()

        # Filter by entity
        if entity == "all":
            org_facts = org_facts_all
        else:
            org_facts = [
                fact for fact in org_facts_all
                if getattr(fact, 'entity', None) == entity
            ]

        logger.info(f"Gathering headcount costs for entity={entity}: {len(org_facts)} org facts")

        # Group by role category
        role_costs = {}
        for fact in org_facts:
            details = getattr(fact, 'details', None) or {}
            role_cat = getattr(fact, 'category', None) or "other"

            # Extract cost info
            headcount = details.get('headcount', details.get('count', 1))
            if isinstance(headcount, str):
                try:
                    headcount = int(headcount.replace(',', ''))
                except:
                    headcount = 1

            total_cost = details.get('total_personnel_cost', details.get('total_cost', 0))
            if isinstance(total_cost, str):
                total_cost = float(total_cost.replace('$', '').replace(',', ''))

            if role_cat not in role_costs:
                role_costs[role_cat] = {'count': 0, 'cost': 0}
            role_costs[role_cat]['count'] += headcount
            role_costs[role_cat]['cost'] += total_cost

        # Create line items
        for role_cat, data_item in role_costs.items():
            if data_item['cost'] > 0:
                category.items.append(CostLineItem(
                    category="headcount",
                    name=role_cat.replace('_', ' ').title(),
                    amount=data_item['cost'],
                    unit="annual",
                    confidence="medium",
                    source="Organization analysis (Database)",
                    item_count=data_item['count']
                ))

    except Exception as e:
        logger.warning(f"Could not gather headcount costs: {e}")

    category.calculate_totals()
    return category


def _gather_application_costs(entity: str = "target") -> CostCategory:
    """Gather application costs from inventory."""
    category = CostCategory(
        name="applications",
        display_name="Application Licenses",
        icon="📱"
    )

    try:
        from web.blueprints.inventory import get_inventory_store
        inv_store = get_inventory_store()

        if len(inv_store) > 0:
            if entity == "all":
                apps = inv_store.get_items(inventory_type="application", status="active")
            else:
                apps = inv_store.get_items(inventory_type="application", entity=entity, status="active")

            # Group by criticality
            by_criticality = {'critical': [], 'high': [], 'medium': [], 'low': [], 'other': []}

            for app in apps:
                crit = str(app.criticality or '').lower()
                if 'critical' in crit:
                    by_criticality['critical'].append(app)
                elif 'high' in crit:
                    by_criticality['high'].append(app)
                elif 'medium' in crit:
                    by_criticality['medium'].append(app)
                elif 'low' in crit:
                    by_criticality['low'].append(app)
                else:
                    by_criticality['other'].append(app)

            # Create line items by criticality
            crit_display = {
                'critical': 'Critical Applications',
                'high': 'High Priority Applications',
                'medium': 'Medium Priority Applications',
                'low': 'Low Priority Applications',
                'other': 'Other Applications'
            }

            for crit, app_list in by_criticality.items():
                if app_list:
                    total_cost = sum(app.cost or 0 for app in app_list)
                    app_names = [app.name for app in app_list[:5]]
                    if len(app_list) > 5:
                        app_names.append(f"+{len(app_list) - 5} more")

                    category.items.append(CostLineItem(
                        category="applications",
                        name=crit_display[crit],
                        amount=total_cost,
                        unit="annual",
                        confidence="high",
                        source="Application Inventory",
                        notes=", ".join(app_names),
                        item_count=len(app_list)
                    ))

    except Exception as e:
        logger.warning(f"Could not gather application costs: {e}")

    category.calculate_totals()
    return category


def _gather_infrastructure_costs(entity: str = "target") -> CostCategory:
    """Gather infrastructure costs from inventory."""
    category = CostCategory(
        name="infrastructure",
        display_name="Infrastructure",
        icon="🏢"
    )

    try:
        from web.blueprints.inventory import get_inventory_store
        inv_store = get_inventory_store()

        if len(inv_store) > 0:
            if entity == "all":
                infra = inv_store.get_items(inventory_type="infrastructure", status="active")
            else:
                infra = inv_store.get_items(inventory_type="infrastructure", entity=entity, status="active")

            for item in infra:
                category.items.append(CostLineItem(
                    category="infrastructure",
                    name=item.name,
                    amount=item.cost or 0,
                    unit="annual",
                    confidence="medium",
                    source="Infrastructure Inventory",
                    notes=item.data.get('category', '')
                ))

    except Exception as e:
        logger.warning(f"Could not gather infrastructure costs: {e}")

    category.calculate_totals()
    return category


def _gather_one_time_costs(entity: str = "target") -> OneTimeCosts:
    """Gather one-time integration costs from work items and cost engine.

    Args:
        entity: Entity filter ("target", "buyer", or "all")

    Phase 2+: Database-first implementation using DealData.
    """
    from flask import session as flask_session
    from web.deal_data import get_deal_data
    from web.context import load_deal_context

    one_time = OneTimeCosts()

    # Cost range lookup: maps string keys to low/high dollar amounts
    # Includes both standard ranges and variations used in work items
    COST_RANGE_VALUES = {
        "under_25k": {"low": 0, "high": 25_000, "label": "<$25K"},
        "25k_to_100k": {"low": 25_000, "high": 100_000, "label": "$25K-$100K"},
        "100k_to_250k": {"low": 100_000, "high": 250_000, "label": "$100K-$250K"},
        "100k_to_500k": {"low": 100_000, "high": 500_000, "label": "$100K-$500K"},  # Combined range
        "250k_to_500k": {"low": 250_000, "high": 500_000, "label": "$250K-$500K"},
        "500k_to_1m": {"low": 500_000, "high": 1_000_000, "label": "$500K-$1M"},
        "over_1m": {"low": 1_000_000, "high": 2_500_000, "label": ">$1M"},
    }

    try:
        # Get current deal context
        current_deal_id = flask_session.get('current_deal_id')
        if not current_deal_id:
            return one_time

        load_deal_context(current_deal_id)
        data = get_deal_data()

        # Get work items from database
        work_items_all = data.get_work_items()

        # Filter by entity
        if entity == "all":
            work_items = work_items_all
        else:
            # Work items have entity field directly
            work_items = [
                wi for wi in work_items_all
                if getattr(wi, 'entity', None) == entity
            ]

        logger.info(f"Gathering one-time costs for entity={entity}: {len(work_items)} work items")

        # Group work items by phase
        phase_costs = {}
        category_costs = {}

        for wi in work_items:
            # Get cost estimate string (e.g., "25k_to_100k")
            cost_estimate_key = getattr(wi, 'cost_estimate', None) or getattr(wi, 'cost_estimate_range', None)
            phase = getattr(wi, 'phase', 'unknown') or 'unknown'
            domain = getattr(wi, 'domain', 'other') or 'other'

            # Convert string key to low/high amounts
            cost_range = COST_RANGE_VALUES.get(cost_estimate_key, {"low": 0, "high": 0})
            cost_low = cost_range["low"]
            cost_high = cost_range["high"]

            # Skip items with no cost
            if cost_low == 0 and cost_high == 0 and not cost_estimate_key:
                continue

            # Initialize phase category
            if phase not in phase_costs:
                phase_costs[phase] = CostCategory(
                    name=phase,
                    display_name=phase.replace('_', ' ').title(),
                    icon="📅"
                )

            # Initialize domain category
            if domain not in category_costs:
                category_costs[domain] = CostCategory(
                    name=domain,
                    display_name=domain.replace('_', ' ').title(),
                    icon="📁"
                )

            # Add to phase
            phase_costs[phase].items.append(CostLineItem(
                category=phase,
                name=getattr(wi, 'title', 'Unnamed work item'),
                amount=(cost_low + cost_high) / 2,
                amount_low=cost_low,
                amount_high=cost_high,
                unit="one-time",
                confidence=getattr(wi, 'confidence', 'medium') or 'medium',
                source=f"Work item ({cost_estimate_key})"
            ))

            # Add to domain
            category_costs[domain].items.append(CostLineItem(
                category=domain,
                name=getattr(wi, 'title', 'Unnamed work item'),
                amount=(cost_low + cost_high) / 2,
                amount_low=cost_low,
                amount_high=cost_high,
                unit="one-time",
                confidence=getattr(wi, 'confidence', 'medium') or 'medium',
                source=f"Work item ({cost_estimate_key})"
            ))

        # Calculate totals
        for phase, cat in phase_costs.items():
            cat.calculate_totals()
        for domain_name, cat in category_costs.items():
            cat.calculate_totals()

        one_time.by_phase = phase_costs
        one_time.by_category = category_costs

        # Calculate grand totals from phase costs (to avoid double-counting)
        all_items = []
        for cat in phase_costs.values():
            all_items.extend(cat.items)

        one_time.total_low = sum(i.amount_low for i in all_items)
        one_time.total_high = sum(i.amount_high for i in all_items)
        one_time.total_mid = (one_time.total_low + one_time.total_high) / 2

        logger.info(f"Gathered one-time costs: {len(all_items)} work items, ${one_time.total_low:,.0f} - ${one_time.total_high:,.0f}")

    except Exception as e:
        logger.warning(f"Could not gather one-time costs: {e}")
        import traceback
        traceback.print_exc()

    return one_time


def _get_current_deal_type() -> str:
    """
    Get deal_type for the current analysis session.

    See: specs/deal-type-awareness/02-synergy-engine-conditional-logic.md

    Returns:
        deal_type string ("acquisition", "carveout", or "divestiture")
        Defaults to "acquisition" if unable to determine
    """
    try:
        from flask import session as flask_session
        from web.context import load_deal_context

        # Try to get from session context first
        if 'deal_context' in flask_session:
            deal_type = flask_session['deal_context'].get('deal_type')
            if deal_type:
                return deal_type

        # Try to load from deal_context
        deal_context = load_deal_context()
        if deal_context and 'deal_type' in deal_context:
            return deal_context['deal_type']

        # Fallback: Try to get from database
        deal_id = flask_session.get('current_deal_id')
        if deal_id:
            from web.database import db, Deal
            deal = db.session.query(Deal).filter_by(id=deal_id).first()
            if deal and deal.deal_type:
                return deal.deal_type

        # Ultimate fallback
        logger.warning("Could not determine deal_type, defaulting to 'acquisition'")
        return 'acquisition'

    except Exception as e:
        logger.warning(f"Error getting deal_type: {e}, defaulting to 'acquisition'")
        return 'acquisition'


def _calculate_consolidation_synergies() -> List[SynergyOpportunity]:
    """
    Calculate consolidation synergies for acquisitions.

    Consolidation Model:
      - Eliminate smaller contract (100% of cost saved)
      - Renegotiate larger contract with volume discount (10-30% savings)
      - Cost to achieve: Migration labor (50-200% of smaller contract)

    See: specs/deal-type-awareness/02-synergy-engine-conditional-logic.md

    Returns:
        List of SynergyOpportunity objects for overlapping categories
    """
    synergies = []

    try:
        from web.blueprints.inventory import get_inventory_store
        inv_store = get_inventory_store()

        if len(inv_store) == 0:
            return synergies

        # Fetch buyer and target apps separately
        buyer_apps = inv_store.get_items(inventory_type="application", entity="buyer", status="active")
        target_apps = inv_store.get_items(inventory_type="application", entity="target", status="active")

        logger.info(f"Consolidation synergy analysis: {len(buyer_apps)} buyer apps vs {len(target_apps)} target apps")

        # Group apps by category for both entities
        buyer_by_category = {}
        for app in buyer_apps:
            cat = app.data.get('category', 'Other')
            if cat not in buyer_by_category:
                buyer_by_category[cat] = []
            buyer_by_category[cat].append(app)

        target_by_category = {}
        for app in target_apps:
            cat = app.data.get('category', 'Other')
            if cat not in target_by_category:
                target_by_category[cat] = []
            target_by_category[cat].append(app)

        # Find category overlaps (both buyer and target have apps in this category)
        overlapping_categories = set(buyer_by_category.keys()) & set(target_by_category.keys())

        logger.info(f"Found {len(overlapping_categories)} overlapping categories for consolidation")

        # Calculate consolidation synergies for each overlapping category
        for category in overlapping_categories:
            buyer_apps_in_cat = buyer_by_category[category]
            target_apps_in_cat = target_by_category[category]

            # Calculate total cost in this category
            buyer_cost = sum(app.cost or 0 for app in buyer_apps_in_cat)
            target_cost = sum(app.cost or 0 for app in target_apps_in_cat)
            combined_cost = buyer_cost + target_cost

            # Skip if combined cost is too low (no meaningful synergy)
            if combined_cost < 100_000:
                continue

            # Consolidation synergy calculation
            # Assumption: Consolidating to one platform saves smaller contract + renegotiation discount
            smaller_cost = min(buyer_cost, target_cost)
            larger_cost = max(buyer_cost, target_cost)

            # Savings model:
            # - Eliminate smaller contract entirely (100% of smaller)
            # - Renegotiate larger contract with volume discount (10-30% of larger)
            savings_low = smaller_cost + (larger_cost * 0.10)  # Conservative: 10% volume discount
            savings_high = smaller_cost + (larger_cost * 0.30)  # Optimistic: 30% volume discount

            # Cost to achieve (migration labor, data conversion, etc.)
            # Estimate based on complexity of migration
            # Simple rule: 50-200% of smaller contract cost
            cost_to_achieve_low = smaller_cost * 0.5
            cost_to_achieve_high = smaller_cost * 2.0

            # Timeframe (based on category)
            # Critical systems (ERP, CRM) take longer
            critical_categories = ['crm', 'erp', 'finance', 'hr', 'hris']
            if category.lower() in critical_categories:
                timeframe = "12-18 months"
                confidence = "medium"
            else:
                timeframe = "6-12 months"
                confidence = "high"

            # Create synergy opportunity
            synergies.append(SynergyOpportunity(
                name=f"{category.title()} Platform Consolidation",
                category="consolidation",
                annual_savings_low=round(savings_low, -3),  # Round to nearest $1K
                annual_savings_high=round(savings_high, -3),
                cost_to_achieve_low=round(cost_to_achieve_low, -3),
                cost_to_achieve_high=round(cost_to_achieve_high, -3),
                timeframe=timeframe,
                confidence=confidence,
                notes=f"Consolidate {len(buyer_apps_in_cat)} buyer + {len(target_apps_in_cat)} target apps in {category}",
                affected_items=[app.name for app in (buyer_apps_in_cat + target_apps_in_cat)]
            ))

        logger.info(f"Identified {len(synergies)} consolidation synergies")

    except Exception as e:
        logger.warning(f"Could not calculate consolidation synergies: {e}")

    return synergies


def _calculate_separation_costs() -> List[SeparationCost]:
    """
    Calculate separation costs for carveouts and divestitures.

    Separation Model:
      - Identify systems target currently shares with parent
      - Calculate cost to build/buy standalone alternative
      - Estimate TSA duration and monthly cost

    See: specs/deal-type-awareness/02-synergy-engine-conditional-logic.md

    Returns:
        List of SeparationCost objects for standup requirements
    """
    separation_costs = []

    try:
        from web.blueprints.inventory import get_inventory_store
        inv_store = get_inventory_store()

        if len(inv_store) == 0:
            return separation_costs

        # Get target's inventory (what needs to become standalone)
        target_apps = inv_store.get_items(inventory_type="application", entity="target", status="active")

        logger.info(f"Separation cost analysis: {len(target_apps)} target apps to evaluate")

        # Critical systems that typically need standup for carveouts
        critical_system_configs = {
            'erp': {
                'priority': 'critical',
                'base_cost_range': (1_000_000, 5_000_000),
                'tsa_duration': 18,
                'timeframe': '12-18 months'
            },
            'crm': {
                'priority': 'high',
                'base_cost_range': (200_000, 1_000_000),
                'tsa_duration': 12,
                'timeframe': '6-12 months'
            },
            'hcm': {
                'priority': 'critical',
                'base_cost_range': (500_000, 2_000_000),
                'tsa_duration': 18,
                'timeframe': '12-18 months'
            },
            'finance': {
                'priority': 'critical',
                'base_cost_range': (300_000, 1_500_000),
                'tsa_duration': 18,
                'timeframe': '12-18 months'
            },
            'email': {
                'priority': 'high',
                'base_cost_range': (50_000, 300_000),
                'tsa_duration': 6,
                'timeframe': '3-6 months'
            }
        }

        # Group target apps by category
        target_by_category = {}
        for app in target_apps:
            cat = app.data.get('category', 'Other')
            if cat not in target_by_category:
                target_by_category[cat] = []
            target_by_category[cat].append(app)

        # For each critical category, determine if standup needed
        for category, config in critical_system_configs.items():
            if category in target_by_category:
                # Target has systems in this category - check if standalone
                apps_in_cat = target_by_category[category]

                # Heuristic: If target has dedicated instance, assume standalone
                # Otherwise, assume shared with parent and needs standup
                is_shared = any('shared' in app.data.get('notes', '').lower() or
                                'parent' in app.data.get('notes', '').lower()
                                for app in apps_in_cat)

                if is_shared or len(apps_in_cat) == 0:
                    # Needs standup
                    setup_cost_low, setup_cost_high = config['base_cost_range']
                    tsa_duration = config['tsa_duration']

                    # Estimate TSA monthly cost (10-15% of annual license cost)
                    current_cost = sum(app.cost or 0 for app in apps_in_cat)
                    tsa_monthly = (current_cost * 0.125) / 12 if current_cost > 0 else 10_000

                    separation_costs.append(SeparationCost(
                        name=f"Standalone {category.upper()} Implementation",
                        category="standup",
                        setup_cost_low=setup_cost_low,
                        setup_cost_high=setup_cost_high,
                        tsa_required=True,
                        tsa_duration_months=tsa_duration,
                        tsa_monthly_cost=tsa_monthly,
                        timeframe=config['timeframe'],
                        criticality=config['priority'],
                        notes=f"Target currently shares {category.upper()} with parent. Requires standalone instance and {tsa_duration}-month TSA.",
                        affected_systems=[app.name for app in apps_in_cat] if apps_in_cat else [f"Parent {category.upper()} (to be exited)"],
                        alternative_approaches=["Buy new SaaS instance", "Extend TSA duration", "Acquire via bolt-on"]
                    ))
            else:
                # Target doesn't have this category at all - likely relies on parent
                setup_cost_low, setup_cost_high = config['base_cost_range']
                tsa_duration = config['tsa_duration']
                tsa_monthly = 15_000  # Default estimate

                separation_costs.append(SeparationCost(
                    name=f"Standalone {category.upper()} Implementation",
                    category="standup",
                    setup_cost_low=setup_cost_low,
                    setup_cost_high=setup_cost_high,
                    tsa_required=True,
                    tsa_duration_months=tsa_duration,
                    tsa_monthly_cost=tsa_monthly,
                    timeframe=config['timeframe'],
                    criticality=config['priority'],
                    notes=f"No {category.upper()} found in target inventory. Likely relies on parent system. Standalone implementation required.",
                    affected_systems=[f"Parent {category.upper()} (to be exited)"],
                    alternative_approaches=["Buy SaaS solution", "Build custom", "Extend TSA", "Outsource to MSP"]
                ))

        # Sort by total cost (setup + TSA fees)
        separation_costs.sort(key=lambda x: x.total_cost_high, reverse=True)

        logger.info(f"Identified {len(separation_costs)} separation/standup requirements")

    except Exception as e:
        logger.warning(f"Could not calculate separation costs: {e}")

    return separation_costs


def _identify_synergies(deal_type: str = "acquisition") -> List[Union[SynergyOpportunity, SeparationCost]]:
    """
    Identify cost optimization opportunities based on deal type.

    For acquisitions: Calculates consolidation synergies (eliminate duplicate systems)
    For carveouts/divestitures: Calculates separation costs (standup standalone capabilities)

    See: specs/deal-type-awareness/02-synergy-engine-conditional-logic.md
    Also see: Doc 01 (deal-type-architecture.md) for entity semantics by deal type

    Args:
        deal_type: Deal structure - "acquisition", "carveout", or "divestiture"
                   Defaults to "acquisition" for backward compatibility

    Returns:
        List of SynergyOpportunity (acquisitions) or SeparationCost (carveouts)
        Empty list if inventory unavailable or no opportunities found

    Raises:
        ValueError: If deal_type is invalid (logs warning and defaults to acquisition)

    Example:
        # Acquisition: Returns consolidation synergies
        synergies = _identify_synergies("acquisition")
        # → [SynergyOpportunity(name="CRM Consolidation", annual_savings_low=380000, ...)]

        # Carveout: Returns separation costs
        costs = _identify_synergies("carveout")
        # → [SeparationCost(name="Standalone CRM", setup_cost_low=500000, ...)]
    """
    # Validate and normalize deal_type
    allowed_types = ['acquisition', 'carveout', 'divestiture', 'bolt_on', 'platform', 'spinoff', 'spin-off']
    if deal_type not in allowed_types:
        logger.warning(f"Unknown deal_type '{deal_type}', defaulting to 'acquisition'")
        deal_type = 'acquisition'

    # Normalize aliases to canonical values
    if deal_type in ['bolt_on', 'platform']:
        deal_type = 'acquisition'
    elif deal_type in ['spinoff', 'spin-off']:
        deal_type = 'carveout'

    logger.info(f"Analyzing synergies/costs for deal_type='{deal_type}'")

    # Branch based on deal type
    if deal_type in ['carveout', 'divestiture']:
        # Carveouts and divestitures: Calculate separation costs
        return _calculate_separation_costs()
    else:
        # Acquisitions: Calculate consolidation synergies
        return _calculate_consolidation_synergies()


def _generate_insights(run_rate: RunRateCosts, one_time: OneTimeCosts, synergies: List[Union[SynergyOpportunity, SeparationCost]]) -> List[CostInsight]:
    """Generate cost insights and commentary.

    See: specs/deal-type-awareness/02-synergy-engine-conditional-logic.md

    Args:
        synergies: Can contain either SynergyOpportunity or SeparationCost objects
    """
    insights = []

    # Headcount to non-headcount ratio
    if run_rate.headcount and run_rate.applications:
        hc_cost = run_rate.headcount.total
        app_cost = run_rate.applications.total
        total = hc_cost + app_cost

        if total > 0:
            hc_pct = (hc_cost / total) * 100

            if hc_pct > 70:
                insights.append(CostInsight(
                    category="observation",
                    title="Headcount-Heavy Cost Structure",
                    description=f"IT costs are {hc_pct:.0f}% headcount vs {100-hc_pct:.0f}% non-headcount. This is above typical ratios (50-60% headcount).",
                    impact=f"${hc_cost:,.0f} in personnel costs",
                    priority="medium",
                    related_costs=["headcount"]
                ))
            elif hc_pct < 40:
                insights.append(CostInsight(
                    category="observation",
                    title="High Non-Headcount Costs",
                    description=f"IT costs are {100-hc_pct:.0f}% non-headcount (applications, infrastructure). Review for optimization opportunities.",
                    impact=f"${app_cost:,.0f} in application costs",
                    priority="medium",
                    related_costs=["applications"]
                ))

    # Large one-time costs
    if one_time.total_high > 5_000_000:
        insights.append(CostInsight(
            category="concern",
            title="Significant Integration Investment Required",
            description=f"One-time integration costs estimated at ${one_time.total_low:,.0f} - ${one_time.total_high:,.0f}. Budget accordingly.",
            impact=f"${one_time.total_mid:,.0f} midpoint",
            priority="high",
            related_costs=["integration"]
        ))

    # Synergy opportunities or separation costs (depends on deal type)
    if synergies:
        # Check if we have SynergyOpportunity or SeparationCost objects
        if isinstance(synergies[0], SynergyOpportunity):
            # Acquisition deal - show synergy opportunities
            total_synergy = sum(s.annual_savings_high for s in synergies)
            if total_synergy > 500_000:
                insights.append(CostInsight(
                    category="opportunity",
                    title="Material Synergy Potential Identified",
                    description=f"{len(synergies)} consolidation opportunities identified with potential annual savings.",
                    impact=f"${total_synergy:,.0f}/year potential",
                    priority="high",
                    related_costs=["synergies"]
                ))
        elif isinstance(synergies[0], SeparationCost):
            # Carveout/divestiture - show separation costs
            total_separation = sum(s.total_cost_high for s in synergies)
            if total_separation > 500_000:
                insights.append(CostInsight(
                    category="concern",
                    title="Significant Separation Costs Identified",
                    description=f"{len(synergies)} standalone systems required for carveout. Includes setup costs and TSA fees.",
                    impact=f"${total_separation:,.0f} total cost",
                    priority="high",
                    related_costs=["separation"]
                ))

    return insights


def _quality_level(value: float, thresholds: List[float]) -> str:
    """Determine quality level based on value and thresholds.

    Args:
        value: Numeric value (cost, count, etc.)
        thresholds: [low_threshold, medium_threshold, high_threshold]

    Returns:
        Quality level string
    """
    if value == 0:
        return "none"
    elif value < thresholds[0]:
        return "low"
    elif value < thresholds[1]:
        return "medium"
    elif value < thresholds[2]:
        return "high"
    else:
        return "very_high"


def _assess_data_quality_per_entity(
    run_rate: RunRateCosts,
    one_time: OneTimeCosts,
    entity: str
) -> Dict[str, Any]:
    """Assess data quality per entity.

    Args:
        run_rate: RunRateCosts object
        one_time: OneTimeCosts object
        entity: Entity filter ("target", "buyer", or "all")

    Returns:
        Dict with quality scores per domain and entity
    """

    quality = {}

    # Headcount quality
    headcount_total = run_rate.headcount.total if run_rate.headcount else 0
    quality["headcount"] = {
        "overall": _quality_level(headcount_total, thresholds=[100_000, 500_000, 1_000_000]),
        "note": f"${headcount_total:,.0f} in headcount costs"
    }

    # Applications quality
    apps_total = run_rate.applications.total if run_rate.applications else 0
    apps_count = len(run_rate.applications.items) if run_rate.applications else 0
    quality["applications"] = {
        "overall": _quality_level(apps_total, thresholds=[50_000, 500_000, 2_000_000]),
        "note": f"{apps_count} applications, ${apps_total:,.0f}"
    }

    # Infrastructure quality
    infra_total = run_rate.infrastructure.total if run_rate.infrastructure else 0
    infra_count = len(run_rate.infrastructure.items) if run_rate.infrastructure else 0
    quality["infrastructure"] = {
        "overall": _quality_level(infra_total, thresholds=[10_000, 100_000, 500_000]),
        "note": f"{infra_count} infrastructure items, ${infra_total:,.0f}"
    }

    # One-time costs quality
    one_time_mid = one_time.total_mid if one_time else 0
    quality["one_time"] = {
        "overall": _quality_level(one_time_mid, thresholds=[100_000, 500_000, 2_000_000]),
        "note": f"${one_time_mid:,.0f} in integration costs"
    }

    # Entity filter status
    if entity == "all":
        quality["entity_filter"] = "Not applicable (showing all entities)"
    else:
        quality["entity_filter"] = f"Filtered to {entity} entity"

    return quality


def build_cost_center_data(entity: str = "target") -> CostCenterData:
    """Build complete cost center data from all sources.

    See: specs/deal-type-awareness/02-synergy-engine-conditional-logic.md

    Args:
        entity: Entity filter ("target", "buyer", or "all")
    """

    # Fetch deal_type from current deal (Doc 02: Synergy Engine Conditional Logic)
    deal_type = _get_current_deal_type()

    # Gather run-rate costs
    run_rate = RunRateCosts(
        headcount=_gather_headcount_costs(entity=entity),
        applications=_gather_application_costs(entity=entity),
        infrastructure=_gather_infrastructure_costs(entity=entity),
        vendors_msp=CostCategory(name="vendors_msp", display_name="Vendors & MSP", icon="🤝")
    )
    run_rate.calculate_total()

    # Gather one-time costs
    one_time = _gather_one_time_costs(entity=entity)

    # Identify synergies (pass deal_type to enable conditional branching)
    synergies = _identify_synergies(deal_type=deal_type)

    # Generate insights
    insights = _generate_insights(run_rate, one_time, synergies)

    # Assess data quality (entity-aware)
    data_quality = _assess_data_quality_per_entity(run_rate, one_time, entity)

    return CostCenterData(
        run_rate=run_rate,
        one_time=one_time,
        synergies=synergies,
        insights=insights,
        data_quality=data_quality
    )


# =============================================================================
# ROUTES
# =============================================================================

@costs_bp.route('/')
def cost_center():
    """Main cost center view."""
    # Support entity filtering via query parameter
    entity = request.args.get('entity', 'target')
    if entity not in ('target', 'buyer', 'all'):
        entity = 'target'

    data = build_cost_center_data(entity=entity)

    return render_template('costs/center.html',
        data=data,
        run_rate=data.run_rate,
        one_time=data.one_time,
        synergies=data.synergies,
        insights=data.insights,
        data_quality=data.data_quality,
        current_entity=entity
    )


@costs_bp.route('/summary')
@costs_bp.route('/summary/<deal_id>')
def cost_summary_page(deal_id: str = None):
    """Cost summary page with scenario-based estimates."""
    from flask import session as flask_session
    from services.cost_engine import get_effective_drivers, calculate_deal_costs
    from web.database import Fact
    from stores.fact_store import FactStore

    # Get deal ID from URL or session
    if not deal_id:
        deal_id = flask_session.get('current_deal_id')

    if not deal_id:
        return render_template('costs/summary.html',
            summary=None,
            deal_id='',
            error='No deal selected'
        )

    try:
        # Load facts directly from database (bypasses analysis run requirement)
        db_facts = Fact.query.filter_by(deal_id=deal_id).all()

        if not db_facts:
            return render_template('costs/summary.html',
                summary=None,
                deal_id=deal_id,
                error=f'No facts found for deal {deal_id}'
            )

        # Build a FactStore from DB facts
        fact_store = FactStore(deal_id=deal_id)
        for f in db_facts:
            fact_store.add_fact(
                domain=f.domain,
                category=f.category or '',
                item=f.item,
                details=f.details or {},
                status=f.status or 'documented',
                evidence=f.evidence or {},
                entity=f.entity or 'target',
                source_document=f.source_document or '',
            )

        # Get effective drivers
        driver_result = get_effective_drivers(deal_id, fact_store)
        drivers = driver_result.drivers

        # Calculate deal costs
        summary = calculate_deal_costs(deal_id, drivers)

        return render_template('costs/summary.html',
            summary=summary,
            deal_id=deal_id,
        )

    except Exception as e:
        logger.error(f"Error loading cost summary: {e}")
        import traceback
        traceback.print_exc()
        return render_template('costs/summary.html',
            summary=None,
            deal_id=deal_id,
            error=str(e)
        )


@costs_bp.route('/drivers')
@costs_bp.route('/drivers/<deal_id>')
def drivers_page(deal_id: str = None):
    """Driver view/edit page."""
    from flask import session as flask_session
    from web.database import DriverOverride, Fact
    from services.cost_engine import get_effective_drivers
    from stores.fact_store import FactStore

    # Get deal ID from URL or session
    if not deal_id:
        deal_id = flask_session.get('current_deal_id')

    if not deal_id:
        return render_template('costs/drivers.html',
            drivers=[],
            summary={'total_extracted': 0, 'total_assumed': 0, 'total_overridden': 0},
            shared_with_parent=[],
            deal_id='',
            error='No deal selected'
        )

    try:
        # Load facts directly from database (bypasses analysis run requirement)
        db_facts = Fact.query.filter_by(deal_id=deal_id).all()

        # Build a FactStore from DB facts
        fact_store = FactStore(deal_id=deal_id)
        for f in db_facts:
            fact_store.add_fact(
                domain=f.domain,
                category=f.category or '',
                item=f.item,
                details=f.details or {},
                status=f.status or 'documented',
                evidence=f.evidence or {},
                entity=f.entity or 'target',
                source_document=f.source_document or '',
            )

        # Get effective drivers
        result = get_effective_drivers(deal_id, fact_store)
        drivers = result.drivers

        # Build drivers list for template
        drivers_list = []
        for field_name in drivers.__dataclass_fields__:
            if field_name in ('sources', 'shared_with_parent'):
                continue

            value = getattr(drivers, field_name)
            source_info = drivers.sources.get(field_name)

            # Handle enum values
            if hasattr(value, 'value'):
                display_value = value.value
            else:
                display_value = value

            # Check for override
            override = DriverOverride.query.filter_by(
                deal_id=deal_id,
                driver_name=field_name,
                active=True
            ).first()

            drivers_list.append({
                'name': field_name,
                'value': display_value,
                'source_type': source_info.extraction_method if source_info else 'not_found',
                'source_fact_id': source_info.fact_id if source_info else None,
                'confidence': source_info.confidence.value if source_info else 'unknown',
                'is_overridden': override is not None,
                'extracted_value': override.extracted_value if override else display_value,
                'override_reason': override.reason if override else None,
            })

        # Count summary
        total_overridden = sum(1 for d in drivers_list if d['is_overridden'])
        total_assumed = sum(1 for d in drivers_list
                          if d['confidence'] == 'low' and d['value'] is not None)

        return render_template('costs/drivers.html',
            drivers=drivers_list,
            summary={
                'total_extracted': result.drivers_extracted,
                'total_assumed': result.drivers_assumed,
                'total_overridden': total_overridden,
            },
            shared_with_parent=drivers.shared_with_parent,
            deal_id=deal_id,
        )

    except Exception as e:
        logger.error(f"Error loading drivers page: {e}")
        import traceback
        traceback.print_exc()
        return render_template('costs/drivers.html',
            drivers=[],
            summary={'total_extracted': 0, 'total_assumed': 0, 'total_overridden': 0},
            shared_with_parent=[],
            deal_id=deal_id,
            error=str(e)
        )


@costs_bp.route('/api/summary')
def api_summary():
    """API endpoint for cost summary."""
    # Support entity filtering via query parameter
    entity = request.args.get('entity', 'target')
    if entity not in ('target', 'buyer', 'all'):
        entity = 'target'

    data = build_cost_center_data(entity=entity)

    return jsonify({
        'entity': entity,
        'run_rate': {
            'total': data.run_rate.total,
            'headcount': data.run_rate.headcount.total if data.run_rate.headcount else 0,
            'applications': data.run_rate.applications.total if data.run_rate.applications else 0,
            'infrastructure': data.run_rate.infrastructure.total if data.run_rate.infrastructure else 0,
        },
        'one_time': {
            'low': data.one_time.total_low,
            'mid': data.one_time.total_mid,
            'high': data.one_time.total_high,
        },
        'synergies': {
            'count': len(data.synergies),
            'total_potential': sum(s.annual_savings_high for s in data.synergies),
        },
        'insights_count': len(data.insights),
    })


# =============================================================================
# DRIVER API ENDPOINTS
# =============================================================================

@costs_bp.route('/api/drivers/<deal_id>')
def api_get_drivers(deal_id: str):
    """Get extracted drivers for a deal with any overrides applied.

    Returns the effective driver values (extracted + overrides merged).
    """
    from web.database import db, DriverOverride
    from services.cost_engine import get_effective_drivers
    from web.deal_data import get_deal_data
    from web.context import load_deal_context

    try:
        # Load deal context and get fact store
        load_deal_context(deal_id)
        data = get_deal_data()

        # Get fact store from deal data
        fact_store = data.fact_store if hasattr(data, 'fact_store') else None

        # Get effective drivers (extracted + overrides)
        result = get_effective_drivers(deal_id, fact_store)

        # Format response
        drivers_list = []
        drivers = result.drivers

        # Convert dataclass to dict with source info
        for field_name in drivers.__dataclass_fields__:
            if field_name in ('sources', 'shared_with_parent'):
                continue

            value = getattr(drivers, field_name)
            source_info = drivers.sources.get(field_name)

            # Check for override
            override = DriverOverride.query.filter_by(
                deal_id=deal_id,
                driver_name=field_name,
                active=True
            ).first()

            drivers_list.append({
                'name': field_name,
                'value': value,
                'source_type': source_info.extraction_method if source_info else 'not_found',
                'source_fact_id': source_info.fact_id if source_info else None,
                'confidence': source_info.confidence.value if source_info else 'unknown',
                'is_overridden': override is not None,
                'extracted_value': override.extracted_value if override else value,
                'override_reason': override.reason if override else None,
            })

        # Add shared_with_parent as special entry
        drivers_list.append({
            'name': 'shared_with_parent',
            'value': drivers.shared_with_parent,
            'source_type': 'derived',
            'source_fact_id': None,
            'confidence': 'medium',
            'is_overridden': False,
            'extracted_value': drivers.shared_with_parent,
            'override_reason': None,
        })

        return jsonify({
            'success': True,
            'deal_id': deal_id,
            'drivers': drivers_list,
            'summary': {
                'total_extracted': result.extracted_count,
                'total_assumed': result.assumed_count,
                'total_overridden': sum(1 for d in drivers_list if d['is_overridden']),
            }
        })

    except Exception as e:
        logger.error(f"Error getting drivers for deal {deal_id}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@costs_bp.route('/api/drivers/<deal_id>/override', methods=['POST'])
def api_override_driver(deal_id: str):
    """Create or update a driver override.

    Request body:
    {
        "driver_name": "total_users",
        "override_value": 1200,
        "reason": "Confirmed with management - 850 was old number"
    }
    """
    from flask_login import current_user
    from web.database import db, DriverOverride

    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        driver_name = data.get('driver_name')
        override_value = data.get('override_value')
        reason = data.get('reason', '')
        extracted_value = data.get('extracted_value')  # Optional - what was extracted

        if not driver_name:
            return jsonify({'success': False, 'error': 'driver_name is required'}), 400

        if override_value is None:
            return jsonify({'success': False, 'error': 'override_value is required'}), 400

        # Check if override already exists (upsert)
        existing = DriverOverride.query.filter_by(
            deal_id=deal_id,
            driver_name=driver_name
        ).first()

        if existing:
            # Update existing override
            existing.override_value = override_value
            existing.reason = reason
            existing.active = True
            if extracted_value is not None:
                existing.extracted_value = extracted_value
            override = existing
        else:
            # Create new override
            override = DriverOverride(
                deal_id=deal_id,
                driver_name=driver_name,
                extracted_value=extracted_value,
                override_value=override_value,
                reason=reason,
                created_by=current_user.id if current_user and current_user.is_authenticated else None
            )
            db.session.add(override)

        db.session.commit()

        return jsonify({
            'success': True,
            'override': override.to_dict()
        })

    except Exception as e:
        logger.error(f"Error creating driver override: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@costs_bp.route('/api/drivers/<deal_id>/override/<driver_name>', methods=['DELETE'])
def api_delete_driver_override(deal_id: str, driver_name: str):
    """Delete (deactivate) a driver override, reverting to extracted value."""
    from web.database import db, DriverOverride

    try:
        override = DriverOverride.query.filter_by(
            deal_id=deal_id,
            driver_name=driver_name,
            active=True
        ).first()

        if not override:
            return jsonify({
                'success': False,
                'error': f'No active override found for driver {driver_name}'
            }), 404

        # Soft delete - mark as inactive
        override.active = False
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Override for {driver_name} removed'
        })

    except Exception as e:
        logger.error(f"Error deleting driver override: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@costs_bp.route('/api/drivers/<deal_id>/export')
def api_export_drivers_csv(deal_id: str):
    """Export drivers to CSV for deal model import."""
    import csv
    import io
    from flask import Response
    from services.cost_engine import get_effective_drivers
    from web.deal_data import get_deal_data
    from web.context import load_deal_context
    from web.database import DriverOverride

    try:
        # Load deal context
        load_deal_context(deal_id)
        data = get_deal_data()
        fact_store = data.fact_store if hasattr(data, 'fact_store') else None

        # Get effective drivers
        result = get_effective_drivers(deal_id, fact_store)
        drivers = result.drivers

        # Build CSV
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['driver', 'value', 'source_type', 'source_id', 'confidence', 'overridden'])

        for field_name in drivers.__dataclass_fields__:
            if field_name in ('sources', 'shared_with_parent'):
                continue

            value = getattr(drivers, field_name)
            source_info = drivers.sources.get(field_name)

            # Check for override
            override = DriverOverride.query.filter_by(
                deal_id=deal_id,
                driver_name=field_name,
                active=True
            ).first()

            writer.writerow([
                field_name,
                value if value is not None else '',
                source_info.extraction_method if source_info else 'not_found',
                source_info.fact_id if source_info else '',
                source_info.confidence.value if source_info else 'unknown',
                'true' if override else 'false'
            ])

        # Add shared_with_parent
        writer.writerow([
            'shared_with_parent',
            ','.join(drivers.shared_with_parent) if drivers.shared_with_parent else '',
            'derived',
            '',
            'medium',
            'false'
        ])

        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=drivers_{deal_id}.csv'}
        )

    except Exception as e:
        logger.error(f"Error exporting drivers CSV: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@costs_bp.route('/api/export/<deal_id>/costs')
def api_export_costs_csv(deal_id: str):
    """Export deal costs to CSV for deal model import."""
    from flask import Response
    from services.cost_engine import (
        get_effective_drivers,
        calculate_deal_costs,
        generate_deal_costs_csv,
    )
    from web.deal_data import get_deal_data
    from web.context import load_deal_context

    try:
        # Load deal context
        load_deal_context(deal_id)
        data = get_deal_data()
        fact_store = data.fact_store if hasattr(data, 'fact_store') else None

        # Get drivers and calculate costs
        driver_result = get_effective_drivers(deal_id, fact_store)
        summary = calculate_deal_costs(deal_id, driver_result.drivers)

        # Generate CSV
        csv_content = generate_deal_costs_csv(summary)

        return Response(
            csv_content,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=deal_costs_{deal_id}.csv'}
        )

    except Exception as e:
        logger.error(f"Error exporting costs CSV: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@costs_bp.route('/api/export/<deal_id>/assumptions')
def api_export_assumptions_csv(deal_id: str):
    """Export assumptions to CSV."""
    from flask import Response
    from services.cost_engine import (
        get_effective_drivers,
        calculate_deal_costs,
        generate_assumptions_csv,
    )
    from web.deal_data import get_deal_data
    from web.context import load_deal_context

    try:
        # Load deal context
        load_deal_context(deal_id)
        data = get_deal_data()
        fact_store = data.fact_store if hasattr(data, 'fact_store') else None

        # Get drivers and calculate costs
        driver_result = get_effective_drivers(deal_id, fact_store)
        summary = calculate_deal_costs(deal_id, driver_result.drivers)

        # Generate CSV
        csv_content = generate_assumptions_csv(summary, driver_result)

        return Response(
            csv_content,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=assumptions_{deal_id}.csv'}
        )

    except Exception as e:
        logger.error(f"Error exporting assumptions CSV: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
