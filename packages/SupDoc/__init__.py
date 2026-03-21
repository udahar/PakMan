"""
Auto-Doc - Generate Skill Documentation
"""

import os
import re
from typing import Dict, List, Optional
from pathlib import Path


class SkillAnalyzer:
    """Analyze skill prompts to understand what they do."""

    CATEGORIES = {
        "inquiry": ["ask", "question", "discover", "explore", "understand"],
        "coding": ["code", "program", "function", "implement", "debug", "refactor"],
        "writing": ["write", "create", "compose", "draft", "content"],
        "analysis": ["analyze", "review", "evaluate", "assess", "compare"],
        "research": ["research", "search", "find", "investigate", "learn"],
        "planning": ["plan", "strategy", "roadmap", "organize"],
        "problem_solving": ["fix", "solve", "resolve", "debug", "troubleshoot"],
    }

    def analyze(self, skill_name: str, prompt: str) -> Dict:
        """Analyze a skill prompt."""
        prompt_lower = prompt.lower()

        detected_categories = []
        for category, keywords in self.CATEGORIES.items():
            if any(kw in prompt_lower for kw in keywords):
                detected_categories.append(category)

        return {
            "name": skill_name,
            "categories": detected_categories or ["general"],
            "complexity": self._detect_complexity(prompt),
            "inputs": self._extract_inputs(prompt),
            "outputs": self._extract_outputs(prompt),
        }

    def _detect_complexity(self, prompt: str) -> str:
        """Detect skill complexity."""
        length = len(prompt)
        if length < 500:
            return "simple"
        elif length < 2000:
            return "moderate"
        return "complex"

    def _extract_inputs(self, prompt: str) -> List[str]:
        """Extract potential inputs."""
        patterns = [
            r"input[:\s]+([^\n]+)",
            r"receive[:\s]+([^\n]+)",
            r"takes?\s+([^\n]+)",
        ]

        inputs = []
        for pattern in patterns:
            matches = re.findall(pattern, prompt, re.IGNORECASE)
            inputs.extend(matches)

        return inputs[:5]

    def _extract_outputs(self, prompt: str) -> List[str]:
        """Extract potential outputs."""
        patterns = [
            r"output[:\s]+([^\n]+)",
            r"return[:\s]+([^\n]+)",
            r"respond[:\s]+([^\n]+)",
        ]

        outputs = []
        for pattern in patterns:
            matches = re.findall(pattern, prompt, re.IGNORECASE)
            outputs.extend(matches)

        return outputs[:5]


class DocGenerator:
    """Generate documentation from skill analysis."""

    def generate(self, skill_name: str, analysis: Dict) -> str:
        """Generate documentation."""
        doc = f"# {skill_name}\n\n"

        doc += f"**Category:** {', '.join(analysis['categories'])}\n\n"
        doc += f"**Complexity:** {analysis['complexity']}\n\n"

        doc += "## Description\n\n"
        doc += f"This skill performs {analysis['categories'][0]} tasks. "
        doc += f"It is classified as a {analysis['complexity']} skill.\n\n"

        if analysis["inputs"]:
            doc += "## Inputs\n\n"
            for inp in analysis["inputs"]:
                doc += f"- {inp}\n"
            doc += "\n"

        if analysis["outputs"]:
            doc += "## Outputs\n\n"
            for out in analysis["outputs"]:
                doc += f"- {out}\n"
            doc += "\n"

        doc += "## Usage\n\n"
        doc += f"```python\nfrom skills import {skill_name}\n\n"
        doc += f"result = {skill_name}.execute(input_data)\n```\n"

        return doc


class AutoDoc:
    """
    Auto-generate documentation for skills.

    Usage:
        doc = AutoDoc()
        skill_doc = doc.generate("humble_inquiry")
        all_docs = doc.generate_all("/path/to/skills")
    """

    def __init__(self):
        self.analyzer = SkillAnalyzer()
        self.generator = DocGenerator()

    def generate(self, skill_name: str, prompt: str = None) -> str:
        """Generate documentation for a skill."""
        if not prompt:
            prompt = f"You are a {skill_name} skill."

        analysis = self.analyzer.analyze(skill_name, prompt)
        return self.generator.generate(skill_name, analysis)

    def generate_all(self, skills_dir: str) -> Dict[str, str]:
        """Generate docs for all skills in directory."""
        results = {}

        path = Path(skills_dir)
        if not path.exists():
            return results

        for md_file in path.glob("*.md"):
            skill_name = md_file.stem

            try:
                with open(md_file, "r", encoding="utf-8") as f:
                    prompt = f.read()

                results[skill_name] = self.generate(skill_name, prompt)
            except Exception as e:
                results[skill_name] = f"Error: {e}"

        return results

    def save_docs(self, docs: Dict[str, str], output_dir: str):
        """Save generated docs to directory."""
        os.makedirs(output_dir, exist_ok=True)

        for name, doc in docs.items():
            output_path = os.path.join(output_dir, f"{name}.md")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(doc)


def create_auto_doc() -> AutoDoc:
    """Factory function."""
    return AutoDoc()
