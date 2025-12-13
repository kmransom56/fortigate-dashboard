# Docker Compose Troubleshooting Guide
## FortiGate Dashboard - Grafana Startup Issues

---

## 🔍 Problems Identified

### 1. **Grafana Network Unreachable**
```
Error: dial tcp: lookup grafana.com on 192.168.65.7:53: dial udp 192.168.65.7:53: connect: network is unreachable
```
- **Cause**: Grafana trying to download plugins from internet during startup
- **Impact**: Container restarts in a loop, never becomes healthy

### 2. **Deprecated Plugin Installation**
```
WARN: GF_INSTALL_PLUGINS is deprecated. Use GF_PLUGINS_PREINSTALL or GF_PLUGINS_PREINSTALL_SYNC instead
```
- **Cause**: Using old environment variable for plugin installation
- **Impact**: Warning messages, potential future compatibility issues

### 3. **Missing Provisioning Directories**
```
logger=provisioning.dashboard: can't read dashboard provisioning files from directory
path=/etc/grafana/provisioning/dashboards error="open /etc/grafana/provisioning/dashboards: no such file or directory"
```
- **Cause**: Volume mounts pointing to non-existent host directories
- **Impact**: Dashboard provisioning fails, but Grafana still runs

### 4. **Missing Configuration Files**
- `./redis.conf` - Redis trying to load config that doesn't exist
- `./monitoring/prometheus.yml` - Prometheus has no config
- `./nginx/nginx.conf` - NGINX has no config

---

## ✅ Solution Summary

**What Changed:**
1. ❌ Removed deprecated `GF_INSTALL_PLUGINS` environment variable
2. ❌ Removed non-existent volume mounts for Grafana dashboards/provisioning
3. ❌ Removed Redis config file mount (using defaults)
4. ❌ Removed Prometheus config mount (will create minimal config)
5. ❌ Removed NGINX config mount (using defaults)

**Result:** 
- Grafana starts immediately without network calls
- Services use sensible defaults
- Plugins can be installed manually via UI after startup

---

## 🚀 Quick Fix Steps

### Step 1: Stop Current Stack
```bash
cd D:\projects\fortigate-visio-topology  # or wherever your docker-compose.yml is
docker-compose down
```

### Step 2: Backup Original
```bash
copy docker-compose.yml docker-compose.yml.backup
```

### Step 3: Replace with Fixed Version
Replace your `docker-compose.yml` with the fixed version provided.

### Step 4: Start Services
```bash
docker-compose up -d
```

### Step 5: Verify Status
```bash
docker-compose ps
docker-compose logs grafana | tail -20
```

---

## 📊 Service Access After Fix

| Service | URL | Default Credentials |
|---------|-----|-------------------|
| FortiGate Dashboard | http://localhost:8000 | - |
| Grafana | http://localhost:3001 | admin / admin_password |
| Prometheus | http://localhost:9091 | - |
| Redis | localhost:6380 | - |
| PostgreSQL | localhost:5437 | dashboard_user / dashboard_pass |
| Neo4j Browser | http://localhost:7475 | neo4j / neo4j_password |
| NGINX | http://localhost:8081 | - |

---

## 🔧 Optional: Add Grafana Plugins Manually

If you need the piechart and worldmap plugins:

### Option 1: Via Grafana UI
1. Open http://localhost:3001
2. Login with admin / admin_password
3. Go to Administration → Plugins
4. Search and install desired plugins

### Option 2: Via Docker Exec
```bash
docker exec -it fortigate-grafana grafana-cli plugins install grafana-piechart-panel
docker exec -it fortigate-grafana grafana-cli plugins install grafana-worldmap-panel
docker restart fortigate-grafana
```

---

## 📁 Optional: Create Minimal Configs

If you want to customize Prometheus or NGINX later:

### Prometheus Config (monitoring/prometheus.yml)
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
  
  - job_name: 'fortigate-dashboard'
    static_configs:
      - targets: ['fortigate-dashboard:8000']
```

### NGINX Config (nginx/nginx.conf)
```nginx
events {
    worker_connections 1024;
}

http {
    server {
        listen 80;
        location / {
            proxy_pass http://fortigate-dashboard:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}
```

Then update docker-compose.yml to mount these:
```yaml
prometheus:
  volumes:
    - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
    - prometheus_data:/prometheus

nginx:
  volumes:
    - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    - nginx_logs:/var/log/nginx
```

---

## 🐛 Troubleshooting Common Issues

### Grafana Still Won't Start
```bash
# Check logs
docker-compose logs grafana

# Remove old volume and restart
docker-compose down -v
docker volume rm fortigate-visio-topology_grafana_data
docker-compose up -d
```

### PostgreSQL Connection Issues
```bash
# Test connection
docker exec -it fortigate-postgres psql -U dashboard_user -d fortigate_dashboard

# If fails, recreate database
docker-compose down
docker volume rm fortigate-visio-topology_postgres_data
docker-compose up -d postgres
```

### Port Conflicts
If ports are already in use, modify in docker-compose.yml:
```yaml
ports:
  - "3002:3000"  # Change 3001 to 3002 if conflict
```

### Check All Service Health
```bash
docker-compose ps
docker stats --no-stream
docker-compose logs --tail=50
```

---

## 📝 Next Steps After Fix

1. ✅ Verify all services are running: `docker-compose ps`
2. ✅ Access Grafana at http://localhost:3001
3. ✅ Set up Prometheus data source in Grafana
4. ✅ Configure dashboards for monitoring
5. ✅ Test FortiGate Dashboard functionality

---

## 💾 Files Needed

**Minimum to run:**
- ✅ `docker-compose.yml` (fixed version provided)
- ✅ `Dockerfile` (for fortigate-dashboard service)
- ✅ `./secrets/` directory with token files (if using API tokens)

**Optional for full features:**
- `./monitoring/prometheus.yml` (for custom metrics)
- `./nginx/nginx.conf` (for custom routing)
- `./init-scripts/` (for PostgreSQL initialization)

---

## 🔒 Security Notes

1. **Change default passwords** in production:
   - Grafana admin password
   - PostgreSQL password
   - Neo4j password

2. **Use secrets files** instead of environment variables for sensitive data

3. **Enable HTTPS** on NGINX for production deployments

---

Need help? Check:
- Grafana logs: `docker-compose logs grafana`
- All logs: `docker-compose logs`
- Container status: `docker-compose ps`
