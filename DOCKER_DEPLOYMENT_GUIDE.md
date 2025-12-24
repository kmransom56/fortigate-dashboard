# Docker Deployment Guide - FortiGate Enterprise Dashboard

This guide covers Docker deployment options for the FortiGate Dashboard, from development to enterprise-scale deployments managing 5,300+ FortiGate locations across three restaurant brands.

## 🏗️ Architecture Overview

The FortiGate Dashboard uses a multi-service Docker architecture:

- **Dashboard App**: FastAPI application with enterprise features
- **Redis**: Caching and session management
- **PostgreSQL**: Enterprise data persistence (production/enterprise)
- **NGINX**: Load balancing and SSL termination (enterprise)
- **Monitoring**: Prometheus, Grafana, ELK Stack (enterprise)

## 📋 Prerequisites

### System Requirements

**Development:**
- Docker Engine 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum
- 10GB disk space

**Production:**
- Docker Engine 20.10+
- Docker Compose 2.0+
- 8GB RAM minimum
- 50GB disk space

**Enterprise:**
- Docker Swarm or Kubernetes
- 16GB+ RAM per node
- 100GB+ disk space
- Load balancer capabilities

### Required Files

1. **FortiGate Inventory**: `downloaded_files/vlan10_interfaces.csv` (5,300+ locations)
2. **Secrets Directory**: `secrets/` with credential files
3. **SSL Certificates**: `nginx/ssl/` (for HTTPS)

## 🚀 Quick Start

### Development Deployment

```bash
# Clone and navigate to project
cd fortigate-dashboard

# Start development stack
docker compose up -d

# Access dashboard
open http://localhost:10000
```

### Production Deployment

```bash
# Deploy production stack
docker compose -f compose.yml -f docker-compose.prod.yml up -d

# Verify deployment
curl http://localhost:10000/api/enterprise/summary
```

### Enterprise Deployment

```bash
# Use deployment script (recommended)
./scripts/deploy_enterprise.sh enterprise 3

# Or manual deployment
docker compose -f compose.yml -f docker-compose.enterprise.yml up -d
```

## 📁 File Structure

```
fortigate-dashboard/
├── Dockerfile                          # Multi-stage build definition
├── compose.yml                         # Base Docker Compose
├── docker-compose.prod.yml             # Production overrides
├── docker-compose.enterprise.yml       # Enterprise HA configuration
├── nginx/
│   ├── nginx.conf                      # Load balancer config
│   └── ssl/                            # SSL certificates
├── secrets/                            # Credential files
│   ├── fortigate_password.txt
│   ├── fortiswitch_password.txt
│   └── postgres_password.txt
├── downloaded_files/
│   └── vlan10_interfaces.csv          # FortiGate inventory
└── scripts/
    └── deploy_enterprise.sh            # Deployment automation
```

## 🔧 Configuration

### Environment Variables

**Core Configuration:**
```bash
# FortiGate Settings
FORTIGATE_HOST=https://192.168.0.254
FORTIGATE_USERNAME=admin
FORTIGATE_VERIFY_SSL=false

# Enterprise Features
ENABLE_ENTERPRISE_FEATURES=true
FORTIGATE_INVENTORY_CSV_PATH=/app/downloaded_files/vlan10_interfaces.csv

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
CACHE_TTL=300

# Application Settings
LOG_LEVEL=INFO
MAX_WORKERS=2
```

**Enterprise-Specific:**
```bash
# Meraki Integration (BWW/Arby's)
MERAKI_API_KEY=your_meraki_api_key
MERAKI_ORG_FILTER=bww

# Performance Tuning
DISCOVERY_BATCH_SIZE=100
MAX_CONCURRENT_DISCOVERIES=50
API_RATE_LIMIT_PER_SECOND=200

# Database
POSTGRES_DB=fortigate_enterprise
POSTGRES_USER=dashboard
```

### Resource Limits

**Development:**
```yaml
resources:
  limits:
    memory: 1G
    cpus: '1.0'
```

