import os
import logging
import requests
from urllib3.exceptions import InsecureRequestWarning
from app.services.fortiswitch_manager import FortiSwitchManager

# Suppress only the InsecureRequestWarning from urllib3
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Configure logging
logger = logging.getLogger(__name__)

# FortiGate connection details
FORTIGATE_HOST = os.environ.get('FORTIGATE_HOST', 'https://192.168.0.254')

# Get API token from environment or file
API_TOKEN_FILE = os.environ.get('FORTIGATE_API_TOKEN_FILE')
if API_TOKEN_FILE and os.path.exists(API_TOKEN_FILE):
    with open(API_TOKEN_FILE, 'r') as f:
        API_TOKEN = f.read().strip()
else:
    API_TOKEN = os.environ.get('FORTIGATE_API_TOKEN', 'hmNqQ0st7xrjnyQHt8dzpnkqm5hw5N')

# Initialize FortiSwitchManager
fortiswitch_manager = FortiSwitchManager(fortigate_ip=FORTIGATE_HOST, api_token=API_TOKEN, verify_ssl=False)

def debug_dhcp_info(dhcp_info):
    """Print out the DHCP info for debugging."""
    logger.info(f"DHCP info contains {len(dhcp_info)} entries")
    for idx, (mac, info) in enumerate(list(dhcp_info.items())[:10]):  # First 10 entries
        logger.info(f"DHCP entry {idx}: MAC={mac}, IP={info['ip']}, Hostname={info['hostname']}")

def get_fortiswitches():
    """
    Get FortiSwitch information from FortiGate API.
    
    According to the FortiOS 7.6.3 API documentation, the correct endpoint is:
    /api/v2/monitor/switch-controller/managed-switch/status
    """
    # Use Authorization header with Bearer token
    url = f"{FORTIGATE_HOST}/api/v2/monitor/switch-controller/managed-switch/status"
    params = {}
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {API_TOKEN}"
    }
    
    logger.info(f"Making request to FortiGate API for FortiSwitch information: {url}")
    
    # Variable to store the response
    response = None
    
    try:
        # MODIFIED: Always disable SSL verification for testing
        logger.warning("SSL verification disabled for testing")
        response = requests.get(url, headers=headers, params=params, verify=False, timeout=30)
        
        # Log response information
        logger.info(f"FortiGate API response status code: {response.status_code}")
        
        # Check if the response is successful
        if response.status_code >= 400:
            logger.error(f"FortiGate API returned error status code: {response.status_code}")
            logger.error(f"Response content: {response.text[:1000]}...")  # Truncate for readability
            
            if response.status_code == 401:
                logger.error("Authentication failed (401 Unauthorized)")
                logger.error("Possible causes:")
                logger.error("1. Invalid API token")
                logger.error("2. IP restrictions: Only 192.168.0.0/24 network is allowed (trusthost)")
                logger.error("3. CORS restrictions: Only https://192.168.0.20:80 is allowed")
                logger.error("Check your client IP and ensure it's within the allowed network")
                
            raise Exception(f"FortiGate API error: {response.status_code} - {response.text}")
        
        # Parse the response
        data = response.json()
        logger.info(f"FortiGate API response data type: {type(data)}")
        
        # Log the full response for debugging
        logger.debug(f"Full API response: {data}")
        
        # Get DHCP information to map MAC addresses to IP addresses
        dhcp_info = get_dhcp_info()
        
        # Debug DHCP info
        debug_dhcp_info(dhcp_info)
        
        # Process the response
        return process_fortiswitch_data(data, dhcp_info)
        
    except Exception as e:
        logger.error(f"Error making request to FortiGate API: {e}")
        raise

