# Entity-Aware Cost Engine Architecture

**Status:** SPECIFICATION
**Version:** 1.0
**Date:** 2026-02-11
**Owner:** IT DD Agent Team

---

## Overview

This document specifies how to add entity awareness to the cost engine module (`services/cost_engine/`), enabling separate cost calculations for buyer vs target companies in M&A transactions.

**Purpose:** Allow cost engine to calculate one-time integration costs, annual licenses, and run-rate deltas separately for buyer and target entities.

**Scope:** Modifications to core cost engine dataclasses (DealDrivers, CostEstimate, DealCostSummary) and calculator functions to accept and propagate entity dimension.

**Problem Solved:** Currently, cost engine assumes single-entity deals (target-only carveouts). For M&A transactions with both buyer and target data, costs are calculated without entity separation, leading to inflated estimates and inability to model separate integration paths.

---

## Architecture

### Current State (Entity-Blind)

```
FactStore (mixed buyer + target facts)
    ↓
extract_drivers_from_facts()  ← NO entity filtering
    ↓
DealDrivers (total_users=1200)  ← buyer + target combined
    ↓
calculate_deal_costs()
    ↓
DealCostSummary (total_one_time_base=$2.5M)  ← inflated
```

**Problem:** If buyer has 800 users and target has 400 users, DealDrivers.total_users=1200. Cost calculations use 1200 for per-user costs when they should use 400 (target only) for a target-focused carveout.

---

### Target State (Entity-Aware)

```
FactStore (all facts tagged with entity)
    ↓
extract_drivers_from_facts(entity="target")  ← filter by entity
    ↓
DealDrivers(total_users=400, entity="target")
    ↓
calculate_deal_costs(drivers, entity="target")
    ↓
DealCostSummary(entity="target", total_one_time_base=$1.2M)  ← accurate
```

**Benefit:** Costs calculated based on correct entity scope. Can model separate buyer and target integration scenarios.

---

### Component Dependencies

**Affected Files:**
- `services/cost_engine/drivers.py` — Add entity field to DealDrivers dataclass
- `services/cost_engine/models.py` — Add entity field to CostEstimate dataclass
- `services/cost_engine/calculator.py` — Add entity field to DealCostSummary, propagate through calculations
- `services/cost_engine/__init__.py` — Update exports (no breaking changes)

**Downstream Consumers (require updates):**
- `web/blueprints/costs.py` — Pass entity when calling calculate_deal_costs()
- `tools_v2/cost_estimator.py` (if exists) — Pass entity when extracting drivers
- Any cost reporting tools that consume DealCostSummary

---

## Specification

### 1. Add Entity to DealDrivers Dataclass

**File:** `services/cost_engine/drivers.py`

**Current:**
```python
@dataclass
class DealDrivers:
    """Quantitative drivers extracted from facts."""

    # User/employee metrics
    total_users: Optional[int] = None
    erp_users: Optional[int] = None
    endpoints: Optional[int] = None

    # Infrastructure
    servers: Optional[int] = None
    vms: Optional[int] = None
    sites: Optional[int] = None
    data_centers: Optional[int] = None

    # Systems
    erp_system: Optional[str] = None
    total_apps: Optional[int] = None

    # Ownership
    identity_owned_by: Optional[OwnershipType] = None
    wan_owned_by: Optional[OwnershipType] = None
    soc_owned_by: Optional[OwnershipType] = None
    erp_owned_by: Optional[OwnershipType] = None
    dc_owned_by: Optional[OwnershipType] = None

    # Shared services
    shared_with_parent: List[str] = field(default_factory=list)

    # Source tracking
    sources: Dict[str, DriverSource] = field(default_factory=dict)
```

**Target:**
```python
@dataclass
class DealDrivers:
    """Quantitative drivers extracted from facts."""

    # Entity dimension (NEW)
    entity: str = "target"  # "target", "buyer", or "all"

    # User/employee metrics
    total_users: Optional[int] = None
    erp_users: Optional[int] = None
    endpoints: Optional[int] = None

    # [Rest unchanged]

    def __post_init__(self):
        """Validate entity field."""
        allowed_entities = ["target", "buyer", "all"]
        if self.entity not in allowed_entities:
            raise ValueError(f"entity must be one of {allowed_entities}, got: {self.entity}")
```

**Changes:**
1. Add `entity: str = "target"` field as first field (defaults to "target" for backward compatibility)
2. Add `__post_init__()` validation to enforce allowed values
3. Update docstring to mention entity filtering

**Backward Compatibility:** Existing code that creates DealDrivers() without entity param will default to "target", preserving current behavior.

