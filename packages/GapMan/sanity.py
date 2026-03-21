"""
Sanity Filter Module (inside GapMan)

Quality gate for candidates.
"""

from typing import List, Dict


def sanity_filter(candidates: List[Dict], existing: List[str] = None, min_score: float = 0.7) -> List[Dict]:
    """Filter candidates"""
    if existing is None:
        existing = []
    
    filtered = []
    
    for c in candidates:
        issues = []
        
        # Check conflicts
        for existing_pkg in existing:
            if existing_pkg.lower() in c.get("name", "").lower():
                issues.append(f"Conflicts with {existing_pkg}")
        
        # Check complexity
        if c.get("complexity") == "high":
            issues.append("High complexity")
        if len(c.get("dependencies", [])) > 5:
            issues.append("Too many dependencies")
        
        # Score
        score = c.get("overall_score", 0.5)
        score -= len(issues) * 0.1
        
        c["overall_score"] = score
        c["issues"] = issues
        
        if score >= min_score:
            filtered.append(c)
    
    filtered.sort(key=lambda c: c.get("overall_score", 0), reverse=True)
    return filtered


def get_top_candidates(candidates: List[Dict], top_n: int = 10) -> List[Dict]:
    """Get top N candidates"""
    filtered = sanity_filter(candidates)
    return filtered[:top_n]


__all__ = ["sanity_filter", "get_top_candidates"]
