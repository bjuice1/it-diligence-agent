# Railway Database Fix - Action Plan (PostgreSQL + Redis)

## What I Just Created

### 1. PostgreSQL Diagnostic: `scripts/diagnose_railway_db.py`
**Purpose:** Check database connection and table status on Railway

**Run it to:**
- Verify DATABASE_URL is set
- Test PostgreSQL connection
- List existing tables
- Check for missing required tables
- Test read/write permissions

**Usage:**
```bash
railway run python scripts/diagnose_railway_db.py
```

### 2. Initialization Script: `scripts/railway_init_db.sh`
**Purpose:** Robust database setup for Railway with error handling

**What it does:**
- Validates DATABASE_URL exists
- Tests connection before proceeding
- Runs init_db.py to create all tables
- Creates default admin user
- Provides clear success/failure messages

**Usage:**
```bash
railway run bash scripts/railway_init_db.sh
```

### 3. PostgreSQL Fix Guide: `docs/RAILWAY_DATABASE_FIX.md`
**Purpose:** Step-by-step instructions for fixing PostgreSQL

**Covers:**
- Root cause explanation
- 3-step fix procedure
- Verification checklist
- Troubleshooting common issues
- Prevention recommendations

### 4. Redis Diagnostic: `scripts/diagnose_railway_redis.py`
**Purpose:** Check Redis connection and Celery workers

**Run it to:**
- Verify REDIS_URL is set
- Test Redis connection
- Check Celery worker status
- Test read/write operations

**Usage:**
```bash
railway run python scripts/diagnose_railway_redis.py
```

### 5. Redis Fix Guide: `docs/RAILWAY_REDIS_FIX.md`
**Purpose:** Complete Redis and Celery setup guide

**Covers:**
- What Redis does (task queue + sessions)
- How to connect Redis to your app
- How to start Celery workers
- Architecture overview
- Troubleshooting worker issues

---

## Immediate Action Steps (Do This Now)

### PART A: PostgreSQL Setup (Required - 10 minutes)

#### Step 1: Check if DATABASE_URL is set on Railway (2 minutes)

1. Go to https://railway.app/dashboard
2. Open your IT Diligence Agent project
3. Click on your **app service** (not PostgreSQL)
4. Go to **"Variables"** tab
5. Look for `DATABASE_URL`

**If you see it:** Great! Skip to Step 2
**If you DON'T see it:** This is the problem! Continue below:

   a. Click on your **PostgreSQL service**
   b. Go to **"Variables"** tab
   c. Copy the `DATABASE_URL` value (full connection string)
   d. Go back to your **app service**
   e. Click **"New Variable"**
   f. Name: `DATABASE_URL`
   g. Value: Paste the copied URL
   h. Click **"Add"**
   i. Railway will redeploy automatically

### Step 2: Run Database Initialization (5 minutes)

**Option A: Using Railway Dashboard (Recommended)**

1. Go to your app service
2. Click **"Deployments"** tab
3. Find the most recent deployment
4. Click the three dots (•••) → **"Run One-Off Command"**
5. Enter: `python scripts/init_db.py`
6. Click **"Run"**
7. Watch the logs for success message

**Option B: Using Railway CLI**

```bash
# Install CLI if you don't have it
npm install -g @railway/cli

# Link to your project
railway link

# Run initialization
railway run python scripts/init_db.py
```

### Step 3: Verify Tables Exist (1 minute)

1. In Railway dashboard, click on **PostgreSQL service**
2. Go to **"Database"** tab → **"Data"**
3. You should now see tables like:
   - tenants
   - users
   - deals
   - documents
   - facts
   - findings
   - analysis_runs
   - etc.

**If you see 12+ tables:** Success! Continue to Step 4
**If still empty:** Run the diagnostic script:
```bash
railway run python scripts/diagnose_railway_db.py
```

#### Step 4: Restart App and Test (2 minutes)

1. Go to your **app service**
2. Click **"Settings"**
3. Scroll down and click **"Restart"**
4. Wait for deployment to complete
5. Open your Railway app URL
6. Try to log in with:
   - Email: `admin@example.com`
   - Password: `changeme123`
7. Create a test deal and verify it works

---

### PART B: Redis Setup (Required for Background Tasks - 15 minutes)

#### Step 1: Set REDIS_URL Environment Variable (2 minutes)

1. Go to Railway dashboard → Your project
2. Click on **Redis service** → **Variables** tab
3. Copy the `REDIS_URL` value (or `REDIS_TLS_URL`)
   - Should look like: `redis://default:password@host:6379`
   - Or with TLS: `rediss://default:password@host:6379`
4. Go to your **app service** → **Variables** tab
5. If `REDIS_URL` is NOT there:
   - Click **"New Variable"**
   - Name: `REDIS_URL`
   - Value: Paste the copied URL
   - Click **"Add"**
6. Railway will redeploy automatically

#### Step 2: Verify Redis Connection (2 minutes)

After redeployment:

```bash
# Using Railway CLI
railway run python scripts/diagnose_railway_redis.py

# OR using Railway Dashboard
# App service → Deployments → Latest → ••• → Run One-Off Command
# Enter: python scripts/diagnose_railway_redis.py
```

**Expected output:**
```
✓ REDIS_URL set
✓ Redis connection successful
✓ Celery app initialized
✓ Can write and read from Redis
```

#### Step 3: Start Celery Worker Service (10 minutes)

