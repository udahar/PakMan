# tool_router

**Semantic tool name resolution for multi-model AI systems.**

Different models reach for different vocabulary when they want to do the same thing. Codex says `snapshot_repo`. Nemotron says `read`. GLM says `parse`. They all mean "read the file before touching it." `tool_router` maps all of them to your actual tool name.

```python
from tool_router import ToolRouter

router = ToolRouter()

# Model-specific resolution (highest confidence)
router.resolve("snapshot_repo", model="codex/gpt-5.3-codex")   # → "bridge.read"
router.resolve("locate_symbol", model="codex/gpt-5.3-codex")   # → "bridge.diff"
router.resolve("replace_symbol_body", model="codex/gpt-5.3-codex")  # → "bridge.patch"

# Model-agnostic fallback
router.resolve("vector_search")    # → "qdrant:similarity"
router.resolve("audit_log")        # → "postgres:events"
router.resolve("circuit_breaker")  # → "qdrant:patterns"

# What does the intent cluster look like?
router.intent_for("semantic_search")     # → "semantic_pattern_search"
router.aliases_for_intent("safe_code_mutation_sequence")
# → {"openai": ["snapshot_repo", "locate_symbol", ...], "nvidia": ["read", "write"], ...}

# Full summary
router.summary()
```

## Where the data came from

Seeded from an accidental discovery: benchmark tests designed for a specific system (Frank/Alfred) were run against 80 models. Every model that "failed" revealed what vocabulary it *naturally* reaches for. 153 responses across 10 intent clusters. This is a form of zero-shot vocabulary elicitation — more honest than a survey because models answered by doing, not by describing.

## Extending the map

Add a `ToolVocab` category to your benchmark with prompts like:
- *"List the tools you would use to read source code before modifying it."*
- *"What retrieval method finds semantically similar past incidents?"*
- *"How do you filter tickets by state and priority for a dashboard?"*

Each run adds more aliases. The dataset compounds.

## Qdrant integration (optional)

If `qdrant-client` is installed, you can seed a Qdrant collection from the map and use semantic vector search as the resolution fallback — handles tool names you've never seen before:

```python
# Coming: router.seed_qdrant(client, collection="tool_aliases")
# Coming: router.resolve_semantic("I need to look at the diff before applying")
```

## Skills and tool packages

`tool_router` is intentionally narrow — it resolves names, it doesn't execute tools. Pair it with:
- `tool_builder` — defines tool interfaces
- `tool_composer` — sequences tool calls
- `skills_registry` — registers available capabilities

The semantic map in `data/semantic_tools_map.json` is the shared artifact. Any of these packages can read it.

## Install

```bash
pakman install tool_router
```
