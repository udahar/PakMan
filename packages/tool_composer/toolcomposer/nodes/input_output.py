"""
Input/Output Nodes - Pipeline entry and exit points.
"""

import json
from typing import Any

from toolcomposer.base_node import BaseNode
from toolcomposer.models import NodeConfig


class InputNode(BaseNode):
    """
    Node for providing initial input to a pipeline.

    This node doesn't require inputs - it provides them.

    Outputs:
        - output: The configured or provided input value
    """

    node_type = "input"
    category = "input"
    inputs = []
    outputs = ["output"]
    description = "Provide input data to the pipeline"

    def validate_inputs(self, inputs: dict) -> tuple[bool, str]:
        """Input nodes don't require validation."""
        return True, None

    def process(self, inputs: dict) -> dict:
        """Return the configured input value."""
        # Check for default value in parameters
        default = self.config.parameters.get("default", "")

        # Check for provided input (overrides default)
        value = inputs.get("value", default)

        # Handle different input types
        input_type = self.config.parameters.get("type", "text")

        if input_type == "json":
            try:
                if isinstance(value, str):
                    value = json.loads(value)
            except json.JSONDecodeError as e:
                return {"output": f"Invalid JSON: {str(e)}"}

        elif input_type == "number":
            try:
                value = float(value)
            except (ValueError, TypeError):
                pass

        elif input_type == "boolean":
            if isinstance(value, str):
                value = value.lower() in ("true", "1", "yes")

        return {"output": value}


class OutputNode(BaseNode):
    """
    Node for capturing final pipeline output.

    Inputs:
        - input: The data to output

    Outputs:
        - output: The same data (pass-through)
        - formatted: Formatted version of the data
    """

    node_type = "output"
    category = "output"
    inputs = ["input"]
    outputs = ["output", "formatted"]
    description = "Capture and format pipeline output"

    def process(self, inputs: dict) -> dict:
        """Format and return the output."""
        data = inputs.get("input")
        output_format = self.config.parameters.get("format", "text")
        prefix = self.config.parameters.get("prefix", "")
        suffix = self.config.parameters.get("suffix", "")

        try:
            if output_format == "json":
                formatted = json.dumps(data, indent=2)
            elif output_format == "text":
                formatted = str(data)
            elif output_format == "html":
                formatted = f"<pre>{str(data)}</pre>"
            else:
                formatted = str(data)

            # Add prefix/suffix
            final_output = f"{prefix}{formatted}{suffix}"

            return {
                "output": data,
                "formatted": final_output,
            }

        except Exception as e:
            return {
                "output": data,
                "formatted": f"Error formatting output: {str(e)}",
            }
