# Session Persistence Fix — Implementation Guide

## BUILD MANIFEST

**Status:** READY FOR IMPLEMENTATION
**Total Specs:** 4
**Estimated Effort:** 3-5 hours
**Risk Level:** MEDIUM (database migration + session changes)

---

## Executive Summary

This implementation guide coordinates the execution of 4 specifications that fix the "data lost on page toggle" and "session persistence" issues identified in Audit Stage 1.

**The Problem:**
- Deal selection stored only in ephemeral `flask_session` (lost on browser restart, session expiry, multi-server handoff)
- No database-backed persistence of user's last accessed deal
- Session backend failures cause data loss
- Users see "Please select a deal" errors frequently

**The Solution:**
- **Spec 01:** Add `User.last_deal_id` database schema (persistent storage)
- **Spec 02:** API endpoint for explicit deal selection (dual persistence: session + DB)
- **Spec 03:** Auto-restore hook that loads from DB when session empty (seamless UX)
- **Spec 04:** Harden session architecture for multi-server reliability

**After Implementation:**
- Users never lose their deal selection across sessions
- Application works reliably in multi-server deployments
- Session data persists even if Redis/session backend fails
- Zero "Please select a deal" errors after initial selection

---

## Dependency Graph

```
┌─────────────────────────────────────────────────────────────┐
│ PARALLEL PHASE (can be done simultaneously)                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────┐      ┌──────────────────────┐    │
│  │ Spec 01              │      │ Spec 04              │    │
│  │ Database Schema      │      │ Session Hardening    │    │
│  │ (User.last_deal_id)  │      │ (Redis health check) │    │
│  └──────────┬───────────┘      └──────────────────────┘    │
│             │                                                │
└─────────────┼────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│ SEQUENTIAL PHASE (must be done in order)                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────┐                                   │
│  │ Spec 02              │  (depends on Spec 01)             │
│  │ Deal Selection API   │                                   │
│  │ (POST /api/deals/..  │                                   │
│  └──────────┬───────────┘                                   │
│             │                                                │
│             ▼                                                │
│  ┌──────────────────────┐                                   │
│  │ Spec 03              │  (depends on Specs 01, 02)        │
│  │ Auto-Restore Hook    │                                   │
│  │ (@before_request)    │                                   │
│  └──────────────────────┘                                   │
│                                                              │
└─────────────────────────────────────────────────────────────┘

CRITICAL PATH: Spec 01 → Spec 02 → Spec 03 (3-4 hours)
PARALLEL TRACK: Spec 04 (1 hour, can be done anytime)
```

**Key Insights:**
- Spec 01 is the foundation (all other specs depend on it)
- Spec 04 is independent and can be done in parallel or later
- Spec 03 is the final integration piece (requires 01 and 02)
- Minimum viable fix: Specs 01 + 02 + 03 (Spec 04 is hardening)

---

## Execution Order

### Phase 1: Foundation (CRITICAL PATH)

**Spec 01 — User-Deal Association Schema**
- **Files:** `web/database.py` (~60 lines)
- **Changes:**
  - Add `last_deal_id` and `last_deal_accessed_at` columns to User model
  - Add `update_last_deal()`, `get_last_deal()`, `clear_last_deal()` methods
  - Add migration in `_run_migrations()`
- **Testing:**
  - Run migration locally (SQLite)
  - Verify columns exist: `sqlite3 data/diligence.db ".schema users"`
  - Run 5 unit tests from Spec 01
- **Time:** 1-1.5 hours
- **Risk:** MEDIUM (database migration, must test on staging before production)
- **Rollback:** SQL provided in spec (DROP columns)

**Acceptance Criteria:**
- [ ] Migration runs successfully on local SQLite
- [ ] `users` table has `last_deal_id` and `last_deal_accessed_at` columns
- [ ] User model has helper methods (`update_last_deal`, `get_last_deal`, `clear_last_deal`)
- [ ] All 5 Spec 01 tests pass
- [ ] Existing users have `last_deal_id = NULL` (no data migration needed)

---

### Phase 2: API Integration (CRITICAL PATH)

**Spec 02 — Deal Selection API**
- **Files:**
  - `web/app.py` (~40 lines for `/api/deals/<id>/select` endpoint)
  - `web/permissions.py` (~50 lines, new file)
  - `web/templates/components/deal_selector.html` (~30 lines, optional)
  - `web/static/js/deal_selector.js` (~40 lines, optional)
