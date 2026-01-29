"""
Redis Client - Connection management and utilities

Provides a centralized Redis client with connection pooling,
health checks, and graceful fallback handling.
"""

import os
import logging
from typing import Optional, Any, Dict
from datetime import timedelta
import json

logger = logging.getLogger(__name__)

# Redis URL from environment
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

# Global connection pool
_redis_pool = None
_redis_client = None


def get_redis_client():
    """
    Get a Redis client instance with connection pooling.

    Returns:
        Redis client or None if unavailable
    """
    global _redis_client, _redis_pool

    if _redis_client is not None:
        return _redis_client

    try:
        import redis

        if _redis_pool is None:
            _redis_pool = redis.ConnectionPool.from_url(
                REDIS_URL,
                max_connections=10,
                decode_responses=True
            )

        _redis_client = redis.Redis(connection_pool=_redis_pool)
        # Test connection
        _redis_client.ping()
        logger.info("Redis client connected successfully")
        return _redis_client

    except ImportError:
        logger.warning("Redis package not installed")
        return None
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}")
        return None


def redis_health_check() -> Dict[str, Any]:
    """
    Check Redis connection health.

    Returns:
        Dict with health status and details
    """
    try:
        client = get_redis_client()
        if client is None:
            return {
                'status': 'unavailable',
                'error': 'Redis client not available'
            }

        # Ping test
        ping_result = client.ping()
        if not ping_result:
            return {
                'status': 'unhealthy',
                'error': 'Ping failed'
            }

        # Get server info
        info = client.info('server')
        memory_info = client.info('memory')

        return {
            'status': 'healthy',
            'redis_version': info.get('redis_version', 'unknown'),
            'uptime_seconds': info.get('uptime_in_seconds', 0),
            'connected_clients': client.info('clients').get('connected_clients', 0),
            'used_memory_human': memory_info.get('used_memory_human', 'unknown'),
            'used_memory_peak_human': memory_info.get('used_memory_peak_human', 'unknown'),
        }

    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }


def is_redis_available() -> bool:
    """
    Quick check if Redis is available.

    Returns:
        True if Redis is reachable, False otherwise
    """
    try:
        client = get_redis_client()
        return client is not None and client.ping()
    except Exception:
        return False


class RedisCache:
    """
    Simple cache wrapper for Redis with JSON serialization.

    Usage:
        cache = RedisCache(prefix='myapp')
        cache.set('key', {'data': 'value'}, ttl=3600)
        data = cache.get('key')
    """

    def __init__(self, prefix: str = 'cache'):
        """
        Initialize cache with key prefix.

        Args:
            prefix: Prefix for all cache keys (e.g., 'deals', 'sessions')
        """
        self.prefix = prefix
        self._client = None

    @property
    def client(self):
        """Lazy load Redis client."""
        if self._client is None:
            self._client = get_redis_client()
        return self._client

    def _make_key(self, key: str) -> str:
        """Create prefixed cache key."""
        return f"{self.prefix}:{key}"

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache.

        Args:
            key: Cache key
            default: Default value if key not found

        Returns:
            Cached value or default
        """
        if self.client is None:
            return default

        try:
            value = self.client.get(self._make_key(key))
            if value is None:
                return default
            return json.loads(value)
        except Exception as e:
            logger.warning(f"Cache get error for {key}: {e}")
            return default

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
            ttl: Time-to-live in seconds (None = no expiration)

        Returns:
            True if successful, False otherwise
        """
        if self.client is None:
            return False

        try:
            serialized = json.dumps(value, default=str)
            if ttl:
                self.client.setex(self._make_key(key), ttl, serialized)
            else:
                self.client.set(self._make_key(key), serialized)
            return True
        except Exception as e:
            logger.warning(f"Cache set error for {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        Delete key from cache.

        Args:
            key: Cache key

        Returns:
            True if key was deleted, False otherwise
        """
        if self.client is None:
            return False

        try:
            return bool(self.client.delete(self._make_key(key)))
        except Exception as e:
            logger.warning(f"Cache delete error for {key}: {e}")
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if self.client is None:
            return False

        try:
            return bool(self.client.exists(self._make_key(key)))
        except Exception:
            return False

    def clear_prefix(self) -> int:
        """
        Clear all keys with this cache's prefix.

        Returns:
            Number of keys deleted
        """
        if self.client is None:
            return 0

        try:
            pattern = f"{self.prefix}:*"
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"Cache clear error: {e}")
            return 0


# Pre-configured cache instances
deal_cache = RedisCache(prefix='deals')
session_cache = RedisCache(prefix='sessions')
fact_cache = RedisCache(prefix='facts')


# Export
__all__ = [
    'get_redis_client',
    'redis_health_check',
    'is_redis_available',
    'RedisCache',
    'deal_cache',
    'session_cache',
    'fact_cache',
    'REDIS_URL',
]
