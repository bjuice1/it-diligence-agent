# Session Persistence - Quick Reference Guide

**For detailed documentation, see:** [SESSION-PERSISTENCE-IMPLEMENTATION.md](./SESSION-PERSISTENCE-IMPLEMENTATION.md)

---

## 🚨 Emergency Troubleshooting

### Issue: Users Losing Deal Selection

**Quick Checks (in order):**
```python
# 1. Check if user has last_deal_id
from web.database import User
user = User.query.filter_by(email='USER_EMAIL').first()
print(f"last_deal_id: {user.last_deal_id}")  # Should NOT be None

# 2. Check if hook is registered
from web.app import app
hooks = [h.__name__ for h in app.before_request_funcs.get(None, [])]
print('auto_restore_deal_context' in hooks)  # Should be True

# 3. Check session backend
print(f"Backend: {app.config.get('SESSION_TYPE')}")  # Should be 'redis' or 'sqlalchemy'

# 4. Test permission
from web.permissions import user_can_access_deal
from web.database import Deal
deal = Deal.query.get(user.last_deal_id)
print(user_can_access_deal(user, deal))  # Should be True
```

**Most Common Causes:**
1. ❌ User selected deal via old method (not API) → Fix: Use `POST /api/deals/<id>/select`
2. ❌ Deal was soft-deleted → Fix: User must select different deal
3. ❌ Session backend is filesystem (not persistent) → Fix: Configure Redis or PostgreSQL sessions
4. ❌ Hook not registered (import error) → Fix: Check app.py imports successfully

---

### Issue: High Database Load

**Quick Fix:**
```python
# Check if early exit is working (should be 99% of requests)
# Add to auto_restore_deal_context in web/app.py line 373:

if flask_session.get('current_deal_id'):
    logger.debug(f"[PERF] Early exit (warm session)")  # Should see this often
    return
```

**Check Indexes:**
```sql
-- PostgreSQL
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE indexname IN ('idx_users_last_deal', 'idx_flask_sessions_expiry');
```

**Expected:** idx_scan should increase over time (index is being used)

---

### Issue: Session Backend Unhealthy

**Quick Check:**
```bash
# Test health endpoint
curl http://localhost:5001/api/health/session | jq

# Expected:
# {"backend": "redis", "healthy": true, "details": {...}}
```

**If Redis unhealthy:**
```bash
# Check Redis is running
redis-cli ping  # Should return PONG

# Check connection
redis-cli -u $REDIS_URL ping

# Check app can connect
python3 -c "from web.app import check_redis_health; import os; print(check_redis_health(os.environ.get('REDIS_URL')))"
```

**If SQLAlchemy unhealthy:**
```sql
-- Check table exists
SELECT COUNT(*) FROM flask_sessions;

-- If table missing, run migration:
-- python3 -c "from web.database import db, create_all_tables; from web.app import app; create_all_tables(app)"
```

---

## 📍 Critical File Locations

| What | File | Lines | Quick Jump |
|------|------|-------|------------|
| **Auto-restore hook** | web/app.py | 353-397 | `@app.before_request auto_restore_deal_context()` |
| **Deal selection API** | web/app.py | 3957-4040 | `POST /api/deals/<deal_id>/select` |
| **Permission check** | web/permissions.py | 17-60 | `user_can_access_deal(user, deal)` |
| **User.get_last_deal()** | web/database.py | 453-468 | Method returns last deal if exists and not deleted |
| **User.update_last_deal()** | web/database.py | 442-451 | Sets last_deal_id and timestamp |
| **Session health endpoint** | web/app.py | 3858-3920 | `GET /api/health/session` |
| **Redis health check** | web/app.py | 106-122 | `check_redis_health(redis_url)` |

---

## 🔍 Debug Commands

### Check User's Deal Selection

```python
from web.database import User, Deal
from web.permissions import user_can_access_deal

# Get user
user = User.query.filter_by(email='user@example.com').first()

# Check database
print(f"User ID: {user.id}")
print(f"Last deal ID: {user.last_deal_id}")
print(f"Last accessed: {user.last_deal_accessed_at}")

# Check deal
if user.last_deal_id:
    deal = Deal.query.get(user.last_deal_id)
    print(f"Deal exists: {deal is not None}")
    print(f"Deal deleted: {deal.is_deleted if deal else 'N/A'}")
    print(f"Can access: {user_can_access_deal(user, deal) if deal else 'N/A'}")
    print(f"Deal owner: {deal.owner_id if deal else 'N/A'}")
    print(f"User owner: {user.id}")
```

### Check Session Data

```python
from flask import session as flask_session
from web.app import app

with app.test_request_context():
    with app.test_client() as client:
        # Simulate logged-in request
        with client.session_transaction() as sess:
            print(f"Session deal_id: {sess.get('current_deal_id')}")
            print(f"Session keys: {list(sess.keys())}")
```

