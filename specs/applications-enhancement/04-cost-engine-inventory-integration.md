# Cost Engine - Inventory Integration

**Status:** Specification
**Created:** 2026-02-11
**Depends On:** 00-overview-applications-enhancement.md, 03-application-cost-model.md
**Enables:** 05-ui-enrichment-status.md, 07-rollout-migration.md
**Estimated Scope:** 3-4 hours

---

## Overview

**Problem:** Cost engine currently uses `DealDrivers` (simple counts: `applications=50`) instead of querying `InventoryStore` for rich application details (category, complexity, vendor, deployment). This architectural gap prevents cost model from using inventory richness.

**Solution:** Refactor cost engine to query `InventoryStore` directly, iterate over applications, and calculate costs using full inventory metadata.

**Why this exists:** The cost model defined in Doc 03 relies on per-application attributes (category, complexity, deployment_type) that exist in InventoryStore but not in DealDrivers.

---

## Architecture

### Current Flow (Count-Based)

```
DealDrivers(applications=50)
    ↓
calculate_cost(APPLICATION_MIGRATION_MODEL, drivers, deal_type)
    ↓
cost = $50K + ($5K × 50) = $300K  # Flat, no differentiation
```

**Problems:**
- No visibility into what the 50 apps actually are
- Can't vary cost by category or complexity
- Can't add integration costs (API count, SSO, data migration)
- Can't detect parent-hosted apps for TSA

### Target Flow (Inventory-Based)

```
InventoryStore.get_items(inventory_type='application', entity='target')
    ↓
For each app:
    complexity = classify_complexity(app)
    category = app.data['category']
    deployment = detect_deployment_type(app)
    integration_costs = calculate_integration_costs(app)
    tsa_cost = calculate_tsa_cost(app, deal_type)

    app_cost = calculate_application_cost(
        app, deal_type,
        complexity, category, deployment,
        integration_costs, tsa_cost
    )
    ↓
Aggregate all app costs → Total application migration cost
```

**Benefits:**
- Cost varies by actual application portfolio
- Category/complexity awareness
- Integration costs explicitly modeled
- TSA costs for parent-hosted apps

---

## Specification

### 1. New Function: calculate_application_costs_from_inventory

**Primary entry point for application costing:**

```python
# services/cost_engine/calculator.py

def calculate_application_costs_from_inventory(
    inventory_store: InventoryStore,
    deal_type: str = 'acquisition',
    entity: str = 'target',
    tsa_duration_months: int = 12
) -> ApplicationCostSummary:
    """
    Calculate total application migration costs from inventory.

    Args:
        inventory_store: InventoryStore instance
        deal_type: 'acquisition' | 'carveout' | 'divestiture'
        entity: 'target' | 'buyer'
        tsa_duration_months: TSA duration for carveouts (default 12)

    Returns:
        ApplicationCostSummary with per-app breakdown and totals
    """
    # Get all applications for entity
    apps = inventory_store.get_items(
        inventory_type='application',
        entity=entity,
        status='active'
    )

    if not apps:
        return ApplicationCostSummary(
            total_one_time=0,
            total_tsa=0,
            total_integration=0,
            app_costs=[],
            app_count=0,
            deal_type=deal_type,
            entity=entity
        )

    app_costs = []

    for app in apps:
        # Calculate cost for this application
        app_cost = calculate_application_cost(
            app=app,
            deal_type=deal_type,
            tsa_duration_months=tsa_duration_months
        )
        app_costs.append(app_cost)

    # Aggregate
    total_one_time = sum(ac.one_time_total for ac in app_costs)
    total_tsa = sum(ac.tsa_total for ac in app_costs)
    total_integration = sum(ac.integration_total for ac in app_costs)

    return ApplicationCostSummary(
        total_one_time=total_one_time,
        total_tsa=total_tsa,
        total_integration=total_integration,
        app_costs=app_costs,
        app_count=len(apps),
        deal_type=deal_type,
        entity=entity
    )
```

### 2. Per-Application Cost Calculation

**Calculate cost for single application:**

