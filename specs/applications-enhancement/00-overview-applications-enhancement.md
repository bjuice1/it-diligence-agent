# Applications Domain Enhancement - Overview

**Status:** Specification
**Created:** 2026-02-11
**Complexity:** High
**Estimated Scope:** 24-30 hours

---

## Overview

This specification suite addresses four critical gaps in the applications domain identified in audit1:

1. **Entity propagation failures** - Buyer vs target differentiation relies on inference fallbacks
2. **Table parsing brittleness** - Merged cells, non-standard headers cause extraction failures
3. **Cost model neglect** - Stub placeholder with no complexity tiers or category awareness
4. **Inventory-cost disconnection** - Cost engine uses simple counts, ignores rich inventory data

**Why this exists:** Applications are the highest-impact domain in M&A IT due diligence (typically 40-60% of integration costs), yet our current implementation has the weakest cost estimation accuracy and data quality enforcement.

**Scope:** End-to-end enhancement of the applications data pipeline from document extraction through cost estimation and UI presentation.

---

## Architecture

### Current State (Broken Pipeline)

```
Document (PDF/DOCX)
    ↓
Deterministic Parser (brittle, entity-blind)
    ↓
Discovery Agent → FactStore
    ↓
Applications Bridge (entity inference fallback)
    ↓
InventoryStore (rich data: category, complexity, vendor)
    ↓
[GAP - not queried by cost engine]
    ↓
DealDrivers (applications=50) → Cost Engine
    ↓
Stub Cost Model ($5K × count)
    ↓
UI (no enrichment status)
```

**Critical failures:**
- Entity defaults to "target" silently if document structure ambiguous
- Parser crashes on merged cells, skips non-standard headers
- Cost estimate ignores whether app is simple chat tool vs critical ERP
- UI can't show which apps need manual review

### Target State (Enhanced Pipeline)

```
Document (PDF/DOCX)
    ↓
[NEW] Document-level entity tagger
    ↓
Enhanced Parser (merged cells, Unicode normalization, header flexibility)
    ↓
Discovery Agent → FactStore (entity validated)
    ↓
Applications Bridge (strict validation, no silent defaults)
    ↓
InventoryStore (category, complexity, hosted_by_parent, deployment_type)
    ↓
[NEW] Cost Engine Queries Inventory
    ↓
Multi-Tier Cost Model (complexity × category × deployment × deal_type)
    ↓
Enhanced UI (enrichment status, source tracing, data quality flags)
```

**Key improvements:**
- Entity enforced at document parse time, fails loudly on ambiguity
- Parser handles 95%+ real-world table formats
- Cost varies 3-10x by category and complexity (not flat)
- UI shows data quality, links to source facts

---

## Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    DOCUMENT LAYER                           │
│  • Entity Tagging (Doc 01)                                  │
│  • Enhanced Parser (Doc 02)                                 │
└─────────────────┬───────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────────────┐
│                    DATA LAYER                                │
│  • FactStore (entity validated)                             │
│  • InventoryStore (enriched with complexity, category)      │
└─────────────────┬───────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────────────┐
│                    COST LAYER                                │
│  • Multi-Tier Cost Model (Doc 03)                           │
│  • Inventory Integration (Doc 04)                           │
└─────────────────┬───────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                        │
│  • Enhanced UI with enrichment status (Doc 05)              │
└─────────────────────────────────────────────────────────────┘

                  ↓
┌─────────────────────────────────────────────────────────────┐
│                    QUALITY ASSURANCE                         │
│  • Comprehensive Testing (Doc 06)                           │
│  • Rollout Strategy (Doc 07)                                │
└─────────────────────────────────────────────────────────────┘
```

---

## Specification Documents

| Document | Purpose | Dependency | Estimated Hours |
|----------|---------|------------|-----------------|
| **01-entity-propagation-hardening.md** | Document-level entity tagging, strict validation | 00 | 3-4 hours |
| **02-table-parser-robustness.md** | Merged cells, Unicode, header flexibility | 00, 01 | 4-5 hours |
| **03-application-cost-model.md** | Complexity tiers, category multipliers | 00 | 4-5 hours |
| **04-cost-engine-inventory-integration.md** | Query InventoryStore for cost calculations | 00, 03 | 3-4 hours |
| **05-ui-enrichment-status.md** | Display data quality, source links | 00, 01, 02 | 3-4 hours |
| **06-testing-validation.md** | Comprehensive test strategy | 01-05 | 4-5 hours |
| **07-rollout-migration.md** | Feature flags, backward compatibility | 00, 04, 06 | 2-3 hours |

**Total:** 24-30 hours

---

## Data Flows

### 1. Entity Propagation (Document → Inventory)

```
PDF Section Header: "Target Company Applications"
    ↓ [Doc 01: Entity Tagger]
