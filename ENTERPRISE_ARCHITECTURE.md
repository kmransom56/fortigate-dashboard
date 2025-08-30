# Enterprise Multi-Tenant FortiGate Dashboard Architecture

## Scale Requirements

**Total Infrastructure:**
- **5,900 FortiGate firewalls** across 3 restaurant brands
- **Sonic Drive-In**: 3,500 locations (FortiGate + FortiSwitch + FortiAP)
- **Buffalo Wild Wings**: 900 locations (FortiGate + Meraki + FortiAP)
- **Arby's**: 1,500 locations (FortiGate + Meraki + FortiAP)

**Estimated Device Count:**
- ~5,900 FortiGate firewalls
- ~3,500 FortiSwitches (Sonic only)
- ~3,600 Meraki switches (BWW + Arby's: 900 + 1,500 + extras)
- ~11,800+ FortiAPs (2+ per location)
- ~350,000+ restaurant endpoint devices
- **Total: ~375,000+ managed network devices**

## Multi-Tenant Architecture Design

### 1. Organization Hierarchy
```
Enterprise Dashboard
├── Sonic Drive-In (3,500 locations)
│   ├── Region 1 (North)
│   ├── Region 2 (South)
│   ├── Region 3 (East)
│   └── Region 4 (West)
├── Buffalo Wild Wings (900 locations)
│   ├── Corporate Stores
│   └── Franchise Groups
└── Arby's (1,500 locations)
    ├── Company Stores
    └── Franchise Operations
```

### 2. Database Architecture

#### PostgreSQL Primary Database
```sql
-- Organizations table
CREATE TABLE organizations (
    id UUID PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    brand ENUM('sonic', 'bww', 'arbys') NOT NULL,
    region VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Locations table
CREATE TABLE locations (
    id UUID PRIMARY KEY,
    organization_id UUID REFERENCES organizations(id),
    store_number VARCHAR(20) NOT NULL,
    name VARCHAR(200) NOT NULL,
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(50),
    country VARCHAR(50),
    timezone VARCHAR(50),
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    status ENUM('active', 'inactive', 'maintenance') DEFAULT 'active',
    infrastructure_type ENUM('fortinet_full', 'fortinet_meraki', 'mixed') NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Devices table (partitioned by organization)
CREATE TABLE devices (
    id UUID PRIMARY KEY,
    location_id UUID REFERENCES locations(id),
    device_type ENUM('fortigate', 'fortiswitch', 'fortiap', 'meraki_switch', 'restaurant_pos', 'restaurant_camera', 'restaurant_kiosk', 'endpoint') NOT NULL,
    hostname VARCHAR(255),
    ip_address INET,
    mac_address MACADDR,
    serial_number VARCHAR(100),
    model VARCHAR(100),
    firmware_version VARCHAR(50),
    management_ip INET,
    last_seen TIMESTAMP,
    status ENUM('online', 'offline', 'warning', 'error') DEFAULT 'offline',
    security_risk ENUM('low', 'medium', 'high', 'critical') DEFAULT 'medium',
    restaurant_device BOOLEAN DEFAULT FALSE,
    device_category VARCHAR(50),
    manufacturer VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
) PARTITION BY HASH (location_id);

-- Create partitions for better performance
CREATE TABLE devices_p1 PARTITION OF devices FOR VALUES WITH (modulus 10, remainder 0);
CREATE TABLE devices_p2 PARTITION OF devices FOR VALUES WITH (modulus 10, remainder 1);
-- ... continue for all 10 partitions

-- Device connections (for topology mapping)
CREATE TABLE device_connections (
    id UUID PRIMARY KEY,
    source_device_id UUID REFERENCES devices(id),
    target_device_id UUID REFERENCES devices(id),
    connection_type ENUM('ethernet', 'wifi', 'fortilink', 'api') NOT NULL,
    port_name VARCHAR(50),
    bandwidth_mbps INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Performance metrics (time-series data)
CREATE TABLE device_metrics (
    device_id UUID REFERENCES devices(id),
    timestamp TIMESTAMP NOT NULL,
    cpu_usage DECIMAL(5,2),
    memory_usage DECIMAL(5,2),
    uptime_seconds BIGINT,
    interface_utilization JSON,
    security_events INTEGER DEFAULT 0,
    PRIMARY KEY (device_id, timestamp)
) PARTITION BY RANGE (timestamp);
```

#### Redis Cache Layer
```redis
# Organization cache (1 hour TTL)
organizations:{org_id}:locations    # List of location IDs
organizations:{org_id}:stats        # Cached statistics

# Location cache (30 min TTL)
location:{location_id}:devices      # Device list
location:{location_id}:topology     # Topology data
location:{location_id}:status       # Health status

# Device cache (5 min TTL)
device:{device_id}:details          # Device information
device:{device_id}:metrics          # Recent metrics

# Real-time data (1 min TTL)
realtime:alerts:{org_id}            # Active alerts
realtime:events:{location_id}       # Recent events
```

### 3. API Architecture

#### Multi-Tenant API Design
```python
# Base URL structure
/api/v1/{organization_id}/locations
/api/v1/{organization_id}/locations/{location_id}/devices
/api/v1/{organization_id}/locations/{location_id}/topology
/api/v1/{organization_id}/dashboard/overview
/api/v1/{organization_id}/alerts
/api/v1/{organization_id}/reports

# Enterprise-level endpoints
/api/v1/enterprise/overview          # All organizations
/api/v1/enterprise/alerts            # Cross-organization alerts
/api/v1/enterprise/compliance        # Compliance reporting
```

#### Authentication & Authorization
```python
class OrganizationPermissions:
    SONIC_ADMIN = "sonic:admin"
    SONIC_VIEWER = "sonic:viewer"
    BWW_ADMIN = "bww:admin"
    BWW_VIEWER = "bww:viewer"
    ARBYS_ADMIN = "arbys:admin"
    ARBYS_VIEWER = "arbys:viewer"
    ENTERPRISE_ADMIN = "enterprise:admin"
```

### 4. Infrastructure Components

#### Load Balancer Configuration
```nginx
upstream fortigate_dashboard_backend {
    least_conn;
    server dashboard-app-1:8000;
    server dashboard-app-2:8000;
    server dashboard-app-3:8000;
    server dashboard-app-4:8000;
}

# Organization-specific routing
location /api/v1/sonic/ {
    proxy_pass http://sonic_backend;
    proxy_set_header X-Organization "sonic";
}

location /api/v1/bww/ {
    proxy_pass http://bww_backend;
    proxy_set_header X-Organization "bww";
}

location /api/v1/arbys/ {
    proxy_pass http://arbys_backend;
    proxy_set_header X-Organization "arbys";
}
```

#### Message Queue Architecture
```python
# Celery task queues for different operations
CELERY_ROUTES = {
    'device_discovery.*': {'queue': 'discovery'},
    'metrics_collection.*': {'queue': 'metrics'},
    'alerts.*': {'queue': 'alerts'},
    'reports.*': {'queue': 'reports'},
    'compliance.*': {'queue': 'compliance'}
}

# Priority queues
HIGH_PRIORITY = ['security_alerts', 'device_failures']
NORMAL_PRIORITY = ['device_discovery', 'metrics_collection']
LOW_PRIORITY = ['reporting', 'cleanup']
```

### 5. Discovery & Data Collection

#### Distributed Discovery Architecture
```python
# Discovery coordinators per region
DISCOVERY_COORDINATORS = {
    'sonic_north': {'locations': 875, 'coordinator': 'sonic-dc-north'},
    'sonic_south': {'locations': 875, 'coordinator': 'sonic-dc-south'},
    'sonic_east': {'locations': 875, 'coordinator': 'sonic-dc-east'},
    'sonic_west': {'locations': 875, 'coordinator': 'sonic-dc-west'},
    'bww': {'locations': 900, 'coordinator': 'bww-dc-central'},
    'arbys_corporate': {'locations': 800, 'coordinator': 'arbys-dc-corp'},
    'arbys_franchise': {'locations': 700, 'coordinator': 'arbys-dc-fran'}
}

# Rate limiting per organization
RATE_LIMITS = {
    'sonic': {'requests_per_second': 100, 'concurrent_locations': 50},
    'bww': {'requests_per_second': 25, 'concurrent_locations': 15},
    'arbys': {'requests_per_second': 40, 'concurrent_locations': 25}
}
```

#### Device Discovery Strategies
```python
# FortiGate discovery (all brands)
- FortiManager integration where available
- Direct API polling with token rotation
- SNMP fallback for legacy devices

# FortiSwitch discovery (Sonic only)
- FortiLink integration via FortiGate
- SNMP community scanning
- Switch stacking detection

# FortiAP discovery (all brands)
- FortiGate wireless controller integration
- WLC API polling
- CAPWAP tunnel monitoring

# Meraki discovery (BWW/Arby's only)
- Meraki Dashboard API integration
- Organization-level access tokens
- Network-specific device enumeration
```

### 6. Performance Optimization

#### Caching Strategy
```python
# Multi-level caching
L1_CACHE = Redis()          # Hot data (1-5 min TTL)
L2_CACHE = PostgreSQL()     # Warm data (hourly aggregates)
L3_CACHE = S3/MinIO()      # Cold data (historical reports)

# Cache warming schedules
CACHE_WARMING = {
    'topology_data': '*/5 * * * *',      # Every 5 minutes
    'device_stats': '*/15 * * * *',      # Every 15 minutes
    'location_health': '*/10 * * * *',   # Every 10 minutes
    'org_dashboards': '*/30 * * * *'     # Every 30 minutes
}
```

#### Database Optimization
```sql
-- Indexes for performance
CREATE INDEX CONCURRENTLY idx_devices_location_type ON devices(location_id, device_type);
CREATE INDEX CONCURRENTLY idx_devices_org_status ON devices(organization_id, status);
CREATE INDEX CONCURRENTLY idx_devices_restaurant ON devices(restaurant_device, device_category);
CREATE INDEX CONCURRENTLY idx_metrics_device_time ON device_metrics(device_id, timestamp DESC);

-- Materialized views for reporting
CREATE MATERIALIZED VIEW org_device_summary AS
SELECT 
    o.name as organization,
    o.brand,
    COUNT(DISTINCT l.id) as location_count,
    COUNT(d.id) as device_count,
    COUNT(d.id) FILTER (WHERE d.device_type = 'fortigate') as fortigate_count,
    COUNT(d.id) FILTER (WHERE d.device_type = 'fortiswitch') as fortiswitch_count,
    COUNT(d.id) FILTER (WHERE d.device_type = 'fortiap') as fortiap_count,
    COUNT(d.id) FILTER (WHERE d.device_type = 'meraki_switch') as meraki_count,
    COUNT(d.id) FILTER (WHERE d.restaurant_device = true) as restaurant_device_count
FROM organizations o
LEFT JOIN locations l ON o.id = l.organization_id
LEFT JOIN devices d ON l.id = d.location_id
GROUP BY o.id, o.name, o.brand;

-- Refresh every hour
CREATE OR REPLACE FUNCTION refresh_org_summary() RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY org_device_summary;
END;
$$ LANGUAGE plpgsql;

SELECT cron.schedule('refresh-org-summary', '0 * * * *', 'SELECT refresh_org_summary();');
```

### 7. Monitoring & Alerting

#### Health Check Architecture
```python
# Multi-level health checks
HEALTH_CHECKS = {
    'location_level': {
        'fortigate_reachability': 60,    # seconds
        'device_discovery_age': 300,     # 5 minutes
        'critical_alerts': 30            # 30 seconds
    },
    'organization_level': {
        'location_health_percentage': 300,  # 5 minutes
        'compliance_status': 1800,          # 30 minutes
        'performance_metrics': 600          # 10 minutes
    },
    'enterprise_level': {
        'overall_availability': 300,        # 5 minutes
        'security_posture': 900,           # 15 minutes
        'capacity_planning': 3600          # 1 hour
    }
}
```

### 8. Security & Compliance

#### Multi-Tenant Security Model
```python
# Role-based access control
RBAC_POLICIES = {
    'sonic_location_admin': ['read_devices', 'manage_devices', 'view_metrics'],
    'sonic_regional_manager': ['read_all_locations', 'manage_locations', 'view_reports'],
    'sonic_enterprise_admin': ['full_access'],
    'bww_franchise_owner': ['read_assigned_locations', 'manage_assigned_devices'],
    'enterprise_security_admin': ['security_management', 'compliance_reporting']
}

# API rate limiting per organization
RATE_LIMITING = {
    'sonic': {'rpm': 10000, 'burst': 1000},
    'bww': {'rpm': 3000, 'burst': 300},
    'arbys': {'rpm': 5000, 'burst': 500}
}
```

### 9. Deployment Strategy

#### Container Orchestration (Kubernetes)
```yaml
# Namespace per organization for isolation
namespaces:
  - sonic-prod
  - bww-prod
  - arbys-prod
  - enterprise-shared

# Horizontal Pod Autoscaling
hpa:
  discovery_workers:
    min_replicas: 10
    max_replicas: 100
    target_cpu: 70%
  
  api_servers:
    min_replicas: 5
    max_replicas: 50
    target_cpu: 60%
```

This enterprise architecture supports massive scale with proper multi-tenancy, performance optimization, and brand separation while maintaining centralized management capabilities.