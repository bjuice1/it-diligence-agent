# Database Architecture Audit

## Executive Summary

The system had a **memory-first architecture** where data lived in Python objects during analysis and was only written to the database at the very end. This created significant problems:

- **No Persistence**: Data couldn't be pulled up after server restart
- **Crash = Total Data Loss**: If the process crashed during analysis, all extracted data was lost
- **UI Inconsistency**: Routes loaded data from different sources (some DB, some memory)

**Solution:** Two-phase migration to database-first architecture.

| Phase | Goal | Status |
|-------|------|--------|
| Phase 1 | Write to DB immediately during analysis | IMPLEMENTED |
| Phase 2 | Read from DB consistently in all routes | NOT STARTED |

---

## The Core Problem

**Nothing was being saved in a way you could pull it up later.**

```
User runs analysis → Data lives in Python memory → Views results in UI → Closes laptop
                                                                              ↓
                                                          Next day: Everything gone
```

The system was designed for single-session batch processing, not for a real product where you come back to review deals.

---

## Problems Identified (Pre-Fix)

### 1. Late Persistence

**Location:** `web/analysis_runner.py` - `persist_to_database()` function

```
Analysis starts
  ↓
Facts extracted (memory only)
  ↓
Gaps identified (memory only)
  ↓
Findings generated (memory only)
  ↓
[CRASH HERE = ALL DATA LOST]
  ↓
persist_to_database() ← Only writes at the very end
```

### 2. Inconsistent Data Sources

| Route | Data Source | Problem |
|-------|-------------|---------|
| `/facts` | Database | OK |
| `/risks` | Database | OK |
| `/applications` | Memory (fact_store) | Disappears on restart |
| `/organization` | Memory (fact_store) | Disappears on restart |
| `/gaps` | Was never loaded from DB | Fixed in session |

### 3. Session/Cache Problems

- `get_session()` loads some data from DB but not all
- In-memory session can be stale relative to database
- No cache invalidation strategy
- `lru_cache` or global caches are dangerous (cross-user leakage, no invalidation on writes)

### 4. Analysis Run Tracking

- `AnalysisRun` record created at END of analysis
- No way to track in-progress analysis in database
- If server restarts, UI loses track of running analysis

### 5. No Run Scoping

- Multiple analysis runs per deal create "soup" of mixed data
- No rule for which run's data to display
- Users see findings appear/disappear confusingly

---

## Stores Identified

| Store | Location | Persisted? | When? |
|-------|----------|------------|-------|
| `FactStore` | `stores/fact_store.py` | Yes | End of analysis |
| `ReasoningStore` | `stores/reasoning_store.py` | Yes | End of analysis |
| `GapStore` | Part of FactStore | Yes | End of analysis |
| `DocumentStore` | In-memory | No | Never |
| `SessionCache` | `web/app.py` | No | Never |

---

## Root Cause

The architecture was designed for **batch processing** (run analysis → save results → display), not for a **real product** that needs:
- Data to survive restarts
- Multiple users viewing the same deal
- Multiple analysis runs per deal
- Real-time progress visibility

---

## Solution: Two-Phase Fix

### Phase 1: Incremental Database Writes (IMPLEMENTED)

Write facts, gaps, and findings to database **immediately after extraction**, not at the end.

**File:** `stores/db_writer.py`

**What it does:**
- Creates `AnalysisRun` at START of analysis
- Writes each fact/gap/finding immediately after extraction
- Uses UPSERT for idempotent retries
- Throttles progress updates to avoid DB spam
- Commits after each write for crash durability

**Integration:** `web/analysis_runner.py` - `IncrementalPersistence` class

**Result:** If analysis crashes at 60%, you keep the 60% that was written.

**Documentation:** `docs/phase-1-incremental-writes.md`

---

### Phase 2: Consistent Database Reads (NOT YET IMPLEMENTED)

All routes read from database as the single source of truth.

**Key Design Decisions:**

