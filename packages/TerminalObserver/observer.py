"""
TerminalObserver - observer.py
Main orchestrator: wraps a shell subprocess, pipes its output,
detects errors, gets fixes, and puts them on the clipboard.

Usage:
    from TerminalObserver import TerminalObserver

    obs = TerminalObserver(llm=my_llm)
    obs.run(["python", "my_script.py"])

    # Or watch a live command
    obs.watch("npm run dev")
"""
import subprocess
import sys
import threading
from typing import Callable, List, Optional, Union

from .detector import detect_errors, ErrorCapture
from .advisor import get_fix


def _to_clipboard(text: str) -> bool:
    """Copy text to clipboard. Returns True if successful."""
    try:
        import subprocess as sp
        # Windows
        proc = sp.Popen(["clip"], stdin=sp.PIPE, shell=True)
        proc.communicate(input=text.encode("utf-8"))
        return True
    except Exception:
        pass
    try:
        # macOS
        import subprocess as sp
        proc = sp.Popen(["pbcopy"], stdin=sp.PIPE)
        proc.communicate(input=text.encode("utf-8"))
        return True
    except Exception:
        pass
    try:
        # Linux (xclip)
        import subprocess as sp
        proc = sp.Popen(["xclip", "-selection", "clipboard"], stdin=sp.PIPE)
        proc.communicate(input=text.encode("utf-8"))
        return True
    except Exception:
        return False


class TerminalObserver:
    """
    Wraps any subprocess command, monitors its output for errors,
    and proactively suggests fixes via clipboard or stdout.

    Args:
        llm:            Optional fn(prompt) -> str for LLM-backed fixes.
        copy_to_clipboard: If True, copies fix suggestion to clipboard.
        print_fix:      If True, prints fix to stdout inline.
        on_error:       Optional callback fn(error, fix) for custom handling.
    """

    def __init__(
        self,
        llm: Optional[Callable] = None,
        copy_to_clipboard: bool = True,
        print_fix: bool = True,
        on_error: Optional[Callable] = None,
    ):
        self.llm = llm
        self.copy_to_clipboard = copy_to_clipboard
        self.print_fix = print_fix
        self.on_error = on_error
        self.captured_errors: List[ErrorCapture] = []

    def run(self, cmd: Union[str, List[str]], **kwargs) -> int:
        """
        Run a command and observe its output for errors.

        Args:
            cmd:    Command string or list (e.g. ["python", "app.py"]).
            kwargs: Extra arguments passed to subprocess.Popen.

        Returns:
            Process return code.
        """
        if isinstance(cmd, str):
            kwargs.setdefault("shell", True)

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            **kwargs,
        )

        output_lines = []

        for line in proc.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
            output_lines.append(line)

            # Check the last 40 lines rolling window
            window = "".join(output_lines[-40:])
            errors = detect_errors(window)
            new_errors = [e for e in errors if e not in self.captured_errors]

            for error in new_errors:
                self.captured_errors.append(error)
                self._handle_error(error)

        proc.wait()
        return proc.returncode

    def feed(self, text: str) -> List[ErrorCapture]:
        """
        Feed raw terminal text directly (for piped or captured output).
        Returns newly detected errors.
        """
        errors = detect_errors(text)
        new_errors = [e for e in errors if str(e) not in {str(x) for x in self.captured_errors}]
        for e in new_errors:
            self.captured_errors.append(e)
            self._handle_error(e)
        return new_errors

    def _handle_error(self, error: ErrorCapture) -> None:
        fix = get_fix(error, llm=self.llm)

        if self.print_fix:
            print(f"\n{'─'*55}")
            print(f"🔍 TerminalObserver detected: {error.error_type}")
            print(f"   {error.message}")
            if error.primary_file:
                print(f"   @ {error.primary_file}:{error.primary_line}")
            print(f"💡 Fix: {fix}")
            print(f"{'─'*55}\n")

        if self.copy_to_clipboard:
            copied = _to_clipboard(fix)
            if copied and self.print_fix:
                print("   📋 Fix copied to clipboard.")

        if self.on_error:
            try:
                self.on_error(error, fix)
            except Exception:
                pass
