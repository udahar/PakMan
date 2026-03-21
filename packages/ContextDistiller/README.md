# Context Distiller - Auto-Summarization for Long Context

## The Concept

Instead of raw RLM (Recursive Language Model) that chunks and re-chunks, build a smarter module that **identifies and extracts the most relevant passages** before feeding to the LLM.

Uses importance scoring + intelligent extraction to make 100k+ token files manageable.

```
┌─────────────────────────────────────────────────────────────┐
│                   Context Distiller                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Input: 100k+ token document                                 │
│       │                                                      │
│       ▼                                                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Relevance Scorer                        │   │
│  │                                                      │   │
│  │  Given query: "How does auth work?"                 │   │
│  │                                                      │   │
│  │  1. Extract key terms: [auth, login, session]        │   │
│  │  2. Score each paragraph (TF-IDF + embeddings)     │   │
│  │  3. Rank by relevance                               │   │
│  │                                                      │   │
│  └──────────────────────┬──────────────────────────────┘   │
│                         │                                    │
│       ┌─────────────────┴─────────────────┐               │
│       ▼                                   ▼                │
│  ┌──────────────────┐            ┌──────────────────┐      │
│  │  Passages       │            │  Summary         │      │
│  │  [score: 0.95]  │            │  Generator       │      │
│  │  [score: 0.87]  │──────┐    │                  │      │
│  │  [score: 0.82]  │      │    │  - Condense     │      │
│  │  [score: 0.75]  │      │    │  - Preserve    │      │
│  │  ...            │      │    │  - Connect      │      │
│  └──────────────────┘      │    └──────────────────┘      │
│                            │                                 │
│                            ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Distilled Context                      │   │
│  │                                                      │   │
│  │  ~5k tokens (instead of 100k)                       │   │
│  │  - Top 10 relevant passages                         │   │
│  │  - Auto-generated summary                           │   │
│  │  - Preserved citations to original                 │   │
│  │                                                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                            │                                 │
│                            ▼                                 │
│               LLM processes easily!                         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Pre-Work / Integration Guide

### Step 1: Create Scorer

```python
# scorer.py
from langchain_ollama import ChatOllama
from langchain_community.embeddings import OllamaEmbeddings

class RelevanceScorer:
    def __init__(self):
        self.embeddings = OllamaEmbeddings(model="bge-m3:latest")
        self.llm = ChatOllama(model="qwen2.5:7b")
        
    def score_passages(self, text: str, query: str, top_k: int = 10) -> list[dict]:
        """Score each passage by relevance to query"""
        
        # Split into passages
        passages = self.split_into_passages(text)
        
        # Get query embedding
        query_emb = self.embeddings.embed_query(query)
        
        # Score each passage
        scored = []
        for i, passage in enumerate(passages):
            passage_emb = self.embeddings.embed_query(passage)
            score = cosine_similarity(query_emb, passage_emb)
            
            # Also use keyword matching
            keyword_score = self.keyword_match(query, passage)
            
            # Combined score
            final_score = 0.7 * score + 0.3 * keyword_score
            
            scored.append({
                "index": i,
                "text": passage,
                "score": final_score,
                "start_char": i * 1000  # Approximate
            })
            
        # Sort and return top_k
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]
        
    def keyword_match(self, query: str, passage: str) -> float:
        """Simple keyword overlap scoring"""
        query_terms = set(query.lower().split())
        passage_terms = set(passage.lower().split())
        overlap = len(query_terms & passage_terms)
        return overlap / len(query_terms) if query_terms else 0
```

### Step 2: Create Summarizer

```python
# summarizer.py
class ContextSummarizer:
    def __init__(self):
        self.llm = ChatOllama(model="qwen2.5:7b")
        
    def generate_summary(self, passages: list[dict], query: str) -> str:
        """Create a summary that ties passages together"""
        
        combined = "\n\n".join([
            f"[Passage {p['index']}]: {p['text'][:500]}..."
            for p in passages
        ])
        
        prompt = f"""Given these passages from a document and the user's query, 
create a brief summary that connects them:

Query: {query}

Passages:
{combined}

Summary (keep under 500 words):
"""
        response = self.llm.invoke(prompt)
        return response.content
        
    def distill(self, document: str, query: str, max_tokens: int = 5000) -> dict:
        """Main distillation method"""
        
        # Score passages
        passages = self.scorer.score_passages(document, query)
        
        # Check token count
        total_tokens = estimate_tokens(passages)
        
        if total_tokens > max_tokens:
            # Take fewer passages
            passages = self.fit_to_budget(passages, max_tokens)
            
        # Generate summary
        summary = self.generate_summary(passages, query)
        
        return {
            "summary": summary,
            "passages": passages,
            "total_passages": len(passages),
            "estimated_tokens": estimate_tokens(passages)
        }
```

### Step 3: Create Distiller Class

```python
# distiller.py
from scorer import RelevanceScorer
from summarizer import ContextSummarizer

class ContextDistiller:
    def __init__(self):
        self.scorer = RelevanceScorer()
        self.summarizer = ContextSummarizer()
        
    def process(self, document_path: str, query: str, max_context_tokens: int = 5000):
        """Main entry point"""
        
        # Load document
        with open(document_path) as f:
            document = f.read()
            
        # Distill
        result = self.summarizer.distill(document, query, max_context_tokens)
        
        return result
        
    def process_streaming(self, document_path: str, query: str, chunk_size: int = 10000):
        """For very large documents, process in chunks"""
        # For documents too large to fit in memory
        pass
```

### Step 4: Add Caching

```python
# Cache expensive computations
import hashlib

class CachedDistiller(ContextDistiller):
    def __init__(self):
        super().__init__()
        self.cache = {}
        
    def process(self, document_path: str, query: str, max_tokens: int = 5000):
        cache_key = f"{hash(document_path)}:{hash(query)}:{max_tokens}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
            
        result = super().process(document_path, query, max_tokens)
        self.cache[cache_key] = result
        return result
```

## Quick Start

```bash
cd PromptRD/context_distiller
python distiller.py --file /path/to/large_doc.pdf --query "How does auth work?"
```

## Files

- `distiller.py` - Main class
- `scorer.py` - Relevance scoring
- `summarizer.py` - Summary generation
- `cache.py` - Caching layer
- `chunking.py` - Document parsing
- `demo.py` - Test it out

## Integration with Frank

```python
# Replace --rlm flag with smarter distiller
if args.distill:
    from context_distiller import ContextDistiller
    
    distiller = ContextDistiller()
    
    # First, distill the context
    result = distiller.process(args.file, args.prompt)
    
    # Then, query with distilled context
    response = llm.invoke(
        f"Based on this context:\n\n{result['summary']}\n\n{result['passages']}\n\n"
        f"Answer: {args.prompt}"
    )
```

Or use with RLM (combine approaches):
```python
# First distill to get relevant passages
# Then use RLM on just those passages
```

## Extension Ideas

- Multi-modal (handle PDFs, images)
- Citation preservation (link back to original)
- Incremental updates (don't re-summarize everything)
- User feedback (thumbs up/down on relevance)
- Multiple summaries (different perspectives)
- Streaming for huge files
- Query expansion (add related terms)
