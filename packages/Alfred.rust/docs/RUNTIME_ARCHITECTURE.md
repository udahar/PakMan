# AI Runtime Architecture

The complete architecture for Alfred's Rust-based AI runtime environment.

## Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Alfred (AI Agent)                         │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Planner (LLM)                                       │   │
│  │  - Decides which tools/skills to use                │   │
│  │  - Builds pipelines dynamically                     │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────┬───────────────────────────────────────┘
                      │ JSON-RPC / MCP Protocol
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              Rust Runtime Layer                              │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Skills    │  │   Memory    │  │   Genome    │        │
│  │  Registry   │  │   Client    │  │  Tracking   │        │
│  │             │  │             │  │             │        │
│  │ - Pipeline  │  │ - Postgres  │  │ - Lineage   │        │
│  │   storage   │  │ - Qdrant    │  │ - Fitness   │        │
│  │ - Discovery │  │ - KV cache  │  │ - Evolution │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
│         │                │                │                │
│         └────────────────┼────────────────┘                │
│                          │                                  │
│                          ▼                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              rustutils (dispatcher)                  │   │
│  │  - schema    - pipe      - skill                    │   │
│  │  - manifest  - fs_scan   - memory                   │   │
│  │  - list      - repo_index                           │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                  │
│                          ▼                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              40+ Rust Tools                          │   │
│  │  fs_scan, json_fmt, proc_list, queue_processor...   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Skill Registry

**Purpose:** Store and discover reusable pipelines/capabilities

**Commands:**
```bash
# Register a skill
rustutils skill register analyze_repo.json

# Search skills
rustutils skill search "code analysis"

# List all skills
rustutils skill list

# Run a skill
rustutils skill run analyze_repo ./myproject
```

**Skill JSON Format:**
```json
{
  "id": "analyze_repository",
  "name": "analyze_repository",
  "description": "Analyze a code repository and summarize architecture",
  "pipeline": {
    "steps": [
      {"tool": "repo_index", "args": ["--json", "--hash"]},
      {"tool": "json_fmt", "args": ["--minify"]},
      {"tool": "prompt_fmt", "args": ["--format", "ollama"]}
    ]
  },
  "tags": ["analysis", "repository", "code"],
  "category": "analysis",
  "version": "1.0.0"
}
```

**Features:**
- SQLite storage
- Full-text search
- Usage tracking (success/failure counts)
- Average duration tracking
- Tag-based organization

---

### 2. Tool Genome

**Purpose:** Track tool lineage, fitness, and evolution

**Commands:**
```bash
# Register tool in genome
rustutils skill register-tool genome_fs_scan.json

# Get tool genome info
rustutils skill genome fs_scan

# List tools by capability
rustutils skill capabilities filesystem.scan

# Show tool lineage
rustutils skill lineage repo_index

# Record tool execution
rustutils skill record fs_scan true --runtime 85.5
```

**Genome JSON Format:**
```json
{
  "tool_id": "repo_index",
  "version": "1.0.0",
  "parent": "fs_scan",
  "capability": "filesystem.scan",
  "category": "filesystem",
  "created_by": "human",
  "fitness_score": 0.92,
  "mutation_type": "specialized_for_repos"
}
```

**Features:**
- Parent/child relationships (tool lineage)
- Fitness scores (0.0 - 1.0)
- Usage statistics
- Automatic deprecation of low-fitness tools
- Capability mapping (prevents duplicates)

---

### 3. Memory Client

**Purpose:** Unified interface for Postgres and Qdrant

**Commands:**
```bash
# Store a value
rustutils memory store ticket:174 '{"status": "active"}'

# Recall a value
rustutils memory recall ticket:174

# Search memory
rustutils memory search "authentication"
```

**Python Usage:**
```python
from memory_client import MemoryClient

client = MemoryClient(
    postgres_url="postgresql://...",
    qdrant_url="http://localhost:6333"
)

# Store ticket context (shared across AI models)
client.store_ticket_context("ticket_174", "codex", "Working on auth...")

# Get all context for a ticket
context = client.get_ticket_context("ticket_174")

# Store embedding
client.store_embedding("code_embeddings", "file_123", code_text, metadata)

# Search by similarity
similar = client.search_similar("code_embeddings", "auth system", limit=5)
```

**Features:**
- Postgres for structured data
- Qdrant for vector embeddings
- In-memory fallback
- Shared context per ticket
- TTL support

---

## Usage Patterns

### Pattern 1: Direct Tool Calls

```python
import subprocess
import json

# Simple tool call
result = subprocess.run(
    ["rustutils", "fs_scan", "./project", "--json"],
    capture_output=True, text=True
)
data = json.loads(result.stdout)
```

### Pattern 2: Skill Execution

