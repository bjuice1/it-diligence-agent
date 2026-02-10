# 03 — Automatic Context Restoration

## Status: NOT STARTED
## Priority: HIGH (Critical UX improvement)
## Depends On: 01-user-deal-association-schema, 02-deal-selection-api
## Enables: Seamless user experience across sessions

---

## Overview

Currently, users must manually re-select their deal after session expiry, browser restart, or server restart. This creates friction and "Please select a deal" errors throughout the application.

**The fix:** Add a `@app.before_request` hook that automatically restores `flask_session['current_deal_id']` from `User.last_deal_id` when the session is empty, creating a seamless experience.

This spec depends on:
- **Spec 01:** Database schema with `User.last_deal_id` and helper methods
- **Spec 02:** API endpoint that writes to both session and database

With those in place, this hook reads from the database source of truth and restores the session transparently.

---

## Architecture

```
CURRENT FLOW (manual restoration):
  User logs in → Session empty → User clicks page → "Please select a deal" error
  User must manually select deal again

AFTER THIS SPEC (automatic restoration):
  User logs in → Session empty → before_request hook runs
    → Check flask_session['current_deal_id']
    → If empty, load from User.last_deal_id
    → Verify deal exists and user has access
    → Restore flask_session['current_deal_id']
  User clicks page → Deal context already loaded → No error
```

**Data Flow:**

1. Every HTTP request triggers `@app.before_request`
2. Hook checks if `flask_session['current_deal_id']` exists
3. If missing and user is authenticated:
   - Load `current_user.get_last_deal()` (Spec 01 method)
   - Verify deal is not deleted and user has access
   - Restore `flask_session['current_deal_id']`
   - Optionally load `flask.g.deal_data` (existing context.py pattern)
4. If restoration fails (no last deal, access revoked, deal deleted):
   - Leave session empty
   - User sees deal selector on next page that requires a deal

---

## Specification

### Change 1: Add before-request hook in `web/app.py`

**Location:** After the existing `before_request` hooks (around line 340 in `web/app.py`)

**Add this hook:**

```python
@app.before_request
def auto_restore_deal_context():
    """
    Automatically restore deal context from database when session is empty.

    This hook runs on every request for authenticated users. If the session
    doesn't have a current_deal_id but the user has a last_deal_id in the
    database, we restore it to the session.

    This ensures users don't see "Please select a deal" errors after:
    - Session expiry
    - Browser restart
    - Server restart
    - Multi-server handoff

    Note:
        Only restores if user has access to the deal (permissions checked).
        Does not restore if deal is deleted or access was revoked.
    """
    from flask_login import current_user
    from flask import session as flask_session

    # Only run for authenticated users
    if not current_user.is_authenticated:
        return

    # Only restore if session is empty
    if flask_session.get('current_deal_id'):
        return

    # Attempt to restore from database
    try:
        last_deal = current_user.get_last_deal()

        if not last_deal:
            # User has no last deal recorded
            return

        # Verify user still has access (permissions may have changed)
        from web.permissions import user_can_access_deal
        if not user_can_access_deal(current_user, last_deal):
            # User lost access to this deal - clear it from database
            current_user.clear_last_deal()
            db.session.commit()
            logger.warning(f"User {current_user.id} lost access to deal {last_deal.id}, cleared last_deal_id")
            return

        # Restore to session
        flask_session['current_deal_id'] = last_deal.id
        flask_session.modified = True

        logger.info(f"Auto-restored deal {last_deal.id} for user {current_user.id} from database")

        # Optionally: Also load deal context into flask.g
        # (This matches the existing pattern in web/context.py)
        try:
            from web.context import load_deal_context
            load_deal_context()
        except Exception as context_error:
            # Non-fatal: session is restored even if g.deal_data fails
            logger.warning(f"Failed to load deal context into flask.g: {context_error}")

    except Exception as e:
        # Non-fatal: Don't break the request if restoration fails
        logger.error(f"Auto-restore deal context failed for user {current_user.id}: {e}")
```

**Why this approach:**
- Runs on every request → Catches session loss immediately
- Permission check → Prevents restoring deals user no longer has access to
- Clears stale `last_deal_id` → Keeps database clean
- Non-fatal errors → Doesn't break requests if restoration fails
- Logs restoration → Helps debug session issues

---

### Change 2: Update existing routes to remove manual context loading

**Background:** Many routes currently call `load_deal_context()` manually at the start. With automatic restoration, these calls are now redundant.

**Search pattern:**
```bash
grep -r "load_deal_context()" web/*.py
```

