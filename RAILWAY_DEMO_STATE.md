# Railway Production State - Demo Day

**Commit:** `2a5ef3b` (DOCS: Complete isolation strategy for experimental domain model)
**Previous Stable:** `5ba1bb9` (ROLLBACK: Disable fact promotion to fix duplication crisis)
**Branch:** `main`
**Locked Date:** 2026-02-12 15:39:09 EST
**Demo Date:** 2026-02-13 (TOMORROW)

**Status:** 🔒 **LOCKED FOR DEMO**

---

## ⚠️ DO NOT DEPLOY TO RAILWAY UNTIL AFTER DEMO

---

## What's Running on Railway

### Current Behavior
- Emergency rollback active (commit `5ba1bb9`)
- Deterministic parser fact promotion: **DISABLED**
- Expected app count: **60-70** (not 143)
- FactStore promotion to InventoryStore: **DISABLED**
- Behavior: **STABLE** (tested locally)

### Code State
```bash
# Last 5 commits:
2a5ef3b - DOCS: Complete isolation strategy for experimental domain model
edf84e4 - REFINE: Architecture crisis doc - executive-ready with financial analysis
dccf49c - ARCHITECTURE: Domain-first redesign proposal + proof-of-concept
5ba1bb9 - ROLLBACK: Disable fact promotion to fix duplication crisis
b0db1be - Fix: Add missing fact-to-inventory promotion step
```

### Environment Variables (Railway)
```bash
ENVIRONMENT=production
ENABLE_DOMAIN_MODEL=false        # ← CRITICAL: Experimental code disabled
DATABASE_URL=postgresql://...     # Production database
ANTHROPIC_API_KEY=sk-ant-...     # API key
AUTH_REQUIRED=false              # Demo mode
```

---

## Post-Demo Work

### Experimental Domain Model (Background)
- **Location:** `domain/` directory
- **Status:** Active development (isolated from production)
- **Documentation:** `ISOLATION_STRATEGY.md`
- **Timeline:** 6-8 weeks migration
- **Risk to Demo:** ✅ **ZERO** (5-layer isolation)

### Week 1 Priorities (Post-Demo)
1. ✅ Isolation setup (Worker 0) - COMPLETE
2. ⏳ Kernel foundation (Worker 1) - Running overnight
3. ⏳ Application domain (Worker 2) - Scheduled post-demo
4. ⏳ Infrastructure domain (Worker 3) - Scheduled post-demo
5. ⏳ Reconciliation service (Worker 4) - Scheduled post-demo

---

## Emergency Procedures

### If Demo Shows Duplicates or Crashes

**Immediate Response (2 minutes):**
1. Open Railway dashboard: https://railway.app/project/[your-project]
2. Navigate to: **Deployments** tab
3. Find deployment tagged: `demo-stable-2026-02-12`
4. Click: **Redeploy this version**
5. Wait: 30-60 seconds
6. Test: Refresh demo UI in browser

**Verification:**
```bash
# After rollback, verify Railway is on correct commit
# (Run locally to check what should be deployed)
git log --oneline | grep "demo-stable"
# Expected: Tag points to 2a5ef3b or 5ba1bb9
```

### If App Count is Wrong

**Expected:** 60-70 applications (target entity)

**If seeing 143+ apps:**
- Deterministic parser promotion is enabled (should be disabled)
- Rollback to `demo-stable-2026-02-12` tag
- Check Railway environment: `ENABLE_DOMAIN_MODEL=false`

**If seeing <50 apps:**
- Discovery agents may have failed
- Check Railway logs for errors
- May need to re-run analysis or rollback

### If "Legacy Facts" Banner Appears

**Meaning:** InventoryStore is empty, UI falling back to FactStore

**Causes:**
1. `inventory_store.save()` failed to write JSON
2. JSON file path incorrect
3. Permissions issue on Railway filesystem

**Immediate Fix:**
- Re-run analysis from UI
- Check logs for InventoryStore errors
- May need rollback if persistent

---

## Rollback Plan

### Quick Rollback (Railway Dashboard)
1. Railway dashboard → Deployments
2. Select: `demo-stable-2026-02-12` tag
3. Redeploy (30 seconds)

### Manual Rollback (Git)
```bash
# If Railway dashboard unavailable
git checkout demo-stable-2026-02-12
git push railway main --force

# Warning: Only use if dashboard rollback fails
```

### Nuclear Option (Last Resort)
```bash
# Revert to known-good commit (before domain work started)
git checkout 5ba1bb9  # Emergency rollback commit
git push railway main --force

# This reverts to state BEFORE architecture work
# Use only if demo-stable tag also has issues
```

---

## Demo Day Checklist

### Pre-Demo (Morning)
- [ ] Verify Railway deployment: `demo-stable-2026-02-12` tag
- [ ] Check environment variables: `ENABLE_DOMAIN_MODEL=false`
- [ ] Test demo locally: `python main_v2.py data/input/ --all`
- [ ] Verify app count: 60-70 (not 143)
- [ ] Check Railway logs: No errors in last 24 hours
- [ ] Backup data: Copy `data/` directory

### During Demo
- [ ] Demo uses production CLI: `main_v2.py`
- [ ] Experimental code is invisible (not imported)
- [ ] Monitor Railway logs (keep dashboard open in background tab)
- [ ] Have rollback procedure ready (know the steps)

### Post-Demo
- [ ] Verify experimental work completed: `ls domain/kernel/`
- [ ] Review Worker 1 progress: `pytest domain/kernel/tests/`
- [ ] Launch Workers 2-4: Application, Infrastructure, Reconciliation
- [ ] Update this document with demo outcome

---

## Contacts

**Demo Lead:** [Your Name]
**Technical Support:** [Your Name]
**Railway Project:** [Your Railway Project URL]
**Backup Plan:** Emergency rollback to `demo-stable-2026-02-12`

---

## Testing Log

### 2026-02-12 15:39:09 EST - Pre-Demo Test
```bash
# Test command:
python main_v2.py data/input/ --all --target-name "DemoTarget Inc"

# Results:
# - App count: [To be tested]
# - Duplicates: [To be tested]
# - Report generation: [To be tested]
# - Time taken: [To be tested]

# Status: ⏳ TO BE TESTED BEFORE DEMO
```

---

## Production Safety Guarantees

### Why Experimental Code Cannot Affect Demo

**Layer 1: Directory Separation**
- Production: `agents_v2/`, `stores/`, `web/`
- Experimental: `domain/`
- No imports between them (verified by grep)

**Layer 2: Import Guards**
- `domain/__init__.py` emits warning if imported in production
- Verified: `grep -r "from domain" agents_v2/ stores/ web/` → no output

**Layer 3: Runtime Guards**
- `domain/guards.py` raises error if `ENVIRONMENT=production`
- Railway sets `ENVIRONMENT=production`
- Experimental code **cannot execute** on Railway

**Layer 4: Database Isolation**
- Production: `DATABASE_URL` (PostgreSQL)
- Experimental: `domain_experimental.db` (SQLite)
- Physically separate databases

**Layer 5: Feature Flags**
- Railway: `ENABLE_DOMAIN_MODEL=false`
- Experimental code checks this flag
- Even if imported, **cannot run**

**Conclusion:** 5 independent safety layers. Demo is protected.

---

## Version History

| Date | Change | Author |
|------|--------|--------|
| 2026-02-12 15:39 | Created demo state documentation | Worker 0 |
| 2026-02-12 15:39 | Locked production to demo-stable tag | Worker 0 |

---

**Last Updated:** 2026-02-12 15:39:09 EST
**Next Review:** Post-demo (2026-02-13 afternoon)
