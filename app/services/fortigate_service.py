# Add this function at the end of the file
def get_cloud_status() -> str:
    """Check FortiGate cloud connection status (mock or real API call)"""
    # TODO: Replace with real API call if available
    # Example: ping cloud endpoint, check VPN, etc.
    try:
        # Simulate cloud check (replace with real logic)
        # For demo, always return 'Connected'
        return "Connected"
    except Exception:
        return "Disconnected"


import os
import requests
import json
import logging
import time
from typing import Dict, Any, Optional

from .fortigate_session import get_session_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rate limiting - track last API call time
_last_api_call = 0
_min_interval = 10  # Minimum 10 seconds between API calls

# Authentication mode: 'session' (preferred) or 'token'
_auth_mode = "session"


def load_api_token() -> Optional[str]:
    """Load API token from file or environment variable"""
    try:
        # Try Docker secrets first (mounted at /run/secrets/)
        token_files = [
            "/run/secrets/fortigate_api_token",  # Docker secrets mount point
            "/secrets/fortigate_api_token.txt",  # Local development
            "./secrets/fortigate_api_token.txt",  # Relative path
        ]

        for token_file in token_files:
            if os.path.exists(token_file):
                with open(token_file, "r") as f:
                    token = f.read().strip()
                    if token:
                        logger.info(f"API token loaded from {token_file}")
                        return token

        # Fall back to environment variables
        token = os.getenv("FORTIGATE_API_TOKEN")
        if token:
            logger.info("API token loaded from FORTIGATE_API_TOKEN environment")
            return token

        # Check for the environment variable set by docker-compose
        token_file_env = os.getenv("FORTIGATE_API_TOKEN_FILE")
        if token_file_env and os.path.exists(token_file_env):
            with open(token_file_env, "r") as f:
                token = f.read().strip()
                if token:
                    logger.info(f"API token loaded from env file: {token_file_env}")
                    return token

        logger.warning("No API token found in any location")
        return None
    except Exception as e:
        logger.error(f"Error loading API token: {e}")
        return None


def fgt_api(
    endpoint: str, api_token: Optional[str] = None, fortigate_ip: Optional[str] = None
) -> Dict[str, Any]:
    """
    Robust FortiGate API helper that handles all error cases gracefully.
    Supports both session-based and token-based authentication.
    Always returns a dictionary, never raises exceptions.
    """
    global _last_api_call

    try:
        # Determine FortiGate IP from environment if not provided
        if fortigate_ip is None:
            # Get from environment variable, remove https:// prefix if present
            fortigate_host = os.getenv("FORTIGATE_HOST", "https://192.168.0.254")
            if fortigate_host.startswith("https://"):
                fortigate_ip = fortigate_host[8:]  # Remove "https://"
            elif fortigate_host.startswith("http://"):
                fortigate_ip = fortigate_host[7:]  # Remove "http://"
            else:
                fortigate_ip = fortigate_host

        # Rate limiting - ensure minimum interval between calls
        current_time = time.time()
        time_since_last = current_time - _last_api_call
        if time_since_last < _min_interval:
            sleep_time = _min_interval - time_since_last
            logger.info(f"Rate limiting: sleeping {sleep_time:.1f}s before API call")
            time.sleep(sleep_time)

        _last_api_call = time.time()

        # Try session-based authentication first
        if _auth_mode == "session":
            logger.info(
                f"Making API request to: {endpoint} (FortiGate: {fortigate_ip}) using session authentication"
            )
            session_manager = get_session_manager()
            result = session_manager.make_api_request(endpoint)
            logger.info(f"Session API response for {endpoint}: {result}")  # Added log

            # If session auth failed, fall back to token auth
            if "error" in result and result.get("error") == "authentication_failed":
                logger.warning(
                    "Session authentication failed, falling back to token authentication"
                )
                if api_token:
                    return _fgt_api_with_token(endpoint, api_token, fortigate_ip)
                else:
                    # Try to load token as fallback
                    fallback_token = load_api_token()
                    logger.info(
                        f"Fallback API token loaded: {'<present>' if fallback_token else '<not present>'}"
                    )  # Added log
                    if fallback_token:
                        return _fgt_api_with_token(
                            endpoint, fallback_token, fortigate_ip
                        )

            return result
        else:
            # Token-based authentication
            if not api_token:
                api_token = load_api_token()
                logger.info(
                    f"API token loaded for token auth: {'<present>' if api_token else '<not present>'}"
                )  # Added log
                if not api_token:
                    return {"error": "no_token", "message": "No API token available"}

            return _fgt_api_with_token(endpoint, api_token, fortigate_ip)

    except Exception as e:
        logger.error(f"Unexpected error for {endpoint}: {e}")
        return {"error": "unexpected_error", "details": str(e)}


