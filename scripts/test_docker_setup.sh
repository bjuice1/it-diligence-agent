#!/bin/bash
#
# Test script for Docker setup with PostgreSQL, Redis, and Celery
#
# Usage: ./scripts/test_docker_setup.sh
#

set -e

echo "=============================================="
echo "IT Due Diligence - Docker Setup Test"
echo "=============================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "ERROR: Docker is not running. Please start Docker and try again."
    exit 1
fi

# Navigate to project directory
cd "$(dirname "$0")/.."

echo ""
echo "1. Building Docker images..."
docker-compose build --quiet

echo ""
echo "2. Starting services..."
docker-compose up -d

echo ""
echo "3. Waiting for services to be healthy..."
sleep 10

# Check PostgreSQL
echo ""
echo "4. Checking PostgreSQL..."
if docker-compose exec -T postgres pg_isready -U diligence > /dev/null 2>&1; then
    echo "   PostgreSQL: OK"
else
    echo "   PostgreSQL: FAILED"
fi

# Check Redis
echo ""
echo "5. Checking Redis..."
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo "   Redis: OK"
else
    echo "   Redis: FAILED"
fi

# Check App health endpoint
echo ""
echo "6. Checking App health..."
sleep 5  # Give app time to start
HEALTH=$(curl -s http://localhost:5001/health 2>/dev/null)
if echo "$HEALTH" | grep -q '"status": "healthy"'; then
    echo "   App: OK"
    echo ""
    echo "   Health response:"
    echo "$HEALTH" | python3 -m json.tool 2>/dev/null || echo "$HEALTH"
else
    echo "   App: FAILED"
    echo "   Response: $HEALTH"
fi

# Check Celery worker
echo ""
echo "7. Checking Celery worker..."
if docker-compose ps celery-worker | grep -q "Up"; then
    echo "   Celery Worker: OK"
else
    echo "   Celery Worker: FAILED"
fi

# Test login
echo ""
echo "8. Testing authentication..."
CSRF=$(curl -s -c /tmp/docker_test_cookies.txt http://localhost:5001/auth/login | grep -o 'name="csrf_token"[^>]*value="[^"]*"' | sed 's/.*value="//;s/"$//')
LOGIN_RESULT=$(curl -s -b /tmp/docker_test_cookies.txt -c /tmp/docker_test_cookies.txt \
    -X POST http://localhost:5001/auth/login \
    -d "csrf_token=$CSRF&email=admin@example.com&password=changeme123" \
    -L 2>/dev/null)

if echo "$LOGIN_RESULT" | grep -q "Dashboard"; then
    echo "   Authentication: OK"
else
    echo "   Authentication: FAILED"
fi

echo ""
echo "=============================================="
echo "Test Complete"
echo "=============================================="
echo ""
echo "Services are running. To view logs:"
echo "  docker-compose logs -f"
echo ""
echo "To stop services:"
echo "  docker-compose down"
echo ""
echo "To access the app:"
echo "  http://localhost:5001"