---

### 2. Update extract_drivers_from_facts() to Accept Entity Filter

**File:** `services/cost_engine/drivers.py`

**Current Signature:**
```python
def extract_drivers_from_facts(
    deal_id: str,
    fact_store: FactStore
) -> DriverExtractionResult:
    """Extract quantitative drivers from fact store."""
```

**Target Signature:**
```python
def extract_drivers_from_facts(
    deal_id: str,
    fact_store: FactStore,
    entity: str = "target"  # NEW parameter
) -> DriverExtractionResult:
    """Extract quantitative drivers from fact store.

    Args:
        deal_id: The deal ID
        fact_store: Fact store to extract from
        entity: Entity filter ("target", "buyer", or "all")

    Returns:
        DriverExtractionResult with entity-filtered drivers
    """
```

**Implementation Changes:**

1. **Filter facts by entity before extraction:**

```python
def extract_drivers_from_facts(
    deal_id: str,
    fact_store: FactStore,
    entity: str = "target"
) -> DriverExtractionResult:
    """Extract quantitative drivers from fact store."""

    # Validate entity
    if entity not in ["target", "buyer", "all"]:
        raise ValueError(f"Invalid entity: {entity}")

    # Filter facts by entity
    if entity == "all":
        filtered_facts = fact_store.get_all_facts()
    else:
        # Get facts matching this entity only
        filtered_facts = [
            f for f in fact_store.get_all_facts()
            if getattr(f, 'entity', None) == entity
        ]

    logger.info(f"Extracting drivers for entity={entity}: {len(filtered_facts)} facts")

    # Extract drivers from filtered facts
    drivers = DealDrivers(entity=entity)  # Set entity on result

    # [Rest of extraction logic uses filtered_facts instead of all facts]
    # ... existing logic for extracting total_users, servers, etc.

    return DriverExtractionResult(
        drivers=drivers,
        extracted_count=extracted,
        assumed_count=assumed,
        # ... other fields
    )
```

2. **Entity-aware queries for specific metrics:**

```python
# Example: Extract total_users
org_facts = [f for f in filtered_facts if f.domain == "organization"]
total_users = 0
for fact in org_facts:
    headcount = fact.details.get('headcount', 0)
    if isinstance(headcount, int):
        total_users += headcount

drivers.total_users = total_users if total_users > 0 else None
```

**Key Change:** All driver extraction queries operate on `filtered_facts` (entity-filtered) instead of `fact_store.get_all_facts()`.

---

### 3. Add Entity to CostEstimate Dataclass

**File:** `services/cost_engine/models.py`

**Current:**
```python
@dataclass
class CostEstimate:
    """Result of cost calculation."""
    work_item_type: str
    display_name: str
    tower: str

    # One-time costs by scenario
    one_time_upside: float = 0.0
    one_time_base: float = 0.0
    one_time_stress: float = 0.0

    # Annual license costs
    annual_licenses: float = 0.0
    run_rate_delta: float = 0.0

    # [Rest of fields]
```

**Target:**
```python
@dataclass
class CostEstimate:
    """Result of cost calculation."""
    work_item_type: str
    display_name: str
    tower: str

    # Entity dimension (NEW)
    entity: str = "target"

    # One-time costs by scenario
    one_time_upside: float = 0.0
    one_time_base: float = 0.0
    one_time_stress: float = 0.0

    # [Rest unchanged]

    def to_dict(self) -> Dict:
        return {
            'work_item_type': self.work_item_type,
            'display_name': self.display_name,
            'tower': self.tower,
            'entity': self.entity,  # Include in serialization
            'one_time': {
                'upside': self.one_time_upside,
                # ...
            },
            # [Rest of to_dict() unchanged]
        }
```

**Changes:**
1. Add `entity: str = "target"` field
2. Update `to_dict()` to include entity in serialization

---

### 4. Add Entity to DealCostSummary Dataclass

**File:** `services/cost_engine/calculator.py`

**Current:**
```python
@dataclass
class DealCostSummary:
    """Aggregated cost summary for a deal."""
    deal_id: str

    # Totals by scenario
    total_one_time_upside: float = 0.0
    total_one_time_base: float = 0.0
    total_one_time_stress: float = 0.0
    total_annual_licenses: float = 0.0
    total_run_rate_delta: float = 0.0

    # [Rest of fields]
```

