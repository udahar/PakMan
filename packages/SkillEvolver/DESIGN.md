# Skill Evolver - Auto-Improve Skills

**Status:** 📋 Concept - Medium Priority

---

## The Problem

Your **26 skills are static**:
- Same prompts every time
- Never improve from usage
- No learning from success/failure
- Manual updates required

**Result:**
- Skills don't get better over time
- You repeat same mistakes
- No data on what works
- Manual tuning required

---

## The Solution

A **skill evolution system** that:
1. **Tracks usage** - Record every skill use
2. **Measures success** - Did it work?
3. **Auto-tunes prompts** - Improve based on data
4. **Generates versions** - V1 → V2 → V3
5. **Selects best** - Keep what works

---

## Architecture

```
skill_evolver/
├── evolver.py           # Core evolution engine
├── mutations.py         # Prompt mutation strategies
├── selection.py         # Select best versions
├── tracker.py           # Usage tracking
├── metrics.py           # Success metrics
└── cli.py               # Command-line interface
```

---

## Features

### 1. Usage Tracking

**Record every skill use:**

```python
from skill_evolver import SkillTracker

tracker = SkillTracker()

# Track skill usage
tracker.record_usage(
    skill="humble_inquiry",
    prompt_used="Ask clarifying questions...",
    context="User researching unknown topic",
    success=True,  # Did it work?
    user_feedback=0.9,  # User rating 0-1
    outcome="User got clear answer",
)

# Track over time
stats = tracker.get_stats("humble_inquiry")
print(f"Used: {stats.usage_count} times")
print(f"Success rate: {stats.success_rate:.1%}")
print(f"Avg feedback: {stats.avg_feedback:.1f}")
```

**Tracked data:**
- When used
- Prompt version
- Context
- Success/failure
- User feedback
- Outcome quality

---

### 2. Success Metrics

**Measure what works:**

```python
from skill_evolver import SkillMetrics

metrics = SkillMetrics()

# Calculate metrics for skill
skill_metrics = metrics.calculate("humble_inquiry")

print(f"Success rate: {skill_metrics.success_rate:.1%}")
print(f"Avg feedback: {skill_metrics.avg_feedback:.1f}")
print(f"Improvement trend: {skill_metrics.trend}")
```

**Metrics:**
- **Success rate** - % of successful uses
- **Avg feedback** - User rating average
- **Trend** - Getting better or worse?
- **Consistency** - How reliable?
- **Efficiency** - Token usage vs outcome

---

### 3. Prompt Mutations

**Generate improved versions:**

```python
from skill_evolver import PromptMutator

mutator = PromptMutator()

# Mutate existing prompt
original = "Ask clarifying questions to understand the user's need"

mutations = mutator.mutate(original, strategies=[
    "add_examples",      # Add example questions
    "increase_specificity",  # Be more specific
    "add_constraints",   # Add constraints
    "improve_clarity",   # Clearer language
])

# Results:
# V2: "Ask 2-3 clarifying questions like: 'What specifically...?'"
# V3: "Ask targeted questions to clarify scope, constraints, and goals"
# V4: "Before answering, ask: 'What's your specific use case?'"
```

**Mutation strategies:**
- **Add examples** - Include usage examples
- **Increase specificity** - More detailed instructions
- **Add constraints** - Limit scope
- **Improve clarity** - Clearer language
- **Add structure** - Numbered steps
- **Change tone** - More/less formal
- **Optimize length** - Shorter/longer

---

### 4. A/B Testing

**Test which version works better:**

```python
from skill_evolver import ABTester

tester = ABTester()

# Test two versions
test = tester.create_test(
    skill="humble_inquiry",
    version_a="original",
    version_b="mutated_v2",
    sample_size=50,  # Test with 50 uses
)

# Run test (automatic)
results = tester.run_test(test)

# Results
print(f"Version A success: {results.a_success_rate:.1%}")
print(f"Version B success: {results.b_success_rate:.1%}")
print(f"Winner: Version {'B' if results.b_success_rate > results.a_success_rate else 'A'}")
```

**Test types:**
- **A/B** - Two versions
- **Multi-armed** - Multiple versions
- **Sequential** - One after another
- **Context-specific** - Different contexts

---

### 5. Version Selection

**Automatically select best version:**

```python
from skill_evolver import SkillEvolver

evolver = SkillEvolver()

# Get best version for task
best = evolver.get_best_version(
    skill="humble_inquiry",
    task_type="research",
    context="unknown topic"
)

print(f"Using version: {best.version}")
print(f"Success rate: {best.success_rate:.1%}")
```

