# config.py - Advanced configuration management for Fortinet MCP Server

import json
import yaml
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class DeviceConfig:
    """Configuration for a Fortinet device"""
    name: str
    host: str
    device_type: str  # fortigate, fortimanager, fortianalyzer
    username: str
    password: str
    api_token: str = ""
    port: int = 443
    enabled: bool = True
    
class FortinetConfigManager:
    """Manage multiple Fortinet devices and their configurations"""
    
    def __init__(self, config_file: str = "fortinet_devices.yaml"):
        self.config_file = config_file
        self.devices = {}
        self.load_config()
    
    def load_config(self):
        """Load device configurations from file"""
        try:
            with open(self.config_file, 'r') as f:
                config_data = yaml.safe_load(f)
                
            for device_data in config_data.get('devices', []):
                device = DeviceConfig(**device_data)
                self.devices[device.name] = device
                
        except FileNotFoundError:
            print(f"Config file {self.config_file} not found. Using environment variables.")
        except Exception as e:
            print(f"Error loading config: {e}")
    
    def get_device(self, name: str) -> DeviceConfig:
        """Get device configuration by name"""
        return self.devices.get(name)
    
    def list_devices(self) -> List[str]:
        """List all configured device names"""
        return list(self.devices.keys())

# Example fortinet_devices.yaml configuration file:
EXAMPLE_CONFIG = """
devices:
  - name: "main-fortigate"
    host: "192.168.1.1"
    device_type: "fortigate"
    username: "admin"
    password: ""
    api_token: "your_api_token_here"
    port: 443
    enabled: true
    
  - name: "branch-fortigate"
    host: "10.0.1.1"
    device_type: "fortigate"
    username: "admin"
    password: ""
    api_token: "branch_api_token"
    port: 443
    enabled: true
    
  - name: "fortimanager"
    host: "192.168.1.10"
    device_type: "fortimanager"
    username: "admin"
    password: "manager_password"
    api_token: ""
    port: 443
    enabled: true
    
  - name: "fortianalyzer"
    host: "192.168.1.20"
    device_type: "fortianalyzer"
    username: "admin"
    password: "analyzer_password"
    api_token: ""
    port: 443
    enabled: true

# Advanced settings
settings:
  default_timeout: 30
  max_retries: 3
  ssl_verify: false
  log_level: "INFO"
  enable_caching: true
  cache_ttl: 300  # 5 minutes
"""

# Advanced MCP Tools for network automation

