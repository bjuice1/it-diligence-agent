# One-Time Costs Entity Filtering

**Status:** SPECIFICATION
**Version:** 1.0
**Date:** 2026-02-11
**Owner:** IT DD Agent Team

---

## Overview

This document specifies how to add entity filtering to `_gather_one_time_costs()` in the cost blueprint, enabling separate integration cost calculations for buyer vs target companies.

**Purpose:** Fix the gap where one-time integration costs currently mix buyer + target work items regardless of entity filter selection.

**Scope:** Modify `web/blueprints/costs.py` _gather_one_time_costs() function to accept entity parameter and filter work items (findings) accordingly.

**Problem Solved:** Currently, one-time integration costs show ALL work items (buyer + target combined), inflating cost estimates. For a target-focused carveout, costs should reflect target-only integration work.

---

## Architecture

### Current State (Entity-Blind)

```
User selects entity="target" in UI
    ↓
build_cost_center_data(entity="target")
    ↓
one_time=_gather_one_time_costs()  ← NO entity parameter!
    ↓
Query: get_work_items() ← Returns ALL work items (buyer + target)
    ↓
One-time total: $500K-$1.2M ← Incorrect (should be target-only)
```

**Problem:** One-time costs include work items for both buyer and target integration, even when user selected "target" entity filter.

**Example:**
- Target has 400 users → Identity separation: $75K + (400 × $15) = $81K
- Buyer has 800 users → Identity separation: $75K + (800 × $15) = $87K
- **Current:** Shows $168K (both combined)
- **Should:** Show $81K (target-only when entity="target")

---

### Target State (Entity-Aware)

```
User selects entity="target" in UI
    ↓
build_cost_center_data(entity="target")
    ↓
one_time=_gather_one_time_costs(entity="target")  ← Pass entity
    ↓
Query: get_work_items(entity="target") ← Filter by entity
    ↓
One-time total: $250K-$600K ← Correct (target-only)
```

**Benefit:** One-time costs match selected entity, reflecting actual integration scope.

---

## Specification

### 1. Understand Work Item Entity Model

**First, verify: Do work items have entity field?**

**File:** `web/database.py` (check Finding model)

**Expected:**
```python
class Finding(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    deal_id = db.Column(db.String(50), nullable=False)
    entity = db.Column(db.String(20))  # ← Check if this exists
    domain = db.Column(db.String(50))
    type = db.Column(db.String(50))  # risk, work_item, gap
    # ...
```

**Scenarios:**

**Scenario A: Work items have entity field directly**
- Easy case — filter work items by `entity == "target"`

**Scenario B: Work items don't have entity field**
- Work items inherit entity from facts they reference
- Filter by joining work item → fact → entity

**Decision:** Assume Scenario B (more likely based on codebase patterns). If entity field exists, simplify to Scenario A.

---

### 2. Update Function Signature

**File:** `web/blueprints/costs.py:308`

**Current:**
```python
def _gather_one_time_costs() -> OneTimeCosts:
    """Gather one-time integration costs from work items and cost engine.

    Phase 2+: Database-first implementation using DealData.
    """
    from flask import session as flask_session
    from web.deal_data import get_deal_data
    from web.context import load_deal_context

    one_time = OneTimeCosts()
```

**Target:**
```python
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
```

**Changes:**
1. Add `entity: str = "target"` parameter
2. Update docstring

---

### 3. Add Entity Filtering to Work Items Query

**File:** `web/blueprints/costs.py:340-350`

**Current:**
```python
# Get work items from database
work_items = data.get_work_items()
```

**Target (Scenario A - Work items have entity field):**
```python
# Get work items from database, filtered by entity
if entity == "all":
    work_items = data.get_work_items()
else:
    # Filter by entity
    work_items = data.get_work_items(entity=entity)
```

