#!/usr/bin/env python3
# Updated-On: 2026-03-07
# Updated-By: Codex
# PM-Ticket: UNTRACKED
#
"""
Continuous Learning Runner

Runs forever, teaching models to teach each other.
Uses self-discovery, A/B testing, and adversarial testing.
"""

import sys
import time
import json
import os
import random
import shlex
import shutil
import subprocess
import psycopg2
import requests
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# Force PromptOS/PromptForge runtime persistence to DB/Qdrant only.
os.environ.setdefault("PROMPTOS_DB_ONLY", "1")
os.environ.setdefault("PROMPTFORGE_DB_ONLY", "1")

from PromptForge import create_bridge, OllamaClient
from PromptForge.ollama_integration import OllamaHTTPError
from PromptOS.storage import PostgresStorage
from provider_resilience import (
    ProviderCallError,
    ProviderFallbackRouter,
)

try:
    from Benchmark.backend.runner_maintenance import (
        is_embedding_model as benchmark_is_embedding_model,
    )
except Exception:
    benchmark_is_embedding_model = None

# Initialize PostgreSQL storage
print("Connecting to PostgreSQL...")
pg_storage = PostgresStorage()
pg_storage.connect()
print("PostgreSQL connected!")


# ========== STRATEGY MUTATION ENGINE ==========
AVAILABLE_MODULES = [
    "role",
    "decompose",
    "scratchpad",
    "tools",
    "verify",
    "format",
    "planner",
    "few_shot",
    "constraints",
    "chain",
    "branch",
]


def mutate_strategy(strategy: list, mutation_rate: float = 0.4) -> list:
    """Mutate a strategy to create new variations."""
    if not strategy:
        strategy = ["scratchpad"]

    mutated = strategy.copy()

    # Mutation types:
    # 1. Add module (40%)
    if random.random() < mutation_rate:
        available = [m for m in AVAILABLE_MODULES if m not in mutated]
        if available:
            mutated.append(random.choice(available))

    # 2. Remove module (20%)
    if random.random() < mutation_rate * 0.5 and len(mutated) > 1:
        to_remove = random.choice(mutated)
        mutated.remove(to_remove)

    # 3. Swap module (20%)
    if random.random() < mutation_rate * 0.5 and len(mutated) > 0:
        idx = random.randint(0, len(mutated) - 1)
        available = [m for m in AVAILABLE_MODULES if m not in mutated]
        if available:
            mutated[idx] = random.choice(available)

    # 4. Reorder (20%)
    if random.random() < mutation_rate * 0.5 and len(mutated) > 1:
        random.shuffle(mutated)

    return list(set(mutated))  # Dedup


def generate_strategy_variations(base_strategy: list, n: int = 4) -> list:
    """Generate n variations of a base strategy."""
    variations = [base_strategy]  # Keep original

    for _ in range(n - 1):
        variation = mutate_strategy(base_strategy)
        if variation not in variations:
            variations.append(variation)

    return variations[:n]


# ========== LLM JUDGE SCORING ==========
_ollama_client = None


def _resolve_ollama_llm_url() -> str:
    """Resolve preferred Ollama LLM lane URL (default: port 11437 / lane 7)."""
    return (
        os.getenv("PROMPTFORGE_OLLAMA_LLM_URL")
        or os.getenv("OLLAMA_LLM_URL")
        or "http://127.0.0.1:11437"
    ).rstrip("/")


def _build_ollama_client(timeout: int = 300, raise_http_errors: bool = False):
    """Create Ollama client on preferred lane, with optional fallback lane."""
    preferred = _resolve_ollama_llm_url()
    fallback = (
        os.getenv("PROMPTFORGE_OLLAMA_LLM_FALLBACK_URL") or "http://127.0.0.1:11434"
    ).rstrip("/")

    client = OllamaClient(
        base_url=preferred,
        timeout=timeout,
        raise_http_errors=raise_http_errors,
    )
    try:
        models = client.list_models()
        if models:
            return client
        if fallback and fallback != preferred:
            fb_client = OllamaClient(
                base_url=fallback,
                timeout=timeout,
                raise_http_errors=raise_http_errors,
            )
            if fb_client.list_models():
                return fb_client
        return client
    except Exception:
        if fallback and fallback != preferred:
            return OllamaClient(
                base_url=fallback,
                timeout=timeout,
                raise_http_errors=raise_http_errors,
            )
        return client


