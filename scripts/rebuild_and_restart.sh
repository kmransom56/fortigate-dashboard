#!/bin/bash

# Rebuild and restart the FortiGate Dashboard with our changes

echo "Rebuilding and restarting the FortiGate Dashboard..."

# Stop the containers
echo "Stopping containers..."
docker-compose -f docker-compose.yml down

# Build and run the containers
echo "Building and starting containers with docker-compose..."
docker-compose -f docker-compose.yml build
docker-compose -f docker-compose.yml up -d

# Check if the containers are running
echo "Checking container status..."
docker-compose -f docker-compose.yml ps

echo ""
echo "FortiGate Dashboard has been rebuilt and restarted."
echo "You can access the dashboard at: http://localhost:8001"
echo ""
echo "To view logs:"
echo "  docker-compose -f deploy/docker-compose.yml logs -f dashboard"
echo ""
echo "To stop the containers:"
echo "  docker-compose -f docker-compose.yml down"