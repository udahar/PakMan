"""
Task-Based Context Selection
"""

from typing import Dict, List, Optional


class TaskSelector:
    """Select context based on task type."""

    TASK_CONFIGS = {
        "code_generation": {
            "layers": ["working", "skills", "reference"],
            "keywords": [
                "code",
                "function",
                "class",
                "implement",
                "create",
                "build",
                "rust",
                "python",
                "javascript",
            ],
            "preferred_layers": ["skills"],
        },
        "code_review": {
            "layers": ["working", "skills"],
            "keywords": ["review", "refactor", "lint", "code"],
            "preferred_layers": ["skills"],
        },
        "research": {
            "layers": ["working", "long_term", "reference"],
            "keywords": [
                "research",
                "find",
                "search",
                "explain",
                "what is",
                "how does",
            ],
            "preferred_layers": ["long_term"],
        },
        "analysis": {
            "layers": ["working", "long_term", "short_term"],
            "keywords": ["analyze", "compare", "evaluate", "metrics", "data"],
            "preferred_layers": ["long_term"],
        },
        "creative_writing": {
            "layers": ["working", "long_term"],
            "keywords": ["write", "story", "blog", "content", "creative"],
            "preferred_layers": ["long_term"],
        },
        "problem_solving": {
            "layers": ["working", "skills", "reference"],
            "keywords": ["fix", "bug", "error", "debug", "issue"],
            "preferred_layers": ["skills", "reference"],
        },
        "planning": {
            "layers": ["working", "long_term", "reference"],
            "keywords": ["plan", "roadmap", "strategy", "design", "architecture"],
            "preferred_layers": ["long_term", "reference"],
        },
    }

    def __init__(self):
        self.task_history: Dict[str, int] = {}

    def select_for_task(self, task_type: str, query: str = "") -> List[str]:
        """Select layers for task type."""
        config = self.TASK_CONFIGS.get(task_type)

        if not config:
            return ["working", "short_term"]

        selected = config["layers"].copy()

        if query:
            query_lower = query.lower()
            for kw in config["keywords"]:
                if kw in query_lower:
                    selected.extend(config["preferred_layers"])
                    break

        return list(set(selected))

    def get_task_type(self, query: str) -> str:
        """Infer task type from query."""
        query_lower = query.lower()

        best_match = "general"
        best_score = 0

        for task_type, config in self.TASK_CONFIGS.items():
            score = sum(1 for kw in config["keywords"] if kw in query_lower)
            if score > best_score:
                best_score = score
                best_match = task_type

        return best_match

    def record_task(self, task_type: str):
        """Record task execution."""
        self.task_history[task_type] = self.task_history.get(task_type, 0) + 1

    def get_frequent_tasks(self, limit: int = 3) -> List[str]:
        """Get most frequent task types."""
        sorted_tasks = sorted(
            self.task_history.items(), key=lambda x: x[1], reverse=True
        )
        return [t[0] for t in sorted_tasks[:limit]]
