# FortiGate Dashboard - Password Configuration Guide

## Current Passwords

All passwords have been set to: `letsencrypt#0$`

### Service Access

| Service | URL | Username | Password | Status |
|---------|-----|----------|----------|--------|
| **Neo4j** | http://localhost:11103 | neo4j | letsencrypt#0$ | ✅ Active |
| **Grafana** | http://localhost:11106 | admin | letsencrypt#0$ | ✅ Active |
| **Prometheus** | http://localhost:11107/prometheus/ | admin | letsencrypt#0$ | ✅ Nginx Auth |
| **Dashboard** | http://localhost:11100 | N/A | No auth | ✅ Public |

## Passwords Successfully Configured

### ✅ Neo4j Password: `letsencrypt#0$`

**Configuration files:**
- `docker-compose.yml` line 110: `NEO4J_AUTH=neo4j/letsencrypt#0$`
- `docker-compose.yml` line 125: healthcheck password updated
- `docker-compose.yml` line 34: `NEO4J_PASSWORD=letsencrypt#0$` (environment variable)
- `.env` line 22: `NEO4J_PASSWORD=letsencrypt#0$`

**To apply changes:**
```bash
# Stop Neo4j and remove data volume (required for password change)
docker compose stop neo4j
docker volume rm fortigate-dashboard_neo4j_data

# Restart
docker compose up -d neo4j
```

### ✅ Grafana Password: `letsencrypt#0$`

**Configuration files:**
- `docker-compose.yml` line 155: `GF_SECURITY_ADMIN_PASSWORD=letsencrypt#0$`

**To apply changes:**
```bash
# Simple restart (preserves dashboards)
docker compose restart grafana
```

## Prometheus Authentication

### ✅ Current Status: ACTIVE - Nginx Basic Auth

Prometheus is now protected by nginx reverse proxy with HTTP Basic Authentication.

**Access Details:**
- **URL**: http://localhost:11107/prometheus/
- **Username**: admin
- **Password**: letsencrypt#0$

**Configuration Files:**
- `monitoring/nginx/nginx.conf` - nginx reverse proxy configuration
- `monitoring/nginx/.htpasswd` - password file for basic auth
- `docker-compose.yml` - nginx service configuration

**Direct Access:**
- Port 11105 still provides direct access to Prometheus without auth (for internal use)
- For authenticated external access, use http://localhost:11107/prometheus/

### Alternative Access Methods:

#### Option 1: Through Nginx (Recommended - Password Protected)
- URL: http://localhost:11107/prometheus/
- Requires authentication

#### Option 2: Direct Access (Internal Only)
- URL: http://localhost:11105/
- No authentication (should be firewalled for production)

#### Option 3: Via Grafana
Access Prometheus data through Grafana dashboards:
- URL: http://localhost:11106
- Also password protected

## How to Change Passwords

### Change Neo4j Password:

1. Edit `docker-compose.yml` line 110:
```yaml
- NEO4J_AUTH=neo4j/YOUR_NEW_PASSWORD
```

2. Edit `docker-compose.yml` line 125 (healthcheck):
```yaml
test: ["CMD", "cypher-shell", "-u", "neo4j", "-p", "YOUR_NEW_PASSWORD", "RETURN 1"]
```

3. Edit `.env` line 22:
```
NEO4J_PASSWORD=YOUR_NEW_PASSWORD
```

4. Edit `docker-compose.yml` line 34 (environment):
```yaml
- NEO4J_PASSWORD=YOUR_NEW_PASSWORD
```

5. Recreate Neo4j:
```bash
docker compose stop neo4j
docker volume rm fortigate-dashboard_neo4j_data  # WARNING: Deletes data!
docker compose up -d neo4j
```

### Change Grafana Password:

1. Edit `docker-compose.yml` line 155:
```yaml
- GF_SECURITY_ADMIN_PASSWORD=YOUR_NEW_PASSWORD
```

2. Restart Grafana:
```bash
docker compose restart grafana
```

## Security Notes

1. **Production**: Change these default passwords before deploying to production
2. **Secrets**: Consider using Docker secrets or environment files for sensitive data
3. **Network**: Prometheus is exposed on port 11105 without authentication - consider restricting access
4. **Firewall**: Use firewall rules to restrict access to these ports from untrusted networks

## Quick Password Reset Script

Run this to apply current password configuration:

```bash
cd /home/keith/fortigate-dashboard

# Restart services with new passwords
docker compose restart grafana

# For Neo4j (WARNING: deletes data)
docker compose stop neo4j
docker volume rm fortigate-dashboard_neo4j_data
docker compose up -d neo4j
```

---

**Last Updated**: December 12, 2025
**Password Set**: letsencrypt#0$
