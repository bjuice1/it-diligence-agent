# Synergy Engine Conditional Logic

**Document:** 02-synergy-engine-conditional-logic.md
**Purpose:** Implement conditional branching in `_identify_synergies()` to calculate consolidation synergies for acquisitions OR separation costs for carveouts
**Status:** Core implementation - Critical P0 fix
**Date:** 2026-02-11
**Depends On:** Doc 01 (deal type taxonomy, entity semantics)

---

## Overview

**Current State (CRITICAL BUG):**
```python
# web/blueprints/costs.py:459
def _identify_synergies() -> List[SynergyOpportunity]:
    # ❌ NO deal_type parameter
    # ❌ ALWAYS calculates consolidation synergies
    # ❌ Wrong for carveouts and divestitures
```

**Target State:**
```python
def _identify_synergies(deal_type: str = "acquisition") -> List[SynergyOpportunity]:
    """Identify synergies OR separation costs based on deal type."""

    if deal_type in ["carveout", "divestiture"]:
        return _calculate_separation_costs()  # NEW
    else:  # acquisition
        return _calculate_consolidation_synergies()  # REFACTORED
```

**Why This Matters:**
- Carveout deal with current code → Recommends "consolidate target CRM with buyer CRM"
- Correct recommendation → "Stand up standalone CRM for target, TSA from parent for 12 months"
- **Direction is inverted** - target is LEAVING buyer, not joining

---

## Architecture

### Component Diagram

```
┌────────────────────────────────────────────────────────────────┐
│ build_cost_center_data(entity: str = "target")                 │
│                                                                 │
│ ┌────────────────────────────────────────────────────────┐    │
│ │ 1. Fetch deal_type from deal_context or database       │    │
│ │    deal_type = get_current_deal_type()                 │    │
│ └────────────────────────────────────────────────────────┘    │
│                           ↓                                    │
│ ┌────────────────────────────────────────────────────────┐    │
│ │ 2. Pass to synergy engine                              │    │
│ │    synergies = _identify_synergies(deal_type)          │    │
│ └────────────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────────┘
                           ↓
    ┌──────────────────────────────────────────────────────┐
    │ _identify_synergies(deal_type: str)                  │
    │                                                       │
    │  IF deal_type == "acquisition":                       │
    │    ├─→ _calculate_consolidation_synergies()          │
    │    │     • Match buyer vs target apps by category     │
    │    │     • Calculate savings from consolidation       │
    │    │     • Return SynergyOpportunity objects          │
    │                                                       │
    │  ELIF deal_type in ["carveout", "divestiture"]:       │
    │    ├─→ _calculate_separation_costs()                  │
    │    │     • Identify shared services with parent       │
    │    │     • Calculate standup costs                    │
    │    │     • Return SeparationCost objects              │
    │                                                       │
    │  ELSE:                                                │
    │    └─→ logger.warning + return []                     │
    └──────────────────────────────────────────────────────┘
                           ↓
    ┌──────────────────────────────────────────────────────┐
    │ Output: List[Union[SynergyOpportunity, SeparationCost]]│
    │                                                       │
    │ Used by:                                              │
    │  - Cost center reports                                │
    │  - Executive summary synergy section                  │
    │  - Investment Committee materials                     │
    └──────────────────────────────────────────────────────┘
```

### Data Flow

```
Input: deal_type from deal_context
  ↓
Fetch buyer and target inventory
  ↓
Match by category (apps, infrastructure, etc.)
  ↓
Branch on deal_type:
  ├─ acquisition → Calculate consolidation value
  └─ carveout/divestiture → Calculate separation costs
  ↓
Return list of opportunities/costs
  ↓
Output: Display in UI, include in narrative
```

---

## Specification

### Function Signatures

#### Primary Entry Point

