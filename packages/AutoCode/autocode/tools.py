"""
Tool Integration - Connect Agents to External Tools

Provides agents access to file system, code execution, and other tools.
"""

import logging
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional


@dataclass
class ToolResult:
    """Result from tool execution."""

    success: bool
    output: str
    error: Optional[str] = None
    data: Any = None


class ToolRegistry:
    """Registry for available tools."""

    def __init__(self):
        self.logger = logging.getLogger("ToolRegistry")
        self._tools: dict[str, callable] = {}

    def register(self, name: str, tool_func: callable):
        """Register a tool."""
        self._tools[name] = tool_func
        self.logger.debug(f"Tool registered: {name}")

    def get(self, name: str) -> Optional[callable]:
        """Get a tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> list[str]:
        """List all registered tools."""
        return list(self._tools.keys())

    def execute(self, name: str, **kwargs) -> ToolResult:
        """Execute a tool."""
        tool = self.get(name)
        if not tool:
            return ToolResult(
                success=False,
                output="",
                error=f"Unknown tool: {name}",
            )

        try:
            result = tool(**kwargs)
            return ToolResult(success=True, output=str(result), data=result)
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=str(e),
            )


class FileSystemTools:
    """File system operations for agents."""

    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self.logger = logging.getLogger("FileSystemTools")

    def read_file(self, path: str) -> ToolResult:
        """Read a file's contents."""
        try:
            file_path = self.base_dir / path
            if not file_path.exists():
                return ToolResult(
                    success=False,
                    output="",
                    error=f"File not found: {path}",
                )

            content = file_path.read_text()
            return ToolResult(success=True, output=content, data=content)

        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))

    def write_file(self, path: str, content: str) -> ToolResult:
        """Write content to a file."""
        try:
            file_path = self.base_dir / path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)

            return ToolResult(
                success=True,
                output=f"Written: {path}",
                data={"path": str(file_path), "bytes": len(content)},
            )

        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))

    def list_dir(self, path: str = ".") -> ToolResult:
        """List directory contents."""
        try:
            dir_path = self.base_dir / path
            if not dir_path.exists():
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Directory not found: {path}",
                )

            items = [str(p.relative_to(self.base_dir)) for p in dir_path.iterdir()]
            return ToolResult(success=True, output="\n".join(items), data=items)

        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))

    def file_exists(self, path: str) -> ToolResult:
        """Check if file exists."""
        try:
            exists = (self.base_dir / path).exists()
            return ToolResult(success=True, output=str(exists), data=exists)
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))


class ShellTools:
    """Shell command execution for agents."""

    def __init__(self, allowed_commands: Optional[list[str]] = None):
        self.allowed_commands = allowed_commands or []
        self.logger = logging.getLogger("ShellTools")

    def run_command(self, command: str, timeout: int = 30) -> ToolResult:
        """Run a shell command."""
        if self.allowed_commands:
            cmd_base = command.split()[0]
            if cmd_base not in self.allowed_commands:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Command not allowed: {cmd_base}",
                )

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            return ToolResult(
                success=result.returncode == 0,
                output=result.stdout,
                error=result.stderr if result.returncode != 0 else None,
                data={
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                },
            )

        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                output="",
                error=f"Command timed out after {timeout}s",
            )
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))


class CodeExecutionTools:
    """Code execution for agents."""

    def __init__(self, language: str = "python"):
        self.language = language
        self.logger = logging.getLogger("CodeExecutionTools")

    def execute_python(self, code: str, timeout: int = 30) -> ToolResult:
        """Execute Python code."""
        try:
            result = subprocess.run(
                ["python", "-c", code],
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            return ToolResult(
                success=result.returncode == 0,
                output=result.stdout,
                error=result.stderr if result.returncode != 0 else None,
            )

        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                output="",
                error=f"Execution timed out after {timeout}s",
            )
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))


def create_frank_tools(base_dir: Optional[str] = None) -> ToolRegistry:
    """
    Create a registry with Frank's standard tools.

    Args:
        base_dir: Base directory for file operations

    Returns:
        Configured ToolRegistry
    """
    registry = ToolRegistry()

    fs_tools = FileSystemTools(base_dir)
    registry.register("read_file", fs_tools.read_file)
    registry.register("write_file", fs_tools.write_file)
    registry.register("list_dir", fs_tools.list_dir)
    registry.register("file_exists", fs_tools.file_exists)

    shell_tools = ShellTools(allowed_commands=["ls", "dir", "cat", "type"])
    registry.register("run_command", shell_tools.run_command)

    code_tools = CodeExecutionTools()
    registry.register("execute_python", code_tools.execute_python)

    return registry


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    tools = create_frank_tools()

    print("Available tools:", tools.list_tools())

    result = tools.execute("list_dir", path=".")
    print("\nDirectory listing:", result.output)
