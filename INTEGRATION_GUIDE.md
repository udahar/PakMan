# ModLib Integration Guide

**Purpose:** Integrate the Module Library Registry with Frank AI

**Date:** 2026-03-08

---

## The Problem

You have **two parallel skill systems**:

### System 1: `/src/modules/` (LangChain-based)
- **255 trainable skills** in skills_registry
- **LangChain tool execution** in skills_framework
- **Multi-model orchestration** 
- **Prompt library** management
- **Scheduler** for jobs

### System 2: `/PromptRD/` (Prompt Engineering)
- **26 prompt engineering skills**
- **Multi-skill chains** (planner)
- **Ticket-based execution**
- **Background worker**
- **Learning system**

---

## The Solution: ModLib

**ModLib** provides a **unified registry** that:

1. **Discovers** all modules automatically
2. **Reports** status (online/offline/degraded)
3. **Exposes** capabilities
4. **Monitors** health
5. **Enables** self-aware AI operations

---

## Architecture

```
Frank AI Platform
│
├── ModLib (Registry Layer) ← NEW
│   ├── scan_modules()
│   ├── list_modules()
│   ├── get_capabilities()
│   └── check_health()
│
├── PromptRD Module
│   ├── 26 prompt skills
│   ├── skill_planner.py
│   ├── ticket_executor.py
│   ├── frank_worker.py
│   └── skill_graph_viz.py
│
└── /src/modules/ (Existing)
    ├── skills_registry (255 skills)
    ├── skills_framework (LangChain)
    ├── multi_model_orchestrator
    ├── prompt_library
    ├── recursive_context
    └── scheduler
```

---

## Usage

### Python API

```python
from ModLib import modules, status, get_registry

# Quick status
print(status())

# Output:
# 🟢 PromptRD – online
# 🟢 SkillsRegistry – online
# 🟢 MultiModelOrchestrator – online
# ...

# List all modules
for m in modules():
    print(f"{m['name']}: {m['status']} - {m['capabilities']}")

# Detailed info
registry = get_registry()
promptrd = registry.get_module("PromptRD")
print(f"PromptRD has {promptrd['capabilities']}")
```

### CLI

```bash
# Show all modules
python -m ModLib

# Show capabilities
python -m ModLib --capabilities

# Health check
python -m ModLib --health

# From frank.py
./frank --modules
```

---

## Integration Points

### 1. Frank CLI Integration

Added `--modules` flag to `frank.py`:

```bash
./frank --modules

# Output:
# 📦 Module Registry
# ============================================================
# 🟢 PromptRD – online
# 🟢 SkillsRegistry – online
# 🟢 MultiModelOrchestrator – online
# ...
```

### 2. Self-Aware Operations

Frank can now check what's available before executing:

```python
from ModLib import get_registry

registry = get_registry()

# Check if PromptRD is available
if registry.get_module("PromptRD")["status"] == "online":
    # Use prompt engineering skills
    result = await run_task("Research topic")
else:
    # Fallback to basic execution
    result = await basic_execute()

# Check if LangChain skills are available
if registry.get_module("SkillsRegistry")["status"] == "online":
    # Use 255 trainable skills
    skills = registry.get_module("SkillsRegistry")["capabilities"]
```

### 3. Health Monitoring

```python
from ModLib import get_registry

registry = get_registry()
health = registry.check_health()

for module, score in health.items():
    if score < 0.5:
        # Alert: module degraded
        print(f"⚠️ {module} health is {score*100:.0f}%")
```

---

## Module Discovery

### Auto-Discovered Locations

```python
# Scanned automatically
/ Frank/src/modules/          # All subdirectories
/ Frank/PromptRD/             # As single module
/ Frank/PromptForge/          # If exists
/ Frank/BabbleBridge/         # If exists
```

### Module Requirements

To be auto-discovered, a module needs:

1. `__init__.py` file
2. Directory in scanned location
3. No leading underscore in name

### Manual Registration

```python
from ModLib import get_registry, ModuleInfo

registry = get_registry()

registry.modules["custom_module"] = ModuleInfo(
    name="custom_module",
    version="1.0",
    path="/path/to/module",
    status="online",
    capabilities=["feature1", "feature2"],
    endpoints=["endpoint1"]
)
```

