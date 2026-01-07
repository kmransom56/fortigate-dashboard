#!/usr/bin/env python3
"""
FortiManager Management Interface Collector
Captures management interface information from all FortiGate devices for SNMP monitoring
"""

import requests
import json
import csv
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import urllib3
from pathlib import Path

# Disable SSL warnings (adjust based on your security requirements)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'fortigate_mgmt_collection_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class FortiManagerConfig:
    """Configuration for FortiManager environment"""
    name: str
    host: str
    port: int = 443
    username: str = ""
    password: str = ""
    api_key: str = ""
    verify_ssl: bool = False

@dataclass
class ManagementInterfaceInfo:
    """Management interface information structure"""
    fortimanager: str
    device_name: str
    device_serial: str
    platform: str
    management_ip: str
    management_interface: str
    management_port: str
    snmp_enabled: str
    snmp_version: str
    device_status: str
    last_seen: str
    location: str

class FortiManagerAPI:
    """FortiManager API client"""
    
    def __init__(self, config: FortiManagerConfig):
        self.config = config
        self.session = requests.Session()
        self.session.verify = config.verify_ssl
        self.base_url = f"https://{config.host}:{config.port}/jsonrpc"
        self.session_id = None
        
    def login(self) -> bool:
        """Login to FortiManager"""
        try:
            if self.config.api_key:
                # API Key authentication
                self.session.headers.update({
                    'Authorization': f'Bearer {self.config.api_key}'
                })
                return True
            else:
                # Username/Password authentication
                login_data = {
                    "id": 1,
                    "method": "exec",
                    "params": [{
                        "url": "/sys/login/user",
                        "data": {
                            "user": self.config.username,
                            "passwd": self.config.password
                        }
                    }]
                }
                
                response = self.session.post(self.base_url, json=login_data)
                response.raise_for_status()
                
                result = response.json()
                if result.get('result', [{}])[0].get('status', {}).get('code') == 0:
                    self.session_id = result.get('session')
                    logger.info(f"Successfully logged into {self.config.name}")
                    return True
                else:
                    logger.error(f"Login failed for {self.config.name}: {result}")
                    return False
                    
        except Exception as e:
            logger.error(f"Login error for {self.config.name}: {str(e)}")
            return False
    
    def logout(self):
        """Logout from FortiManager"""
        try:
            if self.session_id:
                logout_data = {
                    "id": 1,
                    "method": "exec",
                    "params": [{
                        "url": "/sys/logout"
                    }],
                    "session": self.session_id
                }
                self.session.post(self.base_url, json=logout_data)
                logger.info(f"Logged out from {self.config.name}")
        except Exception as e:
            logger.warning(f"Logout error for {self.config.name}: {str(e)}")
    
    def get_managed_devices(self) -> List[Dict]:
        """Get detailed list of managed FortiGate devices"""
        try:
            request_data = {
                "id": 1,
                "method": "get",
                "params": [{
                    "url": "/dvmdb/device",
                    "fields": [
                        "name", "sn", "ip", "mgmt_mode", "os_type", "platform_str",
                        "desc", "conn_status", "last_checked", "mgmt_id", "adm_usr",
                        "adm_pass", "mgmt_if", "prefer_img_ver", "latitude", "longitude"
                    ]
                }]
            }
            
            if self.session_id:
                request_data["session"] = self.session_id
            
            response = self.session.post(self.base_url, json=request_data)
            response.raise_for_status()
            
            result = response.json()
            if result.get('result', [{}])[0].get('status', {}).get('code') == 0:
                devices = result.get('result', [{}])[0].get('data', [])
                logger.info(f"Found {len(devices)} devices in {self.config.name}")
                return devices
            else:
                logger.error(f"Failed to get devices from {self.config.name}: {result}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting devices from {self.config.name}: {str(e)}")
            return []
    
    def get_device_snmp_config(self, device_name: str) -> Dict:
        """Get SNMP configuration for a specific device"""
        try:
            request_data = {
                "id": 1,
                "method": "get",
                "params": [{
                    "url": f"/pm/config/device/{device_name}/vdom/root/system/snmp/sysinfo",
                    "fields": ["status", "description", "contact-info", "location"]
                }]
            }
            
            if self.session_id:
                request_data["session"] = self.session_id
            
            response = self.session.post(self.base_url, json=request_data)
            response.raise_for_status()
            
            result = response.json()
            if result.get('result', [{}])[0].get('status', {}).get('code') == 0:
                snmp_config = result.get('result', [{}])[0].get('data', {})
                logger.debug(f"Retrieved SNMP config for device {device_name}")
                return snmp_config
            else:
                logger.debug(f"No SNMP config found for device {device_name}")
                return {}
                
        except Exception as e:
            logger.warning(f"Error getting SNMP config from device {device_name}: {str(e)}")
            return {}
    
    def get_device_snmp_users(self, device_name: str) -> List[Dict]:
        """Get SNMPv3 users for a specific device"""
        try:
            request_data = {
                "id": 1,
                "method": "get",
                "params": [{
                    "url": f"/pm/config/device/{device_name}/vdom/root/system/snmp/user",
                    "fields": ["name", "security-level", "auth-proto", "priv-proto", "queries"]
                }]
            }
            
            if self.session_id:
                request_data["session"] = self.session_id
            
            response = self.session.post(self.base_url, json=request_data)
            response.raise_for_status()
            
            result = response.json()
            if result.get('result', [{}])[0].get('status', {}).get('code') == 0:
                users = result.get('result', [{}])[0].get('data', [])
                logger.debug(f"Retrieved {len(users)} SNMP users for device {device_name}")
                return users
            else:
                logger.debug(f"No SNMP users found for device {device_name}")
                return []
                
        except Exception as e:
            logger.warning(f"Error getting SNMP users from device {device_name}: {str(e)}")
            return []
    
    def get_device_management_interface(self, device_name: str) -> Dict:
        """Get management interface details for a specific device"""
        try:
            # Get all interfaces to find management interface
            request_data = {
                "id": 1,
                "method": "get",
                "params": [{
                    "url": f"/pm/config/device/{device_name}/vdom/root/system/interface",
                    "fields": ["name", "ip", "allowaccess", "type", "description", "status"]
                }]
            }
            
            if self.session_id:
                request_data["session"] = self.session_id
            
            response = self.session.post(self.base_url, json=request_data)
            response.raise_for_status()
            
            result = response.json()
            if result.get('result', [{}])[0].get('status', {}).get('code') == 0:
                interfaces = result.get('result', [{}])[0].get('data', [])
                
                # Find management interface (usually has 'https', 'ssh', or 'snmp' in allowaccess)
                mgmt_interfaces = []
                for intf in interfaces:
                    allowaccess = intf.get('allowaccess', [])
                    if isinstance(allowaccess, list):
                        access_str = ' '.join(allowaccess)
                    else:
                        access_str = str(allowaccess)
                    
                    if any(access in access_str.lower() for access in ['https', 'ssh', 'snmp', 'ping']):
                        mgmt_interfaces.append(intf)
                
                if mgmt_interfaces:
                    # Return the first management interface found
                    return mgmt_interfaces[0]
                else:
                    logger.debug(f"No management interface found for device {device_name}")
                    return {}
            else:
                logger.warning(f"Failed to get interfaces from device {device_name}")
                return {}
                
        except Exception as e:
            logger.warning(f"Error getting management interface from device {device_name}: {str(e)}")
            return {}