def change_fortiswitch_ip(switch_serial, new_ip, new_netmask="255.255.255.0"):
    """
    Change the IP address of a FortiSwitch managed by the FortiGate.
    
    Args:
        switch_serial (str): Serial number of the FortiSwitch
        new_ip (str): New IP address to assign to the FortiSwitch
        new_netmask (str): Network mask to use with the new IP
        
    Returns:
        dict: Response with success status and message
    """
    logger.info(f"Changing IP address for FortiSwitch {switch_serial} to {new_ip}/{new_netmask}")
    
    if not API_TOKEN:
        error_msg = "FortiGate API Token is missing, cannot change FortiSwitch IP."
        logger.error(error_msg)
        return {
            "success": False,
            "message": error_msg
        }
    
    # FortiGate API endpoint for managing a specific switch
    endpoint = f"/api/v2/cmdb/switch-controller/managed-switch/{switch_serial}"
    
    # Prepare the data payload for the PUT request
    data = {
        "fsw-wan1-admin": "enable",
        "fsw-wan1-ip": new_ip,
        "fsw-wan1-netmask": new_netmask
    }
   
    try:
        # Make SSL verification configurable
        verify_ssl_str = os.environ.get('FORTIGATE_VERIFY_SSL', 'false').lower()
        verify_ssl = verify_ssl_str == 'true'
        
        # Construct the URL
        url = f"{FORTIGATE_HOST}{endpoint}"
        
        # Set up headers with authentication
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_TOKEN}"
        }
        
        logger.debug(f"Sending PUT request to {url} with data: {data}")
        
        # Make the PUT request to update the FortiSwitch IP
        res = requests.put(
            url, 
            headers=headers, 
            json=data, 
            verify=verify_ssl, 
            timeout=20
        )
        
        logger.info(f"FortiGate API PUT {endpoint} response status: {res.status_code}")
        
        # Handle specific HTTP errors
        if res.status_code == 401:
            error_msg = "FortiGate API Error 401: Unauthorized. Check API Token and trusthost settings."
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg
            }
        elif res.status_code == 403:
            error_msg = "FortiGate API Error 403: Forbidden. Check API user permissions."
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg
            }
        elif res.status_code == 404:
            error_msg = f"FortiGate API Error 404: Not Found. Switch {switch_serial} may not exist or endpoint is incorrect."
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg
            }
        elif res.status_code >= 400:
            # General client/server error
            error_msg = f"FortiGate API error {res.status_code} for {endpoint}: {res.text[:512]}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg
            }
        
        # Success case
        success_msg = f"Successfully changed IP address for FortiSwitch {switch_serial} to {new_ip}/{new_netmask}"
        logger.info(success_msg)
        return {
            "success": True,
            "message": success_msg,
            "data": res.json()
        }
        
    except requests.exceptions.Timeout:
        error_msg = f"FortiGate API request timeout after 20 seconds while changing IP for switch {switch_serial}."
        logger.error(error_msg)
        return {
            "success": False,
            "message": error_msg
        }
    except requests.exceptions.SSLError as e:
        error_msg = f"FortiGate API SSL error while changing IP for switch {switch_serial}: {e}"
        logger.error(error_msg)
        return {
            "success": False,
            "message": error_msg
        }
    except requests.exceptions.ConnectionError as e:
        error_msg = f"FortiGate API connection error while changing IP for switch {switch_serial}: {e}"
        logger.error(error_msg)
        return {
            "success": False,
            "message": error_msg
        }
    except requests.exceptions.RequestException as e:
        error_msg = f"FortiGate API request exception while changing IP for switch {switch_serial}: {e}"
        logger.error(error_msg)
        return {
            "success": False,
            "message": error_msg
        }
    except Exception as e:
        error_msg = f"Unexpected error during FortiGate API call to change IP for switch {switch_serial}: {e}"
        logger.error(error_msg, exc_info=True)
        return {
            "success": False,
            "message": error_msg
        }

