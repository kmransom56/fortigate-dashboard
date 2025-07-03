import os
import requests
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FortiGateSessionManager:
    """
    Manages FortiGate API session authentication.
    Handles login, session key management, and automatic re-authentication.
    """

    def __init__(self):
        self.session_key: Optional[str] = None
        self.session_expires: Optional[datetime] = None
        self.fortigate_ip: Optional[str] = None
        self.username: Optional[str] = None
        self.password: Optional[str] = None
        self.session = requests.Session()
        self.session.verify = (
            False  # Disable SSL verification for self-signed certificates
        )

        # Load credentials
        self._load_credentials()

    def _load_credentials(self) -> None:
        """Load FortiGate credentials from environment or files"""
        try:
            # Get FortiGate IP
            fortigate_host = os.getenv("FORTIGATE_HOST", "https://192.168.0.254")
            if fortigate_host.startswith("https://"):
                self.fortigate_ip = fortigate_host[8:]
            elif fortigate_host.startswith("http://"):
                self.fortigate_ip = fortigate_host[7:]
            else:
                self.fortigate_ip = fortigate_host

            # Load username and password
            self.username = os.getenv("FORTIGATE_USERNAME", "admin")

            # Try to load password from various sources
            password_sources = [
                os.getenv("FORTIGATE_PASSWORD"),
                self._load_from_file(
                    "/run/secrets/fortigate_password"
                ),  # Docker secrets
                self._load_from_file(
                    "/secrets/fortigate_password.txt"
                ),  # Local development
                self._load_from_file(
                    "./secrets/fortigate_password.txt"
                ),  # Relative path
            ]

            for password in password_sources:
                if password:
                    self.password = password
                    break

            if not self.password:
                logger.warning(
                    "No FortiGate password found. Session authentication will not work."
                )

            logger.info(
                f"FortiGate credentials loaded: IP={self.fortigate_ip}, Username={self.username}, Password={'***' if self.password else 'None'}"
            )

        except Exception as e:
            logger.error(f"Error loading FortiGate credentials: {e}")

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

    def _is_session_valid(self) -> bool:
        """Check if current session is still valid"""
        if not self.session_key:
            return False

        if not self.session_expires:
            return False

        # Check if session expires in the next 5 minutes (buffer for safety)
        return datetime.now() + timedelta(minutes=5) < self.session_expires

    def login(self) -> bool:
        """
        Authenticate with FortiGate and obtain session key.
        Returns True if successful, False otherwise.
        """
        try:
            if not self.fortigate_ip or not self.username or not self.password:
                logger.error("Missing FortiGate credentials for session authentication")
                return False

            login_url = f"https://{self.fortigate_ip}/logincheck"

            # Prepare login data
            login_data = {
                "username": self.username,
                "secretkey": self.password,
                "ajax": "1",
            }

            logger.info(
                f"Attempting to authenticate with FortiGate at {self.fortigate_ip}"
            )

            # Perform login
            response = self.session.post(
                login_url, data=login_data, timeout=30, allow_redirects=False
            )

            if response.status_code == 200:
                # Check response content for successful login
                response_text = response.text.strip()

                # FortiGate returns different responses for successful login
                # Usually contains session information or redirect
                if "ret=1" in response_text or "redir=" in response_text:
                    # Extract session key from cookies
                    for cookie_name, cookie_value in self.session.cookies.items():
                        if cookie_name in ["ccsrftoken", "session_key", "APSCOOKIE_"]:
                            self.session_key = cookie_value
                            # Set session expiration (default FortiGate session: 5 minutes)
                            self.session_expires = datetime.now() + timedelta(
                                minutes=30
                            )
                            logger.info("FortiGate session authentication successful")
                            return True

                    # If no specific session cookie found, try using any authentication cookie
                    if self.session.cookies:
                        # Use the first available cookie as session key
                        cookie_items = list(self.session.cookies.items())
                        if cookie_items:
                            self.session_key = cookie_items[0][1]
                            self.session_expires = datetime.now() + timedelta(
                                minutes=30
                            )
                            logger.info(
                                "FortiGate session authentication successful (using generic cookie)"
                            )
                            return True

                logger.error(
                    f"Login successful but no session key found. Response: {response_text}"
                )
                return False

            else:
                logger.error(
                    f"FortiGate login failed with status {response.status_code}: {response.text}"
                )
                return False

        except requests.exceptions.Timeout:
            logger.error("FortiGate login request timed out")
            return False
        except requests.exceptions.ConnectionError:
            logger.error("Could not connect to FortiGate for login")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during FortiGate login: {e}")
            return False

    def logout(self) -> None:
        """Logout from FortiGate session"""
        try:
            if self.session_key and self.fortigate_ip:
                logout_url = f"https://{self.fortigate_ip}/logout"
                self.session.get(logout_url, timeout=10)
                logger.info("FortiGate session logged out")
        except Exception as e:
            logger.debug(f"Error during logout: {e}")
        finally:
            self.session_key = None
            self.session_expires = None

    def get_session_key(self) -> Optional[str]:
        """
        Get a valid session key, performing login if necessary.
        Returns None if authentication fails.
        """
        try:
            # Check if current session is valid
            if self._is_session_valid():
                return self.session_key

            # Session expired or not available, try to login
            if self.login():
                return self.session_key

            logger.error("Failed to obtain valid FortiGate session key")
            return None

        except Exception as e:
            logger.error(f"Error getting session key: {e}")
            return None

    def make_api_request(self, endpoint: str) -> Dict[str, Any]:
        """
        Make an authenticated API request using session key.
        Returns dictionary with response data or error information.
        """
        try:
            session_key = self.get_session_key()
            if not session_key:
                return {
                    "error": "authentication_failed",
                    "message": "Could not obtain session key",
                }

            url = f"https://{self.fortigate_ip}/api/v2/{endpoint}"

            # Use session cookies for authentication
            response = self.session.get(url, timeout=30)

            if response.status_code == 401:
                # Session expired, try to re-authenticate once
                logger.warning("Session expired, attempting re-authentication")
                self.session_key = None
                self.session_expires = None

                session_key = self.get_session_key()
                if session_key:
                    response = self.session.get(url, timeout=30)
                else:
                    return {
                        "error": "authentication_failed",
                        "message": "Re-authentication failed",
                    }

            if response.status_code == 200:
                try:
                    return response.json()
                except json.JSONDecodeError:
                    return {
                        "error": "json_decode_error",
                        "raw_response": response.text[:200],
                    }
            else:
                return {
                    "error": "api_error",
                    "status_code": response.status_code,
                    "message": response.text[:200],
                }

        except Exception as e:
            logger.error(f"Error in API request to {endpoint}: {e}")
            return {"error": "request_failed", "message": str(e)}


# Global session manager instance
_session_manager = None


def get_session_manager() -> FortiGateSessionManager:
    """Get the global session manager instance"""
    global _session_manager
    if _session_manager is None:
        _session_manager = FortiGateSessionManager()
    return _session_manager