class ManagementInterfaceCollector:
    """Main management interface information collector"""
    
    def __init__(self, fortimanager_configs: List[FortiManagerConfig]):
        self.configs = fortimanager_configs
        self.mgmt_data: List[ManagementInterfaceInfo] = []
    
    def collect_all_management_interfaces(self) -> List[ManagementInterfaceInfo]:
        """Collect management interface information from all FortiManager environments"""
        logger.info("Starting management interface collection process...")
        
        for config in self.configs:
            logger.info(f"Processing FortiManager: {config.name}")
            self._collect_mgmt_from_fortimanager(config)
        
        logger.info(f"Collection complete. Total devices found: {len(self.mgmt_data)}")
        return self.mgmt_data
    
    def _collect_mgmt_from_fortimanager(self, config: FortiManagerConfig):
        """Collect management interfaces from a single FortiManager"""
        fm_api = FortiManagerAPI(config)
        
        try:
            if not fm_api.login():
                logger.error(f"Failed to login to {config.name}")
                return
            
            devices = fm_api.get_managed_devices()
            
            for device in devices:
                device_name = device.get('name', 'Unknown')
                device_serial = device.get('sn', 'Unknown')
                
                logger.info(f"Processing device: {device_name} ({device_serial})")
                
                # Get SNMP configuration
                snmp_config = fm_api.get_device_snmp_config(device_name)
                snmp_users = fm_api.get_device_snmp_users(device_name)
                mgmt_interface = fm_api.get_device_management_interface(device_name)
                
                # Determine SNMP version
                snmp_version = "Unknown"
                if snmp_users:
                    snmp_version = "v3"
                elif snmp_config.get('status') == 'enable':
                    snmp_version = "v2c"
                
                # Extract management IP (prefer interface IP over device IP)
                mgmt_ip = device.get('ip', '')
                if mgmt_interface and mgmt_interface.get('ip'):
                    interface_ip = mgmt_interface.get('ip', [''])[0] if isinstance(mgmt_interface.get('ip'), list) else mgmt_interface.get('ip', '')
                    if interface_ip and interface_ip != '0.0.0.0/0':
                        mgmt_ip = interface_ip.split('/')[0]  # Remove subnet mask if present
                
                mgmt_info = ManagementInterfaceInfo(
                    fortimanager=config.name,
                    device_name=device_name,
                    device_serial=device_serial,
                    platform=device.get('platform_str', 'Unknown'),
                    management_ip=mgmt_ip,
                    management_interface=mgmt_interface.get('name', 'Unknown') if mgmt_interface else 'Unknown',
                    management_port='443',  # Default HTTPS port
                    snmp_enabled='Yes' if snmp_config.get('status') == 'enable' else 'No',
                    snmp_version=snmp_version,
                    device_status=device.get('conn_status', 'Unknown'),
                    last_seen=device.get('last_checked', 'Unknown'),
                    location=snmp_config.get('location', device.get('desc', ''))
                )
                self.mgmt_data.append(mgmt_info)
        
        finally:
            fm_api.logout()
    
    def export_to_csv(self, filename: Optional[str] = None) -> str:
        """Export management interface data to CSV"""
        if not filename:
            filename = f"fortigate_management_interfaces_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        filepath = Path(filename)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'FortiManager', 'Device_Name', 'Device_Serial', 'Platform',
                'Management_IP', 'Management_Interface', 'Management_Port',
                'SNMP_Enabled', 'SNMP_Version', 'Device_Status', 'Last_Seen', 'Location'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for mgmt in self.mgmt_data:
                writer.writerow({
                    'FortiManager': mgmt.fortimanager,
                    'Device_Name': mgmt.device_name,
                    'Device_Serial': mgmt.device_serial,
                    'Platform': mgmt.platform,
                    'Management_IP': mgmt.management_ip,
                    'Management_Interface': mgmt.management_interface,
                    'Management_Port': mgmt.management_port,
                    'SNMP_Enabled': mgmt.snmp_enabled,
                    'SNMP_Version': mgmt.snmp_version,
                    'Device_Status': mgmt.device_status,
                    'Last_Seen': mgmt.last_seen,
                    'Location': mgmt.location
                })
        
        logger.info(f"Management interface data exported to {filepath}")
        return str(filepath)
    
    def export_snmp_store_list(self, filename: Optional[str] = None) -> str:
        """Export SNMP-enabled devices in format compatible with SNMP checker script"""
        if not filename:
            filename = f"snmp_stores_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        filepath = Path(filename)
        
        # Filter only SNMP-enabled devices
        snmp_devices = [mgmt for mgmt in self.mgmt_data if mgmt.snmp_enabled == 'Yes' and mgmt.management_ip]
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['store_name', 'ip', 'device_type']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for mgmt in snmp_devices:
                writer.writerow({
                    'store_name': mgmt.device_name,
                    'ip': mgmt.management_ip,
                    'device_type': mgmt.platform
                })
        
        logger.info(f"SNMP store list exported to {filepath} ({len(snmp_devices)} devices)")
        return str(filepath)
    
    def generate_summary_report(self):
        """Generate summary report"""
        total_devices = len(self.mgmt_data)
        snmp_enabled = len([m for m in self.mgmt_data if m.snmp_enabled == 'Yes'])
        snmpv3_devices = len([m for m in self.mgmt_data if m.snmp_version == 'v3'])
        
        print(f"\n{'='*60}")
        print(f"FORTIGATE MANAGEMENT INTERFACE SUMMARY")
        print(f"{'='*60}")
        print(f"Total Devices: {total_devices}")
        print(f"SNMP Enabled: {snmp_enabled}")
        print(f"SNMPv3 Devices: {snmpv3_devices}")
        print(f"Success Rate: {(snmp_enabled/total_devices)*100:.1f}%" if total_devices > 0 else "N/A")
        
        # Summary by FortiManager
        fm_summary = {}
        for mgmt in self.mgmt_data:
            fm_name = mgmt.fortimanager
            if fm_name not in fm_summary:
                fm_summary[fm_name] = {'total': 0, 'snmp': 0}
            fm_summary[fm_name]['total'] += 1
            if mgmt.snmp_enabled == 'Yes':
                fm_summary[fm_name]['snmp'] += 1
        
        print(f"\nSummary by FortiManager:")
        for fm_name, counts in fm_summary.items():
            print(f"  {fm_name}: {counts['snmp']}/{counts['total']} SNMP enabled")

