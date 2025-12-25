# Scanopy Integration Summary

## Investigation Results

**Date**: 2025-01-XX  
**Status**: ✅ **Integration Complete** - Services added to docker-compose.yml

---

## What is Scanopy?

**Scanopy** is a network discovery and visualization tool that:
- Automatically discovers hosts and services on your network
- Detects 200+ services (databases, web servers, containers, etc.)
- Generates interactive network topology diagrams
- Provides distributed scanning across network segments
- Integrates with Docker for container discovery

**Technology Stack**: Rust (backend), Svelte (UI), PostgreSQL (database)

---

## Current Integration Status

### ✅ Fully Implemented

1. **API Client** (`app/services/scanopy_service.py`)
   - Async HTTP client with connection pooling
   - Health check, host discovery, service detection
   - Topology retrieval, scan triggering
   - Error handling and retry logic

2. **API Endpoints** (8 endpoints in `app/main.py`)
   - `/api/scanopy/status` - Health check
   - `/api/scanopy/hosts` - Discovered hosts
   - `/api/scanopy/host/{ip}` - Host details
   - `/api/scanopy/services` - Detected services
   - `/api/scanopy/topology` - Network topology
   - `/api/scanopy/scan` - Trigger scan
   - `/api/scanopy/networks` - Network list
   - `/api/unified/topology` - Combined topology

3. **Topology Integration** (`app/services/hybrid_topology_service_optimized.py`)
   - Automatically enhances topology with Scanopy data
   - Adds standalone discovered hosts
   - Enriches devices with service information

4. **Docker Services** (Added to `docker-compose.yml`)
   - `scanopy-server` - Main server (port 60072)
   - `scanopy-daemon` - Network scanner (port 60073)
   - `scanopy-postgres` - Database for Scanopy

---

## Integration Benefits

### 1. Enhanced Device Discovery
- **Complements FortiGate API**: Discovers devices FortiGate doesn't see
- **Service Detection**: Identifies what's running on each device
- **MAC Vendor Lookup**: Automatic manufacturer identification
- **Port Mapping**: Maps open ports to services

### 2. Unified Topology
- **Combined View**: FortiGate infrastructure + discovered endpoints
- **Service Badges**: Visual indicators for detected services
- **Relationship Mapping**: Shows device connections
- **Multi-Source Data**: FortiGate, Meraki, SNMP, and Scanopy

### 3. Network Documentation
- **Automated Inventory**: Keeps documentation current
- **Service Catalog**: Complete list of all services
- **Change Tracking**: Tracks device appearance/disappearance
- **Export Capabilities**: JSON, PNG, SVG export

---

## Quick Start

### 1. Start Services

```bash
# Start all services including Scanopy
docker compose up -d

# Or start just Scanopy services
docker compose up -d scanopy-server scanopy-daemon scanopy-postgres
```

### 2. Access Scanopy UI

```bash
# Open Scanopy web interface
open http://localhost:60072

# Create admin account when prompted
# Wait for initial network discovery (~5 minutes)
```

### 3. Test Integration

```bash
# Check Scanopy status from FortiGate Dashboard
curl http://localhost:8000/api/scanopy/status | jq

# Get discovered hosts
curl http://localhost:8000/api/scanopy/hosts | jq

# Get unified topology (FortiGate + Scanopy)
curl http://localhost:8000/api/unified/topology | jq
```

---

## Configuration

### Environment Variables

Add to `.env` file:

```bash
# Scanopy Integration
SCANOPY_URL=http://scanopy-server:60072
SCANOPY_API_TOKEN=  # Optional, for API authentication
SCANOPY_POSTGRES_PASSWORD=scanopy_password
SCANOPY_LOG_LEVEL=info
```

### Network Configuration

Scanopy daemon requires:
- `network_mode: host` - For network scanning
- `privileged: true` - For raw socket access
- Docker socket access - For container discovery

---

## Use Cases

### Use Case 1: Complete Network Inventory
**Goal**: Get complete inventory of all devices

```bash
curl http://localhost:8000/api/unified/topology | jq '.discovered_endpoints.count'
```

### Use Case 2: Service Discovery
**Goal**: Find all database services

```bash
curl http://localhost:8000/api/scanopy/services | jq '.services[] | select(.name | test("postgres|mysql|mongo"; "i"))'
```

### Use Case 3: Device Classification
**Goal**: Identify restaurant devices (POS, KDS, menu boards)

```bash
curl http://localhost:8000/api/scanopy/hosts | jq '.hosts[] | select(.services[].name | test("aloha|micros|par"; "i"))'
```

---

## Architecture

```
FortiGate Dashboard (FastAPI)
    ↓
Scanopy Service (API Client)
    ↓
Scanopy Server (Port 60072)
    ↓
Scanopy Daemon (Port 60073) → Network Scanner
    ↓
PostgreSQL Database
```

---

## Files Modified

1. **docker-compose.yml**
   - Added `scanopy-server` service
   - Added `scanopy-daemon` service
   - Added `scanopy-postgres` service
   - Added `scanopy_network` network
   - Added volumes for Scanopy data

2. **Documentation**
   - Created `docs/SCANOPY_INTEGRATION_ANALYSIS.md`
   - Created `docs/SCANOPY_INTEGRATION_SUMMARY.md`
   - Updated `SCANOPY_INTEGRATION.md`

---

## Next Steps

### Immediate
1. Start services: `docker compose up -d`
2. Access Scanopy UI: http://localhost:60072
3. Create admin account
4. Configure network discovery
5. Wait for initial scan (~5 minutes)

### Short-term
1. Test API endpoints
2. Verify topology integration
3. Check service detection accuracy
4. Configure scheduled scans

### Medium-term
1. Add service badges to topology UI
2. Create Scanopy status dashboard
3. Add scan trigger UI
4. Implement service change alerts

---

## Troubleshooting

### Issue: Scanopy services won't start

**Solutions**:
1. Check Docker logs: `docker logs scanopy-server`
2. Verify PostgreSQL is healthy: `docker logs scanopy-postgres`
3. Check network connectivity
4. Verify environment variables

### Issue: No hosts discovered

**Solutions**:
1. Wait for initial scan (5-10 minutes)
2. Trigger manual scan: `POST /api/scanopy/scan`
3. Check daemon logs: `docker logs scanopy-daemon`
4. Verify daemon has network access

### Issue: API returns unavailable

**Solutions**:
1. Check health: `curl http://localhost:60072/health`
2. Verify `SCANOPY_URL` environment variable
3. Check network connectivity from dashboard container
4. Review service logs

---

## Resources

- **Scanopy Documentation**: https://scanopy.net/docs
- **Scanopy UI**: http://localhost:60072
- **Service Definitions**: https://scanopy.net/services
- **Integration Analysis**: `docs/SCANOPY_INTEGRATION_ANALYSIS.md`

---

**Integration Status**: ✅ **Complete**  
**Services Added**: 3 (server, daemon, postgres)  
**API Endpoints**: 8  
**Ready for Testing**: Yes
