# Deployment & Troubleshooting Scripts

This document describes the deployment and troubleshooting utilities available in the `tools/` directory.

## API Troubleshooting Scripts

### api_troubleshoot.py

**Purpose**: Comprehensive FortiGate API authentication and permission diagnostic tool.

**Features**:
- Tests multiple authentication methods (session-based, token-based)
- Validates API token formats (Bearer, Basic, Query Parameter, etc.)
- Checks user permissions and access levels
- Tests various API endpoints for accessibility
- Generates diagnostic reports with recommendations

**Usage**:
```bash
python3 tools/api_troubleshoot.py
```

**Configuration** (edit script):
- `host`: FortiGate IP and port (default: `192.168.0.254`)
- `admin_user`: Admin username
- `api_user`: API user username  
- `password`: User password
- `api_token`: API authentication token

**What it tests**:
1. Basic connectivity to FortiGate
2. Admin user session login
3. API user session login
4. Token formats (Bearer, Basic Auth, Query Parameter, Custom Headers)
5. Session-based API calls
6. Token + username combinations

**Output**:
- Console report with ✅/❌ status indicators
- Recommendations for fixing authentication issues
- Identifies working authentication methods

**Common Issues Resolved**:
- API token not working → Shows which format to use
- Permission denied errors → Identifies missing permissions
- Session vs. token authentication confusion → Tests both methods
- User profile configuration problems → Provides specific recommendations

---

### api_endpoint_discovery.py

**Purpose**: Discovers available FortiGate API endpoints for FortiSwitch management and network monitoring.

**Features**:
- Automatically tests common FortiSwitch endpoint patterns
- Discovers network monitoring endpoints
- Tests endpoint availability and response structure
- Generates JSON report with detailed results
- Identifies working endpoints for switch management

**Usage**:
```bash
python3 tools/api_endpoint_discovery.py
```

**Configuration** (edit script):
- `base_url`: FortiGate base URL (default: `https://192.168.0.254`)
- `token`: API authentication token

**Endpoints Tested**:

**FortiSwitch Endpoints**:
- `monitor/switch-controller/managed-switch`
- `monitor/switch-controller/switch`
- `monitor/switch-controller/fortilink`
- `monitor/switch-controller/status`
- `monitor/switch-controller/health`
- `cmdb/switch-controller/managed-switch`
- And 15+ variations

**Network Endpoints**:
- `monitor/system/interface`
- `monitor/system/status`
- `monitor/router/routing-table`
- `monitor/network/dns`
- `cmdb/system/interface`
- And more

**Output**:
- Console report showing ✅ available / ❌ unavailable endpoints
- `api_endpoint_discovery.json` - Detailed JSON results with:
  - HTTP status codes
  - Response structure analysis
  - Result counts
  - Available data keys

**Use Cases**:
- Finding the correct API endpoints for your FortiGate version
- Understanding what data is available from the API
- Troubleshooting "endpoint not found" errors
- Planning API integration development

---

## Deployment Scripts

### deploy_enhanced_fortiswitch.py

**Purpose**: Deploys the enhanced FortiSwitch service with restaurant device classification capabilities.

**Features**:
- Automatic backup of original service
- Deploys enhanced FortiSwitch service with improved detection
- Integrates restaurant technology device classifier
- Verifies deployment through import testing
- Creates deployment summary documentation

**Usage**:
```bash
python3 tools/deploy_enhanced_fortiswitch.py
```

**What it does**:
1. **Backs up** original `app/services/fortiswitch_service.py` with timestamp
2. **Deploys** `app/services/fortiswitch_service_enhanced.py` as the active service
3. **Verifies** imports and dependencies
4. **Creates** `deployment_summary.md` with complete deployment details

**Enhanced Features Deployed**:
- Improved device detection and correlation
- Better DHCP information mapping
- Enhanced error handling and rate limiting
- Restaurant technology device classification (POS, KDS, kiosks)
- Security and monitoring recommendations
- Comprehensive logging

**Rollback Instructions**:
If issues occur, restore from backup:
```bash
# Find backup file (timestamped)
ls -la app/services/fortiswitch_service.backup.*.py

# Restore backup
cp app/services/fortiswitch_service.backup.YYYYMMDD_HHMMSS.py app/services/fortiswitch_service.py

# Restart service
docker compose restart fortigate-dashboard
```

**Prerequisites**:
- `app/services/fortiswitch_service_enhanced.py` must exist
- `app/utils/restaurant_device_classifier.py` must exist

---

### upgrade_oui_automation.py

