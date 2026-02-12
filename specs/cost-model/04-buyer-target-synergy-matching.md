# Buyer vs Target Synergy Matching

**Status:** SPECIFICATION
**Version:** 1.0
**Date:** 2026-02-11
**Owner:** IT DD Agent Team

---

## Overview

This document specifies how to redesign `_identify_synergies()` to compare buyer and target applications for consolidation opportunities, replacing the current target-only approach.

**Purpose:** Enable accurate synergy identification by cross-matching buyer and target applications to find overlaps and consolidation opportunities.

**Scope:** Modify `web/blueprints/costs.py` _identify_synergies() function to fetch both buyer and target apps, match by category, calculate savings.

**Problem Solved:** Currently, synergies are identified by looking only at target apps (hardcoded `entity="target"`). This misses opportunities where buyer and target have duplicate platforms (e.g., both have Salesforce → consolidate to one contract).

---

## Architecture

### Current State (Target-Only)

```
_identify_synergies()
    ↓
inv_store.get_items(entity="target")  ← HARDCODED
    ↓
Find duplicates within target apps
    ↓
Synergy: Multiple CRM platforms in target
```

**Problem:** Doesn't compare buyer vs target. Misses cross-entity consolidation opportunities.

**Example Missed Opportunity:**
- Buyer has Salesforce ($500K/year)
- Target has Salesforce ($300K/year)
- **Potential Synergy:** Consolidate to one contract, negotiate volume discount → Save ~$200K-$300K/year
- **Current:** Not detected (only looks at target)

---

### Target State (Buyer vs Target Matching)

```
_identify_synergies()
    ↓
buyer_apps = inv_store.get_items(entity="buyer")
target_apps = inv_store.get_items(entity="target")
    ↓
Match by category (CRM → CRM, ERP → ERP)
    ↓
For each match:
  - Calculate consolidation savings
  - Estimate cost to achieve
  - Assess timeframe
    ↓
Synergy Opportunities (buyer vs target overlaps)
```

**Benefit:** Identifies all consolidation opportunities, including cross-entity duplicates.

---

## Specification

### 1. Update Function Signature

**File:** `web/blueprints/costs.py:430`

**Current:**
```python
def _identify_synergies() -> List[SynergyOpportunity]:
    """Identify cost synergy opportunities from inventory analysis."""
    synergies = []
```

**Target (No signature change needed):**
```python
def _identify_synergies() -> List[SynergyOpportunity]:
    """Identify cost synergy opportunities from buyer vs target inventory.

    Synergies are found by:
    1. Cross-matching buyer and target apps by category
    2. Identifying duplicate platforms
    3. Calculating consolidation savings
    """
    synergies = []
```

**Changes:**
1. Update docstring to clarify buyer vs target matching

---

### 2. Fetch Buyer and Target Apps Separately

**File:** `web/blueprints/costs.py:437-439`

**Current:**
```python
apps = inv_store.get_items(inventory_type="application", entity="target", status="active")
```

**Target:**
```python
# Fetch buyer and target apps separately
buyer_apps = inv_store.get_items(inventory_type="application", entity="buyer", status="active")
target_apps = inv_store.get_items(inventory_type="application", entity="target", status="active")

logger.info(f"Synergy matching: {len(buyer_apps)} buyer apps vs {len(target_apps)} target apps")
```

**Changes:**
1. Fetch buyer apps
2. Fetch target apps (rename from `apps` to `target_apps`)
3. Add logging for visibility

---

### 3. Match Apps by Category

**File:** `web/blueprints/costs.py:441-470` (replace existing logic)

**New Implementation:**

```python
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

logger.info(f"Found {len(overlapping_categories)} overlapping categories for synergy analysis")
```

**Benefit:** Identifies categories where both buyer and target have applications (potential for consolidation).

---

### 4. Calculate Consolidation Synergies

**File:** `web/blueprints/costs.py` (after category matching)

```python
for category in overlapping_categories:
    buyer_apps_in_cat = buyer_by_category[category]
    target_apps_in_cat = target_by_category[category]

    # Calculate total cost in this category
    buyer_cost = sum(app.cost or 0 for app in buyer_apps_in_cat)
    target_cost = sum(app.cost or 0 for app in target_apps_in_cat)
    total_cost = buyer_cost + target_cost

    # Skip if combined cost is too low (no meaningful synergy)
    if total_cost < 100_000:
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
    critical_categories = ['crm', 'erp', 'finance', 'hr']
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
```

**Key Logic:**
- **Savings:** Eliminate smaller contract + volume discount on larger
- **Cost:** Migration effort = 50-200% of smaller contract value
- **Timeframe:** Critical systems take longer (12-18 months vs 6-12 months)
- **Confidence:** Higher for non-critical systems

---

### 5. Add Application-Level Exact Matches (Enhanced)

**Optional Enhancement:** Find exact platform matches (e.g., both have "Salesforce")

