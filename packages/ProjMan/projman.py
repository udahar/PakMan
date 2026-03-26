"""
ProjMan - CLI tools for Alfred ProjectManager integration.

Usage:
    from projman import ProjectManager, create_project, list_projects
    
    pm = ProjectManager()
    project_id = pm.create_project("New Feature", "Description")
    
    projects = pm.list_projects()
"""

import os
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional, Dict
from enum import Enum


class ProjectStatus(Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


@dataclass
class Project:
    id: str
    name: str
    description: str
    status: str
    created_at: str
    updated_at: str
    metadata: Dict


@dataclass
class Epic:
    id: str
    project_id: str
    name: str
    description: str
    status: str
    created_at: str


@dataclass
class Story:
    id: str
    epic_id: str
    name: str
    description: str
    status: str
    created_at: str


class ProjectManager:
    def __init__(self, storage_path: str = "~/.pakman/projects.json"):
        self.storage_path = Path(storage_path).expanduser()
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.projects: Dict[str, Project] = {}
        self.epics: Dict[str, Epic] = {}
        self.stories: Dict[str, Story] = {}
        self._load()
    
    def _load(self):
        if self.storage_path.exists():
            try:
                data = json.loads(self.storage_path.read_text())
                for p in data.get("projects", {}).values():
                    self.projects[p["id"]] = Project(**p)
                for e in data.get("epics", {}).values():
                    self.epics[e["id"]] = Epic(**e)
                for s in data.get("stories", {}).values():
                    self.stories[s["id"]] = Story(**s)
            except Exception:
                pass
    
    def _save(self):
        data = {
            "projects": {p.id: asdict(p) for p in self.projects.values()},
            "epics": {e.id: asdict(e) for e in self.epics.values()},
            "stories": {s.id: asdict(s) for s in self.stories.values()},
        }
        self.storage_path.write_text(json.dumps(data, indent=2))
    
    def create_project(self, name: str, description: str = "") -> str:
        import uuid
        project_id = f"PROJ-{uuid.uuid4().hex[:6].upper()}"
        now = datetime.now().isoformat()
        
        project = Project(
            id=project_id,
            name=name,
            description=description,
            status="active",
            created_at=now,
            updated_at=now,
            metadata={}
        )
        self.projects[project_id] = project
        self._save()
        return project_id
    
    def create_epic(self, project_id: str, name: str, description: str = "") -> str:
        import uuid
        epic_id = f"EPIC-{uuid.uuid4().hex[:6].upper()}"
        
        epic = Epic(
            id=epic_id,
            project_id=project_id,
            name=name,
            description=description,
            status="open",
            created_at=datetime.now().isoformat()
        )
        self.epics[epic_id] = epic
        self._save()
        return epic_id
    
    def create_story(self, epic_id: str, name: str, description: str = "") -> str:
        import uuid
        story_id = f"STORY-{uuid.uuid4().hex[:6].upper()}"
        
        story = Story(
            id=story_id,
            epic_id=epic_id,
            name=name,
            description=description,
            status="open",
            created_at=datetime.now().isoformat()
        )
        self.stories[story_id] = story
        self._save()
        return story_id
    
    def list_projects(self, status: Optional[str] = None) -> List[Project]:
        results = list(self.projects.values())
        if status:
            results = [p for p in results if p.status == status]
        return sorted(results, key=lambda p: p.created_at, reverse=True)
    
    def list_epics(self, project_id: str) -> List[Epic]:
        return [e for e in self.epics.values() if e.project_id == project_id]
    
    def list_stories(self, epic_id: str) -> List[Story]:
        return [s for s in self.stories.values() if s.epic_id == epic_id]


def create_project(name: str, description: str = "") -> str:
    """Quick create project function."""
    pm = ProjectManager()
    return pm.create_project(name, description)


def list_projects(status: Optional[str] = None) -> List[Project]:
    """Quick list projects function."""
    pm = ProjectManager()
    return pm.list_projects(status)


__all__ = ["ProjectManager", "Project", "Epic", "Story", "ProjectStatus", "create_project", "list_projects"]