class NetworkAutomation:
    """Advanced network automation capabilities"""
    
    @staticmethod
    def generate_security_report(device_data: Dict) -> str:
        """Generate a comprehensive security report"""
        report = []
        report.append("# FORTINET SECURITY ASSESSMENT REPORT")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # System Information
        report.append("## System Information")
        if 'system_status' in device_data:
            status = device_data['system_status']
            report.append(f"- Hostname: {status.get('hostname', 'N/A')}")
            report.append(f"- Version: {status.get('version', 'N/A')}")
            report.append(f"- Serial: {status.get('serial', 'N/A')}")
            report.append("")
        
        # Policy Analysis
        report.append("## Firewall Policy Analysis")
        if 'policies' in device_data:
            policies = device_data['policies'].get('results', [])
            report.append(f"- Total Policies: {len(policies)}")
            
            # Count enabled/disabled policies
            enabled = sum(1 for p in policies if p.get('status') == 'enable')
            disabled = len(policies) - enabled
            report.append(f"- Enabled: {enabled}, Disabled: {disabled}")
            
            # Check for any-any rules
            any_any_rules = [p for p in policies 
                           if 'all' in str(p.get('srcaddr', [])) and 'all' in str(p.get('dstaddr', []))]
            if any_any_rules:
                report.append(f"- ⚠️ WARNING: {len(any_any_rules)} 'any-to-any' rules found")
            
            report.append("")
        
        # Interface Status
        report.append("## Interface Status")
        if 'interfaces' in device_data:
            interfaces = device_data['interfaces'].get('results', [])
            for iface in interfaces:
                name = iface.get('name', 'Unknown')
                status = iface.get('status', 'Unknown')
                ip = iface.get('ip', 'N/A')
                report.append(f"- {name}: {status} ({ip})")
            report.append("")
        
        # VPN Status
        report.append("## VPN Status")
        if 'vpn_status' in device_data:
            vpn_info = device_data['vpn_status']
            report.append(f"- VPN Tunnels: {len(vpn_info.get('results', []))}")
            report.append("")
        
        # Security Recommendations
        report.append("## Security Recommendations")
        report.append("1. Review and minimize 'any-to-any' firewall rules")
        report.append("2. Ensure all unused interfaces are disabled")
        report.append("3. Regularly update firmware to latest version")
        report.append("4. Enable logging for all security policies")
        report.append("5. Implement network segmentation where possible")
        report.append("6. Regular backup of configuration")
        report.append("7. Monitor VPN usage and access patterns")
        
        return "\n".join(report)
    
    @staticmethod
    def analyze_traffic_patterns(interface_stats: Dict) -> Dict:
        """Analyze traffic patterns for anomaly detection"""
        analysis = {
            "total_interfaces": 0,
            "active_interfaces": 0,
            "high_utilization": [],
            "suspicious_patterns": [],
            "recommendations": []
        }
        
        interfaces = interface_stats.get('results', [])
        analysis["total_interfaces"] = len(interfaces)
        
        for iface in interfaces:
            name = iface.get('name', 'unknown')
            rx_bytes = int(iface.get('rx_bytes', 0))
            tx_bytes = int(iface.get('tx_bytes', 0))
            rx_packets = int(iface.get('rx_packets', 0))
            tx_packets = int(iface.get('tx_packets', 0))
            
            if rx_bytes > 0 or tx_bytes > 0:
                analysis["active_interfaces"] += 1
            
            # Check for high utilization (this is simplified)
            total_bytes = rx_bytes + tx_bytes
            if total_bytes > 1000000000:  # > 1GB
                analysis["high_utilization"].append({
                    "interface": name,
                    "total_bytes": total_bytes,
                    "rx_bytes": rx_bytes,
                    "tx_bytes": tx_bytes
                })
            
            # Check for suspicious patterns
            if rx_packets > 0 and tx_packets > 0:
                ratio = rx_packets / tx_packets if tx_packets > 0 else 0
                if ratio > 100 or ratio < 0.01:  # Very skewed traffic
                    analysis["suspicious_patterns"].append({
                        "interface": name,
                        "pattern": "unusual_packet_ratio",
                        "rx_packets": rx_packets,
                        "tx_packets": tx_packets,
                        "ratio": ratio
                    })
        
        # Generate recommendations
        if analysis["high_utilization"]:
            analysis["recommendations"].append("Monitor high-utilization interfaces for capacity planning")
        
        if analysis["suspicious_patterns"]:
            analysis["recommendations"].append("Investigate interfaces with unusual traffic patterns")
        
        if analysis["active_interfaces"] < analysis["total_interfaces"]:
            analysis["recommendations"].append("Consider disabling unused interfaces for security")
        
        return analysis

    @staticmethod
    def policy_optimization_suggestions(policies: Dict) -> List[Dict]:
        """Suggest policy optimizations"""
        suggestions = []
        policy_list = policies.get('results', [])
        
        # Group policies by action
        allow_policies = [p for p in policy_list if p.get('action') == 'accept']
        deny_policies = [p for p in policy_list if p.get('action') == 'deny']
        
        # Check policy ordering
        for i, policy in enumerate(policy_list):
            if policy.get('action') == 'deny':
                # Check if there are allow rules after deny rules
                subsequent_allows = [p for p in policy_list[i+1:] if p.get('action') == 'accept']
                if subsequent_allows:
                    suggestions.append({
                        "type": "ordering",
                        "policy_id": policy.get('policyid'),
                        "issue": "Deny rule followed by allow rules - may cause confusion",
                        "recommendation": "Consider reordering policies for clarity"
                    })
        
        # Check for duplicate or overlapping rules
        for i, policy1 in enumerate(policy_list):
            for j, policy2 in enumerate(policy_list[i+1:], i+1):
                if (policy1.get('srcaddr') == policy2.get('srcaddr') and
                    policy1.get('dstaddr') == policy2.get('dstaddr') and
                    policy1.get('service') == policy2.get('service')):
                    suggestions.append({
                        "type": "duplicate",
                        "policy_ids": [policy1.get('policyid'), policy2.get('policyid')],
                        "issue": "Potential duplicate policies detected",
                        "recommendation": "Review and consolidate duplicate policies"
                    })
        
        # Check for overly broad rules
        for policy in policy_list:
            srcaddr = policy.get('srcaddr', [])
            dstaddr = policy.get('dstaddr', [])
            service = policy.get('service', [])
            
            if ('all' in str(srcaddr) and 'all' in str(dstaddr) and 'ALL' in str(service)):
                suggestions.append({
                    "type": "security",
                    "policy_id": policy.get('policyid'),
                    "issue": "Policy allows all traffic from any source to any destination",
                    "recommendation": "Implement principle of least privilege - restrict source, destination, and services"
                })
        
        return suggestions

# Write example config file if it doesn't exist
def create_example_config():
    """Create an example configuration file"""
    with open('fortinet_devices_example.yaml', 'w') as f:
        f.write(EXAMPLE_CONFIG)
    print("Example configuration file created: fortinet_devices_example.yaml")

if __name__ == "__main__":
    create_example_config()