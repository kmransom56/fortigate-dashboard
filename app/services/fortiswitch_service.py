import os
import logging
import requests
from urllib3.exceptions import InsecureRequestWarning

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
        # Check if certificate file exists
        CERT_PATH = os.environ.get('FORTIGATE_CERT_PATH', None)
        if CERT_PATH and os.path.exists(CERT_PATH):
            logger.info(f"Using certificate file for SSL verification in FortiSwitch request: {CERT_PATH}")
            # Check if the file is readable
            try:
                with open(CERT_PATH, 'r') as f:
                    cert_content = f.read()
                    logger.info(f"Certificate file is readable for FortiSwitch request, content length: {len(cert_content)} bytes")
                    
                # Try to create an SSL context with the certificate
                import ssl
                context = ssl.create_default_context(cafile=CERT_PATH)
                logger.info("Successfully created SSL context with certificate for FortiSwitch request")
                
                # Use the certificate for verification
                response = requests.get(url, headers=headers, params=params, verify=CERT_PATH, timeout=10)
                logger.info("FortiSwitch request with certificate verification successful")
            except Exception as cert_error:
                logger.error(f"Error using certificate file for FortiSwitch request: {cert_error}")
                logger.warning("Falling back to disabling SSL verification for FortiSwitch request")
                response = requests.get(url, headers=headers, params=params, verify=False, timeout=10)
        else:
            logger.warning(f"Certificate file not found at {CERT_PATH}, disabling SSL verification")
            response = requests.get(url, headers=headers, params=params, verify=False, timeout=10)
        
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
        
        # Process the response
        return process_fortiswitch_data(data, dhcp_info)
        
    except Exception as e:
        logger.error(f"Error making request to FortiGate API: {e}")
        raise

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
        # Check if certificate file exists
        CERT_PATH = os.environ.get('FORTIGATE_CERT_PATH', None)
        if CERT_PATH and os.path.exists(CERT_PATH):
            logger.info(f"Using certificate file for SSL verification in DHCP request: {CERT_PATH}")
            try:
                response = requests.get(url, headers=headers, verify=CERT_PATH, timeout=10)
                logger.info("DHCP request with certificate verification successful")
            except Exception as cert_error:
                logger.error(f"Error using certificate file for DHCP request: {cert_error}")
                logger.warning("Falling back to disabling SSL verification for DHCP request")
                response = requests.get(url, headers=headers, verify=False, timeout=10)
        else:
            logger.warning(f"Certificate file not found at {CERT_PATH}, disabling SSL verification for DHCP request")
            response = requests.get(url, headers=headers, verify=False, timeout=10)
        
        logger.info(f"DHCP API response status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Create a dictionary mapping MAC addresses to IP addresses and hostnames
            mac_to_info = {}
            if 'results' in data and isinstance(data['results'], list):
                logger.info(f"DHCP API returned {len(data['results'])} entries")
                for entry in data['results']:
                    # Store both uppercase and lowercase versions of the MAC address
                    mac_original = entry.get('mac', '')
                    mac_upper = mac_original.upper()
                    mac_lower = mac_original.lower()
                    
                    # Also store versions without colons
                    mac_upper_no_colons = mac_upper.replace(':', '')
                    mac_lower_no_colons = mac_lower.replace(':', '')
                    
                    logger.info(f"DHCP entry: MAC={mac_original}, IP={entry.get('ip', 'Unknown')}, Hostname={entry.get('hostname', 'Unknown')}")
                    
                    if mac_original:
                        info = {
                            'ip': entry.get('ip', 'Unknown'),
                            'hostname': entry.get('hostname', 'Unknown')
                        }
                        # Store multiple versions of the MAC address for flexible matching
                        mac_to_info[mac_upper] = info
                        mac_to_info[mac_lower] = info
                        mac_to_info[mac_upper_no_colons] = info
                        mac_to_info[mac_lower_no_colons] = info
                
                logger.info(f"Found {len(data['results'])} DHCP entries, created {len(mac_to_info)} MAC address mappings")
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
    switches = []
    
    # Check if the response is a dictionary with a 'results' key
    if isinstance(data, dict) and 'results' in data and isinstance(data['results'], list):
        results = data['results']
        logger.info(f"Found {len(results)} FortiSwitches in 'results' list")
        
        for switch in results:
            # Log the full switch data for debugging
            logger.debug(f"Processing switch: {switch}")
            
            # Extract relevant information
            switch_info = {
                'name': switch.get('switch-id', 'Unknown'),
                'serial': switch.get('serial', 'Unknown'),
                'model': switch.get('model', 'Unknown'),
                'status': switch.get('status', 'Unknown'),
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
                    if port.get('status') == 'up' and port.get('fgt_peer_device_name'):
                        device_name = port.get('fgt_peer_device_name', 'Unknown')
                        
                        # Try to find MAC address in the device name (if it's a MAC address)
                        device_mac = 'Unknown'
                        if ':' in device_name or '-' in device_name:
                            # It's already a formatted MAC address
                            device_mac = device_name
                        else:
                            # Check if it's a MAC address without separators
                            if len(device_name) == 12 and all(c in '0123456789ABCDEFabcdef' for c in device_name):
                                # Format as MAC address with colons
                                device_mac = ':'.join(device_name[i:i+2] for i in range(0, 12, 2))
                            else:
                                # Try to find MAC address in DHCP info
                                logger.info(f"Looking for device MAC in DHCP info: {device_name}")
                                
                                # Try different formats of the device name for matching
                                device_name_upper = device_name.upper()
                                device_name_lower = device_name.lower()
                                device_name_formatted = ':'.join(device_name[i:i+2] for i in range(0, len(device_name), 2))
                                device_name_formatted_upper = device_name_formatted.upper()
                                device_name_formatted_lower = device_name_formatted.lower()
                                
                                logger.info(f"Trying to match: {device_name}, {device_name_upper}, {device_name_lower}, {device_name_formatted}, {device_name_formatted_upper}, {device_name_formatted_lower}")
                                
                                # Check if any of these formats are in the DHCP info
                                if device_name_upper in dhcp_info:
                                    logger.info(f"Found match for {device_name_upper} in DHCP info")
                                    device_mac = device_name_formatted_upper
                                    break
                                elif device_name_lower in dhcp_info:
                                    logger.info(f"Found match for {device_name_lower} in DHCP info")
                                    device_mac = device_name_formatted_lower
                                    break
                                elif device_name_formatted_upper in dhcp_info:
                                    logger.info(f"Found match for {device_name_formatted_upper} in DHCP info")
                                    device_mac = device_name_formatted_upper
                                    break
                                elif device_name_formatted_lower in dhcp_info:
                                    logger.info(f"Found match for {device_name_formatted_lower} in DHCP info")
                                    device_mac = device_name_formatted_lower
                                    break
                                else:
                                    # Try the old way of comparing
                                    for mac, info in dhcp_info.items():
                                        # Remove colons for comparison
                                        clean_mac = mac.replace(':', '')
                                        clean_device_name = device_name.replace(':', '')
                                        
                                        logger.info(f"Comparing {clean_mac.lower()} with {clean_device_name.lower()}")
                                        
                                        if clean_mac.lower() == clean_device_name.lower():
                                            logger.info(f"Found match: {mac} == {device_name}")
                                            device_mac = mac
                                            break
                                    
                                if device_mac == 'Unknown':
                                    logger.warning(f"Could not find MAC address {device_name} in DHCP info")
                        
                        # Get IP address from DHCP info if available
                        device_ip = 'Unknown'
                        device_type = 'Unknown'
                        
                        # Check if we have DHCP info for this MAC address
                        if device_mac != 'Unknown':
                            formatted_mac = device_mac.upper()
                            if formatted_mac in dhcp_info:
                                device_ip = dhcp_info[formatted_mac]['ip']
                                # Use hostname as device type if available
                                if dhcp_info[formatted_mac]['hostname'] != 'Unknown':
                                    device_type = dhcp_info[formatted_mac]['hostname']
                        
                        device = {
                            'port': port.get('interface', 'Unknown'),
                            'device_name': device_name,
                            'device_mac': device_mac,
                            'device_ip': device_ip,
                            'device_type': device_type
                        }
                        switch_info['connected_devices'].append(device)
                    
                    switch_info['ports'].append(port_info)
            
            switches.append(switch_info)
    else:
        logger.warning("Unexpected response format from FortiGate API")
        logger.warning(f"Response data: {data}")
    
    if not switches:
        logger.warning("No FortiSwitches found in FortiGate API response")
    else:
        logger.info(f"Successfully processed {len(switches)} FortiSwitches")
    
    return switches