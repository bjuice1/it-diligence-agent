# BUILD MANIFEST: Cost Model Entity Awareness

**Build Type:** TYPE B - Multi-Component Build
**Status:** READY FOR EXECUTION
**Date:** 2026-02-11
**Owner:** IT DD Agent Team

---

## Executive Summary

This manifest defines the complete build plan for adding entity awareness to the cost model, enabling separate cost calculations for buyer vs target companies in M&A transactions.

**Problem:** Cost model currently mixes buyer and target data, inflating estimates and preventing accurate synergy identification.

**Solution:** Add entity dimension to cost engine, filter all cost calculations by entity (target/buyer/all), enable buyer vs target synergy matching.

**Build Duration:** 12-16 hours (1.5-2 days for solo developer)
**Complexity:** MEDIUM-HIGH (architectural changes, multi-file modifications)
**Dependencies:** pytest, Flask, SQLAlchemy, existing cost engine, inventory store

---

## Document Index

### Specification Documents (7 total)

1. **[01-entity-aware-cost-engine.md](01-entity-aware-cost-engine.md)** — Add entity dimension to cost engine dataclasses and calculations (FOUNDATIONAL)

2. **[02-headcount-entity-filtering.md](02-headcount-entity-filtering.md)** — Fix _gather_headcount_costs() to filter by entity

3. **[03-one-time-costs-entity-filtering.md](03-one-time-costs-entity-filtering.md)** — Fix _gather_one_time_costs() to filter by entity

4. **[04-buyer-target-synergy-matching.md](04-buyer-target-synergy-matching.md)** — Design synergy algorithm that compares buyer vs target

5. **[05-deal-id-propagation-audit.md](05-deal-id-propagation-audit.md)** — Audit and fix missing deal_id in inventory items

6. **[06-cost-data-quality-indicators.md](06-cost-data-quality-indicators.md)** — Add entity-aware quality flags and visibility

7. **[07-integration-testing-strategy.md](07-integration-testing-strategy.md)** — End-to-end validation of entity-filtered costs

---

## Execution Order

### Phase 1: Foundation (3 hours)

**Doc 01: Entity-Aware Cost Engine** (CRITICAL PATH - must go first)
- Add entity field to DealDrivers, CostEstimate, DealCostSummary
- Update extract_drivers_from_facts() to filter by entity
- Update calculate_cost() and calculate_deal_costs() to propagate entity
- **Files:** services/cost_engine/drivers.py, models.py, calculator.py
- **Lines Changed:** ~150 lines
- **Tests:** tests/unit/test_cost_engine_entity.py (5 tests)

