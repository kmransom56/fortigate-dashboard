#!/bin/bash
# Quick script to stop and delete the fortigate-dashboard container

CONTAINER_NAME="fortigate-dashboard"

echo "🛑 Stopping container: $CONTAINER_NAME"
docker stop "$CONTAINER_NAME" 2>/dev/null || echo "Container not running"

echo "🗑️  Removing container: $CONTAINER_NAME"
docker rm "$CONTAINER_NAME" 2>/dev/null || echo "Container not found"

echo "✅ Done! Container removed."
echo ""
echo "To rebuild: docker compose up --build -d"
