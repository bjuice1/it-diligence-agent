# Phase 2: Consistent Database Reads

**Status:** IMPLEMENTED

## Implementation Progress

| Component | Status | Notes |
|-----------|--------|-------|
| Repository run_id filtering | DONE | All repos support `run_id` parameter |
| `web/context.py` | DONE | Deal context resolver created |
| `web/deal_data.py` | DONE | DealData + EmptyDealData + adapters |
| `/api/deal/<id>/status` | DONE | New endpoint using AnalysisRunRepository |
| `/api/deal/<id>/runs` | DONE | Run history endpoint |
| `/dashboard` route | DONE | Database-first with session fallback |
| `/applications` routes | DONE | Database-first with InventoryStore/session fallback |
| `/infrastructure` routes | DONE | Database-first with InventoryStore/session fallback |
| `/organization` routes | DONE | Database-first via `get_organization_analysis()` |
| `/facts` route | DONE | Database pagination with session fallback |
| Session cache deprecation | PARTIAL | Routes use DB-first but keep session as fallback |

## Adapters for Bridge Compatibility

The `web/deal_data.py` module includes adapters to make DB models work with existing bridge functions:

- `FactStoreAdapter`: Wraps DB facts to look like a FactStore (has `.facts` attribute)
- `DBFactWrapper`: Ensures DB Fact attributes match what bridges expect
- `ReasoningStoreAdapter`: Wraps DB findings for organization bridge
- `wrap_db_facts()`: Factory function to create adapters
- `create_store_adapters_from_deal_data()`: Creates both adapters from DealData

## Goal

All UI routes should read from the database as the source of truth, not from in-memory session caches. This ensures:

- Data survives server restarts
- Multiple users see the same data
- UI reflects what's actually persisted

---

## Key Design Decisions

### 1. Scoping Rule: Latest Completed Run

**Problem:** A deal can have multiple analysis runs. Without a scoping rule, the UI shows a "soup" of facts/findings from different runs, causing confusion ("why did this risk disappear?").

**Decision:** All routes default to showing data from the **latest completed analysis run** for the deal.

- Dashboard, facts, risks, work-items all filter by `analysis_run_id`
- The run selector UI can come later, but the default is deterministic now
- In-progress runs are not shown until they complete

### 2. No In-Memory Caching

**Decision:** No `lru_cache` or global caches. They cause problems:
- Can cache across users/deals (security issue)
- Won't invalidate when Phase 1 writes new data continuously
- Can blow memory in multi-worker deployments

If caching is needed later:
- Use **request-scoped** caching only (`flask.g`)
- Or use Redis with explicit invalidation keyed by `deal_id + run_id`

### 3. Filtering and Pagination in SQL, Not Python

**Problem:** Loading 500 facts then filtering/paginating in Python won't scale.

**Decision:** Repositories handle all filtering, searching, and pagination at the SQL level. Routes just pass parameters and render results.

### 4. Layer Responsibilities

```
Routes → DealData → Repositories → Models
```

| Layer | Responsibility |
|-------|----------------|
| **Repositories** | SQL queries: filtering, search, pagination, sorting. Return models. |
| **DealData** | Composition + use-case calls (dashboard summary, top risks). Thin facade. |
| **Routes** | Parse query params, call DealData/Repos, render template or return JSON. |

---

## Current Problems

### Routes Using Memory Instead of Database

| Route | Current Source | Should Be |
|-------|---------------|-----------|
| `/deal/<id>/applications` | `session.fact_store` (memory) | Database query |
| `/deal/<id>/organization` | `session.fact_store` (memory) | Database query |
| `/deal/<id>/infrastructure` | `session.fact_store` (memory) | Database query |
| `/api/status` | Task manager (memory) | Database `AnalysisRun` |

### `get_session()` Inconsistency

Location: `web/app.py` around line 575

Currently:
- Loads facts from database
- Loads findings from database
- Loads gaps from database
- But then routes access `session.fact_store` directly...

The session acts as a cache, but cache invalidation is not handled.

---

## Implementation Plan

### Step 1: Add Deal Context Resolver

**File:** `web/context.py` (NEW)

Resolve `deal_id` and `run_id` once per request, store on `flask.g`.

