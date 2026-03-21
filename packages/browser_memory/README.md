# Browser Memory - Personal Knowledge Graph from Web Browsing

**Standalone module** that turns browser history + scraped content into a queryable knowledge graph.

---

## Quick Start

```python
from browser_memory import BrowserMemory

bm = BrowserMemory(db_path="my_browser_memory.db")

# Add pages
bm.add_page(
    url="https://example.com",
    title="Page Title",
    content="Page content...",
    time_spent=300,  # seconds
    tags=["topic1", "topic2"]
)

# Search
results = bm.search("authentication")

# Get research path
path = bm.research_path("OAuth")

# Get stats
stats = bm.get_stats()
```

---

## Features

- ✅ **Vector Search** - Find similar pages semantically
- ✅ **Graph Relationships** - Track links, research paths, tags
- ✅ **SQLite Persistence** - Saves to disk automatically
- ✅ **Tag System** - Auto-extract and query by tags
- ✅ **Research Paths** - See your browsing journey
- ✅ **Standalone** - No dependencies on other modules

---

## Installation

```bash
# Dependencies (already have these)
pip install networkx qdrant-client
```

---

## Usage Examples

### 1. Add Pages

```python
from browser_memory import BrowserMemory

bm = BrowserMemory()

# Simple
bm.add_page(
    url="https://oauth.net/2/",
    title="OAuth 2.0 Tutorial",
    content="OAuth 2.0 is the industry-standard..."
)

# With metadata
bm.add_page(
    url="https://jwt.io/introduction",
    title="JWT Introduction",
    content="JSON Web Tokens are...",
    time_spent=180,  # 3 minutes
    tags=["jwt", "auth", "tokens"],
    metadata={"author": "John Doe"}
)
```

### 2. Search

```python
# Semantic search
results = bm.search("authentication", top_k=10)

for r in results:
    print(f"{r['title']} - {r['url']}")
    print(f"  Score: {r['score']:.3f}")
    print(f"  Tags: {', '.join(r['tags'])}")
```

### 3. Research Paths

```python
# Get your research journey on a topic
path = bm.research_path("OAuth", max_depth=5)

print(f"Topic: {path['topic']}")
print(f"Pages: {len(path['pages'])}")
print(f"Tags: {path['tags']}")

for page in path['pages']:
    print(f"  - {page['title']} ({page['url']})")
```

### 4. Linked Pages

```python
# What pages link to/from this one?
linked = bm.get_linked_pages("https://oauth.net/2/")

for l in linked:
    print(f"{l['relationship']}: {l['title']}")
    print(f"  Direction: {l['direction']}")
```

### 5. Add Relationships

```python
# Manually add relationships
bm.add_relationship(
    from_url="https://oauth.net/2/",
    to_url="https://jwt.io/introduction",
    rel_type="visited_before"
)

bm.add_relationship(
    from_url="https://oauth.net/2/",
    to_url="https://github.com/auth0",
    rel_type="links_to"
)
```

### 6. Statistics

```python
stats = bm.get_stats()

print(f"Total pages: {stats['total_pages']}")
print(f"Total tags: {stats['total_tags']}")
print(f"Graph entities: {stats['graph_entities']}")
print(f"Graph relationships: {stats['graph_relationships']}")
```

### 7. Export

```python
# Export all data as JSON
json_data = bm.export(format="json")

# Save to file
with open("browser_memory_export.json", "w") as f:
    f.write(json_data)
```

---

## Relationship Types

Built-in relationship types:

| Type | Meaning | Example |
|------|---------|---------|
| `links_to` | Page A links to page B | Tutorial → GitHub repo |
| `visited_before` | Temporal sequence | Searched → Read → Code |
| `related_to` | Topical similarity | OAuth ↔ JWT |
| `tagged_with` | Page has tag | Page ↔ "authentication" |

Custom types supported:
```python
bm.add_relationship(url1, url2, "cites")
bm.add_relationship(url1, url2, "contradicts")
bm.add_relationship(url1, url2, "extends")
```

---

## Query Examples

### Find all pages about a topic

```python
results = bm.search("machine learning", top_k=20)
```

### Find pages with specific tags

```python
results = bm.search("auth")
auth_pages = [r for r in results if "auth" in r.get("tags", [])]
```

### See your research path

```python
path = bm.research_path("Kubernetes", max_depth=10)
```

### Find all pages linking to a specific site

```python
linked = bm.get_linked_pages("https://github.com/myproject")
```

### Export for AI analysis

```python
# Export and feed to AI
json_data = bm.export()

# Now AI can answer:
# "What have I read about OAuth?"
# "Show me my research patterns"
# "What topics am I interested in?"
```

---

## Database Schema

### SQLite Tables

**pages:**
- url (PRIMARY KEY)
- title
- content
- scraped_at
- time_spent
- tags (JSON)
- metadata (JSON)
- entity_id (graph ID)

**sessions:**
- session_id
- started_at
- topic
- page_urls (JSON)

### Qdrant Collection

**memory_graph:**
- Vector embeddings for all pages
- Indexed by entity_id

### NetworkX Graph

- Nodes: pages, tags, topics
- Edges: relationships

---

## Integration with Browser Scraper

```python
# In your scraper
from browser_memory import BrowserMemory

bm = BrowserMemory()

def on_page_scraped(url, title, content, time_spent):
    # Auto-add to memory
    bm.add_page(
        url=url,
        title=title,
        content=content,
        time_spent=time_spent,
        tags=extract_tags(content)
    )
    
    # Auto-link to previous page
    if last_url:
        bm.add_relationship(last_url, url, "visited_before")
```

---

## Files

| File | Purpose |
|------|---------|
| `__init__.py` | Main module (~400 lines) |
| `README.md` | This documentation |

---

## Dependencies

- `networkx` - Graph database
- `qdrant-client` - Vector search
- `sqlite3` - Persistence (built-in)

---

## Status

**✅ Implemented:**
- Page storage (SQLite)
- Vector search (Qdrant)
- Graph relationships (NetworkX)
- Tag system
- Research paths
- Export functionality

**🔧 TODO:**
- Auto-tag extraction
- Session tracking
- Browser extension integration
- Visualization

---

**Version:** 1.0
**Author:** Richard
**License:** Personal use
