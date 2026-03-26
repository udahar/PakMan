"""
PakMan-Lock
Deterministic prompt execution locking for AI systems.

Prevents silent prompt drift by SHA-256 hashing templates at lock time.
Any out-of-band modification raises LockedPromptError before execution.

Quick start:
    from PakManLock import PakManLock

    lock = PakManLock("prompts.paklock")

    # Lock a prompt at design time
    lock.lock("auth_reviewer",
              "You are a senior security engineer. "
              "Review the following code for auth vulnerabilities: {code}",
              tags=["security", "code_review"])
    lock.save()

    # Use it safely at runtime
    prompt = lock.render("auth_reviewer", code=my_code)
    response = llm(prompt)

    # Verify nothing has drifted
    lock.verify_all()

    # If you need to update a prompt, unfreeze → edit → freeze
    lock.unfreeze("auth_reviewer")
    lock.lock("auth_reviewer", new_template)
    lock.freeze("auth_reviewer")
    lock.save()
"""
from .injector import PakManLock
from .lockfile import LockFile, LockedPrompt, LockedPromptError

__version__ = "0.1.0"
__all__ = [
    "PakManLock",
    "LockFile",
    "LockedPrompt",
    "LockedPromptError",
]
