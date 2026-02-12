# Headcount Cost Entity Filtering

**Status:** SPECIFICATION
**Version:** 1.0
**Date:** 2026-02-11
**Owner:** IT DD Agent Team

---

## Overview

This document specifies how to add entity filtering to `_gather_headcount_costs()` in the cost blueprint, enabling separate headcount cost calculations for buyer vs target companies.

**Purpose:** Fix the gap where headcount costs currently mix buyer + target data regardless of entity filter selection.

**Scope:** Modify `web/blueprints/costs.py` _gather_headcount_costs() function to accept entity parameter and filter organization facts accordingly.

**Problem Solved:** Currently, selecting "Target" or "Buyer" entity filter works for applications and infrastructure costs, but headcount costs always show the TOTAL of buyer + target combined, breaking entity separation.

---

## Architecture

### Current State (Entity-Blind)

```
User selects entity="target" in UI
    ↓
build_cost_center_data(entity="target")
    ↓
headcount=_gather_headcount_costs()  ← NO entity parameter!
    ↓
Query: get_organization() ← Returns ALL org facts (buyer + target)
    ↓
Headcount total: $6.75M ← Incorrect (should be target-only)
```

**Problem:** Even though user selected "target", headcount shows total compensation for buyer + target combined.

---

### Target State (Entity-Aware)

```
User selects entity="target" in UI
    ↓
build_cost_center_data(entity="target")
    ↓
headcount=_gather_headcount_costs(entity="target")  ← Pass entity
    ↓
Query: get_organization(entity="target") ← Filter by entity
    ↓
Headcount total: $2.5M ← Correct (target-only)
```

**Benefit:** Headcount costs match selected entity, consistent with applications and infrastructure filtering.

---

## Specification

### 1. Update Function Signature

**File:** `web/blueprints/costs.py:134`

**Current:**
```python
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
```

**Target:**
```python
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
```

**Changes:**
1. Add `entity: str = "target"` parameter (defaults to "target" for backward compatibility)
2. Update docstring to document entity parameter

---

### 2. Add Entity Filtering to Org Facts Query

**File:** `web/blueprints/costs.py:158-161`

**Current:**
```python
# Get organization facts from database
org_facts = data.get_organization()
```

**Target (Option A - DealData API supports entity):**
```python
# Get organization facts from database, filtered by entity
if entity == "all":
    org_facts = data.get_organization()  # No filter
else:
    org_facts = data.get_organization(entity=entity)  # Filter by entity
```

