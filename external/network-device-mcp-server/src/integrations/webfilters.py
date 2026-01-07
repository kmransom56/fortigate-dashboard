"""
Web Filters Integration
Integrates fortinet-webfilters-web application functionality into the MCP Web Server
"""

import os
import sys
import json
import subprocess
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import time

class WebFiltersManager:
    """
    Manages web filters operations by integrating the fortinet-webfilters-web application
    """
    
    def __init__(self, webfilters_path: str = None):
        """
        Initialize Web Filters Manager with path to fortinet-webfilters-web project
        
        Args:
            webfilters_path: Path to the fortinet-webfilters-web application
        """
        if webfilters_path is None:
            webfilters_path = "/mnt/c/Users/keith.ransom/CascadeProjects/fortinet-webfilters-web"
        
        self.project_path = Path(webfilters_path)
        self.server_process = None
        self.server_url = "http://localhost:5001"  # Default web filters app port
        self.powershell_command = [
            "C:\\Program Files\\PowerShell\\7\\pwsh.exe",
            "-ExecutionPolicy", "Bypass",
            "-File", 
            str(self.project_path / "startserver.ps1")
        ]
    
    def get_webfilters_status(self) -> Dict[str, Any]:
        """
        Get current status of the web filters application
        
        Returns:
            Status information about the web filters application
        """
        try:
            status = {
                "success": True,
                "application_path": str(self.project_path),
                "application_exists": self.project_path.exists(),
                "server_running": False,
                "server_url": self.server_url,
                "features": []
            }
            
            # Check if application files exist
            key_files = [
                "startserver.ps1",
                "app.py",
                "requirements.txt",
                "config/vault_config.json"
            ]
            
            file_status = {}
            for file in key_files:
                file_path = self.project_path / file
                file_status[file] = file_path.exists()
            
            status["file_status"] = file_status
            status["application_ready"] = all(file_status.values())
            
            # Check if server is running
            try:
                response = requests.get(f"{self.server_url}/health", timeout=5)
                if response.status_code == 200:
                    status["server_running"] = True
                    status["server_info"] = response.json()
            except:
                status["server_running"] = False
            
            # Define available features
            status["features"] = [
                {
                    "name": "web_filtering_policies",
                    "description": "Manage web filtering policies across brands",
                    "available": status["application_ready"]
                },
                {
                    "name": "ssl_certificate_management", 
                    "description": "SSL certificate handling and Vault integration",
                    "available": status["application_ready"]
                },
                {
                    "name": "multi_brand_support",
                    "description": "Support for BWW, Arby's, and Sonic brands",
                    "available": status["application_ready"]
                },
                {
                    "name": "vault_integration",
                    "description": "HashiCorp Vault secrets management",
                    "available": file_status.get("config/vault_config.json", False)
                }
            ]
            
            return status
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get web filters status: {str(e)}"
            }
    
    def start_webfilters_server(self) -> Dict[str, Any]:
        """
        Start the web filters PowerShell server
        
        Returns:
            Server startup results
        """
        try:
            if not self.project_path.exists():
                return {
                    "success": False,
                    "error": f"Web filters application not found at: {self.project_path}"
                }
            
            # Check if server is already running
            status = self.get_webfilters_status()
            if status.get("server_running", False):
                return {
                    "success": True,
                    "message": "Web filters server already running",
                    "server_url": self.server_url
                }
            
            # Start the PowerShell server process
            self.server_process = subprocess.Popen(
                self.powershell_command,
                cwd=str(self.project_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for server to start (up to 30 seconds)
            for i in range(30):
                time.sleep(1)
                try:
                    response = requests.get(f"{self.server_url}/health", timeout=2)
                    if response.status_code == 200:
                        return {
                            "success": True,
                            "message": "Web filters server started successfully",
                            "server_url": self.server_url,
                            "startup_time": f"{i+1} seconds",
                            "process_id": self.server_process.pid
                        }
                except:
                    continue
            
            return {
                "success": False,
                "error": "Web filters server failed to start within 30 seconds"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to start web filters server: {str(e)}"
            }
    
    def stop_webfilters_server(self) -> Dict[str, Any]:
        """
        Stop the web filters PowerShell server
        
        Returns:
            Server shutdown results
        """
        try:
            if self.server_process and self.server_process.poll() is None:
                self.server_process.terminate()
                try:
                    self.server_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    self.server_process.kill()
                
                return {
                    "success": True,
                    "message": "Web filters server stopped successfully"
                }
            else:
                return {
                    "success": True,
                    "message": "Web filters server was not running"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to stop web filters server: {str(e)}"
            }
    
    def get_web_filtering_policies(self, brand: str = None) -> Dict[str, Any]:
        """
        Get web filtering policies for brands
        
        Args:
            brand: Optional brand filter (BWW, ARBYS, SONIC)
            
        Returns:
            Web filtering policies data
        """
        try:
            # Ensure server is running
            if not self._ensure_server_running():
                return {
                    "success": False,
                    "error": "Web filters server not accessible"
                }
            
            # Query web filtering policies
            endpoint = "/api/webfilter/policies"
            params = {"brand": brand} if brand else {}
            
            response = requests.get(
                f"{self.server_url}{endpoint}",
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                policies_data = response.json()
                
                return {
                    "success": True,
                    "brand_filter": brand,
                    "policies": policies_data.get("policies", []),
                    "total_policies": len(policies_data.get("policies", [])),
                    "policy_categories": policies_data.get("categories", []),
                    "last_updated": policies_data.get("last_updated"),
                    "query_time": datetime.now().isoformat()
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to get policies: HTTP {response.status_code}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get web filtering policies: {str(e)}"
            }
    
    def get_store_web_filters(self, brand: str, store_id: str) -> Dict[str, Any]:
        """
        Get web filtering configuration for a specific store
        
        Args:
            brand: Restaurant brand (BWW, ARBYS, SONIC)
            store_id: Store identifier
            
        Returns:
            Store web filtering configuration
        """
        try:
            if not self._ensure_server_running():
                return {
                    "success": False,
                    "error": "Web filters server not accessible"
                }
            
            endpoint = f"/api/webfilter/store/{brand.upper()}/{store_id}"
            
            response = requests.get(
                f"{self.server_url}{endpoint}",
                timeout=30
            )
            
            if response.status_code == 200:
                store_data = response.json()
                
                return {
                    "success": True,
                    "brand": brand.upper(),
                    "store_id": store_id,
                    "device_name": f"IBR-{brand.upper()}-{store_id.zfill(5)}",
                    "web_filter_config": store_data.get("config", {}),
                    "active_policies": store_data.get("active_policies", []),
                    "blocked_categories": store_data.get("blocked_categories", []),
                    "allowed_exceptions": store_data.get("allowed_exceptions", []),
                    "filter_effectiveness": store_data.get("effectiveness", {}),
                    "last_policy_update": store_data.get("last_update"),
                    "query_time": datetime.now().isoformat()
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to get store filters: HTTP {response.status_code}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get store web filters: {str(e)}"
            }
    
    def get_web_filter_analytics(self, brand: str = None, timeframe: str = "24h") -> Dict[str, Any]:
        """
        Get web filtering analytics and statistics
        
        Args:
            brand: Optional brand filter
            timeframe: Time range for analytics (1h, 24h, 7d, 30d)
            
        Returns:
            Web filtering analytics data
        """
        try:
            if not self._ensure_server_running():
                return {
                    "success": False,
                    "error": "Web filters server not accessible"
                }
            
            endpoint = "/api/webfilter/analytics"
            params = {
                "timeframe": timeframe
            }
            if brand:
                params["brand"] = brand.upper()
            
            response = requests.get(
                f"{self.server_url}{endpoint}",
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                analytics_data = response.json()
                
                return {
                    "success": True,
                    "brand_filter": brand,
                    "timeframe": timeframe,
                    "analytics": {
                        "total_requests": analytics_data.get("total_requests", 0),
                        "blocked_requests": analytics_data.get("blocked_requests", 0),
                        "allowed_requests": analytics_data.get("allowed_requests", 0),
                        "block_rate": analytics_data.get("block_rate", 0),
                        "top_blocked_categories": analytics_data.get("top_blocked_categories", []),
                        "top_blocked_urls": analytics_data.get("top_blocked_urls", []),
                        "hourly_distribution": analytics_data.get("hourly_distribution", {}),
                        "policy_violations": analytics_data.get("policy_violations", [])
                    },
                    "analysis_time": datetime.now().isoformat()
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to get analytics: HTTP {response.status_code}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get web filter analytics: {str(e)}"
            }
    
    def update_web_filter_policy(self, brand: str, store_id: str, policy_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update web filtering policy for a store
        
        Args:
            brand: Restaurant brand
            store_id: Store identifier
            policy_data: Policy configuration data
            
        Returns:
            Policy update results
        """
        try:
            if not self._ensure_server_running():
                return {
                    "success": False,
                    "error": "Web filters server not accessible"
                }
            
            endpoint = f"/api/webfilter/policy/{brand.upper()}/{store_id}"
            
            response = requests.post(
                f"{self.server_url}{endpoint}",
                json=policy_data,
                timeout=60
            )
            
            if response.status_code == 200:
                update_result = response.json()
                
                return {
                    "success": True,
                    "brand": brand.upper(),
                    "store_id": store_id,
                    "policy_updated": True,
                    "changes_applied": update_result.get("changes", []),
                    "validation_results": update_result.get("validation", {}),
                    "deployment_status": update_result.get("deployment_status", "pending"),
                    "update_time": datetime.now().isoformat()
                }
            else:
                return {
                    "success": False,
                    "error": f"Policy update failed: HTTP {response.status_code}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to update web filter policy: {str(e)}"
            }
    
    def get_ssl_certificate_status(self) -> Dict[str, Any]:
        """
        Get SSL certificate status from the web filters application
        
        Returns:
            SSL certificate status and Vault integration info
        """
        try:
            if not self._ensure_server_running():
                return {
                    "success": False,
                    "error": "Web filters server not accessible"
                }
            
            endpoint = "/api/ssl/status"
            
            response = requests.get(
                f"{self.server_url}{endpoint}",
                timeout=30
            )
            
            if response.status_code == 200:
                ssl_data = response.json()
                
                return {
                    "success": True,
                    "ssl_status": {
                        "certificates_managed": ssl_data.get("certificates_count", 0),
                        "expiring_soon": ssl_data.get("expiring_soon", []),
                        "vault_connection": ssl_data.get("vault_status", "unknown"),
                        "last_renewal": ssl_data.get("last_renewal"),
                        "auto_renewal_enabled": ssl_data.get("auto_renewal", False)
                    },
                    "vault_integration": {
                        "connected": ssl_data.get("vault_connected", False),
                        "secrets_count": ssl_data.get("vault_secrets_count", 0),
                        "last_sync": ssl_data.get("vault_last_sync")
                    },
                    "status_time": datetime.now().isoformat()
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to get SSL status: HTTP {response.status_code}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get SSL certificate status: {str(e)}"
            }
    
    def search_web_filter_logs(self, query: str, brand: str = None, timeframe: str = "1h") -> Dict[str, Any]:
        """
        Search web filtering logs
        
        Args:
            query: Search query/filter
            brand: Optional brand filter
            timeframe: Search time range
            
        Returns:
            Web filter log search results
        """
        try:
            if not self._ensure_server_running():
                return {
                    "success": False,
                    "error": "Web filters server not accessible"
                }
            
            endpoint = "/api/webfilter/logs/search"
            params = {
                "query": query,
                "timeframe": timeframe
            }
            if brand:
                params["brand"] = brand.upper()
            
            response = requests.get(
                f"{self.server_url}{endpoint}",
                params=params,
                timeout=60
            )
            
            if response.status_code == 200:
                search_results = response.json()
                
                return {
                    "success": True,
                    "query": query,
                    "brand_filter": brand,
                    "timeframe": timeframe,
                    "total_matches": search_results.get("total_matches", 0),
                    "log_entries": search_results.get("entries", []),
                    "search_insights": search_results.get("insights", {}),
                    "search_time": datetime.now().isoformat()
                }
            else:
                return {
                    "success": False,
                    "error": f"Log search failed: HTTP {response.status_code}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Web filter log search failed: {str(e)}"
            }
    
    def _ensure_server_running(self) -> bool:
        """Ensure the web filters server is running"""
        try:
            response = requests.get(f"{self.server_url}/health", timeout=5)
            return response.status_code == 200
        except:
            # Try to start the server if it's not running
            start_result = self.start_webfilters_server()
            return start_result.get("success", False)
    
    def get_webfilters_integration_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive integration summary
        
        Returns:
            Complete integration status and capabilities
        """
        try:
            status = self.get_webfilters_status()
            ssl_status = self.get_ssl_certificate_status() if status.get("server_running") else {"success": False}
            
            return {
                "success": True,
                "integration_name": "fortinet-webfilters-web",
                "integration_status": "ready" if status.get("application_ready") else "needs_setup",
                "server_status": "running" if status.get("server_running") else "stopped",
                "application_path": str(self.project_path),
                "server_url": self.server_url,
                "capabilities": {
                    "web_filtering_management": status.get("application_ready", False),
                    "ssl_certificate_handling": status.get("application_ready", False),
                    "vault_integration": ssl_status.get("vault_integration", {}).get("connected", False),
                    "multi_brand_support": True,
                    "log_analysis": status.get("server_running", False),
                    "policy_management": status.get("application_ready", False)
                },
                "supported_brands": ["BWW", "ARBYS", "SONIC"],
                "available_endpoints": [
                    "/api/webfilter/policies",
                    "/api/webfilter/store/{brand}/{store_id}",
                    "/api/webfilter/analytics",
                    "/api/webfilter/logs/search",
                    "/api/ssl/status"
                ],
                "integration_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get integration summary: {str(e)}"
            }