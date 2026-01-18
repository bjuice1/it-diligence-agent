"""
Simple caching utility for expensive operations.

Uses input hash to cache results and avoid recomputation.
"""

import hashlib
import json
from typing import Any, Callable, Optional
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class SimpleCache:
    """
    Simple in-memory cache with hash-based keys.
    
    Thread-safe for read operations, but not for concurrent writes.
    For this use case (coverage/synthesis), that's acceptable since
    these operations are typically sequential.
    """
    
    def __init__(self, max_size: int = 100):
        """
        Initialize cache.
        
        Args:
            max_size: Maximum number of entries (LRU eviction)
        """
        self._cache: dict = {}
        self._access_order: list = []  # For LRU
        self.max_size = max_size
    
    def _make_key(self, *args, **kwargs) -> str:
        """Create cache key from arguments."""
        # Serialize to JSON for hashing
        try:
            key_data = {
                "args": args,
                "kwargs": kwargs
            }
            key_str = json.dumps(key_data, sort_keys=True, default=str)
            return hashlib.sha256(key_str.encode()).hexdigest()
        except (TypeError, ValueError) as e:
            logger.warning(f"Could not create cache key: {e}")
            return None
    
    def get(self, *args, **kwargs) -> Optional[Any]:
        """Get cached value if exists."""
        key = self._make_key(*args, **kwargs)
        if key is None:
            return None
        
        if key in self._cache:
            # Update access order (move to end)
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)
            return self._cache[key]
        
        return None
    
    def set(self, value: Any, *args, **kwargs):
        """Set cached value."""
        key = self._make_key(*args, **kwargs)
        if key is None:
            return
        
        # Evict oldest if at capacity
        if len(self._cache) >= self.max_size and self._access_order:
            oldest_key = self._access_order.pop(0)
            del self._cache[oldest_key]
        
        self._cache[key] = value
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)
    
    def clear(self):
        """Clear all cached entries."""
        self._cache.clear()
        self._access_order.clear()
    
    def stats(self) -> dict:
        """Get cache statistics."""
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hit_rate": "N/A"  # Would need to track hits/misses
        }


# Global cache instances
_coverage_cache = SimpleCache(max_size=50)
_synthesis_cache = SimpleCache(max_size=50)


def cached_coverage(func: Callable) -> Callable:
    """Decorator to cache coverage calculation results."""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        # Create cache key from fact_store state
        fact_store = self.fact_store if hasattr(self, 'fact_store') else args[0] if args else None
        if fact_store:
            # Use fact count and gap count as part of key (simple but effective)
            cache_key = (
                len(fact_store.facts),
                len(fact_store.gaps),
                tuple(sorted(set(f.domain for f in fact_store.facts)))
            )
        else:
            cache_key = (args, kwargs)
        
        # Try cache
        cached = _coverage_cache.get(cache_key)
        if cached is not None:
            logger.debug(f"Cache hit for {func.__name__}")
            return cached
        
        # Compute and cache
        result = func(self, *args, **kwargs)
        _coverage_cache.set(result, cache_key)
        return result
    
    return wrapper


def cached_synthesis(func: Callable) -> Callable:
    """Decorator to cache synthesis calculation results."""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        # Create cache key from fact_store and reasoning_store state
        fact_store = self.fact_store if hasattr(self, 'fact_store') else None
        reasoning_store = self.reasoning_store if hasattr(self, 'reasoning_store') else None
        
        if fact_store and reasoning_store:
            cache_key = (
                len(fact_store.facts),
                len(fact_store.gaps),
                len(reasoning_store.risks),
                len(reasoning_store.work_items),
                tuple(sorted(set(f.domain for f in fact_store.facts)))
            )
        else:
            cache_key = (args, kwargs)
        
        # Try cache
        cached = _synthesis_cache.get(cache_key)
        if cached is not None:
            logger.debug(f"Cache hit for {func.__name__}")
            return cached
        
        # Compute and cache
        result = func(self, *args, **kwargs)
        _synthesis_cache.set(result, cache_key)
        return result
    
    return wrapper