```python
from flask import g, abort
from models import Deal, AnalysisRun

def load_deal_context(deal_id: str):
    """Call this at the start of any deal-scoped route."""
    deal = Deal.query.get(deal_id)
    if not deal:
        abort(404, "Deal not found")

    # Get latest completed run (the scoping rule)
    latest_run = AnalysisRun.query.filter_by(
        deal_id=deal_id,
        status='completed'
    ).order_by(AnalysisRun.created_at.desc()).first()

    g.deal = deal
    g.deal_id = deal_id
    g.run_id = latest_run.id if latest_run else None
    g.analysis_run = latest_run

def require_deal_context():
    """Decorator or call to ensure deal context is loaded."""
    if not hasattr(g, 'deal_id'):
        raise RuntimeError("Deal context not loaded. Call load_deal_context() first.")
```

### Step 2: Create Repository Layer

**Files to create:**
- `web/repositories/__init__.py`
- `web/repositories/base.py`
- `web/repositories/fact_repository.py`
- `web/repositories/finding_repository.py`
- `web/repositories/gap_repository.py`
- `web/repositories/analysis_run_repository.py`

#### Base Repository (consistent soft-delete handling)

```python
# web/repositories/base.py
from models import db

class BaseRepository:
    model = None

    @classmethod
    def base_query(cls):
        """All queries go through here to enforce soft-delete filter."""
        return cls.model.query.filter(cls.model.deleted_at.is_(None))
```

#### Analysis Run Repository

```python
# web/repositories/analysis_run_repository.py
from models import AnalysisRun
from .base import BaseRepository

class AnalysisRunRepository(BaseRepository):
    model = AnalysisRun

    @classmethod
    def get_latest_completed(cls, deal_id: str) -> AnalysisRun:
        """The canonical way to get the current run for display."""
        return cls.base_query().filter_by(
            deal_id=deal_id,
            status='completed'
        ).order_by(AnalysisRun.created_at.desc()).first()

    @classmethod
    def get_latest(cls, deal_id: str) -> AnalysisRun:
        """Get latest run regardless of status (for status endpoint)."""
        return cls.base_query().filter_by(
            deal_id=deal_id
        ).order_by(AnalysisRun.created_at.desc()).first()

    @classmethod
    def get_by_id(cls, run_id: str) -> AnalysisRun:
        return cls.base_query().filter_by(id=run_id).first()
```

#### Fact Repository (with filtering + pagination in SQL)

```python
# web/repositories/fact_repository.py
from sqlalchemy import or_
from models import Fact
from .base import BaseRepository

class FactRepository(BaseRepository):
    model = Fact

    @classmethod
    def get_paginated(
        cls,
        deal_id: str,
        run_id: str = None,
        domain: str = None,
        status: str = None,
        search: str = None,
        page: int = 1,
        per_page: int = 50
    ):
        """
        Returns (items, total_count) with all filtering done in SQL.
        """
        query = cls.base_query().filter_by(deal_id=deal_id)

        if run_id:
            query = query.filter_by(analysis_run_id=run_id)
        if domain:
            query = query.filter_by(domain=domain)
        if status:
            query = query.filter_by(status=status)
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Fact.name.ilike(search_term),
                    Fact.description.ilike(search_term)
                )
            )

        total = query.count()
        items = query.order_by(Fact.created_at.desc()) \
                     .offset((page - 1) * per_page) \
                     .limit(per_page) \
                     .all()

        return items, total

    @classmethod
    def get_by_domain(cls, deal_id: str, domain: str, run_id: str = None):
        """Get all facts for a domain (for domain overview pages)."""
        query = cls.base_query().filter_by(deal_id=deal_id, domain=domain)
        if run_id:
            query = query.filter_by(analysis_run_id=run_id)
        return query.all()

    @classmethod
    def get_applications(cls, deal_id: str, run_id: str = None):
        return cls.get_by_domain(deal_id, 'applications', run_id)

    @classmethod
    def get_organization(cls, deal_id: str, run_id: str = None):
        return cls.get_by_domain(deal_id, 'organization', run_id)

    @classmethod
    def get_infrastructure(cls, deal_id: str, run_id: str = None):
        return cls.get_by_domain(deal_id, 'infrastructure', run_id)

    @classmethod
    def count_by_domain(cls, deal_id: str, run_id: str = None) -> dict:
        """Get fact counts per domain for dashboard."""
        query = cls.base_query().filter_by(deal_id=deal_id)
        if run_id:
            query = query.filter_by(analysis_run_id=run_id)

        # Group by domain and count
        from sqlalchemy import func
        results = query.with_entities(
            Fact.domain, func.count(Fact.id)
        ).group_by(Fact.domain).all()

        return {domain: count for domain, count in results}
```

