# Railway Deployment Guide 🚂

Quick guide to deploy IT Diligence Agent to Railway.app

## Prerequisites

- Railway account ([railway.app](https://railway.app))
- Railway CLI installed: `npm install -g @railway/cli`
- Git repository pushed to GitHub
- Anthropic API key

## Quick Deploy (5 minutes)

### Option 1: Deploy via Railway Dashboard (Easiest)

1. **Go to Railway:** https://railway.app
2. **Click "New Project"**
3. **Select "Deploy from GitHub repo"**
4. **Choose:** `bjuice1/it-diligence-agent`
5. **Add Plugins:**
   - Click "+ New" → "Database" → "PostgreSQL"
   - Click "+ New" → "Database" → "Redis"
6. **Add Environment Variables:**
   ```
   ANTHROPIC_API_KEY=sk-ant-your-key-here
   FLASK_ENV=production
   SECRET_KEY=<generate-random-key>
   DATABASE_URL=${{Postgres.DATABASE_URL}}
   REDIS_URL=${{Redis.REDIS_URL}}
   ```
7. **Deploy!** Railway will automatically:
   - Build the application
   - Run database migrations (via start.sh)
   - Start the web server

**Your app will be live at:** `https://your-app.railway.app`

### Option 2: Deploy via Railway CLI

```bash
# 1. Login to Railway
railway login

# 2. Create new project
railway init

# 3. Link to GitHub repo (if not done via dashboard)
railway link

# 4. Add PostgreSQL
railway add --plugin postgresql

# 5. Add Redis
railway add --plugin redis

# 6. Set environment variables
railway variables set ANTHROPIC_API_KEY=sk-ant-your-key-here
railway variables set FLASK_ENV=production
railway variables set SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")

# 7. Deploy
railway up

# 8. Open in browser
railway open
```

## Environment Variables

Set these in Railway Dashboard → Project → Variables:

| Variable | Value | Required |
|----------|-------|----------|
| `ANTHROPIC_API_KEY` | Your Claude API key | ✅ Yes |
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` | ✅ Auto |
| `REDIS_URL` | `${{Redis.REDIS_URL}}` | ✅ Auto |
| `FLASK_ENV` | `production` | ✅ Yes |
| `SECRET_KEY` | Random 64-char hex | ✅ Yes |
| `LOG_LEVEL` | `INFO` | ⚪ Optional |
| `PORT` | `5001` | ⚪ Auto |

## Database Migration

**Migrations run automatically** on deployment via `start.sh`:

```bash
#!/bin/bash
alembic upgrade head  # ← Runs migration 003
gunicorn ...          # ← Starts app
```

To run migrations manually:
```bash
railway run alembic upgrade head
```

## Verify Deployment

### 1. Check Health Endpoint
```bash
curl https://your-app.railway.app/api/health
# Expected: {"status": "healthy"}
```

### 2. Check Database Migration
```bash
railway run python -c "
from web.app import app, db
from sqlalchemy import inspect
with app.app_context():
    inspector = inspect(db.engine)
    columns = [c['name'] for c in inspector.get_columns('facts')]
    print('✅ cost_status column exists' if 'cost_status' in columns else '❌ Migration failed')
"
```

### 3. Check Cost Status Data
```bash
railway run python -c "
from web.app import app, db
with app.app_context():
    result = db.session.execute('''
        SELECT cost_status, COUNT(*) 
        FROM facts 
        WHERE domain='applications' 
        GROUP BY cost_status
    ''')
    print('Cost status distribution:', dict(result))
"
```

### 4. Run Pipeline Test
```bash
# SSH into Railway container (if needed)
railway shell

# Run test
python main_v2.py /tmp/test-data/ --domain applications --target-name "Test"
```

## Monitoring

Railway provides built-in monitoring:

1. **Logs:** Railway Dashboard → Project → Deployments → View Logs
2. **Metrics:** CPU, Memory, Network usage in dashboard
3. **Alerts:** Set up in Project Settings

Watch for:
- ✅ Successful startup: "🚀 Starting application..."
- ✅ Migration success: "✅ Migrations complete"
- ❌ Database connection errors
- ❌ API key errors
- ❌ Cost status constraint violations

## Rollback

### Rollback to Previous Deployment

Railway Dashboard → Deployments → Click previous deployment → "Redeploy"

### Rollback Database Migration

```bash
# Connect to Railway
railway shell

# Rollback one migration
alembic downgrade -1

# Verify
alembic current
```

## Multi-Service Setup (Advanced)

For production workloads, deploy web and worker separately:

### Service 1: Web Server
```bash
railway service create web
railway service web --command "bash start.sh"
```

### Service 2: Celery Worker
```bash
railway service create worker
railway service worker --command "celery -A web.celery_app worker --loglevel=info"
```

Both services share the same DATABASE_URL and REDIS_URL.

## Cost Estimation

Railway pricing: https://railway.app/pricing

**Expected costs:**
- **Hobby Plan:** $5/month (good for staging)
  - 500 hours execution time
  - Shared resources
- **Pro Plan:** $20/month + usage (production)
  - Dedicated resources
  - PostgreSQL + Redis included
  - ~$30-50/month for typical load

## Troubleshooting

### Build Fails

```bash
# Check build logs
railway logs --build

# Common issues:
# - Missing requirements.txt
# - Python version mismatch (check runtime.txt)
# - Dependency conflicts
```

### Migration Fails

```bash
# Check if alembic is installed
railway run pip list | grep alembic

# Manually run migration with verbose output
railway run alembic upgrade head --sql
```

### App Won't Start

```bash
# Check startup logs
railway logs --tail 100

# Test locally first
railway run python -c "from web.app import app; print('✅ App imports successfully')"
```

### Database Connection Errors

```bash
# Verify DATABASE_URL is set
railway variables

# Test connection
railway run python -c "
from sqlalchemy import create_engine
import os
engine = create_engine(os.environ['DATABASE_URL'])
print('✅ Database connected' if engine.connect() else '❌ Connection failed')
"
```

## Custom Domain (Optional)

1. Railway Dashboard → Project → Settings → Domains
2. Click "Generate Domain" for free Railway domain
3. Or add custom domain: yourdomain.com
4. Update DNS:
   ```
   CNAME www.yourdomain.com → your-app.railway.app
   ```

## Support

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- GitHub Issues: https://github.com/bjuice1/it-diligence-agent/issues

## Production Checklist

Before going live:

- [ ] PostgreSQL plugin added
- [ ] Redis plugin added
- [ ] All environment variables set
- [ ] Database migration successful (cost_status column exists)
- [ ] Health check endpoint returns 200
- [ ] Pipeline test runs successfully
- [ ] Logs show no errors
- [ ] Custom domain configured (if needed)
- [ ] Monitoring alerts set up
- [ ] Backup strategy documented

---

**Deployment Status:** ✅ Ready to deploy to Railway

**Time to deploy:** ~5 minutes (dashboard) or ~10 minutes (CLI)

**Zero-downtime deployment:** ✅ Yes (Railway handles this automatically)
