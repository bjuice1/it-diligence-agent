# BUILD MANIFEST: Adaptive Organization Domain

**Project:** Adaptive Organization Structure Extraction
**Description:** Enable IT due diligence pipeline to adapt when org census lacks management hierarchy data—generate reasonable assumptions based on industry benchmarks and company size heuristics.
**Date:** 2026-02-11
**Complexity:** Medium-High
**Status:** Specification Complete + P0 Fixes Applied, Ready for Implementation
**P0 Fixes:** 4 critical issues identified and resolved (see P0-FIXES-APPLIED.md)

---

## EXECUTIVE SUMMARY

### Problem Statement

M&A VDR packages frequently omit organizational charts, reporting lines, and management layers. Current system presents empty organization analysis when hierarchy data is missing, forcing analysts to manually estimate structure or skip org risk assessment entirely.

### Solution

Implement adaptive extraction: **if hierarchy exists → extract it; if missing → generate assumptions**. Assumptions are conservative, evidence-based (industry benchmarks), and transparently labeled to distinguish from observed data.

### Business Value

- **Faster deal cycles:** Analysts can proceed with org risk assessment even with sparse documentation
- **Better cost estimates:** Assumed org structure enables staffing cost estimates (vs. "unknown")
- **Professional output:** Reports show reasoned assumptions (vs. blank sections)
- **Traceable assumptions:** Users see what's assumed, with confidence scores and rationale

### Technical Approach

- **Hierarchy detection:** Rule-based logic determines if org census has sufficient structure data
- **Assumption generation:** Python heuristics (NOT LLM) apply industry benchmarks + size adjustments
- **Schema enhancements:** Inventory tracks data provenance (observed/assumed/hybrid) with confidence scores
- **Bridge integration:** Orchestrates detect → extract → assume → merge flow

---

## DOCUMENT INDEX

| Document | Purpose | Lines | Complexity |
|----------|---------|-------|------------|
| [08-org-hierarchy-detection.md](08-org-hierarchy-detection.md) | Detection logic: does census have management structure? | 850 | Medium |
| [09-org-assumption-engine.md](09-org-assumption-engine.md) | Assumption generation: heuristics, benchmarks, inference | 950 | High |
| [10-org-inventory-schema-enhancements.md](10-org-inventory-schema-enhancements.md) | Schema changes: data_source, confidence, assumptions | 750 | Medium |
| [11-org-bridge-integration.md](11-org-bridge-integration.md) | Wire detection+assumptions into bridge service | 780 | Medium |
| [12-org-testing-strategy.md](12-org-testing-strategy.md) | Test coverage for both extract and assume paths | 800 | Medium |
| [13-org-reporting-dashboard-integration.md](13-org-reporting-dashboard-integration.md) | Surface assumption metadata in Excel, HTML, Dashboard, PowerPoint | 850 | Medium |

**Total Specification Size:** ~5,000 lines, ~45,000 words

---

## EXECUTION ORDER

### Phase 1: Foundation (Serial) — 3-4 hours

**Step 1.1:** Implement Hierarchy Detector (Spec 08)
- File: `services/org_hierarchy_detector.py` (new, ~300 lines)
- Deliverable: `detect_hierarchy_presence()` function returning `HierarchyPresence`
- Test: 10 unit tests
- Critical for: Routing logic in Phase 3

**Step 1.2:** Unit tests for detector
- File: `tests/test_org_hierarchy_detector.py` (new, ~250 lines)
- Verify: FULL, PARTIAL, MISSING classification
- Verify: Confidence scoring, gap identification

---

### Phase 2: Parallel Work — 6-8 hours (can overlap)

**Track A: Assumption Engine (Spec 09) — 6-8 hours**
- File: `services/org_assumption_engine.py` (new, ~500 lines)
- Deliverable: `generate_org_assumptions()` with industry benchmarks + size heuristics
- Test: 12 unit tests
- Can run in parallel with Track B

**Track B: Schema Enhancements (Spec 10) — 2-3 hours**
- Files: `stores/inventory_schemas.py` (modify), `models/inventory_enums.py` (new)
- Deliverable: Enhanced schema with data_source fields, updated fingerprinting
- Test: 8 unit tests
- Can run in parallel with Track A

---

### Phase 3: Integration (Serial, depends on Phase 1 & 2) — 3-4 hours

