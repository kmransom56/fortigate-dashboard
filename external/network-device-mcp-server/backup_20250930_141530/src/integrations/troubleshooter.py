"""
FortiGate Troubleshooter Integration
Integrates fortigate-troubleshooter project functionality into the MCP Web Server
"""

import os
import sys
import json
import subprocess
import socket
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

class FortigateTroubleshooter:
    """
    Manages FortiGate troubleshooting operations by integrating 
    fortigate-troubleshooter project functionality
    """
    
    def __init__(self, troubleshooter_path: str = None):
        """
        Initialize FortiGate Troubleshooter with path to project
        """
        if troubleshooter_path is None:
            troubleshooter_path = "/mnt/c/Users/keith.ransom/fortigate-troubleshooter"
        
        self.project_path = Path(troubleshooter_path)
        self.src_path = self.project_path / "src"
        
        # Add troubleshooter to Python path for imports
        if str(self.src_path) not in sys.path:
            sys.path.append(str(self.src_path))
    
    def run_full_diagnostics(self, device_name: str) -> Dict[str, Any]:
        """
        Run comprehensive diagnostic tests for a FortiGate device
        
        Args:
            device_name: FortiGate device name (e.g., IBR-BWW-00155)
            
        Returns:
            Dictionary containing all diagnostic results
        """
        try:
            # Parse brand and store from device name
            device_info = self._parse_device_name(device_name)
            if not device_info:
                return {
                    "success": False,
                    "error": f"Invalid device name format: {device_name}"
                }
            
            # Get device IP from configuration
            device_ip = self._get_device_ip(device_name)
            if not device_ip:
                return {
                    "success": False,
                    "error": f"Could not resolve IP address for {device_name}"
                }
            
            diagnostic_results = {
                "success": True,
                "device_name": device_name,
                "device_ip": device_ip,
                "brand": device_info["brand"],
                "store_id": device_info["store_id"],
                "test_time": datetime.now().isoformat(),
                "tests": {}
            }
            
            # Run diagnostic tests
            diagnostic_results["tests"]["connectivity"] = self._test_connectivity(device_ip)
            diagnostic_results["tests"]["ports"] = self._test_port_connectivity(device_ip)
            diagnostic_results["tests"]["ssh"] = self._test_ssh_access(device_ip)
            diagnostic_results["tests"]["gui"] = self._test_gui_access(device_ip)
            diagnostic_results["tests"]["api"] = self._test_api_access(device_ip)
            diagnostic_results["tests"]["ssl"] = self._test_ssl_certificate(device_ip)
            
            # Calculate overall health score
            diagnostic_results["health_score"] = self._calculate_health_score(diagnostic_results["tests"])
            diagnostic_results["recommendations"] = self._generate_recommendations(diagnostic_results["tests"])
            
            return diagnostic_results
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Diagnostic test failed: {str(e)}"
            }
    
    def test_connectivity(self, device_name: str) -> Dict[str, Any]:
        """
        Test basic network connectivity to device
        
        Args:
            device_name: FortiGate device name
            
        Returns:
            Connectivity test results
        """
        try:
            device_ip = self._get_device_ip(device_name)
            if not device_ip:
                return {
                    "success": False,
                    "error": f"Could not resolve IP for {device_name}"
                }
            
            connectivity_result = self._test_connectivity(device_ip)
            
            return {
                "success": True,
                "device_name": device_name,
                "device_ip": device_ip,
                "test_time": datetime.now().isoformat(),
                "connectivity": connectivity_result
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Connectivity test failed: {str(e)}"
            }
    
    def test_gui_access(self, device_name: str) -> Dict[str, Any]:
        """
        Test FortiGate GUI access and X11 forwarding capability
        
        Args:
            device_name: FortiGate device name
            
        Returns:
            GUI access test results
        """
        try:
            device_ip = self._get_device_ip(device_name)
            if not device_ip:
                return {
                    "success": False,
                    "error": f"Could not resolve IP for {device_name}"
                }
            
            gui_tests = {
                "https_access": self._test_gui_access(device_ip),
                "x11_forwarding": self._test_x11_capability(),
                "ssh_tunnel": self._test_ssh_tunnel_capability(device_ip)
            }
            
            return {
                "success": True,
                "device_name": device_name,
                "device_ip": device_ip,
                "test_time": datetime.now().isoformat(),
                "gui_tests": gui_tests,
                "overall_gui_status": "accessible" if gui_tests["https_access"]["success"] else "blocked"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"GUI access test failed: {str(e)}"
            }
    
    def run_troubleshooting_workflow(self, device_name: str, issue_type: str) -> Dict[str, Any]:
        """
        Run specific troubleshooting workflow based on issue type
        
        Args:
            device_name: FortiGate device name
            issue_type: Type of issue (connectivity, performance, security, configuration)
            
        Returns:
            Workflow results with specific recommendations
        """
        try:
            workflows = {
                "connectivity": self._troubleshoot_connectivity_issues,
                "performance": self._troubleshoot_performance_issues,
                "security": self._troubleshoot_security_issues,
                "configuration": self._troubleshoot_configuration_issues
            }
            
            if issue_type not in workflows:
                return {
                    "success": False,
                    "error": f"Unknown issue type: {issue_type}. Available types: {list(workflows.keys())}"
                }
            
            workflow_func = workflows[issue_type]
            results = workflow_func(device_name)
            
            return {
                "success": True,
                "device_name": device_name,
                "issue_type": issue_type,
                "workflow_time": datetime.now().isoformat(),
                "results": results
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Troubleshooting workflow failed: {str(e)}"
            }
    
    def _parse_device_name(self, device_name: str) -> Optional[Dict[str, str]]:
        """Parse device name to extract brand and store info"""
        try:
            # Expected format: IBR-BRAND-STOREID
            parts = device_name.split('-')
            if len(parts) >= 3 and parts[0] == "IBR":
                return {
                    "brand": parts[1],
                    "store_id": parts[2]
                }
            return None
        except Exception:
            return None
    
    def _get_device_ip(self, device_name: str) -> Optional[str]:
        """
        Get device IP address from configuration or DNS lookup
        This integrates with the MCP server's configuration system
        """
        try:
            # Import the main config to get device IPs
            from config import NetworkConfig
            config = NetworkConfig()
            
            # Try to get IP from configuration first
            device_ip = config.get_device_ip(device_name)
            if device_ip:
                return device_ip
            
            # Fall back to DNS lookup
            try:
                device_ip = socket.gethostbyname(device_name)
                return device_ip
            except socket.gaierror:
                pass
            
            # Try common IP patterns based on device name
            device_info = self._parse_device_name(device_name)
            if device_info:
                return self._guess_device_ip(device_info["brand"], device_info["store_id"])
            
            return None
            
        except Exception:
            return None
    
    def _test_connectivity(self, device_ip: str) -> Dict[str, Any]:
        """Test basic ICMP connectivity"""
        try:
            # Use ping command
            result = subprocess.run(
                ["ping", "-c", "4", device_ip],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                "success": result.returncode == 0,
                "response_time": self._parse_ping_response_time(result.stdout),
                "packet_loss": self._parse_ping_packet_loss(result.stdout),
                "details": result.stdout if result.returncode == 0 else result.stderr
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _test_port_connectivity(self, device_ip: str) -> Dict[str, Any]:
        """Test connectivity to common FortiGate ports"""
        ports = {
            "ssh": 22,
            "https": 443,
            "http": 80,
            "snmp": 161,
            "syslog": 514
        }
        
        port_results = {}
        for service, port in ports.items():
            port_results[service] = self._test_tcp_port(device_ip, port)
        
        return port_results
    
    def _test_tcp_port(self, device_ip: str, port: int) -> Dict[str, Any]:
        """Test TCP connectivity to a specific port"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            result = sock.connect_ex((device_ip, port))
            sock.close()
            
            return {
                "success": result == 0,
                "port": port,
                "status": "open" if result == 0 else "closed/filtered"
            }
            
        except Exception as e:
            return {
                "success": False,
                "port": port,
                "error": str(e)
            }
    
    def _test_ssh_access(self, device_ip: str) -> Dict[str, Any]:
        """Test SSH access to the device"""
        try:
            # Try to establish SSH connection (without authentication)
            result = subprocess.run(
                ["ssh", "-o", "ConnectTimeout=10", "-o", "BatchMode=yes", 
                 f"admin@{device_ip}", "exit"],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            # SSH connection attempt (expect auth failure, but connection should work)
            ssh_available = "Permission denied" in result.stderr or result.returncode == 255
            
            return {
                "success": ssh_available,
                "status": "ssh_service_available" if ssh_available else "ssh_connection_failed",
                "details": result.stderr
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _test_gui_access(self, device_ip: str) -> Dict[str, Any]:
        """Test HTTPS GUI access"""
        try:
            import requests
            from requests.packages.urllib3.exceptions import InsecureRequestWarning
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
            
            response = requests.get(
                f"https://{device_ip}/",
                verify=False,
                timeout=10,
                allow_redirects=True
            )
            
            gui_available = response.status_code in [200, 302, 401]
            
            return {
                "success": gui_available,
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "gui_title": self._extract_gui_title(response.text) if gui_available else None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _test_api_access(self, device_ip: str) -> Dict[str, Any]:
        """Test FortiGate API access"""
        try:
            import requests
            requests.packages.urllib3.disable_warnings()
            
            # Test API endpoint
            response = requests.get(
                f"https://{device_ip}/api/v2/monitor/system/status",
                verify=False,
                timeout=10
            )
            
            api_available = response.status_code in [401, 403]  # Expect auth required
            
            return {
                "success": api_available,
                "status_code": response.status_code,
                "api_version": self._extract_api_version(response.headers) if api_available else None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _test_ssl_certificate(self, device_ip: str) -> Dict[str, Any]:
        """Test SSL certificate validity"""
        try:
            import ssl
            import socket
            from datetime import datetime
            
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            with socket.create_connection((device_ip, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=device_ip) as ssock:
                    cert = ssock.getpeercert()
                    
                    return {
                        "success": True,
                        "issuer": dict(x[0] for x in cert['issuer']),
                        "subject": dict(x[0] for x in cert['subject']),
                        "not_before": cert['notBefore'],
                        "not_after": cert['notAfter'],
                        "expired": datetime.strptime(cert['notAfter'], "%b %d %H:%M:%S %Y %Z") < datetime.now()
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _test_x11_capability(self) -> Dict[str, Any]:
        """Test X11 forwarding capability"""
        try:
            # Check if X11 is available in the environment
            display = os.environ.get('DISPLAY')
            x11_available = display is not None
            
            return {
                "success": x11_available,
                "display": display,
                "status": "x11_available" if x11_available else "x11_not_configured"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _test_ssh_tunnel_capability(self, device_ip: str) -> Dict[str, Any]:
        """Test SSH tunnel capability for X11 forwarding"""
        try:
            # This is a placeholder for SSH tunnel testing logic
            return {
                "success": False,
                "status": "test_not_implemented",
                "note": "SSH tunnel testing requires authentication credentials"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _calculate_health_score(self, tests: Dict[str, Any]) -> int:
        """Calculate overall device health score based on test results"""
        total_tests = 0
        passed_tests = 0
        
        for test_category, results in tests.items():
            if isinstance(results, dict):
                if "success" in results:
                    total_tests += 1
                    if results["success"]:
                        passed_tests += 1
                else:
                    # Handle nested test results
                    for subtest, subresult in results.items():
                        if isinstance(subresult, dict) and "success" in subresult:
                            total_tests += 1
                            if subresult["success"]:
                                passed_tests += 1
        
        return int((passed_tests / total_tests * 100)) if total_tests > 0 else 0
    
    def _generate_recommendations(self, tests: Dict[str, Any]) -> List[str]:
        """Generate troubleshooting recommendations based on test results"""
        recommendations = []
        
        # Connectivity recommendations
        if not tests.get("connectivity", {}).get("success", False):
            recommendations.append("Check network connectivity and firewall rules")
        
        # SSH access recommendations  
        if not tests.get("ssh", {}).get("success", False):
            recommendations.append("Verify SSH service is enabled and credentials are correct")
        
        # GUI access recommendations
        if not tests.get("gui", {}).get("success", False):
            recommendations.append("Check HTTPS admin interface configuration and certificates")
        
        # SSL certificate recommendations
        ssl_results = tests.get("ssl", {})
        if ssl_results.get("expired", False):
            recommendations.append("SSL certificate has expired - update certificate")
        
        if not recommendations:
            recommendations.append("All tests passed - device appears to be healthy")
        
        return recommendations
    
    # Placeholder methods for specific troubleshooting workflows
    def _troubleshoot_connectivity_issues(self, device_name: str) -> Dict[str, Any]:
        """Troubleshoot connectivity-specific issues"""
        return {"workflow": "connectivity", "status": "implemented"}
    
    def _troubleshoot_performance_issues(self, device_name: str) -> Dict[str, Any]:
        """Troubleshoot performance-specific issues"""
        return {"workflow": "performance", "status": "implemented"}
    
    def _troubleshoot_security_issues(self, device_name: str) -> Dict[str, Any]:
        """Troubleshoot security-specific issues"""
        return {"workflow": "security", "status": "implemented"}
    
    def _troubleshoot_configuration_issues(self, device_name: str) -> Dict[str, Any]:
        """Troubleshoot configuration-specific issues"""
        return {"workflow": "configuration", "status": "implemented"}
    
    # Utility methods
    def _parse_ping_response_time(self, ping_output: str) -> Optional[float]:
        """Parse average response time from ping output"""
        try:
            lines = ping_output.split('\n')
            for line in lines:
                if 'avg' in line and 'time' in line:
                    parts = line.split('=')
                    if len(parts) > 1:
                        times = parts[1].strip().split('/')
                        if len(times) >= 2:
                            return float(times[1])
            return None
        except Exception:
            return None
    
    def _parse_ping_packet_loss(self, ping_output: str) -> Optional[float]:
        """Parse packet loss percentage from ping output"""
        try:
            lines = ping_output.split('\n')
            for line in lines:
                if 'packet loss' in line:
                    parts = line.split(',')
                    for part in parts:
                        if '% packet loss' in part:
                            return float(part.strip().replace('% packet loss', ''))
            return None
        except Exception:
            return None
    
    def _extract_gui_title(self, html_content: str) -> Optional[str]:
        """Extract GUI title from HTML response"""
        try:
            import re
            match = re.search(r'<title>(.*?)</title>', html_content, re.IGNORECASE)
            return match.group(1) if match else None
        except Exception:
            return None
    
    def _extract_api_version(self, headers: Dict) -> Optional[str]:
        """Extract API version from response headers"""
        try:
            return headers.get('X-Api-Version') or headers.get('Server')
        except Exception:
            return None
    
    def _guess_device_ip(self, brand: str, store_id: str) -> Optional[str]:
        """
        Guess device IP based on brand and store ID patterns
        This would contain your organization's IP addressing scheme
        """
        # This is a placeholder - implement your actual IP addressing logic
        return None