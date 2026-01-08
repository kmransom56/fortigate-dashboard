#!/usr/bin/env python3
"""
MCP Client for TUI Integration
Allows TUI to call MCP tools and integrate with AI tools
"""

import os
import json
import asyncio
import subprocess
from typing import Dict, Any, Optional, List
from pathlib import Path

class MCPClient:
    """Client to interact with MCP servers"""
    
    def __init__(self, mcp_script_path: str = None):
        """
        Initialize MCP client
        
        Args:
            mcp_script_path: Path to MCP server script (meraki-mcp-dynamic.py)
        """
        if mcp_script_path is None:
            # Default to dynamic MCP
            script_dir = Path(__file__).parent
            mcp_script_path = str(script_dir / "meraki-mcp-dynamic.py")
        
        self.mcp_script_path = mcp_script_path
        self.process = None
        self.tools_cache = {}
        
    async def start_server(self):
        """Start MCP server as subprocess"""
        # MCP servers communicate via stdio
        # For TUI integration, we'll call tools directly via Python imports
        pass
    
    def get_meraki_tools(self) -> Dict[str, Any]:
        """Get available Meraki MCP tools by importing the MCP module"""
        try:
            # Import the MCP server module to access its tools
            import sys
            import importlib.util
            
            spec = importlib.util.spec_from_file_location("meraki_mcp", self.mcp_script_path)
            if spec is None or spec.loader is None:
                return {}
            
            mcp_module = importlib.util.module_from_spec(spec)
            sys.modules["meraki_mcp"] = mcp_module
            spec.loader.exec_module(mcp_module)
            
            # Get the mcp server instance
            if hasattr(mcp_module, 'mcp'):
                mcp_server = mcp_module.mcp
                
                # Extract tools from the FastMCP server
                tools = {}
                if hasattr(mcp_server, '_tools'):
                    for tool_name, tool_info in mcp_server._tools.items():
                        tools[tool_name] = {
                            'name': tool_name,
                            'description': getattr(tool_info, 'description', ''),
                            'parameters': getattr(tool_info, 'parameters', {})
                        }
                
                return tools
        except Exception as e:
            print(f"Error loading MCP tools: {e}")
            return {}
        
        return {}
    
    def call_mcp_tool(self, tool_name: str, **kwargs) -> Any:
        """
        Call an MCP tool directly by importing and using the MCP module's internal functions
        
        Args:
            tool_name: Name of the tool to call
            **kwargs: Tool parameters
            
        Returns:
            Tool result
        """
        try:
            # Import MCP module directly
            import sys
            import importlib.util
            import asyncio
            
            spec = importlib.util.spec_from_file_location("meraki_mcp", self.mcp_script_path)
            if spec is None or spec.loader is None:
                return {"error": "Could not load MCP module"}
            
            mcp_module = importlib.util.module_from_spec(spec)
            sys.modules["meraki_mcp"] = mcp_module
            spec.loader.exec_module(mcp_module)
            
            # Get dashboard and internal functions
            if hasattr(mcp_module, 'dashboard'):
                dashboard = mcp_module.dashboard
                
                # Handle generic API caller
                if tool_name == "call_meraki_api":
                    section = kwargs.get('section')
                    method = kwargs.get('method')
                    parameters = kwargs.get('parameters', {})
                    
                    if section and method:
                        # Use the internal MCP function if available
                        if hasattr(mcp_module, '_call_meraki_method_internal'):
                            # Call the internal function directly (synchronous)
                            result = mcp_module._call_meraki_method_internal(section, method, parameters)
                            # Parse JSON string result
                            if isinstance(result, str):
                                try:
                                    return json.loads(result)
                                except:
                                    return result
                            return result
                        else:
                            # Fallback to direct dashboard call
                            return self._call_meraki_method(dashboard, section, method, parameters)
                
                # Handle pre-registered tools
                elif tool_name in ["getOrganizations", "getOrganizationNetworks", "getOrganizationDevices",
                                  "getNetworkClients", "getNetworkEvents"]:
                    # Call via internal method
                    if hasattr(mcp_module, '_call_meraki_method_internal'):
                        # Map tool names to sections/methods
                        tool_map = {
                            "getOrganizations": ("organizations", "getOrganizations", {}),
                            "getOrganizationNetworks": ("organizations", "getOrganizationNetworks", 
                                                       {"organizationId": kwargs.get('organizationId')}),
                            "getOrganizationDevices": ("organizations", "getOrganizationDevices",
                                                      {"organizationId": kwargs.get('organizationId')}),
                            "getNetworkClients": ("networks", "getNetworkClients",
                                                 {"networkId": kwargs.get('networkId'), 
                                                  "timespan": kwargs.get('timespan', 3600)}),
                            "getNetworkEvents": ("networks", "getNetworkEvents",
                                               {"networkId": kwargs.get('networkId'),
                                                "perPage": kwargs.get('perPage', 10)})
                        }
                        
                        if tool_name in tool_map:
                            section, method, params = tool_map[tool_name]
                            params.update({k: v for k, v in kwargs.items() if k not in params or params[k] is None})
                            result = mcp_module._call_meraki_method_internal(section, method, params)
                            if isinstance(result, str):
                                try:
                                    return json.loads(result)
                                except:
                                    return result
                            return result
                
                # Fallback: try direct dashboard method
                return self._call_dashboard_method(dashboard, tool_name, kwargs)
                
        except Exception as e:
            import traceback
            return {"error": str(e), "tool": tool_name, "traceback": traceback.format_exc()}
    
    def _call_meraki_method(self, dashboard, section: str, method: str, params: dict) -> Any:
        """Call a Meraki API method via dashboard"""
        try:
            if not hasattr(dashboard, section):
                return {"error": f"Section '{section}' not found"}
            
            section_obj = getattr(dashboard, section)
            if not hasattr(section_obj, method):
                return {"error": f"Method '{method}' not found in section '{section}'"}
            
            method_func = getattr(section_obj, method)
            result = method_func(**params)
            return result
            
        except Exception as e:
            return {"error": str(e), "section": section, "method": method}
    
    def _call_dashboard_method(self, dashboard, method_name: str, kwargs: dict) -> Any:
        """Call a dashboard method directly"""
        try:
            # Try common patterns
            if 'organizationId' in kwargs or 'orgId' in kwargs:
                org_id = kwargs.get('organizationId') or kwargs.get('orgId')
                if 'getOrganizations' in method_name:
                    return dashboard.organizations.getOrganizations()
                elif 'getOrganizationNetworks' in method_name:
                    return dashboard.organizations.getOrganizationNetworks(org_id)
                elif 'getOrganizationDevices' in method_name:
                    return dashboard.organizations.getOrganizationDevices(org_id)
            
            # Generic fallback - try to find method
            for section_name in ['organizations', 'networks', 'devices', 'wireless', 'switch', 'appliance']:
                if hasattr(dashboard, section_name):
                    section = getattr(dashboard, section_name)
                    if hasattr(section, method_name):
                        method = getattr(section, method_name)
                        return method(**kwargs)
            
            return {"error": f"Method '{method_name}' not found"}
            
        except Exception as e:
            return {"error": str(e), "method": method_name}