### Check Logs for Auto-Restore

```bash
# Show auto-restore events
grep "Auto-restored deal" logs/*.log

# Show permission denials
grep "lost access to deal" logs/*.log

# Show restore failures
grep "Auto-restore deal context failed" logs/*.log
```

### Check Database Schema

```sql
-- PostgreSQL: Verify columns exist
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'users'
  AND column_name IN ('last_deal_id', 'last_deal_accessed_at');

-- SQLite: Verify columns exist
.schema users  -- Look for last_deal_id and last_deal_accessed_at

-- Check index
SELECT indexname FROM pg_indexes WHERE tablename = 'users';  -- PostgreSQL
.indexes users  -- SQLite
```

---

## 🎯 Common Fixes

### Fix 1: Re-enable Auto-Restore

**If disabled via environment variable:**
```bash
# Remove or set to true
export AUTO_RESTORE_ENABLED=true

# Restart app
```

### Fix 2: Migrate Database

**If columns missing:**
```python
from web.database import db, create_all_tables
from web.app import app

with app.app_context():
    create_all_tables(app)
    # Check logs for migration messages
```

### Fix 3: Clear Stale References

**If users have invalid last_deal_id:**
```python
from web.tasks.maintenance_tasks import cleanup_stale_deal_references

# Run cleanup
result = cleanup_stale_deal_references()
print(f"Cleared {result['users_updated']} stale references")
```

### Fix 4: Clean Up Old Sessions

**If flask_sessions table is huge:**
```python
from web.tasks.maintenance_tasks import cleanup_expired_sessions

# Remove sessions older than 7 days
result = cleanup_expired_sessions(cutoff_days=7)
print(f"Deleted {result['deleted']} sessions")
```

### Fix 5: Switch Session Backend

**From Filesystem to Redis:**
```bash
# Set environment variables
export USE_REDIS_SESSIONS=true
export REDIS_URL=redis://localhost:6379/0

# Restart app
# Check logs for: "✅ Session backend: Redis (healthy)"
```

**From Redis to SQLAlchemy (if Redis down):**
```bash
# Set environment variable
export USE_REDIS_SESSIONS=false

# Restart app
# Check logs for: "✅ Session backend: SQLAlchemy (PostgreSQL)"
```

---

## 📊 Health Check Commands

### Quick Health Check

```bash
# All-in-one health check
curl -s http://localhost:5001/api/health/session | jq '{backend: .backend, healthy: .healthy}'

# Expected: {"backend": "redis", "healthy": true}
```

### Detailed Health Check

```python
from web.tasks.maintenance_tasks import check_session_backend_health

status = check_session_backend_health()
print(f"Current backend: {status['current_backend']}")
print(f"Redis: {status['redis']}")
print(f"Database: {status['database']}")

if 'session_count' in status:
    print(f"Active sessions: {status['session_count']}")
```

### Database Connection Test

```python
from web.database import db
from web.app import app

with app.app_context():
    try:
        db.session.execute(db.text("SELECT 1"))
        print("✅ Database connection OK")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
```

### Redis Connection Test

```python
import os
import redis

redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

try:
    client = redis.from_url(redis_url, socket_connect_timeout=2)
    client.ping()
    print("✅ Redis connection OK")
except Exception as e:
    print(f"❌ Redis connection failed: {e}")
```

---

## 🔧 Configuration Quick Reference

### Environment Variables

```bash
# Session backend
USE_REDIS_SESSIONS=true              # Enable Redis sessions (default: false)
REDIS_URL=redis://localhost:6379/0   # Redis connection string

# Session behavior
PERMANENT_SESSION_LIFETIME=86400     # Session timeout in seconds (24 hours)

# Multi-tenancy
USE_MULTI_TENANCY=true               # Enable tenant-based access (default: false)

# Audit logging
USE_AUDIT_LOGGING=true               # Log deal selections (default: true)

# Database
DATABASE_URL=postgresql://...        # Database connection string
```

### Session Backend Priority

```
1. Redis (if USE_REDIS_SESSIONS=true AND health check passes)
   └─ Logs: "✅ Session backend: Redis (healthy)"

2. SQLAlchemy (if PostgreSQL available)
   └─ Logs: "✅ Session backend: SQLAlchemy (PostgreSQL)"

3. Filesystem/Cookie (fallback, NOT recommended for production)
   └─ Logs: "Using Flask built-in cookie sessions (local dev)"
```

---

## 📈 Performance Benchmarks

### Expected Latency

| Operation | p50 | p95 | p99 | Notes |
|-----------|-----|-----|-----|-------|
| Auto-restore (warm session) | <0.1ms | <0.2ms | <0.5ms | Early exit, no DB query |
| Auto-restore (cold session) | 2ms | 5ms | 10ms | 1-2 DB queries |
| Deal selection API | 5ms | 15ms | 30ms | Permission check + DB writes |
| Permission check | <1ms | 2ms | 5ms | In-memory or single query |
| get_last_deal() | 1ms | 3ms | 5ms | Single query with index |

