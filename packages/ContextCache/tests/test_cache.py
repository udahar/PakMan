"""Tests for ContextCache package."""

import pytest
from datetime import datetime, timedelta
from context_cache import ContextCache, CacheEntry


class TestCacheEntry:
    """Tests for CacheEntry dataclass."""
    
    def test_create_entry(self):
        """Test creating a cache entry."""
        entry = CacheEntry(
            entry_id="test123",
            messages=[{"role": "user", "content": "Hello"}],
            metadata={"user_id": "123"},
            created_at=datetime.now(),
            last_used=datetime.now(),
        )
        
        assert entry.entry_id == "test123"
        assert len(entry.messages) == 1
        assert entry.use_count == 0
    
    def test_entry_to_dict(self):
        """Test converting entry to dict."""
        entry = CacheEntry(
            entry_id="test123",
            messages=[{"role": "user", "content": "Hello"}],
            metadata={},
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            last_used=datetime(2024, 1, 1, 12, 0, 0),
        )
        
        data = entry.to_dict()
        
        assert data["entry_id"] == "test123"
        assert data["messages"] == [{"role": "user", "content": "Hello"}]
        assert data["use_count"] == 0


class TestContextCache:
    """Tests for ContextCache class."""
    
    def test_init_default(self):
        """Test initialization with defaults."""
        cache = ContextCache()
        
        assert cache.max_size == 100
        assert cache.ttl_seconds == 3600
        assert len(cache.cache) == 0
    
    def test_init_custom(self):
        """Test initialization with custom values."""
        cache = ContextCache(max_size=50, ttl_seconds=1800)
        
        assert cache.max_size == 50
        assert cache.ttl_seconds == 1800
    
    def test_store_single_message(self):
        """Test storing a single message."""
        cache = ContextCache()
        messages = [{"role": "user", "content": "Hello"}]
        
        entry_id = cache.store(messages)
        
        assert entry_id is not None
        assert len(entry_id) == 12
        assert len(cache.cache) == 1
    
    def test_store_empty_messages_raises(self):
        """Test storing empty messages raises error."""
        cache = ContextCache()
        
        with pytest.raises(ValueError, match="messages cannot be empty"):
            cache.store([])
    
    def test_get_existing_entry(self):
        """Test retrieving an existing entry."""
        cache = ContextCache()
        messages = [{"role": "user", "content": "Hello"}]
        
        entry_id = cache.store(messages)
        retrieved = cache.get(entry_id)
        
        assert retrieved == messages
    
    def test_get_nonexistent_entry(self):
        """Test retrieving non-existent entry returns None."""
        cache = ContextCache()
        
        result = cache.get("nonexistent")
        
        assert result is None
    
    def test_get_after_expiry(self):
        """Test expired entries are not returned."""
        cache = ContextCache(ttl_seconds=0)
        messages = [{"role": "user", "content": "Hello"}]
        
        entry_id = cache.store(messages)
        retrieved = cache.get(entry_id)
        
        assert retrieved is None
    
    def test_search_basic(self):
        """Test basic search functionality."""
        cache = ContextCache()
        
        cache.store([{"role": "user", "content": "Tell me about Python"}])
        cache.store([{"role": "user", "content": "Tell me about JavaScript"}])
        cache.store([{"role": "user", "content": "What is Rust?"}])
        
        results = cache.search("Python")
        
        assert len(results) >= 1
        assert any("Python" in r.get("match_content", "") for r in results)
    
    def test_search_empty_query(self):
        """Test empty search query returns empty."""
        cache = ContextCache()
        cache.store([{"role": "user", "content": "Hello"}])
        
        results = cache.search("")
        
        assert results == []
    
    def test_remove_existing(self):
        """Test removing existing entry."""
        cache = ContextCache()
        messages = [{"role": "user", "content": "Hello"}]
        
        entry_id = cache.store(messages)
        result = cache.remove(entry_id)
        
        assert result is True
        assert entry_id not in cache.cache
    
    def test_remove_nonexistent(self):
        """Test removing non-existent entry."""
        cache = ContextCache()
        
        result = cache.remove("nonexistent")
        
        assert result is False
    
    def test_clear(self):
        """Test clearing all entries."""
        cache = ContextCache()
        cache.store([{"role": "user", "content": "Hello"}])
        cache.store([{"role": "user", "content": "World"}])
        
        cache.clear()
        
        assert len(cache.cache) == 0
        assert len(cache.access_order) == 0
    
    def test_eviction_when_full(self):
        """Test LRU eviction when cache is full."""
        cache = ContextCache(max_size=2)
        
        id1 = cache.store([{"role": "user", "content": "First"}])
        id2 = cache.store([{"role": "user", "content": "Second"}])
        id3 = cache.store([{"role": "user", "content": "Third"}])
        
        assert len(cache.cache) == 2
        assert id1 not in cache.cache
        assert id2 in cache.cache
        assert id3 in cache.cache
    
    def test_stats(self):
        """Test getting cache statistics."""
        cache = ContextCache()
        
        cache.store([{"role": "user", "content": "Hello"}])
        cache.store([{"role": "user", "content": "World"}])
        
        cache.get(list(cache.cache.keys())[0])
        
        stats = cache.get_stats()
        
        assert stats["size"] == 2
        assert stats["max_size"] == 100
        assert stats["total_uses"] == 1
        assert stats["avg_uses"] == 0.5
    
    def test_cleanup_expired(self):
        """Test cleaning up expired entries."""
        cache = ContextCache(ttl_seconds=0)
        
        cache.store([{"role": "user", "content": "First"}])
        cache.store([{"role": "user", "content": "Second"}])
        
        removed = cache.cleanup_expired()
        
        assert removed == 2
        assert len(cache.cache) == 0
    
    def test_export_all(self):
        """Test exporting all entries."""
        cache = ContextCache()
        
        cache.store([{"role": "user", "content": "Hello"}])
        cache.store([{"role": "user", "content": "World"}])
        
        exported = cache.export_all()
        
        assert len(exported) == 2
        assert all("entry_id" in e for e in exported)


class TestGlobalFunctions:
    """Tests for module-level convenience functions."""
    
    def test_store_and_get(self):
        """Test global store and get functions."""
        from context_cache import store, get, clear
        import uuid
        
        test_id = f"test_{uuid.uuid4().hex[:8]}"
        
        cache = ContextCache()
        entry_id = cache.store([{"role": "user", "content": "Test"}])
        
        result = cache.get(entry_id)
        
        assert result is not None
        assert result[0]["content"] == "Test"
