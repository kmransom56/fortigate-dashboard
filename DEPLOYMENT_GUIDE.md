# FortiGate Network Operations Platform - Deployment Guide

## Overview
Complete integration of:
- 🗺️ Network Topology Visualization (Neo4j)
- 🔄 Switch Discovery & Management
- 📊 Grafana Monitoring Dashboards  
- 🔧 OSI Troubleshooting Agents (14 agents, 13 tools)

**Scale**: 370,000 devices across 20,247 locations

---

## Quick Start

### 1. Deploy to Your Server

```bash
# Copy all files to your project
cd /home/keith/fortigate-dashboard

# Place files in your app directory
mkdir -p app/services app/routers monitoring/grafana

# Copy Python modules
cp topology_visualization.py app/services/
cp switch_discovery.py app/services/
cp osi_troubleshooting_integration.py app/services/
cp network_operations_router.py app/routers/

# Copy Grafana dashboard
cp grafana-dashboard-fortigate.json monitoring/grafana/
```

### 2. Update main.py to Include New Router

```python
# Add to your app/main.py
from app.routers.network_operations_router import router as network_router

app = FastAPI(title="Device Automation Platform")

# Include the unified network operations router
app.include_router(network_router)
```

### 3. Install Dependencies

```bash
# Add to requirements.txt or pyproject.toml
neo4j>=5.15.0
aiohttp>=3.9.0
redis>=5.0.0
```

If using uv:
```bash
uv pip install neo4j aiohttp redis
```

### 4. Configure Environment Variables

Add to your `.env` or docker-compose.yml:

```bash
# Neo4j
NEO4J_URI=bolt://neo4j:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=neo4j_password

# FortiGate
FORTIGATE_HOST=192.168.0.254
FORTIGATE_PORT=10443
FORTIGATE_API_TOKEN=your_token_here

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
```

### 5. Restart Services

```bash
docker-compose restart fortigate-dashboard
```

---

## API Endpoints

### Topology Visualization

```bash
# Get full network topology
GET /api/network/topology/full

# Get topology around specific device
GET /api/network/topology/device/{device_id}?depth=2

# Find path between devices
GET /api/network/topology/path/{source_id}/{target_id}

# Rebuild topology (background task)
POST /api/network/topology/rebuild
```

### Switch Discovery

```bash
# List all switches
GET /api/network/switches

# Get switch details
GET /api/network/switches/{switch_id}

# Get switch health
GET /api/network/switches/{switch_id}/health

# Auto-configure switch
POST /api/network/switches/{switch_id}/configure?template=standard

# Generate switches report
GET /api/network/switches/report/summary

# Scan for rogue devices
GET /api/network/security/rogue-devices
```

### OSI Troubleshooting

```bash
# Analyze entire network
GET /api/network/troubleshooting/analyze

# Analyze specific device
GET /api/network/troubleshooting/device/{device_id}

# Get remediation plan
GET /api/network/troubleshooting/remediation-plan
```

### Unified Dashboard

```bash
# Complete dashboard overview
GET /api/network/dashboard/overview

# Enterprise metrics
GET /api/network/dashboard/enterprise
```

---

## Grafana Dashboard Setup

### 1. Import Dashboard

```bash
# Access Grafana
http://localhost:3001

# Login (default: admin/admin_password)

# Go to: Dashboards → Import
# Upload: grafana-dashboard-fortigate.json
```

### 2. Configure Prometheus Data Source

```bash
# Go to: Configuration → Data Sources → Add data source
# Select: Prometheus
# URL: http://prometheus:9090
# Save & Test
```

### 3. Create Prometheus Exporter (Optional)

For custom metrics, create `app/exporters/fortigate_exporter.py`:

```python
from prometheus_client import Counter, Gauge, Histogram
from prometheus_client import start_http_server

# Define metrics
switch_status = Gauge('fortigate_switch_status', 'Switch status', ['switch_name', 'status'])
switch_cpu = Gauge('fortigate_switch_cpu_usage', 'Switch CPU usage', ['switch_name'])
switch_memory = Gauge('fortigate_switch_memory_usage', 'Switch memory usage', ['switch_name'])
port_status = Gauge('fortigate_switch_port_status', 'Port status', ['switch_name', 'port', 'status'])

async def export_metrics():
    # Update metrics from your switch discovery service
    service = SwitchDiscoveryService(...)
    switches = await service.discover_switches()
    
    for switch in switches:
        switch_status.labels(switch_name=switch.name, status=switch.status).set(1)
        switch_cpu.labels(switch_name=switch.name).set(switch.cpu_usage or 0)
        switch_memory.labels(switch_name=switch.name).set(switch.memory_usage or 0)
        
        for port in switch.ports:
            port_status.labels(
                switch_name=switch.name,
                port=port.name,
                status=port.status
            ).set(1 if port.status == "up" else 0)

# Start exporter on port 9100
if __name__ == "__main__":
    start_http_server(9100)
    # Run export_metrics() periodically
```

---

## Neo4j Topology Queries

Useful Cypher queries for network analysis:

```cypher
// Find all switches
MATCH (n:Device {type: 'fortiswitch'})
RETURN n

// Find devices with most connections (critical devices)
MATCH (n:Device)-[r]-()
WITH n, count(r) as connections
WHERE connections > 5
RETURN n.name, n.type, connections
ORDER BY connections DESC

// Find isolated devices
MATCH (n:Device)
WHERE NOT (n)--()
RETURN n.name, n.type

// Find shortest path between two devices
MATCH path = shortestPath(
  (a:Device {id: 'device1'})-[*]-(b:Device {id: 'device2'})
)
RETURN path

// Network diameter (longest shortest path)
MATCH (a:Device), (b:Device)
WHERE a <> b
WITH a, b, length(shortestPath((a)-[*]-(b))) as distance
RETURN max(distance) as network_diameter
```

