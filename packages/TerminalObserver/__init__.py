"""
TerminalObserver
Proactive dev-terminal error daemon. Zero external dependencies.

Wraps any subprocess, detects Python errors in real-time, suggests fixes,
and copies them to your clipboard before you can even switch windows.

Quick start:
    from TerminalObserver import TerminalObserver

    # Basic — heuristic fixes only
    obs = TerminalObserver()
    obs.run(["python", "app.py"])

    # With LLM-backed fixes
    from my_llm import call_llm
    obs = TerminalObserver(llm=call_llm)
    obs.run("python app.py")

    # Feed captured terminal output directly
    obs = TerminalObserver(copy_to_clipboard=False, print_fix=True)
    errors = obs.feed(some_terminal_output_string)

    # Custom error callback
    def on_err(error, fix):
        send_to_slack(f"Error in CI: {error}\\nFix: {fix}")

    obs = TerminalObserver(on_error=on_err)
    obs.run(["pytest", "tests/"])

Detected error types:
    ModuleNotFoundError, SyntaxError, TypeError, AttributeError,
    NameError, KeyError, ValueError, ConnectionRefusedError,
    FileNotFoundError, IndentationError, OSError (port in use), and more.
"""
from .observer import TerminalObserver
from .detector import detect_errors, ErrorCapture, FrameInfo
from .advisor import get_fix

__version__ = "0.1.0"
__all__ = [
    "TerminalObserver",
    "detect_errors",
    "ErrorCapture",
    "FrameInfo",
    "get_fix",
]