**Step 3.1:** Bridge Integration (Spec 11)
- File: `services/organization_bridge.py` (modify, +150 lines)
- File: `config_v2.py` (modify, +5 lines for feature flags)
- Deliverable: Orchestration logic (detect → extract → assume → merge)
- Test: 8 unit tests + 5 integration tests

**Step 3.2:** Integration tests
- File: `tests/integration/test_adaptive_org_extraction.py` (new)
- Verify: Cross-component flows, error handling, entity isolation

---

### Phase 4: Validation (Serial, depends on Phase 3) — 4-5 hours

**Step 4.1:** Testing Strategy Implementation (Spec 12)
- Files: Create fixtures in `tests/fixtures/org_adaptive/`
- Files: `tests/golden/test_org_golden_fixtures.py` (new)
- Files: `tests/e2e/test_adaptive_org_e2e.py` (new)
- Deliverable: 40+ unit, 15+ integration, 5+ golden, 3+ e2e tests

**Step 4.2:** Manual validation
- Test on 5 real VDR docs with varying hierarchy completeness
- Verify UI rendering with badges
- Verify cost estimates include assumed roles

---

### Critical Path

**Longest sequential dependency chain:**

```
Spec 08 (Detector, 3-4h)
    ↓
Spec 09 (Assumptions, 6-8h)
    ↓
Spec 11 (Integration, 3-4h)
    ↓
Spec 12 (Testing, 4-5h)

Total Critical Path: 16-21 hours
```

**With Parallelization:**

- Phase 1: 3-4 hours (serial)
- Phase 2: 8 hours (parallel, longest track is Spec 09)
- Phase 3: 3-4 hours (serial)
- Phase 4: 4-5 hours (serial)

**Total Estimated Duration: 18-21 hours (2.5-3 days)**

---

## TECH STACK

### Languages & Frameworks

| Component | Technology |
|-----------|------------|
| Backend Logic | Python 3.11 |
| API Calls | Anthropic SDK (direct, no LangChain) |
| Data Validation | Pydantic 2.0 |
| Testing | pytest 7.x, pytest-cov |
| Database | SQLAlchemy 2.0 (PostgreSQL 15, SQLite fallback) |
| Web Framework | Flask 3.0+ |

### New Dependencies

**None.** All logic uses existing dependencies. No new packages required.

### File Inventory

**New Files (5):**
- `services/org_hierarchy_detector.py` (~300 lines)
- `services/org_assumption_engine.py` (~500 lines)
- `models/inventory_enums.py` (~50 lines)
- `tests/test_org_hierarchy_detector.py` (~250 lines)
- `tests/test_org_assumption_engine.py` (~300 lines)
- `tests/test_inventory_schema_enhancements.py` (~200 lines)
- `tests/test_org_bridge_integration.py` (~250 lines)
- `tests/integration/test_adaptive_org_extraction.py` (~300 lines)
- `tests/golden/test_org_golden_fixtures.py` (~200 lines)
- `tests/e2e/test_adaptive_org_e2e.py` (~150 lines)

**Modified Files (3):**
- `stores/inventory_schemas.py` (+10 lines: new optional fields)
- `services/organization_bridge.py` (+150 lines, ~50 modified)
- `config_v2.py` (+5 lines: feature flags)

**Total New Code:** ~2,700 lines
**Total Modified Code:** ~65 lines
**Test Code:** ~1,650 lines (61% of total)

---

## VALIDATION CHECKLIST

Before starting implementation, validate these assumptions:

### Technical Assumptions

- [x] **Assumption 1:** FactStore can accept synthetic facts with `data_source="assumed"`
  - **Validation:** Code inspection confirms `fact.details` is JSON (can hold arbitrary metadata)
  - **Status:** Validated

- [x] **Assumption 2:** Inventory fingerprinting includes entity field (per CLAUDE.md requirement)
  - **Validation:** CLAUDE.md specifies entity is NOT NULL, fingerprints must include it
  - **Status:** Validated, already implemented

- [ ] **Assumption 3:** Industry benchmark data is reasonable and defensible
  - **Validation:** Cross-reference with Gartner IT Staffing Reports 2024, McKinsey Org Design Studies
  - **Status:** Pending (use defaults if research unavailable)
  - **Risk:** LOW (benchmarks are conservative, used for estimates only)

