"""
CodeSandbox
Safe sandboxed code execution for AI agents. Zero mandatory external deps.

Quick start:
    from CodeSandbox import CodeSandbox

    sb = CodeSandbox(timeout=5)
    result = sb.run("print(2 ** 10)")
    print(result.stdout)   # 1024
    print(result.ok)       # True

    # Strict mode — only whitelisted stdlib imports
    sb = CodeSandbox(strict=True)
    result = sb.run("import requests")  # → blocked=True

    # Docker mode for full isolation (requires Docker)
    sb = CodeSandbox(docker_image="python:3.12-slim", timeout=15)
    result = sb.run("import os; print(os.listdir('/'))")

    # Check result
    if result.blocked:
        print(f"Blocked: {result.block_reason}")
    elif result.timed_out:
        print("Execution timed out")
    elif result.ok:
        print(result.stdout)
    else:
        print(f"Error (exit {result.exit_code}): {result.stderr}")
"""
from .sandbox import CodeSandbox, SandboxResult

__version__ = "0.1.0"
__all__ = ["CodeSandbox", "SandboxResult"]