**Target:**
```python
@dataclass
class DealCostSummary:
    """Aggregated cost summary for a deal."""
    deal_id: str

    # Entity dimension (NEW)
    entity: str = "target"

    # Totals by scenario
    total_one_time_upside: float = 0.0
    total_one_time_base: float = 0.0
    total_one_time_stress: float = 0.0
    total_annual_licenses: float = 0.0
    total_run_rate_delta: float = 0.0

    # [Rest unchanged]

    def to_dict(self) -> Dict:
        return {
            'deal_id': self.deal_id,
            'entity': self.entity,  # Include in serialization
            'totals': {
                'one_time': {
                    'upside': self.total_one_time_upside,
                    # ...
                },
                # [Rest of to_dict() unchanged]
            }
        }
```

**Changes:**
1. Add `entity: str = "target"` field
2. Update `to_dict()` to include entity

---

### 5. Update calculate_cost() to Propagate Entity

**File:** `services/cost_engine/calculator.py`

**Current Signature:**
```python
def calculate_cost(
    model: CostModel,
    drivers: DealDrivers,
    complexity_override: Optional[Complexity] = None,
) -> CostEstimate:
```

**Target Implementation:**
```python
def calculate_cost(
    model: CostModel,
    drivers: DealDrivers,
    complexity_override: Optional[Complexity] = None,
) -> CostEstimate:
    """Calculate cost estimate for a single work item type.

    Entity is read from drivers.entity and propagated to result.
    """

    # [Existing calculation logic unchanged]

    # Determine complexity
    complexity = complexity_override or assess_complexity(model.work_item_type, drivers)

    # [Calculate costs using drivers.total_users, drivers.sites, etc.]

    # Create CostEstimate with entity from drivers
    return CostEstimate(
        work_item_type=model.work_item_type.value,
        display_name=model.display_name,
        tower=model.tower,
        entity=drivers.entity,  # NEW: Propagate entity from drivers
        one_time_upside=round(one_time_upside, -3),
        one_time_base=round(one_time_base, -3),
        one_time_stress=round(one_time_stress, -3),
        annual_licenses=round(annual_licenses, -2),
        run_rate_delta=round(run_rate_delta, -2),
        # [Rest of fields unchanged]
    )
```

**Key Change:** Read `drivers.entity` and set `entity=drivers.entity` on returned CostEstimate.

---

### 6. Update calculate_deal_costs() to Accept and Propagate Entity

**File:** `services/cost_engine/calculator.py`

**Current Signature:**
```python
def calculate_deal_costs(
    deal_id: str,
    drivers: DealDrivers,
    work_item_types: Optional[List[str]] = None,
) -> DealCostSummary:
```

**Target Implementation:**
```python
def calculate_deal_costs(
    deal_id: str,
    drivers: DealDrivers,
    work_item_types: Optional[List[str]] = None,
) -> DealCostSummary:
    """Calculate costs for all applicable work items in a deal.

    Entity is read from drivers.entity and propagated to summary.
    """

    # Create summary with entity from drivers
    summary = DealCostSummary(
        deal_id=deal_id,
        entity=drivers.entity  # NEW: Propagate entity
    )

    # [Rest of calculation logic unchanged]
    # Each calculate_work_item_cost() call will use drivers.entity internally

    for wit_str in types_to_calc:
        estimate = calculate_work_item_cost(wit_str, drivers)
        if estimate:
            summary.estimates.append(estimate)
            # [Aggregate totals]

    logger.info(
        f"Deal {deal_id} costs for entity={drivers.entity}: "
        f"${summary.total_one_time_base:,.0f} base, "
        f"${summary.total_annual_licenses:,.0f}/yr licenses, "
        f"{len(summary.estimates)} work items"
    )

    return summary
```

**Key Changes:**
1. Pass `entity=drivers.entity` when creating DealCostSummary
2. Update log message to include entity for visibility

---

### 7. Update get_effective_drivers() Wrapper

**File:** `services/cost_engine/drivers.py`

**Current:**
```python
def get_effective_drivers(
    deal_id: str,
    fact_store: Optional[FactStore] = None
) -> DriverExtractionResult:
    """Get effective drivers (extracted + overrides applied)."""
```

**Target:**
```python
def get_effective_drivers(
    deal_id: str,
    fact_store: Optional[FactStore] = None,
    entity: str = "target"  # NEW parameter
) -> DriverExtractionResult:
    """Get effective drivers (extracted + overrides applied).

    Args:
        deal_id: The deal ID
        fact_store: Optional fact store (loads from DB if None)
        entity: Entity filter ("target", "buyer", or "all")

    Returns:
        DriverExtractionResult with entity-filtered drivers
    """

    # Load fact store if not provided
    if fact_store is None:
        fact_store = _load_fact_store_from_db(deal_id)

    # Extract drivers with entity filter
    result = extract_drivers_from_facts(deal_id, fact_store, entity=entity)

    # Apply any driver overrides (entity-independent)
    drivers = result.drivers
    overrides = DriverOverride.query.filter_by(
        deal_id=deal_id,
        active=True
    ).all()

    for override in overrides:
        if hasattr(drivers, override.driver_name):
            setattr(drivers, override.driver_name, override.override_value)

    return result
```

