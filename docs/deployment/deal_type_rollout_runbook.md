# Deal Type Awareness - Deployment Runbook

**Version**: 1.0
**Last Updated**: 2025-02-11
**Estimated Total Time**: 14 hours (spread over 4 weeks)
**Downtime Required**: None (zero-downtime deployment)

---

## Overview

This runbook provides step-by-step instructions for deploying the deal type awareness feature across all environments. The deployment is structured in 4 phases to minimize risk and ensure backward compatibility.

### What's Being Deployed

- **Database Changes**: Add NOT NULL and CHECK constraints to `deal_type` column
- **Code Changes**: Conditional logic based on `deal_type` in synergy engine, cost engine, and reasoning agents
- **UI Changes**: Required `deal_type` field in deal creation form, edit functionality
- **Feature Flag**: `DEAL_TYPE_AWARENESS_ENABLED` for instant rollback capability

### Rollout Timeline

| Phase | Duration | Description |
|-------|----------|-------------|
| Phase 0 | Week 0 (4 hours) | Pre-flight validation and baseline capture |
| Phase 1 | Week 1 (2 hours) | Database migration to staging and production |
| Phase 2 | Week 2 (3 hours) | Code deployment with feature flag |
| Phase 3 | Week 3 (2 hours) | UI rollout and user communication |
| Phase 4 | Week 4 (3 hours) | Validation and cleanup |

---

## Phase 0: Pre-Flight Validation

**Duration**: 4 hours
**Downtime**: None
**Responsible**: Engineering Team

### Objectives

- Establish baseline behavior before changes
- Identify existing data quality issues
- Ensure test suite is healthy

### Pre-Flight Checklist

- [ ] **0.1** Verify test environment is clean
- [ ] **0.2** Run full test suite (572 tests)
- [ ] **0.3** Snapshot existing deal outputs
- [ ] **0.4** Audit current deal_type values
- [ ] **0.5** Document any known test failures
- [ ] **0.6** Create backup of production database

### Step-by-Step Procedures

#### 0.1 Verify Test Environment

```bash
cd "9.5/it-diligence-agent 2"

# Check Python version
python --version  # Should be 3.11+

# Verify dependencies
pip list | grep -E "(anthropic|pytest|flask|sqlalchemy)"

# Check database connectivity
python -c "from web.database import init_db; init_db(); print('✓ Database connected')"
```

**Expected Output**: All dependencies installed, database accessible

#### 0.2 Run Full Test Suite

```bash
# Run all tests and capture results
python -m pytest tests/ -v --cov --no-cov-on-fail > pre_migration_test_results.txt 2>&1

# Check exit code
echo $?  # Should be 0 (all tests passed)

# Review results
grep -E "passed|failed|error" pre_migration_test_results.txt
```

**Success Criteria**:
- All 572 tests pass (or document known failures to exclude from regression)
- No new test failures introduced

**If Tests Fail**:
- Document failures in `pre_migration_test_results.txt`
- Create list of acceptable failures (if any)
- Fix critical failures before proceeding

#### 0.3 Snapshot Existing Deal Outputs

```bash
# Create snapshots directory
mkdir -p data/

# Run snapshot script
python scripts/snapshot_existing_deals.py

# Verify snapshot created
ls -lh data/pre_migration_snapshots.json

# Review snapshot summary
python -c "import json; d=json.load(open('data/pre_migration_snapshots.json')); print(f\"Deals: {d['total_deals']}, Success: {d['success_count']}, Errors: {d['error_count']}\")"
```

**Success Criteria**:
- Snapshot file created successfully
- `success_count` matches total active deals
- No critical errors

**If Snapshot Fails**:
- Check database connectivity
- Verify deal IDs are valid
- Review error messages in output
- Fix issues and re-run

#### 0.4 Audit Current deal_type Values

```bash
# Run audit script
python scripts/audit_deal_types.py

# Capture output
python scripts/audit_deal_types.py > pre_migration_audit.txt
```

**Review Output**:
- Count of NULL deal_type values
- Count of invalid deal_type values
- Distribution by deal type
- Health score status

**Success Criteria**:
- Audit completes successfully
- Any NULL or invalid values are documented
- Health score is recorded for comparison

