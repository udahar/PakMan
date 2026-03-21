#!/usr/bin/env python3
"""
Context Distiller - Auto-Summarization for Long Context
Starter implementation
"""

import math
from typing import Optional
from dataclasses import dataclass


def estimate_tokens(text: str) -> int:
    """Rough token estimation (4 chars ~= 1 token)"""
    return len(text) // 4


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Simple cosine similarity"""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0
    return dot / (norm_a * norm_b)


class RelevanceScorer:
    def __init__(self, embedding_model: str = "bge-m3:latest"):
        self.embedding_model = embedding_model
        # In production, use actual embeddings

    def split_into_passages(self, text: str, chunk_size: int = 1000) -> list[str]:
        """Split text into passages"""
        passages = []
        for i in range(0, len(text), chunk_size):
            passages.append(text[i : i + chunk_size])
        return passages

    def score_passages(self, text: str, query: str, top_k: int = 10) -> list[dict]:
        """Score each passage by relevance"""
        # Split into passages
        passages = self.split_into_passages(text)

        # Simple keyword matching scoring (replace with embeddings in production)
        query_terms = set(query.lower().split())

        scored = []
        for i, passage in enumerate(passages):
            passage_terms = set(passage.lower().split())
            overlap = len(query_terms & passage_terms)

            # Score based on keyword overlap
            score = overlap / len(query_terms) if query_terms else 0

            # Bonus for query terms appearing multiple times
            for term in query_terms:
                score += passage.lower().count(term) * 0.1

            scored.append(
                {"index": i, "text": passage, "score": score, "char_start": i * 1000}
            )

        # Sort and return top_k
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]


class ContextSummarizer:
    def __init__(self, llm_model: str = "qwen2.5:7b"):
        self.llm_model = llm_model
        self.scorer = RelevanceScorer()

    def generate_summary(self, passages: list[dict], query: str) -> str:
        """Generate summary that connects passages"""
        # In production, use actual LLM
        # For now, return a placeholder

        top_passages = passages[:3]
        summary_parts = [f"Relevant passages for '{query}':"]

        for p in top_passages:
            preview = p["text"][:200] + "..." if len(p["text"]) > 200 else p["text"]
            summary_parts.append(f"\n[Passage {p['index']}] Score: {p['score']:.2f}")
            summary_parts.append(preview)

        return "\n".join(summary_parts)

    def distill(self, document: str, query: str, max_tokens: int = 5000) -> dict:
        """Main distillation method"""
        # Score passages
        passages = self.scorer.score_passages(document, query)

        # Check token count
        total_tokens = sum(estimate_tokens(p["text"]) for p in passages)

        # If too many tokens, take fewer passages
        while total_tokens > max_tokens and len(passages) > 1:
            passages = passages[:-1]
            total_tokens = sum(estimate_tokens(p["text"]) for p in passages)

        # Generate summary
        summary = self.generate_summary(passages, query)

        return {
            "summary": summary,
            "passages": passages,
            "num_passages": len(passages),
            "estimated_tokens": total_tokens,
            "query": query,
        }


class ContextDistiller:
    """Main entry point"""

    def __init__(self):
        self.summarizer = ContextSummarizer()

    def process(self, document_text: str, query: str, max_tokens: int = 5000) -> dict:
        """Process document and return distilled context"""
        result = self.summarizer.distill(document_text, query, max_tokens)
        return result

    def process_file(self, file_path: str, query: str, max_tokens: int = 5000) -> dict:
        """Load and process file"""
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            document = f.read()
        return self.process(document, query, max_tokens)


# Demo
if __name__ == "__main__":
    # Sample long document
    sample_doc = (
        """
    Authentication System
    
    The authentication system handles user login and session management.
    It supports multiple methods including password-based, OAuth, and API keys.
    
    Login Flow
    When a user logs in, the system validates credentials against the database.
    On success, a JWT token is issued with a 1-hour expiration.
    The token contains user ID, roles, and permissions.
    
    Session Management
    Sessions are stored in Redis for fast access.
    Each session has a unique ID and tracks user activity.
    Sessions expire after 30 minutes of inactivity.
    
    Security Considerations
    Passwords are hashed using bcrypt with salt.
    Rate limiting prevents brute force attacks.
    CSRF protection is enabled for all forms.
    
    API Keys
    API keys can be generated in the user settings.
    They have scoped permissions and expiration dates.
    Key rotation is recommended every 90 days.
    
    OAuth Integration
    The system supports Google, GitHub, and Microsoft OAuth.
    OAuth tokens are exchanged for JWT tokens.
    Refresh tokens are stored securely in the database.
    """.strip()
        * 10
    )  # Make it longer

    distiller = ContextDistiller()

    # Test with query
    result = distiller.process(sample_doc, "How does login work?")

    print("=== DISTILLER RESULT ===")
    print(f"Query: {result['query']}")
    print(f"Passages used: {result['num_passages']}")
    print(f"Estimated tokens: {result['estimated_tokens']}")
    print(f"\n=== SUMMARY ===")
    print(result["summary"])
