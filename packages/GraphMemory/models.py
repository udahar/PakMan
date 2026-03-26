"""
GraphMemory - models.py
Node and edge models for the semantic knowledge graph.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid


@dataclass
class Node:
    """
    An entity extracted from AI conversation (person, concept, tool, project, etc.).

    Examples:
        Node(label="PromptForge", kind="tool")
        Node(label="Richard",    kind="person")
        Node(label="auth bug",   kind="issue")
    """
    label: str
    kind: str = "entity"         # person | tool | project | concept | issue | event
    id: str = field(default_factory=lambda: f"n_{uuid.uuid4().hex[:8]}")
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    mentions: int = 1            # How often this entity appears

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "label": self.label,
            "kind": self.kind,
            "properties": self.properties,
            "created_at": self.created_at,
            "mentions": self.mentions,
        }


@dataclass
class Edge:
    """
    A directed relationship between two nodes.

    Examples:
        Edge(src="Richard", rel="worked_on", dst="PromptForge")
        Edge(src="auth bug", rel="found_in", dst="AiOSKernel")
    """
    src_id: str
    rel: str                     # worked_on | created | broke | fixed | discussed | depends_on
    dst_id: str
    id: str = field(default_factory=lambda: f"e_{uuid.uuid4().hex[:8]}")
    weight: float = 1.0
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    context: str = ""            # Source sentence

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "src_id": self.src_id,
            "rel": self.rel,
            "dst_id": self.dst_id,
            "weight": self.weight,
            "created_at": self.created_at,
            "context": self.context,
        }
