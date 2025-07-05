#!/usr/bin/env python3
"""
Fortinet MCP Server - Provides access to Fortigate, Fortimanager, and Fortianalyzer APIs and CLI commands
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional, Union
import base64
import requests
from urllib.parse import urljoin
import paramiko
import time
from datetime import datetime, timedelta

from mcp.server.fastmcp import FastMCP
from mcp.types import Resource, Tool, TextContent, ImageContent

# Initialize FastMCP server
mcp = FastMCP("fortinet-server")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration from environment variables
FORTIGATE_HOST = os.getenv("FORTIGATE_HOST", "192.168.1.1")
FORTIGATE_USERNAME = os.getenv("FORTIGATE_USERNAME", "admin")
FORTIGATE_PASSWORD = os.getenv("FORTIGATE_PASSWORD", "")
FORTIGATE_API_TOKEN = os.getenv("FORTIGATE_API_TOKEN", "")

FORTIMANAGER_HOST = os.getenv("FORTIMANAGER_HOST", "")
FORTIMANAGER_USERNAME = os.getenv("FORTIMANAGER_USERNAME", "admin")
FORTIMANAGER_PASSWORD = os.getenv("FORTIMANAGER_PASSWORD", "")

FORTIANALYZER_HOST = os.getenv("FORTIANALYZER_HOST", "")
FORTIANALYZER_USERNAME = os.getenv("FORTIANALYZER_USERNAME", "admin")
FORTIANALYZER_PASSWORD = os.getenv("FORTIANALYZER_PASSWORD", "")

class FortinetAPI:
    """Base class for Fortinet API interactions"""
    
    def __init__(self, host: str, username: str, password: str, api_token: str = ""):
        self.host = host
        self.username = username
        self.password = password
        self.api_token = api_token
        self.session = requests.Session()
        self.session.verify = False  # Disable SSL verification for lab environments
        
    def _get_headers(self) -> Dict[str, str]:
        """Get appropriate headers for API requests"""
        if self.api_token:
            return {"Authorization": f"Bearer {self.api_token}"}
        return {}
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Make API request with proper error handling"""
        url = f"https://{self.host}/api/v2/{endpoint}"
        headers = self._get_headers()
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, headers=headers, timeout=30)
            elif method.upper() == "POST":
                response = self.session.post(url, headers=headers, json=data, timeout=30)
            elif method.upper() == "PUT":
                response = self.session.put(url, headers=headers, json=data, timeout=30)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, headers=headers, timeout=30)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise Exception(f"API request failed: {str(e)}")

class FortigateManager(FortinetAPI):
    """Fortigate-specific API manager"""
    
    def login(self) -> bool:
        """Login to Fortigate and get session"""
        if self.api_token:
            return True  # API token authentication
            
        try:
            login_data = {
                "username": self.username,
                "secretkey": self.password,
                "ajax": 1
            }
            url = f"https://{self.host}/logincheck"
            response = self.session.post(url, data=login_data, timeout=30)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False
    
    def get_system_status(self) -> Dict:
        """Get system status information"""
        return self._make_request("GET", "monitor/system/status")
    
    def get_interface_stats(self) -> Dict:
        """Get interface statistics"""
        return self._make_request("GET", "monitor/system/interface")
    
    def get_firewall_policies(self) -> Dict:
        """Get firewall policies"""
        return self._make_request("GET", "cmdb/firewall/policy")
    
    def get_vpn_status(self) -> Dict:
        """Get VPN tunnel status"""
        return self._make_request("GET", "monitor/vpn/ssl")
    
    def get_system_resources(self) -> Dict:
        """Get system resource usage"""
        return self._make_request("GET", "monitor/system/resource-usage")

class FortiCLI:
    """Fortigate CLI manager using SSH"""
    
    def __init__(self, host: str, username: str, password: str):
        self.host = host
        self.username = username
        self.password = password
        
    def execute_command(self, command: str) -> str:
        """Execute CLI command via SSH"""
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.host, username=self.username, password=self.password)
            
            stdin, stdout, stderr = ssh.exec_command(command)
            result = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            
            ssh.close()
            
            if error:
                raise Exception(f"CLI Error: {error}")
                
            return result
            
        except Exception as e:
            logger.error(f"CLI command failed: {e}")
            raise Exception(f"CLI command failed: {str(e)}")

# Initialize managers
fortigate = FortigateManager(FORTIGATE_HOST, FORTIGATE_USERNAME, FORTIGATE_PASSWORD, FORTIGATE_API_TOKEN)
forticli = FortiCLI(FORTIGATE_HOST, FORTIGATE_USERNAME, FORTIGATE_PASSWORD)

# Resources - Application-controlled context
@mcp.resource("fortinet://system/status")
async def get_system_status_resource() -> str:
    """Get Fortigate system status information"""
    try:
        status = fortigate.get_system_status()
        return json.dumps(status, indent=2)
    except Exception as e:
        return f"Error getting system status: {str(e)}"

