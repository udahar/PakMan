# PromptForge - Benchmarking Framework

**Purpose:** Test which prompts/strategies work best

---

## Concept

A/B test your prompts and strategies. Track success rates. Know what actually works.

---

## Features

- **A/B Testing** - Compare two prompts side-by-side
- **Success Tracking** - Measure which prompts win
- **Benchmark Suites** - Pre-built test sets
- **Analytics Dashboard** - See trends over time

---

## Usage

```python
from promptforge import benchmark

# Compare two strategies
results = benchmark.run(
    strategy_a="chain_of_thought",
    strategy_b="tree_of_thought",
    tasks=benchmark_suite["math"]
)

print(f"Chain of Thought: {results['a_win_rate']:.1%}")
print(f"Tree of Thought: {results['b_win_rate']:.1%}")
```

---

## Files

- `benchmark.py` - Core benchmarking engine
- `suites/` - Pre-built test suites
- `analytics.py` - Results analysis
- `dashboard.py` - Visual dashboard (future)

---

**Status:** 📋 Concept - Ready to build
