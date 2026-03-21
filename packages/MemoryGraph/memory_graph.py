#!/usr/bin/env python3
"""
Memory Graph - Knowledge Graph + Vector Hybrid

Combines:
- Vector search (Qdrant) for semantic similarity
- Knowledge graph (NetworkX) for relationships
- Hybrid queries for both

Usage:
    from memory_graph import MemoryGraph

    mg = MemoryGraph()

    # Add entities
    mg.add_entity("file1", "file", "auth.py", "Authentication module")
    mg.add_relationship("file1", "func1", "contains")

    # Hybrid query
    results = mg.hybrid_query("login vulnerability", relationships=["calls", "imports"])
"""

import networkx as nx
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from typing import Optional, List, Dict, Any, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import json
import asyncio
import os


@dataclass
class GraphEntity:
    """Entity in the knowledge graph"""

    id: str
    type: str  # file, function, class, bug, api, module, etc.
    name: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "content": self.content,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "GraphEntity":
        return cls(
            id=data["id"],
            type=data["type"],
            name=data["name"],
            content=data["content"],
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"])
            if data.get("created_at")
            else None,
        )


class MemoryGraph:
    """
    Hybrid memory system combining vector search + knowledge graph.

    Enables queries like:
    - "Find bugs related to authentication" (vector)
    - "What files call this function?" (graph)
    - "Find authentication bugs that affect login files" (hybrid)
    """

    def __init__(
        self,
        qdrant_url: str = "http://localhost:6333",
        collection_name: str = "memory_graph",
        vector_size: int = 1024,
    ):
        self.graph = nx.MultiDiGraph()
        self.qdrant = QdrantClient(url=qdrant_url)
        self.collection_name = collection_name
        self.vector_size = int(os.getenv("BROWSE_EMBED_DIM", str(vector_size)))
        self.embed_url = os.getenv(
            "BROWSE_OLLAMA_EMBED_URL", "http://127.0.0.1:11437/api/embed"
        )
        self.embed_model = os.getenv("BROWSE_EMBED_MODEL", "bge-m3:latest")

        # Entity cache
        self.entities: Dict[str, GraphEntity] = {}

        # Initialize Qdrant collection
        self._init_qdrant()

    def _init_qdrant(self):
        """Initialize Qdrant collection"""
        try:
            if not self.qdrant.collection_exists(self.collection_name):
                self.qdrant.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size, distance=Distance.COSINE
                    ),
                )
                print(f"[OK] Created Qdrant collection: {self.collection_name}")
            else:
                info = self.qdrant.get_collection(self.collection_name)
                configured_size = None
                try:
                    configured_size = info.config.params.vectors.size
                except Exception:
                    configured_size = None
                if configured_size and int(configured_size) != int(self.vector_size):
                    self.qdrant.delete_collection(self.collection_name)
                    self.qdrant.create_collection(
                        collection_name=self.collection_name,
                        vectors_config=VectorParams(
                            size=self.vector_size, distance=Distance.COSINE
                        ),
                    )
                    print(
                        f"[OK] Recreated Qdrant collection: {self.collection_name} ({configured_size} -> {self.vector_size})"
                    )
                else:
                    print(f"[OK] Using existing collection: {self.collection_name}")
        except Exception as e:
            print(f"[WARN] Qdrant init warning: {e}")

    def _generate_id(self, content: str) -> str:
        """Generate unique ID from content"""
        return hashlib.md5(content.encode()).hexdigest()[:16]

    def _get_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text using Ollama.

        Uses the local Alfred/Ollama embedding endpoint first, then a hash fallback.
        It intentionally avoids remote Hugging Face downloads.
        """
        try:
            import requests

            response = requests.post(
                self.embed_url,
                json={"model": self.embed_model, "input": text[:5000]},
                timeout=20,
            )
            if response.status_code == 200:
                payload = response.json() or {}
                embedding = payload.get("embeddings")
                if isinstance(embedding, list) and embedding and isinstance(
                    embedding[0], list
                ):
                    vector = embedding[0]
                else:
                    vector = payload.get("embedding") or []
                if vector:
                    if len(vector) > self.vector_size:
                        return vector[: self.vector_size]
                    if len(vector) < self.vector_size:
                        return vector + [0.0] * (self.vector_size - len(vector))
                    return vector
        except Exception as e:
            pass

        # Fallback to hash-based placeholder (not semantically accurate)
        embedding = [0.0] * self.vector_size
        for i, char in enumerate(text[:500]):
            embedding[i % self.vector_size] += ord(char) / 255.0

        norm = sum(v * v for v in embedding) ** 0.5
        if norm > 0:
            embedding = [v / norm for v in embedding]

        return embedding

    # === Entity Management ===

    def add_entity(
        self,
        entity_id: Optional[str] = None,
        type: str = "generic",
        name: str = "",
        content: str = "",
        metadata: Optional[Dict] = None,
    ) -> str:
        """
        Add entity to both graph and vector index.

        Args:
            entity_id: Optional ID (auto-generated if not provided)
            type: Entity type (file, function, class, bug, etc.)
            name: Entity name
            content: Content for embedding
            metadata: Additional metadata

        Returns:
            Entity ID
        """
        if not entity_id:
            entity_id = self._generate_id(f"{type}:{name}:{content}")

        # Create entity
        entity = GraphEntity(
            id=entity_id, type=type, name=name, content=content, metadata=metadata or {}
        )

        # Add to graph
        self.graph.add_node(
            entity_id,
            type=entity.type,
            name=entity.name,
            content=entity.content,
            **entity.metadata,
        )

        # Add to Qdrant
        embedding = self._get_embedding(entity.content)
        entity.embedding = embedding

        point = PointStruct(
            id=hash(entity_id) % (2**63),  # Qdrant needs int ID
            vector=embedding,
            payload={
                "entity_id": entity_id,
                "type": entity.type,
                "name": entity.name,
                "content": entity.content,
                **entity.metadata,
            },
        )

        try:
            self.qdrant.upsert(collection_name=self.collection_name, points=[point])
        except Exception as e:
            print(f"⚠️  Qdrant upsert warning: {e}")

        # Cache
        self.entities[entity_id] = entity

        return entity_id

    def get_entity(self, entity_id: str) -> Optional[GraphEntity]:
        """Get entity by ID"""
        if entity_id in self.entities:
            return self.entities[entity_id]

        if self.graph.has_node(entity_id):
            data = self.graph.nodes[entity_id]
            return GraphEntity(
                id=entity_id,
                type=data.get("type", "unknown"),
                name=data.get("name", ""),
                content=data.get("content", ""),
                metadata={
                    k: v
                    for k, v in data.items()
                    if k not in ["type", "name", "content"]
                },
            )

        return None

    def remove_entity(self, entity_id: str):
        """Remove entity from graph and vector index"""
        if entity_id in self.entities:
            del self.entities[entity_id]

        if self.graph.has_node(entity_id):
            self.graph.remove_node(entity_id)

        # Remove from Qdrant (would need to implement)

    # === Relationship Management ===

    def add_relationship(
        self, from_id: str, to_id: str, rel_type: str, metadata: Optional[Dict] = None
    ):
        """
        Add relationship between entities.

        Args:
            from_id: Source entity ID
            to_id: Target entity ID
            rel_type: Relationship type (calls, imports, contains, affects, etc.)
            metadata: Optional relationship metadata
        """
        self.graph.add_edge(from_id, to_id, relation=rel_type, **(metadata or {}))

    def get_relationships(
        self,
        entity_id: str,
        rel_types: Optional[List[str]] = None,
        direction: str = "both",
    ) -> List[Dict]:
        """
        Get relationships for an entity.

        Args:
            entity_id: Entity ID
            rel_types: Filter by relationship types
            direction: "out", "in", or "both"

        Returns:
            List of relationship dicts
        """
        results = []

        if direction in ["out", "both"]:
            for _, target, data in self.graph.out_edges(entity_id, data=True):
                if not rel_types or data.get("relation") in rel_types:
                    results.append(
                        {
                            "from": entity_id,
                            "to": target,
                            "type": data.get("relation"),
                            **{k: v for k, v in data.items() if k != "relation"},
                        }
                    )

        if direction in ["in", "both"]:
            for source, _, data in self.graph.in_edges(entity_id, data=True):
                if not rel_types or data.get("relation") in rel_types:
                    results.append(
                        {
                            "from": source,
                            "to": entity_id,
                            "type": data.get("relation"),
                            **{k: v for k, v in data.items() if k != "relation"},
                        }
                    )

        return results

    # === Query Methods ===

    def similar_to(
        self, query: str, top_k: int = 5, filter_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Vector similarity search.

        Args:
            query: Search query
            top_k: Number of results
            filter_type: Filter by entity type

        Returns:
            List of matching entities with scores
        """
        # Generate query embedding
        query_embedding = self._get_embedding(query)

        # Search Qdrant
        try:
            search_filter = None
            if filter_type:
                from qdrant_client.http.models import Filter, FieldCondition, MatchValue

                search_filter = Filter(
                    must=[
                        FieldCondition(key="type", match=MatchValue(value=filter_type))
                    ]
                )

            results = self.qdrant.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=top_k,
                query_filter=search_filter,
            )

            return [
                {
                    "entity_id": r.payload.get("entity_id"),
                    "type": r.payload.get("type"),
                    "name": r.payload.get("name"),
                    "content": r.payload.get("content", "")[:200],
                    "score": r.score,
                    "metadata": {
                        k: v
                        for k, v in r.payload.items()
                        if k not in ["entity_id", "type", "name", "content"]
                    },
                }
                for r in results
            ]
        except Exception as e:
            print(f"⚠️  Qdrant search warning: {e}")
            return []

    def query(self, pattern: str) -> List[Dict]:
        """
        Simple graph pattern query.

        Patterns:
        - "calls" - Find all calls relationships
        - "imports" - Find all imports
        - "contains" - Find containment

        Args:
            pattern: Relationship pattern

        Returns:
            List of matching relationships
        """
        results = []
        pattern_lower = pattern.lower()

        for u, v, data in self.graph.edges(data=True):
            rel_type = data.get("relation", "")
            if pattern_lower in rel_type.lower():
                results.append(
                    {
                        "from": u,
                        "to": v,
                        "type": rel_type,
                        "from_name": self.graph.nodes[u].get("name", u),
                        "to_name": self.graph.nodes[v].get("name", v),
                    }
                )

        return results

    def hybrid_query(
        self,
        text: str,
        relationships: Optional[List[str]] = None,
        max_depth: int = 3,
        top_k: int = 5,
    ) -> Dict:
        """
        Combined vector + graph search.

        Args:
            text: Search query
            relationships: Relationship types to expand
            max_depth: Max graph expansion depth
            top_k: Initial vector results

        Returns:
            Dict with similar and expanded results
        """
        # 1. Vector search
        similar = self.similar_to(text, top_k=top_k)

        # 2. Expand via graph
        expanded = []
        if relationships:
            expanded_set: Set[str] = set()

            for entity in similar[:5]:
                entity_id = entity.get("entity_id")
                if entity_id:
                    expanded_set.update(
                        self._expand(entity_id, relationships, max_depth)
                    )

            # Get expanded entity details
            for entity_id in expanded_set:
                entity = self.get_entity(entity_id)
                if entity and entity_id not in [e.get("entity_id") for e in similar]:
                    expanded.append(entity.to_dict())

        return {
            "similar": similar,
            "expanded": expanded,
            "query": text,
            "total_results": len(similar) + len(expanded),
        }

    def _expand(
        self,
        entity_id: str,
        rel_types: List[str],
        depth: int,
        visited: Optional[Set[str]] = None,
    ) -> Set[str]:
        """Expand from entity via relationships"""
        if visited is None:
            visited = set()

        if depth <= 0 or entity_id in visited:
            return {entity_id}

        visited.add(entity_id)
        expanded = {entity_id}

        for rel in self.get_relationships(entity_id, rel_types, direction="both"):
            other_id = rel["to"] if rel["from"] == entity_id else rel["from"]
            if other_id not in visited:
                expanded.update(self._expand(other_id, rel_types, depth - 1, visited))

        return expanded

    # === Graph Analysis ===

    def get_stats(self) -> Dict:
        """Get graph statistics"""
        return {
            "entities": self.graph.number_of_nodes(),
            "relationships": self.graph.number_of_edges(),
            "entity_types": len(
                set(
                    self.graph.nodes[n].get("type", "unknown")
                    for n in self.graph.nodes()
                )
            ),
            "relationship_types": len(
                set(
                    data.get("relation", "unknown")
                    for _, _, data in self.graph.edges(data=True)
                )
            ),
            "cached_entities": len(self.entities),
        }

    def visualize(self) -> nx.MultiDiGraph:
        """Return graph for visualization"""
        return self.graph

    def export_graph(self, format: str = "json") -> str:
        """Export graph to various formats"""
        if format == "json":
            data = {
                "nodes": [{"id": n, **self.graph.nodes[n]} for n in self.graph.nodes()],
                "edges": [
                    {"source": u, "target": v, **data}
                    for u, v, data in self.graph.edges(data=True)
                ],
            }
            return json.dumps(data, indent=2, default=str)

        return ""


