"""
SupDoc - Auto-generate documentation for skills.

Analyzes skill prompts and generates comprehensive documentation including
category classification, complexity analysis, input/output extraction,
and usage examples.

Features:
- Automatic category classification
- Complexity detection
- Input/output extraction from prompts
- Markdown documentation generation
- Batch documentation for skill directories

Usage:
    from supdoc import AutoDoc
    
    doc = AutoDoc()
    result = doc.generate("humble_inquiry", prompt="You are a researcher...")
    
    # Generate all in directory
    results = doc.generate_all("/path/to/skills")
    doc.save_docs(results, "/output/docs")
"""

import os
import re
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class SupDocError(Exception):
    """Base exception for SupDoc operations."""
    pass


class AnalysisError(SupDocError):
    """Raised when skill analysis fails."""
    pass


class SkillAnalyzer:
    """Analyze skill prompts to understand what they do."""
    
    CATEGORIES: Dict[str, List[str]] = {
        "inquiry": ["ask", "question", "discover", "explore", "understand", "investigate"],
        "coding": ["code", "program", "function", "implement", "debug", "refactor", "algorithm"],
        "writing": ["write", "create", "compose", "draft", "content", "author"],
        "analysis": ["analyze", "review", "evaluate", "assess", "compare", "examine"],
        "research": ["research", "search", "find", "investigate", "learn", "discover"],
        "planning": ["plan", "strategy", "roadmap", "organize", "schedule"],
        "problem_solving": ["fix", "solve", "resolve", "troubleshoot", "debug"],
        "creative": ["creative", "imagine", "design", "brainstorm", "innovate"],
        "communication": ["explain", "describe", "summarize", "translate", "present"],
    }
    
    COMPLEXITY_INDICATORS: Dict[str, int] = {
        "simple": 500,
        "moderate": 2000,
        "complex": 5000,
    }
    
    INPUT_PATTERNS: List[str] = [
        r"(?:input|receive|takes?)[:\s]+([^\n.]+)",
        r"(?:parameter|arg|argument)[:\s]+([^\n.]+)",
        r"Given[:\s]+([^\n.]+)",
    ]
    
    OUTPUT_PATTERNS: List[str] = [
        r"(?:output|return|respond)[:\s]+([^\n.]+)",
        r"(?:produce|generate|create)[:\s]+([^\n.]+)",
        r"(?:result|outcome)[:\s]+([^\n.]+)",
    ]
    
    def analyze(self, skill_name: str, prompt: str) -> Dict[str, Any]:
        """
        Analyze a skill prompt.
        
        Args:
            skill_name: Name of the skill
            prompt: Skill prompt text
        
        Returns:
            Dict with analysis results
        """
        if not prompt:
            raise ValueError("prompt cannot be empty")
        
        prompt_lower = prompt.lower()
        
        detected_categories = self._detect_categories(prompt_lower)
        complexity = self._detect_complexity(prompt)
        inputs = self._extract_inputs(prompt)
        outputs = self._extract_outputs(prompt)
        keywords = self._extract_keywords(prompt_lower)
        
        return {
            "name": skill_name,
            "categories": detected_categories or ["general"],
            "complexity": complexity,
            "inputs": inputs,
            "outputs": outputs,
            "keywords": keywords,
            "prompt_length": len(prompt),
            "estimated_difficulty": self._estimate_difficulty(prompt),
        }
    
    def _detect_categories(self, prompt_lower: str) -> List[str]:
        """Detect skill categories based on keywords."""
        detected: List[str] = []
        
        for category, keywords in self.CATEGORIES.items():
            matches = sum(1 for kw in keywords if kw in prompt_lower)
            if matches >= 2 or (category in prompt_lower and matches >= 1):
                detected.append(category)
        
        return detected
    
    def _detect_complexity(self, prompt: str) -> str:
        """Detect skill complexity based on length."""
        length = len(prompt)
        
        for complexity, threshold in sorted(
            self.COMPLEXITY_INDICATORS.items(),
            key=lambda x: x[1]
        ):
            if length < threshold:
                return complexity
        
        return "complex"
    
    def _extract_inputs(self, prompt: str) -> List[str]:
        """Extract potential inputs from prompt."""
        inputs: Set[str] = set()
        
        for pattern in self.INPUT_PATTERNS:
            matches = re.findall(pattern, prompt, re.IGNORECASE)
            inputs.update(m.strip() for m in matches if m.strip())
        
        return list(inputs)[:5]
    
    def _extract_outputs(self, prompt: str) -> List[str]:
        """Extract potential outputs from prompt."""
        outputs: Set[str] = set()
        
        for pattern in self.OUTPUT_PATTERNS:
            matches = re.findall(pattern, prompt, re.IGNORECASE)
            outputs.update(m.strip() for m in matches if m.strip())
        
        return list(outputs)[:5]
    
    def _extract_keywords(self, prompt_lower: str) -> List[str]:
        """Extract significant keywords from prompt."""
        words = re.findall(r"\b[a-z]{4,}\b", prompt_lower)
        
        stop_words = {
            "that", "this", "with", "from", "have", "been",
            "will", "your", "should", "would", "could", "must",
            "need", "make", "want", "know", "think", "also",
        }
        
        significant = [w for w in set(words) if w not in stop_words]
        significant.sort()
        
        return significant[:10]
    
    def _estimate_difficulty(self, prompt: str) -> str:
        """Estimate difficulty based on multiple factors."""
        score = 0
        
        score += len(prompt) // 1000
        
        technical_terms = len(re.findall(
            r"\b(api|algorithm|function|class|module|async|await)\b",
            prompt.lower()
        ))
        score += technical_terms
        
        if re.search(r"(?:chain|sequential|parallel|concurrent)", prompt.lower()):
            score += 1
        
        if score <= 2:
            return "beginner"
        elif score <= 5:
            return "intermediate"
        else:
            return "advanced"


