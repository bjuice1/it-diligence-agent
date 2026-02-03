# Database Architecture Audit - Updated Review

**Date:** 2026-02-02 (Updated - Session 2)
**Status:** SIGNIFICANT PROGRESS - Final Stretch
**Previous Issues:** 10 identified
**Issues Fixed:** 6 fully, 2 partially

---

## Executive Summary

Major progress has been made on the Phase 2 database-first migration:

| Issue | Previous Status | Current Status |
|-------|-----------------|----------------|
| Cost Center bypass | CRITICAL | **FIXED** |
| Route migration gap | 72 `get_session()` calls | **Reduced to ~36 direct uses** |
| Risks/Work Items routes | Session-only | **MIGRATED to database** |
| Export routes | Session-only | **MIGRATED to database (11 routes)** |
| Review routes | Session-only | **MIGRATED to database (4 routes)** |
| DealData pagination | Limited | **ENHANCED** (domain, phase, severity ordering) |

**Remaining Work:**
- ~36 routes still use `get_session()` (mostly document management & organization)
- No orphan migration script created
- Adapters still present (maintenance burden)
- Document management routes intentionally use DocumentRegistry (file-based)

---

## FIXED: Issue #5 - Cost Center Blueprint

**Previous:** Cost Center imported `get_session()` and ignored database entirely.

**Current:** Now uses `DealData` and `load_deal_context`:

```python
# _gather_headcount_costs() - FIXED
from web.deal_data import get_deal_data
from web.context import load_deal_context

load_deal_context(current_deal_id)
data = get_deal_data()
org_facts = data.get_organization()
```

```python
# _gather_one_time_costs() - FIXED
load_deal_context(current_deal_id)
data = get_deal_data()
work_items = data.get_work_items()
```

**Verdict:** Issue resolved. Cost Center now reads from database.

---

## FIXED: Risks and Work Items Routes Migrated

**Previous:** `/risks` and `/work_items` used `get_session()` only.

**Current:** Both routes now use database-first pattern:

```python
# risks() route - FIXED
from web.deal_data import DealData
from web.context import load_deal_context

load_deal_context(current_deal_id)
data = DealData()

# Get from database with filtering
risks, total = data.get_findings_paginated(
    finding_type='risk',
    severity=severity_filter or None,
    domain=domain_filter or None,
    search=search_query or None,
    page=page,
    per_page=per_page,
    order_by_severity=True
)
```

**Verdict:** Core finding routes migrated.

---

## FIXED: FindingRepository Enhanced

**Previous:** `get_paginated` had limited filtering.

**Current:** Added:
- `domain` parameter for domain filtering
- `phase` parameter for work item phase filtering
- `order_by_severity` for risk ordering (critical > high > medium > low)

```python
def get_paginated(
    self,
    deal_id: str,
    run_id: str = None,
    finding_type: str = None,
    domain: str = None,        # NEW
    severity: str = None,
    phase: str = None,         # NEW
    search: str = None,
    page: int = 1,
    per_page: int = 50,
    include_orphaned: bool = True,
    order_by_severity: bool = False  # NEW
):
```

**Verdict:** Repository now supports full filtering needs.

---

## FIXED: DealData Facade Enhanced

**Previous:** Limited pagination parameters.

**Current:** `get_findings_paginated` now supports all filter options:

```python
def get_findings_paginated(
    self,
    finding_type: str = None,
    domain: str = None,
    severity: str = None,
    phase: str = None,
    search: str = None,
    page: int = 1,
    per_page: int = 50,
    order_by_severity: bool = False
) -> Tuple[List, int]:
```

**Verdict:** DealData facade now matches route needs.

---

## NEWLY MIGRATED: Export Routes (11 routes)

All export routes now use database-first pattern:

| Route | Status |
|-------|--------|
| `/export-vdr` | **MIGRATED** |
| `/export` POST | **MIGRATED** |
| `/api/export/json` | **MIGRATED** |
| `/api/export/excel` | **MIGRATED** |
| `/api/export/dossiers/<domain>` | **MIGRATED** |
| `/api/export/inventory/<domain>` | **MIGRATED** |
| `/api/export/work-items` | **MIGRATED** |
| `/api/export/risks` | **MIGRATED** |
| `/api/export/vdr-requests` | **MIGRATED** |
| `/api/export/executive-summary` | **MIGRATED** |
| `/exports` page | **MIGRATED** |

---

## NEWLY MIGRATED: Review & Validation Routes (4 routes)

| Route | Status |
|-------|--------|
| `/review` | **MIGRATED** |
| `/api/review/queue` | **MIGRATED** |
| `/api/review/stats` | **MIGRATED** |
| `/api/review/export-report` | **MIGRATED** |

---

## NEWLY MIGRATED: Other Core Routes (6 routes)

| Route | Status |
|-------|--------|
| `/context` | **MIGRATED** (uses Deal.context JSON field) |
| `/facts` | **MIGRATED** (removed fallback) |
| `/api/facts` | **MIGRATED** (removed fallback) |
| `/api/entity-summary` | **MIGRATED** |
| `/api/session/info` | **MIGRATED** |
| `/search` | Previously migrated |

---

