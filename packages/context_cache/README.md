# Context Cache

In-memory caching for context management.

## Usage

```python
from context_cache import ContextCache

cache = ContextCache()
cache.set("key", {"data": "value"})
result = cache.get("key")
```

## Features

- TTL support
- LRU eviction
- Memory-efficient