def _fgt_api_with_token(
    endpoint: str, api_token: str, fortigate_ip: str
) -> Dict[str, Any]:
    """
    Make API request using token authentication.
    Internal function used by fgt_api.
    """
    try:
        url = f"https://{fortigate_ip}/api/v2/{endpoint}"
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        }

        logger.info(
            f"Making API request to: {endpoint} (FortiGate: {fortigate_ip}) using token authentication"
        )

        response = requests.get(url, headers=headers, verify=False, timeout=30)

        # Handle specific HTTP status codes
        if response.status_code == 401:
            logger.error("FortiGate API authentication failed (401)")
            return {"error": "authentication_failed", "status_code": 401}
        elif response.status_code == 403:
            logger.error("FortiGate API access forbidden (403)")
            return {"error": "access_forbidden", "status_code": 403}
        elif response.status_code == 404:
            logger.error(f"FortiGate API endpoint not found (404): {endpoint}")
            return {"error": "endpoint_not_found", "status_code": 404}
        elif response.status_code == 429:
            logger.warning(
                f"FortiGate API rate limit exceeded (429) for {endpoint}. Waiting 60s before retry."
            )
            # Wait longer before next request
            time.sleep(60)
            global _last_api_call
            _last_api_call = time.time()
            return {
                "error": "rate_limit_exceeded",
                "status_code": 429,
                "retry_after": 60,
            }
        elif response.status_code >= 400:
            logger.error(
                f"FortiGate API error {response.status_code}: {response.text[:200]}"
            )
            return {"error": "api_error", "status_code": response.status_code}

        # Success case
        try:
            data = response.json()
            logger.info(
                f"API request successful for {endpoint}. Response: {data}"
            )  # Modified log
            return data
        except json.JSONDecodeError:
            logger.error("Failed to parse JSON response")
            return {"error": "json_decode_error", "raw_response": response.text[:200]}

    except requests.exceptions.Timeout:
        logger.error(f"API request timeout for {endpoint}")
        return {"error": "timeout"}
    except requests.exceptions.SSLError:
        logger.error(f"SSL error for {endpoint}")
        return {"error": "ssl_error"}
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection error for {endpoint}")
        return {"error": "connection_error"}
    except Exception as e:
        logger.error(f"Unexpected error for {endpoint}: {e}")
        return {"error": "unexpected_error", "details": str(e)}


def process_interface_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Process interface data from API response, handling different formats"""
    if not data or "error" in data:
        return {}

    interfaces = {}

    # Handle different response formats
    if "results" in data:
        # Standard format
        for interface in data["results"]:
            if isinstance(interface, dict):
                name = interface.get("name", "unknown")
                interfaces[name] = {
                    "name": name,
                    "status": interface.get("status", "unknown"),
                    "ip": interface.get("ip", ""),
                    "type": interface.get("type", "unknown"),
                    "speed": interface.get("speed", 0),
                    "duplex": interface.get("duplex", "unknown"),
                }
    elif isinstance(data, list):
        # Direct list format
        for interface in data:
            if isinstance(interface, dict):
                name = interface.get("name", "unknown")
                interfaces[name] = {
                    "name": name,
                    "status": interface.get("status", "unknown"),
                    "ip": interface.get("ip", ""),
                    "type": interface.get("type", "unknown"),
                    "speed": interface.get("speed", 0),
                    "duplex": interface.get("duplex", "unknown"),
                }

    return interfaces


def get_interfaces() -> Dict[str, Any]:
    """
    Get FortiGate interfaces. Always returns a dictionary, never raises exceptions.
    Returns empty dict on any error.
    """
    try:
        # Get interface data using the updated fgt_api function
        data = fgt_api("cmdb/system/interface")

        # Process the data
        interfaces = process_interface_data(data)

        logger.info(f"Retrieved {len(interfaces)} interfaces")
        return interfaces

    except Exception as e:
        logger.error(f"Unexpected error in get_interfaces: {e}")
        return {}
