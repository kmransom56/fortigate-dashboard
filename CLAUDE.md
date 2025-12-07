# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**FortiGate Enterprise Dashboard** - A FastAPI-based web application for real-time network topology visualization and management of Fortinet infrastructure (FortiGate firewalls and FortiSwitch devices), with multi-vendor support for Cisco Meraki.

Key capabilities:
- Interactive 2D/3D Security Fabric topology visualization (Three.js force graphs)
- Real-time device discovery with OUI manufacturer identification
- Redis-based session management and caching
- PostgreSQL for enterprise data, Neo4j for topology relationships
- Prometheus/Grafana monitoring stack
- Glass-morphism UI with enterprise-grade design

## Development Commands

### Python Environment (use `uv` on Linux)

```bash
# Setup virtual environment
uv venv
source .venv/bin/activate  # Linux
uv pip install -r requirements.txt

# Development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Alternative: direct Python execution
python -m uvicorn app.main:app --reload
```

### Docker Development

```bash
# Standard development workflow
docker compose up --build -d        # Build and start all services
docker compose logs -f fortigate-dashboard  # Follow dashboard logs
docker compose down                 # Stop all services

# Environment-specific deployments
docker compose -f docker-compose.dev.yml up -d          # Development
docker compose -f docker-compose.prod.yml up -d         # Production
docker compose -f docker-compose.enterprise.yml up -d   # Enterprise (full stack)

# Service-specific operations
docker compose restart fortigate-dashboard
docker compose exec fortigate-dashboard /bin/sh
docker compose logs redis --tail 100
```

### Testing (when tests are added)

```bash
# Run tests with pytest
pytest                          # Run all tests
pytest -v                       # Verbose output
pytest --cov                    # With coverage
pytest tests/services/          # Specific directory

# Watch mode during development
pytest-watch
```

## Architecture

### Service Layer Structure

The codebase uses a **service-oriented architecture** with clear separation:

**Core Services** (`app/services/`):
- `hybrid_topology_service.py` - Combines SNMP, FortiGate Monitor API, and FortiSwitch API data
- `fortigate_service.py` - FortiGate firewall API interactions
- `fortiswitch_api_service.py` - FortiSwitch management via FortiGate controller
- `fortigate_monitor_service.py` - Real-time device monitoring via FortiGate Monitor API
- `snmp_service.py` - SNMP-based device discovery
- `meraki_service.py` - Cisco Meraki integration
- `redis_session_manager.py` - Redis-based session pooling and caching
- `fortigate_redis_session.py` - FortiGate-specific session management
- `organization_service.py` - Multi-organization device management
- `brand_detection_service.py` - AI-powered device brand/model detection
- `scraped_topology_service.py` - FortiGate web UI scraping for topology extraction
- `eraser_service.py` - Eraser.io diagram export integration
- `icon_3d_service.py` - 3D device icon management
- `3d_asset_service.py` - 3D asset library service

**API Layer** (`app/api/`):
- `fortigate.py` - REST API endpoints for FortiGate operations

**Utilities** (`app/utils/`):
- `oui_lookup.py` - MAC address vendor identification with rate limiting (50 req/min)
- `icon_db.py` - Device icon database seeding and lookup

### Database Architecture (Polyglot Persistence)

- **Redis** (port 6379) - Session management, caching, rate limiting
- **PostgreSQL** (port 5432) - Enterprise data storage, audit logs
- **Neo4j** (ports 7474/7687) - Network topology graph relationships
- **Prometheus** (port 9090) - Metrics collection and time-series data
- **Grafana** (port 3000) - Monitoring dashboards

### Session Management Pattern

The codebase uses **Redis-pooled session management** for Fortinet API calls:

```python
# Pattern used throughout services
from app.services.redis_session_manager import get_redis_session_manager

session_mgr = get_redis_session_manager()
session = session_mgr.get_session(host, username, password, verify_ssl)
response = session.get(f"{host}/api/v2/monitor/...")
```

This provides:
- Connection pooling to reduce overhead
- Automatic session cleanup
- Cookie-based authentication persistence
- SSL verification handling

### Frontend Structure

