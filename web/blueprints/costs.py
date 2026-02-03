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
from typing import Dict, List, Any, Tuple
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
    """Complete cost center data."""
    run_rate: RunRateCosts = None
    one_time: OneTimeCosts = None
    synergies: List[SynergyOpportunity] = field(default_factory=list)
    insights: List[CostInsight] = field(default_factory=list)
    data_quality: Dict[str, str] = field(default_factory=dict)


# =============================================================================
# DATA GATHERING
# =============================================================================

def _gather_headcount_costs() -> CostCategory:
    """Gather headcount costs from organization analysis.

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
        org_facts = data.get_organization()

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


def _gather_application_costs() -> CostCategory:
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
            apps = inv_store.get_items(inventory_type="application", entity="target", status="active")

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


def _gather_infrastructure_costs() -> CostCategory:
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
            infra = inv_store.get_items(inventory_type="infrastructure", entity="target", status="active")

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


def _gather_one_time_costs() -> OneTimeCosts:
    """Gather one-time integration costs from work items and cost engine.

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
        work_items = data.get_work_items()

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


def _identify_synergies() -> List[SynergyOpportunity]:
    """Identify cost synergy opportunities from inventory analysis."""
    synergies = []

    try:
        from web.blueprints.inventory import get_inventory_store
        inv_store = get_inventory_store()

        if len(inv_store) > 0:
            apps = inv_store.get_items(inventory_type="application", entity="target", status="active")

            # Find duplicate platforms
            categories = {}
            for app in apps:
                cat = app.data.get('category', 'Other')
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(app)

            # Look for consolidation opportunities
            for cat, app_list in categories.items():
                if len(app_list) >= 2:
                    # Check if multiple apps in same category with significant cost
                    total_cost = sum(app.cost or 0 for app in app_list)
                    if total_cost > 200000:  # Significant spend
                        # Estimate savings (typically 30-50% of lower-cost platform)
                        costs = sorted([app.cost or 0 for app in app_list])
                        potential_savings = costs[0] * 0.3  # Conservative: 30% of smaller platform

                        synergies.append(SynergyOpportunity(
                            name=f"{cat} Platform Consolidation",
                            category="consolidation",
                            annual_savings_low=potential_savings * 0.8,
                            annual_savings_high=potential_savings * 1.5,
                            cost_to_achieve_low=potential_savings * 0.5,
                            cost_to_achieve_high=potential_savings * 2,
                            timeframe="12-18 months",
                            confidence="medium",
                            notes=f"Consolidate {len(app_list)} platforms in {cat}",
                            affected_items=[app.name for app in app_list]
                        ))

    except Exception as e:
        logger.warning(f"Could not identify synergies: {e}")

    return synergies


def _generate_insights(run_rate: RunRateCosts, one_time: OneTimeCosts, synergies: List[SynergyOpportunity]) -> List[CostInsight]:
    """Generate cost insights and commentary."""
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

    # Synergy opportunities
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

    return insights


def build_cost_center_data() -> CostCenterData:
    """Build complete cost center data from all sources."""

    # Gather run-rate costs
    run_rate = RunRateCosts(
        headcount=_gather_headcount_costs(),
        applications=_gather_application_costs(),
        infrastructure=_gather_infrastructure_costs(),
        vendors_msp=CostCategory(name="vendors_msp", display_name="Vendors & MSP", icon="🤝")
    )
    run_rate.calculate_total()

    # Gather one-time costs
    one_time = _gather_one_time_costs()

    # Identify synergies
    synergies = _identify_synergies()

    # Generate insights
    insights = _generate_insights(run_rate, one_time, synergies)

    # Assess data quality
    data_quality = {
        "headcount": "medium" if run_rate.headcount.total > 0 else "none",
        "applications": "high" if run_rate.applications.total > 0 else "none",
        "infrastructure": "low" if run_rate.infrastructure.total > 0 else "none",
        "one_time": "medium" if one_time.total_mid > 0 else "none",
    }

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
    data = build_cost_center_data()

    return render_template('costs/center.html',
        data=data,
        run_rate=data.run_rate,
        one_time=data.one_time,
        synergies=data.synergies,
        insights=data.insights,
        data_quality=data.data_quality
    )


@costs_bp.route('/api/summary')
def api_summary():
    """API endpoint for cost summary."""
    data = build_cost_center_data()

    return jsonify({
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
