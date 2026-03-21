"""
Prompt Blueprints - Personal Prompt Library

Save prompts with triggers, auto-expand when you type casually.
"""

import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class Blueprint:
    """A saved prompt blueprint."""
    id: str
    name: str
    trigger: str  # What you type: "like a streetpunk"
    full_prompt: str  # What it expands to
    tags: List[str]
    created_at: str
    usage_count: int = 0
    last_used: Optional[str] = None
    rating: float = 0.0  # 0-5 stars
    notes: str = ""


class BlueprintLibrary:
    """
    Your personal prompt library.
    
    Usage:
    1. Save prompts with triggers
    2. Type casually ("explain like a streetpunk")
    3. System auto-expands to full prompt
    """
    
    def __init__(self, db_path: str = "blueprint_db.json"):
        self.db_path = Path(db_path)
        self.blueprints: Dict[str, Blueprint] = {}
        self._load()
    
    def _load(self):
        """Load blueprints from database."""
        if self.db_path.exists():
            with open(self.db_path) as f:
                data = json.load(f)
                for bp_data in data.get("blueprints", []):
                    bp = Blueprint(**bp_data)
                    self.blueprints[bp.id] = bp
    
    def _save(self):
        """Save blueprints to database."""
        data = {
            "blueprints": [asdict(bp) for bp in self.blueprints.values()],
            "last_updated": datetime.now().isoformat(),
        }
        with open(self.db_path, "w") as f:
            json.dump(data, f, indent=2)
    
    def save(
        self,
        name: str,
        trigger: str,
        full_prompt: str,
        tags: Optional[List[str]] = None,
        notes: str = "",
    ) -> str:
        """
        Save a new blueprint.
        
        Args:
            name: Short name (e.g., "streetpunk")
            trigger: What you type (e.g., "like a streetpunk")
            full_prompt: Full expanded prompt
            tags: Optional tags for organization
            notes: Personal notes
        
        Returns:
            Blueprint ID
        """
        bp_id = f"{name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        blueprint = Blueprint(
            id=bp_id,
            name=name,
            trigger=trigger.lower(),
            full_prompt=full_prompt,
            tags=tags or [],
            created_at=datetime.now().isoformat(),
            notes=notes,
        )
        
        self.blueprints[bp_id] = blueprint
        self._save()
        
        return bp_id
    
    def expand(self, text: str) -> str:
        """
        Expand triggers in text to full prompts.
        
        Args:
            text: User input (may contain triggers)
        
        Returns:
            Expanded text with triggers replaced
        """
        result = text
        
        # Find matching triggers
        for bp in self.blueprints.values():
            # Check for trigger in text (case insensitive)
            if bp.trigger.lower() in result.lower():
                # Replace trigger with full prompt
                result = result.replace(
                    bp.trigger,
                    f"{bp.full_prompt}\n\n",
                )
                # Update usage stats
                bp.usage_count += 1
                bp.last_used = datetime.now().isoformat()
                self._save()
        
        return result
    
    def find_by_trigger(self, text: str) -> List[Blueprint]:
        """Find blueprints whose triggers appear in text."""
        matches = []
        for bp in self.blueprints.values():
            if bp.trigger.lower() in text.lower():
                matches.append(bp)
        return matches
    
    def list_all(self, tag: Optional[str] = None) -> List[Blueprint]:
        """List all blueprints, optionally filtered by tag."""
        blueprints = list(self.blueprints.values())
        
        if tag:
            blueprints = [bp for bp in blueprints if tag in bp.tags]
        
        # Sort by usage count (most used first)
        return sorted(blueprints, key=lambda b: b.usage_count, reverse=True)
    
    def get(self, blueprint_id: str) -> Optional[Blueprint]:
        """Get a specific blueprint by ID."""
        return self.blueprints.get(blueprint_id)
    
    def delete(self, blueprint_id: str) -> bool:
        """Delete a blueprint."""
        if blueprint_id in self.blueprints:
            del self.blueprints[blueprint_id]
            self._save()
            return True
        return False
    
    def rate(self, blueprint_id: str, rating: float):
        """Rate a blueprint (0-5 stars)."""
        if blueprint_id in self.blueprints:
            self.blueprints[blueprint_id].rating = rating
            self._save()
    
    def search(self, query: str) -> List[Blueprint]:
        """Search blueprints by name, trigger, or tags."""
        query_lower = query.lower()
        matches = []
        
        for bp in self.blueprints.values():
            if (
                query_lower in bp.name.lower() or
                query_lower in bp.trigger.lower() or
                query_lower in " ".join(bp.tags).lower() or
                query_lower in bp.full_prompt.lower()
            ):
                matches.append(bp)
        
        return matches
    
    def get_stats(self) -> Dict[str, Any]:
        """Get library statistics."""
        total = len(self.blueprints)
        total_uses = sum(bp.usage_count for bp in self.blueprints.values())
        avg_rating = (
            sum(bp.rating for bp in self.blueprints.values() if bp.rating > 0) /
            sum(1 for bp in self.blueprints.values() if bp.rating > 0)
        ) if total > 0 else 0
        
        # Most used
        most_used = max(
            self.blueprints.values(),
            key=lambda b: b.usage_count,
            default=None
        )
        
        return {
            "total_blueprints": total,
            "total_uses": total_uses,
            "average_rating": avg_rating,
            "most_used": asdict(most_used) if most_used else None,
        }


