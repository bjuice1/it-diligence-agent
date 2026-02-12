# Deal Type Awareness System - Build Manifest

**Project**: Deal Type Awareness for IT Due Diligence Agent
**Status**: GREENFIELD - Specifications Complete, Ready for Implementation
**Priority**: P0 (Critical Business Logic Fix)
**Total Estimated Effort**: 12-16 hours (9 hours parallelized)
**Created**: 2025-02-11
**Audit Trail**: /audit1 → /audit2 → /audit3

---

## Executive Summary

The IT Due Diligence Agent currently does NOT differentiate between deal types (acquisition vs carve-out vs divestiture), causing it to make inappropriate merger/consolidation recommendations for ALL deals regardless of structure. This is a **critical business logic flaw** that produces wrong recommendations and cost estimates.

**Example of Current Bug**:
- **Scenario**: User creates a carve-out deal (Target is being separated from Parent company)
- **Expected**: System recommends building standalone IT infrastructure, calculates separation costs
- **Actual**: System recommends consolidating Target → Buyer systems (WRONG - Target is separating from Parent, not merging with Buyer)

**Root Cause Analysis**:
1. `deal_type` field EXISTS in database (`web/database.py:514`) but is NOT USED in critical paths
2. Synergy engine (`web/blueprints/costs.py:459`) has NO deal_type parameter, always calculates consolidation
3. Reasoning prompts do NOT condition on deal_type, apply all M&A lenses equally
4. Narrative synthesis does NOT wire up existing deal-type templates

**This build fixes the issue** by implementing deal-type-aware conditional logic across 7 subsystems.

---

## Problem Statement

### User's Fear (Confirmed by Adversarial Analysis)

> "I think that it does not matter if I say that it is an acquisition or a carve out -- standalone versus integration -- I think it will make recommendations off a merger lens and think it does not do a good job at the logic there."

**Audit Result**: ✅ **FEAR CONFIRMED**

The system ALWAYS operates in "merger mode" regardless of deal_type selection. This manifests as:

1. **Carve-outs get consolidation recommendations** → User told to merge Target into Buyer infrastructure when Target is actually SEPARATING from Parent
2. **Cost estimates are wrong** → Carve-outs need standalone build-out (2-3x more expensive) but system calculates integration costs
3. **TSA exposure is ignored** → Carve-outs depend on parent services temporarily, but system doesn't identify this risk
4. **Work items are misdirected** → "Decommission target datacenter" is wrong for carve-outs where target needs STANDALONE datacenter

---

## Solution Architecture

### Three Deal Types

| Deal Type | Description | Buyer Entity Meaning | Recommendation Focus |
|-----------|-------------|----------------------|----------------------|
| **Acquisition** | Buyer acquires target, integrates into existing infrastructure | Buyer = acquirer, owner of consolidated systems | Consolidation synergies (merge systems) |
| **Carve-Out** | Target is separated from parent company, becomes standalone | Buyer = new owner (NOT parent) | Separation costs, TSA exposure, standalone build |
| **Divestiture** | Seller divests division/subsidiary to buyer (clean break) | Buyer = acquirer of divested unit | Extraction costs, untangling from parent |

### Conditional Logic Branching

```
User Selects Deal Type
        │
        ├─ Acquisition
        │   ├─> Synergy Engine: Calculate consolidation opportunities
        │   ├─> Cost Engine: Use 1.0x baseline multipliers
        │   ├─> Reasoning: Focus on Synergy Opportunity lens
        │   └─> Narrative: Use acquisition template
        │
        ├─ Carve-Out
        │   ├─> Synergy Engine: Calculate separation costs + TSA exposure
        │   ├─> Cost Engine: Use 1.5-3.0x multipliers for standalone build
        │   ├─> Reasoning: Focus on TSA Exposure, Separation Complexity lenses
        │   └─> Narrative: Use carve-out template (already exists, not wired)
        │
        └─ Divestiture
            ├─> Synergy Engine: Calculate extraction costs (higher than carve-out)
            ├─> Cost Engine: Use 2.0-3.5x multipliers
            ├─> Reasoning: Focus on Separation Complexity, Cost Driver lenses
            └─> Narrative: Use divestiture template
```