**Templates** (`app/templates/`):
- `index.html` - Main dashboard landing page
- `topology.html` - 2D Security Fabric visualization
- `topology_3d.html` - Three.js 3D force graph topology
- `topology_fortigate.html` - FortiGate-style topology view
- `switches.html` - FortiSwitch management interface
- `enterprise.html` - Enterprise multi-org dashboard
- `meraki.html` - Cisco Meraki integration page

**Static Assets** (`app/static/`):
- `icons/` - Device icon libraries (Fortinet, Meraki, generic network devices)
- `vendor/` - Local fallback for Three.js and 3d-force-graph (CDN with SRI)

### Multi-Vendor Integration

**FortiGate API Integration**:
- Authentication: API token via `/logincheck` or token file
- Endpoints: Monitor API (`/api/v2/monitor/`) and Management API (`/api/v2/cmdb/`)
- SSL handling: Support for self-signed certificates via `FORTIGATE_VERIFY_SSL=false`

**FortiSwitch Management**:
- Managed via FortiGate controller (not direct access)
- Discovery endpoint: `/api/v2/monitor/switch-controller/managed-switch`
- Port details: Per-switch via `/api/v2/monitor/switch-controller/managed-switch/health`

**Cisco Meraki API**:
- REST API via `meraki_service.py`
- Organization-based device management
- Network and device inventory queries

### Scraping System Architecture

**FortiGate Web UI Scraping** (`scraped_topology_service.py`):
- Selenium-based automation for topology extraction
- Parses FortiGate Security Fabric web UI
- Extracts device positions, connections, and metadata
- Converts scraped data to topology JSON format

**Brand Detection** (`brand_detection_service.py`):
- AI-powered device brand/model identification
- Fallback to OUI lookup when AI detection unavailable
- Supports custom brand detection models

## Configuration

### Environment Variables

**FortiGate Configuration**:
```bash
FORTIGATE_HOST=https://192.168.0.254
FORTIGATE_USERNAME=admin
FORTIGATE_PASSWORD=your-password
FORTIGATE_API_PORT=8443
FORTIGATE_VERIFY_SSL=false
FORTIGATE_API_TOKEN_FILE=/app/secrets/fortigate_api_token.txt
```

**FortiSwitch Configuration**:
```bash
FORTISWITCH_HOST=192.168.0.253  # Usually managed via FortiGate
FORTISWITCH_PASSWORD_FILE=/app/secrets/fortiswitch_password.txt
```

**Database Configuration**:
```bash
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
POSTGRES_HOST=postgres
POSTGRES_DB=fortigate_dashboard
POSTGRES_USER=dashboard_user
POSTGRES_PASSWORD=dashboard_pass
NEO4J_URI=bolt://neo4j:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=neo4j_password
```

**Optional Integrations**:
```bash
MERAKI_API_KEY=your_meraki_api_key
SNMP_COMMUNITY=netintegrate
ERASER_ENABLED=true
ERASER_API_URL=https://app.eraser.io
ERASER_API_KEY_FILE=/app/secrets/eraser_api_token.txt
```

### Secrets Management

Store sensitive data in `secrets/` directory (mounted read-only in containers):
```bash
mkdir -p secrets
echo "your-api-token" > secrets/fortigate_api_token.txt
echo "your-password" > secrets/fortigate_password.txt
echo "your-password" > secrets/fortiswitch_password.txt
echo "your-eraser-key" > secrets/eraser_api_token.txt
chmod 600 secrets/*
```

### Volume Mounts

Persistent data locations:
- `./app/static/icons` - Device icon library (read/write)
- `./app/data` - OUI cache and persistent data
- `./secrets` - API tokens and passwords (read-only)
- Named volumes: `redis_data`, `postgres_data`, `neo4j_data`, `prometheus_data`, `grafana_data`

## Key Patterns and Conventions

### Service Initialization Pattern

Services use singleton pattern with factory functions:

```python
# In service file
_hybrid_topology_service = None

def get_hybrid_topology_service():
    global _hybrid_topology_service
    if _hybrid_topology_service is None:
        _hybrid_topology_service = HybridTopologyService()
    return _hybrid_topology_service
```

### Error Handling

Fortinet API calls should handle common errors:
- SSL certificate verification failures (self-signed certs)
- Authentication failures (expired sessions, invalid tokens)
- Network timeouts (corporate proxies, firewall rules)
- Rate limiting (OUI lookup service limited to 50 req/min)

### Icon Lookup System

