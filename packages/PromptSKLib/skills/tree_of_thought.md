# Skill: Tree of Thought Reasoning

**skill_id:** `tree_of_thought_001`  
**name:** tree_of_thought  
**category:** prompt_strategy  
**version:** 1.0  

## Description

Enables systematic exploration of multiple reasoning paths by branching thoughts, evaluating each branch, and backtracking when needed.

## Primitive Tags

- branching_reasoning
- explore_alternatives
- evaluate_paths
- backtrack
- systematic_exploration
- decision_tree

## Prompt Strategy

```
For Tree of Thought reasoning:

1. DECOMPOSE PROBLEM
   - Identify the main question/goal
   - Break into sub-decisions

2. GENERATE BRANCHES
   - For each decision point, generate 2-4 options
   - Each branch represents a different approach

3. EVALUATE BRANCHES
   - Assess each branch for:
     - Feasibility
     - Correctness indicators
     - Potential issues
   - Score or rank branches

4. EXPLORE PROMISING PATHS
   - Continue down highest-scoring branches
   - Backtrack if path fails
   - Prune obviously wrong branches

5. SYNTHESIZE CONCLUSION
   - Compare final outcomes from different paths
   - Select best solution
   - Explain reasoning
```

## Solution Summary

```
Problem: {problem_statement}

## Step 1: Identify Decision Points
- Decision 1: {first_choice}
- Decision 2: {second_choice}

## Step 2: Generate Branches

### Branch A: {approach_a}
Reasoning: {why_consider_this}

### Branch B: {approach_b}
Reasoning: {why_consider_this}

### Branch C: {approach_c}
Reasoning: {why_consider_this}

## Step 3: Evaluate Branches

| Branch | Feasibility | Risks | Score |
|--------|-------------|-------|-------|
| A      | High/Med/Low | ...   | 1-10  |
| B      | High/Med/Low | ...   | 1-10  |
| C      | High/Med/Low | ...   | 1-10  |

## Step 4: Explore Top Branch

Following Branch {X} because {reason}:

Sub-decision 1: ...
  → Option 1a: ...
  → Option 1b: ...

Sub-decision 2: ...
  → Option 2a: ...
  → Option 2b: ...

## Step 5: Conclusion

Best solution: {selected_approach}

Confidence: {level}

Why this over alternatives: {comparison}
```

## Tests Passed

- [x] Generates multiple distinct approaches
- [x] Evaluates branches systematically
- [x] Backtracks when path fails
- [x] Compares final outcomes
- [x] Explains selection reasoning

## Failure Modes

- **Analysis paralysis**: Too many branches
  - Mitigation: Limit to 3-4 branches per decision
- **Shallow exploration**: Too many levels deep
  - Mitigation: Limit depth to 3-4 levels
- **Biased evaluation**: Favoring initial intuition
  - Mitigation: Explicitly score each branch

## Related Skills

- `react_reasoning_001` - ReAct reasoning pattern
- `chain_of_thought_001` - Sequential reasoning
- `self_reflection_001` - Critique and improve

## Timestamp

2026-03-08