#### 0.5 Document Known Issues

Create `pre_migration_status.md`:

```markdown
# Pre-Migration Status - Deal Type Awareness

**Date**: [DATE]
**Tested By**: [NAME]

## Test Results
- Total tests: 572
- Passed: [COUNT]
- Failed: [COUNT]
- Known failures: [LIST]

## Deal Audit
- Total deals: [COUNT]
- NULL deal_type: [COUNT]
- Invalid deal_type: [COUNT]
- Health score: [SCORE]%

## Baseline Snapshots
- Snapshot file: data/pre_migration_snapshots.json
- Successful snapshots: [COUNT]
- Failed snapshots: [COUNT]

## Go/No-Go Decision
- [ ] All critical tests pass
- [ ] Snapshots captured successfully
- [ ] Data quality issues documented
- [ ] **APPROVED TO PROCEED** or **HOLD FOR FIXES**
```

#### 0.6 Backup Production Database

```bash
# PostgreSQL backup
pg_dump diligence_prod > backups/pre_deal_type_migration_$(date +%Y%m%d_%H%M%S).sql

# Verify backup
ls -lh backups/*.sql | tail -1

# Test restore (on non-production database)
# createdb test_restore
# psql test_restore < backups/pre_deal_type_migration_*.sql
# dropdb test_restore
```

**Success Criteria**:
- Backup file created
- Backup size is reasonable (>1MB typically)
- Test restore succeeds (optional but recommended)

### Phase 0 Sign-Off

Before proceeding to Phase 1, verify:

- [ ] All pre-flight checks completed
- [ ] Baseline documented in `pre_migration_status.md`
- [ ] Production database backed up
- [ ] Team approved to proceed

**Approved By**: ________________  **Date**: ________

---

## Phase 1: Database Migration

**Duration**: 2 hours
**Downtime**: ~5 minutes (during production migration)
**Responsible**: Database Team / DevOps

### Objectives

- Add NOT NULL constraint to `deal_type`
- Add CHECK constraint for valid values
- Backfill existing NULL values with 'acquisition'

### Migration Checklist

- [ ] **1.1** Review migration script
- [ ] **1.2** Test migration on local copy
- [ ] **1.3** Deploy to staging environment
- [ ] **1.4** Verify staging migration
- [ ] **1.5** Schedule production maintenance window
- [ ] **1.6** Deploy to production
- [ ] **1.7** Verify production migration
- [ ] **1.8** Monitor for issues

### Step-by-Step Procedures

#### 1.1 Review Migration Script

```bash
# View migration script
cat migrations/versions/004_add_deal_type_constraint.py

# Verify migration order
flask db history
```

**Review Points**:
- Backfill logic: NULL → 'acquisition'
- Normalization: 'carve-out' → 'carveout'
- Constraint logic: NOT NULL + CHECK
- Downgrade procedure

#### 1.2 Test Migration on Local Copy

```bash
# Create test database from production backup
createdb diligence_test
psql diligence_test < backups/pre_deal_type_migration_*.sql

# Run migration
export DATABASE_URL="postgresql://localhost/diligence_test"
flask db upgrade

# Verify constraints applied
psql diligence_test -c "\d deals" | grep -A 10 deal_type

# Expected output:
#   deal_type | character varying(50) | not null
#   Check constraints:
#     "valid_deal_type" CHECK (deal_type IN ('acquisition', 'carveout', 'divestiture'))

# Test insert with invalid value (should fail)
psql diligence_test -c "INSERT INTO deals (name, target_name, deal_type) VALUES ('Test', 'Target', 'invalid');"
# Expected: ERROR: new row for relation "deals" violates check constraint "valid_deal_type"

# Clean up
dropdb diligence_test
```

**Success Criteria**:
- Migration runs without errors
- Constraints are applied
- Invalid inserts are rejected

#### 1.3 Deploy to Staging Environment

```bash
# SSH to staging server
ssh staging-server

# Navigate to app directory
cd /app/it-diligence-agent

# Backup staging database
pg_dump diligence_staging > backups/staging_pre_migration_$(date +%Y%m%d_%H%M%S).sql

# Run migration
export FLASK_ENV=staging
flask db upgrade

# Verify
psql diligence_staging -c "\d deals" | grep -A 10 deal_type
```

