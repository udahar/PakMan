# Software Evolution Engine - Complete Architecture

**Darwin for Software.** 🧬

---

## The Big Picture

```
┌──────────────────────────────────────────────────────────────────┐
│                  SOFTWARE EVOLUTION ENGINE                        │
│                                                                   │
│  "Natural selection for AI tools"                                │
└──────────────────────────────────────────────────────────────────┘

     Inspiration      →    Mutation       →      Design
         ↓                   ↓                      ↓
    ┌─────────┐        ┌─────────┐          ┌─────────┐
    │  Frank  │        │ GapMan  │          │ ProjMan │
    │         │        │         │          │         │
    │ Mines   │        │ Combines│          │ Creates │
    │ patterns│        │ fragments│         │ tickets │
    └────┬────┘        └────┬────┘          └────┬────┘
         │                  │                     │
         │                  │                     ↓
         │                  │              ┌─────────┐
         │                  │              │Autocoder│
         │                  │              │         │
         │                  │              │ Generates│
         │                  │              │ code    │
         │                  │              └────┬────┘
         │                  │                   │
         │                  │                   ↓
         │                  │              ┌─────────┐
         │                  │              │  Bench  │
         │                  │              │         │
         │                  │              │ Tests   │
         │                  │              │ Fitness │
         │                  │              └────┬────┘
         │                  │                   │
         │                  │                   ↓
         │                  │              ┌─────────┐
         └──────────────────┴─────────────→│ PkgMan  │
                          (Survivors)      │         │
                                           │ Distrib │
                                           └─────────┘
```

---

## The 6 Components

### 1. **Frank** - Inspiration Mining

**Purpose:** Extract design patterns from existing repos (no code copying)

**Input:**
- List of repos to study (LangChain, AutoGen, etc.)
- Focus areas (APIs, architectures, patterns)

**Output:**
```python
DesignFragment = {
    "name": "vector_cache",
    "category": "caching",
    "inputs": ["prompt", "embedding"],
    "outputs": ["cached_response"],
    "dependencies": ["qdrant", "redis"],
    "methods": ["store()", "retrieve()", "clear()"],
    "complexity": "low",
    "usefulness": 0.85
}
```

**NOT COPIED:**
- ❌ Actual implementation code
- ❌ Specific variable names
- ❌ Repo-specific logic

**EXTRACTED:**
- ✅ Architectural patterns
- ✅ API designs
- ✅ Dependency patterns
- ✅ Common workflows

---

### 2. **GapMan** - Mutation Engine

**Purpose:** Combine fragments into new package candidates

