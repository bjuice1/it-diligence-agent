# 04 — Session Architecture Hardening

## Status: NOT STARTED
## Priority: MEDIUM (Infrastructure reliability)
## Depends On: Nothing (can be implemented in parallel with Spec 01)
## Enables: Multi-server deployment, production reliability

---

## Overview

The application currently has fallback session backends (Redis → SQLAlchemy → filesystem) but lacks robust configuration, monitoring, and cache-aside patterns needed for production multi-server deployments.

**The problem:**
- Session backend failures cause user logouts
- No visibility into which backend is active
- No automatic failover testing
- Cache invalidation issues in multi-server setups
- Session store (in-memory) doesn't work across servers

**The fix:** Harden session architecture with:
1. Explicit Redis configuration with health checks
2. SQLAlchemy session table with proper indexes
3. Cache-aside pattern for session-critical data
4. Monitoring and alerting for session backend health
5. Graceful degradation when backends fail

This spec is **independent** of Specs 01-03 (database schema and API changes) but complements them by ensuring session reliability.

---

## Architecture

### Current Session Backend Logic (web/app.py lines 86-150)

```python
# Priority: Redis > SQLAlchemy > Filesystem
if redis_url:
    app.config['SESSION_TYPE'] = 'redis'
elif db_configured:
    app.config['SESSION_TYPE'] = 'sqlalchemy'
else:
    app.config['SESSION_TYPE'] = 'filesystem'
```

**Problems:**
- No health check before choosing Redis
- No fallback if Redis fails after startup
- SQLAlchemy session table not explicitly created
- Filesystem sessions don't work in multi-server (each server has separate FS)

### Proposed Architecture

```
Session Data Flow:
  1. User logs in → Flask-Session writes to Redis (primary)
  2. Redis write fails → Circuit breaker trips → Fall back to SQLAlchemy
  3. SQLAlchemy write fails → Fall back to signed cookie (temporary)
  4. Critical data (current_deal_id) ALSO written to database (Spec 01)
  5. On read: Try Redis → SQLAlchemy → Database (Spec 03 auto-restore)

Cache-Aside Pattern for current_deal_id:
  Write path:
    1. Write to flask_session (Redis/SQLAlchemy)
    2. Write to User.last_deal_id (database) — Spec 02
    3. Write to Redis cache with 5min TTL (optional)

  Read path:
    1. Check flask_session (fast, but may be stale)
    2. If empty, check User.last_deal_id (database) — Spec 03
    3. Restore to flask_session
```

**Benefits:**
- Defense-in-depth: Multiple persistence layers
- Automatic failover: Circuit breaker handles backend failures
- Multi-server safe: Database is source of truth
- Performance: Redis cache + database fallback

---

## Specification

### Change 1: Redis Health Check and Configuration

**Location:** `web/app.py` around line 100

**Add Redis health check before configuring:**

```python
def check_redis_health(redis_url: str, timeout: int = 2) -> bool:
    """
    Check if Redis is healthy before using it for sessions.

    Args:
        redis_url: Redis connection URL
        timeout: Connection timeout in seconds

    Returns:
        True if Redis is reachable and responsive, False otherwise
    """
    try:
        import redis
        client = redis.from_url(redis_url, socket_connect_timeout=timeout)
        client.ping()
        return True
    except Exception as e:
        logger.warning(f"Redis health check failed: {e}")
        return False


# In session configuration (replace lines 86-110)
redis_url = os.environ.get('REDIS_URL') or os.environ.get('REDIS_TLS_URL')

if redis_url and check_redis_health(redis_url):
    app.config['SESSION_TYPE'] = 'redis'
    app.config['SESSION_REDIS'] = redis.from_url(
        redis_url,
        socket_connect_timeout=2,
        socket_timeout=2,
        retry_on_timeout=True,
        health_check_interval=30  # Check every 30 seconds
    )
    app.config['SESSION_PERMANENT'] = True
    app.config['SESSION_USE_SIGNER'] = True
    app.config['SESSION_KEY_PREFIX'] = 'itdd:session:'
    logger.info("Session backend: Redis (healthy)")

elif db_configured:
    # Fallback to SQLAlchemy-backed sessions
    app.config['SESSION_TYPE'] = 'sqlalchemy'
    app.config['SESSION_SQLALCHEMY'] = db
    app.config['SESSION_SQLALCHEMY_TABLE'] = 'flask_sessions'
    app.config['SESSION_PERMANENT'] = True
    app.config['SESSION_USE_SIGNER'] = True
    logger.warning("Session backend: SQLAlchemy (Redis unavailable)")

else:
    # Emergency fallback: signed cookies (not suitable for production)
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_FILE_DIR'] = os.path.join(tempfile.gettempdir(), 'flask_sessions')
    app.config['SESSION_PERMANENT'] = False
    logger.error("Session backend: Filesystem (INSECURE - set REDIS_URL or DATABASE_URL)")
```

