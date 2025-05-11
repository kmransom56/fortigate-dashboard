#!/usr/bin/env python3
"""
Debug script specifically focused on the mac-cache endpoint to understand
what data is being returned for connected devices.
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

# FortiGate connection details
FORTIGATE_HOST = os.environ.get('FORTIGATE_HOST', '192.168.0.254')
API_TOKEN_FILE = os.environ.get('FORTIGATE_API_TOKEN_FILE')

if API_TOKEN_FILE and os.path.exists(API_TOKEN_FILE):
    with open(API_TOKEN_FILE, 'r') as f:
        API_TOKEN = f.read().strip()
else:
    API_TOKEN = os.environ.get('FORTIGATE_API_TOKEN', 'hmNqQ0st7xrjnyQHt8dzpnkqm5hw5N')

def pretty_print_json(data):
    """Print JSON data in a readable format."""
    print(json.dumps(data, indent=4, sort_keys=True))

def main():
    """Main function to test the mac-cache endpoint."""
    logger.info("Starting debug script to test mac-cache endpoint")
    
    # Set up headers for API requests
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {API_TOKEN}"
    }
    
    # Test mac-cache endpoint
    mac_cache_url = f"https://{FORTIGATE_HOST}/api/v2/monitor/switch-controller/mac-cache"
    # Remove any double https:// that might have been introduced
    mac_cache_url = mac_cache_url.replace('https://https://', 'https://')
    logger.info(f"Testing mac-cache endpoint: {mac_cache_url}")
    
    try:
        response = requests.get(mac_cache_url, headers=headers, verify=False)
        response.raise_for_status()
        data = response.json()
        
        logger.info("MAC cache response structure:")
        if 'results' in data:
            logger.info(f"Found {len(data['results'])} entries in mac-cache")
            
            # Print the first few entries as examples
            for i, entry in enumerate(data['results'][:5]):
                logger.info(f"Entry {i+1}:")
                pretty_print_json(entry)
                
            # Check for specific port entries
            for port in ['port1', 'port19', 'port20', 'port21', 'port22', 'port23']:
                port_entries = [e for e in data['results'] if e.get('port') == port]
                if port_entries:
                    logger.info(f"Found {len(port_entries)} entries for {port}")
                    for entry in port_entries:
                        pretty_print_json(entry)
                else:
                    logger.warning(f"No entries found for {port}")
        else:
            logger.warning("No 'results' key found in response")
            pretty_print_json(data)
    except Exception as e:
        logger.error(f"Error testing mac-cache endpoint: {e}")
    
    # Also test port-stats endpoint to see what data is available there
    port_stats_url = f"https://{FORTIGATE_HOST}/api/v2/monitor/switch-controller/port-stats"
    # Remove any double https:// that might have been introduced
    port_stats_url = port_stats_url.replace('https://https://', 'https://')
    logger.info(f"Testing port-stats endpoint: {port_stats_url}")
    
    try:
        response = requests.get(port_stats_url, headers=headers, verify=False)
        response.raise_for_status()
        data = response.json()
        
        logger.info("Port stats response structure:")
        if 'results' in data:
            logger.info(f"Found {len(data['results'])} entries in port-stats")
            
            # Print the first few entries as examples
            for i, entry in enumerate(data['results'][:5]):
                logger.info(f"Entry {i+1}:")
                pretty_print_json(entry)
                
            # Check for specific port entries
            for port in ['port1', 'port19', 'port20', 'port21', 'port22', 'port23']:
                port_entries = [e for e in data['results'] if e.get('port') == port]
                if port_entries:
                    logger.info(f"Found {len(port_entries)} entries for {port}")
                    for entry in port_entries:
                        pretty_print_json(entry)
                else:
                    logger.warning(f"No entries found for {port}")
        else:
            logger.warning("No 'results' key found in response")
            pretty_print_json(data)
    except Exception as e:
        logger.error(f"Error testing port-stats endpoint: {e}")

if __name__ == "__main__":
    main()
