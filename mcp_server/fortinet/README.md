# 🔥 Fortinet MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io/)

A comprehensive **Model Context Protocol (MCP)** server for **Fortinet FortiGate** and **FortiSwitch** management with **246 auto-discovered API endpoints**. Transform your simple curl commands into enterprise-grade network management with AI integration.

## 🚀 **Features**

- 🔍 **Auto-Discovery**: 246 endpoints from official Fortinet documentation
- 🤖 **AI Integration**: Claude Desktop, VS Code, Windsurf support
- 🔀 **Switch Management**: Complete FortiSwitch control via switch-controller
- ⚙️ **System Management**: Comprehensive FortiGate administration
- 🌐 **REST API Bridge**: curl-friendly HTTP endpoints
- 🐍 **Python SDK**: Direct programmatic access
- 🔧 **Multi-Platform**: 8 different usage methods

## 📊 **API Coverage**

| Category | Endpoints | Description |
|----------|-----------|-------------|
| **FortiGate System** | 192 | System monitoring, configuration, security |
| **FortiSwitch Direct** | 54 | Switch management, port control, VLANs |
| **Total Coverage** | **246** | **Complete Fortinet ecosystem** |

## Installation

### Prerequisites
```bash
pip install requests mcp-server-fastmcp
```

### Environment Configuration
Create a `.env` file or set environment variables:

```bash
# FortiGate Configuration
export FORTIGATE_HOST="https://192.168.0.254"
export FORTIGATE_API_TOKEN="your_api_token_here"
export FORTIGATE_USERNAME="admin"
export FORTIGATE_PASSWORD="your_password"
export FORTIGATE_VDOM="root"

# FortiManager Configuration (Optional)
export FORTIMANAGER_HOST="https://192.168.0.100"
export FORTIMANAGER_API_TOKEN="your_fm_token"
export FORTIMANAGER_USERNAME="admin"
export FORTIMANAGER_PASSWORD="your_fm_password"
```

### Running the Server
```bash
python fortinet_server_enhanced.py
```

### Testing the Installation
```bash
python test_server.py
```

## API Resources

### System Resources
- `fortinet://system/status` - System status information
- `fortinet://system/resource-usage` - Resource utilization
- `fortinet://system/performance` - Performance metrics
- `fortinet://system/global-config` - Global configuration

### Network Resources
- `fortinet://network/interfaces` - Network interfaces
- `fortinet://network/interface-stats` - Interface statistics
- `fortinet://network/routes` - Routing table
- `fortinet://network/arp-table` - ARP table

### Security Resources
- `fortinet://firewall/policies` - Firewall policies
- `fortinet://firewall/addresses` - Address objects
- `fortinet://firewall/services` - Service objects
- `fortinet://security/profiles` - Security profiles

### Switch Controller Resources
- `fortinet://switch-controller/detected-devices` - Detected devices
- `fortinet://switch-controller/managed-switches` - Managed switches
- `fortinet://switch-controller/port-stats` - Port statistics
- `fortinet://switch-controller/vlan-info` - VLAN information

### VPN Resources
- `fortinet://vpn/ipsec-tunnels` - IPSec tunnels
- `fortinet://vpn/ssl-settings` - SSL VPN settings
- `fortinet://vpn/tunnel-status` - Tunnel status

## Available Tools

### General Tools
- `get_endpoint_data(endpoint, params)` - Query any API endpoint
- `search_sessions(filter_criteria)` - Search active sessions
- `get_policy_details(policy_id)` - Get firewall policy details
- `analyze_traffic_logs(duration_minutes, source_ip)` - Analyze traffic
- `check_security_events(event_type, limit)` - Check security events
- `get_bandwidth_usage(interface, duration)` - Bandwidth statistics
- `diagnose_network_path(destination, source_interface)` - Network diagnosis
- `backup_configuration(backup_type)` - Configuration backup
- `list_available_endpoints()` - List all endpoints

### Switch Controller Tools
- `get_switch_details(switch_id)` - Switch information
- `get_switch_port_info(switch_id, port_name)` - Port details
- `manage_switch_vlan(switch_id, action, vlan_id, vlan_name)` - VLAN management
- `diagnose_switch_connectivity(switch_id)` - Switch diagnostics
- `get_switch_topology()` - Network topology
- `monitor_switch_performance(switch_id, duration_minutes)` - Performance monitoring

### Test & Validation Tools
- `test_api_connections()` - Test all connections
- `validate_configuration()` - Configuration validation
- `run_health_check()` - Comprehensive health check

### API Discovery Tools
- `discover_api_endpoints()` - Discover all available endpoints
- `get_endpoints_by_category(category)` - Get endpoints by category
- `call_discovered_endpoint(endpoint_key, parameters)` - Call any endpoint dynamically
- `search_endpoints(search_term)` - Search for specific endpoints
- `generate_endpoint_documentation()` - Generate comprehensive API docs

## Usage Examples

### Basic System Information
```python
# Get system status
await get_endpoint_data("monitor/system/status")

# Get interface statistics
await get_endpoint_data("monitor/system/interface")
```

### Switch Management
```python
# Get all managed switches
await get_switch_details()

# Get specific switch details
await get_switch_details("S124EPTQ22000276")

# List VLANs on a switch
await manage_switch_vlan("S124EPTQ22000276", "list")

# Get switch topology
await get_switch_topology()
```

### Security Monitoring
```python
# Check recent security events
await check_security_events("ips", 100)

# Analyze traffic for specific IP
await analyze_traffic_logs(60, "192.168.1.100")

# Run comprehensive health check
await run_health_check()
```

### Network Diagnostics
```python
# Diagnose path to destination
await diagnose_network_path("8.8.8.8", "wan1")

# Get bandwidth usage
await get_bandwidth_usage("wan1", "1hour")

# Test all connections
await test_api_connections()
```

### API Discovery and Dynamic Calls
```python
# Discover all available endpoints
await discover_api_endpoints()

# Get switch-controller endpoints
await get_endpoints_by_category("switch_controller")

# Search for specific functionality
await search_endpoints("detected-device")

# Call any endpoint dynamically
await call_discovered_endpoint("monitor_switch_controller_detected_device")

# Generate comprehensive documentation
await generate_endpoint_documentation()
```

## Prompt Templates

The server includes comprehensive prompt templates for:

1. **Security Audit Workflow** - Complete security assessment
2. **Network Troubleshooting** - Systematic network issue resolution
3. **Incident Response** - Security incident handling procedures

## Authentication

### API Token (Recommended)
1. Generate API token in FortiGate GUI: System > Administrators > Create New
2. Set token in environment variable: `FORTIGATE_API_TOKEN`

### Username/Password
1. Set credentials in environment variables
2. Ensure API access is enabled for the user

## Troubleshooting

### Common Issues

1. **SSL Certificate Errors**
   ```bash
   # Disable SSL verification (lab environments only)
   requests.session.verify = False
   ```

2. **Authentication Failures**
   ```bash
   # Test API token
   curl -H "Authorization: Bearer YOUR_TOKEN" https://fortigate/api/v2/monitor/system/status
   ```

3. **Permission Errors**
   - Ensure user has sufficient privileges
   - Check VDOM access permissions

### Debugging
Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Security Considerations

- Use API tokens instead of passwords when possible
- Implement proper network segmentation
- Monitor API access logs
- Rotate credentials regularly
- Use HTTPS for all communications

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review FortiGate API documentation
3. Create an issue in the repository