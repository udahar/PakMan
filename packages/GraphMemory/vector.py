"""
GraphMemory - vector.py

Optional Qdrant + Ollama vector layer.
Silently unavailable if Qdrant or Ollama are not running — callers never need
to check; every method returns a safe empty result when offline.
"""
import hashlib
import os
from typing import Any, Dict, List, Optional


class VectorBackend:
    """
    Wraps Qdrant vector search + Ollama embeddings.

    Instantiate unconditionally — it probes the services and marks itself
    available/unavailable.  All public methods are safe to call regardless.
    """

    def __init__(
        self,
        qdrant_url: str = "http://localhost:6333",
        collection_name: str = "memory_graph",
        embed_url: str = "http://127.0.0.1:11437/api/embed",
        embed_model: str = "bge-m3:latest",
        vector_size: int = 1024,
    ):
        self.qdrant_url = qdrant_url
        self.collection_name = collection_name
        self.embed_url = embed_url
        self.embed_model = embed_model
        self.vector_size = int(os.getenv("BROWSE_EMBED_DIM", str(vector_size)))

        self.qdrant = None
        self.qdrant_available = False
        self.embed_available = False

        self._probe_qdrant()
        self._probe_ollama()

    # ── Probes ────────────────────────────────────────────────────────────────

    def _probe_qdrant(self) -> None:
        try:
            from qdrant_client import QdrantClient
            client = QdrantClient(url=self.qdrant_url, timeout=2)
            client.get_collections()          # raises if unreachable
            self.qdrant = client
            self.qdrant_available = True
            self._ensure_collection()
        except Exception:
            self.qdrant = None
            self.qdrant_available = False

    def _probe_ollama(self) -> None:
        try:
            import requests
            r = requests.get(
                self.embed_url.replace("/api/embed", "/api/tags"), timeout=2
            )
            self.embed_available = r.status_code == 200
        except Exception:
            self.embed_available = False

    def _ensure_collection(self) -> None:
        try:
            from qdrant_client.http.models import Distance, VectorParams
            if not self.qdrant.collection_exists(self.collection_name):
                self.qdrant.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size, distance=Distance.COSINE
                    ),
                )
            else:
                info = self.qdrant.get_collection(self.collection_name)
                try:
                    configured = info.config.params.vectors.size
                    if int(configured) != self.vector_size:
                        self.qdrant.delete_collection(self.collection_name)
                        self.qdrant.create_collection(
                            collection_name=self.collection_name,
                            vectors_config=VectorParams(
                                size=self.vector_size, distance=Distance.COSINE
                            ),
                        )
                except Exception:
                    pass
        except Exception:
            self.qdrant_available = False

    # ── Embeddings ────────────────────────────────────────────────────────────

    def embed(self, text: str) -> List[float]:
        """Return embedding vector. Falls back to hash if Ollama is unavailable."""
        if self.embed_available:
            try:
                import requests
                r = requests.post(
                    self.embed_url,
                    json={"model": self.embed_model, "input": text[:5000]},
                    timeout=20,
                )
                if r.status_code == 200:
                    payload = r.json() or {}
                    vec = payload.get("embeddings")
                    if isinstance(vec, list) and vec and isinstance(vec[0], list):
                        vec = vec[0]
                    else:
                        vec = payload.get("embedding") or []
                    if vec:
                        size = self.vector_size
                        if len(vec) > size:
                            return vec[:size]
                        if len(vec) < size:
                            return vec + [0.0] * (size - len(vec))
                        return vec
            except Exception:
                pass

        # Hash-based fallback (not semantically meaningful, but safe)
        vec = [0.0] * self.vector_size
        for i, ch in enumerate(text[:500]):
            vec[i % self.vector_size] += ord(ch) / 255.0
        norm = sum(v * v for v in vec) ** 0.5
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec

    # ── Upsert ────────────────────────────────────────────────────────────────

    def upsert(
        self,
        entity_id: str,
        kind: str,
        name: str,
        content: str,
        metadata: Optional[Dict] = None,
    ) -> None:
        """Index an entity in Qdrant. No-op if Qdrant is unavailable."""
        if not self.qdrant_available:
            return
        try:
            from qdrant_client.http.models import PointStruct
            vector = self.embed(content or name)
            point = PointStruct(
                id=int(hashlib.md5(entity_id.encode()).hexdigest(), 16) % (2 ** 63),
                vector=vector,
                payload={
                    "entity_id": entity_id,
                    "type": kind,
                    "name": name,
                    "content": content,
                    **(metadata or {}),
                },
            )
            self.qdrant.upsert(collection_name=self.collection_name, points=[point])
        except Exception:
            pass

    # ── Search ────────────────────────────────────────────────────────────────

    def search(
        self,
        query: str,
        top_k: int = 5,
        filter_kind: Optional[str] = None,
    ) -> List[Dict]:
        """
        Vector similarity search.  Returns [] gracefully if Qdrant is unavailable.
        """
        if not self.qdrant_available:
            return []
        try:
            query_vector = self.embed(query)
            search_filter = None
            if filter_kind:
                from qdrant_client.http.models import FieldCondition, Filter, MatchValue
                search_filter = Filter(
                    must=[FieldCondition(key="type", match=MatchValue(value=filter_kind))]
                )
            results = self.qdrant.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k,
                query_filter=search_filter,
            )
            return [
                {
                    "entity_id": r.payload.get("entity_id"),
                    "type":      r.payload.get("type"),
                    "name":      r.payload.get("name"),
                    "content":   (r.payload.get("content") or "")[:200],
                    "score":     r.score,
                    "metadata":  {
                        k: v for k, v in r.payload.items()
                        if k not in {"entity_id", "type", "name", "content"}
                    },
                }
                for r in results
            ]
        except Exception:
            return []

    # ── Status ────────────────────────────────────────────────────────────────

    def status(self) -> Dict[str, Any]:
        return {
            "qdrant": self.qdrant_available,
            "embeddings": self.embed_available,
            "collection": self.collection_name if self.qdrant_available else None,
            "vector_size": self.vector_size,
            "embed_model": self.embed_model if self.embed_available else None,
        }