**Strategy:**
1. Routes that call `load_deal_context()` can keep it (it's idempotent)
2. New routes don't need to call it (auto-restore handles it)
3. Consider removing manual calls in future refactor (optional cleanup)

**Example route before:**
```python
@app.route('/deals/<deal_id>/analysis')
@login_required
def deal_analysis(deal_id):
    # Manual context loading
    from web.context import load_deal_context
    load_deal_context()

    # ... rest of route
```

**Example route after (simplified):**
```python
@app.route('/deals/<deal_id>/analysis')
@login_required
def deal_analysis(deal_id):
    # No manual load needed - auto-restore hook handles it
    # ... rest of route
```

**Note:** This cleanup is **optional** and not required for Spec 03 to work. The hook is additive and doesn't break existing manual calls.

---

### Change 3: Handle first-login flow (user has no last_deal_id)

**Scenario:** New user logs in for the first time, or user whose deals were all deleted.

**Current behavior:** `User.last_deal_id = NULL` → Auto-restore does nothing → User sees "Please select a deal"

**Desired behavior:** Same as current (no change). Users must explicitly select a deal at least once.

**Future enhancement (optional):** Auto-select if user owns exactly one deal:

```python
# In auto_restore_deal_context hook, after checking last_deal
if not last_deal:
    # Optional: Auto-select if user owns exactly one deal
    from web.database import Deal
    user_deals = Deal.query.filter_by(
        owner_id=current_user.id,
        deleted_at=None
    ).all()

    if len(user_deals) == 1:
        # User owns exactly one deal - auto-select it
        only_deal = user_deals[0]
        flask_session['current_deal_id'] = only_deal.id
        flask_session.modified = True

        # Also save to database for future sessions
        current_user.update_last_deal(only_deal.id)
        db.session.commit()

        logger.info(f"Auto-selected only deal {only_deal.id} for user {current_user.id}")
```

**This is NOT required for Spec 03** but can be added later if desired.

---

### Change 4: Add restoration metrics (optional observability)

**Purpose:** Track how often auto-restoration happens vs. fails.

**Implementation:** Add metrics to the before-request hook:

```python
# At the top of auto_restore_deal_context()
from web.database import AuditLog  # Assuming audit log exists

# After successful restoration
AuditLog.create(
    user_id=current_user.id,
    action='auto_restore_deal',
    resource_type='deal',
    resource_id=last_deal.id,
    details={'source': 'before_request_hook'}
)

# After access denied
AuditLog.create(
    user_id=current_user.id,
    action='auto_restore_failed',
    resource_type='deal',
    resource_id=last_deal.id,
    details={'reason': 'access_denied'}
)
```

**This is optional** for Spec 03. Audit logging may not exist yet.

---

### Change 5: Performance considerations

**Concern:** Running a database query on every request adds latency.

**Mitigation 1: Early exit if session exists**
```python
if flask_session.get('current_deal_id'):
    return  # No DB query needed
```
This means 99% of requests (with warm sessions) skip the DB query entirely.

**Mitigation 2: Lazy relationship loading**
```python
# In User model (Spec 01)
last_deal = relationship('Deal', foreign_keys=[last_deal_id], lazy='select')
```
Uses `lazy='select'` (default) to only load deal when accessed.

**Mitigation 3: Add caching (future enhancement)**
```python
# Cache last_deal_id in Redis for 5 minutes
cache_key = f"user:{current_user.id}:last_deal_id"
cached_deal_id = redis_client.get(cache_key)

if cached_deal_id:
    flask_session['current_deal_id'] = cached_deal_id
    return

# Otherwise fall through to DB query
```

**For Spec 03:** No caching needed. Early exit is sufficient.

---

### Change 6: Testing the hook

**Manual test:**
1. Log in and select a deal
2. Verify `User.last_deal_id` is set in database
3. Clear browser cookies (or `flask_session.clear()`)
4. Navigate to any page that requires a deal
5. Verify deal context is automatically restored (no "Please select a deal" error)
6. Check logs for "Auto-restored deal..." message

**Session expiry test:**
1. Set `PERMANENT_SESSION_LIFETIME = 60` (1 minute)
2. Log in, select deal, wait 61 seconds
3. Navigate to deal page
4. Verify auto-restore works

**Multi-server test (requires staging environment):**
1. Deploy to multi-server environment (e.g., Railway with 2+ instances)
2. Log in, select deal on server A
3. Force next request to server B (load balancer)
4. Verify deal context restored on server B

---

## Benefits

1. **Zero-friction UX** — Users never see "Please select a deal" after session loss
2. **Multi-server compatibility** — Works across load-balanced servers
3. **Minimal performance impact** — Early exit for 99% of requests
4. **Permission-aware** — Automatically clears stale deals when access revoked
5. **Backward compatible** — Doesn't break existing manual `load_deal_context()` calls

---

## Expectations

After this spec is implemented:

1. The `@app.before_request` hook is registered in `web/app.py`
2. Users' deal context is automatically restored from database when session is empty
3. Users no longer see "Please select a deal" errors after session expiry
4. The hook logs successful restorations and failures
5. Permission checks prevent restoring deals user no longer has access to
6. The hook is non-fatal (doesn't break requests if restoration fails)

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Hook adds latency to every request | Low | Low | Early exit if session exists (99% of requests). Only first request after session loss queries DB. |
| Race condition: two requests restore simultaneously | Low | Low | Flask sessions are per-request. Both will set the same `deal_id`. Last write wins (harmless). |
| User's access revoked but last_deal_id still set | Medium | Medium | Hook verifies permissions before restoring. Calls `clear_last_deal()` if access denied. |
| Hook fails and breaks all requests | Low | High | Entire hook wrapped in try/except. Errors logged but non-fatal. Request continues. |
| Restoration loop: hook restores deal A, another hook changes to B | Low | Low | Hook only runs if session is empty. Once restored, early exit prevents loops. |
| Deal deleted but last_deal_id still references it | Low | Low | `get_last_deal()` checks `is_deleted`. Returns None if deal is soft-deleted. |

---

## Results Criteria

### Automated Tests

**Test 1: Auto-restore on empty session**
```python
def test_auto_restore_deal_on_empty_session(client, auth_user, deal):
    """Verify hook restores deal from database when session is empty."""
    # Set last_deal_id in database
    auth_user.update_last_deal(deal.id)
    db.session.commit()

    # Log in (creates session)
    with client.session_transaction() as sess:
        # Simulate empty session
        sess.pop('current_deal_id', None)

    # Make request to any authenticated route
    response = client.get('/deals')

    # Verify deal was auto-restored to session
    with client.session_transaction() as sess:
        assert sess.get('current_deal_id') == deal.id
```

**Test 2: Hook does not run if session already has deal**
```python
def test_auto_restore_skips_if_session_exists(client, auth_user, deal):
    """Verify hook exits early if session already has current_deal_id."""
    # Set last_deal_id in database to deal A
    deal_a = deal
    auth_user.update_last_deal(deal_a.id)
    db.session.commit()

    # Create deal B
    deal_b = Deal(id='deal-b', target_name='Other Corp', owner_id=auth_user.id)
    db.session.add(deal_b)
    db.session.commit()

    # Set session to deal B
    with client.session_transaction() as sess:
        sess['current_deal_id'] = deal_b.id

    # Make request
    client.get('/deals')

    # Verify session still has deal B (not overwritten by database's deal A)
    with client.session_transaction() as sess:
        assert sess.get('current_deal_id') == deal_b.id
```

**Test 3: Hook clears last_deal_id if access denied**
```python
def test_auto_restore_clears_on_access_denied(client, auth_user, other_user):
    """Verify hook clears last_deal_id if user lost access."""
    # Create deal owned by other_user
    deal = Deal(id='deal-123', target_name='Corp', owner_id=other_user.id)
    db.session.add(deal)
    db.session.commit()

    # Set auth_user's last_deal_id to this deal (simulating past access)
    auth_user.update_last_deal(deal.id)
    db.session.commit()

    # Clear session
    with client.session_transaction() as sess:
        sess.pop('current_deal_id', None)

    # Make request
    client.get('/deals')

    # Verify session is still empty (deal not restored)
    with client.session_transaction() as sess:
        assert sess.get('current_deal_id') is None

    # Verify last_deal_id was cleared in database
    db.session.refresh(auth_user)
    assert auth_user.last_deal_id is None
```

**Test 4: Hook handles deleted deals gracefully**
```python
def test_auto_restore_handles_deleted_deal(client, auth_user, deal):
    """Verify hook returns None if last_deal is soft-deleted."""
    # Set last_deal_id
    auth_user.update_last_deal(deal.id)
    db.session.commit()

    # Soft-delete the deal
    deal.soft_delete()
    db.session.commit()

    # Clear session
    with client.session_transaction() as sess:
        sess.pop('current_deal_id', None)

    # Make request
    client.get('/deals')

    # Verify session is empty (deleted deal not restored)
    with client.session_transaction() as sess:
        assert sess.get('current_deal_id') is None
```

**Test 5: Hook does not run for anonymous users**
```python
def test_auto_restore_skips_anonymous(client):
    """Verify hook does not run for unauthenticated users."""
    # Make request as anonymous user
    response = client.get('/')

    # Should not crash (no current_user.get_last_deal() call)
    assert response.status_code in [200, 302]  # Either success or redirect to login
```

### Manual Verification

1. **Session expiry test:**
   - Log in, select deal, wait for session to expire
   - Navigate to any deal page
   - Verify deal is auto-restored (no error)

2. **Browser restart test:**
   - Log in, select deal, close browser
   - Reopen browser, navigate to application
   - Verify deal is auto-restored

3. **Multi-server test (staging only):**
   - Deploy to Railway/Heroku with 2+ instances
   - Log in, select deal
   - Force next request to different server (via load balancer)
   - Verify deal is auto-restored

4. **Permission revocation test:**
   - User A selects deal owned by User B (via multi-tenancy)
   - Admin revokes User A's tenant access
   - User A logs in again
   - Verify deal is NOT restored, last_deal_id is cleared

5. **Deleted deal test:**
   - User selects deal
   - Admin soft-deletes deal
   - User logs in again
   - Verify deal is NOT restored, no errors

---

## Files Modified

| File | Change |
|------|--------|
| `web/app.py` | Add `@app.before_request` hook `auto_restore_deal_context()` (after line 340, ~50 lines) |
| `web/permissions.py` | Use existing `user_can_access_deal()` from Spec 02 (no changes) |

**Lines of code:** ~50 lines (hook implementation)

---

## Dependencies

**External:**
- Requires Flask-Login (already present)
- Requires flask.session (already configured)

**Internal:**
- **Requires Spec 01:** `User.get_last_deal()` and `User.clear_last_deal()` methods
- **Requires Spec 02:** `user_can_access_deal()` permission helper
- Uses existing `web/context.py::load_deal_context()` (optional)
- Uses existing `web/database.py::Deal` model

**Enables:**
- Seamless UX across sessions, browsers, servers
- Foundation for removing manual `load_deal_context()` calls in routes (future cleanup)

---

## Implementation Notes

### Hook Execution Order

Flask runs `@app.before_request` hooks in registration order. This hook should run **after** authentication hooks (so `current_user` is available) but **before** any route logic.

**Current hook order in `web/app.py`:**
1. Line 318: `check_auth_token()` - API token authentication
2. Line 330: `load_user_from_session()` - Flask-Login user loading
3. **→ INSERT HERE:** `auto_restore_deal_context()` (this spec)
4. Route handler runs

### Integration with existing code

**With `web/context.py::load_deal_context()`:**
- This hook can optionally call `load_deal_context()` after restoring the session
- This populates `flask.g.deal_data` for routes that use it
- The hook includes this call with a try/except (non-fatal if it fails)

**With Spec 02 API endpoint:**
- When user explicitly calls `/api/deals/<id>/select`, both session and database are updated
- Future requests use the hook to restore from database
- The two specs work together seamlessly

**With Spec 04 (session hardening):**
- Spec 04 will ensure session backend is reliable (Redis/SQLAlchemy)
- This hook works regardless of session backend (reads from database)
- Together they provide defense-in-depth

---

## Future Enhancements

1. **Auto-select single deal:** If user owns exactly one deal, auto-select it on first login
2. **Cache last_deal_id in Redis:** Avoid DB query on every first request after session loss
3. **Metrics dashboard:** Track auto-restore success/failure rates
4. **User preference:** "Remember my last deal" toggle in settings (default: on)
5. **Route cleanup:** Remove manual `load_deal_context()` calls from routes (they're now redundant)

---

## Success Metrics

After deployment:

1. **"Please select a deal" error rate drops to near-zero** (track in error logs)
2. **User support tickets about "lost deal selection" decrease**
3. **Session restoration logs show successful auto-restore** on first request after session loss
4. **No performance degradation** (measure p95 latency for authenticated requests)
5. **Zero crashes or exceptions** from the hook (monitor error logs)

Target: <1% of authenticated requests trigger the restoration path (most have warm sessions).

---

## Rollback Plan

If this hook causes issues:

1. **Comment out the hook registration:**
   ```python
   # @app.before_request
   # def auto_restore_deal_context():
   #     ...
   ```

2. **Or add feature flag:**
   ```python
   AUTO_RESTORE_ENABLED = os.environ.get('AUTO_RESTORE_DEAL', 'true').lower() == 'true'

   @app.before_request
   def auto_restore_deal_context():
       if not AUTO_RESTORE_ENABLED:
           return
       # ... rest of hook
   ```

3. **Deploy rollback:**
   - Set `AUTO_RESTORE_DEAL=false` environment variable
   - Or deploy previous version without the hook
   - Users revert to manual deal selection (previous behavior)

Rollback is **safe and immediate** — no database changes required.
