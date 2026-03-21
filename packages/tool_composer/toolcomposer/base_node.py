"""
Base Node - Abstract foundation for all pipeline nodes.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Optional

from toolcomposer.models import NodeConfig, NodeResult, NodeStatus


class BaseNode(ABC):
    """
    Abstract base class for all pipeline nodes.

    Subclasses must define:
    - node_type: Class identifier
    - inputs: Expected input names
    - outputs: Produced output names
    - process(): Core execution logic
    """

    node_type: str = "base"
    category: str = "base"
    inputs: list[str] = []
    outputs: list[str] = []
    description: str = "Base node"

    def __init__(self, config: NodeConfig):
        self.config = config
        self.logger = self._setup_logging()
        self._initialized = False

    def _setup_logging(self) -> logging.Logger:
        """Configure node-specific logger."""
        logger = logging.getLogger(f"Node.{self.config.name}")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def initialize(self) -> bool:
        """
        Initialize the node before execution.

        Override in subclasses for setup logic.
        """
        self._initialized = True
        self.logger.debug(f"Node {self.config.name} initialized")
        return True

    def validate_inputs(self, inputs: dict) -> tuple[bool, Optional[str]]:
        """
        Validate incoming inputs.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.config.enabled:
            return False, "Node is disabled"

        missing = [inp for inp in self.inputs if inp not in inputs]
        if missing:
            return False, f"Missing required inputs: {missing}"

        return True, None

    def execute(self, inputs: dict) -> NodeResult:
        """
        Execute the node with given inputs.

        Handles timing, error handling, and result wrapping.
        """
        start_time = time.time()

        try:
            # Check if enabled
            if not self.config.enabled:
                return NodeResult(
                    node_id=self.config.id,
                    status=NodeStatus.SKIPPED,
                    error="Node is disabled",
                )

            # Validate inputs
            is_valid, error = self.validate_inputs(inputs)
            if not is_valid:
                return NodeResult(
                    node_id=self.config.id,
                    status=NodeStatus.FAILED,
                    error=error,
                )

            # Initialize if needed
            if not self._initialized:
                if not self.initialize():
                    return NodeResult(
                        node_id=self.config.id,
                        status=NodeStatus.FAILED,
                        error="Initialization failed",
                    )

            # Execute process
            self.logger.debug(f"Executing node {self.config.name}")
            output = self.process(inputs)

            duration_ms = (time.time() - start_time) * 1000

            return NodeResult(
                node_id=self.config.id,
                status=NodeStatus.COMPLETED,
                output=output,
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.error(f"Node execution failed: {e}")

            return NodeResult(
                node_id=self.config.id,
                status=NodeStatus.FAILED,
                error=str(e),
                duration_ms=duration_ms,
            )

    @abstractmethod
    def process(self, inputs: dict) -> Any:
        """
        Process inputs and produce outputs.

        Must be implemented by subclasses.

        Args:
            inputs: Dictionary of input values

        Returns:
            Output value(s)
        """
        pass

    def get_config(self) -> NodeConfig:
        """Get the node configuration."""
        return self.config

    def update_config(self, config: NodeConfig):
        """Update the node configuration."""
        self.config = config
        self._initialized = False

    @classmethod
    def create_default_config(cls, node_id: str, name: Optional[str] = None) -> NodeConfig:
        """Create a default configuration for this node type."""
        return NodeConfig(
            id=node_id,
            type=cls.node_type,
            name=name or cls.node_type,
            category=cls.category,
            inputs=cls.inputs.copy(),
            outputs=cls.outputs.copy(),
        )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.config.id}, name={self.config.name})"
