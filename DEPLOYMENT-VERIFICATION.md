# Railway Deployment Verification Guide

## 🚀 Deployment Status

**Git Commit:** `667ac76`
**Pushed to:** `main` branch at https://github.com/bjuice1/it-diligence-agent.git
**Railway URL:** https://it-diligence-agent-production.up.railway.app

---

## ✅ Verification Steps

### Step 1: Check Railway Deployment Status

1. **Go to Railway Dashboard:**
   - Visit https://railway.app/dashboard
   - Find the `it-diligence-agent-production` project
   - Check deployment logs for the latest commit `667ac76`

2. **Expected Logs:**
   ```
   Building...
   Installing dependencies...
   Running migrations...
   ✅ Session backend: Redis (healthy)
   OR
   ✅ Session backend: SQLAlchemy (PostgreSQL)
   
   Index idx_users_last_deal ensured
   ✅ Created flask_sessions table (PostgreSQL)
   
   Server started successfully
   ```

3. **Wait for:** "Deployment successful" or "Service is live"

---

### Step 2: Verify Health Endpoint

**Test the session health endpoint:**

```bash
# Check session backend health
curl https://it-diligence-agent-production.up.railway.app/api/health/session

# Expected response:
{
  "backend": "redis",  # or "sqlalchemy"
  "healthy": true,
  "details": {
    "total_connections": ...,
    "connected_clients": ...,
    "used_memory_human": "..."
  }
}
```

**If response is 200 OK:** ✅ Deployment successful

**If response is 503 or error:** ⚠️ Session backend issue - check Railway logs

---

### Step 3: Verify Database Migrations

**Connect to Railway PostgreSQL:**

```bash
# Option 1: Via Railway CLI
railway connect

# Option 2: Direct connection (get DATABASE_URL from Railway env vars)
psql $DATABASE_URL
```

**Check migrations ran:**

```sql
-- Check User table has new columns
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'users' 
  AND column_name IN ('last_deal_id', 'last_deal_accessed_at');

-- Expected: 2 rows returned

-- Check flask_sessions table exists
SELECT COUNT(*) FROM flask_sessions;

-- Expected: Query succeeds (table exists)

-- Check index exists
SELECT indexname 
FROM pg_indexes 
WHERE tablename = 'users' 
  AND indexname = 'idx_users_last_deal';

-- Expected: 1 row returned
```

**All queries succeed:** ✅ Migrations completed

---

### Step 4: Test Deal Selection API

**Test the new API endpoints:**

```bash
# 1. Log in to get session cookie (use browser or curl)
# 2. List available deals

curl -X GET https://it-diligence-agent-production.up.railway.app/api/deals/list \
  -H "Cookie: session=YOUR_SESSION_COOKIE"

# Expected: {"success": true, "deals": [...], "total": N}

# 3. Select a deal

curl -X POST https://it-diligence-agent-production.up.railway.app/api/deals/DEAL_ID/select \
  -H "Cookie: session=YOUR_SESSION_COOKIE" \
  -H "Content-Type: application/json"

# Expected: {"success": true, "deal": {...}, "message": "Selected deal: ..."}
```

**If both succeed:** ✅ API endpoints working

---

### Step 5: Test Auto-Restore Functionality

**Manual test in browser:**

1. **Log in** to https://it-diligence-agent-production.up.railway.app
2. **Select a deal** (via UI or API)
3. **Open DevTools** → Application → Cookies
4. **Note the deal ID** (check network requests or UI state)
5. **Close browser completely**
6. **Reopen browser and log in again**
7. **Navigate to any page that requires a deal**

**Expected:** Deal is automatically selected (no "Please select a deal" error)

**Check Railway logs for:**
```
Auto-restored deal {DEAL_ID} for user {USER_ID} from database
```

**If auto-restore works:** ✅ Session persistence fully functional

---

### Step 6: Monitor for 1 Hour

**Watch Railway logs for:**

```bash
# In Railway dashboard, monitor live logs for:

# Good signs:
✅ Session backend: Redis (healthy)
Auto-restored deal ...
[PERF] Early exit (warm session)  # If you added debug logging

# Warning signs (investigate):
⚠️ Auto-restore deal context failed for user ...
⚠️ Redis sessions requested but health check failed
Session cleanup failed: ...

# Error signs (needs immediate attention):
❌ Database connection failed
❌ Migration failed
❌ Session backend unhealthy for >5 minutes
```

---

## 🔧 Troubleshooting Deployment Issues

### Issue: Migrations Not Running

**Check Railway logs for:**
```
Migration check failed (non-fatal): ...
```

