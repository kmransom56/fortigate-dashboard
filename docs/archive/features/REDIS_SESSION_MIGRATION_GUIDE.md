# Redis Session Migration Guide

This guide documents the migration from API key authentication to Redis-based session authentication for the FortiGate Dashboard.

## Overview

The FortiGate Dashboard has been upgraded to use Redis-based session management for improved scalability, persistence, and performance. This migration replaces the previous local session storage and problematic API key authentication.

## What Changed

### Before (API Key Authentication)
- ❌ API key authentication was unreliable
- ❌ Local session storage (lost on container restart)
- ❌ No distributed session management
- ❌ Limited session management capabilities

### After (Redis Session Authentication)
- ✅ Reliable session-based authentication with FortiGate
- ✅ Persistent session storage in Redis
- ✅ Distributed session management across containers
- ✅ Comprehensive session management and monitoring
- ✅ Automatic session cleanup and expiration handling

## New Components

### 1. Redis Session Manager (`app/services/redis_session_manager.py`)
- **Purpose**: Core Redis session storage and management
- **Features**:
  - Session storage with TTL (Time-to-Live)
  - Automatic expiration handling
  - Session cleanup utilities
  - Health monitoring and statistics
  - Concurrent session support

### 2. FortiGate Redis Session Manager (`app/services/fortigate_redis_session.py`)
- **Purpose**: FortiGate-specific authentication with Redis backend
- **Features**:
  - FortiGate login/logout management
  - Session key extraction and storage
  - API request handling with session authentication
  - Automatic re-authentication on session expiry

### 3. Docker Compose Updates
- **Redis Service**: Added Redis 7 Alpine with persistence
- **Health Checks**: Redis health checks for service dependencies
- **Persistent Storage**: Redis data volume for session persistence

### 4. New API Endpoints
- `GET /api/session/health` - Session management health status
- `GET /api/session/info` - Current session information
- `POST /api/session/cleanup` - Manual session cleanup
- `DELETE /api/session/current` - Logout current session
- `GET /api/session/test` - Test session authentication

## Environment Variables

### New Variables
```bash
# Redis Configuration
REDIS_HOST=redis                    # Redis hostname (default: localhost)
REDIS_PORT=6379                     # Redis port (default: 6379)
REDIS_DB=0                          # Redis database number (default: 0)
REDIS_PASSWORD=                     # Redis password (optional)

# Session Configuration
FORTIGATE_SESSION_TTL=30           # Session TTL in minutes (default: 30)
```

### Updated Variables
```bash
# Authentication Control
FORTIGATE_ALLOW_TOKEN_FALLBACK=false  # Disable API key fallback (recommended)
```

## Migration Process

### Step 1: Pre-Migration Validation
```bash
# Check current system status
python tools/test_fortigate_api.py

# Verify FortiGate credentials
python tools/test_session_auth.py
```

### Step 2: Deploy Redis-based System
```bash
# Stop current containers
docker compose down

# Update to latest code (includes Redis session implementation)
git pull

# Build and start with Redis
docker compose up --build -d

# Verify Redis is running
docker compose ps redis
```

### Step 3: Validate Migration
```bash
# Run comprehensive validation
python tools/validate_migration.py

# Run detailed Redis session tests
python tools/test_redis_session_auth.py
```

### Step 4: Monitor Session Health
```bash
# Check session health via API
curl http://localhost:10000/api/session/health

# View session information
curl http://localhost:10000/api/session/info

# Test authentication
curl http://localhost:10000/api/session/test
```

## Troubleshooting

### Redis Connection Issues
```bash
# Check Redis container logs
docker compose logs redis

# Test Redis connectivity manually
docker compose exec redis redis-cli ping

# Check network connectivity
docker compose exec dashboard ping redis
```

### Authentication Failures
```bash
# Check FortiGate credentials
python tools/validate_migration.py

# View detailed logs
docker compose logs dashboard | grep -i auth

# Test session authentication directly
python tools/test_redis_session_auth.py
```

### Session Management Issues
```bash
# View current sessions
curl http://localhost:10000/api/session/info

# Clean up expired sessions
curl -X POST http://localhost:10000/api/session/cleanup

# Health check
curl http://localhost:10000/api/session/health
```

## Performance Benefits

### Session Persistence
- **Before**: Sessions lost on container restart
- **After**: Sessions persist in Redis across restarts

