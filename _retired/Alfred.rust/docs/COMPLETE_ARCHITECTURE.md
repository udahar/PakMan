# Complete AI Runtime Architecture

**The Final Architecture** - A self-expanding, self-regulating AI runtime environment

---

## System Overview

```
                         ┌─────────────────┐
                         │    Alfred       │
                         │  (AI Agent)     │
                         └────────┬────────┘
                                  │
                         ┌────────▼────────┐
                         │    Planner      │
                         │   (LLM Brain)   │
                         └────────┬────────┘
                                  │
            ┌─────────────────────┼─────────────────────┐
            │                     │                     │
    ┌───────▼────────┐   ┌───────▼────────┐   ┌───────▼────────┐
    │    Governor    │   │    Skills      │   │  Subsystems    │
    │   (Safety)     │   │   Registry     │   │   Registry     │
    │                │   │                │   │                │
    │ • Capabilities │   │ • Pipelines    │   │ • Modules      │
    │ • Budgets      │   │ • Discovery    │   │ • Coordination │
    │ • Safe Mode    │   │ • Usage Track  │   │ • Fitness      │
    └───────┬────────┘   └───────┬────────┘   └───────┬────────┘
            │                    │                    │
            │            ┌───────▼────────┐           │
            │            │    Memory      │           │
            │            │    Client      │           │
            │            │                │           │
            │            │ • Postgres     │           │
            │            │ • Qdrant       │           │
            │            │ • Context      │           │
            │            └───────┬────────┘           │
            │                    │                    │
            └────────────────────┼────────────────────┘
                                 │
                         ┌───────▼────────┐
                         │  Observatory   │
                         │  (Dashboard)   │
                         │                │
                         │ • Metrics      │
                         │ • Lineage      │
                         │ • Violations   │
                         └───────┬────────┘
                                 │
                         ┌───────▼────────┐
                         │   rustutils    │
                         │  (Dispatcher)  │
                         └───────┬────────┘
                                 │
                         ┌───────▼────────┐
                         │  40+ Tools     │
                         │                │
                         │ • Filesystem   │
                         │ • System       │
                         │ • Network      │
                         │ • AI           │
                         │ • Data         │
                         └────────────────┘
```

---

## Five Architectural Layers

### Layer 1: Tools (40+)

Individual utilities that do actual work.

**Examples:**
- `fs_scan` - Filesystem scanner
- `repo_index` - Code indexer
- `json_fmt` - JSON formatter
- `prompt_fmt` - Prompt formatter

**Characteristics:**
- Single responsibility
- Composable via pipelines
- Tracked by genome

---

### Layer 2: Pipelines

Chains of tools that accomplish complex tasks.

**Example:**
```json
{
  "steps": [
    {"tool": "repo_index", "args": ["--json", "--hash"]},
    {"tool": "context_pack", "args": ["--max-tokens", "4096"]},
    {"tool": "prompt_fmt", "args": ["--format", "ollama"]}
  ]
}
```

**Characteristics:**
- Reusable workflows
- AI-discoverable
- Fitness tracked

---

### Layer 3: Skills

Registered pipelines with metadata.

**Characteristics:**
- Searchable
- Versioned
- Usage statistics
- Success/failure tracking

**Commands:**
```bash
rustutils skill register analyze_repo.json
rustutils skill search "code analysis"
rustutils skill run analyze_repo ./myproject
```

---

### Layer 4: Subsystems

Coordinated clusters of tools and pipelines.

**Examples:**
- **Code Intelligence** - repo_index, embedding_prep, qdrant_insert
- **Security Analysis** - grep_lite, file_hash, log_parse
- **Data Processing** - csv_view, json_fmt, cache_ctrl

**Characteristics:**
- Module-level organization
- Multiple pipelines
- Shared capabilities
- Fitness tracking

**Commands:**
```bash
rustutils subsystem register code_intelligence.json
rustutils subsystem list
rustutils subsystem run code_intelligence ./repo
```

---

### Layer 5: Governor

Safety constraints and build budgets.

**Responsibilities:**
- Capability gatekeeping
- Build budgets (max 3 tools/day, 1 subsystem/week)
- Fitness thresholds
- Mutation limits
- Safe mode enforcement

**Characteristics:**
- Never does creative work
- Only enforces rules
- Prevents runaway expansion

---

## Tool Genome

Every tool has DNA tracking:

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

**Tracked:**
- Lineage (parent → child)
- Fitness (0.0 - 1.0)
- Usage statistics
- Mutations

---

## Observatory Dashboard

Real-time system monitoring:

```bash
rustutils observatory overview
rustutils observatory lineage repo_index
rustutils observatory subsystem-map
rustutils observatory violations
rustutils observatory export
```

**Shows:**
- System health
- Tool lineage graphs
- Subsystem maps
- Budget status
- Violation log

---

## Complete Command Reference

### Tools
```bash
rustutils <tool> [args]
rustutils fs_scan . --json
rustutils repo_index ./src --json --hash
```

### Skills
```bash
rustutils skill register <file.json>
rustutils skill search <query>
rustutils skill list
rustutils skill run <id> <input>
```

