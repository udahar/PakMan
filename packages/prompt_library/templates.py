# Updated-On: 2026-03-08
# Updated-By: Codex
# PM-Ticket: UNTRACKED

"""
Prompt Templates Library
Pre-built prompt templates for common tasks
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class PromptTemplate:
    """A reusable prompt template."""

    template_id: str
    name: str
    description: str
    template: str
    variables: List[str]
    category: str
    tags: List[str]


class PromptTemplates:
    """
    Library of pre-built prompt templates.

    Categories:
    - coding: Code generation, debugging
    - writing: Content creation
    - analysis: Data analysis, review
    - communication: Email, messages
    - learning: Teaching, explanation
    - productivity: Planning, organizing
    """

    TEMPLATES = [
        PromptTemplate(
            template_id="code_explainer",
            name="Code Explainer",
            description="Explain code in simple terms",
            template="""Explain this code step by step, as if teaching a beginner:

```{language}
{code}
```

Provide:
1. What the code does (simple terms)
2. Each major section's purpose
3. Any important concepts to understand""",
            variables=["language", "code"],
            category="coding",
            tags=["explanation", "learning", "beginner"],
        ),
        PromptTemplate(
            template_id="code_reviewer",
            name="Code Reviewer",
            description="Review code for issues",
            template="""Review this code for issues:

```{language}
{code}
```

Check for:
- Bugs and logic errors
- Security vulnerabilities
- Performance problems
- Code style issues
- Missing error handling

Provide a detailed report with severity levels.""",
            variables=["language", "code"],
            category="coding",
            tags=["review", "security", "quality"],
        ),
        PromptTemplate(
            template_id="write_email",
            name="Professional Email",
            description="Write a professional email",
            template="""Write a professional email with the following details:

- To: {recipient}
- Subject: {subject}
- Purpose: {purpose}
- Tone: {tone}
- Key points to include: {key_points}

Make it clear, concise, and professional.""",
            variables=["recipient", "subject", "purpose", "tone", "key_points"],
            category="communication",
            tags=["email", "professional", "business"],
        ),
        PromptTemplate(
            template_id="data_analysis",
            name="Data Analysis",
            description="Analyze data and find insights",
            template="""Analyze this dataset:

{data_description}

Provide:
1. Key patterns and trends
2. Statistical summary
3. Potential insights
4. Recommendations
5. Visualizations suggestions

Use {analysis_method} analysis.""",
            variables=["data_description", "analysis_method"],
            category="analysis",
            tags=["data", "analytics", "insights"],
        ),
        PromptTemplate(
            template_id="teach_concept",
            name="Teach Concept",
            description="Explain a concept thoroughly",
            template="""Teach me about {concept} as if I'm a complete beginner.

Include:
- Simple definition
- Real-world examples
- Why it matters
- Common misconceptions
- How to learn more

Level: {difficulty_level}""",
            variables=["concept", "difficulty_level"],
            category="learning",
            tags=["teaching", "explanation", "beginner"],
        ),
        PromptTemplate(
            template_id="meeting_notes",
            name="Meeting Notes",
            description="Summarize meeting into notes",
            template="""Convert this meeting transcript into organized notes:

{transcript}

Include:
- Key decisions made
- Action items with owners
- Discussion topics
- Next steps
- Important dates/deadlines""",
            variables=["transcript"],
            category="productivity",
            tags=["notes", "meetings", "organization"],
        ),
        PromptTemplate(
            template_id="brainstorm",
            name="Brainstorming Session",
            description="Generate creative ideas",
            template="""Help me brainstorm ideas for: {topic}

Context: {context}
Goal: {goal}
Quantity: Generate {number} ideas

For each idea, provide:
- Title
- Brief description
- Pros
- Potential challenges""",
            variables=["topic", "context", "goal", "number"],
            category="creativity",
            tags=["brainstorming", "ideas", "creative"],
        ),
        PromptTemplate(
            template_id="decision_matrix",
            name="Decision Matrix",
            description="Compare options systematically",
            template="""Help me compare these options: {options}

Criteria to evaluate:
{criteria}

For each option, rate 1-5 on each criteria and provide:
- Total score
- Strengths
- Weaknesses
- Recommendation""",
            variables=["options", "criteria"],
            category="analysis",
            tags=["decision", "comparison", "planning"],
        ),
        PromptTemplate(
            template_id="step_by_step",
            name="Step by Step Guide",
            description="Create detailed instructions",
            template="""Create a step-by-step guide for: {task}

Audience: {audience}
Difficulty: {difficulty}
Time required: {time}

Include:
- Prerequisites
- Each step with clear instructions
- Tips and tricks
- Common mistakes to avoid
- How to verify success""",
            variables=["task", "audience", "difficulty", "time"],
            category="learning",
            tags=["tutorial", "instructions", "guide"],
        ),
        PromptTemplate(
            template_id="sql_generator",
            name="SQL Query Generator",
            description="Generate SQL queries",
            template="""Generate a SQL query for:

Database: {database_type}
Task: {task}
Tables involved: {tables}
Conditions: {conditions}
Desired output: {output}

Also provide:
- Explanation of how it works
- Alternative approaches
- Performance considerations""",
            variables=["database_type", "task", "tables", "conditions", "output"],
            category="coding",
            tags=["sql", "database", "query"],
        ),
        PromptTemplate(
            template_id="api_docs",
            name="API Documentation",
            description="Generate API documentation",
            template="""Create documentation for this API endpoint:

Endpoint: {endpoint}
Method: {method}
Purpose: {purpose}

Include:
- Request parameters
- Request body schema
- Response format
- Error codes
- Example requests/responses
- Usage notes""",
            variables=["endpoint", "method", "purpose"],
            category="coding",
            tags=["api", "documentation", "technical"],
        ),
        PromptTemplate(
            template_id="test_generator",
            name="Test Generator",
            description="Generate unit tests",
            template="""Generate unit tests for:

Language: {language}
Testing framework: {framework}
Code to test: {code}

Include:
- Unit tests for main functions
- Edge case tests
- Mock setup
- Test coverage goals""",
            variables=["language", "framework", "code"],
            category="coding",
            tags=["testing", "unit tests", "quality"],
        ),
    ]

    def __init__(self):
        self.templates = {t.template_id: t for t in self.TEMPLATES}

    def get_template(self, template_id: str) -> Optional[PromptTemplate]:
        """Get template by ID."""
        return self.templates.get(template_id)

    def list_templates(self, category: Optional[str] = None) -> List[PromptTemplate]:
        """List templates, optionally filtered by category."""
        if category:
            return [t for t in self.TEMPLATES if t.category == category]
        return self.TEMPLATES

    def search_templates(self, query: str) -> List[PromptTemplate]:
        """Search templates by name or description."""
        query = query.lower()
        return [
            t
            for t in self.TEMPLATES
            if query in t.name.lower() or query in t.description.lower()
        ]

    def fill_template(self, template_id: str, variables: Dict[str, str]) -> str:
        """Fill in template with variables."""
        template = self.get_template(template_id)
        if not template:
            return f"Template {template_id} not found"

        return template.template.format(**variables)

    def suggest_template(self, task: str) -> List[PromptTemplate]:
        """Suggest templates for a task."""
        task_lower = task.lower()

        suggestions = []

        if any(w in task_lower for w in ["code", "program", "function"]):
            suggestions.extend(self.list_templates("coding"))

        if any(w in task_lower for w in ["email", "write", "message"]):
            suggestions.extend(self.list_templates("communication"))

        if any(w in task_lower for w in ["analyze", "review", "compare"]):
            suggestions.extend(self.list_templates("analysis"))

        if any(w in task_lower for w in ["teach", "learn", "explain"]):
            suggestions.extend(self.list_templates("learning"))

        if any(w in task_lower for w in ["plan", "organize", "meeting"]):
            suggestions.extend(self.list_templates("productivity"))

        if any(w in task_lower for w in ["idea", "brainstorm", "creative"]):
            suggestions.extend(self.list_templates("creativity"))

        return suggestions[:5]

    def get_categories(self) -> List[str]:
        """Get all categories."""
        return list(set(t.category for t in self.TEMPLATES))


def create_prompt_templates() -> PromptTemplates:
    """Factory function to create prompt templates."""
    return PromptTemplates()


# === Template Engine Features ===


class TemplateEngine:
    """
    Advanced template rendering with composition and versioning.

    Usage:
        engine = TemplateEngine()
        prompt = engine.render("explain_like_im_5", topic="quantum computing")
    """

    def __init__(self):
        self.templates = PromptTemplates()
        self.template_versions: Dict[str, List[Dict]] = {}

    def render(self, template_id: str, **kwargs) -> str:
        """Render a template with variables."""
        template = self.templates.get_template(template_id)
        if not template:
            return f"Template '{template_id}' not found"

        return template.template.format(**kwargs)

    def compose(self, template_ids: List[str], separator: str = "\n\n") -> str:
        """Compose multiple templates together."""
        parts = []
        for tid in template_ids:
            template = self.templates.get_template(tid)
            if template:
                parts.append(template.template)
        return separator.join(parts)

    def version_save(self, template_id: str, version: str, content: str = None):
        """Save a version of a template."""
        if template_id not in self.template_versions:
            self.template_versions[template_id] = []

        template = self.templates.get_template(template_id)

        self.template_versions[template_id].append(
            {
                "version": version,
                "content": content or (template.template if template else ""),
            }
        )

    def version_list(self, template_id: str) -> List[Dict]:
        """List versions of a template."""
        return self.template_versions.get(template_id, [])

    def version_get(self, template_id: str, version: str) -> str:
        """Get a specific version of a template."""
        versions = self.template_versions.get(template_id, [])
        for v in versions:
            if v["version"] == version:
                return v["content"]
        return ""
