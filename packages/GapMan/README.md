# GapMan - Complete Software Evolution Engine

**Darwin for Software.** 🧬

All-in-one evolution engine: Pattern mining → Mutation → Filtering → Specs → Code → Evaluation.

---

## Quick Start

```python
from GapMan import evolve_toolkit

# Mine repos, mutate, filter, spec, code, evaluate
results = evolve_toolkit([
    "github.com/langchain-ai/langchain",
    "github.com/microsoft/autogen",
], max_candidates=10)

# Get ProjMan tickets
for ticket in results["final_packages"]:
    print(f"Build: {ticket['title']}")
```

---

## The 6 Components (All in GapMan)

### 1. Frank - Pattern Mining
```python
from GapMan import mine_patterns

patterns = mine_patterns(["github.com/langchain-ai/langchain"])
```

### 2. Mutation - Combine Fragments
```python
from GapMan import mutate_fragments

candidates = mutate_fragments([p.to_dict() for p in patterns])
```

### 3. Sanity - Quality Gate
```python
from GapMan import sanity_filter

filtered = sanity_filter([c.to_dict() for c in candidates])
```

### 4. Spec - Generate Specs
```python
from GapMan import generate_build_spec

spec = generate_build_spec(filtered[0])
```

### 5. Autocoder - Generate Code
```python
from GapMan import generate_code

code = generate_code(spec.to_dict())
```

### 6. Bench - Evaluate
```python
from GapMan import evaluate_package

result = evaluate_package({"spec": spec.to_dict(), "code": code})
print(f"Fitness: {result['fitness']}, Survives: {result['survives']}")
```

---

## Full Evolution Cycle

```python
from GapMan import EvolutionEngine

engine = EvolutionEngine()
results = engine.evolve(
    repos=["github.com/langchain-ai/langchain"],
    max_candidates=10
)

print(f"Patterns mined: {results['stats']['patterns_mined']}")
print(f"Candidates generated: {results['stats']['candidates_generated']}")
print(f"Packages survived: {results['stats']['packages_survived']}")
print(f"Final tickets: {len(results['final_packages'])}")
```

---

## Files (All Inside GapMan/)

```
GapMan/
├── __init__.py          ← Main exports
├── frank.py             ← Pattern mining
├── mutation.py          ← Fragment mutation
├── sanity.py            ← Quality filtering
├── spec.py              ← Spec generation
├── autocoder.py         ← Code generation
├── bench.py             ← Evaluation
├── orchestrator.py      ← Main engine
└── README.md            ← This file
```

---

## Output

**Results include:**
- `final_packages`: List of ProjMan tickets ready to build
- `stats`: Evolution statistics
- `steps`: Each step's results

**Each ticket includes:**
- Title, description, spec
- Priority, estimated hours
- Files to generate
- Tests to write
- Dependencies

---

## Status

**✅ Complete:**
- Pattern mining (Frank)
- Mutation engine
- Sanity filter
- Spec generator
- Code generator
- Evaluator (Bench)
- Orchestrator

**Ready to use!**

---

**Version:** 2.0 (Complete Evolution Engine)
**Location:** `C:\Users\Richard\clawd\Frank\PromptRD\GapMan\`
