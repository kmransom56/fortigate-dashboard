#!/usr/bin/env python3
"""
Debug script to test the FortiGate API and see what data is actually being returned
for connected devices on FortiSwitches.
"""
import os
import sys
import json
import logging
import requests
from urllib3.exceptions import InsecureRequestWarning

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.fortiswitch_manager import FortiSwitchManager

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress only the InsecureRequestWarning from urllib3
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# FortiGate connection details
FORTIGATE_HOST = os.environ.get('FORTIGATE_HOST', '192.168.0.254')
FORTIGATE_URL = f"https://{FORTIGATE_HOST}"
API_TOKEN_FILE = os.environ.get('FORTIGATE_API_TOKEN_FILE')

if API_TOKEN_FILE and os.path.exists(API_TOKEN_FILE):
    with open(API_TOKEN_FILE, 'r') as f:
        API_TOKEN = f.read().strip()
else:
    API_TOKEN = os.environ.get('FORTIGATE_API_TOKEN', 'hmNqQ0st7xrjnyQHt8dzpnkqm5hw5N')

def pretty_print_json(data):
    """Print JSON data in a readable format."""
    print(json.dumps(data, indent=4, sort_keys=True))

def test_api_endpoint(url, headers, verify=False):
    """Test an API endpoint and return the response."""
    try:
        logger.info(f"Testing API endpoint: {url}")
        response = requests.get(url, headers=headers, verify=verify)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error testing API endpoint: {e}")
        return None

def main():
    """Main function to test the FortiGate API."""
    logger.info("Starting debug script to test FortiGate API")
    
    # Initialize FortiSwitchManager
    fortiswitch_manager = FortiSwitchManager(
        fortigate_ip=FORTIGATE_HOST, 
        api_token=API_TOKEN, 
        verify_ssl=False
    )
    
    # Get managed switches
    logger.info("Getting managed switches")
    managed_switches_result = fortiswitch_manager.get_managed_switches()
    if managed_switches_result.get('success', False):
        switches = managed_switches_result.get('switches', [])
        logger.info(f"Found {len(switches)} managed switches")
        
        # Test each switch
        for switch in switches:
            switch_id = switch.get('serial')
            logger.info(f"Testing switch: {switch_id}")
            
            # 1. Test mac-cache endpoint
            headers = {
                "Accept": "application/json",
                "Authorization": f"Bearer {API_TOKEN}"
            }
            mac_cache_url = f"https://{FORTIGATE_HOST}/api/v2/monitor/switch-controller/mac-cache"
            mac_cache_data = test_api_endpoint(mac_cache_url, headers)
            
            if mac_cache_data:
                logger.info("MAC cache data structure:")
                if 'results' in mac_cache_data:
                    # Show the first entry as an example
                    if mac_cache_data['results']:
                        logger.info("Example MAC cache entry:")
                        pretty_print_json(mac_cache_data['results'][0])
                    else:
                        logger.info("No MAC cache entries found")
                else:
                    logger.info("Unexpected MAC cache data structure")
                    pretty_print_json(mac_cache_data)
            
            # 2. Test port-stats endpoint
            port_stats_url = f"https://{FORTIGATE_HOST}/api/v2/monitor/switch-controller/port-stats"
            port_stats_data = test_api_endpoint(port_stats_url, headers)
            
            if port_stats_data:
                logger.info("Port stats data structure:")
                if 'results' in port_stats_data:
                    # Filter for this switch and show the first entry as an example
                    switch_ports = [p for p in port_stats_data['results'] 
                                   if p.get('switch_id') == switch_id or p.get('switch', '').lower() == switch_id.lower()]
                    if switch_ports:
                        logger.info(f"Found {len(switch_ports)} ports for switch {switch_id}")
                        logger.info("Example port stats entry:")
                        pretty_print_json(switch_ports[0])
                    else:
                        logger.info(f"No port stats found for switch {switch_id}")
                else:
                    logger.info("Unexpected port stats data structure")
                    pretty_print_json(port_stats_data)
            
            # 3. Test network-monitor endpoint (FortiOS 7.0+)
            network_monitor_url = f"https://{FORTIGATE_HOST}/api/v2/monitor/switch-controller/network-monitor"
            network_monitor_data = test_api_endpoint(network_monitor_url, headers)
            
            if network_monitor_data:
                logger.info("Network monitor data structure:")
                if 'results' in network_monitor_data:
                    # Show the first entry as an example
                    if network_monitor_data['results']:
                        logger.info("Example network monitor entry:")
                        pretty_print_json(network_monitor_data['results'][0])
                    else:
                        logger.info("No network monitor entries found")
                else:
                    logger.info("Unexpected network monitor data structure")
                    pretty_print_json(network_monitor_data)
            
            # 4. Test ARP table
            arp_result = fortiswitch_manager.get_arp_table()
            logger.info("ARP table data structure:")
            if arp_result.get('success', False):
                # Show a sample of the ARP map
                arp_map = arp_result.get('arp_map', {})
                if arp_map:
                    sample_entries = list(arp_map.items())[:5]
                    logger.info(f"Found {len(arp_map)} ARP entries")
                    logger.info("Sample ARP entries:")
                    for mac, ip in sample_entries:
                        logger.info(f"MAC: {mac}, IP: {ip}")
                else:
                    logger.info("No ARP entries found")
            else:
                logger.error(f"Failed to retrieve ARP table: {arp_result.get('error', 'Unknown error')}")
            
            # 5. Test device database
            device_url = f"https://{FORTIGATE_HOST}/api/v2/cmdb/user/device"
            device_data = test_api_endpoint(device_url, headers)
            
            if device_data:
                logger.info("Device database data structure:")
                if 'results' in device_data:
                    # Show the first entry as an example
                    if device_data['results']:
                        logger.info("Example device database entry:")
                        pretty_print_json(device_data['results'][0])
                    else:
                        logger.info("No device database entries found")
                else:
                    logger.info("Unexpected device database data structure")
                    pretty_print_json(device_data)
            
            # 6. Test DHCP snooping
            dhcp_snooping_url = f"https://{FORTIGATE_HOST}/api/v2/monitor/switch-controller/managed-switch/dhcp-snooping"
            params = {"switch_id": switch_id}
            try:
                dhcp_response = requests.get(dhcp_snooping_url, headers=headers, params=params, verify=False)
                if dhcp_response.status_code == 200:
                    dhcp_data = dhcp_response.json()
                    logger.info("DHCP snooping data structure:")
                    pretty_print_json(dhcp_data)
                else:
                    logger.warning(f"Failed to retrieve DHCP snooping data: {dhcp_response.status_code}")
            except Exception as e:
                logger.error(f"Error retrieving DHCP snooping data: {e}")
            
            # Only test the first switch for brevity
            break
    else:
        logger.error(f"Failed to retrieve managed switches: {managed_switches_result.get('message', 'Unknown error')}")

if __name__ == "__main__":
    main()
