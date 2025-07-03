# --- START OF fortiswitch_service_improved.py ---
import os
import logging
import requests
import time
from urllib3.exceptions import InsecureRequestWarning
import urllib3

# Suppress only the InsecureRequestWarning from urllib3
urllib3.disable_warnings(InsecureRequestWarning)

logger = logging.getLogger(__name__)

# Import session management
from app.services.fortigate_session import FortiGateSessionManager

# Environment/defaults
FORTIGATE_HOST = os.environ.get("FORTIGATE_HOST", "https://192.168.0.254")
FORTISWITCH_HOST = os.environ.get("FORTISWITCH_HOST", "")
FORTISWITCH_USERNAME = os.environ.get("FORTISWITCH_USERNAME", "")
FORTISWITCH_PASSWORD = os.environ.get("FORTISWITCH_PASSWORD", "")

# Initialize session manager
session_manager = FortiGateSessionManager()

# Legacy token support for fallback
API_TOKEN_FILE = os.environ.get("FORTIGATE_API_TOKEN_FILE")
API_TOKEN = ""  # Initialize API_TOKEN

if API_TOKEN_FILE and os.path.exists(API_TOKEN_FILE):
    try:
        with open(API_TOKEN_FILE, "r") as f:
            API_TOKEN = f.read().strip()
        if not API_TOKEN:
            logger.warning(f"API token file {API_TOKEN_FILE} is empty.")
    except Exception as e:
        logger.error(f"Error reading API token file {API_TOKEN_FILE}: {e}")
        # Fallback to environment variable if file read fails or is empty
        API_TOKEN = os.environ.get("FORTIGATE_API_TOKEN", "")
else:
    # If no file path, directly use environment variable
    API_TOKEN = os.environ.get("FORTIGATE_API_TOKEN", "")

if not API_TOKEN and not session_manager.password:
    logger.critical(
        "CRITICAL: Neither FortiGate session credentials nor API Token are available. "
        "Configure session authentication or set FORTIGATE_API_TOKEN."
    )

# Rate limiting globals - IMPROVED: Reduced from 10s to 2s for better responsiveness
last_api_call_time = 0
min_api_interval = 2.0  # Minimum 2 seconds between API calls (was 10s)

# --- Utility Functions ---


def normalize_mac(mac):
    """Normalize MAC to AA:BB:CC:DD:EE:FF uppercase with improved error handling."""
    if not mac or not isinstance(mac, str):
        return None

    # Remove common separators and whitespace
    mac = mac.strip().replace("-", ":").replace(".", ":").replace(" ", "")

    # Handle cases where there are no separators (12 hex chars)
    if ":" not in mac and len(mac) == 12:
        # Insert colons every 2 characters
        mac = ":".join(mac[i : i + 2] for i in range(0, 12, 2))

    # Split by colon and filter out empty parts
    parts = [part for part in mac.split(":") if part]

    # Validate we have exactly 6 parts of 2 hex chars each
    if len(parts) != 6:
        logger.warning(f"Invalid MAC address format (wrong number of parts): '{mac}'")
        return mac.upper()  # Return best effort

    # Validate each part is 2 hex characters
    normalized_parts = []
    for part in parts:
        if len(part) == 1:
            part = "0" + part  # Pad single digit with leading zero
        elif len(part) != 2:
            logger.warning(f"Invalid MAC address part length: '{part}' in '{mac}'")
            return mac.upper()  # Return best effort

        # Check if all characters are hex
        if not all(c in "0123456789abcdefABCDEF" for c in part):
            logger.warning(f"Invalid hex characters in MAC part: '{part}' in '{mac}'")
            return mac.upper()  # Return best effort

        normalized_parts.append(part.upper())

    return ":".join(normalized_parts)


# --- API Helpers ---


