# Codebase Cleanup Plan

## Problem Statement
Half-finished V1→V2 migration left two parallel systems. Code exists but isn't wired in. Duplicate implementations everywhere.

**Status: COMPLETED February 6, 2026**

---

## Phase 1: Archive V1 Code ✅ DONE

### Moved to `archive/v1_legacy/`:
```
agents/                    → archive/v1_legacy/agents/
tools/                     → archive/v1_legacy/tools/
main.py                    → archive/v1_legacy/main.py
app_backup.py              → archive/v1_legacy/app_backup.py
storage/                   → archive/v1_legacy/storage/
synthesizer/               → archive/v1_legacy/synthesizer/
```

### V1 Tests Archived:
```
tests/test_analysis_tools.py       → archive/v1_legacy/tests/
tests/test_parallelization.py      → archive/v1_legacy/tests/
tests/test_phase_*.py (6 files)    → archive/v1_legacy/tests/
tests/test_repository.py           → archive/v1_legacy/tests/
tests/test_run_single_agent.py     → archive/v1_legacy/tests/
tests/test_benchmark_service.py    → archive/v1_legacy/tests/
```

**Verification**: ✅ All key modules import successfully

---

## Phase 2: Consolidate Duplicates ✅ DONE

### Database (3 → 1)
**Keep**: `web/database.py` (SQLAlchemy ORM, production) ✅
**Archived**: `storage/database.py`, `tools_v2/database.py` ✅

### Session Management (3 → 1)
**Keep**: `stores/session_store.py` ✅
**Archived**: `web/session_store.py` (redirect stub) ✅
**Keep**: `tools_v2/session.py` (different purpose - DDSession for CLI)

### Excel Export (2 kept, different purposes)
**Keep**: `tools_v2/excel_export.py` (client-ready findings)
**Keep**: `tools_v2/excel_exporter.py` (granular facts multi-sheet)

### Cost Engine
**Keep**: `services/cost_engine/` ✅
**Archived**: `synthesizer/cost_engine.py` ✅

---

## Phase 3: Clean Up tools_v2/ Dead Code ✅ DONE

### Audited & Archived (25 unused files):
```
archive/v1_legacy/tools_v2_dead_code/
├── anchored_estimator.py
├── asset_inventory.py
├── database.py
├── deal_framework.py
├── deterministic_renderer.py
├── evidence_validator.py
├── identity_inventory.py
├── llm_reasoning.py
├── network_inventory.py
├── preprocessing_router.py
├── quality_modes.py
├── question_tracker.py
├── security_inventory.py
├── triage_flow.py
├── workstream_model.py
└── test_phase*.py (10 test files)
```

### Naming - Kept As-Is (not duplicates)
Audit found these files are chained dependencies, not duplicates:
- `reasoning_engine.py` → `reasoning_integration.py` → `reasoning_orchestrator.py`
- `evidence_verifier.py` (active) vs `evidence_validator.py` (archived - unused)
- `synthesis.py` and `consistency_engine.py` (different purposes)

---

## Phase 4: Entry Point Cleanup ✅ DONE

### Official Entry Points:
- `main_v2.py` - CLI pipeline ✅
- `web/app.py` - Flask web server ✅
- `app.py` - Streamlit UI ✅
- `session_cli.py` - Session-based CLI ✅

### Archived:
- `main.py` - V1 entry point ✅
- `app_backup.py` - Old backup ✅

---

## Phase 5: Remove Redirect Stubs ✅ DONE

### Archived to `archive/v1_legacy/tools_v2_redirects/`:
- `tools_v2/fact_store.py`
- `tools_v2/document_store.py`
- `tools_v2/granular_facts_store.py`

### Updated 36+ files to import from `stores/` directly

### Archived to `archive/v1_legacy/redirect_stubs/`:
- `web/session_store.py`

---

## Phase 6: Activity Templates Audit ✅ DONE

**Result**: All 9 activity template files are actively used (16+ imports each). KEPT.

---

## Summary

| Metric | Before | After |
|--------|--------|-------|
| Python files archived | 0 | 70 |
| Test files | 581 (9 broken) | 572 (0 errors) |
| Redirect stubs | 4 | 0 |
| Dead code files | 25+ | 0 |

---

## Success Criteria

After cleanup:
- [x] `main_v2.py` runs without errors
- [x] `docker compose up` works
- [x] Web UI loads and can run analysis
- [x] No imports from archived directories
- [x] Single source of truth for: database, session, cost engine
- [x] pytest collects 572 tests with 0 errors
- [x] All key modules import successfully

---

## Archive Structure

```
archive/v1_legacy/
├── agents/              # V1 discovery agents
├── tools/               # V1 tools
├── storage/             # V1 storage layer
├── synthesizer/         # V1 synthesis
├── main.py              # V1 CLI entry
├── app_backup.py        # Old backup
├── tests/               # 9 V1 test files
├── tools_v2_redirects/  # 3 redirect stubs
├── tools_v2_dead_code/  # 25 unused files
└── redirect_stubs/      # web/session_store.py
```
