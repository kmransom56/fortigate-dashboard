# 🛡️ FortiGate Enterprise Dashboard

![License](https://img.shields.io/badge/license-MIT-green.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)
![Python](https://img.shields.io/badge/python-3.12-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-modern-green.svg)

> **Professional Security Fabric management dashboard with enterprise-grade network topology visualization, intelligent device automation, and real-time monitoring capabilities.**

A comprehensive FortiGate management platform that provides **Fortinet-authentic Security Fabric topology visualization**, automated device discovery with intelligent manufacturer identification, and professional network monitoring capabilities.

## ✨ Features Overview

### 🌐 Security Fabric Topology Visualization
- **Fortinet-authentic interface** - Mirrors official FortiGate GUI design
- **Interactive network topology** with real-time device discovery
- **Color-coded risk assessment** (green/yellow/red) for security monitoring
- **Professional filtering options**: Device Traffic, Device Count, Device Type, Risk Level
- **Hover tooltips** with detailed device information and manufacturer data
- **Auto-refresh** every 30 seconds for live network monitoring

### 🎨 Professional Dashboard Design
- **Glass-morphism UI** with modern animations and gradients
- **Live status widgets** showing FortiGate status, switch count, and device count
- **Mobile-responsive design** with Bootstrap 5
- **Self-contained assets** - no external dependencies for faster loading
- **Enterprise-grade visual design** with professional color schemes

### 🔧 Enhanced Network Automation
- **Intelligent OUI lookup** with 50 requests/minute rate limiting
- **Persistent caching system** that survives container restarts
- **Expanded manufacturer database** (Microsoft, Dell, Apple, Samsung, etc.)
- **Automatic device risk assessment** based on manufacturer identification
- **Power Automate integration ready** with comprehensive API endpoints

### 📊 Real-Time Monitoring
- **FortiGate interface monitoring** with status, IP addresses, and link speeds
- **FortiSwitch management** with port-level device visibility
- **Connected device enumeration** with manufacturer identification
- **WAN status alerts** and traffic statistics
- **Comprehensive error handling** and fallback mechanisms

## 🚀 Quick Start

### Prerequisites

- **Docker & Docker Compose** installed
- **FortiGate device** with API access configured
- **API token** for FortiGate authentication
- **Network connectivity** to FortiGate management interface

### 1. Clone & Setup

```bash
git clone https://github.com/kmransom56/fortigate-dashboard.git
cd fortigate-dashboard
```

### 2. Configure Secrets

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

### 3. Configure Environment

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

### 4. Deploy with Docker

```bash
# Build and start all services
docker compose up --build -d

# View logs
docker compose logs -f dashboard
```

### 5. Access Dashboard

Open your browser to: **http://localhost:10000**

## 📱 Dashboard Interfaces

### 🏠 Home Dashboard
- **Professional landing page** with live status widgets
- **Three main navigation options**:
  - 🔧 **Manage FortiSwitches** - Port and device management
  - 🌐 **Network Topology** - Security Fabric visualization
  - 📊 **FortiGate Dashboard** - Interface and policy monitoring

### 🌐 Network Topology (`/topology`)
- **Security Fabric visualization** matching official FortiGate interface
- **Interactive device icons** with manufacturer identification
- **Connection mapping** between FortiGate → FortiSwitch → Endpoints
- **Risk-based color coding**:
  - 🟢 **Green**: Fully identified devices (low risk)
  - 🟡 **Yellow**: Known manufacturer, missing details (medium risk)
  - 🔴 **Red**: Unknown devices or security threats (high risk)

### 🔧 FortiSwitch Management (`/switches`)
- **Switch overview** with model, serial, and status information
- **Port-level device visibility** with manufacturer identification
- **Device details** including hostname, MAC, IP, and connection port
- **Real-time device discovery** with automatic manufacturer lookup

### 📊 FortiGate Dashboard (`/dashboard`)
- **Interface monitoring** with status and traffic statistics
- **Device enumeration** across all connected switches
- **Policy and security status** overview
- **Performance metrics** and system health

## 🔌 API Documentation

### Core Endpoints

#### Topology Data
```http
GET /api/topology_data
```
Returns complete network topology with device relationships, manufacturer information, and risk assessments.

**Response Example:**
```json
{
  "devices": [
    {
      "id": "fortigate_main",
      "type": "fortigate",
      "name": "FortiGate-Main",
      "ip": "192.168.0.254",
      "status": "online",
      "risk": "low",
      "position": {"x": 400, "y": 100},
      "details": {
        "model": "FortiGate",
        "interfaces": 8,
        "status": "Active"
      }
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

#### System Status
```http
GET /api/cloud_status
```
Returns FortiGate connection and system status.

#### FortiSwitch Data
```http
GET /fortigate/api/switches
```
Returns comprehensive FortiSwitch information including connected devices.

#### Interface Information
```http
GET /fortigate/api/interfaces
```
Returns FortiGate interface details and statistics.

## 🔧 Advanced Configuration

### Enhanced OUI Lookup System

The dashboard includes an intelligent MAC address vendor lookup system:

```python
# Automatic manufacturer identification
# Built-in database for common vendors
# Rate limiting: 50 requests/minute
# Persistent caching across container restarts
# Exponential backoff for API limits
```

**Features:**
- ✅ **Intelligent caching** - Stores lookups to disk
- ✅ **Rate limiting** - Prevents API overload
- ✅ **Fallback handling** - Graceful degradation
- ✅ **Extensive database** - Pre-loaded common manufacturers

### Container Architecture

```
┌─────────────────┐    ┌──────────────────┐
│   Dashboard     │    │   WAN Monitor    │
│   Port 10000    │    │   Background     │
│                 │    │   Service        │
├─────────────────┤    └──────────────────┘
│ FastAPI         │
│ Jinja2 Templates│
│ Bootstrap 5 UI  │
│ Real-time APIs  │
└─────────────────┘
         │
         ▼
┌─────────────────┐    ┌──────────────────┐
│   FortiGate     │    │   FortiSwitch    │
│   192.168.0.254 │◄──►│   192.168.0.253  │
└─────────────────┘    └──────────────────┘
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FORTIGATE_HOST` | FortiGate management IP | `https://192.168.0.254` |
| `FORTIGATE_USERNAME` | Admin username | `admin` |
| `FORTIGATE_VERIFY_SSL` | SSL certificate verification | `false` |
| `LOG_LEVEL` | Application logging level | `DEBUG` |
| `FORTISWITCH_HOST` | FortiSwitch management IP | `192.168.0.253` |

### Volume Mounts

```yaml
volumes:
  - ./app/certs:/app/certs           # SSL certificates
  - ./app/data:/app/data             # Persistent cache data
```

## 🔄 Power Automate Integration

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

```python
# Example webhook payload for new device detection
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

1. **New Device Alerts** → Teams notification
2. **Security Risk Detection** → Email alert
3. **Unauthorized Device** → Network quarantine
4. **Daily Inventory Report** → SharePoint update

## 🛡️ Security Features

### Network Security
- **Device risk assessment** based on manufacturer identification
- **Unknown device detection** with high-risk flagging
- **Real-time threat monitoring** integration
- **Secure API token management** with Docker secrets

### Access Control
- **Docker network isolation** with custom bridge networks
- **Environment-based configuration** for different deployments
- **SSL certificate support** for production environments
- **API rate limiting** to prevent abuse

## 📊 Performance Optimizations

### Caching Strategy
- **Persistent OUI lookup cache** (`app/data/oui_cache.json`)
- **API response caching** for frequently accessed data
- **Intelligent refresh intervals** based on data volatility
- **Exponential backoff** for failed requests

### Resource Management
- **Rate limiting**: 50 requests/minute for external APIs
- **Connection pooling** for database operations
- **Lazy loading** for large device inventories
- **Compressed asset delivery** for faster page loads

## 🚨 Troubleshooting

### Common Issues

#### 1. API Connection Failed
```bash
# Check FortiGate connectivity
docker compose exec dashboard curl -k https://192.168.0.254

# Verify API token
docker compose logs dashboard | grep "API"

# Check network connectivity
docker compose exec dashboard ping 192.168.0.254
```

#### 2. No Devices Showing
```bash
# Check FortiSwitch connection
docker compose logs dashboard | grep "fortiswitch"

# Verify device discovery
docker compose exec dashboard curl http://localhost:10000/api/topology_data
```

#### 3. Topology Not Loading
```bash
# Clear browser cache
# Hard refresh: Ctrl+F5 (Windows) or Cmd+Shift+R (Mac)

# Check API response
curl http://localhost:10000/api/topology_data
```

### Debug Mode

Enable detailed logging:

```yaml
environment:
  - LOG_LEVEL=DEBUG
```

```bash
# View detailed logs
docker compose logs -f dashboard

# Check specific service logs  
docker compose logs dashboard | grep "ERROR"
```

### Performance Monitoring

```bash
# Container resource usage
docker stats fortigate-dashboard-dashboard-1

# Application metrics
curl http://localhost:10000/api/topology_data | jq '.devices | length'
```

## 🧪 Development

### Local Development Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export FORTIGATE_HOST=https://192.168.0.254
export FORTIGATE_API_TOKEN=your-token

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 10000
```

### Adding New Features

1. **New API Endpoints**: Add routes in `app/main.py`
2. **UI Components**: Create templates in `app/templates/`
3. **Services**: Add business logic in `app/services/`
4. **Utilities**: Helper functions in `app/utils/`

### Testing

```bash
# API testing
curl -X GET http://localhost:10000/api/topology_data

# Container testing
docker compose up --build

# Health check
curl http://localhost:10000/
```

## 📈 Monitoring & Analytics

### Built-in Metrics
- **Device discovery count** and manufacturer distribution
- **API response times** and error rates  
- **Cache hit ratios** for performance optimization
- **Network topology changes** over time

### Integration Options
- **Prometheus metrics** endpoint (planned)
- **Grafana dashboards** for visualization
- **ELK stack** for log analysis
- **Custom webhook** notifications

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Areas for Contribution
- 🌐 **Additional device manufacturers** in OUI database
- 🎨 **UI/UX improvements** and themes
- 🔧 **New FortiGate API integrations**
- 📊 **Advanced analytics and reporting**
- 🔒 **Enhanced security features**

## 📝 Changelog

### v2.0.0 (Latest)
- ✨ **Added Security Fabric topology visualization**
- 🎨 **Professional UI redesign** with glass-morphism
- 🔧 **Enhanced OUI lookup** with intelligent caching
- 🚀 **Power Automate integration** endpoints
- 📊 **Real-time device discovery** improvements
- 🛡️ **Advanced security risk assessment**

### v1.0.0
- 🏠 **Basic FortiGate dashboard**
- 🔧 **FortiSwitch management**
- 📊 **Interface monitoring**
- 🐳 **Docker containerization**

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋‍♂️ Support

- **Documentation**: Check this README and inline code comments
- **Issues**: Open a GitHub issue for bugs or feature requests  
- **Discussions**: Use GitHub Discussions for questions and ideas

## 🌟 Acknowledgments

- **Fortinet** for FortiGate API documentation and design inspiration
- **FastAPI** for the excellent web framework
- **Bootstrap** for responsive UI components
- **Docker** for containerization platform

---

**Built with ❤️ for network automation and security professionals**

*Transform your FortiGate management experience with enterprise-grade visualization and intelligent automation.*
## 🌐 Network Topology 3D (`/topology-3d`)
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
#### Eraser AI status endpoint
- Capability check: `GET /api/eraser/status` returns `{ "enabled": true|false }`.
- Export: `POST /api/eraser/export` returns 501 unless enabled.

#### CDN usage and offline deployments
- The 3D view loads Three.js and 3d-force-graph from CDN with runtime error handling.
- For air-gapped/offline environments, vendor these assets and update the script URLs accordingly.

- Full Eraser AI integration will be added in a future update.
