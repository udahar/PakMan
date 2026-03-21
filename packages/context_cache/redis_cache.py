# Updated-On: 2026-03-08
# Updated-By: Codex
# PM-Ticket: UNTRACKED

"""
Redis Cache Backend
Redis-based caching for distributed systems
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import hashlib

try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class RedisCache:
    """
    Redis-backed context cache for distributed systems.

    Features:
    - Distributed caching
    - TTL support
    - Pub/sub for cache invalidation
    - Cluster support
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        prefix: str = "frank:context:",
        decode_responses: bool = True,
        ssl: bool = False,
    ):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.prefix = prefix
        self.decode_responses = decode_responses
        self.ssl = ssl

        self.client = None
        self.use_redis = False

        self._connect()

    def _connect(self):
        """Connect to Redis."""
        if not REDIS_AVAILABLE:
            print("[RedisCache] Redis package not available")
            return

        try:
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=self.decode_responses,
                ssl=self.ssl,
            )
            self.client.ping()
            self.use_redis = True
            print(f"[RedisCache] Connected to Redis at {self.host}:{self.port}")
        except Exception as e:
            print(f"[RedisCache] Connection failed: {e}")
            self.use_redis = False

    def _make_key(self, key: str) -> str:
        """Make Redis key with prefix."""
        return f"{self.prefix}{key}"

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set cache value with optional TTL."""
        if not self.use_redis:
            return False

        try:
            serialized = json.dumps(value, default=str)

            if ttl:
                self.client.setex(self._make_key(key), ttl, serialized)
            else:
                self.client.set(self._make_key(key), serialized)

            return True
        except Exception as e:
            print(f"[RedisCache] Set error: {e}")
            return False

    def get(self, key: str) -> Optional[Any]:
        """Get cache value."""
        if not self.use_redis:
            return None

        try:
            value = self.client.get(self._make_key(key))

            if value is None:
                return None

            return json.loads(value)
        except Exception as e:
            print(f"[RedisCache] Get error: {e}")
            return None

    def delete(self, key: str) -> bool:
        """Delete cache value."""
        if not self.use_redis:
            return False

        try:
            self.client.delete(self._make_key(key))
            return True
        except Exception:
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists."""
        if not self.use_redis:
            return False

        return bool(self.client.exists(self._make_key(key)))

    def expire(self, key: str, ttl: int) -> bool:
        """Set TTL on key."""
        if not self.use_redis:
            return False

        return bool(self.client.expire(self._make_key(key), ttl))

    def ttl(self, key: str) -> int:
        """Get TTL of key."""
        if not self.use_redis:
            return -2

        return self.client.ttl(self._make_key(key))

    def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching pattern."""
        if not self.use_redis:
            return []

        try:
            full_pattern = self._make_key(pattern)
            return [k.replace(self.prefix, "") for k in self.client.keys(full_pattern)]
        except Exception:
            return []

    def flush_all(self) -> bool:
        """Flush all keys with prefix."""
        if not self.use_redis:
            return False

        try:
            keys = self.client.keys(self._make_key("*"))
            if keys:
                self.client.delete(*keys)
            return True
        except Exception:
            return False

    def incr(self, key: str, amount: int = 1) -> int:
        """Increment counter."""
        if not self.use_redis:
            return 0

        try:
            return self.client.incr(self._make_key(key), amount)
        except Exception:
            return 0

    def zadd(self, key: str, mapping: Dict[str, float]) -> int:
        """Add to sorted set."""
        if not self.use_redis:
            return 0

        try:
            full_key = self._make_key(key)
            return self.client.zadd(full_key, mapping)
        except Exception:
            return 0

    def zrange(
        self, key: str, start: int = 0, end: int = -1, withscores: bool = False
    ) -> List:
        """Get range from sorted set."""
        if not self.use_redis:
            return []

        try:
            return self.client.zrange(
                self._make_key(key), start, end, withscores=withscores
            )
        except Exception:
            return []

    def publish(self, channel: str, message: Any) -> int:
        """Publish message to channel."""
        if not self.use_redis:
            return 0

        try:
            serialized = json.dumps(message, default=str)
            return self.client.publish(channel, serialized)
        except Exception:
            return 0

    def subscribe(self, channel: str, callback):
        """Subscribe to channel (returns pubsub object)."""
        if not self.use_redis:
            return None

        try:
            pubsub = self.client.pubsub()
            pubsub.subscribe(channel)
            return pubsub
        except Exception:
            return None

    def get_stats(self) -> Dict[str, Any]:
        """Get cache stats."""
        if not self.use_redis:
            return {"available": False}

        try:
            info = self.client.info()
            return {
                "available": True,
                "connected": True,
                "keys": len(self.keys()),
                "memory_used": info.get("used_memory_human", "unknown"),
                "clients": info.get("connected_clients", 0),
            }
        except Exception:
            return {"available": True, "connected": False}


def create_redis_cache(
    host: str = "localhost", port: int = 6379, prefix: str = "frank:context:"
) -> RedisCache:
    """Factory function to create Redis cache."""
    return RedisCache(host=host, port=port, prefix=prefix)