class DocGenerator:
    """Generate documentation from skill analysis."""
    
    def generate(self, skill_name: str, analysis: Dict[str, Any]) -> str:
        """
        Generate documentation from analysis.
        
        Args:
            skill_name: Name of the skill
            analysis: Analysis results from SkillAnalyzer
        
        Returns:
            Markdown documentation string
        """
        lines: List[str] = []
        
        lines.append(f"# {skill_name}")
        lines.append("")
        lines.append(f"**Category:** {', '.join(analysis['categories'])}")
        lines.append(f"**Complexity:** {analysis['complexity']}")
        lines.append(f"**Difficulty:** {analysis.get('estimated_difficulty', 'unknown')}")
        lines.append("")
        
        lines.append("## Description")
        lines.append("")
        
        if analysis["categories"]:
            primary = analysis["categories"][0].replace("_", " ").title()
            lines.append(f"This skill performs {primary} tasks.")
        else:
            lines.append("This skill performs general tasks.")
        
        lines.append(f"It is classified as a {analysis['complexity']} skill.")
        lines.append("")
        
        if analysis.get("keywords"):
            lines.append("**Keywords:** " + ", ".join(f"`{k}`" for k in analysis["keywords"][:5]))
            lines.append("")
        
        if analysis["inputs"]:
            lines.append("## Inputs")
            lines.append("")
            for inp in analysis["inputs"]:
                lines.append(f"- {inp}")
            lines.append("")
        
        if analysis["outputs"]:
            lines.append("## Outputs")
            lines.append("")
            for out in analysis["outputs"]:
                lines.append(f"- {out}")
            lines.append("")
        
        lines.append("## Usage")
        lines.append("")
        lines.append("```python")
        lines.append(f"from skills import {skill_name}")
        lines.append("")
        lines.append(f"result = {skill_name}.execute(input_data)")
        lines.append("```")
        lines.append("")
        
        return "\n".join(lines)


