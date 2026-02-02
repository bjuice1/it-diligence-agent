# Database Architecture: Implementation Phases

## Overview

Moving from memory-first to database-first architecture in two phases.

**The core problem:** Nothing was being saved to pull up later. Server restart = data gone.

---

## Phase 1: Incremental Writes ✅ IMPLEMENTED

**Goal:** Write data as it's extracted, not at the end.

**Files created:**
- `stores/db_writer.py` - Incremental write service

**Files modified:**
- `web/analysis_runner.py` - Hooked writer into discovery/reasoning loops

**Result:** If analysis crashes, data up to last commit is preserved.

**Documentation:** `docs/phase-1-incremental-writes.md`

---

## Phase 2: Consistent Reads ⏳ NOT STARTED

**Goal:** All UI routes read from database, not memory.

### Key Design Decisions

| Decision | Why |
|----------|-----|
| Scope by **latest completed run** | Multiple runs per deal need deterministic display rule |
| **No in-memory caching** | `lru_cache` causes cross-user issues, won't invalidate |
| **Filter/paginate in SQL** | Python-side filtering won't scale |
| **Repository pattern** | Consistent soft-delete, reusable queries |

### Files to Create

| File | Purpose |
|------|---------|
| `web/context.py` | Deal context resolver (puts `deal_id`, `run_id` on `flask.g`) |
| `web/deal_data.py` | DealData facade for routes |
| `web/repositories/base.py` | BaseRepository with soft-delete handling |
| `web/repositories/fact_repository.py` | Fact queries with pagination |
| `web/repositories/finding_repository.py` | Finding queries |
| `web/repositories/gap_repository.py` | Gap queries |
| `web/repositories/analysis_run_repository.py` | Run queries (`get_latest_completed`) |

### Files to Modify

| File | Change |
|------|--------|
| All blueprint routes | Use DealData instead of `session.fact_store` |
| `web/app.py` | Update status endpoint, deprecate session cache |

### Database Indexes to Add

```sql
CREATE INDEX idx_facts_deal_run ON facts(deal_id, analysis_run_id);
CREATE INDEX idx_findings_deal_run ON findings(deal_id, analysis_run_id);
CREATE INDEX idx_gaps_deal_run ON gaps(deal_id, analysis_run_id);
CREATE INDEX idx_analysis_runs_deal ON analysis_runs(deal_id, status, created_at DESC);
```

**Result:** Data survives server restarts. UI shows consistent data from latest completed run.

**Documentation:** `docs/phase-2-consistent-reads.md`

---

## Verification Checklist

### Phase 1 ✅
- [x] Analysis creates `AnalysisRun` at start
- [x] Facts written to DB after each domain discovery
- [x] Gaps written to DB after each domain discovery
- [x] Findings written to DB after each domain reasoning
- [x] Kill process mid-analysis → data preserved
- [x] Restart analysis → no duplicates (UPSERT)

### Phase 2 ⏳
- [ ] Create `web/context.py` with `load_deal_context()`
- [ ] Create `web/repositories/` with all repository classes
- [ ] Create `web/deal_data.py` with DealData facade
- [ ] Add database indexes
- [ ] Migrate `/applications` route
- [ ] Migrate `/organization` route
- [ ] Migrate `/infrastructure` route
- [ ] Migrate `/cybersecurity` route
- [ ] Migrate `/identity_access` route
- [ ] Migrate `/network` route
- [ ] Update `/api/status` endpoint
- [ ] Remove `SESSION_CACHE` and `get_session()`
- [ ] **Verify:** Restart server → all data still visible
- [ ] **Verify:** Run second analysis → UI shows only latest run data

---

## Architecture Before vs After

### Before (Memory-First)
```
Analysis → Memory → [crash = lost] → DB (end only)
     ↓
    UI reads memory (stale, lost on restart)
```

### After (Database-First)
```
Analysis → DB (immediate) → [crash = preserved]
     ↓
    UI reads DB (consistent, survives restart, scoped to run)
```

---

## Migration Strategy

Phase 2 can be done incrementally:

1. **Create infrastructure** - repos, DealData, context (no impact on existing code)
2. **Add indexes** - run migration
3. **Migrate routes one by one** - keep `get_session()` working during transition
4. **Remove session cache** - once all routes migrated

This allows rollout without breaking the app mid-migration.

---

## Related Documents

- `docs/database-architecture-audit.md` - Full audit of problems and solutions
- `docs/phase-1-incremental-writes.md` - Phase 1 implementation details
- `docs/phase-2-consistent-reads.md` - Phase 2 implementation plan