@mcp.resource("fortinet://firewall/policies")
async def get_firewall_policies_resource() -> str:
    """Get current firewall policies"""
    try:
        policies = fortigate.get_firewall_policies()
        return json.dumps(policies, indent=2)
    except Exception as e:
        return f"Error getting firewall policies: {str(e)}"

@mcp.resource("fortinet://interfaces/stats")
async def get_interface_stats_resource() -> str:
    """Get network interface statistics"""
    try:
        stats = fortigate.get_interface_stats()
        return json.dumps(stats, indent=2)
    except Exception as e:
        return f"Error getting interface stats: {str(e)}"

@mcp.resource("fortinet://vpn/status")
async def get_vpn_status_resource() -> str:
    """Get VPN tunnel status"""
    try:
        vpn_status = fortigate.get_vpn_status()
        return json.dumps(vpn_status, indent=2)
    except Exception as e:
        return f"Error getting VPN status: {str(e)}"

@mcp.resource("fortinet://system/resources")
async def get_system_resources_resource() -> str:
    """Get system resource usage"""
    try:
        resources = fortigate.get_system_resources()
        return json.dumps(resources, indent=2)
    except Exception as e:
        return f"Error getting system resources: {str(e)}"

# Tools - Model-controlled actions
@mcp.tool()
async def execute_cli_command(command: str) -> str:
    """Execute a CLI command on the Fortigate device.
    
    Args:
        command: The CLI command to execute (e.g., "get system status", "diagnose sys top")
    """
    if not command.strip():
        return "Error: Command cannot be empty"
    
    # Basic security check - only allow read-only commands
    dangerous_commands = ['execute', 'delete', 'purge', 'clear', 'reset', 'format']
    if any(dangerous in command.lower() for dangerous in dangerous_commands):
        return "Error: Potentially dangerous command blocked. Only read-only commands are allowed."
    
    try:
        result = forticli.execute_command(command)
        return f"Command: {command}\n\nOutput:\n{result}"
    except Exception as e:
        return f"Error executing command '{command}': {str(e)}"

@mcp.tool()
async def get_device_info() -> str:
    """Get comprehensive device information including status, version, and hardware details."""
    try:
        if not fortigate.login():
            return "Error: Failed to authenticate with Fortigate"
            
        status = fortigate.get_system_status()
        return f"Device Information:\n{json.dumps(status, indent=2)}"
    except Exception as e:
        return f"Error getting device info: {str(e)}"

@mcp.tool()
async def check_policy_by_source(source_ip: str) -> str:
    """Check which firewall policies apply to a specific source IP address.
    
    Args:
        source_ip: The source IP address to check policies for
    """
    try:
        policies = fortigate.get_firewall_policies()
        matching_policies = []
        
        for policy in policies.get('results', []):
            srcaddr = policy.get('srcaddr', [])
            for addr in srcaddr:
                if source_ip in str(addr):
                    matching_policies.append(policy)
        
        if matching_policies:
            return f"Policies matching source IP {source_ip}:\n{json.dumps(matching_policies, indent=2)}"
        else:
            return f"No policies found matching source IP {source_ip}"
            
    except Exception as e:
        return f"Error checking policies for {source_ip}: {str(e)}"

@mcp.tool()
async def analyze_interface_utilization() -> str:
    """Analyze network interface utilization and identify potential bottlenecks."""
    try:
        stats = fortigate.get_interface_stats()
        analysis = []
        
        for interface in stats.get('results', []):
            name = interface.get('name', 'unknown')
            rx_bytes = interface.get('rx_bytes', 0)
            tx_bytes = interface.get('tx_bytes', 0)
            rx_packets = interface.get('rx_packets', 0)
            tx_packets = interface.get('tx_packets', 0)
            
            analysis.append({
                'interface': name,
                'rx_bytes': rx_bytes,
                'tx_bytes': tx_bytes,
                'rx_packets': rx_packets,
                'tx_packets': tx_packets,
                'total_bytes': rx_bytes + tx_bytes
            })
        
        # Sort by total bytes to identify busiest interfaces
        analysis.sort(key=lambda x: x['total_bytes'], reverse=True)
        
        return f"Interface Utilization Analysis:\n{json.dumps(analysis, indent=2)}"
        
    except Exception as e:
        return f"Error analyzing interface utilization: {str(e)}"

@mcp.tool()
async def get_security_events() -> str:
    """Get recent security events and logs (simulated - would integrate with FortiAnalyzer in production)."""
    try:
        # This would typically query FortiAnalyzer
        # For now, we'll return system logs from CLI
        result = forticli.execute_command("execute log filter category 0")
        return f"Recent Security Events:\n{result}"
    except Exception as e:
        return f"Error getting security events: {str(e)}"

