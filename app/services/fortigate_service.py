# --- START OF fortiswitch_service.py ---
import os
import logging
import requests
from urllib3.exceptions import InsecureRequestWarning
import json

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

logger = logging.getLogger(__name__)

# Environment/defaults
FORTIGATE_HOST = os.environ.get('FORTIGATE_HOST', 'https://192.168.0.254')
FORTISWITCH_HOST = os.environ.get('FORTISWITCH_HOST', '')
FORTISWITCH_USERNAME = os.environ.get('FORTISWITCH_USERNAME', '')
FORTISWITCH_PASSWORD = os.environ.get('FORTISWITCH_PASSWORD', '')

API_TOKEN_FILE = os.environ.get('FORTIGATE_API_TOKEN_FILE')
API_TOKEN = '' # Initialize API_TOKEN

if API_TOKEN_FILE and os.path.exists(API_TOKEN_FILE):
    try:
        with open(API_TOKEN_FILE, 'r') as f:
            API_TOKEN = f.read().strip()
        if not API_TOKEN:
            logger.warning(f"API token file {API_TOKEN_FILE} is empty.")
    except Exception as e:
        logger.error(f"Error reading API token file {API_TOKEN_FILE}: {e}")
        # Fallback to environment variable if file read fails or is empty
        API_TOKEN = os.environ.get('FORTIGATE_API_TOKEN', '')
else:
    # If no file path, directly use environment variable
    API_TOKEN = os.environ.get('FORTIGATE_API_TOKEN', '')

if not API_TOKEN:
    logger.critical("CRITICAL: FortiGate API Token is missing. Set FORTIGATE_API_TOKEN environment variable or configure FORTIGATE_API_TOKEN_FILE.")

# --- Utility Functions ---

def normalize_mac(mac):
    """Normalize MAC to AA:BB:CC:DD:EE:FF uppercase."""
    if not mac or not isinstance(mac, str):
        return None
    mac = mac.strip().replace("-", ":").replace(".", "").replace(" ", "")
    # Handle potential double colons or leading/trailing colons
    mac = ":".join(filter(None, mac.split(':')))
    base = mac.replace(":", "").lower()
    # Check for valid hex characters and length
    if len(base) == 12 and all(c in '0123456789abcdef' for c in base):
        return ":".join(base[i:i+2] for i in range(0, 12, 2)).upper()
    logger.warning(f"Could not normalize MAC address: '{mac}'")
    return mac.upper() # Return best effort uppercase

# --- API Helpers ---

def fgt_api(endpoint, params=None):
    """Helper to make FortiGate API calls."""
    if not API_TOKEN:
        logger.error("FortiGate API Token is missing, cannot make API call.")
        return {} # Return empty dict to avoid downstream errors
    if not endpoint.startswith('/'):
        endpoint = '/' + endpoint
    url = f"{FORTIGATE_HOST}{endpoint}"
    headers = {"Accept": "application/json", "Authorization": f"Bearer {API_TOKEN}"}
    logger.info(f"Calling FGT API: {url} with params: {params}")
    try:
        # Make SSL verification configurable
        verify_ssl_str = os.environ.get('FORTIGATE_VERIFY_SSL', 'false').lower()
        verify_ssl = verify_ssl_str == 'true'
        if not verify_ssl:
            logger.warning(f"SSL verification disabled for FortiGate API ({url}). Set FORTIGATE_VERIFY_SSL=true to enable.")

        res = requests.get(url, headers=headers, params=params, verify=verify_ssl, timeout=20) # Increased timeout
        logger.info(f"FGT API {endpoint} response status: {res.status_code}")

        # Handle specific HTTP errors
        if res.status_code == 401:
            logger.error("FortiGate API Error 401: Unauthorized. Check API Token and trusthost settings.")
            return {}
        elif res.status_code == 403:
            logger.error("FortiGate API Error 403: Forbidden. Check API user permissions.")
            return {}
        elif res.status_code == 404:
            logger.error(f"FortiGate API Error 404: Not Found. Endpoint {endpoint} may be incorrect for this FortiOS version.")
            return {}
        elif res.status_code >= 400:
            # General client/server error
            logger.error(f"FortiGate API error {res.status_code} for {endpoint}: {res.text[:512]}") # Log more context
            return {}

        # Success case
        return res.json()

    except requests.exceptions.Timeout:
        logger.error(f"FGT API request timeout for {endpoint} after 20 seconds.")
        return {}
    except requests.exceptions.SSLError as e:
        logger.error(f"FGT API SSL error for {endpoint}: {e}. If using self-signed certs, ensure FORTIGATE_VERIFY_SSL is false or configure certs correctly.")
        return {}
    except requests.exceptions.ConnectionError as e:
        logger.error(f"FGT API connection error for {endpoint}: {e}. Check hostname/IP and network connectivity.")
        return {}
    except requests.exceptions.RequestException as e:
        # Catch other requests-related errors
        logger.error(f"FGT API request exception for {endpoint}: {e}")
        return {}
    except Exception as e:
        # Catch any other unexpected errors
        logger.error(f"Unexpected error during FGT API call for {endpoint}: {e}", exc_info=True) # Log traceback
        return {}