**Purpose**: Upgrades the OUI lookup system with Power Automate-style automation features.

**Features**:
- Backs up original `app/utils/oui_lookup.py`
- Deploys enhanced OUI lookup with intelligent automation
- Adds rate limiting (50 requests/min)
- Implements persistent disk caching
- Enables exponential backoff for API limits

**Usage**:
```bash
python3 tools/upgrade_oui_automation.py
```

**What it does**:
1. **Backs up** original `app/utils/oui_lookup.py` to `app/utils/oui_lookup_backup.py`
2. **Copies** `app/utils/oui_lookup_enhanced.py` to `app/utils/oui_lookup.py`
3. **Activates** enhanced features

**Enhanced Features**:
- **Intelligent Rate Limiting**: Respects macvendors.com 50 req/min limit
- **Persistent Caching**: Saves cache to disk (`app/data/oui_cache.json`)
- **Exponential Backoff**: Automatically retries on rate limit with delays
- **Expanded Database**: Enhanced local manufacturer database
- **Performance Monitoring**: Built-in metrics for cache hits/misses
- **Graceful Degradation**: Continues working even when API is unavailable

**Post-Deployment**:
```bash
# Restart Docker container to apply changes
docker compose restart fortigate-dashboard

# Monitor cache performance
cat app/data/oui_cache.json | jq 'keys | length'  # Show cached vendors
```

**Performance Benefits**:
- 10-100x faster lookups for cached vendors
- Reduces external API calls by 90%+
- Eliminates rate limit errors
- Works offline with cached data

---

## Troubleshooting Workflow

### API Connection Issues

1. **Test Basic Connectivity**:
   ```bash
   python3 tools/api_troubleshoot.py
   ```
   Look for "✅ Connection successful" in output.

2. **Discover Available Endpoints**:
   ```bash
   python3 tools/api_endpoint_discovery.py
   cat api_endpoint_discovery.json | jq '.summary'
   ```

3. **Check Authentication**:
   - If session login fails → Verify credentials
   - If token fails → Try different token formats from troubleshoot script
   - If all fail → Check FortiGate API user permissions

### FortiSwitch Detection Issues

1. **Deploy Enhanced Service**:
   ```bash
   python3 tools/deploy_enhanced_fortiswitch.py
   ```

2. **Check Available Endpoints**:
   ```bash
   python3 tools/api_endpoint_discovery.py | grep "FortiSwitch"
   ```

3. **Monitor Logs**:
   ```bash
   docker compose logs -f fortigate-dashboard | grep "fortiswitch"
   ```

### OUI Lookup Rate Limiting

1. **Upgrade to Enhanced OUI Lookup**:
   ```bash
   python3 tools/upgrade_oui_automation.py
   docker compose restart fortigate-dashboard
   ```

2. **Verify Cache is Working**:
   ```bash
   # Check cache file exists
   ls -lh app/data/oui_cache.json
   
   # View cached vendors
   cat app/data/oui_cache.json | jq 'keys'
   ```

---

## Script Maintenance

### Configuration Best Practices

**DO**:
- ✅ Use environment variables for credentials when possible
- ✅ Keep backup files for rollback capability
- ✅ Review deployment summaries before applying changes
- ✅ Test in development environment first
- ✅ Monitor logs after deployment

**DON'T**:
- ❌ Hardcode production credentials in scripts
- ❌ Delete backup files immediately after deployment
- ❌ Deploy directly to production without testing
- ❌ Skip verification steps
- ❌ Ignore error messages in deployment output

### Updating Scripts

All scripts should be treated as infrastructure-as-code:

1. **Version Control**: Commit scripts to git
2. **Documentation**: Update this file when adding new scripts
3. **Testing**: Test script changes in development first
4. **Backups**: Scripts create automatic backups before modifications

---

## Integration with CI/CD

These scripts can be integrated into automated deployment pipelines:

```yaml
# Example GitHub Actions workflow
- name: Deploy Enhanced Services
  run: |
    python3 tools/upgrade_oui_automation.py
    python3 tools/deploy_enhanced_fortiswitch.py

- name: Verify API Connectivity
  run: |
    python3 tools/api_troubleshoot.py
    python3 tools/api_endpoint_discovery.py
```

---

## Related Documentation

- **API Integration**: See `CLAUDE.md` for FortiGate API patterns
- **Asset Catalog**: See `docs/ASSET_CATALOG.md` for available resources
- **Testing Scripts**: See `tools/` directory for additional testing utilities

---

Last Updated: 2025-12-07
