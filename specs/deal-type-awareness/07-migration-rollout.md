# Spec 07: Migration & Rollout Strategy

**Status**: GREENFIELD
**Priority**: P0
**Estimated Effort**: 2 hours
**Dependencies**: Specs 01-06 (All prior specs)

---

## Problem Statement

Rolling out deal type awareness affects:
- **572 existing tests** (must not break)
- **Existing deals in database** (may have NULL or default deal_type)
- **Production deployments** (zero-downtime requirement)
- **User workflows** (training and documentation needed)

**Challenge**: Deploy backward-compatible changes that enhance new deals while preserving existing deal analysis integrity.

---

## Migration Strategy

### Phase-Based Rollout

```
┌──────────────────────────────────────────────────────────────┐
│ PHASE 0: Pre-Flight Validation (Week 0)                     │
│ - Run all 572 existing tests                                │
│ - Snapshot current outputs for regression comparison        │
│ - Identify deals with NULL/invalid deal_type                │
└──────────────────────────────────────────────────────────────┘
                          ▼
┌──────────────────────────────────────────────────────────────┐
│ PHASE 1: Database Migration (Week 1)                        │
│ - Add CHECK constraint to deal_type                         │
│ - Backfill NULL values with 'acquisition'                   │
│ - Deploy migration to staging                               │
└──────────────────────────────────────────────────────────────┘
                          ▼
┌──────────────────────────────────────────────────────────────┐
│ PHASE 2: Code Deployment (Week 2)                           │
│ - Deploy conditional logic with defaults                    │
│ - Enable feature flag: DEAL_TYPE_AWARENESS=true             │
│ - Monitor logs for deal_type propagation                    │
└──────────────────────────────────────────────────────────────┘
                          ▼
┌──────────────────────────────────────────────────────────────┐
│ PHASE 3: UI Rollout (Week 3)                                │
│ - Deploy required deal_type field to UI                     │
│ - Add edit deal type functionality                          │
│ - Update user documentation                                 │
└──────────────────────────────────────────────────────────────┘
                          ▼
┌──────────────────────────────────────────────────────────────┐
│ PHASE 4: Validation & Cleanup (Week 4)                      │
│ - Run regression tests vs Phase 0 baseline                  │
│ - Remove feature flag (make permanent)                      │
│ - Archive old deals with corrected deal_type                │
└──────────────────────────────────────────────────────────────┘
```

---

## Phase 0: Pre-Flight Validation

### Objectives
- Establish baseline behavior BEFORE changes
- Identify existing data quality issues
- Ensure test suite is healthy

### Tasks

#### 1. Run Full Test Suite

```bash
cd "9.5/it-diligence-agent 2"
python -m pytest tests/ -v --cov --no-cov-on-fail > pre_migration_test_results.txt
```

**Success Criteria**: All 572 tests pass (or document known failures to exclude from regression comparison)

#### 2. Snapshot Existing Deal Outputs

**Script**: `scripts/snapshot_existing_deals.py` (NEW)

```python
"""
Snapshot existing deal outputs for regression comparison.

Captures:
- Cost estimates
- Synergy recommendations
- Narrative excerpts

For comparison after migration to ensure backward compatibility.
"""

import json
from web.database import Deal, db
from web.analysis_runner import run_reasoning_phase

def snapshot_deal_outputs():
    """Snapshot outputs for all existing deals."""
    deals = Deal.query.filter(Deal.status != 'deleted').all()

    snapshots = []

    for deal in deals:
        print(f"Snapshotting deal: {deal.name} (ID: {deal.id})")

        # Re-run reasoning phase
        try:
            result = run_reasoning_phase(deal_id=deal.id)

            snapshot = {
                'deal_id': deal.id,
                'deal_name': deal.name,
                'deal_type': deal.deal_type,
                'cost_total': result.get('cost_estimate', {}).get('total_cost'),
                'synergy_count': len(result.get('synergies', [])),
                'synergy_types': [s['type'] for s in result.get('synergies', [])],
                'narrative_excerpt': result.get('narrative', '')[:500]
            }

            snapshots.append(snapshot)

        except Exception as e:
            print(f"ERROR: Failed to snapshot {deal.name}: {e}")
            snapshots.append({
                'deal_id': deal.id,
                'deal_name': deal.name,
                'error': str(e)
            })

    # Save to file
    with open('data/pre_migration_snapshots.json', 'w') as f:
        json.dump(snapshots, f, indent=2)

    print(f"\nSnapshotted {len(snapshots)} deals")
    print(f"Saved to: data/pre_migration_snapshots.json")

if __name__ == '__main__':
    snapshot_deal_outputs()
```