def fsw_api(endpoint):
    """Helper to make FortiSwitch API calls."""
    if not FORTISWITCH_HOST or not FORTISWITCH_USERNAME or not FORTISWITCH_PASSWORD:
        logger.debug("FortiSwitch credentials/host missing, skipping direct FSW API call to %s.", endpoint)
        return [] # Return empty list as expected by callers
    if not endpoint.startswith('/'):
        endpoint = '/' + endpoint
    url = f"{FORTISWITCH_HOST}{endpoint}"
    logger.info(f"Calling FSW API: {url}")
    try:
        auth = (FORTISWITCH_USERNAME, FORTISWITCH_PASSWORD)
        # Make SSL verification configurable
        verify_ssl_str = os.environ.get('FORTISWITCH_VERIFY_SSL', 'false').lower()
        verify_ssl = verify_ssl_str == 'true'
        if not verify_ssl:
            logger.warning(f"SSL verification disabled for FortiSwitch API ({url}). Set FORTISWITCH_VERIFY_SSL=true to enable.")

        res = requests.get(url, auth=auth, verify=verify_ssl, timeout=20) # Increased timeout
        logger.info(f"FSW API {endpoint} response status: {res.status_code}")

        if res.status_code == 401:
            logger.error("FortiSwitch API Error 401: Unauthorized. Check FSW username/password.")
            return []
        elif res.status_code == 404:
            logger.error(f"FortiSwitch API Error 404: Not Found. Endpoint {endpoint} may be incorrect for this FortiSwitchOS version.")
            return []
        elif res.status_code >= 400:
            logger.error(f"FortiSwitch API error {res.status_code} for {endpoint}: {res.text[:512]}")
            return []

        # Success case
        return res.json()

    except requests.exceptions.Timeout:
        logger.error(f"FSW API request timeout for {endpoint} after 20 seconds.")
        return []
    except requests.exceptions.SSLError as e:
        logger.error(f"FSW API SSL error for {endpoint}: {e}. If using self-signed certs, ensure FORTISWITCH_VERIFY_SSL is false.")
        return []
    except requests.exceptions.ConnectionError as e:
        logger.error(f"FSW API connection error for {endpoint}: {e}. Check hostname/IP and network connectivity.")
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"FSW API request exception for {endpoint}: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error during FSW API call for {endpoint}: {e}", exc_info=True) # Log traceback
        return []

# --- Data Source Wrappers (with logging) ---
def get_managed_switches():
    logger.debug("Fetching managed switch status...")
    try:
        data = fgt_api("/api/v2/monitor/switch-controller/managed-switch/status")
        logger.debug(f"Managed switch status data: {json.dumps(data, indent=2)}")
        return data
    except Exception as e:
        logger.error(f"Error fetching managed switch status: {e}")
        return None

def get_detected_devices():
    logger.debug("Fetching detected devices...")
try:
    # Verify this endpoint in the FortiOS 7.6.3 Monitor API switch-controller.json
    data = fgt_api("/api/v2/monitor/switch-controller/detected-device")
    logger.debug(f"Detected devices raw data: {json.dumps(data, indent=2)}")
    return data
