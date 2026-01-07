# 🔧 Troubleshooting Guide

This guide helps you diagnose and resolve common issues with the LTM Network Intelligence Platform.

## 🚨 Quick Diagnostics

### Health Check Command
Run this first to get an overview of system health:

```bash
python unified_network_intelligence.py --health-check
```

### System Status Check
```bash
# Check all service statuses
docker-compose ps  # For Docker deployment
systemctl status neo4j redis postgresql  # For native deployment

# Check platform logs
tail -f logs/ltm_platform.log

# Check platform connectivity
curl -f http://localhost:8002/health || echo "Platform API not responding"
```

---

## 🛠️ Common Installation Issues

### Issue: `Permission denied` during installation

**Symptoms:**
```
chmod: cannot access 'scripts/quick_setup.sh': Permission denied
```

**Solutions:**
```bash
# Fix script permissions
sudo chmod +x scripts/*.sh

# Fix directory ownership
sudo chown -R $USER:$USER /path/to/ltm-platform

# Run with proper permissions
sudo -u $USER ./scripts/quick_setup.sh
```

### Issue: `Port already in use` errors

**Symptoms:**
```
Error: bind: address already in use (port 8002)
Error: bind: address already in use (port 7687)
```

**Solutions:**
```bash
# Find what's using the ports
sudo netstat -tulpn | grep :8002
sudo lsof -i :8002

# Kill conflicting processes
sudo kill -9 [PID]

# Or use different ports in configuration
# Edit config/unified_config.json:
{
  "components": {
    "api_gateway": {
      "port": 8003  // Change from 8002
    }
  }
}
```

### Issue: `Module not found` errors

**Symptoms:**
```
ModuleNotFoundError: No module named 'fastapi'
ModuleNotFoundError: No module named 'milvus'
```

**Solutions:**
```bash
# Reinstall dependencies
pip install --force-reinstall -r requirements.txt

# Update pip first
pip install --upgrade pip

# Clear pip cache
pip cache purge

# Use virtual environment (recommended)
python -m venv ltm-venv
source ltm-venv/bin/activate
pip install -r requirements.txt
```

---

## 🗄️ Database Connection Issues

### Neo4j Connection Problems

**Symptoms:**
```
ServiceUnavailable: Could not connect to bolt://localhost:7687
neo4j.exceptions.AuthError: Authentication failure
```

**Solutions:**
```bash
# Check if Neo4j is running
sudo systemctl status neo4j
docker-compose ps neo4j  # For Docker

# Test connection manually
curl http://localhost:7474/db/neo4j/tx/commit

# Reset Neo4j password
sudo neo4j-admin set-initial-password newpassword

# Update configuration
# Edit config/unified_config.json:
{
  "components": {
    "knowledge_graph": {
      "neo4j_password": "your_new_password"
    }
  }
}
```

### Milvus Connection Issues

**Symptoms:**
```
MilvusException: <MilvusException: (code=1, message=failed to connect to server)>
```

**Solutions:**
```bash
# Check Milvus status
docker ps | grep milvus
curl -f http://localhost:19530/health

# Restart Milvus
docker restart milvus-standalone

# Check Milvus logs
docker logs milvus-standalone

# Alternative: Use standalone Milvus
wget https://raw.githubusercontent.com/milvus-io/milvus/v2.2.0/scripts/standalone_embed.sh
bash standalone_embed.sh start
```

### Redis Connection Problems

**Symptoms:**
```
redis.exceptions.ConnectionError: Error 111 connecting to localhost:6379
```

**Solutions:**
```bash
# Check Redis status
sudo systemctl status redis
docker-compose ps redis

# Test Redis connection
redis-cli ping

# Restart Redis
sudo systemctl restart redis
docker-compose restart redis

# Check Redis configuration
sudo nano /etc/redis/redis.conf
```

### PostgreSQL Issues

**Symptoms:**
```
psycopg2.OperationalError: could not connect to server
```

**Solutions:**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql
docker-compose ps postgres

# Test connection
psql -h localhost -U ltm_user -d ltm_audit

# Check if database exists
sudo -u postgres psql -l | grep ltm_audit

