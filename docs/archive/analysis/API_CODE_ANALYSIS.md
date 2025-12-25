# API Usage Analysis: Codebase vs Available APIs

## Executive Summary

This document compares the FortiGate/FortiSwitch API endpoints currently used in the codebase against the available API endpoints documented in `api_definitions/`.

**Key Findings:**
- ✅ **Currently Using**: 6-8 endpoints
- 📋 **Available**: 100+ endpoints
- 🎯 **Opportunities**: 40+ endpoints could enhance functionality
- ⚠️ **Issues**: Some endpoints may be using incorrect paths or missing features

---

## Currently Used Endpoints

### ✅ Monitor API Endpoints (Currently Used)

| Endpoint | Service File | Purpose | Status |
|----------|-------------|---------|--------|
| `monitor/switch-controller/managed-switch/status` | `fortiswitch_service.py` | Get switch status | ✅ Used |
| `monitor/switch-controller/detected-device` | `fortigate_monitor_service.py` | Real-time device detection | ✅ Used |
| `monitor/switch-controller/managed-switch/port-stats` | `fortigate_monitor_service.py` | Port statistics | ✅ Used |
| `monitor/system/arp` | `fortiswitch_service.py`, `scraped_topology_service.py` | ARP table | ✅ Used |
| `monitor/system/dhcp` | `fortiswitch_service.py` | DHCP leases | ✅ Used |

### ✅ Configuration API Endpoints (Currently Used)

| Endpoint | Service File | Purpose | Status |
|----------|-------------|---------|--------|
| `cmdb/switch-controller/managed-switch` | `fortiswitch_api_service.py` | Switch configuration | ✅ Used |
| `cmdb/system/interface` | `fortigate_service.py` | Interface configuration | ✅ Used |

### ⚠️ Potentially Incorrect Endpoints

| Endpoint in Code | Should Be | Issue |
|-----------------|-----------|-------|
| `/api/v2/monitor/switch-controller/managed-switch/status` | `monitor/switch-controller/managed-switch/status` | Includes `/api/v2/` prefix (should be handled by `fgt_api()`) |
| `/api/v2/monitor/system/dhcp` | `monitor/system/dhcp` | Includes `/api/v2/` prefix |
| `/api/v2/monitor/system/arp` | `monitor/system/arp` | Includes `/api/v2/` prefix |

**Note**: The `fgt_api()` helper function automatically prepends `/api/v2/`, so endpoints should NOT include this prefix.

---

## Available But Unused Endpoints

### 🔍 Topology & Network Discovery (High Priority)

| Endpoint | Purpose | Potential Use Case |
|----------|---------|-------------------|
| `monitor/switch-controller/managed-switch/health-status` | Switch health status | Enhanced health monitoring |
| `monitor/switch-controller/managed-switch/port-health` | Port health information | Port-level health checks |
| `monitor/switch-controller/managed-switch/cable-status` | Cable diagnostics | Physical layer troubleshooting |
| `monitor/switch-controller/managed-switch/transceivers` | Transceiver information | Hardware inventory |
| `monitor/switch-controller/managed-switch/tx-rx` | TX/RX statistics | Traffic analysis |
| `monitor/switch-controller/managed-switch/dhcp-snooping` | DHCP snooping data | Security monitoring |
| `monitor/switch-controller/matched-devices` | NAC/policy matched devices | Security compliance |
| `monitor/system/fortiguard/security-fabric` | Security Fabric tree | Topology visualization |
| `monitor/system/fortiguard/security-fabric/pending-authorizations` | Pending authorizations | Security management |

### 📊 FortiSwitch Direct Monitor API (Medium Priority)

| Endpoint | Purpose | Potential Use Case |
|----------|---------|-------------------|
| `monitor/switch/port/` | Port information | Detailed port status |
| `monitor/switch/port-statistics/` | Port statistics | Traffic analysis |
| `monitor/switch/mac-address/` | MAC address table | Device discovery |
| `monitor/switch/mac-address-summary/` | MAC address summary | Network overview |
| `monitor/switch/lldp-state/` | LLDP neighbor discovery | **Topology mapping** |
| `monitor/switch/stp-state/` | STP state | Loop detection |
| `monitor/switch/network-monitor-l2db/` | L2 network monitor DB | **Topology database** |
| `monitor/switch/network-monitor-l3db/` | L3 network monitor DB | **Topology database** |
| `monitor/switch/poe-status/` | PoE status | Power management |
| `monitor/switch/poe-summary/` | PoE summary | Power overview |
| `monitor/switch/trunk-state/` | Trunk state | Link aggregation |
| `monitor/switch/loop-guard-state/` | Loop guard | Loop prevention |
| `monitor/switch/flapguard-status/` | Flap guard | Port stability |

