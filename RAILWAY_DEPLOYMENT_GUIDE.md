# Railway Deployment Guide: "it-dd-v2"

Complete guide to deploy IT Due Diligence Agent V2 with domain model integration to Railway.

---

## Quick Start

### 1. Create New Railway Project

```bash
# Login to Railway
railway login

# Create new project
railway init

# Name it: it-dd-v2
```

**Or via Railway Dashboard:**
1. Go to https://railway.app
2. Click "New Project"
3. Choose "Deploy from GitHub repo"
4. Select your `it-diligence-agent` repository
5. Name the project: **"it-dd-v2"**

---

## 2. Add Required Services

### PostgreSQL Database

1. In Railway project, click "New"
2. Select "Database" → "PostgreSQL"
3. Railway will auto-provision and set `DATABASE_URL`

### Redis (for Celery task queue)

1. Click "New" → "Database" → "Redis"
2. Railway auto-sets `REDIS_URL`

---

## 3. Environment Variables

Set these in Railway project settings:

### Required

```bash
# Anthropic API
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Database (auto-set by Railway)
DATABASE_URL=postgresql://...
REDIS_URL=redis://...

# Domain Model Integration (NEW!)
USE_DOMAIN_MODEL=true

# Flask
FLASK_ENV=production
SECRET_KEY=<generate-random-secret>

# Enable features
USE_DATABASE=true
USE_REDIS_SESSIONS=true
USE_CELERY=true
```

### Optional

```bash
# Parallel agents (set to 1 for Railway to avoid OOM)
MAX_PARALLEL_AGENTS=1

# Organization assumptions (experimental - keep false)
ENABLE_ORG_ASSUMPTIONS=false

# Debug mode (set to false in production)
DEBUG=false
```

---

## 4. Deployment Configuration

Railway uses the existing config files in the repo:

### `railway.toml` (already configured)

```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "bash start.sh"
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 3

[healthcheck]
path = "/health"
timeout = 100

[[services]]
name = "web"
command = "gunicorn -w 4 -b 0.0.0.0:${PORT:-8080} --timeout 300 --log-level info web.app:app"

[[services]]
name = "worker"
command = "celery -A web.celery_app worker --loglevel=info --concurrency=4"
```

### `Procfile` (already configured)

```
web: gunicorn -w 4 -b 0.0.0.0:${PORT:-8080} --timeout 300 --log-level info web.app:app
worker: celery -A web.celery_app worker --loglevel=info --concurrency=4
```

### `start.sh` (already configured)

Runs database migrations and starts the app.

---

## 5. Deploy

### Via Railway CLI

```bash
cd "9.5/it-diligence-agent 2"

# Deploy
railway up

# Watch logs
railway logs
```

### Via GitHub Integration

1. Connect Railway project to GitHub repo
2. Every push to `main` branch auto-deploys
3. Enable auto-deploy in Railway settings

---

## 6. Access the App

Once deployed, Railway provides a URL:

```
https://it-dd-v2.up.railway.app
```

### Test the Deployment

1. **Health Check:**
   ```
   curl https://it-dd-v2.up.railway.app/health
   ```
   Should return: `{"status": "healthy"}`

2. **Web UI:**
   - Navigate to the Railway URL
   - Should see login page or main dashboard

3. **Upload Documents:**
   - Upload test PDFs (Great Insurance docs)
   - Start analysis
   - Verify domain model integration logs in Railway console

---

## 7. Domain Model Integration Verification

### Check Logs

In Railway logs, you should see:

```
============================================================
DOMAIN MODEL INTEGRATION
============================================================

[Applications Domain]
  Created 4 target + 1 buyer applications
  Total: 5 (after deduplication)

[Infrastructure Domain]
  Created 3 target + 0 buyer infrastructure
  Total: 3 (after deduplication)

[Organization Domain]
  Created 5 target + 2 buyer people
  Total: 7 (after deduplication)

[Domain Model Integration Complete]
  Aggregates created: 15
  Items synced to inventory: 15
============================================================
```

### Verify Deduplication

1. Upload documents with duplicate application names (e.g., "Salesforce", "salesforce", "SALESFORCE")
2. After analysis completes, check inventory
3. Should see:
   - **1 application** named "Salesforce"
   - **Observation count: 3** (showing it merged 3 variants)

---

## 8. Troubleshooting

### Issue: Domain Model Import Error

**Symptom:**
```
DOMAIN MODEL INTEGRATION - IMPORT ERROR
Cannot import domain model packages: No module named 'domain'
```

**Fix:**
- Ensure `domain/` directory is in the repository
- Check Railway build logs for errors
- Verify `requirements.txt` includes all dependencies

---

### Issue: Out of Memory (OOM) on Railway

**Symptom:**
- App crashes during analysis
- Railway shows "Out of Memory" error

**Fix:**
Set in environment variables:
```bash
MAX_PARALLEL_AGENTS=1
```

This runs agents sequentially instead of parallel, reducing memory usage.

---

### Issue: Database Connection Errors

**Symptom:**
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Fix:**
1. Check PostgreSQL service is running in Railway
2. Verify `DATABASE_URL` is set correctly
3. Railway auto-sets this - if manual, format is:
   ```
   postgresql://user:pass@host:port/dbname
   ```

---

### Issue: Celery Worker Not Starting

**Symptom:**
- Analysis jobs stay in "pending" status
- No "worker" service in Railway

