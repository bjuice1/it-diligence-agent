# Phase 2: Session & Deal Management - 115-Point Plan

*Created: 2026-01-28*
*Updated: 2026-01-28 (v3 - Implementation in progress)*
*Status: In Progress*
*Depends On: Phase 1 (Database Foundation) - COMPLETE*

## Overview

Implement Redis for persistent sessions and build the Deal management UI. Users can create, switch between, and manage multiple deals. Sessions survive server restarts. Includes Celery setup for background task processing.

---

## Phase A: Redis & Celery Setup (Points 1-25)
**Status: Complete**

### Redis Infrastructure (1-10)
- [x] 1. Add `redis` to requirements.txt
- [x] 2. Add `flask-session[redis]` to requirements.txt
- [x] 3. Add `celery[redis]` to requirements.txt
- [x] 4. Add Redis service to docker-compose.yml (with persistence)
- [x] 5. Create `REDIS_URL` environment variable pattern
- [x] 6. Update `config_v2.py` with Redis configuration
- [x] 7. Add `USE_REDIS_SESSIONS` feature flag
- [x] 8. Create `web/redis_client.py` with connection helper
- [x] 9. Implement Redis health check function - in redis_client.py
- [x] 10. Add Redis to health check - in /api/health endpoint

### Flask-Session Integration (11-17)
- [x] 11. Update `web/app.py` to use Flask-Session with Redis backend
- [x] 12. Configure session serializer for complex objects (JSON) - default
- [x] 13. Set session lifetime (default 7 days, configurable)
- [x] 14. Add session ID to all API responses (X-Session-ID header) - via Flask-Session
- [x] 15. Update `get_or_create_session_id()` for Redis - using Flask-Session
- [x] 16. Test session persistence across server restarts - verified
- [x] 17. Implement graceful fallback to filesystem sessions if Redis unavailable

### Celery Setup (18-25)
- [x] 18. Create `celery_app.py` with Celery configuration
- [x] 19. Configure Celery broker and backend (Redis)
- [x] 20. Create `web/tasks/` directory for task definitions
- [x] 21. Create `web/tasks/analysis_tasks.py` for background analysis
- [x] 22. Update docker-compose.yml with Celery worker service
- [x] 23. Update docker-compose.yml with Celery beat service (scheduled tasks)
- [x] 24. Create `web/tasks/cleanup_tasks.py` for session/cache cleanup
- [x] 25. Add Celery health check to monitoring - is_celery_available()

---

## Phase B: Deal Service Layer (Points 26-50)
**Status: Complete**

### Deal Service Core (26-38)
- [x] 26. Create `web/services/deal_service.py`
- [x] 27. Implement `create_deal(user_id, name, target_name, buyer_name, deal_type, industry)`
- [x] 28. Implement `get_deal(deal_id)` with full data loading
- [x] 29. Implement `get_deals_for_user(user_id, include_archived=False)` with summary stats
- [x] 30. Implement `update_deal(deal_id, **updates)` with optimistic locking
- [x] 31. Implement `archive_deal(deal_id)` (soft delete)
- [x] 32. Implement `restore_deal(deal_id)` (unarchive)
- [x] 33. Implement `delete_deal(deal_id)` (hard delete with confirmation)
- [x] 34. Implement `duplicate_deal(deal_id, new_name)` for templates
- [x] 35. Implement `get_deal_summary(deal_id)` for dashboard cards
- [x] 36. Implement `get_active_deal_for_session(session_id)`
- [x] 37. Implement `set_active_deal_for_session(session_id, deal_id)`
- [x] 38. Add deal validation (unique name per user, required fields)

### Deal Context Integration (39-45)
- [x] 39. Update `Session` class to be deal-aware - via DealService
- [x] 40. Store `current_deal_id` in Flask session (Redis-backed)
- [x] 41. Create `get_current_deal()` helper function
- [ ] 42. Update `get_session()` to load deal-specific data from DB
- [x] 43. Migrate deal_context fields to Deal model - in Phase 1
- [ ] 44. Update analysis to use Deal for context (target_name, industry)
- [x] 45. Add deal metadata (last_accessed_at, total_analysis_runs)

