# --- WAN Interface Helper ---
def get_wan_ips():
    """Get WAN interface IPs from FortiGate."""
    try:
        from app.services.fortigate_service import get_interfaces

        interfaces = get_interfaces()
        wan_ips = []
        for name, iface in interfaces.items():
            if name.lower().startswith("wan") and iface.get("ip"):
                wan_ips.append({"name": name, "ip": iface["ip"]})
        return wan_ips
    except Exception as e:
        logger.error(f"Error getting WAN IPs: {e}")
        return []


import os
import logging
import requests
import time
from urllib3.exceptions import InsecureRequestWarning
import urllib3
from typing import Dict, Any, List, Optional

# Assuming these utilities exist in your project structure
from app.utils import oui_lookup
from app.utils.restaurant_device_classifier import enhance_device_info

# Suppress only the InsecureRequestWarning from urllib3
urllib3.disable_warnings(InsecureRequestWarning)

logger = logging.getLogger(__name__)

# Import session management
from app.services.fortigate_session import FortiGateSessionManager
from app.services.fortiswitch_session import FortiSwitchSessionManager

# Environment/defaults
FORTIGATE_HOST = os.environ.get("FORTIGATE_HOST", "https://192.168.0.254")
FORTISWITCH_HOST = os.environ.get("FORTISWITCH_HOST", "")
FORTISWITCH_USERNAME = os.environ.get("FORTISWITCH_USERNAME", "")
FORTISWITCH_PASSWORD = os.environ.get("FORTISWITCH_PASSWORD", "")

session_manager = FortiGateSessionManager()
fortiswitch_session_manager = FortiSwitchSessionManager()


def get_fortiswitches() -> List[Dict[str, Any]]:
    """
    Get a list of FortiSwitch devices managed by the FortiGate or FortiSwitch API.

    This function attempts to retrieve information about connected FortiSwitches
    using either the FortiGate's FortiLink API or directly from a specified
    FortiSwitch via its API.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries, each representing a FortiSwitch.
                              Returns an empty list on failure or if not configured.
    """
    # Check if a FortiSwitch host is configured for direct API access
    if FORTISWITCH_HOST and FORTISWITCH_USERNAME and FORTISWITCH_PASSWORD:
        logger.info("Attempting to get FortiSwitches via FortiSwitch API...")
        try:
            # The actual API endpoint will depend on the FortiSwitch firmware.
            # You may need to replace this with the correct endpoint for your version.
            endpoint = "/api/v2/monitor/system/status"
            switches_data = fortiswitch_session_manager.make_api_request(endpoint)
            # You will need to process the switches_data based on the actual API response
            if switches_data and switches_data.get("http_status") == 200:
                logger.info("Successfully fetched FortiSwitches from FortiSwitch API.")
                return switches_data.get("results", [])
            else:
                logger.warning(
                    f"Failed to get switches via FortiSwitch API. Response: {switches_data}"
                )
        except Exception as e:
            logger.error(f"Error calling FortiSwitch API: {e}")

    # Fallback to FortiGate's FortiLink API if not using direct FortiSwitch access
    # Assumes 'app.services.fortigate_service.fgt_api' is available
    from app.services.fortigate_service import fgt_api

    logger.info("Falling back to get FortiSwitches via FortiGate FortiLink API...")
    try:
        # The FortiLink API on the FortiGate returns information about managed switches
        data = fgt_api("/api/v2/monitor/fortilink/switch")
        if data and data.get("http_status") == 200 and "results" in data:
            logger.info(
                f"Successfully fetched {len(data['results'])} switches from FortiGate FortiLink."
            )
            return data["results"]
        else:
            logger.error(
                f"Failed to get FortiSwitches via FortiGate API or malformed response. Data: {data}"
            )
            return []
    except ImportError:
        logger.warning(
            "fortigate_service is not available. Cannot fetch switches from FortiGate."
        )
        return []
    except Exception as e:
        logger.error(f"Error getting FortiSwitches via FortiGate API: {e}")
        return []


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

