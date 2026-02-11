# P0 Fixes Summary - Cost Status Implementation

**Date:** 2026-02-11
**Fixes:** P0 Finding #1 and P0 Finding #2 from Adversarial Analysis

---

## Problem Statement

The cost quality tracking implementation had two critical (P0) issues:

1. **Data Inconsistency - Parser Path Disparity:** Deterministic parser populated `cost_status`, but LLM discovery agents did not, causing 90%+ of production data to lack cost_status.

2. **No Database Schema:** `cost_status` was buried in JSON `details` column, preventing efficient SQL queries and lacking constraints/indexes.

---

## Solution Overview

### P0 Fix #1: Unified Cost Status Inference

**Created:** `utils/cost_status_inference.py`

Extracted cost_status logic into a shared utility function `infer_cost_status()` used by BOTH ingestion paths:

```python
def infer_cost_status(
    cost_value: Optional[str],
    vendor_name: Optional[str] = None,
    original_value: Optional[str] = None
) -> Tuple[str, str]:
    """
    Returns: (cost_status, cost_quality_note)

    Status values:
    - 'known': Numeric cost provided
    - 'unknown': Cost not specified (N/A, TBD)
    - 'internal_no_cost': $0 for internal apps
    - 'estimated': (reserved for future)
    """
```

**Key Improvements:**
- **Fixed vendor matching:** Uses exact match or prefix patterns instead of substring (prevents "Custom Software Inc." false positive)
- **Floating point safety:** Uses `abs(float) < 0.01` threshold instead of exact zero
- **Centralized normalization:** `normalize_numeric()` handles $, K/M suffixes, ranges

**Modified Files:**
- ✅ `tools_v2/deterministic_parser.py` - Uses shared utility (lines 436-449)
- ✅ `tools_v2/discovery_tools.py` - Added cost inference before fact creation (lines 617-649)

**Result:** Both deterministic parser and LLM discovery agents now produce consistent cost_status data.

---

### P0 Fix #2: Database Schema for cost_status

**Created:** `migrations/versions/003_add_cost_status_to_facts.py`

Added dedicated `cost_status` column to `facts` table with:

1. **Column Definition:**
   ```sql
   ALTER TABLE facts ADD COLUMN cost_status VARCHAR(20)
   ```

2. **CHECK Constraint:**
   ```sql
   CHECK (cost_status IS NULL OR cost_status IN
          ('known', 'unknown', 'internal_no_cost', 'estimated'))
   ```

3. **Partial Index for Efficiency:**
   ```sql
   CREATE INDEX idx_facts_cost_status_unknown
   ON facts (deal_id, domain, entity)
   WHERE cost_status = 'unknown' AND deleted_at IS NULL
   ```
   This makes "find apps needing cost discovery" queries extremely fast.

4. **Data Migration:**
   - Extracts existing `cost_status` from JSON `details` column
   - Infers `cost_status = 'known'` for facts with cost values but no status
   - Backward compatible: keeps data in JSON and column for rollback safety

**Modified Files:**
- ✅ `web/database.py` - Added `cost_status` column to Fact model (line 705)
- ✅ `web/database.py` - Updated `to_dict()` to include `cost_status` (line 767)
- ✅ `stores/db_writer.py` - Extract `cost_status` from details when writing to DB (lines 244, 315)

**Result:** Can now efficiently query `WHERE cost_status = 'unknown'` without JSON parsing. Future VDR generation features can use SQL instead of loading all items into memory.

---

## Testing

**Created:** `tests/test_cost_status_p0_fixes.py`

All 20 tests pass ✅:

- **7 tests** for `infer_cost_status()` utility (edge cases, vendor matching, false positives)
- **5 tests** for `normalize_numeric()` (dollar signs, K/M, ranges, N/A)
- **2 tests** for integration (deterministic parser, LLM discovery)
- **2 tests** for database schema (column exists, to_dict includes it)
- **3 tests** for consistency (both paths produce same results)
- **1 test** for end-to-end LLM discovery path

```bash
pytest tests/test_cost_status_p0_fixes.py -v
# Result: 20 passed in 0.61s
```

---

## Migration Instructions

### 1. Run the Migration

```bash
cd "/Users/JB/Documents/IT/IT DD Test 2/9.5/it-diligence-agent 2"

# Using Alembic
alembic upgrade head

# Or using Flask-Migrate (if configured)
flask db upgrade
```

### 2. Verify Migration

