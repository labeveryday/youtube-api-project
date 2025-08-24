"""Caching utilities for API responses."""

import time
import json
from typing import Any, Dict, Optional
from cachetools import TTLCache
from dataclasses import dataclass


@dataclass
class CacheStats:
    """Cache statistics."""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    size: int = 0
    max_size: int = 0


class APICache:
    """TTL-based cache for API responses."""
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self._cache = TTLCache(maxsize=max_size, ttl=ttl)
        self._stats = CacheStats(max_size=max_size)
        self._enabled = True
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache."""
        if not self._enabled:
            return None
            
        try:
            value = self._cache[key]
            self._stats.hits += 1
            return value
        except KeyError:
            self._stats.misses += 1
            return None
    
    def set(self, key: str, value: Any) -> None:
        """Set item in cache."""
        if not self._enabled:
            return
            
        self._cache[key] = value
        self._stats.sets += 1
        self._stats.size = len(self._cache)
    
    def delete(self, key: str) -> bool:
        """Delete item from cache."""
        try:
            del self._cache[key]
            self._stats.size = len(self._cache)
            return True
        except KeyError:
            return False
    
    def clear(self) -> None:
        """Clear entire cache."""
        self._cache.clear()
        self._stats.size = 0
    
    def enable(self) -> None:
        """Enable caching."""
        self._enabled = True
    
    def disable(self) -> None:
        """Disable caching."""
        self._enabled = False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._stats.hits + self._stats.misses
        hit_rate = self._stats.hits / total_requests if total_requests > 0 else 0
        
        return {
            "enabled": self._enabled,
            "hits": self._stats.hits,
            "misses": self._stats.misses,
            "sets": self._stats.sets,
            "hit_rate": round(hit_rate, 3),
            "size": self._stats.size,
            "max_size": self._stats.max_size
        }
    
    def create_key(self, *parts: str) -> str:
        """Create a cache key from parts."""
        return ":".join(str(part) for part in parts)