```python
# After category-level synergies, add app-level matches
for category in overlapping_categories:
    buyer_apps_in_cat = buyer_by_category[category]
    target_apps_in_cat = target_by_category[category]

    # Find exact name matches
    buyer_names = {app.name.lower(): app for app in buyer_apps_in_cat}
    target_names = {app.name.lower(): app for app in target_apps_in_cat}

    exact_matches = set(buyer_names.keys()) & set(target_names.keys())

    for app_name in exact_matches:
        buyer_app = buyer_names[app_name]
        target_app = target_names[app_name]

        buyer_cost = buyer_app.cost or 0
        target_cost = target_app.cost or 0

        if buyer_cost + target_cost < 50_000:
            continue  # Skip small apps

        # More accurate savings for exact matches
        savings = min(buyer_cost, target_cost) * 0.8  # Keep 80% of smaller contract
        cost_to_achieve = min(buyer_cost, target_cost) * 0.3  # 30% of smaller for migration

        synergies.append(SynergyOpportunity(
            name=f"{app_name.title()} Consolidation",
            category="platform_duplication",
            annual_savings_low=round(savings * 0.7, -3),
            annual_savings_high=round(savings * 1.2, -3),
            cost_to_achieve_low=round(cost_to_achieve * 0.8, -3),
            cost_to_achieve_high=round(cost_to_achieve * 1.5, -3),
            timeframe="6-12 months",
            confidence="high",
            notes=f"Both buyer and target use {app_name} — consolidate to one contract",
            affected_items=[buyer_app.name, target_app.name]
        ))
```

**Benefit:** More granular synergies for exact platform duplicates.

---

## Verification Strategy

### Unit Tests

**File:** `tests/unit/test_synergy_matching.py` (NEW)

```python
import pytest
from web.blueprints.costs import _identify_synergies, SynergyOpportunity
from stores.inventory_store import InventoryStore

def test_identify_synergies_buyer_target_overlap():
    """Identify synergies from buyer vs target category overlap."""
    inv_store = InventoryStore()

    # Buyer has Salesforce
    inv_store.add_item(
        inventory_type="application",
        name="Salesforce",
        data={"category": "crm"},
        cost=500_000,
        entity="buyer",
        deal_id="test-deal",
    )

    # Target has Salesforce
    inv_store.add_item(
        inventory_type="application",
        name="Salesforce",
        data={"category": "crm"},
        cost=300_000,
        entity="target",
        deal_id="test-deal",
    )

    synergies = _identify_synergies()

    # Should find CRM consolidation synergy
    assert len(synergies) > 0
    crm_synergy = next((s for s in synergies if "CRM" in s.name or "Salesforce" in s.name), None)
    assert crm_synergy is not None
    assert crm_synergy.annual_savings_low > 0

def test_identify_synergies_no_overlap():
    """No synergies when buyer and target have different categories."""
    inv_store = InventoryStore()

    # Buyer has CRM
    inv_store.add_item(
        inventory_type="application",
        name="Salesforce",
        data={"category": "crm"},
        cost=500_000,
        entity="buyer",
        deal_id="test-deal",
    )

    # Target has ERP (different category)
    inv_store.add_item(
        inventory_type="application",
        name="NetSuite",
        data={"category": "erp"},
        cost=300_000,
        entity="target",
        deal_id="test-deal",
    )

    synergies = _identify_synergies()

    # Should find no synergies (no overlap)
    assert len(synergies) == 0

def test_synergy_savings_calculation():
    """Verify synergy savings calculation logic."""
    inv_store = InventoryStore()

    # Buyer: $400K, Target: $200K in same category
    inv_store.add_item(
        inventory_type="application",
        name="BuyerApp",
        data={"category": "analytics"},
        cost=400_000,
        entity="buyer",
        deal_id="test-deal",
    )
    inv_store.add_item(
        inventory_type="application",
        name="TargetApp",
        data={"category": "analytics"},
        cost=200_000,
        entity="target",
        deal_id="test-deal",
    )

    synergies = _identify_synergies()

    analytics_synergy = synergies[0]

    # Savings = smaller contract ($200K) + volume discount on larger (10-30% of $400K)
    # Low: $200K + $40K = $240K
    # High: $200K + $120K = $320K
    assert 200_000 <= analytics_synergy.annual_savings_low <= 250_000
    assert 300_000 <= analytics_synergy.annual_savings_high <= 350_000
```

**Expected:** Tests pass with correct synergy identification and savings calculation.

---

### Integration Tests

**File:** `tests/integration/test_cost_center_synergies.py` (NEW)

```python
def test_cost_center_synergies_buyer_target(populated_deal):
    """Cost center identifies synergies from buyer vs target overlap."""

    data = build_cost_center_data(entity="all")  # Need both entities for synergies

    assert len(data.synergies) > 0
    total_synergy_potential = sum(s.annual_savings_high for s in data.synergies)
    assert total_synergy_potential > 0
```

