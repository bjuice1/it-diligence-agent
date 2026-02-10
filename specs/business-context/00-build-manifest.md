# Build Manifest: Business Context & Benchmarking Layer

**Project:** IT Due Diligence Agent — Business Context Feature
**One-line description:** Auto-generated company profile, industry benchmarking, and expected vs. observed technology stack comparison that gives deal teams instant context before diving into findings.

---

## Document Index

| # | File | Purpose | Size |
|---|------|---------|------|
| 00 | `00-build-manifest.md` | This file — project overview, execution order, tech decisions | — |
| 01 | `01-company-profile-extraction.md` | Unified CompanyProfile with auto-extraction from FactStore, confidence + provenance on every field | 57KB |
| 02 | `02-industry-classification-taxonomy.md` | Deterministic industry classification from 6 ranked evidence signals with tie-break logic | 97KB |
| 03 | `03-industry-template-dataset.md` | JSON dataset of expected tech stacks, metrics, workflows for 5 industries + general fallback | 163KB |
| 04 | `04-benchmark-comparison-engine.md` | Expected/Observed/Variance computation with eligibility rules preventing misleading metrics | 81KB |
| 05 | `05-business-context-ui.md` | Web UI page, dashboard card, HTML report section, deal-lens controls, provenance display | 78KB |
| 06 | `06-testing-validation.md` | 80+ test cases: unit tests, integration, determinism, confidence calibration, graceful degradation | 121KB |

**Total specification:** ~597KB across 6 specs + manifest

All files located at: `specs/business-context/`

---

## Execution Order

### Phase A: Data Layer (Specs 01 + 02 + 03 — Parallel)

These three specs have no dependencies on each other and can be built simultaneously.

| Order | Spec | New Files | Modified Files |
|-------|------|-----------|----------------|
| A.1 | 01 — Company Profile | `stores/company_profile.py`, `services/profile_extractor.py` | `consistency_engine.py` (use new profile) |
| A.2 | 02 — Industry Classifier | `services/industry_classifier.py`, `stores/industry_taxonomy.py` | None (reads existing stores) |
| A.3 | 03 — Industry Templates | `data/industry_templates/*.json` (6 files), `stores/industry_templates.py` | None |

**Gate 1:** After Phase A, validate:
- ProfileExtractor produces correct profile from test FactStore
- IndustryClassifier returns "insurance" for insurance fixture with confidence > 0.8
- All 6 templates load and pass schema validation

### Phase B: Computation Layer (Spec 04 — Sequential)

Depends on all Phase A outputs.

| Order | Spec | New Files | Modified Files |
|-------|------|-----------|----------------|
| B.1 | 04 — Benchmark Engine | `services/benchmark_engine.py`, `models/benchmark_comparison.py` | None |

**Gate 2:** After Phase B, validate:
- Full-data fixture produces 4+ eligible metrics with correct variance classifications
- Empty fixture produces 0 eligible metrics with clear ineligibility reasons
- Tech stack comparison shows Found/Not Found correctly

### Phase C: Presentation Layer (Spec 05 — Sequential)

Depends on Phase B output.

| Order | Spec | New Files | Modified Files |
|-------|------|-----------|----------------|
| C.1 | 05 — UI & Report | `web/routes/business_context.py`, `web/services/business_context_service.py`, `web/templates/business_context/overview.html` + components, `web/static/css/business_context.css` | `web/templates/dashboard.html`, `web/templates/base.html`, `tools_v2/html_report.py` |

### Phase D: Validation (Spec 06 — Last)

Depends on all phases.

| Order | Spec | New Files | Modified Files |
|-------|------|-----------|----------------|
| D.1 | 06 — Tests | `tests/test_company_profile.py`, `tests/test_industry_classifier.py`, `tests/test_industry_templates.py`, `tests/test_benchmark_engine.py`, `tests/test_business_context_service.py`, `tests/fixtures/business_context_fixtures.py` | None |

---

## Dependency Chain

```
01-company-profile ──┐
                     ├──→ 04-benchmark-engine ──→ 05-business-context-ui ──→ 06-testing
02-industry-classify─┤                           ↑
                     ├──→ 03-industry-templates───┘
```

---

## Tech Stack Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Industry classification method | Rule-based scoring (no LLM) | Determinism is critical — same facts must produce same classification every run |
| Template format | JSON files on disk | Editable by domain experts without code changes; version-controlled in git |
| Template storage location | `data/industry_templates/` | Follows existing pattern (`data/` directory for reference data) |
| Benchmark computation | Pure Python, no API calls | Must be fast (<2s) and deterministic; all data already available locally |
| Confidence model | 3 levels (high/medium/low) | Matches existing confidence patterns in the codebase (fact confidence_score) |
| Provenance tracking | Per-field on CompanyProfile, per-metric on comparisons | GPT feedback emphasized this as the #1 trust-building feature |
| Deal lens implementation | Dropdown selector, persisted per deal | PE teams need thesis-specific framing; persists so lens doesn't reset |
| UI integration point | First section on dashboard + dedicated page | Business context must appear BEFORE findings to set the frame |
| HTML report integration | "Section 0" before existing sections | Same principle: context before conclusions |
| CSS approach | Dedicated `business_context.css` with `bc-` prefix | Avoids conflicts with existing styles; follows existing pattern |

