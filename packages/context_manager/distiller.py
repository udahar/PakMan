"""
Context Distiller - Auto-Summarization for Long Context
"""

import math
from typing import Optional, List, Dict


def estimate_tokens(text: str) -> int:
    """Rough token estimation (4 chars ~= 1 token)"""
    return len(text) // 4


class ContextDistiller:
    """
    Condense long context into relevant summaries.

    Usage:
        from context_manager import ContextDistiller

        distiller = ContextDistiller()
        result = distiller.distill(document, "login flow", max_tokens=2000)
    """

    def __init__(self, llm_model: str = None):
        self.llm_model = llm_model

    def distill(self, document: str, query: str, max_tokens: int = 5000) -> Dict:
        """Distill document to relevant passages."""
        passages = self._split_passages(document)
        scored = self._score_passages(passages, query)

        total_tokens = sum(estimate_tokens(p["text"]) for p in scored)

        while total_tokens > max_tokens and len(scored) > 1:
            scored = scored[:-1]
            total_tokens = sum(estimate_tokens(p["text"]) for p in scored)

        summary = self._generate_summary(scored, query)

        return {
            "summary": summary,
            "passages": scored,
            "num_passages": len(scored),
            "estimated_tokens": total_tokens,
            "query": query,
        }

    def _split_passages(self, text: str, chunk_size: int = 1000) -> List[str]:
        """Split text into passages."""
        return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]

    def _score_passages(self, passages: List[str], query: str) -> List[Dict]:
        """Score passages by relevance."""
        query_terms = set(query.lower().split())

        scored = []
        for i, passage in enumerate(passages):
            passage_terms = set(passage.lower().split())
            overlap = len(query_terms & passage_terms)

            score = overlap / len(query_terms) if query_terms else 0

            for term in query_terms:
                score += passage.lower().count(term) * 0.1

            scored.append(
                {"index": i, "text": passage, "score": score, "char_start": i * 1000}
            )

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored

    def _generate_summary(self, passages: List[Dict], query: str) -> str:
        """Generate summary from passages."""
        top = passages[:3]
        parts = [f"Relevant passages for '{query}':"]

        for p in top:
            preview = p["text"][:200] + "..." if len(p["text"]) > 200 else p["text"]
            parts.append(f"\n[Passage {p['index']}] Score: {p['score']:.2f}")
            parts.append(preview)

        return "\n".join(parts)

    def process_file(self, file_path: str, query: str, max_tokens: int = 5000) -> Dict:
        """Load and process file."""
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            document = f.read()
        return self.distill(document, query, max_tokens)
