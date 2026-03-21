"""
Engineer Role Test Suite

Tests code generation and validation capabilities.
"""

ENGINEER_TESTS = [
    {
        "name": "fix_broken_rust",
        "description": "Debug compilation error",
        "input": """
fn main() {
    let x = 5
    println!("x = {}", x);
}
""",
        "expected_fix": "Add semicolon after 'let x = 5'",
        "scoring": {
            "accuracy": 0.5,
            "explanation": 0.3,
            "speed": 0.2,
        }
    },
    {
        "name": "generate_tool_skeleton",
        "description": "Create new tool template",
        "input": "Create a Rust tool that counts words in files",
        "expected_contains": ["struct", "fn main", "clap"],
        "scoring": {
            "completeness": 0.4,
            "best_practices": 0.4,
            "documentation": 0.2,
        }
    },
    {
        "name": "validate_pipeline",
        "description": "Check tool compatibility",
        "input": {
            "pipeline": ["fs_scan", "json_fmt", "prompt_fmt"],
            "expected_io": "json"
        },
        "scoring": {
            "io_matching": 0.4,
            "error_detection": 0.4,
            "suggestions": 0.2,
        }
    },
    {
        "name": "write_test_harness",
        "description": "Generate tests for code",
        "input": "fn add(a: i32, b: i32) -> i32 { a + b }",
        "expected_contains": ["test", "assert", "assert_eq"],
        "scoring": {
            "coverage": 0.4,
            "edge_cases": 0.4,
            "clarity": 0.2,
        }
    },
    {
        "name": "refactor_code",
        "description": "Improve existing code",
        "input": """
def process(data):
    result = []
    for i in range(len(data)):
        if data[i] > 0:
            result.append(data[i] * 2)
    return result
""",
        "expected_improvements": ["enumerate", "list comprehension"],
        "scoring": {
            "readability": 0.3,
            "efficiency": 0.4,
            "pythonic": 0.3,
        }
    },
]
