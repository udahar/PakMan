#!/usr/bin/env python3
# Updated-On: 2026-03-07
# Updated-By: Codex
# PM-Ticket: UNTRACKED
#
"""
Response Caching Layer for PromptOS

Caches LLM responses to save tokens + time on repeated prompts.
Supports TTL, prompt hashing, and cache invalidation.

Usage:
    cache = ResponseCache(ttl_seconds=3600, max_size=10000)
    
    # Check cache
    cached = cache.get(prompt, model, strategy)
    if cached:
        return cached.response
    
    # Run LLM and cache
    response = llm(prompt)
    cache.set(prompt, model, strategy, response)
"""

import hashlib
import json
import os
import time
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict


@dataclass
class CachedResponse:
    """A cached LLM response."""
    prompt_hash: str
    model: str
    strategy_key: str
    response: str
    tokens_used: int
    created_at: float
    ttl_seconds: int
    hit_count: int = 0
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        return time.time() > (self.created_at + self.ttl_seconds)
    
    def to_dict(self) -> Dict:
        """Convert to dict for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CachedResponse':
        """Create from dict."""
        return cls(**data)


class ResponseCache:
    """
    Response caching layer for PromptOS.
    
    Features:
    - TTL-based expiry
    - LRU eviction
    - Prompt hashing for lookup
    - Hit/miss tracking
    - Persistent storage
    """
    
    def __init__(
        self,
        ttl_seconds: int = 3600,
        max_size: int = 10000,
        storage_path: Optional[str] = None,
    ):
        """
        Initialize response cache.
        
        Args:
            ttl_seconds: Default TTL for cache entries (1 hour)
            max_size: Maximum cache entries before LRU eviction
            storage_path: Path for persistent storage
        """
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size
        self.storage_path = storage_path or "PromptOS/cache.json"
        self.db_only = str(os.getenv("PROMPTOS_DB_ONLY", "1")).lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        
        # Cache storage: key → CachedResponse
        self._cache: Dict[str, CachedResponse] = {}
        
        # Access order for LRU: list of keys (most recent at end)
        self._access_order: List[str] = []
        
        # Statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "tokens_saved": 0,
        }
        
        # Load existing cache
        self._load()
    
    def _make_key(self, prompt: str, model: str, strategy: List[str]) -> str:
        """Create cache key from prompt + model + strategy."""
        key_data = {
            "prompt": prompt.strip().lower(),
            "model": model,
            "strategy": sorted(strategy),
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()[:32]
    
    def get(
        self,
        prompt: str,
        model: str,
        strategy: List[str],
    ) -> Optional[CachedResponse]:
        """
        Get cached response if available and not expired.
        
        Args:
            prompt: Original prompt
            model: Model name
            strategy: Strategy modules used
        
        Returns:
            CachedResponse or None
        """
        key = self._make_key(prompt, model, strategy)
        
        if key not in self._cache:
            self.stats["misses"] += 1
            return None
        
        entry = self._cache[key]
        
        # Check expiry
        if entry.is_expired():
            self._delete(key)
            self.stats["misses"] += 1
            return None
        
        # Update access order (move to end = most recent)
        self._touch(key)
        
        # Update hit count
        entry.hit_count += 1
        self.stats["hits"] += 1
        
        return entry
    
    def set(
        self,
        prompt: str,
        model: str,
        strategy: List[str],
        response: str,
        tokens_used: int = 0,
        ttl_seconds: Optional[int] = None,
    ) -> str:
        """
        Cache a response.
        
        Args:
            prompt: Original prompt
            model: Model name
            strategy: Strategy modules used
            response: LLM response
            tokens_used: Token count
            ttl_seconds: Custom TTL (uses default if None)
        
        Returns:
            Cache key
        """
        key = self._make_key(prompt, model, strategy)
        
        # Create cache entry
        entry = CachedResponse(
            prompt_hash=key,
            model=model,
            strategy_key=",".join(sorted(strategy)),
            response=response,
            tokens_used=tokens_used,
            created_at=time.time(),
            ttl_seconds=ttl_seconds or self.ttl_seconds,
        )
        
        # Evict if over capacity
        while len(self._cache) >= self.max_size:
            self._evict_lru()
        
        # Store
        self._cache[key] = entry
        self._access_order.append(key)
        
        # Auto-save periodically
        if len(self._cache) % 100 == 0:
            self._save()
        
        return key
    
    def _touch(self, key: str):
        """Update access order (mark as recently used)."""
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)
    
    def _delete(self, key: str):
        """Delete cache entry."""
        if key in self._cache:
            del self._cache[key]
        if key in self._access_order:
            self._access_order.remove(key)
    
    def _evict_lru(self):
        """Evict least recently used entry."""
        if not self._access_order:
            return
        
        # First entry = least recently used
        lru_key = self._access_order[0]
        self._delete(lru_key)
        self.stats["evictions"] += 1
    
    def clear(self):
        """Clear entire cache."""
        self._cache.clear()
        self._access_order.clear()
        self._save()
    
    def cleanup_expired(self) -> int:
        """Remove expired entries. Returns count removed."""
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired()
        ]
        
        for key in expired_keys:
            self._delete(key)
        
        if expired_keys:
            self._save()
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = len(self._cache)
        hit_rate = (
            self.stats["hits"] / (self.stats["hits"] + self.stats["misses"])
            if (self.stats["hits"] + self.stats["misses"]) > 0
            else 0.0
        )
        
        return {
            "entries": total,
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "evictions": self.stats["evictions"],
            "hit_rate": hit_rate,
            "tokens_saved": self.stats["tokens_saved"],
            "max_size": self.max_size,
            "ttl_seconds": self.ttl_seconds,
        }
    
    def _save(self):
        """Save cache to storage."""
        if self.db_only:
            return
        try:
            data = {
                "entries": {k: v.to_dict() for k, v in self._cache.items()},
                "access_order": self._access_order,
                "stats": self.stats,
                "saved_at": time.time(),
            }
            
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"[Cache] Save failed: {e}")
    
    def _load(self):
        """Load cache from storage."""
        if self.db_only:
            return
        try:
            if Path(self.storage_path).exists():
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                
                self._cache = {
                    k: CachedResponse.from_dict(v)
                    for k, v in data.get("entries", {}).items()
                }
                self._access_order = data.get("access_order", [])
                self.stats = data.get("stats", self.stats)
                
                print(f"[Cache] Loaded {len(self._cache)} entries")
        except Exception as e:
            print(f"[Cache] Load failed: {e}")