**Target (Option B - DealData doesn't support entity, filter manually):**
```python
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
```

**Decision:** Use Option B (manual filtering) — safer assumption, works regardless of DealData API support.

**Changes:**
1. Fetch all org facts first
2. Filter list by entity field
3. Add logging for visibility

---

### 3. Update Call Site in build_cost_center_data()

**File:** `web/blueprints/costs.py:545`

**Current:**
```python
def build_cost_center_data(entity: str = "target") -> CostCenterData:
    """Build complete cost center data from all sources.

    Args:
        entity: Entity filter ("target", "buyer", or "all")
    """

    # Gather run-rate costs
    run_rate = RunRateCosts(
        headcount=_gather_headcount_costs(),  # ← Not passing entity!
        applications=_gather_application_costs(entity=entity),
        infrastructure=_gather_infrastructure_costs(entity=entity),
        vendors_msp=CostCategory(name="vendors_msp", display_name="Vendors & MSP", icon="🤝")
    )
```

**Target:**
```python
def build_cost_center_data(entity: str = "target") -> CostCenterData:
    """Build complete cost center data from all sources.

    Args:
        entity: Entity filter ("target", "buyer", or "all")
    """

    # Gather run-rate costs
    run_rate = RunRateCosts(
        headcount=_gather_headcount_costs(entity=entity),  # ← Pass entity
        applications=_gather_application_costs(entity=entity),
        infrastructure=_gather_infrastructure_costs(entity=entity),
        vendors_msp=CostCategory(name="vendors_msp", display_name="Vendors & MSP", icon="🤝")
    )
```

**Changes:**
1. Pass `entity=entity` when calling _gather_headcount_costs()

---

### 4. Handle Empty Results Gracefully

**File:** `web/blueprints/costs.py:163-195`

**Add check after filtering:**

```python
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

# Early return if no facts for this entity
if not org_facts:
    logger.info(f"No organization facts found for entity={entity}")
    category.calculate_totals()  # Total will be 0
    return category

# [Rest of existing logic - group by role category, etc.]
```

**Benefit:** Clean handling when entity has no org facts (e.g., buyer-only query when only target data exists).

---

## Verification Strategy

### Unit Tests

**File:** `tests/unit/test_cost_blueprint_entity.py` (NEW or ADD TO EXISTING)

```python
import pytest
from web.blueprints.costs import _gather_headcount_costs, CostCategory

def test_headcount_costs_default_entity(mock_deal_data):
    """Headcount costs default to target entity."""
    # Mock DealData to return org facts with entity tags
    mock_deal_data.get_organization.return_value = [
        create_org_fact("Engineering", headcount=10, cost=1_500_000, entity="target"),
        create_org_fact("Engineering", headcount=20, cost=3_000_000, entity="buyer"),
    ]

    # Call without entity parameter (should default to "target")
    category = _gather_headcount_costs()

    assert category.total == 1_500_000  # Only target costs
    assert category.total != 4_500_000  # Not buyer + target

def test_headcount_costs_buyer_entity(mock_deal_data):
    """Headcount costs filter to buyer entity."""
    mock_deal_data.get_organization.return_value = [
        create_org_fact("Engineering", headcount=10, cost=1_500_000, entity="target"),
        create_org_fact("Engineering", headcount=20, cost=3_000_000, entity="buyer"),
    ]

    category = _gather_headcount_costs(entity="buyer")

    assert category.total == 3_000_000  # Only buyer costs

def test_headcount_costs_all_entity(mock_deal_data):
    """Headcount costs include all entities when entity='all'."""
    mock_deal_data.get_organization.return_value = [
        create_org_fact("Engineering", headcount=10, cost=1_500_000, entity="target"),
        create_org_fact("Engineering", headcount=20, cost=3_000_000, entity="buyer"),
    ]

    category = _gather_headcount_costs(entity="all")

    assert category.total == 4_500_000  # Buyer + target combined

def test_headcount_costs_empty_entity(mock_deal_data):
    """Headcount costs handle entity with no facts gracefully."""
    mock_deal_data.get_organization.return_value = [
        create_org_fact("Engineering", headcount=10, cost=1_500_000, entity="target"),
    ]

    # Query for buyer (no buyer org facts exist)
    category = _gather_headcount_costs(entity="buyer")

    assert category.total == 0  # No costs for buyer
    assert len(category.items) == 0  # No line items
```

**Expected:** All tests pass with entity filtering working correctly.

---

### Integration Tests

**File:** `tests/integration/test_cost_center_entity_filtering.py` (NEW)

```python
import pytest
from web.blueprints.costs import build_cost_center_data

def test_cost_center_headcount_entity_separation(populated_deal):
    """Cost center headcount respects entity filter."""

    # Build cost data for target
    data_target = build_cost_center_data(entity="target")

    # Build cost data for buyer
    data_buyer = build_cost_center_data(entity="buyer")

    # Build cost data for all
    data_all = build_cost_center_data(entity="all")

    # Verify separation
    assert data_target.run_rate.headcount.total > 0
    assert data_buyer.run_rate.headcount.total > 0
    assert data_all.run_rate.headcount.total == (
        data_target.run_rate.headcount.total + data_buyer.run_rate.headcount.total
    )

    # Verify target != all (proof that filtering works)
    assert data_target.run_rate.headcount.total < data_all.run_rate.headcount.total
```

**Expected:** Headcount costs for target + buyer sum to "all" costs.

---

### Manual Verification

**Scenario 1: Target Entity Filter**

1. Load deal with buyer and target org facts
2. Navigate to `/costs?entity=target` in browser
3. Check "IT Headcount" section in run-rate costs
4. **Expected:** Headcount costs show only target compensation (e.g., $2.5M)
5. Verify total run-rate matches (headcount + apps + infra for target)

---

**Scenario 2: Buyer Entity Filter**

1. Navigate to `/costs?entity=buyer`
2. Check "IT Headcount" section
3. **Expected:** Headcount costs show only buyer compensation (e.g., $4.2M)
4. Different from target (proof filtering works)

---

**Scenario 3: All Entities**

1. Navigate to `/costs?entity=all`
2. Check "IT Headcount" section
3. **Expected:** Headcount costs = target + buyer combined (e.g., $6.7M)
4. Matches sum of individual entity queries

---

**Scenario 4: API Response Verification**

```bash
# Test API endpoint
curl http://localhost:5001/costs/api/summary?entity=target | jq '.run_rate.headcount'
# Expected: Target headcount cost

curl http://localhost:5001/costs/api/summary?entity=buyer | jq '.run_rate.headcount'
# Expected: Buyer headcount cost (different value)

curl http://localhost:5001/costs/api/summary?entity=all | jq '.run_rate.headcount'
# Expected: Sum of target + buyer
```

---

## Benefits

### Why Filter at Query Time (Not at Data Layer)

**Alternative:** Add entity parameter to DealData.get_organization() API.

**Rejected Because:**
- DealData API may not support entity filtering yet
- Manual filtering works immediately (no dependencies)
- Easy to verify (explicit list comprehension)

**Chosen Approach:** Filter facts after retrieval.

**Benefit:** Works regardless of DealData API capabilities. Can optimize later if needed.

---

### Why Default to "target"

**Rationale:** Consistent with applications and infrastructure filtering (all default to "target").

**Benefit:** Backward compatibility — existing calls without entity param work as before.

---

## Expectations

### Success Criteria

1. **_gather_headcount_costs() accepts entity parameter**
2. **Org facts filtered by entity before aggregation**
3. **Headcount costs match entity filter** (target shows target-only, buyer shows buyer-only)
4. **Unit tests pass** for all entity scenarios
5. **Integration test validates** target + buyer = all
6. **Manual verification** confirms UI shows correct costs

### Measurable Outcomes

- **Baseline:** Headcount costs always $6.75M (buyer + target mixed)
- **Target Entity:** Headcount costs ~$2.5M (target-only)
- **Buyer Entity:** Headcount costs ~$4.2M (buyer-only)
- **All Entity:** Headcount costs $6.75M (sum of target + buyer)

---

## Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Org facts missing entity field** | Low | High | Check audit B1 — entity should be enforced. Add validation if missing. |
| **DealData.get_organization() returns None** | Low | Medium | Early return with empty category if no facts found |
| **Entity filtering breaks existing code** | Low | Low | Default entity="target" preserves current behavior |
| **Performance degradation from filtering** | Low | Low | Filtering is in-memory list comprehension, negligible overhead |

---

## Results Criteria

### Code Changes Required

**Files Modified:**
1. `web/blueprints/costs.py`
   - Line 134: Add entity parameter to _gather_headcount_costs()
   - Line 158: Add entity filtering to org facts query
   - Line 545: Pass entity when calling _gather_headcount_costs()

**Tests Created:**
- `tests/unit/test_cost_blueprint_entity.py` — Unit tests (4 test functions)
- `tests/integration/test_cost_center_entity_filtering.py` — Integration test (1 test function)

**Estimated Lines Changed:** ~20 lines (10 new, 10 modified)

---

### Acceptance Checklist

- [ ] _gather_headcount_costs() signature includes entity parameter
- [ ] Org facts filtered by entity before aggregation
- [ ] build_cost_center_data() passes entity to _gather_headcount_costs()
- [ ] Unit tests created and passing
- [ ] Integration test created and passing
- [ ] Manual verification performed (target/buyer/all scenarios)
- [ ] API endpoint returns correct headcount costs per entity
- [ ] Logging added for visibility (entity filter applied, fact count)

---

## Cross-References

- **Depends On:**
  - 01-entity-aware-cost-engine.md (establishes entity filtering pattern)
  - audits/B1_buyer_target_separation.md (entity field exists on org facts)
- **Enables:**
  - 06-cost-data-quality-indicators.md (quality flags depend on correct filtering)
  - 07-integration-testing-strategy.md (validates headcount entity filtering)
- **Related:**
  - 03-one-time-costs-entity-filtering.md (similar pattern for work items)

---

**IMPLEMENTATION NOTE:** This is a straightforward extension of the existing entity filtering pattern used in applications and infrastructure. Should take ~1-2 hours to implement and test.