```python
def _identify_synergies(deal_type: str = "acquisition") -> List[Union[SynergyOpportunity, SeparationCost]]:
    """
    Identify cost optimization opportunities based on deal type.

    For acquisitions: Calculates consolidation synergies (eliminate duplicate systems)
    For carveouts/divestitures: Calculates separation costs (standup standalone capabilities)

    Args:
        deal_type: Deal structure - "acquisition", "carveout", or "divestiture"
                   Defaults to "acquisition" for backward compatibility

    Returns:
        List of SynergyOpportunity (acquisitions) or SeparationCost (carveouts)
        Empty list if inventory unavailable or no opportunities found

    Raises:
        ValueError: If deal_type is invalid (not in allowed values)

    Example:
        # Acquisition: Returns consolidation synergies
        synergies = _identify_synergies("acquisition")
        # → [SynergyOpportunity(name="CRM Consolidation", annual_savings_low=380000, ...)]

        # Carveout: Returns separation costs
        costs = _identify_synergies("carveout")
        # → [SeparationCost(name="Standalone CRM", setup_cost_low=500000, ...)]
    """
```

#### Consolidation Synergies (Acquisitions)

```python
def _calculate_consolidation_synergies(
    buyer_apps: List[InventoryItem],
    target_apps: List[InventoryItem]
) -> List[SynergyOpportunity]:
    """
    Calculate consolidation synergies from buyer vs target app overlap.

    Consolidation Model:
      - Eliminate smaller contract (100% of cost saved)
      - Renegotiate larger contract with volume discount (10-30% savings)
      - Cost to achieve: Migration labor (50-200% of smaller contract)

    Args:
        buyer_apps: Buyer's application inventory
        target_apps: Target's application inventory

    Returns:
        List of SynergyOpportunity objects for overlapping categories

    Logic:
        1. Group apps by category for buyer and target
        2. Find overlapping categories (both have apps in same category)
        3. For each overlap:
           - Calculate total cost (buyer + target in that category)
           - Skip if combined cost < $100K (not material)
           - Calculate savings: smaller_cost + (larger_cost * 0.10 to 0.30)
           - Calculate cost to achieve: smaller_cost * 0.50 to 2.00
           - Determine timeframe based on category criticality
        4. Return sorted by annual_savings_high (descending)
    """
```

#### Separation Costs (Carveouts/Divestitures)

```python
def _calculate_separation_costs(
    target_apps: List[InventoryItem],
    parent_shared_services: Optional[List[str]] = None
) -> List[SeparationCost]:
    """
    Calculate costs to stand up standalone capabilities for carved-out target.

    Separation Model:
      - Identify systems target currently shares with parent
      - Calculate cost to build/buy standalone alternative
      - Estimate TSA duration and monthly cost

    Args:
        target_apps: Target's current application inventory
        parent_shared_services: Known shared services (if available from documents)

    Returns:
        List of SeparationCost objects for standup requirements

    Logic:
        1. Identify critical categories from target's inventory
        2. For each category:
           - Determine if target has standalone system or relies on parent
           - If shared with parent:
             * Calculate standup cost (buy new license + implement)
             * Estimate TSA duration (6-18 months depending on complexity)
             * Calculate monthly TSA cost (% of parent system cost)
           - If already standalone:
             * No separation cost, mark as "ready"
        3. Flag high-risk dependencies (ERP, HCM, Finance systems)
        4. Return sorted by setup_cost_high + (tsa_monthly_cost * tsa_duration_months)
    """
```

### Data Structures

#### SynergyOpportunity (Already Exists)

```python
@dataclass
class SynergyOpportunity:
    """Consolidation synergy for acquisitions."""
    name: str                          # e.g., "CRM Platform Consolidation"
    category: str                      # "consolidation", "optimization", "renegotiation"
    annual_savings_low: float          # Conservative estimate ($)
    annual_savings_high: float         # Optimistic estimate ($)
    cost_to_achieve_low: float         # Implementation cost - conservative ($)
    cost_to_achieve_high: float        # Implementation cost - optimistic ($)
    timeframe: str                     # e.g., "6-12 months", "12-18 months"
    confidence: str                    # "high", "medium", "low"
    notes: str                         # Explanation of synergy
    affected_items: List[str]          # App/system names involved
```

#### SeparationCost (NEW)