**CRITICAL:** Redis is just the message broker - you need a worker to process tasks!

**Check if worker exists:**
1. In Railway dashboard, look for a service named "worker"
2. If it exists and shows "Online" - great, skip to Step 4!
3. If it doesn't exist or is stopped, continue below:

**Create worker service:**

1. In Railway dashboard, click **"New Service"**
2. Select **"Deploy from GitHub"**
3. Choose your repo and branch (same as main app)
4. Configure the service:
   - **Service Name:** `worker`
   - **Start Command:** `celery -A web.celery_app worker --loglevel=info --concurrency=2`
5. Add environment variables (CRITICAL - worker needs these):
   - `REDIS_URL` - Copy from Redis service
   - `DATABASE_URL` - Copy from PostgreSQL service
   - `ANTHROPIC_API_KEY` - Copy from app service
   - `USE_DATABASE` - Set to `true`
6. Deploy and wait for "Online" status

#### Step 4: Test Background Tasks (1 minute)

1. Open your Railway app URL
2. Create a new deal
3. Upload test documents
4. Click **"Run Analysis"**
5. **You should see:**
   - ✅ Analysis starts immediately (doesn't freeze UI)
   - ✅ Progress bar updates in real-time
   - ✅ Can navigate away and come back
   - ✅ Task status shows on dashboard
6. Check Redis in Railway:
   - Go to Redis service → Database tab
   - Should now see keys like `celery-task-meta-*`

**If analysis freezes the UI for 5-10 minutes:** Worker is not running or not connected to Redis

---

## Expected Outcomes

### Before Fix
- ❌ PostgreSQL: "You have no tables"
- ❌ Redis: "This is empty"
- ❌ App logs: "Continuing without database - some features may be limited"
- ❌ UI: Cannot create deals or view data
- ❌ Analysis freezes UI for 5-10 minutes (synchronous)
- ❌ All data goes to local JSON files only

### After Fix
- ✅ PostgreSQL: 12+ tables visible
- ✅ Redis: Shows keys after running analysis
- ✅ Celery worker: "Online" status in Railway
- ✅ App logs: "Database initialized (USE_DATABASE=True)"
- ✅ Analysis runs in background (UI responsive)
- ✅ Real-time progress updates
- ✅ Data persisted to database and visible in UI

---

## Timeline

### PostgreSQL Setup
- **Step 1 (Set DATABASE_URL):** 2 minutes
- **Step 2 (Initialize database):** 5 minutes
- **Step 3 (Verify tables):** 1 minute
- **Step 4 (Restart and test):** 2 minutes
- **Subtotal: 10 minutes**

### Redis + Celery Setup
- **Step 1 (Set REDIS_URL):** 2 minutes
- **Step 2 (Verify connection):** 2 minutes
- **Step 3 (Create worker service):** 10 minutes
- **Step 4 (Test background tasks):** 1 minute
- **Subtotal: 15 minutes**

**Total estimated time: 25 minutes**

**Priority:** Do PostgreSQL first (required for UI), then Redis (required for background tasks)

---

## If Something Goes Wrong

### PostgreSQL Issues

#### Error: "DATABASE_URL not set"
**Solution:** Make sure you copied DATABASE_URL to your **app service**, not just the PostgreSQL service

#### Error: "Connection refused"
**Solution:** Check if PostgreSQL service is online in Railway dashboard

#### Error: "Permission denied to create table"
**Solution:** Recreate PostgreSQL service with proper permissions, or check user privileges

#### Still stuck with PostgreSQL?
1. Run diagnostic script and save output:
   ```bash
   railway run python scripts/diagnose_railway_db.py > db_diagnostics.txt
   ```
2. Check app logs in Railway
3. Check PostgreSQL logs in Railway
4. Review the full guide: `docs/RAILWAY_DATABASE_FIX.md`

### Redis Issues

#### Error: "REDIS_URL not set"
**Solution:** Copy REDIS_URL from Redis service to app service (and worker service)

#### Error: Analysis freezes UI
**Cause:** No Celery worker running
**Solution:** Create worker service (see Part B, Step 3)

#### Error: Tasks stay "pending" forever
**Cause:** Worker can't connect to Redis or worker crashed
**Solution:**
1. Check worker logs in Railway
2. Verify worker has REDIS_URL environment variable
3. Restart worker service

#### Still stuck with Redis?
1. Run diagnostic script:
   ```bash
   railway run python scripts/diagnose_railway_redis.py > redis_diagnostics.txt
   ```
2. Check worker logs in Railway
3. Check Redis logs in Railway
4. Review the full guide: `docs/RAILWAY_REDIS_FIX.md`

---

## After You Fix This

### Re-run the CloudServe Test

Once the database is working:

1. Upload the CloudServe test documents again
2. Run the analysis
3. This time data should persist to PostgreSQL
4. You'll be able to see inventory counts in the UI
5. Then we can verify if the extraction bugs (infrastructure under-extraction, application category headers) are still present

### Next: Fix Extraction Bugs

After confirming the database works, we can proceed to **Phase 2: Fix Extraction Bugs**:
- Expand infrastructure header matching for cloud terminology
- Filter category headers in application parsing
- Update tests and validate fixes

But DATABASE must work FIRST, otherwise we can't verify the extraction fixes in the UI.

---

## Questions?

If you need help with any step, just ask! The scripts I created have detailed error messages to guide you.
