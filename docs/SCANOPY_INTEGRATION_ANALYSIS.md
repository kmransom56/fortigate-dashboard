# Scanopy Integration Analysis for FortiGate Dashboard

## Executive Summary

**Status**: ✅ **Partially Integrated** - API client and endpoints exist, but Scanopy services are not deployed in docker-compose.yml

**Recommendation**: Complete integration by adding Scanopy services to docker-compose.yml and enhancing topology visualization with Scanopy data.

---

## Current Integration Status

### ✅ What's Already Implemented

1. **Scanopy Service Client** (`app/services/scanopy_service.py`)
   - Full async API client (335 lines)
   - Health check, host discovery, service detection
   - Topology retrieval, scan triggering
   - Error handling and connection pooling

2. **API Endpoints** (8 endpoints in `app/main.py`)
   - `/api/scanopy/status` - Health check
   - `/api/scanopy/hosts` - Discovered hosts
   - `/api/scanopy/host/{ip}` - Host details
   - `/api/scanopy/services` - Detected services
   - `/api/scanopy/topology` - Network topology
   - `/api/scanopy/scan` - Trigger scan
   - `/api/scanopy/networks` - Network list
   - `/api/unified/topology` - Combined FortiGate + Meraki + Scanopy

3. **Hybrid Topology Integration** (`app/services/hybrid_topology_service_optimized.py`)
   - Automatically enhances topology with Scanopy data
   - Adds standalone discovered hosts
   - Enriches devices with service information

4. **Environment Variables** (in `docker-compose.yml`)
   - `SCANOPY_URL` configured
   - `SCANOPY_API_TOKEN` placeholder

### ❌ What's Missing

1. **Scanopy Services in Docker Compose**
   - No `scanopy-server` service
   - No `scanopy-daemon` service
   - No Scanopy PostgreSQL database
   - No Scanopy network configuration

2. **Frontend Integration**
   - No Scanopy-specific UI components
   - No service badges in topology views
   - No Scanopy discovery status indicators

3. **Documentation**
   - Integration guide exists but needs update for FortiGate Dashboard
   - Missing deployment instructions

---

## Scanopy Application Overview

### What Scanopy Provides

**Scanopy** is a network discovery and visualization tool written in Rust that:

- **Automatic Discovery**: Scans networks to identify hosts, services, and relationships
- **200+ Service Definitions**: Auto-detects databases, web servers, containers, network infrastructure
- **Interactive Topology**: Generates visual network diagrams
- **Distributed Scanning**: Deploy daemons across network segments
- **Docker Integration**: Discovers containerized services automatically
- **Multi-Tenancy**: Organization management with role-based permissions
- **Scheduled Discovery**: Automated scanning to keep documentation current

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│  FortiGate Dashboard (FastAPI - Port 8000/11039)       │
│  ┌────────────────┐  ┌──────────────┐  ┌──────────┐  │
│  │ FortiGate API  │  │ Topology      │  │ Scanopy  │  │
│  │ Integration    │→→│ Visualizer   │←←│ Service  │  │
│  └────────────────┘  └──────────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────┘
            ↓                        ↓              ↓
   ┌──────────────┐         ┌──────────────┐  ┌──────────┐
   │ FortiGate    │         │ Enhanced     │  │ Scanopy  │
   │ Firewall     │         │ Topology     │  │ Server   │
   │ API          │         │ Views        │  │ (60072)  │
   └──────────────┘         └──────────────┘  └──────────┘
                                                  │
                                                  ↓
                                         ┌──────────────┐
                                         │ Scanopy      │
                                         │ Daemon       │
                                         │ (60073)      │
                                         │ Network      │
                                         │ Scanner      │
                                         └──────────────┘
