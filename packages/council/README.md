# The Council - Multi-Mind AI Architecture

A distributed decision-making system where specialized AI models serve different roles.

## The Five Roles

### 1. Planner
**Role:** Strategy and creativity
**Responsibility:** Proposes solutions and pipelines
**Does NOT:** Execute anything

### 2. Engineer
**Role:** Technical validation
**Responsibility:** Checks feasibility, tool compatibility
**Does NOT:** Design solutions

### 3. Scientist
**Role:** Data-driven evaluation
**Responsibility:** Analyzes metrics, recommends based on performance
**Does NOT:** Make final decisions

### 4. Governor
**Role:** Safety enforcement
**Responsibility:** Enforces rules, budgets, constraints
**Does NOT:** Creative work

### 5. Archivist
**Role:** Memory and history
**Responsibility:** Tracks lineage, records decisions
**Does NOT:** Active decision-making

## Council Flow

```
Task arrives
    ↓
Planner proposes solution
    ↓
Engineer validates feasibility
    ↓
Scientist evaluates performance data
    ↓
Governor checks safety constraints
    ↓
Archivist records decision
    ↓
Pipeline executes (if all approve)
```

## Files

- `council/__init__.py` - Package exports
- `council/roles.py` - Role definitions
- `council/planner.py` - Strategy role
- `council/engineer.py` - Technical validation
- `council/scientist.py` - Data analysis
- `council/governor.py` - Safety enforcement
- `council/archivist.py` - Memory/records
- `council/decision.py` - Decision aggregation
- `council/session.py` - Council session management

## Usage

```python
from council import Council

council = Council()

decision = council.deliberate({
    "task": "analyze repo architecture",
    "context": {...}
})

if decision.approved:
    execute(decision.pipeline)
```

## Model Assignment

Different models can fill different roles:

- **Planner:** Claude (creative reasoning)
- **Engineer:** Codex/Qwen (code expertise)
- **Scientist:** Gemini (data analysis)
- **Governor:** Rule engine (deterministic)
- **Archivist:** Small local model (efficiency)

## Voting

Major decisions require:
- Engineer: ✅ (technical feasibility)
- Governor: ✅ (safety compliance)
- Scientist: Score > threshold (performance confidence)

---

**Status:** In Development
