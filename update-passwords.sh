#!/bin/bash

echo "FortiGate Dashboard Password Update Script"
echo "==========================================="
echo ""

# Function to update passwords
update_passwords() {
    echo "Current passwords are placeholders. Please update them in:"
    echo "1. docker-compose.yml"
    echo "2. .env"
    echo ""
    echo "To apply the changes, you need to recreate the containers:"
    echo ""
    echo "For Neo4j (data will be preserved):"
    echo "  docker compose stop neo4j"
    echo "  docker volume rm fortigate-dashboard_neo4j_data  # WARNING: This deletes data!"
    echo "  docker compose up -d neo4j"
    echo ""
    echo "For Grafana (will preserve dashboards if using volume):"
    echo "  docker compose restart grafana"
    echo ""
    echo "Recommended: Update passwords, then run:"
    echo "  docker compose down"
    echo "  docker compose up -d"
    echo ""
}

# Show current configuration
echo "Current Password Locations:"
echo "============================"
echo ""
echo "Neo4j:"
echo "  - docker-compose.yml: NEO4J_AUTH=neo4j/letsencrypt#0$"
echo "  - .env: NEO4J_PASSWORD=letsencrypt#0$"
echo "  - Access: http://localhost:11103"
echo ""
echo "Grafana:"
echo "  - docker-compose.yml: GF_SECURITY_ADMIN_PASSWORD=letsencrypt#0$"
echo "  - Username: admin"
echo "  - Access: http://localhost:11106"
echo ""
echo "Prometheus:"
echo "  - No authentication configured (public access)"
echo "  - Access: http://localhost:11105"
echo ""

update_passwords
