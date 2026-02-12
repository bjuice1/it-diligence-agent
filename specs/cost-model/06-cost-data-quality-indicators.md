# Cost Data Quality Indicators

**Status:** SPECIFICATION
**Version:** 1.0
**Date:** 2026-02-11
**Owner:** IT DD Agent Team

---

## Overview

This document specifies how to add entity-aware quality indicators to the cost model, providing visibility into data completeness and filtering success per entity.

**Purpose:** Help users understand the reliability of cost estimates by showing separate quality scores for buyer vs target data.

**Scope:** Extend `data_quality` dict in `build_cost_center_data()` to report per-entity quality, add UI indicators.

**Problem Solved:** Currently, quality flags are entity-blind (e.g., "applications: high"). Users can't tell if target data is complete but buyer data is missing, or vice versa.

---

## Architecture

### Current State (Entity-Blind Quality)

```
data_quality = {
    "headcount": "medium",
    "applications": "high",
    "infrastructure": "low",
    "one_time": "medium",
}
```

**Problem:** No visibility into per-entity quality. Can't tell if "applications: high" means:
- Both buyer and target have complete data
- Only target has data (buyer missing)
- Mix of complete and incomplete

---

### Target State (Entity-Aware Quality)

```
data_quality = {
    "headcount": {
        "target": "medium",  # Target org facts 80% complete
        "buyer": "none",     # No buyer org facts
        "overall": "low"     # Combined quality suffers
    },
    "applications": {
        "target": "high",    # 95% of expected target apps
        "buyer": "high",     # 90% of expected buyer apps
        "overall": "high"    # Both entities complete
    },
    "infrastructure": {
        "target": "medium",
        "buyer": "low",
        "overall": "medium"
    },
    "one_time": {
        "target": "medium",
        "buyer": "medium",
        "overall": "medium"
    },
    "entity_filter_status": "working"  # NEW: Confirms filtering is operational
}
```

**Benefit:** Clear visibility into data quality per entity. User knows if costs are reliable for each company.

---

## Specification

### 1. Define Quality Assessment Function

**File:** `web/blueprints/costs.py` (add before build_cost_center_data)

```python
def _assess_data_quality_per_entity(
    run_rate: RunRateCosts,
    one_time: OneTimeCosts,
    entity: str
) -> Dict[str, Dict[str, str]]:
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
```

---

### 2. Update build_cost_center_data() to Use New Quality Function

**File:** `web/blueprints/costs.py:562-567`

**Current:**
```python
# Assess data quality
data_quality = {
    "headcount": "medium" if run_rate.headcount.total > 0 else "none",
    "applications": "high" if run_rate.applications.total > 0 else "none",
    "infrastructure": "low" if run_rate.infrastructure.total > 0 else "none",
    "one_time": "medium" if one_time.total_mid > 0 else "none",
}
```

**Target:**
```python
# Assess data quality (entity-aware)
data_quality = _assess_data_quality_per_entity(run_rate, one_time, entity)
```

**Changes:**
1. Replace simple dict with function call
2. Function returns entity-aware quality scores

---

### 3. Add Per-Entity Quality Breakdown (Enhanced)

**If entity == "all", show buyer vs target breakdown:**

```python
def _assess_data_quality_per_entity(
    run_rate: RunRateCosts,
    one_time: OneTimeCosts,
    entity: str,
    inv_store = None  # Optional: pass inventory store for detailed analysis
) -> Dict[str, Dict[str, str]]:
    """Assess data quality per entity."""

    quality = {}

    # If entity == "all" and we have inventory store, break down by entity
    if entity == "all" and inv_store:
        # Get item counts per entity
        target_app_count = len(inv_store.get_items(inventory_type="application", entity="target"))
        buyer_app_count = len(inv_store.get_items(inventory_type="application", entity="buyer"))

        quality["applications"] = {
            "target": "high" if target_app_count > 10 else ("medium" if target_app_count > 0 else "none"),
            "buyer": "high" if buyer_app_count > 10 else ("medium" if buyer_app_count > 0 else "none"),
            "overall": "high" if (target_app_count + buyer_app_count) > 20 else "medium",
            "note": f"{target_app_count} target apps, {buyer_app_count} buyer apps"
        }

        # Similar for other domains...

    else:
        # Single entity mode (simpler quality assessment)
        quality["applications"] = {
            "overall": _quality_level(run_rate.applications.total, [50_000, 500_000, 2_000_000]),
            "note": f"{len(run_rate.applications.items)} applications"
        }

    # [Rest of quality assessment]

    return quality
```

