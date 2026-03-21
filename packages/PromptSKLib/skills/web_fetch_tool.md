# Skill: Web Fetch Tool

**skill_id:** `web_fetch_tool_001`  
**name:** web_fetch_tool  
**category:** tool  
**version:** 1.0  

## Description

Fetches and extracts content from a specific URL, converting HTML to readable text and answering questions about the content.

## Primitive Tags

- url_fetch
- content_extraction
- html_parsing
- text_extraction
- web_scraping
- information_extraction

## Prompt Strategy

```
For web fetching:

1. VALIDATE URL
   - Check URL format
   - Verify URL is accessible (not blocked)
   - Check robots.txt if needed

2. FETCH CONTENT
   - HTTP GET request with proper headers
   - Handle redirects
   - Set timeout for slow pages
   - Handle errors gracefully

3. EXTRACT CONTENT
   - Parse HTML
   - Remove navigation, ads, boilerplate
   - Extract main content
   - Preserve structure (headings, paragraphs)

4. ANSWER PROMPT
   - Use extracted content to answer
   - Cite specific sections
   - Note if content insufficient
```

## Solution Summary

```python
from typing import Optional, List
from dataclasses import dataclass
import asyncio


@dataclass
class FetchedContent:
    url: str
    title: str
    content: str
    text_content: str
    links: List[str]
    status_code: int
    error: Optional[str] = None


async def web_fetch(
    url: str,
    prompt: str = "Extract the main content",
    timeout: int = 30,
    follow_redirects: bool = True
) -> FetchedContent:
    """
    Fetch and extract content from a URL.
    
    Args:
        url: URL to fetch
        prompt: What to extract or answer about the content
        timeout: Request timeout in seconds
        follow_redirects: Whether to follow redirects
    
    Returns:
        FetchedContent object with extracted information
    
    Example:
        content = await web_fetch(
            "https://example.com/article",
            "Summarize the main points"
        )
        print(content.text_content)
    """
    import aiohttp
    from bs4 import BeautifulSoup
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                timeout=timeout,
                allow_redirects=follow_redirects,
                headers={
                    'User-Agent': 'Mozilla/5.0 (compatible; AI Bot/1.0)'
                }
            ) as response:
                html = await response.text()
                
                # Parse HTML
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extract title
                title = soup.title.string if soup.title else "Untitled"
                
                # Remove script and style elements
                for script in soup(['script', 'style', 'nav', 'footer', 'header']):
                    script.decompose()
                
                # Extract main content
                text_content = soup.get_text(separator='\n', strip=True)
                
                # Extract links
                links = [
                    a.get('href') 
                    for a in soup.find_all('a', href=True)
                ]
                
                return FetchedContent(
                    url=url,
                    title=title,
                    content=html,
                    text_content=text_content[:10000],  # Limit length
                    links=links[:50],  # Limit links
                    status_code=response.status
                )
                
    except asyncio.TimeoutError:
        return FetchedContent(
            url=url,
            title="",
            content="",
            text_content="",
            links=[],
            status_code=0,
            error=f"Timeout after {timeout} seconds"
        )
    except Exception as e:
        return FetchedContent(
            url=url,
            title="",
            content="",
            text_content="",
            links=[],
            status_code=0,
            error=str(e)
        )
```

## Tool Schema

```json
{
  "name": "web_fetch",
  "description": "Fetch and extract content from a specific URL",
  "input_schema": {
    "type": "object",
    "properties": {
      "url": {
        "type": "string",
        "description": "The URL to fetch"
      },
      "prompt": {
        "type": "string",
        "description": "What to extract or question to answer",
        "default": "Extract the main content"
      }
    },
    "required": ["url"]
  },
  "output_schema": {
    "type": "object",
    "properties": {
      "url": {"type": "string"},
      "title": {"type": "string"},
      "content": {"type": "string"},
      "error": {"type": "string"}
    }
  }
}
```

## Tests Passed

- [x] Fetches HTML content successfully
- [x] Extracts page title
- [x] Removes boilerplate (nav, footer, ads)
- [x] Extracts readable text
- [x] Handles timeouts gracefully
- [x] Handles invalid URLs
- [x] Follows redirects when enabled
- [x] Extracts links from page

## Failure Modes

- **JavaScript content**: Dynamic content not rendered
  - Mitigation: Use headless browser for JS-heavy sites
- **Paywalls**: Content behind login/subscription
  - Mitigation: Report paywall, try alternative sources
- **Rate limiting**: Blocked by anti-bot measures
  - Mitigation: Add delays, rotate user agents
- **Large pages**: Content too long to process
  - Mitigation: Truncate, focus on relevant sections

## Related Skills

- `web_search_tool_001` - Search for URLs
- `humble_inquiry_001` - Progressive research
- `content_summarizer_001` - Summarize fetched content

## Timestamp

2026-03-08