**Run**:
```bash
python scripts/snapshot_existing_deals.py
```

#### 3. Audit Existing deal_type Values

**Script**: `scripts/audit_deal_types.py` (NEW)

```python
"""
Audit existing deal_type values in database.

Reports:
- NULL deal_type count
- Invalid deal_type values
- Deal type distribution
"""

from web.database import Deal, db
from collections import Counter

def audit_deal_types():
    """Audit deal_type field across all deals."""
    deals = Deal.query.all()

    null_count = sum(1 for d in deals if d.deal_type is None)
    invalid_count = sum(1 for d in deals if d.deal_type not in ['acquisition', 'carveout', 'divestiture', None])

    deal_type_dist = Counter(d.deal_type for d in deals)

    print(f"Total deals: {len(deals)}")
    print(f"NULL deal_type: {null_count}")
    print(f"Invalid deal_type: {invalid_count}")
    print(f"\nDistribution:")
    for deal_type, count in deal_type_dist.items():
        print(f"  {deal_type or 'NULL'}: {count}")

    # List invalid deals
    if invalid_count > 0:
        print(f"\nInvalid deal_type values:")
        invalid_deals = [d for d in deals if d.deal_type not in ['acquisition', 'carveout', 'divestiture', None]]
        for deal in invalid_deals:
            print(f"  - {deal.name} (ID: {deal.id}): deal_type={deal.deal_type}")

if __name__ == '__main__':
    audit_deal_types()
```

**Run**:
```bash
python scripts/audit_deal_types.py
```

---

## Phase 1: Database Migration

### Objectives
- Add NOT NULL constraint to deal_type
- Add CHECK constraint for valid values
- Backfill existing NULL values

### Migration Script

**File**: `migrations/versions/20250215_deal_type_constraints.py` (NEW)

```python
"""
Add deal_type constraints and backfill NULL values.

Revision ID: 20250215_dealtype
Revises: <previous_revision>
Create Date: 2025-02-15
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

def upgrade():
    """Apply deal_type constraints."""

    # Step 1: Backfill NULL values with 'acquisition' (safe default)
    print("Backfilling NULL deal_type values...")
    op.execute(text("""
        UPDATE deals
        SET deal_type = 'acquisition'
        WHERE deal_type IS NULL
    """))

    # Step 2: Fix any invalid values (anything not in valid set)
    print("Fixing invalid deal_type values...")
    op.execute(text("""
        UPDATE deals
        SET deal_type = 'acquisition'
        WHERE deal_type NOT IN ('acquisition', 'carveout', 'divestiture')
    """))

    # Step 3: Add NOT NULL constraint
    print("Adding NOT NULL constraint...")
    op.alter_column('deals', 'deal_type',
                    existing_type=sa.String(50),
                    nullable=False,
                    existing_nullable=True)

    # Step 4: Add CHECK constraint for valid values
    print("Adding CHECK constraint...")
    op.create_check_constraint(
        'valid_deal_type',
        'deals',
        "deal_type IN ('acquisition', 'carveout', 'divestiture')"
    )

    print("Migration complete!")

def downgrade():
    """Rollback deal_type constraints."""
    op.drop_constraint('valid_deal_type', 'deals', type_='check')
    op.alter_column('deals', 'deal_type',
                    existing_type=sa.String(50),
                    nullable=True,
                    existing_nullable=False)
```

### Deployment Steps