except Exception as e:
    logger.error(f"Error fetching detected devices: {e}")
    return None
        return None

def get_fgt_dhcp():
    logger.debug("Fetching FortiGate DHCP leases...")
    try:
        data = fgt_api("/api/v2/monitor/system/dhcp")
        logger.debug(f"FortiGate DHCP leases data: {json.dumps(data, indent=2)}")
        return data
    except Exception as e:
        logger.error(f"Error fetching FortiGate DHCP leases: {e}")
        return None

def get_fsw_mac_table():
    logger.debug("Fetching FortiSwitch MAC table...")
    try:
        data = fsw_api("/api/v2/monitor/switch/mac-address/")
        logger.debug(f"FortiSwitch MAC table data: {json.dumps(data, indent=2)}")
        return data
    except Exception as e:
        logger.error(f"Error fetching FortiSwitch MAC table: {e}")
        return None

def get_fsw_dhcp_clients():
    logger.debug("Fetching FortiSwitch DHCP snooping clients...")
    try:
        data = fsw_api("/api/v2/monitor/switch/dhcp-snooping-client-db/")
        logger.debug(f"FortiSwitch DHCP snooping clients data: {json.dumps(data, indent=2)}")
        return data
    except Exception as e:
        logger.error(f"Error fetching FortiSwitch DHCP snooping clients: {e}")
        return None
def get_fsw_detailed_mac_table():
    logger.debug("Fetching detailed FortiSwitch MAC table...")
    try:
        # Verify this endpoint in the FortiSwitch 7.6.1 Monitor API switch.json
        data = fsw_api("/api/v2/monitor/switch/mac-address")
        logger.debug(f"Detailed FortiSwitch MAC table data: {json.dumps(data, indent=2)}")
        return data
    except Exception as e:
        logger.error(f"Error fetching detailed FortiSwitch MAC table: {e}")
        return None
# --- Mapping and Extraction (with robust checks) ---

def build_mac_ip_map(dhcp_data):
    logger.debug(f"Building MAC-IP map from DHCP data: {json.dumps(dhcp_data, indent=2)}")
    # ... rest of the function ...
    return macmap

def build_detected_device_map(det_data):
    """Map 'switch_serial:port_name' to list of detected device dicts."""
    devmap = {}
    if not isinstance(det_data, dict):
        logger.warning("FortiGate detected device data is not a dictionary, cannot build map.")
        return devmap
    results = det_data.get("results")
    if not isinstance(results, list):
        logger.warning("No valid 'results' list found in FortiGate detected devices data.")
        return devmap

    logger.info(f"Processing {len(results)} detected device entries from FortiGate.")
    count = 0
    for d in results:
        if not isinstance(d, dict): continue
        sw_serial = d.get("switch_id") # FortiGate uses switch serial here
        port_name = d.get("port_name")
        if sw_serial and port_name:
            key = f"{sw_serial}:{port_name}"
            devmap.setdefault(key, []).append(d)
            count += 1
        else:
            logger.debug(f"Skipping detected device entry with missing switch_id or port_name: {d}")
    logger.info(f"Built map for {count} valid detected device entries.")
    return devmap

def build_fsw_mac_map(mac_table):
    """Map port name to list of mac dicts from FSW MAC table."""
    portmap = {}
    if not isinstance(mac_table, list):
        # Allow None/empty list but warn for other types
        if mac_table is not None:
            logger.warning(f"FortiSwitch MAC table data is not a list (type: {type(mac_table)}), cannot build map.")
        return portmap

    logger.info(f"Processing {len(mac_table)} MAC entries from FortiSwitch.")
    count = 0
    for entry in mac_table:
        if not isinstance(entry, dict): continue
        iface = entry.get("interface")
        if iface:
            portmap.setdefault(iface, []).append(entry)
            count += 1
        else:
            logger.debug(f"Skipping FSW MAC entry with missing interface: {entry}")
    logger.info(f"Built map for {count} valid FSW MAC entries across {len(portmap)} ports.")
    return portmap