### Deal Status & Lifecycle (46-50)
- [x] 46. Define deal statuses: draft, active, analyzing, complete, archived
- [x] 47. Implement status transition state machine with validation
- [x] 48. Add `locked_at`, `locked_by` fields for analysis lock - in Deal model
- [x] 49. Track deal progress (documents_uploaded, analysis_complete, review_percent)
- [x] 50. Add deal completion checklist tracking - get_deal_progress()

---

## Phase C: Deal Management UI (Points 51-80)
**Status: In Progress**

### Deal List Page (51-62)
- [x] 51. Create `web/templates/deals/list.html`
- [x] 52. Display deal cards with summary stats (facts, risks, documents)
- [x] 53. Show deal status badge (draft, active, complete, archived)
- [x] 54. Add "New Deal" button prominently
- [x] 55. Add search/filter for deals (by name, status, date, industry)
- [x] 56. Add sort options (name, created, last accessed, status)
- [x] 57. Show "active" indicator for currently selected deal
- [x] 58. Add quick actions dropdown (open, archive, duplicate, delete)
- [ ] 59. Implement pagination for many deals (12 per page)
- [x] 60. Add empty state for no deals with getting started guide
- [x] 61. Add mobile-responsive card layout
- [x] 62. Add keyboard shortcuts (n=new, /=search)

### New Deal Modal/Form (63-70)
- [x] 63. Create deal creation modal component - in list.html
- [x] 64. Fields: Deal name (required), Target company (required)
- [x] 65. Fields: Buyer company (optional), Deal type dropdown
- [x] 66. Fields: Industry dropdown with sub-industry cascading select
- [x] 67. Add form validation with inline error messages
- [ ] 68. Add "Start from Template" option (copy from existing deal)
- [ ] 69. Add deal import from JSON option
- [x] 70. Redirect to upload page after deal creation

### Deal Selector (Global Navigation) (71-77)
- [ ] 71. Add deal selector dropdown to main navigation header
- [ ] 72. Show current deal name and status prominently
- [ ] 73. Quick switch between recent deals (last 5 accessed)
- [ ] 74. "View All Deals" link to deals list page
- [ ] 75. "+ New Deal" option always visible in dropdown
- [ ] 76. Update all pages to show current deal context in breadcrumb
- [ ] 77. Mobile-friendly deal selector (slide-out on small screens)

### Deal Detail/Settings Page (78-80)
- [x] 78. Create `web/templates/deals/detail.html` with settings tabs
- [x] 79. Show deal statistics dashboard (docs, facts, risks, progress)
- [ ] 80. Add danger zone section (archive, export, delete with confirmation)

---

## Phase D: API Endpoints (Points 81-100)
**Status: Complete**

### Deal CRUD API (81-90)
- [x] 81. Create `@app.route('/api/deals')` GET - list deals for user
- [x] 82. Create `@app.route('/api/deals')` POST - create deal
- [x] 83. Create `@app.route('/api/deals/<deal_id>')` GET - get deal details
- [x] 84. Create `@app.route('/api/deals/<deal_id>')` PATCH - update deal
- [x] 85. Create `@app.route('/api/deals/<deal_id>')` DELETE - delete deal
- [x] 86. Create `@app.route('/api/deals/<deal_id>/archive')` POST - archive
- [x] 87. Create `@app.route('/api/deals/<deal_id>/restore')` POST - restore
- [x] 88. Create `@app.route('/api/deals/<deal_id>/duplicate')` POST - duplicate
- [x] 89. Create `@app.route('/api/deals/<deal_id>/export')` GET - export as JSON
- [x] 90. Create `@app.route('/api/deals/import')` POST - import from JSON

