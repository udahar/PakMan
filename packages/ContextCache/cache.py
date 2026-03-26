"""
Context Cache - In-memory cache for conversation contexts.

A high-performance caching system for storing and retrieving conversation
contexts with TTL expiration, LRU eviction, and content search.

Features:
- Store conversation history
- Search by content
- TTL expiration
- LRU eviction
- Statistics tracking

Usage:
    from context_cache import ContextCache
    
    cache = ContextCache(max_size=100, ttl_seconds=3600)
    
    # Store conversation
    entry_id = cache.store(messages, metadata={"user_id": "123"})
    
    # Retrieve
    messages = cache.get(entry_id)
    
    # Search
    results = cache.search("authentication", limit=5)
"""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class CacheError(Exception):
    """Base exception for cache operations."""
    pass


class CacheExpiredError(CacheError):
    """Raised when a cache entry has expired."""
    pass


class CacheNotFoundError(CacheError):
    """Raised when a cache entry is not found."""
    pass


@dataclass
class CacheEntry:
    """A cached conversation context."""
    entry_id: str
    messages: List[Dict[str, str]]
    metadata: Dict[str, Any]
    created_at: datetime
    last_used: datetime
    use_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "messages": self.messages,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "last_used": self.last_used.isoformat(),
            "use_count": self.use_count,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CacheEntry":
        return cls(
            entry_id=data["entry_id"],
            messages=data["messages"],
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            last_used=datetime.fromisoformat(data["last_used"]),
            use_count=data.get("use_count", 0),
        )


