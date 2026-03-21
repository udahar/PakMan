# Skills Library - Complete Index

**Total: 26 skills** across 5 categories  
**Last updated:** 2026-03-08

---

## Quick Reference Table

| Skill ID | Name | Category | Semantic Description |
|----------|------|----------|---------------------|
| `humble_inquiry_001` | humble_inquiry | inquiry | Admits uncertainty explicitly, searches internal knowledge bases first, then falls back to web search with citations |
| `web_research_001` | web_research | inquiry | Conducts thorough web investigations using search and fetch tools, returning structured findings with source attribution |
| `source_verification_001` | source_verification | inquiry | Cross-references information across multiple sources to verify accuracy and identify potential misinformation or contradictions |
| `knowledge_gap_analysis_001` | knowledge_gap_analysis | inquiry | Identifies specific gaps in knowledge about a topic, enabling targeted research rather than vague uncertainty |
| `chain_of_thought_001` | chain_of_thought | prompt_strategy | Forces step-by-step reasoning before answering, improving accuracy on math, logic, and debugging tasks significantly |
| `self_consistent_cot_001` | self_consistent_cot | prompt_strategy | Runs chain-of-thought multiple times with varied paths, uses majority voting to select most reliable answer |
| `react_reasoning_001` | react_reasoning | prompt_strategy | Alternates between reasoning steps and tool usage, enabling systematic problem-solving with external resources |
| `tree_of_thought_001` | tree_of_thought | prompt_strategy | Explores multiple reasoning branches simultaneously, evaluates each path, and selects the best solution |
| `reflexion_001` | reflexion | prompt_strategy | Critiques its own output, identifies mistakes and gaps, then iteratively improves the solution |
| `meta_prompting_001` | meta_prompting | prompt_strategy | Designs the optimal prompt for a task first, then executes that prompt to solve the problem |
| `role_persona_001` | role_persona | prompt_strategy | Assigns expert identity to model for domain-specific reasoning, tone, and specialized problem-solving approaches |
| `debate_multi_agent_001` | debate_multi_agent | prompt_strategy | Simulates multiple agents with different perspectives debating, leading to more robust and examined conclusions |
| `contrastive_prompting_001` | contrastive_prompting | prompt_strategy | Generates multiple candidate answers, compares strengths and weaknesses systematically, then selects or synthesizes best |
| `rag_001` | retrieval_augmented_generation | prompt_strategy | Retrieves relevant context from external knowledge bases and injects it into prompts for accurate, grounded responses |
| `program_of_thought_001` | program_of_thought | prompt_strategy | Writes and executes code to perform calculations and logical operations, ensuring accurate computational results |
| `decomposition_001` | decomposition | prompt_strategy | Breaks complex tasks into smaller manageable subtasks, solves each independently, then combines results coherently |
| `retry_backoff_001` | retry_with_exponential_backoff | engineering | Handles transient failures by retrying operations with exponentially increasing delays between attempts |
| `circuit_breaker_001` | circuit_breaker | engineering | Prevents cascading failures by stopping requests to failing services temporarily, allowing recovery time |
| `csv_parser_quotes_001` | csv_parser_with_quotes | engineering | Parses CSV files correctly handling quoted fields, embedded commas, newlines within quotes, and escaped quotes |
| `safe_sql_builder_001` | safe_sql_query_builder | engineering | Builds SQL queries safely using parameterized queries to prevent SQL injection attacks |
| `regex_email_validator_001` | regex_email_validator | engineering | Validates email addresses using practical regex patterns that balance accuracy with readability |
| `dockerize_fastapi_001` | dockerize_fastapi_app | engineering | Creates production-ready Docker configuration for FastAPI applications with multi-stage builds and security |
| `off_by_one_fix_001` | off_by_one_loop_fix | repair | Identifies and fixes off-by-one errors in loops, array indexing, and boundary conditions |
| `null_pointer_guard_001` | null_pointer_guard | repair | Adds defensive checks to prevent null, None, or undefined reference errors in code |
| `web_search_tool_001` | web_search_tool | tool | Searches the web for current information on topics, returning relevant results with titles, URLs, snippets |
| `web_fetch_tool_001` | web_fetch_tool | tool | Fetches and extracts content from specific URLs, converting HTML to readable text for analysis |

---

## By Category

### Inquiry (4 skills)
*Knowledge gathering & verification*