def build_fsw_dhcp_map(dhcp_clients):
    """Map normalized MAC to full client dict for FSW DHCP snooping clients."""
    mac_dhcp_map = {}
    if not isinstance(dhcp_clients, list):
        if dhcp_clients is not None:
            logger.warning(f"FortiSwitch DHCP snooping data is not a list (type: {type(dhcp_clients)}), cannot build map.")
        return mac_dhcp_map

    logger.info(f"Processing {len(dhcp_clients)} DHCP snooping entries from FortiSwitch.")
    count = 0
    for c in dhcp_clients:
        if not isinstance(c, dict): continue
        mac = normalize_mac(c.get("mac"))
        if mac:
            mac_dhcp_map[mac] = c
            count += 1
        else:
            logger.debug(f"Skipping FSW DHCP snooping entry with missing MAC: {c}")
    logger.info(f"Built map for {count} valid FSW DHCP snooping entries.")
    return mac_dhcp_map

# --- Aggregation (More robust processing) ---
def collect_devices_per_port(ports_data, switch_serial, detected_map, fsw_mac_map, fsw_dhcp_map, fgt_dhcp_map, fsw_detailed_mac_map):
    for port_data in ports_data:
        port_name = port_data.get("interface", "Unknown")
        logger.debug(f"Processing port {port_name} for switch {switch_serial}")
        # ... rest of the function ...
        current_port_devices = []
        for device in detected_devices:
            mac = normalize_mac(device.get('mac'))
            device_info = {
                'mac': mac,
                'ip': fgt_dhcp_map.get(mac, {}).get('ip', 'Unknown'),
                'hostname': fgt_dhcp_map.get(mac, {}).get('hostname', 'Unknown'),
                'vlan': device.get('vlan_id', 'Unknown'),
                'last_seen': device.get('last_seen', 'Unknown'),
                'detailed_info': fsw_detailed_mac_map.get(mac, {})  # Add detailed info if available
            }
            current_port_devices.append(device_info)
        port_devices_aggregate[port_name] = current_port_devices
    return port_devices_aggregate
# --- Main Service Function ---