```python
def calculate_application_cost(
    app: InventoryItem,
    deal_type: str,
    tsa_duration_months: int = 12
) -> ApplicationCost:
    """
    Calculate migration cost for single application using multi-tier model.

    Args:
        app: InventoryItem from inventory store
        deal_type: 'acquisition' | 'carveout' | 'divestiture'
        tsa_duration_months: TSA duration for carveouts

    Returns:
        ApplicationCost with breakdown
    """
    # Classify complexity
    complexity = classify_complexity(app)
    complexity_multiplier = COMPLEXITY_MULTIPLIERS[complexity]

    # Get category multiplier
    category = app.data.get('category', 'unknown')
    category_multiplier = CATEGORY_COST_MULTIPLIERS.get(category, 1.0)

    # Get deployment multiplier
    deployment_type = detect_deployment_type(app)
    deployment_multiplier = DEPLOYMENT_TYPE_MULTIPLIERS[deployment_type]

    # Get deal type multiplier (from existing deal-type awareness system)
    deal_multiplier = get_deal_type_multiplier(deal_type, 'application')

    # Base cost calculation
    base_cost = 20000  # $20K base per app
    one_time_base = (
        base_cost *
        complexity_multiplier *
        category_multiplier *
        deployment_multiplier *
        deal_multiplier
    )

    # Integration costs
    integration_costs = calculate_integration_costs(app)
    integration_total = integration_costs['total_integration_cost']

    # TSA costs (carveouts only)
    tsa_cost = calculate_tsa_cost(app, deal_type, tsa_duration_months)

    # Total
    one_time_total = one_time_base + integration_total

    return ApplicationCost(
        app_name=app.data.get('name', 'Unknown'),
        app_id=app.item_id,
        complexity=complexity,
        category=category,
        deployment_type=deployment_type,
        one_time_base=one_time_base,
        integration_costs=integration_costs,
        integration_total=integration_total,
        tsa_monthly=tsa_cost / tsa_duration_months if tsa_cost > 0 else 0,
        tsa_total=tsa_cost,
        one_time_total=one_time_total,
        grand_total=one_time_total + tsa_cost,
        cost_breakdown={
            'base_cost': base_cost,
            'complexity_multiplier': complexity_multiplier,
            'category_multiplier': category_multiplier,
            'deployment_multiplier': deployment_multiplier,
            'deal_multiplier': deal_multiplier,
            'one_time_base': one_time_base,
            **integration_costs,
            'tsa_cost': tsa_cost
        }
    )
```

### 3. Data Models

**ApplicationCost (per-app result):**

```python
@dataclass
class ApplicationCost:
    """Cost estimate for single application."""
    app_name: str
    app_id: str
    complexity: str                    # simple/medium/complex/critical
    category: str                      # erp, crm, collaboration, etc.
    deployment_type: str               # saas, on_prem, hybrid, custom

    # Costs
    one_time_base: float              # Base migration cost (before integration)
    integration_costs: Dict[str, float]  # Breakdown of integration costs
    integration_total: float           # Sum of integration costs
    tsa_monthly: float                 # Monthly TSA (carveouts only)
    tsa_total: float                   # Total TSA over duration
    one_time_total: float              # Base + integration
    grand_total: float                 # One-time + TSA

    # Transparency
    cost_breakdown: Dict[str, Any]     # All multipliers and drivers
```

**ApplicationCostSummary (aggregate):**

```python
@dataclass
class ApplicationCostSummary:
    """Aggregate application costs for a deal."""
    total_one_time: float           # Sum of all one-time costs
    total_tsa: float                # Sum of all TSA costs
    total_integration: float        # Sum of all integration costs
    app_costs: List[ApplicationCost]  # Per-app breakdown
    app_count: int
    deal_type: str
    entity: str

    @property
    def grand_total(self) -> float:
        return self.total_one_time + self.total_tsa

    def get_apps_by_complexity(self) -> Dict[str, List[ApplicationCost]]:
        """Group apps by complexity tier for reporting."""
        from collections import defaultdict
        by_complexity = defaultdict(list)
        for app_cost in self.app_costs:
            by_complexity[app_cost.complexity].append(app_cost)
        return dict(by_complexity)

    def get_top_cost_apps(self, n: int = 10) -> List[ApplicationCost]:
        """Get N most expensive applications."""
        return sorted(self.app_costs, key=lambda ac: ac.grand_total, reverse=True)[:n]
```

