# Railway Database Fix Guide

## Problem

The Railway deployment shows **"You have no tables"** in the PostgreSQL database. This is because:

1. The `start.sh` script catches database initialization errors and continues anyway (non-fatal)
2. The app starts with `USE_DATABASE=False` when database init fails
3. All data is saved to local JSON files only (not persisted to database)
4. The UI cannot query the database for data

## Root Cause

**Most likely:** The `DATABASE_URL` environment variable is not set on your Railway app service.

Railway's PostgreSQL service has a `DATABASE_URL` variable, but it's **scoped to that service only**. Your app service needs its own copy of this variable.

## Solution: 3-Step Fix

### Step 1: Set DATABASE_URL Environment Variable

1. **Open your Railway project dashboard**

2. **Find the PostgreSQL service** (should show "Postgres" icon)
   - Click on it
   - Go to the **"Variables"** tab
   - Find `DATABASE_URL` (or `PGDATABASE`, `PGHOST`, etc.)
   - Copy the full `DATABASE_URL` value
   - It should look like: `postgresql://postgres:password@host:5432/railway`

3. **Go to your app service** (the one running `web.app:app`)
   - Click on it
   - Go to the **"Variables"** tab
   - Click **"New Variable"**
   - Name: `DATABASE_URL`
   - Value: Paste the copied database URL
   - Click **"Add"**

4. **Verify other required variables:**
   - `ANTHROPIC_API_KEY` - Your Claude API key
   - `FLASK_SECRET_KEY` - Random string for Flask sessions
   - `USE_DATABASE` - Set to `true` (or leave unset, defaults to true)

### Step 2: Initialize Database Tables

After setting `DATABASE_URL`, you need to create the database tables. **Two options:**

#### Option A: Automatic (via deployment)

1. Commit the new scripts to your repo:
   ```bash
   git add scripts/diagnose_railway_db.py scripts/railway_init_db.sh
   git commit -m "Add Railway database diagnostic and init scripts"
   git push
   ```

2. Wait for Railway to redeploy

3. In Railway, run the init script as a **one-time command**:
   - Go to your app service settings
   - Click **"Deployments"**
   - Find the latest deployment
   - Click the three dots menu → **"Run One-Off Command"**
   - Enter: `bash scripts/railway_init_db.sh`
   - Click **"Run"**

4. Monitor the logs to verify tables are created

#### Option B: Manual via Railway CLI

1. Install Railway CLI:
   ```bash
   npm install -g @railway/cli
   ```

2. Link to your project:
   ```bash
   railway link
   ```

3. Run initialization:
   ```bash
   railway run python scripts/init_db.py
   ```

4. Verify:
   ```bash
   railway run python scripts/diagnose_railway_db.py
   ```

### Step 3: Verify and Restart

1. **Check PostgreSQL database in Railway:**
   - Click on PostgreSQL service
   - Go to **"Database"** tab
   - Should now see tables: `deals`, `users`, `tenants`, `facts`, `findings`, etc.

2. **Restart your app service:**
   - Go to app service
   - Click **"Settings"**
   - Scroll down to **"Restart"**
   - Click **"Restart"**

3. **Test the UI:**
   - Open your Railway app URL
   - Should no longer show database errors
   - Try creating a new deal
   - Upload test documents
   - Run analysis

## Verification Checklist

- [ ] `DATABASE_URL` environment variable is set on app service
- [ ] PostgreSQL shows 12+ tables (deals, users, tenants, facts, findings, etc.)
- [ ] Default admin user exists: `admin@example.com` / `changeme123`
- [ ] App logs show: `"Database initialized (USE_DATABASE=True)"`
- [ ] UI loads without database errors
- [ ] Can create deals and upload documents

## Troubleshooting

### Problem: DATABASE_URL set but still no tables

**Check connection format:**
```bash
# Correct format:
postgresql://user:password@host:5432/database

# Common mistakes:
postgres://...  # Wrong - should be "postgresql://"
missing port    # Must include :5432 or actual port
missing password # Must have full credentials
```

**Test connection manually:**
```bash
railway run python scripts/diagnose_railway_db.py
```

This script will:
- Verify DATABASE_URL is set
- Test connection to PostgreSQL
- List existing tables
- Check for required tables
- Test read/write operations

### Problem: Connection timeout or refused

**Causes:**
- PostgreSQL service is stopped (check Railway dashboard)
- Wrong host/port in DATABASE_URL
- Network issues (rare on Railway)

**Solution:**
- Verify PostgreSQL service shows "Online" status
- Check PostgreSQL logs for errors
- Try restarting PostgreSQL service

### Problem: Tables exist but app still uses JSON files

**Check environment variable:**
```bash
railway run python -c "import os; print('USE_DATABASE:', os.environ.get('USE_DATABASE', 'not set'))"
```

Should output: `USE_DATABASE: true` or `USE_DATABASE: not set` (defaults to true)

If it shows `false`, change it to `true` or remove the variable.

### Problem: Permission denied when creating tables

**Cause:** Database user lacks CREATE TABLE permissions

**Solution:**
1. In Railway PostgreSQL settings, check user permissions
2. Or recreate the PostgreSQL service with proper permissions

### Problem: Default admin user login fails

**Try these credentials:**
- Email: `admin@example.com`
- Password: `changeme123`

**If still fails:**
```bash
# Reset admin password
railway run python -c "
from web.app import app
from web.database import db, User
import bcrypt

with app.app_context():
    admin = User.query.filter_by(email='admin@example.com').first()
    if admin:
        admin.password_hash = bcrypt.hashpw('newpassword123'.encode(), bcrypt.gensalt()).decode()
        db.session.commit()
        print('✓ Password reset to: newpassword123')
    else:
        print('✗ Admin user not found')
"
```

## Prevention: Make Database Init Required

To prevent this issue in the future, update `start.sh` to **fail hard** if database initialization fails:

```bash
# OLD (current - swallows errors):
except Exception as e:
    print(f'⚠️  Migration warning: {e}')
    print('Continuing with startup...')

# NEW (recommended - fails on error):
except Exception as e:
    print(f'❌ DATABASE INITIALIZATION FAILED: {e}')
    print('Cannot start without database.')
    exit 1
```

This ensures you catch database issues immediately rather than running with a broken setup.

## Support

If you continue to have issues:

1. Run diagnostics and save output:
   ```bash
   railway run python scripts/diagnose_railway_db.py > db_diagnostics.txt
   ```

2. Check Railway logs:
   - App service → "Logs" tab
   - PostgreSQL service → "Logs" tab

3. Common log messages to look for:
   - `"Database initialized (USE_DATABASE=True)"` - Good
   - `"Continuing without database"` - Bad (DATABASE_URL not set)
   - `"SQLALCHEMY_DATABASE_URI"` - Shows what connection string is being used
   - `"psycopg2.OperationalError"` - Connection failed

## Additional Resources

- Railway PostgreSQL docs: https://docs.railway.app/databases/postgresql
- Flask-SQLAlchemy docs: https://flask-sqlalchemy.palletsprojects.com/
- Our database models: `web/database.py`
- Our init script: `scripts/init_db.py`