class ContextCache:
    """
    Cache conversation contexts for reuse.
    
    Features:
    - Store conversation history
    - Search by content
    - TTL expiration
    - LRU eviction
    """
    
    DEFAULT_MAX_SIZE = 100
    DEFAULT_TTL_SECONDS = 3600
    
    def __init__(
        self,
        max_size: Optional[int] = None,
        ttl_seconds: Optional[int] = None
    ) -> None:
        self.max_size = max_size or self.DEFAULT_MAX_SIZE
        self.ttl_seconds = ttl_seconds or self.DEFAULT_TTL_SECONDS
        self.cache: Dict[str, CacheEntry] = {}
        self.access_order: List[str] = []
        
        logger.info(
            "ContextCache initialized (max_size=%d, ttl=%ds)",
            self.max_size, self.ttl_seconds
        )
    
    def _generate_id(self, messages: List[Dict[str, str]]) -> str:
        """Generate cache ID from messages."""
        content = json.dumps(messages, sort_keys=True, default=str)
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def store(
        self,
        messages: List[Dict[str, str]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store conversation in cache.
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys
            metadata: Optional metadata dict
        
        Returns:
            Cache entry ID
        """
        if not messages:
            raise ValueError("messages cannot be empty")
        
        entry_id = self._generate_id(messages)
        now = datetime.now()
        
        entry = CacheEntry(
            entry_id=entry_id,
            messages=messages,
            metadata=metadata or {},
            created_at=now,
            last_used=now,
        )
        
        if entry_id in self.cache:
            self.access_order.remove(entry_id)
        else:
            self._evict_if_needed()
        
        self.cache[entry_id] = entry
        self.access_order.append(entry_id)
        
        logger.debug("Stored cache entry: %s (%d messages)", entry_id, len(messages))
        
        return entry_id
    
    def get(self, entry_id: str) -> Optional[List[Dict[str, str]]]:
        """
        Get conversation by ID.
        
        Args:
            entry_id: Cache entry ID
        
        Returns:
            List of messages or None if not found/expired
        """
        if entry_id not in self.cache:
            logger.debug("Cache miss: %s", entry_id)
            return None
        
        entry = self.cache[entry_id]
        
        if self._is_expired(entry):
            logger.debug("Cache entry expired: %s", entry_id)
            self.remove(entry_id)
            return None
        
        entry.last_used = datetime.now()
        entry.use_count += 1
        
        if entry_id in self.access_order:
            self.access_order.remove(entry_id)
        self.access_order.append(entry_id)
        
        logger.debug("Cache hit: %s (use #%d)", entry_id, entry.use_count)
        
        return entry.messages
    
    def get_with_metadata(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation with full metadata."""
        if entry_id not in self.cache:
            return None
        
        entry = self.cache[entry_id]
        
        if self._is_expired(entry):
            self.remove(entry_id)
            return None
        
        return entry.to_dict()
    
    def search(
        self,
        query: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search cached conversations.
        
        Args:
            query: Search query string
            limit: Maximum number of results
        
        Returns:
            List of matching entries with metadata
        """
        if not query:
            return []
        
        query_lower = query.lower()
        results: List[Dict[str, Any]] = []
        
        for entry_id, entry in self.cache.items():
            if self._is_expired(entry):
                continue
            
            for msg in entry.messages:
                content = msg.get("content", "")
                if content and query_lower in content.lower():
                    results.append({
                        "entry_id": entry_id,
                        "messages": entry.messages,
                        "metadata": entry.metadata,
                        "use_count": entry.use_count,
                        "last_used": entry.last_used.isoformat(),
                        "match_content": content[:200],
                    })
                    break
        
        results.sort(key=lambda x: x["use_count"], reverse=True)
        
        logger.debug("Search '%s' found %d results", query, len(results))
        
        return results[:limit]
    
    def remove(self, entry_id: str) -> bool:
        """
        Remove entry from cache.
        
        Args:
            entry_id: Cache entry ID
        
        Returns:
            True if entry was removed, False if not found
        """
        if entry_id in self.cache:
            del self.cache[entry_id]
            if entry_id in self.access_order:
                self.access_order.remove(entry_id)
            logger.debug("Removed cache entry: %s", entry_id)
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
        self.access_order.clear()
        logger.info("Cache cleared")
    
    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if entry is expired."""
        age = datetime.now() - entry.created_at
        return age.total_seconds() > self.ttl_seconds
    
    def _evict_if_needed(self) -> None:
        """Evict oldest entries if cache is full."""
        while len(self.cache) >= self.max_size:
            if not self.access_order:
                break
            
            oldest_id = self.access_order[0]
            self.remove(oldest_id)
            logger.debug("Evicted oldest entry: %s", oldest_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_uses = sum(e.use_count for e in self.cache.values())
        expired_count = sum(1 for e in self.cache.values() if self._is_expired(e))
        
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "total_uses": total_uses,
            "avg_uses": total_uses / len(self.cache) if self.cache else 0,
            "expired_entries": expired_count,
            "ttl_seconds": self.ttl_seconds,
        }
    
    def cleanup_expired(self) -> int:
        """Remove all expired entries."""
        expired_ids = [
            entry_id for entry_id, entry in self.cache.items()
            if self._is_expired(entry)
        ]
        
        for entry_id in expired_ids:
            self.remove(entry_id)
        
        if expired_ids:
            logger.info("Cleaned up %d expired entries", len(expired_ids))
        
        return len(expired_ids)
    
    def export_all(self) -> List[Dict[str, Any]]:
        """Export all non-expired entries."""
        return [
            entry.to_dict()
            for entry in self.cache.values()
            if not self._is_expired(entry)
        ]


_cache: Optional[ContextCache] = None


def get_cache(
    max_size: Optional[int] = None,
    ttl_seconds: Optional[int] = None
) -> ContextCache:
    """Get or create global cache instance."""
    global _cache
    if _cache is None:
        _cache = ContextCache(max_size=max_size, ttl_seconds=ttl_seconds)
    return _cache


def store(messages: List[Dict[str, str]], metadata: Optional[Dict[str, Any]] = None) -> str:
    """Store conversation in global cache."""
    return get_cache().store(messages, metadata)


def get(entry_id: str) -> Optional[List[Dict[str, str]]]:
    """Get conversation from global cache."""
    return get_cache().get(entry_id)


def search(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search global cache."""
    return get_cache().search(query, limit)


def clear() -> None:
    """Clear global cache."""
    get_cache().clear()
