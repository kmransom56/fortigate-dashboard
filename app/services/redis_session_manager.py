import os
import redis
import json
import logging
import time
from typing import Dict, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SessionData:
    """Session data structure for FortiGate authentication"""

    session_key: str
    expires_at: datetime
    fortigate_ip: str
    username: str
    created_at: datetime
    last_used: datetime
    request_count: int = 0

    def is_expired(self, buffer_minutes: int = 5) -> bool:
        """Check if session is expired (with buffer for safety)"""
        return datetime.now() + timedelta(minutes=buffer_minutes) >= self.expires_at

    def is_valid(self) -> bool:
        """Check if session is valid and not expired"""
        return bool(self.session_key) and not self.is_expired()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Redis storage"""
        data = asdict(self)
        # Convert datetime objects to ISO strings for JSON serialization
        data["expires_at"] = self.expires_at.isoformat()
        data["created_at"] = self.created_at.isoformat()
        data["last_used"] = self.last_used.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionData":
        """Create SessionData from dictionary (Redis storage)"""
        # Convert ISO strings back to datetime objects
        data["expires_at"] = datetime.fromisoformat(data["expires_at"])
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        data["last_used"] = datetime.fromisoformat(data["last_used"])
        return cls(**data)


class RedisSessionManager:
    """
    Redis-based FortiGate session manager with distributed session storage.
    Handles session caching, expiration, and automatic cleanup.
    """

    def __init__(
        self,
        redis_host: str = None,
        redis_port: int = None,
        redis_db: int = 0,
        redis_password: str = None,
        session_ttl: int = 1800,  # 30 minutes default
    ):
        """
        Initialize Redis session manager

        Args:
            redis_host: Redis server hostname (default from env REDIS_HOST)
            redis_port: Redis server port (default from env REDIS_PORT or 6379)
            redis_db: Redis database number (default 0)
            redis_password: Redis password (default from env REDIS_PASSWORD)
            session_ttl: Session TTL in seconds (default 30 minutes)
        """
        # Load Redis configuration from environment
        self.redis_host = redis_host or os.getenv("REDIS_HOST", "localhost")
        self.redis_port = redis_port or int(os.getenv("REDIS_PORT", 6379))
        self.redis_db = redis_db
        self.redis_password = redis_password or os.getenv("REDIS_PASSWORD")
        self.session_ttl = session_ttl

        # Redis connection
        self.redis_client: Optional[redis.Redis] = None
        self._connect_redis()

        # Session key prefix for namespacing
        self.key_prefix = "fortigate_session"

        logger.info(
            f"Redis session manager initialized: {self.redis_host}:{self.redis_port}"
        )

    def _connect_redis(self) -> None:
        """Establish Redis connection with error handling"""
        try:
            self.redis_client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                db=self.redis_db,
                password=self.redis_password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
            )

            # Test connection
            self.redis_client.ping()
            logger.info("Redis connection established successfully")

        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
        except Exception as e:
            logger.error(f"Unexpected error connecting to Redis: {e}")
            self.redis_client = None

    def _get_session_key(self, fortigate_ip: str, username: str) -> str:
        """Generate unique session key for FortiGate instance and user"""
        # Create unique identifier based on FortiGate IP and username
        identifier = f"{fortigate_ip}:{username}"
        hash_obj = hashlib.md5(identifier.encode())
        return f"{self.key_prefix}:{hash_obj.hexdigest()}"

    def _is_redis_available(self) -> bool:
        """Check if Redis connection is available"""
        try:
            if self.redis_client is None:
                self._connect_redis()

            if self.redis_client:
                self.redis_client.ping()
                return True

        except Exception as e:
            logger.debug(f"Redis not available: {e}")

        return False

    def store_session(
        self,
        fortigate_ip: str,
        username: str,
        session_key: str,
        expires_in_minutes: int = 30,
    ) -> bool:
        """
        Store session data in Redis

        Args:
            fortigate_ip: FortiGate IP address
            username: Username for the session
            session_key: FortiGate session key/cookie
            expires_in_minutes: Session expiration time in minutes

        Returns:
            True if stored successfully, False otherwise
        """
        try:
            if not self._is_redis_available():
                logger.warning("Redis not available, cannot store session")
                return False

            # Create session data
            now = datetime.now()
            session_data = SessionData(
                session_key=session_key,
                expires_at=now + timedelta(minutes=expires_in_minutes),
                fortigate_ip=fortigate_ip,
                username=username,
                created_at=now,
                last_used=now,
                request_count=0,
            )

            # Store in Redis with TTL
            redis_key = self._get_session_key(fortigate_ip, username)
            session_json = json.dumps(session_data.to_dict())

            # Set with TTL (add buffer to TTL for cleanup)
            ttl_seconds = (expires_in_minutes * 60) + 300  # +5 minute buffer

            result = self.redis_client.setex(redis_key, ttl_seconds, session_json)

            if result:
                logger.info(f"Session stored in Redis for {username}@{fortigate_ip}")
                return True
            else:
                logger.error("Failed to store session in Redis")
                return False

        except Exception as e:
            logger.error(f"Error storing session in Redis: {e}")
            return False

    def get_session(self, fortigate_ip: str, username: str) -> Optional[SessionData]:
        """
        Retrieve session data from Redis

        Args:
            fortigate_ip: FortiGate IP address
            username: Username for the session

        Returns:
            SessionData if valid session exists, None otherwise
        """
        try:
            if not self._is_redis_available():
                logger.debug("Redis not available, cannot retrieve session")
                return None

            redis_key = self._get_session_key(fortigate_ip, username)
            session_json = self.redis_client.get(redis_key)

            if not session_json:
                logger.debug(f"No session found for {username}@{fortigate_ip}")
                return None

            # Parse session data
            session_dict = json.loads(session_json)
            session_data = SessionData.from_dict(session_dict)

            # Check if session is still valid
            if session_data.is_expired():
                logger.info(f"Session expired for {username}@{fortigate_ip}")
                self.delete_session(fortigate_ip, username)
                return None

            # Update last used timestamp
            session_data.last_used = datetime.now()
            session_data.request_count += 1

            # Update in Redis
            updated_json = json.dumps(session_data.to_dict())
            self.redis_client.setex(
                redis_key,
                int((session_data.expires_at - datetime.now()).total_seconds()) + 300,
                updated_json,
            )

            logger.debug(f"Retrieved valid session for {username}@{fortigate_ip}")
            return session_data

        except Exception as e:
            logger.error(f"Error retrieving session from Redis: {e}")
            return None

    def delete_session(self, fortigate_ip: str, username: str) -> bool:
        """
        Delete session from Redis

        Args:
            fortigate_ip: FortiGate IP address
            username: Username for the session

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            if not self._is_redis_available():
                logger.debug("Redis not available, cannot delete session")
                return False

            redis_key = self._get_session_key(fortigate_ip, username)
            result = self.redis_client.delete(redis_key)

            if result > 0:
                logger.info(f"Session deleted for {username}@{fortigate_ip}")
                return True
            else:
                logger.debug(f"No session to delete for {username}@{fortigate_ip}")
                return False

        except Exception as e:
            logger.error(f"Error deleting session from Redis: {e}")
            return False

    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions from Redis

        Returns:
            Number of sessions cleaned up
        """
        try:
            if not self._is_redis_available():
                return 0

            # Get all session keys
            pattern = f"{self.key_prefix}:*"
            session_keys = self.redis_client.keys(pattern)

            cleaned_count = 0
            for redis_key in session_keys:
                try:
                    session_json = self.redis_client.get(redis_key)
                    if session_json:
                        session_dict = json.loads(session_json)
                        session_data = SessionData.from_dict(session_dict)

                        if session_data.is_expired(
                            buffer_minutes=0
                        ):  # No buffer for cleanup
                            self.redis_client.delete(redis_key)
                            cleaned_count += 1
                            logger.debug(f"Cleaned expired session: {redis_key}")

                except Exception as e:
                    logger.debug(f"Error processing session key {redis_key}: {e}")
                    # Delete corrupted session data
                    self.redis_client.delete(redis_key)
                    cleaned_count += 1

            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} expired sessions")

            return cleaned_count

        except Exception as e:
            logger.error(f"Error during session cleanup: {e}")
            return 0

    def get_session_info(self, fortigate_ip: str = None) -> Dict[str, Any]:
        """
        Get information about current sessions

        Args:
            fortigate_ip: Optional filter by FortiGate IP

        Returns:
            Dictionary with session statistics
        """
        try:
            if not self._is_redis_available():
                return {"error": "Redis not available"}

            pattern = f"{self.key_prefix}:*"
            session_keys = self.redis_client.keys(pattern)

            total_sessions = 0
            active_sessions = 0
            expired_sessions = 0
            sessions_by_ip = {}

            for redis_key in session_keys:
                try:
                    session_json = self.redis_client.get(redis_key)
                    if session_json:
                        session_dict = json.loads(session_json)
                        session_data = SessionData.from_dict(session_dict)

                        total_sessions += 1

                        # Count by IP
                        ip = session_data.fortigate_ip
                        if ip not in sessions_by_ip:
                            sessions_by_ip[ip] = {"active": 0, "expired": 0}

                        if session_data.is_expired(buffer_minutes=0):
                            expired_sessions += 1
                            sessions_by_ip[ip]["expired"] += 1
                        else:
                            active_sessions += 1
                            sessions_by_ip[ip]["active"] += 1

                except Exception as e:
                    logger.debug(f"Error processing session info for {redis_key}: {e}")

            return {
                "total_sessions": total_sessions,
                "active_sessions": active_sessions,
                "expired_sessions": expired_sessions,
                "sessions_by_ip": sessions_by_ip,
                "redis_connected": True,
            }

        except Exception as e:
            logger.error(f"Error getting session info: {e}")
            return {"error": str(e), "redis_connected": False}

    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on Redis session manager

        Returns:
            Dictionary with health status
        """
        try:
            health_status = {
                "redis_connected": False,
                "redis_host": self.redis_host,
                "redis_port": self.redis_port,
                "session_ttl": self.session_ttl,
                "timestamp": datetime.now().isoformat(),
            }

            if self._is_redis_available():
                health_status["redis_connected"] = True

                # Get Redis info
                redis_info = self.redis_client.info()
                health_status["redis_version"] = redis_info.get("redis_version")
                health_status["redis_memory"] = redis_info.get("used_memory_human")
                health_status["redis_uptime"] = redis_info.get("uptime_in_seconds")

                # Get session count
                session_info = self.get_session_info()
                health_status.update(session_info)

            return health_status

        except Exception as e:
            logger.error(f"Error in health check: {e}")
            return {
                "error": str(e),
                "redis_connected": False,
                "timestamp": datetime.now().isoformat(),
            }


# Global Redis session manager instance
_redis_session_manager: Optional[RedisSessionManager] = None


def get_redis_session_manager() -> RedisSessionManager:
    """Get the global Redis session manager instance"""
    global _redis_session_manager
    if _redis_session_manager is None:
        _redis_session_manager = RedisSessionManager()
    return _redis_session_manager


# Background cleanup function (can be called by scheduler)
def cleanup_expired_sessions() -> int:
    """Cleanup expired sessions - can be called by background scheduler"""
    session_manager = get_redis_session_manager()
    return session_manager.cleanup_expired_sessions()
