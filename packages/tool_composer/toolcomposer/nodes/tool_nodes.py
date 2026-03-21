"""
Tool Nodes - Bash, File, and HTTP operations.
"""

import subprocess
import logging
from pathlib import Path
from typing import Optional

import requests

from toolcomposer.base_node import BaseNode
from toolcomposer.models import NodeConfig


class BashNode(BaseNode):
    """
    Node for executing bash/shell commands.

    Inputs:
        - command: The command to execute

    Outputs:
        - output: Combined stdout/stderr
        - stdout: Standard output only
        - stderr: Standard error only
        - returncode: Process return code
    """

    node_type = "bash"
    category = "tool"
    inputs = ["command"]
    outputs = ["output", "stdout", "stderr", "returncode"]
    description = "Execute shell commands"

    def process(self, inputs: dict) -> dict:
        """Execute shell command."""
        command = inputs.get("command", "")
        timeout = self.config.parameters.get("timeout", 30)
        shell = self.config.parameters.get("shell", True)

        self.logger.info(f"Executing command: {command[:100]}...")

        try:
            result = subprocess.run(
                command,
                shell=shell,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            return {
                "output": result.stdout or result.stderr,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }

        except subprocess.TimeoutExpired:
            return {
                "output": f"Command timed out after {timeout}s",
                "stdout": "",
                "stderr": f"Timeout after {timeout}s",
                "returncode": -1,
            }
        except Exception as e:
            return {
                "output": f"Error: {str(e)}",
                "stdout": "",
                "stderr": str(e),
                "returncode": -1,
            }


class FileReadNode(BaseNode):
    """
    Node for reading file contents.

    Inputs:
        - path: Path to the file to read

    Outputs:
        - content: File contents as string
        - lines: File contents as list of lines
    """

    node_type = "file_read"
    category = "tool"
    inputs = ["path"]
    outputs = ["content", "lines"]
    description = "Read file contents"

    def process(self, inputs: dict) -> dict:
        """Read file contents."""
        path = inputs.get("path", "")
        encoding = self.config.parameters.get("encoding", "utf-8")
        base_dir = self.config.parameters.get("base_dir")

        try:
            file_path = Path(base_dir) / path if base_dir else Path(path)

            if not file_path.exists():
                return {
                    "content": f"Error: File not found: {path}",
                    "lines": [],
                }

            content = file_path.read_text(encoding=encoding)
            lines = content.splitlines()

            return {
                "content": content,
                "lines": lines,
            }

        except Exception as e:
            return {
                "content": f"Error: {str(e)}",
                "lines": [],
            }


class FileWriteNode(BaseNode):
    """
    Node for writing content to files.

    Inputs:
        - path: Path to the file
        - content: Content to write

    Outputs:
        - success: Boolean indicating success
        - path: Absolute path of written file
        - bytes: Number of bytes written
    """

    node_type = "file_write"
    category = "tool"
    inputs = ["path", "content"]
    outputs = ["success", "path", "bytes"]
    description = "Write content to file"

    def process(self, inputs: dict) -> dict:
        """Write content to file."""
        path = inputs.get("path", "")
        content = inputs.get("content", "")
        encoding = self.config.parameters.get("encoding", "utf-8")
        base_dir = self.config.parameters.get("base_dir")
        append = self.config.parameters.get("append", False)

        try:
            file_path = Path(base_dir) / path if base_dir else Path(path)
            file_path.parent.mkdir(parents=True, exist_ok=True)

            mode = "a" if append else "w"
            if append:
                file_path.write_text(
                    file_path.read_text(encoding=encoding) + content,
                    encoding=encoding,
                )
            else:
                file_path.write_text(content, encoding=encoding)

            return {
                "success": True,
                "path": str(file_path.absolute()),
                "bytes": len(content.encode(encoding)),
            }

        except Exception as e:
            return {
                "success": False,
                "path": path,
                "error": str(e),
            }


class HttpNode(BaseNode):
    """
    Node for making HTTP requests.

    Inputs:
        - url: The URL to request
        - method: HTTP method (GET, POST, etc.)
        - body: Request body (for POST/PUT)

    Outputs:
        - response: Response body
        - status_code: HTTP status code
        - headers: Response headers
    """

    node_type = "http"
    category = "tool"
    inputs = ["url", "method", "body"]
    outputs = ["response", "status_code", "headers"]
    description = "Make HTTP requests"

    def process(self, inputs: dict) -> dict:
        """Make HTTP request."""
        url = inputs.get("url", "")
        method = inputs.get("method", "GET").upper()
        body = inputs.get("body")
        timeout = self.config.parameters.get("timeout", 30)

        headers = self.config.parameters.get("headers", {})

        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == "POST":
                response = requests.post(
                    url, json=body, headers=headers, timeout=timeout
                )
            elif method == "PUT":
                response = requests.put(
                    url, json=body, headers=headers, timeout=timeout
                )
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, timeout=timeout)
            else:
                return {
                    "response": f"Unsupported method: {method}",
                    "status_code": 400,
                    "headers": {},
                }

            return {
                "response": response.text,
                "status_code": response.status_code,
                "headers": dict(response.headers),
            }

        except requests.exceptions.Timeout:
            return {
                "response": f"Request timed out after {timeout}s",
                "status_code": 408,
                "headers": {},
            }
        except Exception as e:
            return {
                "response": f"Error: {str(e)}",
                "status_code": 500,
                "headers": {},
            }