def fgt_api(endpoint, params=None):
    """Helper to make FortiGate API calls with session authentication (preferred) or token fallback."""
    global last_api_call_time

    # Rate limiting: ensure minimum interval between calls
    current_time = time.time()
    elapsed = current_time - last_api_call_time
    if elapsed < min_api_interval:
        sleep_time = min_api_interval - elapsed
        logger.debug(f"Rate limiting: sleeping {sleep_time:.1f}s before API call")
        time.sleep(sleep_time)

    # Try session authentication first
    if session_manager.password:
        try:
            # Ensure endpoint format is correct for session manager
            if endpoint.startswith("/api/v2/"):
                api_endpoint = endpoint[8:]  # Remove "/api/v2/" prefix
            else:
                api_endpoint = endpoint

            logger.info(
                f"Making API request to: {endpoint} (FortiGate: {FORTIGATE_HOST}) using session authentication"
            )
            result = session_manager.make_api_request(api_endpoint)
            last_api_call_time = time.time()
            return result
        except Exception as e:
            logger.warning(f"Session authentication failed for {endpoint}: {e}")
            logger.info("Falling back to token authentication")

    # Fallback to token authentication
    if not API_TOKEN:
        logger.error("Neither session authentication nor API token is available.")
        return {}

    logger.info(
        f"Making API request to: {endpoint} (FortiGate: {FORTIGATE_HOST}) using token authentication"
    )

    if not endpoint.startswith("/"):
        endpoint = "/" + endpoint
    url = f"{FORTIGATE_HOST}{endpoint}"
    headers = {"Accept": "application/json", "Authorization": f"Bearer {API_TOKEN}"}

    try:
        # Make SSL verification configurable
        verify_ssl_str = os.environ.get("FORTIGATE_VERIFY_SSL", "false").lower()
        verify_ssl = verify_ssl_str == "true"

        res = requests.get(
            url, headers=headers, params=params, verify=verify_ssl, timeout=20
        )
        last_api_call_time = time.time()

        logger.debug(f"FGT API {endpoint} response status: {res.status_code}")

        # Handle specific HTTP errors
        if res.status_code == 401:
            logger.error(
                "FortiGate API Error 401: Unauthorized. Check API Token and trusthost settings."
            )
            return {}
        elif res.status_code == 403:
            logger.error(
                "FortiGate API Error 403: Forbidden. Check API user permissions."
            )
            return {}
        elif res.status_code == 404:
            logger.error(
                f"FortiGate API Error 404: Not Found. Endpoint {endpoint} may be incorrect for this FortiOS version."
            )
            return {}
        elif res.status_code == 429:
            logger.warning(
                f"FortiGate API rate limit exceeded (429) for {endpoint}. Waiting 30s before retry."
            )
            time.sleep(30)  # Reduced from 60s to 30s
            # Retry once after waiting
            try:
                res = requests.get(
                    url, headers=headers, params=params, verify=verify_ssl, timeout=20
                )
                last_api_call_time = time.time()
                if res.status_code == 200:
                    return res.json()
                else:
                    logger.error(
                        f"FortiGate API retry failed with status {res.status_code} for {endpoint}"
                    )
                    return {}
            except Exception as retry_e:
                logger.error(f"FortiGate API retry exception for {endpoint}: {retry_e}")
                return {}
        elif res.status_code >= 400:
            # General client/server error
            logger.error(
                f"FortiGate API error {res.status_code} for {endpoint}: {res.text[:512]}"
            )
            return {}

        # Success case
        return res.json()

    except requests.exceptions.RequestException as e:
        logger.error(f"FortiGate API request exception for {endpoint}: {e}")
        return {}
    except Exception as e:
        logger.error(f"FortiGate API unexpected error for {endpoint}: {e}")
        return {}


# --- Data Source Wrappers (with logging) ---


def get_managed_switches():
    """Fetch managed switch status from FortiGate."""
    logger.debug("Fetching managed switch status...")
    data = fgt_api("/api/v2/monitor/switch-controller/managed-switch/status")
    logger.debug("Finished fetching managed switch status.")
    return data


def get_detected_devices():
    """Fetch detected devices from FortiGate switch controller."""
    logger.debug("Fetching detected devices...")
    data = fgt_api("/api/v2/monitor/switch-controller/detected-device")
    logger.debug("Finished fetching detected devices.")
    return data