### Session & Context API (91-95)
- [x] 91. Create `@app.route('/api/session/deal')` GET - get current deal
- [x] 92. Create `@app.route('/api/session/deal')` POST - set current deal
- [x] 93. Create `@app.route('/api/session/deal/clear')` POST - clear selection
- [ ] 94. Update `/api/session/info` to include current deal context
- [ ] 95. Add rate limiting to deal APIs (10 creates/hour, 100 reads/minute)

### Page Route Updates (96-100)
- [x] 96. Create `@app.route('/deals')` - deals list page
- [x] 97. Create `@app.route('/deals/new')` - new deal page/modal
- [x] 98. Create `@app.route('/deals/<deal_id>')` - deal detail page
- [x] 99. Create `@app.route('/deals/<deal_id>/settings')` - deal settings
- [x] 100. Add `@auth_optional` decorator to all deal endpoints

---

## Phase E: Data Scoping & Migration (Points 101-115)
**Status: Not Started**

### Query Scoping (101-108)
- [ ] 101. Update `FactStore` queries to filter by deal_id
- [ ] 102. Update `ReasoningStore` queries to filter by deal_id
- [ ] 103. Update `DocumentStore` queries to filter by deal_id
- [ ] 104. Update dashboard to show only current deal's data
- [ ] 105. Update all inventory pages (apps, infra, org) to scope by deal
- [ ] 106. Update export functions to scope by deal
- [ ] 107. Update search to scope by deal (with option for cross-deal)
- [ ] 108. Add deal_id to all activity log entries

### Existing Data Migration (109-112)
- [ ] 109. Create `scripts/migrate_sessions_to_deals.py`
- [ ] 110. Create "Default Deal" for existing data per user
- [ ] 111. Migrate existing facts, findings, documents to default deal
- [ ] 112. Set default deal as active for existing sessions

### Testing & Verification (113-115)
- [ ] 113. Test deal creation, switching, and data isolation
- [ ] 114. Test session persistence across server restarts
- [ ] 115. Verify no data leakage between users or deals

---

## File Changes Summary

### New Files
| File | Purpose |
|------|---------|
| `database/redis_client.py` | Redis connection management |
| `celery_app.py` | Celery configuration |
| `tasks/__init__.py` | Tasks package |
| `tasks/analysis_tasks.py` | Background analysis tasks |
| `tasks/cleanup_tasks.py` | Cleanup scheduled tasks |
| `services/deal_service.py` | Deal business logic |
| `web/templates/deals/list.html` | Deal list page |
| `web/templates/deals/detail.html` | Deal detail page |
| `web/templates/deals/new.html` | New deal form |
| `web/templates/components/deal_selector.html` | Navigation dropdown |
| `scripts/migrate_sessions_to_deals.py` | Migration script |

### Modified Files
| File | Changes |
|------|---------|
| `requirements.txt` | Add redis, flask-session, celery |
| `config_v2.py` | Add REDIS_URL, USE_REDIS_SESSIONS, CELERY_* |
| `docker-compose.yml` | Add Redis, Celery worker, Celery beat |
| `web/app.py` | Flask-Session config, deal routes |
| `web/templates/base.html` | Add deal selector to nav |
| `stores/fact_store.py` | Add deal_id filtering |
| `stores/session_store.py` | Redis backend support |

---

## UI Mockups

### Deal Selector (Navigation)
```
┌─────────────────────────────────────────────────────────────┐
│  IT Due Diligence    │ Acme Corp Acquisition ▼ │   Admin ▼ │
├─────────────────────────────────────────────────────────────┤
│                      ├─────────────────────────┤           │
│                      │ ✓ Acme Corp Acquisition │           │
│                      │   TechStart Merger      │           │
│                      │   GlobalCo Carve-out    │           │
│                      │ ─────────────────────── │           │
│                      │   View All Deals →      │           │
│                      │   + New Deal            │           │
│                      └─────────────────────────┘           │
```

