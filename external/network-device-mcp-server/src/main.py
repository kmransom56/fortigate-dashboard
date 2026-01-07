#!/usr/bin/env python3
"""
Network Device Management MCP Server with absolute path resolution
Supports FortiManager, FortiGate, and Cisco Meraki platforms
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional, Sequence
from pathlib import Path

# Establish absolute paths immediately
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.resolve()

# Add current directory to path for imports
sys.path.insert(0, str(SCRIPT_DIR))

import httpx
from mcp import types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest, 
    ListToolsResult,
    ListResourcesRequest,
    ListResourcesResult,
    ListPromptsRequest,
    ListPromptsResult,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource
)

# Import our modules
from config import get_config
from platforms.fortigate import FortiGateManager
from platforms.fortimanager import FortiManagerManager  
from platforms.meraki import MerakiManager

# Set up logging to stderr (not stdout for MCP)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)

logger = logging.getLogger(__name__)

# Log absolute path information for debugging
logger.info(f"MCP Server starting from: {SCRIPT_DIR}")
logger.info(f"Project root: {PROJECT_ROOT}")
logger.info(f"Current working directory: {Path.cwd()}")

class NetworkDeviceMCPServer:
    def __init__(self):
        self.server = Server("network-device-mcp")
        
        # Load configuration with absolute path resolution
        logger.info("Loading configuration...")
        self.config = get_config()
        
        # Log configuration debug info
        debug_info = self.config.debug_info()
        logger.info(f"Configuration debug info: {debug_info}")
        
        # Initialize platform managers
        self.fortigate = FortiGateManager()
        self.fortimanager = FortiManagerManager()
        self.meraki = MerakiManager()
        
        # Set up tool handlers
        self.setup_tools()
        self.setup_resources()
        self.setup_prompts()
    
    def setup_tools(self):
        """Register all available tools - FIXED VERSION"""
        
        # Register the tool list handler
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            tools = [
                # FortiManager Tools
                Tool(
                    name="list_fortimanager_instances",
                    description="List all available FortiManager instances (Arbys, BWW, Sonic)",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="get_fortimanager_devices",
                    description="Get managed devices from a FortiManager instance",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "fortimanager_name": {"type": "string", "description": "FortiManager name (Arbys, BWW, or Sonic)"},
                            "adom": {"type": "string", "default": "root", "description": "Administrative domain"}
                        },
                        "required": ["fortimanager_name"]
                    }
                ),
                Tool(
                    name="get_policy_packages",
                    description="Get policy packages from a FortiManager instance",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "fortimanager_name": {"type": "string", "description": "FortiManager name (Arbys, BWW, or Sonic)"},
                            "adom": {"type": "string", "default": "root"}
                        },
                        "required": ["fortimanager_name"]
                    }
                ),
                Tool(
                    name="install_policy_package",
                    description="Install policy package to devices via FortiManager",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "fortimanager_name": {"type": "string", "description": "FortiManager name (Arbys, BWW, or Sonic)"},
                            "adom": {"type": "string", "default": "root"},
                            "package": {"type": "string", "description": "Policy package name"},
                            "devices": {"type": "array", "items": {"type": "string"}, "description": "Target device names"}
                        },
                        "required": ["fortimanager_name", "package"]
                    }
                ),
                
                # Infrastructure Summary Tools
                Tool(
                    name="get_network_infrastructure_summary",
                    description="Get comprehensive summary of all managed network infrastructure",
                    inputSchema={"type": "object", "properties": {}}
                ),
                Tool(
                    name="show_configuration_status",
                    description="Show current MCP server configuration status and debug information",
                    inputSchema={"type": "object", "properties": {}}
                ),
                
                # Enhanced Security Analysis Tools for Message Limit Efficiency
                Tool(
                    name="get_security_event_summary",
                    description="Get condensed security event summary for a specific device or store",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "device_name": {"type": "string", "description": "Device name (e.g., IBR-BWW-00155)"},
                            "timeframe": {"type": "string", "default": "1h", "description": "Time period (1h, 24h, 7d)"},
                            "event_types": {"type": "array", "items": {"type": "string"}, "default": ["webfilter", "ips", "antivirus", "application"], "description": "Security event types to include"},
                            "top_count": {"type": "integer", "default": 10, "description": "Number of top events to return"}
                        },
                        "required": ["device_name"]
                    }
                ),
                Tool(
                    name="analyze_url_blocking_patterns",
                    description="Analyze URL blocking patterns and generate executive summary for any restaurant brand",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "brand": {"type": "string", "description": "Restaurant brand (BWW, ARBYS, SONIC)", "enum": ["BWW", "ARBYS", "SONIC"]},
                            "store_id": {"type": "string", "description": "Store identifier (e.g., 155)"},
                            "analysis_period": {"type": "string", "default": "24h", "description": "Analysis time period"},
                            "export_report": {"type": "boolean", "default": true, "description": "Export detailed report to file"}
                        },
                        "required": ["brand", "store_id"]
                    }
                ),
                Tool(
                    name="get_store_security_health",
                    description="Get overall security health status for any restaurant brand store",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "brand": {"type": "string", "description": "Restaurant brand (BWW, ARBYS, SONIC)", "enum": ["BWW", "ARBYS", "SONIC"]},
                            "store_id": {"type": "string", "description": "Store number (e.g., 155)"},
                            "include_recommendations": {"type": "boolean", "default": true, "description": "Include security recommendations"}
                        },
                        "required": ["brand", "store_id"]
                    }
                ),
                
                # Brand Management Tools
                Tool(
                    name="list_supported_brands",
                    description="List all supported restaurant brands and their device naming patterns",
                    inputSchema={"type": "object", "properties": {}}
                ),
                Tool(
                    name="get_brand_store_summary", 
                    description="Get summary of all stores for a specific brand",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "brand": {"type": "string", "description": "Restaurant brand (BWW, ARBYS, SONIC)", "enum": ["BWW", "ARBYS", "SONIC"]}
                        },
                        "required": ["brand"]
                    }
                ),
                
                # Advanced Network Tools
                Tool(
                    name="get_policy_package_rules",
                    description="Get the specific rules from a policy package on a FortiManager instance",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "fortimanager_name": {"type": "string", "description": "FortiManager name (Arbys, BWW, or Sonic)"},
                            "adom": {"type": "string", "default": "root", "description": "Administrative domain"},
                            "package_name": {"type": "string", "description": "The name of the policy package"}
                        },
                        "required": ["fortimanager_name", "package_name"]
                    }
                ),
                Tool(
                    name="get_webfilter_profile",
                    description="Get details of a web filter profile from a FortiGate, including URL filters",
                    inputSchema={
                        "type": "object", 
                        "properties": {
                            "fortigate_name": {"type": "string", "description": "The name of the target FortiGate device"},
                            "profile_name": {"type": "string", "description": "The name of the web filter profile"}
                        },
                        "required": ["fortigate_name", "profile_name"]
                    }
                ),
                Tool(
                    name="get_device_routing_table",
                    description="Get the active routing table from a network device",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "device_name": {"type": "string", "description": "The name of the target device"},
                            "device_platform": {"type": "string", "enum": ["fortigate", "meraki"], "description": "The platform of the device"}
                        },
                        "required": ["device_name", "device_platform"]
                    }
                ),
                Tool(
                    name="get_device_logs",
                    description="Search for traffic, event, or threat logs on a device. All filters are optional",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "device_name": {"type": "string", "description": "The name of the target device"},
                            "log_type": {"type": "string", "enum": ["traffic", "event", "utm"], "default": "traffic", "description": "Type of logs to retrieve"},
                            "duration_minutes": {"type": "integer", "default": 60, "description": "How many minutes back to search"},
                            "max_results": {"type": "integer", "default": 100, "description": "Maximum number of log entries"},
                            "filter_string": {"type": "string", "description": "A free-text filter string, e.g., 'srcip=10.1.1.5 and dstport=443'"}
                        },
                        "required": ["device_name"]
                    }
                ),
                Tool(
                    name="execute_connectivity_test",
                    description="Executes a ping or traceroute from a network device to a target destination",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "device_name": {"type": "string", "description": "The device to run the test from"},
                            "test_type": {"type": "string", "enum": ["ping", "traceroute"], "default": "ping", "description": "Type of connectivity test"},
                            "destination": {"type": "string", "description": "The IP address or hostname to test connectivity to"}
                        },
                        "required": ["device_name", "destination"]
                    }
                )
            ]
            
            # Add FortiGate tools if devices are configured
            if self.config.fortigate_devices:
                tools.extend([
                    Tool(
                        name="list_fortigate_devices",
                        description="List all available FortiGate devices",
                        inputSchema={"type": "object", "properties": {}}
                    ),
                    Tool(
                        name="get_fortigate_system_status",
                        description="Get system status from a FortiGate device",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "fortigate_name": {"type": "string", "description": "FortiGate device name"}
                            },
                            "required": ["fortigate_name"]
                        }
                    )
                ])
            
            # Add Meraki tools if configured
            if self.config.has_meraki_config():
                tools.extend([
                    Tool(
                        name="get_meraki_organizations",
                        description="Get Meraki organizations",
                        inputSchema={"type": "object", "properties": {}}
                    ),
                    Tool(
                        name="get_meraki_networks",
                        description="Get networks in the configured Meraki organization",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "org_id": {"type": "string", "description": "Organization ID (optional)"}
                            }
                        }
                    ),
                    Tool(
                        name="get_meraki_devices",
                        description="Get devices in a Meraki network",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "network_id": {"type": "string", "description": "Network ID"}
                            },
                            "required": ["network_id"]
                        }
                    )
                ])
            
            return tools
        
        # FIXED: Single call_tool handler that dispatches based on tool name
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
            """Handle all tool calls with proper routing - FIXED SIGNATURE"""
            try:
                # Route to the appropriate handler based on tool name
                if name == "list_fortimanager_instances":
                    return await list_fortimanager_instances_impl()
                elif name == "get_fortimanager_devices":
                    return await get_fortimanager_devices_impl(arguments)
                elif name == "get_policy_packages":
                    return await get_policy_packages_impl(arguments)
                elif name == "install_policy_package":
                    return await install_policy_package_impl(arguments)
                elif name == "get_network_infrastructure_summary":
                    return await get_network_infrastructure_summary_impl()
                elif name == "show_configuration_status":
                    return await show_configuration_status_impl()
                elif name == "list_fortigate_devices":
                    return await list_fortigate_devices_impl()
                elif name == "get_fortigate_system_status":
                    return await get_fortigate_system_status_impl(arguments)
                elif name == "get_meraki_organizations":
                    return await get_meraki_organizations_impl()
                elif name == "get_meraki_networks":
                    return await get_meraki_networks_impl(arguments)
                elif name == "get_meraki_devices":
                    return await get_meraki_devices_impl(arguments)
                elif name == "get_security_event_summary":
                    return await get_security_event_summary_impl(arguments)
                elif name == "analyze_url_blocking_patterns":
                    return await analyze_url_blocking_patterns_impl(arguments)
                elif name == "get_store_security_health":
                    return await get_store_security_health_impl(arguments)
                elif name == "list_supported_brands":
                    return await list_supported_brands_impl()
                elif name == "get_brand_store_summary":
                    return await get_brand_store_summary_impl(arguments)
                elif name == "get_policy_package_rules":
                    return await get_policy_package_rules_impl(arguments)
                elif name == "get_webfilter_profile":
                    return await get_webfilter_profile_impl(arguments)
                elif name == "get_device_routing_table":
                    return await get_device_routing_table_impl(arguments)
                elif name == "get_device_logs":
                    return await get_device_logs_impl(arguments)
                elif name == "execute_connectivity_test":
                    return await execute_connectivity_test_impl(arguments)
                else:
                    return [TextContent(type="text", text=f"Unknown tool: {name}")]
            except Exception as e:
                logger.error(f"Error in tool {name}: {e}")
                return [TextContent(type="text", text=f"Error in {name}: {str(e)}")]
        
        # FIXED: Local function implementations (not class methods)
        async def list_fortimanager_instances_impl() -> list[TextContent]:
            """List all available FortiManager instances - FIXED"""
            try:
                instances = []
                for fm in self.config.fortimanager_instances:
                    instances.append({
                        "name": fm["name"],
                        "host": fm["host"],
                        "description": fm.get("description", "")
                    })
                
                response = {
                    "fortimanager_instances": instances,
                    "total_count": len(instances),
                    "configuration_source": "Local .env file" if self.config.env_file.exists() else "System environment variables"
                }
                
                return [TextContent(type="text", text=json.dumps(response, indent=2))]
            except Exception as e:
                logger.error(f"Error listing FortiManager instances: {e}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]

        async def get_fortimanager_devices_impl(arguments: dict) -> list[TextContent]:
            """Get managed devices from a FortiManager instance - FIXED"""
            try:
                fm_name = arguments.get("fortimanager_name", "")
                adom = arguments.get("adom", "root")
                
                if not fm_name:
                    available = self.config.list_fortimanager_names()
                    return [TextContent(
                        type="text", 
                        text=f"Error: fortimanager_name required. Available: {', '.join(available)}"
                    )]
                
                fm_config = self.config.get_fortimanager_by_name(fm_name)
                if not fm_config:
                    return [TextContent(type="text", text=f"Error: FortiManager '{fm_name}' not found")]
                
                result = await self.fortimanager.get_managed_devices(
                    fm_config["host"], fm_config["username"], fm_config["password"], adom
                )
                
                response = {
                    "fortimanager": fm_name,
                    "host": fm_config["host"],
                    "adom": adom,
                    "device_count": len(result),
                    "devices": result
                }
                
                return [TextContent(type="text", text=json.dumps(response, indent=2))]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]

        async def get_policy_packages_impl(arguments: dict) -> list[TextContent]:
            """Get policy packages from a FortiManager instance - FIXED"""
            try:
                fm_name = arguments.get("fortimanager_name", "")
                adom = arguments.get("adom", "root")
                
                if not fm_name:
                    available = self.config.list_fortimanager_names()
                    return [TextContent(
                        type="text", 
                        text=f"Error: fortimanager_name required. Available: {', '.join(available)}"
                    )]
                
                fm_config = self.config.get_fortimanager_by_name(fm_name)
                if not fm_config:
                    return [TextContent(type="text", text=f"Error: FortiManager '{fm_name}' not found")]
                
                result = await self.fortimanager.get_policy_packages(
                    fm_config["host"], fm_config["username"], fm_config["password"], adom
                )
                
                response = {
                    "fortimanager": fm_name,
                    "host": fm_config["host"],
                    "adom": adom,
                    "policy_packages": result
                }
                
                return [TextContent(type="text", text=json.dumps(response, indent=2))]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]

        async def install_policy_package_impl(arguments: dict) -> list[TextContent]:
            """Install policy package to devices via FortiManager - FIXED"""
            try:
                fm_name = arguments.get("fortimanager_name", "")
                adom = arguments.get("adom", "root")
                package = arguments.get("package", "")
                devices = arguments.get("devices", [])
                
                if not fm_name:
                    available = self.config.list_fortimanager_names()
                    return [TextContent(
                        type="text", 
                        text=f"Error: fortimanager_name required. Available: {', '.join(available)}"
                    )]
                
                if not package:
                    return [TextContent(type="text", text="Error: package name required")]
                
                fm_config = self.config.get_fortimanager_by_name(fm_name)
                if not fm_config:
                    return [TextContent(type="text", text=f"Error: FortiManager '{fm_name}' not found")]
                
                result = await self.fortimanager.install_policy_package(
                    fm_config["host"], fm_config["username"], fm_config["password"], adom, package, devices
                )
                
                response = {
                    "fortimanager": fm_name,
                    "adom": adom,
                    "package": package,
                    "target_devices": devices,
                    "result": result
                }
                
                return [TextContent(type="text", text=json.dumps(response, indent=2))]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]

        async def get_network_infrastructure_summary_impl() -> list[TextContent]:
            """Get comprehensive summary of all managed network infrastructure - FIXED"""
            try:
                summary = {
                    "infrastructure_overview": {
                        "fortimanager_instances": len(self.config.fortimanager_instances),
                        "fortigate_devices": len(self.config.fortigate_devices),
                        "meraki_configured": self.config.has_meraki_config(),
                        "configuration_source": "GitHub Actions" if self.config.is_github_deployment() else "Local .env file"
                    },
                    "fortimanager_instances": [],
                    "configuration_debug": self.config.debug_info(),
                    "validation_status": self.config.validate_config()
                }
                
                # Add FortiManager instance details
                for fm in self.config.fortimanager_instances:
                    summary["fortimanager_instances"].append({
                        "name": fm["name"],
                        "host": fm["host"],
                        "status": "configured"
                    })
                
                return [TextContent(type="text", text=json.dumps(summary, indent=2))]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]

        async def show_configuration_status_impl() -> list[TextContent]:
            """Show current configuration status and debug information - FIXED"""
            try:
                debug_info = self.config.debug_info()
                validation = self.config.validate_config()
                
                status = {
                    "server_info": {
                        "script_directory": debug_info["script_dir"],
                        "project_root": debug_info["project_root"],
                        "current_working_directory": debug_info["current_working_dir"],
                        "env_file_location": debug_info["env_file"],
                        "env_file_exists": debug_info["env_file_exists"]
                    },
                    "configuration": {
                        "fortimanager_instances": [
                            {"name": fm["name"], "host": fm["host"]} 
                            for fm in self.config.fortimanager_instances
                        ],
                        "fortigate_devices": [
                            {"name": fg["name"], "host": fg["host"]} 
                            for fg in self.config.fortigate_devices
                        ],
                        "meraki_configured": self.config.has_meraki_config(),
                        "is_github_deployment": debug_info["is_github_deployment"]
                    },
                    "paths": {
                        "backup_path": debug_info["backup_path"],
                        "report_path": debug_info["report_path"]
                    },
                    "validation_results": validation
                }
                
                return [TextContent(type="text", text=json.dumps(status, indent=2))]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        
        # Placeholder implementations for other tools (to be expanded)
        async def list_fortigate_devices_impl() -> list[TextContent]:
            devices = [{"name": fg["name"], "host": fg["host"]} for fg in self.config.fortigate_devices]
            response = {"fortigate_devices": devices, "total_count": len(devices)}
            return [TextContent(type="text", text=json.dumps(response, indent=2))]
        
        async def get_fortigate_system_status_impl(arguments: dict) -> list[TextContent]:
            return [TextContent(type="text", text="FortiGate system status - Not implemented yet")]
        
        async def get_meraki_organizations_impl() -> list[TextContent]:
            return [TextContent(type="text", text="Meraki organizations - Not implemented yet")]
        
        async def get_meraki_networks_impl(arguments: dict) -> list[TextContent]:
            return [TextContent(type="text", text="Meraki networks - Not implemented yet")]
        
        async def get_meraki_devices_impl(arguments: dict) -> list[TextContent]:
            return [TextContent(type="text", text="Meraki devices - Not implemented yet")]
        
        async def get_security_event_summary_impl(arguments: dict) -> list[TextContent]:
            return [TextContent(type="text", text="Security event summary - Not implemented yet")]
        
        async def analyze_url_blocking_patterns_impl(arguments: dict) -> list[TextContent]:
            return [TextContent(type="text", text="URL blocking patterns analysis - Not implemented yet")]
        
        async def get_store_security_health_impl(arguments: dict) -> list[TextContent]:
            return [TextContent(type="text", text="Store security health - Not implemented yet")]
        
        async def list_supported_brands_impl() -> list[TextContent]:
            return [TextContent(type="text", text="Supported brands - Not implemented yet")]
        
        async def get_brand_store_summary_impl(arguments: dict) -> list[TextContent]:
            return [TextContent(type="text", text="Brand store summary - Not implemented yet")]
        
        async def get_policy_package_rules_impl(arguments: dict) -> list[TextContent]:
            return [TextContent(type="text", text="Policy package rules - Not implemented yet")]
        
        async def get_webfilter_profile_impl(arguments: dict) -> list[TextContent]:
            return [TextContent(type="text", text="Web filter profile - Not implemented yet")]
        
        async def get_device_routing_table_impl(arguments: dict) -> list[TextContent]:
            return [TextContent(type="text", text="Device routing table - Not implemented yet")]
        
        async def get_device_logs_impl(arguments: dict) -> list[TextContent]:
            return [TextContent(type="text", text="Device logs - Not implemented yet")]
        
        async def execute_connectivity_test_impl(arguments: dict) -> list[TextContent]:
            return [TextContent(type="text", text="Connectivity test - Not implemented yet")]
    
    def setup_resources(self):
        """Register resource handlers to satisfy MCP protocol requirements"""
        
        @self.server.list_resources()
        async def list_resources() -> list:
            """Return available resources - required by MCP protocol"""
            return []
    
    def setup_prompts(self):
        """Register prompt handlers to satisfy MCP protocol requirements"""
        
        @self.server.list_prompts()
        async def list_prompts() -> list:
            """Return available prompts - required by MCP protocol"""
            return []
    
    # Tool implementation methods
    async def _list_fortimanager_instances(self, arguments: dict) -> list[TextContent]:
        """List all available FortiManager instances"""
        try:
            instances = []
            for fm in self.config.fortimanager_instances:
                instances.append({
                    "name": fm["name"],
                    "host": fm["host"],
                    "description": fm.get("description", "")
                })
            
            response = {
                "fortimanager_instances": instances,
                "total_count": len(instances),
                "configuration_source": "Local .env file" if self.config.env_file.exists() else "System environment variables"
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(response, indent=2)
            )]
        except Exception as e:
            logger.error(f"Error listing FortiManager instances: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    async def _get_fortimanager_devices(self, arguments: dict) -> list[TextContent]:
        """Get managed devices from a FortiManager instance"""
        try:
            fm_name = arguments.get("fortimanager_name", "")
            adom = arguments.get("adom", "root")
            
            if not fm_name:
                available = self.config.list_fortimanager_names()
                return [TextContent(
                    type="text", 
                    text=f"Error: fortimanager_name required. Available: {', '.join(available)}"
                )]
            
            fm_config = self.config.get_fortimanager_by_name(fm_name)
            if not fm_config:
                return [TextContent(type="text", text=f"Error: FortiManager '{fm_name}' not found")]
            
            result = await self.fortimanager.get_managed_devices(
                fm_config["host"], fm_config["username"], fm_config["password"], adom
            )
            
            response = {
                "fortimanager": fm_name,
                "host": fm_config["host"],
                "adom": adom,
                "device_count": len(result),
                "devices": result
            }
            
            return [TextContent(type="text", text=json.dumps(response, indent=2))]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    async def _get_policy_packages(self, arguments: dict) -> list[TextContent]:
        """Get policy packages from a FortiManager instance"""
        try:
            fm_name = arguments.get("fortimanager_name", "")
            adom = arguments.get("adom", "root")
            
            if not fm_name:
                available = self.config.list_fortimanager_names()
                return [TextContent(
                    type="text", 
                    text=f"Error: fortimanager_name required. Available: {', '.join(available)}"
                )]
            
            fm_config = self.config.get_fortimanager_by_name(fm_name)
            if not fm_config:
                return [TextContent(type="text", text=f"Error: FortiManager '{fm_name}' not found")]
            
            result = await self.fortimanager.get_policy_packages(
                fm_config["host"], fm_config["username"], fm_config["password"], adom
            )
            
            response = {
                "fortimanager": fm_name,
                "host": fm_config["host"],
                "adom": adom,
                "policy_packages": result
            }
            
            return [TextContent(type="text", text=json.dumps(response, indent=2))]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    async def _install_policy_package(self, arguments: dict) -> list[TextContent]:
        """Install policy package to devices via FortiManager"""
        try:
            fm_name = arguments.get("fortimanager_name", "")
            adom = arguments.get("adom", "root")
            package = arguments.get("package", "")
            devices = arguments.get("devices", [])
            
            if not fm_name:
                available = self.config.list_fortimanager_names()
                return [TextContent(
                    type="text", 
                    text=f"Error: fortimanager_name required. Available: {', '.join(available)}"
                )]
            
            if not package:
                return [TextContent(type="text", text="Error: package name required")]
            
            fm_config = self.config.get_fortimanager_by_name(fm_name)
            if not fm_config:
                return [TextContent(type="text", text=f"Error: FortiManager '{fm_name}' not found")]
            
            result = await self.fortimanager.install_policy_package(
                fm_config["host"], fm_config["username"], fm_config["password"], adom, package, devices
            )
            
            response = {
                "fortimanager": fm_name,
                "adom": adom,
                "package": package,
                "target_devices": devices,
                "result": result
            }
            
            return [TextContent(type="text", text=json.dumps(response, indent=2))]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    async def _show_configuration_status(self, arguments: dict) -> list[TextContent]:
        """Show current configuration status and debug information"""
        try:
            debug_info = self.config.debug_info()
            validation = self.config.validate_config()
            
            status = {
                "server_info": {
                    "script_directory": debug_info["script_dir"],
                    "project_root": debug_info["project_root"],
                    "current_working_directory": debug_info["current_working_dir"],
                    "env_file_location": debug_info["env_file"],
                    "env_file_exists": debug_info["env_file_exists"]
                },
                "configuration": {
                    "fortimanager_instances": [
                        {"name": fm["name"], "host": fm["host"]} 
                        for fm in self.config.fortimanager_instances
                    ],
                    "fortigate_devices": [
                        {"name": fg["name"], "host": fg["host"]} 
                        for fg in self.config.fortigate_devices
                    ],
                    "meraki_configured": self.config.has_meraki_config(),
                    "is_github_deployment": debug_info["is_github_deployment"]
                },
                "paths": {
                    "backup_path": debug_info["backup_path"],
                    "report_path": debug_info["report_path"]
                },
                "validation_results": validation
            }
            
            return [TextContent(type="text", text=json.dumps(status, indent=2))]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    async def _get_network_infrastructure_summary(self, arguments: dict) -> list[TextContent]:
        """Get comprehensive summary of all managed network infrastructure"""
        try:
            summary = {
                "infrastructure_overview": {
                    "fortimanager_instances": len(self.config.fortimanager_instances),
                    "fortigate_devices": len(self.config.fortigate_devices),
                    "meraki_configured": self.config.has_meraki_config(),
                    "configuration_source": "GitHub Actions" if self.config.is_github_deployment() else "Local .env file"
                },
                "fortimanager_instances": [],
                "configuration_debug": self.config.debug_info(),
                "validation_status": self.config.validate_config()
            }
            
            # Add FortiManager instance details
            for fm in self.config.fortimanager_instances:
                summary["fortimanager_instances"].append({
                    "name": fm["name"],
                    "host": fm["host"],
                    "status": "configured"
                })
            
            return [TextContent(type="text", text=json.dumps(summary, indent=2))]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    # Additional tool methods (FortiGate, Meraki) would go here
    async def _list_fortigate_devices(self, arguments: dict) -> list[TextContent]:
        """List all available FortiGate devices"""
        try:
            devices = [{"name": fg["name"], "host": fg["host"]} for fg in self.config.fortigate_devices]
            response = {"fortigate_devices": devices, "total_count": len(devices)}
            return [TextContent(type="text", text=json.dumps(response, indent=2))]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    async def _get_fortigate_system_status(self, arguments: dict) -> list[TextContent]:
        """Get system status from a FortiGate device"""
        # Implementation would go here
        return [TextContent(type="text", text="FortiGate system status - Not implemented yet")]

    async def _get_meraki_organizations(self, arguments: dict) -> list[TextContent]:
        """Get Meraki organizations"""
        # Implementation would go here
        return [TextContent(type="text", text="Meraki organizations - Not implemented yet")]

    async def _get_meraki_networks(self, arguments: dict) -> list[TextContent]:
        """Get networks in the configured Meraki organization"""
        # Implementation would go here
        return [TextContent(type="text", text="Meraki networks - Not implemented yet")]

    async def _get_meraki_devices(self, arguments: dict) -> list[TextContent]:
        """Get devices in a Meraki network"""
        # Implementation would go here
        return [TextContent(type="text", text="Meraki devices - Not implemented yet")]

    async def _get_security_event_summary(self, arguments: dict) -> list[TextContent]:
        """Get condensed security event summary for a specific device or store"""
        try:
            device_name = arguments.get("device_name", "")
            timeframe = arguments.get("timeframe", "1h")
            event_types = arguments.get("event_types", ["webfilter", "ips", "antivirus", "application"])
            top_count = arguments.get("top_count", 10)
            
            if not device_name:
                return [TextContent(type="text", text="Error: device_name is required")]
            
            # Generate condensed summary optimized for message limits
            summary = {
                "device": device_name,
                "analysis_period": timeframe,
                "executive_summary": {
                    "total_events": 0,  # Would be populated from actual data
                    "critical_alerts": 0,
                    "blocked_threats": 0,
                    "policy_violations": 0
                },
                "top_security_events": [
                    # Would be populated from FortiGate/FortiAnalyzer data
                    {"type": "webfilter", "count": 0, "top_blocked_url": "example.com"},
                    {"type": "ips", "count": 0, "top_signature": "N/A"},
                    {"type": "antivirus", "count": 0, "top_malware": "N/A"}
                ],
                "recommendations": [
                    "Review top blocked URLs for potential policy adjustments",
                    "Investigate repeated IPS signatures for targeted attacks",
                    "Consider updating antivirus definitions if outdated"
                ],
                "detailed_report_path": f"{self.config.report_path}/{device_name}_security_analysis_{timeframe}.json" if self.config.report_path else None
            }
            
            return [TextContent(type="text", text=json.dumps(summary, indent=2))]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    async def _analyze_url_blocking_patterns(self, arguments: dict) -> list[TextContent]:
        """Analyze URL blocking patterns and generate executive summary for any brand"""
        try:
            brand = arguments.get("brand", "")
            store_id = arguments.get("store_id", "")
            analysis_period = arguments.get("analysis_period", "24h")
            export_report = arguments.get("export_report", True)
            
            if not brand:
                return [TextContent(type="text", text="Error: brand is required (BWW, ARBYS, SONIC)")]
            if not store_id:
                return [TextContent(type="text", text="Error: store_id is required")]
            
            # Build device name using brand-aware logic
            device_name = self.config.build_device_name(brand, store_id)
            brand_info = self.config.get_brand_info(brand)
            
            # Generate URL blocking analysis optimized for message limits
            analysis = {
                "store_analysis": {
                    "brand": brand_info.get("name", brand),
                    "brand_code": brand,
                    "store_id": store_id,
                    "device_name": device_name,
                    "fortimanager": brand_info.get("fortimanager", brand),
                    "analysis_period": analysis_period,
                    "timestamp": "2024-01-01T00:00:00Z"  # Would be current timestamp
                },
                "blocking_summary": {
                    "total_blocked_urls": 0,  # Would be populated from actual data
                    "unique_domains": 0,
                    "repeat_violations": 0,
                    "policy_categories": {
                        "social_media": 0,
                        "streaming": 0,
                        "gaming": 0,
                        "malicious": 0,
                        "adult_content": 0
                    }
                },
                "top_blocked_patterns": [
                    # Would be populated from FortiGate logs
                    {"domain": "example.com", "category": "social_media", "block_count": 0},
                    {"domain": "streaming-site.com", "category": "streaming", "block_count": 0}
                ],
                "user_behavior_insights": [
                    "Peak blocking times: 12:00-13:00 (lunch break)",
                    "Most violations: Social media during business hours",
                    "Potential policy review needed for streaming services"
                ],
                "next_steps": [
                    f"Review detailed logs in FortiManager for {device_name}",
                    "Consider employee training on acceptable use policy",
                    "Evaluate if current blocking categories are appropriate"
                ]
            }
            
            if export_report and self.config.report_path:
                report_file = self.config.report_path / f"store_{store_id}_url_blocking_{analysis_period}.json"
                try:
                    with open(report_file, 'w') as f:
                        json.dump(analysis, f, indent=2)
                    analysis["detailed_report_exported"] = str(report_file)
                except Exception as e:
                    analysis["export_error"] = f"Failed to export report: {str(e)}"
            
            return [TextContent(type="text", text=json.dumps(analysis, indent=2))]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    async def _get_store_security_health(self, arguments: dict) -> list[TextContent]:
        """Get overall security health status for any restaurant brand store"""
        try:
            brand = arguments.get("brand", "")
            store_id = arguments.get("store_id", "")
            include_recommendations = arguments.get("include_recommendations", True)
            
            if not brand:
                return [TextContent(type="text", text="Error: brand is required (BWW, ARBYS, SONIC)")]
            if not store_id:
                return [TextContent(type="text", text="Error: store_id is required")]
            
            # Build device name using brand-aware logic
            device_name = self.config.build_device_name(brand, store_id)
            brand_info = self.config.get_brand_info(brand)
            
            # Generate security health assessment optimized for message limits
            health_status = {
                "store_security_health": {
                    "brand": brand_info.get("name", brand),
                    "brand_code": brand,
                    "store_id": store_id,
                    "device_name": device_name,
                    "fortimanager": brand_info.get("fortimanager", brand),
                    "overall_status": "HEALTHY",  # Would be calculated from actual data
                    "security_score": 85,  # Out of 100
                    "last_assessment": "2024-01-01T00:00:00Z"
                },
                "security_metrics": {
                    "firewall_policies": {"status": "ACTIVE", "last_update": "2024-01-01"},
                    "antivirus_status": {"status": "UP_TO_DATE", "last_scan": "2024-01-01"},
                    "ips_protection": {"status": "ENABLED", "signature_version": "current"},
                    "web_filtering": {"status": "ACTIVE", "policy": "BWW_Standard"},
                    "vpn_tunnels": {"status": "CONNECTED", "uptime": "99.9%"}
                },
                "recent_activity": {
                    "threats_blocked_24h": 0,  # Would be from actual data
                    "policy_violations_24h": 0,
                    "system_alerts": 0,
                    "configuration_changes": 0
                },
                "compliance_status": {
                    "pci_compliance": "COMPLIANT",
                    "security_policies": "APPLIED",
                    "backup_status": "CURRENT",
                    "monitoring": "ACTIVE"
                }
            }
            
            if include_recommendations:
                health_status["recommendations"] = [
                    "✅ Security posture is good for Store " + store_id,
                    "📊 Continue monitoring URL blocking patterns",
                    "🔍 Schedule quarterly security policy review",
                    "🛡️ Verify backup configurations are current"
                ]
            
            return [TextContent(type="text", text=json.dumps(health_status, indent=2))]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    async def _list_supported_brands(self, arguments: dict) -> list[TextContent]:
        """List all supported restaurant brands and their device naming patterns"""
        try:
            brands_info = self.config.get_brand_info()
            
            supported_brands = {
                "supported_restaurant_brands": [],
                "device_naming_patterns": {},
                "fortimanager_mapping": {}
            }
            
            for brand_code, brand_info in brands_info.items():
                supported_brands["supported_restaurant_brands"].append({
                    "brand_code": brand_code,
                    "name": brand_info["name"],
                    "description": brand_info["description"],
                    "device_prefix": brand_info["device_prefix"],
                    "fortimanager": brand_info["fortimanager"]
                })
                
                supported_brands["device_naming_patterns"][brand_code] = {
                    "format": f"{brand_info['device_prefix']}-{brand_info['store_format']}",
                    "example": f"{brand_info['device_prefix']}-{brand_info['store_format'].format(155)}"
                }
                
                supported_brands["fortimanager_mapping"][brand_code] = brand_info["fortimanager"]
            
            supported_brands["usage_examples"] = [
                "analyze_url_blocking_patterns brand=\"BWW\" store_id=\"155\"",
                "get_store_security_health brand=\"ARBYS\" store_id=\"1234\"",
                "get_security_event_summary device_name=\"IBR-SONIC-00789\""
            ]
            
            return [TextContent(type="text", text=json.dumps(supported_brands, indent=2))]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    async def _get_brand_store_summary(self, arguments: dict) -> list[TextContent]:
        """Get summary of all stores for a specific brand"""
        try:
            brand = arguments.get("brand", "")
            
            if not brand:
                return [TextContent(type="text", text="Error: brand is required (BWW, ARBYS, SONIC)")]
            
            brand_info = self.config.get_brand_info(brand)
            if not brand_info:
                return [TextContent(type="text", text=f"Error: Unsupported brand '{brand}'. Supported: BWW, ARBYS, SONIC")]
            
            # Get FortiManager for this brand
            fm_config = self.config.get_fortimanager_for_brand(brand)
            
            summary = {
                "brand_summary": {
                    "brand": brand_info["name"],
                    "brand_code": brand,
                    "device_prefix": brand_info["device_prefix"],
                    "fortimanager": brand_info["fortimanager"],
                    "fortimanager_configured": fm_config is not None
                },
                "infrastructure_status": {
                    "fortimanager_host": fm_config["host"] if fm_config else "Not configured",
                    "total_managed_devices": 0,  # Would be populated from FortiManager API
                    "online_devices": 0,
                    "offline_devices": 0,
                    "devices_needing_updates": 0
                },
                "security_overview": {
                    "last_policy_update": "2024-01-01T00:00:00Z",  # Would be from actual data
                    "active_security_policies": 0,
                    "recent_security_events": 0,
                    "compliance_status": "COMPLIANT"
                },
                "next_steps": [
                    f"Use get_fortimanager_devices fortimanager_name=\"{brand}\" to see all managed devices",
                    f"Use analyze_url_blocking_patterns brand=\"{brand}\" store_id=\"<store>\" for specific store analysis",
                    f"Use get_store_security_health brand=\"{brand}\" store_id=\"<store>\" for security assessment"
                ]
            }
            
            if not fm_config:
                summary["configuration_warning"] = f"FortiManager for {brand} is not configured. Check environment variables: FORTIMANAGER_{brand}_HOST, FORTIMANAGER_{brand}_USERNAME, FORTIMANAGER_{brand}_PASSWORD"
            
            return [TextContent(type="text", text=json.dumps(summary, indent=2))]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    # Advanced Network Tools Implementation
    async def _get_policy_package_rules(self, arguments: dict) -> list[TextContent]:
        """Get the specific rules from a policy package on a FortiManager instance"""
        try:
            fm_name = arguments.get("fortimanager_name", "")
            adom = arguments.get("adom", "root")
            package_name = arguments.get("package_name", "")
            
            if not fm_name or not package_name:
                return [TextContent(type="text", text="Error: fortimanager_name and package_name are required")]
            
            fm_config = self.config.get_fortimanager_by_name(fm_name)
            if not fm_config:
                return [TextContent(type="text", text=f"Error: FortiManager '{fm_name}' not found")]
            
            # This would call the actual FortiManager API to get policy rules
            # For now, returning structured placeholder data
            result = {
                "fortimanager": fm_name,
                "adom": adom,
                "package_name": package_name,
                "rules": [
                    {
                        "id": 1,
                        "name": "Allow_Internal_to_Internet",
                        "srcintf": ["internal"],
                        "dstintf": ["wan1"],
                        "srcaddr": ["all"],
                        "dstaddr": ["all"],
                        "service": ["HTTP", "HTTPS"],
                        "action": "accept",
                        "status": "enable"
                    },
                    {
                        "id": 2,
                        "name": "Block_Social_Media",
                        "srcintf": ["internal"],
                        "dstintf": ["wan1"],
                        "srcaddr": ["all"],
                        "dstaddr": ["Social_Media_FQDN"],
                        "service": ["all"],
                        "action": "deny",
                        "status": "enable"
                    }
                ],
                "note": "This is placeholder data. Actual implementation would call FortiManager API."
            }
            
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    async def _get_webfilter_profile(self, arguments: dict) -> list[TextContent]:
        """Get details of a web filter profile from a FortiGate, including URL filters"""
        try:
            fortigate_name = arguments.get("fortigate_name", "")
            profile_name = arguments.get("profile_name", "")
            
            if not fortigate_name or not profile_name:
                return [TextContent(type="text", text="Error: fortigate_name and profile_name are required")]
            
            # This would call the actual FortiGate API to get web filter profile
            # For now, returning structured placeholder data
            result = {
                "fortigate_device": fortigate_name,
                "profile_name": profile_name,
                "web_filter_settings": {
                    "status": "enable",
                    "safe_search": "enable",
                    "youtube_restrict": "moderate",
                    "log_all_url": "enable",
                    "categories": {
                        "social_networking": "block",
                        "streaming_media": "block",
                        "gaming": "block",
                        "malicious": "block",
                        "adult_content": "block",
                        "business": "allow",
                        "education": "allow"
                    }
                },
                "url_filters": [
                    {"url": "*.facebook.com", "action": "block", "status": "enable"},
                    {"url": "*.youtube.com", "action": "block", "status": "enable"},
                    {"url": "*.netflix.com", "action": "block", "status": "enable"}
                ],
                "ftgd_wf": {
                    "rating": "enable",
                    "options": ["error-allow", "http-err-detail"]
                },
                "note": "This is placeholder data. Actual implementation would call FortiGate API."
            }
            
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    async def _get_device_routing_table(self, arguments: dict) -> list[TextContent]:
        """Get the active routing table from a network device"""
        try:
            device_name = arguments.get("device_name", "")
            device_platform = arguments.get("device_platform", "")
            
            if not device_name or not device_platform:
                return [TextContent(type="text", text="Error: device_name and device_platform are required")]
            
            # This would call the actual device API to get routing table
            # For now, returning structured placeholder data
            if device_platform == "fortigate":
                result = {
                    "device": device_name,
                    "platform": device_platform,
                    "routing_table": [
                        {
                            "destination": "0.0.0.0/0",
                            "gateway": "192.168.1.1",
                            "interface": "wan1",
                            "distance": 10,
                            "metric": 0,
                            "uptime": "2d 14h 32m"
                        },
                        {
                            "destination": "192.168.10.0/24",
                            "gateway": "0.0.0.0",
                            "interface": "internal",
                            "distance": 0,
                            "metric": 0,
                            "uptime": "2d 14h 32m"
                        },
                        {
                            "destination": "172.16.0.0/16",
                            "gateway": "10.1.1.1",
                            "interface": "vpn_tunnel",
                            "distance": 20,
                            "metric": 100,
                            "uptime": "1d 8h 15m"
                        }
                    ]
                }
            else:
                result = {"error": f"Platform {device_platform} not yet implemented"}
            
            result["note"] = "This is placeholder data. Actual implementation would call device API."
            
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    async def _get_device_logs(self, arguments: dict) -> list[TextContent]:
        """Search for traffic, event, or threat logs on a device"""
        try:
            device_name = arguments.get("device_name", "")
            log_type = arguments.get("log_type", "traffic")
            duration_minutes = arguments.get("duration_minutes", 60)
            max_results = arguments.get("max_results", 100)
            filter_string = arguments.get("filter_string", "")
            
            if not device_name:
                return [TextContent(type="text", text="Error: device_name is required")]
            
            # This would call the actual device/FortiAnalyzer API to get logs
            # For now, returning structured placeholder data based on log type
            if log_type == "traffic":
                sample_logs = [
                    {
                        "timestamp": "2024-01-01 10:30:15",
                        "srcip": "192.168.10.50",
                        "dstip": "8.8.8.8",
                        "srcport": 54321,
                        "dstport": 53,
                        "proto": "UDP",
                        "action": "accept",
                        "service": "DNS",
                        "bytes_sent": 64,
                        "bytes_received": 128
                    },
                    {
                        "timestamp": "2024-01-01 10:30:12",
                        "srcip": "192.168.10.45",
                        "dstip": "facebook.com",
                        "srcport": 49234,
                        "dstport": 443,
                        "proto": "TCP",
                        "action": "deny",
                        "service": "HTTPS",
                        "reason": "Web filter block"
                    }
                ]
            elif log_type == "event":
                sample_logs = [
                    {
                        "timestamp": "2024-01-01 10:25:00",
                        "level": "warning",
                        "event": "Interface wan1 link down",
                        "source": "system"
                    },
                    {
                        "timestamp": "2024-01-01 10:25:30",
                        "level": "information",
                        "event": "Interface wan1 link up",
                        "source": "system"
                    }
                ]
            else:  # utm logs
                sample_logs = [
                    {
                        "timestamp": "2024-01-01 10:20:00",
                        "srcip": "192.168.10.33",
                        "dstip": "malicious-site.com",
                        "threat": "Malware.Win32.Generic",
                        "action": "blocked",
                        "severity": "high"
                    }
                ]
            
            result = {
                "device": device_name,
                "log_type": log_type,
                "duration_minutes": duration_minutes,
                "filter_applied": filter_string,
                "total_logs": len(sample_logs),
                "logs": sample_logs[:max_results],
                "note": "This is placeholder data. Actual implementation would call FortiGate/FortiAnalyzer API."
            }
            
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    async def _execute_connectivity_test(self, arguments: dict) -> list[TextContent]:
        """Execute a ping or traceroute from a network device to a target destination"""
        try:
            device_name = arguments.get("device_name", "")
            test_type = arguments.get("test_type", "ping")
            destination = arguments.get("destination", "")
            
            if not device_name or not destination:
                return [TextContent(type="text", text="Error: device_name and destination are required")]
            
            # This would call the actual device API or SSH to run diagnostics
            # For now, returning structured placeholder data
            if test_type == "ping":
                result = {
                    "device": device_name,
                    "test_type": "ping",
                    "destination": destination,
                    "results": {
                        "packets_sent": 5,
                        "packets_received": 5,
                        "packet_loss": "0%",
                        "min_rtt": "12.3ms",
                        "avg_rtt": "15.7ms",
                        "max_rtt": "21.2ms",
                        "status": "success"
                    },
                    "raw_output": f"PING {destination} (8.8.8.8): 56 data bytes\\n64 bytes from 8.8.8.8: icmp_seq=0 ttl=119 time=12.3 ms\\n64 bytes from 8.8.8.8: icmp_seq=1 ttl=119 time=15.7 ms\\n--- {destination} ping statistics ---\\n5 packets transmitted, 5 packets received, 0% packet loss"
                }
            else:  # traceroute
                result = {
                    "device": device_name,
                    "test_type": "traceroute",
                    "destination": destination,
                    "results": {
                        "hops": [
                            {"hop": 1, "ip": "192.168.1.1", "rtt1": "1.2ms", "rtt2": "1.1ms", "rtt3": "1.3ms"},
                            {"hop": 2, "ip": "10.0.0.1", "rtt1": "5.4ms", "rtt2": "5.2ms", "rtt3": "5.6ms"},
                            {"hop": 3, "ip": "8.8.8.8", "rtt1": "12.1ms", "rtt2": "11.9ms", "rtt3": "12.3ms"}
                        ],
                        "total_hops": 3,
                        "status": "success"
                    }
                }
            
            result["note"] = "This is placeholder data. Actual implementation would SSH or API call to device."
            
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

async def main():
    """Main execution function to run the MCP server with stdio transport."""
    # Log startup information
    logger.info("Starting Network Device MCP Server")
    logger.info(f"Python executable: {sys.executable}")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Script path: {SCRIPT_DIR}")
    logger.info(f"Project root: {PROJECT_ROOT}")
    
    try:
        network_server_instance = NetworkDeviceMCPServer()
        
        # Log successful initialization
        config_count = len(network_server_instance.config.fortimanager_instances)
        logger.info(f"MCP Server initialized with {config_count} FortiManager instances")
        
        # Start the server
        async with stdio_server() as (read_stream, write_stream):
            await network_server_instance.server.run(
                read_stream, 
                write_stream, 
                InitializationOptions(
                    server_name=network_server_instance.server.name,
                    server_version="1.0.0",
                    capabilities={}
                )
            )
            
    except Exception as e:
        logger.error(f"Failed to start MCP server: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server shut down by user.")
    except Exception as e:
        logger.error(f"A top-level error occurred: {e}", exc_info=True)