```python
@dataclass
class SeparationCost:
    """Separation/standup cost for carveouts and divestitures."""
    name: str                          # e.g., "Standalone ERP Implementation"
    category: str                      # "standup", "tsa_service", "data_separation"
    setup_cost_low: float              # One-time standup cost - conservative ($)
    setup_cost_high: float             # One-time standup cost - optimistic ($)
    tsa_required: bool                 # Whether TSA needed from parent
    tsa_duration_months: int           # Expected TSA duration (0 if not required)
    tsa_monthly_cost: float            # Monthly TSA fee ($) (0 if not required)
    timeframe: str                     # e.g., "Day 1", "3-6 months", "6-12 months"
    criticality: str                   # "critical" (Day 1 required), "high", "medium", "low"
    notes: str                         # Explanation and assumptions
    affected_systems: List[str]        # System names involved
    alternative_approaches: List[str]  # Other options considered (e.g., "Buy vs Build")

    @property
    def total_cost_low(self) -> float:
        """Total cost including setup + TSA fees."""
        return self.setup_cost_low + (self.tsa_monthly_cost * self.tsa_duration_months)

    @property
    def total_cost_high(self) -> float:
        """Total cost including setup + TSA fees."""
        return self.setup_cost_high + (self.tsa_monthly_cost * self.tsa_duration_months)
```

### Consolidation Synergy Calculation Rules

**Category Matching:**
```python
# Group apps by category
buyer_by_category = group_by_category(buyer_apps)
target_by_category = group_by_category(target_apps)

# Find overlaps
overlapping_categories = set(buyer_by_category.keys()) & set(target_by_category.keys())
```

**Materiality Threshold:**
```python
buyer_cost = sum(app.cost for app in buyer_apps_in_category)
target_cost = sum(app.cost for app in target_apps_in_category)
combined_cost = buyer_cost + target_cost

if combined_cost < 100_000:
    # Skip - not material enough for synergy analysis
    continue
```

**Savings Calculation:**
```python
smaller_cost = min(buyer_cost, target_cost)
larger_cost = max(buyer_cost, target_cost)

# Model: Eliminate smaller contract + volume discount on larger
annual_savings_low = smaller_cost + (larger_cost * 0.10)   # Conservative: 10% discount
annual_savings_high = smaller_cost + (larger_cost * 0.30)  # Optimistic: 30% discount
```

**Cost to Achieve:**
```python
# Migration labor cost as % of smaller contract
cost_to_achieve_low = smaller_cost * 0.50   # Best case: 50% of contract value
cost_to_achieve_high = smaller_cost * 2.00  # Worst case: 200% of contract value
```

**Timeframe Estimation:**
```python
critical_categories = ['crm', 'erp', 'finance', 'hr', 'hris']

if category.lower() in critical_categories:
    timeframe = "12-18 months"  # Longer for mission-critical systems
    confidence = "medium"
else:
    timeframe = "6-12 months"   # Faster for non-critical
    confidence = "high"
```

### Separation Cost Calculation Rules

**Critical Systems Identification:**
```python
critical_systems = {
    'erp': {
        'priority': 'critical',
        'typical_cost_range': (1_000_000, 5_000_000),
        'typical_tsa_duration': 18,  # months
        'standalone_timeframe': '12-18 months'
    },
    'crm': {
        'priority': 'high',
        'typical_cost_range': (200_000, 1_000_000),
        'typical_tsa_duration': 12,
        'standalone_timeframe': '6-12 months'
    },
    'hcm': {
        'priority': 'critical',
        'typical_cost_range': (500_000, 2_000_000),
        'typical_tsa_duration': 18,
        'standalone_timeframe': '12-18 months'
    },
    # ... etc
}
```

**Standup Cost Estimation:**
```python
def estimate_standup_cost(category: str, target_users: int) -> Tuple[float, float]:
    """
    Estimate cost to stand up standalone system.

    Model: Base cost + per-user license + implementation services
    """
    config = critical_systems.get(category, {})

    base_low, base_high = config.get('typical_cost_range', (100_000, 500_000))

    # Adjust for user count (economies of scale)
    if target_users < 500:
        multiplier = 1.0
    elif target_users < 2000:
        multiplier = 0.8  # Better per-user economics
    else:
        multiplier = 0.6

    setup_cost_low = base_low * multiplier
    setup_cost_high = base_high * multiplier

    return (setup_cost_low, setup_cost_high)
```