def get_fortiswitches_fullview():
    """
    Main function to fetch and aggregate FortiSwitch and connected device data.
    Returns: List of FortiSwitch dictionaries with detailed port and device info.
    """
    logger.info("=== Starting full FortiSwitch discovery and aggregation process ===")

    def get_fortiswitches_fullview():
        # ... existing code ...
    
        switches_raw_data = get_managed_switches()
        detected_devices_data = get_detected_devices()
        fgt_dhcp_data = get_fgt_dhcp()
        fsw_mac_table_data = get_fsw_mac_table()
        fsw_dhcp_clients_data = get_fsw_dhcp_clients()
        fsw_detailed_mac_data = get_fsw_detailed_mac_table()  # New data source
        fsw_detailed_mac_data = get_fsw_detailed_mac_table()  # New data source
    
        # ... rest of the function ...
    fsw_dhcp_clients_data = get_fsw_dhcp_clients()
    logger.info("--- Finished fetching data from APIs ---")

    # 2. Build necessary maps for quick lookup (check for empty/invalid data)
    logger.info("--- Building lookup maps ---")
    fgt_dhcp_map = build_mac_ip_map(fgt_dhcp_data)
    detected_map = build_detected_device_map(detected_devices_data)
    fsw_mac_map = build_fsw_mac_map(fsw_mac_table_data)
    fsw_dhcp_map = build_fsw_dhcp_map(fsw_dhcp_clients_data)
    logger.info("--- Finished building lookup maps ---")

    # 3. Process switches and aggregate devices per port
    final_switch_list = []
    # Safely access nested 'results' list
    switch_results = switches_raw_data.get("results") if isinstance(switches_raw_data, dict) else None

    if not isinstance(switch_results, list):
        logger.error("Managed switch data from FortiGate is not in expected format (missing 'results' list). Cannot process switches.")
        return [] # Return empty list if primary data is missing/invalid

    logger.info(f"--- Processing {len(switch_results)} managed switches ---")
    for sw_data in switch_results:
        if not isinstance(sw_data, dict):
            logger.warning("Skipping invalid switch data entry (not a dictionary).")
            continue

        switch_serial = sw_data.get('serial', 'Unknown')
        switch_id_name = sw_data.get('switch-id', 'Unknown') # Hostname/name

        if switch_serial == 'Unknown':
            logger.warning(f"Skipping switch with unknown serial number: ID={switch_id_name}")
            continue

        logger.info(f"Processing Switch: Name='{switch_id_name}', Serial='{switch_serial}'")
        ports_data = sw_data.get('ports', []) # Get the list of ports for this switch

        # Aggregate devices found on ports of this switch using all collected data maps
        logger.debug(f"Aggregating devices for switch {switch_serial}...")
        port_device_map = collect_devices_per_port(
            ports_data, switch_serial, detected_map,
            fsw_mac_map, fsw_dhcp_map, fgt_dhcp_map
        )
        logger.debug(f"Finished aggregating devices for switch {switch_serial}.")

        # Build the final structure for this switch including detailed port info
        output_ports = []
        if isinstance(ports_data, list):
            for port_data in ports_data:
                if not isinstance(port_data, dict): continue # Skip invalid port data
                port_name = port_data.get('interface', 'Unknown')
                port_info = {
                    'name': port_name,
                    'status': port_data.get('status', 'Unknown'),
                    'speed': port_data.get('speed', 0),
                    'duplex': port_data.get('duplex', 'Unknown'),
                    'vlan': port_data.get('vlan', 'Unknown'),
                    # Get the aggregated & deduplicated devices for this specific port
                    'connected_devices': port_device_map.get(port_name, []) # Default to empty list if port had no devices
                 }
                output_ports.append(port_info)
        else:
            logger.warning(f"Ports data for switch {switch_serial} is not a list (type: {type(ports_data)}), port details will be empty.")


        switch_object = {
            'name': switch_id_name,
            'serial': switch_serial,
            'model': sw_data.get('model', 'Unknown'),
            'status': sw_data.get('status', 'Unknown'),
            'version': sw_data.get('os_version', 'Unknown'),
            'ip': sw_data.get('ip', 'Unknown'),
            'mac': sw_data.get('mac', 'Unknown'),
            'ports': output_ports, # Include the detailed port list with aggregated devices
        }
        final_switch_list.append(switch_object)
        logger.info(f"Finished processing Switch: Name='{switch_id_name}', Serial='{switch_serial}'")

    logger.info(f"=== Finished aggregation process. Returning data for {len(final_switch_list)} switches. ===")
    return final_switch_list

# --- Compatibility Legacy Entry-Point ---
def get_fortiswitch():
    """Alias for backward compatibility."""
    logger.warning("Using deprecated 'get_fortiswitch'. Please update calls to use 'get_fortiswitches_fullview'.")
    return get_fortiswitches_fullview()

# --- Example Usage ---
# To run this file directly for testing:
# 1. Ensure environment variables are set (e.g., FORTIGATE_API_TOKEN, FORTISWITCH_HOST etc.)
# 2. Run: python /path/to/fortiswitch_service.py
if __name__ == '__main__':
    # Setup basic logging to console for testing
    # Use DEBUG level for detailed API call and processing logs
    log_level_str = os.environ.get('LOG_LEVEL', 'DEBUG').upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')

    # Check for API token before proceeding
    if not API_TOKEN:
        logger.critical("API_TOKEN is not set. Cannot run test. Please set FORTIGATE_API_TOKEN or FORTIGATE_API_TOKEN_FILE environment variable.")
    else:
        logger.info("Starting standalone test run of get_fortiswitches_fullview()...")
        try:
            full_switch_data = get_fortiswitches_fullview()

            # Pretty print the JSON output
          
            try:
                print(json.dumps(full_switch_data, indent=2))
                logger.info(f"Successfully retrieved and printed data for {len(full_switch_data)} switches.")
            except TypeError as e:
                logger.error(f"Error serializing final data to JSON: {e}")
                logger.info("Printing raw data structure instead:")
                print(full_switch_data) # Print raw structure if JSON fails

        except Exception as main_e:
            logger.critical(f"An unexpected error occurred during the main test run: {main_e}", exc_info=True)

#
