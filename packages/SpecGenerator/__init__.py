"""
SpecGenerator - Build Spec Generator

Creates build specs from candidates.

Usage:
    from SpecGenerator import generate_build_spec
    
    spec = generate_build_spec(candidate)
"""

__version__ = "1.0.0"

from typing import Dict, List
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class BuildSpec:
    """Build specification"""
    name: str
    purpose: str
    description: str
    category: str
    interfaces: Dict[str, str] = field(default_factory=dict)
    files: List[str] = field(default_factory=list)
    tests: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    difficulty: str = "medium"
    estimated_time: str = "2 days"
    success_criteria: List[str] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "purpose": self.purpose,
            "description": self.description,
            "category": self.category,
            "interfaces": self.interfaces,
            "files": self.files,
            "tests": self.tests,
            "dependencies": self.dependencies,
            "difficulty": self.difficulty,
            "estimated_time": self.estimated_time,
            "success_criteria": self.success_criteria,
        }
    
    def to_ticket(self) -> dict:
        """Convert to ProjMan ticket"""
        return {
            "title": f"Build: {self.name}",
            "description": self.description,
            "spec": self.to_dict(),
            "priority": "HIGH" if self.difficulty == "low" else "MEDIUM",
            "estimated_hours": int(self.estimated_time.split()[0]) * 8,
        }


def generate_build_spec(candidate: Dict, debate_rounds: int = 3) -> BuildSpec:
    """Generate spec from candidate"""
    # Create initial spec
    spec = BuildSpec(
        name=candidate["name"],
        purpose=candidate.get("description", ""),
        description=candidate.get("description", ""),
        category=candidate.get("category", "unknown"),
        files=[
            f"{candidate['name']}/__init__.py",
            f"{candidate['name']}/core.py",
            f"{candidate['name']}/api.py",
        ],
        tests=[
            f"tests/test_{candidate['name']}_core.py",
            f"tests/test_{candidate['name']}_api.py",
        ],
        dependencies=candidate.get("dependencies", []),
        difficulty=candidate.get("complexity", "medium"),
        estimated_time=candidate.get("estimated_effort", "2 days"),
        success_criteria=["Tests pass", "API works", "Docs complete"]
    )
    
    # Simple debate loop
    for _ in range(debate_rounds):
        if not spec.interfaces:
            spec.interfaces = {"run": "run(input) -> Any", "get_result": "get_result() -> Any"}
        if len(spec.files) < 4:
            spec.files.append(f"{spec.name}/utils.py")
    
    return spec


def create_projman_ticket(spec: BuildSpec) -> dict:
    """Create ProjMan ticket"""
    return spec.to_ticket()


__all__ = ["generate_build_spec", "create_projman_ticket", "BuildSpec"]