**Success Criteria**:
- Migration completes successfully
- No errors in logs
- Constraints visible in schema

#### 1.4 Verify Staging Migration

```bash
# Check deal counts before/after
psql diligence_staging -c "SELECT deal_type, COUNT(*) FROM deals GROUP BY deal_type;"

# Expected: All NULL values converted to 'acquisition'

# Test application startup
systemctl status diligence-web
journalctl -u diligence-web -n 50

# Run smoke tests
python -m pytest tests/integration/test_deal_type_*.py -v
```

**Success Criteria**:
- All NULL values backfilled
- Application starts successfully
- Smoke tests pass

#### 1.5 Schedule Production Maintenance Window

**Recommended Window**: Low-traffic period (e.g., 2 AM UTC on Tuesday)

**Communication Template**:

```
Subject: Scheduled Maintenance - IT DD Agent - [DATE] 2:00-2:15 AM UTC

The IT Due Diligence Agent will undergo a brief maintenance window:

Date: [DATE]
Time: 2:00-2:15 AM UTC (5 minutes expected downtime)
Impact: Database schema update (deal type constraints)

What to Expect:
- Application will be unavailable for ~5 minutes
- In-progress analysis may be interrupted (resume after restart)
- No data loss expected

We will send an update when maintenance is complete.

Thank you,
IT DD Team
```

#### 1.6 Deploy to Production

**⚠ CRITICAL: Follow these steps exactly**

```bash
# 1. SSH to production
ssh production-server

# 2. Navigate to app directory
cd /app/it-diligence-agent

# 3. Backup database (CRITICAL)
pg_dump diligence_prod > backups/prod_pre_migration_$(date +%Y%m%d_%H%M%S).sql

# 4. Verify backup
ls -lh backups/*.sql | tail -1
# Should show recent backup with reasonable size

# 5. Put application in maintenance mode (if available)
# touch maintenance.flag
# OR stop accepting new requests via load balancer

# 6. Stop application
systemctl stop diligence-web
systemctl stop diligence-celery  # If using Celery

# 7. Run migration
export FLASK_ENV=production
flask db upgrade

# 8. Verify migration
psql diligence_prod -c "\d deals" | grep -A 10 deal_type

# 9. Restart application
systemctl start diligence-web
systemctl start diligence-celery

# 10. Remove maintenance mode
# rm maintenance.flag

# 11. Verify application is up
curl -I https://your-domain.com/health
# Should return 200 OK
```

**Expected Duration**: 5-10 minutes

#### 1.7 Verify Production Migration

```bash
# Check deal counts
psql diligence_prod -c "SELECT deal_type, COUNT(*) FROM deals GROUP BY deal_type;"

# Check for constraint
psql diligence_prod -c "SELECT conname, contype FROM pg_constraint WHERE conname = 'valid_deal_type';"

# Test insert (should fail)
psql diligence_prod -c "INSERT INTO deals (name, target_name, deal_type) VALUES ('Test', 'Test', 'invalid');"
# Expected: ERROR (check constraint violated)

# Rollback test insert
psql diligence_prod -c "ROLLBACK;"
```

**Success Criteria**:
- All NULL values converted to 'acquisition'
- Constraint exists
- Invalid inserts rejected
- Application responding

#### 1.8 Monitor for Issues

```bash
# Monitor application logs
tail -f /var/log/diligence/app.log

# Monitor error logs
tail -f /var/log/diligence/error.log

# Monitor database connections
psql diligence_prod -c "SELECT count(*) FROM pg_stat_activity WHERE datname = 'diligence_prod';"

# Check for errors in last hour
journalctl -u diligence-web --since "1 hour ago" | grep -i error
```

**Monitor for 2 hours after deployment**

**Alert Thresholds**:
- Database errors > 0
- Application startup failures > 0
- Deal creation failures > 5%

### Phase 1 Rollback Procedure

**If critical issues arise:**

