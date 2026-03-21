"""
Logic Nodes - Filter, Transform, Merge, and Condition operations.
"""

import json
import re
from typing import Any, Callable

from toolcomposer.base_node import BaseNode
from toolcomposer.models import NodeConfig


class FilterNode(BaseNode):
    """
    Node for filtering data based on conditions.

    Inputs:
        - data: Data to filter

    Outputs:
        - filtered: Filtered data
        - passed: Boolean indicating if filter passed
    """

    node_type = "filter"
    category = "logic"
    inputs = ["data"]
    outputs = ["filtered", "passed"]
    description = "Filter data based on conditions"

    def process(self, inputs: dict) -> dict:
        """Filter data based on configured condition."""
        data = inputs.get("data")
        condition = self.config.parameters.get("condition", "True")
        filter_type = self.config.parameters.get("filter_type", "python")

        try:
            if filter_type == "python":
                # Evaluate Python expression
                context = {"data": data, "input": data}
                result = eval(condition, {}, context)

                if isinstance(result, bool):
                    passed = result
                    filtered = data if passed else None
                else:
                    # Use result as filtered data
                    passed = bool(result)
                    filtered = result

            elif filter_type == "regex":
                # Regex matching
                text = str(data)
                match = re.search(condition, text)
                passed = bool(match)
                filtered = match.group() if match else None

            elif filter_type == "contains":
                # Simple contains check
                passed = condition in str(data)
                filtered = data if passed else None

            else:
                passed = True
                filtered = data

            return {
                "filtered": filtered,
                "passed": passed,
            }

        except Exception as e:
            return {
                "filtered": None,
                "passed": False,
                "error": str(e),
            }


class TransformNode(BaseNode):
    """
    Node for transforming data.

    Inputs:
        - data: Data to transform

    Outputs:
        - result: Transformed data
    """

    node_type = "transform"
    category = "logic"
    inputs = ["data"]
    outputs = ["result"]
    description = "Transform data using Python expressions"

    def process(self, inputs: dict) -> dict:
        """Transform data using configured transformation."""
        data = inputs.get("data")
        transform = self.config.parameters.get("transform", "data")
        output_format = self.config.parameters.get("format", "text")

        try:
            # Create transformation context
            context = {
                "data": data,
                "input": data,
                "str": str,
                "int": int,
                "float": float,
                "list": list,
                "dict": dict,
                "json": json,
            }

            # Execute transformation
            if output_format == "json":
                result = json.loads(eval(transform, {}, context))
            else:
                result = eval(transform, {}, context)

            return {"result": result}

        except Exception as e:
            return {
                "result": f"Error: {str(e)}",
            }


class MergeNode(BaseNode):
    """
    Node for merging multiple inputs.

    Inputs:
        - input1: First input
        - input2: Second input
        - (additional inputs via parameters)

    Outputs:
        - merged: Combined output
    """

    node_type = "merge"
    category = "logic"
    inputs = ["input1", "input2"]
    outputs = ["merged"]
    description = "Merge multiple inputs together"

    def process(self, inputs: dict) -> dict:
        """Merge inputs based on configured strategy."""
        merge_type = self.config.parameters.get("merge_type", "concat")
        separator = self.config.parameters.get("separator", "\n")

        # Get all inputs
        values = [v for k, v in inputs.items() if k.startswith("input")]

        try:
            if merge_type == "concat":
                # String concatenation
                merged = separator.join(str(v) for v in values)

            elif merge_type == "list":
                # Combine into list
                merged = list(values)

            elif merge_type == "dict":
                # Combine into dictionary
                merged = {}
                for i, v in enumerate(values):
                    if isinstance(v, dict):
                        merged.update(v)
                    else:
                        merged[f"input{i + 1}"] = v

            elif merge_type == "template":
                # Use template string
                template = self.config.parameters.get("template", "{input1}")
                merged = template.format(**{f"input{i + 1}": v for i, v in enumerate(values)})

            else:
                merged = values

            return {"merged": merged}

        except Exception as e:
            return {
                "merged": f"Error: {str(e)}",
            }


class ConditionNode(BaseNode):
    """
    Node for conditional branching.

    Inputs:
        - data: Data to evaluate

    Outputs:
        - true_output: Output if condition is true
        - false_output: Output if condition is false
        - result: Boolean result of condition
    """

    node_type = "condition"
    category = "logic"
    inputs = ["data"]
    outputs = ["true_output", "false_output", "result"]
    description = "Evaluate conditions and branch execution"

    def process(self, inputs: dict) -> dict:
        """Evaluate condition and route data."""
        data = inputs.get("data")
        condition = self.config.parameters.get("condition", "True")

        try:
            # Evaluate condition
            context = {"data": data, "input": data}
            result = eval(condition, {}, context)
            is_true = bool(result)

            true_output = self.config.parameters.get("true_value", data)
            false_output = self.config.parameters.get("false_value", None)

            return {
                "true_output": true_output if is_true else false_output,
                "false_output": false_output if not is_true else true_output,
                "result": is_true,
            }

        except Exception as e:
            return {
                "true_output": None,
                "false_output": None,
                "result": False,
                "error": str(e),
            }
