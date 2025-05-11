#!/usr/bin/env python3
"""
Debug script to analyze the connected devices data from the FortiGate API.
This will help us understand what data is available and how to display it correctly.
"""
import os
import sys
import json
import logging
import requests
from urllib3.exceptions import InsecureRequestWarning

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress only the InsecureRequestWarning from urllib3
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def pretty_print_json(data):
    """Print JSON data in a readable format."""
    print(json.dumps(data, indent=4, sort_keys=True))

def main():
    """Main function to debug connected devices data."""
    logger.info("Starting debug script to analyze connected devices data")
    
    # FortiGate connection details
    FORTIGATE_HOST = os.environ.get('FORTIGATE_HOST', '192.168.0.254')
    API_TOKEN_FILE = os.environ.get('FORTIGATE_API_TOKEN_FILE')
    
    if API_TOKEN_FILE and os.path.exists(API_TOKEN_FILE):
        with open(API_TOKEN_FILE, 'r') as f:
            API_TOKEN = f.read().strip()
    else:
        API_TOKEN = os.environ.get('FORTIGATE_API_TOKEN', 'hmNqQ0st7xrjnyQHt8dzpnkqm5hw5N')
    
    # Set up headers for API requests
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {API_TOKEN}"
    }
    
    # Step 1: Get managed switches
    logger.info("Step 1: Getting managed switches")
    # Make sure we don't have double https://
    if FORTIGATE_HOST.startswith('https://'):
        FORTIGATE_HOST = FORTIGATE_HOST.replace('https://', '')
    switches_url = f"https://{FORTIGATE_HOST}/api/v2/monitor/switch-controller/managed-switch/status"
    logger.info(f"Using URL: {switches_url}")
    try:
        response = requests.get(switches_url, headers=headers, verify=False)
        response.raise_for_status()
        switches_data = response.json()
        
        if 'results' in switches_data:
            switches = switches_data['results']
            logger.info(f"Found {len(switches)} managed switches")
            
            # Print the first switch as an example
            if switches:
                logger.info("Example switch data:")
                pretty_print_json(switches[0])
                
                # Get the first switch ID for further testing
                switch_id = switches[0].get('serial')
                logger.info(f"Using switch ID: {switch_id}")
                
                # Step 2: Get MAC cache information
                logger.info("Step 2: Getting MAC cache information")
                mac_cache_url = f"https://{FORTIGATE_HOST}/api/v2/monitor/switch-controller/mac-cache"
                try:
                    response = requests.get(mac_cache_url, headers=headers, verify=False)
                    response.raise_for_status()
                    mac_data = response.json()
                    
                    if 'results' in mac_data:
                        mac_entries = mac_data['results']
                        logger.info(f"Found {len(mac_entries)} MAC cache entries")
                        
                        # Filter entries for the selected switch
                        switch_entries = [e for e in mac_entries if e.get('switch_id') == switch_id or e.get('switch', '').lower() == switch_id.lower()]
                        logger.info(f"Found {len(switch_entries)} MAC cache entries for switch {switch_id}")
                        
                        # Print the entries for each port
                        for port in ['port1', 'port19', 'port20', 'port21', 'port22', 'port23']:
                            port_entries = [e for e in switch_entries if e.get('port') == port]
                            if port_entries:
                                logger.info(f"Found {len(port_entries)} entries for {port}")
                                for entry in port_entries:
                                    logger.info(f"Entry for {port}:")
                                    pretty_print_json(entry)
                            else:
                                logger.warning(f"No MAC cache entries found for {port}")
                    else:
                        logger.warning("No 'results' key found in MAC cache response")
                        pretty_print_json(mac_data)
                except Exception as e:
                    logger.error(f"Error getting MAC cache information: {e}")
                
                # Step 3: Get port stats information
                logger.info("Step 3: Getting port stats information")
                port_stats_url = f"https://{FORTIGATE_HOST}/api/v2/monitor/switch-controller/port-stats"
                try:
                    response = requests.get(port_stats_url, headers=headers, verify=False)
                    response.raise_for_status()
                    port_stats_data = response.json()
                    
                    if 'results' in port_stats_data:
                        port_stats = port_stats_data['results']
                        logger.info(f"Found {len(port_stats)} port stats entries")
                        
                        # Filter entries for the selected switch
                        switch_ports = [p for p in port_stats if p.get('switch_id') == switch_id or p.get('switch', '').lower() == switch_id.lower()]
                        logger.info(f"Found {len(switch_ports)} port stats entries for switch {switch_id}")
                        
                        # Print the entries for each port
                        for port in ['port1', 'port19', 'port20', 'port21', 'port22', 'port23']:
                            port_entries = [p for p in switch_ports if p.get('port') == port]
                            if port_entries:
                                logger.info(f"Found {len(port_entries)} port stats entries for {port}")
                                for entry in port_entries:
                                    logger.info(f"Port stats for {port}:")
                                    pretty_print_json(entry)
                            else:
                                logger.warning(f"No port stats entries found for {port}")
                    else:
                        logger.warning("No 'results' key found in port stats response")
                        pretty_print_json(port_stats_data)
                except Exception as e:
                    logger.error(f"Error getting port stats information: {e}")
                
                # Step 4: Get ARP table information
                logger.info("Step 4: Getting ARP table information")
                arp_url = f"https://{FORTIGATE_HOST}/api/v2/monitor/system/arp"
                try:
                    response = requests.get(arp_url, headers=headers, verify=False)
                    response.raise_for_status()
                    arp_data = response.json()
                    
                    if 'results' in arp_data:
                        arp_entries = arp_data['results']
                        logger.info(f"Found {len(arp_entries)} ARP table entries")
                        
                        # Print the first few entries as examples
                        for i, entry in enumerate(arp_entries[:5]):
                            logger.info(f"ARP entry {i+1}:")
                            pretty_print_json(entry)
                    else:
                        logger.warning("No 'results' key found in ARP table response")
                        pretty_print_json(arp_data)
                except Exception as e:
                    logger.error(f"Error getting ARP table information: {e}")
                
                # Step 5: Get device database information
                logger.info("Step 5: Getting device database information")
                device_url = f"https://{FORTIGATE_HOST}/api/v2/cmdb/user/device"
                try:
                    response = requests.get(device_url, headers=headers, verify=False)
                    response.raise_for_status()
                    device_data = response.json()
                    
                    if 'results' in device_data:
                        devices = device_data['results']
                        logger.info(f"Found {len(devices)} device database entries")
                        
                        # Print the first few entries as examples
                        for i, device in enumerate(devices[:5]):
                            logger.info(f"Device entry {i+1}:")
                            pretty_print_json(device)
                    else:
                        logger.warning("No 'results' key found in device database response")
                        pretty_print_json(device_data)
                except Exception as e:
                    logger.error(f"Error getting device database information: {e}")
            else:
                logger.warning("No managed switches found")
        else:
            logger.warning("No 'results' key found in managed switches response")
            pretty_print_json(switches_data)
    except Exception as e:
        logger.error(f"Error getting managed switches: {e}")

if __name__ == "__main__":
    main()
