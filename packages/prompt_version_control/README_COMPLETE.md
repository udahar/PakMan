# Prompt Version Control - Complete System

**Status:** ✅ Complete Architecture

Git-like version control for LLM prompts with branching, merging, benchmarking, and visual diff.

---

## Quick Start

```bash
cd PromptRD/prompt_version_control

# Initialize
python cli.py init

# Commit a prompt
python cli.py commit "You are a helpful assistant" \
  -m "Initial prompt" \
  --system "Be concise" \
  --model qwen2.5:7b \
  --tag production

# View history
python cli.py log

# Create branch
python cli.py branch experiment_v1

# Test a version
python cli.py test <version_id> "Hello, how are you?"

# Compare versions
python cli.py diff abc123 def456

# View stats
python cli.py stats
```

---

## Features

### 1. Version Control
- Commit prompts with metadata
- Branch for experiments
- Merge changes back
- Tag releases (v1.0, v2.0)

### 2. Benchmarking
- Run standardized tests
- Track latency, quality, tokens
- Compare versions
- Save metrics to commits

### 3. Visual Diff
- See what changed between versions
- Compare prompt text
- Compare system prompts
- Compare metrics

### 4. Integration
- Works with existing prompt library
- Integrates with benchmark arena
- KOFH tournament compatibility
- Council role assignment

---

## Commands

| Command | Description |
|---------|-------------|
| `init` | Initialize repository |
| `commit` | Commit new version |
| `log` | View history |
| `show` | Show specific version |
| `diff` | Compare versions |
| `branch` | Create branch |
| `branches` | List branches |
| `tag` | Create tag |
| `tags` | List tags |
| `merge` | Merge branches |
| `test` | Test a version |
| `stats` | Repository stats |

---

## Database Schema

```sql
-- Commits table
CREATE TABLE commits (
    id TEXT PRIMARY KEY,
    prompt TEXT NOT NULL,
    system TEXT,
    model TEXT NOT NULL,
    branch TEXT NOT NULL,
    parent_id TEXT,
    commit_message TEXT,
    tags TEXT,
    metrics TEXT,
    config_hash TEXT,
    created_at TEXT NOT NULL
);

-- Branches table
CREATE TABLE branches (
    name TEXT PRIMARY KEY,
    head_commit_id TEXT,
    created_at TEXT
);

-- Tags table
CREATE TABLE tags (
    name TEXT PRIMARY KEY,
    commit_id TEXT NOT NULL,
    created_at TEXT
);
```

---

## Files

| File | Purpose |
|------|---------|
| `prompt_repo_enhanced.py` | Core repository with Git-like ops |
| `cli.py` | Command-line interface |
| `benchmarking.py` | Benchmark integration |
| `web_ui.py` | Visual interface (TODO) |
| `README.md` | This documentation |

---

## Example Workflow

```bash
# Start on main branch
python cli.py commit "You are a coding assistant" \
  -m "Initial coding assistant" \
  --tag v1.0

# Create experiment branch
python cli.py branch gpt4_optimized

# Commit optimized version
python cli.py commit "You are an expert Python developer" \
  -m "Optimized for GPT-4" \
  --model gpt-4

# Test both versions
python cli.py test abc123 "Write a function to sort a list"
python cli.py test def456 "Write a function to sort a list"

# Compare results
python cli.py diff abc123 def456

# Merge if better
python cli.py merge gpt4_optimized --into main

# Tag release
python cli.py tag v2.0 $(python cli.py branches | head -1)
```

---

## Integration with KOFH

```python
from prompt_version_control import PromptRepo
from kofh import TournamentSystem

repo = PromptRepo()
tournament = TournamentSystem()

# Get best prompt for each role from tournament
for role in ["planner", "engineer", "scientist"]:
    king = tournament.get_throne_holder(role)
    
    # Find prompt version optimized for this model
    versions = repo.log(branch=f"{role}_prompts")
    best_version = max(versions, key=lambda v: v.metrics.get('quality_score', 0))
    
    print(f"{role} king: {king} uses prompt {best_version.id}")
```

---

## Integration with Council

```python
from council import CouncilSession
from prompt_version_control import PromptRepo

repo = PromptRepo()
council = CouncilSession()

# Load best prompts for each role
planner_prompt = repo.checkout("planner_v3")
engineer_prompt = repo.checkout("engineer_v2")

# Assign to council roles
council.planner = Planner(
    model=planner_prompt.model,
    system=planner_prompt.system,
)
```

---

## Benchmark Integration

```python
from benchmarking import PromptBenchmarker, EXAMPLE_TEST_SUITES

bench = PromptBenchmarker()

# Register test suites
for name, tests in EXAMPLE_TEST_SUITES.items():
    bench.register_test_suite(name, tests)

# Run benchmark suite
results = bench.run_test_suite(
    version_id="abc123",
    prompt="You are a helpful assistant",
    system="Be concise",
    model="qwen2.5:7b",
    suite_name="code_generation",
)

# Save to repo
repo.update_metrics("abc123", {
    "avg_latency_ms": sum(r.latency_ms for r in results) / len(results),
    "avg_quality_score": sum(r.quality_score for r in results) / len(results),
})
```

---

## Best Practices

### 1. Branch Strategy
```
main              → Production prompts
├── experiments   → Testing new approaches
├── gpt4_branch   → GPT-4 optimized
├── claude_branch → Claude optimized
└── qwen_branch   → Qwen optimized
```

### 2. Tagging
```
v1.0.0  → Initial release
v1.1.0  → Minor improvements
v2.0.0  → Major revision
```

### 3. Commit Messages
```
feat: Add system prompt for code generation
fix: Improve error handling
perf: Optimize for latency
test: Add benchmark tests
```

### 4. Metrics to Track
- Latency (ms)
- Quality score (0-1)
- Token count
- Cost estimate
- User rating (if applicable)

---

## Future Enhancements

- [ ] Web UI for visual diff
- [ ] A/B testing deployment
- [ ] Automatic rollback on quality drop
- [ ] Model-specific optimization suggestions
- [ ] Prompt template variables
- [ ] Multi-language support
- [ ] Export/import between repos
- [ ] Remote sync (like git push/pull)

---

**Prompt Version Control is ready for production!** 🎯📝
