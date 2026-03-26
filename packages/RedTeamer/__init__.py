"""
RedTeamer
Automated adversarial penetration suite for AI systems. Zero external deps.

Quick start:
    from RedTeamer import RedTeamer
    from RedTeamer.reporter import print_report

    # Point at your target (any fn(prompt)->str)
    def my_llm(prompt):
        return call_ollama(prompt)

    rt = RedTeamer(target=my_llm)
    results = rt.run()
    print_report(results, rt.summary())

    # Filter to only critical/high attacks
    rt = RedTeamer(target=my_llm, severities=["critical", "high"])
    results = rt.run()

    # Only jailbreaks
    rt = RedTeamer(target=my_llm, categories=["jailbreak"])
    results = rt.run()

    # Save JSONL vulnerability log
    from RedTeamer.reporter import to_jsonl
    to_jsonl(results, "vulnerabilities.jsonl")

    # Generate Markdown report
    from RedTeamer.reporter import to_markdown
    print(to_markdown(results, rt.summary()))
"""
from .runner import RedTeamer, AttackResult
from .attacks import ATTACKS, get_by_category, get_by_severity, all_categories
from .reporter import print_report, to_jsonl, to_markdown

__version__ = "0.1.0"
__all__ = [
    "RedTeamer",
    "AttackResult",
    "ATTACKS",
    "get_by_category",
    "get_by_severity",
    "all_categories",
    "print_report",
    "to_jsonl",
    "to_markdown",
]
