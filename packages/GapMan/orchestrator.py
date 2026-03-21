"""
Evolution Engine Orchestrator (inside GapMan)

Ties all 6 components together.
"""

from typing import List, Dict
from datetime import datetime

from .frank import mine_patterns, categorize_fragments
from .mutation import mutate_fragments, rank_candidates
from .sanity import sanity_filter, get_top_candidates
from .spec import generate_build_spec, create_projman_ticket
from .autocoder import generate_code
from .bench import evaluate_package, get_survivors


class EvolutionEngine:
    """
    Complete software evolution engine.
    
    Usage:
        engine = EvolutionEngine()
        results = engine.evolve(repos, max_candidates=10)
    """
    
    def __init__(self):
        self.stats = {
            "patterns_mined": 0,
            "candidates_generated": 0,
            "candidates_filtered": 0,
            "specs_generated": 0,
            "packages_coded": 0,
            "packages_survived": 0,
        }
    
    def evolve(self, repos: List[str], max_candidates: int = 10) -> Dict:
        """
        Run complete evolution cycle.
        
        Args:
            repos: List of repos to mine
            max_candidates: Max candidates to generate
        
        Returns:
            Evolution results
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "repos_analyzed": repos,
            "steps": [],
            "final_packages": [],
        }
        
        # Step 1: Mine patterns
        print("🔍 Step 1: Mining patterns...")
        patterns = mine_patterns(repos)
        self.stats["patterns_mined"] = len(patterns)
        results["steps"].append({
            "step": 1,
            "name": "Pattern Mining",
            "result": f"{len(patterns)} patterns mined"
        })
        
        # Step 2: Mutate
        print("🧬 Step 2: Mutating fragments...")
        fragments = [p.to_dict() for p in patterns]
        candidates = mutate_fragments(fragments, max_candidates=max_candidates * 5)
        self.stats["candidates_generated"] = len(candidates)
        results["steps"].append({
            "step": 2,
            "name": "Mutation",
            "result": f"{len(candidates)} candidates generated"
        })
        
        # Step 3: Sanity filter
        print("🔍 Step 3: Sanity filtering...")
        filtered = sanity_filter([c.to_dict() for c in candidates], max_candidates)
        self.stats["candidates_filtered"] = len(filtered)
        results["steps"].append({
            "step": 3,
            "name": "Sanity Filter",
            "result": f"{len(filtered)} candidates passed"
        })
        
        # Step 4: Generate specs
        print("📝 Step 4: Generating specs...")
        specs = []
        for candidate in filtered[:max_candidates]:
            spec = generate_build_spec(candidate)
            specs.append(spec)
        self.stats["specs_generated"] = len(specs)
        results["steps"].append({
            "step": 4,
            "name": "Spec Generation",
            "result": f"{len(specs)} specs generated"
        })
        
        # Step 5: Generate code
        print("💻 Step 5: Generating code...")
        packages = []
        for spec in specs:
            code = generate_code(spec.to_dict())
            packages.append({
                "spec": spec.to_dict(),
                "code": code,
                "ticket": create_projman_ticket(spec)
            })
        self.stats["packages_coded"] = len(packages)
        results["steps"].append({
            "step": 5,
            "name": "Code Generation",
            "result": f"{len(packages)} packages generated"
        })
        
        # Step 6: Evaluate
        print("🏆 Step 6: Evaluating packages...")
        survivors = []
        for pkg in packages:
            eval_result = evaluate_package(pkg)
            if eval_result["survives"]:
                pkg["evaluation"] = eval_result
                survivors.append(pkg)
        self.stats["packages_survived"] = len(survivors)
        results["steps"].append({
            "step": 6,
            "name": "Evaluation",
            "result": f"{len(survivors)} packages survived"
        })
        
        # Final results
        results["final_packages"] = [p["ticket"] for p in survivors]
        results["stats"] = self.stats
        
        return results


def evolve_toolkit(repos: List[str], max_candidates: int = 10) -> Dict:
    """
    Quick evolution function.
    
    Args:
        repos: List of repos to mine
        max_candidates: Max final candidates
    
    Returns:
        Evolution results
    """
    engine = EvolutionEngine()
    return engine.evolve(repos, max_candidates)


__all__ = ["EvolutionEngine", "evolve_toolkit"]