---

## Specification Documents

### Document Index

| Doc # | Title | Purpose | Effort | Dependencies |
|-------|-------|---------|--------|--------------|
| **01** | [Deal Type Architecture](01-deal-type-architecture.md) | Foundation: taxonomy, entity semantics, data flow | 1.5h | None |
| **02** | [Synergy Engine Conditional Logic](02-synergy-engine-conditional-logic.md) | Fix `_identify_synergies()` to branch by deal_type | 2h | Doc 01 |
| **03** | [Reasoning Prompt Conditioning](03-reasoning-prompt-conditioning.md) | Inject deal-type conditioning into 6 reasoning prompts | 3h | Doc 01 |
| **04** | [Cost Engine Deal Awareness](04-cost-engine-deal-awareness.md) | Add deal_type multipliers to cost calculation | 2h | Doc 01 |
| **05** | [UI Validation & Enforcement](05-ui-validation-enforcement.md) | Make deal_type required in UI, add validation | 1.5h | Docs 01, 04 |
| **06** | [Testing & Validation](06-testing-validation.md) | Build 70+ tests for all 3 deal types × 6 domains | 3h | Docs 01-05 |
| **07** | [Migration & Rollout](07-migration-rollout.md) | Phased deployment with backward compatibility | 2h | Docs 01-06 |

**Total Effort**: 15 hours sequential, **9 hours parallelized** (Docs 02, 03, 04 can run in parallel)

---

## Implementation Plan

### Dependency Chain

```
Doc 01: Deal Type Architecture (Foundation)
    │
    ├──────────────┬──────────────┬──────────────┐
    │              │              │              │
    ▼              ▼              ▼              ▼
Doc 02:        Doc 03:        Doc 04:        Doc 05:
Synergy        Reasoning      Cost           UI
Engine         Prompts        Engine         Validation
(2h)           (3h)           (2h)           (1.5h)
    │              │              │              │
    └──────────────┴──────────────┴──────────────┘
                    │
                    ▼
                Doc 06: Testing (3h)
                    │
                    ▼
                Doc 07: Migration & Rollout (2h)
```

### Build Order (Optimized for Parallelization)

#### Phase 1: Foundation (1.5 hours)
- [ ] **Doc 01**: Deal Type Architecture
  - Define taxonomy, entity semantics, M&A lens applicability matrix
  - Document end-to-end data flow

#### Phase 2: Core Logic (3 hours - PARALLEL)
Run these 3 specs in PARALLEL using separate agents:

- [ ] **Doc 02**: Synergy Engine Conditional Logic
  - Add `deal_type` parameter to `_identify_synergies()`
  - Create `_calculate_separation_costs()` function
  - Branch logic: acquisition → consolidation, carve-out/divestiture → separation

- [ ] **Doc 03**: Reasoning Prompt Conditioning
  - Update 6 reasoning prompts with deal-type conditioning
  - Create conditioning templates (acquisition, carve-out, divestiture)
  - Wire narrative synthesis to template factory

- [ ] **Doc 04**: Cost Engine Deal Awareness
  - Add `deal_type` parameter to `calculate_costs()`
  - Define `DEAL_TYPE_MULTIPLIERS` dictionary (1.0x → 3.0x range)
  - Create TSA cost driver for carve-outs

#### Phase 3: UI & Validation (2.5 hours - PARALLEL)
Run these 2 specs in PARALLEL:

- [ ] **Doc 05**: UI Validation & Enforcement
  - Make `deal_type` REQUIRED in deal form
  - Add server-side + client-side validation
  - Add database constraints (NOT NULL + CHECK)
  - Create "Edit Deal Type" functionality

