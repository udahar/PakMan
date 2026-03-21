"""
Planner Role Test Suite

Tests reasoning and orchestration capabilities.
"""

PLANNER_TESTS = [
    {
        "name": "build_pipeline",
        "description": "Create a tool chain for a given task",
        "input": "Analyze repository architecture",
        "expected_output_contains": ["repo_index", "pipeline"],
        "scoring": {
            "completeness": 0.4,
            "tool_selection": 0.4,
            "efficiency": 0.2,
        }
    },
    {
        "name": "decompose_problem",
        "description": "Break down complex task into steps",
        "input": "Build a complete AI runtime with tool execution",
        "expected_output_contains": ["step", "phase"],
        "scoring": {
            "granularity": 0.3,
            "logical_flow": 0.4,
            "completeness": 0.3,
        }
    },
    {
        "name": "choose_tools",
        "description": "Select appropriate tools for task",
        "input": "Scan filesystem for security vulnerabilities",
        "expected_tools": ["file_scan", "grep_lite", "log_parse"],
        "scoring": {
            "relevance": 0.5,
            "efficiency": 0.3,
            "coverage": 0.2,
        }
    },
    {
        "name": "plan_recovery",
        "description": "Handle failure scenario",
        "input": "Tool execution failed mid-pipeline",
        "expected_output_contains": ["retry", "fallback", "error"],
        "scoring": {
            "robustness": 0.4,
            "alternatives": 0.4,
            "clarity": 0.2,
        }
    },
    {
        "name": "optimize_workflow",
        "description": "Improve existing pipeline",
        "input": "Current pipeline: repo_index → context_pack → LLM",
        "expected_output_contains": ["optimize", "improve"],
        "scoring": {
            "innovation": 0.3,
            "practicality": 0.4,
            "performance_gain": 0.3,
        }
    },
]
