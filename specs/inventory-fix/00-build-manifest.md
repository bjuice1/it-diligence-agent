# 00 — Build Manifest: Inventory Fix Specification Suite

## Project: IT Due Diligence Agent — Inventory System Fix
## Date: 2026-02-09
## Scope: Fix entity scoping, inventory population, deduplication, and UI source routing

---

## Problem Statement

The InventoryStore system is fully implemented (content-hashed IDs, entity-aware fingerprints, deal isolation, merge/dedupe logic, schema validation, thread-safe writes) but **never receives data in production**. The `inventory_store` parameter defaults to `None` at every pipeline entry point, causing:

1. **Target shows all apps, Buyer shows none** — entity defaults silently to "target"
2. **Inflated counts** — UI reads from FactStore (same app in 3 docs = 3 counts)
3. **No organization inventory** — deterministic parser lacks org table detection
4. **Dead code** — bidirectional linking (Fact ↔ InventoryItem) never executes
5. **No data quality visibility** — no reconciliation or audit after discovery

---

## Specification Documents

| # | Document | Priority | Status | Summary |
|---|----------|----------|--------|---------|
| 01 | [01-pipeline-wiring.md](01-pipeline-wiring.md) | CRITICAL | NOT STARTED | Create InventoryStore at pipeline entry, pass to discovery agents, persist after completion. Unblocks all other specs. |
| 02 | [02-llm-fact-promotion.md](02-llm-fact-promotion.md) | HIGH | NOT STARTED | Post-discovery promotion of LLM-extracted facts (prose mentions) to InventoryItems. Closes structured/unstructured gap. |
| 03 | [03-entity-enforcement.md](03-entity-enforcement.md) | HIGH | NOT STARTED | Fix silent entity default in `create_inventory_entry`. Add org table parser to deterministic pipeline. |
| 04 | [04-ui-inventory-source-switch.md](04-ui-inventory-source-switch.md) | HIGH | NOT STARTED | Invert route priority: InventoryStore first, FactStore as legacy fallback. Add org bridge function. |
| 05 | [05-reconciliation-and-audit.md](05-reconciliation-and-audit.md) | MEDIUM | NOT STARTED | Wire post-discovery reconciliation, generate per-run audit report, extend matching to all domains. |

---

## Dependency Graph

```
                    ┌──────────────────────────┐
                    │  01 — Pipeline Wiring    │ ← CRITICAL PATH (start here)
                    │  Unblocks everything     │
                    └─────────┬────────────────┘
                              │
              ┌───────────────┼──────────────────┐
              ▼               ▼                  ▼
   ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
   │ 02 — LLM Fact    │  │ 03 — Entity      │  │ (parallel)       │
   │    Promotion     │  │    Enforcement   │  │                  │
   │ Depends: 01, 03  │  │ Depends: none    │  │                  │
   └────────┬─────────┘  └────────┬─────────┘  │                  │
            │                     │             │                  │
            └──────────┬──────────┘             │                  │
                       ▼                        │                  │
            ┌──────────────────────┐            │                  │
            │ 04 — UI Source       │            │                  │
            │    Switch           │◄───────────┘                  │
            │ Depends: 01, 02, 03 │                               │
            └──────────┬──────────┘                               │
                       │                                          │
                       ▼                                          │
            ┌──────────────────────┐                              │
            │ 05 — Reconciliation  │◄─────────────────────────────┘
            │    & Audit          │
            │ Depends: 01, 02, 03 │
            └─────────────────────┘
```

**Note:** Spec 03 has no dependencies and can start in parallel with Spec 01.

---

## Execution Order

### Phase 1 — Foundation (Specs 01 + 03, parallel)

**Spec 01: Pipeline Wiring** — CRITICAL PATH
- Files: `main_v2.py`, `web/tasks/analysis_tasks.py`
- Changes: ~40 lines added, ~10 modified
- Creates `InventoryStore` at all 4 pipeline entry points
- Passes `inventory_store` to discovery agent constructors
- Calls `inventory_store.save()` after discovery completes
- After this: deterministic parser creates InventoryItems from table rows

**Spec 03: Entity Enforcement + Org Parser** — Parallel with 01
- Files: `tools_v2/discovery_tools.py`, `tools_v2/deterministic_parser.py`
- Changes: ~120 lines added, ~5 modified
- Removes silent `entity="target"` default, requires explicit entity from LLM
- Adds `_org_table_to_facts()` for structured org tables (Team, Headcount, FTE, Location)
- Adds `"organization_inventory"` to `detect_table_type()`

### Phase 2 — Enrichment (Spec 02, depends on Phase 1)

**Spec 02: LLM Fact Promotion**
- Files: `tools_v2/inventory_integration.py`, `main_v2.py`, `web/tasks/analysis_tasks.py`
- Changes: ~100 lines added
- New function `promote_facts_to_inventory()` — iterates unlinked facts, matches or creates items
- Wired as post-discovery hook (after save, before audit)
- Category mapping for LLM-extracted facts to inventory types

### Phase 3 — UI Switch (Spec 04, depends on Phases 1+2)

**Spec 04: UI Inventory Source Switch**
- Files: `web/app.py`, `services/organization_bridge.py`, 3 template files
- Changes: ~80 lines added, ~60 modified, ~10/template
- Inverts `/applications`, `/infrastructure`, `/organization` route priority
- New `build_organization_from_inventory_store()` function
- Data source badges in templates ("Inventory Store" vs "Legacy Facts")
- Buyer entity query param support (`?entity=buyer`)

### Phase 4 — Verification (Spec 05, depends on Phases 1+2)