def get_judge_client():
    """Get LLM client for judging."""
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = _build_ollama_client(timeout=120)
    return _ollama_client


def llm_judge_score(response: str, prompt: str, task_type: str) -> float:
    """
    Use LLM as unbiased judge to score response.

    The key is to NOT tell the judge what strategy was used - only evaluate quality.
    """
    judge_prompt = f"""You are an expert evaluator. Score this response objectively.

Task Type: {task_type}
Original Prompt: {prompt}

Response to evaluate:
{response[:1500]}

Evaluate on a scale of 0.0 to 1.0:
- 0.0-0.3: Poor - wrong, incomplete, or nonsensical
- 0.4-0.6: Fair - partially correct but missing key elements  
- 0.7-0.8: Good - correct and complete
- 0.9-1.0: Excellent - thorough, well-reasoned, exceeds expectations

Respond ONLY with a number between 0.0 and 1.0. No explanation."""

    try:
        judge = get_judge_client()
        # Use a small fast model as judge
        score_str = judge.generate("qwen2.5:1.5b", judge_prompt)

        # Parse score from response
        import re

        match = re.search(r"0?\.\d+", score_str)
        if match:
            score = float(match.group())
            return min(1.0, max(0.0, score))
    except Exception as e:
        print(f"[Judge Error]: {e}")

    return 0.5  # Fallback


def efficiency_score(raw_score: float, tokens_used: int) -> float:
    """
    Calculate efficiency-adjusted score.

    Rewards high quality with low token usage.
    """
    if tokens_used == 0:
        return raw_score

    # Token efficiency: bonus for getting good scores with fewer tokens
    # Penalty for high tokens with low scores
    token_bonus = min(0.1, 1000 / max(tokens_used, 100))

    if raw_score >= 0.7:
        return raw_score + token_bonus
    elif raw_score >= 0.5:
        return raw_score
    else:
        return raw_score - token_bonus * 0.5


def bench_score(
    response, prompt, task_type="coding", tokens_used=0, use_llm_judge=False
):
    """
    Scoring callback with multiple strategies.

    Args:
        response: Model response (or None for connection failure)
        prompt: Original prompt
        task_type: Type of task
        tokens_used: Token count for efficiency scoring
        use_llm_judge: Whether to use LLM judge (slower but more accurate)

    Returns:
        float: Score 0.0-1.0, or -1 to signal "skip recording" (connection failure)
    """
    # Handle connection failure - return -1 to signal skip recording
    if response is None:
        return -1

    # Handle empty responses
    if not response:
        return -1

    # Option 1: LLM Judge (more accurate, slower)
    if use_llm_judge:
        return llm_judge_score(response, prompt, task_type)

    # Option 2: Heuristic scoring (fast)
    score = 0.5

    # Length check - responses should have substance
    if 100 < len(response) < 3000:
        score += 0.1
    elif len(response) >= 3000:
        score += 0.05

    # Reasoning indicators
    reasoning_words = [
        "step",
        "therefore",
        "because",
        "thus",
        "hence",
        "analyzing",
        "first",
        "then",
    ]
    if any(word in response.lower() for word in reasoning_words):
        score += 0.15

    # Solution indicators
    if "answer" in response.lower() or "solution" in response.lower():
        score += 0.1

    # Code blocks (for coding tasks)
    if "```" in response or "def " in response or "function" in response:
        score += 0.1

    # Task-specific checks
    if task_type == "coding":
        if "return " in response or "def " in response:
            score += 0.05
    elif task_type == "debugging":
        if "error" in response.lower() or "fix" in response.lower():
            score += 0.1
    elif task_type == "reasoning":
        if "explain" in response.lower() or "because" in response.lower():
            score += 0.1

    # Apply efficiency adjustment
    if tokens_used > 0:
        score = efficiency_score(score, tokens_used)

    return min(1.0, max(0.0, score))


# Good models - includes small/fast models for testing
GOOD_MODELS = [
    "qwen2.5:3b-instruct",
    "qwen2.5:1.5b",
    "qwen2.5-coder:1.5b",
    "qwen3.5:2b",
    "smollm:360m",  # Tiny model - tests if small can learn!
    "smollm:1.7b",
    "phi3:3.8b",
    "llama3:8b",
    "aya-expanse:8b",
]


