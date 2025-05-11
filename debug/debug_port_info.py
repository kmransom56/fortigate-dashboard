#!/usr/bin/env python3
"""
Debug script to analyze port information from the FortiGate API.
This will help us understand what data is available for each port.
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
    """Main function to debug port information."""
    logger.info("Starting debug script to analyze port information")
    
    # FortiGate connection details
    FORTIGATE_HOST = os.environ.get('FORTIGATE_HOST', '192.168.0.254')
    API_TOKEN_FILE = os.environ.get('FORTIGATE_API_TOKEN_FILE')
    
    if API_TOKEN_FILE and os.path.exists(API_TOKEN_FILE):
        with open(API_TOKEN_FILE, 'r') as f:
            API_TOKEN = f.read().strip()
    else:
        API_TOKEN = os.environ.get('FORTIGATE_API_TOKEN', 'hmNqQ0st7xrjnyQHt8dzpnkqm5hw5N')
    
    # Make sure we don't have double https://
    if FORTIGATE_HOST.startswith('https://'):
        FORTIGATE_HOST = FORTIGATE_HOST.replace('https://', '')
    
    # Set up headers for API requests
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {API_TOKEN}"
    }
    
    # Step 1: Get managed switches
    logger.info("Step 1: Getting managed switches")
    switches_url = f"https://{FORTIGATE_HOST}/api/v2/monitor/switch-controller/managed-switch/status"
    logger.info(f"Using URL: {switches_url}")
    
    try:
        response = requests.get(switches_url, headers=headers, verify=False)
        response.raise_for_status()
        switches_data = response.json()
        
        if 'results' in switches_data:
            switches = switches_data['results']
            logger.info(f"Found {len(switches)} managed switches")
            
            # Process each switch
            for switch in switches:
                switch_id = switch.get('serial')
                logger.info(f"Processing switch: {switch_id}")
                
                # Extract and analyze port information
                if 'ports' in switch and isinstance(switch['ports'], list):
                    logger.info(f"Found {len(switch['ports'])} ports for switch {switch_id}")
                    
                    # Create a file to save port information
                    output_file = f"debug_port_info_{switch_id}.json"
                    with open(output_file, 'w') as f:
                        json.dump(switch['ports'], f, indent=4)
                    logger.info(f"Saved port information to {output_file}")
                    
                    # Log detailed information for specific ports
                    target_ports = ['port1', 'port19', 'port20', 'port21', 'port22', 'port23']
                    for port in switch['ports']:
                        if port.get('interface') in target_ports:
                            logger.info(f"Detailed information for {port.get('interface')}:")
                            pretty_print_json(port)
                            
                            # Check if MAC address is available
                            mac_address = port.get('mac')
                            if mac_address:
                                logger.info(f"MAC address found for {port.get('interface')}: {mac_address}")
                            else:
                                logger.info(f"No MAC address found for {port.get('interface')}")
                                
                                # Check for alternative MAC address fields
                                for key in port.keys():
                                    if 'mac' in key.lower():
                                        logger.info(f"Potential MAC address field found: {key} = {port.get(key)}")
                else:
                    logger.warning(f"No ports found for switch {switch_id}")
        else:
            logger.warning("No 'results' key found in managed switches response")
            logger.warning(f"Response data: {switches_data}")
    except Exception as e:
        logger.error(f"Error getting managed switches: {e}")

if __name__ == "__main__":
    main()