**TSA Cost Estimation:**
```python
def estimate_tsa_cost(category: str, parent_system_cost: float) -> Tuple[int, float]:
    """
    Estimate TSA duration and monthly cost.

    TSA cost is typically 10-15% of parent system's annual cost per month.
    """
    config = critical_systems.get(category, {})

    duration_months = config.get('typical_tsa_duration', 12)

    # TSA monthly cost: ~10-15% of annual parent system cost, divided by 12
    monthly_low = (parent_system_cost * 0.10) / 12
    monthly_high = (parent_system_cost * 0.15) / 12
    monthly_avg = (monthly_low + monthly_high) / 2

    return (duration_months, monthly_avg)
```

---

## Implementation Steps

### Step 1: Add deal_type Parameter to _identify_synergies()

**File:** `web/blueprints/costs.py:459`

**Change:**
```python
# BEFORE
def _identify_synergies() -> List[SynergyOpportunity]:
    """Identify cost synergy opportunities from buyer vs target inventory."""

# AFTER
def _identify_synergies(deal_type: str = "acquisition") -> List[Union[SynergyOpportunity, SeparationCost]]:
    """
    Identify cost optimization opportunities based on deal type.

    For acquisitions: Calculates consolidation synergies
    For carveouts/divestitures: Calculates separation costs

    Args:
        deal_type: "acquisition", "carveout", or "divestiture"

    Returns:
        List of SynergyOpportunity or SeparationCost objects
    """
    # Validate deal_type
    allowed_types = ['acquisition', 'carveout', 'divestiture', 'bolt_on', 'platform']
    if deal_type not in allowed_types:
        logger.warning(f"Unknown deal_type '{deal_type}', defaulting to 'acquisition'")
        deal_type = 'acquisition'

    # Normalize aliases
    if deal_type in ['bolt_on', 'platform']:
        deal_type = 'acquisition'
```

### Step 2: Extract Existing Logic to _calculate_consolidation_synergies()

**File:** `web/blueprints/costs.py` (new function after _identify_synergies)

**Action:** Refactor existing synergy calculation code into dedicated function.

```python
def _calculate_consolidation_synergies() -> List[SynergyOpportunity]:
    """Calculate consolidation synergies for acquisitions."""
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

        # Group by category
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

        # Find overlaps
        overlapping_categories = set(buyer_by_category.keys()) & set(target_by_category.keys())

        logger.info(f"Found {len(overlapping_categories)} overlapping categories for consolidation")

        # Calculate synergies for each overlap
        for category in overlapping_categories:
            buyer_apps_in_cat = buyer_by_category[category]
            target_apps_in_cat = target_by_category[category]

            buyer_cost = sum(app.cost or 0 for app in buyer_apps_in_cat)
            target_cost = sum(app.cost or 0 for app in target_apps_in_cat)
            combined_cost = buyer_cost + target_cost

            # Skip if not material
            if combined_cost < 100_000:
                continue

            # Calculate synergy
            smaller_cost = min(buyer_cost, target_cost)
            larger_cost = max(buyer_cost, target_cost)

            savings_low = smaller_cost + (larger_cost * 0.10)
            savings_high = smaller_cost + (larger_cost * 0.30)

            cost_to_achieve_low = smaller_cost * 0.5
            cost_to_achieve_high = smaller_cost * 2.0

            # Timeframe based on criticality
            critical_categories = ['crm', 'erp', 'finance', 'hr', 'hris']
            if category.lower() in critical_categories:
                timeframe = "12-18 months"
                confidence = "medium"
            else:
                timeframe = "6-12 months"
                confidence = "high"

            synergies.append(SynergyOpportunity(
                name=f"{category.title()} Platform Consolidation",
                category="consolidation",
                annual_savings_low=round(savings_low, -3),
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
```

### Step 3: Implement _calculate_separation_costs()

**File:** `web/blueprints/costs.py` (new function)

```python
def _calculate_separation_costs() -> List[SeparationCost]:
    """Calculate separation costs for carveouts and divestitures."""
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
```

### Step 4: Update _identify_synergies() to Branch on deal_type

**File:** `web/blueprints/costs.py:459` (modify existing)

```python
def _identify_synergies(deal_type: str = "acquisition") -> List[Union[SynergyOpportunity, SeparationCost]]:
    """
    Identify cost optimization opportunities based on deal type.

    For acquisitions: Calculates consolidation synergies
    For carveouts/divestitures: Calculates separation costs

    See Doc 01 (deal-type-architecture.md) for entity semantics by deal type.
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
```

