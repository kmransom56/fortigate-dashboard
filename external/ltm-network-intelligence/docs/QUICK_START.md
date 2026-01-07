# LTM Network Intelligence Platform - Quick Start Guide

## Overview

Get up and running with the LTM Network Intelligence Platform in minutes. This guide covers the essential steps to deploy and use the platform for network device management and observability.

## Prerequisites

- Python 3.8 or higher
- Docker and Docker Compose (optional but recommended)
- Git
- At least 4GB RAM and 10GB disk space

## Installation Methods

### Method 1: Quick Setup (Recommended)

```bash
# Clone the repository
git clone [your-repository-url] ltm-platform
cd ltm-platform

# Run the quick setup script
chmod +x scripts/quick_setup.sh
./scripts/quick_setup.sh
```

### Method 2: Manual Setup

```bash
# Clone the repository
git clone [your-repository-url] ltm-platform
cd ltm-platform

# Create virtual environment
python -m venv ltm-venv
source ltm-venv/bin/activate  # On Windows: ltm-venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize platform
python unified_network_intelligence.py --initialize
```

### Method 3: Docker Setup

```bash
# Clone the repository
git clone [your-repository-url] ltm-platform
cd ltm-platform

# Start with Docker Compose
docker-compose up -d

# Check status
docker-compose ps
```

## First Run

### 1. Initialize the Platform

```bash
# Initialize with all components
python unified_network_intelligence.py --initialize --components ltm,mcp,kg,security,performance,api

# Or initialize step by step
python unified_network_intelligence.py --initialize --components ltm
python unified_network_intelligence.py --initialize --components mcp,api
```

### 2. Configure Your Environment

Edit the configuration file `config/unified_config.json`:

```json
{
  "platform": {
    "name": "My Network Intelligence Platform",
    "environment": "development"
  },
  "ltm": {
    "server_url": "http://localhost:8000",
    "learning_enabled": true
  },
  "components": {
    "knowledge_graph": {
      "neo4j_uri": "bolt://localhost:7687",
      "neo4j_user": "neo4j",
      "neo4j_password": "your_password_here"
    }
  }
}
```

### 3. Start the Platform

```bash
# Start the platform
python unified_network_intelligence.py

# Or run specific components
python unified_network_intelligence.py --components ltm,api,performance
```

## Quick Usage Examples

### Example 1: Basic Network Analysis

```python
from unified_network_intelligence import UnifiedNetworkIntelligencePlatform

# Initialize platform
platform = UnifiedNetworkIntelligencePlatform()
await platform.initialize()

# Run network analysis
analysis = await platform.analyze_network_holistically()
print(f"Network health: {analysis['executive_summary']['overall_health']}")
print(f"Systems analyzed: {len(analysis['systems_contributing'])}")
```

### Example 2: Device Management via API

```bash
# Login to get JWT token
curl -X POST "http://localhost:8002/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Get device status (replace TOKEN with actual JWT)
curl -X GET "http://localhost:8002/api/devices/fortigate-fw01/status" \
  -H "Authorization: Bearer TOKEN"

# Analyze network health
curl -X GET "http://localhost:8002/api/analysis/health?scope=all" \
  -H "Authorization: Bearer TOKEN"
```

### Example 3: LTM Memory Search

```python
# Search LTM for network patterns
from ltm_integration import LTMClient

ltm = LTMClient("http://localhost:8000")
await ltm.initialize()

# Search for performance patterns
memories = await ltm.search_memories(
    query="network performance issues FortiGate",
    tags=["performance", "troubleshooting"],
    limit=10
)

for memory in memories:
    print(f"Relevance: {memory.relevance_score:.2f}")
    print(f"Content: {memory.content}")
    print("---")
```

## Web Dashboard Access

Once the platform is running, access the web interfaces:

- **API Documentation**: http://localhost:8002/api/docs
- **Prometheus Metrics**: http://localhost:8003/metrics
- **Neo4j Browser**: http://localhost:7474 (if Neo4j is running)

## Configuration Quick Reference

### Essential Configuration Files

```
config/
├── unified_config.json          # Main platform configuration
├── devices_enhanced.json        # Device configurations
├── security_config.json         # Security settings
├── api_gateway_config.json      # API gateway settings
├── performance_config.json      # Performance monitoring
└── network_persona.json         # LTM persona configuration
```

### Key Environment Variables

```bash
# LTM Configuration
export LTM_SERVER_URL="http://localhost:8000"
export LTM_LEARNING_ENABLED="true"

# Database Configuration
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="your_password"
export MILVUS_HOST="localhost"
export MILVUS_PORT="19530"
export REDIS_URL="redis://localhost:6379"

# API Configuration
export API_GATEWAY_PORT="8002"
export JWT_SECRET="your-secure-jwt-secret"

# Device API Keys
export FORTIGATE_API_KEY="your_fortigate_api_key"
export MERAKI_API_KEY="your_meraki_api_key"
```

## Adding Your First Device

### 1. Configure Device

Add to `config/devices_enhanced.json`:

```json
{
  "devices": {
    "my-fortigate": {
      "type": "FortiGate",
      "host": "192.168.1.1",
      "port": 443,
      "credentials": {
        "username": "admin",
        "api_key": "${FORTIGATE_API_KEY}"
      },
      "monitoring": {
        "enabled": true,
        "interval_seconds": 30
      },
      "ltm_context": {
        "device_role": "primary_firewall",
        "criticality": "high"
      }
    }
  }
}
```