# Example blueprints to get you started
EXAMPLE_BLUEPRINTS = [
    {
        "name": "streetpunk",
        "trigger": "like a streetpunk",
        "full_prompt": "Write in the style of an urban street punk. Use slang, informal grammar, rebellious tone. Reference city life, be irreverent and sarcastic. Don't be polite or formal.",
        "tags": ["style", "casual", "creative"],
    },
    {
        "name": "lawyer",
        "trigger": "like my lawyer",
        "full_prompt": "Write in formal, precise language. Use legal terminology where appropriate. Be thorough, cite potential issues, cover edge cases. Maintain professional tone.",
        "tags": ["style", "formal", "professional"],
    },
    {
        "name": "eli5",
        "trigger": "explain like I'm 5",
        "full_prompt": "Explain this in simple terms a 5-year-old could understand. Use analogies, avoid jargon, keep sentences short. Make it fun and engaging.",
        "tags": ["explanation", "simple", "educational"],
    },
    {
        "name": "roast",
        "trigger": "roast me",
        "full_prompt": "Give a funny, sarcastic roast. Be witty and clever, not mean-spirited. Use humor, exaggeration, and playful insults. Keep it light-hearted.",
        "tags": ["fun", "casual", "entertainment"],
    },
    {
        "name": "code_review",
        "trigger": "code review",
        "full_prompt": "Review this code thoroughly. Check for: bugs, security issues, performance problems, code style, missing error handling, edge cases. Provide specific suggestions for improvement.",
        "tags": ["code", "review", "development"],
    },
    {
        "name": "planner",
        "trigger": "planner mode",
        "full_prompt": "Think strategically. Break down complex problems into steps. Consider tradeoffs, risks, and alternatives. Plan for long-term maintainability and scalability.",
        "tags": ["ai", "council", "strategy"],
    },
    {
        "name": "engineer",
        "trigger": "engineer mode",
        "full_prompt": "You are an expert software engineer. Write clean, efficient, well-documented code. Follow best practices. Consider error handling, testing, and maintainability.",
        "tags": ["ai", "council", "code"],
    },
    {
        "name": "critic",
        "trigger": "critic mode",
        "full_prompt": "You are a meticulous critic. Find flaws, bugs, and issues. Be thorough and constructive. Question assumptions. Identify edge cases and failure modes.",
        "tags": ["ai", "council", "review"],
    },
]


def create_example_library() -> BlueprintLibrary:
    """Create a library with example blueprints."""
    lib = BlueprintLibrary("blueprint_db.json")
    
    for example in EXAMPLE_BLUEPRINTS:
        lib.save(**example)
    
    return lib


if __name__ == "__main__":
    # Demo usage
    print("Creating example blueprint library...\n")
    
    lib = create_example_library()
    
    print(f"Saved {len(lib.blueprints)} blueprints\n")
    
    # Test expansion
    test_inputs = [
        "Explain quantum computing like a streetpunk",
        "Write this contract like my lawyer",
        "Can you code review this function?",
        "Enter planner mode for this problem",
    ]
    
    print("Testing expansion:\n")
    for test in test_inputs:
        expanded = lib.expand(test)
        print(f"Input:  {test}")
        print(f"Output: {expanded[:100]}...")
        print()