**Target (Scenario B - Filter manually via fact entity):**
```python
# Get work items from database
work_items_all = data.get_work_items()

# Filter by entity
if entity == "all":
    work_items = work_items_all
else:
    # Work items inherit entity from their source facts
    work_items = []
    for wi in work_items_all:
        # Check if work item has entity field directly
        wi_entity = getattr(wi, 'entity', None)

        if wi_entity:
            # Work item has entity — use it
            if wi_entity == entity:
                work_items.append(wi)
        else:
            # No direct entity — infer from source facts
            # Most work items are generated from facts in a specific domain
            # Assume work item belongs to entity if its domain facts are that entity
            # SIMPLIFICATION: Skip work items without clear entity (rare edge case)
            # Alternative: Query work_item.source_fact_ids to check fact.entity
            pass  # Skip work items with unclear entity

logger.info(f"Gathering one-time costs for entity={entity}: {len(work_items)} work items")
```

**Refinement (Best Practice):**

If work items have `source_fact_ids` field, use that to determine entity:

```python
# Get work items from database
work_items_all = data.get_work_items()

# Get fact store for entity lookup
fact_store = data.fact_store if hasattr(data, 'fact_store') else None

# Filter by entity
if entity == "all":
    work_items = work_items_all
else:
    work_items = []
    for wi in work_items_all:
        # Option 1: Work item has entity field
        wi_entity = getattr(wi, 'entity', None)
        if wi_entity == entity:
            work_items.append(wi)
            continue

        # Option 2: Infer from source facts
        if fact_store and hasattr(wi, 'source_fact_ids'):
            source_fact_ids = wi.source_fact_ids or []
            if source_fact_ids:
                # Check first source fact's entity
                first_fact = fact_store.get_fact_by_id(source_fact_ids[0])
                if first_fact and getattr(first_fact, 'entity', None) == entity:
                    work_items.append(wi)

logger.info(f"Gathering one-time costs for entity={entity}: {len(work_items)} work items")
```

**Decision:** Use Option 1 (direct entity field) if it exists. Fall back to Option 2 (infer from facts) if needed.

---

### 4. Update Call Site in build_cost_center_data()

**File:** `web/blueprints/costs.py:553`

**Current:**
```python
# Gather one-time costs
one_time = _gather_one_time_costs()
```

**Target:**
```python
# Gather one-time costs
one_time = _gather_one_time_costs(entity=entity)
```

**Changes:**
1. Pass `entity=entity` when calling _gather_one_time_costs()

---

### 5. Handle Empty Results Gracefully

**File:** `web/blueprints/costs.py:340-420`

**Add check after filtering:**

```python
# Filter work items by entity
work_items = filter_work_items_by_entity(work_items_all, entity, fact_store)

logger.info(f"Gathering one-time costs for entity={entity}: {len(work_items)} work items")

# Early return if no work items for this entity
if not work_items:
    logger.info(f"No work items found for entity={entity}")
    one_time.total_low = 0
    one_time.total_mid = 0
    one_time.total_high = 0
    return one_time

# [Rest of existing logic - group by phase, calculate totals]
```

---

### 6. Implement Helper Function for Clarity

**File:** `web/blueprints/costs.py` (add before _gather_one_time_costs)

```python
def _filter_work_items_by_entity(
    work_items: List,
    entity: str,
    fact_store = None
) -> List:
    """Filter work items by entity.

    Work items may have entity field directly, or inherit from source facts.

    Args:
        work_items: List of work item objects
        entity: Entity filter ("target", "buyer", or "all")
        fact_store: Optional fact store for entity inference

    Returns:
        Filtered list of work items
    """
    if entity == "all":
        return work_items

    filtered = []
    for wi in work_items:
        # Check direct entity field
        wi_entity = getattr(wi, 'entity', None)
        if wi_entity == entity:
            filtered.append(wi)
            continue

        # Infer from source facts (if available)
        if fact_store and hasattr(wi, 'source_fact_ids'):
            source_fact_ids = wi.source_fact_ids or []
            if source_fact_ids:
                first_fact = fact_store.get_fact_by_id(source_fact_ids[0])
                if first_fact and getattr(first_fact, 'entity', None) == entity:
                    filtered.append(wi)

    return filtered
```

