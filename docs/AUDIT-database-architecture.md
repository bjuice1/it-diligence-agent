# Database Architecture Audit

**Date:** 2026-02-02
**Status:** CRITICAL REVIEW
**Reviewer Notes:** Hypercritical assessment as requested

---

## Executive Summary

The Phase 1/Phase 2 database-first migration is **partially complete** but has significant technical debt, inconsistencies, and architectural concerns that should be addressed before production use.

**Major Issues:**
1. ~70% of routes still use `get_session()` (in-memory) instead of database
2. Dual-path fallback pattern creates data inconsistency risks
3. `include_orphaned=True` default is a maintenance burden, not a proper migration
4. Adapter pattern adds complexity without clear benefit
5. Cost Center blueprint completely bypasses database architecture

---

## Issue #1: Massive Route Migration Gap

### Finding
**Severity: HIGH**

The `get_session()` function is called **72 times** in `web/app.py`, while only ~5 routes have been migrated to use `DealData` from the database.

**Still using `get_session()` (in-memory only):**
- `/risks` - All risk views
- `/work_items` - All work item views
- `/facts` - Fact detail view
- `/context` - Deal context management
- `/export` - All export endpoints
- `/search` - Search functionality
- `/documents` - Document management
- `/validation` - Fact validation
- `/review` - Human review queue
- `/api/session-info` - Session API
- `/api/runs/*` - Run management
- All Excel/dossier export endpoints
- Cost Center blueprint (`costs.py`)

**Migrated to database:**
- `/dashboard` (partial - falls back to session)
- `/applications` (partial)
- `/infrastructure` (partial)
- `/organization` (partial)
- `/gaps` (partial)

### Impact
- Data shown to users depends on which route they visit
- Database has the "truth" but most routes ignore it
- Crash recovery only works for the database side; in-memory data is lost
- Users see inconsistent data between dashboard and detail views

### Recommendation
Complete the migration or remove the fallback pattern entirely. The current state is worse than either pure approach because it creates confusion about which data source is authoritative.

---

## Issue #2: Fallback Pattern Creates Data Ghosts

### Finding
**Severity: HIGH**

Routes use a pattern like:
```python
# Try database first
try:
    data = DealData()
    results = data.get_applications()
except:
    pass

# Fallback to in-memory
if not results:
    s = get_session()
    results = s.fact_store.facts
```

### Problems
1. **Silent failures**: If database query fails, users see stale in-memory data without warning
2. **Race conditions**: User could see database data on one request, in-memory on the next
3. **No audit trail**: No logging of which data source was actually used
4. **Testing nightmare**: Behavior depends on database state, hard to reproduce bugs

### Recommendation
Either:
- **Option A**: Fully commit to database - remove all `get_session()` fallbacks
- **Option B**: Fully commit to session - remove database reads from UI routes

The hybrid approach multiplies complexity without clear benefit.

---

## Issue #3: `include_orphaned=True` Is Not a Migration Strategy

### Finding
**Severity: MEDIUM**

All repository queries include orphaned records (NULL `analysis_run_id`) by default:
```python
def get_by_deal(self, deal_id, run_id=None, include_orphaned=True):
    if run_id and include_orphaned:
        query = query.filter(
            or_(
                Fact.analysis_run_id == run_id,
                Fact.analysis_run_id.is_(None)
            )
        )
```

### Problems
1. **Performance**: Every query adds an OR condition, preventing index optimization
2. **Confusing semantics**: "Give me facts from run X" actually means "run X plus orphans"
3. **Never-ending debt**: Orphaned data will accumulate over time
4. **Testing difficulty**: Hard to test run-scoped queries when orphans leak through

### What Should Exist Instead
A one-time migration script that:
1. Associates orphaned records with their appropriate runs (based on timestamps)
2. Or creates a synthetic "legacy" run to contain pre-migration data
3. Removes the `include_orphaned` parameter entirely

### Recommendation
Write `migrate_orphaned_data.py` that runs once to fix historical data, then remove the `include_orphaned` parameter. The current approach kicks the can indefinitely.

