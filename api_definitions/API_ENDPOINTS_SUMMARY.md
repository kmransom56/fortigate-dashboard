# FortiGate/FortiSwitch API Endpoints Summary

## Overview
This document summarizes available API endpoints from FortiOS 7.6.3 and FortiSwitch 7.6.1 Monitor/Configuration APIs.

## Base Paths
- **FortiOS Monitor API**: `/api/v2/monitor`
- **FortiOS Configuration API**: `/api/v2/cmdb`
- **FortiSwitch Monitor API**: `/api/v2/monitor` (FortiSwitch-specific endpoints)

---

## Switch Controller Endpoints (FortiOS Monitor API)

### Managed Switch Operations
- `GET /switch-controller/managed-switch/status` - Retrieve statistics for configured FortiSwitches
- `GET /switch-controller/managed-switch/health-status` - Get health status
- `GET /switch-controller/managed-switch/port-health` - Get port health information
- `GET /switch-controller/managed-switch/port-stats` - Get port statistics
- `POST /switch-controller/managed-switch/port-stats-reset` - Reset port statistics
- `GET /switch-controller/managed-switch/cable-status` - Get cable status
- `GET /switch-controller/managed-switch/transceivers` - Get transceiver information
- `GET /switch-controller/managed-switch/tx-rx` - Get TX/RX statistics
- `GET /switch-controller/managed-switch/dhcp-snooping` - Get DHCP snooping information
- `GET /switch-controller/managed-switch/models` - Get supported models
- `GET /switch-controller/managed-switch/bios` - Get BIOS information
- `GET /switch-controller/managed-switch/faceplate-xml` - Get faceplate XML
- `POST /switch-controller/managed-switch/bounce-port` - Bounce a port
- `POST /switch-controller/managed-switch/poe-reset` - Reset PoE
- `POST /switch-controller/managed-switch/restart` - Restart switch
- `POST /switch-controller/managed-switch/factory-reset` - Factory reset
- `POST /switch-controller/managed-switch/update` - Update switch

### Device Detection
- `GET /switch-controller/detected-device` - Get detected devices
- `GET /switch-controller/matched-devices` - Get matched devices

### Firmware Management
- `GET /switch-controller/fsw-firmware` - Get firmware information
- `POST /switch-controller/fsw-firmware/download` - Download firmware
- `POST /switch-controller/fsw-firmware/push` - Push firmware
- `POST /switch-controller/fsw-firmware/upload` - Upload firmware

### Other Switch Controller Endpoints
- `GET /switch-controller/isl-lockdown/status` - ISL lockdown status
- `POST /switch-controller/isl-lockdown/update` - Update ISL lockdown
- `GET /switch-controller/known-nac-device-criteria-list` - NAC device criteria
- `GET /switch-controller/nac-device/stats` - NAC device statistics
- `GET /switch-controller/mclag-icl/eligible-peer` - MCLAG ICL eligible peer
- `POST /switch-controller/mclag-icl/set-tier1` - Set MCLAG ICL tier 1
- `POST /switch-controller/mclag-icl/set-tier-plus` - Set MCLAG ICL tier plus
- `GET /switch-controller/mclag-icl/tier-plus-candidates` - Get tier plus candidates
- `GET /switch-controller/recommendation/pse-config` - PSE configuration recommendations

---

## FortiSwitch Direct Monitor API Endpoints

### Port Information
- `GET /switch/port/` - Get port information
- `GET /switch/port-speed/` - Get port speed
- `GET /switch/port-statistics/` - Get port statistics

### MAC Address Information
- `GET /switch/mac-address/` - Get MAC address table
- `GET /switch/mac-address-summary/` - Get MAC address summary

### PoE Information
- `GET /switch/poe-status/` - Get PoE status
- `GET /switch/poe-summary/` - Get PoE summary

### Network Monitoring
- `GET /switch/network-monitor-l2db/` - L2 network monitor database
- `GET /switch/network-monitor-l3db/` - L3 network monitor database

### Protocol Status
- `GET /switch/802.1x-status/` - 802.1x status
- `GET /switch/lldp-state/` - LLDP state
- `GET /switch/stp-state/` - STP state
- `GET /switch/trunk-state/` - Trunk state
- `GET /switch/loop-guard-state/` - Loop guard state
- `GET /switch/flapguard-status/` - Flap guard status

### ACL and QoS
- `GET /switch/acl-stats/` - ACL statistics
- `GET /switch/acl-stats-egress/` - ACL egress statistics
- `GET /switch/acl-stats-ingress/` - ACL ingress statistics
- `GET /switch/acl-stats-prelookup/` - ACL pre-lookup statistics
- `GET /switch/acl-usage/` - ACL usage
- `GET /switch/qos-stats/` - QoS statistics

### DHCP Snooping
- `GET /switch/dhcp-snooping-db/` - DHCP snooping database
- `GET /switch/dhcp-snooping-client-db/` - DHCP snooping client database
- `GET /switch/dhcp-snooping-client6-db/` - DHCP snooping IPv6 client database
- `GET /switch/dhcp-snooping-server-db/` - DHCP snooping server database
- `GET /switch/dhcp-snooping-server6-db/` - DHCP snooping IPv6 server database
- `GET /switch/dhcp-snooping-limit-db-details/` - DHCP snooping limit database details