```bash
# 1. Backup database
pg_dump diligence_prod > backup_pre_deal_type_migration.sql

# 2. Run migration on staging
export FLASK_ENV=staging
flask db upgrade

# 3. Verify constraints applied
psql diligence_staging -c "\d deals"
# Should show:
#   deal_type | character varying(50) | not null
#   Check constraints:
#     "valid_deal_type" CHECK (deal_type IN ('acquisition', 'carveout', 'divestiture'))

# 4. Test insert with invalid deal_type (should fail)
psql diligence_staging -c "INSERT INTO deals (name, target_name, deal_type) VALUES ('Test', 'Target', 'merger');"
# Expected: ERROR: check constraint "valid_deal_type" violated

# 5. Deploy to production (during maintenance window)
export FLASK_ENV=production
flask db upgrade
```

---

## Phase 2: Code Deployment with Feature Flag

### Objectives
- Deploy new code with deal_type awareness
- Use feature flag to enable/disable new behavior
- Monitor logs for issues

### Feature Flag Implementation

**File**: `config_v2.py` (UPDATE)

```python
# Feature Flags
DEAL_TYPE_AWARENESS_ENABLED = os.getenv('DEAL_TYPE_AWARENESS', 'true').lower() == 'true'
```

**File**: `web/blueprints/costs.py` (UPDATE)

```python
from config_v2 import DEAL_TYPE_AWARENESS_ENABLED

def _identify_synergies(inv_store: InventoryStore, deal_type: str = "acquisition"):
    """
    Identify synergies or separation costs based on deal type.

    Feature-flagged for safe rollout.
    """
    if not DEAL_TYPE_AWARENESS_ENABLED:
        # Fallback to old behavior (always consolidation)
        return _calculate_consolidation_synergies(inv_store)

    # New behavior: branch by deal_type
    if deal_type in ['carveout', 'divestiture']:
        return _calculate_separation_costs(inv_store, deal_type)
    else:
        return _calculate_consolidation_synergies(inv_store)
```

### Deployment Steps

```bash
# 1. Deploy code to staging with feature flag ENABLED
export DEAL_TYPE_AWARENESS=true
gunicorn web.app:app --reload

# 2. Run smoke tests
python -m pytest tests/integration/test_deal_type_cost_flow.py -v

# 3. Monitor logs for deal_type propagation
tail -f logs/app.log | grep "deal_type"

# 4. Deploy to production with feature flag ENABLED
# (No code changes needed, just restart app with env var)
export DEAL_TYPE_AWARENESS=true
systemctl restart diligence-web

# 5. Monitor production for 24 hours
# If issues arise, disable feature flag instantly:
export DEAL_TYPE_AWARENESS=false
systemctl restart diligence-web
```

---

## Phase 3: UI Rollout

### Objectives
- Make deal_type selection required in UI
- Add deal type edit functionality
- Deploy user documentation

### Deployment Steps

```bash
# 1. Deploy updated templates to staging
rsync -av web/templates/ staging:/app/web/templates/

# 2. Deploy updated JavaScript
rsync -av web/static/js/ staging:/app/web/static/js/

# 3. Restart staging app
ssh staging "systemctl restart diligence-web"

# 4. Manual testing checklist:
#    - [ ] Create new deal → deal_type required
#    - [ ] Edit existing deal → can change deal_type
#    - [ ] Create acquisition → see consolidation recommendations
#    - [ ] Create carve-out → see separation costs
#    - [ ] Check cost report → TSA costs for carve-out only

# 5. Deploy to production
rsync -av web/templates/ production:/app/web/templates/
rsync -av web/static/js/ production:/app/web/static/js/
ssh production "systemctl restart diligence-web"
```

### User Communication

**Email Template** (send to all users):

