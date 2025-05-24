#!/bin/bash

# FortiGate Dashboard & Troubleshooter Installation Script
# This script helps you easily install and run the FortiGate Dashboard application

# Color codes for better readability
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=======================================${NC}"
echo -e "${BLUE}FortiGate Dashboard Installation Script${NC}"
echo -e "${BLUE}=======================================${NC}"
echo

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed.${NC}"
    echo -e "Please install Docker before continuing:"
    echo -e "https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed.${NC}"
    echo -e "Please install Docker Compose before continuing:"
    echo -e "https://docs.docker.com/compose/install/"
    exit 1
fi

# Check if .env file exists, create it if not
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file for configuration...${NC}"
    
    # Prompt for FortiGate configuration
    read -p "Enter your FortiGate IP address [default: 192.168.0.254]: " fortigate_ip
    fortigate_ip=${fortigate_ip:-192.168.0.254}
    
    read -p "Enter your FortiGate API token: " api_token
    
    # Create .env file
    cat > .env << EOF
# FortiGate Dashboard Configuration
FORTIGATE_HOST=https://$fortigate_ip
FORTIGATE_API_TOKEN=$api_token

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# Logging Configuration
LOG_LEVEL=INFO
EOF
    
    echo -e "${GREEN}Configuration file created successfully.${NC}"
else
    echo -e "${GREEN}Using existing .env configuration file.${NC}"
fi

# Create necessary directories
mkdir -p logs
mkdir -p app/certs

# Check if SSL certificate exists
if [ ! -f app/certs/cert.pem ] || [ ! -f app/certs/key.pem ]; then
    echo -e "${YELLOW}Creating self-signed SSL certificate...${NC}"
    
    # Generate self-signed certificate
    openssl req -x509 -newkey rsa:2048 -keyout app/certs/key.pem -out app/certs/cert.pem -days 365 -nodes -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
    
    echo -e "${GREEN}SSL certificate created successfully.${NC}"
else
    echo -e "${GREEN}Using existing SSL certificate.${NC}"
fi

# Build and start the Docker containers
echo -e "${YELLOW}Building and starting Docker containers...${NC}"
docker-compose up -d --build

# Check if containers are running
if [ $? -eq 0 ]; then
    echo -e "${GREEN}FortiGate Dashboard installed successfully!${NC}"
    echo
    echo -e "${BLUE}Access your applications at:${NC}"
    echo -e "Dashboard: ${GREEN}http://localhost:8001${NC}"
    echo -e "Troubleshooter: ${GREEN}https://localhost:5002${NC}"
    echo
    echo -e "${YELLOW}Note:${NC} The SSL certificate is self-signed, so you may need to accept the security warning in your browser."
else
    echo -e "${RED}Error: Failed to start Docker containers.${NC}"
    echo -e "Please check the logs for more information:"
    echo -e "docker-compose logs"
fi

echo
echo -e "${BLUE}=======================================${NC}"
echo -e "${BLUE}      Installation Complete           ${NC}"
echo -e "${BLUE}=======================================${NC}"
