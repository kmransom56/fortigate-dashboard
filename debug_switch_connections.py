#!/usr/bin/env python3
"""
Debug script to investigate why connected devices aren't showing up in the FortiSwitch dashboard.
This script will:
1. Fetch data from the FortiGate API
2. Process the data using the same logic as the application
3. Print detailed information about the switches and connected devices
"""

import os
import sys
import json
import logging
import requests
from urllib3.exceptions import InsecureRequestWarning

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Try to load environment variables from dotenv if available
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("Loaded environment variables from .env file")
except ImportError:
    logger.warning("dotenv module not found, skipping .env file loading")

# Suppress only the InsecureRequestWarning from urllib3
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# FortiGate connection details
FORTIGATE_HOST = os.environ.get('FORTIGATE_HOST', 'https://192.168.0.254')
API_TOKEN = os.environ.get('FORTIGATE_API_TOKEN', '')

# Get API token from file if specified
API_TOKEN_FILE = os.environ.get('FORTIGATE_API_TOKEN_FILE')

# If API_TOKEN_FILE is not set or the file doesn't exist, try the default location
if not API_TOKEN_FILE or not os.path.exists(API_TOKEN_FILE):
    API_TOKEN_FILE = './secrets/fortigate_api_token.txt'
    logger.info(f"Using default API token file: {API_TOKEN_FILE}")

if os.path.exists(API_TOKEN_FILE):
    with open(API_TOKEN_FILE, 'r') as f:
        API_TOKEN = f.read().strip()
        logger.info(f"Loaded API token from file: {API_TOKEN_FILE}")
else:
    logger.warning(f"API token file not found: {API_TOKEN_FILE}")

def make_api_request(url, headers=None, params=None):
    """Make a request to the FortiGate API with proper error handling and SSL verification."""
    if headers is None:
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {API_TOKEN}"
        }
    
    if params is None:
        params = {}
    
    logger.info(f"Making request to: {url}")
    
    try:
        # Check if certificate file exists
        CERT_PATH = os.environ.get('FORTIGATE_CERT_PATH', None)
        
        if CERT_PATH and os.path.exists(CERT_PATH):
            logger.info(f"Using certificate file for SSL verification: {CERT_PATH}")
            response = requests.get(url, headers=headers, params=params, verify=CERT_PATH, timeout=10)
        else:
            logger.warning(f"Certificate file not found, disabling SSL verification")
            response = requests.get(url, headers=headers, params=params, verify=False, timeout=10)
        
        # Log response information
        logger.info(f"Response status code: {response.status_code}")
        
        # Check if the response is successful
        if response.status_code >= 400:
            logger.error(f"API returned error status code: {response.status_code}")
            logger.error(f"Response content: {response.text[:1000]}...")  # Truncate for readability
            return None
        
        # Parse the response
        data = response.json()
        return data
        
    except Exception as e:
        logger.error(f"Error making request: {e}")
        return None

def get_switch_status():
    """Get FortiSwitch status from FortiGate API."""
    url = f"{FORTIGATE_HOST}/api/v2/monitor/switch-controller/managed-switch/status"
    return make_api_request(url)

def get_detected_devices():
    """Get detected devices from FortiGate API."""
    url = f"{FORTIGATE_HOST}/api/v2/monitor/switch-controller/detected-device"
    return make_api_request(url)

def get_dhcp_info():
    """Get DHCP information from FortiGate API."""
    url = f"{FORTIGATE_HOST}/api/v2/monitor/system/dhcp"
    return make_api_request(url)

