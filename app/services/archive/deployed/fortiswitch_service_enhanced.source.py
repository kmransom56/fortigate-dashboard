import os
import logging
import requests
import time
from urllib3.exceptions import InsecureRequestWarning
import urllib3
from app.utils import oui_lookup
from app.utils.restaurant_device_classifier import enhance_device_info

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

# Rate limiting globals - Increased to handle FortiGate rate limiting
last_api_call_time = 0
min_api_interval = 2.0  # Minimum 2 seconds between API calls

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
        logger.debug(
            f"Rate limiting: sleeping {sleep_time:.1f}s before API call to {endpoint}"
        )
        time.sleep(sleep_time)

    # Try session authentication first
    if session_manager.password:
        try:
            # Ensure endpoint format is correct for session manager
            if endpoint.startswith("/api/v2/"):
                api_endpoint = endpoint[8:]  # Remove "/api/v2/" prefix
            else:
                api_endpoint = endpoint

            logger.debug(
                f"Making API request to: {endpoint} using session authentication"
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

    logger.debug(f"Making API request to: {endpoint} using token authentication")

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
            time.sleep(30)  # Wait for rate limit to reset
            # Retry once after waiting
            try:
                res = requests.get(
                    url, headers=headers, params=params, verify=verify_ssl, timeout=30
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
        result = res.json()
        logger.debug(
            f"FortiGate API {endpoint} successful - returned {len(str(result))} characters of data"
        )
        if isinstance(result, dict) and "results" in result:
            logger.debug(
                f"FortiGate API {endpoint} - found {len(result['results'])} items in results array"
            )
        return result

    except requests.exceptions.RequestException as e:
        logger.error(f"FortiGate API request exception for {endpoint}: {e}")
        return {}
    except Exception as e:
        logger.error(f"FortiGate API unexpected error for {endpoint}: {e}")
        return {}


# --- Data Source Functions ---


def get_managed_switches():
    """Fetch managed switch status from FortiGate."""
    logger.info("Fetching managed switch status...")
    data = fgt_api("/api/v2/monitor/switch-controller/managed-switch/status")
    logger.info("Finished fetching managed switch status.")
    return data


def get_detected_devices():
    """Fetch detected devices from FortiGate switch controller."""
    logger.info("Fetching detected devices...")
    data = fgt_api("/api/v2/monitor/switch-controller/detected-device")

    if data and "results" in data:
        logger.info(f"Found {len(data['results'])} detected devices")
        for device in data["results"]:
            if "mac" in device:
                manufacturer = oui_lookup.get_manufacturer_from_mac(device["mac"])
                device["manufacturer"] = manufacturer

    logger.info("Finished fetching detected devices.")
    return data


def get_fgt_dhcp():
    """Fetch DHCP lease info from FortiGate."""
    logger.info("Fetching FortiGate DHCP leases...")
    data = fgt_api("/api/v2/monitor/system/dhcp")
    logger.info("Finished fetching FortiGate DHCP leases.")
    return data


def get_system_arp():
    """Fetch ARP table from FortiGate for additional device discovery."""
    logger.info("Fetching FortiGate ARP table...")
    data = fgt_api("/api/v2/monitor/system/arp")
    logger.info("Finished fetching FortiGate ARP table.")
    return data


# --- Enhanced Mapping Functions ---


def build_dhcp_map(dhcp_data):
    """Build a comprehensive MAC to device info map from DHCP data."""
    dhcp_map = {}
    if not isinstance(dhcp_data, dict) or "results" not in dhcp_data:
        logger.warning("Invalid DHCP data format")
        return dhcp_map

    results = dhcp_data.get("results", [])
    logger.info(f"Processing {len(results)} DHCP entries")

    for entry in results:
        if not isinstance(entry, dict):
            continue

        mac = normalize_mac(entry.get("mac"))
        if mac:
            dhcp_map[mac] = {
                "ip": entry.get("ip", "Unknown"),
                "hostname": entry.get("hostname", ""),
                "interface": entry.get("interface", ""),
                "expire_time": entry.get("expire_time", 0),
                "status": entry.get("status", "unknown"),
                "vci": entry.get("vci", ""),
                "type": entry.get("type", "ipv4"),
            }

    logger.info(f"Built DHCP map for {len(dhcp_map)} devices")
    return dhcp_map


def build_arp_map(arp_data):
    """Build MAC to IP mapping from ARP table."""
    arp_map = {}
    if not isinstance(arp_data, dict) or "results" not in arp_data:
        logger.warning("Invalid ARP data format")
        return arp_map

    results = arp_data.get("results", [])
    logger.info(f"Processing {len(results)} ARP entries")

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

    logger.info(f"Built ARP map for {len(arp_map)} devices")
    return arp_map


def build_detected_device_map(detected_data):
    """Build a map of switch_serial:port_name to detected devices."""
    detected_map = {}
    if not isinstance(detected_data, dict) or "results" not in detected_data:
        logger.warning("Invalid detected device data format")
        return detected_map

    results = detected_data.get("results", [])
    logger.info(f"Processing {len(results)} detected device entries")

    for device in results:
        if not isinstance(device, dict):
            continue

        switch_id = device.get("switch_id")
        port_name = device.get("port_name")

        if switch_id and port_name:
            key = f"{switch_id}:{port_name}"
            if key not in detected_map:
                detected_map[key] = []
            detected_map[key].append(device)
            logger.debug(f"Added detected device: {key} -> MAC: {device.get('mac')}")

    logger.info(f"Built detected device map for {len(detected_map)} port combinations")
    return detected_map


# --- Enhanced Device Aggregation ---


def aggregate_port_devices(switch_serial, port_name, detected_map, dhcp_map, arp_map):
    """Aggregate all device information for a specific port."""
    devices = []

    # Get detected devices for this port
    port_key = f"{switch_serial}:{port_name}"
    detected_devices = detected_map.get(port_key, [])

    logger.debug(f"Port {port_name}: Found {len(detected_devices)} detected devices")

    for device in detected_devices:
        mac = normalize_mac(device.get("mac"))
        if not mac:
            continue

        # Get additional info from DHCP and ARP
        dhcp_info = dhcp_map.get(mac, {})
        arp_info = arp_map.get(mac, {})

        # Determine device name/hostname
        hostname = dhcp_info.get("hostname", "")
        if not hostname:
            hostname = f"Device-{port_name}-{mac[-5:].replace(':', '')}"

        # Determine IP address
        ip_address = dhcp_info.get("ip") or arp_info.get("ip", "Unknown")

        # Get manufacturer info
        manufacturer = device.get("manufacturer", "Unknown")

        device_info = {
            "device_mac": mac,
            "device_ip": ip_address,
            "device_name": hostname,
            "device_type": hostname,
            "manufacturer": manufacturer,
            "source": "switch_controller_detected",
            "vlan": device.get("vlan_id", "N/A"),
            "last_seen": device.get("last_seen", 0),
            "port_id": device.get("port_id", 0),
            "dhcp_status": dhcp_info.get("status", "unknown"),
            "dhcp_interface": dhcp_info.get("interface", ""),
            "vci": dhcp_info.get("vci", ""),
        }

        # Enhance with restaurant technology classification
        enhanced_device_info = enhance_device_info(device_info)
        devices.append(enhanced_device_info)
        logger.debug(
            f"Port {port_name}: Added device {hostname} ({mac}) with IP {ip_address}"
        )

    return devices


# --- Main Enhanced Service Function ---


def get_fortiswitches_enhanced():
    """
    Enhanced FortiSwitch discovery with improved device detection and correlation.
    Returns: List of FortiSwitch dictionaries with detailed port and device info.
    """
    logger.info("=== Starting ENHANCED FortiSwitch discovery process ===")

    # 1. Fetch all required data
    logger.info("--- Fetching data from FortiGate APIs ---")
    switches_data = get_managed_switches()
    detected_devices_data = get_detected_devices()
    dhcp_data = get_fgt_dhcp()
    arp_data = get_system_arp()
    logger.info("--- Finished fetching API data ---")

    # 2. Build lookup maps
    logger.info("--- Building device lookup maps ---")
    dhcp_map = build_dhcp_map(dhcp_data)
    arp_map = build_arp_map(arp_data)
    detected_map = build_detected_device_map(detected_devices_data)

    logger.info(
        f"Maps built - DHCP: {len(dhcp_map)}, ARP: {len(arp_map)}, Detected: {len(detected_map)}"
    )
    logger.info("--- Finished building lookup maps ---")

    # 3. Process switches
    switches = []
    switch_results = (
        switches_data.get("results", []) if isinstance(switches_data, dict) else []
    )

    if not switch_results:
        logger.error("No managed switches found in FortiGate response")
        return []

    logger.info(f"--- Processing {len(switch_results)} managed switches ---")

    for switch_data in switch_results:
        if not isinstance(switch_data, dict):
            continue

        switch_serial = switch_data.get("serial", "Unknown")
        switch_name = switch_data.get("switch-id", switch_serial)

        logger.info(f"Processing switch: {switch_name} (Serial: {switch_serial})")

        # Process ports
        ports = []
        ports_data = switch_data.get("ports", [])

        for port_data in ports_data:
            if not isinstance(port_data, dict):
                continue

            port_name = port_data.get("interface", "Unknown")

            # Aggregate devices for this port
            connected_devices = aggregate_port_devices(
                switch_serial, port_name, detected_map, dhcp_map, arp_map
            )

            port_info = {
                "name": port_name,
                "status": port_data.get("status", "Unknown"),
                "speed": port_data.get("speed", 0),
                "duplex": port_data.get("duplex", "Unknown"),
                "vlan": port_data.get("vlan", "Unknown"),
                "poe_capable": port_data.get("poe_capable", False),
                "poe_status": port_data.get("poe_status", "disabled"),
                "fortilink_port": port_data.get("fortilink_port", False),
                "connected_devices": connected_devices,
            }

            ports.append(port_info)

            if connected_devices:
                logger.info(
                    f"  Port {port_name}: {len(connected_devices)} devices detected"
                )

        # Build switch object
        switch_info = {
            "name": switch_name,
            "serial": switch_serial,
            "model": switch_data.get("model", "Unknown"),
            "status": switch_data.get("status", "Unknown"),
            "version": switch_data.get("os_version", "Unknown"),
            "ip": switch_data.get("connecting_from", "Unknown"),
            "mac": switch_data.get("mac", "Unknown"),
            "ports": ports,
        }

        switches.append(switch_info)
        logger.info(f"Finished processing switch: {switch_name}")

    logger.info(
        f"=== Enhanced discovery complete. Processed {len(switches)} switches ==="
    )
    return switches


# --- Compatibility wrapper ---
def get_fortiswitches():
    """Main entry point for FortiSwitch data retrieval."""
    return get_fortiswitches_enhanced()


# --- Debug and Testing ---
if __name__ == "__main__":
    # Setup logging for testing
    log_level_str = os.environ.get("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    logging.basicConfig(
        level=log_level, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )

    if not API_TOKEN and not session_manager.password:
        logger.critical("No authentication available. Please configure authentication.")
    else:
        logger.info("Starting enhanced FortiSwitch service test...")
        try:
            switches = get_fortiswitches_enhanced()

            import json

            print(json.dumps(switches, indent=2))
            logger.info(f"Successfully retrieved data for {len(switches)} switches")

            # Print summary
            total_devices = 0
            for switch in switches:
                for port in switch.get("ports", []):
                    total_devices += len(port.get("connected_devices", []))

            logger.info(f"Total devices detected across all switches: {total_devices}")

        except Exception as e:
            logger.critical(f"Error during test run: {e}", exc_info=True)
