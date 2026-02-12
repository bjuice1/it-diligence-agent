# Integration Testing Strategy for Cost Model Entity Awareness

**Status:** SPECIFICATION
**Version:** 1.0
**Date:** 2026-02-11
**Owner:** IT DD Agent Team

---

## Overview

This document defines the end-to-end integration testing strategy to validate that all cost model entity awareness features work correctly together.

**Purpose:** Ensure entity filtering, cost calculations, synergy matching, and quality indicators work as a cohesive system across all domains.

**Scope:** Integration test scenarios, test data setup, validation criteria, regression testing approach.

**Problem Solved:** Unit tests validate individual components, but only integration tests can confirm the full cost model works correctly with buyer vs target entity separation.

---

## Architecture

### Test Pyramid

```
E2E Tests (Manual) — 5 scenarios
    ↓
Integration Tests (Automated) — 15 scenarios
    ↓
Unit Tests (Automated) — 40+ scenarios
```

**Focus:** This spec covers **Integration Tests** layer.

---

### Test Scenarios Coverage

**Domains Tested:**
1. Headcount costs (entity filtering)
2. Application costs (entity filtering)
3. Infrastructure costs (entity filtering)
4. One-time costs (entity filtering)
5. Synergies (buyer vs target matching)
6. Quality indicators (per-entity visibility)
7. Cost engine (entity-aware drivers)

**Entity Scenarios:**
- Target-only filtering
- Buyer-only filtering
- All entities combined
- Empty entity (no data for buyer or target)
- Mixed data (target complete, buyer partial)

---

## Specification

### 1. Test Data Setup

**File:** `tests/fixtures/cost_model_test_data.py` (NEW)

```python
"""Test data for cost model integration tests."""

from stores.fact_store import FactStore
from stores.inventory_store import InventoryStore

def create_test_deal_with_buyer_and_target(deal_id: str = "test-deal-001"):
    """Create test deal with both buyer and target data.

    Returns:
        Tuple of (fact_store, inv_store) with populated data
    """

    fact_store = FactStore(deal_id=deal_id)
    inv_store = InventoryStore()

    # ========== TARGET DATA ==========

    # Target: Organization facts (400 users, $2.5M compensation)
    fact_store.add_fact(
        domain="organization",
        category="headcount",
        item="Engineering Team",
        details={"headcount": 25, "total_personnel_cost": 1_500_000},
        entity="target",
        source_document="target_org.pdf"
    )
    fact_store.add_fact(
        domain="organization",
        category="headcount",
        item="DevOps Team",
        details={"headcount": 10, "total_personnel_cost": 1_000_000},
        entity="target",
        source_document="target_org.pdf"
    )

    # Target: Applications (5 apps, $800K annual cost)
    target_apps = [
        ("Salesforce", "crm", 300_000),
        ("NetSuite", "erp", 200_000),
        ("Datadog", "monitoring", 150_000),
        ("GitHub", "development", 100_000),
        ("Okta", "identity", 50_000),
    ]

    for name, category, cost in target_apps:
        fact_store.add_fact(
            domain="applications",
            category=category,
            item=name,
            details={"annual_cost": cost},
            entity="target",
            source_document="target_apps.pdf"
        )
        inv_store.add_item(
            inventory_type="application",
            name=name,
            data={"category": category},
            cost=cost,
            entity="target",
            deal_id=deal_id,
            source_fact_ids=[f"F-APP-{name}"],
        )

    # ========== BUYER DATA ==========

    # Buyer: Organization facts (800 users, $4.2M compensation)
    fact_store.add_fact(
        domain="organization",
        category="headcount",
        item="IT Department",
        details={"headcount": 50, "total_personnel_cost": 4_200_000},
        entity="buyer",
        source_document="buyer_org.pdf"
    )

    # Buyer: Applications (4 apps, $1.2M annual cost, includes Salesforce overlap)
    buyer_apps = [
        ("Salesforce", "crm", 500_000),  # OVERLAP with target
        ("SAP", "erp", 400_000),
        ("Splunk", "monitoring", 200_000),
        ("JumpCloud", "identity", 100_000),
    ]

    for name, category, cost in buyer_apps:
        fact_store.add_fact(
            domain="applications",
            category=category,
            item=name,
            details={"annual_cost": cost},
            entity="buyer",
            source_document="buyer_apps.pdf"
        )
        inv_store.add_item(
            inventory_type="application",
            name=name,
            data={"category": category},
            cost=cost,
            entity="buyer",
            deal_id=deal_id,
            source_fact_ids=[f"F-APP-{name}"],
        )

    return fact_store, inv_store
```

