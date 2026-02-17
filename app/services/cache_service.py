# app/services/cache_service.py
from typing import Any, Optional
import hashlib
import json
from datetime import datetime, timedelta
from app.core.config import settings
from app.core.logger import logger

class CacheService:
    """Simple in-memory cache service (fallback implementation)"""
    
    def __init__(self):
        self._cache = {}  # Simple dict cache
        self._timestamps = {}  # Track when items were cached
        self.hits = 0  # Cache hit counter
        self.misses = 0  # Cache miss counter
        logger.info("Cache service initialized (in-memory mode)")
    
    def _generate_key(self, query: str, session_id: Optional[str] = None) -> str:
        """Generate cache key from query and session_id"""
        # Include session_id in cache key for session isolation
        key_string = f"{query}:{session_id or 'global'}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _is_expired(self, key: str) -> bool:
        """Check if cache entry is expired"""
        if key not in self._timestamps:
            return True
        
        cached_time = self._timestamps[key]
        expiry_time = cached_time + timedelta(seconds=settings.CACHE_TTL)
        return datetime.now() > expiry_time
    
    def get(self, query: str, session_id: Optional[str] = None) -> Optional[Any]:
        """
        Get cached response for query.
        
        Args:
            query: Query string
            session_id: Optional session ID for cache isolation
            
        Returns:
            Cached response or None
        """
        if not settings.ENABLE_CACHE:
            return None
        
        key = self._generate_key(query, session_id)
        
        if key in self._cache and not self._is_expired(key):
            self.hits += 1
            logger.info(f"Cache HIT for query: {query[:50]}...")
            return self._cache[key]
        
        self.misses += 1
        logger.info(f"Cache MISS for query: {query[:50]}...")
        return None
    
    def set(self, query: str, response: Any, session_id: Optional[str] = None) -> None:
        """
        Cache a response for a query.
        
        Args:
            query: Query string
            response: Response to cache
            session_id: Optional session ID for cache isolation
        """
        if not settings.ENABLE_CACHE:
            return
        
        key = self._generate_key(query, session_id)
        self._cache[key] = response
        self._timestamps[key] = datetime.now()
        logger.debug(f"Cached response for query: {query[:50]}...")
    
    def clear(self) -> None:
        """Clear all cache"""
        self._cache.clear()
        self._timestamps.clear()
        self.hits = 0
        self.misses = 0
        logger.info("Cache cleared")
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "size": len(self._cache),
            "enabled": settings.ENABLE_CACHE,
            "ttl_seconds": settings.CACHE_TTL,
            "hits": self.hits,
            "misses": self.misses,
            "total_requests": total_requests,
            "hit_rate_percent": round(hit_rate, 2)
        }

# Global instance
cache_service = CacheService()