- **Changes:**
  - Create `user_can_access_deal()` permission helper
  - Add `POST /api/deals/<deal_id>/select` route
  - Add `GET /api/deals/list` route
  - Wire up frontend (or verify existing deal selector)
  - Add audit logging for deal selections
- **Testing:**
  - Test API endpoint with curl/Postman
  - Verify session AND database updated
  - Verify permission checks work
  - Run 7 unit tests from Spec 02
- **Time:** 1-1.5 hours
- **Risk:** LOW (pure addition, no breaking changes)
- **Rollback:** Remove endpoint (app continues to work without it)

**Acceptance Criteria:**
- [ ] `POST /api/deals/<deal_id>/select` endpoint works
- [ ] Endpoint updates both `flask_session['current_deal_id']` AND `User.last_deal_id`
- [ ] Permission check prevents access to deals user doesn't own
- [ ] `GET /api/deals/list` returns user's deals
- [ ] Frontend integration works (or existing selector uses new API)
- [ ] All 7 Spec 02 tests pass
- [ ] Audit log records deal selections

---

### Phase 3: Auto-Restore Integration (CRITICAL PATH)

**Spec 03 — Automatic Context Restoration**
- **Files:** `web/app.py` (~50 lines for `@before_request` hook)
- **Changes:**
  - Add `auto_restore_deal_context()` before-request hook
  - Hook checks session, restores from `User.last_deal_id` if empty
  - Verify permissions before restoring
  - Clear stale `last_deal_id` if access denied
  - Optionally load `flask.g.deal_data` context
- **Testing:**
  - Clear browser cookies, verify deal auto-restores
  - Simulate session expiry, verify restoration
  - Test with deleted deal (should not restore)
  - Test with revoked access (should clear last_deal_id)
  - Run 5 unit tests from Spec 03
- **Time:** 1 hour
- **Risk:** MEDIUM (runs on every request, must be non-fatal)
- **Rollback:** Comment out hook registration (immediate revert)

**Acceptance Criteria:**
- [ ] `@app.before_request` hook registered in `web/app.py`
- [ ] Hook restores `flask_session['current_deal_id']` from database when empty
- [ ] Hook exits early if session already has `current_deal_id` (performance)
- [ ] Hook verifies permissions before restoring
- [ ] Hook clears `last_deal_id` if user lost access
- [ ] All 5 Spec 03 tests pass
- [ ] Manual test: clear cookies, navigate to deal page, no error
- [ ] Logs show "Auto-restored deal..." messages

---

### Phase 4: Session Hardening (PARALLEL TRACK - Optional)

**Spec 04 — Session Architecture Hardening**
- **Files:**
  - `web/app.py` (~50 lines for health check + config)
  - `web/database.py` (~30 lines for session table migration)
  - `web/tasks/maintenance_tasks.py` (~100 lines, new file)
- **Changes:**
  - Add `check_redis_health()` before selecting session backend
  - Create `flask_sessions` table for SQLAlchemy backend
  - Add session cleanup task
  - Add `/api/health/session` endpoint
  - Optional: cache-aside pattern for `current_deal_id`
- **Testing:**
  - Stop Redis, verify fallback to SQLAlchemy
  - Verify `flask_sessions` table created
  - Run cleanup task, verify old sessions deleted
  - Call health endpoint, verify status
  - Run 5 unit tests from Spec 04
- **Time:** 1-1.5 hours
- **Risk:** LOW (infrastructure hardening, no functional changes)
- **Rollback:** Revert config changes (session works without health checks)

**Acceptance Criteria:**
- [ ] Redis health check runs before configuring session backend
- [ ] Logs show "Session backend: Redis (healthy)" or "SQLAlchemy (Redis unavailable)"
- [ ] `flask_sessions` table exists with `expiry` index
- [ ] Cleanup task removes expired sessions
- [ ] `/api/health/session` endpoint returns 200 with backend status
- [ ] All 5 Spec 04 tests pass
- [ ] Multi-server test: sessions persist across load-balanced instances

**Note:** Spec 04 can be deferred to after Specs 01-03 are complete. It's hardening, not required for core functionality.

---

## Testing Strategy

### Unit Tests (Automated)

