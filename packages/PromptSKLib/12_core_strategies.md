# 12 Core Prompt Strategies - Quick Reference

These are the fundamental "thinking modes" for AI reasoning. Each can be used as:
1. **Prompt template** - Inject into system prompt
2. **Executable skill** - Call Python implementation for structured execution

---

## The Strategies

### 1. Chain of Thought (CoT)
**Purpose:** Force step-by-step reasoning before answering

**When to use:** Math, logic, debugging, multi-step calculations

**Structure:**
```
Question → Reason step-by-step → Final answer
```

**Prompt skeleton:**
```
Solve this step-by-step before giving the answer.
Show each step clearly.
```

---

### 2. Self-Consistent Chain of Thought (SCoT)
**Purpose:** Run CoT multiple times, vote on most consistent answer

**When to use:** High-stakes decisions, complex problems, when reliability > speed

**Structure:**
```
Prompt → 5 reasoning attempts → Majority vote → Answer
```

**Performance:** +5-15% accuracy over single CoT, 5x cost

---

### 3. ReAct (Reason + Act)
**Purpose:** Alternate reasoning with tool use

**When to use:** Tool-based systems, research tasks, data gathering

**Structure:**
```
Thought → Action → Observation → Thought → Action → ...
```

**Example:**
```
Thought: Need data about X
Action: search_web("X")
Observation: Found 5 results
Thought: Analyze results...
```

---

### 4. Tree of Thoughts (ToT)
**Purpose:** Explore multiple reasoning paths, pick best branch

**When to use:** Planning, architecture design, puzzles, decisions with trade-offs

**Structure:**
```
Generate branches (A, B, C) → Evaluate → Expand best → Continue
```

**Best for:** Problems with multiple valid approaches

---

### 5. Reflexion
**Purpose:** Self-critique and iteratively improve

**When to use:** Code generation, writing, complex reasoning, learning from mistakes

**Structure:**
```
Attempt solution → Reflect on errors → Revise → (Repeat)
```

**Performance:** +10-20% quality over single attempt, 2-3x cost

---

### 6. Meta-Prompting
**Purpose:** Design the optimal prompt, then execute it

**When to use:** Novel problems, PromptForge experiments, optimization tasks

**Structure:**
```
Analyze task → Design best prompt → Execute designed prompt → Answer
```

**Key insight:** Let the model design its own instructions

---

### 7. Role / Persona Prompting
**Purpose:** Assign expert identity for domain-specific reasoning

**When to use:** Domain tasks, code review, technical writing, security analysis

**Structure:**
```
You are {expert persona} with {background}.
Approach problems by {method}.
Communicate in {style}.

Task: {task}
```

**Personas:** Senior DevOps, Data Scientist, Security Researcher, UX Designer, etc.

---

### 8. Debate / Multi-Agent Reasoning
**Purpose:** Simulate multiple perspectives debating

**When to use:** Architecture decisions, policy discussions, trade-off analysis

**Structure:**
```
Agent A proposes → Agent B critiques → A responds → Moderator synthesizes
```

**Best for:** Finding hidden issues, exploring trade-offs

---

### 9. Contrastive Prompting
**Purpose:** Generate multiple answers, compare, select best

**When to use:** Creative tasks, design choices, optimization problems

**Structure:**
```
Generate 3 solutions → Evaluate each → Compare → Select/synthesize winner
```

**Advantage:** Explores solution space before committing

---

### 10. Retrieval-Augmented Generation (RAG)
**Purpose:** Inject external knowledge for grounded answers

**When to use:** Questions about docs, company knowledge, technical support

**Structure:**
```
Query → Retrieve context → Inject into prompt → Generate with citations
```

**Sources:** Qdrant (vector), Postgres (structured), files, web

---

### 11. Program of Thought (PoT)
**Purpose:** Write and execute code for accurate computation

**When to use:** Math calculations, data analysis, algorithmic problems

**Structure:**
```
Problem → Write code → Execute → Interpret results → Answer
```

**Accuracy:** Near-perfect for computational problems

---

### 12. Decomposition / Task Chunking
**Purpose:** Break complex tasks into solvable subtasks

**When to use:** Multi-step projects, overwhelming tasks, workflow automation

**Structure:**
```
Task → Break into subtasks → Solve each → Combine results
```

**Best for:** Tasks that feel too complex for single-shot

---

## Strategy Selection Guide

| Task Type | Best Strategies |
|-----------|-----------------|
| Math/Calculation | CoT, PoT, SCoT |
| Logic Puzzles | CoT, ToT, SCoT |
| Code Generation | Reflexion, PoT, Role |
| Debugging | CoT, Reflexion, Role |
| Research | ReAct, RAG, Decomposition |
| Architecture Design | ToT, Debate, Role |
| Creative Writing | Contrastive, Role, ToT |
| Analysis | Decomposition, RAG, CoT |
| Decision Making | ToT, Debate, Contrastive |
| Technical Writing | Role, Decomposition |
| Security Analysis | Role, Debate, Reflexion |
| Data Analysis | PoT, RAG, Decomposition |

---

## Cost vs. Quality Trade-offs

| Strategy | Relative Cost | Quality Boost | Best Use |
|----------|--------------|---------------|----------|
| CoT | 1x | +10-20% | Default for reasoning |
| SCoT | 5x | +5-15% | High-stakes |
| ReAct | 2-4x | +20-30% | Tool tasks |
| ToT | 3-5x | +15-25% | Complex decisions |
| Reflexion | 2-3x | +10-20% | Code/writing |
| Meta-Prompting | 2x | Variable | Novel problems |
| Role | 1x | +10-15% | Domain tasks |
| Debate | 4-6x | +20-30% | Important decisions |
| Contrastive | 3-5x | +10-20% | Creative/optimize |
| RAG | 1x + retrieval | +30-50% | Knowledge tasks |
| PoT | 2x | +40-50% | Computation |
| Decomposition | N+2x | +20-40% | Complex workflows |

---

## Combining Strategies

Strategies can be composed:

```
RAG + CoT = Retrieve context, then reason step-by-step about it
Role + Debate = Expert personas debate (DevOps vs Security)
Decomposition + PoT = Break task down, solve subtasks with code
ToT + Reflexion = Explore branches, critique each one
```

---

## Implementation Notes

### As Prompt Templates
Inject into system prompt:
```python
system_prompt = f"""{strategy_template}

Task: {user_task}
"""
```

### As Executable Skills
Call Python implementation:
```python
from skills.chain_of_thought import chain_of_thought

result = await chain_of_thought(
    question="Your question",
    model_fn=model_call
)
```

---

## Benchmarking with FieldBench

Track which strategies work best for which tasks:

```python
# Example experiment
for strategy in strategies:
    for task in benchmark_tasks:
        result = await execute_strategy(strategy, task)
        record_benchmark(strategy, task, result.score)

# Analysis: "regex tasks → CoT best, API tasks → ReAct best"
```

---

## The Big Picture

These 12 strategies form a **reasoning toolkit**:

```
Model (reasoning engine)
+
Prompt Strategy (thinking mode)
+
Skill Library (learned patterns)
=
Intelligent System
```

Most AI systems use only the model layer. By adding **strategy selection** and **skill retrieval**, you get:

- Better accuracy on complex tasks
- More reliable outputs
- Ability to tackle novel problems
- Measurable improvement via benchmarking

This is the foundation for **PromptForge** and **Alfred's reasoning system**.

---

**Timestamp:** 2026-03-08
**Version:** 1.0
