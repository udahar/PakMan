# Skill: Web Search Tool

**skill_id:** `web_search_tool_001`  
**name:** web_search_tool  
**category:** tool  
**version:** 1.0  

## Description

Searches the web for current information on a given topic, returning relevant results with titles, URLs, and snippets.

## Primitive Tags

- web_search
- information_retrieval
- search_query
- result_ranking
- current_information
- external_knowledge

## Prompt Strategy

```
For web search:

1. FORMULATE QUERY
   - Extract key terms from user question
   - Create specific, focused search query
   - Include relevant qualifiers (date, type, etc.)

2. EXECUTE SEARCH
   - Use search API (Tavily, Google, Bing, etc.)
   - Request appropriate number of results (5-10)
   - Include content/snippets if available

3. PROCESS RESULTS
   - Extract title, URL, snippet from each
   - Filter irrelevant results
   - Rank by relevance and credibility

4. RETURN STRUCTURED RESULTS
   - List of result objects
   - Include metadata (source, date if available)
   - Preserve original query for reference
```

## Solution Summary

```python
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    source: Optional[str] = None
    date: Optional[str] = None


async def web_search(
    query: str,
    num_results: int = 5,
    search_depth: str = "basic",
    include_domains: List[str] = None,
    exclude_domains: List[str] = None
) -> List[SearchResult]:
    """
    Search the web for information.
    
    Args:
        query: Search query string
        num_results: Number of results to return
        search_depth: "basic" or "advanced"
        include_domains: Optional list of domains to include
        exclude_domains: Optional list of domains to exclude
    
    Returns:
        List of SearchResult objects
    
    Example:
        results = await web_search(
            "Python async best practices 2025",
            num_results=5
        )
        for r in results:
            print(f"{r.title}: {r.url}")
    """
    # Implementation depends on search provider
    # Example with Tavily:
    from tavily import TavilyClient
    
    client = TavilyClient(api_key="...")
    
    response = client.search(
        query=query,
        search_depth=search_depth,
        max_results=num_results,
        include_domains=include_domains,
        exclude_domains=exclude_domains
    )
    
    return [
        SearchResult(
            title=result.get('title', 'Untitled'),
            url=result.get('url', ''),
            snippet=result.get('content', ''),
            source=result.get('source'),
            date=result.get('date')
        )
        for result in response.get('results', [])
    ]
```

## Tool Schema

```json
{
  "name": "web_search",
  "description": "Search the web for current information on a topic",
  "input_schema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "The search query"
      },
      "num_results": {
        "type": "integer",
        "description": "Number of results (default: 5)",
        "default": 5
      }
    },
    "required": ["query"]
  },
  "output_schema": {
    "type": "array",
    "items": {
      "type": "object",
      "properties": {
        "title": {"type": "string"},
        "url": {"type": "string"},
        "snippet": {"type": "string"}
      }
    }
  }
}
```

## Tests Passed

- [x] Returns relevant results for query
- [x] Handles empty result sets
- [x] Respects num_results limit
- [x] Includes title, URL, snippet
- [x] Handles special characters in query
- [x] Filters by domain when specified

## Failure Modes

- **No results**: Query too specific or obscure topic
  - Mitigation: Broaden query, reduce filters
- **Irrelevant results**: Query too vague
  - Mitigation: Add specific qualifiers
- **Rate limiting**: Too many requests
  - Mitigation: Implement retry with backoff

## Related Skills

- `web_fetch_tool_001` - Fetch content from URL
- `humble_inquiry_001` - Progressive research
- `source_verification_001` - Cross-reference sources

## Timestamp

2026-03-08
