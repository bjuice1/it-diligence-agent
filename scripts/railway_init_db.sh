#!/bin/bash
# Railway Database Initialization Script
#
# Run this as a one-time job on Railway to initialize the database.
# This is more robust than the inline Python in start.sh
#
# Usage in Railway:
#   1. Deploy this script
#   2. Run as one-time command: bash scripts/railway_init_db.sh
#   3. Check logs to verify tables were created
#   4. Restart your main service

set -e  # Exit on any error

echo "=================================================="
echo "Railway Database Initialization"
echo "=================================================="
echo ""

# Check DATABASE_URL
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL environment variable not set"
    echo ""
    echo "SOLUTION:"
    echo "  1. Go to your Railway project"
    echo "  2. Click on the PostgreSQL service"
    echo "  3. Go to 'Variables' tab"
    echo "  4. Copy the DATABASE_URL value"
    echo "  5. Add it to your app service as an environment variable"
    echo ""
    exit 1
fi

echo "✓ DATABASE_URL is set"
echo ""

# Extract database info for logging (mask password)
DB_INFO=$(echo $DATABASE_URL | sed 's/:\/\/[^:]*:[^@]*@/:\/\/****:****@/')
echo "Database: $DB_INFO"
echo ""

# Test database connection
echo "Testing database connection..."
python3 -c "
import psycopg2
import os
import sys

try:
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    cur.execute('SELECT version()')
    version = cur.fetchone()[0]
    print(f'✓ Connected to: {version.split(\",\")[0]}')
    cur.close()
    conn.close()
except Exception as e:
    print(f'❌ Connection failed: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Database connection test failed!"
    echo "Check your DATABASE_URL and ensure PostgreSQL service is running."
    exit 1
fi

echo ""
echo "Running database initialization..."
echo ""

# Run the init_db.py script
python3 scripts/init_db.py

if [ $? -eq 0 ]; then
    echo ""
    echo "=================================================="
    echo "✅ DATABASE INITIALIZATION COMPLETE"
    echo "=================================================="
    echo ""
    echo "Next steps:"
    echo "  1. Verify tables exist in Railway PostgreSQL"
    echo "  2. Restart your main app service"
    echo "  3. Test the UI at your Railway URL"
    echo ""
    echo "Default admin credentials (CHANGE IMMEDIATELY):"
    echo "  Email: admin@example.com"
    echo "  Password: changeme123"
    echo ""
else
    echo ""
    echo "❌ Database initialization failed!"
    echo "Check the error messages above."
    exit 1
fi
