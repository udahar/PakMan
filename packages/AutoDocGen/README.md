# AutoDocGen
> **Status:** 🔬 IN PROGRESS
> **Note:** Extends and complements `SupDoc` — merging ideas from both.

## What It Is
An AI-powered documentation engine that watches your codebase, reads the Abstract Syntax Tree (AST), understands what functions actually *do*, and keeps READMEs and API docs surgically accurate without human effort.

## Why It Matters  
SupDoc provides structured project documentation. AutoDocGen takes it a step further by hooking directly into code changes — so docs are never stale again.

## How It Works

```
Developer saves file.py
         │
         ▼
AutoDocGen detects change (file watcher / git pre-commit hook)
         │
AST Parse: extract functions, classes, signatures, docstrings
         │
         ▼
Diff against existing README/docs
  "Function authenticate() is not documented"
  "Parameter `timeout` was renamed to `wait_ms`"
         │
         ▼
LLM pass: write clean professional docs for the diff only
         │
         ▼
Patch the README/API doc in-place
```

### What It Documents Automatically
| Artifact | How Generated |
|---|---|
| Function signatures | AST extraction |
| Parameter descriptions | LLM inference from names + body |
| Return value docs | Type hints + LLM |
| Usage examples | Pulled from unit tests if present |
| Changelog entry | Git commit message → summary |

### SupDoc Integration
- AutoDocGen feeds structured per-function metadata to SupDoc's schema.
- SupDoc provides project-level narrative; AutoDocGen provides code-level precision.
- Together: full-stack documentation with near-zero maintenance.

## Integration Points
- Watches any `packages/` directory automatically
- `PromptOS` → uses LLM for description generation
- `PakMan-Lock` → uses locked model version for consistency

## Roadmap
- [ ] File watcher trigger (watchdog)
- [ ] Python AST extractor (signatures, types, docstrings)
- [ ] LLM-based description generator
- [ ] README patch writer (surgical, not full rewrites)
- [ ] Git pre-commit hook installer
- [ ] SupDoc schema bridge