Device icons resolved via multi-tier fallback:
1. Database lookup by manufacturer (`app/utils/icon_db.py`)
2. Database lookup by device type
3. Hardcoded fallback mapping in `get_device_icon_fallback()`
4. Default unknown device icon (`icons/Application.svg`)

### Caching Strategy

- **OUI lookups**: Persistent JSON cache (`app/data/oui_cache.json`)
- **API responses**: Redis-based caching with TTL
- **Session objects**: Redis connection pooling
- **Static assets**: Browser cache headers for icons/vendor files

## API Endpoints

### Topology Endpoints

```
GET  /                          # Main dashboard landing page
GET  /topology                  # 2D Security Fabric visualization
GET  /topology-3d               # 3D force graph topology
GET  /topology-fortigate        # FortiGate-style topology view
GET  /api/topology_data         # Topology JSON data
GET  /api/hybrid_topology       # Combined SNMP/API topology data
```

### FortiSwitch Endpoints

```
GET  /switches                  # FortiSwitch management UI
GET  /fortigate/api/switches    # Switch inventory JSON
GET  /fortigate/api/interfaces  # FortiGate interface status
```

### Monitoring Endpoints

```
GET  /health                    # Application health check
GET  /api/metrics               # Prometheus metrics (if enabled)
```

### Integration Endpoints

```
POST /api/eraser/export         # Export topology to Eraser.io (requires ERASER_ENABLED=true)
GET  /meraki                    # Meraki integration page
```

## Service Access Ports

- **Dashboard**: 8000 (FastAPI app)
- **NGINX**: 80, 443 (reverse proxy)
- **Redis**: 6379
- **PostgreSQL**: 5432
- **Neo4j**: 7474 (HTTP), 7687 (Bolt)
- **Prometheus**: 9090
- **Grafana**: 3000

## Debugging

### View Logs

```bash
# Dashboard application logs
docker compose logs -f fortigate-dashboard

# Filter for specific issues
docker compose logs fortigate-dashboard | grep "ERROR"
docker compose logs fortigate-dashboard | grep "API"
docker compose logs fortigate-dashboard | grep "Session"

# Database logs
docker compose logs redis
docker compose logs postgres
docker compose logs neo4j
```

### Common Issues

**FortiGate Authentication**:
- Check `FORTIGATE_VERIFY_SSL=false` for self-signed certificates
- Verify API token file exists and is readable
- Check FortiGate allows API access from container IP

**Session/Redis Issues**:
- Verify Redis is accessible: `docker compose exec redis redis-cli ping`
- Check session cleanup: `docker compose logs redis | grep "session"`
- Monitor connection pool: View Redis connections with `redis-cli CLIENT LIST`

**Icon/Asset Loading**:
- Check volume mount permissions: `ls -la app/static/icons`
- Verify icon database seeding: Search logs for "seed_default_icons"
- Check CDN fallback: Test with network disabled to verify local vendor files

### Health Checks

All services have health checks defined in docker-compose files:
- Dashboard: `curl -f http://localhost:8000/`
- Redis: `redis-cli ping`
- PostgreSQL: `pg_isready`
- Neo4j: `cypher-shell` connectivity test

## Development Workflow

1. **Setup**: Copy `.env.example` to `.env` and configure credentials
2. **Secrets**: Create `secrets/` directory with required token/password files
3. **Build**: `docker compose up --build -d`
4. **Access**: Navigate to `http://localhost:8000`
5. **Develop**: Edit code (hot-reload enabled in dev mode)
6. **Test**: Add tests in `tests/` directory, run with `pytest`
7. **Commit**: Always update GitHub repository after changes

## GitHub Actions (to be implemented)

Per project guidelines, GitHub Actions should include:
- pytest execution on push/PR
- Code linting (black, flake8)
- Docker image builds
- Security scanning

## Enterprise Deployment Considerations

- **Corporate Proxies**: All HTTP clients support proxy configuration
- **SSL Certificates**: Mount corporate CA bundle for Zscaler/proxy environments
- **Multi-Organization**: Use `organization_service.py` for managing multiple customer networks
- **Scalability**: Redis connection pooling and async operations handle 812+ devices across 7 orgs
- **Monitoring**: Prometheus/Grafana stack for production observability
- **Backup**: Regular database snapshots for PostgreSQL and Neo4j