```bash
# 1. Stop application
systemctl stop diligence-web

# 2. Rollback migration
flask db downgrade

# 3. Verify rollback
psql diligence_prod -c "\d deals" | grep deal_type
# Should show: deal_type | character varying(50) | (nullable)

# 4. Restart application
systemctl start diligence-web

# 5. Investigate issue
# Review logs, consult team, fix issue

# 6. Re-attempt migration after fix
```

### Phase 1 Sign-Off

- [ ] Migration deployed to staging successfully
- [ ] Migration deployed to production successfully
- [ ] All constraints verified
- [ ] No errors in logs (2 hours post-deployment)
- [ ] Rollback procedure tested (optional)

**Approved By**: ________________  **Date**: ________

---

## Phase 2: Code Deployment with Feature Flag

**Duration**: 3 hours
**Downtime**: None (rolling restart only)
**Responsible**: Engineering Team

### Objectives

- Deploy new code with deal_type awareness
- Use feature flag to enable/disable new behavior
- Monitor logs for issues

### Deployment Checklist

- [ ] **2.1** Review code changes
- [ ] **2.2** Run tests with feature flag enabled
- [ ] **2.3** Deploy to staging with flag ENABLED
- [ ] **2.4** Verify staging behavior
- [ ] **2.5** Deploy to production with flag ENABLED
- [ ] **2.6** Monitor logs for deal_type propagation
- [ ] **2.7** Run production smoke tests

### Step-by-Step Procedures

#### 2.1 Review Code Changes

**Files Modified**:
- `config_v2.py`: Added `DEAL_TYPE_AWARENESS_ENABLED` flag
- `services/synergy_engine.py`: Conditional logic for carveout/divestiture
- `services/cost_service.py`: Deal-aware cost multipliers
- `prompts/*.py`: Conditional prompt templates

**Review Points**:
- Feature flag checks in place
- Fallback to old behavior when flag=false
- Backward compatibility maintained

#### 2.2 Run Tests with Feature Flag

```bash
# Test with flag ENABLED (new behavior)
export DEAL_TYPE_AWARENESS=true
python -m pytest tests/ -v -k deal_type

# Test with flag DISABLED (old behavior)
export DEAL_TYPE_AWARENESS=false
python -m pytest tests/ -v

# Both should pass
```

**Success Criteria**:
- All tests pass with flag enabled
- All tests pass with flag disabled
- No new test failures

#### 2.3 Deploy to Staging with Flag ENABLED

```bash
# SSH to staging
ssh staging-server

# Pull latest code
cd /app/it-diligence-agent
git pull origin main

# Set feature flag
echo "DEAL_TYPE_AWARENESS=true" >> .env

# Restart application
systemctl restart diligence-web

# Verify environment variable
systemctl show diligence-web --property=Environment | grep DEAL_TYPE
```

#### 2.4 Verify Staging Behavior

```bash
# Create test acquisition deal
curl -X POST http://staging-url/api/v1/deals \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Acquisition", "target_name": "Target", "deal_type": "acquisition"}'

# Create test carveout deal
curl -X POST http://staging-url/api/v1/deals \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Carveout", "target_name": "Target", "deal_type": "carveout"}'

# Check logs for deal_type propagation
tail -f /var/log/diligence/app.log | grep "deal_type"

# Expected: Logs show deal_type being passed through analysis pipeline
```

**Success Criteria**:
- Acquisition deals produce consolidation synergies
- Carveout deals produce separation costs
- Logs show deal_type propagation

#### 2.5 Deploy to Production with Flag ENABLED

```bash
# SSH to production
ssh production-server

# Pull latest code
cd /app/it-diligence-agent
git pull origin main

# Set feature flag
echo "DEAL_TYPE_AWARENESS=true" >> .env

# Restart application (rolling restart if using multiple workers)
systemctl restart diligence-web

# Verify
systemctl status diligence-web
```

**Downtime**: ~10 seconds per worker (rolling restart)

#### 2.6 Monitor Logs for deal_type Propagation

```bash
# Monitor application logs
tail -f /var/log/diligence/app.log | grep "deal_type"

# Count deal_type occurrences by type
cat /var/log/diligence/app.log | grep "deal_type" | grep -oP 'deal_type=\w+' | sort | uniq -c

# Expected output:
#   150 deal_type=acquisition
#    25 deal_type=carveout
#     5 deal_type=divestiture
```