def debug_port_status(switch_data):
    """Debug port status information."""
    if not switch_data or not isinstance(switch_data, dict) or 'results' not in switch_data:
        logger.error("Invalid switch data format")
        return
    
    results = switch_data['results']
    logger.info(f"Found {len(results)} FortiSwitches")
    
    for switch in results:
        switch_id = switch.get('switch-id', 'Unknown')
        logger.info(f"Switch: {switch_id} (Serial: {switch.get('serial', 'Unknown')})")
        
        if 'ports' in switch and isinstance(switch['ports'], list):
            # Count ports with different statuses
            up_ports = [p for p in switch['ports'] if p.get('status') == 'up']
            down_ports = [p for p in switch['ports'] if p.get('status') == 'down']
            other_ports = [p for p in switch['ports'] if p.get('status') not in ['up', 'down']]
            
            logger.info(f"Port status summary: {len(up_ports)} up, {len(down_ports)} down, {len(other_ports)} other")
            
            # Log all up ports
            logger.info("UP PORTS:")
            for port in up_ports:
                port_name = port.get('interface', 'Unknown')
                logger.info(f"  - {port_name}")
                
                # Check for connected device information
                if port.get('fgt_peer_device_name'):
                    logger.info(f"    * Connected device (fgt_peer_device_name): {port.get('fgt_peer_device_name')}")
                if port.get('mac_addr'):
                    logger.info(f"    * MAC address (mac_addr): {port.get('mac_addr')}")
                if port.get('ip'):
                    logger.info(f"    * IP address (ip): {port.get('ip')}")
                
                # Log all port properties for debugging
                logger.info(f"    * All properties: {json.dumps(port, indent=2)}")

def debug_detected_devices(detected_devices):
    """Debug detected devices information."""
    if not detected_devices or not isinstance(detected_devices, dict) or 'results' not in detected_devices:
        logger.error("Invalid detected devices format or no devices detected")
        return
    
    results = detected_devices['results']
    logger.info(f"Found {len(results)} detected devices")
    
    for device in results:
        logger.info(f"Detected device:")
        logger.info(f"  - MAC: {device.get('mac', 'Unknown')}")
        logger.info(f"  - Switch: {device.get('switch_id', 'Unknown')}")
        logger.info(f"  - Port: {device.get('port_name', 'Unknown')}")
        logger.info(f"  - VLAN: {device.get('vlan_id', 'Unknown')}")
        logger.info(f"  - Last seen: {device.get('last_seen', 'Unknown')} seconds ago")
        logger.info(f"  - All properties: {json.dumps(device, indent=2)}")

def debug_dhcp_info(dhcp_data):
    """Debug DHCP information."""
    if not dhcp_data or not isinstance(dhcp_data, dict) or 'results' not in dhcp_data:
        logger.error("Invalid DHCP data format or no DHCP information available")
        return
    
    results = dhcp_data['results']
    logger.info(f"Found {len(results)} DHCP entries")
    
    for entry in results:
        logger.info(f"DHCP entry:")
        logger.info(f"  - MAC: {entry.get('mac', 'Unknown')}")
        logger.info(f"  - IP: {entry.get('ip', 'Unknown')}")
        logger.info(f"  - Hostname: {entry.get('hostname', 'Unknown')}")
        logger.info(f"  - All properties: {json.dumps(entry, indent=2)}")

def main():
    """Main function to debug FortiSwitch connections."""
    logger.info("Starting FortiSwitch connection debugging")
    
    # Get switch status
    logger.info("Fetching switch status...")
    switch_data = get_switch_status()
    if switch_data:
        # Save the raw data for reference
        with open("debug_switch_status.json", "w") as f:
            json.dump(switch_data, f, indent=2)
        logger.info("Saved raw switch status data to debug_switch_status.json")
        
        # Debug port status
        debug_port_status(switch_data)
    else:
        logger.error("Failed to get switch status")
    
    # Get detected devices
    logger.info("Fetching detected devices...")
    detected_devices = get_detected_devices()
    if detected_devices:
        # Save the raw data for reference
        with open("debug_detected_devices.json", "w") as f:
            json.dump(detected_devices, f, indent=2)
        logger.info("Saved raw detected devices data to debug_detected_devices.json")
        
        # Debug detected devices
        debug_detected_devices(detected_devices)
    else:
        logger.error("Failed to get detected devices")
    
    # Get DHCP information
    logger.info("Fetching DHCP information...")
    dhcp_data = get_dhcp_info()
    if dhcp_data:
        # Save the raw data for reference
        with open("debug_dhcp_info.json", "w") as f:
            json.dump(dhcp_data, f, indent=2)
        logger.info("Saved raw DHCP information to debug_dhcp_info.json")
        
        # Debug DHCP information
        debug_dhcp_info(dhcp_data)
    else:
        logger.error("Failed to get DHCP information")
    
    logger.info("FortiSwitch connection debugging completed")

if __name__ == "__main__":
    main()