**Benefit:** Consistent test data for all integration tests.

---

### 2. Core Integration Test Suite

**File:** `tests/integration/test_cost_model_entity_awareness.py` (NEW)

```python
import pytest
from web.blueprints.costs import build_cost_center_data
from tests.fixtures.cost_model_test_data import create_test_deal_with_buyer_and_target

@pytest.fixture
def cost_test_deal():
    """Create test deal for cost model testing."""
    return create_test_deal_with_buyer_and_target()

# ========== Test 1: Target Entity Filtering ==========

def test_target_entity_filtering(cost_test_deal):
    """Target entity filter shows only target costs."""
    fact_store, inv_store = cost_test_deal

    # Build cost data for target
    data = build_cost_center_data(entity="target")

    # Headcount: Only target ($2.5M)
    assert data.run_rate.headcount.total == 2_500_000
    assert data.run_rate.headcount.total != 6_700_000  # Not buyer + target

    # Applications: Only target ($800K)
    assert data.run_rate.applications.total == 800_000
    assert data.run_rate.applications.total != 2_000_000  # Not buyer + target

    # Application count: 5 target apps (not 9 total)
    app_items = data.run_rate.applications.items
    assert len(app_items) <= 6  # Allow for criticality grouping
    # Check that Salesforce is included (target version)
    # (Implementation depends on how items are grouped)

# ========== Test 2: Buyer Entity Filtering ==========

def test_buyer_entity_filtering(cost_test_deal):
    """Buyer entity filter shows only buyer costs."""
    fact_store, inv_store = cost_test_deal

    data = build_cost_center_data(entity="buyer")

    # Headcount: Only buyer ($4.2M)
    assert data.run_rate.headcount.total == 4_200_000

    # Applications: Only buyer ($1.2M)
    assert data.run_rate.applications.total == 1_200_000

# ========== Test 3: All Entities Combined ==========

def test_all_entities_combined(cost_test_deal):
    """All entities shows buyer + target combined."""
    fact_store, inv_store = cost_test_deal

    # Get individual entity costs
    data_target = build_cost_center_data(entity="target")
    data_buyer = build_cost_center_data(entity="buyer")
    data_all = build_cost_center_data(entity="all")

    # Headcount: Sum of target + buyer
    assert data_all.run_rate.headcount.total == (
        data_target.run_rate.headcount.total +
        data_buyer.run_rate.headcount.total
    )

    # Applications: Sum of target + buyer
    assert data_all.run_rate.applications.total == (
        data_target.run_rate.applications.total +
        data_buyer.run_rate.applications.total
    )

# ========== Test 4: Synergy Identification ==========

def test_synergies_buyer_target_overlap(cost_test_deal):
    """Synergies identified from buyer vs target overlap."""
    fact_store, inv_store = cost_test_deal

    data = build_cost_center_data(entity="all")

    # Should find Salesforce consolidation synergy
    # (Both buyer and target have Salesforce)
    synergies = data.synergies
    assert len(synergies) > 0

    # Check for CRM or Salesforce synergy
    salesforce_synergy = next(
        (s for s in synergies if "CRM" in s.name or "Salesforce" in s.name),
        None
    )
    assert salesforce_synergy is not None, "Should find Salesforce consolidation synergy"

    # Savings should be reasonable (smaller contract + discount on larger)
    # Target Salesforce: $300K, Buyer Salesforce: $500K
    # Expected savings: $300K + (10-30% of $500K) = $350K-$450K
    assert 300_000 <= salesforce_synergy.annual_savings_low <= 400_000
    assert 450_000 <= salesforce_synergy.annual_savings_high <= 550_000

# ========== Test 5: Quality Indicators ==========

def test_quality_indicators_per_entity(cost_test_deal):
    """Quality indicators show per-entity data completeness."""
    fact_store, inv_store = cost_test_deal

    data = build_cost_center_data(entity="target")

    # Quality indicators should exist
    assert "headcount" in data.data_quality
    assert "applications" in data.data_quality

    # Quality levels should be reasonable (not "none" for target)
    assert data.data_quality["headcount"]["overall"] in ["medium", "high", "very_high"]
    assert data.data_quality["applications"]["overall"] in ["medium", "high", "very_high"]

# ========== Test 6: Empty Entity Handling ==========

def test_empty_entity_graceful_handling(cost_test_deal):
    """Cost model handles entity with no data gracefully."""
    fact_store, inv_store = cost_test_deal

    # Create new deal with only target data (no buyer)
    fact_store_target_only = FactStore(deal_id="target-only-deal")
    # Add only target facts (omitting buyer facts)
    # [Add target org and app facts]

    # Query for buyer (which has no data)
    # NOTE: This test assumes we can override inventory store in build_cost_center_data
    # May need to mock or refactor to support this scenario

    # For now, document expected behavior:
    # - Headcount: $0 for buyer
    # - Applications: $0 for buyer
    # - Quality: "none" for buyer

# ========== Test 7: Cost Engine Entity Propagation ==========

def test_cost_engine_entity_propagation(cost_test_deal):
    """Cost engine propagates entity through calculations."""
    from services.cost_engine import extract_drivers_from_facts, calculate_deal_costs

    fact_store, inv_store = cost_test_deal

    # Extract drivers for target
    drivers_target = extract_drivers_from_facts("test-deal-001", fact_store, entity="target")
    assert drivers_target.drivers.entity == "target"
    assert drivers_target.drivers.total_users == 35  # 25 + 10 from target org facts

    # Extract drivers for buyer
    drivers_buyer = extract_drivers_from_facts("test-deal-001", fact_store, entity="buyer")
    assert drivers_buyer.drivers.entity == "buyer"
    assert drivers_buyer.drivers.total_users == 50  # From buyer org facts

    # Calculate costs with entity-aware drivers
    summary_target = calculate_deal_costs("test-deal-001", drivers_target.drivers)
    assert summary_target.entity == "target"

    summary_buyer = calculate_deal_costs("test-deal-001", drivers_buyer.drivers)
    assert summary_buyer.entity == "buyer"

    # Costs should differ (different user counts)
    assert summary_target.total_one_time_base != summary_buyer.total_one_time_base
```