# === Convenience Functions ===

_memory_graph: Optional[MemoryGraph] = None


def get_memory_graph() -> MemoryGraph:
    """Get or create memory graph instance"""
    global _memory_graph
    if not _memory_graph:
        _memory_graph = MemoryGraph()
    return _memory_graph


def add_entity(*args, **kwargs) -> str:
    """Add entity to memory graph"""
    return get_memory_graph().add_entity(*args, **kwargs)


def add_relationship(*args, **kwargs):
    """Add relationship"""
    get_memory_graph().add_relationship(*args, **kwargs)


def similar_to(*args, **kwargs) -> List[Dict]:
    """Vector search"""
    return get_memory_graph().similar_to(*args, **kwargs)


def hybrid_query(*args, **kwargs) -> Dict:
    """Hybrid query"""
    return get_memory_graph().hybrid_query(*args, **kwargs)


def get_stats() -> Dict:
    """Get graph stats"""
    return get_memory_graph().get_stats()


if __name__ == "__main__":
    print("🧠 Memory Graph Demo")
    print("=" * 60)

    mg = MemoryGraph()

    # Add sample entities
    print("\n📦 Adding entities...")

    file1 = mg.add_entity(
        type="file",
        name="auth.py",
        content="Authentication module with login and logout functions",
    )
    func1 = mg.add_entity(
        type="function", name="login", content="Login function - validates credentials"
    )
    func2 = mg.add_entity(
        type="function", name="verify_token", content="Verify JWT token validity"
    )
    bug1 = mg.add_entity(
        type="bug",
        name="auth_bypass",
        content="Authentication bypass vulnerability in login",
    )

    print(f"   Added 4 entities")

    # Add relationships
    print("\n🔗 Adding relationships...")

    mg.add_relationship(file1, func1, "contains")
    mg.add_relationship(file1, func2, "contains")
    mg.add_relationship(func1, func2, "calls")
    mg.add_relationship(bug1, func1, "affects")
    mg.add_relationship(bug1, file1, "affects")

    print(f"   Added 5 relationships")

    # Vector search
    print("\n🔍 Vector search: 'authentication vulnerability'")
    results = mg.similar_to("authentication vulnerability", top_k=3)
    for r in results:
        print(f"   [{r['score']:.3f}] {r['type']}/{r['name']}: {r['content'][:60]}")

    # Graph query
    print("\n🔗 Graph query: 'contains'")
    results = mg.query("contains")
    for r in results:
        print(f"   {r['from_name']} → {r['to_name']}")

    # Hybrid query
    print("\n🎯 Hybrid query: 'login bug' with relationships")
    results = mg.hybrid_query(
        "login bug", relationships=["calls", "affects", "contains"], max_depth=2
    )

    print(f"   Similar: {len(results['similar'])}")
    for r in results["similar"][:3]:
        print(f"     - {r['type']}/{r['name']}")

    print(f"   Expanded: {len(results['expanded'])}")
    for e in results["expanded"][:3]:
        print(f"     - {e['type']}/{e['name']}")

    # Stats
    print("\n📊 Graph Statistics")
    stats = mg.get_stats()
    print(f"   Entities: {stats['entities']}")
    print(f"   Relationships: {stats['relationships']}")
    print(f"   Entity types: {stats['entity_types']}")
    print(f"   Relationship types: {stats['relationship_types']}")

    print("\n✅ Demo complete!")
