# Deployment Guide - IT Diligence Agent v2.4

**Last Updated:** 2026-02-11
**Version:** 2.4 (P0 Cost Status Tracking)

This guide covers deploying the P0 cost status tracking fixes to staging and production environments.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Variables](#environment-variables)
- [Database Migration](#database-migration)
- [Deployment Procedures](#deployment-procedures)
- [Verification Steps](#verification-steps)
- [Rollback Procedures](#rollback-procedures)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Software Requirements

- Python 3.11+
- PostgreSQL 15+ (production/staging)
- SQLite 3.9.0+ (local development)
- Redis 7+ (for Celery background tasks)
- Node.js 18+ (for frontend assets, if applicable)

### Access Requirements

- Database admin credentials (for running migrations)
- SSH access to staging/production servers
- GitHub repository access
- Anthropic API key with sufficient credits

### Pre-Deployment Checklist

- [ ] All P0 tests passing locally (23/23 cost status tests)
- [ ] Full test suite passing (821+ tests)
- [ ] Code reviewed and approved
- [ ] Backup of production database taken
- [ ] Rollback plan reviewed with team
- [ ] Deployment window scheduled (off-peak hours recommended)

---

## Environment Variables

### Required Variables

```bash
# API Keys
ANTHROPIC_API_KEY=sk-ant-...          # Claude API key (required)

# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname  # PostgreSQL connection string
# OR for SQLite (local dev only)
DATABASE_URL=sqlite:///data/diligence.db

# Redis (for background tasks)
REDIS_URL=redis://localhost:6379/0

# Flask Configuration
FLASK_APP=web.app
FLASK_ENV=production                   # production | staging | development
SECRET_KEY=<strong-random-key>         # Generate with: python -c "import secrets; print(secrets.token_hex(32))"

# Optional
LOG_LEVEL=INFO                         # DEBUG | INFO | WARNING | ERROR
MAX_WORKERS=4                          # Celery worker count
```

### Configuration Files

- `.env` - Local development (gitignored)
- `.env.staging` - Staging environment
- `.env.production` - Production environment

**Security Note:** Never commit `.env` files to version control. Use environment-specific files and secrets management (e.g., AWS Secrets Manager, Vault).

---

## Database Migration

### Migration 003: Add cost_status Column to facts Table

**Purpose:** Promote cost_status from JSON details column to dedicated indexed column for efficient querying.

**Impact:**
- Adds `cost_status` column (nullable, VARCHAR(20))
- Adds CHECK constraint for valid values
- Adds partial index (PostgreSQL) or full index (SQLite)
- Migrates existing data from JSON to column
- **Downtime:** None (nullable column, backward compatible)

### PostgreSQL (Production/Staging)

#### 1. Backup Database

```bash
# Create backup before migration
pg_dump -h <host> -U <user> -d <database> -F c -f backup_$(date +%Y%m%d_%H%M%S).dump

# Verify backup
pg_restore --list backup_*.dump | head -20
```

#### 2. Run Migration

```bash
# Via Alembic (recommended)
cd /path/to/it-diligence-agent
source venv/bin/activate
alembic upgrade head

# Via Flask-Migrate (alternative)
flask db upgrade

# Via init script (creates schema if needed)
python scripts/init_db.py
```

#### 3. Verify Migration

```sql
-- Connect to database
psql -h <host> -U <user> -d <database>

-- Check column exists
\d facts

-- Verify data migrated
SELECT cost_status, COUNT(*)
FROM facts
WHERE domain = 'applications'
GROUP BY cost_status;

-- Should show:
--   known           | (count)
--   unknown         | (count)
--   internal_no_cost| (count)
--   NULL            | (count)

-- Test partial index
EXPLAIN SELECT * FROM facts
WHERE cost_status = 'unknown' AND deleted_at IS NULL;
-- Should show "Index Scan using idx_facts_cost_status_unknown"
```

### SQLite (Local Development)

#### 1. Backup Database

```bash
# Copy database file
cp data/diligence.db data/diligence.db.backup.$(date +%Y%m%d_%H%M%S)
```

#### 2. Run Migration

```bash
# Via Flask app context
cd /path/to/it-diligence-agent
source venv/bin/activate

python -c "
from web.app import app, db
from flask_migrate import upgrade
with app.app_context():
    upgrade()
"

# Or via Alembic
alembic upgrade head
```

#### 3. Verify Migration

```bash
sqlite3 data/diligence.db

-- Check schema
.schema facts

-- Verify data
SELECT cost_status, COUNT(*)
FROM facts
WHERE domain = 'applications'
GROUP BY cost_status;

-- Exit
.quit
```

### Migration Idempotency

Migration 003 is idempotent - safe to run multiple times:
- Checks if column exists before creating
- Checks if indexes exist before creating
- Skips data migration if cost_status already populated

```bash
# Safe to run multiple times
alembic upgrade head
alembic upgrade head  # No-op if already at head
```

---

## Deployment Procedures

### Staging Deployment

#### 1. Pull Latest Code

```bash
ssh user@staging-server
cd /var/www/it-diligence-agent
git fetch origin
git checkout main
git pull origin main

# Verify commit
git log -1 --oneline
# Should show: "Fix organization schema: add 'entity' to optional fields"
```

#### 2. Update Dependencies

```bash
source venv/bin/activate
pip install -r requirements.txt --upgrade
```

#### 3. Run Database Migration

```bash
# Backup first
pg_dump -h localhost -U itdd_user -d itdd_staging -F c -f backup_staging_$(date +%Y%m%d_%H%M%S).dump

# Run migration
alembic upgrade head

# Verify
alembic current
# Should show: "003 (head)"
```

#### 4. Restart Services

```bash
# Restart Flask app
sudo systemctl restart itdd-web

# Restart Celery workers
sudo systemctl restart itdd-celery

# Check status
sudo systemctl status itdd-web
sudo systemctl status itdd-celery
```

#### 5. Run Smoke Tests

```bash
# Run P0 tests on staging
pytest tests/test_cost_status_p0_fixes.py -v
pytest tests/test_migration_003_sqlite.py -v

# Run full test suite (optional)
pytest tests/ -v --tb=short
```

### Production Deployment

**Timing:** Deploy during off-peak hours (e.g., 2-4 AM EST)

**Rollback Window:** Have 30 minutes available for rollback if issues occur

#### 1. Pre-Deployment

```bash
# Announce deployment to team
# Ensure all stakeholders are available
# Verify staging deployment successful

# Take final production backup
ssh user@prod-server
cd /var/www/it-diligence-agent
pg_dump -h prod-db -U itdd_user -d itdd_production -F c -f backup_prod_$(date +%Y%m%d_%H%M%S).dump

# Copy backup to safe location
scp backup_prod_*.dump backup-server:/backups/itdd/
```

#### 2. Deploy Code

```bash
ssh user@prod-server
cd /var/www/it-diligence-agent

# Fetch latest
git fetch origin
git checkout main
git pull origin main

# Verify commit hash matches staging
git log -1 --oneline

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt --upgrade
```

#### 3. Run Migration (Zero-Downtime)

**Note:** Migration adds nullable column, no downtime required

```bash
# Run migration
alembic upgrade head

# Verify immediately
alembic current
psql -h prod-db -U itdd_user -d itdd_production -c "SELECT cost_status, COUNT(*) FROM facts WHERE domain='applications' GROUP BY cost_status;"
```

#### 4. Restart Services (Rolling Restart)

```bash
# Restart web servers one at a time (if load balanced)
sudo systemctl restart itdd-web-1
sleep 30  # Wait for health check
sudo systemctl restart itdd-web-2
sleep 30
sudo systemctl restart itdd-web-3

# Restart Celery workers
sudo systemctl restart itdd-celery

# Verify all services healthy
sudo systemctl status itdd-web-*
sudo systemctl status itdd-celery
```

#### 5. Monitor Immediately Post-Deployment

- [ ] Check application logs: `tail -f /var/log/itdd/app.log`
- [ ] Check error rate in monitoring dashboard
- [ ] Verify API endpoints responding: `curl http://localhost:5001/api/health`
- [ ] Run sample pipeline test (see Verification section)

---

## Verification Steps

### Automated Tests

```bash
# On staging/production server
cd /var/www/it-diligence-agent
source venv/bin/activate

# Run P0 cost status tests
pytest tests/test_cost_status_p0_fixes.py -v
# Expected: 20 passed

# Run migration tests
pytest tests/test_migration_003_sqlite.py -v
# Expected: 3 passed

# Run schema validation
pytest tests/test_inventory_store.py::TestSchemas::test_id_fields_exist_in_schema -v
# Expected: 1 passed
```

### Database Verification

```sql
-- Connect to production database
psql -h prod-db -U itdd_user -d itdd_production

-- 1. Verify cost_status column exists
\d facts

-- 2. Check data distribution
SELECT cost_status, COUNT(*) as count,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) as percentage
FROM facts
WHERE domain = 'applications' AND deleted_at IS NULL
GROUP BY cost_status
ORDER BY count DESC;

-- Expected output (approximate):
--  cost_status      | count | percentage
-- ------------------+-------+------------
--  known            |  xxx  |  60-70%
--  unknown          |  xxx  |  15-25%
--  internal_no_cost |  xxx  |  5-15%
--  NULL             |  xxx  |  <5%

-- 3. Verify index is used
EXPLAIN SELECT * FROM facts
WHERE cost_status = 'unknown' AND deleted_at IS NULL;
-- Should show: "Index Scan using idx_facts_cost_status_unknown"

-- 4. Check for constraint violations
SELECT cost_status, COUNT(*)
FROM facts
WHERE cost_status NOT IN ('known', 'unknown', 'internal_no_cost', 'estimated')
  AND cost_status IS NOT NULL;
-- Should return 0 rows

-- Exit
\q
```

### Pipeline Test (End-to-End)

```bash
# Run a test pipeline on production
cd /var/www/it-diligence-agent
source venv/bin/activate

# Use test data
mkdir -p /tmp/pipeline-test-prod
cp data/input/Target_CloudServe_Document_2_Application_Inventory.md /tmp/pipeline-test-prod/

# Run pipeline
python main_v2.py /tmp/pipeline-test-prod/ --domain applications --target-name "ProdTest"

# Check output
cat output/runs/*/facts/facts.json | python3 -c "
import json, sys
from collections import Counter
data = json.load(sys.stdin)
statuses = [f['details'].get('cost_status', 'MISSING') for f in data['facts'] if f['domain']=='applications']
print('Cost status distribution:', dict(Counter(statuses)))
"

# Expected: {'known': X, 'internal_no_cost': Y, 'unknown': Z}
# At least 70% should have cost_status (known or internal_no_cost)
```

### UI Verification

1. **Login to Web UI:** http://production-domain.com
2. **Navigate to:** Deals → [Any Deal] → Inventory → Applications
3. **Verify cost_status visible** in application list
4. **Check cost quality metrics:** Should show breakdown by status
5. **Test VDR generation:** Should list apps with `cost_status = 'unknown'`

### API Verification

```bash
# Get cost quality metrics
curl -X GET http://localhost:5001/api/deals/{deal_id}/inventory?domain=applications \
  -H "Authorization: Bearer $API_TOKEN" | jq '.cost_quality'

# Expected response:
# {
#   "total_items": 51,
#   "items_with_cost": 39,
#   "percentage": 76.5,
#   "by_status": {
#     "known": 31,
#     "internal_no_cost": 8,
#     "unknown": 12
#   }
# }
```

---

## Rollback Procedures

### When to Rollback

Rollback immediately if ANY of these occur within 30 minutes of deployment:

- **Database errors:** Check constraint violations, query failures
- **Application errors:** 5xx error rate >1%, startup failures
- **Data corruption:** cost_status showing invalid values
- **Performance degradation:** Query latency >2x baseline

### Rollback Steps

#### 1. Rollback Code

```bash
ssh user@prod-server
cd /var/www/it-diligence-agent

# Rollback to previous commit
git log -5 --oneline  # Find commit before deployment
git checkout <previous-commit-hash>

# Restart services
sudo systemctl restart itdd-web
sudo systemctl restart itdd-celery
```

#### 2. Rollback Database Migration

```bash
# Downgrade one migration
alembic downgrade -1

# Verify rollback
alembic current
# Should show: "002" (previous version)

# Check cost_status removed
psql -h prod-db -U itdd_user -d itdd_production -c "\d facts"
# Should NOT show cost_status column

# Verify data preserved in JSON
psql -h prod-db -U itdd_user -d itdd_production -c "
SELECT details->>'cost_status' as cost_status, COUNT(*)
FROM facts
WHERE domain='applications'
GROUP BY details->>'cost_status';
"
# Should show cost_status values still in JSON details column
```

#### 3. Restore from Backup (If Needed)

**Only if migration rollback fails or data corruption detected**

```bash
# Stop all services
sudo systemctl stop itdd-web
sudo systemctl stop itdd-celery

# Restore database
pg_restore -h prod-db -U itdd_user -d itdd_production -c backup_prod_TIMESTAMP.dump

# Restart services
sudo systemctl start itdd-web
sudo systemctl start itdd-celery

# Verify
psql -h prod-db -U itdd_user -d itdd_production -c "SELECT COUNT(*) FROM facts;"
```

#### 4. Post-Rollback Verification

```bash
# Run tests
pytest tests/test_cost_status_p0_fixes.py -v

# Check application health
curl http://localhost:5001/api/health

# Monitor logs
tail -f /var/log/itdd/app.log
```

---

## Monitoring

### Metrics to Watch (First 24 Hours)

#### Application Metrics

- **Error Rate:** <0.5% (baseline)
- **Response Time:** p95 <500ms (baseline: 300ms)
- **API Success Rate:** >99%
- **Background Job Success Rate:** >95%

#### Database Metrics

- **Query Latency:** p95 <100ms (baseline: 50ms)
- **Connection Pool:** <80% utilization
- **Index Usage:** `idx_facts_cost_status_unknown` should show scans
- **Deadlocks:** 0 per hour

#### Business Metrics

- **Pipeline Runs:** Complete successfully
- **Cost Status Coverage:** >70% for applications domain
- **VDR Generation:** Lists apps with `unknown` cost status
- **Data Quality:** No constraint violations

### Log Locations

```bash
# Application logs
/var/log/itdd/app.log
/var/log/itdd/celery.log
/var/log/itdd/error.log

# Database logs (PostgreSQL)
/var/log/postgresql/postgresql-15-main.log

# Nginx/web server logs
/var/log/nginx/access.log
/var/log/nginx/error.log
```

### Key Log Patterns to Watch

```bash
# Check for constraint violations
grep "violates check constraint \"check_cost_status_values\"" /var/log/itdd/app.log

# Check for migration errors
grep "alembic.runtime.migration" /var/log/itdd/app.log

# Check for cost_status related errors
grep "cost_status" /var/log/itdd/error.log
```

### Alerting Rules

Set up alerts for:

1. **Error Rate >1% for 5 minutes:** Page on-call engineer
2. **Database connection errors >10 in 5 minutes:** Page DBA
3. **Pipeline failure rate >10%:** Alert product team
4. **CHECK constraint violations >0:** Page on-call engineer immediately

---

## Troubleshooting

### Issue: Migration Fails with "column already exists"

**Cause:** Migration run multiple times or partial previous migration

**Solution:**
```bash
# Check if column exists
psql -c "\d facts"

# If column exists and has data, mark migration as complete
alembic stamp head

# If column exists but empty, drop and re-run
psql -c "ALTER TABLE facts DROP COLUMN IF EXISTS cost_status;"
alembic upgrade head
```

### Issue: CHECK Constraint Violations

**Symptom:** `ERROR: new row for relation "facts" violates check constraint "check_cost_status_values"`

**Cause:** Application code trying to insert invalid cost_status value

**Solution:**
```bash
# Find invalid values
psql -c "SELECT DISTINCT cost_status FROM facts WHERE cost_status NOT IN ('known', 'unknown', 'internal_no_cost', 'estimated') AND cost_status IS NOT NULL;"

# Fix in code: utils/cost_status_inference.py
# Valid values: 'known', 'unknown', 'internal_no_cost', 'estimated'
```

### Issue: Query Performance Degraded

**Symptom:** Queries using cost_status are slow

**Solution:**
```bash
# Check if index exists
psql -c "\d facts"

# Check index usage
psql -c "EXPLAIN ANALYZE SELECT * FROM facts WHERE cost_status = 'unknown' AND deleted_at IS NULL;"

# Rebuild index if needed (PostgreSQL)
psql -c "REINDEX INDEX idx_facts_cost_status_unknown;"

# For SQLite, recreate index
sqlite3 data/diligence.db "DROP INDEX IF EXISTS idx_facts_cost_status_unknown;"
alembic upgrade head
```

### Issue: cost_status Not Populated

**Symptom:** All items show `cost_status = NULL` or `MISSING`

**Cause:** Shared utility not being called during fact creation

**Solution:**
```bash
# Verify shared utility is imported
grep "from utils.cost_status_inference import infer_cost_status" tools_v2/deterministic_parser.py
grep "from utils.cost_status_inference import infer_cost_status" tools_v2/discovery_tools.py

# Run manual fix script (if needed)
python scripts/backfill_cost_status.py --deal-id <deal_id>
```

### Issue: Alembic Version Chain Broken

**Symptom:** `KeyError: '001'` when running `alembic upgrade head`

**Cause:** Migration file revision IDs don't match alembic_version table

**Solution:**
```bash
# Check current version
alembic current

# Check alembic_version table
psql -c "SELECT * FROM alembic_version;"

# Manually set version to latest known good
psql -c "UPDATE alembic_version SET version_num = '003';"

# Verify
alembic current
```

---

## Post-Deployment Tasks

### Within 24 Hours

- [ ] Monitor error rates and performance metrics
- [ ] Review logs for any warnings or errors
- [ ] Verify cost_status coverage meets targets (>70%)
- [ ] Run full regression test suite on production
- [ ] Update team on deployment success

### Within 1 Week

- [ ] Analyze cost_status data quality
- [ ] Identify apps with `unknown` status for VDR requests
- [ ] Review database query performance
- [ ] Optimize indexes if needed
- [ ] Document any production-specific issues encountered

### Within 1 Month

- [ ] Address P1 findings from adversarial analysis
- [ ] Create monitoring dashboard for cost data quality
- [ ] Train team on new cost tracking features
- [ ] Review and update this deployment guide based on experience

---

## Support Contacts

- **On-Call Engineer:** [Contact info]
- **Database Admin:** [Contact info]
- **Product Owner:** [Contact info]
- **DevOps Team:** [Contact info]

## Related Documentation

- [P0_FIXES_SUMMARY.md](P0_FIXES_SUMMARY.md) - Technical details of P0 fixes
- [MIGRATION_FIX_SUMMARY.md](MIGRATION_FIX_SUMMARY.md) - SQLite compatibility fix
- [README.md](README.md) - General system documentation
- [CLAUDE.md](CLAUDE.md) - Developer guide

---

**Document Version:** 1.0
**Last Reviewed:** 2026-02-11
**Next Review:** 2026-03-11
