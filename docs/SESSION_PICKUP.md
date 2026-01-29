# Session Pickup Guide - January 29, 2026

## Current Status: Phase 2 Testing

### What's Working
- Docker environment fully operational (app, postgres, redis, celery, minio)
- Authentication system (optional, disabled for dev)
- Deal management (create, select, manage deals)
- Document upload with deal association
- Analysis pipeline runs and extracts facts
- Database persistence (facts/findings stored with deal_id)

### Recent Fixes Applied
1. **Multi-worker issue** - Set `GUNICORN_WORKERS=1` (in-memory task state needs single worker)
2. **Rate limiting** - Disabled for development (`USE_RATE_LIMITING=false`)
3. **Session race condition** - Added task_id query param fallback
4. **Path portability** - Document store uses relative paths
5. **User sync** - Auto-syncs authenticated users to database

### Known Issues to Address
- [ ] Rate limiting needs proper exemptions for status endpoints before production
- [ ] Task state should use Redis for multi-worker support (production)
- [ ] UI feedback during analysis could be improved

---

## Quick Start (Docker)

```bash
cd docker

# Start all services
docker compose up -d

# Check health
curl http://localhost:5001/health

# View logs
docker compose logs app -f

# Stop
docker compose down
```

**Access**: http://localhost:5001

---

## Testing Flow

1. **Create Deal**: `/deals` → New Deal → Enter target/buyer info
2. **Upload Documents**: Select deal → Upload → Drag files
3. **Run Analysis**: Documents auto-analyze after upload
4. **View Results**: Dashboard shows facts, risks, work items
5. **Review by Deal**: All data scoped to active deal

---

## Environment Variables (docker-compose.yml)

```yaml
# Core
ANTHROPIC_API_KEY=sk-ant-...
FLASK_SECRET_KEY=your-secret

# Features (all enabled by default)
USE_DATABASE=true
USE_REDIS_SESSIONS=true
USE_CELERY=true
USE_RATE_LIMITING=false  # Disabled for dev
USE_AUDIT_LOGGING=true

# Performance
GUNICORN_WORKERS=1  # Single worker for task state consistency
```

---

## Architecture Notes

### Deal-Scoped Data Model
```
Deal
 ├── Documents (target/buyer separation)
 ├── Facts (F-DOMAIN-001)
 ├── Findings (risks, work items)
 └── Analysis runs (timestamps, progress)
```

### Task Flow
```
Upload → Create Task → Background Thread → Save Results → Database + JSON
           ↓
    Task Manager (in-memory, single worker)
           ↓
    Status Polling (/analysis/status?task_id=xxx)
```

---

## Files Changed This Session

| File | Change |
|------|--------|
| `docker/docker-compose.yml` | Added GUNICORN_WORKERS=1, disabled rate limiting |
| `web/app.py` | Session race condition fix, deal_id to start_task |
| `web/routes/deals.py` | User sync to database |
| `web/templates/processing.html` | Task ID in status poll URL |
| `stores/document_store.py` | Relative path storage |

---

## Next Steps

1. **Test different deal types** - Create test documents for:
   - Bolt-on acquisition (small target, simple IT)
   - Platform deal (larger target, complex IT)
   - Carve-out (target is division of larger company)

2. **Industry-specific testing**:
   - Insurance (regulatory, legacy systems)
   - Healthcare (HIPAA, EMR systems)
   - SaaS (cloud-native, modern stack)
   - Manufacturing (OT/IT convergence)

3. **UI improvements** based on testing feedback

4. **Production prep**:
   - Redis-based task state
   - Rate limit exemptions for polling
   - Proper multi-worker support

---

## Resuming Development

```bash
# 1. Start Docker
cd docker && docker compose up -d

# 2. Clear any stale data (if needed)
docker compose exec redis redis-cli FLUSHALL

# 3. Check logs
docker compose logs app -f

# 4. Access app
open http://localhost:5001
```

---

*Last updated: January 29, 2026 02:15 EST*