def get_dhcp_info():
    """
    Get DHCP information from FortiGate API to map MAC addresses to IP addresses.
    """
    url = f"{FORTIGATE_HOST}/api/v2/monitor/system/dhcp"
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {API_TOKEN}"
    }
    
    logger.info(f"Making request to FortiGate API for DHCP information: {url}")
    
    try:
        # MODIFIED: Always disable SSL verification for testing
        logger.warning("SSL verification disabled for DHCP request")
        response = requests.get(url, headers=headers, verify=False, timeout=30)
        
        logger.info(f"DHCP API response status code: {response.status_code}")
        
        # Add detailed logging of the DHCP response
        logger.info(f"Raw DHCP API response (first 1000 chars): {response.text[:1000]}...")
        
        if response.status_code == 200:
            data = response.json()
            
            # Log the structure of the response
            logger.info(f"DHCP API response structure: {list(data.keys())}")
            
            # Create a dictionary mapping MAC addresses to IP addresses and hostnames
            mac_to_info = {}
            if 'results' in data and isinstance(data['results'], list):
                logger.info(f"DHCP API returned {len(data['results'])} entries")
                
                # Print first few entries for debugging
                for i, entry in enumerate(data['results'][:5]):  # First 5 entries
                    logger.info(f"DHCP entry {i}: {entry}")
                
                for entry in data['results']:
                    # Store both uppercase and lowercase versions of the MAC address
                    mac_original = entry.get('mac', '')
                    
                    # Skip empty MAC addresses
                    if not mac_original:
                        continue
                        
                    mac_upper = mac_original.upper()
                    mac_lower = mac_original.lower()
                    
                    # Also store versions without colons
                    mac_upper_no_colons = mac_upper.replace(':', '')
                    mac_lower_no_colons = mac_lower.replace(':', '')
                    
                    logger.info(f"DHCP entry: MAC={mac_original}, IP={entry.get('ip', 'Unknown')}, Hostname={entry.get('hostname', 'Unknown')}")
                    
                    info = {
                        'ip': entry.get('ip', 'Unknown'),
                        'hostname': entry.get('hostname', 'Unknown')
                    }
                    
                    # Store multiple versions of the MAC address for flexible matching
                    mac_to_info[mac_upper] = info
                    mac_to_info[mac_lower] = info
                    mac_to_info[mac_upper_no_colons] = info
                    mac_to_info[mac_lower_no_colons] = info
                
                # Log the keys in mac_to_info for debugging
                logger.info(f"Found {len(data['results'])} DHCP entries, created {len(mac_to_info)} MAC address mappings")
                sample_keys = list(mac_to_info.keys())[:10] if mac_to_info else []
                logger.info(f"Sample MAC addresses in DHCP info: {sample_keys}")
                
                # Specifically check if our problematic MAC exists
                test_mac = "E023FF6F4A80"
                test_mac_formatted = "E0:23:FF:6F:4A:80"
                if test_mac in mac_to_info:
                    logger.info(f"Found {test_mac} in DHCP info: {mac_to_info[test_mac]}")
                else:
                    logger.info(f"{test_mac} not found in DHCP info")
                
                if test_mac_formatted in mac_to_info:
                    logger.info(f"Found {test_mac_formatted} in DHCP info: {mac_to_info[test_mac_formatted]}")
                else:
                    logger.info(f"{test_mac_formatted} not found in DHCP info")
                
            return mac_to_info
        else:
            logger.error(f"DHCP API error: {response.status_code} - {response.text}")
            return {}
    except Exception as e:
        logger.error(f"Error getting DHCP information: {e}")
        return {}

def process_fortiswitch_data(data, dhcp_info):
    """
    Process the FortiGate API response data and extract FortiSwitch information.
    
    The response format is a dictionary with a 'results' key that contains an array of FortiSwitch objects.
    """
    # Initialize the list to store switch information
    switches = []
    
    # Check if the response is a dictionary with a 'results' key
    if isinstance(data, dict) and 'results' in data and isinstance(data['results'], list):
        results = data['results']
        logger.info(f"Found {len(results)} FortiSwitches in 'results' list")
        
        for switch in results:
            # Log the full switch data for debugging
            logger.debug(f"Processing switch: {switch}")
            
            # Map the API status to the dashboard status
            status_mapping = {
                'Connected': 'online',
                'Authorized/Up': 'online',
                'Authorized': 'online'
            }
            
            # Get the original status from the API
            original_status = switch.get('status', 'Unknown')
            logger.info(f"Switch {switch.get('serial', 'Unknown')} has original status: '{original_status}'")
            
            # Map the status to a dashboard status if it exists in the mapping
            # Otherwise, keep the original status
            dashboard_status = status_mapping.get(original_status, original_status)
            logger.info(f"Mapped status for switch {switch.get('serial', 'Unknown')}: '{original_status}' -> '{dashboard_status}'")
            
            # Extract relevant information
            switch_info = {
                'name': switch.get('switch-id', 'Unknown'),
                'serial': switch.get('serial', 'Unknown'),
                'model': switch.get('model', 'Unknown'),
                'status': dashboard_status,  # Use the mapped status instead of the original
                'version': switch.get('os_version', 'Unknown'),
                'ip': switch.get('ip', 'Unknown'),
                'mac': switch.get('mac', 'Unknown'),
                'ports': [],
                'connected_devices': []
            }
            
            # Extract port information
            if 'ports' in switch and isinstance(switch['ports'], list):
                for port in switch['ports']:
                    # Log the full port data for debugging
                    logger.debug(f"Processing port: {port}")
                    
                    port_info = {
                        'name': port.get('interface', 'Unknown'),
                        'status': port.get('status', 'Unknown'),
                        'speed': port.get('speed', 0),
                        'duplex': port.get('duplex', 'Unknown'),
                        'vlan': port.get('vlan', 'Unknown')
                    }
                    
                    # Add connected device information if available
                    if port.get('status') == 'up' or port.get('fgt_peer_device_name'):
                        device_name = port.get('fgt_peer_device_name', 'Unknown')
                        logger.debug(f"Active port: {port}")
                        logger.debug(f"Device name: {device_name}")

                        # Validate and normalize MAC address
                        device_mac = 'Unknown'
                        if len(device_name) == 12 and all(c in '0123456789ABCDEFabcdef' for c in device_name):
                            device_mac = ':'.join(device_name[i:i+2] for i in range(0, 12, 2)).upper()
                            logger.debug(f"Formatted 12-char MAC: {device_name} -> {device_mac}")
                        elif ':' in device_name or '-' in device_name:
                            device_mac = device_name.replace('-', ':').upper()
                            logger.debug(f"Normalized MAC with separators: {device_name} -> {device_mac}")

                        logger.debug(f"Normalized MAC address: {device_mac}")

                        # Generate all possible formats for lookup
                        possible_formats = [
                            device_mac,  # E0:23:FF:6F:4A:80
                            device_mac.lower(),  # e0:23:ff:6f:4a:80
                            device_mac.replace(':', ''),  # E023FF6F4A80
                            device_mac.lower().replace(':', '')  # e023ff6f4a80
                        ]

                        # Match MAC address with DHCP info
                        device_ip = 'Unknown'
                        device_type = 'Unknown'
                        match_found = False

                        for mac_format in possible_formats:
                            if mac_format in dhcp_info:
                                device_ip = dhcp_info[mac_format]['ip']
                                device_type = dhcp_info[mac_format]['hostname']
                                logger.info(f"Found match for {mac_format} in DHCP info: IP={device_ip}, Type={device_type}")
                                match_found = True
                                break

                        if not match_found:
                            logger.warning(f"MAC address not found in DHCP info. Tried formats: {possible_formats}")
                            # Log some keys from the dhcp_info dictionary for debugging
                            sample_keys = list(dhcp_info.keys())[:5] if dhcp_info else []
                            logger.warning(f"Sample MAC addresses in DHCP info: {sample_keys}")

                        device = {
                            'port': port.get('interface', 'Unknown'),
                            'device_name': device_name,
                            'device_mac': device_mac,
                            'device_ip': device_ip,
                            'device_type': device_type
                        }
                        switch_info['connected_devices'].append(device)

                    switch_info['ports'].append(port_info)
            
            # Add the switch info to our list
            switches.append(switch_info)
    else:
        logger.warning("Unexpected response format from FortiGate API")
        logger.warning(f"Response data: {data}")

    if not switches:
        logger.warning("No FortiSwitches found in FortiGate API response")
    else:
        logger.info(f"Successfully processed {len(switches)} FortiSwitches")

    return switches

