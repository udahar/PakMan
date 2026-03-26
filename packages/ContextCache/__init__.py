"""
ContextCache - In-memory cache for conversation contexts.

A high-performance caching system for storing and retrieving conversation
contexts with TTL expiration, LRU eviction, and content search.

Usage:
    from context_cache import ContextCache
    
    cache = ContextCache()
    entry_id = cache.store([{"role": "user", "content": "Hello"}])
    messages = cache.get(entry_id)
"""

__version__ = "0.1.0"

from .cache import ContextCache, CacheEntry

__all__ = [
    "ContextCache",
    "CacheEntry",
]
