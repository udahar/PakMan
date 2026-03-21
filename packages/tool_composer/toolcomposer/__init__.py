"""
Tool Composer - Visual AI Workflow Builder

A drag-and-drop interface for building AI pipelines by connecting nodes.
"""

from toolcomposer.models import NodeConfig, EdgeConfig, PipelineConfig, NodeResult
from toolcomposer.base_node import BaseNode
from toolcomposer.node_registry import NodeRegistry
from toolcomposer.flow_engine import FlowEngine
from toolcomposer.serializer import PipelineSerializer

__version__ = "1.0.0"
__all__ = [
    "NodeConfig",
    "EdgeConfig",
    "PipelineConfig",
    "NodeResult",
    "BaseNode",
    "NodeRegistry",
    "FlowEngine",
    "PipelineSerializer",
]
