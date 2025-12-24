# FortiOS Monitor API System.json Coverage Analysis

## Overview

The file `FortiOS 7.6 FortiOS 7.6.3 Monitor API system.json` contains **156 system-level endpoints**. This document analyzes which endpoints are currently used in the codebase and which are available but unused.

## Currently Used Endpoints

### ✅ Implemented in Codebase

| Endpoint | Service File | Status |
|----------|-------------|--------|
| `monitor/system/dhcp` | `fortiswitch_service.py` | ✅ Used |
| `monitor/system/arp` | `fortiswitch_service.py`, `scraped_topology_service.py` | ✅ Used |
| `monitor/system/fortiguard/security-fabric` | `fortigate_monitor_service.py`, `fortiswitch_service.py` | ✅ **Just Added** |

### ⚠️ Referenced but May Need Updates

| Endpoint | Service File | Issue |
|----------|-------------|-------|
| `monitor/system/status` | `fortigate-auth.js` | Referenced in JS file |
| `monitor/system/interface` | `fortigate_service.no_ssl.py` | Old/backup file |

## Available but Unused System Endpoints

### 🔍 Security Fabric Related

| Endpoint | Purpose | Priority |
|----------|---------|----------|
| `/system/csf` | Security Fabric information | **HIGH** - Alternative to fortiguard/security-fabric |
| `/system/csf/pending-authorizations` | Pending Security Fabric authorizations | **HIGH** - Security management |
| `/system/csf/register-appliance` | Register appliance to Security Fabric | **MEDIUM** - Management operation |

**Note**: The codebase uses `monitor/system/fortiguard/security-fabric` but the API docs show `/system/csf` endpoints. These may be aliases or different versions.

### 📊 System Status & Monitoring

| Endpoint | Purpose | Priority |
|----------|---------|----------|
| `/system/status` | System status information | **HIGH** - Health monitoring |
| `/system/available-interfaces` | Available interfaces | **MEDIUM** - Network discovery |
| `/system/available-interfaces/meta` | Interface metadata | **MEDIUM** - Enhanced interface info |
| `/system/interface` | Interface status | **MEDIUM** - Interface monitoring |
| `/system/performance/status` | Performance metrics | **LOW** - Performance monitoring |
| `/system/central-management/status` | Central management status | **LOW** - Management status |

### 🔌 Interface Management

| Endpoint | Purpose | Priority |
|----------|---------|----------|
| `/system/interface/dhcp-status` | DHCP status per interface | **MEDIUM** - Network configuration |
| `/system/interface/transceivers` | Transceiver information | **MEDIUM** - Hardware inventory |
| `/system/interface/poe` | PoE status | **MEDIUM** - Power management |
| `/system/interface/kernel-interfaces` | Kernel interface info | **LOW** - Low-level interface data |

### 🌐 Network Services

| Endpoint | Purpose | Priority |
|----------|---------|----------|
| `/system/dhcp6` | IPv6 DHCP information | **MEDIUM** - IPv6 support |
| `/system/dhcp/revoke` | Revoke DHCP lease | **LOW** - Management operation |
| `/system/ntp/status` | NTP status | **LOW** - Time synchronization |
| `/system/ipam/status` | IPAM status | **LOW** - IP address management |

### 🔐 Security & Compliance

| Endpoint | Purpose | Priority |
|----------|---------|----------|
| `/system/security-rating/status` | Security rating status | **MEDIUM** - Security assessment |
| `/system/botnet` | Botnet information | **LOW** - Threat intelligence |
| `/system/botnet-domains` | Botnet domains | **LOW** - Threat intelligence |
| `/system/sandbox/status` | Sandbox status | **LOW** - Security features |

### 📡 FortiGuard Services

| Endpoint | Purpose | Priority |
|----------|---------|----------|
| `/system/fortiguard/server-info` | FortiGuard server info | **LOW** - Service status |
| `/system/fortiguard/test-availability` | Test FortiGuard availability | **LOW** - Connectivity test |
| `/system/fortiguard/update` | FortiGuard update | **LOW** - Management operation |
| `/system/fortiguard/manual-update` | Manual FortiGuard update | **LOW** - Management operation |

### 🔧 Configuration & Management

| Endpoint | Purpose | Priority |
|----------|---------|----------|
| `/system/config/backup` | Backup configuration | **LOW** - Management operation |
| `/system/config/restore` | Restore configuration | **LOW** - Management operation |
| `/system/config-sync/status` | Config sync status | **LOW** - HA/cluster status |
| `/system/cluster/state` | Cluster state | **LOW** - HA/cluster status |

## Coverage Summary

### Currently Used: 3 endpoints
- ✅ `monitor/system/dhcp`
- ✅ `monitor/system/arp`
- ✅ `monitor/system/fortiguard/security-fabric`

### Available: 156 endpoints
- **High Priority**: ~5 endpoints (Security Fabric, System Status, Interfaces)
- **Medium Priority**: ~15 endpoints (Interface management, Network services)
- **Low Priority**: ~136 endpoints (Management operations, Advanced features)

## Recommendations

### Immediate Actions

1. **Verify Security Fabric Endpoint**
   - Code uses: `monitor/system/fortiguard/security-fabric`
   - API docs show: `/system/csf`
   - **Action**: Test both endpoints to determine which is correct/available

2. **Add System Status Endpoint**
   ```python
   def get_system_status():
       """Get FortiGate system status"""
       return fgt_api("monitor/system/status")
   ```

3. **Add Available Interfaces Endpoint**
   ```python
   def get_available_interfaces():
       """Get available interfaces with metadata"""
       return fgt_api("monitor/system/available-interfaces")
   ```

### Medium Priority

4. **Add Interface Status Endpoint**
   - Endpoint: `monitor/system/interface`
   - Use case: Real-time interface monitoring

5. **Add Security Rating Status**
   - Endpoint: `monitor/system/security-rating/status`
   - Use case: Security compliance dashboard

## Integration Points

These system endpoints can be integrated into:

1. **`fortigate_monitor_service.py`**
   - Add system status monitoring
   - Add interface status tracking
   - Add Security Fabric via `/system/csf` if different from current

2. **`fortigate_service.py`**
   - Add interface management functions
   - Add system health checks

3. **Dashboard Endpoints**
   - `/api/system/status` - System health endpoint
   - `/api/system/interfaces` - Interface status endpoint
   - `/api/system/security-rating` - Security compliance endpoint

## Conclusion

**Answer**: The `FortiOS 7.6 FortiOS 7.6.3 Monitor API system.json` file contains **156 endpoints**, but the codebase currently uses only **3 endpoints** from this file:

- ✅ `monitor/system/dhcp` - DHCP leases
- ✅ `monitor/system/arp` - ARP table
- ✅ `monitor/system/fortiguard/security-fabric` - Security Fabric (just added)

**Coverage**: **~2% of available system endpoints are currently used**.

**Opportunity**: Many high-value endpoints like system status, interface monitoring, and Security Fabric alternatives (`/system/csf`) are available but not implemented.