# ========== PROMPT + TASK FRAMEWORK MUTATION ==========


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


def get_llm():
    """Get LLM callable with provider-level fallback/circuit-breaker resilience."""
    client = _build_ollama_client(raise_http_errors=True)
    fallback_url = (
        os.getenv("PROMPTFORGE_OLLAMA_LLM_FALLBACK_URL") or "http://127.0.0.1:11434"
    ).rstrip("/")
    fallback_client = None
    if fallback_url and fallback_url != client.base_url:
        fallback_client = OllamaClient(base_url=fallback_url, raise_http_errors=True)
    known_ollama_models = {m.name for m in client.list_models()}
    default_ollama_model = (
        next(iter(known_ollama_models), None)
        or os.getenv("PROMPTFORGE_OLLAMA_FALLBACK_MODEL", "qwen2.5:3b-instruct")
    )

    breaker_timeout = int(os.getenv("PROMPTFORGE_PROVIDER_BREAKER_TIMEOUT_SECONDS", "300"))
    router = ProviderFallbackRouter(timeout_seconds=breaker_timeout)

    def infer_provider(model_name: str) -> str:
        lower = str(model_name or "").lower()
        if lower.startswith("cerebras:") or "gpt-oss" in lower:
            return "cerebras"
        if lower.startswith("qwen-cli:") or lower.startswith("qwencli:"):
            return "qwen-cli"
        if lower.startswith("openai:"):
            return "openai"
        if lower.startswith(("gpt-", "o1", "o3", "o4")):
            return "openai"
        return "ollama"

    def strip_prefix(name: str, prefix: str) -> str:
        if str(name or "").lower().startswith(prefix.lower()):
            return name[len(prefix):]
        return name

    def openai_model_for(requested_model: str) -> str:
        clean = strip_prefix(requested_model, "openai:")
        if clean.startswith(("gpt-", "o1", "o3", "o4")):
            return clean
        return os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def cerebras_model_for(requested_model: str) -> str:
        clean = strip_prefix(requested_model, "cerebras:")
        if clean and clean != requested_model:
            return clean
        return os.getenv("CEREBRAS_MODEL", "gpt-oss-120b")

    def ollama_model_for(requested_model: str) -> str:
        if requested_model in known_ollama_models:
            return requested_model
        clean = strip_prefix(requested_model, "ollama:")
        if clean in known_ollama_models:
            return clean
        return default_ollama_model

    def call_ollama(prompt: str, requested_model: str) -> str:
        use_model = ollama_model_for(requested_model)
        if not use_model:
            raise ProviderCallError("ollama", None, "no_ollama_model_available")
        num_predict = int(os.getenv("PROMPTFORGE_OLLAMA_NUM_PREDICT", "256"))
        gen_options = {"num_predict": num_predict}
        try:
            response = client.generate(use_model, prompt, options=gen_options)
            if response:
                return response
            model_lower = str(use_model or "").lower()
            if ("cloud" in model_lower) or ("chat" in model_lower):
                response = client.chat(
                    model=use_model,
                    messages=[{"role": "user", "content": prompt}],
                    options=gen_options,
                )
                if response:
                    return response
            if fallback_client is not None:
                response = fallback_client.generate(use_model, prompt, options=gen_options)
                if response:
                    return response
            raise ProviderCallError("ollama", None, "empty_response")
        except OllamaHTTPError as e:
            raise ProviderCallError("ollama", e.status_code, e.message) from e
        except ProviderCallError:
            raise
        except Exception as e:
            msg = str(e)
            if "timeout" in msg.lower():
                raise ProviderCallError("ollama", None, f"timeout: {msg}") from e
            raise ProviderCallError("ollama", None, msg) from e

    def call_cerebras(prompt: str, requested_model: str) -> str:
        api_key = os.getenv("CEREBRAS_API_KEY", "").strip()
        if not api_key:
            raise ProviderCallError("cerebras", None, "missing_cerebras_api_key")

        base_url = os.getenv("CEREBRAS_BASE_URL", "https://api.cerebras.ai/v1").rstrip("/")
        payload = {
            "model": cerebras_model_for(requested_model),
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        timeout = int(os.getenv("CEREBRAS_TIMEOUT", "120"))
        try:
            r = requests.post(
                f"{base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=timeout,
            )
            if r.status_code == 429:
                raise ProviderCallError("cerebras", 429, "rate_limited")
            r.raise_for_status()
            text = r.json().get("choices", [{}])[0].get("message", {}).get("content", "")
            if not text:
                raise ProviderCallError("cerebras", None, "empty_response")
            return text
        except ProviderCallError:
            raise
        except requests.exceptions.Timeout as e:
            raise ProviderCallError("cerebras", None, f"timeout: {e}") from e
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if getattr(e, "response", None) else None
            raise ProviderCallError("cerebras", status, str(e)) from e
        except requests.exceptions.RequestException as e:
            raise ProviderCallError("cerebras", None, str(e)) from e

    def call_openai(prompt: str, requested_model: str) -> str:
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise ProviderCallError("openai", None, "missing_openai_api_key")

        base_url = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1").rstrip("/")
        payload = {
            "model": openai_model_for(requested_model),
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        }
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        timeout = int(os.getenv("OPENAI_TIMEOUT", "120"))
        try:
            r = requests.post(
                f"{base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=timeout,
            )
            if r.status_code == 429:
                raise ProviderCallError("openai", 429, "rate_limited")
            r.raise_for_status()
            text = r.json().get("choices", [{}])[0].get("message", {}).get("content", "")
            if not text:
                raise ProviderCallError("openai", None, "empty_response")
            return text
        except ProviderCallError:
            raise
        except requests.exceptions.Timeout as e:
            raise ProviderCallError("openai", None, f"timeout: {e}") from e
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if getattr(e, "response", None) else None
            raise ProviderCallError("openai", status, str(e)) from e
        except requests.exceptions.RequestException as e:
            raise ProviderCallError("openai", None, str(e)) from e

    def call_qwen_cli(prompt: str, requested_model: str) -> str:
        del requested_model
        cmd = os.getenv("QWEN_CLI_COMMAND", "qwen").strip()
        cmd_path = shutil.which(cmd) if cmd else None
        if not cmd_path:
            raise ProviderCallError("qwen-cli", None, "qwen_cli_not_found")

        args = shlex.split(os.getenv("QWEN_CLI_ARGS", ""))
        prompt_flag = os.getenv("QWEN_CLI_PROMPT_FLAG", "--prompt").strip()
        command = [cmd_path] + args
        if prompt_flag:
            command += [prompt_flag, prompt]
        else:
            command += [prompt]

        timeout = int(os.getenv("QWEN_CLI_TIMEOUT", "120"))
        try:
            res = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            if res.returncode != 0:
                err = (res.stderr or res.stdout or "").strip()
                err_lower = err.lower()
                if "429" in err_lower or "rate limit" in err_lower:
                    raise ProviderCallError("qwen-cli", 429, err or "rate_limited")
                raise ProviderCallError("qwen-cli", None, err or f"exit_{res.returncode}")
            text = (res.stdout or "").strip()
            if not text:
                raise ProviderCallError("qwen-cli", None, "empty_response")
            return text
        except ProviderCallError:
            raise
        except subprocess.TimeoutExpired as e:
            raise ProviderCallError("qwen-cli", None, f"timeout: {e}") from e
        except Exception as e:
            raise ProviderCallError("qwen-cli", None, str(e)) from e

    router.register("ollama", call_ollama)
    router.register("cerebras", call_cerebras)
    router.register("openai", call_openai)
    router.register("qwen-cli", call_qwen_cli)

    print(f"[Provider Router] Enabled vendor fallback; breaker timeout={breaker_timeout}s")

    def llm(prompt, model="qwen2.5:3b-instruct", **kwargs):
        del kwargs
        primary_provider = infer_provider(model)
        try:
            result = router.call(primary_provider, prompt, requested_model=model)
            if result.fallback_used:
                print(
                    f"[Provider Fallback] requested={primary_provider} "
                    f"served_by={result.provider} attempts={result.attempts}"
                )
            return result.response
        except ProviderCallError as e:
            print(f"[LLM Error]: {e}")
            error_msg = str(e).lower()
            if "timeout" in error_msg:
                raise
            return None

    return llm, client


def _is_embedding_model_name(model_name: str) -> bool:
    if benchmark_is_embedding_model is not None:
        try:
            return bool(
                benchmark_is_embedding_model(
                    model_name,
                    get_db_fn=lambda: psycopg2.connect(pg_storage.postgres_url),
                )
            )
        except Exception:
            pass

    name = str(model_name or "").lower()
    patterns = [
        "embed",
        "-embedding",
        "bge-",
        "minilm",
        "snowflake-arctic-embed",
        "mxbai-embed",
        "embeddinggemma",
        "nomic-embed",
    ]
    return any(pattern in name for pattern in patterns)


def _get_generation_models(client) -> list:
    """Get generation-capable models, preferring bm_models metadata from PostgreSQL."""
    all_models = client.list_models()
    ollama_names = [m.name for m in all_models]
    ollama_set = set(ollama_names)

    if getattr(pg_storage, "_cursor", None):
        try:
            pg_storage._cursor.execute(
                """
                SELECT model_name, tags
                FROM bm_models
                WHERE installed = true
                  AND COALESCE(status, 'ACTIVE') NOT IN ('DELETE', 'BANNED', 'MISSING')
                ORDER BY model_name
                """
            )
            rows = pg_storage._cursor.fetchall()
            db_filtered = []
            for model_name, tags in rows:
                tags_lower = {str(t).lower() for t in (tags or [])}
                if "embedding" in tags_lower:
                    continue
                if _is_embedding_model_name(model_name):
                    continue
                model_lower = str(model_name or "").lower()
                if model_name in ollama_set:
                    db_filtered.append(model_name)
                    continue
                if (
                    "cerebras" in tags_lower
                    or "openai" in tags_lower
                    or "qwen-cli" in tags_lower
                    or "qwen_cli" in tags_lower
                    or model_lower.startswith(("cerebras:", "openai:", "qwen-cli:", "qwencli:"))
                    or model_lower.startswith(("gpt-", "o1", "o3", "o4"))
                ):
                    db_filtered.append(model_name)

            if db_filtered:
                return db_filtered
        except Exception as e:
            print(f"[Model Filter] DB metadata query failed, using local fallback: {e}")

    # Fallback when DB is unavailable: local model-name heuristics.
    return [name for name in ollama_names if not _is_embedding_model_name(name)]


def run_adversarial_test(bridge, prompt: str, models: list, task_type: str) -> dict:
    """Run adversarial test - models compete on same prompt."""
    print(f"\n>>> ADVERSARIAL: {len(models)} models competing")

    results = []
    for model in models:
        print(f"   Testing {model}...")
        try:
            response = bridge.promptos.run(prompt, model=model)
            score = bench_score(response, prompt)
            # Skip connection failures
            if score == -1:
                print(f"   {model}: ⚠️  Connection failed - skipping")
                continue
            results.append(
                {
                    "model": model,
                    "response": response,
                    "score": score,
                    "strategy": bridge.promptos.last_modules,
                }
            )
            print(f"   {model}: {score:.2f}")
        except Exception as e:
            print(f"   {model}: ERROR - {e}")

    if not results:
        return {}

    # Find winner
    winner = max(results, key=lambda x: x["score"])
    print(f"   WINNER: {winner['model']} ({winner['score']:.2f})")

    # Record winner to genome
    is_success = winner["score"] >= 0.7
    bridge.promptos.genome.record(
        model=winner["model"],
        task_type=task_type,
        strategy=winner["strategy"],
        score=winner["score"],
        success=is_success,
        status="success" if is_success else "failure",
    )

    return {
        "winner": winner,
        "all_results": results,
    }


def run_continuous_learning(hours=2, model=None):
    """Run continuous learning for specified hours."""

    print("=" * 60)
    print("CONTINUOUS LEARNING RUNNER")
    print("=" * 60)
    print(f"Duration: {hours} hours")
    print()

    # Setup
    llm, client = get_llm()

    # Get generation-capable models, using Postgres bm_models tags when available.
    available = _get_generation_models(client)

    # Add our known good models
    for m in GOOD_MODELS:
        if m not in available:
            available.append(m)

    print(f"Available models: {available[:8]}...")

    if model and model not in available:
        print(f"[Model Filter] Requested model '{model}' is not generation-eligible; ignoring.")
        model = None

    timeout_strike_limit = int(os.getenv("PROMPTFORGE_TIMEOUT_STRIKE_LIMIT", "3"))
    timeout_strikes = {m: 0 for m in available}
    timeout_quarantine = {m: False for m in available}

    def choose_model(preferred: str = None) -> str:
        if not available:
            return "qwen2.5:3b-instruct"

        active = [m for m in available if not timeout_quarantine.get(m, False)]
        candidate_pool = active[:10] if active else []
        if preferred and preferred in candidate_pool:
            return preferred
        if candidate_pool:
            return random.choice(candidate_pool)

        # All lanes are quarantined; release one for probation call.
        quarantined = [m for m in available if timeout_quarantine.get(m, False)]
        if quarantined:
            probation = random.choice(quarantined[:10])
            timeout_quarantine[probation] = False
            print(f"[Timeout Scheduler] Releasing '{probation}' for probation retry.")
            return probation

        return preferred or random.choice(available[:10])

    def register_timeout(model_name: str) -> None:
        timeout_strikes[model_name] = timeout_strikes.get(model_name, 0) + 1
        strikes = timeout_strikes[model_name]
        if strikes >= timeout_strike_limit:
            timeout_quarantine[model_name] = True
            print(
                "[Timeout Scheduler] "
                f"'{model_name}' reached {strikes} timeout strikes; quarantined."
            )
        else:
            print(
                "[Timeout Scheduler] "
                f"'{model_name}' timeout strike {strikes}/{timeout_strike_limit}."
            )

    def clear_timeout_state(model_name: str) -> None:
        prior = timeout_strikes.get(model_name, 0)
        was_quarantined = timeout_quarantine.get(model_name, False)
        timeout_strikes[model_name] = 0
        timeout_quarantine[model_name] = False
        if prior > 0 or was_quarantined:
            print(
                "[Timeout Scheduler] "
                f"'{model_name}' recovered; timeout strikes reset."
            )

    # Use provided model or pick random active model
    current_model = choose_model(preferred=model)
    print(f"Starting model: {current_model}")
    print()

    # Setup bridge. PromptOS now passes `model=` into the llm callable.
    bridge = create_bridge(
        llm,
        bench_score,
        cache_enabled=False,
    )

    start_time = time.time()
    end_time = start_time + (hours * 3600)
    iteration = 0

    print(f"Started at: {datetime.now()}")
    print(f"Will end at: {datetime.fromtimestamp(end_time)}")
    print()

    def record_iteration_outcome(
        *,
        iteration_id: int,
        model_name: str,
        task: str,
        strategy: list,
        score: float,
        success: bool,
    ) -> None:
        bridge.promptos.genome.record(
            model=model_name,
            task_type=task,
            strategy=strategy,
            score=score,
            success=success,
            status="success" if success else "failure",
        )
        pg_storage.save_genome_record(
            {
                "model": model_name,
                "task_type": task,
                "strategy": strategy,
                "avg_score": score,
                "trials": 1,
            }
        )
        pg_storage.save_evolution_record(
            {
                "model": model_name,
                "task_type": task,
                "strategy": strategy,
                "score": score,
                "success": success,
            }
        )
        bridge.promptos.record_ticket(
            ticket_id=f"iter_{iteration_id}",
            success=success,
            score=score,
            model=model_name,
            task_type=task,
        )

    while time.time() < end_time:
        iteration += 1

        # Periodically rotate models (every 10 iterations)
        if iteration % 10 == 0 and len(available) >= 2:
            current_model = choose_model()
            print(f"\n>>> Rotating to model: {current_model}")

        # Pick random task type and prompt
        task_type = random.choice(["coding", "debugging", "reasoning", "planning"])
        prompt = get_unique_prompt(task_type)

        print(f"\n--- Iteration {iteration} ---")
        print(f"Model: {current_model}")
        print(f"Task: {task_type}")
        print(f"Prompt: {prompt[:60]}...")

        try:
            # Get current best strategy for THIS model
            best_strategy = bridge.get_best_strategy(current_model, task_type)
            print(f"Strategy: {best_strategy}")

            # Run with current best
            response = bridge.promptos.run(
                prompt,
                model=current_model,
                modules=best_strategy,
            )

            # Score
            score = bench_score(response, prompt)

            # Skip recording if connection failed (score == -1)
            if score == -1:
                print("⚠️  Connection failed - skipping database recording")
                continue

            success = score >= 0.7
            clear_timeout_state(current_model)

            print(f"Score: {score:.2f}, Success: {success}")

            record_iteration_outcome(
                iteration_id=iteration,
                model_name=current_model,
                task=task_type,
                strategy=best_strategy,
                score=score,
                success=success,
            )

            # Every 5 iterations, run A/B test with mutated strategies
            if iteration % 5 == 0:
                print("\n>>> Running A/B test with mutations...")

                # Generate strategy variations using mutation engine
                base = best_strategy or ["scratchpad"]
                strategies = generate_strategy_variations(base, n=4)

                print(f"Testing strategies: {strategies}")

                result = bridge.run_and_learn(
                    prompt,
                    current_model,
                    strategies,
                    task_type=task_type,
                    n_runs=2,
                )

                winner = result.get("analysis", {}).get("winner", {})
                print(f"A/B Winner: {winner.get('strategy', 'none')}")

            # Every 10 iterations, run adversarial test (models compete)
            if iteration % 10 == 0 and len(available) >= 2:
                adversarial_models = random.sample(
                    available[:10], min(3, len(available[:10]))
                )
                run_adversarial_test(bridge, prompt, adversarial_models, task_type)

            # Every 15 iterations, run distillation
            if iteration % 15 == 0:
                print("\n>>> Running distillation pipeline...")

                result = bridge.run_distillation_pipeline(
                    task_type=task_type,
                    base_model=current_model,
                    test_prompts=[get_unique_prompt(task_type) for _ in range(3)],
                    min_score=0.7,
                )

                if result.get("success"):
                    print(f"Trained model: {result.get('trained_model')}")
                    print(f"Improvement: {result.get('improvement')}")

            # Print stats every 10 iterations
            if iteration % 10 == 0:
                stats = bridge.get_stats()
                print(f"\n>>> Stats: {json.dumps(stats['evolution_stats'], indent=2)}")

            # Save checkpoint
            if iteration % 5 == 0:
                print(f"\n[Checkpoint saved]")

        except Exception as e:
            print(f"Error: {e}")
            err_lower = str(e).lower()
            if "timeout" in err_lower:
                try:
                    print(
                        "⚠️  Timeout reached; recording model failure "
                        f"(model={current_model}, score=0.0)"
                    )
                    register_timeout(current_model)
                    record_iteration_outcome(
                        iteration_id=iteration,
                        model_name=current_model,
                        task=task_type,
                        strategy=best_strategy if isinstance(best_strategy, list) else ["scratchpad"],
                        score=0.0,
                        success=False,
                    )
                    if timeout_quarantine.get(current_model, False) and len(available) >= 2:
                        current_model = choose_model()
                        print(
                            "[Timeout Scheduler] "
                            f"Switching to next model: {current_model}"
                        )
                except Exception as persist_err:
                    print(f"[Record Error] Failed to persist timeout failure: {persist_err}")
            import traceback

            traceback.print_exc()

        # Small delay between iterations
        time.sleep(1)

    # Final stats
    print("\n" + "=" * 60)
    print("RUN COMPLETE")
    print("=" * 60)

    stats = bridge.get_stats()
    print(f"\nFinal stats:")
    print(f"  Total iterations: {iteration}")
    print(f"  Genome records: {stats['genome_records']}")
    print(f"  Evolution events: {stats['evolution_stats']['evolution_events']}")
    print(f"  A/B tests: {stats['sync_stats']['ab_tests_performed']}")
    print(f"  Distillations: {stats['sync_stats']['distillations_run']}")

    print("\nPersistence mode:")
    print("  - PromptOS/PromptForge JSON sidecar persistence: disabled")
    print("  - PostgreSQL tables: promptos_genome, promptos_evolution")
    print("  - Qdrant collection: promptforge_experiments")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Continuous learning runner")
    parser.add_argument("--hours", type=float, default=2, help="Hours to run")
    parser.add_argument(
        "--model", type=str, default=None, help="Model to use (default: random)"
    )

    args = parser.parse_args()

    run_continuous_learning(args.hours, args.model)
