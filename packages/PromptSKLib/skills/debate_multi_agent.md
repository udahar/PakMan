# Skill: Debate / Multi-Agent Reasoning

**skill_id:** `debate_multi_agent_001`  
**name:** debate_multi_agent  
**category:** prompt_strategy  
**version:** 1.0  

## Description

Simulates multiple agents with different perspectives debating a problem, leading to more robust conclusions.

## Primitive Tags

- multi_agent
- adversarial_reasoning
- perspective_taking
- critique_and_defend
- consensus_building
- dialectical_reasoning

## Prompt Strategy

```
For Multi-Agent Debate:

1. DEFINE AGENTS
   - Agent A: Proponent (proposes solution)
   - Agent B: Critic (finds flaws)
   - Optional Agent C: Moderator (synthesizes)

2. ROUND 1: INITIAL POSITIONS
   - Agent A proposes solution
   - Agent B critiques

3. ROUND 2: RESPONSE
   - Agent A defends/revises
   - Agent B responds

4. SYNTHESIS
   - Identify points of agreement
   - Note remaining disagreements
   - Produce final recommendation
```

## Solution Summary

### Prompt Templates

**Agent A (Proponent)**
```
You are Agent A, proposing a solution to: {problem}

Present your best solution with clear reasoning.
Be prepared to defend it against criticism.
```

**Agent B (Critic)**
```
You are Agent B, the critic.

Review Agent A's proposal:
{proposal}

Identify:
1. Logical flaws
2. Missing considerations
3. Better alternatives
4. Potential failure modes

Be constructive but rigorous.
```

**Agent A (Response)**
```
Agent A, respond to the criticism:

{criticism}

Address each valid point. Revise your proposal if needed.
Defend aspects you believe are correct.
```

**Moderator (Synthesis)**
```
You are the moderator.

Review the debate:
- Proposal: {proposal}
- Criticism: {criticism}
- Response: {response}

Synthesize:
1. Points of agreement
2. Remaining disagreements
3. Best path forward
4. Final recommendation
```

### Python Implementation

