"""
Analyst Role Test Suite

Tests information synthesis capabilities.
"""

ANALYST_TESTS = [
    {
        "name": "summarize_research",
        "description": "Condense information",
        "input": """
        [Long research paper about AI agent architectures]
        The paper discusses multi-agent systems, focusing on:
        1. Decentralized coordination mechanisms
        2. Communication protocols between agents
        3. Emergent behavior in agent swarms
        4. Applications in distributed computing
        ... [2000 more words]
        """,
        "expected_output_length": "300-500 words",
        "scoring": {
            "completeness": 0.3,
            "conciseness": 0.4,
            "accuracy": 0.3,
        }
    },
    {
        "name": "extract_insights",
        "description": "Find key points",
        "input": "[System logs from 1000 tool executions]",
        "expected_output_contains": ["pattern", "trend", "insight"],
        "scoring": {
            "insight_quality": 0.4,
            "relevance": 0.4,
            "novelty": 0.2,
        }
    },
    {
        "name": "compare_sources",
        "description": "Cross-reference data",
        "input": {
            "source_a": "Tool success rate: 85%",
            "source_b": "Tool success rate: 82%",
            "source_c": "Tool success rate: 88%",
        },
        "expected_output_contains": ["consensus", "variance", "reliability"],
        "scoring": {
            "accuracy": 0.4,
            "synthesis": 0.4,
            "clarity": 0.2,
        }
    },
    {
        "name": "identify_gaps",
        "description": "Find missing information",
        "input": "[System architecture document]",
        "expected_output_contains": ["missing", "gap", "unclear"],
        "scoring": {
            "coverage": 0.4,
            "insight": 0.4,
            "actionability": 0.2,
        }
    },
    {
        "name": "generate_report",
        "description": "Structured output",
        "input": "[Raw benchmark data]",
        "expected_structure": ["executive_summary", "methodology", "results", "conclusions"],
        "scoring": {
            "structure": 0.3,
            "completeness": 0.4,
            "clarity": 0.3,
        }
    },
]
