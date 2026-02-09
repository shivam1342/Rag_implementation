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
        logger.info("Cache service initialized (in-memory mode)")
    
    def _generate_key(self, query: str) -> str:
        """Generate cache key from query"""
        return hashlib.md5(query.encode()).hexdigest()
    
    def _is_expired(self, key: str) -> bool:
        """Check if cache entry is expired"""
        if key not in self._timestamps:
            return True
        
        cached_time = self._timestamps[key]
        expiry_time = cached_time + timedelta(seconds=settings.CACHE_TTL)
        return datetime.now() > expiry_time
    
    def get(self, query: str) -> Optional[Any]:
        """
        Get cached response for query.
        
        Args:
            query: Query string
            
        Returns:
            Cached response or None
        """
        if not settings.ENABLE_CACHE:
            return None
        
        key = self._generate_key(query)
        
        if key in self._cache and not self._is_expired(key):
            logger.info(f"Cache HIT for query: {query[:50]}...")
            return self._cache[key]
        
        logger.info(f"Cache MISS for query: {query[:50]}...")
        return None
    
    def set(self, query: str, response: Any) -> None:
        """
        Cache a response for a query.
        
        Args:
            query: Query string
            response: Response to cache
        """
        if not settings.ENABLE_CACHE:
            return
        
        key = self._generate_key(query)
        self._cache[key] = response
        self._timestamps[key] = datetime.now()
        logger.debug(f"Cached response for query: {query[:50]}...")
    
    def clear(self) -> None:
        """Clear all cache"""
        self._cache.clear()
        self._timestamps.clear()
        logger.info("Cache cleared")
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        return {
            "size": len(self._cache),
            "enabled": settings.ENABLE_CACHE,
            "ttl_seconds": settings.CACHE_TTL
        }

# Global instance
cache_service = CacheService()
