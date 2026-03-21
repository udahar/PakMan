"""
Frank - Pattern Mining Module (inside GapMan)

Extracts design patterns from repos without copying code.
"""

from typing import List, Dict
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class DesignFragment:
    """Extracted design pattern"""
    name: str
    category: str
    description: str
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    complexity: str = "medium"
    usefulness: float = 0.5
    source_repo: str = ""
    extracted_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "dependencies": self.dependencies,
            "methods": self.methods,
            "complexity": self.complexity,
            "usefulness": self.usefulness,
            "source_repo": self.source_repo,
        }


def mine_patterns(repos: List[str], focus_areas: List[str] = None) -> List[DesignFragment]:
    """Mine design patterns from repos"""
    patterns = []
    
    for repo in repos:
        repo_name = repo.split("/")[-1].replace(".git", "")
        
        # Extract based on repo type
        if "langchain" in repo.lower():
            patterns.extend(_extract_langchain_patterns(repo))
        elif "autogen" in repo.lower():
            patterns.extend(_extract_autogen_patterns(repo))
        else:
            patterns.extend(_extract_generic_patterns(repo, focus_areas))
    
    return patterns


def _extract_langchain_patterns(repo: str) -> List[DesignFragment]:
    """Extract from LangChain"""
    return [
        DesignFragment(
            name="chain_executor",
            category="orchestration",
            description="Execute chain of operations",
            inputs=["chain_steps", "input"],
            outputs=["result"],
            dependencies=["langchain"],
            methods=["add_step()", "run()", "get_result()"],
            usefulness=0.9,
            source_repo=repo
        ),
        DesignFragment(
            name="tool_wrapper",
            category="agent",
            description="Wrap functions as tools",
            inputs=["function", "name"],
            outputs=["tool"],
            dependencies=["langchain"],
            methods=["call()", "get_schema()"],
            usefulness=0.85,
            source_repo=repo
        ),
    ]


def _extract_autogen_patterns(repo: str) -> List[DesignFragment]:
    """Extract from AutoGen"""
    return [
        DesignFragment(
            name="agent_conversation",
            category="agent",
            description="Multi-agent conversation",
            inputs=["agents", "topic"],
            outputs=["conversation", "result"],
            dependencies=["llm"],
            methods=["add_agent()", "start_conversation()"],
            complexity="high",
            usefulness=0.92,
            source_repo=repo
        ),
    ]


def _extract_generic_patterns(repo: str, focus: List[str] = None) -> List[DesignFragment]:
    """Extract generic patterns"""
    return []


def categorize_fragments(fragments: List[DesignFragment]) -> Dict[str, List[DesignFragment]]:
    """Categorize by type"""
    categorized = {}
    for f in fragments:
        if f.category not in categorized:
            categorized[f.category] = []
        categorized[f.category].append(f)
    return categorized


def filter_fragments(fragments: List[DesignFragment], min_usefulness: float = 0.7) -> List[DesignFragment]:
    """Filter by usefulness"""
    return [f for f in fragments if f.usefulness >= min_usefulness]


__all__ = ["mine_patterns", "DesignFragment", "categorize_fragments", "filter_fragments"]