**Production:**
```yaml
resources:
  limits:
    memory: 2G
    cpus: '2.0'
```

**Enterprise:**
```yaml
resources:
  limits:
    memory: 4G
    cpus: '4.0'
```

## 🏭 Deployment Scenarios

### Scenario 1: Home Lab Development

**Use Case**: Testing, development, and demonstration
**Scale**: Single FortiGate + FortiSwitch

```bash
# Simple development startup
docker compose up -d

# Access services
echo "Dashboard: http://localhost:10000"
echo "Enterprise View: http://localhost:10000/enterprise"
```

### Scenario 2: Production Single-Site

**Use Case**: Production deployment for single restaurant location
**Scale**: 1 FortiGate + network infrastructure

```bash
# Production deployment
docker compose -f compose.yml -f docker-compose.prod.yml up -d

# Enable monitoring
docker compose -f compose.yml -f docker-compose.prod.yml up -d --profile monitoring
```

### Scenario 3: Enterprise Multi-Brand

**Use Case**: Corporate headquarters managing all restaurant brands
**Scale**: 5,300+ FortiGates across Sonic, BWW, and Arby's

```bash
# Enterprise deployment with HA
./scripts/deploy_enterprise.sh enterprise 5

# Verify enterprise features
curl http://localhost:10000/api/fortigate/inventory/summary
curl http://localhost:10000/api/organizations
```

## 🔍 Monitoring and Logging

### Health Checks

**Application Health:**
```bash
# Check container status
docker compose ps

# Test API endpoints
curl http://localhost:10000/api/enterprise/summary
curl http://localhost:10000/api/fortigate/inventory/summary
```

**Enterprise Monitoring:**
```bash
# Prometheus metrics
open http://localhost:9090

# Grafana dashboards
open http://localhost:3000
# Default login: admin / (check secrets/grafana_password.txt)

# Elasticsearch logs (with profile)
docker compose --profile logging up -d
open http://localhost:5601
```

### Log Management

**View Container Logs:**
```bash
# Dashboard application logs
docker compose logs -f dashboard

# All services logs
docker compose logs -f

# Specific service with timestamps
docker compose logs -f --timestamps redis
```

**Log Locations:**
- Application logs: `/app/logs/`
- NGINX logs: `/var/log/nginx/`
- Container logs: `docker compose logs`

## 📊 Performance Tuning

### Database Optimization

**PostgreSQL Settings:**
```yaml
environment:
  - POSTGRES_SHARED_BUFFERS=256MB
  - POSTGRES_EFFECTIVE_CACHE_SIZE=1GB
  - POSTGRES_MAINTENANCE_WORK_MEM=64MB
  - POSTGRES_CHECKPOINT_COMPLETION_TARGET=0.9
```

**Redis Optimization:**
```yaml
command: >
  redis-server --appendonly yes 
  --maxmemory 2gb 
  --maxmemory-policy allkeys-lru 
  --tcp-keepalive 300
```

### Application Scaling

**Horizontal Scaling:**
```bash
# Scale dashboard instances
docker compose up -d --scale dashboard=5

# Scale with resource limits
docker compose -f compose.yml -f docker-compose.enterprise.yml up -d --scale dashboard=3
```

**Load Balancing:**
- NGINX handles load balancing across dashboard instances
- Rate limiting configured per endpoint type
- Health checks ensure traffic goes to healthy instances

## 🔐 Security Configuration

### SSL/TLS Setup

**Generate Self-Signed Certificates:**
```bash
mkdir -p nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout nginx/ssl/dashboard.key \
    -out nginx/ssl/dashboard.crt \
    -subj "/CN=dashboard.enterprise.local"
```

**Production Certificates:**
```bash
# Copy your certificates
cp your-cert.crt nginx/ssl/dashboard.crt
cp your-private-key.key nginx/ssl/dashboard.key
```

### Secrets Management