**Key improvements:**
- Health check before choosing Redis
- Explicit Redis client config (timeouts, retries)
- Key prefix to namespace sessions
- Logging shows active backend
- Emergency fallback to filesystem (with warning)

---

### Change 2: Create SQLAlchemy Session Table

**Problem:** SQLAlchemy session backend requires a table, but it's not created in migrations.

**Location:** `web/database.py` in the `_run_migrations()` function

**Add migration for session table:**

```python
# Migration 5: Create flask_sessions table for SQLAlchemy session backend
def _create_session_table():
    """Create flask_sessions table if it doesn't exist."""
    try:
        dialect = db.engine.dialect.name

        # Check if table exists
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        if 'flask_sessions' in inspector.get_table_names():
            logger.info("flask_sessions table already exists")
            return

        # Create table based on Flask-Session schema
        if dialect == 'postgresql':
            db.session.execute(db.text("""
                CREATE TABLE flask_sessions (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(255) UNIQUE NOT NULL,
                    data BYTEA,
                    expiry TIMESTAMP
                );
                CREATE INDEX idx_flask_sessions_expiry ON flask_sessions(expiry);
            """))
        elif dialect == 'sqlite':
            db.session.execute(db.text("""
                CREATE TABLE flask_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id VARCHAR(255) UNIQUE NOT NULL,
                    data BLOB,
                    expiry TIMESTAMP
                );
                CREATE INDEX idx_flask_sessions_expiry ON flask_sessions(expiry);
            """))

        db.session.commit()
        logger.info("Created flask_sessions table")

    except Exception as e:
        logger.warning(f"Failed to create flask_sessions table: {e}")
        db.session.rollback()

# Call in _run_migrations() after existing migrations
_create_session_table()
```

**Why this helps:**
- SQLAlchemy session backend works out-of-box
- Index on expiry for efficient cleanup
- Survives server restarts (unlike filesystem)
- Works in multi-server (shared database)

---

### Change 3: Session Cleanup Job

**Problem:** Old sessions accumulate in database/Redis, wasting storage.

**Solution:** Periodic cleanup task (Celery or manual)

**Location:** `web/tasks/` (new file: `maintenance_tasks.py`)

```python
"""
Maintenance Tasks - Background cleanup and health checks
"""

import logging
from datetime import datetime, timedelta
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name='web.tasks.cleanup_expired_sessions')
def cleanup_expired_sessions():
    """
    Remove expired sessions from database.

    Run this periodically (e.g., daily at 3am) via cron or Celery beat.
    Only needed if using SQLAlchemy session backend.
    """
    from web.database import db

    try:
        # Delete sessions older than PERMANENT_SESSION_LIFETIME
        cutoff = datetime.utcnow() - timedelta(days=7)  # Adjust based on config

        result = db.session.execute(db.text("""
            DELETE FROM flask_sessions
            WHERE expiry < :cutoff
        """), {'cutoff': cutoff})

        db.session.commit()
        deleted = result.rowcount

        logger.info(f"Cleaned up {deleted} expired sessions")
        return {'deleted': deleted, 'cutoff': cutoff.isoformat()}

    except Exception as e:
        logger.error(f"Session cleanup failed: {e}")
        db.session.rollback()
        raise


@shared_task(name='web.tasks.check_session_backend_health')
def check_session_backend_health():
    """
    Health check for session backend.

    Returns status of Redis/SQLAlchemy and switches backends if needed.
    """
    from web.app import app
    import redis

    results = {
        'redis': 'unknown',
        'database': 'unknown',
        'current_backend': app.config.get('SESSION_TYPE')
    }

    # Check Redis
    redis_url = os.environ.get('REDIS_URL') or os.environ.get('REDIS_TLS_URL')
    if redis_url:
        try:
            client = redis.from_url(redis_url, socket_connect_timeout=2)
            client.ping()
            results['redis'] = 'healthy'
        except Exception as e:
            results['redis'] = f'unhealthy: {e}'

    # Check Database
    try:
        from web.database import db
        db.session.execute(db.text("SELECT 1"))
        results['database'] = 'healthy'
    except Exception as e:
        results['database'] = f'unhealthy: {e}'

    return results
```

