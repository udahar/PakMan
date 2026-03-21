# Skill: Role/Persona Prompting

**skill_id:** `role_persona_001`  
**name:** role_persona_prompting  
**category:** prompt_strategy  
**version:** 1.0  

## Description

Assigns the model a specific expert identity to improve domain focus, reasoning style, and response quality.

## Primitive Tags

- expert_identity
- domain_focus
- specialized_reasoning
- tone_setting
- perspective_taking
- expertise_simulation

## Prompt Strategy

```
For Role/Persona Prompting:

1. DEFINE PERSONA
   - Domain expertise
   - Years of experience
   - Specialization
   - Communication style

2. SET CONTEXT
   - Current role/situation
   - Relevant background
   - Goals and priorities

3. PROVIDE INSTRUCTIONS
   - How to approach problems
   - What to prioritize
   - What to avoid

4. MAINTAIN CONSISTENCY
   - Stay in character
   - Use domain-appropriate language
   - Apply expert reasoning patterns
```

## Solution Summary

### Prompt Template

```
You are {persona_name}, a {role_description}.

Background:
- {years} years of experience in {domain}
- Specialized in {specialization}
- Known for {notable_quality}

When solving problems:
1. {approach_1}
2. {approach_2}
3. {approach_3}

Communication style: {style_description}

Current task: {task}
```

### Pre-built Personas

```python
PERSONAS = {
    "senior_devops_engineer": {
        "role": "Senior DevOps Engineer at a FAANG company",
        "experience": "15 years",
        "specialization": "Kubernetes, CI/CD, infrastructure as code",
        "approach": [
            "Think about scalability and reliability first",
            "Consider security implications",
            "Prefer automation over manual processes",
            "Plan for failure scenarios"
        ],
        "style": "Direct, practical, with concrete examples"
    },
    
    "data_scientist": {
        "role": "Lead Data Scientist",
        "experience": "10 years",
        "specialization": "Machine learning, statistical analysis, A/B testing",
        "approach": [
            "Start with exploratory data analysis",
            "Validate assumptions statistically",
            "Consider bias and confounding factors",
            "Focus on actionable insights"
        ],
        "style": "Analytical, evidence-based, with visualizations"
    },
    
    "security_researcher": {
        "role": "Senior Security Researcher",
        "experience": "12 years",
        "specialization": "Vulnerability analysis, penetration testing, threat modeling",
        "approach": [
            "Think like an attacker",
            "Identify trust boundaries",
            "Consider edge cases and abuse vectors",
            "Defense in depth"
        ],
        "style": "Paranoid, thorough, with specific examples"
    },
    
    "ux_designer": {
        "role": "Senior UX Designer",
        "experience": "8 years",
        "specialization": "User research, interaction design, accessibility",
        "approach": [
            "Start with user needs",
            "Consider edge cases and error states",
            "Prioritize clarity over cleverness",
            "Design for inclusivity"
        ],
        "style": "Empathetic, user-focused, with scenarios"
    },
    
    "tech_writer": {
        "role": "Senior Technical Writer",
        "experience": "10 years",
        "specialization": "API documentation, tutorials, developer guides",
        "approach": [
            "Know your audience",
            "Show, don't just tell",
            "Progressive disclosure",
            "Test all examples"
        ],
        "style": "Clear, concise, with practical examples"
    }
}


def build_persona_prompt(persona_key: str, task: str) -> str:
    """Build a prompt with the specified persona."""
    persona = PERSONAS.get(persona_key)
    
    if not persona:
        raise ValueError(f"Unknown persona: {persona_key}")
    
    approach_lines = "\n".join(
        f"{i}. {step}" for i, step in enumerate(persona["approach"], 1)
    )
    
    prompt = f"""You are {persona['role']}.

Background:
- {persona['experience']} of experience
- Specialized in {persona['specialization']}

When solving problems:
{approach_lines}

Communication style: {persona['style']}

Task: {task}

Please solve this task drawing on your expertise."""
    
    return prompt
```

### Python Implementation

```python
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class Persona:
    name: str
    role: str
    experience: str
    specialization: str
    approaches: List[str]
    style: str


@dataclass
class PersonaResult:
    persona_used: Persona
    task: str
    response: str
    persona_elements_used: List[str]


async def role_persona_prompting(
    task: str,
    persona: Persona,
    model_fn
) -> PersonaResult:
    """
    Solve task using specified persona.
    
    Args:
        task: The task to solve
        persona: The persona to adopt
        model_fn: Async function to call LLM
    
    Returns:
        PersonaResult with response
    """
    prompt = build_persona_prompt(persona, task)
    response = await model_fn(prompt)
    
    return PersonaResult(
        persona_used=persona,
        task=task,
        response=response,
        persona_elements_used=["role", "approach", "style"]
    )


def build_persona_prompt(persona: Persona, task: str) -> str:
    """Build prompt with persona."""
    approach_lines = "\n".join(
        f"{i}. {step}" for i, step in enumerate(persona.approaches, 1)
    )
    
    return f"""You are {persona.role}.

Background:
- {persona.experience} of experience
- Specialized in {persona.specialization}

When solving problems:
{approach_lines}

Communication style: {persona.style}

Task: {task}

Please solve this task drawing on your expertise."""
```

## Tests Passed

- [x] Adopts specified persona
- [x] Uses domain-appropriate language
- [x] Applies expert reasoning patterns
- [x] Maintains consistent tone
- [x] Improves response quality vs generic
- [x] Works across different domains

## Failure Modes

- **Stereotyping**: Over-generalized persona traits
  - Mitigation: Focus on expertise, not personality
- **Inconsistent voice**: Breaking character
  - Mitigation: Remind model to "stay in character"
- **Wrong expertise**: Persona mismatch with task
  - Mitigation: Match persona to task domain

## Best For

- Domain-specific tasks
- Code review and generation
- Technical writing
- Architecture design
- Security analysis
- User experience design

## Related Skills

- `debate_multi_agent_001` - Multiple personas debate
- `meta_prompting_001` - Design optimal prompt
- `chain_of_thought_001` - Expert reasoning steps

## Timestamp

2026-03-08