class AutoDoc:
    """
    Auto-generate documentation for skills.
    
    Usage:
        doc = AutoDoc()
        
        # Generate single doc
        doc_string = doc.generate("humble_inquiry", "You are a researcher...")
        
        # Generate all docs in directory
        all_docs = doc.generate_all("/path/to/skills")
        
        # Save to files
        doc.save_docs(all_docs, "/output/docs")
    """
    
    def __init__(self) -> None:
        self.analyzer = SkillAnalyzer()
        self.generator = DocGenerator()
        logger.info("AutoDoc initialized")
    
    def generate(
        self,
        skill_name: str,
        prompt: Optional[str] = None,
        prompt_file: Optional[str] = None
    ) -> str:
        """
        Generate documentation for a skill.
        
        Args:
            skill_name: Name of the skill
            prompt: Optional prompt text (if not provided, reads from prompt_file)
            prompt_file: Optional path to prompt file
        
        Returns:
            Generated documentation string
        """
        if prompt is None and prompt_file is None:
            prompt = f"You are a {skill_name} skill."
        elif prompt_file:
            try:
                prompt = Path(prompt_file).read_text(encoding="utf-8")
            except IOError as e:
                raise AnalysisError(f"Failed to read prompt file: {e}") from e
        
        analysis = self.analyzer.analyze(skill_name, prompt)
        doc = self.generator.generate(skill_name, analysis)
        
        logger.debug("Generated doc for %s", skill_name)
        
        return doc
    
    def generate_all(
        self,
        skills_dir: str,
        extension: str = ".md"
    ) -> Dict[str, str]:
        """
        Generate docs for all skills in directory.
        
        Args:
            skills_dir: Path to skills directory
            extension: File extension to look for
        
        Returns:
            Dict mapping skill names to documentation
        """
        results: Dict[str, str] = {}
        path = Path(skills_dir)
        
        if not path.exists():
            logger.error("Skills directory not found: %s", skills_dir)
            return results
        
        for skill_file in path.glob(f"*{extension}"):
            skill_name = skill_file.stem
            
            try:
                prompt = skill_file.read_text(encoding="utf-8")
                results[skill_name] = self.generate(skill_name, prompt)
                logger.debug("Generated doc for %s", skill_name)
            except Exception as e:
                logger.error("Failed to generate doc for %s: %s", skill_name, e)
                results[skill_name] = f"# {skill_name}\n\nError: {e}"
        
        logger.info("Generated %d documentation files from %s", len(results), skills_dir)
        
        return results
    
    def save_docs(
        self,
        docs: Dict[str, str],
        output_dir: str
    ) -> List[str]:
        """
        Save generated docs to directory.
        
        Args:
            docs: Dict of documentation strings
            output_dir: Output directory path
        
        Returns:
            List of created file paths
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        created: List[str] = []
        
        for name, doc in docs.items():
            file_path = output_path / f"{name}.md"
            try:
                file_path.write_text(doc, encoding="utf-8")
                created.append(str(file_path))
                logger.debug("Saved doc to %s", file_path)
            except IOError as e:
                logger.error("Failed to save %s: %s", file_path, e)
        
        logger.info("Saved %d documentation files to %s", len(created), output_dir)
        
        return created
    
    def analyze_directory(self, skills_dir: str) -> Dict[str, Dict[str, Any]]:
        """Analyze all skills in directory without generating docs."""
        path = Path(skills_dir)
        
        if not path.exists():
            return {}
        
        results: Dict[str, Dict[str, Any]] = {}
        
        for skill_file in path.glob("*.md"):
            skill_name = skill_file.stem
            try:
                prompt = skill_file.read_text(encoding="utf-8")
                results[skill_name] = self.analyzer.analyze(skill_name, prompt)
            except Exception as e:
                logger.error("Failed to analyze %s: %s", skill_name, e)
        
        return results


def create_auto_doc() -> AutoDoc:
    """Factory function to create AutoDoc instance."""
    return AutoDoc()