### 2. Test Device Connection

```bash
# Test via API
curl -X GET "http://localhost:8002/api/devices/my-fortigate/status" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 3. Monitor Device

```python
# Monitor device performance
from unified_network_intelligence import UnifiedNetworkIntelligencePlatform

platform = UnifiedNetworkIntelligencePlatform()
await platform.initialize()

# Get device insights
device_insights = await platform.mcp_server._get_device_status_enhanced(
    "my-fortigate", 
    include_ltm_insights=True
)

print(f"Device: {device_insights['device_name']}")
print(f"Status: {device_insights['current_status']['health_status']}")
print(f"LTM Insights: {len(device_insights['ltm_insights']['recent_insights'])}")
```

## Common Commands

### Platform Management

```bash
# Start platform
python unified_network_intelligence.py

# Initialize specific components
python unified_network_intelligence.py --initialize --components ltm,mcp

# Run analysis
python unified_network_intelligence.py --analyze

# Generate dashboard
python unified_network_intelligence.py --dashboard

# Health check
python unified_network_intelligence.py --health-check
```

### API Gateway

```bash
# Start API gateway
python api_gateway/ltm_api_gateway.py

# Test authentication
curl -X POST "http://localhost:8002/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### Performance Monitoring

```bash
# Start performance monitor
python -c "
import asyncio
from monitoring import LTMPerformanceMonitor
from ltm_integration import LTMClient

async def start_monitoring():
    ltm = LTMClient()
    await ltm.initialize()
    
    monitor = LTMPerformanceMonitor(ltm)
    await monitor.initialize()
    await monitor.start()
    
    # Keep running
    await asyncio.sleep(3600)

asyncio.run(start_monitoring())
"
```

## Monitoring and Observability

### Key Metrics to Watch

1. **System Health**
   - CPU usage < 80%
   - Memory usage < 85%
   - Disk usage < 85%

2. **LTM Performance**
   - Response time < 2000ms
   - Memory growth rate
   - Session activity

3. **API Gateway**
   - Request rate
   - Error rate < 5%
   - Response time < 500ms

### Log Locations

```
logs/
├── ltm_platform.log             # Main platform logs
├── security_audit.log           # Security events
├── performance.log              # Performance metrics
├── api_gateway.log              # API requests/responses
└── integration.log              # Repository integration logs
```

### Health Check Commands

```bash
# Platform health
curl -X GET "http://localhost:8002/health"

# Detailed component status
python -c "
import asyncio
from unified_network_intelligence import UnifiedNetworkIntelligencePlatform

async def check_health():
    platform = UnifiedNetworkIntelligencePlatform()
    await platform.initialize()
    
    # Check all components
    status = await platform.get_platform_status()
    print(f'Overall Status: {status[\"overall_status\"]}')
    for component, health in status['components'].items():
        print(f'{component}: {health}')

asyncio.run(check_health())
"
```

## Troubleshooting Quick Fixes

### Issue: LTM Not Connecting

```bash
# Check if LTM server is running
curl -X GET "http://localhost:8000/health"

# Start LTM server if not running
python -m ltm_server --port 8000
```

### Issue: Database Connection Failed

```bash
# Check Neo4j
docker run --rm neo4j:latest neo4j status

# Check Redis
redis-cli ping

# Check if ports are open
netstat -tuln | grep -E ':(7687|6379|19530)'
```

### Issue: API Gateway Not Responding

```bash
# Check if port is available
netstat -tuln | grep :8002

# Restart API gateway
python api_gateway/ltm_api_gateway.py --config config/api_gateway_config.json
```

### Issue: Performance Monitor Alerts

```bash
# Check system resources
top
df -h
free -h

# Check monitoring logs
tail -f logs/performance.log
```

## Next Steps

1. **Add More Devices**: Configure additional FortiGate, Meraki, or other devices
2. **Setup Knowledge Graph**: Configure Neo4j and Milvus for advanced analytics
3. **Enable Security Framework**: Configure compliance monitoring and audit logging
4. **Integrate Existing Repositories**: Follow the Integration Guide to connect your existing tools
5. **Configure Dashboards**: Set up custom dashboards for your specific needs
6. **Set up Monitoring**: Configure alerts and notifications for critical events

## Getting Help

- **Documentation**: Check the `/docs` folder for detailed guides
- **API Reference**: Visit `http://localhost:8002/api/docs` when the platform is running
- **Logs**: Check the `/logs` folder for error messages and debugging information
- **Configuration**: Review and validate your configuration files
- **Health Checks**: Run the built-in health checks to identify issues

## Example Production Setup

For a production deployment, consider this minimal setup:

```bash
# 1. Clone and setup
git clone [repository] ltm-production
cd ltm-production

# 2. Create production config
cp config/unified_config.json config/production_config.json
# Edit production_config.json with your production settings

# 3. Set environment variables
export ENVIRONMENT=production
export LTM_CONFIG_PATH=config/production_config.json
export NEO4J_PASSWORD=$(openssl rand -base64 32)
export JWT_SECRET=$(openssl rand -base64 64)

# 4. Start with docker-compose
docker-compose -f docker-compose.production.yml up -d

# 5. Initialize
docker-compose exec ltm-platform python unified_network_intelligence.py --initialize

# 6. Verify
curl -X GET "http://localhost:8002/health"
```

This quick start guide should have you up and running with the LTM Network Intelligence Platform. For more advanced configuration and integration with existing repositories, see the Integration Guide.