**Total Tests:** 22 (5 + 7 + 5 + 5 across all specs)

Run all tests:
```bash
pytest tests/test_session_persistence.py -v
```

Individual spec tests:
```bash
pytest tests/test_session_persistence.py::test_user_update_last_deal -v  # Spec 01
pytest tests/test_session_persistence.py::test_select_deal_api -v        # Spec 02
pytest tests/test_session_persistence.py::test_auto_restore_deal -v      # Spec 03
pytest tests/test_session_persistence.py::test_redis_health_check -v     # Spec 04
```

**Create test file:** `tests/test_session_persistence.py` with all tests from specs 01-04.

---

### Integration Tests (Manual)

**Test 1: End-to-end session persistence**
1. Log in as user
2. Select a deal (via API or UI)
3. Verify `User.last_deal_id` set in database
4. Close browser completely
5. Reopen browser, log in
6. Navigate to any deal page
7. ✅ **Expected:** Deal context restored, no "Please select a deal" error

**Test 2: Multi-server session persistence**
1. Deploy to staging with 2+ instances (Railway)
2. Log in, select deal on instance A
3. Force next request to instance B (via load balancer)
4. ✅ **Expected:** Deal context persists across servers

**Test 3: Permission revocation**
1. User A selects deal owned by User B (multi-tenant scenario)
2. Admin revokes User A's access to deal
3. User A logs out and back in
4. ✅ **Expected:** Deal not restored, `last_deal_id` cleared, user sees deal selector

**Test 4: Deleted deal**
1. User selects deal
2. Admin soft-deletes the deal
3. User logs out and back in
4. ✅ **Expected:** Deal not restored (deleted), user sees deal selector

**Test 5: Session expiry**
1. Set `PERMANENT_SESSION_LIFETIME = 60` seconds
2. Log in, select deal
3. Wait 61 seconds
4. Navigate to deal page
5. ✅ **Expected:** Deal auto-restored from database

---

### Staging Environment Tests

Before deploying to production, test on staging:

**Staging Checklist:**
- [ ] Deploy all 4 specs to Railway staging environment
- [ ] Run database migration (PostgreSQL)
- [ ] Verify Redis health check works
- [ ] Test with 2+ Railway instances (multi-server)
- [ ] Simulate Redis failure (scale Redis to 0), verify SQLAlchemy fallback
- [ ] Run all 22 automated tests
- [ ] Run all 5 manual integration tests
- [ ] Monitor logs for errors
- [ ] Check `/api/health/session` endpoint

**Only deploy to production after all staging tests pass.**

---

## Rollback Plan

### Emergency Rollback (< 5 minutes)

If critical issues arise in production:

**Option 1: Disable auto-restore hook**
```python
# In web/app.py, comment out:
# @app.before_request
# def auto_restore_deal_context():
#     ...
```
Redeploy. Users revert to manual deal selection (previous behavior).

**Option 2: Revert to previous deployment**
```bash
# Railway/Heroku
railway rollback
# OR
git revert <commit-hash> && git push
```

**Option 3: Feature flag**
```python
# Add to web/app.py
AUTO_RESTORE_ENABLED = os.environ.get('AUTO_RESTORE_DEAL', 'true').lower() == 'true'

@app.before_request
def auto_restore_deal_context():
    if not AUTO_RESTORE_ENABLED:
        return
    # ... rest of hook
```
Set `AUTO_RESTORE_DEAL=false` in environment variables (no redeploy needed if using Railway).

---

### Database Rollback (if needed)

**Drop new columns (PostgreSQL):**
```sql
DROP INDEX IF EXISTS idx_users_last_deal;
ALTER TABLE users DROP COLUMN last_deal_accessed_at;
ALTER TABLE users DROP COLUMN last_deal_id;
```

**Drop new columns (SQLite):**
```sql
DROP INDEX IF EXISTS idx_users_last_deal;
ALTER TABLE users DROP COLUMN last_deal_accessed_at;
ALTER TABLE users DROP COLUMN last_deal_id;
```

**Drop session table (if Spec 04 deployed):**
```sql
DROP TABLE flask_sessions;
```

**NOTE:** Database rollback is **destructive** (loses all `last_deal_id` data). Only use if absolutely necessary.

---

## Risk Assessment

