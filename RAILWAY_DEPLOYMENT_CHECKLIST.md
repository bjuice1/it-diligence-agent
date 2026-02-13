# Railway Deployment Checklist: "it-dd-v2"

Quick step-by-step checklist to get your IT DD Agent V2 live on Railway.

---

## 🎯 Pre-Deployment Status

**Railway Project:** `serene-spontaneity`
**URL:** https://railway.com/project/9f1f4bd7-fcd0-4893-81a1-0698951818bb

### ✅ Already Configured

- [x] Railway project created
- [x] PostgreSQL database added
- [x] Environment variables set:
  - [x] `ANTHROPIC_API_KEY`
  - [x] `USE_DOMAIN_MODEL=true` ← **Domain model enabled!**
  - [x] `SECRET_KEY`
  - [x] `FLASK_ENV=production`
  - [x] `MAX_PARALLEL_AGENTS=1`
  - [x] `USE_DATABASE=true`
  - [x] `USE_CELERY=true`
  - [x] `USE_REDIS_SESSIONS=true`

---

## 📋 Deployment Steps (5 minutes)

### Step 1: Add Redis Service

**In Railway Dashboard:**

- [ ] Click **"+ New"** button
- [ ] Select **"Database"**
- [ ] Choose **"Redis"**
- [ ] Wait for provisioning (~30 seconds)
- [ ] Verify `REDIS_URL` appears in environment variables

**Expected:** Redis service shows green status ✅

---

### Step 2: Add Web Service from GitHub

**In Railway Dashboard:**

- [ ] Click **"+ New"** button again
- [ ] Select **"GitHub Repo"**
- [ ] Choose repository: **`bjuice1/it-diligence-agent`**
- [ ] Railway auto-detects Python app
- [ ] Click **"Deploy"**

**Expected:** Build starts automatically

---

### Step 3: Monitor Build Progress

**Watch Railway Build Logs:**

- [ ] Click on **Web Service**
- [ ] Click **"Deployments"** tab
- [ ] Click **"View Logs"**

**Look for:**
```
✓ Installing dependencies...
✓ Building application...
✓ Running migrations...
✓ Starting server...
✓ Deployment live
```

**Build time:** ~2-4 minutes

---

### Step 4: Get Your Live URL

**Once deployed:**

- [ ] Railway shows **"Active"** status (green)
- [ ] Copy the public URL (shown at top of service)
  - Format: `https://serene-spontaneity.up.railway.app`
  - Or click **"Open"** button to visit

**Expected:** URL format `https://[project-name].up.railway.app`

---

### Step 5: Verify Deployment

**Health Check:**
- [ ] Visit: `https://[your-url]/health`
- [ ] Should return: `{"status": "healthy"}`

**Web UI:**
- [ ] Visit: `https://[your-url]`
- [ ] Should see: Login page or dashboard

**Expected:** Both endpoints respond successfully

---

## 🧪 Test Domain Model Integration

### Upload Test Documents

- [ ] Navigate to web UI
- [ ] Upload Great Insurance test PDFs:
  - `Great_Insurance_Document_1_Executive_IT_Profile.pdf`
  - `Great_Insurance_Document_2_Application_Inventory.pdf`
- [ ] Start analysis

### Check Railway Logs

**In Railway → Web Service → Logs, look for:**

```
============================================================
DOMAIN MODEL INTEGRATION
============================================================

[Applications Domain]
  Created 4 target + 1 buyer applications
  Total: 5 (after deduplication)

[Infrastructure Domain]
  Created 3 target + 0 buyer infrastructure
  Total: 3 (after deduplication)

[Organization Domain]
  Created 5 target + 2 buyer people
  Total: 7 (after deduplication)

[Domain Model Integration Complete]
  Aggregates created: 15
  Items synced to inventory: 15
============================================================
```

- [ ] Domain model integration logs appear
- [ ] See deduplication statistics
- [ ] No import errors

### Verify Deduplication

**In the web UI inventory:**

- [ ] Search for "Salesforce"
- [ ] Should see **1 application** (not 3)
- [ ] Observation count: **3** (showing 3 variants merged)
- [ ] SAP ERP and SAP SuccessFactors: **separate** (not collided)

**Expected:** Deduplication working correctly ✅

---

## 🎨 Optional: Rename Project

**To change from "serene-spontaneity" to "it-dd-v2":**

- [ ] In Railway dashboard, click project name
- [ ] Go to **Settings**
- [ ] Under "Project Name", enter: `it-dd-v2`
- [ ] Click **Save**
- [ ] New URL will be: `https://it-dd-v2.up.railway.app`

---

## ⚙️ Optional: Add Celery Worker (for background jobs)

**If you need async task processing:**

- [ ] Click **"+ New"** → **"Empty Service"**
- [ ] Name it: `worker`
- [ ] Set start command:
  ```
  celery -A web.celery_app worker --loglevel=info --concurrency=4
  ```