# Create database if missing
sudo -u postgres createdb ltm_audit
sudo -u postgres createuser ltm_user
```

---

## 🔗 Integration Issues

### Repository Integration Failures

**Symptoms:**
```
Repository network-ai-troubleshooter not found at ../network-ai-troubleshooter
Integration failed for FortiGate-Enterprise-Platform
```

**Solutions:**
```bash
# Check repository paths
ls -la ../network-ai-troubleshooter
find ~ -name "network-ai-troubleshooter" -type d 2>/dev/null

# Update integration config
# Edit config/kmransom56_integration_config.json
{
  "integration_categories": {
    "core_network_management": {
      "repositories": {
        "network-ai-troubleshooter": {
          "path": "/correct/path/to/network-ai-troubleshooter"
        }
      }
    }
  }
}

# Rescan for repositories
./scripts/setup_kmransom56_integration.sh --scan-paths /path/to/repos

# Manual integration
python scripts/setup_integration.py --repositories /path/to/repo --force
```

### LTM Server Connection Issues

**Symptoms:**
```
LTM server not responding at http://localhost:8000
Failed to initialize LTM client
```

**Solutions:**
```bash
# Check if LTM server is configured
grep -r "ltm.*server" config/

# Check LTM server status
curl -f http://localhost:8000/health

# Start local LTM fallback mode
# Edit config/unified_config.json:
{
  "ltm": {
    "local_fallback": true,
    "fallback_mode": "file_based"
  }
}

# Test LTM client manually
python -c "
from ltm_integration.ltm_client import LTMClient
import asyncio
async def test():
    client = LTMClient('http://localhost:8000')
    await client.initialize()
    stats = await client.get_session_stats()
    print('LTM Stats:', stats)
asyncio.run(test())
"
```

### Knowledge Graph Bridge Issues

**Symptoms:**
```
Knowledge Graph Bridge initialization failed
Neo4j topology query failed
Milvus collection not found
```

**Solutions:**
```bash
# Test knowledge graph components individually
python -c "
from ltm_integration.knowledge_graph_bridge import KnowledgeGraphBridge
import asyncio
async def test():
    bridge = KnowledgeGraphBridge(None, 
        neo4j_config={'uri': 'bolt://localhost:7687', 'user': 'neo4j', 'password': 'password'},
        milvus_config={'host': 'localhost', 'port': '19530'}
    )
    await bridge.initialize()
    status = await bridge.get_bridge_status()
    print('Bridge Status:', status)
asyncio.run(test())
"

# Reset knowledge graph collections
python scripts/reset_knowledge_graph.py

# Recreate Milvus collections
python -c "
from ltm_integration.knowledge_graph_bridge import KnowledgeGraphBridge
import asyncio
async def recreate():
    bridge = KnowledgeGraphBridge(None, {}, {'host': 'localhost', 'port': '19530'})
    await bridge._create_milvus_collection('network_embeddings')
asyncio.run(recreate())
"
```

---

## 🚀 Performance Issues

### High Memory Usage

**Symptoms:**
```
System running out of memory
Python process consuming excessive RAM
Docker containers being killed (OOMKilled)
```

**Solutions:**
```bash
# Check memory usage
free -h
docker stats

# Reduce LTM memory limits
# Edit config/unified_config.json:
{
  "ltm": {
    "memory_limit": 2000  // Reduce from 5000
  }
}

# Optimize Docker memory
# Edit docker-compose.yml:
services:
  ltm-platform:
    mem_limit: 2g
    mem_reservation: 1g

# Clear Python memory
python -c "
import gc
gc.collect()
"

# Restart platform to clear memory
docker-compose restart ltm-platform
# Or for native
python unified_network_intelligence.py --restart
```

### Slow Response Times

**Symptoms:**
```
API responses taking >10 seconds
Database queries timing out
Dashboard loading slowly
```

**Solutions:**
```bash
# Check database performance
# Neo4j queries
curl -X POST http://localhost:7474/db/neo4j/tx/commit \\
  -H "Content-Type: application/json" \\
  -d '{"statements":[{"statement":"SHOW TRANSACTIONS YIELD *"}]}'

# Check Redis performance
redis-cli --latency-history -i 1

# Optimize configuration
# Edit config/performance_config.json:
{
  "caching": {
    "enabled": true,
    "ttl_seconds": 300
  },
  "database": {
    "connection_pool_size": 20,
    "query_timeout": 30
  }
}

