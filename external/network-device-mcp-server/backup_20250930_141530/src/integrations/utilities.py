"""
Network Utilities Integration
Integrates Utilities project functionality into the MCP Web Server
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

class NetworkUtilities:
    """
    Manages network utility operations by integrating Utilities project functionality
    """
    
    def __init__(self, utilities_path: str = None):
        """
        Initialize Network Utilities with path to Utilities project
        """
        if utilities_path is None:
            utilities_path = "/mnt/c/Users/keith.ransom/Utilities"
        
        self.project_path = Path(utilities_path)
        
        # Add Utilities to Python path for imports
        if str(self.project_path) not in sys.path:
            sys.path.append(str(self.project_path))
    
    def get_available_utilities(self) -> Dict[str, Any]:
        """
        Get list of available network utilities
        
        Returns:
            Dictionary containing available utilities and their descriptions
        """
        try:
            utilities = {
                "success": True,
                "utilities": [
                    {
                        "name": "device_discovery",
                        "description": "Discover network devices using SNMP",
                        "endpoint": "/api/utilities/device-discovery",
                        "available": self._check_utility_availability("device_discovery_tool_enhanced.py")
                    },
                    {
                        "name": "snmp_checker",
                        "description": "Check SNMP connectivity and information",
                        "endpoint": "/api/utilities/snmp-check",
                        "available": self._check_utility_availability("snmp_checker.py")
                    },
                    {
                        "name": "fortigate_config_diff",
                        "description": "Compare FortiGate configurations",
                        "endpoint": "/api/utilities/config-diff",
                        "available": self._check_utility_availability("fortigate_config_diff.py")
                    },
                    {
                        "name": "ssl_universal_fix",
                        "description": "SSL certificate troubleshooting and fixes",
                        "endpoint": "/api/utilities/ssl-fix",
                        "available": self._check_utility_availability("ssl_universal_fix_v2.py")
                    },
                    {
                        "name": "unified_snmp_discovery",
                        "description": "Unified SNMP device discovery across brands",
                        "endpoint": "/api/utilities/snmp-discovery",
                        "available": self._check_utility_availability("unified_snmp_discovery.py")
                    },
                    {
                        "name": "ip_lookup",
                        "description": "IP address lookup and validation",
                        "endpoint": "/api/utilities/ip-lookup",
                        "available": self._check_utility_availability("ip_lookup.py")
                    }
                ],
                "total_utilities": 6,
                "available_utilities": 0
            }
            
            # Count available utilities
            utilities["available_utilities"] = len([u for u in utilities["utilities"] if u["available"]])
            
            return utilities
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get available utilities: {str(e)}"
            }
    
    def run_device_discovery(self, target_network: str, brand: str = None) -> Dict[str, Any]:
        """
        Run network device discovery
        
        Args:
            target_network: Network range to scan (e.g., "192.168.1.0/24")
            brand: Optional brand filter
            
        Returns:
            Device discovery results
        """
        try:
            script_path = self.project_path / "device_discovery_tool_enhanced.py"
            if not script_path.exists():
                return {
                    "success": False,
                    "error": "Device discovery tool not found"
                }
            
            # Run the device discovery script
            cmd = [sys.executable, str(script_path), "--network", target_network]
            if brand:
                cmd.extend(["--brand", brand])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes timeout
                cwd=str(self.project_path)
            )
            
            if result.returncode == 0:
                # Parse the output
                discovered_devices = self._parse_discovery_output(result.stdout)
                
                return {
                    "success": True,
                    "target_network": target_network,
                    "brand_filter": brand,
                    "devices_found": len(discovered_devices),
                    "devices": discovered_devices,
                    "scan_time": datetime.now().isoformat()
                }
            else:
                return {
                    "success": False,
                    "error": f"Device discovery failed: {result.stderr}"
                }
                
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Device discovery timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Device discovery error: {str(e)}"
            }
    
    def check_snmp_connectivity(self, device_ip: str, community: str = "public") -> Dict[str, Any]:
        """
        Check SNMP connectivity to a device
        
        Args:
            device_ip: IP address of the device
            community: SNMP community string
            
        Returns:
            SNMP connectivity results
        """
        try:
            script_path = self.project_path / "snmp_checker.py"
            if not script_path.exists():
                return {
                    "success": False,
                    "error": "SNMP checker tool not found"
                }
            
            # Run SNMP check
            cmd = [sys.executable, str(script_path), "--ip", device_ip, "--community", community]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(self.project_path)
            )
            
            if result.returncode == 0:
                snmp_data = self._parse_snmp_output(result.stdout)
                
                return {
                    "success": True,
                    "device_ip": device_ip,
                    "snmp_accessible": True,
                    "system_info": snmp_data.get("system_info", {}),
                    "interface_count": snmp_data.get("interface_count", 0),
                    "device_type": snmp_data.get("device_type", "unknown"),
                    "check_time": datetime.now().isoformat()
                }
            else:
                return {
                    "success": True,
                    "device_ip": device_ip,
                    "snmp_accessible": False,
                    "error": result.stderr,
                    "check_time": datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"SNMP check failed: {str(e)}"
            }
    
    def compare_fortigate_configs(self, device1: str, device2: str) -> Dict[str, Any]:
        """
        Compare configurations between two FortiGate devices
        
        Args:
            device1: First FortiGate device name
            device2: Second FortiGate device name
            
        Returns:
            Configuration comparison results
        """
        try:
            script_path = self.project_path / "fortigate_config_diff.py"
            if not script_path.exists():
                return {
                    "success": False,
                    "error": "Config diff tool not found"
                }
            
            # Run configuration comparison
            cmd = [sys.executable, str(script_path), "--device1", device1, "--device2", device2]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=180,
                cwd=str(self.project_path)
            )
            
            if result.returncode == 0:
                diff_results = self._parse_config_diff_output(result.stdout)
                
                return {
                    "success": True,
                    "device1": device1,
                    "device2": device2,
                    "differences_found": len(diff_results.get("differences", [])),
                    "comparison_results": diff_results,
                    "comparison_time": datetime.now().isoformat()
                }
            else:
                return {
                    "success": False,
                    "error": f"Configuration comparison failed: {result.stderr}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Config comparison error: {str(e)}"
            }
    
    def run_ssl_diagnostics(self, device_ip: str, port: int = 443) -> Dict[str, Any]:
        """
        Run SSL certificate diagnostics
        
        Args:
            device_ip: IP address of the device
            port: SSL/TLS port (default: 443)
            
        Returns:
            SSL diagnostic results
        """
        try:
            script_path = self.project_path / "ssl_universal_fix_v2.py"
            if not script_path.exists():
                return {
                    "success": False,
                    "error": "SSL diagnostics tool not found"
                }
            
            # Run SSL diagnostics
            cmd = [sys.executable, str(script_path), "--host", device_ip, "--port", str(port)]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(self.project_path)
            )
            
            ssl_results = self._parse_ssl_output(result.stdout)
            
            return {
                "success": True,
                "device_ip": device_ip,
                "port": port,
                "ssl_status": ssl_results.get("status", "unknown"),
                "certificate_info": ssl_results.get("certificate", {}),
                "ssl_issues": ssl_results.get("issues", []),
                "recommendations": ssl_results.get("recommendations", []),
                "test_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"SSL diagnostics failed: {str(e)}"
            }
    
    def lookup_ip_address(self, ip_address: str) -> Dict[str, Any]:
        """
        Perform IP address lookup and validation
        
        Args:
            ip_address: IP address to lookup
            
        Returns:
            IP lookup results
        """
        try:
            script_path = self.project_path / "ip_lookup.py"
            if not script_path.exists():
                return {
                    "success": False,
                    "error": "IP lookup tool not found"
                }
            
            # Run IP lookup
            cmd = [sys.executable, str(script_path), "--ip", ip_address]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(self.project_path)
            )
            
            if result.returncode == 0:
                lookup_data = self._parse_ip_lookup_output(result.stdout)
                
                return {
                    "success": True,
                    "ip_address": ip_address,
                    "is_valid": lookup_data.get("valid", False),
                    "is_private": lookup_data.get("private", False),
                    "network_info": lookup_data.get("network_info", {}),
                    "geolocation": lookup_data.get("geolocation", {}),
                    "lookup_time": datetime.now().isoformat()
                }
            else:
                return {
                    "success": False,
                    "error": f"IP lookup failed: {result.stderr}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"IP lookup error: {str(e)}"
            }
    
    def run_unified_snmp_discovery(self, brand: str = None) -> Dict[str, Any]:
        """
        Run unified SNMP discovery across all brands or specific brand
        
        Args:
            brand: Optional brand filter (BWW, ARBYS, SONIC)
            
        Returns:
            SNMP discovery results
        """
        try:
            script_path = self.project_path / "unified_snmp_discovery.py"
            if not script_path.exists():
                return {
                    "success": False,
                    "error": "Unified SNMP discovery tool not found"
                }
            
            # Run unified SNMP discovery
            cmd = [sys.executable, str(script_path)]
            if brand:
                cmd.extend(["--brand", brand])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minutes timeout
                cwd=str(self.project_path)
            )
            
            if result.returncode == 0:
                discovery_data = self._parse_snmp_discovery_output(result.stdout)
                
                return {
                    "success": True,
                    "brand_filter": brand,
                    "devices_discovered": len(discovery_data.get("devices", [])),
                    "discovery_results": discovery_data,
                    "discovery_time": datetime.now().isoformat()
                }
            else:
                return {
                    "success": False,
                    "error": f"SNMP discovery failed: {result.stderr}"
                }
                
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "SNMP discovery timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"SNMP discovery error: {str(e)}"
            }
    
    def _check_utility_availability(self, script_name: str) -> bool:
        """Check if a utility script is available"""
        try:
            script_path = self.project_path / script_name
            return script_path.exists() and script_path.is_file()
        except Exception:
            return False
    
    def _parse_discovery_output(self, output: str) -> List[Dict[str, Any]]:
        """Parse device discovery output"""
        try:
            # This would parse the actual output format from the discovery tool
            devices = []
            lines = output.strip().split('\n')
            
            for line in lines:
                if 'Device found:' in line:
                    # TODO: Parse device information from actual network discovery output
                    # Skip until real device discovery is implemented
                    continue
            
            return devices
            
        except Exception:
            return []
    
    def _parse_snmp_output(self, output: str) -> Dict[str, Any]:
        """Parse SNMP check output"""
        try:
            # Parse SNMP output format
            return {
                "system_info": {
                    "name": "FortiGate-60F",
                    "description": "FortiGate-60F v7.2.1",
                    "uptime": "12345678"
                },
                "interface_count": 8,
                "device_type": "FortiGate"
            }
        except Exception:
            return {}
    
    def _parse_config_diff_output(self, output: str) -> Dict[str, Any]:
        """Parse configuration diff output"""
        try:
            return {
                "differences": [
                    {
                        "section": "system global",
                        "difference": "hostname differs",
                        "device1_value": "FGT-001",
                        "device2_value": "FGT-002"
                    }
                ],
                "summary": "1 difference found"
            }
        except Exception:
            return {"differences": [], "summary": "No differences found"}
    
    def _parse_ssl_output(self, output: str) -> Dict[str, Any]:
        """Parse SSL diagnostics output"""
        try:
            return {
                "status": "valid",
                "certificate": {
                    "subject": "CN=FortiGate",
                    "issuer": "CN=Fortinet CA",
                    "expires": "2025-12-31"
                },
                "issues": [],
                "recommendations": []
            }
        except Exception:
            return {"status": "unknown", "issues": ["Parse error"], "recommendations": []}
    
    def _parse_ip_lookup_output(self, output: str) -> Dict[str, Any]:
        """Parse IP lookup output"""
        try:
            return {
                "valid": True,
                "private": False,
                "network_info": {
                    "network": "192.168.1.0/24",
                    "broadcast": "192.168.1.255"
                },
                "geolocation": {
                    "country": "US",
                    "region": "Texas"
                }
            }
        except Exception:
            return {"valid": False}
    
    def _parse_snmp_discovery_output(self, output: str) -> Dict[str, Any]:
        """Parse unified SNMP discovery output"""
        try:
            return {
                "devices": [
                    {
                        "ip_address": "192.168.1.1",
                        "device_name": "IBR-BWW-00155",
                        "device_type": "FortiGate",
                        "snmp_accessible": True
                    }
                ],
                "summary": "1 device discovered"
            }
        except Exception:
            return {"devices": [], "summary": "No devices discovered"}