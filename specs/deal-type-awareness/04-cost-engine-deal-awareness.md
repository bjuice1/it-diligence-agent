# Spec 04: Cost Engine Deal Type Awareness

**Status**: GREENFIELD
**Priority**: P0
**Estimated Effort**: 2 hours
**Dependencies**: Spec 01 (Deal Type Architecture)

---

## Problem Statement

The cost engine (`services/cost_engine/`) calculates work item costs using fixed multipliers and drivers that do NOT account for deal structure. A carve-out separation of identity systems costs 2-3x more than an acquisition integration due to:

- **Carve-out**: Must build NEW standalone IAM infrastructure, migrate identities OUT of parent systems, establish new SSO/MFA, recreate directory services from scratch
- **Acquisition**: Extend EXISTING buyer IAM to cover target users, simpler consolidation path

**Current bug**: Same cost estimate for both scenarios leads to massive budget underestimation for carve-outs.

---

## Solution Design

### 1. Add `deal_type` Parameter to Cost Calculator

**File**: `services/cost_engine/calculator.py`

#### Current Signature (Line ~45)
```python
def calculate_costs(
    work_items: List[WorkItem],
    inventory_store: InventoryStore,
    company_profile: Optional[Dict[str, Any]] = None
) -> CostEstimate:
    """Calculate total cost estimate from work items."""
    # ... no deal_type awareness
```

#### New Signature
```python
def calculate_costs(
    work_items: List[WorkItem],
    inventory_store: InventoryStore,
    company_profile: Optional[Dict[str, Any]] = None,
    deal_type: str = "acquisition"  # NEW: Default to acquisition for backward compatibility
) -> CostEstimate:
    """
    Calculate total cost estimate from work items.

    Args:
        work_items: List of work items to estimate
        inventory_store: Inventory for sizing drivers
        company_profile: Optional company profile for context
        deal_type: One of ['acquisition', 'carveout', 'divestiture']

    Returns:
        CostEstimate with deal-type-aware multipliers applied
    """
```

---

### 2. Deal Type Cost Multipliers

**File**: `services/cost_engine/models.py` (NEW section)

```python
# Deal Type Cost Multipliers
# Applied to base effort estimates based on deal structure

DEAL_TYPE_MULTIPLIERS = {
    'acquisition': {
        # Acquisition = consolidation path (baseline)
        'identity_separation': 1.0,        # Extend existing IAM
        'application_migration': 1.0,      # Migrate to buyer infra
        'infrastructure_consolidation': 1.0,
        'network_integration': 1.0,
        'cybersecurity_harmonization': 1.0,
        'org_restructuring': 1.0
    },
    'carveout': {
        # Carve-out = build standalone systems (HIGHER costs)
        'identity_separation': 2.5,        # Build NEW IAM from scratch
        'application_migration': 1.8,      # Standup new environments
        'infrastructure_consolidation': 2.0,  # Build new datacenter/cloud
        'network_integration': 2.2,        # New WAN/connectivity
        'cybersecurity_harmonization': 1.9,   # New security stack
        'org_restructuring': 1.6           # More disruption to target
    },
    'divestiture': {
        # Divestiture = clean separation (HIGHEST costs)
        'identity_separation': 3.0,        # Full identity extraction
        'application_migration': 2.2,      # Extract from shared systems
        'infrastructure_consolidation': 2.5,
        'network_integration': 2.8,        # Complex untangling
        'cybersecurity_harmonization': 2.3,
        'org_restructuring': 2.0           # Maximum disruption
    }
}

def get_deal_type_multiplier(deal_type: str, work_item_category: str) -> float:
    """
    Get cost multiplier for a work item category based on deal type.

    Args:
        deal_type: One of ['acquisition', 'carveout', 'divestiture']
        work_item_category: Category key from DEAL_TYPE_MULTIPLIERS

    Returns:
        Multiplier (1.0 = baseline, >1.0 = higher complexity)

    Raises:
        ValueError: If deal_type or category invalid
    """
    if deal_type not in DEAL_TYPE_MULTIPLIERS:
        raise ValueError(f"Invalid deal_type: {deal_type}. Must be one of {list(DEAL_TYPE_MULTIPLIERS.keys())}")

    multipliers = DEAL_TYPE_MULTIPLIERS[deal_type]

    # Map work item categories to multiplier keys
    # (Work items may have different naming than multiplier keys)
    category_mapping = {
        'identity': 'identity_separation',
        'application': 'application_migration',
        'infrastructure': 'infrastructure_consolidation',
        'network': 'network_integration',
        'cybersecurity': 'cybersecurity_harmonization',
        'organization': 'org_restructuring'
    }

    multiplier_key = category_mapping.get(work_item_category.lower(), 'infrastructure_consolidation')
    return multipliers.get(multiplier_key, 1.0)
```