# Add database indexes
python scripts/optimize_database.py --add-indexes
```

---

## 🔐 Security Issues

### Authentication Failures

**Symptoms:**
```
401 Unauthorized
JWT token invalid or expired
Authentication failed for user
```

**Solutions:**
```bash
# Check JWT configuration
grep -r "jwt" config/

# Generate new JWT secret
python -c "
import secrets
print('New JWT Secret:', secrets.token_urlsafe(32))
"

# Update JWT secret in config
# Edit .env file:
JWT_SECRET_KEY=your_new_secret_key_here

# Test authentication manually
curl -X POST "http://localhost:8002/api/auth/login" \\
  -H "Content-Type: application/json" \\
  -d '{"username": "admin", "password": "admin123"}'

# Reset admin password
python scripts/reset_admin_password.py --password newpassword
```

### SSL/TLS Certificate Issues

**Symptoms:**
```
SSL certificate verification failed
HTTPS connections failing
Certificate expired warnings
```

**Solutions:**
```bash
# Check certificate validity
openssl x509 -in config/ssl/platform.crt -text -noout

# Generate new self-signed certificate
openssl req -x509 -newkey rsa:4096 -keyout config/ssl/platform.key \\
  -out config/ssl/platform.crt -days 365 -nodes

# Disable SSL verification for testing (NOT for production)
# Edit config/unified_config.json:
{
  "security": {
    "ssl_verify": false,
    "development_mode": true
  }
}
```

---

## 📊 API Issues

### API Gateway Not Responding

**Symptoms:**
```
Connection refused to localhost:8002
502 Bad Gateway
API endpoints returning 500 errors
```

**Solutions:**
```bash
# Check API gateway process
ps aux | grep api_gateway
docker-compose logs api-gateway

# Test API gateway directly
curl -v http://localhost:8002/health

# Restart API gateway
docker-compose restart api-gateway
# Or for native
pkill -f api_gateway
python api_gateway/ltm_api_gateway.py &

# Check API gateway logs
tail -f logs/api_gateway.log

# Test specific endpoints
curl -X GET "http://localhost:8002/api/docs"
```

### Rate Limiting Issues

**Symptoms:**
```
429 Too Many Requests
Rate limit exceeded
API calls being blocked
```

**Solutions:**
```bash
# Check rate limiting configuration
grep -r "rate_limit" config/

# Temporarily disable rate limiting
# Edit config/unified_config.json:
{
  "components": {
    "api_gateway": {
      "rate_limiting": false
    }
  }
}

# Increase rate limits
{
  "api_gateway": {
    "rate_limits": {
      "requests_per_minute": 1000,  // Increase from default
      "burst_limit": 100
    }
  }
}

# Clear rate limit cache
redis-cli FLUSHDB
```

---

## 🐳 Docker-Specific Issues

### Container Startup Failures

**Symptoms:**
```
Container ltm-platform exited with code 1
Service 'neo4j' failed to start
Docker compose up failing
```

**Solutions:**
```bash
# Check container logs
docker-compose logs ltm-platform
docker-compose logs neo4j

# Check Docker resources
docker system df
docker system prune  # Clean up if low on space

# Restart Docker daemon
sudo systemctl restart docker

# Remove and recreate containers
docker-compose down --volumes
docker-compose up --force-recreate
```

### Volume Mount Issues

**Symptoms:**
```
Permission denied: '/app/config'
Config files not found in container
Logs not persisting
```

**Solutions:**
```bash
# Fix volume permissions
sudo chown -R 1000:1000 ./config ./logs ./data

# Check volume mounts
docker inspect ltm-platform | grep -A 10 Mounts

# Update docker-compose.yml with proper permissions:
version: '3.8'
services:
  ltm-platform:
    volumes:
      - ./config:/app/config:Z
      - ./logs:/app/logs:Z
    user: "${UID:-1000}:${GID:-1000}"
```

---

## 📋 Log Analysis

### Important Log Locations

```bash
# Platform logs
tail -f logs/ltm_platform.log
tail -f logs/api_gateway.log
tail -f logs/integration.log

# Service logs (Docker)
docker-compose logs -f ltm-platform
docker-compose logs -f neo4j
docker-compose logs -f milvus