- [ ] **Doc 06**: Testing & Validation (can start early, runs alongside Doc 05)
  - Write 70+ tests (unit, integration, E2E)
  - Create golden test fixtures for regression testing
  - Validate all 3 deal types × 6 domains

#### Phase 4: Deployment (2 hours)
- [ ] **Doc 07**: Migration & Rollout
  - Database migration (backfill NULL values, add constraints)
  - Phased rollout with feature flag
  - Regression validation vs baseline

---

## Critical Files & Line Numbers

### Files to Modify

| File | Current Lines | Purpose | Changes |
|------|---------------|---------|---------|
| `web/database.py` | 514 | Deal model | Add NOT NULL + CHECK constraint to deal_type |
| `web/blueprints/costs.py` | 459 | Synergy engine | Add deal_type param, branch consolidation vs separation |
| `prompts/v2_applications_reasoning_prompt.py` | 62-75 | Reasoning prompt | Inject deal-type conditioning at top |
| `prompts/v2_infrastructure_reasoning_prompt.py` | ~60 | Reasoning prompt | Inject deal-type conditioning at top |
| `prompts/v2_network_reasoning_prompt.py` | ~60 | Reasoning prompt | Inject deal-type conditioning at top |
| `prompts/v2_cybersecurity_reasoning_prompt.py` | ~60 | Reasoning prompt | Inject deal-type conditioning at top |
| `prompts/v2_identity_access_reasoning_prompt.py` | ~60 | Reasoning prompt | Inject deal-type conditioning at top |
| `prompts/v2_organization_reasoning_prompt.py` | ~60 | Reasoning prompt | Inject deal-type conditioning at top |
| `services/cost_engine/calculator.py` | ~45 | Cost calculator | Add deal_type param, apply multipliers |
| `services/cost_engine/models.py` | NEW | Cost models | Define DEAL_TYPE_MULTIPLIERS |
| `services/cost_engine/drivers.py` | NEW | Cost drivers | Add TSACostDriver for carve-outs |
| `web/templates/deal/deal_form.html` | ~45 | Deal creation form | Make deal_type required |
| `web/routes/deals.py` | ~80 | Deal routes | Add validation logic |
| `agents_v2/narrative_synthesis_agent.py` | ~100 | Narrative synthesis | Wire to deal-type template factory |

### Files to Create

| File | Lines | Purpose |
|------|-------|---------|
| `migrations/versions/20250215_deal_type_constraints.py` | 60 | Database migration |
| `tests/unit/test_deal_type_validation.py` | 120 | Unit tests |
| `tests/unit/test_synergy_engine_branching.py` | 150 | Unit tests |
| `tests/unit/test_cost_multipliers.py` | 130 | Unit tests |
| `tests/unit/test_prompt_conditioning.py` | 100 | Unit tests |
| `tests/integration/test_deal_type_cost_flow.py` | 180 | Integration tests |
| `tests/integration/test_deal_type_reasoning_flow.py` | 140 | Integration tests |
| `tests/e2e/test_full_pipeline_by_deal_type.py` | 200 | E2E tests |
| `tests/fixtures/golden_acquisition.json` | 20 | Golden fixtures |
| `tests/fixtures/golden_carveout.json` | 20 | Golden fixtures |
| `web/static/js/deal_form_validation.js` | 50 | Client-side validation |
| `scripts/snapshot_existing_deals.py` | 80 | Migration tooling |
| `scripts/audit_deal_types.py` | 50 | Migration tooling |
| `scripts/compare_snapshots.py` | 100 | Migration tooling |
| `docs/developer/deal_type_system.md` | 50 | Developer guide |

**Total New Lines**: ~2,500
**Total Modified Lines**: ~300
**Total Test Lines**: ~1,160

---

## Success Criteria (Acceptance Tests)

### Functional Requirements

