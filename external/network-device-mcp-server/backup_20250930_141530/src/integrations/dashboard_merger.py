"""
Dashboard Merger Integration
Integrates fortimanagerdashboard project functionality into the MCP Web Server
"""

import os
import sys
import json
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

class DashboardMerger:
    """
    Manages dashboard consolidation by integrating fortimanagerdashboard 
    project functionality into the unified MCP Web Server
    """
    
    def __init__(self, dashboard_path: str = None):
        """
        Initialize Dashboard Merger with path to fortimanagerdashboard project
        """
        if dashboard_path is None:
            dashboard_path = "/mnt/c/Users/keith.ransom/fortimanagerdashboard"
        
        self.project_path = Path(dashboard_path)
        
        # Add dashboard project to Python path for imports
        if str(self.project_path) not in sys.path:
            sys.path.append(str(self.project_path))
    
    def get_dashboard_capabilities(self) -> Dict[str, Any]:
        """
        Get capabilities available from the FortiManager dashboard project
        
        Returns:
            Dictionary containing available dashboard features
        """
        try:
            capabilities = {
                "success": True,
                "available_features": [
                    {
                        "name": "advanced_fortimanager_api",
                        "description": "Advanced FortiManager API operations",
                        "available": self._check_feature_availability("fortimanager_api_server.py"),
                        "endpoints": [
                            "/api/dashboard/fortimanager/devices",
                            "/api/dashboard/fortimanager/policies",
                            "/api/dashboard/fortimanager/certificates"
                        ]
                    },
                    {
                        "name": "ssl_certificate_management",
                        "description": "SSL certificate handling and troubleshooting",
                        "available": self._check_feature_availability("ssl_certificate_handler.py"),
                        "endpoints": [
                            "/api/dashboard/ssl/validate",
                            "/api/dashboard/ssl/troubleshoot"
                        ]
                    },
                    {
                        "name": "corporate_ssl_bypass",
                        "description": "Corporate SSL certificate bypass solutions",
                        "available": self._check_feature_availability("corporate_ssl_bypass.py"),
                        "endpoints": [
                            "/api/dashboard/ssl/corporate-bypass"
                        ]
                    },
                    {
                        "name": "nextjs_frontend",
                        "description": "Advanced React/NextJS dashboard components",
                        "available": self._check_feature_availability("frontend/"),
                        "endpoints": [
                            "/api/dashboard/frontend/components"
                        ]
                    }
                ],
                "integration_status": "ready"
            }
            
            # Count available features
            available_count = len([f for f in capabilities["available_features"] if f["available"]])
            capabilities["available_count"] = available_count
            capabilities["total_features"] = len(capabilities["available_features"])
            
            return capabilities
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get dashboard capabilities: {str(e)}"
            }
    
    def get_advanced_fortimanager_data(self, fortimanager_name: str) -> Dict[str, Any]:
        """
        Get advanced FortiManager data using enhanced API methods
        
        Args:
            fortimanager_name: Name of the FortiManager instance
            
        Returns:
            Advanced FortiManager data
        """
        try:
            # Import enhanced FortiManager client
            enhanced_client = self._get_enhanced_fortimanager_client()
            if not enhanced_client:
                return {
                    "success": False,
                    "error": "Enhanced FortiManager client not available"
                }
            
            # Get advanced data
            fm_data = enhanced_client.get_comprehensive_data(fortimanager_name)
            
            return {
                "success": True,
                "fortimanager_name": fortimanager_name,
                "advanced_data": fm_data,
                "data_timestamp": datetime.now().isoformat(),
                "source": "enhanced_dashboard_integration"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get advanced FortiManager data: {str(e)}"
            }
    
    def run_ssl_certificate_analysis(self, device_ip: str, port: int = 443) -> Dict[str, Any]:
        """
        Run comprehensive SSL certificate analysis using dashboard tools
        
        Args:
            device_ip: IP address of the device
            port: SSL/TLS port (default: 443)
            
        Returns:
            SSL certificate analysis results
        """
        try:
            ssl_handler = self._get_ssl_certificate_handler()
            if not ssl_handler:
                return {
                    "success": False,
                    "error": "SSL certificate handler not available"
                }
            
            # Run comprehensive SSL analysis
            ssl_results = ssl_handler.analyze_certificate(device_ip, port)
            
            return {
                "success": True,
                "device_ip": device_ip,
                "port": port,
                "certificate_analysis": ssl_results,
                "analysis_time": datetime.now().isoformat(),
                "source": "dashboard_ssl_integration"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"SSL certificate analysis failed: {str(e)}"
            }
    
    def get_corporate_ssl_solutions(self, ssl_issue_type: str) -> Dict[str, Any]:
        """
        Get corporate SSL bypass solutions for specific issues
        
        Args:
            ssl_issue_type: Type of SSL issue (cert_validation, proxy_bypass, etc.)
            
        Returns:
            SSL bypass solutions
        """
        try:
            ssl_bypass = self._get_corporate_ssl_bypass()
            if not ssl_bypass:
                return {
                    "success": False,
                    "error": "Corporate SSL bypass module not available"
                }
            
            solutions = ssl_bypass.get_solutions(ssl_issue_type)
            
            return {
                "success": True,
                "issue_type": ssl_issue_type,
                "available_solutions": solutions,
                "solution_count": len(solutions),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get SSL solutions: {str(e)}"
            }
    
    def get_enhanced_api_operations(self) -> Dict[str, Any]:
        """
        Get list of enhanced API operations available from dashboard integration
        
        Returns:
            List of enhanced API operations
        """
        try:
            operations = {
                "success": True,
                "enhanced_operations": [
                    {
                        "category": "FortiManager Advanced",
                        "operations": [
                            {
                                "name": "bulk_device_management",
                                "description": "Manage multiple devices simultaneously",
                                "endpoint": "/api/dashboard/fortimanager/bulk-operations"
                            },
                            {
                                "name": "policy_optimization",
                                "description": "Optimize firewall policies across devices",
                                "endpoint": "/api/dashboard/fortimanager/policy-optimization"
                            },
                            {
                                "name": "certificate_deployment",
                                "description": "Deploy certificates to multiple devices",
                                "endpoint": "/api/dashboard/fortimanager/certificate-deployment"
                            }
                        ]
                    },
                    {
                        "category": "SSL Certificate Management",
                        "operations": [
                            {
                                "name": "certificate_inventory",
                                "description": "Inventory all certificates across network",
                                "endpoint": "/api/dashboard/ssl/inventory"
                            },
                            {
                                "name": "expiration_monitoring",
                                "description": "Monitor certificate expiration dates",
                                "endpoint": "/api/dashboard/ssl/expiration-monitor"
                            },
                            {
                                "name": "auto_renewal",
                                "description": "Automated certificate renewal workflows",
                                "endpoint": "/api/dashboard/ssl/auto-renewal"
                            }
                        ]
                    },
                    {
                        "category": "Enhanced Troubleshooting",
                        "operations": [
                            {
                                "name": "multi_device_diagnostics",
                                "description": "Run diagnostics across multiple devices",
                                "endpoint": "/api/dashboard/diagnostics/multi-device"
                            },
                            {
                                "name": "network_topology_analysis",
                                "description": "Analyze network topology and connections",
                                "endpoint": "/api/dashboard/diagnostics/topology"
                            },
                            {
                                "name": "performance_analytics",
                                "description": "Advanced performance analytics and reporting",
                                "endpoint": "/api/dashboard/analytics/performance"
                            }
                        ]
                    }
                ],
                "total_operations": 9,
                "integration_level": "full"
            }
            
            return operations
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get enhanced operations: {str(e)}"
            }
    
    def merge_dashboard_components(self) -> Dict[str, Any]:
        """
        Merge dashboard components from the NextJS frontend into the unified interface
        
        Returns:
            Dashboard component integration results
        """
        try:
            frontend_path = self.project_path / "frontend"
            if not frontend_path.exists():
                return {
                    "success": False,
                    "error": "NextJS frontend not found"
                }
            
            # Analyze available components
            components = self._analyze_frontend_components()
            
            # Create component mapping for integration
            component_mapping = self._create_component_mapping(components)
            
            return {
                "success": True,
                "components_found": len(components),
                "components": components,
                "integration_mapping": component_mapping,
                "merge_status": "ready_for_integration",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Dashboard component merge failed: {str(e)}"
            }
    
    def run_advanced_fortimanager_operation(self, operation: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run advanced FortiManager operation using dashboard integration
        
        Args:
            operation: Operation to perform
            parameters: Operation parameters
            
        Returns:
            Operation results
        """
        try:
            enhanced_client = self._get_enhanced_fortimanager_client()
            if not enhanced_client:
                return {
                    "success": False,
                    "error": "Enhanced FortiManager client not available"
                }
            
            # Execute the advanced operation
            result = enhanced_client.execute_operation(operation, parameters)
            
            return {
                "success": True,
                "operation": operation,
                "parameters": parameters,
                "result": result,
                "execution_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Advanced operation failed: {str(e)}"
            }
    
    def _check_feature_availability(self, feature_path: str) -> bool:
        """Check if a dashboard feature is available"""
        try:
            full_path = self.project_path / feature_path
            return full_path.exists()
        except Exception:
            return False
    
    def _get_enhanced_fortimanager_client(self):
        """Get enhanced FortiManager client from dashboard project"""
        try:
            # Import the enhanced client
            from advanced_fortimanager_client import AdvancedFortiManagerClient
            return AdvancedFortiManagerClient()
        except ImportError:
            return None
    
    def _get_ssl_certificate_handler(self):
        """Get SSL certificate handler from dashboard project"""
        try:
            from ssl_certificate_handler import SSLCertificateHandler
            return SSLCertificateHandler()
        except ImportError:
            return None
    
    def _get_corporate_ssl_bypass(self):
        """Get corporate SSL bypass module from dashboard project"""
        try:
            from corporate_ssl_bypass import CorporateSSLBypass
            return CorporateSSLBypass()
        except ImportError:
            return None
    
    def _analyze_frontend_components(self) -> List[Dict[str, Any]]:
        """Analyze available frontend components"""
        try:
            components = []
            frontend_path = self.project_path / "frontend"
            
            # Look for React/NextJS components
            component_files = list(frontend_path.rglob("*.tsx"))
            component_files.extend(list(frontend_path.rglob("*.jsx")))
            
            for component_file in component_files:
                component_info = {
                    "name": component_file.stem,
                    "path": str(component_file.relative_to(self.project_path)),
                    "type": "react_component",
                    "size": component_file.stat().st_size
                }
                components.append(component_info)
            
            return components
            
        except Exception:
            return []
    
    def _create_component_mapping(self, components: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create mapping for component integration"""
        try:
            mapping = {
                "components_to_integrate": [],
                "integration_strategy": "embed_in_unified_dashboard",
                "modification_required": True
            }
            
            for component in components:
                if component["name"] in ["Dashboard", "DeviceList", "PolicyManager"]:
                    mapping["components_to_integrate"].append({
                        "component": component["name"],
                        "integration_method": "embed",
                        "target_section": self._map_component_to_section(component["name"])
                    })
            
            return mapping
            
        except Exception:
            return {}
    
    def _map_component_to_section(self, component_name: str) -> str:
        """Map component to unified dashboard section"""
        mapping = {
            "Dashboard": "overview",
            "DeviceList": "devices", 
            "PolicyManager": "fortimanager"
        }
        return mapping.get(component_name, "advanced")