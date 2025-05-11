#!/usr/bin/env python3
"""
Debug script to analyze ARP table information from the FortiGate API.
This will help us understand what data is available for MAC to IP mapping.
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
    """Main function to debug ARP table information."""
    logger.info("Starting debug script to analyze ARP table information")
    
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
    
    # Try different ARP table endpoints
    arp_endpoints = [
        "/api/v2/monitor/system/arp",
        "/api/v2/monitor/router/ipv4/arp",
        "/api/v2/cmdb/system/arp-table"
    ]
    
    for endpoint in arp_endpoints:
        arp_url = f"https://{FORTIGATE_HOST}{endpoint}"
        logger.info(f"Trying ARP table endpoint: {arp_url}")
        
        try:
            response = requests.get(arp_url, headers=headers, verify=False)
            logger.info(f"Response status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"ARP table response keys: {list(data.keys())}")
                
                if 'results' in data and isinstance(data['results'], list):
                    logger.info(f"Found {len(data['results'])} ARP entries")
                    
                    # Save the ARP table to a file
                    output_file = f"debug_arp_table_{endpoint.replace('/', '_')}.json"
                    with open(output_file, 'w') as f:
                        json.dump(data, f, indent=4)
                    logger.info(f"Saved ARP table to {output_file}")
                    
                    # Print the first few entries
                    for i, entry in enumerate(data['results'][:5]):
                        logger.info(f"ARP entry {i}:")
                        pretty_print_json(entry)
                else:
                    logger.warning(f"No 'results' key found in ARP table response for endpoint {endpoint}")
                    logger.warning(f"Response data: {data}")
            else:
                logger.warning(f"Failed to get ARP table from endpoint {endpoint}: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"Error getting ARP table from endpoint {endpoint}: {e}")
    
    # Also try the DHCP server information
    dhcp_url = f"https://{FORTIGATE_HOST}/api/v2/monitor/system/dhcp"
    logger.info(f"Getting DHCP server information: {dhcp_url}")
    
    try:
        response = requests.get(dhcp_url, headers=headers, verify=False)
        logger.info(f"DHCP response status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if 'results' in data and isinstance(data['results'], list):
                logger.info(f"Found {len(data['results'])} DHCP entries")
                
                # Save the DHCP information to a file
                output_file = "debug_dhcp_info_full.json"
                with open(output_file, 'w') as f:
                    json.dump(data, f, indent=4)
                logger.info(f"Saved DHCP information to {output_file}")
                
                # Print the first few entries
                for i, entry in enumerate(data['results'][:5]):
                    logger.info(f"DHCP entry {i}:")
                    pretty_print_json(entry)
            else:
                logger.warning("No 'results' key found in DHCP response")
                logger.warning(f"Response data: {data}")
        else:
            logger.warning(f"Failed to get DHCP information: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"Error getting DHCP information: {e}")

if __name__ == "__main__":
    main()
