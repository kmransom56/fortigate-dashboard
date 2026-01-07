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
        
        # Set up handlers
        self.setup_tools()
        self.setup_resources()
        self.setup_prompts()
    
    def setup_tools(self):
        """Register all available tools"""
        
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            tools = [
                Tool(
                    name="list_fortimanager_instances",
                    description="List all available FortiManager instances (Arbys, BWW, Sonic)",
                    inputSchema={"type": "object", "properties": {}}
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
                    name="get_network_infrastructure_summary",
                    description="Get comprehensive summary of all managed network infrastructure",
                    inputSchema={"type": "object", "properties": {}}
                ),
                Tool(
                    name="show_configuration_status",
                    description="Show current MCP server configuration status and debug information",
                    inputSchema={"type": "object", "properties": {}}
                )
            ]
            return tools
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
            """Handle all tool calls with proper routing"""
            try:
                if name == "list_fortimanager_instances":
                    return await self._list_fortimanager_instances(arguments)
                elif name == "get_fortimanager_devices":
                    return await self._get_fortimanager_devices(arguments)
                elif name == "get_network_infrastructure_summary":
                    return await self._get_network_infrastructure_summary(arguments)
                elif name == "show_configuration_status":
                    return await self._show_configuration_status(arguments)
                else:
                    return [TextContent(type="text", text=f"Unknown tool: {name}")]
            except Exception as e:
                logger.error(f"Error in tool {name}: {e}")
                return [TextContent(type="text", text=f"Error in {name}: {str(e)}")]
    
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
                    "description": fm.get("description", f"{fm['name']} FortiManager instance")
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