**Cron setup (optional):**
```bash
# In Railway/Heroku, add to scheduler:
# Daily at 3am UTC
0 3 * * * python -c "from web.tasks.maintenance_tasks import cleanup_expired_sessions; cleanup_expired_sessions()"
```

---

### Change 4: Cache-Aside Pattern for current_deal_id (Optional)

**Purpose:** Reduce database queries for frequently-accessed data.

**Implementation:** Add Redis cache layer for `current_deal_id`

**Location:** `web/app.py` in the `auto_restore_deal_context` hook (Spec 03)

```python
# In auto_restore_deal_context hook
def auto_restore_deal_context():
    # ... existing authentication check ...

    # Try Redis cache first (if available)
    cache_key = f"user:{current_user.id}:last_deal_id"
    cached_deal_id = None

    if app.config['SESSION_TYPE'] == 'redis':
        try:
            redis_client = app.config['SESSION_REDIS']
            cached_deal_id = redis_client.get(cache_key)
            if cached_deal_id:
                cached_deal_id = cached_deal_id.decode('utf-8')
        except Exception:
            pass  # Cache miss, fall through to database

    if cached_deal_id:
        # Fast path: restore from cache
        flask_session['current_deal_id'] = cached_deal_id
        flask_session.modified = True
        return

    # Slow path: restore from database (existing Spec 03 logic)
    last_deal = current_user.get_last_deal()
    if last_deal:
        flask_session['current_deal_id'] = last_deal.id
        flask_session.modified = True

        # Write back to cache (5 minute TTL)
        if app.config['SESSION_TYPE'] == 'redis':
            try:
                redis_client.setex(cache_key, 300, last_deal.id)  # 5 min TTL
            except Exception:
                pass  # Non-fatal
```

**This is OPTIONAL** for Spec 04. It's a performance optimization, not required for correctness.

---

### Change 5: Monitoring and Observability

**Add metrics to track session backend health:**

**Location:** `web/app.py` (new utility function)

```python
def get_session_backend_status() -> dict:
    """
    Get current session backend status for health checks.

    Returns:
        dict with backend type, health, and metrics
    """
    backend = app.config.get('SESSION_TYPE', 'unknown')
    status = {
        'backend': backend,
        'healthy': False,
        'details': {}
    }

    if backend == 'redis':
        try:
            redis_client = app.config.get('SESSION_REDIS')
            info = redis_client.info('stats')
            status['healthy'] = True
            status['details'] = {
                'total_connections': info.get('total_connections_received'),
                'connected_clients': info.get('connected_clients'),
                'used_memory': info.get('used_memory_human'),
            }
        except Exception as e:
            status['healthy'] = False
            status['details'] = {'error': str(e)}

    elif backend == 'sqlalchemy':
        try:
            from web.database import db
            result = db.session.execute(db.text(
                "SELECT COUNT(*) FROM flask_sessions"
            )).scalar()
            status['healthy'] = True
            status['details'] = {'active_sessions': result}
        except Exception as e:
            status['healthy'] = False
            status['details'] = {'error': str(e)}

    return status


# Add health check endpoint
@app.route('/api/health/session')
def session_health():
    """Health check endpoint for session backend."""
    status = get_session_backend_status()
    return jsonify(status), 200 if status['healthy'] else 503
```

**Railway/Heroku health check:**
```yaml
# railway.toml or Procfile
healthcheck:
  path: /api/health/session
  interval: 60
  timeout: 10
```

---

### Change 6: Circuit Breaker Pattern (Advanced)

**Purpose:** Automatically fail over when Redis is degraded.

**Implementation:** Use pybreaker library

```python
# Install: pip install pybreaker
from pybreaker import CircuitBreaker

# Configure circuit breaker for Redis
redis_breaker = CircuitBreaker(
    fail_max=5,           # Open after 5 failures
    timeout_duration=60,  # Try again after 60 seconds
    name='redis_session'
)

@redis_breaker
def write_to_redis_session(key, value):
    """Write to Redis with circuit breaker protection."""
    redis_client = app.config['SESSION_REDIS']
    return redis_client.set(key, value)

# When circuit opens, fall back to SQLAlchemy
try:
    write_to_redis_session(session_key, session_data)
except CircuitBreakerError:
    logger.warning("Redis circuit open, falling back to SQLAlchemy")
    # Write to database instead
```