def get_connected_devices_workflow():
    """
    Enhanced workflow to identify connected devices using FortiSwitchManager.
    Combines data from multiple sources for more complete device information.
    """
    try:
        # Get all managed switches
        managed_switches_result = fortiswitch_manager.get_managed_switches()
        logger.debug(f"Managed switches result: {managed_switches_result}")
        if not managed_switches_result.get('success', False):
            logger.error(f"Failed to retrieve managed switches: {managed_switches_result.get('message', 'Unknown error')}")
            return []

        # Get ARP table for IP mapping
        arp_result = fortiswitch_manager.get_arp_table()
        logger.debug(f"ARP table result: {arp_result}")
        if not arp_result.get('success', False):
            logger.warning(f"Failed to retrieve ARP table: {arp_result.get('message', 'Unknown error')}")

        # Get user device database for device identification
        device_result = fortiswitch_manager.get_user_device_list()
        logger.debug(f"User device list result: {device_result}")
        if not device_result.get('success', False):
            logger.warning(f"Failed to retrieve device list: {device_result.get('message', 'Unknown error')}")

        # Process each switch
        all_switches = []
        for switch in managed_switches_result.get('switches', []):
            switch_id = switch.get('serial')
            logger.info(f"Processing switch: {switch_id}")

            # Get enhanced connected devices info
            connected_devices_result = fortiswitch_manager.get_connected_devices(switch_id=switch_id)
            logger.debug(f"Connected devices result for switch {switch_id}: {connected_devices_result}")

            switch_info = {
                **switch,  # Include all switch details
                'connected_devices': connected_devices_result.get('devices', []) if connected_devices_result.get('success', False) else []
            }

            # Get port information
            port_result = fortiswitch_manager.get_switch_ports(switch_id=switch_id)
            logger.debug(f"Port result for switch {switch_id}: {port_result}")
            if port_result.get('success', False):
                switch_info['ports'] = port_result.get('ports', [])
            else:
                logger.error(f"Failed to retrieve port information for switch {switch_id}")
                switch_info['ports'] = []

            logger.debug(f"Final switch info for {switch_id}: {switch_info}")
            all_switches.append(switch_info)

        return all_switches

    except Exception as e:
        logger.error(f"Error in connected devices workflow: {e}", exc_info=True)
        return []