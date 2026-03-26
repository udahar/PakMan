"""
PatternMiner - Pattern Mining Engine

Extracts design patterns from repos without copying code.
Clean-room inspiration extraction.

Usage:
    from PatternMiner import mine_patterns
    
    patterns = mine_patterns([
        "github.com/langchain-ai/langchain",
        "github.com/microsoft/autogen",
    ])
"""

__version__ = "1.0.0"

from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
import re


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
    complexity: str = "medium"  # low, medium, high
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
            "extracted_at": self.extracted_at
        }


# Pattern templates to look for
PATTERN_TEMPLATES = {
    "caching": {
        "keywords": ["cache", "memoize", "store", "retrieve"],
        "structure": ["store(key, value)", "retrieve(key)", "clear()"],
        "dependencies": ["redis", "memcached", "qdrant"],
    },
    "vector_store": {
        "keywords": ["vector", "embedding", "similarity", "search"],
        "structure": ["embed(text)", "search(query, top_k)", "store(vectors)"],
        "dependencies": ["qdrant", "pinecone", "faiss"],
    },
    "agent": {
        "keywords": ["agent", "tool", "action", "observe"],
        "structure": ["act()", "observe()", "think()"],
        "dependencies": ["langchain", "llm"],
    },
    "orchestrator": {
        "keywords": ["orchestrate", "coordinate", "workflow", "pipeline"],
        "structure": ["add_step()", "run()", "get_result()"],
        "dependencies": ["asyncio", "celery"],
    },
    "cli": {
        "keywords": ["cli", "command", "terminal", "argparse"],
        "structure": ["add_command()", "run()", "parse_args()"],
        "dependencies": ["click", "typer", "argparse"],
    },
    "api": {
        "keywords": ["api", "endpoint", "route", "request"],
        "structure": ["get()", "post()", "route()"],
        "dependencies": ["fastapi", "flask", "requests"],
    },
    "monitoring": {
        "keywords": ["monitor", "track", "metric", "alert"],
        "structure": ["log()", "metric()", "alert()"],
        "dependencies": ["prometheus", "grafana"],
    },
    "testing": {
        "keywords": ["test", "assert", "mock", "fixture"],
        "structure": ["test_*()", "assert", "setup()", "teardown()"],
        "dependencies": ["pytest", "unittest"],
    },
}


def mine_patterns(repos: List[str], focus_areas: List[str] = None) -> List[DesignFragment]:
    """
    Mine design patterns from repos.
    
    Args:
        repos: List of repo URLs to study
        focus_areas: Specific areas to focus on (caching, agents, etc.)
    
    Returns:
        List of DesignFragments
    """
    patterns = []
    
    for repo in repos:
        # Extract patterns from repo
        # For now, template-based extraction
        # TODO: Actually clone and analyze repos
        
        repo_name = repo.split("/")[-1].replace(".git", "")
        
        # Extract patterns based on repo type
        if "langchain" in repo.lower():
            patterns.extend(_extract_langchain_patterns(repo))
        elif "autogen" in repo.lower():
            patterns.extend(_extract_autogen_patterns(repo))
        elif "llama" in repo.lower():
            patterns.extend(_extract_llama_patterns(repo))
        else:
            patterns.extend(_extract_generic_patterns(repo, focus_areas))
    
    return patterns


def _extract_langchain_patterns(repo: str) -> List[DesignFragment]:
    """Extract patterns from LangChain-style repos"""
    patterns = []
    
    # Chain pattern
    patterns.append(DesignFragment(
        name="chain_executor",
        category="orchestration",
        description="Execute a chain of operations in sequence",
        inputs=["chain_steps", "input_data"],
        outputs=["final_result", "intermediate_steps"],
        dependencies=["langchain"],
        methods=["add_step()", "run()", "get_result()"],
        complexity="medium",
        usefulness=0.9,
        source_repo=repo
    ))
    
    # Tool pattern
    patterns.append(DesignFragment(
        name="tool_wrapper",
        category="agent",
        description="Wrap functions as callable tools",
        inputs=["function", "name", "description"],
        outputs=["tool"],
        dependencies=["langchain"],
        methods=["call()", "get_schema()"],
        complexity="low",
        usefulness=0.85,
        source_repo=repo
    ))
    
    # Memory pattern
    patterns.append(DesignFragment(
        name="conversation_memory",
        category="memory",
        description="Store and retrieve conversation history",
        inputs=["messages"],
        outputs=["history", "context"],
        dependencies=["redis", "sqlite"],
        methods=["add_message()", "get_history()", "clear()"],
        complexity="medium",
        usefulness=0.88,
        source_repo=repo
    ))
    
    return patterns