**Monitor for 24 hours**

#### 2.7 Run Production Smoke Tests

```bash
# Test acquisition workflow
python -m pytest tests/integration/test_acquisition_workflow.py -v

# Test carveout workflow
python -m pytest tests/integration/test_carveout_workflow.py -v

# Test UI deal creation
# (Manual test in browser or automated E2E tests)
```

### Phase 2 Rollback Procedure

**Instant Rollback (Feature Flag)**

```bash
# Disable feature flag (keeps code deployed but reverts to old behavior)
ssh production-server
cd /app/it-diligence-agent
echo "DEAL_TYPE_AWARENESS=false" >> .env
systemctl restart diligence-web

# System reverts to always using consolidation logic
# No code or database changes needed
```

**Full Rollback (Code)**

```bash
# If feature flag rollback insufficient:
git revert <commit_hash>
git push origin main
systemctl restart diligence-web
```

### Phase 2 Sign-Off

- [ ] Code deployed to staging successfully
- [ ] Code deployed to production successfully
- [ ] Feature flag controls behavior correctly
- [ ] Logs show deal_type propagation
- [ ] No errors in 24-hour monitoring period

**Approved By**: ________________  **Date**: ________

---

## Phase 3: UI Rollout

**Duration**: 2 hours
**Downtime**: None
**Responsible**: Product Team / Engineering

### Objectives

- Make deal_type selection required in UI
- Add deal type edit functionality
- Deploy user documentation
- Communicate changes to users

### Deployment Checklist

- [ ] **3.1** Review UI changes
- [ ] **3.2** Deploy templates to staging
- [ ] **3.3** Manual UI testing checklist
- [ ] **3.4** Deploy to production
- [ ] **3.5** Send user communication email
- [ ] **3.6** Update user documentation

### Step-by-Step Procedures

#### 3.1 Review UI Changes

**Files Modified**:
- `web/templates/deals/create.html`: Required deal_type field
- `web/templates/deals/edit.html`: Deal type edit dropdown
- `web/static/js/deal_form.js`: Client-side validation

**Review Points**:
- Deal type field is required
- Default value is 'acquisition'
- Edit functionality preserves existing deals
- Help text explains each deal type

#### 3.2 Deploy Templates to Staging

```bash
# SSH to staging
ssh staging-server

# Pull latest templates
cd /app/it-diligence-agent
git pull origin main

# Restart (to reload templates)
systemctl restart diligence-web
```

#### 3.3 Manual UI Testing Checklist

**Test in Staging Environment**:

- [ ] Create new deal → deal_type field is required
- [ ] Create new deal → default value is 'acquisition'
- [ ] Create new deal with 'acquisition' → see consolidation recommendations
- [ ] Create new deal with 'carveout' → see separation costs
- [ ] Create new deal with 'divestiture' → see extraction costs
- [ ] Edit existing deal → can change deal_type
- [ ] Edit existing deal → change persists after save
- [ ] Check cost report → TSA costs appear for carveout only
- [ ] Check cost report → consolidation synergies appear for acquisition only
- [ ] Help text displays correctly for each deal type

**Bug Reporting**: Document any issues in GitHub/Jira before production deployment

#### 3.4 Deploy to Production

```bash
# SSH to production
ssh production-server

# Pull latest code
cd /app/it-diligence-agent
git pull origin main

# Restart application
systemctl restart diligence-web

# Verify
curl -I https://your-domain.com/deals/create
# Should return 200 OK
```

#### 3.5 Send User Communication Email

**See**: `docs/user_communication/deal_type_announcement_email.md`

**Send To**: All active users

**Timing**: Immediately after production deployment

#### 3.6 Update User Documentation

**Files to Update**:
- `docs/user_guide/creating_deals.md` (already updated in Spec 05)
- `docs/FAQ.md`: Add deal type FAQ section
- `docs/GETTING_STARTED.md`: Mention deal type selection

### Phase 3 Sign-Off

