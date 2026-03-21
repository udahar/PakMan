# Skill: Knowledge Gap Analysis

**skill_id:** `knowledge_gap_analysis_001`  
**name:** knowledge_gap_analysis  
**category:** inquiry  
**version:** 1.0  

## Description

Identifies specific gaps in knowledge about a topic, enabling targeted research rather than vague uncertainty.

## Primitive Tags

- identify_unknowns
- structure_knowledge
- gap_detection
- targeted_questioning

## Prompt Strategy

```
For analyzing knowledge gaps:

1. DECOMPOSE TOPIC
   - Break topic into sub-components
   - Create knowledge tree/outline
   
2. ASSESS KNOWLEDGE
   - For each component: known vs unknown
   - Identify specific missing information
   
3. PRIORITIZE GAPS
   - Critical gaps (block understanding)
   - Important gaps (reduce confidence)
   - Minor gaps (nice to know)
   
4. FORMULATE QUERIES
   - Create specific search queries for each gap
   - Enable targeted research
```

## Solution Summary

```python
def analyze_knowledge_gaps(topic: str, known_context: dict) -> dict:
    # Decompose topic
    knowledge_tree = decompose_topic(topic)
    
    gaps = {
        "critical": [],   # Must know to understand topic
        "important": [],  # Should know for full understanding
        "minor": []       # Nice to know details
    }
    
    for node in knowledge_tree:
        if not has_knowledge(node, known_context):
            gap = {
                "component": node,
                "question": formulate_question(node),
                "priority": assess_priority(node, knowledge_tree)
            }
            gaps[gap["priority"]].append(gap)
    
    return {
        "topic": topic,
        "knowledge_tree": knowledge_tree,
        "gaps": gaps,
        "targeted_queries": generate_queries(gaps)
    }
```

## Tests Passed

- [x] Breaks topics into components
- [x] Identifies specific unknowns
- [x] Prioritizes knowledge gaps

## Failure Modes

- **Over-decomposition**: Too many tiny gaps
  - Mitigation: Focus on high-level gaps first
- **False gaps**: Model thinks it knows but doesn't
  - Mitigation: Verify with actual retrieval

## Timestamp

2026-03-08
