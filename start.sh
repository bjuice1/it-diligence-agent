#!/bin/bash
set -e

echo "🚂 Railway deployment starting..."

# Run database migrations
echo "📦 Running database migrations..."
alembic upgrade head

echo "✅ Migrations complete"

# Start the application
echo "🚀 Starting application..."
exec gunicorn -w 4 -b 0.0.0.0:$PORT --timeout 300 --log-level info "web.app:app"
