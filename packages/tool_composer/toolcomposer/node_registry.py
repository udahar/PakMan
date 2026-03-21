"""
Node Registry - Central registration for all node types.
"""

import logging
from typing import Optional, Type

from toolcomposer.base_node import BaseNode
from toolcomposer.models import NodeConfig


class NodeRegistry:
    """
    Central registry for all available node types.

    Provides:
    - Node type registration
    - Node instantiation by type
    - Available node listing
    """

    _instance: Optional["NodeRegistry"] = None
    _nodes: dict[str, Type[BaseNode]] = {}

    def __new__(cls) -> "NodeRegistry":
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.logger = logging.getLogger("NodeRegistry")
        return cls._instance

    def register(self, node_class: Type[BaseNode], override: bool = False) -> bool:
        """
        Register a node class.

        Args:
            node_class: The node class to register
            override: Allow overriding existing registrations

        Returns:
            True if registered, False if already exists
        """
        node_type = node_class.node_type

        if node_type in self._nodes and not override:
            self.logger.warning(f"Node type '{node_type}' already registered")
            return False

        self._nodes[node_type] = node_class
        self.logger.info(f"Node registered: {node_type}")
        return True

    def unregister(self, node_type: str) -> bool:
        """Remove a node type from the registry."""
        if node_type in self._nodes:
            del self._nodes[node_type]
            self.logger.info(f"Node unregistered: {node_type}")
            return True
        return False

    def get(self, node_type: str) -> Optional[Type[BaseNode]]:
        """Get a node class by type."""
        return self._nodes.get(node_type)

    def create(self, node_type: str, config: NodeConfig) -> Optional[BaseNode]:
        """
        Create a node instance by type.

        Args:
            node_type: The type of node to create
            config: Configuration for the node

        Returns:
            Node instance or None if type not found
        """
        node_class = self.get(node_type)
        if not node_class:
            self.logger.error(f"Unknown node type: {node_type}")
            return None

        try:
            return node_class(config)
        except Exception as e:
            self.logger.error(f"Failed to create node '{node_type}': {e}")
            return None

    def list_nodes(self) -> list[dict]:
        """List all registered node types with metadata."""
        return [
            {
                "type": node_class.node_type,
                "category": node_class.category,
                "name": node_class.__name__,
                "inputs": node_class.inputs,
                "outputs": node_class.outputs,
                "description": node_class.description,
            }
            for node_class in self._nodes.values()
        ]

    def get_by_category(self, category: str) -> list[dict]:
        """Get all nodes in a category."""
        return [
            info
            for info in self.list_nodes()
            if info["category"] == category
        ]

    def get_categories(self) -> list[str]:
        """Get all unique categories."""
        return list(set(info["category"] for info in self.list_nodes()))

    def is_registered(self, node_type: str) -> bool:
        """Check if a node type is registered."""
        return node_type in self._nodes

    def clear(self):
        """Clear all registrations."""
        self._nodes.clear()
        self.logger.info("Node registry cleared")

    @property
    def count(self) -> int:
        """Get the number of registered node types."""
        return len(self._nodes)


# Global registry instance
registry = NodeRegistry()


def register_node(node_class: Type[BaseNode], override: bool = False) -> bool:
    """Convenience function to register a node."""
    return registry.register(node_class, override)


def create_node(node_type: str, config: NodeConfig) -> Optional[BaseNode]:
    """Convenience function to create a node."""
    return registry.create(node_type, config)


def get_available_nodes() -> list[dict]:
    """Get list of all available nodes."""
    return registry.list_nodes()
