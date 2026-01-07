#!/usr/bin/env python3
"""
Meraki Device Collector for SNMP Testing
Discovers Meraki switches and their management IPs for SNMP monitoring
"""

import requests
import json
import csv
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'meraki_device_collection_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class MerakiConfig:
    """Configuration for Meraki Dashboard API"""
    api_key: str
    base_url: str = "https://api.meraki.com/api/v1"
    org_id: Optional[str] = None

@dataclass
class MerakiDeviceInfo:
    """Meraki device information structure"""
    organization_name: str
    network_name: str
    device_name: str
    device_serial: str
    model: str
    device_type: str
    management_ip: str
    mac_address: str
    firmware_version: str
    status: str
    last_seen: str
    location: str
    tags: str

class MerakiAPI:
    """Meraki Dashboard API client"""
    
    def __init__(self, config: MerakiConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {config.api_key}',
            'Content-Type': 'application/json'
        })
        
        # Rate limiting
        self.rate_limit_delay = 0.1  # 100ms between requests
        
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Make API request with rate limiting and error handling"""
        try:
            # Rate limiting
            time.sleep(self.rate_limit_delay)
            
            url = f"{self.config.base_url}{endpoint}"
            response = self.session.get(url, params=params)
            
            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                logger.warning(f"Rate limited. Waiting {retry_after} seconds...")
                time.sleep(retry_after)
                response = self.session.get(url, params=params)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed for {endpoint}: {str(e)}")
            return None
    
    def get_organizations(self) -> List[Dict]:
        """Get list of organizations"""
        logger.info("Fetching organizations...")
        orgs = self._make_request("/organizations")
        if orgs:
            logger.info(f"Found {len(orgs)} organizations")
            return orgs
        return []
    
    def get_networks(self, org_id: str) -> List[Dict]:
        """Get networks for an organization"""
        logger.info(f"Fetching networks for organization {org_id}...")
        networks = self._make_request(f"/organizations/{org_id}/networks")
        if networks:
            logger.info(f"Found {len(networks)} networks")
            return networks
        return []
    
    def get_network_devices(self, network_id: str) -> List[Dict]:
        """Get devices in a network"""
        logger.debug(f"Fetching devices for network {network_id}...")
        devices = self._make_request(f"/networks/{network_id}/devices")
        if devices:
            logger.debug(f"Found {len(devices)} devices in network")
            return devices
        return []
    
    def get_device_management_interface(self, serial: str) -> Optional[Dict]:
        """Get management interface info for a device"""
        try:
            # Get device management interface
            mgmt_info = self._make_request(f"/devices/{serial}/managementInterface")
            return mgmt_info
        except Exception as e:
            logger.debug(f"Could not get management interface for {serial}: {str(e)}")
            return None
    
    def get_organization_snmp_settings(self, org_id: str) -> Optional[Dict]:
        """Get SNMP settings for organization"""
        try:
            snmp_settings = self._make_request(f"/organizations/{org_id}/snmp")
            return snmp_settings
        except Exception as e:
            logger.debug(f"Could not get SNMP settings for org {org_id}: {str(e)}")
            return None

class MerakiDeviceCollector:
    """Main Meraki device information collector"""
    
    def __init__(self, config: MerakiConfig):
        self.config = config
        self.api = MerakiAPI(config)
        self.device_data: List[MerakiDeviceInfo] = []
    
    def collect_all_devices(self, device_types: List[str] = None) -> List[MerakiDeviceInfo]:
        """Collect device information from Meraki Dashboard"""
        if device_types is None:
            device_types = ['switch', 'wireless', 'appliance', 'camera', 'cellularGateway']
        
        logger.info("Starting Meraki device collection process...")
        
        # Get organizations
        organizations = self.api.get_organizations()
        
        for org in organizations:
            org_id = org['id']
            org_name = org['name']
            
            logger.info(f"Processing organization: {org_name} ({org_id})")
            
            # If specific org_id is configured, only process that one
            if self.config.org_id and org_id != self.config.org_id:
                continue
            
            # Get SNMP settings for organization
            snmp_settings = self.api.get_organization_snmp_settings(org_id)
            
            # Get networks
            networks = self.api.get_networks(org_id)
            
            for network in networks:
                network_id = network['id']
                network_name = network['name']
                
                logger.info(f"  Processing network: {network_name}")
                
                # Get devices in network
                devices = self.api.get_network_devices(network_id)
                
                for device in devices:
                    # Filter by device type if specified
                    device_type = device.get('productType', 'unknown')
                    if device_types and device_type not in device_types:
                        continue
                    
                    self._process_device(device, org_name, network_name, snmp_settings)
        
        logger.info(f"Collection complete. Total devices found: {len(self.device_data)}")
        return self.device_data
    
    def _process_device(self, device: Dict, org_name: str, network_name: str, snmp_settings: Optional[Dict]):
        """Process individual device"""
        device_serial = device.get('serial', 'Unknown')
        device_name = device.get('name', device_serial)
        
        logger.debug(f"    Processing device: {device_name} ({device_serial})")
        
        # Get management interface info
        mgmt_interface = self.api.get_device_management_interface(device_serial)
        
        # Extract management IP
        management_ip = ""
        if mgmt_interface:
            wan1 = mgmt_interface.get('wan1', {})
            management_ip = wan1.get('staticIp', wan1.get('ip', ''))
        
        # If no management IP from interface, try device level
        if not management_ip:
            management_ip = device.get('lanIp', device.get('wan1Ip', ''))
        
        # Create device info
        device_info = MerakiDeviceInfo(
            organization_name=org_name,
            network_name=network_name,
            device_name=device_name,
            device_serial=device_serial,
            model=device.get('model', 'Unknown'),
            device_type=device.get('productType', 'Unknown'),
            management_ip=management_ip,
            mac_address=device.get('mac', ''),
            firmware_version=device.get('firmware', ''),
            status=device.get('status', 'Unknown'),
            last_seen=device.get('lastReportedAt', ''),
            location=device.get('address', device.get('notes', '')),
            tags=', '.join(device.get('tags', []))
        )
        
        self.device_data.append(device_info)
    
    def export_to_csv(self, filename: Optional[str] = None) -> str:
        """Export device data to CSV"""
        if not filename:
            filename = f"meraki_devices_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        filepath = Path(filename)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'Organization', 'Network', 'Device_Name', 'Device_Serial', 'Model',
                'Device_Type', 'Management_IP', 'MAC_Address', 'Firmware_Version',
                'Status', 'Last_Seen', 'Location', 'Tags'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for device in self.device_data:
                writer.writerow({
                    'Organization': device.organization_name,
                    'Network': device.network_name,
                    'Device_Name': device.device_name,
                    'Device_Serial': device.device_serial,
                    'Model': device.model,
                    'Device_Type': device.device_type,
                    'Management_IP': device.management_ip,
                    'MAC_Address': device.mac_address,
                    'Firmware_Version': device.firmware_version,
                    'Status': device.status,
                    'Last_Seen': device.last_seen,
                    'Location': device.location,
                    'Tags': device.tags
                })
        
        logger.info(f"Device data exported to {filepath}")
        return str(filepath)
    
    def export_snmp_store_list(self, filename: Optional[str] = None, device_types: List[str] = None) -> str:
        """Export devices in format compatible with SNMP checker script"""
        if not filename:
            filename = f"meraki_snmp_stores_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        if device_types is None:
            device_types = ['switch']  # Default to switches only
        
        filepath = Path(filename)
        
        # Filter devices with management IPs and specified types
        snmp_devices = [
            device for device in self.device_data 
            if device.management_ip and device.management_ip != '' 
            and device.device_type in device_types
            and device.status == 'online'
        ]
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['store_name', 'ip', 'device_type']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for device in snmp_devices:
                writer.writerow({
                    'store_name': device.device_name,
                    'ip': device.management_ip,
                    'device_type': f"Meraki-{device.model}"
                })
        
        logger.info(f"Meraki SNMP store list exported to {filepath} ({len(snmp_devices)} devices)")
        return str(filepath)
    
    def generate_summary_report(self):
        """Generate summary report"""
        total_devices = len(self.device_data)
        online_devices = len([d for d in self.device_data if d.status == 'online'])
        devices_with_mgmt_ip = len([d for d in self.device_data if d.management_ip])
        
        print(f"\n{'='*60}")
        print(f"MERAKI DEVICE SUMMARY")
        print(f"{'='*60}")
        print(f"Total Devices: {total_devices}")
        print(f"Online Devices: {online_devices}")
        print(f"Devices with Management IP: {devices_with_mgmt_ip}")
        
        # Summary by device type
        type_summary = {}
        for device in self.device_data:
            device_type = device.device_type
            if device_type not in type_summary:
                type_summary[device_type] = {'total': 0, 'online': 0}
            type_summary[device_type]['total'] += 1
            if device.status == 'online':
                type_summary[device_type]['online'] += 1
        
        print(f"\nSummary by Device Type:")
        for device_type, counts in type_summary.items():
            print(f"  {device_type}: {counts['online']}/{counts['total']} online")

def combine_store_lists(fortigate_file: str, meraki_file: str, output_file: Optional[str] = None) -> str:
    """Combine FortiGate and Meraki store lists into single file"""
    if not output_file:
        output_file = f"combined_snmp_stores_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    combined_devices = []
    
    # Read FortiGate devices
    try:
        with open(fortigate_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                combined_devices.append(row)
        logger.info(f"Loaded {len(combined_devices)} FortiGate devices")
    except FileNotFoundError:
        logger.warning(f"FortiGate file {fortigate_file} not found")
    
    # Read Meraki devices
    try:
        with open(meraki_file, 'r') as f:
            reader = csv.DictReader(f)
            meraki_count = 0
            for row in reader:
                combined_devices.append(row)
                meraki_count += 1
        logger.info(f"Loaded {meraki_count} Meraki devices")
    except FileNotFoundError:
        logger.warning(f"Meraki file {meraki_file} not found")
    
    # Write combined file
    with open(output_file, 'w', newline='') as f:
        if combined_devices:
            fieldnames = ['store_name', 'ip', 'device_type']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(combined_devices)
    
    logger.info(f"Combined store list saved to {output_file} ({len(combined_devices)} total devices)")
    return output_file

def main():
    """Main execution function"""
    
    # Meraki API configuration
    # You'll need to get your API key from the Meraki Dashboard
    # Dashboard > Organization > Settings > Dashboard API access
    meraki_config = MerakiConfig(
        api_key="YOUR_MERAKI_API_KEY_HERE",  # Replace with your API key
        # org_id="YOUR_ORG_ID"  # Optional: specify specific organization ID
    )
    
    if meraki_config.api_key == "YOUR_MERAKI_API_KEY_HERE":
        print("Please configure your Meraki API key in the script!")
        print("Get your API key from: Dashboard > Organization > Settings > Dashboard API access")
        return
    
    # Initialize collector
    collector = MerakiDeviceCollector(meraki_config)
    
    # Collect device information (switches only for SNMP testing)
    devices = collector.collect_all_devices(device_types=['switch'])
    
    if devices:
        # Export to various formats
        csv_file = collector.export_to_csv()
        snmp_store_file = collector.export_snmp_store_list()
        
        # Generate summary
        collector.generate_summary_report()
        
        print(f"\nMeraki device collection complete!")
        print(f"Detailed export: {csv_file}")
        print(f"SNMP store list: {snmp_store_file}")
        print(f"\nTo test SNMP connectivity:")
        print(f"python3 snmp_checker.py -u InspireSNMP -A 'auth_pass' -X 'priv_pass' -f {snmp_store_file}")
        
        # Optional: Combine with FortiGate devices
        print(f"\nTo combine with FortiGate devices:")
        print(f"python3 meraki_device_collector.py --combine-with fortigate_snmp_stores.csv")
    
    else:
        print("No Meraki devices found")

if __name__ == "__main__":
    main()