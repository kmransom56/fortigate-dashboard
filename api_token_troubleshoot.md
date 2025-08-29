# FortiGate API Token Troubleshooting Guide

## Current Status ❌
- **Network**: ✅ Connection to FortiGate working (192.168.0.254:8443)
- **SSL/TLS**: ✅ TLS 1.3 handshake successful  
- **API Token**: ❌ Invalid token error (`www-authenticate: error="invalid_token"`)

## API Token Issues Identified

### Error Details
```
HTTP/2 401 
www-authenticate: error="invalid_token"
```

This indicates the API token is either:
1. **Expired** - FortiGate tokens have expiration dates
2. **Invalid format** - Wrong token string
3. **Permissions insufficient** - Token lacks required API access
4. **Scope limited** - Token doesn't have monitor API access

## How to Fix the API Token

### Method 1: Create New API Token via FortiGate GUI

1. **Access FortiGate WebUI**:
   ```
   https://192.168.0.254:8443
   Username: admin
   Password: [your admin password]
   ```

2. **Navigate to API Token Management**:
   ```
   System > Administrators > Create New > REST API Admin
   ```

3. **Create API Token**:
   - **Name**: `dashboard-api-token`
   - **Administrator Profile**: `super_admin` (or create custom profile)
   - **CORS Allow Origin**: `*` (or specific domain)
   - **Trusted Hosts**: Leave empty or add your server IP
   - **Comments**: `FortiGate Dashboard API Access`

4. **Copy the Generated Token**:
   - ⚠️ **IMPORTANT**: Token is only shown once!
   - Save to: `secrets/fortigate_api_token.txt`

### Method 2: Verify Current Token Status

1. **Check Token in FortiGate**:
   ```
   System > Administrators
   Look for existing API tokens and their status
   ```

2. **Check Token Permissions**:
   - Ensure profile has `read` access to:
     - System settings
     - Monitor data
     - FortiSwitch management

### Method 3: CLI Token Creation (if GUI not accessible)

```bash
# Connect to FortiGate CLI via SSH
ssh admin@192.168.0.254

# Create API admin user
config system api-user
    edit "dashboard-api"
        set api-key "your-custom-token-here"
        set accprofile "super_admin"
        set vdom "root"
        set cors-allow-origin "*"
    next
end
```

## Required API Permissions

For the dashboard to work, the API token needs access to:

### System Information
- `GET /api/v2/monitor/system/status`
- `GET /api/v2/cmdb/system/interface`

### FortiSwitch Management  
- `GET /api/v2/monitor/switch-controller/managed-switch`
- `GET /api/v2/monitor/fortilink/health-check`
- `GET /api/v2/monitor/switch-controller/fortilink`

### Network Monitoring
- `GET /api/v2/monitor/system/interface`
- `GET /api/v2/monitor/router/routing-table`

## Testing New Token

After creating a new token, test it:

```bash
# Test system status
curl -k "https://192.168.0.254:8443/api/v2/monitor/system/status?access_token=NEW_TOKEN_HERE"

# Test interface data  
curl -k "https://192.168.0.254:8443/api/v2/cmdb/system/interface?access_token=NEW_TOKEN_HERE"
```

## Quick Fix Steps

1. **Create new API token** via FortiGate GUI
2. **Update token file**:
   ```bash
   echo "NEW_TOKEN_HERE" > secrets/fortigate_api_token.txt
   ```
3. **Restart dashboard**:
   ```bash
   docker compose restart dashboard
   ```
4. **Test topology**:
   ```bash
   curl http://localhost:10000/api/topology_data
   ```

## Alternative: Session Authentication

If API tokens continue to fail, we can switch back to session authentication:

```bash
# Disable token fallback to force session auth
docker compose exec dashboard env FORTIGATE_ALLOW_TOKEN_FALLBACK=false
```

## Next Steps

1. ✅ **Create valid API token** using FortiGate GUI
2. ✅ **Update secrets/fortigate_api_token.txt**
3. ✅ **Restart dashboard container**  
4. ✅ **Verify topology shows real network data**

Once the API token is fixed, you should see:
- **Multiple devices** (FortiGate + FortiSwitch + connected endpoints)
- **Network connections** showing topology relationships
- **Device details** with real manufacturer information
- **Port mappings** showing which devices connect to which switch ports