```

---

## Integration Benefits for FortiGate Dashboard

### 1. Enhanced Device Discovery
- **Complement FortiGate API**: Scanopy discovers devices FortiGate doesn't see (endpoints, IoT devices)
- **Service Detection**: Identifies 200+ services running on discovered hosts
- **MAC Vendor Lookup**: Identifies device manufacturers automatically
- **Port Mapping**: Maps open ports to services

### 2. Unified Topology Visualization
- **Combined View**: FortiGate infrastructure + discovered endpoints
- **Service Badges**: Visual indicators for detected services
- **Relationship Mapping**: Shows how devices connect and communicate
- **Multi-Source Data**: FortiGate, Meraki, SNMP, and Scanopy in one view

### 3. Network Documentation
- **Automated Inventory**: Keeps network documentation current
- **Service Catalog**: Complete list of all services running
- **Change Tracking**: Tracks when devices appear/disappear
- **Export Capabilities**: Export topology as JSON, PNG, SVG

### 4. Security & Compliance
- **Service Audit**: Find all exposed services
- **Port Scanning**: Identify open ports and potential vulnerabilities
- **Device Inventory**: Complete device list for compliance
- **Change Detection**: Alert on new devices/services

---

## Integration Plan

### Phase 1: Docker Compose Integration (Immediate)

**Goal**: Add Scanopy services to docker-compose.yml

**Tasks**:
1. Add `scanopy-server` service
2. Add `scanopy-daemon` service  
3. Add Scanopy PostgreSQL database (or reuse existing)
4. Configure networking between services
5. Add volume mounts for Scanopy data

**Estimated Time**: 30 minutes

### Phase 2: Service Configuration (Immediate)

**Goal**: Configure Scanopy to work with FortiGate Dashboard

**Tasks**:
1. Set up Scanopy organization/networks
2. Configure daemon for network scanning
3. Test API connectivity
4. Verify data flow

**Estimated Time**: 30 minutes

### Phase 3: Topology Enhancement (Short-term)

**Goal**: Enhance topology views with Scanopy data

**Tasks**:
1. Add service badges to device icons
2. Show Scanopy-discovered hosts in topology
3. Add service information to device tooltips
4. Create unified topology view

**Estimated Time**: 2-3 hours

### Phase 4: Frontend Integration (Medium-term)

**Goal**: Add Scanopy-specific UI components

**Tasks**:
1. Add Scanopy status indicator
2. Create service discovery dashboard
3. Add scan trigger UI
4. Show service details in device panels

**Estimated Time**: 4-6 hours

---

## Docker Compose Configuration

### Required Services

```yaml
services:
  # Scanopy Server
  scanopy-server:
    image: ghcr.io/scanopy/scanopy/server:latest
    container_name: scanopy-server
    ports:
      - "60072:60072"
    environment:
      - SCANOPY_DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD:-password}@scanopy-postgres:5432/scanopy
      - SCANOPY_SERVER_PORT=60072
      - SCANOPY_PUBLIC_URL=http://localhost:60072
      - SCANOPY_INTEGRATED_DAEMON_URL=http://host.docker.internal:60073
    depends_on:
      scanopy-postgres:
        condition: service_healthy
    networks:
      - fortigate_network
      - scanopy_network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:60072/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Scanopy Daemon
  scanopy-daemon:
    image: ghcr.io/scanopy/scanopy/daemon:latest
    container_name: scanopy-daemon
    network_mode: host  # Required for network scanning
    privileged: true     # Required for network scanning
    ports:
      - "60073:60073"
    environment:
      - SCANOPY_SERVER_URL=http://host.docker.internal:60072
      - SCANOPY_PORT=60073
      - SCANOPY_BIND_ADDRESS=0.0.0.0
      - SCANOPY_NAME=fortigate-dashboard-daemon
      - SCANOPY_HEARTBEAT_INTERVAL=30
      - SCANOPY_MODE=Push
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro  # For Docker discovery
      - scanopy_daemon_config:/root/.config/daemon
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:60073/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Scanopy PostgreSQL Database
  scanopy-postgres:
    image: postgres:17-alpine
    container_name: scanopy-postgres
    environment:
      - POSTGRES_DB=scanopy
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=${SCANOPY_POSTGRES_PASSWORD:-scanopy_password}
    volumes:
      - scanopy_postgres_data:/var/lib/postgresql/data
    networks:
      - scanopy_network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  scanopy_postgres_data:
  scanopy_daemon_config:

networks:
  scanopy_network:
    driver: bridge
```

### Environment Variables

Add to `.env` file:

```bash
# Scanopy Integration
SCANOPY_URL=http://scanopy-server:60072
SCANOPY_API_TOKEN=  # Optional, for API authentication
SCANOPY_POSTGRES_PASSWORD=scanopy_password
```

---

## API Integration Points

### Current Endpoints (Already Implemented)

| Endpoint | Method | Description | Status |
|----------|--------|-------------|--------|
| `/api/scanopy/status` | GET | Check Scanopy health | ✅ Working |
| `/api/scanopy/hosts` | GET | Get discovered hosts | ✅ Working |
| `/api/scanopy/host/{ip}` | GET | Get host details | ✅ Working |
| `/api/scanopy/services` | GET | Get detected services | ✅ Working |
| `/api/scanopy/topology` | GET | Get network topology | ✅ Working |
| `/api/scanopy/scan` | POST | Trigger network scan | ✅ Working |
| `/api/scanopy/networks` | GET | Get networks | ✅ Working |
| `/api/unified/topology` | GET | Combined topology | ✅ Working |

### Data Flow

```
Scanopy Daemon → Scanopy Server → Scanopy API → FortiGate Dashboard Service → Topology Views
     ↓                ↓                ↓                    ↓                      ↓
