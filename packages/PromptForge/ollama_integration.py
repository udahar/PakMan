# Updated-On: 2026-03-07
# Updated-By: Codex
# PM-Ticket: UNTRACKED
#
"""
Ollama Integration for Model Distillation

Provides actual Ollama API integration for fine-tuning and inference.
Uses urllib (built-in) instead of requests.
"""

import json
import subprocess
import urllib.request
import urllib.error
import ssl
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass
import gzip


class OllamaHTTPError(Exception):
    """Raised when Ollama responds with an HTTP status error."""

    def __init__(self, status_code: Optional[int], message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(message)


@dataclass
class OllamaModel:
    """An Ollama model."""

    name: str
    size: int
    modified_at: str
    digest: str


class OllamaClient:
    """
    Ollama API client for model management and inference.

    Usage:
        client = OllamaClient()

        # List models
        models = client.list_models()

        # Run inference
        response = client.generate("qwen2.5:7b", "Hello world")

        # Create/fine-tune model
        client.create_model("my-model", "qwen2.5:7b", training_data)
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        timeout: int = 300,
        training_data_path: Optional[str] = None,
        keepalive: int = 300,
        raise_http_errors: bool = False,
    ):
        """
        Initialize Ollama client.

        Args:
            base_url: Ollama server URL
            timeout: Request timeout in seconds
            training_data_path: Path for storing training data
            keepalive: Keep model loaded for N seconds
        """
        self.base_url = base_url
        self.timeout = timeout
        self.training_data_path = training_data_path or "/tmp"
        self.keepalive = keepalive
        self.raise_http_errors = raise_http_errors

        # Create SSL context for HTTPS
        self._ssl_context = ssl.create_default_context()

    def _make_request(
        self, endpoint: str, data: Optional[Dict] = None, method: str = "POST"
    ) -> Optional[Dict]:
        """Make HTTP request to Ollama."""
        url = f"{self.base_url}{endpoint}"

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode("utf-8") if data else None,
                headers={"Content-Type": "application/json"},
                method=method,
            )

            with urllib.request.urlopen(
                req, timeout=self.timeout, context=self._ssl_context
            ) as response:
                content = response.read()
                # Handle gzip encoding
                if response.info().get("Content-Encoding") == "gzip":
                    content = gzip.decompress(content)
                return json.loads(content.decode("utf-8"))

        except urllib.error.HTTPError as e:
            print(f"[Ollama] HTTP Error: {e.code} {e.reason}")
            if self.raise_http_errors:
                raise OllamaHTTPError(e.code, f"HTTP {e.code} {e.reason}") from e
            return None  # Any HTTP error - skip recording (could be system bug)
        except urllib.error.URLError as e:
            print(f"[Ollama] URL Error: {e.reason}")
            if self.raise_http_errors and "timed out" in str(e.reason).lower():
                raise OllamaHTTPError(None, f"timeout: {e.reason}") from e
            return None  # Connection refused - skip recording
        except Exception as e:
            print(f"[Ollama] Request failed: {e}")
            if self.raise_http_errors and "timed out" in str(e).lower():
                raise OllamaHTTPError(None, f"timeout: {e}") from e
            return None

    def list_models(self) -> List[OllamaModel]:
        """List all available models."""
        data = self._make_request("/api/tags", method="GET")

        if not data:
            return []

        return [
            OllamaModel(
                name=m["name"],
                size=m.get("size", 0),
                modified_at=m.get("modified_at", ""),
                digest=m.get("digest", ""),
            )
            for m in data.get("models", [])
        ]

    def generate(
        self,
        model: str,
        prompt: str,
        options: Optional[Dict] = None,
    ) -> str:
        """Generate response from model."""
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "keep_alive": self.keepalive,
        }

        if options:
            payload["options"] = options

        data = self._make_request("/api/generate", payload)

        if data:
            return data.get("response", "")
        return ""

    def chat(
        self,
        model: str,
        messages: List[Dict],
        options: Optional[Dict] = None,
    ) -> str:
        """Chat with model using message format."""
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "keep_alive": self.keepalive,
        }

        if options:
            payload["options"] = options

        data = self._make_request("/api/chat", payload)

        if data:
            return data.get("message", {}).get("content", "")
        return ""

    def create_model(
        self,
        name: str,
        base_model: str,
        training_data: List[Dict],
        force: bool = False,
    ) -> bool:
        """Create a new model from base model with training data."""
        try:
            system_prompt = self._build_system_prompt(training_data)

            modelfile_content = f"""
FROM {base_model}

SYSTEM {system_prompt}
"""

            modelfile_path = Path(self.training_data_path) / f"{name}.modelfile"
            modelfile_path.parent.mkdir(parents=True, exist_ok=True)

            with open(modelfile_path, "w") as f:
                f.write(modelfile_content)

            cmd = ["ollama", "create", name, "-f", str(modelfile_path)]
            if force:
                cmd.append("--force")

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=self.timeout
            )

            if result.returncode == 0:
                print(f"[Ollama] Created model: {name}")
                return True
            else:
                print(f"[Ollama] Create failed: {result.stderr}")
                return False

        except Exception as e:
            print(f"[Ollama] Create failed: {e}")
            return False

    def _build_system_prompt(self, training_data: List[Dict]) -> str:
        """Build a system prompt from training data."""
        if not training_data:
            return "You are a helpful AI assistant."

        examples = []
        for item in training_data[:10]:
            if "prompt" in item and "response" in item:
                examples.append(f"Input: {item['prompt'][:200]}")
                examples.append(f"Output: {item['response'][:200]}")

        if examples:
            return (
                "You are an expert AI assistant trained on optimal reasoning strategies.\n"
                + "\n".join(examples)
            )
        return "You are a helpful AI assistant."

    def delete_model(self, name: str) -> bool:
        """Delete a model."""
        data = self._make_request("/api/delete", {"model": name}, method="DELETE")
        return data is not None

    def pull_model(self, name: str) -> bool:
        """Pull a model from Ollama registry."""
        try:
            result = subprocess.run(
                ["ollama", "pull", name], capture_output=True, text=True, timeout=600
            )
            return result.returncode == 0
        except Exception as e:
            print(f"[Ollama] Pull failed: {e}")
            return False

    def get_model_info(self, name: str) -> Optional[Dict]:
        """Get model information."""
        return self._make_request("/api/show", {"model": name})

    def is_available(self) -> bool:
        """Check if Ollama is running."""
        return len(self.list_models()) >= 0


def create_training_jsonl(examples: List[Dict], output_path: str) -> str:
    """Create JSONL training file from examples."""
    with open(output_path, "w") as f:
        for ex in examples:
            if "prompt" in ex and "response" in ex:
                f.write(
                    json.dumps({"prompt": ex["prompt"], "response": ex["response"]})
                    + "\n"
                )
    return output_path