- [ ] Deploy

**Note:** Worker shares same environment variables as web service

---

## 🛟 Troubleshooting

### If Build Fails

**Check Railway build logs for:**

- [ ] Error: "No module named 'X'"
  - **Fix:** Add to `requirements.txt`, commit, push

- [ ] Error: "Out of memory"
  - **Fix:** Already set `MAX_PARALLEL_AGENTS=1`, should not happen

- [ ] Error: "Can't connect to database"
  - **Fix:** Ensure PostgreSQL service is green (running)

### If Domain Model Import Error

**If logs show:**
```
DOMAIN MODEL INTEGRATION - IMPORT ERROR
Cannot import domain model packages
```

**Fix:**
- [ ] Verify `domain/` directory exists in repo
- [ ] Check it's committed to GitHub
- [ ] Trigger redeploy in Railway

### If Health Check Fails

**If `/health` returns 404 or 500:**

- [ ] Check web service logs for errors
- [ ] Verify `web/app.py` has health endpoint
- [ ] Check Flask is running (logs show "Gunicorn started")

---

## 📊 Success Criteria

### ✅ Deployment Successful When:

- [x] Railway shows **Active** status (green)
- [x] Health check returns `{"status": "healthy"}`
- [x] Web UI loads without errors
- [x] Can upload documents
- [x] Analysis runs successfully
- [x] Domain model integration logs appear
- [x] Deduplication working (Salesforce: 3 observations → 1 app)
- [x] No import errors in logs

---

## 🎯 Demo Readiness Checklist

**Before showing stakeholders:**

- [ ] Upload test documents
- [ ] Run full analysis end-to-end
- [ ] Take screenshot of Railway logs showing domain model integration
- [ ] Take screenshot of inventory showing Salesforce with 3 observations
- [ ] Prepare comparison:
  - Without domain model: Would show 3 Salesforce apps
  - With domain model: Shows 1 Salesforce app (3 observations)
- [ ] Test rollback: Set `USE_DOMAIN_MODEL=false`, redeploy, verify old behavior
- [ ] Re-enable: Set `USE_DOMAIN_MODEL=true`, redeploy

---

## 📱 Quick Reference

### Railway Dashboard URLs

- **Project:** https://railway.com/project/9f1f4bd7-fcd0-4893-81a1-0698951818bb
- **Settings:** Click project name → Settings
- **Logs:** Web Service → Deployments → View Logs
- **Metrics:** Web Service → Metrics tab

### Railway CLI Commands

```bash
# View project status
railway status

# View logs
railway logs

# Open in browser
railway open

# Set environment variable
railway variables set KEY=value

# Deploy
railway up
```

### Important Environment Variables

| Variable | Value | Purpose |
|----------|-------|---------|
| `USE_DOMAIN_MODEL` | `true` | Enable deduplication |
| `MAX_PARALLEL_AGENTS` | `1` | Prevent OOM |
| `ANTHROPIC_API_KEY` | `sk-ant-...` | API access |
| `DATABASE_URL` | Auto-set | PostgreSQL connection |
| `REDIS_URL` | Auto-set | Redis connection |

---

## 🎬 Next Steps After Deployment

### Immediate (Today)

1. [ ] Complete Steps 1-5 above
2. [ ] Test with sample documents
3. [ ] Verify domain model working
4. [ ] Screenshot logs for demo

### Short-Term (This Week)

5. [ ] Upload production documents
6. [ ] Compare counts: old system vs new system
7. [ ] Validate P0-3 fix at scale
8. [ ] Collect performance metrics

### Medium-Term (Next 2 Weeks)

9. [ ] Gradual rollout (10% → 50% → 100%)
10. [ ] Monitor error rates
11. [ ] Gather user feedback
12. [ ] Iterate based on production data

---

## ✅ Final Checklist

**Deployment Complete When All Green:**

- [ ] PostgreSQL: ✅ Active
- [ ] Redis: ✅ Active
- [ ] Web Service: ✅ Active
- [ ] Health check: ✅ Passing
- [ ] Web UI: ✅ Loading
- [ ] Domain model: ✅ Enabled
- [ ] Test analysis: ✅ Completed
- [ ] Deduplication: ✅ Working

---

## 🚀 Ready to Deploy!

**Estimated Time:** 5-10 minutes

**What you're deploying:**
- IT Due Diligence Agent V2
- With domain model integration (P0-3 fix)
- PostgreSQL + Redis backend
- Production-ready web UI
- Smart deduplication enabled

**Your live URL will be:**
```
https://serene-spontaneity.up.railway.app
```

**Or after rename:**
```
https://it-dd-v2.up.railway.app
```

---

💡 **Tip:** Keep this checklist open in one tab, Railway dashboard in another, and check off items as you go!

🎉 **You're ready to ship!** Follow the steps above and you'll have a live demo in ~5 minutes.