---

## Issue #4: Adapter Pattern Adds Complexity Without Clear Benefit

### Finding
**Severity: MEDIUM**

`web/deal_data.py` includes elaborate adapter classes:
```python
class DBFactWrapper:
    """Wrapper that ensures DB Fact model attributes match what bridge functions expect."""

    @property
    def fact_id(self):
        return self._fact.id

    @property
    def domain(self):
        return self._fact.domain
    # ... 15+ properties
```

### Problems
1. **Indirection**: Debugging requires tracing through multiple layers
2. **Property-by-property mapping**: If DB schema changes, adapter needs updating too
3. **Performance overhead**: Every attribute access goes through `@property`
4. **Rarely used**: Most migrated routes access DB models directly anyway

### Root Cause
The adapters exist because bridge functions expect the old `FactStore` interface. But those bridge functions are also rarely used now.

### Recommendation
Either:
- **Option A**: Update bridge functions to accept DB models directly (breaking change)
- **Option B**: Remove bridge functions entirely if they're not used
- **Option C**: Keep adapters but document when they're actually needed

Currently: 485 lines of adapter code for unclear benefit.

---

## Issue #5: Cost Center Blueprint Completely Ignores Database

### Finding
**Severity: HIGH**

`web/blueprints/costs.py` imports and uses `get_session()` directly:
```python
def _gather_headcount_costs():
    from web.app import get_session
    session = get_session()
    if session and session.fact_store:
        org_facts = [f for f in session.fact_store.facts if f.domain == "organization"]
```

### Impact
- Cost center shows in-memory data only
- No benefit from database persistence
- If analysis crashes, cost data is lost
- Inconsistent with other domain pages that try to use DB

### Recommendation
Migrate cost center to use `DealData` like other routes. This is a complete miss from Phase 2.

---

## Issue #6: Session Scope Management Is Complex

### Finding
**Severity: MEDIUM**

`IncrementalDBWriter.session_scope()` handles multiple scenarios:
- Nested calls (depth tracking)
- Flask request context (don't remove Flask's session)
- Background threads (create app context)
- Existing app context (reuse it)

```python
@contextmanager
def session_scope(self):
    if not hasattr(self._local, 'scope_depth'):
        self._local.scope_depth = 0
    is_outermost = self._local.scope_depth == 0
    self._local.scope_depth += 1
    # ... 30 more lines of context management
```

### Problems
1. **Hard to reason about**: Multiple code paths for different contexts
2. **Thread-local state**: `self._local.scope_depth` can accumulate on errors
3. **Inconsistent cleanup**: Different cleanup rules for request vs non-request

### Risk
If any path forgets to decrement depth or remove session, you get:
- Connection leaks
- Stale data reads
- "detached instance" errors

### Recommendation
Consider using Flask-SQLAlchemy's built-in scoped_session handling more directly. The custom context manager may be over-engineering.

---

## Issue #7: No Caching Strategy

### Finding
**Severity: MEDIUM**

Every page load hits the database with fresh queries:
```python
def get_dashboard_summary(self):
    return {
        'fact_counts': self._fact_repo.count_by_domain(self.deal_id, self.run_id),
        'top_risks': self.get_top_risks(5),
        'gap_counts': self._gap_repo.count_by_importance(self.deal_id, self.run_id),
        'risk_summary': self._finding_repo.get_risk_summary(self.deal_id, self.run_id),
        'work_item_summary': self._finding_repo.get_work_item_summary(self.deal_id, self.run_id),
        # ... 5 separate queries
    }
```

### Impact
- Slow dashboard load times at scale
- Redundant computation for unchanged data
- No benefit from SQLAlchemy's identity map (new queries each time)

### Recommendation
Add request-level or short-TTL caching for summary data. Options:
- Flask-Caching with simple timeout
- Store summary on AnalysisRun when completed
- Memoize within request using `flask.g`

---

## Issue #8: Soft Delete Not Consistently Applied

