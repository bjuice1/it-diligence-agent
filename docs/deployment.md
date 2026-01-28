# IT Due Diligence Agent - Deployment Guide

## Quick Start (Local Development)

```bash
# Clone repository
git clone https://github.com/bjuice1/it-diligence-agent.git
cd it-diligence-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Run the application
python -m web.app

# Access at http://localhost:5001
```

## Docker Deployment

### Build and Run

```bash
# Build image
docker build -t it-diligence-agent .

# Run container
docker run -d \
  -p 5001:8080 \
  -e ANTHROPIC_API_KEY=sk-ant-... \
  -e FLASK_SECRET_KEY=$(openssl rand -hex 32) \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/output:/app/output \
  it-diligence-agent
```

### Docker Compose (Full Stack)

```bash
# Start all services (from docker/ directory)
cd docker
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop
docker-compose down
```

Services included:
- **app**: Main Flask application
- **celery-worker**: Background task processing
- **celery-beat**: Scheduled tasks
- **postgres**: PostgreSQL database
- **redis**: Session and task queue
- **minio**: S3-compatible storage

## Railway Deployment

### One-Click Deploy

1. Fork the repository on GitHub
2. Go to [Railway](https://railway.app)
3. Create new project from GitHub repo
4. Set environment variables:
   - `ANTHROPIC_API_KEY`
   - `FLASK_SECRET_KEY`
5. Deploy

### Manual Setup

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Deploy
railway up

# Set environment variables
railway variables set ANTHROPIC_API_KEY=sk-ant-...
railway variables set FLASK_SECRET_KEY=$(openssl rand -hex 32)
```

## Environment Variables

### Required
```bash
ANTHROPIC_API_KEY=sk-ant-...        # Anthropic API key
FLASK_SECRET_KEY=<random-32-bytes>  # Session encryption
```

### Optional (Production)
```bash
# Flask
FLASK_ENV=production
LOG_LEVEL=info

# Database (Phase 3)
USE_DATABASE=true
DATABASE_URL=postgresql://user:pass@host:5432/db

# Redis (Phase 4)
USE_REDIS_SESSIONS=true
USE_CELERY=true
REDIS_URL=redis://host:6379/0

# Storage (Phase 5)
STORAGE_TYPE=s3
S3_BUCKET=diligence-documents
S3_REGION=us-east-1
S3_ENDPOINT=https://...  # For R2/MinIO
S3_ACCESS_KEY=...
S3_SECRET_KEY=...

# Multi-tenancy (Phase 6)
USE_MULTI_TENANCY=true

# Monitoring (Phase 7)
USE_STRUCTURED_LOGGING=true
USE_ERROR_TRACKING=true
SENTRY_DSN=https://...
USE_RATE_LIMITING=true
USE_AUDIT_LOGGING=true
```

## Production Checklist

### Security
- [ ] Set strong `FLASK_SECRET_KEY`
- [ ] Enable HTTPS (TLS termination)
- [ ] Configure CORS if needed
- [ ] Enable rate limiting
- [ ] Set up authentication

### Performance
- [ ] Use gunicorn with multiple workers
- [ ] Configure Redis for sessions
- [ ] Set up Celery for background tasks
- [ ] Enable S3 for document storage

### Reliability
- [ ] Configure health checks
- [ ] Set up monitoring (Sentry, Datadog)
- [ ] Configure backups for PostgreSQL
- [ ] Set up log aggregation

### Scaling
- [ ] Use PostgreSQL instead of JSON files
- [ ] Configure Redis cluster
- [ ] Set up CDN for static files
- [ ] Consider horizontal scaling

## Health Checks

The application exposes a health endpoint:

```bash
curl http://localhost:5001/health
```

Response:
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "checks": {
    "api_key": true,
    "output_dir": true
  }
}
```

## Gunicorn Configuration

`gunicorn.conf.py`:
```python
bind = "0.0.0.0:8080"
workers = 2
threads = 4
timeout = 300  # 5 min for long analysis
keepalive = 2
errorlog = "-"
accesslog = "-"
```

## Troubleshooting

### Common Issues

**"ANTHROPIC_API_KEY not configured"**
- Ensure the environment variable is set
- Check `.env` file exists and is loaded

**"Cannot write to output directory"**
- Check directory permissions
- Ensure volume mounts are correct in Docker

**Analysis stuck or slow**
- Check API rate limits
- Review logs for circuit breaker trips
- Increase timeout settings

### Logs

```bash
# Docker
docker-compose logs -f app

# Local
tail -f output/logs/analysis.log

# Railway
railway logs
```

## Backup & Restore

### Backup
```bash
# Backup uploads and output
tar -czf backup.tar.gz uploads/ output/

# Backup PostgreSQL (if using)
pg_dump $DATABASE_URL > backup.sql
```

### Restore
```bash
# Restore files
tar -xzf backup.tar.gz

# Restore PostgreSQL
psql $DATABASE_URL < backup.sql
```

## Upgrading

```bash
# Pull latest code
git pull origin main

# Update dependencies
pip install -r requirements.txt

# Restart application
docker-compose restart app
# or
railway up
```

See also:
- [Architecture Overview](architecture.md)
- [API Reference](api.md)
- [Storage Architecture](storage.md)