**This is ADVANCED** and not required for Spec 04. Include only if needed.

---

## Benefits

1. **Multi-server compatibility** — SQLAlchemy sessions work across load-balanced servers
2. **Automatic failover** — Health checks ensure reliable backend selection
3. **Observability** — Health endpoints and logging expose session status
4. **Performance** — Redis primary + cache-aside pattern for speed
5. **Data durability** — Database fallback prevents session loss

---

## Expectations

After this spec is implemented:

1. Redis health check runs before selecting session backend
2. SQLAlchemy session table exists and is indexed
3. Session cleanup task removes expired sessions
4. Health check endpoint reports session backend status
5. Logs clearly show which backend is active
6. Application works in multi-server deployment

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Redis health check false negative (healthy Redis marked unhealthy) | Low | Medium | Use short timeout (2s) and retry logic. Log health check results. |
| SQLAlchemy session table creation fails in production | Low | High | Test migration on staging first. Include rollback SQL. Non-fatal error handling. |
| Session cleanup task deletes active sessions | Low | High | Use conservative cutoff (7 days > PERMANENT_SESSION_LIFETIME). Test on staging. |
| Cache-aside pattern creates stale data | Medium | Low | Use short TTL (5 min). Database is source of truth (Spec 01). |
| Circuit breaker trips unnecessarily | Low | Medium | Tune fail_max and timeout_duration based on monitoring. |
| Multi-server sessions cause race conditions | Low | Low | Flask-Session handles locking. Database transactions are ACID. |

---

## Results Criteria

### Automated Tests

**Test 1: Redis health check**
```python
def test_redis_health_check_success(monkeypatch):
    """Verify health check returns True for healthy Redis."""
    redis_url = "redis://localhost:6379/0"

    # Mock Redis client
    class MockRedis:
        def ping(self):
            return True

    monkeypatch.setattr('redis.from_url', lambda url, **kwargs: MockRedis())

    from web.app import check_redis_health
    assert check_redis_health(redis_url) is True
```

**Test 2: Session backend fallback**
```python
def test_session_backend_falls_back_to_sqlalchemy(monkeypatch):
    """Verify SQLAlchemy backend used when Redis fails health check."""
    # Mock failed Redis health check
    monkeypatch.setattr('web.app.check_redis_health', lambda url: False)

    # Configure app
    from web.app import app
    assert app.config['SESSION_TYPE'] == 'sqlalchemy'
```

**Test 3: Session table exists**
```python
def test_flask_sessions_table_created():
    """Verify migration creates flask_sessions table."""
    from sqlalchemy import inspect
    from web.database import db

    inspector = inspect(db.engine)
    tables = inspector.get_table_names()

    assert 'flask_sessions' in tables

    # Verify index exists
    indexes = inspector.get_indexes('flask_sessions')
    index_names = [idx['name'] for idx in indexes]
    assert 'idx_flask_sessions_expiry' in index_names
```

**Test 4: Session cleanup removes old sessions**
```python
def test_cleanup_expired_sessions():
    """Verify cleanup task removes expired sessions."""
    from web.database import db
    from datetime import datetime, timedelta

    # Insert old session
    old_expiry = datetime.utcnow() - timedelta(days=10)
    db.session.execute(db.text("""
        INSERT INTO flask_sessions (session_id, data, expiry)
        VALUES (:sid, :data, :expiry)
    """), {'sid': 'old-session', 'data': b'data', 'expiry': old_expiry})
    db.session.commit()

    # Run cleanup
    from web.tasks.maintenance_tasks import cleanup_expired_sessions
    result = cleanup_expired_sessions()

    # Verify old session deleted
    count = db.session.execute(db.text(
        "SELECT COUNT(*) FROM flask_sessions WHERE session_id = 'old-session'"
    )).scalar()
    assert count == 0
    assert result['deleted'] >= 1
```

**Test 5: Health endpoint returns status**
```python
def test_session_health_endpoint(client):
    """Verify health endpoint returns session backend status."""
    response = client.get('/api/health/session')

    assert response.status_code in [200, 503]
    data = response.get_json()

    assert 'backend' in data
    assert data['backend'] in ['redis', 'sqlalchemy', 'filesystem']
    assert 'healthy' in data
```

