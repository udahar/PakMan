# Updated-On: 2026-03-08
# Updated-By: Codex
# PM-Ticket: UNTRACKED

"""
Skill Loader
Load and manage skill definitions - nanoclaw-style
Inspired by nanoclaw's skill system - custom Python implementation
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
import json

try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


@dataclass
class SkillDefinition:
    """Definition of a skill."""

    skill_id: str
    name: str
    description: str
    prompt_template: str
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    examples: List[str] = field(default_factory=list)
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "description": self.description,
            "prompt_template": self.prompt_template,
            "category": self.category,
            "tags": self.tags,
            "parameters": self.parameters,
            "examples": self.examples,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SkillDefinition":
        return cls(
            skill_id=data["skill_id"],
            name=data["name"],
            description=data.get("description", ""),
            prompt_template=data["prompt_template"],
            category=data.get("category", "general"),
            tags=data.get("tags", []),
            parameters=data.get("parameters", {}),
            examples=data.get("examples", []),
            enabled=data.get("enabled", True),
        )


class SkillLoader:
    """
    Loads and manages skill definitions.

    Similar to nanoclaw's skill loading.
    """

    def __init__(self):
        self.skills: Dict[str, SkillDefinition] = {}
        self.categories: Dict[str, List[str]] = {}

    def load_from_json(self, file_path: str) -> int:
        """Load skills from JSON file."""
        path = Path(file_path)
        if not path.exists():
            return 0

        with open(path, "r") as f:
            data = json.load(f)

        count = 0
        for skill_data in data.get("skills", []):
            skill = SkillDefinition.from_dict(skill_data)
            self._add_skill(skill)
            count += 1

        return count

    def load_from_yaml(self, file_path: str) -> int:
        """Load skills from YAML file."""
        if not YAML_AVAILABLE:
            return 0

        path = Path(file_path)
        if not path.exists():
            return 0

        with open(path, "r") as f:
            data = yaml.safe_load(f)

        count = 0
        for skill_data in data.get("skills", []):
            skill = SkillDefinition.from_dict(skill_data)
            self._add_skill(skill)
            count += 1

        return count

    def load_from_directory(self, dir_path: str) -> int:
        """Load all skills from a directory."""
        path = Path(dir_path)
        if not path.exists():
            return 0

        count = 0
        for file_path in path.glob("*.json"):
            count += self.load_from_json(str(file_path))
        for file_path in path.glob("*.yaml"):
            count += self.load_from_yaml(str(file_path))
        for file_path in path.glob("*.yml"):
            count += self.load_from_yaml(str(file_path))

        return count

    def _add_skill(self, skill: SkillDefinition):
        """Add a skill to the loader."""
        self.skills[skill.skill_id] = skill

        if skill.category not in self.categories:
            self.categories[skill.category] = []
        self.categories[skill.category].append(skill.skill_id)

    def register_skill(
        self,
        skill_id: str,
        name: str,
        prompt_template: str,
        description: str = "",
        category: str = "general",
        tags: Optional[List[str]] = None,
    ):
        """Register a skill programmatically."""
        skill = SkillDefinition(
            skill_id=skill_id,
            name=name,
            description=description,
            prompt_template=prompt_template,
            category=category,
            tags=tags or [],
        )
        self._add_skill(skill)

    def get_skill(self, skill_id: str) -> Optional[SkillDefinition]:
        """Get a skill by ID."""
        return self.skills.get(skill_id)

    def get_skills_by_category(self, category: str) -> List[SkillDefinition]:
        """Get all skills in a category."""
        skill_ids = self.categories.get(category, [])
        return [self.skills[sid] for sid in skill_ids if sid in self.skills]

    def get_skills_by_tag(self, tag: str) -> List[SkillDefinition]:
        """Get all skills with a tag."""
        return [s for s in self.skills.values() if tag in s.tags]

    def search_skills(self, query: str) -> List[SkillDefinition]:
        """Search skills by name or description."""
        query = query.lower()
        return [
            s
            for s in self.skills.values()
            if query in s.name.lower() or query in s.description.lower()
        ]

    def get_all_skills(self) -> List[SkillDefinition]:
        """Get all skills."""
        return list(self.skills.values())

    def get_enabled_skills(self) -> List[SkillDefinition]:
        """Get all enabled skills."""
        return [s for s in self.skills.values() if s.enabled]

    def list_categories(self) -> List[str]:
        """List all categories."""
        return list(self.categories.keys())

    def enable_skill(self, skill_id: str) -> bool:
        """Enable a skill."""
        if skill_id in self.skills:
            self.skills[skill_id].enabled = True
            return True
        return False

    def disable_skill(self, skill_id: str) -> bool:
        """Disable a skill."""
        if skill_id in self.skills:
            self.skills[skill_id].enabled = False
            return True
        return False

    def get_prompt_template(self, skill_id: str) -> Optional[str]:
        """Get prompt template for a skill."""
        skill = self.skills.get(skill_id)
        return skill.prompt_template if skill else None

    def export_to_json(self, file_path: str):
        """Export skills to JSON."""
        data = {"skills": [s.to_dict() for s in self.skills.values()]}
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)

    def export_to_yaml(self, file_path: str):
        """Export skills to YAML."""
        if not YAML_AVAILABLE:
            return

        data = {"skills": [s.to_dict() for s in self.skills.values()]}
        with open(file_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False)

    def get_stats(self) -> Dict[str, Any]:
        """Get loader statistics."""
        enabled = sum(1 for s in self.skills.values() if s.enabled)
        return {
            "total_skills": len(self.skills),
            "enabled_skills": enabled,
            "disabled_skills": len(self.skills) - enabled,
            "categories": {cat: len(sids) for cat, sids in self.categories.items()},
        }


def create_skill_loader() -> SkillLoader:
    """Factory function to create skill loader."""
    return SkillLoader()
