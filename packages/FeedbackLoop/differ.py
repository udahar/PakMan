"""
FeedbackLoop - differ.py
Computes a structured diff between original AI output and human edit.
"""
import difflib
from dataclasses import dataclass, field
from typing import List


@dataclass
class DiffResult:
    filepath: str
    added: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)
    context: str = ""
    change_ratio: float = 0.0

    @property
    def is_meaningful(self) -> bool:
        """True if the human changed more than just whitespace."""
        return bool(self.added or self.removed)


def compute_diff(filepath: str, original: str, modified: str) -> DiffResult:
    """
    Produce a structured diff between original AI output and the human edit.
    """
    orig_lines = original.splitlines()
    mod_lines = modified.splitlines()

    diff = list(difflib.unified_diff(orig_lines, mod_lines, n=2))

    added = [l[1:] for l in diff if l.startswith("+") and not l.startswith("+++")]
    removed = [l[1:] for l in diff if l.startswith("-") and not l.startswith("---")]

    total = max(len(orig_lines), 1)
    ratio = len(added + removed) / (2 * total)

    context_lines = [l for l in diff if l.startswith(" ")][:5]
    context = "\n".join(context_lines)

    return DiffResult(
        filepath=filepath,
        added=added,
        removed=removed,
        context=context,
        change_ratio=ratio,
    )