- [ ] UI deployed to staging and tested
- [ ] UI deployed to production
- [ ] User communication sent
- [ ] Documentation updated
- [ ] No user-reported issues (first 48 hours)

**Approved By**: ________________  **Date**: ________

---

## Phase 4: Validation & Cleanup

**Duration**: 3 hours
**Downtime**: None
**Responsible**: Engineering Team / QA

### Objectives

- Compare post-migration outputs to baseline
- Validate no regressions for acquisition deals
- Remove feature flag (make permanent)
- Archive migration artifacts

### Validation Checklist

- [ ] **4.1** Capture post-migration snapshots
- [ ] **4.2** Run regression comparison
- [ ] **4.3** Investigate any regressions
- [ ] **4.4** Remove feature flag
- [ ] **4.5** Run full test suite
- [ ] **4.6** Archive migration artifacts
- [ ] **4.7** Post-migration audit (30 days later)

### Step-by-Step Procedures

#### 4.1 Capture Post-Migration Snapshots

```bash
# Run snapshot script with --post flag
python scripts/snapshot_existing_deals.py --post

# Verify snapshot created
ls -lh data/post_migration_snapshots.json
```

#### 4.2 Run Regression Comparison

```bash
# Compare snapshots
python scripts/compare_snapshots.py

# Expected output:
# ✓ NO REGRESSIONS: All acquisition deals match baseline
```

**Success Criteria**:
- No regressions detected (within 5% tolerance)
- Acquisition deals produce identical outputs

**If Regressions Found**:
- Review each regression detail
- Determine if change is expected or bug
- Fix bugs or adjust tolerance if justified
- Re-run comparison

#### 4.3 Investigate Any Regressions

**For each regression**:

1. Check deal details:
   ```bash
   psql diligence_prod -c "SELECT * FROM deals WHERE id = [DEAL_ID];"
   ```

2. Review logs:
   ```bash
   grep "deal_id=[DEAL_ID]" /var/log/diligence/app.log
   ```

3. Re-run analysis manually:
   ```bash
   python main_v2.py --deal-id [DEAL_ID] --all
   ```

4. Compare outputs

5. Document findings

#### 4.4 Remove Feature Flag

**Once validated, make deal_type awareness permanent:**

```bash
# Edit config_v2.py
# REMOVE: DEAL_TYPE_AWARENESS_ENABLED = os.getenv(...)

# Edit web/blueprints/costs.py
# REMOVE: if not DEAL_TYPE_AWARENESS_ENABLED: ...

# Commit changes
git add config_v2.py web/blueprints/costs.py
git commit -m "Remove DEAL_TYPE_AWARENESS feature flag (now permanent)"
git push origin main

# Deploy
ssh production-server
cd /app/it-diligence-agent
git pull origin main
systemctl restart diligence-web
```

#### 4.5 Run Full Test Suite

```bash
# Run all tests post-cleanup
python -m pytest tests/ -v --cov

# Compare to pre-migration results
diff pre_migration_test_results.txt post_migration_test_results.txt
```

**Success Criteria**:
- All tests pass
- No new failures vs. baseline

#### 4.6 Archive Migration Artifacts

```bash
# Create archive directory
mkdir -p archives/deal_type_migration_$(date +%Y%m%d)

# Archive snapshots
cp data/pre_migration_snapshots.json archives/deal_type_migration_*/
cp data/post_migration_snapshots.json archives/deal_type_migration_*/

# Archive test results
cp pre_migration_test_results.txt archives/deal_type_migration_*/
cp post_migration_test_results.txt archives/deal_type_migration_*/

# Archive audit reports
cp pre_migration_audit.txt archives/deal_type_migration_*/

# Archive database backups (reference only, keep originals)
ls backups/pre_deal_type_migration_* >> archives/deal_type_migration_*/backup_locations.txt

# Archive runbook
cp docs/deployment/deal_type_rollout_runbook.md archives/deal_type_migration_*/
```

#### 4.7 Post-Migration Audit (30 Days Later)

**Run 30 days after Phase 4 completion:**

```bash
# Re-run deal type audit
python scripts/audit_deal_types.py --json > post_migration_audit_30d.json

# Check health score
python -c "import json; d=json.load(open('post_migration_audit_30d.json')); print(f\"Health: {d['health_score']['status']}\")"
```