document_entity = "target"
    ↓ [Doc 02: Enhanced Parser]
ParsedTable(entity="target", headers=[...], rows=[...])
    ↓ [Applications Bridge - strict mode]
if not table.entity:
    raise EntityValidationError("Entity required, not inferrable")
    ↓ [InventoryStore]
InventoryItem(entity="target", category="erp", ...)
```

### 2. Cost Calculation (Inventory → Cost Estimate)

**Old flow (broken):**
```
DealDrivers(applications=50)
    ↓
Cost = $50K + ($5K × 50) = $300K  # Flat, ignores complexity
```

**New flow (enhanced):**
```
InventoryStore.get_items(inventory_type="application", entity="target")
    ↓
[
  {name: "SAP ERP", category: "erp", complexity: "critical", deployment: "on-prem"},
  {name: "Slack", category: "collaboration", complexity: "simple", deployment: "saas"},
  ...
]
    ↓ [Doc 03: Cost Model + Doc 04: Integration]
SAP: $50K base × 3.0 (critical) × 2.5 (erp) × 1.5 (on-prem) × 2.5 (carveout) = $703K
Slack: $5K base × 0.5 (simple) × 0.8 (collaboration) × 0.3 (saas) × 1.0 (acquisition) = $0.6K
    ↓
Total = $703K + $0.6K + ... = realistic estimate
```

### 3. UI Presentation (Inventory → User)

```
InventoryStore.get_items() + enrichment metadata
    ↓ [Doc 05: UI Enhancement]
Template renders:
  • Name: SAP ERP
  • Category: ERP ✅ (high confidence)
  • Enrichment: Success (LLM validated)
  • Source: facts_20260211.json → F-APP-042
  • Needs Review: No