- [ ] **FR-1**: User can select deal type (acquisition, carve-out, divestiture) when creating a deal
- [ ] **FR-2**: Deal type is REQUIRED (cannot create deal without selecting)
- [ ] **FR-3**: User can edit deal type post-creation
- [ ] **FR-4**: Acquisition deals generate consolidation synergies
- [ ] **FR-5**: Carve-out deals generate separation costs (no consolidation recommendations)
- [ ] **FR-6**: Divestiture deals generate extraction costs (higher than carve-out)
- [ ] **FR-7**: Cost estimates for carve-outs are 1.5-3.0x higher than acquisitions (same work items)
- [ ] **FR-8**: TSA costs appear ONLY for carve-outs, not acquisitions
- [ ] **FR-9**: Reasoning prompts condition on deal type (visible in prompt content)
- [ ] **FR-10**: Narrative synthesis uses deal-type-specific templates

### Non-Functional Requirements

- [ ] **NFR-1**: All 572 existing tests still pass post-migration
- [ ] **NFR-2**: Existing acquisition deals produce IDENTICAL outputs (±5% cost variance allowed)
- [ ] **NFR-3**: Database constraints prevent NULL or invalid deal_type values
- [ ] **NFR-4**: Feature flag enables instant rollback if issues arise
- [ ] **NFR-5**: Zero production incidents during rollout
- [ ] **NFR-6**: API backward compatibility (omitted deal_type defaults to 'acquisition')

### Negative Test Cases (What Should NOT Happen)

- [ ] **NT-1**: Carve-out deals should NEVER recommend "consolidate target → buyer"
- [ ] **NT-2**: Acquisition deals should NEVER calculate TSA costs
- [ ] **NT-3**: System should NEVER accept deal_type='merger' or other invalid values
- [ ] **NT-4**: User should NEVER be able to create deal without selecting deal_type

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Regression in existing acquisition logic** | Medium | High | Pre/post snapshots, regression tests, feature flag for instant rollback |
| **Database migration fails** | Low | Critical | Test migration in staging, backup before prod deployment |
| **User confusion about deal type selection** | Medium | Medium | Contextual help text, user documentation, training email |
| **Cross-entity contamination** (buyer/target mixing) | Low | High | Entity isolation tests, validate entity + deal_type together |
| **LLM ignores prompt conditioning** | Low | High | Place conditioning at TOP of prompts, use visual formatting, validate outputs |
| **Cost multipliers too high/low** | Medium | Medium | Calibrate from industry benchmarks, plan recalibration after 10+ deals |

---

## Rollback Plan

### Immediate Rollback (Feature Flag)
```bash
export DEAL_TYPE_AWARENESS=false
systemctl restart diligence-web
```
**Impact**: System reverts to old behavior (always consolidation) within seconds.

### Full Rollback (Code + Database)
```bash
git revert <commit_hash>
flask db downgrade -1
pg_restore -d diligence_prod backup_pre_deal_type_migration.sql
```
**Impact**: Complete rollback to pre-migration state within 5 minutes.

---

## Metrics & Monitoring

### KPIs to Track Post-Deployment

| Metric | Target | Alert Threshold |
|--------|--------|----------------|
| Deal creation failures | <1% | >5% |
| Cost calculation errors | 0 | Any exception |
| Regression test pass rate | 100% | <95% |
| User support tickets | <5/week | >20/week |
| TSA costs for acquisitions | 0 | Any >$0 |
| Consolidation recommendations for carve-outs | 0 | Any occurrence |

### Logging Additions

```python
logger.info(f"Cost calculation: deal_type={deal_type}, work_item_count={len(work_items)}")
logger.info(f"Synergy engine: deal_type={deal_type}, synergy_type={synergy_type}")
logger.info(f"Reasoning: deal_type={deal_type}, domain={domain}, conditioning_applied=True")
```

---

## Documentation Deliverables

### For Users
- [x] Updated user guide: "Selecting the Correct Deal Type" (Spec 05)
- [x] Email template for rollout announcement (Spec 07)
- [x] Deal type selection decision tree (Spec 01)

