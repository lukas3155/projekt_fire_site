#!/bin/bash
set -e

echo "=== Deploying Projekt FIRE ==="

cd /opt/projektfire

# Pull latest code
git pull origin main

# Build and restart
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d

# Run migrations
docker compose -f docker-compose.prod.yml exec -T app alembic upgrade head

# Health check
sleep 3
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/blog)
if [ "$STATUS" = "200" ]; then
    echo "=== Deploy successful! Status: $STATUS ==="
else
    echo "=== WARNING: Health check returned $STATUS ==="
    docker compose -f docker-compose.prod.yml logs --tail=20 app
fi
