#!/usr/bin/env python3
"""
Enhanced Fortinet MCP Server with extensive API endpoint support
Includes automatic API endpoint discovery from Fortinet documentation
"""

import asyncio
import json
import logging
import os
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

# from mcp.server.fastmcp import FastMCP
try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    # Fallback: define a dummy FastMCP or raise a clear error
    class FastMCP:
        def __init__(self, *args, **kwargs):
            raise ImportError(
                "FastMCP could not be imported. Please ensure the 'mcp' package is installed and available."
            )


# Initialize FastMCP server
mcp = FastMCP("fortinet-server")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration from environment variables
FORTIGATE_HOST = os.getenv("FORTIGATE_HOST", "192.168.0.254")
FORTIGATE_USERNAME = os.getenv("FORTIGATE_USERNAME", "admin")
FORTIGATE_PASSWORD = os.getenv("FORTIGATE_PASSWORD", "!cg@RW%G@o")
FORTIGATE_API_TOKEN = os.getenv("FORTIGATE_API_TOKEN", "HbsysGgkc7wd1pp3xzQ095bb7jhzk8")
FORTIGATE_VDOM = os.getenv("FORTIGATE_VDOM", "root")

# FortiManager configuration
FORTIMANAGER_HOST = os.getenv("FORTIMANAGER_HOST", "")
FORTIMANAGER_USERNAME = os.getenv("FORTIMANAGER_USERNAME", "admin")
FORTIMANAGER_PASSWORD = os.getenv("FORTIMANAGER_PASSWORD", "")
FORTIMANAGER_API_TOKEN = os.getenv("FORTIMANAGER_API_TOKEN", "")


class FortinetAPIParser:
    """Parse Fortinet API documentation and discover endpoints"""
    
    def __init__(self, api_files_dir: str = "../../fortiosapi"):
        self.api_files_dir = Path(api_files_dir)
        self.discovered_endpoints = {}
        self.categories = {}
        
    def discover_endpoints(self) -> Dict[str, Any]:
        """Discover all available endpoints from API documentation"""
        if not self.api_files_dir.exists():
            logger.warning(f"API files directory {self.api_files_dir} not found")
            return {}
            
        logger.info("Discovering endpoints from API documentation...")
        
        for api_file in self.api_files_dir.glob("*.json"):
            try:
                with open(api_file, 'r') as f:
                    api_data = json.load(f)
                self._parse_swagger_api(api_data, api_file.stem)
            except Exception as e:
                logger.error(f"Error parsing {api_file}: {e}")
        
        logger.info(f"Discovered {len(self.discovered_endpoints)} endpoints across {len(self.categories)} categories")
        return self.discovered_endpoints
    
    def _parse_swagger_api(self, api_data: Dict, source_file: str):
        """Parse Swagger/OpenAPI format API documentation"""
        if "paths" not in api_data:
            return
            
        base_path = api_data.get("basePath", "/api/v2")
        paths = api_data.get("paths", {})
        
        for path, methods in paths.items():
            for method, details in methods.items():
                if method.lower() in ['get', 'post', 'put', 'delete']:
                    # Clean up the path
                    clean_path = path.replace(base_path, "").lstrip("/")
                    if base_path == "/api/v2/monitor":
                        clean_path = f"monitor/{clean_path}"
                    elif base_path == "/api/v2/cmdb":
                        clean_path = f"cmdb/{clean_path}"
                    
                    endpoint_info = {
                        'path': clean_path,
                        'full_path': f"{base_path}{path}",
                        'method': method.upper(),
                        'summary': details.get('summary', ''),
                        'description': details.get('description', ''),
                        'parameters': details.get('parameters', []),
                        'tags': details.get('tags', []),
                        'source_file': source_file,
                        'operationId': details.get('operationId', '')
                    }
                    
                    endpoint_key = clean_path.replace('/', '_').replace('-', '_').replace('{', '').replace('}', '')
                    self.discovered_endpoints[endpoint_key] = endpoint_info
                    
                    # Categorize endpoint
                    category = self._determine_category(clean_path, details.get('tags', []))
                    if category not in self.categories:
                        self.categories[category] = []
                    self.categories[category].append(endpoint_key)
    
    def _determine_category(self, path: str, tags: List[str]) -> str:
        """Determine the category for an endpoint"""
        path_lower = path.lower()
        
        categories = {
            'system': ['system', 'status', 'global', 'admin', 'interface', 'resource', 'config'],
            'switch_controller': ['switch-controller', 'switch_controller', 'fsw', 'managed-switch'],
            'switch_direct': ['switch/', 'switch-', 'port-', 'vlan-', 'stp-', 'lacp-', 'lldp-'],
            'firewall': ['firewall', 'policy', 'address', 'service', 'schedule', 'arp-table', 'proxy-arp'],
            'network': ['network', 'routing', 'dns', 'dhcp', 'interface', 'snooping'],
            'vpn': ['vpn', 'ipsec', 'ssl', 'tunnel'],
            'security': ['security', 'antivirus', 'ips', 'application', 'web-filter', '802.1x', 'acl'],
            'monitoring': ['monitor', 'log', 'traffic', 'performance', 'stats', 'utilization'],
            'configuration': ['cmdb/', 'config-', 'upgrade-', 'backup-', 'restore-'],
            'user': ['user', 'group', 'authentication', 'ldap'],
            'wireless': ['wireless', 'wifi', 'ap', 'ssid'],
            'ha': ['ha-', 'cluster', 'sync'],
            'qos': ['qos', 'traffic-shaping', 'priority'],
            'mac': ['mac-address', 'mac-table', 'fdb']
        }
        
        # Check for CMDB (configuration) endpoints first
        if path_lower.startswith('cmdb/'):
            return 'configuration'
        
        # Check for direct switch endpoints
        if any(keyword in path_lower for keyword in categories['switch_direct']):
            return 'switch_direct'
        
        # Check other categories
        for category, keywords in categories.items():
            if any(keyword in path_lower for keyword in keywords):
                return category
        
        return 'misc'
    
    def get_endpoints_by_category(self, category: str) -> List[str]:
        """Get all endpoints for a specific category"""
        return self.categories.get(category, [])
    
    def get_endpoint_info(self, endpoint_key: str) -> Dict:
        """Get detailed information about a specific endpoint"""
        return self.discovered_endpoints.get(endpoint_key, {})


class FortigateAPIClient:
    """Enhanced Fortigate API client with comprehensive endpoint support"""

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        api_token: str = "",
        vdom: str = "root",
    ):
        self.host = host
        self.username = username
        self.password = password
        self.api_token = api_token
        self.vdom = vdom
        self.session = requests.Session()
        self.session.verify = False  # Disable SSL verification for lab environments

    def _get_headers(self) -> Dict[str, str]:
        """Get appropriate headers for API requests"""
        headers = {"Content-Type": "application/json"}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"
        return headers

    def _make_request(
        self, method: str, endpoint: str, params: Dict = None, data: Dict = None
    ) -> Dict:
        """Make API request with proper error handling"""
        # Add vdom parameter if not already specified
        if params is None:
            params = {}
        if "vdom" not in params and self.vdom:
            params["vdom"] = self.vdom

        url = f"https://{self.host}/api/v2/{endpoint}"
        headers = self._get_headers()
        response = None

        try:
            if method.upper() == "GET":
                response = self.session.get(
                    url, headers=headers, params=params, timeout=30
                )
            elif method.upper() == "POST":
                response = self.session.post(
                    url, headers=headers, params=params, json=data, timeout=30
                )
            elif method.upper() == "PUT":
                response = self.session.put(
                    url, headers=headers, params=params, json=data, timeout=30
                )
            elif method.upper() == "DELETE":
                response = self.session.delete(
                    url, headers=headers, params=params, timeout=30
                )

            if response is None:
                return {"error": f"Unsupported method: {method}", "endpoint": endpoint}

            response.raise_for_status()
            
            # Handle empty responses
            if response.status_code == 204 or not response.text:
                return {"status": "success", "message": "Operation completed successfully"}
            
            return response.json()

        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP error {response.status_code if response else 'unknown'} for {endpoint}"
            if response and response.text:
                try:
                    error_detail = response.json()
                    error_msg += f": {error_detail.get('error', error_detail)}"
                except:
                    error_msg += f": {response.text[:200]}"
            logger.error(error_msg)
            return {"error": error_msg, "endpoint": endpoint, "status_code": response.status_code if response else None}
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed for {endpoint}: {e}")
            return {"error": str(e), "endpoint": endpoint}

    def test_connection(self) -> Dict:
        """Test API connection and authentication"""
        try:
            result = self._make_request("GET", "monitor/system/status")
            if "error" in result:
                return {"status": "failed", "error": result["error"]}
            return {"status": "success", "message": "Connection successful"}
        except Exception as e:
            return {"status": "failed", "error": str(e)}