| Skill | Semantic Description (5-20 words) | File |
|-------|-----------------------------------|------|
| humble_inquiry | Admits uncertainty explicitly, searches internal knowledge bases first, then falls back to web search with citations | `skills/humble_inquiry.md` |
| web_research | Conducts thorough web investigations using search and fetch tools, returning structured findings with source attribution | `skills/web_research.md` |
| source_verification | Cross-references information across multiple sources to verify accuracy and identify potential misinformation | `skills/source_verification.md` |
| knowledge_gap_analysis | Identifies specific gaps in knowledge about a topic, enabling targeted research rather than vague uncertainty | `skills/knowledge_gap_analysis.md` |

---

### Prompt Strategy (12 skills)
*Reasoning modes & prompt techniques*

| Skill | Semantic Description (5-20 words) | File |
|-------|-----------------------------------|------|
| chain_of_thought | Forces step-by-step reasoning before answering, improving accuracy on math, logic, and debugging tasks | `skills/chain_of_thought.md` |
| self_consistent_cot | Runs chain-of-thought multiple times with varied paths, uses majority voting to select most reliable answer | `skills/self_consistent_cot.md` |
| react_reasoning | Alternates between reasoning steps and tool usage, enabling systematic problem-solving with external resources | `skills/react_reasoning.md` |
| tree_of_thought | Explores multiple reasoning branches simultaneously, evaluates each path, and selects the best solution | `skills/tree_of_thought.md` |
| reflexion | Critiques its own output, identifies mistakes and gaps, then iteratively improves the solution | `skills/reflexion.md` |
| meta_prompting | Designs the optimal prompt for a task first, then executes that prompt to solve the problem | `skills/meta_prompting.md` |
| role_persona | Assigns expert identity to model for domain-specific reasoning, tone, and specialized approaches | `skills/role_persona.md` |
| debate_multi_agent | Simulates multiple agents debating with different perspectives, leading to more robust examined conclusions | `skills/debate_multi_agent.md` |
| contrastive_prompting | Generates multiple candidate answers, compares strengths and weaknesses systematically, selects or synthesizes best | `skills/contrastive_prompting.md` |
| rag | Retrieves relevant context from external knowledge bases, injects into prompts for accurate grounded responses | `skills/rag.md` |
| program_of_thought | Writes and executes code to perform calculations and logical operations, ensuring accurate computational results | `skills/program_of_thought.md` |
| decomposition | Breaks complex tasks into smaller manageable subtasks, solves each independently, combines results coherently | `skills/decomposition.md` |

---

### Engineering (6 skills)
*Reusable implementation patterns*

| Skill | Semantic Description (5-20 words) | File |
|-------|-----------------------------------|------|
| retry_with_exponential_backoff | Handles transient failures by retrying operations with exponentially increasing delays between attempts | `skills/retry_backoff.md` |
| circuit_breaker | Prevents cascading failures by stopping requests to failing services temporarily, allowing recovery time | `skills/circuit_breaker.md` |
| csv_parser_with_quotes | Parses CSV files correctly handling quoted fields, embedded commas, and escaped quotes | `skills/csv_parser_quotes.md` |
| safe_sql_query_builder | Builds SQL queries safely using parameterized queries to prevent SQL injection attacks | `skills/safe_sql_builder.md` |
| regex_email_validator | Validates email addresses using practical regex patterns that balance accuracy with readability | `skills/regex_email_validator.md` |
| dockerize_fastapi_app | Creates production-ready Docker configuration for FastAPI with multi-stage builds and security hardening | `skills/dockerize_fastapi.md` |

---

### Repair (2 skills)
*Common bug fixes*

| Skill | Semantic Description (5-20 words) | File |
|-------|-----------------------------------|------|
| off_by_one_loop_fix | Identifies and fixes off-by-one errors in loops, array indexing, and boundary conditions | `skills/off_by_one_fix.md` |
| null_pointer_guard | Adds defensive checks to prevent null, None, or undefined reference errors in code | `skills/null_pointer_guard.md` |

---

### Tool (2 skills)
*Executable tools*

| Skill | Semantic Description (5-20 words) | File |
|-------|-----------------------------------|------|
| web_search_tool | Searches the web for current information on topics, returning results with titles, URLs, snippets | `skills/web_search_tool.md` |
| web_fetch_tool | Fetches and extracts content from specific URLs, converting HTML to readable text for analysis | `skills/web_fetch_tool.md` |

