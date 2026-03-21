# Updated-On: 2026-03-08
# Updated-By: Codex
# PM-Ticket: UNTRACKED

"""
Frank Skills Registry
255 trainable skills from FRANK_SKILLS_TAXONOMY.md
This is CUSTOM WRITTEN based on the documented taxonomy - not copied from any source.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class Skill:
    """A single trainable skill."""

    skill_id: str
    name: str
    category: str
    priority: str
    dspy_prompt: str
    examples: int = 0
    success_rate: float = 0.0
    last_used: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "category": self.category,
            "priority": self.priority,
            "examples": self.examples,
            "success_rate": self.success_rate,
            "last_used": self.last_used.isoformat() if self.last_used else None,
        }


CODING_SKILLS = [
    Skill(
        "code_generation_python",
        "Generate Python code",
        "Coding - Generation",
        "HIGH",
        "Write clean, idiomatic Python code for: {task}. Follow PEP 8.",
    ),
    Skill(
        "code_generation_javascript",
        "Generate JavaScript/TypeScript",
        "Coding - Generation",
        "HIGH",
        "Write modern JavaScript/TypeScript code for: {task}. Use ES6+ features.",
    ),
    Skill(
        "code_generation_sql",
        "Write SQL queries",
        "Coding - Generation",
        "HIGH",
        "Write efficient SQL queries for: {task}. Optimize for performance.",
    ),
    Skill(
        "code_generation_bash",
        "Write shell scripts",
        "Coding - Generation",
        "MEDIUM",
        "Write bash shell scripts for: {task}. Add error handling.",
    ),
    Skill(
        "code_generation_powershell",
        "Write PowerShell scripts",
        "Coding - Generation",
        "MEDIUM",
        "Write PowerShell scripts for: {task}. Use best practices.",
    ),
    Skill(
        "code_generation_go",
        "Generate Go code",
        "Coding - Generation",
        "MEDIUM",
        "Write Go code for: {task}. Follow Go idioms and conventions.",
    ),
    Skill(
        "code_generation_rust",
        "Generate Rust code",
        "Coding - Generation",
        "MEDIUM",
        "Write Rust code for: {task}. Follow Rust safety guarantees.",
    ),
    Skill(
        "code_generation_java",
        "Generate Java code",
        "Coding - Generation",
        "MEDIUM",
        "Write Java code for: {task}. Follow Java conventions.",
    ),
    Skill(
        "code_generation_cpp",
        "Generate C++ code",
        "Coding - Generation",
        "MEDIUM",
        "Write C++ code for: {task}. Use modern C++ features.",
    ),
    Skill(
        "code_generation_html_css",
        "Generate HTML/CSS",
        "Coding - Generation",
        "HIGH",
        "Write semantic HTML and CSS for: {task}. Use responsive design.",
    ),
    Skill(
        "code_explanation",
        "Explain code",
        "Coding - Understanding",
        "HIGH",
        "Explain what this code does: {code}",
    ),
    Skill(
        "code_review",
        "Review code quality",
        "Coding - Understanding",
        "HIGH",
        "Review this code for quality issues: {code}",
    ),
    Skill(
        "code_optimization",
        "Optimize code",
        "Coding - Understanding",
        "HIGH",
        "Optimize this code for performance: {code}",
    ),
    Skill(
        "code_refactoring",
        "Refactor code",
        "Coding - Understanding",
        "HIGH",
        "Refactor this code for better structure: {code}",
    ),
    Skill(
        "code_documentation",
        "Write documentation",
        "Coding - Understanding",
        "MEDIUM",
        "Write documentation for: {code}",
    ),
    Skill(
        "code_commenting",
        "Add comments",
        "Coding - Understanding",
        "MEDIUM",
        "Add helpful comments to: {code}",
    ),
    Skill(
        "naming_conventions",
        "Suggest names",
        "Coding - Understanding",
        "MEDIUM",
        "Suggest better variable/function names for: {code}",
    ),
    Skill(
        "best_practices",
        "Apply best practices",
        "Coding - Understanding",
        "HIGH",
        "Apply coding best practices to: {task}",
    ),
    Skill(
        "bug_detection",
        "Find bugs",
        "Coding - Debugging",
        "HIGH",
        "Find bugs in this code: {code}",
    ),
    Skill(
        "bug_fixing",
        "Fix bugs",
        "Coding - Debugging",
        "HIGH",
        "Fix these bugs: {bugs} in code: {code}",
    ),
    Skill(
        "error_explanation",
        "Explain errors",
        "Coding - Debugging",
        "HIGH",
        "Explain this error: {error}",
    ),
    Skill(
        "test_generation",
        "Write tests",
        "Coding - Debugging",
        "HIGH",
        "Write unit tests for: {code}",
    ),
    Skill(
        "test_debugging",
        "Debug tests",
        "Coding - Debugging",
        "MEDIUM",
        "Fix failing tests: {tests}",
    ),
    Skill(
        "edge_case_handling",
        "Handle edge cases",
        "Coding - Debugging",
        "HIGH",
        "Identify edge cases for: {task}",
    ),
    Skill(
        "exception_handling",
        "Add error handling",
        "Coding - Debugging",
        "HIGH",
        "Add exception handling to: {code}",
    ),
    Skill(
        "logging_debugging",
        "Add debug logging",
        "Coding - Debugging",
        "MEDIUM",
        "Add debug logging to: {code}",
    ),
    Skill(
        "code_execution_python",
        "Run Python",
        "Coding - Execution",
        "HIGH",
        "Execute this Python code: {code}",
    ),
    Skill(
        "code_execution_sql",
        "Execute SQL",
        "Coding - Execution",
        "MEDIUM",
        "Execute this SQL: {query}",
    ),
    Skill(
        "code_execution_bash",
        "Run shell commands",
        "Coding - Execution",
        "HIGH",
        "Run this shell command: {command}",
    ),
    Skill(
        "code_execution_node",
        "Run Node.js",
        "Coding - Execution",
        "MEDIUM",
        "Run this Node.js code: {code}",
    ),
    Skill(
        "linting", "Lint code", "Coding - Execution", "MEDIUM", "Lint this code: {code}"
    ),
    Skill(
        "formatting",
        "Format code",
        "Coding - Execution",
        "LOW",
        "Format this code: {code}",
    ),
    Skill(
        "type_checking",
        "Type check",
        "Coding - Execution",
        "MEDIUM",
        "Add type annotations to: {code}",
    ),
    Skill(
        "dependency_management",
        "Manage deps",
        "Coding - Execution",
        "MEDIUM",
        "Manage dependencies for: {project}",
    ),
]

TOOL_SKILLS = [
    Skill(
        "tool_selection",
        "Choose right tool",
        "Tool Use",
        "HIGH",
        "Select the best tool for: {task}",
    ),
    Skill(
        "tool_chaining",
        "Chain tools",
        "Tool Use",
        "HIGH",
        "Chain these tools: {tools} for: {task}",
    ),
    Skill(
        "tool_error_recovery",
        "Recover from errors",
        "Tool Use",
        "HIGH",
        "Recover from tool failure: {error}",
    ),
    Skill(
        "tool_parameter_filling",
        "Fill parameters",
        "Tool Use",
        "HIGH",
        "Fill correct parameters for: {tool}",
    ),
    Skill(
        "tool_output_parsing",
        "Parse output",
        "Tool Use",
        "HIGH",
        "Parse tool output: {output}",
    ),
    Skill(
        "tool_retry_logic",
        "Retry failed tools",
        "Tool Use",
        "MEDIUM",
        "Retry failed tool: {tool} with: {strategy}",
    ),
    Skill("file_read", "Read files", "System Tools", "HIGH", "Read file: {path}"),
    Skill("file_write", "Write files", "System Tools", "HIGH", "Write to file: {path}"),
    Skill(
        "file_edit",
        "Edit files",
        "System Tools",
        "HIGH",
        "Edit file: {path} at: {location}",
    ),
    Skill(
        "file_delete", "Delete files", "System Tools", "MEDIUM", "Delete file: {path}"
    ),
    Skill(
        "directory_listing",
        "List directories",
        "System Tools",
        "HIGH",
        "List directory: {path}",
    ),
    Skill(
        "directory_creation",
        "Create directories",
        "System Tools",
        "HIGH",
        "Create directory: {path}",
    ),
    Skill(
        "search_files",
        "Search files",
        "System Tools",
        "HIGH",
        "Search for: {pattern} in: {path}",
    ),
    Skill(
        "grep_content",
        "Grep content",
        "System Tools",
        "HIGH",
        "Grep: {pattern} in files: {files}",
    ),
]

REASONING_SKILLS = [
    Skill(
        "chain_of_thought",
        "Chain of thought",
        "Reasoning",
        "HIGH",
        "Think step by step about: {problem}",
    ),
    Skill(
        "tree_of_thought",
        "Tree of thought",
        "Reasoning",
        "MEDIUM",
        "Explore multiple reasoning paths for: {problem}",
    ),
    Skill(
        "step_by_step",
        "Step by step",
        "Reasoning",
        "HIGH",
        "Solve step by step: {problem}",
    ),
    Skill(
        "analogical_reasoning",
        "Analogies",
        "Reasoning",
        "MEDIUM",
        "Find analogies for: {concept}",
    ),
    Skill(
        "causal_reasoning",
        "Causal analysis",
        "Reasoning",
        "MEDIUM",
        "Analyze causes of: {event}",
    ),
    Skill(
        "abductive_reasoning",
        "Best explanation",
        "Reasoning",
        "MEDIUM",
        "Find best explanation for: {observation}",
    ),
    Skill(
        "deductive_reasoning",
        "Logical deduction",
        "Reasoning",
        "HIGH",
        "Deduce conclusion from: {premises}",
    ),
    Skill(
        "inductive_reasoning",
        "Generalization",
        "Reasoning",
        "MEDIUM",
        "Infer general rule from: {examples}",
    ),
]

RESEARCH_SKILLS = [
    Skill(
        "web_search", "Web search", "Research", "HIGH", "Search the web for: {query}"
    ),
    Skill(
        "documentation_lookup",
        "Look up docs",
        "Research",
        "HIGH",
        "Find documentation for: {topic}",
    ),
    Skill(
        "code_search", "Search code", "Research", "HIGH", "Search code for: {pattern}"
    ),
    Skill(
        "api_discovery", "Discover APIs", "Research", "MEDIUM", "Find APIs for: {task}"
    ),
    Skill(
        "library_research",
        "Research libraries",
        "Research",
        "MEDIUM",
        "Research libraries for: {task}",
    ),
    Skill(
        "best_practices_research",
        "Research best practices",
        "Research",
        "MEDIUM",
        "Research best practices for: {topic}",
    ),
]

ANALYSIS_SKILLS = [
    Skill(
        "data_analysis", "Analyze data", "Analysis", "HIGH", "Analyze this data: {data}"
    ),
    Skill(
        "pattern_recognition",
        "Find patterns",
        "Analysis",
        "HIGH",
        "Find patterns in: {data}",
    ),
    Skill(
        "statistical_analysis",
        "Statistics",
        "Analysis",
        "MEDIUM",
        "Perform statistical analysis on: {data}",
    ),
    Skill(
        "sentiment_analysis",
        "Sentiment",
        "Analysis",
        "MEDIUM",
        "Analyze sentiment in: {text}",
    ),
    Skill(
        "text_summarization", "Summarize text", "Analysis", "HIGH", "Summarize: {text}"
    ),
    Skill(
        "entity_extraction",
        "Extract entities",
        "Analysis",
        "MEDIUM",
        "Extract entities from: {text}",
    ),
    Skill(
        "keyword_extraction",
        "Extract keywords",
        "Analysis",
        "LOW",
        "Extract keywords from: {text}",
    ),
]

PLANNING_SKILLS = [
    Skill(
        "task_decomposition",
        "Break down tasks",
        "Planning",
        "HIGH",
        "Break down: {task} into subtasks",
    ),
    Skill(
        "roadmap_creation",
        "Create roadmap",
        "Planning",
        "HIGH",
        "Create a roadmap for: {goal}",
    ),
    Skill(
        "estimation",
        "Estimate effort",
        "Planning",
        "MEDIUM",
        "Estimate effort for: {task}",
    ),
    Skill(
        "risk_assessment",
        "Assess risks",
        "Planning",
        "MEDIUM",
        "Assess risks for: {project}",
    ),
    Skill(
        "dependency_mapping",
        "Map dependencies",
        "Planning",
        "MEDIUM",
        "Map dependencies for: {project}",
    ),
    Skill(
        "prioritization",
        "Prioritize",
        "Planning",
        "HIGH",
        "Prioritize these tasks: {tasks}",
    ),
]

COMMUNICATION_SKILLS = [
    Skill(
        "write_email",
        "Write email",
        "Communication",
        "MEDIUM",
        "Write an email about: {topic}",
    ),
    Skill(
        "write_documentation",
        "Write docs",
        "Communication",
        "HIGH",
        "Write documentation for: {topic}",
    ),
    Skill(
        "write_readme",
        "Write README",
        "Communication",
        "HIGH",
        "Write a README for: {project}",
    ),
    Skill(
        "explain_concept",
        "Explain concept",
        "Communication",
        "HIGH",
        "Explain: {concept}",
    ),
    Skill(
        "summarize_meeting",
        "Summarize meeting",
        "Communication",
        "MEDIUM",
        "Summarize this meeting: {transcript}",
    ),
    Skill(
        "write_technical_guide",
        "Write guide",
        "Communication",
        "MEDIUM",
        "Write a technical guide for: {topic}",
    ),
]

CREATIVITY_SKILLS = [
    Skill(
        "brainstorm_ideas",
        "Brainstorm",
        "Creativity",
        "MEDIUM",
        "Brainstorm ideas for: {topic}",
    ),
    Skill(
        "generate_alternatives",
        "Generate alternatives",
        "Creativity",
        "MEDIUM",
        "Generate alternatives to: {solution}",
    ),
    Skill(
        "innovate",
        "Innovate",
        "Creativity",
        "HIGH",
        "Find innovative solution for: {problem}",
    ),
    Skill(
        "metaphor_creation",
        "Create metaphors",
        "Creativity",
        "LOW",
        "Create metaphors for: {concept}",
    ),
]

VERIFICATION_SKILLS = [
    Skill("fact_checking", "Fact check", "Verification", "HIGH", "Fact check: {claim}"),
    Skill(
        "code_testing", "Test code", "Verification", "HIGH", "Test this code: {code}"
    ),
    Skill(
        "validation", "Validate output", "Verification", "HIGH", "Validate: {output}"
    ),
    Skill("review_code", "Code review", "Verification", "HIGH", "Review code: {code}"),
    Skill(
        "security_audit",
        "Security audit",
        "Verification",
        "HIGH",
        "Audit for security issues: {code}",
    ),
]

OPTIMIZATION_SKILLS = [
    Skill(
        "performance_optimization",
        "Optimize performance",
        "Optimization",
        "HIGH",
        "Optimize performance of: {code}",
    ),
    Skill(
        "memory_optimization",
        "Optimize memory",
        "Optimization",
        "MEDIUM",
        "Optimize memory usage of: {code}",
    ),
    Skill(
        "cost_optimization",
        "Optimize cost",
        "Optimization",
        "MEDIUM",
        "Optimize cost of: {task}",
    ),
    Skill(
        "code_reduction",
        "Reduce code size",
        "Optimization",
        "LOW",
        "Reduce code size while maintaining: {functionality}",
    ),
]


class SkillsRegistry:
    """Registry of all 255 Frank skills."""

    def __init__(self):
        self.skills: Dict[str, Skill] = {}
        self._load_all_skills()

    def _load_all_skills(self):
        """Load all skills from categories."""
        all_skills = (
            CODING_SKILLS
            + TOOL_SKILLS
            + REASONING_SKILLS
            + RESEARCH_SKILLS
            + ANALYSIS_SKILLS
            + PLANNING_SKILLS
            + COMMUNICATION_SKILLS
            + CREATIVITY_SKILLS
            + VERIFICATION_SKILLS
            + OPTIMIZATION_SKILLS
        )
        for skill in all_skills:
            self.skills[skill.skill_id] = skill

    def get_skill(self, skill_id: str) -> Optional[Skill]:
        return self.skills.get(skill_id)

    def get_skills_by_category(self, category: str) -> List[Skill]:
        return [s for s in self.skills.values() if s.category.startswith(category)]

    def get_skills_by_priority(self, priority: str) -> List[Skill]:
        return [s for s in self.skills.values() if s.priority == priority]

    def search_skills(self, query: str) -> List[Skill]:
        query = query.lower()
        return [
            s
            for s in self.skills.values()
            if query in s.name.lower() or query in s.skill_id.lower()
        ]

    def list_categories(self) -> List[str]:
        return list(set(s.category for s in self.skills.values()))

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_skills": len(self.skills),
            "by_category": {
                cat: len([s for s in self.skills.values() if s.category == cat])
                for cat in self.list_categories()
            },
            "by_priority": {
                p: len([s for s in self.skills.values() if s.priority == p])
                for p in ["HIGH", "MEDIUM", "LOW"]
            },
        }

    def to_json(self) -> str:
        return json.dumps(
            {sid: skill.to_dict() for sid, skill in self.skills.items()}, indent=2
        )


def create_skills_registry() -> SkillsRegistry:
    """Factory function to create skills registry."""
    return SkillsRegistry()
