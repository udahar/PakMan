"""
Humble Inquiry Skill Implementation

When the AI doesn't know something, it:
1. Admits uncertainty explicitly
2. Searches Qdrant vector store
3. Searches Postgres database
4. Falls back to web search if internal sources empty
5. Synthesizes findings with source attribution
"""

from typing import Optional
from dataclasses import dataclass, field


@dataclass
class InquiryResult:
    topic: str
    admission: str
    internal_search: Optional[dict] = None
    web_search: Optional[dict] = None
    summary: Optional[str] = None
    confidence: float = 0.0
    sources: list = field(default_factory=list)
    remaining_uncertainties: list = field(default_factory=list)


async def humble_inquiry(
    topic: str,
    qdrant_client=None,
    postgres_conn=None,
    web_search_fn=None,
    web_fetch_fn=None
) -> InquiryResult:
    """
    Progressive inquiry skill: admit → search internal → search web → synthesize
    
    Args:
        topic: The topic to research
        qdrant_client: Qdrant client for vector search
        postgres_conn: Postgres connection for structured search
        web_search_fn: Web search function (e.g., tavily, google)
        web_fetch_fn: Web fetch function for URL content
    
    Returns:
        InquiryResult with findings and confidence level
    """
    result = InquiryResult(
        topic=topic,
        admission=f"I need to research: {topic}"
    )
    
    # Step 1: Search internal knowledge (Qdrant)
    qdrant_results = []
    if qdrant_client:
        qdrant_results = await _search_qdrant(qdrant_client, topic, limit=5)
    
    # Step 2: Search internal knowledge (Postgres)
    postgres_results = []
    if postgres_conn:
        postgres_results = await _search_postgres(postgres_conn, topic, limit=5)
    
    result.internal_search = {
        "qdrant": qdrant_results,
        "postgres": postgres_results,
        "found": bool(qdrant_results or postgres_results)
    }
    
    # Step 3: Web search if internal knowledge insufficient
    if not result.internal_search["found"]:
        if web_search_fn:
            web_results = await _search_web(
                web_search_fn, 
                web_fetch_fn, 
                topic, 
                num_results=5
            )
            result.web_search = web_results
            result.sources.extend(web_results.get("sources", []))
    
    # Step 4: Synthesize findings
    all_sources = qdrant_results + postgres_results
    if result.web_search:
        all_sources.extend(result.web_search.get("sources", []))
    
    result.summary = _synthesize_findings(all_sources, topic)
    result.confidence = _calculate_confidence(all_sources)
    result.remaining_uncertainties = _identify_remaining_gaps(all_sources, topic)
    result.sources = all_sources
    
    return result


async def _search_qdrant(client, topic: str, limit: int = 5) -> list:
    """Search Qdrant vector store for relevant knowledge"""
    try:
        # Embed the topic
        embedding = await _embed_text(topic)
        
        # Search collection
        results = client.search(
            collection_name="skills_knowledge",
            query_vector=embedding,
            limit=limit
        )
        
        return [
            {
                "source": "qdrant",
                "content": hit.payload.get("content", ""),
                "metadata": hit.payload,
                "score": hit.score
            }
            for hit in results
            if hit.score > 0.5  # Relevance threshold
        ]
    except Exception as e:
        print(f"Qdrant search error: {e}")
        return []


async def _search_postgres(conn, topic: str, limit: int = 5) -> list:
    """Search Postgres for structured knowledge"""
    try:
        async with conn.cursor() as cur:
            # Full-text search on skills/knowledge tables
            await cur.execute("""
                SELECT id, content, metadata, similarity
                FROM knowledge_base
                WHERE content ILIKE %s OR metadata::text ILIKE %s
                ORDER BY similarity DESC
                LIMIT %s
            """, (f"%{topic}%", f"%{topic}%", limit))
            
            rows = await cur.fetchall()
            
            return [
                {
                    "source": "postgres",
                    "content": row[1],
                    "metadata": row[2],
                    "similarity": row[3]
                }
                for row in rows
            ]
    except Exception as e:
        print(f"Postgres search error: {e}")
        return []


async def _search_web(search_fn, fetch_fn, topic: str, num_results: int = 5) -> dict:
    """Search web and fetch content from top results"""
    sources = []
    
    try:
        # Search
        search_results = await search_fn(topic, num_results=num_results)
        
        # Fetch top results
        for result in search_results[:num_results]:
            if 'url' in result:
                content = await fetch_fn(
                    result['url'],
                    f"Extract key information about: {topic}"
                )
                sources.append({
                    "source": "web",
                    "url": result['url'],
                    "title": result.get('title', 'Untitled'),
                    "content": content,
                    "snippet": result.get('content', '')
                })
        
        return {
            "query": topic,
            "sources": sources,
            "search_results": search_results
        }
    except Exception as e:
        print(f"Web search error: {e}")
        return {"query": topic, "sources": [], "error": str(e)}


async def _embed_text(text: str) -> list[float]:
    """Generate embedding for text - placeholder for actual embedding service"""
    # TODO: Integrate with actual embedding model
    # Could use: sentence-transformers, OpenAI embeddings, etc.
    raise NotImplementedError("Embedding service not configured")


def _synthesize_findings(sources: list, topic: str) -> str:
    """Synthesize findings from multiple sources into coherent summary"""
    if not sources:
        return f"No information found about: {topic}"
    
    # Group by source type
    internal = [s for s in sources if s.get("source") in ("qdrant", "postgres")]
    web = [s for s in sources if s.get("source") == "web"]
    
    summary_parts = []
    
    if internal:
        summary_parts.append("From internal knowledge:")
        for src in internal[:3]:
            summary_parts.append(f"- {src.get('content', '')[:200]}")
    
    if web:
        summary_parts.append("\nFrom web sources:")
        for src in web[:3]:
            summary_parts.append(f"- [{src.get('title', 'Untitled')}]({src.get('url', '')}): {src.get('content', '')[:200]}")
    
    return "\n".join(summary_parts)


def _calculate_confidence(sources: list) -> float:
    """Calculate confidence score based on source quality and quantity"""
    if not sources:
        return 0.0
    
    # Base confidence from number of sources
    count_score = min(len(sources) / 5.0, 1.0)  # Max at 5 sources
    
    # Quality score from source types
    internal_count = sum(1 for s in sources if s.get("source") in ("qdrant", "postgres"))
    web_count = sum(1 for s in sources if s.get("source") == "web")
    
    quality_score = (internal_count * 0.8 + web_count * 0.6) / max(len(sources), 1)
    
    # Combined confidence
    confidence = (count_score * 0.6 + quality_score * 0.4)
    
    return round(confidence, 2)


def _identify_remaining_gaps(sources: list, topic: str) -> list:
    """Identify what's still unknown after research"""
    # TODO: Implement gap detection based on topic decomposition
    # For now, return empty - future enhancement
    return []