**Doc 05: deal_id Propagation Audit** (PARALLEL - independent)
- Audit bridge services for missing deal_id propagation
- Fix applications_bridge.py, organization_bridge.py
- Add strict validation to InventoryStore.add_item()
- **Files:** services/*_bridge.py, stores/inventory_store.py
- **Lines Changed:** ~80 lines
- **Tests:** tests/integration/test_deal_id_propagation.py (1 test)

**Phase 1 Deliverable:** Cost engine is entity-aware, deal_id contamination fixed

---

### Phase 2: Cost Filtering (4 hours)

**Doc 02: Headcount Entity Filtering** (PARALLEL)
- Add entity parameter to _gather_headcount_costs()
- Filter org facts by entity
- Update call site in build_cost_center_data()
- **Files:** web/blueprints/costs.py (3 locations)
- **Lines Changed:** ~20 lines
- **Tests:** tests/unit/test_cost_blueprint_entity.py (4 tests)

**Doc 03: One-Time Costs Entity Filtering** (PARALLEL)
- Add entity parameter to _gather_one_time_costs()
- Filter work items by entity (direct field or infer from facts)
- Update call site in build_cost_center_data()
- **Files:** web/blueprints/costs.py (3 locations + helper function)
- **Lines Changed:** ~50 lines
- **Tests:** tests/unit/test_cost_blueprint_entity.py (3 tests)

**Phase 2 Deliverable:** Headcount and one-time costs filter correctly by entity

---

### Phase 3: Synergies (3 hours)

**Doc 04: Buyer vs Target Synergy Matching** (SERIAL - depends on Phase 1+2)
- Fetch buyer and target apps separately
- Match apps by category
- Calculate consolidation synergies (savings + cost to achieve)
- **Files:** web/blueprints/costs.py (_identify_synergies function)
- **Lines Changed:** ~80 lines
- **Tests:** tests/unit/test_synergy_matching.py (3 tests)

**Phase 3 Deliverable:** Synergies identify buyer vs target overlaps

---

### Phase 4: Quality & Testing (3 hours)

**Doc 06: Cost Data Quality Indicators** (PARALLEL)
- Add _assess_data_quality_per_entity() function
- Add _validate_entity_filtering() function
- Update build_cost_center_data() quality assessment
- **Files:** web/blueprints/costs.py (3 new functions)
- **Lines Changed:** ~100 lines
- **Tests:** tests/unit/test_cost_quality_indicators.py (2 tests)

**Doc 07: Integration Testing Strategy** (PARALLEL)
- Create test data fixtures
- Write 7 integration test scenarios
- Write 3 regression tests
- Document manual E2E scenarios
- **Files:** tests/integration/, tests/fixtures/
- **Lines Changed:** ~410 lines (test code)
- **Tests:** 10 integration tests, 3 regression tests

**Phase 4 Deliverable:** Quality indicators working, all tests passing

---

### Critical Path Summary

```
Phase 1: Doc 01 (entity-aware cost engine) - 3 hours
    ↓
Phase 2: Doc 02 + Doc 03 (cost filtering) - 4 hours
    ↓
Phase 3: Doc 04 (synergy matching) - 3 hours
    ↓
Phase 4: Doc 06 + Doc 07 (quality + testing) - 3 hours

Total Critical Path: 13 hours

Parallel Work:
  Doc 05 (deal_id audit) - 2 hours (can run anytime)

Total Elapsed: 12-16 hours (depending on parallelization)
```

---

## Tech Stack

**Languages:**
- Python 3.11

**Frameworks:**
- Flask 3.0+ (web blueprint)
- SQLAlchemy 2.0 (ORM, if work items persisted)

**Testing:**
- pytest
- pytest-cov (coverage reporting)

**Dependencies:**
- stores/inventory_store.py (inventory data access)
- stores/fact_store.py (fact data access)
- services/cost_engine/ (driver extraction, cost calculation)
- web/blueprints/costs.py (cost blueprint)

**Rationale:** Extends existing cost model architecture. No new dependencies required. Uses established patterns from entity separation work (audit B1).

---

## Validation Checklist

Before starting implementation, validate:

- [ ] **Work items have entity field** (or can infer from source facts)
  - Check: `web/database.py` Finding model
  - Mitigation: Use source fact entity inference (spec 03)

- [ ] **Org facts have entity field** and are populated
  - Check: Query facts WHERE domain='organization' and verify entity
  - Mitigation: Entity backfill (from audit B1)

- [ ] **InventoryStore.get_items() supports entity filtering**
  - Check: `stores/inventory_store.py` get_items signature
  - Confirmed: Already working (from audit1 evidence)

- [ ] **Cost cache doesn't break entity filtering**
  - Check: `tools_v2/cost_cache.py` for cache keys
  - Mitigation: Add entity to cache keys if needed

**Verification Completed:** ✅ (audit1 confirmed InventoryStore entity filtering works)

---

## Risk Register

| Risk | Impact | Probability | Mitigation | Status |
|------|--------|-------------|------------|--------|
| **Work items missing entity field** | High | Medium | Implement entity inference from source facts (spec 03) | Planned |
| **Facts missing entity** | High | Low | Audit B1 enforces entity on facts (NOT NULL constraint) | Mitigated |
| **Cost engine changes break existing code** | High | Low | Entity defaults to "target" (backward compatible) | Mitigated |
| **Synergy savings overestimated** | Medium | Medium | Use conservative model (10% discount), document assumptions | Mitigated |
| **Integration tests flaky** | Low | Low | Use deterministic test data, no LLM calls | Mitigated |
| **deal_id audit finds unknown creation paths** | Medium | Medium | Comprehensive grep for add_item() calls | Planned |

---

## Scope Estimate

### By Component

| Component | Effort | Confidence | Files | Lines |
|-----------|--------|------------|-------|-------|
| **01: Cost Engine** | 3 hours | Medium | 3 | ~150 |
| **02: Headcount** | 1.5 hours | High | 1 | ~20 |
| **03: One-Time** | 2 hours | Medium | 1 | ~50 |
| **04: Synergies** | 3 hours | Medium | 1 | ~80 |
| **05: deal_id Audit** | 2 hours | Medium | 5-8 | ~80 |
| **06: Quality** | 1 hour | High | 1 | ~100 |
| **07: Testing** | 1.5 hours | High | 4 | ~410 |
| **Buffer** | 2-3 hours | - | - | - |

**Total Estimate:** 12-16 hours with MEDIUM confidence

**Complexity Breakdown:**
- **Hardest:** 01 (foundational cost engine changes) — HIGH
- **Moderate:** 04 (synergy algorithm), 05 (deal_id audit) — MEDIUM
- **Easy:** 02, 03, 06, 07 (filtering and validation) — LOW

**Team Size:** Solo (1 developer can execute sequentially)

---

## Open Questions

**Q1: Do work items (findings) have an entity field?**
- **Impact:** Spec 03 implementation
- **Default Answer:** If NO, filter via source fact entity (spec provides fallback)
- **Resolution:** Check `web/database.py` Finding model before implementing spec 03

**Q2: Where exactly are inventory items created without deal_id?**
- **Impact:** Spec 05 audit scope
- **Default Answer:** Bridge services (applications_bridge.py, organization_bridge.py)
- **Resolution:** Grep for add_item() calls, trace one item creation

**Q3: Should synergy calculation be category-based or semantic (LLM)?**
- **Impact:** Spec 04 complexity
- **Default Answer:** Category-based (simple, deterministic, good enough for v1)
- **Resolution:** Decided — category matching (can enhance later)

**Q4: Should entity be in DealDrivers or passed as parameter?**
- **Impact:** Spec 01 architecture
- **Default Answer:** Add to DealDrivers dataclass (cleaner, self-documenting)
- **Resolution:** Decided — entity as dataclass field

**All critical questions resolved. Ready to execute.**

---

## Rollback Criteria

Abandon this approach and return to audit1 if:

1. **Cost engine changes break >50% of existing tests**
   - Mitigation: Entity defaults to "target", should be backward compatible
   - Rollback: Revert spec 01 changes, redesign with parameter approach

2. **Performance degradation >50% (cost calculations take >4s)**
   - Mitigation: Entity filtering is in-memory, should be negligible
   - Rollback: Add caching layer, optimize filtering

3. **Integration tests fail >30% of scenarios**
   - Mitigation: Tests validate requirements, failures = bugs to fix
   - Rollback: Only if systematic design flaw discovered (not bugs)

**Rollback Plan:** Git revert commits from most recent to oldest (Phase 4 → Phase 1).

---

## Next Steps

**Immediate Actions:**

1. **Validate assumptions** (Q1, Q2 above) — 15 minutes
   ```bash
   # Check work items entity field
   grep -n "class Finding" web/database.py
   grep -n "entity" web/database.py | grep -A2 -B2 "Finding"

   # Find inventory item creation points
   grep -rn "add_item" services/ | grep -v ".pyc"
   ```

2. **Set up project structure** — 5 minutes
   ```bash
   # Create test directories
   mkdir -p tests/unit/cost_model
   mkdir -p tests/integration/cost_model
   mkdir -p tests/fixtures
   ```

3. **Begin implementation** following execution order:
   - Start with Doc 01 (entity-aware cost engine) — CRITICAL PATH
   - Parallel: Doc 05 (deal_id audit)
   - Then Docs 02 + 03 (cost filtering)
   - Then Doc 04 (synergies)
   - Finally Docs 06 + 07 (quality + testing)

**Implementation Strategy:** Incremental, test-driven

- Write tests first (from spec verification sections)
- Implement feature to make tests pass
- Manually verify in UI
- Move to next spec

**Success Criteria:** All 7 specs implemented, all tests passing (90% coverage), manual E2E scenarios validated.

---

## File Inventory

### Specifications Created (7 documents, ~137KB)

| File | Size | Purpose |
|------|------|---------|
| 00-build-manifest.md | This file | Master build plan and execution guide |
| 01-entity-aware-cost-engine.md | ~22KB | Add entity to cost engine dataclasses |
| 02-headcount-entity-filtering.md | ~16KB | Filter headcount costs by entity |
| 03-one-time-costs-entity-filtering.md | ~18KB | Filter one-time costs by entity |
| 04-buyer-target-synergy-matching.md | ~19KB | Compare buyer vs target for synergies |
| 05-deal-id-propagation-audit.md | ~20KB | Audit and fix missing deal_id |
| 06-cost-data-quality-indicators.md | ~17KB | Add entity-aware quality flags |
| 07-integration-testing-strategy.md | ~21KB | End-to-end validation tests |

---

### Implementation Files (To Be Created)

**Core Cost Model:**
- services/cost_engine/drivers.py (modify, +50 lines)
- services/cost_engine/models.py (modify, +20 lines)
- services/cost_engine/calculator.py (modify, +30 lines)
- web/blueprints/costs.py (modify, +250 lines)

**Bridge Services:**
- services/applications_bridge.py (modify, +10 lines)
- services/organization_bridge.py (modify, +10 lines)
- stores/inventory_store.py (modify, +15 lines)

**Tests:**
- tests/unit/test_cost_engine_entity.py (new, ~100 lines)
- tests/unit/test_cost_blueprint_entity.py (new, ~150 lines)
- tests/unit/test_synergy_matching.py (new, ~80 lines)
- tests/unit/test_cost_quality_indicators.py (new, ~50 lines)
- tests/integration/test_cost_model_entity_awareness.py (new, ~200 lines)
- tests/integration/test_cost_model_regression.py (new, ~80 lines)
- tests/integration/test_deal_id_propagation.py (new, ~50 lines)
- tests/fixtures/cost_model_test_data.py (new, ~100 lines)

**Total Estimated Lines of Code:** ~1,370 lines (870 production, 500 test)

---

## Success Metrics

### Functional Validation

- [ ] **Target costs ≠ All costs** (proof filtering works)
- [ ] **Buyer costs ≠ All costs** (proof filtering works)
- [ ] **Target + Buyer ≈ All** (within 5%, validates aggregation)
- [ ] **Synergies identify buyer vs target overlaps** (e.g., Salesforce consolidation)
- [ ] **Zero "created without deal_id" warnings** (data isolation fixed)
- [ ] **Quality indicators show per-entity scores** (visibility into completeness)

### Technical Validation

- [ ] **All unit tests pass** (40+ tests)
- [ ] **All integration tests pass** (10 tests)
- [ ] **All regression tests pass** (3 tests)
- [ ] **Test coverage >90%** for new code
- [ ] **Performance <2s** for cost center build (1000+ items)
- [ ] **Backward compatible** (existing code works unchanged)

### User Experience

- [ ] **UI shows correct costs per entity** (manual E2E scenarios pass)
- [ ] **Entity filter buttons work** (target/buyer/all)
- [ ] **API returns entity field** in all responses
- [ ] **Quality indicators visible** in UI or API

---

## Documentation Updates

After implementation, update:

1. **CLAUDE.md**
   - Add note about cost model entity awareness
   - Document entity filtering pattern for future features

2. **README.md** (if exists in cost_engine/)
   - Document entity parameter usage
   - Add examples of entity-filtered cost calculations

3. **API Documentation** (if exists)
   - Document entity query parameter
   - Add examples of target/buyer/all queries

---

## Deployment Checklist

Before deploying to production:

- [ ] All specs implemented
- [ ] All tests passing (unit + integration + regression)
- [ ] Manual E2E scenarios validated
- [ ] Code review completed
- [ ] Performance testing completed (<2s for cost center)
- [ ] deal_id warnings eliminated (verify zero warnings in logs)
- [ ] Backward compatibility verified (existing API calls work)
- [ ] Documentation updated
- [ ] Rollback plan tested (can revert cleanly)

---

## Long-Term Maintenance

### Quarterly Reviews

- Review synergy savings estimates vs actuals (if deal closed)
- Adjust savings models based on real-world data
- Update test fixtures if cost models change

### Future Enhancements (Post-V1)

1. **Semantic synergy matching** (LLM-based app similarity)
2. **Multi-entity support** (>2 entities in complex deals)
3. **Synergy timing optimization** (critical path analysis)
4. **Cost trend analysis** (compare estimates vs actuals over time)

---

## Cross-Reference Index

### Spec → Implementation Mapping

| Spec | Key Files | Entry Point | Testing |
|------|-----------|-------------|---------|
| 01 | services/cost_engine/*.py | extract_drivers_from_facts() | tests/unit/test_cost_engine_entity.py |
| 02 | web/blueprints/costs.py | _gather_headcount_costs() | tests/unit/test_cost_blueprint_entity.py |
| 03 | web/blueprints/costs.py | _gather_one_time_costs() | tests/unit/test_cost_blueprint_entity.py |
| 04 | web/blueprints/costs.py | _identify_synergies() | tests/unit/test_synergy_matching.py |
| 05 | services/*_bridge.py | create_inventory_from_facts() | tests/integration/test_deal_id_propagation.py |
| 06 | web/blueprints/costs.py | _assess_data_quality_per_entity() | tests/unit/test_cost_quality_indicators.py |
| 07 | tests/integration/ | (all integration tests) | tests/integration/test_cost_model_*.py |

---

## BUILD STATUS

**Specification Phase:** ✅ COMPLETE (7/7 documents)
**Implementation Phase:** ⏳ PENDING (awaiting execution)
**Expected Completion:** 12-16 hours from start

---

**END OF BUILD MANIFEST**

*This manifest is the master build plan. Start with Phase 1 (Doc 01 + Doc 05) following the execution order above.*

---

📋 **All specification documents are complete. The system is fully described and ready to build. Use these documents as your source of truth for implementation.**
