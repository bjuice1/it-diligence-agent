# Applications Enhancement Specifications

**Status:** Complete - Ready for Implementation
**Created:** 2026-02-11
**Total Specification Size:** 150KB across 9 documents
**Estimated Implementation:** 24-30 hours (3-4 days)

---

## Quick Start

1. **Read first:** [00-BUILD-MANIFEST.md](00-BUILD-MANIFEST.md) - Complete overview, execution order, scope
2. **Then read:** [00-overview-applications-enhancement.md](00-overview-applications-enhancement.md) - Architecture and problem statement
3. **Before coding:** Validate assumptions in BUILD MANIFEST (30 minutes)
4. **Start with:** Phase 1 - Entity Propagation + Parser Robustness (parallel)

---

## Document Map

### Foundation Documents
- **00-BUILD-MANIFEST.md** (15KB) - Complete build guide, execution order, scope estimate
- **00-overview-applications-enhancement.md** (14KB) - Architecture vision, data flows, success criteria

### Implementation Documents
- **01-entity-propagation-hardening.md** (19KB) - Entity extraction heuristics, strict validation
- **02-table-parser-robustness.md** (20KB) - Unicode, merged cells, flexible headers
- **03-application-cost-model.md** (23KB) - Multi-tier complexity model, category multipliers
- **04-cost-engine-inventory-integration.md** (20KB) - InventoryStore integration, dual-mode operation
- **05-ui-enrichment-status.md** (23KB) - Data quality indicators, source tracing, manual enrichment
- **06-testing-validation.md** (20KB) - Comprehensive test strategy, golden fixtures
- **07-rollout-migration.md** (16KB) - Feature flags, gradual rollout, monitoring

---

## What This Fixes

### Current Problems (from audit1)
1. **Entity propagation failures** - Silent defaults to "target" cause buyer/target confusion
2. **Parser brittleness** - 70% success rate, fails on merged cells, Unicode edge cases
3. **Cost model stub** - Flat $5K/app, no complexity awareness, 2-10x underestimation
4. **Inventory-cost disconnect** - Cost engine ignores category, complexity, vendor data

### After Implementation
1. **Entity validation** - 100% validated, fails loudly on ambiguity
2. **Parser robustness** - 95%+ success rate, handles merged cells, Unicode normalization
3. **Multi-tier cost model** - 63x variance (ERP vs Slack), complexity-aware, category multipliers
4. **Inventory integration** - Cost engine queries InventoryStore, uses full application metadata

---

## Implementation Phases

### Phase 1: Foundation (6-9 hours)
**Documents:** 01, 02
**Deliverables:** Entity extraction + enhanced parser
**Tests:** 35+ unit tests, 6+ integration tests

### Phase 2: Cost Model (7-9 hours)
**Documents:** 03, 04
**Deliverables:** Multi-tier cost model + inventory integration
**Tests:** 40+ unit tests, 2+ integration tests
**Can run in parallel with Phase 1**

### Phase 3: UI Enhancement (3-4 hours)
**Documents:** 05
**Deliverables:** Data quality indicators, manual enrichment, cost breakdown
**Tests:** 10+ unit tests

### Phase 4: Testing (4-5 hours)
**Documents:** 06
**Deliverables:** Golden fixtures, performance tests, UI testing
**Tests:** 3+ golden fixtures, 1+ performance test

### Phase 5: Rollout (2-3 hours)
**Documents:** 07
**Deliverables:** Feature flags, monitoring, documentation, runbook

**Total:** 24-30 hours (3-4 days solo, 14-17 hours with 2 developers)

---

## Key Decisions

### Resolved During Planning
- ✅ **SaaS vs on-prem:** Deployment type multipliers (SaaS 0.3x, on-prem 1.5x)
- ✅ **TSA costs:** Auto-trigger for carveouts with parent-hosted apps
- ✅ **Entity detection:** Start with heuristics, add LLM fallback if <90% accurate
- ✅ **Rollback strategy:** Feature flags + dual-mode operation for instant rollback
- ✅ **Cost variance threshold:** ±30% acceptable for model validation

