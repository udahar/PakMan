import random
from datetime import datetime
import hashlib



def mutate_prompt(prompt: str, mutation_type: str = None) -> str:
    """
    Mutate a prompt to create harder/easier variations.

    Types:
    - harder: Add constraints, edge cases
    - easier: Simplify requirements
    - complexity: Add multi-step requirements
    - creative: Add novel constraints
    """
    mutation_type = mutation_type or random.choice(
        ["harder", "easier", "complexity", "creative"]
    )

    mutations = {
        "harder": [
            f"{prompt} Consider edge cases and error handling.",
            f"{prompt} Optimize for time and space complexity.",
            f"{prompt} Make it thread-safe and handle race conditions.",
            f"{prompt} Add input validation and bounds checking.",
        ],
        "easier": f"{prompt} Just provide a basic solution.",
        "complexity": f"{prompt} Break this down into multiple steps.",
        "creative": f"{prompt} Find an unconventional approach.",
    }

    return random.choice(mutations[mutation_type])


def generate_task_framework(task_type: str) -> dict:
    """
    Generate a new task evaluation framework.

    This creates evaluation criteria, constraints, and success metrics.
    """
    frameworks = {
        "coding": [
            {"name": "correctness", "weight": 0.4, "check": "unit_tests_pass"},
            {"name": "efficiency", "weight": 0.3, "check": "time_complexity"},
            {"name": "readability", "weight": 0.3, "check": "lint_score"},
        ],
        "debugging": [
            {"name": "accuracy", "weight": 0.5, "check": "fixes_root_cause"},
            {"name": "speed", "weight": 0.3, "check": "minimal_changes"},
            {"name": "explanation", "weight": 0.2, "check": "clear_reasoning"},
        ],
        "reasoning": [
            {"name": "depth", "weight": 0.4, "check": "multi_angle"},
            {"name": "clarity", "weight": 0.3, "check": "logical_flow"},
            {"name": "evidence", "weight": 0.3, "check": "sources_cited"},
        ],
    }

    base = frameworks.get(task_type, frameworks["coding"])

    # Mutate weights
    mutated = []
    for criterion in base:
        new_criterion = criterion.copy()
        # Add some randomness to weights
        new_criterion["weight"] = max(
            0.1, criterion["weight"] + random.uniform(-0.1, 0.1)
        )
        mutated.append(new_criterion)

    return {
        "task_type": task_type,
        "criteria": mutated,
        "generated_at": datetime.now().isoformat(),
    }


# Track what's been tested
_tested_combinations = set()


def get_test_payload(task_type: str) -> dict:
    """
    Get a unique test payload (prompt + framework).

    Ensures we don't repeat same tests.
    """
    global _tested_combinations

    # Try to generate unique combination
    for _ in range(10):
        # Get or mutate prompt
        base_prompt = get_unique_prompt(task_type)

        # Sometimes mutate
        if random.random() < 0.3:
            prompt = mutate_prompt(base_prompt)
        else:
            prompt = base_prompt

        # Generate evaluation framework
        framework = generate_task_framework(task_type)

        # Check if unique
        key = f"{task_type}:{hash(prompt) % 10000}"
        if key not in _tested_combinations:
            _tested_combinations.add(key)
            return {
                "prompt": prompt,
                "framework": framework,
                "task_type": task_type,
            }

    # Fallback
    return {
        "prompt": get_unique_prompt(task_type),
        "framework": generate_task_framework(task_type),
        "task_type": task_type,
    }


import hashlib

_used_prompts = set()


def get_unique_prompt(task_type: str) -> str:
    """Get a unique prompt for the task type."""
    global _used_prompts

    # Template prompts per task type
    templates = {
        "coding": [
            "Write a function to reverse a linked list in Python",
            "Implement binary search algorithm",
            "Create a function to find duplicates in an array",
            "Write quicksort implementation",
            "Implement a stack using only queues",
            "Write a function to merge two sorted arrays",
            "Implement a binary tree traversal",
            "Create a function to check palindrome",
            "Write code to find maximum subarray sum",
            "Implement a hash table from scratch",
            "Write a function to rotate a matrix 90 degrees",
            "Implement depth-first search",
            "Create a function to validate parentheses",
            "Write a binary search tree implementation",
            "Implement merge sort algorithm",
        ],
        "debugging": [
            "Fix this bug: function returns wrong value for negative numbers",
            "Debug: why is this recursive function causing stack overflow?",
            "Find and fix the memory leak in this code",
            "Debug: why does this async code hang indefinitely?",
            "Fix: null pointer exception in production",
            "Debug this race condition in concurrent code",
            "Find the off-by-one error in this loop",
            "Debug why sorting is not working correctly",
        ],
        "reasoning": [
            "Explain why the sky is blue using physics",
            "Analyze the pros and cons of microservices architecture",
            "Compare and contrast SQL vs NoSQL databases",
            "Explain how neural networks learn",
            "Analyze the trolley problem in ethics",
            "Explain blockchain consensus mechanisms",
            "Compare centralized vs decentralized systems",
        ],
        "planning": [
            "Design a system for a ride-sharing app like Uber",
            "Plan a database schema for an e-commerce platform",
            "Design a scalable chat application architecture",
            "Plan a CI/CD pipeline for a microservices app",
            "Design a recommendation system",
            "Plan a serverless architecture for a web app",
        ],
    }

    # Get prompts for this task type
    prompts = templates.get(task_type, templates["coding"])

    # Filter out already used prompts
    available = [p for p in prompts if p not in _used_prompts]

    # If all used, reset and start over
    if not available:
        _used_prompts.clear()
        available = prompts

    # Pick random
    prompt = random.choice(available)
    _used_prompts.add(prompt)

    return prompt