- [ ] **Assumption 4:** UI rendering can display badges for data_source
  - **Validation:** Inspect `web/templates/organization/` Jinja templates
  - **Status:** Pending (simple Jinja conditional, low risk)

### Business Assumptions

- [x] **Assumption 5:** M&A analysts will accept labeled assumptions (not demand real data only)
  - **Validation:** Per user requirements, "sometimes we don't get management layers called out"
  - **Status:** Validated (user explicitly requested this feature)

- [ ] **Assumption 6:** Confidence scores 0.6-0.8 are appropriate for assumptions
  - **Validation:** Test with M&A team, calibrate if needed
  - **Status:** Pending (can adjust post-implementation)

---

## RISK REGISTER

| Risk | Impact | Probability | Mitigation | Owner |
|------|--------|-------------|------------|-------|
| **Industry benchmarks inaccurate** | Assumptions wrong, bad estimates | Medium | Use conservative defaults (4 layers), cite sources in docs | Dev |
| **Detection thresholds miscalibrated (80%/30%)** | Wrong path triggered (FULL vs PARTIAL) | Medium | Test on 20+ real docs, adjust thresholds | Dev |
| **Assumed data mistaken for real data in UI** | User trusts bad assumptions | High | Prominent badges, tooltips, confidence scores | Dev+UX |
| **Feature flag not respected** | Assumptions run when disabled | Low | Unit test flag behavior explicitly | Dev |
| **Entity filtering fails** | Buyer/target cross-contamination | Medium | Extensive entity isolation tests (already in test suite) | Dev |
| **Performance degradation** | Detection + assumption adds >500ms | Low | Benchmark, optimize if needed (target <350ms) | Dev |
| **Backward compatibility break** | Existing docs fail to extract | High | Golden fixture tests for regression protection | Dev |
| **Assumption generation infinite loop** | System hangs | Very Low | Detection runs once only, assumptions don't re-trigger | Dev |

**Critical Risks (High Impact):**
1. **Assumed data mistaken for real data** → Mitigation: Prominent UI indicators (badges, tooltips, confidence)
2. **Backward compatibility break** → Mitigation: Golden fixture regression tests, feature flag for safe rollout

---

## OPEN QUESTIONS

### Questions with Defaults Chosen

1. **Q: Should detection run for buyer entity?**
   - **Default:** YES, but assumptions disabled for buyer (flag: `ENABLE_BUYER_ORG_ASSUMPTIONS=False`)
   - **Rationale:** Buyer data is context, not investment thesis (less critical)

2. **Q: Should assumptions be persisted or generated on-the-fly?**
   - **Default:** Persisted in FactStore (database-backed)
   - **Rationale:** Consistency, auditability, no re-generation on UI refresh

3. **Q: How granular should assumed roles be?**
   - **Default:** Domain-specific (e.g., "VP of Infrastructure", not just "VP")
   - **Rationale:** More useful for planning, even if confidence is lower

4. **Q: Should confidence threshold gate assumption generation?**
   - **Default:** NO threshold gating—all MISSING/PARTIAL trigger assumptions
   - **Rationale:** Low confidence is logged for review, but assumptions still valuable

### Unresolved Questions (None)

All questions have been resolved with documented defaults.

---

## ROLLBACK CRITERIA

Abandon this approach and return to audit1 if:

1. **Core dependency doesn't work:** FactStore rejects synthetic facts (mitigation: use separate assumption store)
2. **Performance unacceptable:** Detection + assumption adds >1 second (mitigation: async generation)
3. **User testing shows confusion:** M&A analysts can't distinguish assumed from real data (mitigation: redesign UI indicators)
4. **Backward compatibility broken:** >10% of existing docs fail extraction (mitigation: disable assumptions, investigate root cause)
5. **Implementation time exceeds 2x estimate:** >40 hours invested without working prototype (mitigation: reassess scope, ship MVP)

**Rollback Plan:**
1. Set `ENABLE_ORG_ASSUMPTIONS=False` in config
2. Redeploy (system reverts to extract-only mode)
3. Review logs for root cause
4. Decision: Fix issues OR shelve feature

---

## SCOPE ESTIMATE

### By Component

