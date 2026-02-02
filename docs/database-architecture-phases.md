# Database Architecture: Implementation Phases

## Overview

Moving from memory-first to database-first architecture in three phases.

**The core problem:** Nothing was being saved to pull up later. Server restart = data gone.

| Phase | Focus | Status |
|-------|-------|--------|
| Phase 1 | Incremental Writes | ✅ Complete |
| Phase 2 | Consistent Reads | ✅ Complete |
| Phase 3 | Auth Database Migration | ⏳ Not Started |

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

## Phase 2: Consistent Reads ✅ IMPLEMENTED

**Goal:** All UI routes read from database, not memory.

### Key Design Decisions

| Decision | Why |
|----------|-----|
| Scope by **latest completed run** | Multiple runs per deal need deterministic display rule |
| **No in-memory caching** | `lru_cache` causes cross-user issues, won't invalidate |
| **Filter/paginate in SQL** | Python-side filtering won't scale |
| **Repository pattern** | Consistent soft-delete, reusable queries |
| **include_orphaned parameter** | Legacy data with NULL run_id remains visible |

### Files Created

| File | Purpose |
|------|---------|
| `web/context.py` | Deal context resolver (puts `deal_id`, `run_id` on `flask.g`) |
| `web/repositories/base.py` | BaseRepository with soft-delete handling |
| `web/repositories/fact_repository.py` | Fact queries with pagination |
| `web/repositories/finding_repository.py` | Finding queries |
| `web/repositories/gap_repository.py` | Gap queries |
| `web/repositories/analysis_run_repository.py` | Run queries (`get_latest_completed`) |
| `web/repositories/__init__.py` | Repository exports |

### Critical Fixes Applied

| Issue | Fix |
|-------|-----|
| `context.py` returned `run_id=None` when no completed run | Added fallback to latest run of ANY status |
| Facts with NULL `analysis_run_id` were invisible | Added `include_orphaned=True` parameter with OR condition |
| `get_linked_facts/findings` returned soft-deleted records | Added JOIN with parent table + `deleted_at IS NULL` filter |

**Result:** Data survives server restarts. UI shows consistent data from latest completed run.

**Documentation:** `docs/phase-2-consistent-reads.md`

---

## Phase 3: Auth Database Migration ⏳ NOT STARTED

**Goal:** Migrate authentication from file-based (`users.json`) to database.

### The Problem

| Component | Current State | Issue |
|-----------|---------------|-------|
| `web/models/user.py` | File-based `UserStore` with `users.json` | Won't scale, no transactions, inconsistent with DB-first architecture |
| `web/database.py` | SQLAlchemy `User` model exists | Unused - has proper schema but no auth integration |
| Login/Signup routes | Use `UserStore.load_user()` | Need to switch to database queries |

### Files to Create

| File | Purpose |
|------|---------|
| `web/repositories/user_repository.py` | User CRUD with email lookups, password hashing integration |
| `web/services/auth_service.py` | AuthService facade for login/register/logout |
| `scripts/migrate_users_to_db.py` | One-time migration from `users.json` to database |

### Files to Modify

| File | Change |
|------|--------|
| `web/auth/routes.py` | Replace `UserStore` calls with `AuthService` |
| `web/models/user.py` | Deprecate `UserStore` class |

### Key Features

- **Password hashing**: bcrypt via `werkzeug.security`
- **Email normalization**: Case-insensitive lookups
- **Soft-delete support**: Consistent with other repositories
- **Multi-tenant ready**: `tenant_id` column already exists
- **Flask-Login integration**: `User` model implements `UserMixin`

### Migration Strategy

1. Create `UserRepository` and `AuthService` (no impact on existing code)
2. Run migration script to copy users from JSON to database
3. Update auth routes to use new service
4. Verify login/logout/signup work
5. Remove `users.json` and `UserStore` class

**Result:** Unified data layer - all app data (deals, facts, users) in the database.

**Documentation:** `docs/phase-3-auth-database-migration.md`

---

## Verification Checklist

### Phase 1 ✅
- [x] Analysis creates `AnalysisRun` at start
- [x] Facts written to DB after each domain discovery
- [x] Gaps written to DB after each domain discovery
- [x] Findings written to DB after each domain reasoning
- [x] Kill process mid-analysis → data preserved
- [x] Restart analysis → no duplicates (UPSERT)

### Phase 2 ✅
- [x] Create `web/context.py` with `load_deal_context()`
- [x] Create `web/repositories/` with all repository classes
- [x] Add `include_orphaned` parameter for legacy data visibility
- [x] Fix soft-delete filtering in FactFindingLink queries
- [x] Fix fallback when no completed run exists
- [x] **Verify:** Restart server → all data still visible
- [x] **Verify:** Run second analysis → UI shows only latest run data

### Phase 3 ⏳
- [ ] Create `web/repositories/user_repository.py`
- [ ] Create `web/services/auth_service.py`
- [ ] Create migration script `scripts/migrate_users_to_db.py`
- [ ] Run migration to copy users from JSON to database
- [ ] Update `web/auth/routes.py` to use `AuthService`
- [ ] Deprecate `UserStore` class in `web/models/user.py`
- [ ] **Verify:** Login with existing account works
- [ ] **Verify:** Register new account works
- [ ] **Verify:** Server restart → sessions persist
- [ ] Remove `users.json` and `UserStore` code

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

Each phase can be done incrementally without breaking the app:

### Phase 2 (Complete)
1. ✅ Create infrastructure - repos, context (no impact on existing code)
2. ✅ Migrate routes one by one
3. ✅ Apply critical fixes for edge cases

### Phase 3 (Next)
1. Create `UserRepository` and `AuthService` (no impact)
2. Run migration script to copy users from JSON to DB
3. Update auth routes to use new service
4. Test login/logout/register
5. Remove deprecated code

---

## Related Documents

- `docs/database-architecture-audit.md` - Full audit of problems and solutions
- `docs/phase-1-incremental-writes.md` - Phase 1 implementation details
- `docs/phase-2-consistent-reads.md` - Phase 2 implementation details
- `docs/phase-3-auth-database-migration.md` - Phase 3 implementation plan