```
Subject: New Feature: Deal Type Selection for Accurate Recommendations

Hi [User],

We've enhanced the IT Due Diligence Agent with deal type awareness!

What's New:
✅ When creating a deal, you now select the deal type:
   - Acquisition (Integration)
   - Carve-Out (Separation from Parent)
   - Divestiture (Clean Separation)

Why This Matters:
The system now provides recommendations tailored to your specific deal structure:
- Acquisitions → consolidation synergies (merge systems)
- Carve-Outs → separation costs & TSA exposure (build standalone)
- Divestitures → extraction costs (untangle from parent)

Action Required:
1. Review your existing deals
2. Edit deal type if needed (see updated user guide)
3. Re-run analysis to get updated recommendations

Questions? See the updated user guide: [link]

Thanks,
IT DD Team
```

---

## Phase 4: Validation & Cleanup

### Objectives
- Compare post-migration outputs to baseline
- Remove feature flag (make permanent)
- Document migration results

### Regression Validation

**Script**: `scripts/compare_snapshots.py` (NEW)

```python
"""
Compare post-migration outputs to pre-migration baseline.

Validates that acquisition deals produce SAME outputs after migration.
"""

import json

def compare_snapshots():
    """Compare pre/post migration snapshots."""

    with open('data/pre_migration_snapshots.json') as f:
        pre = json.load(f)

    with open('data/post_migration_snapshots.json') as f:
        post = json.load(f)

    # Build lookup by deal_id
    pre_map = {s['deal_id']: s for s in pre}
    post_map = {s['deal_id']: s for s in post}

    regressions = []

    for deal_id, pre_snap in pre_map.items():
        post_snap = post_map.get(deal_id)

        if not post_snap:
            print(f"WARNING: Deal {deal_id} missing from post-migration snapshot")
            continue

        # For acquisition deals, outputs should be IDENTICAL
        if pre_snap['deal_type'] == 'acquisition':
            # Allow 5% cost variation (due to rounding)
            cost_diff_pct = abs(post_snap['cost_total'] - pre_snap['cost_total']) / pre_snap['cost_total']

            if cost_diff_pct > 0.05:
                regressions.append({
                    'deal_id': deal_id,
                    'deal_name': pre_snap['deal_name'],
                    'issue': 'cost_changed',
                    'pre_cost': pre_snap['cost_total'],
                    'post_cost': post_snap['cost_total'],
                    'diff_pct': cost_diff_pct * 100
                })

            # Synergy count should match
            if post_snap['synergy_count'] != pre_snap['synergy_count']:
                regressions.append({
                    'deal_id': deal_id,
                    'deal_name': pre_snap['deal_name'],
                    'issue': 'synergy_count_changed',
                    'pre_count': pre_snap['synergy_count'],
                    'post_count': post_snap['synergy_count']
                })

    if regressions:
        print(f"⚠️ REGRESSIONS DETECTED: {len(regressions)}")
        for reg in regressions:
            print(f"  - {reg['deal_name']}: {reg['issue']}")
        return False
    else:
        print("✅ NO REGRESSIONS: All acquisition deals match baseline")
        return True

if __name__ == '__main__':
    success = compare_snapshots()
    exit(0 if success else 1)
```

**Run**:
```bash
# 1. Capture post-migration snapshots
python scripts/snapshot_existing_deals.py  # Saves to post_migration_snapshots.json

# 2. Compare to baseline
python scripts/compare_snapshots.py

# 3. If regressions found, investigate and fix
# 4. If clean, proceed to cleanup
```

### Remove Feature Flag

Once validated, remove the feature flag and make deal_type awareness permanent:

**File**: `config_v2.py` (UPDATE)

```python
# REMOVE THIS:
# DEAL_TYPE_AWARENESS_ENABLED = os.getenv('DEAL_TYPE_AWARENESS', 'true').lower() == 'true'

# (Feature is now always enabled)
```

**File**: `web/blueprints/costs.py` (UPDATE)

```python
# REMOVE THIS:
# if not DEAL_TYPE_AWARENESS_ENABLED:
#     return _calculate_consolidation_synergies(inv_store)

# New code (no flag check):
def _identify_synergies(inv_store: InventoryStore, deal_type: str = "acquisition"):
    """Identify synergies or separation costs based on deal type."""
    if deal_type in ['carveout', 'divestiture']:
        return _calculate_separation_costs(inv_store, deal_type)
    else:
        return _calculate_consolidation_synergies(inv_store)
```