#### Finding Repository

```python
# web/repositories/finding_repository.py
from sqlalchemy import or_
from models import Finding
from .base import BaseRepository

class FindingRepository(BaseRepository):
    model = Finding

    @classmethod
    def get_paginated(
        cls,
        deal_id: str,
        run_id: str = None,
        finding_type: str = None,
        severity: str = None,
        search: str = None,
        page: int = 1,
        per_page: int = 50
    ):
        """Returns (items, total_count) with filtering in SQL."""
        query = cls.base_query().filter_by(deal_id=deal_id)

        if run_id:
            query = query.filter_by(analysis_run_id=run_id)
        if finding_type:
            query = query.filter_by(finding_type=finding_type)
        if severity:
            query = query.filter_by(severity=severity)
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Finding.title.ilike(search_term),
                    Finding.description.ilike(search_term)
                )
            )

        total = query.count()
        items = query.order_by(Finding.created_at.desc()) \
                     .offset((page - 1) * per_page) \
                     .limit(per_page) \
                     .all()

        return items, total

    @classmethod
    def get_risks(cls, deal_id: str, run_id: str = None):
        query = cls.base_query().filter_by(deal_id=deal_id, finding_type='risk')
        if run_id:
            query = query.filter_by(analysis_run_id=run_id)
        return query.all()

    @classmethod
    def get_work_items(cls, deal_id: str, run_id: str = None):
        query = cls.base_query().filter_by(deal_id=deal_id, finding_type='work_item')
        if run_id:
            query = query.filter_by(analysis_run_id=run_id)
        return query.all()

    @classmethod
    def get_top_risks(cls, deal_id: str, run_id: str = None, limit: int = 5):
        """Get highest severity risks for dashboard."""
        query = cls.base_query().filter_by(deal_id=deal_id, finding_type='risk')
        if run_id:
            query = query.filter_by(analysis_run_id=run_id)

        # Order by severity (critical > high > medium > low)
        from sqlalchemy import case
        severity_order = case(
            (Finding.severity == 'critical', 1),
            (Finding.severity == 'high', 2),
            (Finding.severity == 'medium', 3),
            (Finding.severity == 'low', 4),
            else_=5
        )
        return query.order_by(severity_order).limit(limit).all()
```

#### Gap Repository

```python
# web/repositories/gap_repository.py
from models import Gap
from .base import BaseRepository

class GapRepository(BaseRepository):
    model = Gap

    @classmethod
    def get_by_deal(cls, deal_id: str, run_id: str = None):
        query = cls.base_query().filter_by(deal_id=deal_id)
        if run_id:
            query = query.filter_by(analysis_run_id=run_id)
        return query.all()

    @classmethod
    def get_by_domain(cls, deal_id: str, domain: str, run_id: str = None):
        query = cls.base_query().filter_by(deal_id=deal_id, domain=domain)
        if run_id:
            query = query.filter_by(analysis_run_id=run_id)
        return query.all()

    @classmethod
    def count_by_priority(cls, deal_id: str, run_id: str = None) -> dict:
        """Get gap counts by priority for dashboard."""
        from sqlalchemy import func
        query = cls.base_query().filter_by(deal_id=deal_id)
        if run_id:
            query = query.filter_by(analysis_run_id=run_id)

        results = query.with_entities(
            Gap.priority, func.count(Gap.id)
        ).group_by(Gap.priority).all()

        return {priority: count for priority, count in results}
```

### Step 3: Create DealData Facade

**File:** `web/deal_data.py` (NEW)

Thin facade that composes repository calls for common use cases.

