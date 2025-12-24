"""
Response Cache Service

Provides Redis-based caching for API responses to improve performance.
Reduces redundant API calls and improves response times.
"""

import os
import redis
import json
import logging
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ResponseCacheService:
    """
    Redis-based response caching service for API responses.
    Provides TTL-based caching with automatic expiration.
    """

    def __init__(
        self,
        redis_host: str = None,
        redis_port: int = None,
        redis_db: int = 1,  # Use DB 1 for response cache (DB 0 for sessions)
        redis_password: str = None,
        default_ttl: int = 60,  # Default 60 seconds TTL
    ):
        """
        Initialize response cache service

        Args:
            redis_host: Redis server hostname (default from env REDIS_HOST)
            redis_port: Redis server port (default from env REDIS_PORT or 6379)
            redis_db: Redis database number (default 1 for cache)
            redis_password: Redis password (default from env REDIS_PASSWORD)
            default_ttl: Default cache TTL in seconds (default 60)
        """
        self.redis_host = redis_host or os.getenv("REDIS_HOST", "localhost")
        self.redis_port = redis_port or int(os.getenv("REDIS_PORT", "6379"))
        self.redis_db = redis_db
        self.redis_password = redis_password or os.getenv("REDIS_PASSWORD")
        self.default_ttl = default_ttl

        self.redis_client: Optional[redis.Redis] = None
        self.key_prefix = "api_cache"
        self._connect_redis()

        # Cache statistics
        self.stats = {"hits": 0, "misses": 0, "sets": 0, "errors": 0}

    def _connect_redis(self) -> None:
        """Establish Redis connection with error handling"""
        try:
            self.redis_client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                db=self.redis_db,
                password=self.redis_password,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
            )
            self.redis_client.ping()
            logger.info(
                f"Response cache service connected to Redis: {self.redis_host}:{self.redis_port} (DB {self.redis_db})"
            )
        except redis.ConnectionError as e:
            logger.warning(f"Redis not available for response caching: {e}")
            self.redis_client = None
        except Exception as e:
            logger.error(f"Unexpected error connecting to Redis: {e}")
            self.redis_client = None

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

    def _generate_cache_key(self, endpoint: str, params: Dict[str, Any] = None) -> str:
        """Generate cache key from endpoint and parameters"""
        key_data = {"endpoint": endpoint}
        if params:
            key_data["params"] = sorted(params.items())
        key_string = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        return f"{self.key_prefix}:{key_hash}"

    def get(
        self, endpoint: str, params: Dict[str, Any] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached response for endpoint

        Args:
            endpoint: API endpoint path
            params: Optional parameters dictionary

        Returns:
            Cached response data or None if not found/expired
        """
        if not self._is_redis_available():
            return None

        try:
            cache_key = self._generate_cache_key(endpoint, params)
            cached_data = self.redis_client.get(cache_key)

            if cached_data:
                try:
                    data = json.loads(cached_data)
                    self.stats["hits"] += 1
                    logger.debug(f"Cache HIT for {endpoint}")
                    return data
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to decode cached data for {endpoint}: {e}")
                    self.redis_client.delete(cache_key)
                    self.stats["errors"] += 1
            else:
                self.stats["misses"] += 1
                logger.debug(f"Cache MISS for {endpoint}")

        except Exception as e:
            logger.warning(f"Error retrieving cache for {endpoint}: {e}")
            self.stats["errors"] += 1

        return None

    def set(
        self,
        endpoint: str,
        data: Dict[str, Any],
        params: Dict[str, Any] = None,
        ttl: int = None,
    ) -> bool:
        """
        Cache response data for endpoint

        Args:
            endpoint: API endpoint path
            data: Response data to cache
            params: Optional parameters dictionary
            ttl: Time to live in seconds (defaults to default_ttl)

        Returns:
            True if cached successfully, False otherwise
        """
        if not self._is_redis_available():
            return False

        try:
            cache_key = self._generate_cache_key(endpoint, params)
            ttl = ttl or self.default_ttl

            # Add metadata to cached data
            cached_data = {
                "data": data,
                "cached_at": datetime.now().isoformat(),
                "endpoint": endpoint,
                "ttl": ttl,
            }

            cached_json = json.dumps(cached_data)
            self.redis_client.setex(cache_key, ttl, cached_json)
            self.stats["sets"] += 1
            logger.debug(f"Cached response for {endpoint} (TTL: {ttl}s)")
            return True

        except Exception as e:
            logger.warning(f"Error caching response for {endpoint}: {e}")
            self.stats["errors"] += 1
            return False

    def delete(self, endpoint: str, params: Dict[str, Any] = None) -> bool:
        """
        Delete cached response for endpoint

        Args:
            endpoint: API endpoint path
            params: Optional parameters dictionary

        Returns:
            True if deleted successfully, False otherwise
        """
        if not self._is_redis_available():
            return False

        try:
            cache_key = self._generate_cache_key(endpoint, params)
            result = self.redis_client.delete(cache_key)
            logger.debug(f"Deleted cache for {endpoint}")
            return result > 0
        except Exception as e:
            logger.warning(f"Error deleting cache for {endpoint}: {e}")
            return False

    def clear_all(self) -> int:
        """
        Clear all cached responses

        Returns:
            Number of keys deleted
        """
        if not self._is_redis_available():
            return 0

        try:
            pattern = f"{self.key_prefix}:*"
            keys = self.redis_client.keys(pattern)
            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(f"Cleared {deleted} cached responses")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (
            (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        )

        stats = {
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "sets": self.stats["sets"],
            "errors": self.stats["errors"],
            "total_requests": total_requests,
            "hit_rate_percent": round(hit_rate, 2),
            "redis_available": self._is_redis_available(),
        }

        if self._is_redis_available():
            try:
                pattern = f"{self.key_prefix}:*"
                keys = self.redis_client.keys(pattern)
                stats["cached_items"] = len(keys)
            except Exception:
                stats["cached_items"] = 0
        else:
            stats["cached_items"] = 0

        return stats


# Global instance
_response_cache_service = None


def get_response_cache_service() -> ResponseCacheService:
    """Get global response cache service instance"""
    global _response_cache_service
    if _response_cache_service is None:
        _response_cache_service = ResponseCacheService()
    return _response_cache_service