---

### 3. Apply Multipliers in Cost Calculation

**File**: `services/cost_engine/calculator.py`

#### Updated `_calculate_work_item_cost()` Method

```python
def _calculate_work_item_cost(
    self,
    work_item: WorkItem,
    inventory_store: InventoryStore,
    deal_type: str = "acquisition"  # NEW parameter
) -> Tuple[float, str]:
    """
    Calculate cost for a single work item.

    Args:
        work_item: Work item to estimate
        inventory_store: Inventory for sizing
        deal_type: Deal structure type

    Returns:
        (cost_estimate, cost_range_bucket)
    """
    # 1. Get base effort estimate from drivers
    base_effort_hours = self._estimate_effort_hours(work_item, inventory_store)

    # 2. Apply deal type multiplier
    category = work_item.domain  # Assume domain maps to category
    multiplier = get_deal_type_multiplier(deal_type, category)

    adjusted_effort_hours = base_effort_hours * multiplier

    # 3. Convert to cost using blended rate
    blended_rate = self.config.get('blended_hourly_rate', 150)
    cost = adjusted_effort_hours * blended_rate

    # 4. Bucket into range
    cost_range = self._bucket_cost(cost)

    return cost, cost_range
```

---

### 4. Wire Through Call Chain

#### Update Call Sites

**File**: `web/blueprints/costs.py` (Line ~150)

```python
# BEFORE
cost_estimate = calculate_costs(
    work_items=work_items,
    inventory_store=inv_store,
    company_profile=company_profile
)

# AFTER
cost_estimate = calculate_costs(
    work_items=work_items,
    inventory_store=inv_store,
    company_profile=company_profile,
    deal_type=deal.deal_type  # ✅ Pass deal_type from Deal model
)
```

**File**: `web/analysis_runner.py` (Line ~450)

```python
# In reasoning phase - pass deal_type to cost calculation
cost_estimate = calculate_costs(
    work_items=all_work_items,
    inventory_store=stores['inventory'],
    company_profile=deal_context.get('company_profile'),
    deal_type=deal_context.get('deal_type', 'acquisition')  # ✅ Extract from context
)
```

---

### 5. Carve-Out Specific: Add TSA Cost Model

For carve-outs, add **Transition Service Agreement (TSA)** costs as a new work item category.

**File**: `services/cost_engine/drivers.py` (NEW section)

```python
class TSACostDriver:
    """
    Calculate TSA costs for carve-out deals.

    TSAs are interim service agreements where parent provides services
    to carved-out entity during separation (6-24 months typical).
    """

    def estimate_monthly_tsa_cost(
        self,
        inventory_store: InventoryStore,
        tsa_duration_months: int = 12
    ) -> float:
        """
        Estimate monthly TSA fees based on inventory complexity.

        Typical TSA services:
        - Datacenter hosting
        - Network connectivity
        - Shared application licenses
        - IT support services

        Industry benchmark: $50K-500K/month depending on scale
        """
        # Count critical shared services
        shared_apps = len([a for a in inventory_store.get_items(domain='applications', entity='target')
                          if a.details.get('hosting') == 'parent_datacenter'])

        shared_infra = len([i for i in inventory_store.get_items(domain='infrastructure', entity='target')
                           if i.details.get('ownership') == 'shared'])

        # Base cost per shared service
        cost_per_app = 5000    # $5K/month per application
        cost_per_infra = 10000 # $10K/month per infrastructure component

        monthly_cost = (shared_apps * cost_per_app) + (shared_infra * cost_per_infra)

        # Floor and ceiling
        monthly_cost = max(50000, min(monthly_cost, 500000))

        total_tsa_cost = monthly_cost * tsa_duration_months

        return total_tsa_cost
```