**Key Change:** Add entity parameter, pass to extract_drivers_from_facts().

---

## Verification Strategy

### Unit Tests

**File:** `tests/unit/test_cost_engine_entity.py` (NEW)

```python
import pytest
from services.cost_engine import (
    DealDrivers,
    CostEstimate,
    DealCostSummary,
    calculate_cost,
    calculate_deal_costs,
    get_model,
    WorkItemType,
)

def test_deal_drivers_entity_field():
    """DealDrivers has entity field with default."""
    drivers = DealDrivers(total_users=500)
    assert drivers.entity == "target"

def test_deal_drivers_entity_validation():
    """DealDrivers validates entity values."""
    with pytest.raises(ValueError, match="entity must be one of"):
        DealDrivers(entity="invalid")

def test_cost_estimate_includes_entity():
    """CostEstimate includes entity field."""
    model = get_model(WorkItemType.IDENTITY_SEPARATION.value)
    drivers = DealDrivers(total_users=500, sites=3, entity="buyer")

    estimate = calculate_cost(model, drivers)

    assert estimate.entity == "buyer"
    assert "entity" in estimate.to_dict()

def test_deal_cost_summary_includes_entity():
    """DealCostSummary includes entity field."""
    drivers = DealDrivers(total_users=500, entity="target")
    summary = calculate_deal_costs("test-deal", drivers)

    assert summary.entity == "target"
    assert summary.to_dict()["entity"] == "target"

def test_entity_propagates_through_calculation():
    """Entity propagates from drivers → estimates → summary."""
    drivers = DealDrivers(
        total_users=400,
        sites=2,
        endpoints=400,
        entity="buyer"  # Set to buyer
    )

    summary = calculate_deal_costs("test-deal", drivers)

    # Summary has buyer entity
    assert summary.entity == "buyer"

    # All estimates have buyer entity
    for estimate in summary.estimates:
        assert estimate.entity == "buyer"
```

**Expected:** All tests pass with entity field working correctly.

---

### Integration Tests

**File:** `tests/integration/test_cost_engine_entity_filtering.py` (NEW)

```python
import pytest
from stores.fact_store import FactStore
from services.cost_engine import extract_drivers_from_facts

def test_entity_filtering_in_driver_extraction(sample_facts):
    """extract_drivers_from_facts filters by entity."""
    fact_store = FactStore(deal_id="test-deal")

    # Add target facts (400 users)
    fact_store.add_fact(
        domain="organization",
        category="headcount",
        item="IT Staff",
        details={"headcount": 400},
        entity="target"
    )

    # Add buyer facts (800 users)
    fact_store.add_fact(
        domain="organization",
        category="headcount",
        item="IT Staff",
        details={"headcount": 800},
        entity="buyer"
    )

    # Extract for target only
    result_target = extract_drivers_from_facts("test-deal", fact_store, entity="target")
    assert result_target.drivers.entity == "target"
    assert result_target.drivers.total_users == 400  # Not 1200

    # Extract for buyer only
    result_buyer = extract_drivers_from_facts("test-deal", fact_store, entity="buyer")
    assert result_buyer.drivers.entity == "buyer"
    assert result_buyer.drivers.total_users == 800

    # Extract for all
    result_all = extract_drivers_from_facts("test-deal", fact_store, entity="all")
    assert result_all.drivers.entity == "all"
    assert result_all.drivers.total_users == 1200  # Combined
```

**Expected:** Entity filtering correctly separates buyer vs target facts during driver extraction.

---

### Manual Verification

**Scenario 1: Target-Only Cost Calculation**

1. Load deal with target facts (400 users, 2 sites)
2. Call `get_effective_drivers(deal_id, entity="target")`
3. Verify `drivers.total_users == 400` (not inflated by buyer data)
4. Call `calculate_deal_costs(deal_id, drivers)`
5. Verify `summary.entity == "target"`
6. Verify all estimates have `entity == "target"`
7. Check cost totals match expected for 400 users

**Expected:** Costs calculated based on target-only driver values.

---

**Scenario 2: Buyer Cost Calculation**