### Finding
**Severity: LOW**

`BaseRepository.query()` filters deleted records:
```python
def query(self, include_deleted=False):
    if not include_deleted and hasattr(self.model, 'deleted_at'):
        q = q.filter(self.model.deleted_at.is_(None))
```

But several queries go around this:
```python
# In get_linked_facts():
links = db.session.query(FactFindingLink).join(...)  # Bypasses BaseRepository
```

### Risk
- Some queries return deleted records
- Inconsistent behavior depending on code path

### Recommendation
Ensure all queries use repository methods, or add a model-level default query filter.

---

## Issue #9: Finding Type Polymorphism Is Fragile

### Finding
**Severity: MEDIUM**

All finding types (risk, work_item, recommendation, strategic_consideration) share one table with type-specific columns:
```python
if finding_type == 'risk':
    finding_record.update({
        'severity': ...,
        'mitigation': ...,
    })
elif finding_type == 'work_item':
    finding_record.update({
        'phase': ...,
        'cost_estimate': ...,
    })
```

### Problems
1. **Nullable columns**: Most columns are NULL for most rows
2. **No schema enforcement**: Nothing prevents a work_item from having a severity
3. **Hard to query**: Type-specific queries need explicit filters
4. **Confusing**: `finding.phase` is valid for work_items, undefined for risks

### Alternative
Could use SQLAlchemy's single-table inheritance:
```python
class Finding(db.Model): ...
class Risk(Finding): ...
class WorkItem(Finding): ...
```

### Recommendation
Either add proper polymorphism or document the implicit contract clearly.

---

## Issue #10: Import Cycles and Circular Dependencies

### Finding
**Severity: LOW**

Several files have deferred imports to avoid cycles:
```python
def get_linked_facts(self, finding_id):
    from web.database import Fact  # Import inside method
```

```python
def _gather_headcount_costs():
    from web.app import get_session  # Import inside function
```

### Impact
- Slower first call (import overhead)
- Hard to trace dependencies
- IDE type checking is weaker

### Recommendation
Refactor module structure to eliminate cycles. The `get_session` import from `costs.py` into `app.py` is particularly awkward.

---

## Positive Observations

Not everything is broken:

1. **UPSERT implementation is solid**: Handles PostgreSQL and SQLite correctly
2. **Progress throttling works well**: 2-second throttle prevents DB spam
3. **Context resolver is well-designed**: `load_deal_context()` is clean
4. **Soft delete pattern is correct**: When used, it works properly
5. **Repository pattern is clean**: Good separation of concerns

---

## Recommended Action Plan

### Immediate (Before Production)
1. **Decide on data source authority**: DB-only or session-only, not both
2. **Migrate remaining routes** if DB is chosen
3. **Fix Cost Center blueprint** to use database

### Short Term (1-2 Weeks)
4. **Write orphan migration script** and remove `include_orphaned` parameter
5. **Add basic caching** for dashboard summaries
6. **Remove or simplify adapters** based on actual usage

### Medium Term (1 Month)
7. **Add integration tests** for database consistency
8. **Implement proper polymorphism** for Finding types
9. **Resolve import cycles** via module restructure

---

## Files Requiring Changes

| File | Issue | Priority |
|------|-------|----------|
| `web/app.py` | 72 uses of `get_session()` | HIGH |
| `web/blueprints/costs.py` | Ignores database entirely | HIGH |
| `web/repositories/*.py` | Remove `include_orphaned` | MEDIUM |
| `web/deal_data.py` | Simplify or remove adapters | MEDIUM |
| `stores/db_writer.py` | Session scope complexity | LOW |

---

## Conclusion

The Phase 2 implementation is incomplete. The codebase currently has **two parallel data architectures** that produce different results depending on which route is accessed. This is the worst of both worlds: the complexity of the database architecture without the consistency benefits.

**Recommendation**: Complete the migration to database-first or revert to session-first. The current hybrid state should not ship to production.

---

*End of Audit*
