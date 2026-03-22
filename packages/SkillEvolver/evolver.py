"""
Skill Evolution Engine
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class SkillVersion:
    """Version of a skill."""
    version: str
    prompt: str
    success_rate: float
    avg_score: float
    created_at: datetime = field(default_factory=datetime.now)
    usage_count: int = 0


class Evolver:
    """Evolve skills based on usage feedback."""
    
    def __init__(self, data_dir: str = "skill_data"):
        self.data_dir = data_dir
        self.skills: Dict[str, List[SkillVersion]] = {}
        self.current_versions: Dict[str, str] = {}
    
    def record(self, skill: str, success: bool, user_feedback: float = 0.5, prompt: str = None):
        """Record skill usage."""
        if skill not in self.skills:
            self.skills[skill] = []
        
        if not self.skills[skill]:
            self.current_versions[skill] = "1.0.0"
        
        current = self.get_current(skill)
        
        if current:
            current.usage_count += 1
            
            success_rate = (current.success_rate * (current.usage_count - 1) + (1.0 if success else 0.0)) / current.usage_count
            avg_score = (current.avg_score * (current.usage_count - 1) + user_feedback) / current.usage_count
            
            current.success_rate = success_rate
            current.avg_score = avg_score
    
    def evolve(self, skill: str, threshold: float = 0.7) -> Optional[str]:
        """Evolve skill if performance is poor."""
        current = self.get_current(skill)
        
        if not current:
            return None
        
        if current.avg_score < threshold and current.usage_count >= 5:
            return self._create_new_version(skill)
        
        return None
    
    def _create_new_version(self, skill: str) -> str:
        """Create new version of skill."""
        from .mutations import PromptMutator
        
        current = self.get_current(skill)
        if not current:
            return ""
        
        mutator = PromptMutator()
        new_prompt = mutator.mutate(current.prompt, current.avg_score)
        
        version_parts = current.version.split(".")
        version_parts[-1] = str(int(version_parts[-1]) + 1)
        new_version = ".".join(version_parts)
        
        new_skill_version = SkillVersion(
            version=new_version,
            prompt=new_prompt,
            success_rate=current.success_rate,
            avg_score=current.avg_score,
            usage_count=0
        )
        
        self.skills[skill].append(new_skill_version)
        self.current_versions[skill] = new_version
        
        return new_version
    
    def get_current(self, skill: str) -> Optional[SkillVersion]:
        """Get current version of skill."""
        if skill not in self.skills or not self.skills[skill]:
            return None
        
        version = self.current_versions.get(skill)
        for v in self.skills[skill]:
            if v.version == version:
                return v
        
        return self.skills[skill][-1]
    
    def get_stats(self, skill: str) -> Dict:
        """Get skill statistics."""
        current = self.get_current(skill)
        if not current:
            return {}
        
        return {
            "skill": skill,
            "version": current.version,
            "success_rate": current.success_rate,
            "avg_score": current.avg_score,
            "usage_count": current.usage_count,
            "versions_count": len(self.skills.get(skill, [])),
        }
    
    def list_skills(self) -> List[str]:
        """List all tracked skills."""
        return list(self.skills.keys())