---

## Usage Examples

### As Prompt Templates
```python
# Inject strategy into system prompt
from skills.chain_of_thought import CHAIN_OF_THOUGHT_PROMPT

system_prompt = f"""{CHAIN_OF_THOUGHT_PROMPT}

Task: {user_task}
"""
```

### As Executable Skills
```python
# Call Python implementation
from skills.humble_inquiry import humble_inquiry
from skills.decomposition import decomposition

result = await humble_inquiry(
    topic="Your question",
    qdrant_client=qdrant,
    postgres_conn=postgres,
    web_search_fn=web_search
)

result = await decomposition(
    task="Complex task",
    model_fn=model_call
)
```

---

## Strategy Selection by Task Type

| Task Type | Recommended Skills |
|-----------|-------------------|
| Math/Calculation | chain_of_thought, program_of_thought, self_consistent_cot |
| Logic Puzzles | chain_of_thought, tree_of_thought |
| Code Generation | reflexion, program_of_thought, role_persona (Senior Dev) |
| Debugging | chain_of_thought, reflexion, role_persona |
| Research | react_reasoning, rag, humble_inquiry, decomposition |
| Architecture | tree_of_thought, debate_multi_agent, role_persona |
| Creative Writing | contrastive_prompting, role_persona, tree_of_thought |
| Analysis | decomposition, rag, chain_of_thought |
| Decision Making | tree_of_thought, debate_multi_agent, contrastive_prompting |
| Technical Writing | role_persona (Tech Writer), decomposition |
| Security Analysis | role_persona (Security), debate_multi_agent, reflexion |
| Data Analysis | program_of_thought, rag, decomposition |
| API Integration | react_reasoning, retry_backoff, circuit_breaker |
| Database Queries | safe_sql_builder, rag |

---

## Cost vs. Quality Guide

| Tier | Skills | Cost | Quality Boost |
|------|--------|------|---------------|
| **Default** | chain_of_thought, role_persona, rag | 1x | +10-20% |
| **Enhanced** | reflexion, meta_prompting, program_of_thought | 2x | +10-25% |
| **Thorough** | self_consistent_cot, contrastive_prompting | 3-5x | +10-20% |
| **Comprehensive** | tree_of_thought, debate_multi_agent, decomposition | 4-6x | +20-40% |

---

## File Structure

```
PromptSKLib/
├── INDEX.md                      # This file - complete skill index
├── 12_core_strategies.md         # Strategy quick reference guide
├── README.md                     # Library overview
├── categories/
│   ├── inquiry.json
│   ├── prompt_strategy.json
│   ├── engineering.json
│   ├── repair.json
│   └── tool.json
├── skills/                       # 26 skill definitions
│   ├── humble_inquiry.md
│   ├── humble_inquiry.py         # Python implementation
│   ├── chain_of_thought.md
│   ├── self_consistent_cot.md
│   ├── react_reasoning.md
│   ├── tree_of_thought.md
│   ├── reflexion.md
│   ├── meta_prompting.md
│   ├── role_persona.md
│   ├── debate_multi_agent.md
│   ├── contrastive_prompting.md
│   ├── rag.md
│   ├── program_of_thought.md
│   ├── decomposition.md
│   ├── web_research.md
│   ├── source_verification.md
│   ├── knowledge_gap_analysis.md
│   ├── retry_backoff.md
│   ├── circuit_breaker.md
│   ├── csv_parser_quotes.md
│   ├── safe_sql_builder.md
│   ├── regex_email_validator.md
│   ├── dockerize_fastapi.md
│   ├── off_by_one_fix.md
│   ├── null_pointer_guard.md
│   ├── web_search_tool.md
│   └── web_fetch_tool.md
├── templates/
│   └── humble_inquiry_prompt.md
└── examples/
    └── humble_inquiry_examples.md
```

---

## Integration Points

### PromptForge
- Benchmark each strategy on different task types
- Track success rates and costs
- Build strategy → task_type mapping

### Alfred/FieldBench
- Auto-select strategy based on task classification
- Record which skills were used
- Measure improvement over baseline

### Counsel Collaboration
- Shared context per ticket
- Skills used recorded in context
- Models can build on previous skill applications

---

**Version:** 1.0  
**Maintained by:** PromptSKLib
