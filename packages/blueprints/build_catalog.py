"""
Build Prompt Auto-Catalog

Automatically captures, summarizes, and merges build prompts for future use.

The idea:
1. You ask AI to build something
2. System captures the conversation
3. Extracts what worked (the prompts, the approach)
4. Merges with similar build patterns
5. Next time you build something similar, it uses the learned pattern
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import hashlib


@dataclass
class BuildRecord:
    """A recorded build session."""
    id: str
    what_built: str  # What you asked to build
    initial_prompt: str  # Your initial request
    ai_approach: str  # How AI approached it
    successful_prompts: List[str]  # Prompts that worked
    failed_prompts: List[str]  # Prompts that didn't work
    tags: List[str]
    created_at: str
    build_quality: float = 0.0  # 0-1 rating
    reuse_count: int = 0


class BuildCatalog:
    """
    Auto-catalog of build sessions.
    
    Learns from every build, gets smarter over time.
    """
    
    def __init__(self, db_path: str = "build_catalog.json"):
        self.db_path = Path(db_path)
        self.records: Dict[str, BuildRecord] = {}
        self.patterns: Dict[str, Dict] = {}  # Merged patterns
        self._load()
    
    def _load(self):
        """Load catalog from database."""
        if self.db_path.exists():
            with open(self.db_path) as f:
                data = json.load(f)
                for rec_data in data.get("records", []):
                    rec = BuildRecord(**rec_data)
                    self.records[rec.id] = rec
                self.patterns = data.get("patterns", {})
    
    def _save(self):
        """Save catalog to database."""
        data = {
            "records": [asdict(rec) for rec in self.records.values()],
            "patterns": self.patterns,
            "last_updated": datetime.now().isoformat(),
        }
        with open(self.db_path, "w") as f:
            json.dump(data, f, indent=2)
    
    def record_build(
        self,
        what_built: str,
        conversation: List[Dict[str, str]],
        quality_rating: float = 0.5,
        tags: Optional[List[str]] = None,
    ) -> str:
        """
        Record a build session from conversation.
        
        Args:
            what_built: What you asked to build
            conversation: List of {role, content} dicts
            quality_rating: How well it worked (0-1)
            tags: Optional tags
        
        Returns:
            Record ID
        """
        record_id = f"build_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Extract prompts from conversation
        successful_prompts = []
        failed_prompts = []
        ai_approach = ""
        
        for i, msg in enumerate(conversation):
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            if role == "user":
                # Check if this was a helpful prompt
                if i > 0 and conversation[i-1].get("role") == "assistant":
                    prev_response = conversation[i-1].get("content", "")
                    if len(prev_response) > 100:  # Substantial response
                        successful_prompts.append(content[:200])  # First 200 chars
            
            elif role == "assistant" and not ai_approach:
                # First AI response = approach
                ai_approach = content[:500]  # First 500 chars
        
        record = BuildRecord(
            id=record_id,
            what_built=what_built,
            initial_prompt=conversation[0]["content"] if conversation else "",
            ai_approach=ai_approach,
            successful_prompts=successful_prompts[:5],  # Top 5
            failed_prompts=failed_prompts[:3],  # Top 3
            tags=tags or self._auto_tag(what_built),
            created_at=datetime.now().isoformat(),
            build_quality=quality_rating,
        )
        
        self.records[record_id] = record
        
        # Merge into patterns
        self._merge_pattern(record)
        
        self._save()
        
        return record_id
    
    def _auto_tag(self, what_built: str) -> List[str]:
        """Auto-generate tags from what was built."""
        tags = []
        what_lower = what_built.lower()
        
        if any(word in what_lower for word in ["rust", "cargo", "crate"]):
            tags.append("rust")
        if any(word in what_lower for word in ["python", "pip", "py"]):
            tags.append("python")
        if any(word in what_lower for word in ["api", "endpoint", "http"]):
            tags.append("api")
        if any(word in what_lower for word in ["ui", "interface", "dashboard"]):
            tags.append("ui")
        if any(word in what_lower for word in ["agent", "ai", "model"]):
            tags.append("ai")
        if any(word in what_lower for word in ["build", "compile", "setup"]):
            tags.append("build")
        
        return tags
    
    def _merge_pattern(self, record: BuildRecord):
        """Merge build record into patterns."""
        # Group by tags
        for tag in record.tags:
            if tag not in self.patterns:
                self.patterns[tag] = {
                    "tag": tag,
                    "common_approaches": [],
                    "successful_prompts": [],
                    "avg_quality": 0.0,
                    "build_count": 0,
                }
            
            pattern = self.patterns[tag]
            pattern["build_count"] += 1
            
            # Add successful prompts
            for prompt in record.successful_prompts:
                if prompt not in pattern["successful_prompts"]:
                    pattern["successful_prompts"].append(prompt)
            
            # Update average quality
            total_quality = pattern["avg_quality"] * (pattern["build_count"] - 1)
            pattern["avg_quality"] = (total_quality + record.build_quality) / pattern["build_count"]
    
    def find_similar_builds(self, query: str) -> List[BuildRecord]:
        """Find similar past builds."""
        query_lower = query.lower()
        matches = []
        
        for record in self.records.values():
            # Check if query matches what was built
            if query_lower in record.what_built.lower():
                matches.append(record)
            # Or matches tags
            elif any(tag in query_lower for tag in record.tags):
                matches.append(record)
        
        # Sort by quality and recency
        return sorted(
            matches,
            key=lambda r: (r.build_quality, r.created_at),
            reverse=True
        )
    
    def get_pattern_summary(self, tag: str) -> Optional[Dict]:
        """Get merged pattern summary for a tag."""
        return self.patterns.get(tag)
    
    def get_best_practices(self, tag: str) -> List[str]:
        """Get best practices for a tag."""
        pattern = self.patterns.get(tag)
        if not pattern:
            return []
        
        # Return top successful prompts
        return pattern["successful_prompts"][:3]
    
    def generate_build_prompt(self, what_to_build: str) -> str:
        """
        Generate an optimized build prompt based on past successes.
        
        This is the magic - it merges learnings from similar builds.
        """
        # Find similar builds
        similar = self.find_similar_builds(what_to_build)
        
        if not similar:
            # No history, return basic prompt
            return f"Build this: {what_to_build}"
        
        # Get best practices from similar builds
        all_tags = set()
        for record in similar[:5]:  # Top 5 similar
            all_tags.update(record.tags)
        
        # Collect successful approaches
        successful_approaches = []
        for tag in all_tags:
            pattern = self.patterns.get(tag)
            if pattern:
                successful_approaches.extend(pattern.get("successful_prompts", [])[:2])
        
        # Build enhanced prompt
        prompt = f"""Build this: {what_to_build}

