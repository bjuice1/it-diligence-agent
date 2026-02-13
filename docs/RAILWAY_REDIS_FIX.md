# Railway Redis Fix Guide

## What Redis Does

Redis is used for two critical functions in the IT Diligence Agent:

1. **Celery Task Queue (Primary)** - Processes long-running analysis jobs in the background
   - Without Redis: Analysis blocks the web interface
   - With Redis: Analysis runs asynchronously, UI stays responsive

2. **Session Storage (Optional)** - Stores user sessions across multiple web workers
   - Without Redis: Sessions stored in files (doesn't scale)
   - With Redis: Sessions work across distributed deployments

## Problem

Your Railway Redis shows **"This is empty"** (no key-value pairs). This suggests:

1. Redis service is running but not connected to your app
2. `REDIS_URL` environment variable is not set on your app service
3. Celery workers may not be running
4. Background tasks cannot execute

## Impact

**Without Redis connected:**
- ❌ Analysis jobs run synchronously (blocks UI for 5-10 minutes)
- ❌ Cannot cancel or monitor running analysis
- ❌ No task progress updates
- ❌ Multi-worker deployments won't share sessions properly

**With Redis connected:**
- ✅ Analysis runs in background (UI responsive)
- ✅ Real-time progress updates
- ✅ Can cancel running tasks
- ✅ Scalable to multiple workers

## Solution: 4-Step Fix

### Step 1: Set REDIS_URL Environment Variable

1. **Open your Railway project dashboard**

2. **Find the Redis service** (should show Redis icon, status "Online")
   - Click on it
   - Go to the **"Variables"** tab
   - Find `REDIS_URL` (or `REDIS_TLS_URL`)
   - Copy the full URL
   - It should look like: `redis://default:password@host:6379`
   - Or for TLS: `rediss://default:password@host:6379` (note the double 's')

3. **Go to your app service** (the one running `web.app:app`)
   - Click on it
   - Go to the **"Variables"** tab
   - Click **"New Variable"**
   - Name: `REDIS_URL`
   - Value: Paste the copied Redis URL
   - Click **"Add"**

4. **Optional: Enable Redis sessions** (recommended for production)
   - Add another variable:
   - Name: `USE_REDIS_SESSIONS`
   - Value: `true`
   - Click **"Add"**

### Step 2: Verify Connection

After setting `REDIS_URL`, Railway will redeploy your app. Test the connection:

**Option A: Using Railway CLI**

```bash
railway run python scripts/diagnose_railway_redis.py
```

**Option B: Using Railway Dashboard**

1. Go to your app service
2. Click **"Deployments"** → Latest deployment → Three dots (•••)
3. Select **"Run One-Off Command"**
4. Enter: `python scripts/diagnose_railway_redis.py`
5. Click **"Run"**

**Expected output:**
```
✓ REDIS_URL set
✓ Redis connection successful
  Redis version: 7.x.x
  Connected clients: 1
  Total keys: 0
✓ Celery app initialized
✓ Celery broker (Redis) is available
✓ Can write and read from Redis
```

### Step 3: Start Celery Worker (REQUIRED)

Redis is just the message broker - you also need a **Celery worker** to process tasks.

**Check if you have a worker service:**

1. In Railway dashboard, look for a service named "worker" or similar
2. If you see one, check if it's running (should show "Online")

**If you DON'T have a worker service, create one:**

#### Option A: Using railway.toml (Recommended)

Your `railway.toml` already has a worker service defined (lines 18-19):

```toml
[[services]]
name = "worker"
command = "celery -A web.celery_app worker --loglevel=info --concurrency=4"
```

But Railway might not be using it. To fix:

1. In Railway dashboard, click **"New Service"**
2. Select **"Deploy from GitHub"**
3. Choose your repo and branch
4. In the settings, set:
   - **Service Name:** worker
   - **Start Command:** `celery -A web.celery_app worker --loglevel=info --concurrency=2`
   - **Environment Variables:** Add `REDIS_URL` (same value as app service)

#### Option B: Using Procfile

If Railway is using `Procfile`, it should automatically create both web and worker services.

Check that your `Procfile` has:
```
web: gunicorn -w 4 -b 0.0.0.0:${PORT:-8080} --timeout 300 --log-level info web.app:app
worker: celery -A web.celery_app worker --loglevel=info --concurrency=4
```

### Step 4: Test Background Tasks

1. **Restart both services:**
   - Restart app service
   - Restart worker service (if separate)

2. **Open your Railway app URL**

3. **Create a test deal and upload documents**

4. **Click "Run Analysis"**

5. **You should see:**
   - ✅ Analysis starts immediately
   - ✅ Progress bar updates in real-time
   - ✅ UI remains responsive (can navigate away)
   - ✅ Can see task status on dashboard

6. **Check Redis has data:**
   - Go to Railway → Redis service → Database tab
   - Should now see keys like:
     - `celery-task-meta-<uuid>` (task results)
     - `_kombu.binding.*` (Celery queues)
     - `session:*` (if using Redis sessions)

## Verification Checklist

- [ ] `REDIS_URL` environment variable is set on app service
- [ ] Redis connection test passes
- [ ] Celery worker service exists and is "Online"
- [ ] Worker service has `REDIS_URL` environment variable
- [ ] Redis shows keys after running analysis
- [ ] Analysis runs in background (UI doesn't freeze)
- [ ] Progress updates appear in real-time

## Troubleshooting

### Problem: REDIS_URL set but connection fails

**Check URL format:**
```bash
# Correct formats:
redis://default:password@host:6379
rediss://default:password@host:6379  # TLS (secure)

# Common mistakes:
redis:// without host
Missing port :6379
Wrong password
```

**Test connection manually:**
```bash
railway run python -c "
import redis
import os
r = redis.from_url(os.environ['REDIS_URL'])
r.ping()
print('✓ Redis connected')
"
```

### Problem: Connection timeout or refused

**Causes:**
- Redis service is stopped (check Railway dashboard)
- Wrong host/port in REDIS_URL
- Network issues (rare on Railway)

**Solution:**
- Verify Redis service shows "Online" status
- Check Redis logs for errors
- Try restarting Redis service

### Problem: TLS/SSL errors with rediss://

**Error:** `ssl.SSLError: [SSL: CERTIFICATE_VERIFY_FAILED]`

**Solution:** Use TLS but skip certificate verification:

```python
import redis
r = redis.from_url(redis_url, ssl_cert_reqs=None)
```

The app already handles this - make sure you're using the latest code.

### Problem: No Celery workers found

**Symptoms:**
- Tasks stay in "pending" status forever
- Analysis never completes
- No progress updates

**Diagnosis:**
```bash
railway run python -c "
from web.celery_app import celery
inspect = celery.control.inspect()
stats = inspect.stats()
if stats:
    print(f'✓ Found {len(stats)} worker(s)')
    for name in stats.keys():
        print(f'  - {name}')
else:
    print('✗ No workers found!')
"
```

**Solution:** Start a worker service (see Step 3 above)

### Problem: Worker crashes or restarts constantly

**Check worker logs in Railway:**
- Go to worker service → "Logs" tab
- Look for errors

**Common causes:**
- Missing environment variables (ANTHROPIC_API_KEY, DATABASE_URL, REDIS_URL)
- Out of memory (increase worker memory limit)
- Import errors (missing dependencies)

**Fix worker memory issues:**
```bash
# In worker start command, reduce concurrency:
celery -A web.celery_app worker --loglevel=info --concurrency=1

# Or set memory limit:
celery -A web.celery_app worker --loglevel=info --max-memory-per-child=500000
```

### Problem: Tasks complete but results not saved

**Cause:** Celery backend not configured

**Check:**
```bash
railway run python -c "
from web.celery_app import celery
print(f'Backend: {celery.conf.result_backend}')
"
```

Should output: `Backend: redis://...`

If it shows `Backend: None`, the worker doesn't have REDIS_URL set.

### Problem: Redis fills up and runs out of memory

**Symptoms:**
- `OOM` errors in Redis logs
- Tasks fail with "Redis out of memory"

**Solutions:**

1. **Clean up old task results:**
```bash
railway run python -c "
from web.celery_app import celery
celery.backend.cleanup()
print('✓ Cleaned up old task results')
"
```

2. **Set expiration on keys:**
The app already expires task results after 24 hours (see `celery_app.py:33`)

3. **Increase Redis memory limit:**
   - Railway Redis has memory limits by plan
   - Upgrade Redis service if needed

4. **Enable Redis eviction policy:**
   In Railway Redis settings, set:
   - Eviction policy: `allkeys-lru` (removes least recently used keys)

## Architecture Overview

```
┌─────────────┐
│   Browser   │
│  (Railway   │
│   App URL)  │
└──────┬──────┘
       │ HTTP
       ↓
┌─────────────────────────────────┐
│   Flask Web Service (Gunicorn)  │
│   - Handles HTTP requests        │
│   - Queues tasks to Redis        │
│   - Returns immediately          │
└──────┬──────────────────────────┘
       │ Task Queue
       ↓
┌─────────────────────────────────┐
│         Redis Service            │
│   - Task queue (Celery broker)   │
│   - Task results (backend)       │
│   - Session storage              │
└──────┬──────────────────────────┘
       │ Worker pulls tasks
       ↓
┌─────────────────────────────────┐
│   Celery Worker Service          │
│   - Processes analysis jobs      │
│   - Calls Anthropic API          │
│   - Writes to PostgreSQL         │
│   - Stores results in Redis      │
└──────┬──────────────────────────┘
       │ Updates task status
       ↓
┌─────────────────────────────────┐
│     PostgreSQL Service           │
│   - Stores facts, findings       │
│   - Stores deals, documents      │
└─────────────────────────────────┘
```

## Best Practices

1. **Always run at least one worker** - Without workers, tasks queue up but never execute

2. **Monitor worker health** - Check Railway logs regularly for worker errors

3. **Set environment variables on ALL services:**
   - App service: `REDIS_URL`, `DATABASE_URL`, `ANTHROPIC_API_KEY`
   - Worker service: `REDIS_URL`, `DATABASE_URL`, `ANTHROPIC_API_KEY`

4. **Use Redis for sessions** - Set `USE_REDIS_SESSIONS=true` for production

5. **Tune worker concurrency** - Start with `--concurrency=2`, increase if workers have memory

6. **Clean up old tasks** - The app has automatic cleanup (every hour)

## Additional Resources

- Railway Redis docs: https://docs.railway.app/databases/redis
- Celery docs: https://docs.celeryproject.org/
- Our Celery config: `web/celery_app.py`
- Task definitions: `web/tasks/`