### Query Counts

| Operation | Queries | Cacheable |
|-----------|---------|-----------|
| Auto-restore (early exit) | 0 | N/A |
| Auto-restore (cold, owner) | 1 | Yes (5min) |
| Auto-restore (cold, tenant) | 2 | Yes (5min) |
| Auto-restore (access denied) | 2-3 | No |
| Deal selection | 2-3 | No (writes) |

---

## 🧪 Testing Snippets

### Test Auto-Restore Manually

```python
from web.database import User, Deal, db
from web.app import app

with app.app_context():
    # 1. Create test data
    user = User.query.filter_by(email='test@example.com').first()
    deal = Deal.query.filter_by(owner_id=user.id).first()

    # 2. Set last_deal
    user.update_last_deal(deal.id)
    db.session.commit()

    # 3. Simulate session loss (clear cookies in browser)

    # 4. Make request (auto-restore should work)
    # Check logs for: "Auto-restored deal {deal.id} for user {user.id}"
```

### Test Permission Checks

```python
from web.permissions import user_can_access_deal
from web.database import User, Deal

# Owner check
owner = User.query.get('owner-id')
deal = Deal.query.get('deal-id')
assert user_can_access_deal(owner, deal) == True

# Non-owner check (multi-tenancy off)
other_user = User.query.get('other-user-id')
assert user_can_access_deal(other_user, deal) == False

# Deleted deal check
deal.soft_delete()
db.session.commit()
assert user_can_access_deal(owner, deal) == False
```

### Test Session Table

```sql
-- Insert test session
INSERT INTO flask_sessions (session_id, data, expiry)
VALUES ('test-123', E'\\x80\\x04\\x95...', NOW() + INTERVAL '1 day');

-- Query session
SELECT session_id, expiry FROM flask_sessions WHERE session_id = 'test-123';

-- Delete expired
DELETE FROM flask_sessions WHERE expiry < NOW();
```

---

## 🎬 Quick Start Guide

### For New Deployments

```bash
# 1. Set environment variables
export DATABASE_URL=postgresql://...
export USE_REDIS_SESSIONS=true
export REDIS_URL=redis://localhost:6379/0

# 2. Run migrations
python3 -c "from web.database import create_all_tables; from web.app import app; create_all_tables(app)"

# 3. Start app
python3 -m web.app

# 4. Verify
curl http://localhost:5001/api/health/session
# Should return: {"backend": "redis", "healthy": true}

# 5. Test deal selection
curl -X POST http://localhost:5001/api/deals/DEAL_ID/select \
  -H "Cookie: session=..." \
  -H "Content-Type: application/json"
```

### For Existing Deployments

```bash
# 1. Check current status
curl http://localhost:5001/api/health/session

# 2. Verify migrations ran
psql $DATABASE_URL -c "\d users" | grep last_deal

# 3. Check logs
tail -f logs/app.log | grep -E "(Session backend|Auto-restored|lost access)"

# 4. Monitor for 24 hours
watch -n 60 'curl -s http://localhost:5001/api/health/session | jq'
```

---

## 🔗 Related Documentation Links

- **Full Technical Docs:** [SESSION-PERSISTENCE-IMPLEMENTATION.md](./SESSION-PERSISTENCE-IMPLEMENTATION.md)
- **Spec 01 (Schema):** [../specs/session-persistence-fix/01-user-deal-association-schema.md](../specs/session-persistence-fix/01-user-deal-association-schema.md)
- **Spec 02 (API):** [../specs/session-persistence-fix/02-deal-selection-api.md](../specs/session-persistence-fix/02-deal-selection-api.md)
- **Spec 03 (Auto-Restore):** [../specs/session-persistence-fix/03-automatic-context-restoration.md](../specs/session-persistence-fix/03-automatic-context-restoration.md)
- **Spec 04 (Hardening):** [../specs/session-persistence-fix/04-session-architecture-hardening.md](../specs/session-persistence-fix/04-session-architecture-hardening.md)

---

## 📞 When to Escalate

**Escalate if:**
- Database migrations fail repeatedly
- Session backend always unhealthy (>10 minutes)
- Auto-restore causing >50ms latency consistently
- Permission checks failing for valid users
- Data corruption detected (last_deal_id pointing to wrong deals)

**Don't escalate if:**
- User never selected a deal (expected - they need to select one)
- Deal was deleted (expected - user needs to select different deal)
- Access was revoked (expected - user lost permission)
- Session backend is filesystem in dev (expected - local development)

---

**Last Updated:** 2026-02-09
**Quick Ref Version:** 1.0.0
**Status:** Production Ready