**Spec 05: Reconciliation & Audit**
- Files: `tools_v2/inventory_integration.py`, `main_v2.py`, `web/tasks/analysis_tasks.py`, `web/app.py`, 1 template
- Changes: ~180 lines added, ~30 modified, ~50 template
- `generate_inventory_audit()` — counts, link rates, duplicates, data quality
- Extends `reconcile_facts_and_inventory()` to infra + org (not just apps)
- `/inventory/audit` route for web UI
- Auto-runs after discovery; persists to `inventory_audit.json`

---

## Files Modified (All Specs)

| File | Specs | Nature of Changes |
|------|-------|-------------------|
| `main_v2.py` | 01, 02, 05 | Add inventory_store param, create/pass/save InventoryStore, wire promotion + reconciliation + audit |
| `web/tasks/analysis_tasks.py` | 01, 02, 05 | Same pattern for Celery task entry point |
| `tools_v2/discovery_tools.py` | 03 | Remove silent entity default, require explicit entity |
| `tools_v2/deterministic_parser.py` | 03 | Add `_org_table_to_facts()`, extend `detect_table_type()` |
| `tools_v2/inventory_integration.py` | 02, 05 | Add `promote_facts_to_inventory()`, `generate_inventory_audit()`, `save_inventory_audit()`, extend `reconcile_facts_and_inventory()` |
| `web/app.py` | 04, 05 | Invert route priority (3 routes), add `/inventory/audit` route |
| `services/organization_bridge.py` | 04 | Add `build_organization_from_inventory_store()`, `_safe_int()`, `_safe_float()` |
| `web/templates/applications/overview.html` | 04 | Add data source badge |
| `web/templates/infrastructure/overview.html` | 04 | Add data source badge |
| `web/templates/organization/overview.html` | 04 | Add data source badge |
| `web/templates/inventory/audit.html` | 05 | New template for audit report display |

---

## Estimated Scope

| Metric | Value |
|--------|-------|
| Specs | 5 |
| Files modified | 11 |
| Lines added | ~520 |
| Lines modified | ~105 |
| New functions | 6 (`promote_facts_to_inventory`, `build_organization_from_inventory_store`, `_org_table_to_facts`, `generate_inventory_audit`, `save_inventory_audit`, `_safe_int`/`_safe_float`) |
| New templates | 1 (`inventory/audit.html`) |
| Existing functions extended | 2 (`reconcile_facts_and_inventory`, `detect_table_type`) |
| Existing functions unchanged | All bridge functions (`build_*_from_inventory_store()`) — already implemented and tested |

---

## What Already Exists (No Changes Needed)

These components are fully implemented and require zero modification:

| Component | Location | Status |
|-----------|----------|--------|
| `InventoryStore` | `stores/inventory_store.py` | Full CRUD, query, merge, dedup, thread-safe |
| `InventoryItem` | `stores/inventory_item.py` | Dataclass with entity validation, source_fact_ids |
| `InventorySchemas` | `stores/inventory_schemas.py` | Schemas for app, infra, org, vendor |
| `id_generator` | `stores/id_generator.py` | Content-hashed `I-TYPE-HASH` IDs, entity in hash |
| `BaseDiscoveryAgent.__init__` | `agents_v2/base_discovery_agent.py` | Accepts `inventory_store` param (line 90) |
| `deterministic_preprocess()` | `tools_v2/deterministic_parser.py` | Creates items when `inventory_store is not None` |
| `build_applications_from_inventory_store()` | `services/applications_bridge.py` | Line 353 — builds from InventoryStore |
| `build_infrastructure_from_inventory_store()` | `services/infrastructure_bridge.py` | Line 401 — builds from InventoryStore |
| `sync_inventory_to_facts()` | `tools_v2/inventory_integration.py` | Line 225 — bidirectional sync |
| `reconcile_facts_and_inventory()` | `tools_v2/inventory_integration.py` | Line 319 — similarity matching |
| `get_inventory_store()` | `web/blueprints/inventory.py` | Line 30 — loads from JSON |

---

## Expected Outcomes

After all 5 specs are implemented:

1. **Correct counts**: `/applications` shows unique apps (dedup by content hash), not duplicate facts
2. **Entity separation**: Target and Buyer inventories are distinct; `?entity=buyer` returns buyer-only
3. **Full coverage**: Both table rows (deterministic) and prose mentions (LLM) produce InventoryItems
4. **Organization support**: Org tables parsed deterministically; org bridge function exists
5. **Data quality**: Per-run audit report with linking coverage, duplicates, missing fields
6. **Legacy compatibility**: Deals analyzed before this fix fall back to FactStore counts
7. **Operator visibility**: Data source badges in UI; audit report at `/inventory/audit`

---

## Risks Summary

| Risk | Severity | Mitigation |
|------|----------|------------|
| Return type change in `run_discovery()` breaks callers | Medium | Only 4 call sites, all in same file |
| Entity enforcement causes LLM retries | Low | Better prompts (Spec 03) guide correct entity selection |
| Promotion creates items from low-quality facts | Medium | Quarantine facts without name; confidence threshold |
| Users see lower counts and think data is missing | Medium | Counts were inflated before; add comparison note |
| Parallel Celery tasks write to same InventoryStore | Low | `add_item()` uses `threading.Lock` |

---

## How to Implement

1. Read each spec document in order (01 → 03 → 02 → 04 → 05)
2. Each spec contains exact file locations, line numbers, and code snippets
3. Apply changes to the files indicated
4. Run `pytest tests/` after each spec to verify no regressions
5. Manual verification steps are listed in each spec's "Results Criteria" section

**Start with Spec 01.** Everything else is blocked until InventoryStore is wired into the pipeline.
