# Updated-On: 2026-03-08
# Updated-By: Codex
# PM-Ticket: UNTRACKED

"""
Prompt Parser
Parse prompts from prompts.chat CSV format
"""

import csv
import re
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Prompt:
    """A single prompt from prompts.chat."""

    act: str
    prompt: str
    for_devs: bool
    prompt_type: str
    contributor: str
    vetted: bool = False
    variables: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "act": self.act,
            "prompt": self.prompt,
            "for_devs": self.for_devs,
            "prompt_type": self.prompt_type,
            "contributor": self.contributor,
            "vetting_status": "approved" if self.vetted else "pending",
            "variables": self.variables,
            "tags": self.tags,
        }


class PromptParser:
    """
    Parse prompts from prompts.chat CSV format.

    CSV columns: act, prompt, for_devs, type, contributor
    """

    def __init__(self):
        self.prompts: List[Prompt] = []

    def parse_csv(self, file_path: str) -> int:
        """Parse prompts from CSV file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")

        import csv

        csv.field_size_limit(10000000)  # Handle large prompt fields

        count = 0
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    prompt = self._parse_row(row)
                    if prompt:
                        self.prompts.append(prompt)
                        count += 1
                except Exception:
                    continue

        return count

    def _parse_row(self, row: Dict[str, str]) -> Optional[Prompt]:
        """Parse a single CSV row into a Prompt."""
        act = row.get("act", "").strip()
        prompt_text = row.get("prompt", "").strip()

        if not act or not prompt_text:
            return None

        for_devs = row.get("for_devs", "FALSE").upper() == "TRUE"
        prompt_type = row.get("type", "TEXT").strip()
        contributor = row.get("contributor", "unknown").strip()

        variables = self._extract_variables(prompt_text)

        tags = self._generate_tags(act, prompt_text)

        return Prompt(
            act=act,
            prompt=prompt_text,
            for_devs=for_devs,
            prompt_type=prompt_type,
            contributor=contributor,
            variables=variables,
            tags=tags,
        )

    def _extract_variables(self, text: str) -> List[str]:
        """Extract ${variable} patterns from prompt text."""
        pattern = r"\$\{([^}:]+)(?::([^}]*))?\}"
        matches = re.findall(pattern, text)

        variables = []
        seen = set()
        for name, default in matches:
            if name not in seen:
                variables.append(name)
                seen.add(name)

        return variables

    def _generate_tags(self, act: str, prompt: str) -> List[str]:
        """Generate tags for a prompt based on content."""
        tags = []
        text = (act + " " + prompt).lower()

        tag_keywords = {
            "coding": ["code", "programming", "developer", "function", "script"],
            "writing": ["write", "essay", "article", "content", "creative"],
            "translation": ["translate", "language", "english", "pronunciation"],
            "analysis": ["analyze", "analysis", "review", "improve", "optimize"],
            "roleplay": ["act as", "interviewer", "teacher", "expert", "character"],
            "data": ["excel", "spreadsheet", "data", "sql", "database"],
            "system": ["linux", "terminal", "console", "system", "command"],
            "education": ["explain", "teach", "learn", "tutorial", "concept"],
        }

        for tag, keywords in tag_keywords.items():
            if any(kw in text for kw in keywords):
                tags.append(tag)

        return tags[:5]

    def get_prompts(self) -> List[Prompt]:
        """Get all parsed prompts."""
        return self.prompts

    def get_prompts_by_tag(self, tag: str) -> List[Prompt]:
        """Get prompts filtered by tag."""
        return [p for p in self.prompts if tag in p.tags]

    def get_dev_prompts(self) -> List[Prompt]:
        """Get prompts marked for developers."""
        return [p for p in self.prompts if p.for_devs]

    def search_by_act(self, query: str) -> List[Prompt]:
        """Search prompts by act name."""
        query = query.lower()
        return [p for p in self.prompts if query in p.act.lower()]

    def get_stats(self) -> Dict[str, Any]:
        """Get parsing statistics."""
        all_tags = []
        for p in self.prompts:
            all_tags.extend(p.tags)

        tag_counts = {}
        for tag in all_tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

        return {
            "total_prompts": len(self.prompts),
            "dev_prompts": len(self.get_dev_prompts()),
            "with_variables": len([p for p in self.prompts if p.variables]),
            "top_tags": sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[
                :10
            ],
            "unique_contributors": len(set(p.contributor for p in self.prompts)),
        }


def create_prompt_parser() -> PromptParser:
    """Factory function to create prompt parser."""
    return PromptParser()