---

## Backward Compatibility Guarantees

### 1. Existing Acquisition Deals

**Guarantee**: All existing deals with `deal_type='acquisition'` produce IDENTICAL outputs post-migration.

**Validation**: Regression tests comparing pre/post snapshots with max 5% cost variance allowed.

### 2. NULL deal_type Handling

**Guarantee**: All NULL `deal_type` values are backfilled to `'acquisition'` (safe default).

**Rationale**: Existing deals were analyzed with consolidation logic, so `'acquisition'` preserves that behavior.

### 3. API Backward Compatibility

**Guarantee**: API calls that omit `deal_type` default to `'acquisition'`.

**Example**:
```python
# Old API call (no deal_type) - STILL WORKS
POST /api/v1/deals
{
  "name": "Test Deal",
  "target_name": "Target"
}
# Defaults to deal_type='acquisition'

# New API call (explicit deal_type) - ALSO WORKS
POST /api/v1/deals
{
  "name": "Test Deal",
  "target_name": "Target",
  "deal_type": "carveout"
}
```

### 4. Function Signature Compatibility

**Guarantee**: All functions accept `deal_type` as OPTIONAL parameter with `default='acquisition'`.

**Example**:
```python
# Old call (no deal_type) - STILL WORKS
cost = calculate_costs(work_items, inv_store)

# New call (explicit deal_type) - ALSO WORKS
cost = calculate_costs(work_items, inv_store, deal_type='carveout')
```

---

## Rollback Plan

If critical issues arise post-deployment:

### Immediate Rollback (Feature Flag)

```bash
# Disable feature flag (keeps new code deployed but reverts to old behavior)
export DEAL_TYPE_AWARENESS=false
systemctl restart diligence-web

# System reverts to always using consolidation logic
```

### Full Rollback (Code + Database)

```bash
# 1. Rollback code deployment
git revert <commit_hash>
git push origin main
systemctl restart diligence-web

# 2. Rollback database migration
flask db downgrade -1

# 3. Restore from backup (if needed)
pg_restore -d diligence_prod backup_pre_deal_type_migration.sql
```

### Rollback Decision Tree

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

---

## Success Criteria

- [ ] All 572 existing tests still pass post-migration
- [ ] Pre/post migration snapshots match for acquisition deals (±5% cost variance)
- [ ] Database constraints applied: NOT NULL + CHECK on deal_type
- [ ] Feature flag successfully controls new behavior
- [ ] UI requires deal_type selection for new deals
- [ ] Zero production incidents during rollout
- [ ] User documentation updated and distributed
- [ ] Rollback plan tested in staging environment

---

## Monitoring & Observability

### Metrics to Track

| Metric | Threshold | Alert If |
|--------|-----------|----------|
| Deal creation failures | <1% | >5% fail due to deal_type validation |
| Cost calculation errors | 0 | Any deal_type-related exception |
| Regression test failures | 0 | Any pre/post snapshot mismatch |
| Feature flag usage | 100% enabled after Week 4 | Still using flag after cleanup |
| User support tickets | <5/week | >20 tickets about deal_type confusion |

### Logging

**Add structured logging** to track deal_type propagation:

```python
import logging
logger = logging.getLogger(__name__)

def calculate_costs(work_items, inv_store, deal_type='acquisition'):
    logger.info(f"Cost calculation: deal_type={deal_type}, work_item_count={len(work_items)}")
    # ... calculation logic ...
    logger.info(f"Cost result: total=${total_cost}, multiplier_applied={multiplier}")
```

**Query logs** to verify deal_type is propagating:

```bash
# Count cost calculations by deal_type
cat logs/app.log | grep "Cost calculation" | grep -oP 'deal_type=\w+' | sort | uniq -c

# Expected output:
#   250 deal_type=acquisition
#    45 deal_type=carveout
#    12 deal_type=divestiture
```

---

## Training & Documentation

### User Guide Updates

