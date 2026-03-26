"""
CodeSandbox - sandbox.py
Safe subprocess-based code executor with timeout, output capture,
and a configurable block-list of dangerous patterns.

No Docker required for basic use. Docker mode is opt-in for full isolation.

Usage:
    from CodeSandbox import CodeSandbox

    sb = CodeSandbox()
    result = sb.run("print('Hello, world!')")
    print(result.stdout)   # Hello, world!
    print(result.ok)       # True
"""
import os
import re
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


# ── Safety ────────────────────────────────────────────────────────────────────

_DANGEROUS_PATTERNS = [
    r"\bos\.system\b",
    r"\bsubprocess\b",
    r"\bshutil\.rmtree\b",
    r"\bopen\s*\(.+['\"]w['\"]",   # file writes
    r"\b__import__\b",
    r"\bexec\s*\(",
    r"\beval\s*\(",
    r"import socket",
    r"import requests",
    r"import urllib",
    r"import ftplib",
    r"import smtplib",
    r"\.connect\s*\(",
]

_SAFE_IMPORTS = {
    "math", "random", "json", "re", "datetime", "collections",
    "itertools", "functools", "string", "uuid", "hashlib",
    "dataclasses", "typing", "enum", "pathlib",
}


@dataclass
class SandboxResult:
    stdout: str = ""
    stderr: str = ""
    exit_code: int = -1
    elapsed_ms: float = 0.0
    timed_out: bool = False
    blocked: bool = False
    block_reason: str = ""

    @property
    def ok(self) -> bool:
        return self.exit_code == 0 and not self.timed_out and not self.blocked

    def __str__(self) -> str:
        if self.blocked:
            return f"[BLOCKED] {self.block_reason}"
        if self.timed_out:
            return "[TIMEOUT]"
        return self.stdout or self.stderr or "(no output)"


class CodeSandbox:
    """
    Safe code executor for AI-generated code.

    Args:
        timeout:          Max seconds to run (default: 10).
        max_output_bytes: Truncate stdout/stderr beyond this size.
        allow_network:    If True, skip network import checks.
        strict:           If True, reject any import not in _SAFE_IMPORTS.
        docker_image:     If set, run inside this Docker image (requires Docker).
        env:              Extra env vars for the subprocess.
    """

    def __init__(
        self,
        timeout: float = 10.0,
        max_output_bytes: int = 16_384,
        allow_network: bool = False,
        strict: bool = False,
        docker_image: Optional[str] = None,
        env: Dict[str, str] = None,
    ):
        self.timeout = timeout
        self.max_output = max_output_bytes
        self.allow_network = allow_network
        self.strict = strict
        self.docker_image = docker_image
        self.env = {**os.environ, **(env or {})}

    def run(self, code: str, language: str = "python") -> SandboxResult:
        """
        Execute a code snippet safely.

        Args:
            code:     Source code string.
            language: "python" (default) | "bash" (unsafe without docker).

        Returns:
            SandboxResult with stdout, stderr, exit_code, elapsed_ms.
        """
        # Safety scan first
        blocked, reason = self._scan(code, language)
        if blocked:
            return SandboxResult(blocked=True, block_reason=reason)

        if self.docker_image:
            return self._run_docker(code, language)
        return self._run_subprocess(code, language)

    # ── Scanning ──────────────────────────────────────────────────────────────

    def _scan(self, code: str, language: str) -> tuple:
        if language != "python":
            if not self.docker_image:
                return True, "Non-Python code requires docker_image to be set."
            return False, ""

        for pattern in _DANGEROUS_PATTERNS:
            if not self.allow_network or "socket" not in pattern:
                if re.search(pattern, code):
                    return True, f"Blocked pattern: {pattern}"

        if self.strict:
            import_matches = re.findall(r"^\s*import\s+(\w+)", code, re.MULTILINE)
            from_matches = re.findall(r"^\s*from\s+(\w+)", code, re.MULTILINE)
            for mod in import_matches + from_matches:
                if mod not in _SAFE_IMPORTS:
                    return True, f"Strict mode: disallowed import '{mod}'"

        return False, ""

    # ── Subprocess execution ──────────────────────────────────────────────────

    def _run_subprocess(self, code: str, language: str) -> SandboxResult:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(code)
            tmp = f.name

        try:
            t0 = time.monotonic()
            proc = subprocess.run(
                [sys.executable, tmp],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env=self.env,
            )
            elapsed = (time.monotonic() - t0) * 1000
            return SandboxResult(
                stdout=proc.stdout[: self.max_output],
                stderr=proc.stderr[: self.max_output],
                exit_code=proc.returncode,
                elapsed_ms=round(elapsed, 1),
            )
        except subprocess.TimeoutExpired:
            return SandboxResult(timed_out=True, elapsed_ms=self.timeout * 1000)
        except Exception as e:
            return SandboxResult(stderr=str(e), exit_code=-1)
        finally:
            try:
                Path(tmp).unlink()
            except Exception:
                pass

    # ── Docker execution (opt-in) ─────────────────────────────────────────────

    def _run_docker(self, code: str, language: str) -> SandboxResult:
        ext = ".py" if language == "python" else ".sh"
        interp = "python3" if language == "python" else "bash"

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=ext, delete=False, encoding="utf-8"
        ) as f:
            f.write(code)
            tmp = f.name

        try:
            t0 = time.monotonic()
            proc = subprocess.run(
                [
                    "docker", "run", "--rm",
                    "--network", "none",
                    "--memory", "128m",
                    "--cpus", "0.5",
                    "-v", f"{tmp}:/sandbox/code{ext}:ro",
                    self.docker_image,
                    interp, f"/sandbox/code{ext}",
                ],
                capture_output=True, text=True, timeout=self.timeout + 5,
            )
            elapsed = (time.monotonic() - t0) * 1000
            return SandboxResult(
                stdout=proc.stdout[: self.max_output],
                stderr=proc.stderr[: self.max_output],
                exit_code=proc.returncode,
                elapsed_ms=round(elapsed, 1),
            )
        except subprocess.TimeoutExpired:
            return SandboxResult(timed_out=True)
        except FileNotFoundError:
            return SandboxResult(blocked=True, block_reason="Docker not found on PATH")
        finally:
            try:
                Path(tmp).unlink()
            except Exception:
                pass
