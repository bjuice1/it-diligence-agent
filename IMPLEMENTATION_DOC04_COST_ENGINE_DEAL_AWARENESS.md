# Implementation: Doc 04 - Cost Engine Deal Type Awareness

**Date**: 2026-02-11
**Status**: ✅ COMPLETED
**Spec**: `specs/deal-type-awareness/04-cost-engine-deal-awareness.md`

## Summary

Added deal type awareness to the cost engine so that carveout and divestiture deals apply appropriate cost multipliers (1.5-3.0x higher than acquisition baseline) to reflect the increased complexity of building standalone systems versus simple integration.

## Changes Made

### 1. Added Deal Type Multipliers (`services/cost_engine/models.py`)

**New Constants:**
```python
DEAL_TYPE_MULTIPLIERS = {
    'acquisition': {...},   # 1.0x baseline
    'carveout': {...},      # 1.6-2.5x multipliers
    'divestiture': {...}    # 2.0-3.0x multipliers
}
```

**New Function:**
```python
def get_deal_type_multiplier(deal_type: str, work_item_category: str) -> float
```

**Multiplier Values:**
- **Identity Separation**: 1.0x (acquisition) → 2.5x (carveout) → 3.0x (divestiture)
- **Application Migration**: 1.0x → 1.8x → 2.2x
- **Infrastructure Consolidation**: 1.0x → 2.0x → 2.5x
- **Network Integration**: 1.0x → 2.2x → 2.8x
- **Cybersecurity Harmonization**: 1.0x → 1.9x → 2.3x
- **Organization Restructuring**: 1.0x → 1.6x → 2.0x

### 2. Updated Cost Calculator (`services/cost_engine/calculator.py`)

**Modified Functions:**
- `calculate_cost()` - Added `deal_type` parameter, applies multiplier to adjusted costs
- `calculate_work_item_cost()` - Added `deal_type` parameter, passes through to calculate_cost
- `calculate_deal_costs()` - Added `deal_type` parameter and optional `inventory_store` for TSA
- `calculate_cost_with_volume_discount()` - Added `deal_type` parameter

**Cost Breakdown Updates:**
- Added `'deal_type_multiplier'` to cost breakdown dictionary
- Added deal type to assumptions when not acquisition

**Logging Updates:**
- Enhanced logging to include `deal_type` in cost calculation messages

### 3. Added TSA Cost Driver (`services/cost_engine/drivers.py`)

**New Class:**
```python
class TSACostDriver:
    def estimate_monthly_tsa_cost(self, inventory_store, tsa_duration_months=12) -> float
```

**TSA Cost Logic:**
- Counts shared applications and infrastructure from inventory
- $5K/month per shared application
- $10K/month per shared infrastructure component
- Floor: $50K/month minimum
- Ceiling: $500K/month maximum
- Default duration: 12 months

### 4. Updated Data Models

**CostEstimate** (`services/cost_engine/models.py`):
- Added `tsa_costs: float = 0.0` field
- Updated `to_dict()` to include TSA costs

**DealCostSummary** (`services/cost_engine/calculator.py`):
- Added `total_tsa_costs: float = 0.0` field
- Updated `to_dict()` to include TSA costs
- TSA costs calculated automatically for carveout deals when inventory_store provided

### 5. Comprehensive Test Suite

**New File**: `tests/test_cost_engine_deal_awareness.py`