def get_fgt_dhcp():
    """Fetch DHCP lease info from FortiGate."""
    logger.debug("Fetching FortiGate DHCP leases...")
    data = fgt_api("/api/v2/monitor/system/dhcp")
    logger.debug("Finished fetching FortiGate DHCP leases.")
    return data


def get_system_arp():
    """Fetch ARP table from FortiGate for additional device discovery."""
    logger.debug("Fetching FortiGate ARP table...")
    data = fgt_api("/api/v2/monitor/system/arp")
    logger.debug("Finished fetching FortiGate ARP table.")
    return data


# --- Mapping and Extraction (IMPROVED) ---


def build_mac_ip_map(dhcp_data):
    """Map normalized MAC to IP/host info from FortiGate DHCP table."""
    macmap = {}
    if not isinstance(dhcp_data, dict):
        logger.warning("FortiGate DHCP data is not a dictionary, cannot build map.")
        return macmap
    results = dhcp_data.get("results")
    if not isinstance(results, list):
        logger.warning("No valid 'results' list found in FortiGate DHCP data.")
        return macmap

    logger.info(f"Processing {len(results)} DHCP entries from FortiGate.")
    count = 0
    for entry in results:
        if not isinstance(entry, dict):
            continue  # Skip invalid entries
        mac = normalize_mac(entry.get("mac"))
        if mac:
            macmap[mac] = {
                "ip": entry.get("ip", "Unknown"),
                "hostname": entry.get("hostname", ""),
                "interface": entry.get("interface", ""),  # Add interface info
                "expire_time": entry.get("expire_time", 0),
                "status": entry.get("status", "unknown"),
            }
            count += 1
    logger.info(f"Built DHCP map for {count} valid entries.")
    return macmap


def build_arp_map(arp_data):
    """Map normalized MAC to IP info from FortiGate ARP table."""
    arp_map = {}
    if not isinstance(arp_data, dict):
        logger.warning("FortiGate ARP data is not a dictionary, cannot build map.")
        return arp_map
    results = arp_data.get("results")
    if not isinstance(results, list):
        logger.warning("No valid 'results' list found in FortiGate ARP data.")
        return arp_map

    logger.info(f"Processing {len(results)} ARP entries from FortiGate.")
    count = 0
    for entry in results:
        if not isinstance(entry, dict):
            continue
        mac = normalize_mac(entry.get("mac"))
        if mac:
            arp_map[mac] = {
                "ip": entry.get("ip", "Unknown"),
                "interface": entry.get("interface", ""),
                "age": entry.get("age", 0),
            }
            count += 1
    logger.info(f"Built ARP map for {count} valid entries.")
    return arp_map


def build_detected_device_map(det_data):
    """Map 'switch_serial:port_name' to list of detected device dicts."""
    devmap = {}
    if not isinstance(det_data, dict):
        logger.warning(
            "FortiGate detected device data is not a dictionary, cannot build map."
        )
        return devmap
    results = det_data.get("results")
    if not isinstance(results, list):
        logger.warning(
            "No valid 'results' list found in FortiGate detected devices data."
        )
        return devmap

    logger.info(f"Processing {len(results)} detected device entries from FortiGate.")
    count = 0
    for d in results:
        if not isinstance(d, dict):
            continue
        sw_serial = d.get("switch_id")  # FortiGate uses switch serial here
        port_name = d.get("port_name")
        if sw_serial and port_name:
            key = f"{sw_serial}:{port_name}"
            devmap.setdefault(key, []).append(d)
            count += 1
            logger.debug(f"Added detected device: {key} -> MAC: {d.get('mac')}")
        else:
            logger.debug(
                f"Skipping detected device entry with missing switch_id or port_name: {d}"
            )
    logger.info(f"Built detected device map for {count} valid entries.")
    return devmap


# --- IMPROVED Device Aggregation ---