### Scalability
- **Before**: Single container session storage
- **After**: Distributed session management across multiple containers

### Monitoring
- **Before**: No session visibility
- **After**: Comprehensive session monitoring and statistics

### Reliability
- **Before**: API key authentication failures
- **After**: Robust session-based authentication with automatic recovery

## Configuration Examples

### Development Environment
```yaml
# compose.yml - Development
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  
  dashboard:
    environment:
      - REDIS_HOST=redis
      - FORTIGATE_SESSION_TTL=30
      - FORTIGATE_ALLOW_TOKEN_FALLBACK=false
      - LOG_LEVEL=DEBUG
```

### Production Environment
```yaml
# compose.prod.yml - Production
services:
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    command: >
      redis-server 
      --appendonly yes 
      --maxmemory 512mb 
      --maxmemory-policy allkeys-lru
      --requirepass "${REDIS_PASSWORD}"
  
  dashboard:
    environment:
      - REDIS_HOST=redis
      - REDIS_PASSWORD_FILE=/run/secrets/redis_password
      - FORTIGATE_SESSION_TTL=60
      - FORTIGATE_ALLOW_TOKEN_FALLBACK=false
      - LOG_LEVEL=INFO
```

## Session Lifecycle

### 1. Session Creation
1. User credentials validated against FortiGate
2. Session key extracted from FortiGate response cookies
3. Session data stored in Redis with TTL
4. Session key used for subsequent API calls

### 2. Session Usage
1. API request triggered
2. Valid session retrieved from Redis
3. Session key used for FortiGate authentication
4. Session usage statistics updated

### 3. Session Expiration
1. Session TTL expires in Redis
2. Next API request detects expired session
3. Automatic re-authentication attempted
4. New session created and stored

### 4. Session Cleanup
1. Automatic cleanup runs periodically
2. Manual cleanup via API endpoint
3. Expired sessions removed from Redis
4. Statistics updated

## Monitoring and Alerting

### Key Metrics to Monitor
- Redis connection status
- Active session count
- Session creation/expiration rates
- Authentication success/failure rates
- API response times

### Health Check Endpoints
```bash
# Overall system health
GET /api/session/health

# Session statistics
GET /api/session/info

# Authentication test
GET /api/session/test
```

### Log Analysis
```bash
# Authentication events
docker compose logs dashboard | grep -i "session authentication"

# Redis operations
docker compose logs dashboard | grep -i "redis"

# Session lifecycle
docker compose logs dashboard | grep -i "session"
```

## Security Considerations

### Session Security
- Sessions automatically expire after configured TTL
- Session keys are FortiGate-generated and cryptographically secure
- No sensitive credentials stored in Redis (only session keys)

### Redis Security
- Redis can be password-protected in production
- Redis data encrypted at rest (optional)
- Network isolation via Docker networks

### Authentication Flow
- Credentials only used for initial authentication
- Session-based authentication for all subsequent requests
- Automatic session cleanup prevents accumulation

## Rollback Plan

If issues occur, you can temporarily rollback:

### Emergency Rollback
```bash
# Set environment to enable token fallback
docker compose exec dashboard bash -c 'export FORTIGATE_ALLOW_TOKEN_FALLBACK=true'

# Or restart with token fallback enabled
FORTIGATE_ALLOW_TOKEN_FALLBACK=true docker compose up -d dashboard
```

### Full Rollback (if needed)
1. Revert to previous git commit
2. Use old compose file without Redis
3. Remove Redis-related environment variables

## Support and Troubleshooting

### Common Issues and Solutions

1. **Redis Connection Failed**
   - Check Redis container status: `docker compose ps redis`
   - Verify network connectivity: `docker compose exec dashboard ping redis`

2. **Session Authentication Failed**
   - Verify FortiGate credentials in secrets files
   - Check FortiGate network connectivity
   - Review authentication logs

3. **Sessions Not Persisting**
   - Check Redis data volume mount
   - Verify Redis persistence configuration
   - Review Redis logs for errors

### Getting Help
1. Run comprehensive diagnostics: `python tools/test_redis_session_auth.py`
2. Check API health: `curl http://localhost:10000/api/session/health`
3. Review logs: `docker compose logs dashboard redis`

This migration provides a robust, scalable, and persistent session management system for your FortiGate Dashboard.