**Fix:**
1. SSH into Railway container: `railway run bash`
2. Run migrations manually:
   ```python
   python3 -c "from web.database import create_all_tables; from web.app import app; create_all_tables(app)"
   ```
3. Check logs for success messages

---

### Issue: Session Backend Unhealthy

**Check Railway environment variables:**

```bash
# In Railway dashboard, verify:
USE_REDIS_SESSIONS=true  # If using Redis
REDIS_URL=redis://...    # Redis connection string
DATABASE_URL=postgresql://...  # PostgreSQL connection

# If REDIS_URL is set, test Redis:
railway run redis-cli -u $REDIS_URL ping
# Should return: PONG
```

**If Redis unavailable:**
- App will fall back to SQLAlchemy sessions automatically
- Check logs for: "✅ Session backend: SQLAlchemy (PostgreSQL)"

---

### Issue: Import Errors

**Common error:** `NameError: name '_create_session_table' is not defined`

**Already fixed in commit 667ac76** - function moved to correct location

**If still occurring:**
1. Check Railway is deploying latest commit
2. Restart deployment manually in Railway dashboard

---

### Issue: Permission Denied Errors

**If users can't select deals:**

**Check in Railway database:**
```sql
-- Verify user and deal exist
SELECT id, email FROM users WHERE email = 'user@example.com';
SELECT id, target_name, owner_id FROM deals WHERE id = 'deal-id';

-- Check ownership
SELECT d.id, d.owner_id, u.id as user_id
FROM deals d
CROSS JOIN users u
WHERE u.email = 'user@example.com'
  AND d.id = 'deal-id';

-- Expected: owner_id should match user_id
```

**Check logs for:**
```
User {user_id} attempted to access deal {deal_id} without permission
```

---

## 📊 Expected Performance Metrics

### After Successful Deployment

**API Response Times:**
- GET /api/deals/list: 50-200ms
- POST /api/deals/<id>/select: 50-300ms
- GET /api/health/session: 10-50ms

**Database Queries:**
- Auto-restore (warm session): 0 queries
- Auto-restore (cold session): 1-2 queries
- Deal selection: 2-3 queries

**Memory Usage:**
- Should remain stable (no memory leaks)
- Flask sessions in Redis: ~1-5MB typical
- SQLAlchemy sessions: Check table size

---

## 🎯 Success Criteria

✅ **Deployment successful when:**

1. Health endpoint returns 200 OK
2. Database migrations completed (verified via SQL)
3. API endpoints respond correctly
4. Auto-restore works (tested manually)
5. No errors in logs for 1 hour
6. Users report no "lost deal selection" issues

---

## 📞 If Issues Persist

### Emergency Rollback

**If deployment has critical issues:**

```bash
# 1. Revert to previous commit
git revert 667ac76
git push origin main

# 2. Railway will auto-deploy the revert

# 3. Or disable auto-restore via environment variable:
# In Railway dashboard:
AUTO_RESTORE_ENABLED=false

# 4. Restart service
```

### Get Help

**Include in report:**
1. Railway deployment logs (last 100 lines)
2. Database query results from Step 3
3. Health endpoint response
4. Error messages (exact text)
5. Environment variables (redact sensitive values)

**Check documentation:**
- docs/SESSION-PERSISTENCE-QUICKREF.md (emergency troubleshooting)
- docs/SESSION-PERSISTENCE-IMPLEMENTATION.md (detailed debugging)

---

## 📈 Post-Deployment Monitoring

### Set Up Alerts (Recommended)

**Monitor these endpoints:**
- https://it-diligence-agent-production.up.railway.app/api/health/session (every 5 min)

**Alert if:**
- Health endpoint returns 503 for >5 minutes
- Response time >5 seconds
- Error rate >5%

**Railway Logs to Watch:**
- "Auto-restore deal context failed" (occasional is OK, frequent is not)
- "Session backend unhealthy"
- Database connection errors

---

## ✅ Deployment Complete Checklist

- [ ] Railway deployment shows "success"
- [ ] Health endpoint returns 200 OK with healthy=true
- [ ] Database columns verified (last_deal_id, last_deal_accessed_at)
- [ ] flask_sessions table exists
- [ ] Index idx_users_last_deal exists
- [ ] API endpoints return expected responses
- [ ] Auto-restore tested and working
- [ ] No errors in logs for 1 hour
- [ ] Performance metrics within expected ranges

**When all checked:** 🎉 Session persistence fully deployed and operational!

---

**Deployment Date:** 2026-02-09
**Commit:** 667ac76
**Files Changed:** 7 (4,477 insertions, 106 deletions)
**Status:** ✅ Ready for verification
