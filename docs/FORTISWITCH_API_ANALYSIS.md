# FortiSwitch API Analysis

## 📋 Overview
Analysis of FortiSwitch 7.6.4 Monitor API endpoints for enhanced device discovery and port monitoring.

## 🔍 Key Findings from FortiSwitch API Documentation

### 🌐 Direct FortiSwitch Monitor Endpoints

The FortiSwitch API documentation reveals several valuable endpoints that could enhance our topology discovery:

#### 1. **Port Status Monitoring**
- **Endpoint**: `/switch/port/`
- **Purpose**: Real-time port state information
- **Data**: Link status (UP/DOWN), speed, duplex, autoneg, medium type
- **Value**: More detailed port status than FortiGate API provides

#### 2. **MAC Address Table** ⭐ **HIGHEST VALUE**
- **Endpoint**: `/switch/mac-address/`
- **Purpose**: Complete MAC address table with port mappings
- **Data**: 
  - MAC address
  - VLAN ID
  - Interface/Port
  - Flags (static/dynamic)
- **Value**: **Direct device-to-port mapping for connected device discovery**

#### 3. **Port Statistics**
- **Endpoint**: `/switch/port-statistics/`
- **Purpose**: Detailed port traffic statistics
- **Data**: TX/RX bytes, packets, errors, drops, collisions
- **Value**: Network utilization and health monitoring

#### 4. **Additional Monitoring Endpoints**
- `/switch/802.1x-status/` - 802.1x authentication status per port
- `/switch/dhcp-snooping-client-db/` - DHCP client database
- `/switch/lldp-state/` - LLDP neighbor discovery
- `/switch/flapguard-status/` - Port flapping detection

## 🔧 Current Implementation Analysis

### ✅ **What We're Using (FortiGate API)**
- `cmdb/switch-controller/managed-switch` - Switch configuration and port settings
- `cmdb/switch-controller/system` - Switch controller system settings
- `cmdb/switch-controller/global` - Global switch controller settings

### 🎯 **What We Could Add (Direct FortiSwitch API)**
- `/switch/mac-address/` - **Real-time MAC-to-port mappings**
- `/switch/port/` - **Real-time port status**
- `/switch/port-statistics/` - **Traffic statistics**

## 💡 Enhancement Opportunities

### 1. **MAC Address Table Integration**
The `/switch/mac-address/` endpoint could provide real-time device discovery:
```json
{
  "mac": "d8:43:ae:9f:41:26",
  "vlan": 1,
  "interface": "port13", 
  "flags": "dynamic"
}
```

This would eliminate the need for static SNMP mapping and provide dynamic device discovery.

### 2. **Real-time Port Status**
The `/switch/port/` endpoint provides live port status:
```json
{
  "name": "port13",
  "link": "UP",
  "speed": 1000,
  "duplex": "FULL",
  "medium": "copper"
}
```

### 3. **Enhanced Statistics**
Port-level traffic statistics for network utilization dashboards.

## 🚧 Implementation Challenges

### **Authentication Method**
- FortiSwitch API uses: `?access_token={token}` (query parameter)
- FortiGate API uses: `Authorization: Bearer {token}` (header)

### **Network Access**
- FortiSwitch management IP: `10.255.1.2` (FortiLink network)
- May require routing through FortiGate or direct management network access

### **API User Permissions**
- Need to verify API user has permissions for FortiSwitch direct access
- May require additional switch controller permissions

## 📋 Recommended Implementation Strategy

### Phase 1: **Enhanced FortiGate Integration** ✅ **(COMPLETED)**
- Use FortiGate API for switch configuration and basic port info
- Enhance with SNMP device inventory
- Hybrid approach for maximum reliability

### Phase 2: **Direct FortiSwitch Integration** (Future Enhancement)
- Add FortiSwitch MAC address table discovery
- Real-time port status monitoring
- Enhanced statistics and utilization tracking

### Phase 3: **Advanced Features** (Future)
- LLDP neighbor discovery
- 802.1x client tracking
- DHCP snooping integration
- Port security monitoring

## 🎯 Current Status

### ✅ **Completed**
- FortiGate API integration with 3 working endpoints
- SNMP-based device inventory with 5 known devices
- Hybrid topology service combining both approaches
- Real-time switch configuration and port data

### 🔄 **Next Steps**
1. Test Redis dependency installation for session management
2. Verify topology endpoint returns enhanced device data
3. Consider adding direct FortiSwitch API integration for MAC table discovery

## 📊 **Value Assessment**

| Feature | FortiGate API | SNMP | Direct FortiSwitch API |
|---------|---------------|------|----------------------|
| Switch Config | ✅ Complete | ❌ None | ✅ Complete |
| Port Status | ✅ Config | ❌ None | ✅ Real-time |
| Device Discovery | ❌ Limited | ✅ Static | ✅ Dynamic MAC Table |
| Statistics | ❌ None | ❌ None | ✅ Detailed |
| Reliability | ✅ High | ✅ High | ⚠️ Network dependent |

## 🏆 **Recommendation**

The current hybrid approach (FortiGate API + SNMP) provides excellent coverage and reliability. Adding direct FortiSwitch MAC table discovery would provide the most value for dynamic device discovery, making it a high-priority future enhancement.