## REMAINING: ~36 Routes Still Use get_session() Directly

**Severity: LOW** (reduced from MEDIUM)

Routes still using session without database:

| Category | Routes | Notes |
|----------|--------|-------|
| Document mgmt | `documents_page()`, `api_documents()`, etc. | Uses DocumentRegistry (file-based) |
| Organization | `organization_overview()`, `staffing()`, etc. | Uses analysis bridge functions |
| Narrative gen | `generate_narrative()`, etc. | LLM generation from session data |
| Legacy API | `session_info()` partial | Some legacy endpoints |

**Count:** ~36 direct `s = get_session()` calls remain

**Impact:**
- Document management intentionally file-based (DocumentRegistry)
- Organization module uses bridge functions that expect session stores
- Most user-facing routes now database-first

---

## REMAINING: No Orphan Migration Script

**Severity: MEDIUM**

The `include_orphaned=True` parameter is still the default in all repositories. No migration script was created to associate orphaned records with their appropriate runs.

**Current Behavior:**
```python
# Still in all repositories
if run_id:
    if include_orphaned:  # Default: True
        query = query.filter(
            or_(
                Fact.analysis_run_id == run_id,
                Fact.analysis_run_id.is_(None)  # Always included
            )
        )
```

**Recommendation:** Create `scripts/migrate_orphaned_data.py` to:
1. Find all records with `analysis_run_id IS NULL`
2. Associate them with appropriate run based on `created_at` timestamp
3. Or create a "legacy" synthetic run for pre-migration data

---

## REMAINING: Adapter Classes Still Present

**Severity: LOW**

The adapter classes (`FactStoreAdapter`, `DBFactWrapper`, `ReasoningStoreAdapter`) are still present at ~170 lines of code.

**Current Usage:**
- `wrap_db_facts()` - Used in some inventory bridges
- `create_store_adapters_from_deal_data()` - Used in organization analysis

**Recommendation:** Keep for now since some bridges still use them. Consider removal when all bridges are updated to accept DB models directly.

---

## REMAINING: Some Fallback Patterns Still Exist

**Severity: LOW**

Some routes still have the dual-path pattern:

```python
# Dashboard still has fallback
try:
    data = DealData()
    results = data.get_top_risks()
except:
    pass

# Fallback
if not results:
    s = get_session()  # Still present as fallback
```

**Impact:** Reduced since primary routes are database-first, but fallback can still kick in on errors.

---

## Progress Metrics

| Metric | Before | After Session 1 | After Session 2 | Total Change |
|--------|--------|-----------------|-----------------|--------------|
| `get_session()` calls | 72 | ~42 | ~36 | -50% |
| Routes fully on DB | ~5 | ~15 | ~36 | +620% |
| Export routes | Session-only | Session-only | Database-first | **Fixed** |
| Review routes | Session-only | Session-only | Database-first | **Fixed** |
| Cost Center | Session-only | Database-first | Database-first | Fixed |
| Risks route | Session-only | Database-first | Database-first | Fixed |
| Work Items route | Session-only | Database-first | Database-first | Fixed |

---

## Recommended Next Steps

### Priority 1: Create Orphan Migration Script
- Write `scripts/migrate_orphaned_data.py`
- Run once per environment
- Remove `include_orphaned` parameter

### Priority 2: Evaluate Document Management Routes
- DocumentRegistry is file-based by design
- Consider if these should migrate to database or remain file-based
- May be intentional for document processing workflow

### Priority 3: Migrate Organization Module Routes
- These use bridge functions (`get_organization_analysis()`)
- May need bridge function updates to accept DB models

### Priority 4: Remove Adapter Classes
- Once all bridges updated, remove `FactStoreAdapter`, `DBFactWrapper`
- Reduces maintenance burden (~170 lines)

---

## Files Changed in This Fix

| File | Change |
|------|--------|
| `web/blueprints/costs.py` | Now uses DealData/load_deal_context |
| `web/deal_data.py` | Enhanced get_findings_paginated() |
| `web/repositories/finding_repository.py` | Added domain, phase, order_by_severity |
| `web/app.py` | **36+ routes migrated** including: |
| | - risks(), work_items(), risk_detail(), work_item_detail() |
| | - All 11 export routes |
| | - All 4 review routes |
| | - facts(), context(), search() |
| | - api/facts, api/entity-summary, api/session/info |

---

## Conclusion

The migration has made **significant progress**:
- **Cost Center** is now database-first
- **All export routes** (11) are now database-first - critical for data consistency
- **All review routes** (4) are now database-first
- **Core finding routes** (risks, work items) are now database-first
- **Repository/facade** now support full filtering

Approximately **36 routes remain**, but these are primarily:
1. **Document management** - Intentionally file-based (DocumentRegistry)
2. **Organization module** - Uses bridge functions needing updates
3. **Narrative generation** - LLM-based, may need different approach

**Status:** The system is now predominantly database-first for user-facing data routes. The remaining routes are specialized subsystems that may benefit from different migration strategies.

**Recommendation:**
1. Create orphan migration script (Priority 1)
2. Document which routes intentionally remain session-based
3. Plan bridge function updates for organization module

---

*End of Updated Audit*