### Manual Verification

1. **Redis health check:**
   - Stop Redis: `redis-cli shutdown`
   - Restart app
   - Verify logs show "Session backend: SQLAlchemy (Redis unavailable)"
   - Restart Redis
   - Verify logs show "Session backend: Redis (healthy)" on next app restart

2. **Multi-server session:**
   - Deploy to Railway with 2+ instances
   - Log in on server A
   - Force next request to server B
   - Verify session persists (no re-login required)

3. **Session cleanup:**
   - Insert 100 expired sessions into database
   - Run cleanup task
   - Verify all expired sessions deleted
   - Verify active sessions remain

4. **Health endpoint:**
   - Call `/api/health/session`
   - Verify returns 200 with Redis/SQLAlchemy status
   - Stop Redis
   - Verify returns 503 or shows unhealthy

---

## Files Modified

| File | Change |
|------|--------|
| `web/app.py` | Add `check_redis_health()` (lines ~95). Update session config (lines 100-135). Add health endpoint (lines ~800). |
| `web/database.py` | Add `_create_session_table()` migration (lines ~1480). |
| `web/tasks/maintenance_tasks.py` | **NEW FILE** - Session cleanup and health check tasks (~100 lines). |
| `requirements.txt` | Add `pybreaker` (optional, only if using circuit breaker). |

**Lines of code:** ~150 lines (health checks + migration + maintenance tasks + health endpoint)

---

## Dependencies

**External:**
- Requires Redis (optional, for primary session backend)
- Requires Flask-Session (already present)
- Requires SQLAlchemy (already present)
- Optional: pybreaker for circuit breaker pattern

**Internal:**
- Uses existing database connection (web/database.py)
- Complements Spec 03 auto-restore hook (cache-aside pattern)
- Independent of Specs 01-02 (can be implemented in parallel)

**Enables:**
- Production-ready multi-server deployment
- Reliable session persistence
- Operational visibility into session health

---

## Implementation Order

This spec is **independent** and can be done in parallel with Spec 01. However, the recommended order within this spec is:

1. **First:** Session table migration (Change 2) — Required for SQLAlchemy backend
2. **Second:** Redis health check (Change 1) — Ensures reliable backend selection
3. **Third:** Health endpoint (Change 5) — Enables monitoring
4. **Fourth:** Cleanup task (Change 3) — Operational hygiene
5. **Optional:** Cache-aside pattern (Change 4) — Performance optimization
6. **Optional:** Circuit breaker (Change 6) — Advanced resilience

---

## Production Checklist

Before deploying to production:

- [ ] REDIS_URL environment variable set (Railway/Heroku)
- [ ] Redis health check logs show "Session backend: Redis (healthy)"
- [ ] `flask_sessions` table created in database
- [ ] Session cleanup task scheduled (daily cron)
- [ ] Health endpoint `/api/health/session` returns 200
- [ ] Load balancer configured to use health endpoint
- [ ] PERMANENT_SESSION_LIFETIME configured (default: 7 days)
- [ ] SESSION_COOKIE_SECURE = True in production (HTTPS only)
- [ ] Monitoring alerts set up for session backend failures

---

## Future Enhancements

1. **Session analytics:** Track session duration, user activity patterns
2. **Multi-region Redis:** Replicate sessions across regions for global apps
3. **Session compression:** Compress session data to reduce Redis memory
4. **Audit trail:** Log all session creations/deletions for security
5. **Graceful session migration:** Migrate sessions when upgrading backends

---

## Success Metrics

After deployment:

1. **Zero session-related user logouts** (excluding intentional logout/timeout)
2. **Session backend health check passes 99.9%+** of the time
3. **Multi-server deployments work without session loss**
4. **Redis/SQLAlchemy failover happens automatically** when backends degrade
5. **Session cleanup task runs successfully** every night

Target: 99.99% session persistence (only lose sessions on catastrophic DB+Redis failure).

---

## Rollback Plan

If session hardening causes issues:

1. **Remove health check:** Comment out `check_redis_health()` — app will attempt Redis without checking
2. **Drop session table:** `DROP TABLE flask_sessions;` — fall back to filesystem/cookie
3. **Disable cleanup task:** Stop cron job — sessions accumulate but app works
4. **Revert config:** Deploy previous version of `web/app.py`

All changes are **backward compatible** — removing them reverts to previous behavior.
