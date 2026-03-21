# PromptSKLib - AI Skills Library

A structured skills library for AI agents to admit uncertainty, search knowledge bases, and progressively gather information.

## Architecture

```
Task Input → Skill Retrieval (Qdrant/Postgres) → Web Search (if needed) → Solution
```

## Skill Types

| Category | Count | Description |
|----------|-------|-------------|
| inquiry | 4 | Knowledge gathering & verification |
| engineering | 6 | Reusable implementation patterns |
| prompt_strategy | 12 | Reasoning modes & prompt techniques |
| repair | 2 | Common bug fixes |
| tool | 2 | Executable tools |

**Total: 26 skills**

## Directory Structure

```
PromptSKLib/
├── README.md                    # This file
├── categories/                  # Category metadata
│   ├── inquiry.json
│   ├── engineering.json
│   ├── prompt_strategy.json
│   ├── repair.json
│   └── tool.json
├── skills/                      # Individual skill definitions
│   ├── humble_inquiry.md        # Admit → search internal → search web
│   ├── humble_inquiry.py        # Python implementation
│   ├── web_research.md          # Deep web investigation
│   ├── source_verification.md   # Cross-reference sources
│   ├── knowledge_gap_analysis.md # Identify unknowns
│   ├── retry_backoff.md         # Retry with exponential backoff
│   ├── circuit_breaker.md       # Prevent cascading failures
│   ├── csv_parser_quotes.md     # Robust CSV parsing
│   ├── safe_sql_builder.md      # Parameterized SQL queries
│   ├── regex_email_validator.md # Email format validation
│   ├── dockerize_fastapi.md     # Docker config for FastAPI
│   ├── tree_of_thought.md       # Branching reasoning
│   ├── react_reasoning.md       # Reason + Act pattern
│   ├── off_by_one_fix.md        # Loop boundary fixes
│   ├── null_pointer_guard.md    # Null check patterns
│   ├── web_search_tool.md       # Web search tool
│   └── web_fetch_tool.md        # URL content fetcher
├── templates/                   # Prompt templates
│   └── humble_inquiry_prompt.md
└── examples/                    # Usage examples
    └── humble_inquiry_examples.md
```

## Usage

Skills are retrieved from Qdrant by embedding the task, then injected into prompts as relevant context.

## Quick Start

```python
from skills.humble_inquiry import humble_inquiry

# Research a topic with progressive inquiry
result = await humble_inquiry(
    topic="Your question here",
    qdrant_client=qdrant,
    postgres_conn=postgres,
    web_search_fn=web_search,
    web_fetch_fn=web_fetch
)

print(result.summary)
print(f"Confidence: {result.confidence * 100}%")
```