---

### 4. Add Entity Filter Validation

**Add check to confirm entity filtering is working:**

```python
def _validate_entity_filtering(
    run_rate: RunRateCosts,
    entity: str,
    inv_store = None
) -> Dict[str, Any]:
    """Validate that entity filtering is working correctly.

    Returns:
        Validation result with status and details
    """

    if entity == "all":
        return {"status": "skipped", "reason": "Entity filter not applicable for 'all'"}

    if not inv_store:
        return {"status": "unknown", "reason": "Inventory store not available"}

    # Check if applications are correctly filtered
    apps = inv_store.get_items(inventory_type="application", entity=entity, status="active")
    app_entities = [getattr(app, 'entity', None) for app in apps]

    # All apps should match the requested entity
    correct_entity_count = sum(1 for e in app_entities if e == entity)
    wrong_entity_count = sum(1 for e in app_entities if e and e != entity)

    if wrong_entity_count > 0:
        return {
            "status": "warning",
            "reason": f"Found {wrong_entity_count} apps with wrong entity (expected {entity})",
            "correct": correct_entity_count,
            "wrong": wrong_entity_count
        }

    if correct_entity_count == 0:
        return {
            "status": "no_data",
            "reason": f"No applications found for entity={entity}"
        }

    return {
        "status": "working",
        "reason": f"Entity filtering working correctly ({correct_entity_count} apps match {entity})"
    }
```

**Then add to data_quality:**

```python
data_quality = _assess_data_quality_per_entity(run_rate, one_time, entity, inv_store)

# Add entity filter validation
if entity in ["target", "buyer"]:
    data_quality["entity_filter_validation"] = _validate_entity_filtering(
        run_rate, entity, inv_store
    )
```

---

## Verification Strategy

### Unit Tests

**File:** `tests/unit/test_cost_quality_indicators.py` (NEW)

```python
def test_quality_level_thresholds():
    """Quality level calculation based on thresholds."""
    thresholds = [100_000, 500_000, 2_000_000]

    assert _quality_level(0, thresholds) == "none"
    assert _quality_level(50_000, thresholds) == "low"
    assert _quality_level(250_000, thresholds) == "medium"
    assert _quality_level(1_000_000, thresholds) == "high"
    assert _quality_level(5_000_000, thresholds) == "very_high"

def test_assess_data_quality_per_entity():
    """Data quality assessment returns entity-aware scores."""
    run_rate = RunRateCosts(
        headcount=CostCategory(name="headcount", total=2_500_000),
        applications=CostCategory(name="applications", total=1_000_000),
        infrastructure=CostCategory(name="infrastructure", total=50_000),
    )
    one_time = OneTimeCosts(total_mid=500_000)

    quality = _assess_data_quality_per_entity(run_rate, one_time, entity="target")

    assert quality["headcount"]["overall"] in ["high", "very_high"]
    assert quality["applications"]["overall"] == "high"
    assert quality["infrastructure"]["overall"] == "low"
    assert quality["one_time"]["overall"] == "medium"
```

**Expected:** Quality levels calculated correctly based on cost values.

---

### Integration Tests

**File:** `tests/integration/test_cost_center_quality.py` (NEW)

```python
def test_cost_center_quality_indicators(populated_deal):
    """Cost center includes quality indicators."""

    data = build_cost_center_data(entity="target")

    assert "headcount" in data.data_quality
    assert "applications" in data.data_quality
    assert "infrastructure" in data.data_quality
    assert "one_time" in data.data_quality

    # Each should have "overall" quality level
    assert "overall" in data.data_quality["applications"]
    assert data.data_quality["applications"]["overall"] in ["none", "low", "medium", "high", "very_high"]
```