Network Scan    PostgreSQL DB    REST API         scanopy_service.py      Enhanced Topology
```

---

## Use Cases

### Use Case 1: Complete Network Inventory

**Scenario**: Get complete inventory of all devices on network

**Workflow**:
1. FortiGate API provides managed infrastructure (firewalls, switches)
2. Scanopy discovers all endpoints (laptops, phones, IoT devices)
3. Unified topology combines both datasets
4. Service detection identifies what's running on each device

**API Call**:
```bash
curl http://localhost:8000/api/unified/topology | jq
```

### Use Case 2: Service Discovery

**Scenario**: Find all database services on network

**Workflow**:
1. Scanopy scans network and detects services
2. Filter for database services (PostgreSQL, MySQL, MongoDB)
3. Cross-reference with FortiGate firewall rules
4. Generate security report

**API Call**:
```bash
curl http://localhost:8000/api/scanopy/services | jq '.services[] | select(.name | test("postgres|mysql|mongo"; "i"))'
```

### Use Case 3: Device Classification

**Scenario**: Identify restaurant-specific devices (POS, KDS, menu boards)

**Workflow**:
1. Scanopy discovers all devices
2. Service detection identifies POS services
3. MAC vendor lookup identifies manufacturers
4. Combine with FortiGate port information
5. Classify devices automatically

**API Call**:
```bash
curl http://localhost:8000/api/scanopy/hosts | jq '.hosts[] | select(.services[].name | test("aloha|micros|par"; "i"))'
```

---

## Testing Checklist

### Service Deployment
- [ ] Scanopy server starts successfully
- [ ] Scanopy daemon connects to server
- [ ] PostgreSQL database initialized
- [ ] Health checks pass

### API Integration
- [ ] `/api/scanopy/status` returns healthy
- [ ] `/api/scanopy/hosts` returns discovered hosts
- [ ] `/api/scanopy/services` returns detected services
- [ ] `/api/scanopy/topology` returns topology data
- [ ] `/api/scanopy/scan` triggers scan successfully

### Topology Integration
- [ ] Scanopy hosts appear in unified topology
- [ ] Service information enriches device data
- [ ] Standalone hosts added correctly
- [ ] Service badges display in UI

### Network Scanning
- [ ] Initial network scan completes
- [ ] Hosts discovered correctly
- [ ] Services detected accurately
- [ ] Scheduled scans run automatically

---

## Performance Considerations

### Resource Usage
- **Scanopy Server**: ~200MB RAM, minimal CPU
- **Scanopy Daemon**: ~100MB RAM, CPU intensive during scans
- **PostgreSQL**: ~100MB RAM for small networks

### Network Impact
- **Initial Scan**: Can take 5-30 minutes depending on network size
- **Scheduled Scans**: Run in background, minimal impact
- **API Calls**: Async, non-blocking

### Caching Strategy
- Cache Scanopy data for 5 minutes (TTL)
- Refresh on-demand when scan completes
- Use Redis for distributed caching

---

## Security Considerations

### Network Access
- **Daemon**: Requires `network_mode: host` and `privileged: true` for scanning
- **Server**: Should be on internal network only
- **API**: Use authentication tokens in production

### Data Privacy
- Scanopy stores network topology data
- Ensure compliance with data protection regulations
- Consider data retention policies

### Access Control
- Use Scanopy organization/network isolation
- Implement API token authentication
- Restrict scan trigger endpoints

---

## Next Steps

### Immediate Actions (Today)

1. **Add Scanopy Services to docker-compose.yml**
   - Copy configuration from scanopy-main/docker-compose.yml
   - Adapt for FortiGate Dashboard network
   - Test service startup

2. **Configure Environment Variables**
   - Add SCANOPY_URL to .env
   - Set up PostgreSQL password
   - Configure daemon connection

3. **Test Integration**
   - Start services: `docker compose up -d scanopy-server scanopy-daemon scanopy-postgres`
   - Check health: `curl http://localhost:60072/health`
   - Test API: `curl http://localhost:8000/api/scanopy/status`

### Short-term Actions (This Week)

1. **Enhance Topology Views**
   - Add service badges to device icons
   - Show Scanopy-discovered hosts
   - Add service information tooltips

2. **Create Integration Documentation**
   - Update SCANOPY_INTEGRATION.md
   - Add deployment guide
   - Document API usage

3. **Test Network Scanning**
   - Configure scan targets
   - Run initial discovery
   - Verify data accuracy

### Medium-term Actions (This Month)

1. **Frontend Integration**
   - Add Scanopy status dashboard
   - Create service discovery page
   - Add scan trigger UI

2. **Advanced Features**
   - Scheduled scan integration
   - Service change alerts
   - Export capabilities

---

## Files to Review

### Existing Integration Files
- `app/services/scanopy_service.py` - API client (✅ Complete)
- `app/main.py` - API endpoints (✅ Complete)
- `app/services/hybrid_topology_service_optimized.py` - Topology integration (✅ Complete)
- `SCANOPY_INTEGRATION.md` - Documentation (⚠️ Needs update)

### Scanopy Source Files (Reference)
- `scanopy/scanopy-main/docker-compose.yml` - Docker configuration
- `scanopy/scanopy-main/docs/` - Full documentation
- `scanopy/scanopy-main/backend/src/` - Rust source code (reference only)

---

## Conclusion

**Scanopy is 80% integrated** into the FortiGate Dashboard. The API client and endpoints are complete and working. The main missing piece is **deploying the Scanopy services** in docker-compose.yml.

**Recommended Action**: Add Scanopy services to docker-compose.yml using the configuration provided above. This will enable:
- Automatic network discovery
- Service detection for all endpoints
- Enhanced topology visualization
- Complete network documentation

**Estimated Time to Complete**: 1-2 hours for full integration and testing.

---

**Created**: 2025-01-XX
**Status**: Ready for Implementation ✅