**File**: `docs/user_guide/creating_deals.md` (UPDATE - already covered in Spec 05)

### Developer Onboarding

**File**: `docs/developer/deal_type_system.md` (NEW)

```markdown
# Deal Type System - Developer Guide

## Overview
The deal type system branches analysis logic based on deal structure:
- **Acquisition**: Consolidation synergies, integration focus
- **Carve-Out**: Separation costs, TSA exposure, standalone build-out
- **Divestiture**: Extraction costs, untangling from parent

## Key Decision Points

### When adding new analysis logic, check deal_type:

```python
# WRONG: Always recommending consolidation
def analyze_infrastructure(facts):
    return "Recommend consolidating target datacenter to buyer AWS"

# RIGHT: Conditional on deal_type
def analyze_infrastructure(facts, deal_type):
    if deal_type == 'acquisition':
        return "Recommend consolidating target datacenter to buyer AWS"
    elif deal_type == 'carveout':
        return "Build standalone AWS environment for target (no consolidation)"
    else:
        return "Extract target from parent datacenter"
```

### Testing Checklist
When modifying any analysis component:
- [ ] Test with `deal_type='acquisition'`
- [ ] Test with `deal_type='carveout'`
- [ ] Test with `deal_type='divestiture'`
- [ ] Verify outputs differ appropriately per deal type
```

---

## Post-Migration Audit

**Run 30 days after Phase 4 completion**:

### Audit Checklist

- [ ] All deals have valid deal_type (acquisition, carveout, or divestiture)
- [ ] No NULL deal_type values in database
- [ ] Cost estimates for carve-outs are 1.5-3x higher than comparable acquisitions
- [ ] TSA costs appear ONLY for carve-outs, not acquisitions
- [ ] User support tickets about deal_type <5/week
- [ ] No rollbacks or feature flag toggles in past 30 days
- [ ] Regression test suite passes 100%
- [ ] User guide reflects deal_type selection process

---

## Timeline Summary

| Week | Phase | Effort | Status |
|------|-------|--------|--------|
| 0 | Pre-Flight Validation | 4 hours | Not started |
| 1 | Database Migration | 2 hours | Not started |
| 2 | Code Deployment | 3 hours | Not started |
| 3 | UI Rollout | 2 hours | Not started |
| 4 | Validation & Cleanup | 3 hours | Not started |
| **Total** | **Full Rollout** | **14 hours** | **Not started** |

**Critical Path**: Database migration must complete before code deployment. UI rollout can run in parallel with code deployment.

---

## Files Created/Modified

| File | Type | Lines | Purpose |
|------|------|-------|---------|
| `migrations/versions/20250215_deal_type_constraints.py` | New | 60 | Database migration |
| `scripts/snapshot_existing_deals.py` | New | 80 | Pre/post comparison |
| `scripts/audit_deal_types.py` | New | 50 | Data quality audit |
| `scripts/compare_snapshots.py` | New | 100 | Regression validation |
| `config_v2.py` | Update | +5 | Feature flag |
| `web/blueprints/costs.py` | Update | +10 | Feature flag check |
| `docs/developer/deal_type_system.md` | New | 50 | Developer guide |

**Total**: ~355 lines

---

## Dependencies

**Depends On**:
- Spec 01: Deal Type Architecture
- Spec 02: Synergy Engine Conditional Logic
- Spec 03: Reasoning Prompt Conditioning
- Spec 04: Cost Engine Deal Awareness
- Spec 05: UI Validation Enforcement
- Spec 06: Testing & Validation

**Blocks**: Nothing (this is the final spec)

---

## Estimated Effort

- **Pre-flight validation**: 4 hours
- **Database migration development**: 1 hour
- **Database migration deployment**: 1 hour
- **Code deployment with feature flag**: 2 hours
- **UI rollout**: 2 hours
- **Post-migration validation**: 2 hours
- **Documentation**: 2 hours
- **Total**: 14 hours (spread over 4 weeks)

---

**This completes the migration and rollout specification. The system is now ready for safe, phased deployment with backward compatibility guarantees and rollback capabilities.**
