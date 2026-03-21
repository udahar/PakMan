# Skill: Humble Inquiry

**skill_id:** `humble_inquiry_001`  
**name:** humble_inquiry  
**category:** inquiry  
**version:** 1.0  

## Description

When the AI doesn't know something, it admits uncertainty explicitly, then systematically searches for answers through internal knowledge bases (Qdrant/Postgres) before falling back to web search.

## Primitive Tags

- admit_uncertainty
- search_internal_knowledge
- search_web
- progressive_disclosure
- cite_sources
- summarize_findings

## Prompt Strategy

```
When encountering unknown information:

1. ADMIT UNCERTAINTY
   - Explicitly state: "I'm not certain about this..."
   - Identify the specific knowledge gap
   
2. SEARCH INTERNAL KNOWLEDGE
   - Query Qdrant vector store with the topic
   - Query Postgres for structured data
   - Report findings or absence thereof
   
3. SEARCH WEB (if internal search fails)
   - Use web_search tool to gather current information
   - Fetch relevant URLs with web_fetch
   - Cross-reference multiple sources
   
4. SYNTHESIZE ANSWER
   - Provide a summary statement
   - Cite sources (internal vs web)
   - Note confidence level
   - Flag any remaining uncertainties
```

## Model Used

Any reasoning-capable model (qwen2.5:3b+, claude-3, gpt-4)

## Solution Summary

```python
async def humble_inquiry(topic: str) -> dict:
    result = {
        "topic": topic,
        "admission": None,
        "internal_search": None,
        "web_search": None,
        "summary": None,
        "confidence": None,
        "sources": []
    }
    
    # Step 1: Admit uncertainty
    result["admission"] = f"I need to research: {topic}"
    
    # Step 2: Search internal knowledge
    qdrant_results = await search_qdrant(topic, limit=5)
    postgres_results = await search_postgres(topic, limit=5)
    
    if qdrant_results or postgres_results:
        result["internal_search"] = {
            "qdrant": qdrant_results,
            "postgres": postgres_results
        }
        result["sources"].extend(qdrant_results + postgres_results)
    
    # Step 3: Web search if needed
    if not (qdrant_results or postgres_results):
        web_results = await web_search(topic)
        result["web_search"] = web_results
        result["sources"].extend(web_results)
    
    # Step 4: Synthesize
    result["summary"] = synthesize_findings(result["sources"])
    result["confidence"] = calculate_confidence(result["sources"])
    
    return result
```

## Tests Passed

- [x] Admits uncertainty when topic unknown
- [x] Searches Qdrant before web
- [x] Searches Postgres before web  
- [x] Falls back to web search when internal empty
- [x] Cites sources in final answer
- [x] Reports confidence level

## Benchmark Score

Pending evaluation

## Failure Modes

- **False confidence**: Model claims knowledge without search
  - Mitigation: Enforce search steps in prompt
- **Stale internal data**: Qdrant/Postgres has outdated info
  - Mitigation: Check timestamps, prefer recent web data
- **Web search unavailable**: No internet access
  - Mitigation: Clearly state limitation, provide best internal answer

## Created From Task

Initial skill library creation - "AI admits uncertainty then searches"

## Embedding Vector

`[To be generated on storage]`

## Timestamp

2026-03-08

## Related Skills

- `web_research_001` - Deep web investigation
- `source_verification_001` - Cross-reference multiple sources
- `knowledge_gap_analysis_001` - Identify specific unknowns