@mcp.tool()
async def backup_configuration() -> str:
    """Create a backup of the current Fortigate configuration."""
    try:
        # Get configuration via API
        config = fortigate._make_request("GET", "cmdb/system/global")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # In a real implementation, you might save this to a file or external storage
        return f"Configuration backup created at {timestamp}:\n{json.dumps(config, indent=2)}"
        
    except Exception as e:
        return f"Error creating configuration backup: {str(e)}"

@mcp.tool()
async def diagnose_connectivity(destination: str) -> str:
    """Diagnose network connectivity to a destination.
    
    Args:
        destination: Target IP address or hostname to test connectivity
    """
    try:
        # Execute ping command
        ping_result = forticli.execute_command(f"execute ping {destination}")
        
        # Execute traceroute
        trace_result = forticli.execute_command(f"execute traceroute {destination}")
        
        return f"Connectivity Diagnosis for {destination}:\n\nPing Results:\n{ping_result}\n\nTraceroute Results:\n{trace_result}"
        
    except Exception as e:
        return f"Error diagnosing connectivity to {destination}: {str(e)}"

# Prompts - User-controlled templates
@mcp.prompt()
async def security_audit_prompt(device_name: str = "Fortigate") -> str:
    """Generate a comprehensive security audit checklist for Fortinet devices.
    
    Args:
        device_name: Name of the device to audit
    """
    return f"""
Please perform a comprehensive security audit of the {device_name} device. Review the following areas:

1. **System Configuration**
   - Check system status and version information
   - Verify administrative access controls
   - Review logging and monitoring settings

2. **Firewall Policies**
   - Analyze firewall rule effectiveness
   - Identify unused or overly permissive rules
   - Check for policy optimization opportunities

3. **Network Security**
   - Review VPN configuration and status
   - Check interface security settings
   - Analyze traffic patterns for anomalies

4. **Performance Analysis**
   - Monitor system resource utilization
   - Identify network bottlenecks
   - Review interface utilization patterns

5. **Security Events**
   - Review recent security logs
   - Identify potential threats or attacks
   - Check for configuration drift

Please provide specific recommendations for any issues found and suggest remediation steps.
"""

@mcp.prompt()
async def incident_response_prompt(incident_type: str, severity: str = "medium") -> str:
    """Generate an incident response workflow for network security incidents.
    
    Args:
        incident_type: Type of security incident
        severity: Incident severity level (low, medium, high, critical)
    """
    return f"""
INCIDENT RESPONSE WORKFLOW
Incident Type: {incident_type}
Severity Level: {severity}

**IMMEDIATE ACTIONS:**
1. Assess the scope and impact of the {incident_type}
2. Gather relevant system and security logs
3. Document initial findings and timeline

**INVESTIGATION STEPS:**
1. Check firewall policies for related traffic
2. Review interface statistics for unusual patterns
3. Analyze recent configuration changes
4. Examine VPN connections and user activity

**CONTAINMENT MEASURES:**
1. Identify affected network segments
2. Consider temporary policy adjustments if needed
3. Monitor for lateral movement or escalation

**RECOVERY ACTIONS:**
1. Implement necessary security controls
2. Update firewall rules if required
3. Verify system integrity and performance

**POST-INCIDENT:**
1. Document lessons learned
2. Update security procedures
3. Plan preventive measures

Please execute this workflow step by step, using the available Fortinet tools to gather information and implement necessary actions.
"""

@mcp.prompt()
async def policy_review_prompt(policy_scope: str = "all") -> str:
    """Generate a firewall policy review and optimization workflow.
    
    Args:
        policy_scope: Scope of policies to review (all, specific_service, by_zone)
    """
    return f"""
FIREWALL POLICY REVIEW WORKFLOW
Scope: {policy_scope}

**POLICY ANALYSIS:**
1. Retrieve current firewall policies
2. Identify policy utilization patterns
3. Check for redundant or conflicting rules
4. Review policy ordering and efficiency

**SECURITY ASSESSMENT:**
1. Verify least privilege principles
2. Check for overly permissive rules
3. Validate source and destination definitions
4. Review service and port configurations

**OPTIMIZATION OPPORTUNITIES:**
1. Consolidate similar policies where appropriate
2. Optimize policy order for performance
3. Remove unused or obsolete rules
4. Update object definitions for clarity

**COMPLIANCE CHECK:**
1. Verify policies align with security standards
2. Check documentation and naming conventions
3. Validate change management procedures
4. Ensure proper logging and monitoring

**RECOMMENDATIONS:**
Based on the analysis, provide specific recommendations for:
- Policy consolidation opportunities
- Security improvements
- Performance optimizations
- Compliance enhancements

Please execute this review systematically and provide detailed findings with actionable recommendations.
"""

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')