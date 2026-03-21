# Skill: ReAct Reasoning (Reason + Act)

**skill_id:** `react_reasoning_001`  
**name:** react_reasoning  
**category:** prompt_strategy  
**version:** 1.0  

## Description

Combines reasoning with action by alternating between thinking steps and tool usage, enabling systematic problem-solving with external resources.

## Primitive Tags

- reasoning
- tool_use
- alternating_steps
- observation
- plan_execution
- iterative_problem_solving

## Prompt Strategy

```
For ReAct reasoning:

1. THOUGHT: Reason about current state
   - What do I know?
   - What do I need to find out?
   - What action should I take?

2. ACTION: Execute a tool
   - Search, calculate, fetch, etc.
   - Be specific about parameters

3. OBSERVATION: Record result
   - What did the action return?
   - What new information do I have?

4. REPEAT
   - Loop through Thought → Action → Observation
   - Until problem is solved

5. FINAL ANSWER
   - Synthesize all observations
   - Provide complete answer
```

## Solution Summary

```
Question: {user_question}

Thought 1: I need to find out {X}. I should use {tool} to search for this.
Action 1: {tool_name}({parameters})
Observation 1: {result_from_tool}

Thought 2: Now I know {X}. I also need to find {Y}. Let me {action}.
Action 2: {tool_name}({parameters})
Observation 2: {result_from_tool}

Thought 3: I have enough information to answer. Let me synthesize.

Final Answer: {complete_answer}

Sources:
- {source_1}
- {source_2}
```

## Example Usage

```
Question: What is the population of the city where Tesla's headquarters is located?

Thought 1: I need to find where Tesla's headquarters is located first.
Action 1: web_search("Tesla headquarters location")
Observation 1: Tesla's headquarters is in Austin, Texas.

Thought 2: Now I need to find the population of Austin, Texas.
Action 2: web_search("Austin Texas population 2025")
Observation 2: Austin's population is approximately 1.03 million (2025 estimate).

Thought 3: I have the answer. Let me provide it.

Final Answer: The population of Austin, Texas (where Tesla's headquarters is located) is approximately 1.03 million people as of 2025.
```

## Tests Passed

- [x] Alternates thought and action correctly
- [x] Uses observations to inform next steps
- [x] Knows when to stop and answer
- [x] Cites sources from tool results
- [x] Handles multi-step problems

## Failure Modes

- **Infinite loops**: Keeps searching without answering
  - Mitigation: Set max iteration limit (5-10)
- **Premature conclusion**: Answers before enough research
  - Mitigation: Require minimum 2 observations
- **Tool misuse**: Wrong tool for the task
  - Mitigation: Clear tool descriptions

## Related Skills

- `tree_of_thought_001` - Branching reasoning
- `web_research_001` - Web investigation
- `tool_orchestrator_001` - Tool coordination

## Timestamp

2026-03-08