| Spec | Risk Level | Failure Impact | Mitigation |
|------|-----------|----------------|------------|
| Spec 01 (Schema) | MEDIUM | Migration fails, app won't start | Test on staging PostgreSQL first. Include rollback SQL. Migration is idempotent (safe to re-run). |
| Spec 02 (API) | LOW | New endpoint doesn't work | Pure addition, no breaking changes. Old code continues to work. Can disable endpoint. |
| Spec 03 (Hook) | MEDIUM | Hook crashes, breaks all requests | Entire hook wrapped in try/except. Non-fatal errors logged. Early exit for 99% of requests. |
| Spec 04 (Hardening) | LOW | Health check fails, wrong backend chosen | Health check is conservative (2s timeout). Falls back to SQLAlchemy if Redis unavailable. |

**Overall Risk:** MEDIUM (primarily due to database migration and before-request hook)

**Risk Mitigations:**
- Test all specs on staging before production
- Deploy during low-traffic hours (early morning)
- Monitor error logs for 24 hours after deployment
- Have rollback plan ready (feature flag or revert)
- Use database transaction rollback for migration failures

---

## Deployment Checklist

### Pre-Deployment

- [ ] All 22 unit tests pass locally
- [ ] All 5 manual integration tests pass locally
- [ ] Code reviewed by second developer
- [ ] Staging deployment successful
- [ ] Staging tests pass (PostgreSQL migration)
- [ ] Redis health check works on staging
- [ ] Multi-server test works on staging (2+ Railway instances)
- [ ] Rollback plan documented and tested

### Deployment

- [ ] Deploy during low-traffic window (e.g., 2am-6am)
- [ ] Deploy to production (Railway/Heroku)
- [ ] Monitor deployment logs for errors
- [ ] Run database migration (verify in logs)
- [ ] Verify `/api/health/session` returns 200
- [ ] Verify logs show "Session backend: Redis (healthy)"
- [ ] Test login + deal selection manually
- [ ] Clear browser cookies, verify auto-restore works

### Post-Deployment (24 hour monitoring)

- [ ] Monitor error logs for exceptions from auto-restore hook
- [ ] Check session backend health every 4 hours
- [ ] Verify no increase in "Please select a deal" errors (should decrease)
- [ ] Verify `User.last_deal_id` being set in database (query DB)
- [ ] Check Redis/SQLAlchemy session counts
- [ ] Monitor user support tickets (should decrease)
- [ ] Measure p95 latency (should not increase significantly)

### Post-Deployment (1 week)

- [ ] Analyze session restoration logs (how often auto-restore triggered)
- [ ] Check database for stale `last_deal_id` (deleted deals)
- [ ] Run cleanup task to remove expired sessions
- [ ] Review user feedback (fewer session loss complaints)
- [ ] Consider deploying Spec 04 if not included in initial deployment

---

## Success Metrics

### Quantitative Metrics

**Before Implementation (baseline):**
- "Please select a deal" error rate: ~20% of page loads after session expiry
- User support tickets about "lost deal selection": ~5-10 per week
- Session persistence across browser restarts: 0%
- Multi-server session handoff success: ~60% (depends on sticky sessions)

**After Implementation (target):**
- "Please select a deal" error rate: <1% (only on first login or all deals deleted)
- User support tickets about "lost deal selection": <1 per week
- Session persistence across browser restarts: 99%+
- Multi-server session handoff success: 99%+
- Auto-restore success rate: 95%+ (5% failures due to deleted deals or revoked access)

### Qualitative Metrics

- Users report "seamless experience" when returning to app
- No complaints about "having to select deal again"
- Application feels more "stateful" and "remembers context"
- Developers report fewer bug reports related to session loss

---

## Timeline Estimate

### Conservative Estimate (includes testing)

| Phase | Specs | Time | Cumulative |
|-------|-------|------|------------|
| Phase 1: Schema | Spec 01 | 1.5 hours | 1.5 hours |
| Phase 2: API | Spec 02 | 1.5 hours | 3 hours |
| Phase 3: Auto-Restore | Spec 03 | 1 hour | 4 hours |
| Phase 4: Hardening (optional) | Spec 04 | 1.5 hours | 5.5 hours |
| Testing & Integration | All | 1 hour | 6.5 hours |
| **Total (all specs)** | | | **6.5 hours** |
| **Total (minimal: 01-03)** | | | **5 hours** |