# Rate limiting globals - Disabled for session authentication (sessions have higher limits)
last_api_call_time = 0
min_api_interval = 0.1  # Minimum 0.1 seconds between API calls (session auth has much higher limits)

# --- Utility Functions ---


def normalize_mac(mac: Optional[str]) -> Optional[str]:
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


def fgt_api(endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
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
            # Pass session token and API token if available
            session_token = getattr(session_manager, "session_key", None)
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

    res = None  # Ensure res is always defined
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

        # Handle other non-successful status codes
        if res.status_code != 200:
            logger.error(
                f"FortiGate API Error: Status {res.status_code} for {endpoint}. Response: {res.text[:200]}"
            )
            return {}

        # Success case
        return res.json()

    except requests.exceptions.JSONDecodeError:
        response_text = (
            res.text[:200]
            if res is not None and hasattr(res, "text")
            else "<no response>"
        )
        logger.error(
            f"Failed to decode JSON from FortiGate API response for {endpoint}. Response text: {response_text}"
        )
        return {}
    except requests.exceptions.RequestException as e:
        logger.error(f"FortiGate API request failed for {endpoint}: {e}")
        return {}
    except Exception as e:
        logger.error(f"An unexpected error occurred in fgt_api for {endpoint}: {e}")
        return {}


# --- NEW FUNCTIONS ---


def get_interfaces() -> Dict[str, Any]:
    """
    Retrieves all system interfaces from the FortiGate.

    Returns:
        Dict[str, Any]: A dictionary of interface objects, with the interface name as the key.
                        Returns an empty dictionary on failure.
    """
    logger.info("Fetching system interfaces from FortiGate...")
    data = fgt_api("/api/v2/cmdb/system/interface")

    if data and data.get("http_status") == 200 and "results" in data:
        interfaces = {iface["name"]: iface for iface in data["results"]}
        logger.info(f"Successfully fetched {len(interfaces)} interfaces.")
        return interfaces
    else:
        logger.error(f"Failed to get interfaces or malformed response. Data: {data}")
        return {}


def get_device_inventory() -> List[Dict[str, Any]]:
    """
    Retrieves and processes the device inventory from the FortiGate monitor.

    This function fetches all detected devices, normalizes their MAC addresses,
    looks up vendor information, and enriches the data with custom classifications.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries, each representing a device.
                              Returns an empty list on failure.
    """
    logger.info("Fetching device inventory from FortiGate...")
    data = fgt_api("/api/v2/monitor/user/device/select")

    if not data or data.get("http_status") != 200 or "results" not in data:
        logger.error(
            f"Failed to get device inventory or malformed response. Data: {data}"
        )
        return []

    devices = []
    raw_devices = data["results"]
    logger.info(f"Processing {len(raw_devices)} devices from inventory...")

    for device in raw_devices:
        mac = normalize_mac(device.get("mac"))
        if not mac:
            continue

        ip_addr = device.get("ip_addr")
        if isinstance(ip_addr, list) and len(ip_addr) > 0:
            ip_addr = ip_addr[0]  # Take the first IP if it's a list
        elif isinstance(ip_addr, list) and len(ip_addr) == 0:
            ip_addr = None

        processed_device = {
            "mac": mac,
            "ip": ip_addr,
            "hostname": device.get("host", {}).get("name"),
            "os": device.get("os_name"),
            "os_version": device.get("os_ver"),
            "hardware_vendor": device.get("hardware_vendor"),
            "last_seen": device.get("last_seen"),
            "last_seen_itf": device.get("last_seen_itf"),
            "is_online": device.get("is_online", False),
            "vendor": oui_lookup.lookup_vendor(mac),  # <-- fixed function name
        }

        # Enhance with custom classification logic
        enhanced_info = enhance_device_info(processed_device)
        devices.append(enhanced_info)

    logger.info(f"Successfully processed {len(devices)} devices from inventory.")
    return devices


# --- END OF NEW FUNCTIONS ---
