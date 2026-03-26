"""
Mutation - Mutation engine for package evolution.

Combines fragments into package candidates.
"""

__version__ = "1.0.0"

from typing import List, Dict
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class PackageCandidate:
    """Generated package candidate"""
    name: str
    description: str
    fragments: List[str] = field(default_factory=list)
    category: str = "unknown"
    dependencies: List[str] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    complexity: str = "medium"
    estimated_effort: str = "2 days"
    
    # Scoring
    novelty: float = 0.5
    usefulness: float = 0.5
    gap_fill: float = 0.5
    simplicity: float = 0.5
    overall_score: float = 0.0
    
    mutation_strategy: str = ""
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "fragments": self.fragments,
            "category": self.category,
            "dependencies": self.dependencies,
            "methods": self.methods,
            "complexity": self.complexity,
            "estimated_effort": self.estimated_effort,
            "scores": {
                "novelty": self.novelty,
                "usefulness": self.usefulness,
                "gap_fill": self.gap_fill,
                "simplicity": self.simplicity,
                "overall": self.overall_score
            },
            "mutation_strategy": self.mutation_strategy,
        }


def mutate_fragments(fragments: List[Dict], strategies: List[str] = None, max_candidates: int = 50) -> List[PackageCandidate]:
    """Mutate fragments into candidates"""
    if strategies is None:
        strategies = ["combine", "extend", "specialize"]
    
    candidates = []
    
    for strategy in strategies:
        if strategy == "combine":
            candidates.extend(_mutate_combine(fragments))
        elif strategy == "extend":
            candidates.extend(_mutate_extend(fragments))
        elif strategy == "specialize":
            candidates.extend(_mutate_specialize(fragments))
    
    # Limit and sort
    if len(candidates) > max_candidates:
        candidates.sort(key=lambda c: c.overall_score, reverse=True)
        candidates = candidates[:max_candidates]
    
    return candidates


def _mutate_combine(fragments: List[Dict]) -> List[PackageCandidate]:
    """Combine two fragments"""
    candidates = []
    
    for i, f1 in enumerate(fragments):
        for f2 in fragments[i+1:]:
            if f1.get("category") == f2.get("category"):
                continue
            
            name = f"{f1['name']}_{f2['name']}"
            deps = list(set(f1.get("dependencies", []) + f2.get("dependencies", [])))
            
            candidate = PackageCandidate(
                name=name,
                description=f"Combined {f1['name']} and {f2['name']}",
                fragments=[f1["name"], f2["name"]],
                category=f1.get("category", "unknown"),
                dependencies=deps,
                methods=list(set(f1.get("methods", []) + f2.get("methods", []))),
                complexity="high",
                estimated_effort="3-4 days",
                mutation_strategy="combine",
                novelty=0.85,
                usefulness=0.75,
                gap_fill=0.8,
                simplicity=0.4
            )
            
            candidate.overall_score = _score(candidate)
            candidates.append(candidate)
    
    return candidates


def _mutate_extend(fragments: List[Dict]) -> List[PackageCandidate]:
    """Extend with new capability"""
    candidates = []
    extensions = {
        "cli": {"deps": ["click"], "methods": ["main()", "run()"]},
        "monitoring": {"deps": ["prometheus"], "methods": ["log()", "metric()"]},
        "testing": {"deps": ["pytest"], "methods": ["test_*()"]},
    }
    
    for frag in fragments:
        for ext_name, ext in extensions.items():
            if ext_name in frag.get("name", "").lower():
                continue
            
            name = f"{frag['name']}_{ext_name}"
            candidate = PackageCandidate(
                name=name,
                description=f"{frag['description']} with {ext_name}",
                fragments=[frag["name"], ext_name],
                category=frag.get("category", "unknown"),
                dependencies=list(set(frag.get("dependencies", []) + ext["deps"])),
                methods=list(set(frag.get("methods", []) + ext["methods"])),
                complexity="medium",
                estimated_effort="2-3 days",
                mutation_strategy="extend",
                novelty=0.7,
                usefulness=0.8,
                gap_fill=0.75,
                simplicity=0.6
            )
            
            candidate.overall_score = _score(candidate)
            candidates.append(candidate)
    
    return candidates


def _mutate_specialize(fragments: List[Dict]) -> List[PackageCandidate]:
    """Specialize for niche"""
    candidates = []
    niches = ["conversation", "code", "document", "api"]
    
    for frag in fragments:
        for niche in niches:
            name = f"{niche}_{frag['name']}"
            candidate = PackageCandidate(
                name=name,
                description=f"{frag['description']} for {niche}",
                fragments=[frag["name"]],
                category=frag.get("category", "unknown"),
                complexity="low",
                estimated_effort="1-2 days",
                mutation_strategy="specialize",
                novelty=0.75,
                usefulness=0.7,
                gap_fill=0.8,
                simplicity=0.8
            )
            
            candidate.overall_score = _score(candidate)
            candidates.append(candidate)
    
    return candidates


def _score(candidate: PackageCandidate) -> float:
    """Score candidate"""
    score = (
        candidate.novelty * 0.25 +
        candidate.usefulness * 0.35 +
        candidate.gap_fill * 0.25 +
        candidate.simplicity * 0.15
    )
    
    if candidate.complexity == "high":
        score -= 0.1
    if len(candidate.dependencies) > 5:
        score -= 0.1
    
    return round(score, 2)


def filter_candidates(candidates: List[PackageCandidate], min_score: float = 0.7) -> List[PackageCandidate]:
    """Filter by score"""
    return [c for c in candidates if c.overall_score >= min_score]


def rank_candidates(candidates: List[PackageCandidate]) -> List[PackageCandidate]:
    """Rank by score"""
    return sorted(candidates, key=lambda c: c.overall_score, reverse=True)


def score_candidate(candidate: PackageCandidate) -> float:
    """Score a candidate"""
    return _score(candidate)


__all__ = ["mutate_fragments", "score_candidate", "filter_candidates", "rank_candidates", "PackageCandidate"]