| Component | Estimate | Confidence | Notes |
|-----------|----------|------------|-------|
| Hierarchy Detector (Spec 08) | 3-4 hours | High | Rule-based logic, straightforward |
| Assumption Engine (Spec 09) | 6-8 hours | Medium | Heuristics need calibration, most complex |
| Schema Enhancements (Spec 10) | 2-3 hours | High | Simple field additions, backward compatible |
| Bridge Integration (Spec 11) | 3-4 hours | High | Plumbing logic, well-defined interfaces |
| Testing (Spec 12) | 4-5 hours | Medium | 60+ tests, fixtures need creation |

**Total Estimate:** 18-24 hours with High-Medium confidence

**Breakdown:**
- Coding: 12-15 hours (60%)
- Testing: 6-9 hours (40%)

### Team Size

**Recommended:** 1 developer (cohesive feature, single owner)

**Optional:** Pair programming for assumption engine logic review (most complex component)

---

## NEXT STEPS

### Immediate Actions (Before Implementation)

1. **Validate industry benchmark sources** (if research unavailable, use defaults documented in Spec 09)
2. **Set up project branch:** `feature/adaptive-org-structure`
3. **Create feature flag in config:** `ENABLE_ORG_ASSUMPTIONS=True` (default), `ENABLE_BUYER_ORG_ASSUMPTIONS=False`
4. **Set up test fixtures directory:** `tests/fixtures/org_adaptive/`

### Implementation Strategy

**Approach:** Incremental vertical slices (spec by spec)

1. **Week 1, Day 1-2:** Implement Spec 08 (detector) + unit tests → Merge to feature branch
2. **Week 1, Day 3-4:** Implement Spec 09 (assumptions) + Spec 10 (schema) in parallel → Merge
3. **Week 2, Day 1:** Implement Spec 11 (integration) + integration tests → Merge
4. **Week 2, Day 2:** Implement Spec 12 (testing strategy) + golden fixtures → Merge
5. **Week 2, Day 3:** Manual validation on 5 real docs, fix issues → Feature complete
6. **Week 2, Day 4:** Code review, performance testing → Merge to main

**Merge Strategy:** Merge each spec incrementally to feature branch, then merge feature branch to main after full validation.

---

## SUCCESS CRITERIA

### Must-Have (Acceptance Criteria)

- [ ] Hierarchy detector classifies FULL/PARTIAL/MISSING correctly on test fixtures
- [ ] Assumption engine generates 5-15 assumptions for MISSING hierarchy
- [ ] Schema includes data_source field, fingerprints don't collide
- [ ] Bridge orchestrates detect → assume → merge flow without errors
- [ ] UI shows badges for assumed data (green=observed, yellow=assumed)
- [ ] Feature flag controls behavior (on=assumptions, off=extract-only)
- [ ] Buyer entity assumptions disabled by default
- [ ] All 60+ tests pass (unit + integration + golden + e2e)
- [ ] Coverage ≥85% overall, 100% on critical paths
- [ ] No regression on existing golden fixtures (Great Insurance doc)
- [ ] Performance overhead <350ms for detection + assumptions

### Nice-to-Have (Stretch Goals)

- [ ] VDR gap entries auto-populated from detection gaps
- [ ] Cost engine confidence-weights estimates (observed > assumed)
- [ ] UI tooltip explains assumption basis on hover
- [ ] Metrics tracked for assumption generation rate (Prometheus/Grafana)
- [ ] Admin panel to view/edit assumption benchmarks
- [ ] Assumption export to Excel workbook (separate sheet)

---

## DEPENDENCIES

### Upstream Dependencies (Must Exist Before Starting)

- [x] Discovery agents extract org facts to FactStore
- [x] FactStore supports arbitrary `details` JSON (for metadata)
- [x] Organization bridge service exists (`services/organization_bridge.py`)
- [x] Inventory schema framework (`stores/inventory_schemas.py`)
- [x] Entity scoping enforced (per CLAUDE.md, already implemented)

**Status:** All upstream dependencies exist. Ready to proceed.

### Downstream Consumers (Must Work After Implementation)

- [ ] UI rendering (Jinja templates in `web/templates/organization/`)
- [ ] Cost engine (`services/cost_engine.py`)
- [ ] Report generation (`tools_v2/presentation.py`, exporters)
- [ ] VDR gap generation (`services/vdr_generator.py`)

