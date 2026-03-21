# Updated-On: 2026-03-08
# Updated-By: Codex
# PM-Ticket: UNTRACKED

"""
Context Cache
In-memory cache for conversation contexts
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import json


@dataclass
class CacheEntry:
    """A cached conversation context."""

    entry_id: str
    messages: List[Dict[str, str]]
    metadata: Dict[str, Any]
    created_at: datetime
    last_used: datetime
    use_count: int = 0


class ContextCache:
    """
    Cache conversation contexts for reuse.

    Features:
    - Store conversation history
    - Search by content
    - TTL expiration
    - LRU eviction
    """

    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, CacheEntry] = {}
        self.access_order: List[str] = []

    def _generate_id(self, messages: List[Dict[str, str]]) -> str:
        """Generate cache ID from messages."""
        content = json.dumps(messages, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def store(
        self, messages: List[Dict[str, str]], metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store conversation in cache."""
        entry_id = self._generate_id(messages)

        now = datetime.now()

        entry = CacheEntry(
            entry_id=entry_id,
            messages=messages,
            metadata=metadata or {},
            created_at=now,
            last_used=now,
        )

        self.cache[entry_id] = entry
        self.access_order.append(entry_id)

        self._evict_if_needed()

        return entry_id

    def get(self, entry_id: str) -> Optional[List[Dict[str, str]]]:
        """Get conversation by ID."""
        if entry_id not in self.cache:
            return None

        entry = self.cache[entry_id]

        if self._is_expired(entry):
            self.remove(entry_id)
            return None

        entry.last_used = datetime.now()
        entry.use_count += 1

        self.access_order.remove(entry_id)
        self.access_order.append(entry_id)

        return entry.messages

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search cached conversations."""
        query_lower = query.lower()
        results = []

        for entry_id, entry in self.cache.items():
            if self._is_expired(entry):
                continue

            for msg in entry.messages:
                if query_lower in msg.get("content", "").lower():
                    results.append(
                        {
                            "entry_id": entry_id,
                            "messages": entry.messages,
                            "metadata": entry.metadata,
                            "use_count": entry.use_count,
                            "last_used": entry.last_used.isoformat(),
                        }
                    )
                    break

        results.sort(key=lambda x: x["use_count"], reverse=True)
        return results[:limit]

    def remove(self, entry_id: str) -> bool:
        """Remove entry from cache."""
        if entry_id in self.cache:
            del self.cache[entry_id]
            if entry_id in self.access_order:
                self.access_order.remove(entry_id)
            return True
        return False

    def clear(self):
        """Clear all cache."""
        self.cache.clear()
        self.access_order.clear()

    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if entry is expired."""
        from datetime import timedelta

        age = datetime.now() - entry.created_at
        return age.total_seconds() > self.ttl_seconds

    def _evict_if_needed(self):
        """Evict oldest entries if cache is full."""
        while len(self.cache) > self.max_size:
            if not self.access_order:
                break

            oldest_id = self.access_order[0]
            self.remove(oldest_id)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache stats."""
        total_uses = sum(e.use_count for e in self.cache.values())

        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "total_uses": total_uses,
            "avg_uses": total_uses / len(self.cache) if self.cache else 0,
        }


def create_context_cache(max_size: int = 100) -> ContextCache:
    """Factory function to create context cache."""
    return ContextCache(max_size=max_size)
