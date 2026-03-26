"""
EnvSyncer - syncer.py
Captures, persists, and restores agent environment state across sessions.

"Environment" means the combined execution context that makes an agent session
reproducible: working directory, env vars, active files, pip packages,
Python version, and arbitrary agent-specific config blobs.

Usage:
    from EnvSyncer import EnvSyncer

    # Save current environment
    env = EnvSyncer()
    env.snapshot("my_project")
    env.save()

    # Later, in a new session
    env = EnvSyncer()
    state = env.load("my_project")
    print(state.working_dir)
    print(state.env_vars["DATABASE_URL"])
"""
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class EnvState:
    """Complete captured environment state."""
    name: str
    captured_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    working_dir: str = ""
    python_version: str = ""
    platform: str = ""
    env_vars: Dict[str, str] = field(default_factory=dict)
    packages: List[str] = field(default_factory=list)    # pip freeze output lines
    active_files: List[str] = field(default_factory=list) # recently modified files
    config: Dict[str, Any] = field(default_factory=dict) # agent-specific blobs

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "captured_at": self.captured_at,
            "working_dir": self.working_dir,
            "python_version": self.python_version,
            "platform": self.platform,
            "env_vars": self.env_vars,
            "packages": self.packages,
            "active_files": self.active_files,
            "config": self.config,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "EnvState":
        return cls(
            name=d["name"],
            captured_at=d.get("captured_at", datetime.utcnow().isoformat()),
            working_dir=d.get("working_dir", ""),
            python_version=d.get("python_version", ""),
            platform=d.get("platform", ""),
            env_vars=d.get("env_vars", {}),
            packages=d.get("packages", []),
            active_files=d.get("active_files", []),
            config=d.get("config", {}),
        )


# Keys excluded from env var capture (security / noise)
_ENV_EXCLUDE = {
    "PATH", "PATHEXT", "PROMPT", "PS1", "PS2", "TERM",
    "COLORTERM", "SHELL", "SHLVL", "OLDPWD", "_",
    "LS_COLORS", "LSCOLORS",
}

_SENSITIVE_PREFIXES = (
    "AWS_SECRET", "OPENAI_API_KEY", "STRIPE_SECRET",
    "DATABASE_URL", "REDIS_URL", "PRIVATE_KEY",
)


class EnvSyncer:
    """
    Captures and restores agent environment state.

    Args:
        store_path:     Path to the JSONL state store (default: "env_states.jsonl").
        capture_env:    If True, capture current environment variables.
        capture_pkgs:   If True, run pip freeze to capture installed packages.
        redact_secrets: If True, redact sensitive env var values before storing.
    """

    def __init__(
        self,
        store_path: str = "env_states.jsonl",
        capture_env: bool = True,
        capture_pkgs: bool = True,
        redact_secrets: bool = True,
    ):
        self.store_path = Path(store_path)
        self.capture_env = capture_env
        self.capture_pkgs = capture_pkgs
        self.redact_secrets = redact_secrets
        self._states: Dict[str, EnvState] = {}
        if self.store_path.exists():
            self._load_all()

    # ── Capture ───────────────────────────────────────────────────────────────

    def snapshot(
        self,
        name: str,
        config: Dict[str, Any] = None,
        active_files: List[str] = None,
    ) -> EnvState:
        """
        Capture the current environment into a named state.

        Args:
            name:         Unique state name (e.g., "research_session_v2").
            config:       Optional agent-specific key/values to store.
            active_files: Optional list of file paths to record.

        Returns:
            The captured EnvState.
        """
        state = EnvState(
            name=name,
            working_dir=os.getcwd(),
            python_version=sys.version,
            platform=sys.platform,
            config=config or {},
            active_files=active_files or self._recent_files(),
        )

        if self.capture_env:
            state.env_vars = self._capture_env()

        if self.capture_pkgs:
            state.packages = self._capture_packages()

        self._states[name] = state
        print(f"[EnvSyncer] Snapshot '{name}' captured at {state.captured_at}")
        return state

    # ── Persistence ───────────────────────────────────────────────────────────

    def save(self) -> None:
        """Persist all states to the store file."""
        lines = [json.dumps(s.to_dict(), ensure_ascii=False)
                 for s in self._states.values()]
        self.store_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"[EnvSyncer] Saved {len(lines)} state(s) → {self.store_path}")

    def load(self, name: str) -> Optional[EnvState]:
        """Load a named state from the store."""
        return self._states.get(name)

    def list(self) -> List[str]:
        return list(self._states.keys())

    def delete(self, name: str) -> None:
        self._states.pop(name, None)

    # ── Restore ───────────────────────────────────────────────────────────────

    def restore_cwd(self, name: str) -> bool:
        """Change working directory to the saved state's working_dir."""
        state = self.load(name)
        if state and state.working_dir:
            try:
                os.chdir(state.working_dir)
                print(f"[EnvSyncer] Restored cwd → {state.working_dir}")
                return True
            except OSError as e:
                print(f"[EnvSyncer] Could not restore cwd: {e}")
        return False

    def restore_env(self, name: str, overwrite: bool = False) -> None:
        """Inject saved env vars into the current process environment."""
        state = self.load(name)
        if not state:
            return
        for k, v in state.env_vars.items():
            if overwrite or k not in os.environ:
                os.environ[k] = v
        print(f"[EnvSyncer] Restored {len(state.env_vars)} env vars from '{name}'")

    def diff(self, name_a: str, name_b: str) -> dict:
        """Compare two snapshots and return differences."""
        a = self.load(name_a)
        b = self.load(name_b)
        if not a or not b:
            return {}
        keys_a = set(a.env_vars)
        keys_b = set(b.env_vars)
        return {
            "only_in_a": sorted(keys_a - keys_b),
            "only_in_b": sorted(keys_b - keys_a),
            "changed": sorted(
                k for k in keys_a & keys_b if a.env_vars[k] != b.env_vars[k]
            ),
            "dir_a": a.working_dir,
            "dir_b": b.working_dir,
            "pkg_diff": sorted(
                set(a.packages) ^ set(b.packages)
            )[:20],
        }

    # ── Internals ─────────────────────────────────────────────────────────────

    def _load_all(self):
        for line in self.store_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                s = EnvState.from_dict(d)
                self._states[s.name] = s
            except Exception:
                pass

    def _capture_env(self) -> Dict[str, str]:
        captured = {}
        for k, v in os.environ.items():
            if k in _ENV_EXCLUDE:
                continue
            if self.redact_secrets and any(
                k.upper().startswith(p) for p in _SENSITIVE_PREFIXES
            ):
                v = "[REDACTED]"
            captured[k] = v
        return captured

    def _capture_packages(self) -> List[str]:
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "freeze"],
                capture_output=True, text=True, timeout=15
            )
            return result.stdout.splitlines()
        except Exception:
            return []

    def _recent_files(self, cwd: str = None, limit: int = 20) -> List[str]:
        """Return recently modified Python files in the current directory."""
        base = Path(cwd or os.getcwd())
        try:
            files = sorted(
                base.rglob("*.py"),
                key=lambda f: f.stat().st_mtime,
                reverse=True,
            )
            return [str(f) for f in files[:limit]]
        except Exception:
            return []