```

---

## Benefits

### Business Impact
- **Cost estimate accuracy:** 50% → 85% (eliminates 2-10x underestimation)
- **Data quality visibility:** Users can see which apps need manual review
- **Entity separation:** Zero silent buyer/target confusion
- **Parser robustness:** 70% → 95% automated extraction success rate

### Technical Benefits
- **Architectural coherence:** Cost engine finally uses inventory richness
- **Maintainability:** Explicit validation failures vs silent fallbacks
- **Testability:** Golden fixtures can validate end-to-end accuracy
- **Extensibility:** Cost model tiers support future refinement

### User Experience
- **Trust:** UI shows data quality indicators, not just blind acceptance
- **Traceability:** Click through to source facts and documents
- **Actionability:** "Needs review" flags guide manual effort
- **Accuracy:** Cost estimates respect application complexity

---

## Expectations

### Success Criteria

**Quantitative:**
- [ ] Entity propagation: 100% of parsed apps have explicit entity (never defaulted)
- [ ] Parser robustness: 95%+ of real-world tables parse without manual preprocessing
- [ ] Cost variance: ERP vs collaboration tools show 5-10x cost difference
- [ ] Test coverage: 95%+ on new code, all golden fixtures passing
- [ ] Enrichment visibility: UI shows success/failure for 100% of apps

**Qualitative:**
- [ ] Stakeholders trust cost estimates (validated against historical actuals)
- [ ] Users can self-serve data quality review (no engineer required)
- [ ] Codebase maintainers understand cost model logic (documented, tested)

### Non-Goals (Out of Scope)

- ❌ LLM-based entity detection (start with heuristics, add later if needed)
- ❌ Real-time cost recalculation UI (batch recalc is sufficient)
- ❌ Application dependency mapping (future enhancement)
- ❌ Vendor risk scoring (separate domain)
- ❌ License compliance analysis (separate feature)

---

## Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Cost model accuracy subjective** | Medium | High | Validate against 5-10 historical deals, adjust multipliers based on variance |
| **Merged cell handling infeasible** | Low | Medium | Test PyMuPDF/pdfplumber capabilities early; fallback to manual preprocessing for edge cases |
| **InventoryStore missing fields** | Low | High | Verify schema coverage pre-implementation (assumption A1); add migration if needed |
| **Performance regression on large deals** | Medium | Medium | Performance test with 100-app synthetic inventory; add caching if needed |
| **Backward compatibility breaks** | Low | Critical | Feature flag + dual-mode operation; comprehensive regression testing |
| **Stakeholder rejects cost model** | Medium | Medium | Iterative validation at Doc 03 completion; adjust tiers based on feedback |

---

## Results Criteria

### Definition of Done

**For each document:**
- [ ] All sections complete (no TODOs or placeholders)
- [ ] Cross-references validated (dependencies exist)
- [ ] Acceptance criteria measurable and testable
- [ ] Risks identified with mitigation strategies

**For overall suite:**
- [ ] All 7 documents written and reviewed
- [ ] Build manifest complete with execution order
- [ ] Assumptions validated (A1, A2, A5 from audit2)
- [ ] Open questions resolved or defaulted
- [ ] Rollback plan documented

### Validation Checklist

**Pre-implementation validation (complete before coding):**
- [ ] **A1:** InventoryStore has `category`, `complexity`, `hosted_by_parent` fields
- [ ] **A2:** Enrichment success rate >70% on recent deals
- [ ] **A5:** Entity extraction patterns validated on 10-20 sample documents
- [ ] **Q1 resolved:** SaaS vs on-prem deployment_type cost multipliers defined
- [ ] **Q3 resolved:** hosted_by_parent triggers TSA cost in carveouts

**Post-implementation validation:**
- [ ] All 89+ tests passing (existing + new)
- [ ] Golden fixtures validate end-to-end accuracy
- [ ] Performance test: 100-app deal completes in <30s
- [ ] Cost estimates within ±30% of historical actuals (sample 5 deals)
- [ ] Feature flag rollback tested (both on/off states functional)

---

## Dependencies

### External Dependencies
- PyMuPDF 1.23+ (merged cell detection support)
- pdfplumber 0.10+ (table extraction robustness)
- Flask 3.0+ (UI rendering)
- SQLAlchemy 2.0 (inventory querying)
- Anthropic API (enrichment LLM calls)

### Internal Dependencies
- FactStore (existing, no changes needed)
- InventoryStore (existing, verify schema coverage)
- DealDrivers (existing, maintain for backward compatibility)
- Deal-type awareness system (Doc 03, 04 integrate with deal_type multipliers)

### Cross-Document Dependencies
```
00-overview (this doc)
    ├─→ 01-entity-propagation
    ├─→ 03-cost-model
    └─→ 05-ui-enrichment
        ↓
01-entity-propagation
    └─→ 02-table-parser
        ↓
03-cost-model
    └─→ 04-cost-engine-integration
        ↓
[01, 02, 03, 04, 05]
    └─→ 06-testing
        ↓
[00, 04, 06]
    └─→ 07-rollout
```

---

## Next Steps

1. **Immediate (before implementation):**
   - Validate assumptions A1, A2, A5 (30 minutes)
   - Resolve open questions Q1, Q3 with stakeholders (15 minutes)
   - Review and approve this overview document

2. **Document generation (audit3):**
   - Write documents 01, 03 in parallel (foundational)
   - Write documents 02, 05 in parallel (depends on 01)
   - Write document 04 (depends on 03)
   - Write document 06 (depends on all)
   - Write document 07 (final)

3. **Implementation (post-audit3):**
   - Phase 1: Entity propagation + parser robustness (Docs 01, 02)
   - Phase 2: Cost model + integration (Docs 03, 04)
   - Phase 3: UI enhancement (Doc 05)
   - Phase 4: Testing + rollout (Docs 06, 07)

---

## Related Documents

- `audits/B1_buyer_target_separation.md` - Entity scoping audit (partial fixes documented)
- `specs/deal-type-awareness/03-conditional-logic.md` - Deal type multiplier integration
- `specs/deal-type-awareness/05-cost-buildup-wiring.md` - Cost engine architecture
- `stores/inventory_schemas.py` - InventoryStore field definitions
- `services/cost_engine/models.py` - Current cost model (stub)

---

**Document Status:** ✅ Complete
**Last Updated:** 2026-02-11
**Next Document:** 01-entity-propagation-hardening.md
