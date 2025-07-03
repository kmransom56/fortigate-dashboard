import os
import requests
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import urllib3

# Suppress only the InsecureRequestWarning from urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

class FortiSwitchSessionManager:
    """
    Manages FortiSwitch API session authentication using basic auth.
    Handles login, session key management (though basic auth is stateless, we maintain a session object),
    and automatic re-authentication if needed.
    """

    def __init__(self):
        self.fortiswitch_host: Optional[str] = None
        self.username: Optional[str] = None
        self.password: Optional[str] = None
        self.session = requests.Session()
        self.session.verify = False  # Disable SSL verification by default

        # Load credentials
        self._load_credentials()

    def _load_credentials(self) -> None:
        """Load FortiSwitch credentials from environment or files"""
        try:
            self.fortiswitch_host = os.getenv("FORTISWITCH_HOST", "")
            self.username = os.getenv("FORTISWITCH_USERNAME", "")

            # Try to load password from various sources
            password_sources = [
                os.getenv("FORTISWITCH_PASSWORD"),
                self._load_from_file("/run/secrets/fortiswitch_password"),  # Docker secrets
                self._load_from_file("/secrets/fortiswitch_password.txt"),  # Local development
                self._load_from_file("./secrets/fortiswitch_password.txt"),  # Relative path
            ]

            for password in password_sources:
                if password:
                    self.password = password
                    break

            if not self.fortiswitch_host:
                logger.warning("FORTISWITCH_HOST not set. FortiSwitch API calls will be skipped.")
            if not self.username or not self.password:
                logger.warning("No FortiSwitch username or password found. FortiSwitch API calls will be skipped.")

            logger.info(
                f"FortiSwitch credentials loaded: Host={self.fortiswitch_host}, Username={self.username}, Password={'***' if self.password else 'None'}"
            )

        except Exception as e:
            logger.error(f"Error loading FortiSwitch credentials: {e}")

    def _load_from_file(self, filepath: str) -> Optional[str]:
        """Load content from file if it exists"""
        try:
            if os.path.exists(filepath):
                with open(filepath, "r") as f:
                    content = f.read().strip()
                    if content:
                        logger.info(f"Loaded credential from {filepath}")
                        return content
        except Exception as e:
            logger.debug(f"Could not load from {filepath}: {e}")
        return None

    def make_api_request(self, endpoint: str) -> Dict[str, Any]:
        """
        Make an authenticated API request using basic authentication.
        Returns dictionary with response data or error information.
        """
        if not self.fortiswitch_host or not self.username or not self.password:
            logger.debug("FortiSwitch credentials/host missing, skipping direct FSW API call to %s.", endpoint)
            return {"error": "credentials_missing", "message": "FortiSwitch credentials not configured."}

        if not endpoint.startswith("/"):
            endpoint = "/" + endpoint
        url = f"{self.fortiswitch_host}{endpoint}"

        try:
            auth = (self.username, self.password)
            verify_ssl_str = os.environ.get("FORTISWITCH_VERIFY_SSL", "false").lower()
            verify_ssl = verify_ssl_str == "true"
            if not verify_ssl:
                logger.warning(
                    f"SSL verification disabled for FortiSwitch API ({url}). Set FORTISWITCH_VERIFY_SSL=true to enable."
                )

            logger.info(f"Making FortiSwitch API request to: {url}")
            res = self.session.get(url, auth=auth, verify=verify_ssl, timeout=20)
            logger.info(f"FSW API {endpoint} response status: {res.status_code}")

            if res.status_code == 401:
                logger.error("FortiSwitch API Error 401: Unauthorized. Check FSW username/password.")
                return {"error": "unauthorized", "message": "Authentication failed."}
            elif res.status_code == 404:
                logger.error(f"FortiSwitch API Error 404: Not Found. Endpoint {endpoint} may be incorrect for this FortiSwitchOS version.")
                return {"error": "not_found", "message": "API endpoint not found."}
            elif res.status_code >= 400:
                logger.error(f"FortiSwitch API error {res.status_code} for {endpoint}: {res.text[:512]}")
                return {"error": "api_error", "status_code": res.status_code, "message": res.text[:512]}

            return res.json()

        except requests.exceptions.Timeout:
            logger.error(f"FSW API request timeout for {endpoint} after 20 seconds.")
            return {"error": "timeout", "message": "FortiSwitch API request timed out."}
        except requests.exceptions.SSLError as e:
            logger.error(f"FSW API SSL error for {endpoint}: {e}. If using self-signed certs, ensure FORTISWITCH_VERIFY_SSL is false.")
            return {"error": "ssl_error", "message": str(e)}
        except requests.exceptions.ConnectionError as e:
            logger.error(f"FSW API connection error for {endpoint}: {e}. Check hostname/IP and network connectivity.")
            return {"error": "connection_error", "message": str(e)}
        except requests.exceptions.RequestException as e:
            logger.error(f"FSW API request exception for {endpoint}: {e}")
            return {"error": "request_exception", "message": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error during FSW API call for {endpoint}: {e}", exc_info=True)
            return {"error": "unexpected_error", "message": str(e)}

# Global session manager instance
_fortiswitch_session_manager = None

def get_fortiswitch_session_manager() -> FortiSwitchSessionManager:
    """Get the global FortiSwitch session manager instance"""
    global _fortiswitch_session_manager
    if _fortiswitch_session_manager is None:
        _fortiswitch_session_manager = FortiSwitchSessionManager()
    return _fortiswitch_session_manager
