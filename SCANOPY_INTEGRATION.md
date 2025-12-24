# Scanopy Integration Guide

## Overview

Scanopy network discovery and mapping has been integrated into the FortiGate Dashboard application, providing comprehensive network topology visualization with automatic service detection.

## What Scanopy Provides

- **Automatic Host Discovery**: Finds all devices on network segments
- **Service Detection**: Identifies 200+ services (databases, web servers, containers)
- **Docker Integration**: Discovers containerized services via Docker socket
- **MAC Vendor Lookup**: Identifies device manufacturers
- **Port Scanning**: Maps open ports on discovered hosts
- **Interactive Topology**: Visual network topology with service relationships

## Integration Points

### 1. Scanopy Service (`app/services/scanopy_service.py`)

Async API client for Scanopy server with:
- Health check
- Host discovery
- Service detection
- Topology retrieval
- Network scanning trigger

### 2. API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/scanopy/status` | GET | Check Scanopy server health |
| `/api/scanopy/hosts` | GET | Get all discovered hosts |
| `/api/scanopy/host/{ip}` | GET | Get specific host details |
| `/api/scanopy/services` | GET | Get all detected services |
| `/api/scanopy/topology` | GET | Get network topology |
| `/api/scanopy/scan` | POST | Trigger network scan |
| `/api/scanopy/networks` | GET | Get all networks |
| `/api/unified/topology` | GET | Combined FortiGate + Meraki + Scanopy |

### 3. Hybrid Topology Integration

Scanopy data is automatically integrated into the hybrid topology service:
- Enhances existing devices with Scanopy service information
- Adds standalone discovered hosts
- Provides service detection for all endpoints

## Configuration

### Environment Variables

Add to `.env` file or `docker-compose.yml`:

```bash
# Scanopy Integration
SCANOPY_URL=http://scanopy-server:60072
SCANOPY_API_TOKEN=your_token_here  # Optional
```

### Docker Compose

Scanopy configuration is already added to `docker-compose.yml`:

```yaml
environment:
  - SCANOPY_URL=${SCANOPY_URL:-http://scanopy-server:60072}
  - SCANOPY_API_TOKEN=${SCANOPY_API_TOKEN:-}
```

## Usage Examples

### Check Scanopy Status

```bash
curl http://localhost:8001/api/scanopy/status | jq
```

Response:
```json
{
  "status": "healthy",
  "url": "http://scanopy-server:60072",
  "available": true,
  "status_code": 200
}
```

### Get Discovered Hosts

```bash
curl http://localhost:8001/api/scanopy/hosts | jq
```

### Get Unified Topology

```bash
curl http://localhost:8001/api/unified/topology | jq
```

This combines:
- FortiGate/FortiSwitch infrastructure
- Meraki switches (if configured)
- Scanopy discovered hosts and services

### Trigger Network Scan

```bash
curl -X POST http://localhost:8001/api/scanopy/scan \
  -H "Content-Type: application/json" \
  -d '{"subnet": "192.168.1.0/24", "scan_type": "full"}' | jq
```

## Integration with Topology Visualization

Scanopy data is automatically included in:
- `/api/topology_data` - Main topology endpoint
- `/api/topology_3d_data` - 3D topology visualization
- `/api/unified/topology` - Unified multi-source topology

### Data Enhancement

When Scanopy data is available:
1. Existing devices are enhanced with service information
2. Standalone discovered hosts are added as separate devices
3. Service detection provides detailed port and protocol information

## Deployment

### Option 1: External Scanopy Server

If Scanopy is running separately:

```bash
# Set environment variable
export SCANOPY_URL=http://your-scanopy-server:60072

# Or in docker-compose.yml
environment:
  - SCANOPY_URL=http://your-scanopy-server:60072
```

### Option 2: Docker Compose Integration

Add Scanopy services to `docker-compose.yml`:

```yaml
services:
  scanopy-server:
    image: ghcr.io/scanopy/scanopy/server:latest
    ports:
      - "60072:60072"
    environment:
      - SCANOPY_DATABASE_URL=postgresql://postgres:password@postgres:5432/scanopy
    networks:
      - fortigate_network

  scanopy-daemon:
    image: ghcr.io/scanopy/scanopy/daemon:latest
    ports:
      - "60073:60073"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    networks:
      - fortigate_network
```

## Testing

### 1. Verify Scanopy Connection

```bash
curl http://localhost:8001/api/scanopy/status
```

### 2. Check Discovered Hosts

```bash
curl http://localhost:8001/api/scanopy/hosts | jq '.count'
```

### 3. View Unified Topology

```bash
curl http://localhost:8001/api/unified/topology | jq '.discovered_endpoints.count'
```

## Troubleshooting

### Issue: Scanopy status returns unavailable

**Solutions:**
1. Verify Scanopy is running: `docker ps | grep scanopy`
2. Check Scanopy health: `curl http://localhost:60072/health`
3. Verify `SCANOPY_URL` environment variable
4. Check network connectivity from FortiGate dashboard container

### Issue: No hosts discovered

**Solutions:**
1. Trigger manual scan: `POST /api/scanopy/scan`
2. Check Scanopy daemon logs: `docker logs scanopy-daemon`
3. Wait for initial discovery (5-10 minutes)
4. Verify daemon has network access

### Issue: Services not detected

**Solutions:**
1. Ensure port scanning is enabled in Scanopy configuration
2. Check service detection is enabled
3. Verify Docker socket access (for container discovery)

## Performance Considerations

- **Caching**: Scanopy data is cached via response cache service (60s TTL)
- **Async Operations**: All API calls are non-blocking
- **Connection Pooling**: aiohttp session reuse for efficiency
- **Parallel Execution**: Scanopy data retrieval runs in parallel with other sources

## Next Steps

1. **Start Scanopy Server**: Deploy Scanopy server and daemon
2. **Configure Networks**: Set up network discovery in Scanopy UI
3. **Wait for Discovery**: Allow 5-10 minutes for initial scan
4. **View Results**: Access `/api/unified/topology` to see combined data

## Resources

- **Scanopy Documentation**: https://scanopy.net/docs
- **Scanopy UI**: http://localhost:60072 (if running locally)
- **Service Definitions**: https://scanopy.net/services
- **Integration Guide**: This document

---

**Integration Status**: ✅ Complete
**Date**: 2025-12-24
