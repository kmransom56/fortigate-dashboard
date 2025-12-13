#!/bin/bash

# Stop and remove existing containers
echo "🛑 Stopping existing containers..."
docker-compose down

# Remove any orphaned containers with similar names
echo "🧹 Cleaning up orphaned containers..."
docker ps -a | grep -E '(redis-7-alpine|fortigate-dashboard)' | awk '{print $1}' | xargs -r docker rm -f

# Rebuild the fortigate-dashboard image
echo "🔨 Rebuilding fortigate-dashboard..."
docker-compose build --no-cache fortigate-dashboard

# Start all services
echo "🚀 Starting all services..."
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check service health
echo "🏥 Checking service health..."
docker-compose ps

# Show logs for fortigate-dashboard
echo ""
echo "📋 FortiGate Dashboard logs:"
docker-compose logs --tail=50 fortigate-dashboard

echo ""
echo "✅ Done! Check the logs above for any errors."
echo ""
echo "🔗 Access points:"
echo "   Dashboard: http://localhost:8000"
echo "   Grafana:   http://localhost:3001"
echo "   Neo4j:     http://localhost:7475"
echo ""
echo "📊 To follow logs: docker-compose logs -f fortigate-dashboard"
