import os
from .ollama_integration import OllamaClient

def _resolve_ollama_llm_url() -> str:
    return (os.getenv("PROMPTFORGE_OLLAMA_LLM_URL") or os.getenv("OLLAMA_LLM_URL") or "http://127.0.0.1:11437").rstrip("/")

def _build_ollama_client(timeout: int = 300, raise_http_errors: bool = False):
    preferred = _resolve_ollama_llm_url()
    fallback = (os.getenv("PROMPTFORGE_OLLAMA_LLM_FALLBACK_URL") or "http://127.0.0.1:11434").rstrip("/")
    client = OllamaClient(base_url=preferred, timeout=timeout, raise_http_errors=raise_http_errors)
    try:
        models = client.list_models()
        if models: return client
        if fallback and fallback != preferred:
            fb_client = OllamaClient(base_url=fallback, timeout=timeout, raise_http_errors=raise_http_errors)
            if fb_client.list_models(): return fb_client
        return client
    except Exception:
        if fallback and fallback != preferred:
            return OllamaClient(base_url=fallback, timeout=timeout, raise_http_errors=raise_http_errors)
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