### 4. Integration with calculate_deal_costs

**Modify existing deal-level cost calculation:**

```python
# services/cost_engine/calculator.py

def calculate_deal_costs(
    deal_id: str,
    drivers: DealDrivers,
    deal_type: str = 'acquisition',
    inventory_store: Optional[InventoryStore] = None
) -> DealCostSummary:
    """
    Calculate all costs for a deal.

    If inventory_store provided, use inventory-based application costing.
    Otherwise, fall back to DealDrivers count-based costing (backward compatible).
    """
    # ... existing logic for identity, infrastructure, etc.

    # APPLICATION COSTS - New path
    if inventory_store and FEATURE_FLAG_ENABLED:
        # Use inventory-based costing
        app_cost_summary = calculate_application_costs_from_inventory(
            inventory_store=inventory_store,
            deal_type=deal_type,
            entity=drivers.entity or 'target'
        )

        total_application_cost = app_cost_summary.total_one_time
        total_tsa_costs += app_cost_summary.total_tsa

    else:
        # Legacy path: use DealDrivers count
        app_model = COST_MODELS.get(WorkItemType.APPLICATION_MIGRATION)
        if app_model and drivers.applications:
            app_cost_result = calculate_cost(app_model, drivers, deal_type)
            total_application_cost = app_cost_result.one_time_base
        else:
            total_application_cost = 0

    # ... rest of deal cost aggregation
```

### 5. Feature Flag for Gradual Rollout

**Control new behavior with feature flag:**

```python
# config_v2.py

# Feature flag for inventory-based application costing
APPLICATION_INVENTORY_COSTING_ENABLED = os.getenv(
    'APPLICATION_INVENTORY_COSTING',
    'true'  # Default enabled (can disable via env var)
).lower() == 'true'
```

**Usage in code:**

```python
from config_v2 import APPLICATION_INVENTORY_COSTING_ENABLED

if inventory_store and APPLICATION_INVENTORY_COSTING_ENABLED:
    # New path: inventory-based
    app_costs = calculate_application_costs_from_inventory(...)
else:
    # Old path: count-based
    app_costs = calculate_cost(app_model, drivers, deal_type)
```

### 6. Backward Compatibility

**Ensure existing code continues to work:**

```python
# DealDrivers still accepted for backward compatibility
def calculate_deal_costs(
    deal_id: str,
    drivers: DealDrivers,
    deal_type: str = 'acquisition',
    inventory_store: Optional[InventoryStore] = None  # NEW: optional
) -> DealCostSummary:
    """
    Dual-mode operation:
    - If inventory_store provided → use inventory-based costing
    - Otherwise → use DealDrivers count-based costing (legacy)
    """
```

**Existing callers without inventory_store continue to work:**

```python
# Legacy call (still works)
costs = calculate_deal_costs("deal-123", drivers, "acquisition")

# New call (inventory-aware)
costs = calculate_deal_costs("deal-123", drivers, "acquisition", inv_store)
```

---

## Verification Strategy

### Unit Tests