```python
# web/deal_data.py
from flask import g
from .repositories.fact_repository import FactRepository
from .repositories.finding_repository import FindingRepository
from .repositories.gap_repository import GapRepository
from .repositories.analysis_run_repository import AnalysisRunRepository

class DealData:
    """
    Facade for accessing deal data. Uses flask.g for deal/run context.
    Routes should use this instead of calling repositories directly.
    """

    def __init__(self, deal_id: str = None, run_id: str = None):
        # Use flask.g context if available, otherwise use explicit params
        self.deal_id = deal_id or getattr(g, 'deal_id', None)
        self.run_id = run_id or getattr(g, 'run_id', None)

        if not self.deal_id:
            raise ValueError("deal_id required")

    # --- Facts ---

    def get_applications(self):
        return FactRepository.get_applications(self.deal_id, self.run_id)

    def get_organization(self):
        return FactRepository.get_organization(self.deal_id, self.run_id)

    def get_infrastructure(self):
        return FactRepository.get_infrastructure(self.deal_id, self.run_id)

    def get_facts_paginated(self, domain=None, status=None, search=None, page=1, per_page=50):
        return FactRepository.get_paginated(
            deal_id=self.deal_id,
            run_id=self.run_id,
            domain=domain,
            status=status,
            search=search,
            page=page,
            per_page=per_page
        )

    # --- Findings ---

    def get_risks(self):
        return FindingRepository.get_risks(self.deal_id, self.run_id)

    def get_work_items(self):
        return FindingRepository.get_work_items(self.deal_id, self.run_id)

    def get_top_risks(self, limit=5):
        return FindingRepository.get_top_risks(self.deal_id, self.run_id, limit)

    def get_findings_paginated(self, finding_type=None, severity=None, search=None, page=1, per_page=50):
        return FindingRepository.get_paginated(
            deal_id=self.deal_id,
            run_id=self.run_id,
            finding_type=finding_type,
            severity=severity,
            search=search,
            page=page,
            per_page=per_page
        )

    # --- Gaps ---

    def get_gaps(self):
        return GapRepository.get_by_deal(self.deal_id, self.run_id)

    def get_gaps_by_domain(self, domain: str):
        return GapRepository.get_by_domain(self.deal_id, domain, self.run_id)

    # --- Dashboard ---

    def get_dashboard_summary(self):
        """Aggregated data for the deal dashboard."""
        return {
            'fact_counts': FactRepository.count_by_domain(self.deal_id, self.run_id),
            'top_risks': self.get_top_risks(5),
            'gap_counts': GapRepository.count_by_priority(self.deal_id, self.run_id),
            'analysis_run': AnalysisRunRepository.get_by_id(self.run_id) if self.run_id else None
        }


class EmptyDealData:
    """
    Fallback when no deal context exists. Returns empty collections
    so templates don't crash.
    """
    deal_id = None
    run_id = None

    def get_applications(self): return []
    def get_organization(self): return []
    def get_infrastructure(self): return []
    def get_facts_paginated(self, **kwargs): return [], 0
    def get_risks(self): return []
    def get_work_items(self): return []
    def get_top_risks(self, limit=5): return []
    def get_findings_paginated(self, **kwargs): return [], 0
    def get_gaps(self): return []
    def get_gaps_by_domain(self, domain): return []
    def get_dashboard_summary(self):
        return {
            'fact_counts': {},
            'top_risks': [],
            'gap_counts': {},
            'analysis_run': None
        }
```

### Step 4: Update Routes

**Pattern for all routes:**

```python
# BEFORE (memory-based)
@app.route('/deal/<deal_id>/applications')
def applications_overview(deal_id):
    session = get_session(deal_id)
    apps = [f for f in session.fact_store.facts if f.domain == 'applications']
    return render_template('applications/overview.html', applications=apps)

# AFTER (database-based)
from web.context import load_deal_context
from web.deal_data import DealData

@app.route('/deal/<deal_id>/applications')
def applications_overview(deal_id):
    load_deal_context(deal_id)
    data = DealData()
    apps = data.get_applications()
    return render_template('applications/overview.html', applications=apps)
```