**Test Coverage** (20 tests, all passing):
- ✅ Deal type multipliers (acquisition=1.0x, carveout=1.6-2.5x, divestiture=2.0-3.0x)
- ✅ All 3 deal types × 6 categories defined
- ✅ Category name aliases (application/applications, org/organization)
- ✅ Invalid deal_type raises ValueError
- ✅ Same work items → different costs by deal type
- ✅ Cost breakdown includes deal_type_multiplier
- ✅ Assumptions include deal type for non-acquisition
- ✅ TSA costs calculated for carveout with inventory
- ✅ TSA costs floor ($50K/month) and ceiling ($500K/month)
- ✅ TSA costs ONLY for carveout, not acquisition
- ✅ Backward compatibility (defaults to acquisition)

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Deal Type Set (web/database.py Deal.deal_type)              │
│    Values: "acquisition", "carveout", "divestiture"            │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. Passed to Cost Calculator                                    │
│    calculate_deal_costs(..., deal_type="carveout")            │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. Multipliers Applied Per Work Item                           │
│    - Identity: 2.5x (carveout) vs 1.0x (acquisition)           │
│    - Applications: 1.8x vs 1.0x                                 │
│    - Network: 2.2x vs 1.0x                                      │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. TSA Costs Added (Carveout Only)                             │
│    - Counts shared apps/infra from inventory                    │
│    - $50K-$500K/month × duration                               │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. Return Deal-Aware Cost Estimate                             │
│    - Carveout: $2.4M (vs $1.2M acquisition)                    │
│    - Includes TSA: $600K over 12 months                        │
└─────────────────────────────────────────────────────────────────┘
```

## Backward Compatibility

✅ **FULLY BACKWARD COMPATIBLE**

- All `deal_type` parameters default to `"acquisition"`
- Existing calls without `deal_type` use 1.0x multipliers (no change)
- No breaking changes to existing cost estimates
- TSA costs only calculated when explicitly provided inventory_store

## Example Usage

```python
from services.cost_engine.calculator import calculate_deal_costs
from services.cost_engine.drivers import DealDrivers, OwnershipType
from stores.inventory_store import InventoryStore

# Create drivers
drivers = DealDrivers(
    entity="target",
    total_users=1000,
    sites=5,
    identity_owned_by=OwnershipType.PARENT
)

# Acquisition (baseline)
acq_costs = calculate_deal_costs(
    deal_id="deal-123",
    drivers=drivers,
    deal_type="acquisition"
)
# Result: ~$1.2M one-time costs

# Carveout (with multipliers + TSA)
inv_store = InventoryStore(deal_id="deal-123")
carve_costs = calculate_deal_costs(
    deal_id="deal-123",
    drivers=drivers,
    deal_type="carveout",
    inventory_store=inv_store
)
# Result: ~$2.4M one-time costs + $600K TSA costs
```

## Success Criteria

All criteria from spec met:

- ✅ `get_deal_type_multiplier()` function added to `services/cost_engine/models.py`
- ✅ `DEAL_TYPE_MULTIPLIERS` dictionary defined with 3 deal types × 6 categories
- ✅ `calculate_cost()` signature updated with `deal_type` parameter
- ✅ Cost calculations apply multipliers correctly
- ✅ TSA cost driver added for carve-out deals
- ✅ Test suite covers all 3 deal types × cost variations
- ✅ Carve-out costs are 1.5-3.0x higher than acquisition for same work items
- ✅ TSA costs appear ONLY for carve-outs, not acquisitions

## Files Modified

| File | Lines Changed | Description |
|------|---------------|-------------|
| `services/cost_engine/models.py` | +80 | DEAL_TYPE_MULTIPLIERS + get_deal_type_multiplier() + tsa_costs field |
| `services/cost_engine/calculator.py` | ~45 | deal_type parameters, multiplier application, TSA integration |
| `services/cost_engine/drivers.py` | +75 | TSACostDriver class |
| `tests/test_cost_engine_deal_awareness.py` | +315 | Comprehensive test suite (20 tests) |

**Total**: ~515 lines of code

## Next Steps

To complete full deal-type awareness system:

1. **Update Call Sites** (Doc 05):
   - `web/blueprints/costs.py` - pass `deal.deal_type` to `calculate_deal_costs()`
   - `web/analysis_runner.py` - pass `deal_context['deal_type']` to cost engine

2. **UI Validation** (Doc 05):
   - Ensure deal_type selection enforced in deal creation forms
   - Display TSA costs separately in cost summaries for carveouts

3. **Reasoning Prompt Updates** (Doc 03):
   - Condition reasoning prompts based on deal_type
   - Guide agents to recommend appropriate work items for carveout vs acquisition

## Testing

Run tests:
```bash
cd "9.5/it-diligence-agent 2"
python -m pytest tests/test_cost_engine_deal_awareness.py -v
```

**Result**: ✅ 20/20 tests passing

## Notes

- Multiplier values (2.5x for identity, 1.8x for apps, etc.) are initial estimates based on industry M&A separation playbooks
- Recommend calibrating multipliers after 10+ deals using regression analysis of actual costs
- TSA duration default is 12 months but varies (6-24+ months depending on complexity)
- Future enhancement: Allow UI to specify TSA duration, pass as parameter
