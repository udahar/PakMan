"""
Relevance Scoring
"""

from typing import Dict, List, Optional
import re


class RelevanceScorer:
    """Score context relevance to query."""

    TASK_KEYWORDS = {
        "code_generation": [
            "code",
            "function",
            "class",
            "implement",
            "create",
            "build",
            "write",
            "rust",
            "python",
            "javascript",
        ],
        "code_review": ["review", "refactor", "improve", "code", "lint", "check"],
        "research": [
            "research",
            "find",
            "search",
            "investigate",
            "explain",
            "what is",
            "how does",
        ],
        "analysis": ["analyze", "compare", "evaluate", "assess", "data", "metrics"],
        "creative_writing": ["write", "story", "blog", "post", "content", "creative"],
        "problem_solving": [
            "fix",
            "bug",
            "error",
            "issue",
            "problem",
            "solve",
            "debug",
        ],
        "planning": [
            "plan",
            "roadmap",
            "strategy",
            "approach",
            "design",
            "architecture",
        ],
    }

    def __init__(self, use_embeddings: bool = False):
        self.use_embeddings = use_embeddings
        self._embedding_model = None

    def score(
        self, name: str, content: str, query: str, task_type: str = None
    ) -> float:
        """Score relevance of context item to query."""
        scores = []

        scores.append(self._keyword_score(content, query) * 0.3)
        scores.append(self._task_match_score(content, query, task_type) * 0.4)
        scores.append(self._name_match_score(name, query) * 0.2)
        scores.append(self._length_penalty(content) * 0.1)

        return sum(scores)

    def _keyword_score(self, content: str, query: str) -> float:
        """Score based on keyword overlap."""
        query_words = set(query.lower().split())
        content_words = set(content.lower().split())

        if not query_words:
            return 0.5

        overlap = query_words & content_words
        return len(overlap) / len(query_words)

    def _task_match_score(
        self, content: str, query: str, task_type: str = None
    ) -> float:
        """Score based on task type keywords."""
        if task_type and task_type in self.TASK_KEYWORDS:
            keywords = self.TASK_KEYWORDS[task_type]
            query_lower = query.lower()
            content_lower = content.lower()

            query_matches = sum(1 for kw in keywords if kw in query_lower)
            content_matches = sum(1 for kw in keywords if kw in content_lower)

            return (query_matches + content_matches) / (len(keywords) * 2)

        return self._keyword_score(content, query)

    def _name_match_score(self, name: str, query: str) -> float:
        """Score based on name relevance."""
        query_lower = query.lower()
        name_lower = name.lower()

        if name_lower in query_lower:
            return 1.0

        name_words = set(name_lower.split("_"))
        query_words = set(query_lower.split())

        overlap = name_words & query_words
        return len(overlap) / max(len(name_words), 1)

    def _length_penalty(self, content: str) -> float:
        """Penalize extremely long content."""
        length = len(content)

        if length < 500:
            return 1.0
        elif length < 2000:
            return 0.8
        elif length < 5000:
            return 0.6
        else:
            return 0.4

    def score_all(self, query: str, context_items: List[tuple]) -> Dict[str, float]:
        """Score all context items."""
        results = {}

        for name, content in context_items:
            results[name] = self.score(name, content, query)

        return dict(sorted(results.items(), key=lambda x: x[1], reverse=True))