**Audit Checklist**:
- [ ] All deals have valid deal_type (acquisition, carveout, or divestiture)
- [ ] No NULL deal_type values in database
- [ ] Cost estimates for carveouts are 1.5-3x higher than comparable acquisitions
- [ ] TSA costs appear ONLY for carveouts, not acquisitions
- [ ] User support tickets about deal_type <5/week
- [ ] No rollbacks or feature flag toggles in past 30 days
- [ ] Regression test suite passes 100%

### Phase 4 Sign-Off

- [ ] Post-migration snapshots captured
- [ ] Regression comparison shows no issues
- [ ] Feature flag removed
- [ ] Full test suite passes
- [ ] Migration artifacts archived
- [ ] 30-day audit scheduled

**Approved By**: ________________  **Date**: ________

---

## Monitoring & Observability

### Metrics to Track

| Metric | Query | Threshold | Alert If |
|--------|-------|-----------|----------|
| Deal creation failures | `SELECT COUNT(*) FROM deals WHERE created_at > NOW() - INTERVAL '1 day' AND deal_type IS NULL` | 0 | >0 |
| Cost calculation errors | `grep "cost calculation error" /var/log/diligence/app.log | wc -l` | 0 | >5 per hour |
| Feature flag usage | `grep "DEAL_TYPE_AWARENESS" /var/log/diligence/app.log` | 0 after Phase 4 | >0 |
| User support tickets | Check support system | <5/week | >20/week |

### Log Queries

```bash
# Count deal creations by type (last 7 days)
psql diligence_prod -c "SELECT deal_type, COUNT(*) FROM deals WHERE created_at > NOW() - INTERVAL '7 days' GROUP BY deal_type;"

# Check for errors in last 24 hours
grep -i error /var/log/diligence/app.log | grep -v "expected_error" | tail -50

# Monitor deal_type propagation
cat /var/log/diligence/app.log | grep "deal_type=" | tail -20
```

---

## Rollback Decision Tree

```
Issue Detected
    │
    ├─ Affects <10% of deals
    │   └─> Fix forward (patch deployment)
    │
    ├─ Affects 10-50% of deals
    │   └─> Disable feature flag, investigate, re-deploy with fix
    │
    └─ Affects >50% of deals OR data corruption
        └─> Full rollback (code + database)
```

### Full Rollback Procedure

**⚠ EMERGENCY USE ONLY**

```bash
# 1. Stop application
systemctl stop diligence-web

# 2. Rollback code
git revert <migration_commit_hash>
git push origin main
git pull origin main

# 3. Rollback database
flask db downgrade -1

# 4. Restore from backup (if needed)
pg_restore -d diligence_prod backups/prod_pre_migration_*.sql

# 5. Restart application
systemctl start diligence-web

# 6. Verify
curl -I https://your-domain.com/health
psql diligence_prod -c "\d deals" | grep deal_type

# 7. Notify team and users
# Send incident report
```

---

## Success Criteria (Overall)

- [ ] All 572 existing tests still pass post-migration
- [ ] Pre/post migration snapshots match for acquisition deals (±5% cost variance)
- [ ] Database constraints applied: NOT NULL + CHECK on deal_type
- [ ] Feature flag successfully controls new behavior
- [ ] UI requires deal_type selection for new deals
- [ ] Zero production incidents during rollout
- [ ] User documentation updated and distributed
- [ ] Rollback plan tested in staging environment

---

## Contact Information

| Role | Name | Contact |
|------|------|---------|
| Engineering Lead | [NAME] | [EMAIL] |
| Database Admin | [NAME] | [EMAIL] |
| Product Manager | [NAME] | [EMAIL] |
| On-Call Engineer | [NAME] | [PHONE] |

---

## Post-Deployment Review

**Scheduled**: [DATE] (1 week after Phase 4 completion)

**Agenda**:
- Review deployment timeline vs. plan
- Discuss any issues encountered
- Document lessons learned
- Identify process improvements

**Attendees**: Engineering, Product, DevOps

---

**End of Runbook**