**Recommended approach:**
- **Day 1:** Implement Specs 01-03 (critical path, 4 hours)
- **Day 1:** Test locally and on staging (1 hour)
- **Day 2:** Deploy to production during low-traffic window
- **Day 3:** Monitor for 24 hours, fix any issues
- **Day 4+:** Implement Spec 04 (hardening) if needed

**Fast track (minimal viable fix):**
- Implement only Specs 01-03 (~4 hours)
- Defer Spec 04 to later (can be done anytime)
- Users immediately benefit from session persistence

---

## Dependencies & Prerequisites

### External Services

- PostgreSQL or SQLite database (already configured)
- Redis (optional, recommended for production)
- Celery (optional, only if deploying session cleanup task from Spec 04)

### Code Dependencies

- Flask-Login (already present)
- Flask-Session (already present)
- SQLAlchemy (already present)
- redis-py (already present if using Redis)

**No new external dependencies required for Specs 01-03.**

### Environment Variables

**Required:**
- `DATABASE_URL` - PostgreSQL connection string (already configured)
- `SECRET_KEY` - Flask secret key (already configured)

**Optional (Spec 04):**
- `REDIS_URL` or `REDIS_TLS_URL` - Redis connection string
- `PERMANENT_SESSION_LIFETIME` - Session timeout in seconds (default: 604800 = 7 days)
- `AUTO_RESTORE_DEAL` - Feature flag for auto-restore hook (default: true)

---

## Critical Path

**Minimum viable implementation:**

```
Spec 01 (Schema) → Spec 02 (API) → Spec 03 (Hook) = SESSION PERSISTENCE WORKING
         ↓
    (1.5 hours)  →  (1.5 hours)  →  (1 hour)  = 4 hours total
```

**This is the critical path.** All other work (Spec 04, testing, deployment) is ancillary.

**Spec 04 is off the critical path** and can be done in parallel or deferred.

---

## Post-Implementation Tasks

### Immediate (within 1 week)

- [ ] Monitor logs for auto-restore failures
- [ ] Clean up stale `last_deal_id` references (deleted deals)
- [ ] Add session cleanup cron job (Spec 04)
- [ ] Update documentation with new deal selection flow
- [ ] Train support team on new behavior

### Short-term (within 1 month)

- [ ] Remove manual `load_deal_context()` calls from routes (cleanup)
- [ ] Add user preference "Remember my last deal" toggle (optional)
- [ ] Implement auto-select single deal on first login (optional)
- [ ] Add session analytics dashboard (Spec 04 enhancement)

### Long-term (within 3 months)

- [ ] Multi-region Redis replication (global apps)
- [ ] Session compression to reduce Redis memory
- [ ] Advanced permission system (explicit deal sharing)
- [ ] Audit trail for all deal selections

---

## Appendix: File Map

All specifications are in: `/specs/session-persistence-fix/`

| File | Description | Lines |
|------|-------------|-------|
| `00-implementation-guide.md` | This file (BUILD MANIFEST) | ~800 |
| `01-user-deal-association-schema.md` | Database schema changes | ~450 |
| `02-deal-selection-api.md` | API endpoint specification | ~550 |
| `03-automatic-context-restoration.md` | Auto-restore hook specification | ~600 |
| `04-session-architecture-hardening.md` | Session backend hardening | ~700 |

**Total specification documentation:** ~3,100 lines

---

## Appendix: Spec Dependencies Matrix

|       | Spec 01 | Spec 02 | Spec 03 | Spec 04 |
|-------|---------|---------|---------|---------|
| **Spec 01** | — | Required | Required | Independent |
| **Spec 02** | Requires 01 | — | Required | Independent |
| **Spec 03** | Requires 01 | Requires 02 | — | Independent |
| **Spec 04** | Independent | Independent | Independent | — |

**Legend:**
- **Required:** This spec must be completed first
- **Independent:** Can be done in any order or in parallel

---

## Conclusion

This implementation guide provides a complete roadmap for fixing the session persistence issues identified in Audit Stage 1. Follow the execution order, run all tests, and deploy carefully to ensure a smooth rollout.

**Recommended first step:** Implement Spec 01 (database schema) and verify migration works on local SQLite and staging PostgreSQL.

**Questions or issues during implementation?** Refer to the individual spec documents for detailed technical guidance.

---

**READY TO BUILD.** 🚀