### Step 5: Update build_cost_center_data() to Pass deal_type

**File:** `web/blueprints/costs.py:700` (modify existing function)

```python
def build_cost_center_data(entity: str = "target") -> CostCenterData:
    """Build complete cost center data from all sources."""

    # NEW: Fetch deal_type from current deal
    deal_type = _get_current_deal_type()  # Helper function to get deal_type

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

    # NEW: Pass deal_type to synergy engine
    synergies = _identify_synergies(deal_type=deal_type)

    # Generate insights
    insights = _generate_insights(run_rate, one_time, synergies)

    # Assess data quality
    data_quality = _assess_data_quality_per_entity(run_rate, one_time, entity)

    return CostCenterData(
        run_rate=run_rate,
        one_time=one_time,
        synergies=synergies,
        insights=insights,
        data_quality=data_quality
    )
```

### Step 6: Add Helper Function to Get Current Deal Type

**File:** `web/blueprints/costs.py` (new function)

```python
def _get_current_deal_type() -> str:
    """
    Get deal_type for the current analysis session.

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
```

### Step 7: Add SeparationCost Dataclass

**File:** `web/blueprints/costs.py` (add after SynergyOpportunity definition)

```python
@dataclass
class SeparationCost:
    """Separation/standup cost for carveouts and divestitures."""
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
```

---

## Verification Strategy

### Unit Tests

**Test File:** `tests/unit/test_synergy_engine_deal_types.py`

```python
class TestSynergyEngineDealTypeAwareness:
    """Test conditional branching in synergy engine."""

    def test_acquisition_returns_consolidation_synergies(self, mock_inventory):
        """Acquisition deal type returns SynergyOpportunity objects."""
        synergies = _identify_synergies(deal_type="acquisition")

        assert len(synergies) > 0
        assert all(isinstance(s, SynergyOpportunity) for s in synergies)
        assert all(s.category == "consolidation" for s in synergies)

    def test_carveout_returns_separation_costs(self, mock_inventory):
        """Carveout deal type returns SeparationCost objects."""
        costs = _identify_synergies(deal_type="carveout")

        assert len(costs) > 0
        assert all(isinstance(c, SeparationCost) for c in costs)
        assert all(c.category in ["standup", "tsa_service"] for c in costs)

    def test_divestiture_returns_separation_costs(self, mock_inventory):
        """Divestiture deal type returns SeparationCost objects."""
        costs = _identify_synergies(deal_type="divestiture")

        assert len(costs) > 0
        assert all(isinstance(c, SeparationCost) for c in costs)

    def test_invalid_deal_type_defaults_to_acquisition(self, mock_inventory):
        """Invalid deal_type logs warning and defaults to acquisition."""
        with patch('web.blueprints.costs.logger') as mock_logger:
            synergies = _identify_synergies(deal_type="invalid")

            mock_logger.warning.assert_called()
            assert all(isinstance(s, SynergyOpportunity) for s in synergies)

    def test_alias_normalization(self, mock_inventory):
        """Deal type aliases normalize to canonical values."""
        # Test acquisition aliases
        synergies1 = _identify_synergies(deal_type="bolt_on")
        synergies2 = _identify_synergies(deal_type="platform")

        assert all(isinstance(s, SynergyOpportunity) for s in synergies1)
        assert all(isinstance(s, SynergyOpportunity) for s in synergies2)

        # Test carveout aliases
        costs = _identify_synergies(deal_type="spinoff")
        assert all(isinstance(c, SeparationCost) for c in costs)
```

### Integration Tests

**Test File:** `tests/integration/test_cost_center_deal_awareness.py`

