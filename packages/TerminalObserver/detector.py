"""
TerminalObserver - detector.py
Scans terminal output (text streams) for Python tracebacks, syntax errors,
and common runtime failures. Returns structured ErrorCapture objects.
"""
import re
from dataclasses import dataclass, field
from typing import List, Optional


# ── Patterns ────────────────────────────────────────────────────────────────

_TRACEBACK_START = re.compile(r"Traceback \(most recent call last\):")
_EXCEPTION_LINE = re.compile(r"^(\w+(?:\.\w+)*Error|Exception|Warning|KeyboardInterrupt)[:\s]")
_FILE_LINE = re.compile(r'File "(.+)", line (\d+)')
_SYNTAX_ERROR = re.compile(r"SyntaxError: (.+)")
_MODULE_NOT_FOUND = re.compile(r"ModuleNotFoundError: No module named '(.+)'")
_TYPE_ERROR = re.compile(r"TypeError: (.+)")
_ATTRIBUTE_ERROR = re.compile(r"AttributeError: (.+)")
_VALUE_ERROR = re.compile(r"ValueError: (.+)")
_NAME_ERROR = re.compile(r"NameError: name '(.+)' is not defined")
_CONNECTION_ERROR = re.compile(r"(ConnectionRefusedError|ConnectionError): (.+)")
_PORT_IN_USE = re.compile(r"address already in use|OSError: \[Errno 98\]|WinError 10048", re.IGNORECASE)


@dataclass
class FrameInfo:
    filepath: str
    lineno: int


@dataclass
class ErrorCapture:
    """Structured representation of a captured terminal error."""
    error_type: str           # e.g. "ModuleNotFoundError"
    message: str              # The actual error message
    frames: List[FrameInfo] = field(default_factory=list)
    raw: str = ""             # Full raw traceback text
    context: str = ""         # Surrounding context lines

    @property
    def primary_file(self) -> Optional[str]:
        return self.frames[-1].filepath if self.frames else None

    @property
    def primary_line(self) -> Optional[int]:
        return self.frames[-1].lineno if self.frames else None

    def __str__(self) -> str:
        loc = f"{self.primary_file}:{self.primary_line}" if self.primary_file else "?"
        return f"[{self.error_type}] {self.message} @ {loc}"


def detect_errors(text: str) -> List[ErrorCapture]:
    """
    Scan terminal output text for any number of Python errors/tracebacks.

    Args:
        text: Raw terminal output string.

    Returns:
        List of ErrorCapture objects (empty if no errors found).
    """
    captures = []
    lines = text.splitlines()
    i = 0

    while i < len(lines):
        line = lines[i]

        if _TRACEBACK_START.search(line):
            # Collect entire traceback block
            block_lines = [line]
            i += 1
            while i < len(lines) and lines[i].strip():
                block_lines.append(lines[i])
                i += 1
            capture = _parse_traceback("\n".join(block_lines))
            if capture:
                captures.append(capture)
            continue

        # Detect bare errors (no full traceback)
        for pattern, err_type in [
            (_SYNTAX_ERROR, "SyntaxError"),
            (_MODULE_NOT_FOUND, "ModuleNotFoundError"),
            (_PORT_IN_USE, "OSError"),
        ]:
            m = pattern.search(line)
            if m:
                captures.append(ErrorCapture(
                    error_type=err_type,
                    message=m.group(1) if m.lastindex else line.strip(),
                    raw=line,
                ))
                break

        i += 1

    return captures


def _parse_traceback(block: str) -> Optional[ErrorCapture]:
    """Parse a single traceback block into an ErrorCapture."""
    lines = block.splitlines()
    frames = []
    error_type = "Exception"
    message = ""

    for line in lines:
        fm = _FILE_LINE.search(line)
        if fm:
            frames.append(FrameInfo(filepath=fm.group(1), lineno=int(fm.group(2))))

    # Last non-empty line is usually "ErrorType: message"
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        colon = line.find(":")
        if colon > 0:
            error_type = line[:colon].strip()
            message = line[colon + 1:].strip()
        else:
            error_type = line
        break

    if not error_type:
        return None

    return ErrorCapture(
        error_type=error_type,
        message=message,
        frames=frames,
        raw=block,
    )