**Integration Plan:** Test with each consumer during Phase 4 (validation).

---

## METRICS & MONITORING

### Operational Metrics (Post-Launch)

**Key Metrics to Track:**

1. **Assumption Generation Rate**
   - Metric: `org_extraction.assumptions_generated.count`
   - Target: 20-40% of analyses trigger assumptions (PARTIAL/MISSING docs)

2. **Detection Classification Distribution**
   - Metrics: `org_extraction.detection.full`, `org_extraction.detection.partial`, `org_extraction.detection.missing`
   - Target: FULL >60%, PARTIAL 20-30%, MISSING <20%

3. **Confidence Score Distribution**
   - Metric: `org_extraction.confidence_score` (histogram)
   - Target: Bimodal distribution (0.8-1.0 for observed, 0.6-0.8 for assumed)

4. **Performance Overhead**
   - Metric: `org_extraction.detection_latency_ms`, `org_extraction.assumption_latency_ms`
   - Target: Detection <100ms, Assumption <50ms

5. **Error Rate**
   - Metric: `org_extraction.errors.count`
   - Target: <1% of analyses encounter errors, fallback succeeds in 95%+

### Alerting Thresholds

- **Critical:** Error rate >5% in 1 hour → Page on-call engineer
- **Warning:** Assumption generation >60% in 1 day → Review VDR doc quality
- **Warning:** Performance overhead >500ms p95 → Investigate optimization

---

## DOCUMENTATION REQUIREMENTS

### User-Facing Documentation

- [ ] Update README.md: Explain adaptive org extraction feature
- [ ] Update user guide: How to interpret assumed data (badges, confidence)
- [ ] Update VDR checklist: Note that org charts are "helpful but not required"

### Developer Documentation

- [ ] Docstrings on all public functions (already required by specs)
- [ ] Architecture diagram: Detection → Assumption → Merge flow
- [ ] Decision log: Why these thresholds (80%/30%)? Why these benchmarks?
- [ ] Runbook: How to calibrate thresholds, how to update benchmarks

---

## CHANGELOG ENTRY

**Version:** 2.5.0 (next release)

**Feature:** Adaptive Organization Structure Extraction

**What's New:**
- Organization domain now adapts to missing hierarchy data
- When org charts/reporting lines absent, system generates reasonable assumptions based on industry benchmarks and company size
- Transparent labeling: UI shows badges to distinguish observed vs assumed data
- Feature flags for control: Enable/disable assumptions globally or per-entity (target vs buyer)

**Breaking Changes:** None (backward compatible)

**Migration Required:** None (automatic with feature flag)

**Configuration:**
```bash
# .env file
ENABLE_ORG_ASSUMPTIONS=true          # Master switch (default: true)
ENABLE_BUYER_ORG_ASSUMPTIONS=false   # Buyer assumptions (default: false)
```

---

## FINAL REVIEW CHECKLIST

Before marking specifications as "Complete":

- [x] All 5 specification documents written (08-12)
- [x] Build manifest complete (this document)
- [x] Dependency chain validated (08→09→11→12, 10 parallel with 09)
- [x] Open questions resolved with documented defaults
- [x] Risk register complete with mitigations
- [x] Test strategy covers all paths (extract-only, extract+assume, error paths)
- [x] Success criteria defined (acceptance + stretch goals)
- [x] Rollback plan documented
- [x] File inventory complete (new + modified files listed)
- [ ] Industry benchmarks validated (pending, using defaults if needed)
- [ ] Performance benchmarked (pending, will measure in Phase 4)

**Status:** Specification phase complete. Ready for implementation.

---

## SIGN-OFF

**Specifications Reviewed By:** [Developer Name]
**Date:** 2026-02-11
**Approved for Implementation:** YES / NO / PENDING

**Notes:**
- All specifications are complete and internally consistent
- Dependencies validated, no blockers identified
- Risk mitigation strategies documented
- Ready to proceed to implementation

---

## CONTACT & SUPPORT

**Feature Owner:** [Developer assigned to adaptive org feature]
**Slack Channel:** #it-dd-agent-dev
**Issue Tracker:** GitHub Issues, label: `feature/adaptive-org`
**Documentation:** This manifest + specs 08-12

---

**END OF BUILD MANIFEST**