def main():
    """Main execution function"""
    
    # FortiManager configurations (from your original script)
    fortimanager_configs = [
        FortiManagerConfig(
            name="Arbys Fortimanager",
            host="fmg-vmtm20007492",
            port=443,
            username="ibadmin",
            password="9m!e47IExO7syk@2",
            api_key="E42!yM5Rqzv3#3pZ",
            verify_ssl=False
        ),
        FortiManagerConfig(
            name="BWW Fortimanager",
            host="fmg-vmtm20007517",
            port=443,
            username="ibadmin", 
            password="4@9OJBb4wM@!SExL",
            api_key="*M%CP5^*Dvyec9NX",
            verify_ssl=False
        ),
        FortiManagerConfig(
            name="Sonic Fortimanager",
            host="fmg-vmtm21003463",
            port=443,
            username="ibadmin",
            password="oq+@@61GULn75O_2",
            api_key="U255FmD&kP7k5Rx!",
            verify_ssl=False
        )
    ]
    
    if not fortimanager_configs:
        logger.error("No FortiManager configurations found")
        return
    
    # Initialize collector
    collector = ManagementInterfaceCollector(fortimanager_configs)
    
    # Collect management interface information
    mgmt_interfaces = collector.collect_all_management_interfaces()
    
    if mgmt_interfaces:
        # Export to various formats
        csv_file = collector.export_to_csv()
        snmp_store_file = collector.export_snmp_store_list()
        
        # Generate summary
        collector.generate_summary_report()
        
        print(f"\nManagement interface collection complete!")
        print(f"Detailed export: {csv_file}")
        print(f"SNMP store list: {snmp_store_file}")
        print(f"\nUse '{snmp_store_file}' with the SNMP checker script:")
        print(f"python3 snmp_checker.py -u InspireSNMP -A 'auth_pass' -X 'priv_pass' -f {snmp_store_file}")
    
    else:
        print("No management interface information collected")

if __name__ == "__main__":
    main()