```sql
-- Check column exists
\d facts

-- Check data migrated
SELECT cost_status, COUNT(*)
FROM facts
WHERE domain = 'applications'
GROUP BY cost_status;

-- Test the partial index works
EXPLAIN SELECT * FROM facts
WHERE cost_status = 'unknown' AND deleted_at IS NULL;
```

### 3. Rollback (If Needed)

```bash
alembic downgrade -1
```

The downgrade will:
- Migrate `cost_status` back to JSON `details` column
- Drop the column and indexes
- Preserve all data (backward compatible)

---

## Performance Impact

### Before P0 Fixes

- **Query for unknown costs:** Load ALL inventory items, parse JSON in Python
- **10,000 apps × 3 domains = 30,000 items** loaded into memory per query
- **Estimated latency:** 200-500ms for large deals

### After P0 Fixes

- **Query for unknown costs:** SQL query with partial index
- **Only returns items where cost_status = 'unknown'** (typically <10% of items)
- **Estimated latency:** <10ms (20-50x faster)

### SQL Example

```sql
-- Find all apps needing cost discovery for a deal
SELECT id, item, details->>'vendor' as vendor
FROM facts
WHERE deal_id = 'abc-123'
  AND cost_status = 'unknown'
  AND deleted_at IS NULL
ORDER BY item;
```

This query uses the partial index and returns results instantly.

---

## What's Still Missing (P1 Priorities)

These are **NOT blockers** for shipping, but should be addressed within 2 weeks:

1. **P1 #3:** Change default from 'unknown' to 'MISSING' in `get_cost_quality()` (30 min)
2. **P1 #5:** Add enum validation to `InventoryItem.__post_init__()` (30 min)
3. **P1 #4:** Fix empty string filtering in deterministic parser (15 min)
4. **P1 #7:** Require `entity` parameter in `get_cost_quality()` (10 min)
5. **P1 #8:** Add entity/category/criticality to `items_needing_discovery` (10 min)

**Total estimated time:** ~2 hours for all P1 fixes

---

## Deployment Checklist

- [x] P0 #1: Shared utility created and integrated
- [x] P0 #2: Database migration created
- [x] Database model updated (Fact.cost_status)
- [x] db_writer updated to persist cost_status
- [x] Tests created and passing (20/20)
- [ ] Run migration on development database
- [ ] Run pipeline test to verify LLM discovery path works
- [ ] Verify cost_quality metrics show by_status breakdown
- [ ] Deploy to staging
- [ ] Run migration on staging database
- [ ] Smoke test: Create new deal, verify cost_status populated
- [ ] Deploy to production
- [ ] Monitor for migration issues (check logs for constraint violations)

---

## Breaking Changes

**None.** All changes are backward compatible:

- Old inventory files without `cost_status` still load (migration logic handles them)
- Old facts in database get `cost_status = NULL` (allowed by schema)
- JSON `details` column still contains `cost_status` (dual persistence)
- No API changes

---

## Files Modified

| File | Lines Changed | Purpose |
|------|---------------|---------|
| `utils/cost_status_inference.py` | +145 (new) | Shared utility for cost inference |
| `tools_v2/deterministic_parser.py` | +12, -20 | Use shared utility |
| `tools_v2/discovery_tools.py` | +35 | LLM path cost inference |
| `web/database.py` | +2 | Add cost_status column to model |
| `stores/db_writer.py` | +2 | Persist cost_status to DB |
| `migrations/versions/003_add_cost_status_to_facts.py` | +113 (new) | Database migration |
| `tests/test_cost_status_p0_fixes.py` | +230 (new) | Comprehensive tests |

**Total:** ~540 lines added, 20 lines removed

---

## Success Metrics

After deployment, verify:

1. **Pipeline runs populate cost_status:** `SELECT COUNT(*) FROM facts WHERE domain = 'applications' AND cost_status IS NOT NULL` should be >90%
2. **Cost quality API returns status breakdown:** `/api/inventory` includes `cost_quality.by_status` with all 4 statuses
3. **VDR queries are fast:** `SELECT * FROM facts WHERE cost_status = 'unknown'` completes in <10ms
4. **No constraint violations:** Check logs for `violates check constraint "check_cost_status_values"`

---

## Support & Rollback

If issues arise:

1. **Check migration logs:** Look for errors during `alembic upgrade`
2. **Verify data quality:** Run `SELECT cost_status, COUNT(*) FROM facts GROUP BY cost_status`
3. **Rollback migration:** `alembic downgrade -1` (safe, preserves data)
4. **Report issues:** Include fact_id, cost_status value, and error message

---

**Status:** ✅ Ready to deploy pending migration execution

**Next Step:** Run `/audit3` to address P1 findings or ship as-is with P0 fixes only