def _extract_autogen_patterns(repo: str) -> List[DesignFragment]:
    """Extract patterns from AutoGen-style repos"""
    patterns = []
    
    # Agent conversation pattern
    patterns.append(DesignFragment(
        name="agent_conversation",
        category="agent",
        description="Multi-agent conversation orchestration",
        inputs=["agents", "topic", "max_turns"],
        outputs=["conversation_log", "result"],
        dependencies=["llm", "asyncio"],
        methods=["add_agent()", "start_conversation()", "get_result()"],
        complexity="high",
        usefulness=0.92,
        source_repo=repo
    ))
    
    # Code executor pattern
    patterns.append(DesignFragment(
        name="code_executor",
        category="execution",
        description="Safely execute generated code",
        inputs=["code", "timeout", "environment"],
        outputs=["result", "logs", "error"],
        dependencies=["docker", "subprocess"],
        methods=["execute()", "stop()", "get_logs()"],
        complexity="high",
        usefulness=0.9,
        source_repo=repo
    ))
    
    return patterns


def _extract_llama_patterns(repo: str) -> List[DesignFragment]:
    """Extract patterns from LlamaIndex-style repos"""
    patterns = []
    
    # Index pattern
    patterns.append(DesignFragment(
        name="vector_index",
        category="storage",
        description="Vector index for semantic search",
        inputs=["documents", "embeddings"],
        outputs=["index"],
        dependencies=["qdrant", "pinecone"],
        methods=["add_documents()", "search()", "delete()"],
        complexity="medium",
        usefulness=0.87,
        source_repo=repo
    ))
    
    # Query engine pattern
    patterns.append(DesignFragment(
        name="query_engine",
        category="retrieval",
        description="Query documents with natural language",
        inputs=["query", "filters"],
        outputs=["response", "sources"],
        dependencies=["llm", "embeddings"],
        methods=["query()", "stream_query()"],
        complexity="medium",
        usefulness=0.89,
        source_repo=repo
    ))
    
    return patterns


def _extract_generic_patterns(repo: str, focus_areas: List[str] = None) -> List[DesignFragment]:
    """Extract generic patterns from any repo"""
    patterns = []
    
    # If focus areas specified, extract those
    if focus_areas:
        for area in focus_areas:
            if area in PATTERN_TEMPLATES:
                template = PATTERN_TEMPLATES[area]
                patterns.append(DesignFragment(
                    name=f"{area}_pattern",
                    category=area,
                    description=f"Extracted {area} pattern from {repo}",
                    inputs=template["structure"][:2],
                    outputs=["result"],
                    dependencies=template["dependencies"],
                    methods=template["structure"],
                    complexity="medium",
                    usefulness=0.7,
                    source_repo=repo
                ))
    
    return patterns


def categorize_fragments(fragments: List[DesignFragment]) -> Dict[str, List[DesignFragment]]:
    """Categorize fragments by type"""
    categorized = {}
    
    for fragment in fragments:
        category = fragment.category
        if category not in categorized:
            categorized[category] = []
        categorized[category].append(fragment)
    
    return categorized


def filter_fragments(
    fragments: List[DesignFragment],
    min_usefulness: float = 0.7,
    categories: List[str] = None
) -> List[DesignFragment]:
    """Filter fragments by criteria"""
    filtered = []
    
    for fragment in fragments:
        if fragment.usefulness < min_usefulness:
            continue
        
        if categories and fragment.category not in categories:
            continue
        
        filtered.append(fragment)
    
    return filtered


def export_fragments(fragments: List[DesignFragment], output_file: str):
    """Export fragments to JSON"""
    data = {
        "total": len(fragments),
        "extracted_at": datetime.now().isoformat(),
        "fragments": [f.to_dict() for f in fragments]
    }
    
    with open(output_file, "w") as f:
        json.dump(data, f, indent=2)


# === Main API ===

def mine_patterns(repos: List[str], focus: List[str] = None) -> List[DesignFragment]:
    """Mine patterns from repos"""
    return mine_patterns(repos, focus)


def get_fragments_by_category(fragments: List[DesignFragment], category: str) -> List[DesignFragment]:
    """Get fragments by category"""
    return [f for f in fragments if f.category == category]


__all__ = [
    "mine_patterns",
    "categorize_fragments",
    "filter_fragments",
    "export_fragments",
    "DesignFragment",
    "get_fragments_by_category",
]
