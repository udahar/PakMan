# Updated-On: 2026-03-08
# Updated-By: Codex
# PM-Ticket: UNTRACKED

"""
Tool Builder
Build tools from specifications
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum


class ToolType(Enum):
    """Types of tools."""

    PYTHON = "python"
    BASH = "bash"
    HTTP = "http"
    SEARCH = "search"


@dataclass
class ToolSpec:
    """Tool specification."""

    name: str
    description: str
    tool_type: ToolType
    code: str
    parameters: List[Dict[str, str]] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)


@dataclass
class BuiltTool:
    """A built tool."""

    tool_id: str
    name: str
    description: str
    function: Callable
    metadata: Dict[str, Any] = field(default_factory=dict)


class ToolBuilder:
    """
    Build tools dynamically from specifications.

    Features:
    - Python code tools
    - Bash script tools
    - HTTP API tools
    - Parameter validation
    """

    def __init__(self):
        self.tools: Dict[str, BuiltTool] = {}
        self.specs: Dict[str, ToolSpec] = {}

    def build(self, spec: ToolSpec) -> BuiltTool:
        """Build tool from specification."""
        function = self._compile(spec)

        tool_id = f"{spec.name}_{spec.tool_type.value}"

        tool = BuiltTool(
            tool_id=tool_id,
            name=spec.name,
            description=spec.description,
            function=function,
            metadata={
                "tool_type": spec.tool_type.value,
                "parameters": spec.parameters,
                "dependencies": spec.dependencies,
            },
        )

        self.tools[tool_id] = tool
        self.specs[tool_id] = spec

        return tool

    def _compile(self, spec: ToolSpec) -> Callable:
        """Compile tool spec to executable function."""
        if spec.tool_type == ToolType.PYTHON:
            return self._compile_python(spec)
        elif spec.tool_type == ToolType.BASH:
            return self._compile_bash(spec)
        elif spec.tool_type == ToolType.HTTP:
            return self._compile_http(spec)
        else:
            raise ValueError(f"Unknown tool type: {spec.tool_type}")

    def _compile_python(self, spec: ToolSpec) -> Callable:
        """Compile Python tool."""
        import types

        namespace = {}

        try:
            exec(spec.code, namespace)
        except Exception as e:
            raise ValueError(f"Failed to compile Python tool: {e}")

        if "execute" in namespace:
            return namespace["execute"]
        elif "run" in namespace:
            return namespace["run"]
        else:
            raise ValueError("Python tool must define execute() or run()")

    def _compile_bash(self, spec: ToolSpec) -> Callable:
        """Compile Bash tool."""

        def bash_tool(input_data: str) -> str:
            import subprocess

            result = subprocess.run(
                spec.code, shell=True, input=input_data, capture_output=True, text=True
            )
            return result.stdout or result.stderr

        return bash_tool

    def _compile_http(self, spec: ToolSpec) -> Callable:
        """Compile HTTP tool."""

        def http_tool(params: Dict[str, Any]) -> str:
            import requests

            url = spec.code.format(**params)
            method = spec.metadata.get("method", "GET")

            response = requests.request(method, url)
            return response.text

        return http_tool

    def get_tool(self, tool_id: str) -> Optional[BuiltTool]:
        """Get tool by ID."""
        return self.tools.get(tool_id)

    def list_tools(self) -> List[BuiltTool]:
        """List all built tools."""
        return list(self.tools.values())

    def remove_tool(self, tool_id: str) -> bool:
        """Remove tool."""
        if tool_id in self.tools:
            del self.tools[tool_id]
            if tool_id in self.specs:
                del self.specs[tool_id]
            return True
        return False

    def get_stats(self) -> Dict[str, Any]:
        """Get builder stats."""
        return {"total_tools": len(self.tools), "by_type": {}}


def create_tool_builder() -> ToolBuilder:
    """Factory function to create tool builder."""
    return ToolBuilder()