Access Neo4j Browser: `http://localhost:7475`

---

## OSI Troubleshooting Integration

### Architecture

```
┌─────────────────────────────────────────┐
│   FortiGate Dashboard (FastAPI)         │
├─────────────────────────────────────────┤
│                                          │
│  ┌────────────────────────────────────┐ │
│  │  Network Operations Router         │ │
│  └──────┬─────────┬──────────┬────────┘ │
│         │         │          │           │
│    ┌────▼────┐ ┌──▼──────┐ ┌▼────────┐ │
│    │Topology │ │ Switch  │ │   OSI   │ │
│    │ Service │ │Discovery│ │Agents(14)│ │
│    └────┬────┘ └──┬──────┘ └┬────────┘ │
│         │         │          │           │
└─────────┼─────────┼──────────┼───────────┘
          │         │          │
     ┌────▼────┐ ┌──▼─────┐ ┌─▼────────┐
     │  Neo4j  │ │FortiGate│ │Analytics │
     │ (Graph) │ │   API   │ │  Engine  │
     └─────────┘ └─────────┘ └──────────┘
```

### OSI Agent Layers

1. **Layer 1 (Physical)**: Cable issues, port status, signal strength
2. **Layer 2 (Data Link)**: VLAN, MAC tables, STP, broadcast storms
3. **Layer 3 (Network)**: Routing, IP conflicts, subnet issues
4. **Layer 4-7**: Extended with your custom agents

### Running Full Analysis

```bash
# Run complete network analysis
curl http://localhost:8000/api/network/troubleshooting/analyze

# Response includes:
# - Health score (0-100)
# - Issues by severity
# - Issues by OSI layer
# - Remediation plan
```

---

## Enterprise Deployment

For 370K devices scale:

### 1. Horizontal Scaling

```yaml
# docker-compose.prod.yml
services:
  fortigate-dashboard:
    deploy:
      replicas: 6
      resources:
        limits:
          cpus: '4'
          memory: 8G
```

### 2. Database Clustering

- **Redis**: 6-node cluster for session management
- **PostgreSQL**: Primary + 2 replicas
- **Neo4j**: 3-core cluster for topology

### 3. Load Balancing

```nginx
upstream fortigate_backend {
    least_conn;
    server fortigate-dashboard-1:8000;
    server fortigate-dashboard-2:8000;
    server fortigate-dashboard-3:8000;
}
```

### 4. Monitoring & Alerting

Set up alerts in Grafana for:
- CPU > 80%
- Memory > 90%
- Port utilization > 90%
- Switches offline > 5%
- Critical OSI issues detected

---

## Testing the Integration

### 1. Test Topology

```bash
# Build initial topology
curl -X POST http://localhost:8000/api/network/topology/rebuild

# Wait 30 seconds, then view it
curl http://localhost:8000/api/network/topology/full | jq '.'
```

### 2. Test Switch Discovery

```bash
# Discover all switches
curl http://localhost:8000/api/network/switches | jq '.'

# Get report
curl http://localhost:8000/api/network/switches/report/summary | jq '.'
```

### 3. Test OSI Agents

```bash
# Run full analysis
curl http://localhost:8000/api/network/troubleshooting/analyze | jq '.health'

# Get remediation plan
curl http://localhost:8000/api/network/troubleshooting/remediation-plan | jq '.'
```

### 4. Test Dashboard

```bash
# Get unified overview
curl http://localhost:8000/api/network/dashboard/overview | jq '.'
```

---

## Troubleshooting

### Neo4j Connection Issues

```bash
# Check Neo4j is running
docker ps | grep neo4j

# Test connection
docker exec fortigate-neo4j cypher-shell -u neo4j -p neo4j_password "RETURN 1"

# View logs
docker logs fortigate-neo4j --tail=50
```

### FortiGate API Issues

```bash
# Test API connectivity
curl -k https://192.168.0.254:10443/api/v2/cmdb/system/status \
  -H "Authorization: Bearer YOUR_TOKEN"

# Check credentials in container
docker exec fortigate-dashboard env | grep FORTIGATE
```

### Performance Issues

```bash
# Check resource usage
docker stats fortigate-dashboard

# Check slow queries in Neo4j
docker exec fortigate-neo4j cypher-shell -u neo4j -p neo4j_password \
  "CALL dbms.listQueries()"
```

---

## Next Steps

1. **Customize OSI Agents**: Add your remaining 11 agents (Layer 4-7)
2. **Add More Dashboards**: Create role-specific Grafana dashboards
3. **Set Up Alerting**: Configure alert rules for critical issues
4. **Integrate External Tools**: Connect Meraki, SNMP, Syslog
5. **Build UI**: Create React/Vue frontend for topology visualization
6. **Grant Application**: Prepare for Hiring Our Heroes grant (Dec 15)

---

## Support & Resources

- **Documentation**: http://localhost:8000/docs
- **Neo4j Browser**: http://localhost:7475
- **Grafana**: http://localhost:3001
- **Prometheus**: http://localhost:9091

For issues or questions, check the logs:
```bash
docker-compose logs -f fortigate-dashboard
```

---

## Market Opportunity Summary

**Your OSI Troubleshooting Platform:**
- ✅ 14 AI agents, 13 tools (AutoGen)
- ✅ Validated $2.8B market
- ✅ SaaS pricing: $199-999/month
- ✅ Target: $180K-2.4M ARR
- ✅ 60-80% cost savings vs competitors
- ✅ De-risked side hustle → $100K ARR

**Grant Deadline**: December 15, 2024 (Hiring Our Heroes)

---

**Ready to deploy!** 🚀