### IGMP Snooping
- `GET /switch/igmp-snooping-group/` - IGMP snooping group

### MCLAG
- `GET /switch/mclag-list/` - MCLAG list
- `GET /switch/mclag-icl/` - MCLAG ICL

### Modules
- `GET /switch/modules-status/` - Module status
- `GET /switch/modules-summary/` - Module summary
- `GET /switch/modules-detail/` - Module details
- `GET /switch/modules-limits/` - Module limits

### Other
- `GET /switch/cable-diag/` - Cable diagnostics
- `GET /switch/capabilities/` - Switch capabilities
- `GET /switch/faceplate/` - Faceplate information

---

## System Monitor API Endpoints (FortiOS)

### Security Fabric
- `GET /system/fortiguard/security-fabric` - Security Fabric information
- `GET /system/fortiguard/security-fabric/pending-authorizations` - Pending authorizations
- `POST /system/fortiguard/security-fabric/register` - Register appliance to Security Fabric

### Security Rating
- `GET /system/security-rating` - Get security rating
- `GET /system/security-rating/status` - Get security rating status
- `GET /system/security-rating/history` - Get security rating history
- `GET /system/security-rating/supported-reports` - Get supported reports
- `POST /system/security-rating/trigger` - Trigger security rating

### System Information
- `GET /system/available-interfaces` - Get available interfaces
- `GET /system/available-interfaces/meta` - Get interface metadata
- `GET /system/available-certificates` - Get available certificates
- `GET /system/acquired-dns` - Get acquired DNS
- `GET /system/botnet` - Get botnet information
- `GET /system/botnet-domains` - Get botnet domains
- `GET /system/botnet-domains/hits` - Get botnet domain hits
- `GET /system/botnet-domains/stat` - Get botnet domain statistics
- `GET /system/botnet/stat` - Get botnet statistics

### 3G Modem
- `GET /system/3g-modem` - Get 3G modem status

### Certificate Management
- `GET /system/certificate/download` - Download certificate
- `GET /system/certificate/read-info` - Read certificate info
- `GET /system/acme-certificate-status` - ACME certificate status

### Central Management
- `GET /system/central-management/status` - Central management status

### Automation
- `GET /system/automation-action/stats` - Automation action statistics
- `GET /system/automation-stitch/stats` - Automation stitch statistics
- `POST /system/automation-stitch/test` - Test automation stitch
- `POST /system/automation-stitch/webhook` - Automation stitch webhook

### Admin
- `POST /system/admin/change-vdom-mode` - Change VDOM mode
- `GET /system/api-user/generate-key` - Generate API user key

### SDN Connector
- `GET /system/sdn-connector/nsx-security-tags` - NSX security tags

---

## Configuration API Endpoints (FortiOS CMDB)

### System Configuration
- `GET /system/arp-table` - Get ARP table entries
- `GET /system/arp-table/{id}` - Get specific ARP table entry
- `POST /system/arp-table` - Create ARP table entry
- `PUT /system/arp-table/{id}` - Update ARP table entry
- `DELETE /system/arp-table/{id}` - Delete ARP table entry

- `GET /system/proxy-arp` - Get proxy ARP entries
- `GET /system/proxy-arp/{id}` - Get specific proxy ARP entry
- `POST /system/proxy-arp` - Create proxy ARP entry
- `PUT /system/proxy-arp/{id}` - Update proxy ARP entry
- `DELETE /system/proxy-arp/{id}` - Delete proxy ARP entry

---

## Authentication

All API endpoints require authentication via:
- **API Token**: Query parameter `access_token` or header `Authorization: Bearer <token>`
- **Session Cookie**: After logging in via `/logincheck`

---

## Common Query Parameters

### Pagination
- `start` - Starting entry index
- `count` - Maximum number of entries to return
- `skip_to` - Skip to Nth entry

### Filtering
- `filter` - Filter key/value pairs (supports operators: ==, !=, =@, !@, <=, <, >=, >)
- `key` - Filter on property name
- `pattern` - Filter on property value
- `search` - Search value

### Formatting
- `format` - List of property names to include (separated by |)
- `with_meta` - Include meta information
- `with_contents_hash` - Include checksum
- `datasource` - Include datasource information

### VDOM
- `vdom` - Virtual Domain(s) (root, vdom1,vdom2, or * for all)
- `scope` - Scope (global|vdom|both)

---

## Notes

1. **Monitor API** endpoints are read-only and return real-time status/statistics
2. **Configuration API** endpoints allow CRUD operations on configuration objects
3. All endpoints return JSON responses
4. Error responses follow standard HTTP status codes (400, 401, 403, 404, 500, etc.)
5. Rate limiting may apply - check for 429 responses

---

## Most Relevant for Topology Visualization

For building topology visualizations, the most useful endpoints are:

1. **Switch Controller Status**: `/switch-controller/managed-switch/status`
2. **Switch Port Information**: `/switch/port/`, `/switch/port-statistics/`
3. **MAC Address Tables**: `/switch/mac-address/`, `/switch/mac-address-summary/`
4. **LLDP State**: `/switch/lldp-state/` (for discovering network topology)
5. **Network Monitor**: `/switch/network-monitor-l2db/`, `/switch/network-monitor-l3db/`
6. **Security Fabric**: `/system/fortiguard/security-fabric`
7. **Detected Devices**: `/switch-controller/detected-device`

