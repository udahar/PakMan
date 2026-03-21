# Prompt Version Control - Git for Prompts

## The Concept

Like Git, but for LLM prompts. Branch, diff, merge, and version prompt strategies. Track which prompts work best with which models over time.

```
┌─────────────────────────────────────────────────────────────┐
│                 Prompt Version Control                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Prompt Repository                       │   │
│  │                                                      │   │
│  │  main ─────┄── production_prompt                      │   │
│  │           │                                           │   │
│  │  ┌────────┴────────┐                                 │   │
│  │  │                 │                                 │   │
│  │  v                 v                                 │   │
│  │ exp_v1        exp_v2  (experiments)                  │   │
│  │                 │                                    │   │
│  │                 └────────┐                             │   │
│  │                          v                            │   │
│  │                    gpt4_optimized                     │   │
│  │                                                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  Commands:                                                  │
│  $ prompt init                      # Create repo           │
│  $ prompt branch experiment_v1     # New variant           │
│  $ prompt diff main experiment_v1   # Compare              │
│  $ prompt merge experiment_v1       # Merge back           │
│  $ prompt log --model qwen2.5       # History              │
│  $ prompt test experiment_v1        # Benchmark it         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Pre-Work / Integration Guide

### Step 1: Define Prompt Schema

```python
# prompt_repo.py
from dataclasses import dataclass
from datetime import datetime

@dataclass
class PromptVersion:
    id: str
    prompt: str
    system: str
    model: str
    metadata: dict
    created_at: datetime
    parent_id: str | None
    metrics: dict | None  # Test scores, user ratings
```

### Step 2: Create Storage Backend

```python
# Use your existing Postgres
# Add a prompts table:
# - id, prompt_text, system_text, model, branch, commit_hash
# - parent_id, created_at, metrics
```

### Step 3: Implement Git-like Operations

```python
class PromptRepo:
    def __init__(self, db_connection):
        self.db = db_connection
        
    def init(self, name: str):
        # Create first "commit" on main branch
        
    def branch(self, branch_name: str, from_commit: str = "HEAD"):
        # Create new branch from commit
        
    def commit(self, message: str, prompt: PromptVersion):
        # Save new version
        
    def diff(self, commit_a: str, commit_b: str) -> dict:
        # Show differences (prompt text, parameters, etc.)
        
    def merge(self, source_branch: str, target_branch: str):
        # Merge prompt changes
        
    def log(self, branch: str = "main") -> list[PromptVersion]:
        # History
        
    def test(self, commit: str) -> dict:
        # Run benchmark, save results as metrics
```

### Step 4: Build CLI

```bash
# cli.py
import click

@click.group()
def cli():
    pass

@cli.command()
def init():
    pass

@cli.command()
@click.argument("branch_name")
def branch(branch_name):
    pass

# ... etc
```

## Quick Start

```bash
cd PromptRD/prompt_version_control
prompt init my_prompts
prompt branch experiment_v1
prompt edit --system "You are a Python expert"
prompt commit "Added more context"
prompt test  # Run benchmark
prompt log
```

## Files

- `prompt_repo.py` - Core repository
- `storage.py` - Database operations
- `diff.py` - Compare versions
- `merge.py` - Merge strategies
- `cli.py` - Command-line interface
- `tester.py` - Benchmark integration
- `web_ui.py` - Visual interface

## Integration with Prompt Library

Your existing prompt library (in modules/prompt_library) becomes the "remote":
```python
from prompt_version_control import PromptRepo

repo = PromptRepo()
repo.push("my_prompts", remote="prompt_library")
repo.pull("best_practices", local="main")
```

## Integration with Frank

```python
# In frank.py, when loading prompts:
from prompt_version_control import PromptRepo

repo = PromptRepo()
# Use specific version
prompt = repo.checkout("experiment_v3")
```

## Extension Ideas

- Visual diff (show prompt changes in UI)
- A/B testing (deploy two versions, track metrics)
- Model-specific branches (optimize per model)
- Tags (v1.0, v2.0 stable releases)
- Rollback (instantly revert to working version)
- Integration with CI/CD (test before deploy)