**Expected:** Synergies identified when both buyer and target have apps.

---

### Manual Verification

**Scenario 1: Exact Platform Match**

1. Load deal where buyer and target both have "Salesforce"
2. Navigate to `/costs?entity=all`
3. Scroll to "Synergy Opportunities" section
4. **Expected:** See "Salesforce Consolidation" or "CRM Platform Consolidation" synergy
5. **Verify:** Savings amount is reasonable (e.g., $200K-$300K for $500K+$300K total)

---

**Scenario 2: Category Match (No Exact Name)**

1. Load deal where:
   - Buyer has "HubSpot" (CRM, $300K)
   - Target has "Salesforce" (CRM, $400K)
2. Navigate to `/costs?entity=all`
3. **Expected:** See "CRM Platform Consolidation" synergy (category-level match)
4. **Verify:** Savings calculated based on consolidating to one platform

---

**Scenario 3: No Overlaps**

1. Load deal where:
   - Buyer has only CRM apps
   - Target has only ERP apps (no overlap)
2. Navigate to `/costs?entity=all`
3. **Expected:** Synergies section shows "No consolidation opportunities identified" or empty list

---

## Benefits

### Why Category-Based Matching

**Alternative:** Semantic matching using LLM to find similar apps (e.g., "Salesforce" vs "HubSpot" both are CRM).

**Rejected Because:**
- Adds complexity (LLM calls, non-deterministic)
- Category classification already exists (`app_category_mappings.py`)
- Good enough for v1 (can enhance later)

**Chosen Approach:** Simple category matching (CRM → CRM, ERP → ERP).

**Benefit:** Fast, deterministic, easy to verify. Catches 80% of synergies without AI overhead.

---

### Why Savings = Smaller Contract + Discount

**Rationale:**
- Can't eliminate both contracts (need one platform to survive)
- Smaller contract is easier to migrate away from
- Consolidating volume to one vendor → negotiate discount

**Benefit:** Conservative estimate that's defensible in IC presentations.

---

## Expectations

### Success Criteria

1. **_identify_synergies() fetches both buyer and target apps**
2. **Category-level matching identifies overlaps**
3. **Synergies calculated with savings and costs**
4. **Unit tests validate matching logic**
5. **Integration test confirms synergies appear in cost center**
6. **Manual verification shows realistic synergy opportunities**

### Measurable Outcomes

- **Baseline:** Synergies only within target (misses buyer vs target overlaps)
- **Target:** Synergies include buyer vs target consolidation opportunities
- **Example:** Salesforce consolidation synergy identified when both buyer and target have it

---

## Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Overestimated savings** | Medium | Medium | Use conservative savings model (10% volume discount), document assumptions |
| **Underestimated cost to achieve** | Medium | Medium | Use range (50-200% of smaller contract), flag critical systems as higher cost |
| **Category misclassification** | Low | Low | Synergies are estimates, not guarantees. Review opportunities manually. |
| **No buyer or target apps** | Low | Low | Handle gracefully (return empty synergies list) |

---

## Results Criteria

### Code Changes Required

**Files Modified:**
1. `web/blueprints/costs.py`
   - Line 437: Fetch buyer and target apps separately
   - Line 441-470: Replace existing logic with buyer vs target matching
   - Add category grouping logic (~20 lines)
   - Add consolidation synergy calculation (~40 lines)

**Tests Created:**
- `tests/unit/test_synergy_matching.py` — Unit tests (3 test functions)
- `tests/integration/test_cost_center_synergies.py` — Integration test (1 test function)

**Estimated Lines Changed:** ~80 lines (60 new, 20 modified)

---

### Acceptance Checklist

- [ ] _identify_synergies() fetches buyer apps
- [ ] _identify_synergies() fetches target apps
- [ ] Category-level grouping implemented
- [ ] Consolidation synergy calculation implemented
- [ ] Exact name matching implemented (optional enhancement)
- [ ] Unit tests created and passing
- [ ] Integration test created and passing
- [ ] Manual verification performed (exact match, category match, no overlap scenarios)
- [ ] Synergies appear in cost center UI
- [ ] Logging added for debugging (overlap count, synergy count)

---

## Cross-References

- **Depends On:**
  - 01-entity-aware-cost-engine.md (establishes entity concept)
  - 02-headcount-entity-filtering.md (pattern for entity filtering)
  - 03-one-time-costs-entity-filtering.md (pattern for entity filtering)
- **Enables:**
  - 07-integration-testing-strategy.md (validates synergy matching)
- **Related:**
  - stores/app_category_mappings.py (category classification used for matching)

---

**IMPLEMENTATION NOTE:** This is new logic (not just filtering). Requires careful testing to verify savings calculations are reasonable. Conservative assumptions preferred for IC presentation credibility.