```python
# tests/unit/test_cost_engine_inventory_integration.py

def test_calculate_app_cost_simple_saas():
    """Simple SaaS app has low cost."""
    app = InventoryItem(
        item_id="APP-001",
        inventory_type="application",
        entity="target",
        data={
            'name': 'Slack',
            'category': 'collaboration',
            'complexity': 'simple',
            'deployment_type': 'saas'
        }
    )

    cost = calculate_application_cost(app, 'acquisition')

    # $20K × 0.5 (simple) × 0.8 (collab) × 0.3 (saas) × 1.0 (acq) = $2.4K
    assert cost.one_time_base == pytest.approx(2400, rel=0.05)
    assert cost.integration_total == 0  # No integrations
    assert cost.tsa_total == 0  # Acquisition

def test_calculate_app_cost_critical_erp():
    """Critical ERP has high cost."""
    app = InventoryItem(
        item_id="APP-002",
        inventory_type="application",
        entity="target",
        data={
            'name': 'SAP ERP',
            'category': 'erp',
            'complexity': 'critical',
            'deployment_type': 'on_prem',
            'api_integrations': 5,
            'sso_required': True,
            'data_volume_gb': 200
        }
    )

    cost = calculate_application_cost(app, 'carveout')

    # Base: $20K × 3.0 × 2.5 × 1.5 × 1.8 = $405K
    # Integration: 5×$2K + $5K + 200/100×$10K = $10K + $5K + $20K = $35K
    # Total: $405K + $35K = $440K

    assert cost.one_time_base == pytest.approx(405000, rel=0.05)
    assert cost.integration_total == pytest.approx(35000, rel=0.05)
    assert cost.one_time_total == pytest.approx(440000, rel=0.05)

def test_calculate_app_costs_from_inventory():
    """Aggregate application costs from inventory."""
    inv_store = InventoryStore(deal_id="test")

    # Add 2 apps
    inv_store.add_item(
        inventory_type='application',
        entity='target',
        data={'name': 'Slack', 'category': 'collaboration', 'complexity': 'simple'}
    )
    inv_store.add_item(
        inventory_type='application',
        entity='target',
        data={'name': 'SAP', 'category': 'erp', 'complexity': 'critical'}
    )

    summary = calculate_application_costs_from_inventory(inv_store, 'acquisition')

    assert summary.app_count == 2
    assert summary.total_one_time > 0
    assert len(summary.app_costs) == 2

    # SAP should be most expensive
    top_apps = summary.get_top_cost_apps(1)
    assert top_apps[0].app_name == 'SAP'

def test_backward_compatibility_without_inventory():
    """calculate_deal_costs works without inventory_store (legacy mode)."""
    drivers = DealDrivers(entity="target", applications=10)

    # Call without inventory_store (old API)
    summary = calculate_deal_costs("test", drivers, "acquisition")

    # Should use count-based costing (fallback)
    assert summary.total_one_time_base > 0
    # Won't have per-app breakdown, just total

def test_dual_mode_with_inventory():
    """calculate_deal_costs uses inventory when provided."""
    inv_store = InventoryStore(deal_id="test")
    inv_store.add_item(
        inventory_type='application',
        entity='target',
        data={'name': 'App1', 'category': 'erp'}
    )

    drivers = DealDrivers(entity="target", applications=10)  # Count ignored

    summary = calculate_deal_costs("test", drivers, "acquisition", inv_store)

    # Should use inventory-based costing
    # Total should reflect actual inventory, not DealDrivers count
    assert summary.total_one_time_base > 0
```

### Integration Tests

```python
# tests/integration/test_inventory_costing_end_to_end.py

def test_full_pipeline_with_inventory_costing():
    """Document → Inventory → Cost calculation end-to-end."""
    # Parse document
    parsed = parse_document("sample_target_apps.pdf")

    # Process into inventory
    inv_store = InventoryStore(deal_id="test")
    process_applications(parsed, drivers, inv_store)

    # Calculate costs from inventory
    summary = calculate_application_costs_from_inventory(inv_store, 'carveout')

    # Verify
    assert summary.app_count > 0
    assert summary.total_one_time > 0
    assert len(summary.app_costs) == summary.app_count

    # Top cost apps should be critical/complex
    top_apps = summary.get_top_cost_apps(3)
    for app in top_apps:
        assert app.complexity in ['complex', 'critical']
```

### Manual Verification

**Test scenarios:**

1. **Create deal with 5 simple SaaS apps**
   - ✅ Total cost <$50K
   - ✅ Per-app breakdown shows low costs

2. **Create deal with 1 critical ERP**
   - ✅ Total cost >$300K
   - ✅ Cost breakdown shows all multipliers

3. **Create carveout with parent-hosted app**
   - ✅ TSA costs appear
   - ✅ Monthly and total TSA shown

