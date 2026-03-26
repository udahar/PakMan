"""
GraphMemory
Unified knowledge graph with automatic backend detection.

Tier 1 — always available:
    SQLite persistence, heuristic entity extraction, BFS path queries.

Tier 2 — if Qdrant is running:
    Vector similarity search, hybrid vector+graph queries.

Tier 3 — if Ollama is running:
    Real semantic embeddings (bge-m3 or configurable model).
    Falls back to hash-based vectors when unavailable.

The same API works regardless of which backends are live.
Call `gm.backends()` to see what's active.

─── New API (portable, zero-dep) ───────────────────────────────────────────

    gm = GraphMemory()
    gm.ingest("Richard fixed the auth bug in PromptForge last Tuesday.")
    gm.neighbors("PromptForge")
    gm.path("Richard", "auth bug")
    gm.search("auth")

─── Classic API (MemoryGraph-compatible, used by BrowserV1) ────────────────

    gm = GraphMemory()
    eid = gm.add_entity(entity_id="e1", type="topic", name="auth", content="...")
    gm.add_relationship("e1", "e2", "related_to")
    gm.similar_to("authentication", top_k=5)
    gm.hybrid_query("login bug", relationships=["affects", "calls"])
    gm.get_stats()

─── Introspection ───────────────────────────────────────────────────────────

    gm.backends()
    # {"sqlite": True, "qdrant": True, "embeddings": False, "mode": "full-lite"}

    gm.mode          # "full" | "lite"
"""
import hashlib
import os
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set

from .extractor import extract_heuristic, extract_with_llm
from .models import Edge, Node
from .store import GraphStore
from .vector import VectorBackend