```python
# Register a skill first
subprocess.run(["rustutils", "skill", "register", "my_skill.json"])

# Run the skill
result = subprocess.run(
    ["rustutils", "skill", "run", "analyze_repo", "./myproject"],
    capture_output=True, text=True
)
```

### Pattern 3: Pipeline Execution

```python
pipeline = {
    "steps": [
        {"tool": "repo_index", "args": ["./src", "--json"]},
        {"tool": "context_pack", "args": ["--max-tokens", "4096"]},
        {"tool": "prompt_fmt", "args": ["--format", "ollama"]}
    ]
}

result = subprocess.run(
    ["rustutils", "pipe", json.dumps(pipeline)],
    capture_output=True, text=True
)
```

### Pattern 4: AI Planning + Execution

```python
# AI generates a plan
plan = llm.generate("""
Task: Analyze the repository security

Available skills:
- security_scan: Scan for security issues
- repo_index: Index repository
- grep_lite: Search for patterns

Generate a pipeline to accomplish this task.
""")

# Execute the plan
pipeline = json.loads(plan)
result = subprocess.run(
    ["rustutils", "pipe", json.dumps(pipeline)],
    capture_output=True, text=True
)

# Record success for fitness tracking
subprocess.run(["rustutils", "skill", "record", "security_scan", "true", "--runtime", "1250"])
```

---

## Tool Categories

### Filesystem
- `filesystem.scan` - fs_scan, repo_index
- `filesystem.hash` - file_hash
- `filesystem.watch` - file_watch

### System
- `system.processes` - proc_list
- `system.ports` - port_check
- `system.disk` - disk_info

### Network
- `network.http` - http_get
- `network.dns` - dns_lookup

### AI
- `ai.prompt_format` - prompt_fmt
- `ai.response_parse` - response_parse
- `ai.context_pack` - (future)

### Analysis
- `analysis.code` - repo_index, git_status
- `analysis.security` - (future: vuln_scan)

### Data
- `data.json` - json_fmt, diff_json
- `data.csv` - csv_view, csv_to_json

---

## Fitness Scoring

Tools automatically track fitness:

```
Initial fitness: 0.5 (50%)

On success: fitness += 0.01
On failure: fitness -= 0.05

Fitness > 0.8: Recommended tool
Fitness < 0.3: Deprecated automatically
```

View fitness:
```bash
rustutils skill capabilities filesystem.scan
```

Output:
```
Tools with capability 'filesystem.scan' (2):

  repo_index (v1.0.0) - Fitness: 92.0%, Usage: 234
  fs_scan (v1.0.0) - Fitness: 95.0%, Usage: 567
```

---

## Evolution Chains

Tools evolve through mutations:

```
fs_scan (original filesystem scanner)
    │
    ├── repo_index (specialized for code repos)
    │       │
    │       └── repo_security_scan (security-focused)
    │
    └── fs_scan_parallel (uses rayon for speed)
```

View lineage:
```bash
rustutils skill lineage repo_index
```

---

## Building

```bash
cd C:\Users\Richard\clawd\Frank\Rust

# Build everything
cargo build --release

# Build specific components
cargo build -p skill_registry --release
cargo build -p memory_client --release
cargo build -p rustutils --release
```

---

## File Structure

```
Rust/
├── crates/
│   ├── skill_registry/     # NEW: Skills + Genome
│   │   ├── src/
│   │   │   ├── lib.rs      # Core API
│   │   │   └── main.rs     # CLI
│   │   ├── examples/       # Example skills
│   │   └── Cargo.toml
│   ├── memory_client/      # NEW: Postgres/Qdrant wrapper
│   │   ├── src/
│   │   │   └── lib.rs      # Memory API
│   │   └── Cargo.toml
│   ├── rustutils/          # Updated: Main dispatcher
│   ├── schema_gen/         # Schema auto-discovery
│   ├── mcp_server/         # MCP protocol
│   └── ... (40+ tools)
├── skills.db               # SQLite database (created on first use)
└── README.md
```

---

## Total Crates: 48

```
40 original tools
+ common
+ mcp_server
+ repo_index
+ rustutils
+ schema_gen
+ skill_registry (NEW)
+ memory_client (NEW)
= 48 crates
```

---

## Next Steps

### Immediate (Done)
- ✅ Skill Registry
- ✅ Tool Genome
- ✅ Memory Client
- ✅ Integration with rustutils

### Next Week
- [ ] Tool invention framework
- [ ] Automatic pipeline generation
- [ ] Fitness-based tool recommendation

### Future
- [ ] Mutation engine (auto-improve tools)
- [ ] Capability-based tool discovery
- [ ] Community skill sharing

---

This is your **AI Runtime Environment** - a complete system for:
- Tool execution
- Skill discovery
- Memory management
- Tool evolution tracking

Alfred can now:
1. **Discover** existing skills
2. **Execute** pipelines
3. **Track** tool fitness
4. **Remember** context across sessions
5. **Evolve** tools over time