**Selection criteria:**
- Overall success rate
- Recent performance
- Context match
- User feedback
- Trend (improving?)

---

### 6. Auto-Evolution

**Continuous improvement loop:**

```python
from skill_evolver import SkillEvolver

evolver = SkillEvolver()

# Evolve skill automatically
evolver.evolve(
    skill="humble_inquiry",
    generations=3,  # Create 3 new versions
    test_with=50,   # Test each with 50 uses
    keep_best=True  # Keep best version
)

# Result: Skill improved from V1 → V4
# V4 has 15% higher success rate
```

**Evolution process:**
1. **Measure** current performance
2. **Mutate** to create new versions
3. **Test** new versions
4. **Select** best performer
5. **Deploy** winner
6. **Repeat**

---

## Usage

### Basic

```python
from skill_evolver import SkillEvolver

evolver = SkillEvolver()

# Track usage
evolver.track(
    skill="humble_inquiry",
    success=True,
    feedback=0.9
)

# Get current best version
best = evolver.get_best("humble_inquiry")

# Use in prompt
prompt = best.prompt
```

### Advanced

```python
from skill_evolver import SkillEvolver, ABTester

evolver = SkillEvolver()
tester = ABTester()

# Create new version
original = evolver.get_version("humble_inquiry", "v1")
mutated = evolver.mutate(original, strategy="add_examples")

# A/B test
test = tester.create_test(
    skill="humble_inquiry",
    version_a="v1",
    version_b="v2_mutated",
    sample_size=100
)

# Run test
results = tester.run_test(test)

# Deploy winner
if results.b_success_rate > results.a_success_rate:
    evolver.deploy("humble_inquiry", "v2_mutated")
    print("Deployed v2 - 12% improvement!")
```

---

## Integration Points

### With PromptSKLib

```python
# Auto-evolve skills in PromptSKLib
from skill_evolver import SkillEvolver
from PromptRD.PromptSKLib import load_skill

evolver = SkillEvolver()

# Load skill
skill = load_skill("humble_inquiry")

# Get evolved version
evolved = evolver.get_best("humble_inquiry")

# Use evolved version
prompt = evolved.prompt
```

### With Blueprints

```python
# Evolve blueprints too
from skill_evolver import SkillEvolver
from blueprints import BlueprintLibrary

evolver = SkillEvolver()
lib = BlueprintLibrary()

# Track blueprint usage
lib.add_usage_tracker(evolver)

# Evolve popular blueprints
evolver.evolve_skill("blueprint_streetpunk", generations=2)
```

### With Analytics

```python
# Feed analytics data to evolver
from skill_evolver import SkillEvolver
from prompt_analytics import Analytics

evolver = SkillEvolver()
analytics = Analytics()

# Get usage data
usage_data = analytics.get_usage("humble_inquiry")

# Feed to evolver
evolver.bulk_record(usage_data)

# Evolve based on data
evolver.evolve("humble_inquiry")
```

---

## Benefits

**Before:**
- Static skills
- No learning
- Manual updates
- Same mistakes repeated

**After:**
- Evolving skills
- Data-driven improvements
- Auto-tuning
- Continuous improvement

---

## Implementation Plan

### Phase 1: Tracker (2 hours)
- [ ] Create `tracker.py`
- [ ] Usage recording
- [ ] Basic stats
- [ ] Storage (SQLite/JSON)

### Phase 2: Metrics (2 hours)
- [ ] Create `metrics.py`
- [ ] Success rate calculation
- [ ] Trend analysis
- [ ] Dashboard data

### Phase 3: Mutations (3 hours)
- [ ] Create `mutations.py`
- [ ] Mutation strategies
- [ ] LLM-based mutations
- [ ] Version management

### Phase 4: Evolution (3 hours)
- [ ] Create `evolver.py`
- [ ] A/B testing
- [ ] Auto-selection
- [ ] Deployment

---

## Files to Create

```
skill_evolver/
├── __init__.py
├── evolver.py           # Core evolution engine
├── mutations.py         # Mutation strategies
├── selection.py         # Version selection
├── tracker.py           # Usage tracking
├── metrics.py           # Success metrics
├── ab_testing.py        # A/B testing
├── cli.py               # CLI
└── README.md
```

---

**This turns your 26 static skills into a self-improving system.** 🧬

The more you use it, the smarter it gets.