---

### 3. Regression Test Suite

**File:** `tests/integration/test_cost_model_regression.py` (NEW)

```python
"""Regression tests for cost model — ensure changes don't break existing behavior."""

def test_backward_compatibility_no_entity_param():
    """Cost functions work without entity parameter (default to target)."""
    from web.blueprints.costs import build_cost_center_data

    # Call without entity parameter (backward compatibility)
    data = build_cost_center_data()  # Should default to entity="target"

    # Should not crash
    assert data is not None
    assert data.run_rate is not None

def test_api_endpoint_entity_parameter():
    """Cost API endpoint accepts entity parameter."""
    from flask import Flask
    from web.blueprints.costs import costs_bp

    app = Flask(__name__)
    app.register_blueprint(costs_bp)

    with app.test_client() as client:
        # Test target
        response = client.get('/costs/api/summary?entity=target')
        assert response.status_code == 200
        data = response.get_json()
        assert data['entity'] == 'target'

        # Test buyer
        response = client.get('/costs/api/summary?entity=buyer')
        assert response.status_code == 200
        data = response.get_json()
        assert data['entity'] == 'buyer'

        # Test all
        response = client.get('/costs/api/summary?entity=all')
        assert response.status_code == 200
        data = response.get_json()
        assert data['entity'] == 'all'

def test_cost_totals_consistency():
    """Target + Buyer costs sum to All costs (within rounding)."""
    from web.blueprints.costs import build_cost_center_data

    data_target = build_cost_center_data(entity="target")
    data_buyer = build_cost_center_data(entity="buyer")
    data_all = build_cost_center_data(entity="all")

    # Allow small rounding differences (<1%)
    tolerance = 0.01

    # Run-rate total
    expected_total = data_target.run_rate.total + data_buyer.run_rate.total
    actual_total = data_all.run_rate.total
    diff_pct = abs(actual_total - expected_total) / expected_total if expected_total > 0 else 0

    assert diff_pct < tolerance, f"Run-rate totals don't sum correctly: {diff_pct:.2%} difference"
```