# System logs
sudo journalctl -u neo4j -f
sudo journalctl -u redis -f
```

### Log Analysis Commands

```bash
# Search for errors in logs
grep -i error logs/*.log
grep -i "failed" logs/*.log

# Monitor real-time errors
tail -f logs/ltm_platform.log | grep -i error

# Count error types
grep -i error logs/ltm_platform.log | sort | uniq -c | sort -nr

# Filter logs by component
grep "ltm_client" logs/ltm_platform.log
grep "knowledge_graph" logs/ltm_platform.log
```

---

## 🔄 Recovery Procedures

### Platform Recovery

```bash
# Full platform restart
./scripts/restart_platform.sh

# Or step by step:
docker-compose down
docker-compose up -d
# Wait for services to start
python unified_network_intelligence.py --health-check
```

### Database Recovery

```bash
# Neo4j recovery
sudo systemctl stop neo4j
sudo neo4j-admin check-consistency
sudo systemctl start neo4j

# Milvus recovery
docker restart milvus-standalone
# Check if collections exist
python -c "
from pymilvus import connections, utility
connections.connect('default', host='localhost', port='19530')
print('Collections:', utility.list_collections())
"

# PostgreSQL recovery
sudo systemctl restart postgresql
sudo -u postgres pg_resetwal /var/lib/postgresql/data  # If corrupted
```

### Data Backup and Restore

```bash
# Create backup
python scripts/backup_platform_data.py --output backup_$(date +%Y%m%d).tar.gz

# Restore from backup
python scripts/restore_platform_data.py --input backup_20240101.tar.gz

# Manual database backups
# Neo4j
sudo neo4j-admin dump --database=neo4j --to=/backup/neo4j_backup.dump

# PostgreSQL  
pg_dump -h localhost -U ltm_user ltm_audit > /backup/postgres_backup.sql
```

---

## 🆘 Emergency Procedures

### Complete System Reset

**⚠️ Warning: This will delete all data**

```bash
# Stop all services
docker-compose down --volumes

# Remove all data
sudo rm -rf data/ logs/* backups/neo4j_data milvus_data redis_data

# Recreate from scratch
docker-compose up -d
python unified_network_intelligence.py --initialize
```

### Safe Mode Startup

```bash
# Start in safe mode (minimal components)
python unified_network_intelligence.py --safe-mode --components ltm

# Or with specific components only
python unified_network_intelligence.py --components ltm,api
```

---

## 📞 Getting Help

### Before Contacting Support

1. **Run health check**: `python unified_network_intelligence.py --health-check`
2. **Collect logs**: `tar -czf support_logs.tar.gz logs/`
3. **Note error messages**: Copy exact error messages
4. **Document steps**: What were you trying to do when the error occurred?

### Debug Information Script

```bash
#!/bin/bash
# Generate comprehensive debug information
echo "=== LTM Platform Debug Information ===" > debug_info.txt
echo "Date: $(date)" >> debug_info.txt
echo "Platform Version: $(cat VERSION)" >> debug_info.txt
echo "" >> debug_info.txt

echo "=== System Information ===" >> debug_info.txt
uname -a >> debug_info.txt
docker --version >> debug_info.txt
python --version >> debug_info.txt
echo "" >> debug_info.txt

echo "=== Service Status ===" >> debug_info.txt
docker-compose ps >> debug_info.txt
systemctl status neo4j redis postgresql --no-pager >> debug_info.txt
echo "" >> debug_info.txt

echo "=== Network Status ===" >> debug_info.txt
netstat -tulpn | grep -E "(8000|8002|7687|19530|6379)" >> debug_info.txt
echo "" >> debug_info.txt

echo "=== Recent Errors ===" >> debug_info.txt
tail -50 logs/ltm_platform.log | grep -i error >> debug_info.txt

echo "Debug information saved to debug_info.txt"
```

### Common Support Requests

1. **Installation Issues**: Provide OS version, Docker version, error messages
2. **Performance Issues**: Include resource usage (`htop`, `docker stats`)
3. **Integration Issues**: Provide repository paths, integration config
4. **Database Issues**: Include database logs, connection test results

---

**Remember**: Most issues can be resolved by checking logs, verifying configurations, and ensuring all services are running. When in doubt, try restarting the affected components first!