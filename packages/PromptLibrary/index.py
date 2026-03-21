# Updated-On: 2026-03-08
# Updated-By: Codex
# PM-Ticket: UNTRACKED

"""
Prompt Index
Semantic search index for prompts using Qdrant
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
import json
import hashlib

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        Distance,
        VectorParams,
        PointStruct,
        Filter,
        FieldCondition,
        MatchValue,
    )

    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from .parser import Prompt
from .vetting import VetStatus


class PromptCache:
    """Redis-backed cache for prompt search and embeddings."""

    def __init__(
        self, host: str = "localhost", port: int = 6379, prefix: str = "frank:prompt:"
    ):
        self.prefix = prefix
        self.client = None
        self.use_redis = False
        self._connect(host, port)

    def _connect(self, host: str, port: int):
        if not REDIS_AVAILABLE:
            return
        try:
            self.client = redis.Redis(host=host, port=port, decode_responses=True)
            self.client.ping()
            self.use_redis = True
        except Exception:
            self.use_redis = False

    def _key(self, name: str) -> str:
        return f"{self.prefix}{name}"

    def cache_embedding(self, text: str, embedding: List[float], ttl: int = 86400):
        """Cache embedding for text."""
        if not self.use_redis:
            return
        text_hash = hashlib.sha256(text[:500].encode()).hexdigest()
        try:
            self.client.setex(self._key(f"emb:{text_hash}"), ttl, json.dumps(embedding))
        except Exception:
            pass

    def get_embedding(self, text: str) -> Optional[List[float]]:
        """Get cached embedding."""
        if not self.use_redis:
            return None
        text_hash = hashlib.sha256(text[:500].encode()).hexdigest()
        try:
            data = self.client.get(self._key(f"emb:{text_hash}"))
            return json.loads(data) if data else None
        except Exception:
            return None

    def cache_search(self, query: str, results: List[Dict], ttl: int = 300):
        """Cache search results."""
        if not self.use_redis:
            return
        query_hash = hashlib.md5(query[:200].encode()).hexdigest()
        try:
            self.client.setex(
                self._key(f"search:{query_hash}"), ttl, json.dumps(results)
            )
        except Exception:
            pass

    def get_cached_search(self, query: str) -> Optional[List[Dict]]:
        """Get cached search results."""
        if not self.use_redis:
            return None
        query_hash = hashlib.md5(query[:200].encode()).hexdigest()
        try:
            data = self.client.get(self._key(f"search:{query_hash}"))
            return json.loads(data) if data else None
        except Exception:
            return None

    def cache_prompt(self, prompt_id: str, prompt_data: Dict, ttl: int = 86400):
        """Cache parsed prompt."""
        if not self.use_redis:
            return
        try:
            self.client.setex(
                self._key(f"prompt:{prompt_id}"), ttl, json.dumps(prompt_data)
            )
        except Exception:
            pass

    def get_cached_prompt(self, prompt_id: str) -> Optional[Dict]:
        """Get cached prompt."""
        if not self.use_redis:
            return None
        try:
            data = self.client.get(self._key(f"prompt:{prompt_id}"))
            return json.loads(data) if data else None
        except Exception:
            return None


@dataclass
class IndexedPrompt:
    """A prompt in the index."""

    prompt_id: str
    act: str
    prompt: str
    for_devs: bool
    tags: List[str]
    vetted: bool
    score: float = 0.0


class PromptIndex:
    """
    Semantic search index for prompts using Qdrant.

    If Qdrant is not available, falls back to simple text search.
    """

    COLLECTION_NAME = "frank_prompts"

    def __init__(
        self,
        qdrant_url: str = "http://localhost:6333",
        embedding_model: str = "bge-m3:latest",
        ollama_url: str = "http://127.0.0.1:11434",
        use_cache: bool = True,
        redis_host: str = "localhost",
        redis_port: int = 6379,
    ):
        self.qdrant_url = qdrant_url
        self.embedding_model = embedding_model
        self.ollama_url = ollama_url

        self.client = None
        self.use_qdrant = False
        self.prompts: Dict[str, Prompt] = {}
        self.simple_index: Dict[str, List[str]] = {}

        self.cache = None
        if use_cache:
            self.cache = PromptCache(host=redis_host, port=redis_port)

        self._init_qdrant()

    def _init_qdrant(self):
        """Initialize Qdrant connection."""
        if not QDRANT_AVAILABLE:
            print("[PromptIndex] Qdrant not available, using simple search")
            return

        try:
            self.client = QdrantClient(url=self.qdrant_url)
            self._ensure_collection()
            self.use_qdrant = True
            print("[PromptIndex] Qdrant enabled for semantic search")
        except Exception as e:
            print(f"[PromptIndex] Qdrant unavailable: {e}, using simple search")
            self.use_qdrant = False

    def _ensure_collection(self):
        """Ensure the prompts collection exists."""
        collections = self.client.get_collections().collections
        if not any(c.name == self.COLLECTION_NAME for c in collections):
            self.client.create_collection(
                collection_name=self.COLLECTION_NAME,
                vectors_config=VectorParams(size=1024, distance=CosineDistance),
            )

    def add_prompt(self, prompt: Prompt, prompt_id: Optional[str] = None) -> str:
        """Add a prompt to the index."""
        if prompt_id is None:
            prompt_id = self._generate_id(prompt.act)

        self.prompts[prompt_id] = prompt

        for tag in prompt.tags:
            if tag not in self.simple_index:
                self.simple_index[tag] = []
            self.simple_index[tag].append(prompt_id)

        words = (prompt.act + " " + prompt.prompt).lower().split()
        for word in set(words):
            if word not in self.simple_index:
                self.simple_index[word] = []
            self.simple_index[word].append(prompt_id)

        if self.use_qdrant:
            self._add_to_qdrant(prompt_id, prompt)

        return prompt_id

    def add_prompts(self, prompts: List[Prompt]) -> int:
        """Add multiple prompts to the index."""
        count = 0
        for prompt in prompts:
            try:
                self.add_prompt(prompt)
                count += 1
            except Exception:
                continue
        return count

    def _generate_id(self, act: str) -> str:
        """Generate a unique ID for a prompt."""
        import hashlib

        return hashlib.md5(act.encode()).hexdigest()[:12]

    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using Ollama."""
        if self.cache and self.cache.use_redis:
            cached = self.cache.get_embedding(text)
            if cached:
                return cached

        try:
            import requests

            response = requests.post(
                f"{self.ollama_url}/api/embeddings",
                json={"model": self.embedding_model, "prompt": text},
                timeout=30,
            )
            embedding = response.json()["embedding"]

            if self.cache and self.cache.use_redis:
                self.cache.cache_embedding(text, embedding)

            return embedding
        except Exception:
            return [0.0] * 1024

    def _add_to_qdrant(self, prompt_id: str, prompt: Prompt):
        """Add prompt to Qdrant."""
        text = f"{prompt.act}: {prompt.prompt}"
        embedding = self._get_embedding(text)

        self.client.upsert(
            collection_name=self.COLLECTION_NAME,
            points=[
                PointStruct(
                    id=prompt_id,
                    vector=embedding,
                    payload={
                        "act": prompt.act,
                        "prompt": prompt.prompt,
                        "for_devs": prompt.for_devs,
                        "tags": prompt.tags,
                        "vetting_status": "approved" if prompt.vetted else "pending",
                    },
                )
            ],
        )

    def search(
        self,
        query: str,
        limit: int = 5,
        tags: Optional[List[str]] = None,
        devs_only: bool = False,
    ) -> List[IndexedPrompt]:
        """
        Search for prompts matching query.

        Args:
            query: Search query
            limit: Max results
            tags: Filter by tags
            devs_only: Only developer prompts

        Returns:
            List of indexed prompts with scores
        """
        if self.cache and self.cache.use_redis:
            cached = self.cache.get_cached_search(query)
            if cached:
                return [
                    IndexedPrompt(
                        prompt_id=r["prompt_id"],
                        act=r["act"],
                        prompt=r["prompt"],
                        for_devs=r["for_devs"],
                        tags=r["tags"],
                        vetted=r["vetted"],
                        score=r["score"],
                    )
                    for r in cached[:limit]
                ]

        if self.use_qdrant:
            results = self._search_qdrant(query, limit, tags, devs_only)
        else:
            results = self._search_simple(query, limit, tags, devs_only)

        if self.cache and self.cache.use_redis:
            self.cache.cache_search(
                query,
                [
                    {
                        "prompt_id": r.prompt_id,
                        "act": r.act,
                        "prompt": r.prompt,
                        "for_devs": r.for_devs,
                        "tags": r.tags,
                        "vetted": r.vetted,
                        "score": r.score,
                    }
                    for r in results
                ],
            )

        return results

    def _search_qdrant(
        self, query: str, limit: int, tags: Optional[List[str]], devs_only: bool
    ) -> List[IndexedPrompt]:
        """Search using Qdrant."""
        embedding = self._get_embedding(query)

        filters = []
        if tags:
            filters.append(
                Filter(
                    must=[
                        FieldCondition(key="tags", match=MatchValue(value=tag))
                        for tag in tags
                    ]
                )
            )
        if devs_only:
            filters.append(
                Filter(
                    must=[FieldCondition(key="for_devs", match=MatchValue(value=True))]
                )
            )

        try:
            results = self.client.search(
                collection_name=self.COLLECTION_NAME,
                query_vector=embedding,
                limit=limit,
                query_filter=Filter(must=filters) if filters else None,
            )

            return [
                IndexedPrompt(
                    prompt_id=r.id,
                    act=r.payload["act"],
                    prompt=r.payload["prompt"],
                    for_devs=r.payload.get("for_devs", False),
                    tags=r.payload.get("tags", []),
                    vetted=r.payload.get("vetting_status") == "approved",
                    score=r.score,
                )
                for r in results
            ]
        except Exception:
            return self._search_simple(query, limit, tags, devs_only)

    def _search_simple(
        self, query: str, limit: int, tags: Optional[List[str]], devs_only: bool
    ) -> List[IndexedPrompt]:
        """Simple text-based search."""
        query_words = query.lower().split()

        results = []
        for prompt_id, prompt in self.prompts.items():
            if devs_only and not prompt.for_devs:
                continue

            if tags and not any(t in prompt.tags for t in tags):
                continue

            text = (prompt.act + " " + prompt.prompt).lower()
            score = sum(1 for w in query_words if w in text) / len(query_words)

            if score > 0:
                results.append(
                    IndexedPrompt(
                        prompt_id=prompt_id,
                        act=prompt.act,
                        prompt=prompt.prompt,
                        for_devs=prompt.for_devs,
                        tags=prompt.tags,
                        vetted=prompt.vetted,
                        score=score,
                    )
                )

        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]

    def get_prompt(self, prompt_id: str) -> Optional[Prompt]:
        """Get a prompt by ID."""
        return self.prompts.get(prompt_id)

    def get_all_prompts(self) -> List[Prompt]:
        """Get all prompts."""
        return list(self.prompts.values())

    def get_vetted_prompts(self) -> List[Prompt]:
        """Get only vetted prompts."""
        return [p for p in self.prompts.values() if p.vetted]

    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        return {
            "total_prompts": len(self.prompts),
            "vetting": {
                "approved": len([p for p in self.prompts.values() if p.vetted]),
                "pending": len([p for p in self.prompts.values() if not p.vetted]),
            },
            "dev_prompts": len([p for p in self.prompts.values() if p.for_devs]),
            "search_backend": "qdrant" if self.use_qdrant else "simple",
            "indexed_tags": len(self.simple_index),
        }


def create_prompt_index(
    qdrant_url: str = "http://localhost:6333", embedding_model: str = "bge-m3:latest"
) -> PromptIndex:
    """Factory function to create prompt index."""
    return PromptIndex(qdrant_url=qdrant_url, embedding_model=embedding_model)


class CosineDistance:
    """Placeholder for cosine distance."""

    pass
