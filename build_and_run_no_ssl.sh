#!/bin/bash

# Build and run the fixed Docker containers with SSL verification disabled

echo "Building and running the FortiGate Dashboard with SSL verification disabled..."

# Check if the secrets directory exists
if [ ! -d "./secrets" ]; then
    echo "Creating secrets directory..."
    mkdir -p ./secrets
fi

# Check if the API token file exists
if [ ! -f "./secrets/fortigate_api_token.txt" ]; then
    echo "Creating API token file..."
    echo "hmNqQ0st7xrjnyQHt8dzpnkqm5hw5N" > ./secrets/fortigate_api_token.txt
fi

# Check if the certificates directory exists
if [ ! -d "./app/certs" ]; then
    echo "Creating certificates directory..."
    mkdir -p ./app/certs
fi

# Check if the certificate file exists
if [ ! -f "./app/certs/fortigate.pem" ]; then
    echo "Warning: Certificate file not found at ./app/certs/fortigate.pem"
    echo "The application will run with SSL verification disabled."
fi

# Stop any existing containers
echo "Stopping any existing containers..."
docker-compose -f docker-compose.fixed.yml down

# Build and run the containers
echo "Building and starting containers with docker-compose..."
docker-compose -f docker-compose.no_ssl.yml build
docker-compose -f docker-compose.no_ssl.yml up -d

# Check if the containers are running
echo "Checking container status..."
docker-compose -f docker-compose.no_ssl.yml ps

echo ""
echo "FortiGate Dashboard is now running with SSL verification disabled."
echo "You can access the dashboard at: http://localhost:8001"
echo ""
echo "To view logs:"
echo "  docker-compose -f docker-compose.no_ssl.yml logs -f dashboard"
echo "  docker-compose -f docker-compose.no_ssl.yml logs -f wan_monitor"
echo ""
echo "To stop the containers:"
echo "  docker-compose -f docker-compose.no_ssl.yml down"