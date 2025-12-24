import os
import requests
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from .redis_session_manager import get_redis_session_manager, SessionData

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FortiGateRedisSessionManager:
    """
    Enhanced FortiGate session manager using Redis for distributed session storage.
    Integrates FortiGate authentication with Redis session persistence.
    """

    def __init__(self):
        self.fortigate_ip: Optional[str] = None
        self.username: Optional[str] = None
        self.password: Optional[str] = None
        self.session = requests.Session()
        self.session.verify = (
            False  # Disable SSL verification for self-signed certificates
        )

        # Redis session manager
        self.redis_manager = get_redis_session_manager()

        # Load credentials
        self._load_credentials()

    def _load_credentials(self) -> None:
        """Load FortiGate credentials from environment or files"""
        try:
            # Get FortiGate IP (default HTTPS on 443)
            fortigate_host = os.getenv("FORTIGATE_HOST", "https://192.168.0.254")
            if fortigate_host.startswith("https://"):
                self.fortigate_ip = fortigate_host[8:]
            elif fortigate_host.startswith("http://"):
                self.fortigate_ip = fortigate_host[7:]
            else:
                self.fortigate_ip = fortigate_host

            # Remove port if it's the default HTTPS port
            if ":443" in self.fortigate_ip:
                self.fortigate_ip = self.fortigate_ip.replace(":443", "")

            # Load username and password - use admin for session authentication
            # API users may not support session auth, only token auth
            self.username = os.getenv("FORTIGATE_USERNAME", "admin")

            # Try to load password from various sources
            password_sources = [
                os.getenv("FORTIGATE_PASSWORD"),
                self._load_from_file(os.getenv("FORTIGATE_PASSWORD_FILE")),
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

    def _load_from_file(self, filepath: Optional[str]) -> Optional[str]:
        """Load content from file if it exists"""
        if not filepath:
            return None

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

    def _get_stored_session(self) -> Optional[SessionData]:
        """Get session data from Redis if available"""
        if not self.fortigate_ip or not self.username:
            return None

        return self.redis_manager.get_session(self.fortigate_ip, self.username)

    def _store_session(self, session_key: str, expires_in_minutes: int = 30) -> bool:
        """Store session data in Redis"""
        if not self.fortigate_ip or not self.username:
            return False

        return self.redis_manager.store_session(
            self.fortigate_ip, self.username, session_key, expires_in_minutes
        )

    def _delete_session(self) -> bool:
        """Delete session data from Redis"""
        if not self.fortigate_ip or not self.username:
            return False

        return self.redis_manager.delete_session(self.fortigate_ip, self.username)

    def login(self) -> bool:
        """
        Authenticate with FortiGate and store session in Redis.
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
                if (
                    "ret=1" in response_text
                    or "redir=" in response_text
                    or response_text == ""
                ):
                    # Extract session key from cookies
                    session_key = None

                    # Try different cookie names that FortiGate might use
                    cookie_candidates = ["ccsrftoken", "session_key", "APSCOOKIE_"]
                    for cookie_name in cookie_candidates:
                        if cookie_name in self.session.cookies:
                            session_key = self.session.cookies[cookie_name]
                            logger.info(f"Found session key in cookie: {cookie_name}")
                            break

                    # If no specific session cookie found, try using any authentication cookie
                    if not session_key and self.session.cookies:
                        # Use the first available cookie as session key
                        cookie_items = list(self.session.cookies.items())
                        if cookie_items:
                            session_key = cookie_items[0][1]
                            logger.info(
                                f"Using generic cookie as session key: {cookie_items[0][0]}"
                            )

                    if session_key:
                        # Store session in Redis
                        session_ttl_minutes = int(
                            os.getenv("FORTIGATE_SESSION_TTL", 30)
                        )
                        if self._store_session(session_key, session_ttl_minutes):
                            logger.info(
                                "FortiGate session authentication successful and stored in Redis"
                            )
                            return True
                        else:
                            logger.warning(
                                "FortiGate session authentication successful but failed to store in Redis"
                            )
                            # Still return True as we have a valid session, just not stored
                            return True
                    else:
                        logger.error(
                            f"Login successful but no session key found in cookies. Response: {response_text}"
                        )
                        logger.debug(f"Available cookies: {dict(self.session.cookies)}")
                        return False
                else:
                    logger.error(f"Login failed - unexpected response: {response_text}")
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
        """Logout from FortiGate session and clean up Redis"""
        try:
            # Logout from FortiGate
            if self.fortigate_ip:
                logout_url = f"https://{self.fortigate_ip}/logout"
                self.session.get(logout_url, timeout=10)
                logger.info("FortiGate session logged out")

            # Delete session from Redis
            self._delete_session()

        except Exception as e:
            logger.debug(f"Error during logout: {e}")

    def get_session_key(self) -> Optional[str]:
        """
        Get a valid session key, using Redis cache or performing login if necessary.
        Returns None if authentication fails.
        """
        try:
            # First, try to get session from Redis
            stored_session = self._get_stored_session()
            if stored_session and stored_session.is_valid():
                logger.debug("Using cached session from Redis")
                return stored_session.session_key

            logger.info("No valid cached session, attempting new login")

            # Session expired or not available, try to login
            if self.login():
                # Get the newly created session from Redis
                new_session = self._get_stored_session()
                if new_session:
                    return new_session.session_key
                else:
                    logger.warning(
                        "Login successful but could not retrieve session from Redis"
                    )
                    # Fallback: return session key from local session cookies
                    for cookie_name in ["ccsrftoken", "session_key", "APSCOOKIE_"]:
                        if cookie_name in self.session.cookies:
                            return self.session.cookies[cookie_name]

            logger.error("Failed to obtain valid FortiGate session key")
            return None

        except Exception as e:
            logger.error(f"Error getting session key: {e}")
            return None

    def make_api_request(self, endpoint: str) -> Dict[str, Any]:
        """
        Make an authenticated API request using Redis-managed session.
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
                # Session expired, delete from Redis and try to re-authenticate once
                logger.warning("Session expired, attempting re-authentication")
                self._delete_session()

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

    def get_session_info(self) -> Dict[str, Any]:
        """Get information about the current session"""
        try:
            stored_session = self._get_stored_session()
            if stored_session:
                return {
                    "has_session": True,
                    "is_valid": stored_session.is_valid(),
                    "expires_at": stored_session.expires_at.isoformat(),
                    "created_at": stored_session.created_at.isoformat(),
                    "last_used": stored_session.last_used.isoformat(),
                    "request_count": stored_session.request_count,
                    "fortigate_ip": stored_session.fortigate_ip,
                    "username": stored_session.username,
                }
            else:
                return {"has_session": False, "is_valid": False}
        except Exception as e:
            logger.error(f"Error getting session info: {e}")
            return {"error": str(e)}

    def health_check(self) -> Dict[str, Any]:
        """Perform health check on the session manager"""
        try:
            health_status = {
                "fortigate_ip": self.fortigate_ip,
                "username": self.username,
                "has_password": bool(self.password),
                "timestamp": datetime.now().isoformat(),
            }

            # Add Redis session manager health
            redis_health = self.redis_manager.health_check()
            health_status["redis"] = redis_health

            # Add current session info
            session_info = self.get_session_info()
            health_status["session"] = session_info

            return health_status

        except Exception as e:
            logger.error(f"Error in health check: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}


# Global Redis-based session manager instance
_redis_session_manager = None


def get_fortigate_redis_session_manager() -> FortiGateRedisSessionManager:
    """Get the global Redis-based FortiGate session manager instance"""
    global _redis_session_manager
    if _redis_session_manager is None:
        _redis_session_manager = FortiGateRedisSessionManager()
    return _redis_session_manager