def collect_devices_per_port_improved(
    ports_data, switch_serial, detected_map, dhcp_map, arp_map
):
    """
    IMPROVED: Aggregates devices for each port from all sources, with better matching logic.
    Returns dict: {port_name: [device_info_dict, ...]}
    """
    port_devices_aggregate = {}
    if not isinstance(ports_data, list):
        logger.warning(
            f"Ports data for switch {switch_serial} is not a list (type: {type(ports_data)}). Skipping device aggregation for this switch."
        )
        return {}

    logger.debug(
        f"Aggregating devices for switch {switch_serial} with {len(ports_data)} ports."
    )

    # Process each port
    for port_data in ports_data:
        if not isinstance(port_data, dict):
            continue  # Skip invalid port entries

        port_name = port_data.get("interface", "Unknown")
        if port_name == "Unknown":
            logger.warning(
                f"Skipping port with unknown interface name in switch {switch_serial}"
            )
            continue

        current_port_devices = []
        seen_macs_on_port = set()  # Track MACs added for this specific port

        # --- Source 1: Detected Devices (from FortiGate switch-controller) ---
        detected_key = f"{switch_serial}:{port_name}"
        detected_devices = detected_map.get(detected_key, [])

        logger.debug(
            f"Port {port_name}: Found {len(detected_devices)} detected devices"
        )

        for device in detected_devices:
            if not isinstance(device, dict):
                continue
            mac = normalize_mac(device.get("mac"))
            if mac and mac not in seen_macs_on_port:
                # Get additional info from DHCP and ARP
                dhcp_info = dhcp_map.get(mac, {})
                arp_info = arp_map.get(mac, {})

                # Prefer DHCP hostname, fallback to ARP, then default
                hostname = dhcp_info.get("hostname") or f"Device-{port_name}"
                ip_address = dhcp_info.get("ip") or arp_info.get("ip", "Unknown")

                device_info = {
                    "device_mac": mac,
                    "device_ip": ip_address,
                    "device_type": hostname,
                    "source": "switch_controller_detected",
                    "vlan": device.get("vlan_id", "N/A"),
                    "last_seen": device.get("last_seen", 0),
                    "port_id": device.get("port_id", 0),
                }
                current_port_devices.append(device_info)
                seen_macs_on_port.add(mac)
                logger.debug(
                    f"Port {port_name}: Added detected device {hostname} ({mac})"
                )

        # Store the aggregated list for this port
        port_devices_aggregate[port_name] = current_port_devices

        if current_port_devices:
            logger.info(
                f"Switch {switch_serial}, Port {port_name}: Aggregated {len(current_port_devices)} devices"
            )

    return port_devices_aggregate


# --- Main Service Function (IMPROVED) ---


