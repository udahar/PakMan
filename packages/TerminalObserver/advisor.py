"""
TerminalObserver - advisor.py
Converts an ErrorCapture into a fix suggestion.
Uses heuristic rules-first for speed; falls back to an LLM if provided.
"""
from typing import Callable, Optional
from .detector import ErrorCapture

# ── Rule-based quick responses ────────────────────────────────────────────────

_RULES = [
    (
        "ModuleNotFoundError",
        lambda e: "pip install " + e.message.replace("No module named ", "").strip("'"),
    ),
    (
        "SyntaxError",
        lambda e: f"Check {e.primary_file}:{e.primary_line} for a syntax error: {e.message}",
    ),
    (
        "OSError",
        lambda e: (
            "A port is already in use. Try: "
            "`netstat -ano | findstr :PORT` then `taskkill /PID <pid> /F`"
            if "in use" in e.message.lower() or "10048" in e.raw or "98" in e.raw
            else f"OS error: {e.message}"
        ),
    ),
    (
        "NameError",
        lambda e: f"Variable {e.message} — check spelling or import at {e.primary_file}:{e.primary_line}",
    ),
    (
        "AttributeError",
        lambda e: f"Check that the object has the attribute: {e.message}",
    ),
    (
        "KeyError",
        lambda e: f"Missing key {e.message} — use .get() or verify the key exists.",
    ),
    (
        "ConnectionRefusedError",
        lambda e: "Service is not running. Start it, or check the host/port.",
    ),
    (
        "FileNotFoundError",
        lambda e: f"File not found: {e.message}. Verify the path is correct.",
    ),
    (
        "IndentationError",
        lambda e: f"Indentation error at {e.primary_file}:{e.primary_line}. Check your tabs/spaces.",
    ),
    (
        "TypeError",
        lambda e: f"Type mismatch: {e.message}. At {e.primary_file}:{e.primary_line}.",
    ),
]


def get_fix(
    error: ErrorCapture,
    llm: Optional[Callable] = None,
) -> str:
    """
    Return a fix suggestion for the given error.

    1. Quickly checks rule-based responses (no LLM cost).
    2. Falls back to LLM with a focused prompt if provided.

    Args:
        error: Parsed ErrorCapture.
        llm:   Optional fn(prompt) -> str for LLM-backed suggestions.

    Returns:
        A plain-text fix suggestion string.
    """
    # Rule-based first
    for err_type, rule_fn in _RULES:
        if err_type.lower() in error.error_type.lower():
            try:
                return rule_fn(error)
            except Exception:
                break

    # LLM fallback
    if llm:
        return _llm_fix(error, llm)

    return f"Unknown error: {error.error_type}: {error.message}"


def _llm_fix(error: ErrorCapture, llm: Callable) -> str:
    """Ask the LLM for a concise fix. Minimize token usage."""
    context = error.raw[:600].strip() if error.raw else str(error)
    prompt = (
        f"Python error in '{error.primary_file or 'unknown'}':\n\n"
        f"{context}\n\n"
        "Give ONE short, specific fix (max 2 sentences). No code blocks, just plain text."
    )
    try:
        return str(llm(prompt)).strip()
    except Exception as e:
        return f"(LLM suggestion failed: {e})"
