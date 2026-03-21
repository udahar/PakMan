"""
Node implementations for Tool Composer.
"""

from toolcomposer.nodes.llm_node import LLMNode
from toolcomposer.nodes.tool_nodes import (
    BashNode,
    FileReadNode,
    FileWriteNode,
    HttpNode,
)
from toolcomposer.nodes.logic_nodes import (
    FilterNode,
    TransformNode,
    MergeNode,
    ConditionNode,
)
from toolcomposer.nodes.input_output import InputNode, OutputNode
from toolcomposer.node_registry import register_node

# Register all nodes
register_node(LLMNode)
register_node(BashNode)
register_node(FileReadNode)
register_node(FileWriteNode)
register_node(HttpNode)
register_node(FilterNode)
register_node(TransformNode)
register_node(MergeNode)
register_node(ConditionNode)
register_node(InputNode)
register_node(OutputNode)

__all__ = [
    "LLMNode",
    "BashNode",
    "FileReadNode",
    "FileWriteNode",
    "HttpNode",
    "FilterNode",
    "TransformNode",
    "MergeNode",
    "ConditionNode",
    "InputNode",
    "OutputNode",
]