**Input:**
- Design fragments (from Frank)
- Your existing toolkit (from PkgMan)
- Gap analysis (what's missing)

**Process:**
```python
# Mutation strategies
strategies = [
    "combine(fragment_a, fragment_b)",     # Merge two fragments
    "extend(fragment, new_feature)",        # Add capability
    "specialize(fragment, niche)",          # Focus on niche
    "simplify(fragment)",                   # Remove complexity
    "adapt(fragment, new_domain)",          # Apply to new domain
]

# Example mutations
candidate1 = combine(
    fragment("vector_cache"),
    fragment("CLI"),
    fragment("monitoring")
)
# Result: "cli_vector_cache_monitor"

candidate2 = specialize(
    fragment("embedding_store"),
    niche="conversation_history"
)
# Result: "conversation_embedding_store"
```

**Output:**
```python
PackageCandidate = {
    "name": "cli_vector_cache",
    "fragments": ["vector_cache", "CLI"],
    "score": 0.87,
    "novelty": 0.9,
    "usefulness": 0.85,
    "gap_fill": 0.88,
    "complexity": "medium",
    "estimated_effort": "2 days"
}
```

---

### 3. **Sanity Filter** - Quality Gate

**Purpose:** Kill bad ideas before they waste time

**Scoring Algorithm:**
```python
def score_candidate(candidate):
    score = (
        novelty * 0.25 +       # Is it new? (0-1)
        usefulness * 0.35 +    # Is it useful? (0-1)
        gap_fill * 0.25 +      # Does it fill a gap? (0-1)
        simplicity * 0.15      # Is it simple? (0-1)
    )
    
    # Penalties
    if candidate.conflicts_with_existing():
        score -= 0.3
    if candidate.too_complex():
        score -= 0.2
    if candidate.similar_to_existing():
        score -= 0.1
    
    return score

# Filter
candidates = [c for c in candidates if score(c) > 0.7]
```

**Output:** Top 10-20 candidates (from 50-100 generated)

---

### 4. **ProjMan** - Design & Specification

**Purpose:** Turn candidates into buildable specs (NOT evaluation)

**Input:** Package candidates (filtered)

**Process: The Debate Loop**
```python
def debate_loop(candidate, rounds=3):
    spec = candidate.initial_spec()
    
    for round in range(rounds):
        # Architect proposes
        proposal = architect_ai.propose(spec)
        
        # Critic attacks
        criticisms = critic_ai.attack(proposal)
        
        # Optimizer fixes
        spec = optimizer_ai.fix(proposal, criticisms)
    
    return final_spec
```

**Output:**
```python
BuildTicket = {
    "name": "vector_cache_cli",
    "purpose": "CLI tool for managing vector caches",
    "interfaces": {
        "store": "store(prompt: str, response: str) -> bool",
        "retrieve": "retrieve(prompt: str) -> Optional[str]",
        "clear": "clear() -> int"
    },
    "dependencies": ["qdrant-client", "click", "redis"],
    "files": [
        "vector_cache_cli/__init__.py",
        "vector_cache_cli/cli.py",
        "vector_cache_cli/cache.py"
    ],
    "tests": [
        "test_cache.py",
        "test_cli.py"
    ],
    "difficulty": "low",
    "estimated_time": "2 days",
    "success_criteria": [
        "CLI commands work",
        "Cache stores/retrieves correctly",
        "Tests pass"
    ]
}
```

**NOTE:** No evaluation here - that's Bench's job!

---

### 5. **Autocoder** - Code Generation

**Purpose:** Generate code from specs

**Input:** Build tickets (from ProjMan)

**Process:**
```python
def generate_code(ticket):
    # Generate file structure
    for file in ticket.files:
        code = coder_ai.generate(
            spec=ticket,
            file=file,
            style="clean",
            tests=True
        )
        save(file, code)
    
    # Generate tests
    for test in ticket.tests:
        test_code = test_ai.generate(
            spec=ticket,
            test_file=test
        )
        save(test, test_code)
    
    # Generate docs
    generate_readme(ticket)
    generate_docstrings(ticket)
```

**Output:**
```
vector_cache_cli/
├── __init__.py
├── cli.py
├── cache.py
├── tests/
│   ├── test_cache.py
│   └── test_cli.py
├── README.md
└── requirements.txt
```

---

### 6. **Bench** - Fitness Testing

**Purpose:** Evaluate if packages are worth keeping

**Input:** Generated packages (from Autocoder)

**Tests:**
```python
def evaluate_package(package):
    scores = {
        "builds": test_builds(package),           # Does it install?
        "tests_pass": test_suite(package),        # Do tests pass?
        "api_works": test_api(package),           # Does API work?
        "performance": test_performance(package), # Is it fast?
        "memory": test_memory(package),           # Memory usage
        "compatibility": test_compat(package),    # Works with others?
    }
    
    # Overall fitness score
    fitness = sum(scores.values()) / len(scores)
    
    return {
        "scores": scores,
        "fitness": fitness,
        "survives": fitness > 0.7
    }
```

**Output:**
```python
EvaluationResult = {
    "package": "vector_cache_cli",
    "fitness": 0.87,
    "survives": True,
    "scores": {
        "builds": 1.0,
        "tests_pass": 0.95,
        "api_works": 0.9,
        "performance": 0.8,
        "memory": 0.85,
        "compatibility": 0.75
    },
    "issues": ["Could be faster", "Memory usage high"],
    "recommendation": "KEEP - Good candidate"
}
```

**Survivors → PkgMan**
**Failures → Back to GapMan (mutate again)**

---

### 7. **PkgMan** - Ecosystem Distribution

**Purpose:** Install surviving packages into ecosystem

**Input:** Evaluated packages (from Bench)

**Process:**
```python
def distribute(package):
    if package.evaluation.survives:
        # Add to PkgMan catalog
        pkgman.add_package(package)
        
        # Make available for install
        pkgman.make_available(package.name)
        
        # Track usage
        pkgman.track_install(package.name)
```

**Output:**
```python
from PkgMan import install

install("vector_cache_cli")  # Available!
```

---

## The Evolution Loop

```
┌─────────────────────────────────────────────────────────────┐
│                     EVOLUTION LOOP                           │
│                                                              │
│  1. Frank mines patterns from repos                         │
│         ↓                                                    │
│  2. GapMan mutates fragments into candidates                │
│         ↓                                                    │
│  3. Sanity Filter kills bad ideas                           │
│         ↓                                                    │
│  4. ProjMan creates specs (debate loop)                     │
│         ↓                                                    │
│  5. Autocoder generates code                                │
│         ↓                                                    │
│  6. Bench evaluates fitness                                 │
│         ↓                                                    │
│  7. Survivors → PkgMan ecosystem                            │
│         ↓                                                    │
│  8. Failures → Back to GapMan (mutate again)               │
│         ↓                                                    │
│  REPEAT                                                     │
│                                                              │
│  Result: Evolving toolkit of useful tools                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Production Rate

**Per Day:**
- Frank mines: 10-20 repos
- GapMan generates: 50 candidates
- Sanity Filter: 10 survive
- ProjMan specs: 5-10 tickets
- Autocoder: 3-5 packages
- Bench: 3-5 evaluations
- PkgMan: 2-3 survivors

**Per Month:** ~60-90 quality packages
**Per Year:** ~700-1000 packages (but only 120-300 good ones)

---

## Why This Works

1. **Frank** - Clean inspiration (no copying)
2. **GapMan** - Intelligent mutation (not random)
3. **Sanity Filter** - Quality gate (no spaghetti)
4. **ProjMan** - Structured specs (debate loop)
5. **Autocoder** - Clean code (from specs)
6. **Bench** - Survival of fittest (real testing)
7. **PkgMan** - Ecosystem (distribution)

**Natural selection for software.** 🧬

---

## What NOT to Release

**Vault-Worthy (Secret Sauce):**
1. Frank's pattern extraction algorithm
2. GapMan's mutation strategies
3. Sanity Filter scoring algorithm
4. Debate loop prompts
5. Bench's fitness criteria

**Can Release:**
- PkgMan (package manager)
- ProjMan (ticket system)
- Individual generated packages

**The evolution engine itself stays private.**

---

**Version:** 1.0
**Status:** Architecture Complete
**Next:** Build all 6 components
