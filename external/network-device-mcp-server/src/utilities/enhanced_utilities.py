"""
Enhanced Network Utilities Integration
Integrates 30+ utility scripts with voice commands and REST API endpoints
"""

import os
import sys
import json
import subprocess
import importlib.util
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import asyncio
import logging

logger = logging.getLogger(__name__)

class EnhancedNetworkUtilities:
    """
    Enhanced Network Utilities manager with voice command integration
    Provides access to 30+ specialized network tools via voice and API
    """
    
    def __init__(self, utilities_path: str = None):
        """Initialize Enhanced Network Utilities"""
        # Set paths
        if utilities_path is None:
            self.utilities_path = Path(__file__).parent / "scripts"
        else:
            self.utilities_path = Path(utilities_path)
        
        # Add to Python path
        if str(self.utilities_path) not in sys.path:
            sys.path.append(str(self.utilities_path))
        
        # Initialize utility registry
        self.utilities_registry = self._build_utilities_registry()
        
        logger.info(f"✅ Enhanced Network Utilities initialized with {len(self.utilities_registry)} tools")
    
    def _build_utilities_registry(self) -> Dict[str, Dict[str, Any]]:
        """Build registry of available utilities"""
        registry = {
            # Network Discovery Tools
            "device_discovery": {
                "script": "device_discovery_tool_enhanced.py",
                "description": "Enhanced network device discovery with multi-protocol support",
                "voice_commands": ["discover devices", "scan network", "find devices"],
                "category": "discovery",
                "parameters": ["network", "timeout", "protocols"],
                "endpoint": "/api/utilities/device-discovery"
            },
            "unified_snmp_discovery": {
                "script": "unified_snmp_discovery.py", 
                "description": "Unified SNMP discovery across all restaurant brands",
                "voice_commands": ["snmp discovery", "scan snmp", "discover snmp devices"],
                "category": "discovery",
                "parameters": ["brand", "community", "timeout"],
                "endpoint": "/api/utilities/snmp-discovery"
            },
            "snmp_checker": {
                "script": "snmp_checker.py",
                "description": "SNMP connectivity and information checker", 
                "voice_commands": ["check snmp", "snmp status", "verify snmp"],
                "category": "monitoring",
                "parameters": ["ip", "community", "version"],
                "endpoint": "/api/utilities/snmp-check"
            },
            
            # SSL/Security Tools
            "ssl_diagnostics": {
                "script": "ssl_diagnostic_tool.py",
                "description": "Comprehensive SSL certificate diagnostics",
                "voice_commands": ["check ssl", "ssl diagnostics", "verify certificates"],
                "category": "security",
                "parameters": ["host", "port", "timeout"],
                "endpoint": "/api/utilities/ssl-diagnostics"
            },
            "ssl_universal_fix": {
                "script": "ssl_universal_fix_v2.py",
                "description": "Universal SSL troubleshooting and fixes",
                "voice_commands": ["fix ssl", "ssl troubleshoot", "repair ssl"],
                "category": "security", 
                "parameters": ["target", "fix_mode", "backup"],
                "endpoint": "/api/utilities/ssl-fix"
            },
            "create_cert_bundle": {
                "script": "create_cert_bundle.py",
                "description": "Create SSL certificate bundles for corporate environments",
                "voice_commands": ["create cert bundle", "bundle certificates", "make cert bundle"],
                "category": "security",
                "parameters": ["certs_path", "output_path"],
                "endpoint": "/api/utilities/cert-bundle"
            },
            "zscaler_ssl_fix": {
                "script": "zscaler_ssl_fix.py",
                "description": "Zscaler-specific SSL configuration fixes",
                "voice_commands": ["fix zscaler ssl", "zscaler ssl repair"],
                "category": "security",
                "parameters": ["config_type", "backup_existing"],
                "endpoint": "/api/utilities/zscaler-ssl-fix"
            },
            
            # FortiNet Management Tools  
            "fortigate_config_diff": {
                "script": "fortigate_config_diff.py",
                "description": "Compare FortiGate device configurations",
                "voice_commands": ["compare configs", "config diff", "fortigate diff"],
                "category": "fortigate",
                "parameters": ["device1", "device2", "output_format"],
                "endpoint": "/api/utilities/config-diff"
            },
            "fortigate_utils": {
                "script": "fortigate_utils.py", 
                "description": "FortiGate utility functions and helpers",
                "voice_commands": ["fortigate utils", "fortigate tools"],
                "category": "fortigate",
                "parameters": ["operation", "device", "parameters"],
                "endpoint": "/api/utilities/fortigate-utils"
            },
            "fortimanager_api": {
                "script": "fortimanager_api_solution.py",
                "description": "FortiManager API wrapper and operations",
                "voice_commands": ["fortimanager api", "manage fortimanager"],
                "category": "fortigate",
                "parameters": ["operation", "adom", "device"],
                "endpoint": "/api/utilities/fortimanager-api"
            },
            "fortimanager_deploy": {
                "script": "fortimanager_deploy.py",
                "description": "FortiManager deployment automation",
                "voice_commands": ["deploy fortimanager", "fortimanager deployment"],
                "category": "fortigate", 
                "parameters": ["deployment_type", "target_devices"],
                "endpoint": "/api/utilities/fortimanager-deploy"
            },
            
            # Threat Intelligence & Security
            "fortiguard_scraper": {
                "script": "fortiguard_ssl_fixed_scraper.py",
                "description": "FortiGuard threat intelligence scraper",
                "voice_commands": ["scrape fortiguard", "get threat intel", "fortiguard data"],
                "category": "threat_intel",
                "parameters": ["query_type", "time_range"],
                "endpoint": "/api/utilities/fortiguard-scraper"
            },
            "fortiguard_psirt": {
                "script": "fortiguard_psirt.py",
                "description": "FortiGuard PSIRT security advisory tracker",
                "voice_commands": ["check psirt", "security advisories", "fortiguard psirt"],
                "category": "threat_intel",
                "parameters": ["advisory_type", "severity"],
                "endpoint": "/api/utilities/psirt-tracker"
            },
            
            # Network Analysis Tools
            "topology_visualizer": {
                "script": "topology_visualizer.py",
                "description": "Network topology visualization generator",
                "voice_commands": ["visualize topology", "create topology", "network map"],
                "category": "analysis",
                "parameters": ["input_data", "output_format", "layout"],
                "endpoint": "/api/utilities/topology-visualizer"
            },
            "ip_lookup": {
                "script": "ip_lookup.py",
                "description": "IP address lookup and geolocation",
                "voice_commands": ["lookup ip", "ip info", "check ip address"],
                "category": "analysis",
                "parameters": ["ip_address", "detail_level"],
                "endpoint": "/api/utilities/ip-lookup"
            },
            "mac_lookup": {
                "script": "final_mac_lookup_solution.py",
                "description": "MAC address lookup and vendor identification",
                "voice_commands": ["lookup mac", "mac address info", "check mac"],
                "category": "analysis", 
                "parameters": ["mac_address", "lookup_type"],
                "endpoint": "/api/utilities/mac-lookup"
            },
            
            # Data Processing Tools
            "csv_converter": {
                "script": "csv_converter.py",
                "description": "Advanced CSV data conversion and processing",
                "voice_commands": ["convert csv", "process data", "transform csv"],
                "category": "data",
                "parameters": ["input_file", "output_format", "transformations"],
                "endpoint": "/api/utilities/csv-converter"
            },
            "json_formatter": {
                "script": "json_to_readable.py",
                "description": "JSON data formatting and readability enhancement",
                "voice_commands": ["format json", "readable json", "clean json"],
                "category": "data",
                "parameters": ["input_json", "format_type"],
                "endpoint": "/api/utilities/json-formatter"
            },
            "parse_fortinet_data": {
                "script": "parse_fortinet_data.py",
                "description": "FortiNet data parsing and extraction",
                "voice_commands": ["parse fortinet data", "extract fortinet info"],
                "category": "data",
                "parameters": ["data_source", "output_format"],
                "endpoint": "/api/utilities/fortinet-parser"
            },
            
            # Monitoring & Reporting
            "isp_report_generator": {
                "script": "isp_report_generator.py", 
                "description": "ISP connectivity and performance reports",
                "voice_commands": ["generate isp report", "isp analysis", "connectivity report"],
                "category": "reporting",
                "parameters": ["report_type", "time_period"],
                "endpoint": "/api/utilities/isp-report"
            },
            "splunk_monitor": {
                "script": "splunk_monitor.py",
                "description": "Splunk monitoring and log analysis",
                "voice_commands": ["monitor splunk", "splunk status", "check splunk"],
                "category": "monitoring",
                "parameters": ["query", "time_range"],
                "endpoint": "/api/utilities/splunk-monitor"
            },
            
            # Meraki Tools
            "meraki_collector": {
                "script": "meraki_device_collector.py",
                "description": "Meraki device data collection and analysis",
                "voice_commands": ["collect meraki data", "meraki devices", "scan meraki"],
                "category": "meraki",
                "parameters": ["org_id", "network_id", "device_types"],
                "endpoint": "/api/utilities/meraki-collector"
            }
        }
        
        # Verify which scripts are actually available
        available_registry = {}
        for name, config in registry.items():
            script_path = self.utilities_path / config["script"]
            if script_path.exists():
                config["available"] = True
                config["script_path"] = str(script_path)
                available_registry[name] = config
            else:
                logger.warning(f"Utility script not found: {config['script']}")
        
        logger.info(f"Found {len(available_registry)} available utilities out of {len(registry)} defined")
        return available_registry
    
    def get_available_utilities(self) -> Dict[str, Any]:
        """Get all available utilities with metadata"""
        return {
            "success": True,
            "utilities_count": len(self.utilities_registry),
            "utilities": self.utilities_registry,
            "categories": self.get_categories(),
            "voice_commands": self.get_all_voice_commands()
        }
    
    def get_categories(self) -> Dict[str, List[str]]:
        """Get utilities organized by category"""
        categories = {}
        for name, config in self.utilities_registry.items():
            category = config.get("category", "misc")
            if category not in categories:
                categories[category] = []
            categories[category].append(name)
        return categories
    
    def get_all_voice_commands(self) -> Dict[str, str]:
        """Get all voice commands mapped to utility names"""
        voice_commands = {}
        for name, config in self.utilities_registry.items():
            for command in config.get("voice_commands", []):
                voice_commands[command] = name
        return voice_commands
    
    async def execute_utility(self, utility_name: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a utility by name with parameters"""
        if utility_name not in self.utilities_registry:
            return {
                "success": False,
                "error": f"Utility '{utility_name}' not found"
            }
        
        config = self.utilities_registry[utility_name]
        script_path = config["script_path"]
        
        try:
            # Build command arguments
            cmd = [sys.executable, script_path]
            
            # Add parameters if provided
            if parameters:
                for key, value in parameters.items():
                    cmd.extend([f"--{key}", str(value)])
            
            # Execute with timeout
            timeout = parameters.get("timeout", 300) if parameters else 300
            
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.utilities_path)
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(result.communicate(), timeout=timeout)
            except asyncio.TimeoutError:
                result.kill()
                return {
                    "success": False,
                    "error": f"Utility '{utility_name}' timed out after {timeout} seconds"
                }
            
            # Parse results
            if result.returncode == 0:
                return {
                    "success": True,
                    "utility": utility_name,
                    "output": stdout.decode('utf-8'),
                    "execution_time": datetime.now().isoformat(),
                    "parameters": parameters or {}
                }
            else:
                return {
                    "success": False,
                    "utility": utility_name,
                    "error": stderr.decode('utf-8'),
                    "return_code": result.returncode
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to execute utility '{utility_name}': {str(e)}"
            }
    
    async def execute_voice_command(self, voice_input: str) -> Dict[str, Any]:
        """Execute utility based on voice command"""
        voice_commands = self.get_all_voice_commands()
        
        # Simple command matching (can be enhanced with NLP)
        matched_utility = None
        for command, utility in voice_commands.items():
            if command.lower() in voice_input.lower():
                matched_utility = utility
                break
        
        if not matched_utility:
            return {
                "success": False,
                "error": "Voice command not recognized",
                "available_commands": list(voice_commands.keys())
            }
        
        # Execute the matched utility
        return await self.execute_utility(matched_utility)
    
    def get_utility_info(self, utility_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific utility"""
        if utility_name not in self.utilities_registry:
            return {
                "success": False,
                "error": f"Utility '{utility_name}' not found"
            }
        
        config = self.utilities_registry[utility_name]
        return {
            "success": True,
            "name": utility_name,
            "description": config["description"],
            "category": config["category"],
            "voice_commands": config["voice_commands"],
            "parameters": config["parameters"],
            "endpoint": config["endpoint"],
            "script": config["script"],
            "available": config["available"]
        }
    
    # Specialized utility functions with enhanced functionality
    
    async def run_network_discovery(self, network: str, protocols: List[str] = None) -> Dict[str, Any]:
        """Enhanced network discovery with multiple protocols"""
        parameters = {"network": network}
        if protocols:
            parameters["protocols"] = ",".join(protocols)
        
        return await self.execute_utility("device_discovery", parameters)
    
    async def run_ssl_diagnostics(self, host: str, port: int = 443, check_chain: bool = True) -> Dict[str, Any]:
        """Enhanced SSL diagnostics with chain validation"""
        parameters = {
            "host": host,
            "port": port,
            "check_chain": "true" if check_chain else "false"
        }
        
        return await self.execute_utility("ssl_diagnostics", parameters)
    
    async def compare_fortigate_configs(self, device1: str, device2: str, sections: List[str] = None) -> Dict[str, Any]:
        """Enhanced FortiGate configuration comparison"""
        parameters = {
            "device1": device1,
            "device2": device2
        }
        if sections:
            parameters["sections"] = ",".join(sections)
        
        return await self.execute_utility("fortigate_config_diff", parameters)
    
    async def run_threat_intel_scan(self, query_type: str, indicators: List[str]) -> Dict[str, Any]:
        """Run threat intelligence scanning"""
        parameters = {
            "query_type": query_type,
            "indicators": ",".join(indicators)
        }
        
        return await self.execute_utility("fortiguard_scraper", parameters)
    
    async def generate_topology_visualization(self, data_source: str, layout: str = "auto") -> Dict[str, Any]:
        """Generate network topology visualization"""
        parameters = {
            "input_data": data_source,
            "layout": layout,
            "output_format": "json"
        }
        
        return await self.execute_utility("topology_visualizer", parameters)
    
    async def batch_ip_lookup(self, ip_addresses: List[str]) -> Dict[str, Any]:
        """Batch IP address lookup and analysis"""
        results = []
        for ip in ip_addresses:
            result = await self.execute_utility("ip_lookup", {"ip_address": ip})
            results.append(result)
        
        return {
            "success": True,
            "batch_lookup": True,
            "total_ips": len(ip_addresses),
            "results": results,
            "execution_time": datetime.now().isoformat()
        }
    
    def get_voice_help(self) -> Dict[str, Any]:
        """Get voice command help organized by category"""
        categories = self.get_categories()
        voice_help = {}
        
        for category, utilities in categories.items():
            voice_help[category] = []
            for utility in utilities:
                config = self.utilities_registry[utility]
                voice_help[category].extend(config["voice_commands"])
        
        return {
            "success": True,
            "voice_commands_by_category": voice_help,
            "total_commands": sum(len(commands) for commands in voice_help.values()),
            "usage_examples": [
                "Say: 'discover devices on network 192.168.1.0/24'",
                "Say: 'check ssl for host 192.168.1.1'", 
                "Say: 'compare configs between device1 and device2'",
                "Say: 'scan network for snmp devices'",
                "Say: 'generate topology visualization'"
            ]
        }

# Global instance for easy access
enhanced_utilities = None

def get_enhanced_utilities() -> EnhancedNetworkUtilities:
    """Get global enhanced utilities instance"""
    global enhanced_utilities
    if enhanced_utilities is None:
        enhanced_utilities = EnhancedNetworkUtilities()
    return enhanced_utilities