**Then use in _gather_one_time_costs():**

```python
work_items_all = data.get_work_items()
fact_store = data.fact_store if hasattr(data, 'fact_store') else None

work_items = _filter_work_items_by_entity(work_items_all, entity, fact_store)
```

**Benefit:** Clean separation of concerns, testable function.

---

## Verification Strategy

### Unit Tests

**File:** `tests/unit/test_cost_blueprint_entity.py`

```python
def test_filter_work_items_by_entity_direct():
    """Filter work items by direct entity field."""
    work_items = [
        create_work_item("WI-001", entity="target", cost="100k_to_500k"),
        create_work_item("WI-002", entity="buyer", cost="25k_to_100k"),
        create_work_item("WI-003", entity="target", cost="500k_to_1m"),
    ]

    filtered = _filter_work_items_by_entity(work_items, entity="target", fact_store=None)

    assert len(filtered) == 2
    assert all(wi.entity == "target" for wi in filtered)

def test_filter_work_items_by_entity_all():
    """Entity='all' returns all work items."""
    work_items = [
        create_work_item("WI-001", entity="target"),
        create_work_item("WI-002", entity="buyer"),
    ]

    filtered = _filter_work_items_by_entity(work_items, entity="all", fact_store=None)

    assert len(filtered) == 2

def test_one_time_costs_entity_filtering(mock_deal_data):
    """One-time costs filter by entity."""
    mock_deal_data.get_work_items.return_value = [
        create_work_item("WI-001", entity="target", cost_estimate="100k_to_500k"),
        create_work_item("WI-002", entity="buyer", cost_estimate="100k_to_500k"),
    ]

    # Target only
    one_time_target = _gather_one_time_costs(entity="target")
    assert one_time_target.total_mid > 0
    assert one_time_target.total_mid < one_time_all.total_mid  # Less than all

    # Buyer only
    one_time_buyer = _gather_one_time_costs(entity="buyer")
    assert one_time_buyer.total_mid > 0

    # All
    one_time_all = _gather_one_time_costs(entity="all")
    assert one_time_all.total_mid == one_time_target.total_mid + one_time_buyer.total_mid
```

**Expected:** Tests pass with entity filtering working.

---

### Integration Tests

**File:** `tests/integration/test_cost_center_entity_filtering.py`

```python
def test_cost_center_one_time_entity_separation(populated_deal):
    """Cost center one-time costs respect entity filter."""

    # Build cost data for target
    data_target = build_cost_center_data(entity="target")

    # Build cost data for buyer
    data_buyer = build_cost_center_data(entity="buyer")

    # Build cost data for all
    data_all = build_cost_center_data(entity="all")

    # Verify separation
    assert data_target.one_time.total_mid > 0
    assert data_buyer.one_time.total_mid > 0
    assert abs(
        data_all.one_time.total_mid -
        (data_target.one_time.total_mid + data_buyer.one_time.total_mid)
    ) < 1000  # Allow small rounding differences

    # Verify target < all (proof filtering works)
    assert data_target.one_time.total_mid < data_all.one_time.total_mid
```

**Expected:** One-time costs for target + buyer sum to "all" costs (within rounding).

---

### Manual Verification

**Scenario 1: Target Entity Filter**

1. Load deal with buyer and target work items
2. Navigate to `/costs?entity=target`
3. Check "One-Time Costs" section
4. **Expected:** Cost range shows only target integration work (e.g., $250K-$600K)
5. Verify work item list shows only target items (if displayed)

---

**Scenario 2: Buyer Entity Filter**

1. Navigate to `/costs?entity=buyer`
2. Check "One-Time Costs" section
3. **Expected:** Cost range shows only buyer integration work (e.g., $400K-$900K)
4. Different from target (proof filtering works)

---

**Scenario 3: All Entities**

1. Navigate to `/costs?entity=all`
2. Check "One-Time Costs" section
3. **Expected:** Cost range = target + buyer combined (e.g., $650K-$1.5M)
4. Sum of individual entity ranges

