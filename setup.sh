#!/bin/bash

# FortiGate Network Operations Platform - Quick Setup Script
# Deploys: Topology Visualization, Switch Discovery, Grafana, OSI Troubleshooting

set -e

echo "🚀 FortiGate Network Operations Platform - Setup"
echo "================================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/home/keith/fortigate-dashboard"
BACKUP_DIR="/media/keith/Windows Backup/projects/fortigate-dashboard"

echo "📁 Checking project directories..."
if [ -d "$PROJECT_DIR" ]; then
    DEPLOY_DIR="$PROJECT_DIR"
    echo -e "${GREEN}✓${NC} Using: $PROJECT_DIR"
elif [ -d "$BACKUP_DIR" ]; then
    DEPLOY_DIR="$BACKUP_DIR"
    echo -e "${GREEN}✓${NC} Using: $BACKUP_DIR"
else
    echo -e "${RED}✗${NC} Project directory not found!"
    echo "Please update PROJECT_DIR in this script"
    exit 1
fi

cd "$DEPLOY_DIR"

# Step 1: Create directory structure
echo ""
echo "📂 Creating directory structure..."
mkdir -p app/services
mkdir -p app/routers
mkdir -p app/exporters
mkdir -p monitoring/grafana
mkdir -p monitoring/prometheus

echo -e "${GREEN}✓${NC} Directories created"

# Step 2: Check if files are present
echo ""
echo "📋 Checking for integration files..."

FILES=(
    "topology_visualization.py"
    "switch_discovery.py"
    "osi_troubleshooting_integration.py"
    "network_operations_router.py"
    "grafana-dashboard-fortigate.json"
)

MISSING_FILES=0
for file in "${FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}✗${NC} Missing: $file"
        MISSING_FILES=$((MISSING_FILES + 1))
    else
        echo -e "${GREEN}✓${NC} Found: $file"
    fi
done

if [ $MISSING_FILES -gt 0 ]; then
    echo ""
    echo -e "${YELLOW}⚠${NC}  $MISSING_FILES files missing. Please download them first."
    echo "Download from Claude.ai and place in: $DEPLOY_DIR"
    exit 1
fi

# Step 3: Move files to correct locations
echo ""
echo "📦 Installing integration modules..."

cp topology_visualization.py app/services/
cp switch_discovery.py app/services/
cp osi_troubleshooting_integration.py app/services/
cp network_operations_router.py app/routers/
cp grafana-dashboard-fortigate.json monitoring/grafana/

echo -e "${GREEN}✓${NC} Files installed"

# Step 4: Check if main.py exists and needs updating
echo ""
echo "🔧 Checking main.py..."

if [ ! -f "app/main.py" ]; then
    echo -e "${RED}✗${NC} app/main.py not found!"
    echo "Please create app/main.py first"
    exit 1
fi

if grep -q "network_operations_router" app/main.py; then
    echo -e "${GREEN}✓${NC} Router already imported in main.py"
else
    echo -e "${YELLOW}⚠${NC}  Need to add router import to main.py"
    echo ""
    echo "Add this to your app/main.py:"
    echo ""
    echo "from app.routers.network_operations_router import router as network_router"
    echo "app.include_router(network_router)"
    echo ""
fi

# Step 5: Check dependencies
echo ""
echo "📦 Checking Python dependencies..."

REQUIRED_DEPS=("neo4j" "aiohttp" "redis")

if [ -f "requirements.txt" ]; then
    echo -e "${GREEN}✓${NC} requirements.txt found"
    
    for dep in "${REQUIRED_DEPS[@]}"; do
        if grep -q "$dep" requirements.txt; then
            echo -e "${GREEN}✓${NC} $dep in requirements.txt"
        else
            echo -e "${YELLOW}⚠${NC}  Add $dep to requirements.txt"
        fi
    done
elif [ -f "pyproject.toml" ]; then
    echo -e "${GREEN}✓${NC} pyproject.toml found"
    echo "Add dependencies: neo4j, aiohttp, redis"
else
    echo -e "${RED}✗${NC} No dependency file found"
fi

# Step 6: Check Docker containers
echo ""
echo "🐳 Checking Docker containers..."

if command -v docker &> /dev/null; then
    REQUIRED_CONTAINERS=("neo4j" "redis" "postgres" "grafana" "prometheus")
    
    for container in "${REQUIRED_CONTAINERS[@]}"; do
        if docker ps | grep -q "$container"; then
            echo -e "${GREEN}✓${NC} $container is running"
        else
            echo -e "${YELLOW}⚠${NC}  $container is not running"
        fi
    done
else
    echo -e "${YELLOW}⚠${NC}  Docker not available from this script"
fi

# Step 7: Check environment variables
echo ""
echo "🔐 Checking environment configuration..."

ENV_FILE=".env"
if [ -f "$ENV_FILE" ]; then
    echo -e "${GREEN}✓${NC} .env file exists"
    
    REQUIRED_VARS=("NEO4J_URI" "FORTIGATE_HOST" "FORTIGATE_PORT" "REDIS_HOST")
    
    for var in "${REQUIRED_VARS[@]}"; do
        if grep -q "^$var=" "$ENV_FILE"; then
            echo -e "${GREEN}✓${NC} $var configured"
        else
            echo -e "${YELLOW}⚠${NC}  $var not found in .env"
        fi
    done
else
    echo -e "${YELLOW}⚠${NC}  No .env file found"
    echo "Create .env with:"
    echo "  NEO4J_URI=bolt://neo4j:7687"
    echo "  FORTIGATE_HOST=192.168.0.254"
    echo "  FORTIGATE_PORT=10443"
    echo "  REDIS_HOST=redis"
fi

# Step 8: Summary and next steps
echo ""
echo "================================================"
echo "✅ Setup Complete!"
echo "================================================"
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Install Python dependencies:"
echo "   ${GREEN}uv pip install neo4j aiohttp redis${NC}"
echo ""
echo "2. Update app/main.py to include the router:"
echo "   ${GREEN}from app.routers.network_operations_router import router as network_router${NC}"
echo "   ${GREEN}app.include_router(network_router)${NC}"
echo ""
echo "3. Restart your application:"
echo "   ${GREEN}docker-compose restart fortigate-dashboard${NC}"
echo ""
echo "4. Import Grafana dashboard:"
echo "   - Go to http://localhost:3001"
echo "   - Dashboards → Import"
echo "   - Upload: monitoring/grafana/grafana-dashboard-fortigate.json"
echo ""
echo "5. Test the integration:"
echo "   ${GREEN}curl http://localhost:8000/api/network/dashboard/overview | jq '.'${NC}"
echo ""
echo "📚 Full documentation: ${GREEN}DEPLOYMENT_GUIDE.md${NC}"
echo ""
echo "🎯 API docs: ${GREEN}http://localhost:8000/docs${NC}"
echo ""

# Optional: Open documentation
read -p "Open DEPLOYMENT_GUIDE.md? (y/n): " open_docs
if [ "$open_docs" = "y" ]; then
    if command -v less &> /dev/null; then
        less DEPLOYMENT_GUIDE.md
    elif command -v cat &> /dev/null; then
        cat DEPLOYMENT_GUIDE.md
    fi
fi

echo ""
echo "Happy deploying! 🚀"
