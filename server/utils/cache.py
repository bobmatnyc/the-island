"""
Performance Caching Module

Design Decision: Time-based LRU cache for expensive operations
Rationale:
- Entity detection: ~158ms avg, can cache by text hash
- Document similarity: ~200ms avg, can cache by doc_id
- TTL prevents stale data while improving performance

Trade-offs:
- Memory: ~10MB for 1000 cached results vs. no cache
- Staleness: 5-min TTL vs. always fresh data
- Complexity: Simple dict-based cache vs. Redis (overkill for our scale)

Performance Target:
- Cache hit: <1ms
- Cache miss: Original operation time
- Memory: <50MB total cache size

Alternatives Considered:
1. Redis: Rejected - adds deployment complexity, not needed at 33K docs
2. functools.lru_cache: Rejected - no TTL support, memory leaks possible
3. No caching: Rejected - user experience suffers with repeated searches
"""

import hashlib
import time
from collections import OrderedDict
from typing import Any, Callable, Optional, TypeVar, Generic
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class TTLCache(Generic[T]):
    """
    Time-based LRU cache with automatic expiration.

    Usage:
        cache = TTLCache[list](max_size=100, ttl_seconds=300)
        result = cache.get_or_compute(key, expensive_function)

    Performance:
        - Get: O(1) average, O(n) worst case for expired cleanup
        - Set: O(1) average
        - Memory: O(max_size)

    Thread Safety: Not thread-safe. Use locks if needed for concurrent access.
    """

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 300):
        """
        Initialize TTL cache.

        Args:
            max_size: Maximum cache entries (default: 1000)
            ttl_seconds: Time to live in seconds (default: 300 = 5 minutes)
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: OrderedDict[str, tuple[T, float]] = OrderedDict()
        self.hits = 0
        self.misses = 0

    def _is_expired(self, timestamp: float) -> bool:
        """Check if cache entry is expired."""
        return time.time() - timestamp > self.ttl_seconds

    def _cleanup_expired(self):
        """Remove expired entries from cache."""
        current_time = time.time()
        expired_keys = [
            key for key, (_, timestamp) in self.cache.items()
            if current_time - timestamp > self.ttl_seconds
        ]
        for key in expired_keys:
            del self.cache[key]

        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

    def get(self, key: str) -> Optional[T]:
        """
        Get value from cache if exists and not expired.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        if key in self.cache:
            value, timestamp = self.cache[key]

            if not self._is_expired(timestamp):
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                self.hits += 1
                return value
            else:
                # Expired, remove it
                del self.cache[key]

        self.misses += 1
        return None

    def set(self, key: str, value: T):
        """
        Store value in cache with current timestamp.

        Args:
            key: Cache key
            value: Value to cache
        """
        # Remove if already exists (update timestamp)
        if key in self.cache:
            del self.cache[key]

        # Add new entry
        self.cache[key] = (value, time.time())

        # Evict oldest if over capacity
        while len(self.cache) > self.max_size:
            self.cache.popitem(last=False)

        # Periodic cleanup (every 100 sets)
        if len(self.cache) % 100 == 0:
            self._cleanup_expired()

    def get_or_compute(self, key: str, compute_fn: Callable[[], T]) -> T:
        """
        Get from cache or compute and store.

        Args:
            key: Cache key
            compute_fn: Function to compute value if not cached

        Returns:
            Cached or computed value

        Example:
            >>> cache = TTLCache[list]()
            >>> result = cache.get_or_compute("entities:doc-123", lambda: detect_entities(text))
        """
        cached = self.get(key)
        if cached is not None:
            return cached

        # Compute and cache
        value = compute_fn()
        self.set(key, value)
        return value

    def invalidate(self, key: str):
        """Remove key from cache."""
        if key in self.cache:
            del self.cache[key]

    def clear(self):
        """Clear entire cache."""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
        logger.info("Cache cleared")

    def stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache metrics:
            - size: Current entries
            - max_size: Maximum capacity
            - hits: Cache hit count
            - misses: Cache miss count
            - hit_rate: Hit rate percentage
        """
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0.0

        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(hit_rate, 2),
            "ttl_seconds": self.ttl_seconds
        }


def hash_text(text: str) -> str:
    """
    Create stable hash for text content.

    Used for cache keys when content is the key identifier.

    Args:
        text: Text to hash

    Returns:
        SHA-256 hash (hex string)

    Example:
        >>> hash_text("Jeffrey Epstein and...")
        'a1b2c3d4...'
    """
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


# Global cache instances for different services
_entity_detection_cache: Optional[TTLCache] = None
_similarity_cache: Optional[TTLCache] = None


def get_entity_cache() -> TTLCache:
    """
    Get singleton cache for entity detection results.

    Configuration:
    - Max size: 500 entries
    - TTL: 5 minutes
    - Key format: hash(document_text)

    Returns:
        TTLCache instance for entity detection
    """
    global _entity_detection_cache
    if _entity_detection_cache is None:
        _entity_detection_cache = TTLCache(max_size=500, ttl_seconds=300)
        logger.info("Initialized entity detection cache (500 entries, 5min TTL)")
    return _entity_detection_cache


def get_similarity_cache() -> TTLCache:
    """
    Get singleton cache for document similarity results.

    Configuration:
    - Max size: 200 entries
    - TTL: 10 minutes (similarity less likely to change)
    - Key format: f"{doc_id}:{limit}:{threshold}"

    Returns:
        TTLCache instance for similarity search
    """
    global _similarity_cache
    if _similarity_cache is None:
        _similarity_cache = TTLCache(max_size=200, ttl_seconds=600)
        logger.info("Initialized similarity search cache (200 entries, 10min TTL)")
    return _similarity_cache
