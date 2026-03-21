# Updated-On: 2026-03-08
# Updated-By: Codex
# PM-Ticket: UNTRACKED

"""
Advanced Tool Types
SQL, API, File operations, and more
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
import json
import subprocess
import requests


@dataclass
class SQLToolConfig:
    """SQL tool configuration."""

    connection_string: str
    query_template: str
    timeout: int = 30


class SQLTool:
    """Execute SQL queries."""

    def __init__(self, config: SQLToolConfig):
        self.config = config
        self._conn = None

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute SQL query."""
        try:
            import psycopg2

            conn = psycopg2.connect(self.config.connection_string)
            cursor = conn.cursor()

            query = self.config.query_template.format(**params)
            cursor.execute(query)

            if query.strip().upper().startswith("SELECT"):
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                result = {"columns": columns, "rows": rows, "row_count": len(rows)}
            else:
                conn.commit()
                result = {"affected_rows": cursor.rowcount}

            cursor.close()
            conn.close()

            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": str(e)}


class HTTPAPITool:
    """Execute HTTP API calls."""

    def __init__(
        self,
        base_url: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 30,
    ):
        self.base_url = base_url
        self.method = method.upper()
        self.headers = headers or {}
        self.timeout = timeout

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute HTTP request."""
        try:
            url = self.base_url.format(**params)

            response = requests.request(
                method=self.method,
                url=url,
                headers=self.headers,
                timeout=self.timeout,
                json=params.get("body"),
            )

            return {
                "success": True,
                "status_code": response.status_code,
                "data": response.json()
                if response.headers.get("content-type", "").startswith(
                    "application/json"
                )
                else response.text,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


class FileTool:
    """File operations tool."""

    def __init__(self, base_path: str = "."):
        self.base_path = base_path

    def read(self, file_path: str) -> Dict[str, Any]:
        """Read file."""
        try:
            full_path = f"{self.base_path}/{file_path}"
            with open(full_path, "r") as f:
                content = f.read()
            return {"success": True, "content": content}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def write(self, file_path: str, content: str) -> Dict[str, Any]:
        """Write file."""
        try:
            full_path = f"{self.base_path}/{file_path}"
            with open(full_path, "w") as f:
                f.write(content)
            return {"success": True, "path": full_path}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list(self, directory: str = ".") -> Dict[str, Any]:
        """List directory."""
        try:
            import os

            full_path = f"{self.base_path}/{directory}"
            files = os.listdir(full_path)
            return {"success": True, "files": files}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def exists(self, file_path: str) -> bool:
        """Check if file exists."""
        import os

        return os.path.exists(f"{self.base_path}/{file_path}")


class SearchTool:
    """Web search tool."""

    def __init__(self, engine: str = "duckduckgo"):
        self.engine = engine

    def search(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Perform web search."""
        try:
            if self.engine == "duckduckgo":
                from duckduckgo_search import DDGS

                ddgs = DDGS()
                results = ddgs.text(query, max_results=limit)

                return {
                    "success": True,
                    "results": [
                        {"title": r.title, "url": r.url, "body": r.body}
                        for r in results
                    ],
                }
            elif self.engine == "serpapi":
                params = {"q": query, "num": limit, "api_key": os.getenv("SERPAPI_KEY")}
                response = requests.get("https://serpapi.com/search", params=params)
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": f"Unknown engine: {self.engine}"}
        except Exception as e:
            return {"success": False, "error": str(e)}


class WebFetchTool:
    """Fetch web pages."""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    def fetch(self, url: str) -> Dict[str, Any]:
        """Fetch URL content."""
        try:
            response = requests.get(url, timeout=self.timeout)

            return {
                "success": True,
                "status_code": response.status_code,
                "content": response.text[:10000],
                "content_type": response.headers.get("content-type", ""),
                "url": response.url,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def fetch_json(self, url: str) -> Dict[str, Any]:
        """Fetch JSON from URL."""
        try:
            response = requests.get(url, timeout=self.timeout)
            return {"success": True, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}


class CalculatorTool:
    """Mathematical calculations."""

    def __init__(self):
        self.operators = {
            "add": lambda a, b: a + b,
            "subtract": lambda a, b: a - b,
            "multiply": lambda a, b: a * b,
            "divide": lambda a, b: a / b if b != 0 else None,
            "power": lambda a, b: a**b,
            "mod": lambda a, b: a % b,
            "sqrt": lambda a, **_: a**0.5,
            "abs": lambda a, **_: abs(a),
            "round": lambda a, decimals=0: round(a, decimals),
        }

    def calculate(
        self, operation: str, a: float, b: Optional[float] = None, **kwargs
    ) -> Dict[str, Any]:
        """Perform calculation."""
        try:
            if operation not in self.operators:
                return {"success": False, "error": f"Unknown operation: {operation}"}

            if operation in ["sqrt", "abs", "round"]:
                result = self.operators[operation](a, **kwargs)
            elif b is not None:
                result = self.operators[operation](a, b)
            else:
                return {"success": False, "error": "Missing operand b"}

            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def evaluate(self, expression: str) -> Dict[str, Any]:
        """Evaluate mathematical expression."""
        try:
            allowed_names = {
                "add": (lambda a, b: a + b, 2),
                "sub": (lambda a, b: a - b, 2),
                "mul": (lambda a, b: a * b, 2),
                "div": (lambda a, b: a / b, 2),
                "sqrt": (lambda a: a**0.5, 1),
                "abs": (lambda a: abs(a), 1),
                "sin": (lambda a: __import__("math").sin(a), 1),
                "cos": (lambda a: __import__("math").cos(a), 1),
                "tan": (lambda a: __import__("math").tan(a), 1),
                "log": (lambda a: __import__("math").log(a), 1),
            }

            result = eval(expression, {"__builtins__": {}}, allowed_names)
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}


class JSONTool:
    """JSON manipulation tool."""

    def parse(self, text: str) -> Dict[str, Any]:
        """Parse JSON string."""
        try:
            return {"success": True, "data": json.loads(text)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def stringify(self, data: Any, indent: int = 2) -> Dict[str, Any]:
        """Stringify to JSON."""
        try:
            return {"success": True, "data": json.dumps(data, indent=indent)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def query(self, json_data: Any, path: str) -> Dict[str, Any]:
        """Query JSON with path."""
        try:
            current = json_data
            for key in path.split("."):
                if isinstance(current, dict):
                    current = current.get(key)
                elif isinstance(current, list) and key.isdigit():
                    current = current[int(key)]
                else:
                    return {"success": False, "error": f"Path not found: {key}"}

            return {"success": True, "data": current}
        except Exception as e:
            return {"success": False, "error": str(e)}
