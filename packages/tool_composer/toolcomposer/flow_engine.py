"""
Flow Engine - Pipeline Execution Engine

Executes pipelines by traversing the node graph and passing data between nodes.
"""

import logging
import time
from collections import deque
from typing import Any, Optional

from toolcomposer.models import (
    PipelineConfig,
    PipelineResult,
    NodeResult,
    NodeStatus,
    EdgeConfig,
)
from toolcomposer.node_registry import registry as node_registry


class FlowEngine:
    """
    Executes pipeline configurations.

    Features:
    - Topological sorting of nodes
    - Data flow between nodes via edges
    - Conditional execution
    - Error handling and recovery
    """

    def __init__(self, pipeline: PipelineConfig):
        self.pipeline = pipeline
        self.logger = logging.getLogger("FlowEngine")
        self._node_instances: dict[str, Any] = {}
        self._node_outputs: dict[str, Any] = {}
        self._execution_order: list[str] = []

    def _build_node_instances(self) -> bool:
        """Create instances of all nodes in the pipeline."""
        for node_config in self.pipeline.nodes:
            node = node_registry.create(node_config.type, node_config)
            if not node:
                self.logger.error(f"Failed to create node: {node_config.id}")
                return False
            self._node_instances[node_config.id] = node

        self.logger.info(f"Built {len(self._node_instances)} node instances")
        return True

    def _topological_sort(self) -> list[str]:
        """
        Sort nodes in execution order using Kahn's algorithm.

        Returns:
            List of node IDs in execution order
        """
        # Build adjacency list and in-degree count
        in_degree: dict[str, int] = {n.id: 0 for n in self.pipeline.nodes}
        adjacency: dict[str, list[str]] = {n.id: [] for n in self.pipeline.nodes}

        for edge in self.pipeline.edges:
            if edge.source_node in adjacency:
                adjacency[edge.source_node].append(edge.target_node)
                if edge.target_node in in_degree:
                    in_degree[edge.target_node] += 1

        # Start with nodes that have no dependencies
        queue = deque([node_id for node_id, degree in in_degree.items() if degree == 0])
        result = []

        while queue:
            node_id = queue.popleft()
            result.append(node_id)

            for neighbor in adjacency[node_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(result) != len(self.pipeline.nodes):
            self.logger.warning("Cycle detected in pipeline graph")
            # Return nodes in original order if cycle exists
            return [n.id for n in self.pipeline.nodes]

        self.logger.debug(f"Execution order: {result}")
        return result

    def _get_node_inputs(self, node_id: str) -> dict:
        """
        Gather inputs for a node from connected edges.

        Args:
            node_id: The target node ID

        Returns:
            Dictionary of input values
        """
        inputs = {}
        node_config = self.pipeline.get_node(node_id)

        if not node_config:
            return inputs

        # Get incoming edges
        incoming = self.pipeline.get_incoming_edges(node_id)

        for edge in incoming:
            source_output = self._node_outputs.get(edge.source_node, {})

            if isinstance(source_output, dict):
                value = source_output.get(edge.source_output)
            else:
                value = source_output

            inputs[edge.target_input] = value

        # Also check pipeline variables
        for var_name, var_value in self.pipeline.variables.items():
            if var_name not in inputs:
                inputs[var_name] = var_value

        return inputs

    def _should_execute(self, edge: EdgeConfig, source_result: NodeResult) -> bool:
        """
        Check if an edge's condition allows execution.

        Args:
            edge: The edge to evaluate
            source_result: Result from the source node

        Returns:
            True if execution should proceed
        """
        if not edge.condition:
            return True

        # Simple condition evaluation
        try:
            # Support basic conditions like "output > 0" or "status == 'success'"
            context = {"output": source_result.output, "result": source_result}
            return bool(eval(edge.condition, {}, context))
        except Exception as e:
            self.logger.warning(f"Condition evaluation failed: {e}")
            return True  # Default to execute on error

    def execute(self, initial_inputs: Optional[dict] = None) -> PipelineResult:
        """
        Execute the complete pipeline.

        Args:
            initial_inputs: Optional initial input values

        Returns:
            PipelineResult with all node outputs
        """
        start_time = time.time()
        self.logger.info(f"Starting pipeline: {self.pipeline.name}")

        # Build node instances
        if not self._build_node_instances():
            return PipelineResult(
                pipeline_id=self.pipeline.id,
                success=False,
                error="Failed to build node instances",
            )

        # Determine execution order
        self._execution_order = self._topological_sort()

        # Set initial inputs as a virtual node output
        if initial_inputs:
            self._node_outputs["__initial__"] = initial_inputs

        node_results: list[NodeResult] = []
        pipeline_success = True

        # Execute nodes in order
        for node_id in self._execution_order:
            node = self._node_instances.get(node_id)
            if not node:
                continue

            # Get inputs for this node
            inputs = self._get_node_inputs(node_id)

            # Merge with initial inputs if this is a starting node
            if not self.pipeline.get_incoming_edges(node_id) and initial_inputs:
                inputs.update(initial_inputs)

            self.logger.debug(f"Executing node {node_id} with inputs: {inputs}")

            # Execute the node
            result = node.execute(inputs)
            node_results.append(result)

            # Store output for downstream nodes
            if result.success:
                self._node_outputs[node_id] = result.output
            else:
                self.logger.error(f"Node {node_id} failed: {result.error}")
                pipeline_success = False

                # Check if we should continue or abort
                if node.config.parameters.get("abort_on_failure", False):
                    break

        duration_ms = (time.time() - start_time) * 1000

        # Get final output (from last node in execution order)
        final_output = None
        if self._execution_order:
            last_node_id = self._execution_order[-1]
            final_output = self._node_outputs.get(last_node_id)

        return PipelineResult(
            pipeline_id=self.pipeline.id,
            success=pipeline_success,
            node_results=node_results,
            final_output=final_output,
            duration_ms=duration_ms,
            completed_at=time.time(),
        )

    def execute_node(self, node_id: str, inputs: dict) -> NodeResult:
        """
        Execute a single node by ID.

        Args:
            node_id: The node to execute
            inputs: Inputs for the node

        Returns:
            NodeResult from execution
        """
        node = self._node_instances.get(node_id)
        if not node:
            # Try to build just this node
            node_config = self.pipeline.get_node(node_id)
            if node_config:
                node = node_registry.create(node_config.type, node_config)
                self._node_instances[node_id] = node

        if not node:
            return NodeResult(
                node_id=node_id,
                status=NodeStatus.FAILED,
                error=f"Node not found: {node_id}",
            )

        return node.execute(inputs)

    def get_execution_order(self) -> list[str]:
        """Get the determined execution order."""
        return self._execution_order.copy()

    def get_node_output(self, node_id: str) -> Any:
        """Get the output from a previously executed node."""
        return self._node_outputs.get(node_id)

    def get_all_outputs(self) -> dict[str, Any]:
        """Get outputs from all executed nodes."""
        return self._node_outputs.copy()

    def reset(self):
        """Reset the engine state for re-execution."""
        self._node_outputs.clear()
        self._execution_order.clear()
        self.logger.debug("FlowEngine reset")