class FortiManagerAPIClient:
    """FortiManager API client for centralized management"""
    
    def __init__(self, host: str, username: str, password: str, api_token: str = ""):
        self.host = host
        self.username = username
        self.password = password
        self.api_token = api_token
        self.session = requests.Session()
        self.session.verify = False
        self.session_id = None
        
    def _authenticate(self) -> bool:
        """Authenticate with FortiManager"""
        if not self.host:
            return False
            
        try:
            if self.api_token:
                # Use API token authentication
                return True
            else:
                # Use username/password authentication
                auth_data = {
                    "method": "exec",
                    "params": [{
                        "url": "/sys/login/user",
                        "data": {
                            "user": self.username,
                            "passwd": self.password
                        }
                    }]
                }
                
                response = self.session.post(
                    f"https://{self.host}/jsonrpc",
                    json=auth_data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("result", [{}])[0].get("status", {}).get("code") == 0:
                        self.session_id = result.get("session")
                        return True
                        
                return False
        except Exception as e:
            logger.error(f"FortiManager authentication failed: {e}")
            return False
    
    def _make_request(self, method: str, url: str, data: Dict = None) -> Dict:
        """Make FortiManager API request"""
        if not self.host:
            return {"error": "FortiManager host not configured"}
            
        try:
            if not self._authenticate():
                return {"error": "Authentication failed"}
                
            headers = {"Content-Type": "application/json"}
            if self.api_token:
                headers["Authorization"] = f"Bearer {self.api_token}"
                
            request_data = {
                "method": method,
                "params": [{
                    "url": url,
                    "data": data if data else {}
                }]
            }
            
            if self.session_id:
                request_data["session"] = self.session_id
                
            response = self.session.post(
                f"https://{self.host}/jsonrpc",
                json=request_data,
                headers=headers,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            if result.get("result", [{}])[0].get("status", {}).get("code") == 0:
                return result.get("result", [{}])[0].get("data", {})
            else:
                return {"error": result.get("result", [{}])[0].get("status", {}).get("message", "Unknown error")}
                
        except Exception as e:
            logger.error(f"FortiManager API request failed: {e}")
            return {"error": str(e)}
    
    def test_connection(self) -> Dict:
        """Test FortiManager connection"""
        if not self.host:
            return {"status": "skipped", "message": "FortiManager not configured"}
            
        try:
            result = self._make_request("get", "/sys/status")
            if "error" in result:
                return {"status": "failed", "error": result["error"]}
            return {"status": "success", "message": "FortiManager connection successful"}
        except Exception as e:
            return {"status": "failed", "error": str(e)}


# Initialize Fortigate API client
fg_api = FortigateAPIClient(
    FORTIGATE_HOST,
    FORTIGATE_USERNAME,
    FORTIGATE_PASSWORD,
    FORTIGATE_API_TOKEN,
    FORTIGATE_VDOM,
)

# Initialize FortiManager API client
fm_api = FortiManagerAPIClient(
    FORTIMANAGER_HOST,
    FORTIMANAGER_USERNAME,
    FORTIMANAGER_PASSWORD,
    FORTIMANAGER_API_TOKEN,
)

# Initialize API parser and discover endpoints
api_parser = FortinetAPIParser()
discovered_endpoints = api_parser.discover_endpoints()

# ==================== RESOURCES (Application-controlled context) ====================


# System Resources
@mcp.resource("fortinet://system/status")
async def get_system_status() -> str:
    """Get comprehensive system status"""
    result = fg_api._make_request("GET", "monitor/system/status")
    return json.dumps(result, indent=2)


@mcp.resource("fortinet://system/resource-usage")
async def get_system_resources() -> str:
    """Get system resource utilization"""
    result = fg_api._make_request("GET", "monitor/system/resource/usage")
    return json.dumps(result, indent=2)


@mcp.resource("fortinet://system/performance")
async def get_system_performance() -> str:
    """Get system performance statistics"""
    result = fg_api._make_request("GET", "monitor/system/performance")
    return json.dumps(result, indent=2)


@mcp.resource("fortinet://system/global-config")
async def get_global_config() -> str:
    """Get global system configuration"""
    result = fg_api._make_request("GET", "cmdb/system/global")
    return json.dumps(result, indent=2)


# Network Resources
@mcp.resource("fortinet://network/interfaces")
async def get_interfaces() -> str:
    """Get all network interfaces"""
    result = fg_api._make_request("GET", "cmdb/system/interface")
    return json.dumps(result, indent=2)


@mcp.resource("fortinet://network/interface-stats")
async def get_interface_stats() -> str:
    """Get network interface statistics"""
    result = fg_api._make_request("GET", "monitor/system/interface")
    return json.dumps(result, indent=2)


@mcp.resource("fortinet://network/routes")
async def get_routes() -> str:
    """Get routing table"""
    result = fg_api._make_request("GET", "monitor/router/ipv4")
    return json.dumps(result, indent=2)


@mcp.resource("fortinet://network/arp-table")
async def get_arp_table() -> str:
    """Get ARP table"""
    result = fg_api._make_request("GET", "monitor/system/arp")
    return json.dumps(result, indent=2)


# Security/Firewall Resources
@mcp.resource("fortinet://firewall/policies")
async def get_firewall_policies() -> str:
    """Get firewall policies"""
    result = fg_api._make_request("GET", "cmdb/firewall/policy")
    return json.dumps(result, indent=2)


@mcp.resource("fortinet://firewall/addresses")
async def get_firewall_addresses() -> str:
    """Get firewall address objects"""
    result = fg_api._make_request("GET", "cmdb/firewall/address")
    return json.dumps(result, indent=2)


@mcp.resource("fortinet://firewall/services")
async def get_firewall_services() -> str:
    """Get firewall service objects"""
    result = fg_api._make_request("GET", "cmdb/firewall.service/custom")
    return json.dumps(result, indent=2)


@mcp.resource("fortinet://security/profiles")
async def get_security_profiles() -> str:
    """Get security profiles"""
    profiles = {
        "antivirus": fg_api._make_request("GET", "cmdb/antivirus/profile"),
        "ips": fg_api._make_request("GET", "cmdb/ips/sensor"),
        "application": fg_api._make_request("GET", "cmdb/application/list"),
        "web_filter": fg_api._make_request("GET", "cmdb/webfilter/profile"),
    }
    return json.dumps(profiles, indent=2)


# VPN Resources
@mcp.resource("fortinet://vpn/ipsec-tunnels")
async def get_ipsec_tunnels() -> str:
    """Get IPSec tunnel configuration"""
    result = fg_api._make_request("GET", "cmdb/vpn.ipsec/phase1-interface")
    return json.dumps(result, indent=2)


@mcp.resource("fortinet://vpn/ssl-settings")
async def get_ssl_vpn() -> str:
    """Get SSL VPN configuration"""
    result = fg_api._make_request("GET", "cmdb/vpn.ssl/settings")
    return json.dumps(result, indent=2)


@mcp.resource("fortinet://vpn/tunnel-status")
async def get_vpn_tunnel_status() -> str:
    """Get VPN tunnel status"""
    result = fg_api._make_request("GET", "monitor/vpn/ipsec")
    return json.dumps(result, indent=2)


# User & Authentication Resources
@mcp.resource("fortinet://users/local")
async def get_local_users() -> str:
    """Get local user accounts"""
    result = fg_api._make_request("GET", "cmdb/user/local")
    return json.dumps(result, indent=2)


@mcp.resource("fortinet://users/groups")
async def get_user_groups() -> str:
    """Get user groups"""
    result = fg_api._make_request("GET", "cmdb/user/group")
    return json.dumps(result, indent=2)


# High Availability Resources
@mcp.resource("fortinet://ha/status")
async def get_ha_status() -> str:
    """Get High Availability status"""
    result = fg_api._make_request("GET", "monitor/system/ha-peer")
    return json.dumps(result, indent=2)


# Switch Controller Resources
@mcp.resource("fortinet://switch-controller/detected-devices")
async def get_detected_devices() -> str:
    """Get detected switch-controller devices"""
    result = fg_api._make_request("GET", "monitor/switch-controller/detected-device")
    return json.dumps(result, indent=2)


@mcp.resource("fortinet://switch-controller/managed-switches")
async def get_managed_switches() -> str:
    """Get managed FortiSwitch devices"""
    result = fg_api._make_request("GET", "monitor/switch-controller/managed-switch")
    return json.dumps(result, indent=2)


@mcp.resource("fortinet://switch-controller/switch-log")
async def get_switch_log() -> str:
    """Get switch controller logs"""
    result = fg_api._make_request("GET", "monitor/switch-controller/switch-log")
    return json.dumps(result, indent=2)


@mcp.resource("fortinet://switch-controller/fsw-firmware")
async def get_switch_firmware() -> str:
    """Get FortiSwitch firmware information"""
    result = fg_api._make_request("GET", "monitor/switch-controller/fsw-firmware")
    return json.dumps(result, indent=2)


@mcp.resource("fortinet://switch-controller/port-stats")
async def get_switch_port_stats() -> str:
    """Get switch port statistics"""
    result = fg_api._make_request("GET", "monitor/switch-controller/port-stats")
    return json.dumps(result, indent=2)


@mcp.resource("fortinet://switch-controller/vlan-info")
async def get_switch_vlan_info() -> str:
    """Get switch VLAN information"""
    result = fg_api._make_request("GET", "monitor/switch-controller/vlan")
    return json.dumps(result, indent=2)


@mcp.resource("fortinet://switch-controller/dhcp-snooping")
async def get_dhcp_snooping() -> str:
    """Get DHCP snooping information"""
    result = fg_api._make_request("GET", "monitor/switch-controller/dhcp-snooping")
    return json.dumps(result, indent=2)


# ==================== TOOLS (Model-controlled actions) ====================


@mcp.tool()
async def get_endpoint_data(endpoint: str, params: str = "{}") -> str:
    """Get data from any Fortinet API endpoint.

    Args:
        endpoint: The API endpoint path (e.g., "monitor/system/status")
        params: JSON string of additional parameters (default: "{}")
    """
    try:
        # Parse parameters
        param_dict = json.loads(params) if params != "{}" else {}

        # Make the API call
        result = fg_api._make_request("GET", endpoint, params=param_dict)

        return f"Endpoint: {endpoint}\nParameters: {params}\n\nResponse:\n{json.dumps(result, indent=2)}"
    except json.JSONDecodeError:
        return f"Error: Invalid JSON in parameters: {params}"
    except Exception as e:
        return f"Error calling endpoint {endpoint}: {str(e)}"


@mcp.tool()
async def search_sessions(filter_criteria: str = "") -> str:
    """Search active sessions with optional filtering.

    Args:
        filter_criteria: Filter criteria for sessions (e.g., source IP, destination, etc.)
    """
    try:
        params = {}
        if filter_criteria:
            params["filter"] = filter_criteria

        result = fg_api._make_request("GET", "monitor/system/session", params=params)

        if isinstance(result, dict) and "results" in result:
            session_count = len(result["results"])
            return f"Active Sessions (Count: {session_count}):\n{json.dumps(result, indent=2)}"
        else:
            return f"Session search results:\n{json.dumps(result, indent=2)}"

    except Exception as e:
        return f"Error searching sessions: {str(e)}"


@mcp.tool()
async def get_policy_details(policy_id: str) -> str:
    """Get detailed information about a specific firewall policy.

    Args:
        policy_id: The ID of the firewall policy to examine
    """
    try:
        # Get specific policy
        result = fg_api._make_request("GET", f"cmdb/firewall/policy/{policy_id}")

        if "error" in result:
            return f"Error: Could not find policy {policy_id}: {result['error']}"

        return f"Policy {policy_id} Details:\n{json.dumps(result, indent=2)}"

    except Exception as e:
        return f"Error getting policy details: {str(e)}"


@mcp.tool()
async def analyze_traffic_logs(duration_minutes: int = 60, source_ip: str = "") -> str:
    """Analyze recent traffic logs.

    Args:
        duration_minutes: How many minutes back to analyze (default: 60)
        source_ip: Filter by specific source IP (optional)
    """
    try:
        # Calculate time range
        end_time = int(time.time())
        start_time = end_time - (duration_minutes * 60)

        params = {"start": start_time, "end": end_time}

        if source_ip:
            params["srcip"] = source_ip

        result = fg_api._make_request("GET", "monitor/log/device", params=params)

        analysis = {
            "time_range": f"{duration_minutes} minutes",
            "filter": f"Source IP: {source_ip}" if source_ip else "All traffic",
            "logs": result,
        }

        return f"Traffic Log Analysis:\n{json.dumps(analysis, indent=2)}"

    except Exception as e:
        return f"Error analyzing traffic logs: {str(e)}"


@mcp.tool()
async def check_security_events(event_type: str = "all", limit: int = 50) -> str:
    """Check recent security events and alerts.

    Args:
        event_type: Type of events to check (all, ips, av, web_filter, etc.)
        limit: Maximum number of events to return (default: 50)
    """
    try:
        params = {"lines": limit}

        if event_type != "all":
            params["subtype"] = event_type

        result = fg_api._make_request("GET", "monitor/log/event", params=params)

        return f"Security Events ({event_type}):\n{json.dumps(result, indent=2)}"

    except Exception as e:
        return f"Error checking security events: {str(e)}"


@mcp.tool()
async def get_bandwidth_usage(interface: str = "", duration: str = "1hour") -> str:
    """Get bandwidth usage statistics.

    Args:
        interface: Specific interface to check (optional, checks all if empty)
        duration: Time duration (1hour, 1day, 1week)
    """
    try:
        params = {"scope": "global"}

        if interface:
            params["interface"] = interface

        if duration:
            params["period"] = duration

        result = fg_api._make_request(
            "GET", "monitor/system/interface-bandwidth", params=params
        )

        return f"Bandwidth Usage ({duration}):\n{json.dumps(result, indent=2)}"

    except Exception as e:
        return f"Error getting bandwidth usage: {str(e)}"


@mcp.tool()
async def diagnose_network_path(destination: str, source_interface: str = "") -> str:
    """Diagnose network path to a destination.

    Args:
        destination: Target IP address or hostname
        source_interface: Source interface to use (optional)
    """
    try:
        # Get routing information
        route_result = fg_api._make_request(
            "GET", f"monitor/router/lookup", params={"destination": destination}
        )

        # Get interface information if source specified
        interface_info = {}
        if source_interface:
            interface_info = fg_api._make_request(
                "GET", f"cmdb/system/interface/{source_interface}"
            )

        diagnosis = {
            "destination": destination,
            "source_interface": source_interface,
            "route_lookup": route_result,
            "interface_info": interface_info if source_interface else "Not specified",
        }

        return f"Network Path Diagnosis:\n{json.dumps(diagnosis, indent=2)}"

    except Exception as e:
        return f"Error diagnosing network path: {str(e)}"


@mcp.tool()
async def backup_configuration(backup_type: str = "full") -> str:
    """Create a configuration backup.

    Args:
        backup_type: Type of backup (full, partial)
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Get system configuration
        if backup_type == "full":
            config_data = {
                "system_global": fg_api._make_request("GET", "cmdb/system/global"),
                "firewall_policies": fg_api._make_request(
                    "GET", "cmdb/firewall/policy"
                ),
                "interfaces": fg_api._make_request("GET", "cmdb/system/interface"),
                "routes": fg_api._make_request("GET", "cmdb/router/static"),
                "security_profiles": {
                    "antivirus": fg_api._make_request("GET", "cmdb/antivirus/profile"),
                    "ips": fg_api._make_request("GET", "cmdb/ips/sensor"),
                },
            }
        else:
            config_data = {
                "system_global": fg_api._make_request("GET", "cmdb/system/global"),
                "firewall_policies": fg_api._make_request(
                    "GET", "cmdb/firewall/policy"
                ),
            }

        backup_info = {
            "timestamp": timestamp,
            "backup_type": backup_type,
            "device": FORTIGATE_HOST,
            "configuration": config_data,
        }

        return f"Configuration Backup Created:\n{json.dumps(backup_info, indent=2)}"

    except Exception as e:
        return f"Error creating backup: {str(e)}"


@mcp.tool()
async def list_available_endpoints() -> str:
    """List common Fortinet API endpoints organized by category."""

    endpoints = {
        "System Monitoring": [
            "monitor/system/status",
            "monitor/system/resource/usage",
            "monitor/system/performance",
            "monitor/system/interface",
            "monitor/system/session",
            "monitor/system/arp",
            "monitor/system/ha-peer",
        ],
        "Configuration Management": [
            "cmdb/system/global",
            "cmdb/system/interface",
            "cmdb/system/admin",
            "cmdb/system/dns",
            "cmdb/system/ntp",
        ],
        "Firewall & Security": [
            "cmdb/firewall/policy",
            "cmdb/firewall/address",
            "cmdb/firewall.service/custom",
            "cmdb/antivirus/profile",
            "cmdb/ips/sensor",
            "cmdb/webfilter/profile",
            "cmdb/application/list",
        ],
        "VPN": [
            "cmdb/vpn.ipsec/phase1-interface",
            "cmdb/vpn.ipsec/phase2-interface",
            "cmdb/vpn.ssl/settings",
            "monitor/vpn/ipsec",
            "monitor/vpn/ssl",
        ],
        "Routing & Networking": [
            "cmdb/router/static",
            "cmdb/router/policy",
            "monitor/router/ipv4",
            "monitor/router/ipv6",
        ],
        "Logging & Events": [
            "monitor/log/device",
            "monitor/log/event",
            "monitor/log/virus",
            "monitor/log/ips",
            "monitor/log/webfilter",
        ],
        "User Management": [
            "cmdb/user/local",
            "cmdb/user/group",
            "cmdb/user/ldap",
            "monitor/user/device",
        ],
    }

    return f"Available Fortinet API Endpoints:\n{json.dumps(endpoints, indent=2)}"


# Switch Controller Tools
@mcp.tool()
async def get_switch_details(switch_id: str = "") -> str:
    """Get detailed information about a specific FortiSwitch or all switches.
    
    Args:
        switch_id: The ID/serial number of the switch to examine (optional)
    """
    try:
        if switch_id:
            # Get specific switch details
            result = fg_api._make_request("GET", f"monitor/switch-controller/managed-switch/{switch_id}")
            return f"Switch {switch_id} Details:\n{json.dumps(result, indent=2)}"
        else:
            # Get all managed switches
            result = fg_api._make_request("GET", "monitor/switch-controller/managed-switch")
            return f"All Managed Switches:\n{json.dumps(result, indent=2)}"
    except Exception as e:
        return f"Error getting switch details: {str(e)}"


@mcp.tool()
async def get_switch_port_info(switch_id: str, port_name: str = "") -> str:
    """Get port information for a specific FortiSwitch.
    
    Args:
        switch_id: The ID/serial number of the switch
        port_name: Specific port to examine (optional, gets all ports if empty)
    """
    try:
        params = {"mkey": switch_id}
        if port_name:
            params["port"] = port_name
            
        result = fg_api._make_request("GET", "monitor/switch-controller/port-stats", params=params)
        
        if port_name:
            return f"Switch {switch_id} Port {port_name} Info:\n{json.dumps(result, indent=2)}"
        else:
            return f"Switch {switch_id} All Ports Info:\n{json.dumps(result, indent=2)}"
    except Exception as e:
        return f"Error getting switch port info: {str(e)}"


@mcp.tool()
async def manage_switch_vlan(switch_id: str, action: str, vlan_id: str = "", vlan_name: str = "") -> str:
    """Manage VLANs on a FortiSwitch.
    
    Args:
        switch_id: The ID/serial number of the switch
        action: Action to perform (list, create, delete, modify)
        vlan_id: VLAN ID for create/delete/modify actions
        vlan_name: VLAN name for create/modify actions
    """
    try:
        if action == "list":
            # List all VLANs
            result = fg_api._make_request("GET", "monitor/switch-controller/vlan", params={"mkey": switch_id})
            return f"Switch {switch_id} VLANs:\n{json.dumps(result, indent=2)}"
        elif action == "create":
            if not vlan_id:
                return "Error: VLAN ID is required for create action"
            data = {"vlanid": vlan_id}
            if vlan_name:
                data["name"] = vlan_name
            result = fg_api._make_request("POST", f"cmdb/switch-controller/vlan", data=data)
            return f"VLAN {vlan_id} creation result:\n{json.dumps(result, indent=2)}"
        elif action == "delete":
            if not vlan_id:
                return "Error: VLAN ID is required for delete action"
            result = fg_api._make_request("DELETE", f"cmdb/switch-controller/vlan/{vlan_id}")
            return f"VLAN {vlan_id} deletion result:\n{json.dumps(result, indent=2)}"
        else:
            return f"Error: Unsupported action '{action}'. Use: list, create, delete"
    except Exception as e:
        return f"Error managing switch VLAN: {str(e)}"


@mcp.tool()
async def diagnose_switch_connectivity(switch_id: str) -> str:
    """Diagnose connectivity issues with a FortiSwitch.
    
    Args:
        switch_id: The ID/serial number of the switch to diagnose
    """
    try:
        diagnosis = {}
        
        # Get switch status
        switch_info = fg_api._make_request("GET", f"monitor/switch-controller/managed-switch/{switch_id}")
        diagnosis["switch_status"] = switch_info
        
        # Get port statistics
        port_stats = fg_api._make_request("GET", "monitor/switch-controller/port-stats", params={"mkey": switch_id})
        diagnosis["port_statistics"] = port_stats
        
        # Get DHCP snooping info
        dhcp_info = fg_api._make_request("GET", "monitor/switch-controller/dhcp-snooping", params={"mkey": switch_id})
        diagnosis["dhcp_snooping"] = dhcp_info
        
        # Get VLAN info
        vlan_info = fg_api._make_request("GET", "monitor/switch-controller/vlan", params={"mkey": switch_id})
        diagnosis["vlan_info"] = vlan_info
        
        return f"Switch {switch_id} Connectivity Diagnosis:\n{json.dumps(diagnosis, indent=2)}"
    except Exception as e:
        return f"Error diagnosing switch connectivity: {str(e)}"


@mcp.tool()
async def get_switch_topology() -> str:
    """Get network topology showing all managed switches and their connections."""
    try:
        topology = {}
        
        # Get all managed switches
        managed_switches = fg_api._make_request("GET", "monitor/switch-controller/managed-switch")
        topology["managed_switches"] = managed_switches
        
        # Get detected devices
        detected_devices = fg_api._make_request("GET", "monitor/switch-controller/detected-device")
        topology["detected_devices"] = detected_devices
        
        # Get switch logs for connection events
        switch_logs = fg_api._make_request("GET", "monitor/switch-controller/switch-log")
        topology["recent_events"] = switch_logs
        
        return f"Network Topology:\n{json.dumps(topology, indent=2)}"
    except Exception as e:
        return f"Error getting switch topology: {str(e)}"


@mcp.tool()
async def monitor_switch_performance(switch_id: str, duration_minutes: int = 60) -> str:
    """Monitor switch performance metrics over time.
    
    Args:
        switch_id: The ID/serial number of the switch to monitor
        duration_minutes: How many minutes back to analyze performance
    """
    try:
        performance_data = {}
        
        # Get current port statistics
        port_stats = fg_api._make_request("GET", "monitor/switch-controller/port-stats", params={"mkey": switch_id})
        performance_data["current_port_stats"] = port_stats
        
        # Get switch system info
        switch_info = fg_api._make_request("GET", f"monitor/switch-controller/managed-switch/{switch_id}")
        performance_data["switch_info"] = switch_info
        
        # Calculate time range for historical data
        end_time = int(time.time())
        start_time = end_time - (duration_minutes * 60)
        
        # Get historical performance data if available
        hist_params = {"mkey": switch_id, "start": start_time, "end": end_time}
        historical_data = fg_api._make_request("GET", "monitor/switch-controller/port-stats", params=hist_params)
        performance_data["historical_data"] = historical_data
        
        performance_summary = {
            "switch_id": switch_id,
            "monitoring_duration": f"{duration_minutes} minutes",
            "timestamp": datetime.now().isoformat(),
            "performance_data": performance_data
        }
        
        return f"Switch {switch_id} Performance Monitor:\n{json.dumps(performance_summary, indent=2)}"
    except Exception as e:
        return f"Error monitoring switch performance: {str(e)}"


# Test and Validation Tools
@mcp.tool()
async def test_api_connections() -> str:
    """Test all API connections and authentication."""
    try:
        results = {}
        
        # Test FortiGate connection
        fg_result = fg_api.test_connection()
        results["fortigate"] = fg_result
        
        # Test FortiManager connection
        fm_result = fm_api.test_connection()
        results["fortimanager"] = fm_result
        
        # Summary
        summary = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "success" if all(r.get("status") == "success" for r in results.values()) else "partial" if any(r.get("status") == "success" for r in results.values()) else "failed",
            "connection_tests": results
        }
        
        return f"API Connection Test Results:\n{json.dumps(summary, indent=2)}"
    except Exception as e:
        return f"Error testing API connections: {str(e)}"


@mcp.tool()
async def validate_configuration() -> str:
    """Validate system configuration and identify potential issues."""
    try:
        validation_results = {}
        
        # Check system status
        system_status = fg_api._make_request("GET", "monitor/system/status")
        validation_results["system_status"] = system_status
        
        # Check license status
        license_status = fg_api._make_request("GET", "monitor/system/license")
        validation_results["license_status"] = license_status
        
        # Check interface configuration
        interfaces = fg_api._make_request("GET", "cmdb/system/interface")
        validation_results["interface_config"] = interfaces
        
        # Check firewall policies
        policies = fg_api._make_request("GET", "cmdb/firewall/policy")
        validation_results["firewall_policies"] = policies
        
        # Analyze configuration issues
        issues = []
        
        # Check for common configuration issues
        if isinstance(interfaces, dict) and "results" in interfaces:
            for interface in interfaces["results"]:
                if interface.get("status") == "down":
                    issues.append(f"Interface {interface.get('name')} is down")
        
        if isinstance(policies, dict) and "results" in policies:
            for policy in policies["results"]:
                if policy.get("status") == "disable":
                    issues.append(f"Firewall policy {policy.get('policyid')} is disabled")
        
        validation_summary = {
            "timestamp": datetime.now().isoformat(),
            "validation_status": "passed" if not issues else "issues_found",
            "issues_found": issues,
            "detailed_results": validation_results
        }
        
        return f"Configuration Validation Results:\n{json.dumps(validation_summary, indent=2)}"
    except Exception as e:
        return f"Error validating configuration: {str(e)}"


@mcp.tool()
async def run_health_check() -> str:
    """Run comprehensive health check on FortiGate and managed switches."""
    try:
        health_results = {}
        
        # System health
        system_health = {
            "status": fg_api._make_request("GET", "monitor/system/status"),
            "resources": fg_api._make_request("GET", "monitor/system/resource/usage"),
            "performance": fg_api._make_request("GET", "monitor/system/performance")
        }
        health_results["system"] = system_health
        
        # Network health
        network_health = {
            "interface_stats": fg_api._make_request("GET", "monitor/system/interface"),
            "routes": fg_api._make_request("GET", "monitor/router/ipv4"),
            "sessions": fg_api._make_request("GET", "monitor/system/session")
        }
        health_results["network"] = network_health
        
        # Switch health
        switch_health = {
            "managed_switches": fg_api._make_request("GET", "monitor/switch-controller/managed-switch"),
            "detected_devices": fg_api._make_request("GET", "monitor/switch-controller/detected-device"),
            "port_stats": fg_api._make_request("GET", "monitor/switch-controller/port-stats")
        }
        health_results["switches"] = switch_health
        
        # Security health
        security_health = {
            "av_stats": fg_api._make_request("GET", "monitor/antivirus/stats"),
            "ips_stats": fg_api._make_request("GET", "monitor/ips/stats"),
            "web_filter_stats": fg_api._make_request("GET", "monitor/webfilter/stats")
        }
        health_results["security"] = security_health
        
        # Calculate overall health score
        health_score = 100
        health_issues = []
        
        # Check CPU usage
        if isinstance(system_health["resources"], dict) and "results" in system_health["resources"]:
            cpu_usage = system_health["resources"]["results"].get("cpu", 0)
            if cpu_usage > 80:
                health_score -= 20
                health_issues.append(f"High CPU usage: {cpu_usage}%")
        
        # Check memory usage
        if isinstance(system_health["resources"], dict) and "results" in system_health["resources"]:
            memory_usage = system_health["resources"]["results"].get("memory", 0)
            if memory_usage > 80:
                health_score -= 15
                health_issues.append(f"High memory usage: {memory_usage}%")
        
        health_summary = {
            "timestamp": datetime.now().isoformat(),
            "overall_health_score": health_score,
            "health_status": "excellent" if health_score > 90 else "good" if health_score > 70 else "warning" if health_score > 50 else "critical",
            "issues_identified": health_issues,
            "detailed_results": health_results
        }
        
        return f"Health Check Results:\n{json.dumps(health_summary, indent=2)}"
    except Exception as e:
        return f"Error running health check: {str(e)}"


# API Discovery and Dynamic Endpoint Tools
@mcp.tool()
async def discover_api_endpoints() -> str:
    """Discover all available API endpoints from Fortinet documentation."""
    try:
        if not discovered_endpoints:
            # Try to re-discover if empty
            api_parser.discover_endpoints()
        
        summary = {
            "total_endpoints": len(discovered_endpoints),
            "categories": {},
            "recent_discovery": datetime.now().isoformat()
        }
        
        for category, endpoints in api_parser.categories.items():
            summary["categories"][category] = {
                "count": len(endpoints),
                "sample_endpoints": endpoints[:5]  # Show first 5 as samples
            }
        
        return f"API Endpoint Discovery Results:\n{json.dumps(summary, indent=2)}"
    except Exception as e:
        return f"Error discovering API endpoints: {str(e)}"


@mcp.tool()
async def get_endpoints_by_category(category: str) -> str:
    """Get all discovered endpoints for a specific category.
    
    Args:
        category: Category name (system, switch_controller, firewall, network, etc.)
    """
    try:
        endpoints = api_parser.get_endpoints_by_category(category)
        
        if not endpoints:
            available_categories = list(api_parser.categories.keys())
            return f"No endpoints found for category '{category}'. Available categories: {available_categories}"
        
        endpoint_details = []
        for endpoint_key in endpoints:
            endpoint_info = api_parser.get_endpoint_info(endpoint_key)
            endpoint_details.append({
                "key": endpoint_key,
                "path": endpoint_info.get("path", ""),
                "method": endpoint_info.get("method", "GET"),
                "summary": endpoint_info.get("summary", ""),
                "source": endpoint_info.get("source_file", "")
            })
        
        result = {
            "category": category,
            "endpoint_count": len(endpoints),
            "endpoints": endpoint_details
        }
        
        return f"Endpoints for category '{category}':\n{json.dumps(result, indent=2)}"
    except Exception as e:
        return f"Error getting endpoints for category '{category}': {str(e)}"


@mcp.tool()
async def call_discovered_endpoint(endpoint_key: str, parameters: str = "{}") -> str:
    """Call any discovered API endpoint dynamically.
    
    Args:
        endpoint_key: The endpoint key from discovery (e.g., 'monitor_switch_controller_detected_device')
        parameters: JSON string of parameters to pass to the endpoint
    """
    try:
        endpoint_info = api_parser.get_endpoint_info(endpoint_key)
        
        if not endpoint_info:
            return f"Endpoint '{endpoint_key}' not found. Use discover_api_endpoints() to see available endpoints."
        
        # Parse parameters
        try:
            params = json.loads(parameters) if parameters != "{}" else {}
        except json.JSONDecodeError:
            return f"Error: Invalid JSON in parameters: {parameters}"
        
        # Make the API call
        result = fg_api._make_request(
            endpoint_info["method"], 
            endpoint_info["path"], 
            params=params
        )
        
        response_summary = {
            "endpoint_key": endpoint_key,
            "path": endpoint_info["path"],
            "method": endpoint_info["method"],
            "summary": endpoint_info.get("summary", ""),
            "parameters_used": params,
            "response": result
        }
        
        return f"Dynamic Endpoint Call Results:\n{json.dumps(response_summary, indent=2)}"
    except Exception as e:
        return f"Error calling endpoint '{endpoint_key}': {str(e)}"


@mcp.tool()
async def search_endpoints(search_term: str) -> str:
    """Search for endpoints containing specific terms.
    
    Args:
        search_term: Term to search for in endpoint paths, summaries, or descriptions
    """
    try:
        matching_endpoints = []
        search_lower = search_term.lower()
        
        for endpoint_key, endpoint_info in discovered_endpoints.items():
            # Search in key, path, summary, and description
            searchable_text = " ".join([
                endpoint_key,
                endpoint_info.get("path", ""),
                endpoint_info.get("summary", ""),
                endpoint_info.get("description", "")
            ]).lower()
            
            if search_lower in searchable_text:
                matching_endpoints.append({
                    "key": endpoint_key,
                    "path": endpoint_info.get("path", ""),
                    "method": endpoint_info.get("method", "GET"),
                    "summary": endpoint_info.get("summary", ""),
                    "category": next((cat for cat, eps in api_parser.categories.items() if endpoint_key in eps), "misc")
                })
        
        result = {
            "search_term": search_term,
            "matches_found": len(matching_endpoints),
            "endpoints": matching_endpoints
        }
        
        return f"Endpoint Search Results:\n{json.dumps(result, indent=2)}"
    except Exception as e:
        return f"Error searching endpoints: {str(e)}"


@mcp.tool()
async def generate_endpoint_documentation() -> str:
    """Generate comprehensive documentation for all discovered endpoints."""
    try:
        doc_sections = {}
        
        for category, endpoints in api_parser.categories.items():
            doc_sections[category] = {
                "description": f"Endpoints related to {category.replace('_', ' ').title()}",
                "endpoint_count": len(endpoints),
                "endpoints": []
            }
            
            for endpoint_key in endpoints:
                endpoint_info = api_parser.get_endpoint_info(endpoint_key)
                doc_sections[category]["endpoints"].append({
                    "key": endpoint_key,
                    "path": endpoint_info.get("path", ""),
                    "method": endpoint_info.get("method", "GET"),
                    "summary": endpoint_info.get("summary", ""),
                    "description": endpoint_info.get("description", "")[:200] + "..." if len(endpoint_info.get("description", "")) > 200 else endpoint_info.get("description", ""),
                    "parameters": len(endpoint_info.get("parameters", [])),
                    "source_file": endpoint_info.get("source_file", "")
                })
        
        documentation = {
            "generated_at": datetime.now().isoformat(),
            "total_endpoints": len(discovered_endpoints),
            "total_categories": len(api_parser.categories),
            "categories": doc_sections
        }
        
        return f"API Endpoint Documentation:\n{json.dumps(documentation, indent=2)}"
    except Exception as e:
        return f"Error generating documentation: {str(e)}"


# FortiSwitch Direct API Tools  
@mcp.tool()
async def get_switch_direct_endpoints() -> str:
    """Get all direct FortiSwitch API endpoints for advanced switch management."""
    try:
        switch_endpoints = api_parser.get_endpoints_by_category("switch_direct")
        
        if not switch_endpoints:
            return "No direct FortiSwitch endpoints found"
        
        # Group by functionality
        grouped_endpoints = {
            "port_management": [],
            "vlan_management": [],  
            "security": [],
            "monitoring": [],
            "mac_tables": [],
            "other": []
        }
        
        for endpoint_key in switch_endpoints:
            endpoint_info = api_parser.get_endpoint_info(endpoint_key)
            path = endpoint_info.get("path", "").lower()
            
            endpoint_data = {
                "key": endpoint_key,
                "path": endpoint_info.get("path", ""),
                "method": endpoint_info.get("method", "GET"),
                "summary": endpoint_info.get("summary", "")
            }
            
            if "port" in path:
                grouped_endpoints["port_management"].append(endpoint_data)
            elif "vlan" in path:
                grouped_endpoints["vlan_management"].append(endpoint_data)
            elif "802.1x" in path or "acl" in path:
                grouped_endpoints["security"].append(endpoint_data)
            elif "mac-address" in path or "fdb" in path:
                grouped_endpoints["mac_tables"].append(endpoint_data)
            elif "stats" in path or "status" in path:
                grouped_endpoints["monitoring"].append(endpoint_data)
            else:
                grouped_endpoints["other"].append(endpoint_data)
        
        result = {
            "total_switch_endpoints": len(switch_endpoints),
            "grouped_endpoints": grouped_endpoints
        }
        
        return f"FortiSwitch Direct API Endpoints:\n{json.dumps(result, indent=2)}"
    except Exception as e:
        return f"Error getting switch direct endpoints: {str(e)}"


@mcp.tool()
async def get_configuration_endpoints() -> str:
    """Get all CMDB configuration management endpoints."""
    try:
        config_endpoints = api_parser.get_endpoints_by_category("configuration")
        
        if not config_endpoints:
            return "No configuration endpoints found"
        
        endpoint_details = []
        for endpoint_key in config_endpoints:
            endpoint_info = api_parser.get_endpoint_info(endpoint_key)
            endpoint_details.append({
                "key": endpoint_key,
                "path": endpoint_info.get("path", ""),
                "method": endpoint_info.get("method", "GET"),
                "summary": endpoint_info.get("summary", ""),
                "description": endpoint_info.get("description", "")[:100] + "..." if len(endpoint_info.get("description", "")) > 100 else endpoint_info.get("description", "")
            })
        
        result = {
            "total_config_endpoints": len(config_endpoints),
            "endpoints": endpoint_details,
            "note": "These are CMDB endpoints for system configuration management"
        }
        
        return f"Configuration Management Endpoints:\n{json.dumps(result, indent=2)}"
    except Exception as e:
        return f"Error getting configuration endpoints: {str(e)}"


@mcp.tool()
async def call_switch_direct_endpoint(endpoint_key: str, parameters: str = "{}") -> str:
    """Call FortiSwitch direct API endpoints for advanced switch operations.
    
    Args:
        endpoint_key: Switch endpoint key (use get_switch_direct_endpoints to see available ones)
        parameters: JSON string of parameters
    """
    try:
        endpoint_info = api_parser.get_endpoint_info(endpoint_key)
        
        if not endpoint_info:
            return f"Switch endpoint '{endpoint_key}' not found"
            
        # Verify this is a switch direct endpoint
        if not endpoint_key in api_parser.get_endpoints_by_category("switch_direct"):
            return f"'{endpoint_key}' is not a direct switch endpoint"
        
        # Parse parameters
        try:
            params = json.loads(parameters) if parameters != "{}" else {}
        except json.JSONDecodeError:
            return f"Error: Invalid JSON in parameters: {parameters}"
        
        # Make the API call
        result = fg_api._make_request(
            endpoint_info["method"], 
            endpoint_info["path"], 
            params=params
        )
        
        response_summary = {
            "endpoint_type": "switch_direct",
            "endpoint_key": endpoint_key,
            "path": endpoint_info["path"],
            "method": endpoint_info["method"],
            "summary": endpoint_info.get("summary", ""),
            "parameters_used": params,
            "response": result
        }
        
        return f"FortiSwitch Direct API Call Results:\n{json.dumps(response_summary, indent=2)}"
    except Exception as e:
        return f"Error calling switch direct endpoint '{endpoint_key}': {str(e)}"


@mcp.tool()
async def manage_system_configuration(action: str, config_type: str = "arp-table", config_data: str = "{}") -> str:
    """Manage system configuration using CMDB endpoints.
    
    Args:
        action: Action to perform (get, create, update, delete)
        config_type: Type of configuration (arp-table, proxy-arp, etc.)
        config_data: JSON string of configuration data for create/update operations
    """
    try:
        # Map actions to HTTP methods
        action_map = {
            "get": "GET",
            "create": "POST", 
            "update": "PUT",
            "delete": "DELETE"
        }
        
        if action not in action_map:
            return f"Invalid action '{action}'. Use: get, create, update, delete"
        
        # Find appropriate endpoint
        config_endpoints = api_parser.get_endpoints_by_category("configuration")
        target_endpoint = None
        
        for endpoint_key in config_endpoints:
            endpoint_info = api_parser.get_endpoint_info(endpoint_key)
            if config_type in endpoint_info.get("path", "").lower() and endpoint_info.get("method") == action_map[action]:
                target_endpoint = endpoint_info
                break
        
        if not target_endpoint:
            available_configs = set()
            for endpoint_key in config_endpoints:
                endpoint_info = api_parser.get_endpoint_info(endpoint_key)
                path_parts = endpoint_info.get("path", "").split("/")
                if len(path_parts) > 2:
                    available_configs.add(path_parts[-1].replace("{id}", ""))
            return f"Configuration type '{config_type}' not found for action '{action}'. Available types: {list(available_configs)}"
        
        # Parse configuration data
        try:
            data = json.loads(config_data) if config_data != "{}" else {}
        except json.JSONDecodeError:
            return f"Error: Invalid JSON in config_data: {config_data}"
        
        # Make the API call
        if action in ["create", "update"]:
            result = fg_api._make_request(target_endpoint["method"], target_endpoint["path"], data=data)
        else:
            result = fg_api._make_request(target_endpoint["method"], target_endpoint["path"])
        
        response_summary = {
            "action": action,
            "config_type": config_type,
            "endpoint_path": target_endpoint["path"],
            "method": target_endpoint["method"],
            "config_data_used": data if action in ["create", "update"] else None,
            "response": result
        }
        
        return f"System Configuration Management Results:\n{json.dumps(response_summary, indent=2)}"
    except Exception as e:
        return f"Error managing system configuration: {str(e)}"


# FortiGate Specific API Tools
@mcp.tool()
async def get_fortigate_endpoints() -> str:
    """Get all FortiGate specific API endpoints organized by functionality."""
    try:
        # Filter FortiGate endpoints by source file
        fortigate_files = [
            'FortiOS 7.6 FortiOS 7.6.3 Configuration API system',
            'FortiOS 7.6 FortiOS 7.6.3 Monitor API system', 
            'FortiOS 7.6 FortiOS 7.6.3 Monitor API switch-controller'
        ]
        
        fortigate_endpoints = {}
        functional_groups = {
            'system_management': [],
            'network_monitoring': [],
            'security_management': [],
            'switch_controller': [],
            'configuration': [],
            'logging': [],
            'vpn_management': [],
            'user_management': [],
            'high_availability': [],
            'other': []
        }
        
        for key, info in discovered_endpoints.items():
            source = info.get('source_file', '')
            if any(fg_file in source for fg_file in fortigate_files):
                path = info.get('path', '').lower()
                endpoint_data = {
                    'key': key,
                    'path': info.get('path', ''),
                    'method': info.get('method', 'GET'),
                    'summary': info.get('summary', ''),
                    'source': source
                }
                
                # Categorize by functionality
                if 'switch-controller' in path:
                    functional_groups['switch_controller'].append(endpoint_data)
                elif 'system' in path and any(x in path for x in ['status', 'admin', 'interface', 'resource']):
                    functional_groups['system_management'].append(endpoint_data)
                elif any(x in path for x in ['firewall', 'policy', 'security', 'antivirus', 'ips']):
                    functional_groups['security_management'].append(endpoint_data)
                elif any(x in path for x in ['vpn', 'ipsec', 'ssl']):
                    functional_groups['vpn_management'].append(endpoint_data)
                elif any(x in path for x in ['user', 'group', 'authentication']):
                    functional_groups['user_management'].append(endpoint_data)
                elif any(x in path for x in ['ha', 'cluster']):
                    functional_groups['high_availability'].append(endpoint_data)
                elif any(x in path for x in ['log', 'event']):
                    functional_groups['logging'].append(endpoint_data)
                elif 'cmdb' in path:
                    functional_groups['configuration'].append(endpoint_data)
                elif any(x in path for x in ['network', 'interface', 'routing']):
                    functional_groups['network_monitoring'].append(endpoint_data)
                else:
                    functional_groups['other'].append(endpoint_data)
        
        # Create summary
        total_fortigate = sum(len(eps) for eps in functional_groups.values())
        result = {
            'total_fortigate_endpoints': total_fortigate,
            'functional_groups': {}
        }
        
        for group, endpoints in functional_groups.items():
            if endpoints:  # Only include non-empty groups
                result['functional_groups'][group] = {
                    'count': len(endpoints),
                    'endpoints': endpoints
                }
        
        return f"FortiGate API Endpoints by Functionality:\n{json.dumps(result, indent=2)}"
    except Exception as e:
        return f"Error getting FortiGate endpoints: {str(e)}"


@mcp.tool()
async def fortigate_system_overview() -> str:
    """Get comprehensive FortiGate system overview using multiple endpoints."""
    try:
        overview = {
            'timestamp': datetime.now().isoformat(),
            'system_info': {},
            'resource_usage': {},
            'interface_status': {},
            'security_status': {},
            'switch_controller': {}
        }
        
        # System status
        system_status = fg_api._make_request("GET", "monitor/system/status")
        if "error" not in system_status:
            results = system_status.get('results', {})
            overview['system_info'] = {
                'hostname': results.get('hostname', 'Unknown'),
                'version': results.get('version', 'Unknown'),
                'serial': results.get('serial', 'Unknown'),
                'model': results.get('model', 'Unknown'),
                'uptime': results.get('uptime', 'Unknown'),
                'timezone': results.get('timezone', 'Unknown')
            }
        
        # Resource usage
        resource_usage = fg_api._make_request("GET", "monitor/system/resource/usage")
        if "error" not in resource_usage:
            results = resource_usage.get('results', {})
            overview['resource_usage'] = {
                'cpu_usage': results.get('cpu', 'Unknown'),
                'memory_usage': results.get('memory', 'Unknown'),
                'disk_usage': results.get('disk', 'Unknown'),
                'session_count': results.get('session_count', 'Unknown')
            }
        
        # Interface statistics
        interfaces = fg_api._make_request("GET", "monitor/system/interface")
        if "error" not in interfaces:
            interface_list = interfaces.get('results', [])
            overview['interface_status'] = {
                'total_interfaces': len(interface_list),
                'active_interfaces': len([i for i in interface_list if i.get('link', False)]),
                'interfaces': [
                    {
                        'name': iface.get('name', ''),
                        'status': 'up' if iface.get('link', False) else 'down',
                        'speed': iface.get('speed', 'Unknown'),
                        'duplex': iface.get('duplex', 'Unknown')
                    }
                    for iface in interface_list[:10]  # First 10 interfaces
                ]
            }
        
        # Switch controller status
        detected_devices = fg_api._make_request("GET", "monitor/switch-controller/detected-device")
        if "error" not in detected_devices:
            devices = detected_devices.get('results', [])
            overview['switch_controller'] = {
                'detected_devices': len(devices),
                'switches': list(set([d.get('switch_id', '') for d in devices if d.get('switch_id')])),
                'vlans_in_use': list(set([d.get('vlan_id') for d in devices if d.get('vlan_id')]))
            }
        
        return f"FortiGate System Overview:\n{json.dumps(overview, indent=2)}"
    except Exception as e:
        return f"Error getting system overview: {str(e)}"


@mcp.tool()
async def fortigate_security_analysis() -> str:
    """Analyze FortiGate security configuration and status."""
    try:
        security_analysis = {
            'timestamp': datetime.now().isoformat(),
            'firewall_policies': {},
            'security_profiles': {},
            'threats_detected': {},
            'vpn_status': {},
            'user_activity': {}
        }
        
        # Get firewall policies (if available)
        policies = fg_api._make_request("GET", "cmdb/firewall/policy")
        if "error" not in policies:
            policy_results = policies.get('results', [])
            security_analysis['firewall_policies'] = {
                'total_policies': len(policy_results),
                'enabled_policies': len([p for p in policy_results if p.get('status') == 'enable']),
                'disabled_policies': len([p for p in policy_results if p.get('status') == 'disable'])
            }
        
        # Check antivirus stats
        av_stats = fg_api._make_request("GET", "monitor/antivirus/stats")
        if "error" not in av_stats:
            security_analysis['threats_detected']['antivirus'] = av_stats.get('results', {})
        
        # Check IPS stats
        ips_stats = fg_api._make_request("GET", "monitor/ips/stats")
        if "error" not in ips_stats:
            security_analysis['threats_detected']['ips'] = ips_stats.get('results', {})
        
        # Check web filter stats
        webfilter_stats = fg_api._make_request("GET", "monitor/webfilter/stats")
        if "error" not in webfilter_stats:
            security_analysis['threats_detected']['web_filter'] = webfilter_stats.get('results', {})
        
        # VPN status
        vpn_status = fg_api._make_request("GET", "monitor/vpn/ipsec")
        if "error" not in vpn_status:
            vpn_tunnels = vpn_status.get('results', [])
            security_analysis['vpn_status'] = {
                'total_tunnels': len(vpn_tunnels),
                'active_tunnels': len([t for t in vpn_tunnels if t.get('status') == 'up']),
                'inactive_tunnels': len([t for t in vpn_tunnels if t.get('status') != 'up'])
            }
        
        return f"FortiGate Security Analysis:\n{json.dumps(security_analysis, indent=2)}"
    except Exception as e:
        return f"Error performing security analysis: {str(e)}"


@mcp.tool()
async def fortigate_network_diagnostics(target_ip: str = "", interface: str = "") -> str:
    """Perform comprehensive network diagnostics on FortiGate.
    
    Args:
        target_ip: IP address to diagnose connectivity to (optional)
        interface: Specific interface to check (optional)
    """
    try:
        diagnostics = {
            'timestamp': datetime.now().isoformat(),
            'target_ip': target_ip,
            'interface': interface,
            'routing_table': {},
            'arp_table': {},
            'interface_stats': {},
            'session_info': {},
            'path_analysis': {}
        }
        
        # Get routing table
        routes = fg_api._make_request("GET", "monitor/router/ipv4")
        if "error" not in routes:
            route_results = routes.get('results', [])
            diagnostics['routing_table'] = {
                'total_routes': len(route_results),
                'default_routes': len([r for r in route_results if r.get('destination') == '0.0.0.0/0']),
                'static_routes': len([r for r in route_results if r.get('type') == 'static'])
            }
        
        # Get ARP table
        arp_table = fg_api._make_request("GET", "monitor/system/arp")
        if "error" not in arp_table:
            arp_results = arp_table.get('results', [])
            diagnostics['arp_table'] = {
                'total_entries': len(arp_results),
                'dynamic_entries': len([a for a in arp_results if a.get('type') == 'dynamic']),
                'static_entries': len([a for a in arp_results if a.get('type') == 'static'])
            }
        
        # Interface statistics
        interfaces = fg_api._make_request("GET", "monitor/system/interface")
        if "error" not in interfaces:
            interface_results = interfaces.get('results', [])
            if interface:
                # Filter for specific interface
                interface_data = next((i for i in interface_results if i.get('name') == interface), None)
                if interface_data:
                    diagnostics['interface_stats'] = interface_data
            else:
                diagnostics['interface_stats'] = {
                    'total_interfaces': len(interface_results),
                    'up_interfaces': len([i for i in interface_results if i.get('link', False)]),
                    'summary': [
                        {
                            'name': i.get('name', ''),
                            'status': 'up' if i.get('link', False) else 'down',
                            'rx_packets': i.get('rx_packets', 0),
                            'tx_packets': i.get('tx_packets', 0),
                            'rx_errors': i.get('rx_errors', 0),
                            'tx_errors': i.get('tx_errors', 0)
                        }
                        for i in interface_results[:5]  # First 5 interfaces
                    ]
                }
        
        # Active sessions
        sessions = fg_api._make_request("GET", "monitor/system/session")
        if "error" not in sessions:
            session_results = sessions.get('results', [])
            diagnostics['session_info'] = {
                'total_sessions': len(session_results),
                'tcp_sessions': len([s for s in session_results if s.get('proto') == 6]),
                'udp_sessions': len([s for s in session_results if s.get('proto') == 17])
            }
            
            # If target IP specified, find related sessions
            if target_ip:
                related_sessions = [
                    s for s in session_results 
                    if target_ip in [s.get('srcip', ''), s.get('dstip', '')]
                ]
                diagnostics['path_analysis']['related_sessions'] = len(related_sessions)
        
        # Path analysis for target IP
        if target_ip:
            route_lookup = fg_api._make_request("GET", f"monitor/router/lookup", params={"destination": target_ip})
            if "error" not in route_lookup:
                diagnostics['path_analysis']['route_lookup'] = route_lookup.get('results', {})
        
        return f"FortiGate Network Diagnostics:\n{json.dumps(diagnostics, indent=2)}"
    except Exception as e:
        return f"Error performing network diagnostics: {str(e)}"


@mcp.tool()
async def fortigate_performance_monitor(duration_minutes: int = 5) -> str:
    """Monitor FortiGate performance metrics over time.
    
    Args:
        duration_minutes: How many minutes of performance data to analyze
    """
    try:
        performance_data = {
            'timestamp': datetime.now().isoformat(),
            'monitoring_duration': f"{duration_minutes} minutes",
            'current_performance': {},
            'resource_utilization': {},
            'traffic_statistics': {},
            'recommendations': []
        }
        
        # Current performance metrics
        perf_stats = fg_api._make_request("GET", "monitor/system/performance")
        if "error" not in perf_stats:
            performance_data['current_performance'] = perf_stats.get('results', {})
        
        # Resource utilization
        resource_usage = fg_api._make_request("GET", "monitor/system/resource/usage")
        if "error" not in resource_usage:
            results = resource_usage.get('results', {})
            performance_data['resource_utilization'] = results
            
            # Generate recommendations based on usage
            cpu_usage = results.get('cpu', 0)
            memory_usage = results.get('memory', 0)
            
            if cpu_usage > 80:
                performance_data['recommendations'].append(f"High CPU usage detected ({cpu_usage}%). Consider reviewing firewall policies and security profiles.")
            
            if memory_usage > 85:
                performance_data['recommendations'].append(f"High memory usage detected ({memory_usage}%). Monitor active sessions and consider system optimization.")
        
        # Interface traffic statistics
        interfaces = fg_api._make_request("GET", "monitor/system/interface")
        if "error" not in interfaces:
            interface_results = interfaces.get('results', [])
            high_traffic_interfaces = []
            
            for iface in interface_results:
                if iface.get('link', False):  # Only active interfaces
                    rx_bytes = iface.get('rx_bytes', 0)
                    tx_bytes = iface.get('tx_bytes', 0)
                    if rx_bytes > 1000000 or tx_bytes > 1000000:  # > 1MB
                        high_traffic_interfaces.append({
                            'name': iface.get('name', ''),
                            'rx_bytes': rx_bytes,
                            'tx_bytes': tx_bytes,
                            'rx_packets': iface.get('rx_packets', 0),
                            'tx_packets': iface.get('tx_packets', 0)
                        })
            
            performance_data['traffic_statistics'] = {
                'total_interfaces': len(interface_results),
                'active_interfaces': len([i for i in interface_results if i.get('link', False)]),
                'high_traffic_interfaces': high_traffic_interfaces
            }
        
        return f"FortiGate Performance Monitor:\n{json.dumps(performance_data, indent=2)}"
    except Exception as e:
        return f"Error monitoring performance: {str(e)}"


# ==================== PROMPTS (User-controlled templates) ====================


@mcp.prompt()
async def comprehensive_security_audit(
    device_name: str = "Fortigate", scope: str = "full"
) -> str:
    """Generate a comprehensive security audit workflow.

    Args:
        device_name: Name of the device to audit
        scope: Audit scope (full, firewall, network, system)
    """
    return f"""
# COMPREHENSIVE SECURITY AUDIT: {device_name}
Scope: {scope.upper()}

## 1. SYSTEM HEALTH CHECK
- Get system status and version information
- Check system resource utilization and performance
- Verify High Availability status (if applicable)
- Review system global configuration

## 2. NETWORK SECURITY ANALYSIS
- Analyze firewall policies for effectiveness and compliance
- Review network interfaces and routing configuration
- Check VPN tunnel status and configuration
- Examine active network sessions

## 3. SECURITY PROFILE REVIEW
- Audit antivirus profile settings
- Review IPS sensor configuration
- Check web filtering policies
- Analyze application control settings

## 4. ACCESS CONTROL ASSESSMENT
- Review user accounts and group memberships
- Check administrative access controls
- Audit authentication settings
- Verify privilege escalation controls

## 5. LOG AND EVENT ANALYSIS
- Review recent security events and alerts
- Analyze traffic patterns for anomalies
- Check for indicators of compromise
- Verify logging configuration

## 6. COMPLIANCE AND BEST PRACTICES
- Verify security hardening measures
- Check against industry best practices
- Review backup and disaster recovery
- Assess change management procedures

Please execute this audit systematically using the available tools and provide detailed findings with prioritized recommendations.
"""


@mcp.prompt()
async def network_troubleshooting_workflow(
    issue_description: str, affected_users: str = "unknown"
) -> str:
    """Generate a network troubleshooting workflow.

    Args:
        issue_description: Description of the network issue
        affected_users: Users or systems affected
    """
    return f"""
# NETWORK TROUBLESHOOTING WORKFLOW
Issue: {issue_description}
Affected Users/Systems: {affected_users}

## PHASE 1: INFORMATION GATHERING
1. **System Status Check**
   - Verify overall system health and performance
   - Check interface status and statistics
   - Review active sessions and connections

2. **Network Layer Analysis**
   - Examine routing table and interface configuration
   - Check ARP table for layer 2 connectivity
   - Analyze bandwidth utilization patterns

3. **Traffic Flow Analysis**
   - Review firewall policies affecting the issue
   - Check traffic logs for dropped or denied packets
   - Examine session table for connection states

## PHASE 2: ISSUE ISOLATION
1. **Path Analysis**
   - Trace network path to affected destinations
   - Verify routing decisions and next-hop selection
   - Check for routing loops or blackholes

2. **Policy Verification** 
   - Validate firewall policies are allowing expected traffic
   - Check security profiles for blocks or drops
   - Verify NAT policies if applicable

3. **Performance Analysis**
   - Check interface utilization and errors
   - Monitor system resource consumption
   - Analyze connection limits and thresholds

## PHASE 3: RESOLUTION AND VERIFICATION
1. **Implement Solution**
   - Apply necessary configuration changes
   - Clear relevant caches or states if needed
   - Monitor for immediate improvements

2. **Verification Testing**
   - Test connectivity from affected systems
   - Verify traffic flows as expected
   - Confirm resolution with affected users

3. **Documentation and Prevention**
   - Document root cause and resolution
   - Update monitoring and alerting
   - Implement preventive measures

Use the available diagnostic tools to work through each phase systematically.
"""


@mcp.prompt()
async def incident_response_security_breach(
    incident_type: str, severity: str = "high", initial_indicators: str = ""
) -> str:
    """Generate security incident response workflow.

    Args:
        incident_type: Type of security incident
        severity: Incident severity (low, medium, high, critical)
        initial_indicators: Initial signs or indicators of the incident
    """
    return f"""
# SECURITY INCIDENT RESPONSE PROTOCOL
Incident Type: {incident_type}
Severity: {severity.upper()}
Initial Indicators: {initial_indicators}

## IMMEDIATE RESPONSE (First 15 minutes)
1. **Incident Verification**
   - Confirm the security incident is genuine
   - Assess immediate scope and impact
   - Determine if containment is urgently needed

2. **Initial Containment**
   - Identify affected systems and network segments
   - Consider temporary access restrictions if needed
   - Document all immediate actions taken

## INVESTIGATION PHASE (15 minutes - 1 hour)
1. **Evidence Collection**
   - Gather security event logs and alerts
   - Capture current firewall sessions and states
   - Document system configurations and states

2. **Threat Analysis**
   - Analyze traffic patterns for anomalies
   - Check for lateral movement indicators
   - Identify potential attack vectors and methods

3. **Scope Assessment**
   - Map affected networks and systems
   - Identify data or systems at risk
   - Assess potential business impact

## CONTAINMENT AND ERADICATION (1-4 hours)
1. **Enhanced Containment**
   - Implement additional firewall rules if needed
   - Block malicious IP addresses or domains
   - Isolate compromised systems if identified

2. **Threat Elimination**
   - Remove identified threats from the environment
   - Patch vulnerabilities that enabled the incident
   - Update security configurations as needed

3. **System Hardening**
   - Strengthen security controls
   - Update detection signatures and rules
   - Implement additional monitoring

## RECOVERY AND LESSONS LEARNED
1. **Service Restoration**
   - Gradually restore normal operations
   - Monitor for recurrence or related activity
   - Validate security controls are effective

2. **Post-Incident Analysis**
   - Conduct thorough incident review
   - Document lessons learned and improvements
   - Update incident response procedures

Execute this response plan using available security tools and monitoring capabilities.
"""


if __name__ == "__main__":
    # Run the server
    mcp.run()