class MerakiMCPWrapper:
    """
    Wrapper that provides MCP tool interface for TUI
    Uses MCP client to call tools, with fallback to direct API
    """
    
    def __init__(self, use_mcp: bool = True):
        """
        Initialize wrapper
        
        Args:
            use_mcp: Whether to use MCP tools (True) or direct API (False)
        """
        self.use_mcp = use_mcp
        self.mcp_client = None
        self.dashboard = None
        
        if use_mcp:
            try:
                self.mcp_client = MCPClient()
            except Exception as e:
                print(f"Warning: Could not initialize MCP client: {e}")
                print("Falling back to direct API calls")
                self.use_mcp = False
        
        if not self.use_mcp:
            # Fallback to direct Meraki API
            import meraki
            from dotenv import load_dotenv
            load_dotenv()
            
            api_key = os.getenv("MERAKI_API_KEY")
            self.dashboard = meraki.DashboardAPI(
                api_key=api_key,
                suppress_logging=True
            )
    
    def get_organizations(self) -> List[Dict]:
        """Get all organizations"""
        if self.use_mcp and self.mcp_client:
            result = self.mcp_client.call_mcp_tool("getOrganizations")
            # Handle different result types
            if isinstance(result, list):
                return result
            elif isinstance(result, dict):
                if 'error' in result:
                    # Error occurred, fall through to direct API
                    pass
                else:
                    # Single result or wrapped result
                    return [result] if result else []
            elif isinstance(result, str):
                try:
                    parsed = json.loads(result)
                    return parsed if isinstance(parsed, list) else [parsed] if parsed else []
                except:
                    pass
        
        # Fallback to direct API
        if self.dashboard:
            return self.dashboard.organizations.getOrganizations()
        return []
    
    def get_organization_networks(self, org_id: str) -> List[Dict]:
        """Get networks for an organization"""
        if self.use_mcp and self.mcp_client:
            result = self.mcp_client.call_mcp_tool("getOrganizationNetworks", organizationId=org_id)
            # Handle different result types
            if isinstance(result, list):
                return result
            elif isinstance(result, dict):
                if 'error' not in result:
                    return [result] if result else []
            elif isinstance(result, str):
                try:
                    parsed = json.loads(result)
                    return parsed if isinstance(parsed, list) else [parsed] if parsed else []
                except:
                    pass
        
        # Fallback to direct API
        if self.dashboard:
            return self.dashboard.organizations.getOrganizationNetworks(org_id)
        return []
    
    def get_organization_devices(self, org_id: str) -> List[Dict]:
        """Get devices for an organization"""
        if self.use_mcp and self.mcp_client:
            result = self.mcp_client.call_mcp_tool("getOrganizationDevices", organizationId=org_id)
            # Handle different result types
            if isinstance(result, list):
                return result
            elif isinstance(result, dict):
                if 'error' not in result:
                    return [result] if result else []
            elif isinstance(result, str):
                try:
                    parsed = json.loads(result)
                    return parsed if isinstance(parsed, list) else [parsed] if parsed else []
                except:
                    pass
        
        # Fallback to direct API
        if self.dashboard:
            return self.dashboard.organizations.getOrganizationDevices(org_id)
        return []
    
    def get_network_clients(self, network_id: str, timespan: int = 3600) -> List[Dict]:
        """Get clients for a network"""
        if self.use_mcp and self.mcp_client:
            result = self.mcp_client.call_mcp_tool("getNetworkClients", networkId=network_id, timespan=timespan)
            # Handle different result types
            if isinstance(result, list):
                return result
            elif isinstance(result, dict):
                if 'error' not in result:
                    return [result] if result else []
            elif isinstance(result, str):
                try:
                    parsed = json.loads(result)
                    return parsed if isinstance(parsed, list) else [parsed] if parsed else []
                except:
                    pass
        
        # Fallback to direct API
        if self.dashboard:
            return self.dashboard.networks.getNetworkClients(network_id, timespan=timespan)
        return []
    
    def get_network_events(self, network_id: str, per_page: int = 10) -> Dict:
        """Get events for a network"""
        if self.use_mcp and self.mcp_client:
            result = self.mcp_client.call_mcp_tool("getNetworkEvents", networkId=network_id, perPage=per_page)
            # Handle different result types
            if isinstance(result, dict):
                return result
            elif isinstance(result, str):
                try:
                    return json.loads(result)
                except:
                    pass
        
        # Fallback to direct API
        if self.dashboard:
            return self.dashboard.networks.getNetworkEvents(network_id, perPage=per_page)
        return {}
    
    def call_meraki_api(self, section: str, method: str, parameters: dict) -> Any:
        """
        Generic method to call any Meraki API via MCP
        
        Args:
            section: API section (organizations, networks, etc.)
            method: Method name
            parameters: Method parameters
            
        Returns:
            API result
        """
        if self.use_mcp and self.mcp_client:
            result = self.mcp_client.call_mcp_tool(
                "call_meraki_api",
                section=section,
                method=method,
                parameters=parameters
            )
            if not (isinstance(result, dict) and 'error' in result):
                return result
        
        # Fallback to direct API
        if self.dashboard:
            try:
                section_obj = getattr(self.dashboard, section)
                method_func = getattr(section_obj, method)
                return method_func(**parameters)
            except Exception as e:
                return {"error": str(e)}
        
        return {"error": "No API connection available"}
