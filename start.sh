#!/bin/bash
# Railway startup script for it-diligence-agent

# Use Railway's PORT if set, otherwise default to 8080
PORT=${PORT:-8080}

echo "Starting IT Diligence Agent on port $PORT"

# Run database migrations before starting app
echo "Running database migrations..."
if [ -n "$DATABASE_URL" ]; then
    python -c "
from web.app import app
from web.database import create_all_tables
import logging
logging.basicConfig(level=logging.INFO)
try:
    create_all_tables(app)
    print('✅ Database migrations complete')
except Exception as e:
    print(f'⚠️  Migration warning: {e}')
    print('Continuing with startup...')
"
fi

echo "Starting gunicorn..."

# Start gunicorn with detailed logging
exec gunicorn \
    -w 1 \
    -b 0.0.0.0:$PORT \
    --timeout 300 \
    --log-level debug \
    --access-logfile - \
    --error-logfile - \
    --capture-output \
    web.app:app