**Fix:**
1. Railway doesn't auto-detect multiple services
2. Manually add worker service:
   - In Railway, click "New" → "Service"
   - Set start command:
     ```
     celery -A web.celery_app worker --loglevel=info --concurrency=4
     ```
3. Ensure Redis is provisioned

---

### Issue: Static Files Not Loading

**Symptom:**
- Web UI loads but CSS/JS missing
- 404 errors for `/static/*`

**Fix:**
Check `web/app.py` static folder configuration:
```python
app = Flask(__name__, static_folder='static', template_folder='templates')
```

Ensure `web/static/` directory exists in repo.

---

## 9. Monitoring

### Railway Metrics

Railway provides built-in metrics:
- CPU usage
- Memory usage
- Request count
- Response times

Access via Railway dashboard → Project → Metrics

### Application Logs

```bash
# Via CLI
railway logs --tail 100

# Via Dashboard
Railway → Project → Deployments → View Logs
```

### Health Check Endpoint

Railway monitors `/health` automatically (configured in `railway.toml`).

If health check fails 3 times, Railway restarts the service.

---

## 10. Scaling

### Horizontal Scaling (Multiple Web Instances)

Railway Pro plan allows replicas:

```toml
[deploy]
replicas = 2  # Run 2 web instances
```

**Note:** Requires sticky sessions for Flask session storage.

### Vertical Scaling (More Resources)

Railway auto-scales based on usage.

**Manual limits:**
- Settings → Resources → Set memory/CPU limits

---

## 11. Cost Estimation

### Railway Pricing (as of 2024)

**Hobby Plan:** $5/month
- 500 hours of execution
- Good for testing/demos

**Pro Plan:** $20/month + usage
- Unlimited execution hours
- Better for production

**Estimated costs for "it-dd-v2":**
- PostgreSQL: ~$5/month
- Redis: ~$5/month
- Web service: ~$10/month (depends on usage)
- Worker service: ~$5/month

**Total:** ~$25-30/month for moderate usage

---

## 12. Backup & Recovery

### Database Backups

Railway Pro provides automatic backups.

**Manual backup:**
```bash
railway run pg_dump $DATABASE_URL > backup.sql
```

**Restore:**
```bash
railway run psql $DATABASE_URL < backup.sql
```

### Code Rollback

Railway keeps deployment history.

**Rollback to previous deployment:**
1. Railway Dashboard → Deployments
2. Find previous working deployment
3. Click "Redeploy"

---

## 13. Security

### Environment Variables

- Never commit `.env` file
- Use Railway's environment variable management
- Rotate `SECRET_KEY` periodically

### API Keys

- Use Railway's variable management for `ANTHROPIC_API_KEY`
- Never log API keys
- Rotate if compromised

### HTTPS

Railway provides HTTPS by default on all `*.railway.app` domains.

Custom domains also get free SSL certificates.

---

## 14. Custom Domain (Optional)

1. Buy domain (e.g., `itdd.yourcompany.com`)
2. In Railway:
   - Settings → Domains
   - Add custom domain
3. Update DNS:
   - Add CNAME record pointing to Railway's URL
4. Railway auto-provisions SSL certificate

---

## 15. CI/CD Pipeline

### GitHub Actions Integration

Railway supports GitHub Actions for advanced workflows.

**Example:** Run tests before deploy

```yaml
# .github/workflows/railway-deploy.yml
name: Railway Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: |
          pip install -r requirements.txt
          pytest tests/

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to Railway
        run: railway up
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
```

---

## 16. Demo Checklist

Before showing the demo:

- [ ] Domain model integration enabled (`USE_DOMAIN_MODEL=true`)
- [ ] Test documents uploaded (Great Insurance dataset)
- [ ] Run full analysis end-to-end
- [ ] Verify deduplication working (check logs for "3 observations merged")
- [ ] Check inventory counts (should be lower than without domain model)
- [ ] Prepare Railway logs screenshot showing domain model integration
- [ ] Test rollback (set `USE_DOMAIN_MODEL=false` and redeploy)

---

## 17. Quick Reference

### Essential Commands

```bash
# Login
railway login

# Deploy
railway up

# View logs
railway logs

# Open app
railway open

# Environment variables
railway variables

# Database shell
railway run psql $DATABASE_URL

# Status
railway status
```

### Important URLs

- **Railway Dashboard:** https://railway.app/dashboard
- **Docs:** https://docs.railway.app
- **Status:** https://status.railway.app

---

## 18. Next Steps After Deployment

1. **Monitor initial deploys** - Watch logs for errors
2. **Test with real data** - Upload production documents
3. **Verify P0-3 fix** - Check for Salesforce/SAP deduplication
4. **Performance test** - Upload 50+ documents, measure time
5. **Gradual rollout** - Start with `USE_DOMAIN_MODEL=false`, then enable for 10% of analyses
6. **Collect feedback** - Monitor error rates, deduplication quality
7. **Iterate** - Based on production data, tune fingerprinting logic

---

## Support

**Railway issues:** https://railway.app/help
**Application issues:** Check `TROUBLESHOOTING.md` in repo
**Domain model issues:** See `DOMAIN_MODEL_INTEGRATION_REFERENCE.md`

---

✅ **Deployment complete! Your IT DD Agent V2 is live with smart deduplication.** 🚀
