#!/usr/bin/env python3
"""
Enhanced Fortinet MCP Server with extensive API endpoint support
"""

import asyncio
import json
import logging
import os
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

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

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed for {endpoint}: {e}")
            return {"error": str(e), "endpoint": endpoint}


# Initialize Fortigate API client
fg_api = FortigateAPIClient(
    FORTIGATE_HOST,
    FORTIGATE_USERNAME,
    FORTIGATE_PASSWORD,
    FORTIGATE_API_TOKEN,
    FORTIGATE_VDOM,
)

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
