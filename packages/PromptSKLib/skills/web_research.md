# Skill: Web Research

**skill_id:** `web_research_001`  
**name:** web_research  
**category:** inquiry  
**version:** 1.0  

## Description

Conducts thorough web research on a topic using search and fetch tools, returning structured findings with source attribution.

## Primitive Tags

- web_search
- url_fetch
- extract_key_points
- compare_sources
- synthesize_information

## Prompt Strategy

```
For web research on topic:

1. FORMULATE SEARCH QUERY
   - Extract key terms from topic
   - Generate specific search query
   
2. EXECUTE WEB SEARCH
   - Use web_search tool
   - Collect top 5-10 results
   
3. FETCH KEY SOURCES
   - Use web_fetch on most relevant URLs
   - Extract key information from each
   
4. SYNTHESIZE FINDINGS
   - Compare information across sources
   - Identify consensus and disagreements
   - Note source credibility
   - Return structured summary
```

## Solution Summary

```python
async def web_research(topic: str, depth: int = 2) -> dict:
    # Search
    search_results = await web_search(topic, num_results=10)
    
    # Fetch top sources
    fetched = []
    for result in search_results[:depth]:
        content = await web_fetch(result['url'], f"Extract key information about: {topic}")
        fetched.append({
            "url": result['url'],
            "title": result['title'],
            "content": content
        })
    
    # Synthesize
    return {
        "topic": topic,
        "search_results": search_results,
        "fetched_sources": fetched,
        "key_findings": extract_key_points(fetched),
        "consensus": identify_consensus(fetched),
        "disagreements": identify_disagreements(fetched)
    }
```

## Tests Passed

- [x] Returns multiple sources
- [x] Fetches full content from URLs
- [x] Identifies consensus vs disagreements

## Failure Modes

- **Paywalled content**: Cannot access full articles
- **Dynamic content**: JavaScript-heavy sites may not render
- **Rate limiting**: Too many requests blocked

## Timestamp

2026-03-08
