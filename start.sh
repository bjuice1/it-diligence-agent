#!/bin/bash
# Railway startup script for it-diligence-agent

# Use Railway's PORT if set, otherwise default to 8080
PORT=${PORT:-8080}

echo "Starting IT Diligence Agent on port $PORT"
echo "Workers: 1 (for Railway)"
echo "Timeout: 300s"

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
