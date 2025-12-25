# FortiGate API Endpoints Reference

## Base Configuration

**Base URL**: `https://<FORTIGATE_IP>/api/v2`
**Authentication**: Session-based (preferred) or API token via `access_token` query parameter

## Monitor API Endpoints (Real-time Data)

### Switch Controller Endpoints

#### 1. Managed Switch Status
- **Endpoint**: `monitor/switch-controller/managed-switch/status`
- **Method**: GET
- **Purpose**: Retrieve statistics for configured FortiSwitches
- **Returns**: Array of FortiSwitch status objects with:
  - `serial` - FortiSwitch serial number
  - `switch-id` - FortiSwitch ID
  - `fgt_peer_intf_name` - FortiLink interface name
  - `state` - Authorization state (Discovered, DeAuthorized, Authorized)
  - `status` - Connection status
  - `ports` - Array of port details
  - `os_version` - Firmware version
  - `max_poe_budget` - PoE budget
  - `igmp_snooping_supported` - IGMP snooping support
  - `dhcp_snooping_supported` - DHCP snooping support

#### 2. Detected Devices
- **Endpoint**: `monitor/switch-controller/detected-device`
- **Method**: GET
- **Purpose**: Real-time device detection on FortiSwitch ports
- **Returns**: Array of detected devices with:
  - `mac` - MAC address
  - `switch_id` - FortiSwitch ID
  - `port_name` - Port name
  - `port_id` - Port ID
  - `vlan_id` - VLAN ID
  - `last_seen` - Seconds since last seen
  - `vdom` - VDOM name

#### 3. Port Statistics
- **Endpoint**: `monitor/switch-controller/managed-switch/port-stats`
- **Method**: GET
- **Query Parameters**: 
  - `mkey` (optional) - Switch ID to filter by specific switch
- **Purpose**: Get port traffic statistics
- **Returns**: Port statistics including:
  - `tx-bytes` - Transmit bytes
  - `tx-packets` - Transmit packets
  - `rx-bytes` - Receive bytes
  - `rx-packets` - Receive packets
  - `tx-errors` - Transmit errors
  - `rx-errors` - Receive errors
  - `rx-drops` - Receive drops

#### 4. Managed Switch Health
- **Endpoint**: `monitor/switch-controller/managed-switch/health`
- **Method**: GET
- **Query Parameters**:
  - `mkey` (required) - Switch serial number
- **Purpose**: Get health status for a specific managed switch
- **Returns**: Health status information

#### 5. ISL Lockdown Status
- **Endpoint**: `monitor/switch-controller/isl-lockdown/status`
- **Method**: GET
- **Query Parameters**:
  - `fortilink` (required) - FortiLink interface name
- **Purpose**: Get ISL lockdown status

#### 6. ISL Lockdown Update
- **Endpoint**: `monitor/switch-controller/isl-lockdown/update`
- **Method**: POST
- **Body Parameters**:
  - `fortilink` (required) - FortiLink interface name
  - `status` (required) - Enable/disable lockdown (enable|disable)
- **Purpose**: Enable/disable ISL lockdown

## CMDB API Endpoints (Configuration Data)

### Switch Controller Configuration

#### 1. Managed Switches
- **Endpoint**: `cmdb/switch-controller/managed-switch`
- **Method**: GET
- **Purpose**: Get managed FortiSwitch configuration
- **Returns**: Array of switch configuration objects with:
  - `sn` - Serial number
  - `switch-id` - Switch ID
  - `name` - Switch name
  - `ports` - Port configuration array
  - `fsw-wan1-admin` - WAN1 admin status
  - `fsw-wan1-peer` - WAN1 peer information
  - `override-snmp-sysinfo` - SNMP override settings

#### 2. Switch Controller System
- **Endpoint**: `cmdb/switch-controller/system`
- **Method**: GET
- **Purpose**: Get switch controller system settings

#### 3. Switch Controller Global
- **Endpoint**: `cmdb/switch-controller/global`
- **Method**: GET
- **Purpose**: Get global switch controller settings

## System API Endpoints

#### 1. System Status
- **Endpoint**: `monitor/system/status`
- **Method**: GET
- **Purpose**: Get system status information

#### 2. System Interface
- **Endpoint**: `monitor/system/interface`
- **Method**: GET
- **Purpose**: Get interface status information

## Current Implementation Usage

### Services Using These Endpoints

1. **FortiSwitchAPIService** (`app/services/fortiswitch_api_service.py`)
   - Uses: `cmdb/switch-controller/managed-switch`
   - Purpose: Get switch configuration and port information

2. **FortiGateMonitorService** (`app/services/fortigate_monitor_service.py`)
   - Uses: `monitor/switch-controller/detected-device`
   - Uses: `monitor/switch-controller/managed-switch/port-stats`
   - Purpose: Real-time device discovery and port statistics

3. **HybridTopologyService** (`app/services/hybrid_topology_service.py`)
   - Combines data from multiple sources:
     - Monitor API for real-time devices
     - CMDB API for switch configuration
     - SNMP for additional device data

## API Call Pattern

All endpoints are called through the `fgt_api()` helper function:

**IMPORTANT**: The `fgt_api()` function automatically prepends `/api/v2/` to the endpoint. 
**DO NOT** include `/api/v2/` in the endpoint string - only provide the path after `/api/v2/`.

```python
from app.services.fortigate_service import fgt_api

# ✅ CORRECT - Just the endpoint path
data = fgt_api("cmdb/switch-controller/managed-switch")
data = fgt_api("monitor/switch-controller/detected-device")
data = fgt_api("monitor/switch-controller/managed-switch/port-stats?mkey=SERIAL_NUMBER")

# ❌ INCORRECT - Don't include /api/v2/ prefix
# data = fgt_api("/api/v2/monitor/switch-controller/detected-device")  # WRONG!
```

The function internally constructs the full URL as:
```
https://<FORTIGATE_IP>/api/v2/{endpoint}
```

## Response Format

All API responses follow this structure:

```json
{
  "http_method": "GET",
  "revision": "1234567890",
  "results": [...],
  "vdom": "root",
  "path": "switch-controller",
  "name": "managed-switch",
  "status": "success",
  "http_status": 200,
  "serial": "FGVM000000000000",
  "version": "v7.6.3",
  "build": 1234
}
```

## Error Handling

API errors are returned in this format:

```json
{
  "error": {
    "code": -651,
    "message": "Invalid API endpoint",
    "status": "error"
  }
}
```

## Notes

- All Monitor API endpoints return real-time/current state data
- All CMDB API endpoints return configuration data
- Use Monitor API for topology visualization (real-time device detection)
- Use CMDB API for switch configuration and management
- Session-based authentication is preferred over token-based for better reliability