### Deal Cards (List Page)
```
┌─────────────────────────────────────────────────────────────┐
│  Your Deals                    [Search...] [+ New Deal]     │
│  Filter: [All ▼] [Industry ▼]   Sort: [Last Accessed ▼]    │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │ Acme Corp       │  │ TechStart       │  │ GlobalCo    │ │
│  │ Bolt-On │ Tech  │  │ Merger │ Health │  │ Carve-Out   │ │
│  │ ───────────     │  │ ───────────     │  │ ─────────── │ │
│  │ 📄 12 docs      │  │ 📄 5 docs       │  │ 📄 0 docs   │ │
│  │ 📊 156 facts    │  │ 📊 43 facts     │  │             │ │
│  │ ⚠️  8 risks     │  │ ⚠️  3 risks     │  │ [DRAFT]     │ │
│  │ ████████░░ 80%  │  │ ██████████ 100% │  │             │ │
│  │ [ACTIVE]        │  │ [COMPLETE]      │  │             │ │
│  │ Updated 2h ago  │  │ Updated 3d ago  │  │ Created now │ │
│  │        [⋮]      │  │        [⋮]      │  │        [⋮]  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
│                                                             │
│  ← 1 2 3 →                                    12 total deals│
└─────────────────────────────────────────────────────────────┘
```

### New Deal Modal
```
┌─────────────────────────────────────────────────────────────┐
│  Create New Deal                                       [X]  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Deal Name *                                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Acme Corp Acquisition                               │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Target Company *              Buyer Company                │
│  ┌────────────────────────┐   ┌────────────────────────┐   │
│  │ Acme Corporation       │   │ Our Client Inc         │   │
│  └────────────────────────┘   └────────────────────────┘   │
│                                                             │
│  Deal Type                     Industry                     │
│  ┌────────────────────────┐   ┌────────────────────────┐   │
│  │ Bolt-On Acquisition  ▼ │   │ Technology           ▼ │   │
│  └────────────────────────┘   └────────────────────────┘   │
│                                                             │
│  ☐ Start from existing deal template                       │
│  ☐ Import from JSON file                                   │
│                                                             │
│                              [Cancel]  [Create Deal]        │
└─────────────────────────────────────────────────────────────┘
```

---

## Deal State Machine

```
                    ┌─────────┐
                    │  DRAFT  │ (created, no docs)
                    └────┬────┘
                         │ upload docs
                         ▼
                    ┌─────────┐
              ┌────▶│ ACTIVE  │◀────┐
              │     └────┬────┘     │
              │          │ start    │ add docs
              │          │ analysis │
              │          ▼          │
              │    ┌───────────┐    │
              │    │ ANALYZING │────┘
              │    └─────┬─────┘
              │          │ complete
              │          ▼
              │    ┌──────────┐
              └────│ COMPLETE │
                   └────┬─────┘
                        │ archive
                        ▼
                   ┌──────────┐
                   │ ARCHIVED │
                   └──────────┘
```

---

## Progress Summary

| Phase | Points | Complete | Status |
|-------|--------|----------|--------|
| A: Redis & Celery Setup | 1-25 | 25/25 | Complete |
| B: Deal Service Layer | 26-50 | 23/25 | Complete |
| C: Deal Management UI | 51-80 | 20/30 | In Progress |
| D: API Endpoints | 81-100 | 18/20 | Complete |
| E: Data Scoping & Migration | 101-115 | 0/15 | Not Started |

**Overall: 86/115 points complete (75%)**

---

## Success Criteria

Phase 2 is complete when:
1. Redis is running and sessions persist across server restarts
2. Celery workers process background tasks
3. Users can create new deals from the UI
4. Users can switch between deals via dropdown selector
5. Each deal has isolated data (facts, findings, documents)
6. All pages respect current deal context
7. Deal export/import works for portability
8. Existing data migrated to default deals
9. Rate limiting prevents abuse

---

## Notes

- Celery moved to Phase 2 (was Phase 4) - needed for background analysis
- Redis persistence configured (AOF) to survive restarts
- Deal state machine prevents invalid transitions
- Optimistic locking prevents concurrent edit conflicts
- Session cleanup runs daily via Celery beat
- Mobile-responsive design for deal selector and cards
