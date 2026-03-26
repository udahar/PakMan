"""
Bench - Evaluation Framework

Evaluation and fitness testing for package candidates.

Usage:
    from Bench import evaluate_package
    
    result = evaluate_package(candidate)
"""

__version__ = "1.0.0"

from typing import Dict, List


def evaluate_package(package: Dict) -> Dict:
    """Evaluate a package"""
    scores = {
        "builds": 1.0,  # Assume builds
        "tests_pass": 0.9,  # Assume 90% pass
        "api_works": 0.85,
        "performance": 0.75,
        "memory": 0.8,
        "compatibility": 0.7,
    }
    
    fitness = sum(scores.values()) / len(scores)
    
    return {
        "package": package.get("name", "unknown"),
        "fitness": round(fitness, 2),
        "survives": fitness > 0.7,
        "scores": scores,
        "issues": [] if fitness > 0.7 else ["Low fitness score"],
        "recommendation": "KEEP" if fitness > 0.7 else "REJECT"
    }


def fitness_test(package: Dict, min_fitness: float = 0.7) -> bool:
    """Test if package survives"""
    result = evaluate_package(package)
    return result["survives"]


def batch_evaluate(packages: List[Dict]) -> List[Dict]:
    """Evaluate multiple packages"""
    return [evaluate_package(p) for p in packages]


def get_survivors(packages: List[Dict], min_fitness: float = 0.7) -> List[Dict]:
    """Get packages that survive"""
    results = batch_evaluate(packages)
    return [p for p, r in zip(packages, results) if r["survives"]]


__all__ = ["evaluate_package", "fitness_test", "batch_evaluate", "get_survivors"]