**Create Required Secrets:**
```bash
# FortiGate authentication
echo "your_fortigate_password" > secrets/fortigate_password.txt

# FortiSwitch authentication  
echo "your_fortiswitch_password" > secrets/fortiswitch_password.txt

# Database password
openssl rand -base64 32 > secrets/postgres_password.txt

# Monitoring passwords
openssl rand -base64 16 > secrets/grafana_password.txt
```

### Network Security

**Firewall Rules:**
```bash
# Allow dashboard access
iptables -A INPUT -p tcp --dport 10000 -j ACCEPT

# Allow HTTPS (enterprise)
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Monitoring (restrict as needed)
iptables -A INPUT -p tcp --dport 3000 -s trusted_network/24 -j ACCEPT
```

## 🚨 Troubleshooting

### Common Issues

**1. FortiGate Inventory Not Loading**
```bash
# Check CSV file
ls -la downloaded_files/vlan10_interfaces.csv
head -5 downloaded_files/vlan10_interfaces.csv

# Check container logs
docker compose logs dashboard | grep -i inventory
```

**2. High Memory Usage**
```bash
# Monitor resource usage
docker stats

# Adjust memory limits in compose files
# Increase Redis maxmemory setting
```

**3. API Timeouts**
```bash
# Check NGINX timeout settings
docker compose exec nginx nginx -t

# Increase timeouts in nginx.conf
proxy_read_timeout 600s;
```

**4. Container Health Check Failures**
```bash
# Check health status
docker compose ps

# Manual health check
docker compose exec dashboard curl http://localhost:10000/api/enterprise/summary
```

### Performance Issues

**Slow Dashboard Loading:**
1. Check Redis connectivity
2. Verify CSV file is properly mounted
3. Monitor CPU/memory usage
4. Check network connectivity to FortiGate

**API Rate Limiting:**
1. Adjust NGINX rate limits
2. Increase API timeout values
3. Scale dashboard instances

### Recovery Procedures

**Complete Reset:**
```bash
# Stop all services
docker compose -f compose.yml -f docker-compose.enterprise.yml down

# Remove volumes (careful!)
docker volume prune

# Rebuild and restart
./scripts/deploy_enterprise.sh enterprise
```

**Backup and Restore:**
```bash
# Backup important data
docker run --rm -v fortigate-enterprise_postgres_data:/data -v $(pwd):/backup postgres:15-alpine tar czf /backup/postgres-backup.tar.gz -C /data .

# Restore data
docker run --rm -v fortigate-enterprise_postgres_data:/data -v $(pwd):/backup postgres:15-alpine tar xzf /backup/postgres-backup.tar.gz -C /data
```

## 📈 Scaling Guidelines

### Vertical Scaling (Single Node)

**Resource Allocation:**
- **Small**: 4GB RAM, 2 CPU cores (up to 1000 FortiGates)
- **Medium**: 8GB RAM, 4 CPU cores (up to 3000 FortiGates)  
- **Large**: 16GB RAM, 8 CPU cores (5000+ FortiGates)

### Horizontal Scaling (Multi-Node)

**Docker Swarm:**
```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c compose.yml -c docker-compose.enterprise.yml fortigate-enterprise
```

**Kubernetes:**
- Use Helm charts (development in progress)
- Configure persistent volumes
- Set up ingress controllers
- Implement horizontal pod autoscaling

## 🔄 CI/CD Integration

### GitHub Actions

```yaml
name: Deploy Enterprise Dashboard
on:
  push:
    branches: [main]
  
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to production
        run: |
          docker compose -f compose.yml -f docker-compose.prod.yml up -d
          ./scripts/deploy_enterprise.sh production
```

### Automated Testing

```bash
# Health check integration
./scripts/deploy_enterprise.sh development
curl -f http://localhost:10000/api/enterprise/summary || exit 1
```

This guide provides comprehensive Docker deployment options for the FortiGate Dashboard, from simple development setups to enterprise-scale deployments capable of managing thousands of FortiGate locations across multiple restaurant brands.