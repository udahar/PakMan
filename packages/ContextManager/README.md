# Context Manager - Smart Context Window

Automatically manage what AI remembers.

## Usage

```python
from context_manager import ContextManager

ctx = ContextManager()
ctx.add("user_preference", "likes concise answers")
ctx.add("project_info", "building AI agent system")

relevant = ctx.get_for_task("code_review")
```

## Features

- **Relevance Scoring** - What matters now?
- **Auto-Pruning** - Drop irrelevant context
- **Task-Based Selection** - Different context for different tasks
- **Memory Layers** - Short-term, long-term, working memory

## Installation

```bash
pip install context-manager
```

## Status

✅ Production Ready
