"""
GraphMemory
Semantic knowledge graph for AI conversational memory. Zero external deps.

Quick start:
    from GraphMemory import GraphMemory

    gm = GraphMemory()

    # Ingest a conversation turn
    gm.ingest("Richard worked on PromptForge last week and fixed the auth bug.")

    # Query neighbors
    neighbors = gm.neighbors("PromptForge")
    # [{"label": "Richard", "rel": "worked_on", ...}]

    # Find connections between two entities
    path = gm.path("Richard", "auth bug")
    # [["Richard", "PromptForge", "auth bug"]]

    # Search for entities
    results = gm.search("auth")

    # Use LLM for richer extraction
    gm = GraphMemory(llm=my_llm)
    gm.ingest(long_conversation_text)

    # Stats
    print(gm.stats())
"""
from typing import Callable, List, Optional
from .models import Node, Edge
from .store import GraphStore
from .extractor import extract_heuristic, extract_with_llm


class GraphMemory:
    """
    High-level API: ingest text → grow graph → query relationships.

    Args:
        db_path: Path to SQLite graph database (default: "graph_memory.db").
        llm:     Optional fn(prompt)->str for LLM-assisted extraction.
    """

    def __init__(self, db_path: str = "graph_memory.db", llm: Optional[Callable] = None):
        self.store = GraphStore(db_path)
        self.llm = llm

    def ingest(self, text: str) -> dict:
        """
        Parse text, extract entities/relationships, and store them.

        Returns:
            {"nodes_added": int, "edges_added": int}
        """
        if self.llm:
            nodes, edges = extract_with_llm(text, self.llm)
        else:
            nodes, edges = extract_heuristic(text)

        self.store.bulk_upsert(nodes, edges)
        return {"nodes_added": len(nodes), "edges_added": len(edges)}

    def neighbors(self, label: str) -> List[dict]:
        """Return all entities connected to the given entity label."""
        return self.store.neighbors(label)

    def path(self, src: str, dst: str, max_hops: int = 3) -> List[List[str]]:
        """Find relationship paths between two entities."""
        return self.store.path(src, dst, max_hops)

    def search(self, query: str, kind: str = None) -> List[dict]:
        """Search entities by label substring."""
        return self.store.search_nodes(query, kind=kind)

    def add_node(self, label: str, kind: str = "entity", **props) -> Node:
        """Manually add a node."""
        n = Node(label=label, kind=kind, properties=props)
        self.store.upsert_node(n)
        return n

    def add_edge(self, src_label: str, rel: str, dst_label: str, context: str = "") -> Edge:
        """Manually add a relationship edge."""
        src = self.store.find_node(src_label) or self.add_node(src_label).to_dict()
        dst = self.store.find_node(dst_label) or self.add_node(dst_label).to_dict()
        e = Edge(src_id=src["id"], rel=rel, dst_id=dst["id"], context=context)
        self.store.upsert_edge(e)
        return e

    def stats(self) -> dict:
        return self.store.stats()


__version__ = "0.1.0"
__all__ = ["GraphMemory", "GraphStore", "Node", "Edge"]