---

## New Files Summary

| File | Spec | Type |
|------|------|------|
| `stores/company_profile.py` | 01 | Python — CompanyProfile + ProfileField dataclasses |
| `services/profile_extractor.py` | 01 | Python — Extract profile from FactStore |
| `services/industry_classifier.py` | 02 | Python — Multi-signal industry classification |
| `stores/industry_taxonomy.py` | 02 | Python — Taxonomy definitions + evidence signals |
| `data/industry_templates/insurance.json` | 03 | JSON — Insurance template |
| `data/industry_templates/healthcare.json` | 03 | JSON — Healthcare template |
| `data/industry_templates/financial_services.json` | 03 | JSON — Financial services template |
| `data/industry_templates/manufacturing.json` | 03 | JSON — Manufacturing template |
| `data/industry_templates/technology.json` | 03 | JSON — Technology template |
| `data/industry_templates/general.json` | 03 | JSON — General/fallback template |
| `stores/industry_templates.py` | 03 | Python — Template loader + accessor |
| `services/benchmark_engine.py` | 04 | Python — E/O/V computation engine |
| `models/benchmark_comparison.py` | 04 | Python — BenchmarkReport + comparison dataclasses |
| `web/routes/business_context.py` | 05 | Python — Flask blueprint + routes |
| `web/services/business_context_service.py` | 05 | Python — Orchestration service |
| `web/templates/business_context/overview.html` | 05 | Jinja2 — Main page template |
| `web/templates/business_context/components/*.html` | 05 | Jinja2 — Reusable components (6 files) |
| `web/static/css/business_context.css` | 05 | CSS — Styles |
| `tests/fixtures/business_context_fixtures.py` | 06 | Python — 4 test fixture factories |
| `tests/test_company_profile.py` | 06 | Python — 16 tests |
| `tests/test_industry_classifier.py` | 06 | Python — 14 tests |
| `tests/test_industry_templates.py` | 06 | Python — 10 tests |
| `tests/test_benchmark_engine.py` | 06 | Python — 18 tests |
| `tests/test_business_context_service.py` | 06 | Python — 22+ tests |

**Total: ~28 new files, 4 modified files**

---

## Modified Files Summary

| File | Spec | Change |
|------|------|--------|
| `consistency_engine.py` | 01 | Accept new canonical CompanyProfile instead of old dataclass |
| `web/templates/dashboard.html` | 05 | Add Business Context summary card (first position) |
| `web/templates/base.html` | 05 | Add "Business Context" to sidebar nav (after Dashboard) |
| `tools_v2/html_report.py` | 05 | Add "Section 0: Business Context" to HTML export |

---

## Open Questions

**None.** All architectural decisions are resolved. All data structures are specified. All integration points are identified with exact file paths and function signatures.

---

## Estimated Scope by Component

| Component | New Code (est. lines) | Tests (est. count) | Complexity |
|-----------|-----------------------|--------------------|------------|
| 01 — Company Profile | ~400 | 16 | Low-Medium |
| 02 — Industry Classifier | ~600 | 14 | Medium |
| 03 — Industry Templates | ~300 code + ~2000 JSON | 10 | Low (data entry) |
| 04 — Benchmark Engine | ~700 | 18 | Medium |
| 05 — UI & Report | ~500 Python + ~800 HTML/CSS | 22 | Medium |
| 06 — Testing | ~1200 | 80+ | Low |
| **Total** | **~4500 lines** | **80+ tests** | **Medium** |

---

## Key Design Principles

1. **No LLM calls in this feature.** Everything is deterministic computation on already-extracted data.
2. **Confidence + provenance on every assertion.** If the system doesn't know something, it says so.
3. **Expected / Observed / Variance structure.** Not prose — structured, scannable tables.
4. **Eligibility rules prevent misleading output.** If data is insufficient for a metric, the metric is marked ineligible with a clear reason.
5. **Templates are data, not code.** JSON files editable by domain experts without developer involvement.
6. **Context before conclusions.** Business Context appears first — before risks, work items, or costs.
7. **Deal-lens framing.** Growth, carve-out, turnaround, and platform add-on each emphasize different aspects.

---

All specification documents are complete. The system is fully described and ready to build. Use these documents as your source of truth for implementation.