### Technical Choices
- **No new dependencies:** Uses existing PyMuPDF, pdfplumber, Flask, SQLAlchemy
- **Feature flags:** `APPLICATION_INVENTORY_COSTING` for gradual rollout
- **Backward compatible:** Dual-mode operation, existing APIs unchanged
- **Complexity tiers:** Simple (0.5x), Medium (1.0x), Complex (2.0x), Critical (3.0x)

---

## Success Metrics

### Code Quality
- [ ] 89+ new tests passing
- [ ] 572 existing tests passing (no regressions)
- [ ] 95%+ code coverage on new files

### Functional Validation
- [ ] 95%+ parser success rate on 20 real documents
- [ ] Cost variance by complexity: 5-10x minimum (simple vs critical)
- [ ] Entity extraction: 100% validated (zero silent defaults)
- [ ] UI: Data quality scores displayed for all apps

### Performance
- [ ] 100-app portfolio costs calculated in <5s
- [ ] No memory leaks or resource exhaustion

### Rollout
- [ ] 10+ new deals processed successfully in Phase 2
- [ ] 50+ existing deals migrated in Phase 3
- [ ] User documentation complete
- [ ] Support team trained

---

## Pre-Implementation Checklist

**Before starting Phase 1, validate:**

- [ ] **A1:** InventoryStore has required fields (category, complexity, hosted_by_parent)
  - Verify: `grep -r "category\|complexity" stores/inventory_schemas.py`

- [ ] **A2:** Enrichment success rate >70%
  - Verify: Query last 10 analysis runs, check field coverage

- [ ] **A5:** Entity patterns exist in real documents
  - Verify: Review 10-20 sample PDFs for "Target", "Buyer" section headers

- [ ] **Create branch:**
  ```bash
  git checkout -b feature/applications-enhancement
  git push -u origin feature/applications-enhancement
  ```

- [ ] **Set up fixtures:**
  ```bash
  mkdir -p tests/fixtures/entity_extraction
  mkdir -p tests/fixtures/parser_robustness
  mkdir -p tests/fixtures/golden/applications_enhancement
  ```

---

## Risk Mitigation

### High-Risk Areas
1. **Merged cell detection** - Test on Day 1 with real Excel→PDF samples
2. **Cost model accuracy** - Validate against 5-10 historical deals
3. **Performance at scale** - Test with 100-app synthetic portfolio
4. **Backward compatibility** - Run full 572-test suite after each phase

### Rollback Options
- **Instant:** Feature flag off (`APPLICATION_INVENTORY_COSTING=false`)
- **Per-deal:** Set `deal.use_inventory_costing = False`
- **Full:** Git revert to previous release

---

## Related Work

**Prior specs:**
- `specs/deal-type-awareness/` - Deal type multiplier system (Doc 03, 04 integrate with this)
- `specs/deal-type-awareness/01-preprocessing.md` - Unicode work (related to Doc 02)

**Audits:**
- `audits/B1_buyer_target_separation.md` - Entity scoping background (Doc 01 addresses)

**Code to modify:**
- `tools_v2/deterministic_parser.py` - Enhanced in Doc 02
- `services/applications_bridge.py` - Strict validation in Doc 01
- `services/cost_engine/calculator.py` - Inventory integration in Doc 04
- `stores/app_category_mappings.py` - Cost multipliers in Doc 03

---

## Questions?

**Architecture questions:** See [00-overview-applications-enhancement.md](00-overview-applications-enhancement.md)

**Implementation questions:** See individual spec documents (01-07)

**Rollout questions:** See [07-rollout-migration.md](07-rollout-migration.md)

**Scope/timeline questions:** See [00-BUILD-MANIFEST.md](00-BUILD-MANIFEST.md)

---

**Generated by:** /audit1 → /audit2 → /audit3 workflow
**Audit Date:** 2026-02-11
**Status:** ✅ Complete and ready to build