---

## Capabilities Mapping

### PromptRD Capabilities

```json
{
  "name": "PromptRD",
  "version": "4.0",
  "capabilities": [
    "26 prompt engineering skills",
    "Multi-skill chain orchestration",
    "Ticket-based execution",
    "Autonomous background worker",
    "CLI interface",
    "Skill learning",
    "Graph visualization"
  ],
  "endpoints": [
    "./frank --execute",
    "./frank --map",
    "./frank --plan",
    "./frank --learning",
    "./frank --worker"
  ]
}
```

### SkillsRegistry Capabilities

```json
{
  "name": "SkillsRegistry",
  "version": "1.0",
  "capabilities": [
    "255 trainable skills",
    "LangChain tool execution",
    "Skill routing",
    "Performance tracking"
  ],
  "endpoints": [
    "create_skills_registry()",
    "create_skill_router()"
  ]
}
```

---

## Future Integration Opportunities

### 1. Unified Skill Execution

```python
# Combine both skill systems
from PromptRD import run_task as prompt_run
from src.modules.skills_framework import create_skill_executor

# Use PromptRD for reasoning tasks
result1 = await prompt_run("Research quantum computing")

# Use LangChain skills for tool tasks
executor = create_skill_executor()
result2 = executor.execute_skill("file_read", "/path/to/file")
```

### 2. Cross-Module Orchestration

```python
# Multi-model orchestrator + PromptRD skills
from src.modules.multi_model_orchestrator import create_orchestrator
from PromptRD.skill_planner import get_planner

orchestrator = create_orchestrator()
planner = get_planner()

# Plan skill chain
plan = await planner.create_plan("Debug this code")

# Execute with multiple models
result = await orchestrator.execute_chain(plan)
```

### 3. Shared Learning

```python
# Both systems learn from each other
from PromptRD.skill_learning import get_learner
from src.modules.skills_registry import create_skills_registry

prompt_learner = get_learner()
langchain_registry = create_skills_registry()

# Share success metrics
for skill_id, metrics in prompt_learner.get_metrics().items():
    langchain_registry.update_skill_stats(
        f"prompt_{skill_id}",
        metrics["success_rate"]
    )
```

---

## Files Created

| File | Purpose | Lines |
|------|---------|-------|
| `ModLib/__init__.py` | Module registry | ~350 |
| `ModLib/__main__.py` | CLI interface | ~100 |
| `ModLib/README.md` | Documentation | ~200 |

**Total:** ~650 lines

---

## Testing

```bash
# Test ModLib
python -m ModLib
python -m ModLib --capabilities
python -m ModLib --health

# Test from frank.py
./frank --modules
```

---

## Benefits

### 1. Self-Awareness ✅

Frank can now introspect its own capabilities:

```python
from ModLib import modules

available = [m["name"] for m in modules() if m["status"] == "online"]
print(f"Available: {available}")
```

### 2. Health Monitoring 🟡

Track module health over time:

```python
health = registry.check_health()
# Alert if health drops
```

### 3. Graceful Degradation 🟡

Fallback when modules unavailable:

```python
if registry.get_module("PromptRD")["status"] == "offline":
    # Use alternative
    pass
```

### 4. Discovery ✅

Find new modules automatically:

```python
# Just drop module in /src/modules/
# Auto-discovered on next scan
```

---

## Next Steps

### Phase 1: Basic Integration ✅
- [x] Create ModLib
- [x] Auto-discovery
- [x] CLI interface
- [x] Frank integration

### Phase 2: Health Monitoring 🟡
- [ ] Ping endpoints
- [ ] Check dependencies
- [ ] Track over time

### Phase 3: Cross-Module Orchestration 🔴
- [ ] Unified skill API
- [ ] Shared learning
- [ ] Multi-model + PromptRD chains

### Phase 4: Self-Healing 🔴
- [ ] Auto-restart failed modules
- [ ] Fallback mechanisms
- [ ] Load balancing

---

**Status:** ✅ Phase 1 Complete  
**Version:** 1.0  
**Next:** Health monitoring integration