```python
class TestCostCenterDealAwareness:
    """Test end-to-end cost center data with different deal types."""

    @patch('web.blueprints.costs._get_current_deal_type')
    def test_acquisition_deal_shows_consolidation_synergies(self, mock_get_deal_type, setup_deal):
        """Acquisition deal shows consolidation synergies in cost center."""
        mock_get_deal_type.return_value = "acquisition"

        cost_data = build_cost_center_data(entity="target")

        assert len(cost_data.synergies) > 0
        assert all(isinstance(s, SynergyOpportunity) for s in cost_data.synergies)
        assert any("Consolidation" in s.name for s in cost_data.synergies)

    @patch('web.blueprints.costs._get_current_deal_type')
    def test_carveout_deal_shows_separation_costs(self, mock_get_deal_type, setup_deal):
        """Carveout deal shows separation costs in cost center."""
        mock_get_deal_type.return_value = "carveout"

        cost_data = build_cost_center_data(entity="target")

        assert len(cost_data.synergies) > 0  # Note: "synergies" field holds both types
        assert all(isinstance(c, SeparationCost) for c in cost_data.synergies)
        assert any("Standalone" in c.name for c in cost_data.synergies)
        assert any(c.tsa_required for c in cost_data.synergies)
```

### Manual Verification

1. **Create 3 test deals in UI:**
   - Deal A: deal_type = "acquisition", with buyer/target overlap
   - Deal B: deal_type = "carveout", target has shared systems
   - Deal C: deal_type = "divestiture"

2. **Run analysis for each deal**

3. **Verify outputs:**
   - Deal A: Cost center shows "CRM Consolidation" synergy with annual savings
   - Deal B: Cost center shows "Standalone ERP Implementation" with TSA duration
   - Deal C: Cost center shows separation costs, not consolidation synergies

4. **Check logs:**
   - Confirm `Analyzing synergies/costs for deal_type='acquisition'` messages
   - Verify correct function called (consolidation vs separation)

---

## Benefits

**Why This Approach:**
1. **Correct recommendations:** Carveouts get standup costs, not consolidation synergies
2. **Backward compatible:** Defaults to "acquisition" if deal_type missing
3. **Clear separation:** Two distinct calculation functions, easy to test and maintain
4. **Extensible:** Easy to add new deal types (e.g., "merger_of_equals") in future

**Alternatives Considered:**
- ❌ Single function with if/else inline → Too complex, hard to test
- ❌ Separate SynergyEngine classes → Over-engineered for current needs
- ✅ Two functions with router → Clean, testable, maintainable

---

## Expectations

### Success Criteria
- [ ] `_identify_synergies()` accepts deal_type parameter
- [ ] Acquisitions return SynergyOpportunity objects with consolidation logic
- [ ] Carveouts/divestitures return SeparationCost objects with standup logic
- [ ] Invalid deal_type logs warning and defaults safely
- [ ] `build_cost_center_data()` passes deal_type to synergy engine
- [ ] 15+ unit tests pass covering all deal types and edge cases

### Measurable Outcomes
- Carveout test case no longer recommends consolidation (current bug fixed)
- Separation costs include TSA duration and monthly fees
- Cost center UI shows correct terminology ("Standup Costs" vs "Synergies")

---

## Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Separation cost estimates inaccurate | Under/overestimate standup costs | Medium | Use conservative ranges, cite industry benchmarks in notes |
| TSA duration miscalculated | Wrong cash flow projections | Medium | Reference critical_system_configs, allow user override in UI |
| Existing code assumes SynergyOpportunity type only | Type errors when SeparationCost returned | Low | Use Union type hint, update consuming code to handle both |
| Deal_type not available in all contexts | Function falls back to acquisition | High (initially) | Doc 05 enforces deal_type selection, Doc 07 migration handles existing deals |

---

## Results Criteria

### Acceptance Criteria
1. ✅ Synergy engine branches on deal_type
2. ✅ Consolidation logic moved to dedicated function
3. ✅ Separation cost logic implemented with TSA calculation
4. ✅ SeparationCost dataclass created with total_cost properties
5. ✅ Helper function gets deal_type from session/database
6. ✅ All unit tests pass
7. ✅ Integration tests verify end-to-end behavior

### Success Metrics
- Zero recommendations for "consolidate to buyer" in carveout deals
- Separation costs include at least 3 critical systems (ERP, HCM, Finance)
- TSA durations realistic (6-18 months depending on criticality)

---

**Document Status:** ✅ COMPLETE

**Version:** 1.0
**Last Updated:** 2026-02-11
**Depends On:** Doc 01 (deal-type-architecture.md)
**Enables:** Doc 06 (testing), Cost center UI