**Expected:** Quality indicators present in cost center data.

---

### Manual Verification

**Scenario 1: Complete Target Data**

1. Load deal with complete target data (apps, org, infra)
2. Navigate to `/costs?entity=target`
3. Check data quality indicators (in UI or API response)
4. **Expected:** Quality scores show "high" or "medium" for most domains

---

**Scenario 2: Incomplete Buyer Data**

1. Load deal with only target data (no buyer)
2. Navigate to `/costs?entity=buyer`
3. Check data quality indicators
4. **Expected:** Quality scores show "none" or "low" (no buyer data)

---

**Scenario 3: Entity Filter Validation**

1. Navigate to `/costs?entity=target`
2. Check `entity_filter_validation` in API response
3. **Expected:** `{"status": "working", "reason": "..."}` (confirms filtering works)

---

## Benefits

### Why Per-Entity Quality Indicators

**Alternative:** Keep single overall quality score.

**Rejected Because:**
- Hides gaps in buyer vs target data
- User can't tell if entity filter is working
- No visibility into data completeness per entity

**Chosen Approach:** Separate quality scores per entity.

**Benefit:** Users know which entity data is reliable, can make informed decisions about estimate confidence.

---

## Expectations

### Success Criteria

1. **data_quality includes per-entity scores** (target, buyer, overall)
2. **Quality levels calculated based on cost values** (thresholds for none/low/medium/high)
3. **Entity filter validation added** (confirms filtering is working)
4. **Unit tests validate quality calculation**
5. **Integration test confirms quality indicators in cost center**
6. **Manual verification shows accurate quality scores**

### Measurable Outcomes

- **Quality Visibility:** Users can see if target data is "high" but buyer data is "none"
- **Filter Confidence:** Entity filter validation status shown (working/warning/no_data)
- **Data Gaps:** Clear indication when costs are unreliable due to missing data

---

## Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Thresholds too strict** | Low | Low | Use conservative thresholds based on typical deal sizes |
| **Quality indicators confusing** | Medium | Low | Add clear notes explaining what each quality level means |
| **Filter validation false positives** | Low | Medium | Only show warning if clear mismatch (>10% wrong entity) |

---

## Results Criteria

### Code Changes Required

**Files Modified:**
1. `web/blueprints/costs.py`
   - Add `_assess_data_quality_per_entity()` function (~50 lines)
   - Add `_quality_level()` helper (~10 lines)
   - Add `_validate_entity_filtering()` function (~30 lines)
   - Update build_cost_center_data() quality assessment (~5 lines)

**Tests Created:**
- `tests/unit/test_cost_quality_indicators.py` — Unit tests (2 test functions)
- `tests/integration/test_cost_center_quality.py` — Integration test (1 test function)

**Estimated Lines Changed:** ~100 lines (95 new, 5 modified)

---

### Acceptance Checklist

- [ ] _assess_data_quality_per_entity() implemented
- [ ] _quality_level() helper implemented
- [ ] _validate_entity_filtering() implemented
- [ ] build_cost_center_data() uses new quality function
- [ ] Quality scores include per-entity breakdown (if entity="all")
- [ ] Entity filter validation added
- [ ] Unit tests created and passing
- [ ] Integration test created and passing
- [ ] Manual verification performed
- [ ] UI displays quality indicators (or API returns them)

---

## Cross-References

- **Depends On:**
  - 02-headcount-entity-filtering.md (headcount filtering must work)
  - 03-one-time-costs-entity-filtering.md (one-time filtering must work)
- **Enables:**
  - 07-integration-testing-strategy.md (validates quality indicators)
- **Related:**
  - 01-entity-aware-cost-engine.md (entity concept in cost model)

---

**IMPLEMENTATION NOTE:** This is a reporting/visibility enhancement. No changes to cost calculations, just better quality indicators. Low risk, high value for user confidence.