**Files to modify:**
- `web/blueprints/applications.py`
- `web/blueprints/organization.py`
- `web/blueprints/infrastructure.py`
- `web/blueprints/cybersecurity.py`
- `web/blueprints/identity_access.py`
- `web/blueprints/network.py`

### Step 5: Update Status Endpoint

**File:** `web/app.py` - `/api/deal/<deal_id>/status`

```python
from web.repositories.analysis_run_repository import AnalysisRunRepository

@app.route('/api/deal/<deal_id>/status')
def get_analysis_status(deal_id):
    # Get latest run (any status) to show in-progress analysis
    run = AnalysisRunRepository.get_latest(deal_id)

    if run:
        return jsonify({
            'status': run.status,
            'progress': run.progress,
            'current_step': run.current_step,
            'facts_created': run.facts_created,
            'findings_created': run.findings_created,
            'run_id': run.id,
            'started_at': run.created_at.isoformat() if run.created_at else None,
            'completed_at': run.completed_at.isoformat() if run.completed_at else None,
        })
    return jsonify({'status': 'no_analysis'})
```

### Step 6: Deprecate Session Cache

Once routes use DealData:
- Remove `get_session()` or simplify to only load minimal data
- Remove `SESSION_CACHE` global
- Analysis writes directly to DB (Phase 1), routes read directly from DB (Phase 2)

---

## Database Indexes

Add indexes for the query patterns used by repositories:

```sql
-- Fact queries
CREATE INDEX idx_facts_deal_id ON facts(deal_id);
CREATE INDEX idx_facts_deal_domain ON facts(deal_id, domain);
CREATE INDEX idx_facts_deal_run ON facts(deal_id, analysis_run_id);

-- Finding queries
CREATE INDEX idx_findings_deal_id ON findings(deal_id);
CREATE INDEX idx_findings_deal_type ON findings(deal_id, finding_type);
CREATE INDEX idx_findings_deal_run ON findings(deal_id, analysis_run_id);

-- Gap queries
CREATE INDEX idx_gaps_deal_id ON gaps(deal_id);
CREATE INDEX idx_gaps_deal_run ON gaps(deal_id, analysis_run_id);

-- Analysis run queries
CREATE INDEX idx_analysis_runs_deal ON analysis_runs(deal_id, status, created_at DESC);
```

Or via Flask-Migrate/Alembic migration.

---

## Files to Create

| File | Purpose |
|------|---------|
| `web/context.py` | Deal context resolver (`load_deal_context`, `flask.g`) |
| `web/repositories/__init__.py` | Package init |
| `web/repositories/base.py` | BaseRepository with soft-delete handling |
| `web/repositories/fact_repository.py` | Fact queries with pagination |
| `web/repositories/finding_repository.py` | Risk/work item queries |
| `web/repositories/gap_repository.py` | Gap queries |
| `web/repositories/analysis_run_repository.py` | Run queries including `get_latest_completed` |
| `web/deal_data.py` | DealData facade + EmptyDealData |

## Files to Modify

| File | Change |
|------|--------|
| `web/blueprints/applications.py` | Use DealData |
| `web/blueprints/organization.py` | Use DealData |
| `web/blueprints/infrastructure.py` | Use DealData |
| `web/blueprints/cybersecurity.py` | Use DealData |
| `web/blueprints/identity_access.py` | Use DealData |
| `web/blueprints/network.py` | Use DealData |
| `web/app.py` | Update status endpoint, deprecate session cache |

---

## Migration Strategy

1. **Create repositories and DealData** - no impact on existing code
2. **Add indexes** - run migration
3. **Migrate routes one by one** - keep `get_session()` working during transition
4. **Remove session cache** - once all routes migrated

This allows incremental rollout without breaking the app.

---

## Verification

After implementation:

1. Run analysis on a deal
2. Restart the server
3. Navigate to any route (applications, organization, etc.)
4. **Data should still be visible** (loaded from DB, not memory)
5. Run a second analysis on the same deal
6. **UI should show data from the new (latest completed) run only**

---

## Dependencies

- Phase 1 (Incremental Writes) must be complete
- Database must have all facts/findings persisted during analysis
- Models must have `analysis_run_id` foreign key (should already exist from Phase 1)