1. Same deal, call `get_effective_drivers(deal_id, entity="buyer")`
2. Verify `drivers.total_users == 800` (buyer headcount)
3. Calculate costs
4. Verify `summary.entity == "buyer"`
5. Verify cost totals higher than target (more users)

**Expected:** Separate cost calculation for buyer entity.

---

**Scenario 3: Backward Compatibility**

1. Call `get_effective_drivers(deal_id)` (no entity param)
2. Verify defaults to `entity="target"`
3. Verify costs match previous behavior

**Expected:** Existing code works unchanged, defaults to target.

---

## Benefits

### Why Add Entity to Dataclasses (Not Separate Parameters)

**Alternative Considered:** Pass entity as separate parameter to all functions.

**Rejected Because:**
- Entity is a property of the data (drivers represent target OR buyer)
- Passing separately leads to mismatches (drivers from target, entity="buyer")
- Dataclass approach is type-safe and self-documenting

**Chosen Approach:** Entity lives in DealDrivers, propagates automatically.

**Benefit:** Impossible to create CostEstimate for "buyer" using target drivers — entity is bound to the data.

---

### Why Default to "target"

**Rationale:** Due diligence is about the target company (what you're buying). Buyer data is context.

**Benefit:** Backward compatibility — existing code continues working without changes.

---

## Expectations

### Success Criteria

1. **DealDrivers has entity field** with validation (target/buyer/all)
2. **extract_drivers_from_facts() filters by entity** correctly
3. **CostEstimate includes entity** field
4. **DealCostSummary includes entity** field
5. **Entity propagates** from drivers → estimates → summary
6. **Backward compatibility preserved** (defaults to "target")

### Measurable Outcomes

- **Zero breaking changes:** Existing cost calculations work unchanged
- **Correct filtering:** Target costs use target driver values (not buyer+target mixed)
- **Entity visibility:** All cost API responses include entity field
- **Test coverage:** >90% for new entity-related code paths

---

## Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Existing code breaks from new required field** | Low | High | Entity has default="target", making it optional for existing callers |
| **Driver extraction logic too complex** | Medium | Medium | Use simple list comprehension filtering, log filtered fact count for debugging |
| **Overrides don't work with entity filtering** | Low | Medium | Overrides apply AFTER entity filtering, so they work on entity-specific drivers |
| **Performance degradation from filtering** | Low | Low | Entity filtering is in-memory list comprehension, negligible overhead |

---

## Results Criteria

### Code Changes Required

**Files Modified:**
1. `services/cost_engine/drivers.py`
   - Add entity field to DealDrivers
   - Update extract_drivers_from_facts() signature and implementation
   - Update get_effective_drivers() signature

2. `services/cost_engine/models.py`
   - Add entity field to CostEstimate
   - Update to_dict() method

3. `services/cost_engine/calculator.py`
   - Add entity field to DealCostSummary
   - Update calculate_cost() to propagate entity
   - Update calculate_deal_costs() to propagate entity
   - Update to_dict() method

4. `services/cost_engine/__init__.py`
   - No changes (exports remain same)

**Tests Created:**
- `tests/unit/test_cost_engine_entity.py` (5 test functions)
- `tests/integration/test_cost_engine_entity_filtering.py` (1 test function)

**Estimated Lines Changed:** ~150 lines (50 new, 100 modified)

---

### Acceptance Checklist

- [ ] DealDrivers.entity field exists with default="target"
- [ ] DealDrivers.__post_init__() validates entity values
- [ ] extract_drivers_from_facts() accepts entity parameter
- [ ] extract_drivers_from_facts() filters facts by entity before extraction
- [ ] CostEstimate.entity field exists
- [ ] CostEstimate.to_dict() includes entity
- [ ] DealCostSummary.entity field exists
- [ ] DealCostSummary.to_dict() includes entity
- [ ] calculate_cost() propagates entity from drivers to estimate
- [ ] calculate_deal_costs() propagates entity from drivers to summary
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Manual verification scenarios pass
- [ ] Backward compatibility verified (existing code works)

---

## Cross-References

- **Depends On:** audit1 findings (Root Cause #1 - entity dimension missing from cost engine)
- **Enables:**
  - 02-headcount-entity-filtering.md (needs entity-aware foundation)
  - 03-one-time-costs-entity-filtering.md (needs entity-aware foundation)
  - 04-buyer-target-synergy-matching.md (needs entity concept for buyer vs target comparison)
- **Related:**
  - 07-integration-testing-strategy.md (will validate entity propagation end-to-end)

---

**IMPLEMENTATION NOTE:** This is the foundational change. All other cost model entity awareness specs (02-06) depend on this being implemented first. Do not proceed to downstream specs until this spec is validated and working.