---

### 4. Manual End-to-End Test Scenarios

**Documented scenarios for human testers:**

#### Scenario 1: Complete Buyer + Target Deal

**Setup:**
1. Upload 6 target documents (org, apps, infra)
2. Upload 4 buyer documents (org, apps)
3. Run discovery pipeline
4. Wait for completion (~10 minutes)

**Test Steps:**
1. Navigate to `/costs?entity=target`
2. Verify headcount shows target-only compensation
3. Verify applications shows target-only apps
4. Note total run-rate cost (e.g., $3.3M)

5. Navigate to `/costs?entity=buyer`
6. Verify headcount shows buyer-only compensation
7. Verify applications shows buyer-only apps
8. Note total run-rate cost (e.g., $5.4M)

9. Navigate to `/costs?entity=all`
10. Verify run-rate total ≈ target + buyer (within 5%)
11. Check "Synergy Opportunities" section
12. **Expected:** See consolidation opportunities for overlapping platforms

**Pass Criteria:**
- Target costs < All costs
- Buyer costs < All costs
- Target + Buyer ≈ All (within 5%)
- Synergies identified (1-3 opportunities)

---

#### Scenario 2: Target-Only Deal (No Buyer Data)

**Setup:**
1. Upload only target documents
2. Run discovery

**Test Steps:**
1. Navigate to `/costs?entity=target`
2. **Expected:** Shows target costs normally

3. Navigate to `/costs?entity=buyer`
4. **Expected:** Shows $0 or "No data" message

5. Navigate to `/costs?entity=all`
6. **Expected:** Shows same as target (no buyer data to add)

**Pass Criteria:**
- Buyer query returns zero costs gracefully
- No errors or crashes
- Quality indicators show "none" for buyer

---

#### Scenario 3: Entity Filter Switching

**Setup:**
1. Load complete deal with buyer + target

**Test Steps:**
1. Start at `/costs?entity=target`
2. Click "Buyer" button (or change query param)
3. Verify page updates to show buyer costs
4. Click "All" button
5. Verify page updates to show combined costs
6. Click "Target" button
7. Verify page updates back to target

**Pass Criteria:**
- Costs change when switching entities
- No page reload errors
- URL updates with `?entity=...` param

---

### 5. Performance Testing

**File:** `tests/performance/test_cost_model_performance.py` (OPTIONAL)

```python
import pytest
import time

def test_cost_center_performance_with_large_dataset():
    """Cost center builds in <2 seconds with 1000+ items."""
    from web.blueprints.costs import build_cost_center_data

    # Create large test dataset
    # [Add 500 buyer apps + 500 target apps]

    start = time.time()
    data = build_cost_center_data(entity="all")
    elapsed = time.time() - start

    assert elapsed < 2.0, f"Cost center took {elapsed:.2f}s (expected <2s)"
```