4. **Disable feature flag, recalculate**
   - ✅ Falls back to count-based costing
   - ✅ No per-app breakdown

5. **Compare inventory-based vs count-based for same deal**
   - ✅ Inventory-based varies by app complexity
   - ✅ Count-based is flat $5K per app

---

## Benefits

### Cost Accuracy
- **Complexity awareness:** Costs vary 60x+ between simple and critical apps
- **Category differentiation:** ERP costs 3x more than collaboration tools
- **Deployment impact:** SaaS 5x cheaper than on-prem migration
- **Integration visibility:** API, SSO, data migration explicitly costed

### Architectural Coherence
- **Inventory richness utilized:** Finally uses category, complexity, deployment data
- **Single source of truth:** InventoryStore drives both UI and costs
- **Extensibility:** Easy to add new cost drivers (e.g., custom integrations)

### Business Value
- **Realistic budgets:** No more 2-10x underestimation
- **Deal insights:** Can see which apps drive integration costs
- **Scenario analysis:** Recalculate costs for different deal structures

---

## Expectations

### Success Criteria

- [ ] `calculate_application_costs_from_inventory()` implemented and tested
- [ ] Per-app cost calculation uses all multipliers from Doc 03
- [ ] `ApplicationCost` and `ApplicationCostSummary` data models defined
- [ ] `calculate_deal_costs()` supports dual-mode operation (with/without inventory)
- [ ] Feature flag enables/disables inventory-based costing
- [ ] Backward compatibility maintained (existing callers work)
- [ ] All unit tests passing (10+ tests)
- [ ] Integration tests validate end-to-end flow

### Non-Goals

- ❌ Real-time cost updates in UI (batch calculation is sufficient)
- ❌ Cost optimization recommendations (separate feature)
- ❌ Historical cost tracking (separate audit trail feature)

---

## Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Performance regression | Low | Medium | Benchmark on 100-app portfolio; add caching if >5s |
| Inventory fields missing | Medium | High | Validated in Doc 03 assumption A2; add defaults |
| Feature flag confusion | Low | Low | Clear documentation; default enabled |
| Backward compat breaks | Low | Critical | Comprehensive regression tests; dual-mode operation |

---

## Results Criteria

### Acceptance Criteria

1. **New functions implemented:**
   - `calculate_application_costs_from_inventory()`
   - `calculate_application_cost()`

2. **Data models defined:**
   - `ApplicationCost`
   - `ApplicationCostSummary`

3. **Dual-mode operation:**
   - Works with inventory_store (new)
   - Works without inventory_store (legacy)

4. **Feature flag:**
   - `APPLICATION_INVENTORY_COSTING_ENABLED` in config
   - Controls behavior globally

5. **Tests:**
   - 10+ unit tests passing
   - 2+ integration tests passing
   - Backward compatibility validated

### Implementation Checklist

**Files to modify:**

- [ ] `services/cost_engine/calculator.py`
  - Add `calculate_application_costs_from_inventory()`
  - Add `calculate_application_cost()`
  - Modify `calculate_deal_costs()` for dual-mode

- [ ] `services/cost_engine/models.py`
  - Add `ApplicationCost` dataclass
  - Add `ApplicationCostSummary` dataclass

- [ ] `config_v2.py`
  - Add `APPLICATION_INVENTORY_COSTING_ENABLED` flag

- [ ] `tests/unit/test_cost_engine_inventory_integration.py` (new file)
  - 10+ unit tests

- [ ] `tests/integration/test_inventory_costing_end_to_end.py` (new file)
  - 2+ integration tests

---

## Related Documents

- **00-overview-applications-enhancement.md** - Architecture overview
- **03-application-cost-model.md** - Cost model definition (prerequisite)
- **05-ui-enrichment-status.md** - UI displays per-app costs
- **07-rollout-migration.md** - Feature flag rollout strategy
- `specs/deal-type-awareness/05-cost-buildup-wiring.md` - Cost engine architecture

---

**Document Status:** ✅ Complete
**Last Updated:** 2026-02-11
**Next Document:** 05-ui-enrichment-status.md, 06-testing-validation.md
