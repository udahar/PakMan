"""
ApprovalGate - registry.py
Registry of flagged operation patterns that require approval.
"""
import re
from typing import List

# Default flagged patterns
DEFAULT_PATTERNS = [
    # File system
    r"\brm\b",
    r"shutil\.rmtree",
    r"os\.unlink",
    r"os\.remove",
    r"Path\.unlink",
    # Git
    r"git push",
    r"git reset --hard",
    r"git clean -f",
    # Subprocess / Shell
    r"subprocess\.run.*shell=True",
    r"os\.system",
    # API / Network
    r"stripe\.",
    r"requests\.post.*api",
    r"send_email",
    r"bulk_send",
    # Database
    r"DROP TABLE",
    r"DELETE FROM",
    r"TRUNCATE",
]


class FlaggedOperationRegistry:
    """Maintains a list of regex patterns for operations requiring approval."""

    def __init__(self, patterns: List[str] = None):
        self._patterns = [re.compile(p, re.IGNORECASE)
                          for p in (patterns or DEFAULT_PATTERNS)]

    def add(self, pattern: str) -> None:
        self._patterns.append(re.compile(pattern, re.IGNORECASE))

    def remove(self, pattern: str) -> None:
        self._patterns = [p for p in self._patterns
                          if p.pattern != pattern]

    def is_flagged(self, action: str) -> bool:
        return any(p.search(action) for p in self._patterns)

    def list_patterns(self) -> List[str]:
        return [p.pattern for p in self._patterns]
