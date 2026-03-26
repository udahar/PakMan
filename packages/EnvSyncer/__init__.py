"""
EnvSyncer
Environment state sync across AI agent sessions. Zero external deps.

Captures your working directory, env vars, installed packages, and
active files into a named snapshot, then restores them in a new session.

Quick start:
    from EnvSyncer import EnvSyncer

    # In session 1 — save state
    env = EnvSyncer()
    env.snapshot("task_42", config={"project": "PromptForge", "stage": "debug"})
    env.save()

    # In session 2 — restore state
    env = EnvSyncer()
    state = env.load("task_42")
    print(state.working_dir)
    print(state.config)
    env.restore_cwd("task_42")
    env.restore_env("task_42")

    # Compare two sessions
    diff = env.diff("task_42", "task_43")
    print(diff["changed"])   # env vars that changed between sessions

    # List all saved states
    print(env.list())
"""
from .syncer import EnvSyncer, EnvState

__version__ = "0.1.0"
__all__ = ["EnvSyncer", "EnvState"]
