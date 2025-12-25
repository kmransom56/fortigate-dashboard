# Scanopy Integration Guide - Cisco Meraki CLI

## Overview

This guide details the integration between **Scanopy** (network discovery and visualization) and the **Cisco Meraki CLI FastAPI application**, creating a unified network management and visualization platform.

**Integration Benefits:**
- Combine Meraki cloud-managed infrastructure with on-premises network discovery
- Unified topology views showing both Meraki devices and discovered endpoints
- Automated service detection for connected devices (200+ services)
- Docker container discovery for containerized workloads
- Multi-VLAN topology mapping across QSR locations

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│  Cisco Meraki CLI Application (FastAPI - Port 11015)       │
│  ┌────────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │ Meraki API     │  │ Topology     │  │ Scanopy        │  │
│  │ Integration    │→→│ Visualizer   │←←│ API Client     │  │
│  └────────────────┘  └──────────────┘  └────────────────┘  │
│           ↓                 ↓                    ↓           │
└───────────┼─────────────────┼────────────────────┼─────────┘
            │                 │                    │
            ↓                 ↓                    ↓
   ┌────────────────┐  ┌──────────────┐  ┌────────────────┐
   │ Meraki Cloud   │  │ Enhanced     │  │ Scanopy Server │
   │ Dashboard API  │  │ Visualizations│  │ (Port 60072)   │
   └────────────────┘  └──────────────┘  └────────────────┘
                                                  │
                                                  ↓
                                         ┌────────────────┐
                                         │ Scanopy Daemon │
                                         │ (Port 60073)   │
                                         │ Network Scanner│
                                         └────────────────┘
```

---

## What Scanopy Provides

### 1. Network Discovery
- **Automatic Host Discovery**: Finds all devices on network segments
- **Service Detection**: Identifies 200+ services (databases, web servers, containers)
- **Docker Integration**: Discovers containerized services via Docker socket
- **MAC Vendor Lookup**: Identifies device manufacturers
- **Port Scanning**: Maps open ports on discovered hosts

### 2. Topology Visualization
- **Interactive Network Maps**: Visual representation of network topology
- **Grouping and Filtering**: Organize by subnet, service type, or custom groups
- **Scheduled Discovery**: Automated scans to keep documentation current
- **Multi-VLAN Support**: Maps complex network segments

### 3. Multi-Tenancy
- **Organization Management**: Separate views for different clients/locations
- **Role-Based Access**: User permissions and access control
- **API Access**: RESTful API for integration

---

## Integration Implementation

### API Endpoints Added

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/scanopy/status` | GET | Check Scanopy server health |
| `/api/scanopy/hosts` | GET | Get all discovered hosts |
| `/api/scanopy/host/{ip}` | GET | Get specific host details |
| `/api/scanopy/services` | GET | Get all detected services |
| `/api/scanopy/topology` | GET | Get network topology |
| `/api/scanopy/scan` | POST | Trigger network scan |
| `/api/unified/topology/{network_id}` | GET | Meraki + Scanopy combined |

### Example Usage

#### Check Scanopy Status
```bash
curl http://localhost:11015/api/scanopy/status | jq

# Response:
{
  "status": "healthy",
  "url": "http://localhost:60072",
  "available": true
}
```

#### Get All Discovered Hosts
```bash
curl http://localhost:11015/api/scanopy/hosts | jq

# Response:
{
  "hosts": [
    {
      "id": "192.168.1.100",
      "ip_address": "192.168.1.100",
      "mac_address": "00:11:22:33:44:55",
      "hostname": "pos-terminal-01",
      "vendor": "Cisco Systems",
      "services": [
        {
          "name": "SSH",
          "port": 22,
          "protocol": "tcp",
          "confidence": "High"
        },
        {
          "name": "Aloha POS",
          "port": 5432,
          "protocol": "tcp",
          "confidence": "High"
        }
      ]
    }
  ],
  "count": 45
}
```

#### Trigger Network Scan
```bash
curl -X POST http://localhost:11015/api/scanopy/scan \
  -H "Content-Type: application/json" \
  -d '{"subnet": "192.168.1.0/24", "scan_type": "full"}' | jq

# Response:
{
  "success": true,
  "subnet": "192.168.1.0/24",
  "scan_type": "full",
  "result": {
    "job_id": "scan_12345",
    "status": "queued"
  }
}
```

