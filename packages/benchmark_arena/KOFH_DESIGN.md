# King-of-the-Hill Tournament System

**Status:** 👑 In Development

A competitive model tournament where AI models fight for council seats. No permanent positions - only performance matters.

---

## The Concept

Every model enters a pool. They compete for **four throne seats**:

```
🎯 Planner Throne
🔧 Engineer Throne  
🔬 Scientist Throne
📊 Analyst Throne
```

The highest scorer becomes **King** of that role until dethroned.

---

## Scoring Formula

```python
final_score = (
    quality * 0.6 +      # Output quality
    reliability * 0.2 +  # Consistency
    speed * 0.2          # Latency score
)
```

**Thresholds:**
- Minimum quality: 80
- Minimum reliability: 90

Below threshold → Challenger pool (cannot win throne)

---

## Role Test Suites

### Planner Throne Tests

Tests reasoning and orchestration:

```python
tests = [
    "build_pipeline",           # Create tool chain
    "decompose_problem",        # Break down complex task
    "choose_tools",             # Select appropriate tools
    "plan_recovery",            # Handle failure scenario
    "optimize_workflow",        # Improve existing pipeline
]
```

### Engineer Throne Tests

Tests code generation and validation:

```python
tests = [
    "fix_broken_rust",          # Debug compilation error
    "generate_tool_skeleton",   # Create new tool template
    "validate_pipeline",        # Check tool compatibility
    "write_test_harness",       # Generate tests
    "refactor_code",            # Improve existing code
]
```

### Scientist Throne Tests

Tests data analysis and interpretation:

```python
tests = [
    "analyze_telemetry",        # Interpret metrics
    "compare_pipelines",        # A/B test analysis
    "detect_anomalies",         # Find outliers
    "recommend_optimization",   # Suggest improvements
    "statistical_significance", # Validate results
]
```

### Analyst Throne Tests

Tests information synthesis:

```python
tests = [
    "summarize_research",       # Condense information
    "extract_insights",         # Find key points
    "compare_sources",          # Cross-reference data
    "identify_gaps",            # Find missing information
    "generate_report",          # Structured output
]
```

---

## Leaderboard Example

```
╔══════════════════════════════════════════════════════════╗
║              ENGINEER THRONE LEADERBOARD                  ║
╠══════════════════════════════════════════════════════════╣
║  👑 codex              96.2    520ms    KING             ║
║  2  qwen-coder         91.4    420ms    Challenger       ║
║  3  deepseek-coder     88.7    380ms    Challenger       ║
║  4  claude-3.5         85.3    890ms    Challenger       ║
╚══════════════════════════════════════════════════════════╝

╔══════════════════════════════════════════════════════════╗
║              PLANNER THRONE LEADERBOARD                   ║
╠══════════════════════════════════════════════════════════╣
║  👑 claude-3.5         94.1    890ms    KING             ║
║  2  gemini-pro         90.3    650ms    Challenger       ║
║  3  llama-3.2          83.7    120ms    Challenger       ║
╚══════════════════════════════════════════════════════════╝
```

---

## Throne Swap Logic

```python
# Current king must be beaten by ≥3%
def should_swap_throne(current_king_score, challenger_score):
    threshold = current_king_score * 1.03  # 3% buffer
    return challenger_score > threshold
```

**Example:**
- Current king: 96.2
- Challenger needs: 96.2 × 1.03 = **99.1** to win

This prevents constant throne-flipping from tiny score differences.

---

## Automatic Challenges

When a new model appears:

```python
def on_new_model(model_name):
    # Schedule trial matches
    tournament.schedule_evaluation(
        model=model_name,
        roles=["planner", "engineer", "scientist", "analyst"],
        test_suite="full_benchmark"
    )
    
    # If scores beat kings, trigger throne swap
    if tournament.check_throne_eligibility(model_name):
        tournament.swap_throne(model_name)
        log_king_change(model_name)
```

---

## Integration with Council

```python
from council import CouncilSession
from kofh import TournamentSystem

tournament = TournamentSystem()
council = CouncilSession()

# Get current kings for council seats
planner_king = tournament.get_throne_holder("planner")
engineer_king = tournament.get_throne_holder("engineer")

# Assign to council
council.session.planner = Planner(model=planner_king)
council.session.engineer = Engineer(model=engineer_king)
```

---

## Files

- `kofh/__init__.py` - Package exports
- `kofh/tournament.py` - Main tournament system
- `kofh/throne.py` - Throne management
- `kofh/scoring.py` - Score calculation
- `kofh/tests/` - Role-specific test suites
  - `planner_tests.py`
  - `engineer_tests.py`
  - `scientist_tests.py`
  - `analyst_tests.py`
- `kofh/leaderboard.py` - Leaderboard display

---

## Usage

```python
from kofh import TournamentSystem

tournament = TournamentSystem()

# Run evaluation for a model
results = tournament.evaluate_model(
    model="qwen-coder",
    role="engineer",
    test_suite="full_benchmark"
)

# Get current king
king = tournament.get_throne_holder("engineer")
print(f"Engineer King: {king}")

# Get leaderboard
leaderboard = tournament.get_leaderboard("engineer")
print(leaderboard)

# Challenge throne
challenger_result = tournament.challenge_throne(
    model="codex",
    role="engineer"
)

if challenger_result.success:
    print(f"New Engineer King: {challenger_result.model}")
```

---

## Dashboard Integration

The tournament feeds into your existing benchmark dashboard:

```python
# Dashboard shows:
- Current kings (4 thrones)
- Challenger rankings
- Recent throne swaps
- Score trends over time
- Model performance by role
```

---

## Status

**Infrastructure:** 70-80% exists in current benchmark system  
**Missing Pieces:**
- [ ] Role-specific test suites
- [ ] Throne swap logic
- [ ] Automatic challenge scheduling
- [ ] King/Challenger pool separation
- [ ] 3% stability buffer

---

**The Tournament Begins When You're Ready.** 👑⚔️