### For Developers
- [x] Developer guide: "Deal Type System Architecture" (Spec 07)
- [x] Code comments in modified files
- [x] Test coverage report

### For Operations
- [x] Migration runbook (Spec 07)
- [x] Rollback procedures (Spec 07)
- [x] Monitoring dashboard queries (Spec 07)

---

## Open Questions (Resolved)

### Q1: For carve-outs, who is the "buyer"?
**Answer**: Buyer = new owner of carved-out entity (NOT the parent company). See Spec 01, section "Entity Semantics for Carve-Outs".

### Q2: Should we create a 4th deal type for "merger of equals"?
**Answer**: No, out of scope for MVP. Rare enough to defer. User can select "acquisition" as closest match.

### Q3: What if a deal is hybrid (acquire some divisions, carve out others)?
**Answer**: Create SEPARATE Deal records (one per structure), combine reports manually. Complexity not justified for MVP.

### Q4: Should TSA duration be user-configurable?
**Answer**: Not in MVP. Default to 12 months. Future enhancement: add TSA duration field to deal form.

### Q5: How to calibrate cost multipliers (2.5x for identity, 1.8x for apps, etc.)?
**Answer**: Initial estimates based on industry benchmarks. Plan recalibration after 10+ deals using regression analysis. See Spec 04.

---

## Timeline

| Week | Phase | Tasks | Effort |
|------|-------|-------|--------|
| **0** | Pre-Flight | Snapshot existing deals, audit database, run test baseline | 4h |
| **1** | Database | Migration script, deploy to staging, deploy to prod | 2h |
| **2** | Code | Deploy Docs 02-04 with feature flag enabled | 5h |
| **3** | UI | Deploy Doc 05 (required field, validation) | 2h |
| **4** | Validation | Run regression tests, remove feature flag, cleanup | 3h |

**Total**: 16 hours over 4 weeks (allows time for monitoring between phases)

---

## Next Steps for User

### To Implement This Build:

1. **Review Specifications** (30 minutes)
   - Read through Docs 01-07
   - Validate assumptions match your business logic
   - Flag any concerns or questions

2. **Approve Build** (5 minutes)
   - Confirm scope is correct
   - Approve estimated effort (12-16 hours)
   - Approve phased rollout plan

3. **Execute Implementation** (12-16 hours)
   - **Option A**: Implement yourself using specs as guide
   - **Option B**: Ask Claude to implement (use Task tool with specs as context)
   - **Option C**: Parallelize across multiple Claude agents (Docs 02, 03, 04 in parallel)

4. **Deploy & Monitor** (4 weeks)
   - Follow Spec 07 migration plan
   - Run regression tests at each phase
   - Monitor metrics and user feedback

---

## Specification Completion Status

- [x] **Doc 01**: Deal Type Architecture ✅ COMPLETE
- [x] **Doc 02**: Synergy Engine Conditional Logic ✅ COMPLETE
- [x] **Doc 03**: Reasoning Prompt Conditioning ✅ COMPLETE
- [x] **Doc 04**: Cost Engine Deal Awareness ✅ COMPLETE
- [x] **Doc 05**: UI Validation & Enforcement ✅ COMPLETE
- [x] **Doc 06**: Testing & Validation ✅ COMPLETE
- [x] **Doc 07**: Migration & Rollout ✅ COMPLETE
- [x] **Doc 00**: Build Manifest ✅ COMPLETE

**All specifications ready for implementation.**

---

## Contact & Support

**Questions about specifications?** Reference the specific doc number and section (e.g., "Doc 02, Section 3.2").

**Need clarification during implementation?** Each spec has a "Success Criteria" section defining exact acceptance tests.

**Found edge cases not covered?** Document in implementation notes, propose as future enhancement.

---

**END OF BUILD MANIFEST**

**Status**: ✅ Specifications Complete, Ready for Implementation
**Total Deliverable**: 7 specification documents + 1 build manifest (8 documents, ~12,000 words)
**Next Action**: User approval to proceed with implementation
