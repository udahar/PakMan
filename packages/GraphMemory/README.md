# GraphMemory

Unified knowledge graph with automatic backend detection and graceful fallback.

No config required. Works standalone out of the box. Lights up automatically
when Qdrant and Ollama are running.

---

## Tiers

| Tier | Requires | What you get |
|------|----------|-------------|
| **1 — Lite** | nothing | SQLite persistence, entity extraction, BFS path queries |
| **2 — Full** | Qdrant running | + vector similarity search, hybrid queries |
| **3 — Semantic** | Qdrant + Ollama | + real semantic embeddings (bge-m3 or configurable) |

Same API at every tier. Call `gm.backends()` to see what's active.

---

## Install

```bash
pakman install GraphMemory

# With vector support
pip install pakman-graphmemory[vector]
```

---

## Quick Start

```python
from GraphMemory import GraphMemory

gm = GraphMemory()
print(gm.mode)        # "full" or "lite"
print(gm.backends())  # {"sqlite": True, "qdrant": True, ...}
```

---

## New API (portable, zero-dep)

```python
gm.ingest("Richard fixed the auth bug in PromptForge last Tuesday.")
gm.neighbors("PromptForge")
gm.path("Richard", "auth bug")
gm.search("auth")
gm.add_node("PromptForge", kind="project")
gm.add_edge("Richard", "worked_on", "PromptForge")
gm.stats()
```

---

## Classic API (MemoryGraph-compatible, used by BrowserV1)

```python
eid = gm.add_entity(entity_id="topic_auth", type="topic",
                    name="authentication", content="OAuth, JWT...")
gm.add_relationship("topic_auth", "company_google", "related_to")
gm.similar_to("authentication vulnerability", top_k=5)   # [] if Qdrant down
gm.hybrid_query("login bug", relationships=["affects", "calls"])
gm.get_stats()
```

---

## Auto-Hookup Env Vars

| Variable | Default | Purpose |
|----------|---------|---------|
| `BROWSE_QDRANT_URL` | `http://localhost:6333` | Qdrant server |
| `BROWSE_OLLAMA_EMBED_URL` | `http://127.0.0.1:11437/api/embed` | Ollama embed |
| `BROWSE_EMBED_MODEL` | `bge-m3:latest` | Embedding model |
| `BROWSE_EMBED_DIM` | `1024` | Vector dimensions |

---

## Config

```python
gm = GraphMemory(db_path="~/.pakman/graph_memory.db", auto_vector=False)
gm = GraphMemory(qdrant_url="http://myserver:6333", embed_model="nomic-embed-text")
gm = GraphMemory(llm=lambda prompt: my_model.generate(prompt))
```

---

Part of [PakMan](https://github.com/udahar/PakMan)