**Expected:** Cost calculations remain fast even with large inventories.

---

## Verification Strategy

### Automated Test Execution

**Run all integration tests:**

```bash
cd "9.5/it-diligence-agent 2"

# Run cost model integration tests
pytest tests/integration/test_cost_model_entity_awareness.py -v

# Run regression tests
pytest tests/integration/test_cost_model_regression.py -v

# Run all integration tests
pytest tests/integration/ -v -k cost
```

**Expected:** All tests pass with 0 failures.

---

### CI/CD Integration

**Add to GitHub Actions workflow:**

```yaml
- name: Run cost model integration tests
  run: |
    cd "9.5/it-diligence-agent 2"
    pytest tests/integration/test_cost_model_entity_awareness.py -v --tb=short
```

---

## Benefits

### Why Integration Tests (Not Just Unit Tests)

**Alternative:** Rely on unit tests for individual functions.

**Rejected Because:**
- Unit tests can't validate cross-component interactions
- Entity filtering touches 6+ functions across multiple files
- Synergy matching depends on inventory + facts + cost calculation
- Only integration tests catch issues like "target + buyer ≠ all"

**Chosen Approach:** Comprehensive integration test suite.

**Benefit:** Confidence that the full cost model works end-to-end.

---

## Expectations

### Success Criteria

1. **7 integration test scenarios created and passing**
2. **Regression tests validate backward compatibility**
3. **Manual E2E scenarios documented**
4. **Performance test confirms <2s for large datasets**
5. **Test data fixtures created for consistency**
6. **All tests pass in CI/CD pipeline**

### Test Coverage Target

- **Integration Tests:** 90% coverage of entity-aware cost flows
- **Unit Tests:** >90% coverage of individual functions (from other specs)
- **Manual E2E:** 100% of user-facing scenarios tested

---

## Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Test data becomes stale** | Medium | Medium | Document how to regenerate test fixtures |
| **Integration tests too slow** | Low | Low | Use minimal test data (5-10 apps per entity) |
| **Flaky tests** | Low | Medium | Use deterministic test data, no LLM calls in tests |
| **Manual tests not run** | Medium | High | Add E2E tests to release checklist |

---

## Results Criteria

### Files Created

**Test Files:**
- `tests/fixtures/cost_model_test_data.py` (~100 lines)
- `tests/integration/test_cost_model_entity_awareness.py` (~200 lines, 7 test functions)
- `tests/integration/test_cost_model_regression.py` (~80 lines, 3 test functions)
- `tests/performance/test_cost_model_performance.py` (~30 lines, 1 test function)

**Documentation:**
- Manual E2E test scenarios (this spec, Scenarios 1-3)

**Estimated Total:** ~410 lines of test code

---

### Acceptance Checklist

- [ ] Test data fixtures created
- [ ] 7 integration test scenarios implemented
- [ ] All integration tests passing
- [ ] Regression tests created and passing
- [ ] Manual E2E scenarios documented
- [ ] Performance test created
- [ ] Tests integrated into CI/CD pipeline
- [ ] Test coverage report generated (>90%)

---

## Cross-References

- **Validates:**
  - 01-entity-aware-cost-engine.md
  - 02-headcount-entity-filtering.md
  - 03-one-time-costs-entity-filtering.md
  - 04-buyer-target-synergy-matching.md
  - 05-deal-id-propagation-audit.md
  - 06-cost-data-quality-indicators.md
- **Depends On:** All other specs (final validation step)
- **Related:**
  - specs/test-validation/07-integration-testing-strategy.md (similar concept for discovery pipeline)

---

**IMPLEMENTATION NOTE:** This is the final validation layer. Do not mark cost model entity awareness as "complete" until all integration tests pass. These tests are the contract for correct behavior.
