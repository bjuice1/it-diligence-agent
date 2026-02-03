"""
Cost Estimate Cache

Provides deterministic caching for cost estimates.
Same inputs will always produce the same outputs.

Key features:
- Content-based cache keys (deterministic hash of inputs)
- Input normalization for consistent hashing
- TTL-based expiration (optional)
- Persistence to disk (optional)
"""

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """A cached cost estimate."""
    cache_key: str
    estimate: Dict[str, Any]
    created_at: float
    inputs_hash: str
    hits: int = 0

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "CacheEntry":
        return cls(**data)


class CostEstimateCache:
    """
    Cache for cost estimates with deterministic hashing.

    Usage:
        cache = CostEstimateCache()

        # Check cache before calculating
        cached = cache.get(user_count=1500, deal_type="carveout", facts=facts)
        if cached:
            return cached

        # Calculate and cache
        estimate = cost_model.estimate_costs(...)
        cache.set(estimate, user_count=1500, deal_type="carveout", facts=facts)
    """

    def __init__(
        self,
        max_entries: int = 1000,
        ttl_seconds: Optional[int] = None,
        persist_path: Optional[Path] = None
    ):
        """
        Initialize the cache.

        Args:
            max_entries: Maximum number of cached estimates
            ttl_seconds: Time-to-live for entries (None = no expiration)
            persist_path: Path to persist cache to disk (None = memory only)
        """
        self._cache: Dict[str, CacheEntry] = {}
        self.max_entries = max_entries
        self.ttl_seconds = ttl_seconds
        self.persist_path = persist_path
        self._stats = {"hits": 0, "misses": 0, "evictions": 0}

        if persist_path and persist_path.exists():
            self._load_from_disk()

    def _normalize_inputs(
        self,
        user_count: int,
        deal_type: str,
        facts: List[Dict],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Normalize inputs for consistent hashing.

        Ensures:
        - Facts are sorted by content
        - Strings are lowercased and stripped
        - Numbers are rounded to remove floating-point noise
        - Optional kwargs are sorted alphabetically
        """
        # Normalize facts - extract content and sort
        normalized_facts = []
        for fact in facts:
            content = fact.get("content", "")
            if isinstance(content, str):
                content = content.lower().strip()[:100]  # Truncate for consistency
            normalized_facts.append(content)

        # Sort for deterministic ordering
        normalized_facts = sorted(set(normalized_facts))

        # Build normalized input dict
        normalized = {
            "user_count": int(user_count),
            "deal_type": deal_type.lower().strip(),
            "facts": normalized_facts,
        }

        # Add sorted kwargs
        for key in sorted(kwargs.keys()):
            value = kwargs[key]
            if isinstance(value, float):
                value = round(value, 4)  # Remove floating-point noise
            elif isinstance(value, str):
                value = value.lower().strip()
            normalized[key] = value

        return normalized

    def _compute_hash(self, normalized_inputs: Dict[str, Any]) -> str:
        """
        Compute deterministic hash of normalized inputs.

        Uses SHA-256 for collision resistance.
        """
        # Create canonical JSON representation
        json_str = json.dumps(normalized_inputs, sort_keys=True, separators=(',', ':'))

        # Compute hash
        return hashlib.sha256(json_str.encode('utf-8')).hexdigest()[:16]

    def get_cache_key(
        self,
        user_count: int,
        deal_type: str,
        facts: List[Dict],
        **kwargs
    ) -> str:
        """
        Get the cache key for given inputs.

        Returns:
            Deterministic cache key string
        """
        normalized = self._normalize_inputs(user_count, deal_type, facts, **kwargs)
        return self._compute_hash(normalized)

    def get(
        self,
        user_count: int,
        deal_type: str,
        facts: List[Dict],
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached estimate if available.

        Returns:
            Cached estimate dict or None if not found
        """
        cache_key = self.get_cache_key(user_count, deal_type, facts, **kwargs)

        entry = self._cache.get(cache_key)
        if entry is None:
            self._stats["misses"] += 1
            return None

        # Check TTL
        if self.ttl_seconds is not None:
            age = time.time() - entry.created_at
            if age > self.ttl_seconds:
                del self._cache[cache_key]
                self._stats["misses"] += 1
                return None

        # Cache hit
        entry.hits += 1
        self._stats["hits"] += 1

        logger.debug(f"Cache hit for key {cache_key} (hits: {entry.hits})")
        return entry.estimate

    def set(
        self,
        estimate: Dict[str, Any],
        user_count: int,
        deal_type: str,
        facts: List[Dict],
        **kwargs
    ) -> str:
        """
        Cache an estimate.

        Returns:
            Cache key for the stored estimate
        """
        normalized = self._normalize_inputs(user_count, deal_type, facts, **kwargs)
        cache_key = self._compute_hash(normalized)
        inputs_hash = self._compute_hash({"inputs": normalized})

        # Evict if at capacity
        if len(self._cache) >= self.max_entries:
            self._evict_oldest()

        entry = CacheEntry(
            cache_key=cache_key,
            estimate=estimate,
            created_at=time.time(),
            inputs_hash=inputs_hash,
        )

        self._cache[cache_key] = entry

        logger.debug(f"Cached estimate with key {cache_key}")

        # Persist if configured
        if self.persist_path:
            self._save_to_disk()

        return cache_key

    def invalidate(self, cache_key: str) -> bool:
        """
        Remove a specific entry from cache.

        Returns:
            True if entry was found and removed
        """
        if cache_key in self._cache:
            del self._cache[cache_key]
            return True
        return False

    def clear(self) -> int:
        """
        Clear all cached entries.

        Returns:
            Number of entries cleared
        """
        count = len(self._cache)
        self._cache.clear()

        if self.persist_path and self.persist_path.exists():
            self.persist_path.unlink()

        return count

    def _evict_oldest(self) -> None:
        """Evict the oldest entry from cache."""
        if not self._cache:
            return

        oldest_key = min(self._cache, key=lambda k: self._cache[k].created_at)
        del self._cache[oldest_key]
        self._stats["evictions"] += 1

    def _save_to_disk(self) -> None:
        """Persist cache to disk."""
        if not self.persist_path:
            return

        data = {
            "entries": [entry.to_dict() for entry in self._cache.values()],
            "saved_at": time.time()
        }

        with open(self.persist_path, 'w') as f:
            json.dump(data, f)

    def _load_from_disk(self) -> None:
        """Load cache from disk."""
        if not self.persist_path or not self.persist_path.exists():
            return

        try:
            with open(self.persist_path, 'r') as f:
                data = json.load(f)

            for entry_data in data.get("entries", []):
                entry = CacheEntry.from_dict(entry_data)

                # Check TTL on load
                if self.ttl_seconds is not None:
                    age = time.time() - entry.created_at
                    if age > self.ttl_seconds:
                        continue

                self._cache[entry.cache_key] = entry

            logger.info(f"Loaded {len(self._cache)} cached estimates from disk")

        except Exception as e:
            logger.warning(f"Failed to load cache from disk: {e}")

    @property
    def stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return {
            **self._stats,
            "entries": len(self._cache),
            "hit_rate": self._stats["hits"] / max(1, self._stats["hits"] + self._stats["misses"])
        }

    def __len__(self) -> int:
        return len(self._cache)

    def __contains__(self, key: str) -> bool:
        return key in self._cache


# Global cache instance
_cost_cache: Optional[CostEstimateCache] = None


def get_cost_cache(
    max_entries: int = 1000,
    ttl_seconds: Optional[int] = None,
    persist_path: Optional[Path] = None
) -> CostEstimateCache:
    """
    Get or create the global cost estimate cache.

    Args:
        max_entries: Maximum cached estimates
        ttl_seconds: Cache TTL (None = no expiration)
        persist_path: Path for persistence (None = memory only)

    Returns:
        Global CostEstimateCache instance
    """
    global _cost_cache

    if _cost_cache is None:
        _cost_cache = CostEstimateCache(
            max_entries=max_entries,
            ttl_seconds=ttl_seconds,
            persist_path=persist_path
        )

    return _cost_cache


def clear_cost_cache() -> int:
    """Clear the global cost cache."""
    global _cost_cache

    if _cost_cache is not None:
        return _cost_cache.clear()
    return 0


# =============================================================================
# DETERMINISTIC ESTIMATION HELPERS
# =============================================================================

def normalize_facts_for_estimation(facts: List[Dict]) -> List[Dict]:
    """
    Normalize facts for deterministic estimation.

    - Sorts by content for consistent ordering
    - Normalizes content strings
    - Removes duplicates

    Args:
        facts: List of fact dicts

    Returns:
        Normalized and sorted facts
    """
    seen = set()
    normalized = []

    for fact in facts:
        content = fact.get("content", "")
        if isinstance(content, str):
            content = content.strip()

        # Create unique key
        key = content.lower()[:100] if isinstance(content, str) else str(content)

        if key in seen:
            continue
        seen.add(key)

        normalized.append({
            **fact,
            "content": content,
            "_normalized": True
        })

    # Sort by content for deterministic ordering
    normalized.sort(key=lambda f: f.get("content", "").lower() if isinstance(f.get("content", ""), str) else "")

    return normalized


def get_deterministic_estimate_hash(
    user_count: int,
    deal_type: str,
    facts: List[Dict],
    **kwargs
) -> str:
    """
    Get a deterministic hash for cost estimation inputs.

    Same inputs will always produce the same hash.

    Args:
        user_count: Number of users
        deal_type: Deal type (carveout, acquisition)
        facts: List of facts
        **kwargs: Additional parameters

    Returns:
        Deterministic hash string
    """
    cache = get_cost_cache()
    return cache.get_cache_key(user_count, deal_type, facts, **kwargs)