**Integration into Cost Calculation**:

```python
# In calculate_costs() - add TSA costs for carve-outs
if deal_type == 'carveout':
    tsa_driver = TSACostDriver()
    tsa_cost = tsa_driver.estimate_monthly_tsa_cost(
        inventory_store=inventory_store,
        tsa_duration_months=12  # Default 1 year
    )

    # Add as separate line item
    cost_estimate.tsa_costs = tsa_cost
    cost_estimate.total_cost += tsa_cost
```

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Deal Type Set in UI (web/templates/deal_form.html)          │
│    User selects: Acquisition / Carve-Out / Divestiture         │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. Stored in Database (web/database.py Deal model)             │
│    deal.deal_type = "carveout"                                  │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. Passed to Analysis Runner (web/analysis_runner.py)          │
│    deal_context['deal_type'] = deal.deal_type                  │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. Flows to Cost Calculator (services/cost_engine/calculator.py)│
│    calculate_costs(..., deal_type="carveout")                  │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. Multipliers Applied Per Work Item                           │
│    - Identity work: 2.5x multiplier (carve-out)                 │
│    - Application work: 1.8x multiplier                          │
│    - TSA costs added ($600K over 12 months)                     │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. Return Deal-Aware Cost Estimate                             │
│    Total Cost: $2.4M (vs $1.2M without deal-type awareness)     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Validation

### Test Cases

**File**: `tests/test_cost_engine_deal_awareness.py` (NEW)

```python
import pytest
from services.cost_engine.calculator import calculate_costs
from services.cost_engine.models import get_deal_type_multiplier
from stores.inventory_store import InventoryStore
from models.work_item import WorkItem

class TestDealTypeMultipliers:
    """Test deal type multipliers are applied correctly."""

    def test_acquisition_baseline(self):
        """Acquisition should use 1.0 multipliers (baseline)."""
        multiplier = get_deal_type_multiplier('acquisition', 'identity')
        assert multiplier == 1.0

    def test_carveout_identity_higher(self):
        """Carve-out identity work should cost 2.5x more."""
        multiplier = get_deal_type_multiplier('carveout', 'identity')
        assert multiplier == 2.5

    def test_divestiture_highest(self):
        """Divestiture should have highest multipliers."""
        acq_mult = get_deal_type_multiplier('acquisition', 'identity')
        carve_mult = get_deal_type_multiplier('carveout', 'identity')
        div_mult = get_deal_type_multiplier('divestiture', 'identity')

        assert div_mult > carve_mult > acq_mult

class TestCostCalculationByDealType:
    """Test end-to-end cost calculation respects deal type."""

    def test_same_work_items_different_costs_by_deal_type(self):
        """Same work items should yield different costs for different deal types."""
        # Arrange
        inv_store = InventoryStore(deal_id="test")
        work_items = [
            WorkItem(
                id="WI-001",
                domain="identity",
                title="Separate IAM systems",
                effort_estimate="high"
            )
        ]

        # Act
        acq_cost = calculate_costs(work_items, inv_store, deal_type='acquisition')
        carve_cost = calculate_costs(work_items, inv_store, deal_type='carveout')

        # Assert
        assert carve_cost.total_cost > acq_cost.total_cost
        assert carve_cost.total_cost / acq_cost.total_cost >= 2.0  # At least 2x

    def test_tsa_costs_only_for_carveout(self):
        """TSA costs should only appear for carve-out deals."""
        inv_store = InventoryStore(deal_id="test")
        work_items = []

        acq_cost = calculate_costs(work_items, inv_store, deal_type='acquisition')
        carve_cost = calculate_costs(work_items, inv_store, deal_type='carveout')

        assert acq_cost.tsa_costs == 0
        assert carve_cost.tsa_costs > 0
```