### Subsystems
```bash
rustutils subsystem register <file.json>
rustutils subsystem list
rustutils subsystem run <id> <input>
rustutils subsystem map
```

### Genome
```bash
rustutils genome <tool_id>
rustutils capabilities <capability>
rustutils lineage <tool_id>
rustutils record <tool_id> <success> --runtime <ms>
```

### Memory
```bash
rustutils memory store <key> <value>
rustutils memory recall <key>
rustutils memory search <query>
```

### Governor
```bash
rustutils governor status
rustutils governor config
rustutils governor violations
rustutils governor safe-mode
```

### Observatory
```bash
rustutils observatory overview
rustutils observatory lineage <tool>
rustutils observatory subsystem-map
rustutils observatory export
```

### Pipeline
```bash
rustutils pipe '<json>'
rustutils pipe pipeline.json --input in.txt --output out.txt
```

### Schema
```bash
rustutils schema          # All schemas
rustutils schema fs_scan  # Single schema
```

---

## Evolution Hierarchy

```
Tools evolve → tracked by Genome
     ↓
Pipelines evolve → tracked by Skills
     ↓
Subsystems evolve → tracked by Subsystem Registry
     ↓
Architecture evolves → monitored by Observatory
     ↓
Safety enforced → by Governor
```

---

## File Structure

```
Rust/
├── crates/
│   ├── common/              # Shared utilities
│   ├── rustutils/           # Main dispatcher
│   ├── mcp_server/          # AI protocol
│   ├── schema_gen/          # Schema discovery
│   ├── skill_registry/      # Skills + Genome
│   ├── memory_client/       # Postgres/Qdrant
│   ├── repo_index/          # File indexer
│   ├── subsystem_registry/  # NEW: Subsystems
│   ├── governor/            # NEW: Safety
│   ├── observatory/         # NEW: Dashboard
│   └── ... (40 tools)
├── skills.db                # Skills database
├── subsystems.db            # Subsystems database
├── examples/
│   ├── skills/
│   ├── subsystems/
│   └── genomes/
└── docs/
    ├── QUICKSTART.md
    ├── RUNTIME_ARCHITECTURE.md
    ├── AI_INTEGRATION.md
    ├── COMPLETE_ARCHITECTURE.md  # This file
    └── STATUS.md
```

---

## Total: 51 Crates

```
40 individual tools
+ common
+ rustutils
+ mcp_server
+ schema_gen
+ skill_registry
+ memory_client
+ repo_index
+ subsystem_registry (NEW)
+ governor (NEW)
+ observatory (NEW)
= 51 crates
```

---

## Safety Features

### Governor Enforces:
- Max 3 new tools per day
- Max 1 new subsystem per week
- Max 5 compile attempts per tool
- Minimum fitness: 0.65
- Mutation cooldown: 24 hours
- Allowed capabilities list

### Safe Mode Triggers:
- Too many failed builds
- Sudden tool explosion
- Memory spike
- Mutation cascade

### Human Override:
- Manual safe mode toggle
- Review queue for rejected tools
- Violation log

---

## AI Integration Flow

```
1. AI receives task
       ↓
2. AI queries schema (rustutils schema)
       ↓
3. AI searches skills (rustutils skill search)
       ↓
4. AI checks subsystems (rustutils subsystem list)
       ↓
5. AI builds pipeline
       ↓
6. Governor validates (capability check, budget)
       ↓
7. rustutils executes pipeline
       ↓
8. Observatory records metrics
       ↓
9. Genome updates fitness
```

---

## Example: AI Analyzes Repository

```python
# AI generates plan
plan = {
    "subsystem": "code_intelligence",
    "pipeline": "analyze_architecture",
    "input": "./myproject"
}

# Execute
result = subprocess.run([
    "rustutils", "subsystem", "run",
    "code_intelligence", "./myproject"
], capture_output=True, text=True)

# Record success
subprocess.run([
    "rustutils", "genome", "record",
    "repo_index", "true", "--runtime", "1250"
])
```

---

## Key Insights

### 1. Separation of Concerns
- **LLM** → Reasoning and planning
- **Rust** → Execution
- **Governor** → Safety
- **Genome** → Evolution tracking

### 2. Hierarchy Prevents Chaos
```
Tools (50+) → organized into → Subsystems (10)
Pipelines (100+) → organized into → Skills (20)
```

### 3. Fitness-Based Evolution
- Successful tools survive
- Poor performers deprecated
- Lineage tracked
- Mutations limited

### 4. Governor Prevents Runaway
- Budget limits
- Capability gates
- Safe mode
- Human override

---

## This Is A Complete AI Runtime

Not a chatbot. Not a tool collection.

**A self-expanding, self-regulating AI runtime environment.**

Alfred can now:
1. **Reason** about tasks (LLM)
2. **Discover** capabilities (schemas, skills, subsystems)
3. **Plan** pipelines
4. **Execute** via rustutils
5. **Remember** via memory client
6. **Evolve** tools and subsystems
7. **Learn** from fitness tracking
8. **Stay safe** via governor

---

**Status:** ✅ Complete Architecture