class GraphMemory:
    """
    Unified knowledge graph — SQLite core, optional Qdrant vector layer.

    Args:
        db_path:          SQLite database path (default: graph_memory.db).
        qdrant_url:       Qdrant base URL (default: http://localhost:6333).
        collection_name:  Qdrant collection (default: memory_graph).
        embed_url:        Ollama embed endpoint (default: local port 11437).
        embed_model:      Embedding model name (default: bge-m3:latest).
        vector_size:      Embedding dimensions (default: 1024).
        llm:              Optional fn(prompt)->str for LLM entity extraction.
        auto_vector:      Probe for Qdrant/Ollama on init (default: True).
    """

    def __init__(
        self,
        db_path: str = "graph_memory.db",
        qdrant_url: str = "http://localhost:6333",
        collection_name: str = "memory_graph",
        embed_url: str = "http://127.0.0.1:11437/api/embed",
        embed_model: str = "bge-m3:latest",
        vector_size: int = 1024,
        llm: Optional[Callable] = None,
        auto_vector: bool = True,
    ):
        # Read env overrides so BrowserV1's existing env vars just work
        self._db_path = db_path
        self.store = GraphStore(db_path)
        self.llm = llm

        # Optional vector backend — probes services, never raises
        if auto_vector:
            self.vector = VectorBackend(
                qdrant_url=os.getenv("BROWSE_QDRANT_URL", qdrant_url),
                collection_name=collection_name,
                embed_url=os.getenv("BROWSE_OLLAMA_EMBED_URL", embed_url),
                embed_model=os.getenv("BROWSE_EMBED_MODEL", embed_model),
                vector_size=int(os.getenv("BROWSE_EMBED_DIM", str(vector_size))),
            )
        else:
            self.vector = VectorBackend.__new__(VectorBackend)
            self.vector.qdrant_available = False
            self.vector.embed_available = False
            self.vector.qdrant = None
            self.vector.collection_name = collection_name
            self.vector.vector_size = vector_size
            self.vector.embed_model = embed_model

    # ── Introspection ─────────────────────────────────────────────────────────

    @property
    def mode(self) -> str:
        """'full' if Qdrant is live, 'lite' otherwise."""
        return "full" if self.vector.qdrant_available else "lite"

    def backends(self) -> Dict[str, Any]:
        """Return a dict describing which backends are currently active."""
        vs = self.vector.status()
        return {
            "sqlite":     True,
            "qdrant":     vs["qdrant"],
            "embeddings": vs["embeddings"],
            "mode":       self.mode,
            "collection": vs["collection"],
            "embed_model": vs["embed_model"],
        }

    # ══════════════════════════════════════════════════════════════════════════
    # NEW API  (portable, zero external deps)
    # ══════════════════════════════════════════════════════════════════════════

    def ingest(self, text: str) -> Dict[str, int]:
        """
        Parse text, extract entities/relationships, persist them.

        Returns {"nodes_added": int, "edges_added": int}
        """
        if self.llm:
            nodes, edges = extract_with_llm(text, self.llm)
        else:
            nodes, edges = extract_heuristic(text)
        self.store.bulk_upsert(nodes, edges)
        # Also index new nodes in Qdrant if available
        for n in nodes:
            self.vector.upsert(n.id, n.kind, n.label, n.label, n.properties)
        return {"nodes_added": len(nodes), "edges_added": len(edges)}

    def add_node(self, label: str, kind: str = "entity", **props) -> Node:
        """Manually add a node by label."""
        n = Node(label=label, kind=kind, properties=props)
        self.store.upsert_node(n)
        self.vector.upsert(n.id, kind, label, label, props)
        return n

    def add_edge(
        self, src_label: str, rel: str, dst_label: str, context: str = ""
    ) -> Edge:
        """Manually add a relationship by label."""
        src = self.store.find_node(src_label) or self.add_node(src_label).to_dict()
        dst = self.store.find_node(dst_label) or self.add_node(dst_label).to_dict()
        e = Edge(src_id=src["id"], rel=rel, dst_id=dst["id"], context=context)
        self.store.upsert_edge(e)
        return e

    def neighbors(self, label: str) -> List[Dict]:
        """Return all entities connected to label (1-hop)."""
        return self.store.neighbors(label)

    def path(
        self, src: str, dst: str, max_hops: int = 3
    ) -> List[List[str]]:
        """BFS paths between two entities."""
        return self.store.path(src, dst, max_hops)

    def search(self, query: str, kind: str = None) -> List[Dict]:
        """Search entities by label substring."""
        return self.store.search_nodes(query, kind=kind)

    def stats(self) -> Dict:
        """Graph statistics."""
        base = self.store.stats()
        base["backends"] = self.backends()
        return base

    # ══════════════════════════════════════════════════════════════════════════
    # CLASSIC API  (MemoryGraph-compatible — used by BrowserV1 / bootstrap)
    # ══════════════════════════════════════════════════════════════════════════

    def add_entity(
        self,
        entity_id: Optional[str] = None,
        type: str = "generic",
        name: str = "",
        content: str = "",
        metadata: Optional[Dict] = None,
    ) -> str:
        """
        Add entity — MemoryGraph-compatible signature.

        Stores in SQLite always; also indexes in Qdrant when available.
        Returns the entity_id.
        """
        if not entity_id:
            entity_id = hashlib.md5(
                f"{type}:{name}:{content}".encode()
            ).hexdigest()[:16]

        label = name or entity_id
        props = {"_type": type, "_content": content, **(metadata or {})}

        # SQLite: upsert as a node (id-keyed so we keep the caller's id)
        node = Node(
            id=entity_id,
            label=label,
            kind=type,
            properties=props,
            created_at=datetime.utcnow().isoformat(),
        )
        self.store.upsert_node(node)

        # Qdrant: index with full content for vector search
        self.vector.upsert(entity_id, type, name, content or name, metadata)

        return entity_id

    def add_relationship(
        self,
        from_id: str,
        to_id: str,
        rel_type: str,
        metadata: Optional[Dict] = None,
    ) -> None:
        """
        Add relationship between two entity IDs — MemoryGraph-compatible.
        """
        edge_id = hashlib.md5(
            f"{from_id}:{rel_type}:{to_id}".encode()
        ).hexdigest()[:16]
        edge = Edge(
            id=edge_id,
            src_id=from_id,
            rel=rel_type,
            dst_id=to_id,
            context=str(metadata or ""),
        )
        self.store.upsert_edge(edge)

    def get_entity(self, entity_id: str) -> Optional[Dict]:
        """Retrieve entity by ID."""
        with self.store._conn() as conn:
            row = conn.execute(
                "SELECT * FROM nodes WHERE id=?", (entity_id,)
            ).fetchone()
            return dict(row) if row else None

    def get_relationships(
        self,
        entity_id: str,
        rel_types: Optional[List[str]] = None,
        direction: str = "both",
    ) -> List[Dict]:
        """Get relationships for an entity ID."""
        with self.store._conn() as conn:
            results = []
            if direction in ("out", "both"):
                rows = conn.execute(
                    "SELECT * FROM edges WHERE src_id=?", (entity_id,)
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    if not rel_types or d["rel"] in rel_types:
                        results.append({
                            "from": d["src_id"], "to": d["dst_id"],
                            "type": d["rel"], "context": d.get("context"),
                        })
            if direction in ("in", "both"):
                rows = conn.execute(
                    "SELECT * FROM edges WHERE dst_id=?", (entity_id,)
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    if not rel_types or d["rel"] in rel_types:
                        results.append({
                            "from": d["src_id"], "to": d["dst_id"],
                            "type": d["rel"], "context": d.get("context"),
                        })
            return results

    def get_stats(self) -> Dict:
        """Alias for stats() — MemoryGraph-compatible."""
        return self.stats()

    # ── Vector methods (Tier 2 — Qdrant required) ─────────────────────────────

    def similar_to(
        self,
        query: str,
        top_k: int = 5,
        filter_type: Optional[str] = None,
    ) -> List[Dict]:
        """
        Vector similarity search.

        Returns results when Qdrant is available.
        Returns [] gracefully when it isn't — no exception raised.
        """
        return self.vector.search(query, top_k=top_k, filter_kind=filter_type)

    def hybrid_query(
        self,
        text: str,
        relationships: Optional[List[str]] = None,
        max_depth: int = 3,
        top_k: int = 5,
    ) -> Dict:
        """
        Combined vector + graph search.

        Vector part requires Qdrant (returns empty similar[] when unavailable).
        Graph expansion always works via SQLite.
        """
        similar = self.similar_to(text, top_k=top_k)

        expanded = []
        if relationships and similar:
            expanded_ids: Set[str] = set()
            for hit in similar[:5]:
                eid = hit.get("entity_id")
                if eid:
                    expanded_ids.update(
                        self._graph_expand(eid, relationships, max_depth)
                    )
            seen = {h["entity_id"] for h in similar if h.get("entity_id")}
            for eid in expanded_ids - seen:
                entity = self.get_entity(eid)
                if entity:
                    expanded.append(entity)

        return {
            "similar":       similar,
            "expanded":      expanded,
            "query":         text,
            "total_results": len(similar) + len(expanded),
            "mode":          self.mode,
        }

    def _graph_expand(
        self,
        entity_id: str,
        rel_types: List[str],
        depth: int,
        visited: Optional[Set[str]] = None,
    ) -> Set[str]:
        if visited is None:
            visited = set()
        if depth <= 0 or entity_id in visited:
            return {entity_id}
        visited.add(entity_id)
        result = {entity_id}
        for rel in self.get_relationships(entity_id, rel_types, direction="both"):
            other = rel["to"] if rel["from"] == entity_id else rel["from"]
            if other not in visited:
                result.update(
                    self._graph_expand(other, rel_types, depth - 1, visited)
                )
        return result


# ── Module-level convenience ──────────────────────────────────────────────────

_instance: Optional[GraphMemory] = None


def get_graph_memory(**kwargs) -> GraphMemory:
    """Return a shared module-level GraphMemory instance."""
    global _instance
    if _instance is None:
        _instance = GraphMemory(**kwargs)
    return _instance


__version__ = "0.2.0"
__all__ = [
    "GraphMemory",
    "GraphStore",
    "Node",
    "Edge",
    "VectorBackend",
    "get_graph_memory",
]
