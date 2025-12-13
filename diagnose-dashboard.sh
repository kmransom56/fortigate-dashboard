#!/bin/bash

echo "🔍 Checking FortiGate Dashboard Environment Variables"
echo "=================================================="
echo ""

# Check if container is running
if ! docker ps | grep -q fortigate-dashboard; then
    echo "❌ fortigate-dashboard container is not running!"
    exit 1
fi

echo "✅ Container is running"
echo ""

# Check critical environment variables
echo "📋 Critical Environment Variables:"
echo "-----------------------------------"

docker exec fortigate-dashboard bash -c '
echo "REDIS_HOST: ${REDIS_HOST:-NOT SET}"
echo "REDIS_PORT: ${REDIS_PORT:-NOT SET}"
echo "FORTIGATE_HOST: ${FORTIGATE_HOST:-NOT SET}"
echo "FORTIGATE_USERNAME: ${FORTIGATE_USERNAME:-NOT SET}"
echo "FORTIGATE_PASSWORD: ${FORTIGATE_PASSWORD:+***SET***}"
echo "FORTIGATE_API_PORT: ${FORTIGATE_API_PORT:-NOT SET}"
'

echo ""
echo "🔌 Network Connectivity Tests:"
echo "-------------------------------"

# Test Redis connection
echo -n "Redis (redis:6379): "
if docker exec fortigate-dashboard bash -c 'nc -zv redis 6379 2>&1 | grep -q succeeded'; then
    echo "✅ Connected"
else
    echo "❌ Cannot connect"
fi

# Test Postgres connection
echo -n "Postgres (postgres:5432): "
if docker exec fortigate-dashboard bash -c 'nc -zv postgres 5432 2>&1 | grep -q succeeded'; then
    echo "✅ Connected"
else
    echo "❌ Cannot connect"
fi

# Test Neo4j connection
echo -n "Neo4j (neo4j:7687): "
if docker exec fortigate-dashboard bash -c 'nc -zv neo4j 7687 2>&1 | grep -q succeeded'; then
    echo "✅ Connected"
else
    echo "❌ Cannot connect"
fi

echo ""
echo "🌐 Testing FortiGate API connection:"
echo "------------------------------------"
docker exec fortigate-dashboard bash -c 'nc -zv 192.168.0.254 10443 2>&1'

echo ""
echo "📊 Recent Application Logs:"
echo "---------------------------"
docker logs fortigate-dashboard --tail=20

echo ""
echo "=================================================="
echo "Diagnostic complete!"
