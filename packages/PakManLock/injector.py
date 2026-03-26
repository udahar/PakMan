"""
PakMan-Lock - injector.py
Safe prompt variable injection — fills a locked template's {variables}
while raising on integrity violations.

Usage:
    from PakManLock import PakManLock

    lock = PakManLock()
    lock.lock("summarizer", "Summarize the following for {audience}: {text}")
    lock.save()

    prompt = lock.render("summarizer", audience="executives", text=doc)
"""
import re
from typing import Any, Dict, Optional
from .lockfile import LockFile, LockedPrompt, LockedPromptError


_VAR_PATTERN = re.compile(r"\{(\w+)\}")


class PakManLock:
    """
    High-level API for PakMan-Lock.

    Wraps a LockFile and provides safe template rendering.
    Renders are hash-validated before injection to detect drift.
    """

    def __init__(self, lockfile_path: str = "prompts.paklock"):
        self._lf = LockFile(lockfile_path)

    # ── Authoring ─────────────────────────────────────────────────────────────

    def lock(self, prompt_id: str, template: str, **kwargs) -> LockedPrompt:
        """Lock a new prompt template."""
        p = self._lf.lock(prompt_id, template, **kwargs)
        print(f"[PakMan-Lock] Locked '{prompt_id}' ({p.hash})")
        return p

    def save(self) -> None:
        self._lf.save()
        print(f"[PakMan-Lock] Saved → {self._lf.path}")

    def unfreeze(self, prompt_id: str) -> None:
        self._lf.unfreeze(prompt_id)
        print(f"[PakMan-Lock] Unfrozen '{prompt_id}'")

    def freeze(self, prompt_id: str) -> None:
        self._lf.freeze(prompt_id)
        print(f"[PakMan-Lock] Frozen '{prompt_id}'")

    # ── Rendering ─────────────────────────────────────────────────────────────

    def render(self, prompt_id: str, **variables: Any) -> str:
        """
        Safely render a locked prompt template with variable substitution.

        1. Retrieves the locked prompt
        2. Verifies its hash hasn't changed
        3. Injects variables
        4. Returns the rendered prompt string

        Raises:
            KeyError if prompt_id not found.
            LockedPromptError if the template was tampered with.
            ValueError if required variables are missing.
        """
        prompt = self._lf.get(prompt_id)
        if prompt is None:
            raise KeyError(f"[PakMan-Lock] Unknown prompt: '{prompt_id}'")

        if prompt.frozen and not prompt.verify():
            raise LockedPromptError(
                f"[PakMan-Lock] Integrity check FAILED for '{prompt_id}'. "
                f"Hash mismatch — template was modified without unlocking."
            )

        # Find required variables
        required = set(_VAR_PATTERN.findall(prompt.template))
        missing = required - set(variables.keys())
        if missing:
            raise ValueError(
                f"[PakMan-Lock] Missing variables for '{prompt_id}': {missing}"
            )

        result = prompt.template
        for key, val in variables.items():
            result = result.replace("{" + key + "}", str(val))

        return result

    # ── Inspection ────────────────────────────────────────────────────────────

    def verify_all(self) -> Dict[str, bool]:
        """Check integrity of all locked prompts."""
        results = self._lf.verify_all()
        for pid, ok in results.items():
            status = "✓" if ok else "⚠️  TAMPERED"
            print(f"  {status} {pid}")
        return results

    def list(self):
        return self._lf.list()

    def get(self, prompt_id: str) -> Optional[LockedPrompt]:
        return self._lf.get(prompt_id)

    def required_vars(self, prompt_id: str):
        p = self._lf.get(prompt_id)
        return _VAR_PATTERN.findall(p.template) if p else []