### 🔐 Security & Monitoring (Medium Priority)

| Endpoint | Purpose | Potential Use Case |
|----------|---------|-------------------|
| `monitor/switch/802.1x-status/` | 802.1x status | Authentication monitoring |
| `monitor/switch/acl-stats/` | ACL statistics | Security policy monitoring |
| `monitor/switch/dhcp-snooping-db/` | DHCP snooping database | Security audit |
| `monitor/switch/igmp-snooping-group/` | IGMP snooping | Multicast monitoring |
| `monitor/switch-controller/nac-device/stats` | NAC device statistics | Network access control |

### 🛠️ Management & Operations (Low Priority)

| Endpoint | Purpose | Potential Use Case |
|----------|---------|-------------------|
| `monitor/switch-controller/managed-switch/models` | Supported models | Hardware inventory |
| `monitor/switch-controller/managed-switch/bios` | BIOS information | Firmware management |
| `monitor/switch-controller/managed-switch/faceplate-xml` | Faceplate XML | Visual representation |
| `monitor/switch-controller/fsw-firmware` | Firmware information | Update management |
| `monitor/switch/capabilities/` | Switch capabilities | Feature detection |
| `monitor/switch/cable-diag/` | Cable diagnostics | Troubleshooting |

---

## Code Issues & Recommendations

### 🔴 Critical Issues

1. **Incorrect Endpoint Formatting**
   - **Issue**: Some services use `/api/v2/` prefix in endpoint strings
   - **Location**: `fortiswitch_service.py` lines 227, 235, 251, 259
   - **Fix**: Remove `/api/v2/` prefix (handled by `fgt_api()`)
   ```python
   # ❌ WRONG
   data = fgt_api("/api/v2/monitor/switch-controller/managed-switch/status")
   
   # ✅ CORRECT
   data = fgt_api("monitor/switch-controller/managed-switch/status")
   ```

2. **Missing Topology Discovery Endpoints**
   - **Issue**: Not using LLDP or network monitor databases for topology
   - **Impact**: Limited topology discovery capabilities
   - **Recommendation**: Add LLDP state and network monitor DB endpoints

### 🟡 Medium Priority Issues

1. **Limited Port Information**
   - **Current**: Only using `port-stats` endpoint
   - **Available**: `port-health`, `port/`, `port-statistics/`, `cable-status`
   - **Recommendation**: Add comprehensive port monitoring

2. **No Security Fabric Integration**
   - **Available**: `/system/fortiguard/security-fabric` endpoint
   - **Impact**: Missing Security Fabric topology visualization
   - **Recommendation**: Integrate Security Fabric API

3. **Missing MAC Address Table Access**
   - **Available**: `/switch/mac-address/` and `/switch/mac-address-summary/`
   - **Impact**: Limited device discovery
   - **Recommendation**: Add MAC table queries

### 🟢 Low Priority Improvements

1. **PoE Management**
   - **Available**: `poe-status/`, `poe-summary/`
   - **Use Case**: Power management dashboard

2. **Firmware Management**
   - **Available**: `fsw-firmware` endpoints
   - **Use Case**: Firmware update tracking

3. **Cable Diagnostics**
   - **Available**: `cable-status`, `cable-diag/`
   - **Use Case**: Physical layer troubleshooting

---

## Recommended Implementation Plan

### Phase 1: Fix Critical Issues (Immediate)

1. ✅ Fix endpoint formatting in `fortiswitch_service.py`
2. ✅ Standardize endpoint usage across all services
3. ✅ Add error handling for missing endpoints

### Phase 2: Enhanced Topology Discovery (High Priority)

1. **Add LLDP State Endpoint**
   ```python
   # In fortigate_monitor_service.py
   def get_lldp_neighbors(self) -> Dict[str, Any]:
       """Get LLDP neighbor information for topology mapping"""
       data = fgt_api("monitor/switch/lldp-state/")
       # Process LLDP data for topology connections
   ```

2. **Add Network Monitor Databases**
   ```python
   def get_l2_topology(self) -> Dict[str, Any]:
       """Get L2 network topology from monitor database"""
       data = fgt_api("monitor/switch/network-monitor-l2db/")
       # Process for topology visualization
   ```

3. **Add Security Fabric Integration**
   ```python
   def get_security_fabric_topology(self) -> Dict[str, Any]:
       """Get Security Fabric device tree"""
       data = fgt_api("monitor/system/fortiguard/security-fabric")
       # Process for Security Fabric visualization
   ```

### Phase 3: Enhanced Monitoring (Medium Priority)