```python
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum


class AgentRole(Enum):
    PROPONENT = "proponent"
    CRITIC = "critic"
    MODERATOR = "moderator"


@dataclass
class AgentMessage:
    role: AgentRole
    content: str
    round: int


@dataclass
class DebateResult:
    problem: str
    messages: List[AgentMessage]
    synthesis: str
    consensus_points: List[str]
    remaining_disagreements: List[str]
    final_recommendation: str


async def debate_multi_agent(
    problem: str,
    model_fn,
    num_rounds: int = 2
) -> DebateResult:
    """
    Simulate multi-agent debate.
    
    Args:
        problem: The problem to debate
        model_fn: Async function to call LLM
        num_rounds: Number of debate rounds
    
    Returns:
        DebateResult with synthesis
    """
    messages = []
    
    # Round 1: Initial proposal
    proposal = await agent_proponent(problem, model_fn)
    messages.append(AgentMessage(AgentRole.PROPONENT, proposal, 1))
    
    # Round 1: Criticism
    criticism = await agent_critic(proposal, problem, model_fn)
    messages.append(AgentMessage(AgentRole.CRITIC, criticism, 1))
    
    # Additional rounds
    current_proposal = proposal
    for round_num in range(2, num_rounds + 1):
        # Proponent responds
        response = await agent_proponent_respond(
            current_proposal, criticism, model_fn
        )
        messages.append(AgentMessage(AgentRole.PROPONENT, response, round_num))
        current_proposal = response
        
        # Critic responds
        criticism = await agent_critic(response, problem, model_fn)
        messages.append(AgentMessage(AgentRole.CRITIC, criticism, round_num))
    
    # Synthesis
    synthesis = await moderator_synthesize(messages, model_fn)
    
    return parse_debate_result(synthesis, messages)


async def agent_proponent(problem: str, model_fn) -> str:
    """Generate initial proposal."""
    prompt = f"""You are Agent A (Proponent).

Problem: {problem}

Propose a well-reasoned solution. Include:
1. Your recommended approach
2. Key reasoning
3. Expected benefits
4. Potential concerns you anticipate

Be clear and specific."""
    
    return await model_fn(prompt)


async def agent_critic(proposal: str, problem: str, model_fn) -> str:
    """Generate criticism."""
    prompt = f"""You are Agent B (Critic).

Problem: {problem}

Proposal to critique:
{proposal}

Identify:
1. Logical flaws or gaps
2. Missing considerations
3. Better alternatives
4. Potential failure modes

Be constructive but rigorous. Focus on substance."""
    
    return await model_fn(prompt)


async def agent_proponent_respond(
    proposal: str,
    criticism: str,
    model_fn
) -> str:
    """Proponent responds to criticism."""
    prompt = f"""You are Agent A (Proponent).

Your original proposal:
{proposal}

Criticism received:
{criticism}

Respond to the criticism:
1. Address each valid concern
2. Revise your proposal where appropriate
3. Defend aspects you believe are correct
4. Explain your reasoning

Be intellectually honest."""
    
    return await model_fn(prompt)


async def moderator_synthesize(messages: List[AgentMessage], model_fn) -> str:
    """Synthesize debate results."""
    debate_summary = "\n\n".join(
        f"{m.role.value.upper()} (Round {m.round}):\n{m.content}"
        for m in messages
    )
    
    prompt = f"""You are the Moderator.

Debate transcript:
{debate_summary}

Synthesize the debate:

POINTS OF AGREEMENT:
[List points both agents agree on]

REMAINING DISAGREEMENTS:
[List unresolved disagreements]

BEST PATH FORWARD:
[Recommend the best approach]

FINAL RECOMMENDATION:
[Clear, actionable recommendation]"""
    
    return await model_fn(prompt)


def parse_debate_result(synthesis: str, messages: List[AgentMessage]) -> DebateResult:
    """Parse synthesis into structured result."""
    import re
    
    consensus = extract_section(synthesis, "POINTS OF AGREEMENT")
    disagreements = extract_section(synthesis, "REMAINING DISAGREEMENTS")
    recommendation = extract_section(synthesis, "FINAL RECOMMENDATION")
    
    return DebateResult(
        problem=messages[0].content[:100] + "...",
        messages=messages,
        synthesis=synthesis,
        consensus_points=consensus.split('\n') if consensus else [],
        remaining_disagreements=disagreements.split('\n') if disagreements else [],
        final_recommendation=recommendation or synthesis
    )


def extract_section(text: str, header: str) -> str:
    """Extract section from text."""
    import re
    
    pattern = rf'{header}:\s*\n(.*?)(?=\n\n[A-Z]|\Z)'
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else ""
```

## Tests Passed

- [x] Generates distinct agent perspectives
- [x] Criticism identifies real issues
- [x] Proponent responds constructively
- [x] Synthesis finds common ground
- [x] Produces actionable recommendation
- [x] Works for technical debates
- [x] Works for policy decisions

## Failure Modes

- **Agreement too fast**: Superficial consensus
  - Mitigation: Encourage deeper critique
- **Endless disagreement**: No synthesis possible
  - Mitigation: Moderator identifies compromise
- **Same voice**: Agents sound identical
  - Mitigation: Give agents distinct personas

## Best For

- Architecture decisions
- Policy discussions
- Trade-off analysis
- Complex technical choices
- Ethical reasoning
- Strategic planning

## Performance

- **Quality**: Often finds issues single reasoning misses
- **Cost**: 4-6x single generation (2+ rounds)
- **Latency**: Sequential rounds

## Related Skills

- `role_persona_001` - Give agents distinct personas
- `reflexion_001` - Self-critique variant
- `contrastive_prompting_001` - Compare alternatives

## Timestamp

2026-03-08
