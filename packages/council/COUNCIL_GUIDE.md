# The Council - Multi-Mind AI Architecture

**Status:** ✅ Core Architecture Complete

A distributed decision-making system where specialized AI models serve different roles in a checks-and-balances architecture.

---

## The Five Judges

### 1. Planner 🎯
**Role:** Strategy and creativity  
**Responsibility:** Proposes solutions and pipelines  
**Does NOT:** Execute anything

```python
planner = Planner(model="claude-3.5")
response = planner.deliberate(context)
# → Proposes: repo_index → context_pack → prompt_fmt
```

### 2. Engineer 🔧
**Role:** Technical validation  
**Responsibility:** Checks feasibility, tool compatibility  
**Does NOT:** Design solutions

```python
engineer = Engineer(model="codex")
response = engineer.deliberate(context)
# → Validates: tools exist, memory OK, warnings=[]
```

### 3. Scientist 🔬
**Role:** Data-driven evaluation  
**Responsibility:** Analyzes metrics, recommends based on performance  
**Does NOT:** Make final decisions

```python
scientist = Scientist(model="gemini-pro")
response = scientist.deliberate(context)
# → Analyzes: observatory data, performance scores
```

### 4. Governor ⚖️
**Role:** Safety enforcement  
**Responsibility:** Enforces rules, budgets, constraints  
**Does NOT:** Creative work

```python
governor = Governor()  # Rule engine (deterministic)
response = governor.deliberate(context)
# → Checks: allowed capabilities, budget remaining
```

### 5. Archivist 📚
**Role:** Memory and history  
**Responsibility:** Tracks lineage, records decisions  
**Does NOT:** Active decision-making

```python
archivist = Archivist(model="llama3.2")
response = archivist.deliberate(context)
# → Records: decision archived, record_id=42
```

---

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

---

## Usage

### Basic Deliberation

```python
from council import CouncilSession

session = CouncilSession()

decision = session.deliberate({
    "task": "Analyze the repository architecture",
    "context": {...}
})

if decision.approved:
    execute(decision.proposed_pipeline)
else:
    print(f"Rejected: {decision.reasoning}")
```

### Check Decision Status

```python
print(f"Status: {decision.status.value}")      # approved/rejected
print(f"Confidence: {decision.confidence:.1%}") # 0.62 = 62%
print(f"Execution Allowed: {decision.execution_allowed}")
print(f"Human Review Needed: {decision.requires_human_review}")
```

### Get Role Votes

```python
for role, input_data in decision.get_role_votes().items():
    print(f"{role}: {input_data}")
```

---

## Decision States

| Status | Meaning |
|--------|---------|
| `APPROVED` | All roles approved, execution allowed |
| `REJECTED` | Engineer or Governor vetoed |
| `PENDING` | Deliberation in progress |
| `NEEDS_REVISION` | Requires changes before approval |

---

## Approval Requirements

For a decision to be approved:

1. **Engineer:** ✅ Must approve (technical feasibility)
2. **Governor:** ✅ Must approve (safety compliance)
3. **Scientist:** Score considered (performance confidence)
4. **Planner:** Proposal required (strategy)
5. **Archivist:** Records regardless (memory)

**Veto Power:**
- Engineer can reject for technical infeasibility
- Governor can reject for safety violations

---

## Model Assignment

Different models can fill different roles:

```python
session = CouncilSession(
    planner=Planner(model="claude-3.5"),      # Creative reasoning
    engineer=Engineer(model="codex"),         # Code expertise
    scientist=Scientist(model="gemini-pro"),  # Data analysis
    governor=Governor(),                       # Rule engine
    archivist=Archivist(model="llama3.2"),    # Efficient local
)
```

**Benefits:**
- No single model controls everything
- Each model does what it's best at
- Diversity prevents blind spots

---

## Statistics

```python
stats = session.get_stats()

print(f"Sessions: {stats['session_count']}")
print(f"Planner calls: {stats['planner']['call_count']}")
print(f"Engineer calls: {stats['engineer']['call_count']}")
```

---

## Example Output

```
============================================================
  COUNCIL DEMO - Basic Deliberation
============================================================

Task: Analyze the repository architecture

Decision: [✅] Analyze the repository architecture
Status: approved
Confidence: 62.5%
Execution Allowed: True
Requires Human Review: True

Role Inputs:
  planner: {'task': '...', 'proposed_pipeline': [...]}
  engineer: {'feasible': True, 'tools_available': True}
  scientist: {'performance_score': 0.85, ...}
  governor: {'approved': True, 'constraints': []}
  archivist: {'recorded': True, 'record_id': 1}

Reasoning:
  All roles approved
```

---

## Files

| File | Purpose |
|------|---------|
| `roles.py` | Role definitions (Planner, Engineer, etc.) |
| `decision.py` | Decision aggregation |
| `session.py` | Council session management |
| `demo.py` | Demo script |

---

## Integration Points

### With Rust Runtime

```python
# Council decides, Rust executes
decision = session.deliberate(task)

if decision.approved:
    # Call rustutils
    subprocess.run(["rustutils"] + decision.proposed_pipeline)
    
    # Report back to observatory
    observatory.record_execution(...)
```

### With Observatory

```python
# Scientist reads observatory data
context.observatory_data = observatory.get_pipeline_stats()

decision = session.deliberate(task, context)
```

### With Memory

```python
# Archivist stores in memory
context.memory_data = memory_client.get_ticket_context(ticket_id)

decision = session.deliberate(task, context)
archivist.record(decision)
```

---

## The King-of-the-Hill Model

Future enhancement: Tournament system for role assignment.

```python
# Models compete for roles based on performance
tournament = ModelTournament()

best_planner = tournament.compete(
    role="planner",
    candidates=["claude", "gpt4", "gemini"]
)

# Winner gets the role
session.planner = Planner(model=best_planner)
```

---

## Why This Matters

### Prevents Dictatorship
No single model makes all decisions.

### Enables Specialization
Each model does what it's best at.

### Data-Driven Decisions
Scientist role ensures metrics matter.

### Safety Built-In
Governor can veto any unsafe proposal.

### Historical Memory
Archivist tracks all decisions for learning.

---

## Demo

```bash
cd C:\Users\Richard\clawd\Frank\council
python demo.py
```

---

## Next Steps

1. **Connect to LLM APIs** - Replace stubs with real model calls
2. **Integrate Observatory** - Scientist reads real metrics
3. **Add Governor Rules** - Connect to Rust governor via MCP
4. **Archivist Persistence** - Store decisions in Postgres
5. **Model Tournament** - King-of-the-hill competition

---

**The Council is ready. The Judges await their first case.** ⚖️