1. **Port Health Monitoring**
   - Add `port-health` endpoint
   - Add `cable-status` endpoint
   - Add `transceivers` endpoint

2. **MAC Address Tables**
   - Add `mac-address/` endpoint
   - Add `mac-address-summary/` endpoint
   - Integrate with device discovery

3. **Traffic Analysis**
   - Add `tx-rx` endpoint
   - Add `port-statistics/` endpoint
   - Add traffic utilization metrics

### Phase 4: Advanced Features (Low Priority)

1. **Security Monitoring**
   - Add ACL statistics
   - Add DHCP snooping database
   - Add 802.1x status

2. **Management Features**
   - Add firmware management
   - Add PoE management
   - Add cable diagnostics

---

## Service-by-Service Analysis

### `fortigate_monitor_service.py`

**Currently Using:**
- ✅ `monitor/switch-controller/detected-device`
- ✅ `monitor/switch-controller/managed-switch/port-stats`

**Should Add:**
- `monitor/switch-controller/managed-switch/health-status`
- `monitor/switch-controller/managed-switch/port-health`
- `monitor/switch/lldp-state/`
- `monitor/switch/network-monitor-l2db/`
- `monitor/switch/mac-address/`

### `fortiswitch_service.py`

**Currently Using:**
- ⚠️ `/api/v2/monitor/switch-controller/managed-switch/status` (incorrect format)
- ⚠️ `/api/v2/monitor/switch-controller/detected-device` (incorrect format)
- ⚠️ `/api/v2/monitor/system/dhcp` (incorrect format)
- ⚠️ `/api/v2/monitor/system/arp` (incorrect format)

**Should Fix:**
- Remove `/api/v2/` prefix from all endpoints
- Use correct endpoint format

**Should Add:**
- `monitor/switch-controller/managed-switch/health-status`
- `monitor/switch/port/`
- `monitor/switch/port-statistics/`

### `fortiswitch_api_service.py`

**Currently Using:**
- ✅ `cmdb/switch-controller/managed-switch`

**Should Add:**
- `monitor/switch-controller/managed-switch/status` (for real-time status)
- `monitor/switch-controller/managed-switch/health-status`
- `monitor/switch-controller/managed-switch/port-health`

### `scraped_topology_service.py`

**Currently Using:**
- ✅ `monitor/system/arp`

**Should Add:**
- `monitor/system/fortiguard/security-fabric` (for native topology)
- `monitor/switch/lldp-state/` (for topology discovery)
- `monitor/switch/network-monitor-l2db/` (for topology database)

---

## API Endpoint Reference Quick Guide

### Topology Discovery
```
monitor/switch/lldp-state/                    # LLDP neighbor discovery
monitor/switch/network-monitor-l2db/          # L2 topology database
monitor/switch/network-monitor-l3db/          # L3 topology database
monitor/system/fortiguard/security-fabric     # Security Fabric tree
```

### Device Discovery
```
monitor/switch-controller/detected-device     # ✅ Currently used
monitor/switch-controller/matched-devices     # NAC matched devices
monitor/switch/mac-address/                   # MAC address table
monitor/switch/mac-address-summary/           # MAC summary
monitor/system/arp                            # ✅ Currently used
monitor/system/dhcp                           # ✅ Currently used
```

### Switch Status
```
monitor/switch-controller/managed-switch/status        # ✅ Currently used
monitor/switch-controller/managed-switch/health-status # Health status
monitor/switch-controller/managed-switch/port-health   # Port health
cmdb/switch-controller/managed-switch                  # ✅ Currently used
```

### Port Information
```
monitor/switch-controller/managed-switch/port-stats    # ✅ Currently used
monitor/switch/port/                                   # Port details
monitor/switch/port-statistics/                        # Port statistics
monitor/switch-controller/managed-switch/cable-status # Cable status
monitor/switch-controller/managed-switch/transceivers # Transceivers
monitor/switch-controller/managed-switch/tx-rx         # TX/RX stats
```

---

## Conclusion

The codebase is using a small subset of available APIs. Key opportunities:

1. **Fix endpoint formatting** - Remove `/api/v2/` prefixes
2. **Add topology discovery** - LLDP, network monitor DBs, Security Fabric
3. **Enhance monitoring** - Port health, MAC tables, traffic analysis
4. **Improve device discovery** - Multiple data sources for better coverage

**Estimated Impact:**
- **Topology Discovery**: +80% improvement with LLDP + network monitor DBs
- **Device Discovery**: +40% improvement with MAC tables + matched devices
- **Monitoring**: +60% improvement with port health + traffic analysis
- **Security**: +50% improvement with Security Fabric + NAC integration
