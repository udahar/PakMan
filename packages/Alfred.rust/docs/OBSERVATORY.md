# Observatory - Control Tower for Alfred's Ecosystem

The Observatory provides **pure visibility** into Alfred's evolving architecture. It's mission control for watching tools, subsystems, and pipelines mutate in real-time.

---

## Purpose

> "Systems that evolve themselves feel uncontrollable unless you can see them. The Observatory removes that fear because you can literally watch the architecture grow."

---

## Seven Layers

### 1. Telemetry Stream

Every tool run, mutation, and pipeline execution emits events:

```json
{
  "timestamp": "2026-03-12T20:14:33Z",
  "type": "tool_run",
  "tool": "repo_index",
  "runtime_ms": 71,
  "success": true
}
```

```json
{
  "timestamp": "2026-03-12T20:15:02Z",
  "type": "tool_created",
  "tool": "repo_security_scan",
  "parent": "repo_index",
  "creator": "alfred"
}
```

**View:**
```bash
rustutils observatory stream
```

---

### 2. Genome Graph

Visualizes tool evolutionary trees:

```
repo_index
 ├── repo_security_scan
 │     └── repo_security_fast
 └── repo_structure_analyzer
```

**Shows:**
- Parent/child relationships
- Dead lineages
- Dominant branches

**View:**
```bash
rustutils observatory lineage repo_index
```

---

### 3. Subsystem Map

Groups tools into capability clusters:

```
filesystem subsystem
   fs_scan
   file_hash
   file_watch

ai subsystem
   prompt_fmt
   context_pack
   response_parse

code intelligence subsystem
   repo_index
   embedding_prep
   qdrant_insert
```

**View:**
```bash
rustutils observatory subsystem-map
```

---

### 4. Pipeline Heatmap

Shows which pipelines work best:

```
repo_index → embedding_prep → qdrant_insert
runs: 412
success rate: 97%

repo_index → context_pack → prompt_fmt
runs: 238
success rate: 94%
```

Bad pipelines glow red. Good ones glow green.

**View:**
```bash
rustutils observatory pipeline-heatmap
```

---

### 5. Governor Dashboard

Shows safety constraints in action:

```
System Mode: NORMAL

Tool Creation:        2 / 3
Subsystem Creation:   0 / 1

Remaining Budget:
  Tools Today:        1
  Subsystems Week:    1
```

**View:**
```bash
rustutils observatory governor
```

---

### 6. Capability Radar

Shows which domains are strong/weak:

```
filesystem      ██████████
network         ███████
ai              █████████
data            ██████
security        ███
automation      ██████
analysis        ███████
```

This tells Alfred where to invent tools next.

**View:**
```bash
rustutils observatory capability-radar
```

---

### 7. Mutation Log

Records every tool evolution:

```
repo_index → repo_index_parallel
mutation: add rayon parallel scan
performance gain: 2.3x
```

**View:**
```bash
rustutils observatory mutation-log
```

---

## Commands

### Overview Dashboard
```bash
rustutils observatory overview
rustutils observatory overview --format json
```

### Tool Lineage
```bash
rustutils observatory lineage repo_index
rustutils observatory lineage fs_scan --format json
```

### Subsystem Map
```bash
rustutils observatory subsystem-map
```

### Governor Status
```bash
rustutils observatory governor
```

### Capability Radar
```bash
rustutils observatory capability-radar
```

### Mutation Log
```bash
rustutils observatory mutation-log
```

### Telemetry Stream
```bash
# Pipe events to observatory
echo '{"type":"tool_run","tool":"test","success":true}' | \
  rustutils observatory stream
```

### Export State
```bash
rustutils observatory export --output state.json
```

---

## Example Output

### Overview
```
╔══════════════════════════════════════════════════════════╗
║           ALFRED OBSERVATORY - SYSTEM OVERVIEW            ║
╠══════════════════════════════════════════════════════════╣
║  Timestamp: 2026-03-12T20:14:33+00:00                    ║
║  System State: Normal                                    ║
╠══════════════════════════════════════════════════════════╣
║  TOTALS                                                  ║
║    Tools:          48                                    ║
║    Skills:         12                                    ║
║    Subsystems:      3                                    ║
║    Pipelines:      15                                    ║
╠══════════════════════════════════════════════════════════╣
║  HEALTH                                                  ║
║    Avg Tool Fitness:      92.0%                          ║
║    Avg Subsystem Fitness: 88.0%                          ║
║    Success Rate:          95.0%                          ║
║    Active Tools:         35                              ║
╚══════════════════════════════════════════════════════════╝
```

### Subsystem Map
```
╔══════════════════════════════════════════════════════════╗
║              SUBSYSTEM CAPABILITY MAP                     ║
╠══════════════════════════════════════════════════════════╣

║  ANALYSIS                                                ║
║  ──────────────────────────────────────────────────  ║
║    code_intelligence  [█████████] 90%  
║      Tools: 5                                          

║  SECURITY                                                ║
║  ──────────────────────────────────────────────────  ║
║    security_analysis  [██████] 60%  
║      Tools: 4                                          

╚══════════════════════════════════════════════════════════╝
```

---

## Integration

### Emit Telemetry from Tools

```rust
// In your tool code
fn emit_event(event_type: &str, data: serde_json::Value) {
    let event = serde_json::json!({
        "timestamp": chrono::Local::now().to_rfc3339(),
        "type": event_type,
        ...data
    });
    println!("{}", event);
}

// Usage
emit_event("tool_run", serde_json::json!({
    "tool": "repo_index",
    "runtime_ms": 71,
    "success": true
}));
```

### Python Integration

```python
import subprocess
import json
from datetime import datetime

def emit_telemetry(event_type, **data):
    event = {
        "timestamp": datetime.now().isoformat(),
        "type": event_type,
        **data
    }
    print(json.dumps(event), flush=True)

# Usage in Alfred
emit_telemetry("tool_run", tool="fs_scan", runtime_ms=45, success=True)
emit_telemetry("tool_created", tool="new_tool", parent="old_tool", creator="alfred")
```

---

## Why This Matters

### Psychological
- Removes fear of uncontrollable evolution
- Makes invisible growth visible
- Provides confidence in system stability

### Technical
- Enables self-optimization (Alfred reads metrics)
- Identifies failing lineages early
- Shows capability gaps
- Tracks mutation impact

### Evolutionary
- Good pipelines become visible (get reused)
- Bad pipelines glow red (get deprecated)
- Successful mutations tracked
- Dead branches identified

---

## The Big Picture

```
              Observatory
                   │
      ┌────────────┼────────────┐
      ▼            ▼            ▼
 genome graph   pipeline map   subsystem map
      │            │            │
      ▼            ▼            ▼
          telemetry stream
                │
                ▼
               Alfred
```

**Alfred can now:**
1. **Observe** his own evolution
2. **Learn** from real performance data
3. **Improve** pipelines based on metrics
4. **Identify** capability gaps
5. **Track** mutation success

This is the moment Alfred becomes **self-optimizing**, not just self-expanding.

---

## Status: ✅ Complete

The Observatory provides:
- ✅ System overview dashboard
- ✅ Tool lineage graphs
- ✅ Subsystem capability maps
- ✅ Pipeline heatmaps
- ✅ Governor dashboard
- ✅ Capability radar
- ✅ Mutation log
- ✅ Telemetry streaming
- ✅ State export

**You're no longer flying blind. You have mission control.**
