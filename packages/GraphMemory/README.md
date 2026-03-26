# GraphMemory

> **Category:** Context & Memory
> **Focus:** Semantic Knowledge Graphing for Conversational Memory

## Abstract
Extracts entities and relationships from AI interactions into a local graph database. Rather than standard string-based vector lookup, this engine understands semantic connections (e.g., 'Frank' -> 'worked on' -> 'PromptOS').

## How It Operates Under the Hood
This module operates with the following system life-cycle:

1. Hooks into AiOSKernel memory stream.
2. Uses a fast LLM pass to extract discrete entities (Noun nodes) and relationships (Verb edges).
3. Dumps to a lightweight graph schema (SQLite/NetworkX).
4. Provides an API endpoint for path-finding and logic querying.

## Engineering Roadmap
*(Code to be implemented in future development phases).*

- [ ] Define precise interface boundaries (Input/Output).
- [ ] Connect with existing `AiOSKernel` and `PromptRouter` dependencies.
- [ ] Implement initial proof-of-concept tests.
- [ ] Evaluate performance constraints (Latency vs Token Cost).
