"""
SemanticCache
Prompt deduplication and response cache. Zero mandatory external deps.

Quick start:
    from SemanticCache import SemanticCache

    # Exact match (fastest)
    cache = SemanticCache(similarity="exact")

    # Fuzzy match — catches paraphrases, no embeddings needed
    cache = SemanticCache(similarity="fuzzy", threshold=0.85)

    # Embedding match — true semantic dedup (bring your own embed fn)
    cache = SemanticCache(similarity="embedding",
                          embed_fn=my_embed_fn,
                          threshold=0.92)

    # With TTL (cache entries expire after 1 hour)
    cache = SemanticCache(ttl=3600)

    # Usage
    cache.set("What is Python?", "Python is a programming language.")
    result = cache.get("What is Python?")

    # One-liner get-or-compute
    response, was_cached = cache.get_or_set("What is Python?", lambda: llm(prompt))

    # Stats
    print(cache.stats())
    # {"entries": 42, "total_hits": 180, "similarity_mode": "fuzzy", "threshold": 0.85}
"""
from .cache import SemanticCache

__version__ = "0.1.0"
__all__ = ["SemanticCache"]