---

## Backward Compatibility

### Default Behavior
- `deal_type` parameter defaults to `"acquisition"` in all functions
- Existing calls WITHOUT `deal_type` parameter continue to work (use 1.0 multipliers)
- No breaking changes to existing cost estimates

### Migration Path
1. **Phase 1**: Add parameter with default (this spec)
2. **Phase 2**: Update all call sites to pass explicit `deal_type` (Spec 05)
3. **Phase 3**: After validation, remove default and make required (Spec 07)

---

## Success Criteria

- [ ] `get_deal_type_multiplier()` function added to `services/cost_engine/models.py`
- [ ] `DEAL_TYPE_MULTIPLIERS` dictionary defined with 3 deal types × 6 categories
- [ ] `calculate_costs()` signature updated with `deal_type` parameter
- [ ] `_calculate_work_item_cost()` applies multipliers correctly
- [ ] TSA cost driver added for carve-out deals
- [ ] All cost calculation call sites updated (costs.py, analysis_runner.py)
- [ ] Test suite covers all 3 deal types × cost variations
- [ ] Carve-out costs are 1.5-3.0x higher than acquisition for same work items
- [ ] TSA costs appear ONLY for carve-outs, not acquisitions

---

## Implementation Notes

### Multiplier Calibration

The multipliers (2.5x for identity, 1.8x for apps, etc.) are **initial estimates** based on:
- Industry M&A separation playbooks
- Typical TSA durations (12-18 months)
- Comparative effort for "build new" vs "extend existing"

**Recommend**: After 10+ deals, analyze actual costs and recalibrate multipliers using regression analysis.

### TSA Duration Variability

Default TSA duration is **12 months**, but this varies widely:
- Simple carve-outs: 6 months
- Complex entanglements: 24+ months
- Regulatory restrictions may extend TSAs

**Future enhancement**: Allow user to specify TSA duration in UI, pass as parameter to cost engine.

### Edge Cases

**Q**: What if a deal is hybrid (e.g., acquire some divisions, carve out others)?
**A**: Current design assumes single deal_type. For hybrid deals, recommend creating SEPARATE Deal records (one per structure) and combining reports manually. Rare enough to defer MVP complexity.

**Q**: What about joint ventures or mergers of equals?
**A**: Not in scope for MVP. Default to "acquisition" type for now.

---

## Files Modified

| File | Lines Changed | Type |
|------|---------------|------|
| `services/cost_engine/models.py` | +80 | New section |
| `services/cost_engine/calculator.py` | ~25 | Signature + logic |
| `services/cost_engine/drivers.py` | +60 | New TSA driver |
| `web/blueprints/costs.py` | ~5 | Add parameter |
| `web/analysis_runner.py` | ~5 | Add parameter |
| `tests/test_cost_engine_deal_awareness.py` | +120 | New file |

**Total**: ~295 lines of code

---

## Dependencies

**Depends On**:
- Spec 01: Deal Type Architecture (entity semantics, taxonomy)

**Blocks**:
- Spec 05: UI Validation (UI needs accurate cost estimates to display)
- Spec 06: Testing (regression tests need deal-aware cost engine)

---

## Estimated Effort

- **Implementation**: 1.5 hours (straightforward parameter threading + multipliers)
- **Testing**: 0.5 hours (write test cases for 3 deal types)
- **Total**: 2 hours

---

**Next Steps**: Proceed to Spec 05 (UI Validation & Enforcement) to ensure deal_type selection is enforced and validated at the UI layer.