def get_fortiswitches_fullview_improved():
    """
    IMPROVED: Main function to fetch and aggregate FortiSwitch and connected device data.
    Returns: List of FortiSwitch dictionaries with detailed port and device info.
    """
    logger.info(
        "=== Starting IMPROVED FortiSwitch discovery and aggregation process ==="
    )

    # 1. Fetch raw data from multiple sources
    logger.info("--- Fetching data from APIs ---")
    switches_raw_data = get_managed_switches()
    detected_devices_data = get_detected_devices()
    fgt_dhcp_data = get_fgt_dhcp()
    arp_data = get_system_arp()  # Additional data source

    logger.info("--- Finished fetching data from APIs ---")

    # 2. Build necessary maps for quick lookup
    logger.info("--- Building lookup maps ---")
    dhcp_map = build_mac_ip_map(fgt_dhcp_data)
    arp_map = build_arp_map(arp_data)
    detected_map = build_detected_device_map(detected_devices_data)

    logger.info(
        f"Built maps: DHCP={len(dhcp_map)}, ARP={len(arp_map)}, Detected={len(detected_map)}"
    )
    logger.info("--- Finished building lookup maps ---")

    # 3. Process switches and aggregate devices per port
    final_switch_list = []
    switch_results = (
        switches_raw_data.get("results")
        if isinstance(switches_raw_data, dict)
        else None
    )

    if not isinstance(switch_results, list):
        logger.error(
            "Managed switch data from FortiGate is not in expected format (missing 'results' list). Cannot process switches."
        )
        return []

    logger.info(f"--- Processing {len(switch_results)} managed switches ---")
    for sw_data in switch_results:
        if not isinstance(sw_data, dict):
            logger.warning("Skipping invalid switch data entry (not a dictionary).")
            continue

        switch_serial = sw_data.get("serial", "Unknown")
        switch_id_name = sw_data.get("switch-id", "Unknown")

        if switch_serial == "Unknown":
            logger.warning(
                f"Skipping switch with unknown serial number: ID={switch_id_name}"
            )
            continue

        logger.info(
            f"Processing Switch: Name='{switch_id_name}', Serial='{switch_serial}'"
        )
        ports_data = sw_data.get("ports", [])

        # Use improved device aggregation
        logger.debug(f"Aggregating devices for switch {switch_serial}...")
        port_device_map = collect_devices_per_port_improved(
            ports_data, switch_serial, detected_map, dhcp_map, arp_map
        )
        logger.debug(f"Finished aggregating devices for switch {switch_serial}.")

        # Build the final structure for this switch
        output_ports = []
        if isinstance(ports_data, list):
            for port_data in ports_data:
                if not isinstance(port_data, dict):
                    continue
                port_name = port_data.get("interface", "Unknown")
                port_info = {
                    "name": port_name,
                    "status": port_data.get("status", "Unknown"),
                    "speed": port_data.get("speed", 0),
                    "duplex": port_data.get("duplex", "Unknown"),
                    "vlan": port_data.get("vlan", "Unknown"),
                    "poe_capable": port_data.get("poe_capable", False),
                    "poe_status": port_data.get("poe_status", "disabled"),
                    "fortilink_port": port_data.get("fortilink_port", False),
                    # Get the aggregated devices for this specific port
                    "connected_devices": port_device_map.get(port_name, []),
                }
                output_ports.append(port_info)

        switch_object = {
            "name": switch_id_name,
            "serial": switch_serial,
            "model": sw_data.get("model", "Unknown"),
            "status": sw_data.get("status", "Unknown"),
            "version": sw_data.get("os_version", "Unknown"),
            "ip": sw_data.get("connecting_from", "Unknown"),
            "mac": sw_data.get("mac", "Unknown"),
            "ports": output_ports,
        }
        final_switch_list.append(switch_object)
        logger.info(
            f"Finished processing Switch: Name='{switch_id_name}', Serial='{switch_serial}'"
        )

    logger.info(
        f"=== Finished IMPROVED aggregation process. Returning data for {len(final_switch_list)} switches. ==="
    )
    return final_switch_list


# --- Compatibility Entry-Point ---
def get_fortiswitches():
    """Entry point that uses the improved version."""
    return get_fortiswitches_fullview_improved()


# --- Example Usage ---
if __name__ == "__main__":
    # Setup basic logging to console for testing
    log_level_str = os.environ.get("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    logging.basicConfig(
        level=log_level, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )

    # Check for authentication before proceeding
    if not API_TOKEN and not session_manager.password:
        logger.critical(
            "No authentication available. Please set FORTIGATE_API_TOKEN or configure session authentication."
        )
    else:
        logger.info(
            "Starting standalone test run of get_fortiswitches_fullview_improved()..."
        )
        try:
            full_switch_data = get_fortiswitches_fullview_improved()

            # Pretty print the JSON output
            import json

            try:
                print(json.dumps(full_switch_data, indent=2))
                logger.info(
                    f"Successfully retrieved and printed data for {len(full_switch_data)} switches."
                )
            except TypeError as e:
                logger.error(f"Error serializing final data to JSON: {e}")
                logger.info("Printing raw data structure instead:")
                print(full_switch_data)

        except Exception as main_e:
            logger.critical(
                f"An unexpected error occurred during the main test run: {main_e}",
                exc_info=True,
            )

# --- END OF fortiswitch_service_improved.py ---
