"""
Core data models for Tool Composer.

All shared dataclasses and types used across modules.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class NodeType(Enum):
    """Categories of nodes in the pipeline."""

    LLM = "llm"
    TOOL = "tool"
    LOGIC = "logic"
    INPUT = "input"
    OUTPUT = "output"


class NodeStatus(Enum):
    """Execution status of a node."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class NodeConfig:
    """Configuration for a node in the pipeline."""

    id: str
    type: str
    name: str
    category: NodeType = NodeType.LLM
    parameters: dict = field(default_factory=dict)
    inputs: list = field(default_factory=list)
    outputs: list = field(default_factory=list)
    position: dict = field(default_factory=lambda: {"x": 0, "y": 0})
    enabled: bool = True
    description: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "category": self.category.value,
            "parameters": self.parameters,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "position": self.position,
            "enabled": self.enabled,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "NodeConfig":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            type=data["type"],
            name=data.get("name", data["type"]),
            category=NodeType(data.get("category", "llm")),
            parameters=data.get("parameters", {}),
            inputs=data.get("inputs", []),
            outputs=data.get("outputs", []),
            position=data.get("position", {"x": 0, "y": 0}),
            enabled=data.get("enabled", True),
            description=data.get("description", ""),
        )


@dataclass
class EdgeConfig:
    """Connection between two nodes."""

    id: str
    source_node: str
    target_node: str
    source_output: str = "output"
    target_input: str = "input"
    condition: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "source": self.source_node,
            "target": self.target_node,
            "source_output": self.source_output,
            "target_input": self.target_input,
            "condition": self.condition,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EdgeConfig":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            source_node=data["source"],
            target_node=data["target"],
            source_output=data.get("source_output", "output"),
            target_input=data.get("target_input", "input"),
            condition=data.get("condition"),
        )


@dataclass
class PipelineConfig:
    """Complete pipeline configuration."""

    id: str
    name: str
    description: str = ""
    nodes: list[NodeConfig] = field(default_factory=list)
    edges: list[EdgeConfig] = field(default_factory=list)
    variables: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    version: str = "1.0.0"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "variables": self.variables,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PipelineConfig":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            nodes=[NodeConfig.from_dict(n) for n in data.get("nodes", [])],
            edges=[EdgeConfig.from_dict(e) for e in data.get("edges", [])],
            variables=data.get("variables", {}),
            version=data.get("version", "1.0.0"),
            created_at=datetime.fromisoformat(data["created_at"])
            if "created_at" in data
            else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"])
            if "updated_at" in data
            else datetime.now(),
        )

    def add_node(self, node: NodeConfig):
        """Add a node to the pipeline."""
        self.nodes.append(node)
        self.updated_at = datetime.now()

    def add_edge(self, edge: EdgeConfig):
        """Add an edge to the pipeline."""
        self.edges.append(edge)
        self.updated_at = datetime.now()

    def get_node(self, node_id: str) -> Optional[NodeConfig]:
        """Get a node by ID."""
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None

    def get_incoming_edges(self, node_id: str) -> list[EdgeConfig]:
        """Get all edges coming into a node."""
        return [e for e in self.edges if e.target_node == node_id]

    def get_outgoing_edges(self, node_id: str) -> list[EdgeConfig]:
        """Get all edges going out of a node."""
        return [e for e in self.edges if e.source_node == node_id]


@dataclass
class NodeResult:
    """Result from executing a node."""

    node_id: str
    status: NodeStatus
    output: Any = None
    error: Optional[str] = None
    duration_ms: float = 0.0
    metadata: dict = field(default_factory=dict)

    @property
    def success(self) -> bool:
        """Check if node executed successfully."""
        return self.status == NodeStatus.COMPLETED

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "node_id": self.node_id,
            "status": self.status.value,
            "output": self.output,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "metadata": self.metadata,
        }


@dataclass
class PipelineResult:
    """Result from executing a complete pipeline."""

    pipeline_id: str
    success: bool
    node_results: list[NodeResult] = field(default_factory=list)
    final_output: Any = None
    error: Optional[str] = None
    duration_ms: float = 0.0
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "pipeline_id": self.pipeline_id,
            "success": self.success,
            "node_results": [r.to_dict() for r in self.node_results],
            "final_output": self.final_output,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
        }