Based on {len(similar)} similar successful builds, here's what worked:

"""
        
        for i, approach in enumerate(successful_approaches[:5], 1):
            prompt += f"{i}. {approach}\n"
        
        prompt += "\nUse these proven approaches. Focus on quality over speed."
        
        return prompt
    
    def get_stats(self) -> Dict[str, Any]:
        """Get catalog statistics."""
        total_builds = len(self.records)
        avg_quality = (
            sum(r.build_quality for r in self.records.values()) / total_builds
            if total_builds > 0 else 0
        )
        
        return {
            "total_builds": total_builds,
            "average_quality": avg_quality,
            "patterns_learned": len(self.patterns),
            "tags": list(self.patterns.keys()),
        }


# Example usage
def demo():
    """Demonstrate the build catalog."""
    print("=" * 60)
    print("  BUILD CATALOG - Auto-Learning Build Prompts")
    print("=" * 60)
    
    catalog = BuildCatalog()
    
    # Simulate recording builds
    example_builds = [
        {
            "what": "Rust CLI tool",
            "conversation": [
                {"role": "user", "content": "Build a Rust CLI for file hashing"},
                {"role": "assistant", "content": "I'll create a Rust CLI with clap for argument parsing..."},
            ],
            "quality": 0.9,
            "tags": ["rust", "cli", "build"],
        },
        {
            "what": "Python API client",
            "conversation": [
                {"role": "user", "content": "Create Python client for REST API"},
                {"role": "assistant", "content": "I'll use requests library with proper error handling..."},
            ],
            "quality": 0.85,
            "tags": ["python", "api", "build"],
        },
    ]
    
    print("\n📝 Recording builds...\n")
    
    for build in example_builds:
        record_id = catalog.record_build(
            what_built=build["what"],
            conversation=build["conversation"],
            quality_rating=build["quality"],
            tags=build["tags"],
        )
        print(f"✅ Recorded: {build['what']} ({record_id[:12]}...)")
    
    # Show stats
    stats = catalog.get_stats()
    print(f"\n📊 Catalog Stats:")
    print(f"   Total builds: {stats['total_builds']}")
    print(f"   Avg quality: {stats['average_quality']:.1%}")
    print(f"   Patterns: {stats['patterns_learned']}")
    
    # Generate enhanced prompt
    print("\n🎯 Generate Build Prompt:\n")
    
    test_query = "Build a Rust web service"
    enhanced = catalog.generate_build_prompt(test_query)
    
    print(f"Query: {test_query}")
    print(f"\nEnhanced Prompt:")
    print(enhanced)
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    demo()