| Decision | Rationale |
|----------|-----------|
| **Scope by latest completed run** | Multiple runs per deal → need deterministic rule for what to show |
| **No in-memory caching** | `lru_cache` causes cross-user issues, doesn't invalidate on writes |
| **Filter/paginate in SQL** | Loading 500 rows then filtering in Python won't scale |
| **Repository pattern** | Consistent soft-delete handling, reusable query logic |

**Architecture:**

```
Routes → DealData → Repositories → Models → Database
           ↓
       flask.g (deal_id, run_id context)
```

| Layer | Responsibility |
|-------|----------------|
| **Routes** | Parse params, call DealData, render response |
| **DealData** | Facade for common use cases (dashboard, domain pages) |
| **Repositories** | SQL queries with filtering, pagination, soft-delete |
| **Models** | SQLAlchemy ORM |

**Files to create:**
- `web/context.py` - Deal context resolver
- `web/deal_data.py` - DealData facade
- `web/repositories/` - Repository classes

**Result:** Data survives server restarts. UI shows consistent data from latest completed run.

**Documentation:** `docs/phase-2-consistent-reads.md`

---

## Files Modified in Phase 1

| File | Change |
|------|--------|
| `stores/db_writer.py` | NEW - Incremental write service |
| `web/analysis_runner.py` | Added `IncrementalPersistence` class, hooked into discovery/reasoning loops |

---

## Files to Create in Phase 2

| File | Purpose |
|------|---------|
| `web/context.py` | Deal context resolver (`load_deal_context`) |
| `web/deal_data.py` | DealData + EmptyDealData facades |
| `web/repositories/base.py` | BaseRepository with soft-delete |
| `web/repositories/fact_repository.py` | Fact queries |
| `web/repositories/finding_repository.py` | Finding queries |
| `web/repositories/gap_repository.py` | Gap queries |
| `web/repositories/analysis_run_repository.py` | Run queries |

## Files to Modify in Phase 2

| File | Change |
|------|--------|
| `web/blueprints/applications.py` | Use DealData instead of session |
| `web/blueprints/organization.py` | Use DealData instead of session |
| `web/blueprints/infrastructure.py` | Use DealData instead of session |
| `web/blueprints/cybersecurity.py` | Use DealData instead of session |
| `web/blueprints/identity_access.py` | Use DealData instead of session |
| `web/blueprints/network.py` | Use DealData instead of session |
| `web/app.py` | Update status endpoint, deprecate session cache |

---

## Database Indexes Needed

```sql
CREATE INDEX idx_facts_deal_id ON facts(deal_id);
CREATE INDEX idx_facts_deal_domain ON facts(deal_id, domain);
CREATE INDEX idx_facts_deal_run ON facts(deal_id, analysis_run_id);
CREATE INDEX idx_findings_deal_id ON findings(deal_id);
CREATE INDEX idx_findings_deal_type ON findings(deal_id, finding_type);
CREATE INDEX idx_findings_deal_run ON findings(deal_id, analysis_run_id);
CREATE INDEX idx_gaps_deal_id ON gaps(deal_id);
CREATE INDEX idx_gaps_deal_run ON gaps(deal_id, analysis_run_id);
CREATE INDEX idx_analysis_runs_deal ON analysis_runs(deal_id, status, created_at DESC);
```

---

## Architecture Before vs After

### Before (Memory-First)

```
Analysis → Memory → [crash = lost] → DB (end only)
     ↓
    UI reads memory (stale, gone on restart)
```

### After (Database-First)

```
Analysis → DB (immediate) → [crash = preserved]
     ↓
    UI reads DB (consistent, survives restart, scoped to latest run)
```

---

## Related Documents

- `docs/phase-1-incremental-writes.md` - Phase 1 implementation details
- `docs/phase-2-consistent-reads.md` - Phase 2 implementation plan
- `docs/database-architecture-phases.md` - Phase overview and checklists
