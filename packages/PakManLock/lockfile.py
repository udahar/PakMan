"""
PakMan-Lock - lockfile.py
Prompt lockfile format — stores hashed, pinned prompt templates.

Analogous to requirements.txt for packages, but for prompts.
A .paklock file is human-readable JSONL. One entry per locked prompt.

Format per entry:
    {
        "id":       "auth_reviewer",        # logical prompt name
        "hash":     "sha256:abcdef1234...", # content hash
        "version":  "1.0.0",               # semver
        "template": "You are a code reviewer who checks for auth flaws...",
        "created":  "2026-03-25T...",
        "tags":     ["security", "code_review"],
        "frozen":   true                    # if frozen, changes raise LockedPromptError
    }
"""
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


def _hash(content: str) -> str:
    return "sha256:" + hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


@dataclass
class LockedPrompt:
    id: str
    template: str
    version: str = "1.0.0"
    hash: str = ""
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    tags: List[str] = field(default_factory=list)
    frozen: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.hash:
            self.hash = _hash(self.template)

    def verify(self) -> bool:
        """Check that the template hasn't been tampered with."""
        return self.hash == _hash(self.template)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "hash": self.hash,
            "version": self.version,
            "template": self.template,
            "created": self.created,
            "tags": self.tags,
            "frozen": self.frozen,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "LockedPrompt":
        return cls(
            id=d["id"],
            template=d["template"],
            version=d.get("version", "1.0.0"),
            hash=d.get("hash", ""),
            created=d.get("created", datetime.utcnow().isoformat()),
            tags=d.get("tags", []),
            frozen=d.get("frozen", True),
            metadata=d.get("metadata", {}),
        )


class LockedPromptError(Exception):
    """Raised when a frozen prompt is modified without unlocking first."""


class LockFile:
    """
    Read/write a .paklock file.

    Usage:
        lf = LockFile("prompts.paklock")
        lf.lock("auth_reviewer", "You are a code reviewer...", tags=["security"])
        lf.save()

        # Later...
        lf = LockFile("prompts.paklock")
        prompt = lf.get("auth_reviewer")
        print(prompt.template)
    """

    def __init__(self, path: str = "prompts.paklock"):
        self.path = Path(path)
        self._prompts: Dict[str, LockedPrompt] = {}
        if self.path.exists():
            self._load()

    def _load(self):
        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                p = LockedPrompt.from_dict(d)
                self._prompts[p.id] = p
            except Exception:
                pass

    def save(self) -> None:
        """Write all locked prompts back to disk."""
        lines = [json.dumps(p.to_dict(), ensure_ascii=False) for p in self._prompts.values()]
        self.path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def lock(
        self,
        prompt_id: str,
        template: str,
        version: str = "1.0.0",
        tags: List[str] = None,
        frozen: bool = True,
        **metadata,
    ) -> LockedPrompt:
        """Add or replace a prompt in the lockfile."""
        p = LockedPrompt(
            id=prompt_id,
            template=template,
            version=version,
            tags=tags or [],
            frozen=frozen,
            metadata=metadata,
        )
        self._prompts[prompt_id] = p
        return p

    def get(self, prompt_id: str) -> Optional[LockedPrompt]:
        return self._prompts.get(prompt_id)

    def verify_all(self) -> Dict[str, bool]:
        """Verify integrity of all stored prompts. Returns {id: ok}."""
        return {pid: p.verify() for pid, p in self._prompts.items()}

    def list(self) -> List[LockedPrompt]:
        return list(self._prompts.values())

    def unfreeze(self, prompt_id: str) -> None:
        if prompt_id in self._prompts:
            self._prompts[prompt_id].frozen = False

    def freeze(self, prompt_id: str) -> None:
        p = self._prompts.get(prompt_id)
        if p:
            p.frozen = True
            p.hash = _hash(p.template)