---

**Scenario 4: Empty Entity**

1. Create deal with only target work items (no buyer)
2. Navigate to `/costs?entity=buyer`
3. **Expected:** One-time costs show $0 (no buyer work items)

---

## Benefits

### Why Filter Work Items (Not Recalculate from Drivers)

**Alternative:** Use entity-aware cost engine (spec 01) to recalculate one-time costs from entity-filtered drivers.

**Rejected Because:**
- Work items already exist (generated by reasoning agents)
- Work items may have custom estimates (not formulaic)
- Filtering existing work items preserves reasoning agent output

**Chosen Approach:** Filter existing work items by entity.

**Benefit:** Respects reasoning agent's work item generation (custom estimates, phase assignments, etc.).

---

### Why Infer Entity from Source Facts

**Rationale:** Work items are generated from facts. If a work item references target facts, it's a target work item.

**Benefit:** Works even if work items don't have direct entity field (backward compatible).

---

## Expectations

### Success Criteria

1. **_gather_one_time_costs() accepts entity parameter**
2. **Work items filtered by entity before aggregation**
3. **One-time costs match entity filter** (target shows target-only, buyer shows buyer-only)
4. **Unit tests pass** for filtering logic
5. **Integration test validates** target + buyer = all
6. **Manual verification** confirms UI shows correct costs

### Measurable Outcomes

- **Baseline:** One-time costs always $500K-$1.2M (buyer + target mixed)
- **Target Entity:** One-time costs ~$250K-$600K (target-only)
- **Buyer Entity:** One-time costs ~$400K-$900K (buyer-only)
- **All Entity:** One-time costs $650K-$1.5M (sum of target + buyer, allowing overlap in ranges)

---

## Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Work items missing entity field** | Medium | High | Implement entity inference from source facts as fallback |
| **Work items without source_fact_ids** | Low | Medium | Skip work items with unclear entity (rare edge case) |
| **Cost ranges overlap incorrectly** | Low | Low | Use midpoint for validation (low + high) / 2 |
| **Performance degradation from filtering** | Low | Low | In-memory filtering, negligible overhead |

---

## Results Criteria

### Code Changes Required

**Files Modified:**
1. `web/blueprints/costs.py`
   - Add `_filter_work_items_by_entity()` helper function (~30 lines)
   - Line 308: Add entity parameter to _gather_one_time_costs()
   - Line 340: Add entity filtering to work items query
   - Line 553: Pass entity when calling _gather_one_time_costs()

**Tests Created:**
- `tests/unit/test_cost_blueprint_entity.py` — Unit tests (3 test functions)
- `tests/integration/test_cost_center_entity_filtering.py` — Integration test (1 test function)

**Estimated Lines Changed:** ~50 lines (40 new, 10 modified)

---

### Acceptance Checklist

- [ ] _gather_one_time_costs() signature includes entity parameter
- [ ] Work items filtered by entity before cost calculation
- [ ] build_cost_center_data() passes entity to _gather_one_time_costs()
- [ ] Helper function _filter_work_items_by_entity() implemented
- [ ] Unit tests created and passing
- [ ] Integration test created and passing
- [ ] Manual verification performed (target/buyer/all scenarios)
- [ ] Empty entity case handled gracefully
- [ ] Logging added for visibility (work item count per entity)

---

## Cross-References

- **Depends On:**
  - 01-entity-aware-cost-engine.md (establishes entity filtering pattern)
  - audits/B1_buyer_target_separation.md (entity field exists on facts, may exist on work items)
- **Enables:**
  - 06-cost-data-quality-indicators.md (quality flags depend on correct filtering)
  - 07-integration-testing-strategy.md (validates one-time cost entity filtering)
- **Related:**
  - 02-headcount-entity-filtering.md (similar filtering pattern for org facts)

---

**IMPLEMENTATION NOTE:** Requires investigation of work item entity field. If work items have entity directly, implementation is simple (5-line filter). If not, use source fact entity inference (more complex but robust).
