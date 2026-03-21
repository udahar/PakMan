"""
Sanity Filter - Quality Gate

Filters package candidates before they waste development time.

Usage:
    from SanityFilter import filter_candidates, score_candidate
    
    filtered = filter_candidates(candidates, min_score=0.7)
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
import json


@dataclass
class SanityResult:
    """Result of sanity check"""
    candidate_name: str
    passed: bool
    score: float
    issues: List[str]
    recommendations: List[str]


def score_candidate(candidate: Dict) -> float:
    """
    Score a candidate package.
    
    Scoring criteria:
    - Novelty (25%): Is it new?
    - Usefulness (35%): Is it useful?
    - Gap Fill (25%): Does it fill a gap?
    - Simplicity (15%): Is it simple?
    """
    score = 0.0
    
    # Novelty (0-1)
    novelty = candidate.get("novelty", 0.5)
    score += novelty * 0.25
    
    # Usefulness (0-1)
    usefulness = candidate.get("usefulness", 0.5)
    score += usefulness * 0.35
    
    # Gap Fill (0-1)
    gap_fill = candidate.get("gap_fill", 0.5)
    score += gap_fill * 0.25
    
    # Simplicity (0-1)
    simplicity = candidate.get("simplicity", 0.5)
    score += simplicity * 0.15
    
    return round(score, 2)


def check_conflicts(candidate: Dict, existing_packages: List[str]) -> tuple:
    """Check if candidate conflicts with existing packages"""
    conflicts = []
    
    candidate_name = candidate.get("name", "").lower()
    
    for existing in existing_packages:
        if existing.lower() in candidate_name or candidate_name in existing.lower():
            conflicts.append(f"Similar to existing package: {existing}")
    
    return len(conflicts) == 0, conflicts


def check_complexity(candidate: Dict) -> tuple:
    """Check if candidate is too complex"""
    complexity = candidate.get("complexity", "medium")
    num_deps = len(candidate.get("dependencies", []))
    num_methods = len(candidate.get("methods", []))
    
    issues = []
    
    if complexity == "high":
        issues.append("High complexity - consider simplifying")
    
    if num_deps > 5:
        issues.append(f"Too many dependencies ({num_deps}) - reduce to <5")
    
    if num_methods > 10:
        issues.append(f"Too many methods ({num_methods}) - focus on core functionality")
    
    return len(issues) == 0, issues


def check_usefulness(candidate: Dict) -> tuple:
    """Check if candidate is useful enough"""
    usefulness = candidate.get("usefulness", 0.5)
    gap_fill = candidate.get("gap_fill", 0.5)
    
    issues = []
    
    if usefulness < 0.5:
        issues.append("Low usefulness score - reconsider purpose")
    
    if gap_fill < 0.5:
        issues.append("Doesn't fill a significant gap")
    
    return len(issues) == 0, issues


def filter_candidates(
    candidates: List[Dict],
    existing_packages: List[str] = None,
    min_score: float = 0.7
) -> List[Dict]:
    """
    Filter candidates through sanity checks.
    
    Args:
        candidates: List of PackageCandidates (as dicts)
        existing_packages: List of existing package names
        min_score: Minimum score to pass
    
    Returns:
        Filtered list of candidates
    """
    if existing_packages is None:
        existing_packages = []
    
    filtered = []
    
    for candidate in candidates:
        # Run all checks
        conflicts_ok, conflict_issues = check_conflicts(candidate, existing_packages)
        complexity_ok, complexity_issues = check_complexity(candidate)
        usefulness_ok, usefulness_issues = check_usefulness(candidate)
        
        # Calculate score
        score = score_candidate(candidate)
        
        # Collect all issues
        all_issues = []
        if not conflicts_ok:
            all_issues.extend(conflict_issues)
        if not complexity_ok:
            all_issues.extend(complexity_issues)
        if not usefulness_ok:
            all_issues.extend(usefulness_issues)
        
        # Apply penalties
        if all_issues:
            score -= len(all_issues) * 0.1
        
        # Store score in candidate
        candidate["overall_score"] = score
        candidate["issues"] = all_issues
        
        # Filter by score
        if score >= min_score:
            filtered.append(candidate)
    
    # Sort by score
    filtered.sort(key=lambda c: c.get("overall_score", 0), reverse=True)
    
    return filtered


def generate_report(candidates: List[Dict], filtered: List[Dict]) -> str:
    """Generate filter report"""
    lines = []
    lines.append("# Sanity Filter Report")
    lines.append("")
    lines.append(f"**Total Candidates:** {len(candidates)}")
    lines.append(f"**Passed Filter:** {len(filtered)}")
    lines.append(f"**Filtered Out:** {len(candidates) - len(filtered)}")
    lines.append("")
    
    # Top candidates
    lines.append("## Top Candidates")
    lines.append("")
    
    for i, candidate in enumerate(filtered[:10], 1):
        lines.append(f"{i}. **{candidate['name']}** (Score: {candidate.get('overall_score', 0):.2f})")
        lines.append(f"   - {candidate.get('description', 'No description')}")
        lines.append(f"   - Complexity: {candidate.get('complexity', 'unknown')}")
        lines.append(f"   - Effort: {candidate.get('estimated_effort', 'unknown')}")
        if candidate.get("issues"):
            lines.append(f"   - Issues: {', '.join(candidate['issues'])}")
        lines.append("")
    
    # Filtered out
    if len(candidates) > len(filtered):
        lines.append("## Filtered Out")
        lines.append("")
        
        filtered_out = [c for c in candidates if c not in filtered]
        for candidate in filtered_out[:10]:
            lines.append(f"- **{candidate['name']}** (Score: {candidate.get('overall_score', 0):.2f})")
            if candidate.get("issues"):
                lines.append(f"  - Issues: {', '.join(candidate['issues'])}")
        lines.append("")
    
    return "\n".join(lines)


def export_results(filtered: List[Dict], output_file: str):
    """Export filtered results to JSON"""
    data = {
        "total": len(filtered),
        "candidates": filtered
    }
    
    with open(output_file, "w") as f:
        json.dump(data, f, indent=2)


# === Main API ===

def sanity_filter(candidates, existing=None, min_score=0.7):
    """Filter candidates"""
    return filter_candidates(candidates, existing, min_score)


def get_top_candidates(candidates: List[Dict], top_n: int = 10) -> List[Dict]:
    """Get top N candidates"""
    filtered = filter_candidates(candidates)
    return filtered[:top_n]


__all__ = [
    "score_candidate",
    "filter_candidates",
    "generate_report",
    "export_results",
    "sanity_filter",
    "get_top_candidates",
]
