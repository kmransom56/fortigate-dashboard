# 🛡️ FortiGate Enterprise Dashboard

![Python](https://img.shields.io/badge/python-3.12-blue.svg)

## Features Overview

- Interactive network topology with real-time device discovery
- Glass-morphism UI with modern animations and gradients
- Live status widgets showing FortiGate status, switch count, and device count
- Mobile-responsive design with Bootstrap 5
- Self-contained assets for faster loading
- Enterprise-grade visual design

## Enhanced Network Automation

- Intelligent OUI lookup (50 requests/minute rate limiting)
- Persistent caching system
- Expanded manufacturer database (Microsoft, Dell, Apple, Samsung, etc.)
- Automatic device risk assessment
- Power Automate integration ready

## Real-Time Monitoring

- FortiGate interface monitoring
- FortiSwitch management
- Connected device enumeration
- WAN status alerts
- Comprehensive error handling

## Quick Start

### Prerequisites

- API token for FortiGate authentication
- Network connectivity to FortiGate management interface

### Clone & Setup

```bash
git clone https://github.com/kmransom56/fortigate-dashboard.git
cd fortigate-dashboard
```

### Configure Secrets

```bash
# Create secrets directory
mkdir -p secrets
# Add your FortiGate API token
echo "your-fortigate-api-token" > secrets/fortigate_api_token.txt
# Add FortiGate admin password
echo "your-admin-password" > secrets/fortigate_password.txt
# Add FortiSwitch password (if different)
echo "your-fortiswitch-password" > secrets/fortiswitch_password.txt
```

### Configure Environment

Update `compose.yml` with your FortiGate settings:

```yaml
environment:
  - FORTIGATE_HOST=https://192.168.0.254  # Your FortiGate IP
  - FORTIGATE_USERNAME=admin
  - FORTIGATE_VERIFY_SSL=false
  - LOG_LEVEL=DEBUG
  - FORTISWITCH_HOST=192.168.0.253       # Your FortiSwitch IP
  - FORTISWITCH_USERNAME=admin
```

### Deploy with Docker

```bash
# Build and start all services
docker compose up --build -d
# View logs
docker compose logs -f dashboard
```

### Access Dashboard

Open your browser to: [http://localhost:10000](http://localhost:10000)

## Dashboard Interfaces

### Home Dashboard

- Professional landing page with live status widgets
- Three main navigation options:
  - Manage FortiSwitches (port and device management)
  - Network Topology (Security Fabric visualization)
  - FortiGate Dashboard (interface and policy monitoring)

### Network Topology (`/topology`)

- Security Fabric visualization matching official FortiGate interface
- Interactive device icons with manufacturer identification
- Connection mapping between FortiGate → FortiSwitch → Endpoints
- Risk-based color coding:
  - Green: Fully identified devices (low risk)
  - Yellow: Known manufacturer, missing details (medium risk)
  - Red: Unknown devices or security threats (high risk)

### FortiSwitch Management (`/switches`)

- Switch overview with model, serial, and status information
- Port-level device visibility with manufacturer identification
- Device details including hostname, MAC, IP, and connection port
- Real-time device discovery with automatic manufacturer lookup
- Device enumeration across all connected switches
- Policy and security status overview
- Performance metrics and system health

## API Documentation

### Topology Data Endpoint

```http
GET /api/topology_data
```

**Response Example:**

```json
{
  "devices": [
    {
      "id": "fortigate_main",
      "type": "fortigate",
      "name": "FortiGate-Main",
      "ip": "192.168.0.254",
      "status": "Active"
    }
  ],
  "connections": [
    {
      "from": "fortigate_main",
      "to": "switch_0"
    }
  ]
}
```

### FortiSwitch Data Endpoint

```http
GET /fortigate/api/switches
```

### Interface Information Endpoint

```http
GET /fortigate/api/interfaces
```

## Enhanced OUI Lookup System

The dashboard includes an intelligent MAC address vendor lookup system:

```python
# Rate limiting: 50 requests/minute
# Persistent caching across container restarts
# Exponential backoff for API limits
```

- Fallback handling - Graceful degradation
- Extensive database - Pre-loaded common manufacturers

## Container Architecture

```text
┌─────────────────┐    ┌──────────────────┐
│   Dashboard     │    │   WAN Monitor    │
│   Port 10000    │    │   Background     │
│                 │    │   Service        │
├─────────────────┤    └──────────────────┘
│ FastAPI         │
│ Real-time APIs  │
└─────────────────┘
         │
         ▼
┌─────────────────┐    ┌──────────────────┐
│   FortiGate     │    │   FortiSwitch    │
│   192.168.0.254 │◄──►│   192.168.0.253  │
└─────────────────┘    └──────────────────┘
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FORTISWITCH_HOST` | FortiSwitch management IP | `192.168.0.253` |

## Volume Mounts

```yaml
volumes:
  - ./app/certs:/app/certs           # SSL certificates
  - ./app/data:/app/data             # Persistent cache data
```

## Power Automate Integration

### Automation Endpoints

Perfect for Microsoft Power Automate workflows:

```http
# Device discovery notifications
GET /api/topology_data

# Security risk alerts
GET /api/topology_data?filter=risk

# New device detection
GET /api/topology_data?changes=true
```

### Webhook Integration

```json
{
  "event": "device_discovered",
  "device": {
    "mac": "FC:8C:11:AA:BB:CC",
    "manufacturer": "Microsoft Corporation",
    "risk_level": "low",
    "switch": "S124EPTQ22000276",
    "port": "port15"
  },
  "timestamp": "2025-07-19T08:00:00Z"
}
```

### Process Automation Examples

1. New Device Alerts → Teams notification
2. Security Risk Detection → Email alert
3. Unauthorized Device → Network quarantine
4. Daily Inventory Report → SharePoint update

## Security Features

### Network Security

### Access Control


docker compose logs -f dashboard

## Performance Optimizations

### Caching Strategy

- Persistent OUI lookup cache (`app/data/oui_cache.json`)
- API response caching for frequently accessed data
- Rate limiting: 50 requests/minute for external APIs
- Connection pooling for database operations
- Lazy loading for large device inventories
- Compressed asset delivery for faster page loads

### Debug Mode

```bash
docker compose logs dashboard | grep "API"
# Clear browser cache
# Hard refresh: Ctrl+F5 (Windows) or Cmd+Shift+R (Mac)
docker compose logs -f dashboard
```

### Performance Monitoring

```bash
# Application metrics
curl http://localhost:10000/api/topology_data | jq '.devices | length'
```


pip install -r requirements.txt

## Development

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run development server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 10000
```

1. New API Endpoints: Add routes in `app/main.py`
2. UI Components: Create templates in `app/templates/`
3. Services: Add business logic in `app/services/`
4. Utilities: Helper functions in `app/utils/`

## Monitoring & Analytics

- Device discovery count and manufacturer distribution
- API response times and error rates
- Cache hit ratios
- Network topology changes over time
- Prometheus metrics endpoint (planned)
- Grafana dashboards
- ELK stack for logs
- Custom webhook notifications

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

- Additional device manufacturers
- UI/UX improvements
- New FortiGate API integrations
- Advanced analytics/reporting
- Enhanced security features

## Changelog

### v2.0.0 (Latest)

- Security Fabric topology visualization
- Professional UI redesign
- Enhanced OUI lookup
- Power Automate integration
- Real-time device discovery
- Advanced security risk assessment

### v1.0.0

- Basic FortiGate dashboard
- FortiSwitch management
- Interface monitoring
- Docker containerization

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- Documentation: This README and inline code comments
- Issues: Open a GitHub issue for bugs or feature requests
- Discussions: Use GitHub Discussions for questions and ideas

## Acknowledgments

- Fortinet for FortiGate API documentation and design inspiration
- FastAPI for the excellent web framework
- Bootstrap for UI components
- Docker for containerization

---

### Built with ❤️ for network automation and security professionals

*Transform your FortiGate management experience with enterprise-grade visualization and intelligent automation.*

## Network Topology 3D (`/topology-3d`)

- Three.js-based 3D force layout using 3d-force-graph via CDN
- Type-based colors and risk halos consistent with the 2D view
- Hover labels show device details; click to select
- Camera orbit, pan, and zoom supported
- Cross-links between 2D (`/topology`) and 3D (`/topology-3d`) views

### Eraser AI (Preview)

- This repository includes hooks for future Eraser AI integration.
- Set `ERASER_ENABLED=true` in the dashboard environment to enable the export endpoint.
- API: `POST /api/eraser/export` returns 501 unless `ERASER_ENABLED` is set to true.
- The 3D view contains a disabled “Export to Eraser” button that becomes enabled when the endpoint is active.
- Full Eraser AI integration will be added in a future update.

#### CDN with SRI and local fallback

- The 3D view uses pinned CDN URLs with Subresource Integrity (SRI) for Three.js and 3d-force-graph.
- If CDN loading fails (e.g., offline/air-gapped), the page attempts to load local copies from:
  - /static/vendor/three.min.js
  - /static/vendor/3d-force-graph.min.js
- To use local-only loading, block access to unpkg in your environment or remove the CDN script tags in app/templates/topology_3d.html. The runtime will detect missing globals and load local vendor files.