#### Get Unified Topology
```bash
curl http://localhost:11015/api/unified/topology/ARGLAB01 | jq

# Response:
{
  "network_id": "ARGLAB01",
  "meraki_devices": {
    "count": 0,
    "devices": []
  },
  "discovered_endpoints": {
    "count": 45,
    "hosts": [...]
  },
  "services_summary": {
    "types": ["SSH", "HTTP", "PostgreSQL", "Aloha POS"],
    "count": 4,
    "details": {
      "Aloha POS": [
        {
          "ip": "192.168.1.100",
          "hostname": "pos-terminal-01",
          "port": 5432
        }
      ]
    }
  }
}
```

---

## Docker Configuration

Scanopy services are configured in `docker-compose.full.yml`:

```yaml
services:
  # FastAPI Application
  cisco-meraki-fastapi:
    ports: ["11015:11015"]
    environment:
      - SCANOPY_URL=http://scanopy-server:60072
    networks:
      - meraki-network
      - scanopy

  # Scanopy Server
  scanopy-server:
    image: ghcr.io/scanopy/scanopy/server:latest
    ports: ["60072:60072"]
    environment:
      - SCANOPY_DATABASE_URL=postgresql://postgres:password@postgres:5432/scanopy
    depends_on:
      - postgres
      - daemon
    networks:
      - scanopy

  # Scanopy Daemon
  scanopy-daemon:
    image: ghcr.io/scanopy/scanopy/daemon:latest
    ports: ["60073:60073"]
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    networks:
      - scanopy

  # PostgreSQL Database
  postgres:
    image: postgres:17-alpine
    environment:
      - POSTGRES_DB=scanopy
      - POSTGRES_PASSWORD=password
    networks:
      - scanopy
```

---

## Use Cases

### Use Case 1: QSR Store Network Audit

**Goal**: Audit all devices at an Arby's location (ARGLAB01)

**Workflow**:
1. Scanopy discovers all devices (POS, KDS, menu boards, phones, etc.)
2. Meraki API provides managed infrastructure (switches, APs, firewall)
3. FastAPI combines both datasets
4. Enhanced visualization shows:
   - Meraki MS switches with port-level detail
   - Connected devices with service detection
   - QSR-specific icons and classifications
   - Network topology showing all interconnections

**Command**:
```bash
curl http://localhost:11015/api/unified/topology/ARGLAB01 | jq
```

### Use Case 2: Security Audit

**Goal**: Find all services running that shouldn't be exposed

**Workflow**:
1. Scanopy scans network and detects all open ports/services
2. FastAPI filters for high-risk services (databases, admin panels)
3. Cross-reference with Meraki firewall rules
4. Generate security report

**Command**:
```bash
# Get all hosts with PostgreSQL
curl http://localhost:11015/api/scanopy/hosts | jq '
  .hosts[] |
  select(
    .services[].name == "PostgreSQL"
  )
'
```

### Use Case 3: Service Inventory

**Goal**: Generate complete inventory of all services

**Workflow**:
1. Get all Scanopy discovered services
2. Group by service type
3. Export as documentation

**Command**:
```bash
curl http://localhost:11015/api/scanopy/services | jq
```

---

## Environment Variables

Add to `.env` file:

```bash
# Scanopy Integration
SCANOPY_URL=http://localhost:60072
SCANOPY_API_TOKEN=your_token_here  # Optional
```

---

## Testing

### Start Services

```bash
# Start full stack including Scanopy
docker-compose -f docker_config/docker-compose.full.yml up -d

# Verify services are running
docker-compose -f docker_config/docker-compose.full.yml ps
```

### Test Integration

```bash
# 1. Check Scanopy status
curl http://localhost:11015/api/scanopy/status | jq

# 2. Wait for initial scan (~5 minutes)

# 3. Get discovered hosts
curl http://localhost:11015/api/scanopy/hosts | jq

# 4. View in Scanopy UI
open http://localhost:60072
```

---

## Troubleshooting

### Issue: Scanopy status returns unavailable

**Solutions**:
1. Verify Scanopy is running: `docker ps | grep scanopy`
2. Check health: `curl http://localhost:60072/health`
3. Review logs: `docker logs scanopy-server`

### Issue: No hosts discovered

**Solutions**:
1. Trigger manual scan: `POST /api/scanopy/scan`
2. Check daemon logs: `docker logs scanopy-daemon`
3. Wait for initial discovery (5-10 minutes)

---

## Resources

- **Scanopy Documentation**: docs/scanopy/
- **Scanopy UI**: http://localhost:60072
- **FastAPI Docs**: http://localhost:11015/docs
- **Service Definitions**: https://scanopy.net/services

---

**Created**: 2025-12-24
**Status**: Production Ready ✅
