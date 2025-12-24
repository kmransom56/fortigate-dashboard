#!/bin/bash
# Reset Docker Container Script
# Stops and removes the fortigate-dashboard container to force a rebuild

set -e

CONTAINER_NAME="fortigate-dashboard"

echo "🛑 Stopping and removing Docker container: $CONTAINER_NAME"

# Stop the container if running
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "Stopping container..."
    docker stop "$CONTAINER_NAME" 2>/dev/null || true
    
    echo "Removing container..."
    docker rm "$CONTAINER_NAME" 2>/dev/null || true
    
    echo "✅ Container removed successfully"
else
    echo "⚠️  Container $CONTAINER_NAME not found"
fi

# Also remove the image to force a complete rebuild (optional)
read -p "Do you want to remove the image to force a complete rebuild? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    IMAGE_NAME=$(docker images --format '{{.Repository}}:{{.Tag}}' | grep fortigate-dashboard | head -1)
    if [ -n "$IMAGE_NAME" ]; then
        echo "Removing image: $IMAGE_NAME"
        docker rmi "$IMAGE_NAME" 2>/dev/null || true
        echo "✅ Image removed"
    fi
fi

echo ""
echo "To rebuild and start the container:"
echo "  docker compose up --build -d"
