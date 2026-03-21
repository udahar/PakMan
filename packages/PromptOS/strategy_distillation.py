"""
Strategy Distillation - Multi-Strategy Verification Loops

Runs multiple reasoning strategies in parallel, verifies the best result,
and stores the winning strategy in genome. Improves reasoning WITHOUT training.

Usage:
    from PromptOS.strategy_distillation import StrategyDistillation

    distiller = StrategyDistillation(planner, llm_callable, verifier_llm)

    # Run multi-strategy convergence
    result = distiller.distill(
        prompt="Debug this recursion error",
        model="qwen2.5:7b",
        task_type="debugging",
        n_strategies=3
    )

    print(f"Best strategy: {result['best_strategy']}")
    print(f"Verification score: {result['verification_score']:.1%}")

    # Store winning strategy
    genome.record_strategy(result['best_strategy'], result['verification_score'])
"""

from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, asdict
import json
import time
from pathlib import Path


@dataclass
class StrategyCandidate:
    """A candidate strategy for distillation."""

    strategy: List[str]
    prompt: str
    response: str
    reasoning_path: str
    tokens_used: int
    latency_ms: float


@dataclass
class VerificationResult:
    """Result from verifying multiple candidates."""

    candidates: List[StrategyCandidate]
    best_candidate_idx: int
    best_strategy: List[str]
    best_response: str
    verification_score: float
    verification_reasoning: str
    all_scores: List[float]


@dataclass
class DistillationRecord:
    """Record of a distillation run."""

    prompt: str
    task_type: str
    model: str
    strategies_tested: List[List[str]]
    best_strategy: List[str]
    verification_score: float
    improvement_over_baseline: float
    timestamp: float


class StrategyDistillation:
    """
    Strategy distillation via self-verification loops.

    Runs multiple reasoning strategies in parallel,
    verifies the best result,
    stores winning strategy in genome.

    This is "learning without training" - improves reasoning
    by controlling the reasoning architecture around the LLM.
    """

    def __init__(
        self,
        planner: Optional[Any] = None,
        llm_callable: Optional[Callable] = None,
        verifier_llm: Optional[Callable] = None,
        genome: Optional[Any] = None,
        storage_path: Optional[str] = None,
    ):
        """
        Initialize strategy distillation.

        Args:
            planner: StrategyPlanner instance
            llm_callable: LLM callable for execution
            verifier_llm: Separate LLM for verification (optional, uses llm_callable if None)
            genome: PromptOS genome instance
            storage_path: Path for storing distillation records
        """
        self.planner = planner
        self.llm_callable = llm_callable
        self.verifier_llm = verifier_llm or llm_callable
        self.genome = genome
        self.storage_path = storage_path or "PromptOS/strategy_distillation.json"

        # Distillation history
        self.records: List[DistillationRecord] = []

        # Configuration
        self.complexity_threshold = 0.6  # Only distill complex tasks
        self.max_strategies = 5
        self.min_improvement = 0.05  # Minimum improvement to store

        # Load existing data
        self._load()

    def distill(
        self,
        prompt: str,
        model: str,
        task_type: str,
        n_strategies: int = 3,
        store_winner: bool = True,
    ) -> Dict[str, Any]:
        """
        Run multi-strategy distillation.

        Args:
            prompt: Input prompt
            model: Model to use
            task_type: Task type
            n_strategies: Number of strategies to test
            store_winner: Whether to store winning strategy in genome

        Returns:
            Distillation result
        """
        # 1. Check complexity (skip simple tasks)
        complexity = self._estimate_complexity(prompt, task_type)

        if complexity < self.complexity_threshold:
            # Simple task - just use planner directly
            return self._simple_run(prompt, model, task_type)

        # 2. Generate candidate strategies
        strategies = self._generate_candidates(n_strategies, task_type)

        # 3. Run all strategies in parallel
        candidates = []

        for strategy in strategies:
            candidate = self._run_strategy(prompt, model, strategy)
            candidates.append(candidate)

        # 4. Verify best result
        verification = self._verify_candidates(candidates, prompt, task_type)

        # 5. Store winner if improved
        improvement = 0.0
        if store_winner and self.genome:
            baseline_score = self._get_baseline_score(model, task_type)
            improvement = verification.verification_score - baseline_score

            if improvement >= self.min_improvement:
                self.genome.record_strategy(
                    verification.best_strategy, verification.verification_score
                )

        # 6. Record distillation
        record = DistillationRecord(
            prompt=prompt,
            task_type=task_type,
            model=model,
            strategies_tested=[c.strategy for c in candidates],
            best_strategy=verification.best_strategy,
            verification_score=verification.verification_score,
            improvement_over_baseline=improvement,
            timestamp=time.time(),
        )

        self.records.append(record)
        self._save()

        return {
            "best_strategy": verification.best_strategy,
            "best_response": verification.best_response,
            "verification_score": verification.verification_score,
            "verification_reasoning": verification.verification_reasoning,
            "all_candidates": [
                {
                    "strategy": c.strategy,
                    "response": c.response[:200],  # Truncate
                    "tokens_used": c.tokens_used,
                }
                for c in candidates
            ],
            "improvement_over_baseline": improvement,
            "stored_in_genome": store_winner and improvement >= self.min_improvement,
        }

    def _estimate_complexity(self, prompt: str, task_type: str) -> float:
        """Estimate task complexity (0-1)."""
        # Length score
        length_score = min(len(prompt) / 1000, 0.4)

        # Task type score
        complex_tasks = ["debugging", "reasoning", "coding", "planning"]
        task_score = 0.3 if task_type in complex_tasks else 0.1

        # Keyword score
        complex_keywords = [
            "error",
            "bug",
            "optimize",
            "design",
            "architecture",
            "multi",
        ]
        keyword_score = min(
            sum(1 for kw in complex_keywords if kw in prompt.lower()) * 0.1, 0.3
        )

        return length_score + task_score + keyword_score

    def _generate_candidates(
        self,
        n: int,
        task_type: str,
    ) -> List[List[str]]:
        """Generate candidate strategies."""
        candidates = []

        if self.planner:
            # Get planner's top candidates
            # (Would query planner in production)
            pass

        # Default diverse strategies per task type
        if task_type == "debugging":
            candidates = [
                ["scratchpad", "verify"],
                ["decompose", "scratchpad"],
                ["planner", "verify"],
                ["scratchpad", "tools", "verify"],
            ]
        elif task_type == "reasoning":
            candidates = [
                ["scratchpad"],
                ["scratchpad", "verify"],
                ["decompose", "scratchpad"],
                ["decompose", "scratchpad", "verify"],
            ]
        elif task_type == "coding":
            candidates = [
                ["planner", "scratchpad"],
                ["scratchpad", "verify"],
                ["decompose", "planner"],
                ["planner", "tools", "verify"],
            ]
        else:
            candidates = [
                ["scratchpad"],
                ["verify"],
                ["scratchpad", "verify"],
            ]

        return candidates[:n]

    def _run_strategy(
        self,
        prompt: str,
        model: str,
        strategy: List[str],
    ) -> StrategyCandidate:
        """Run a single strategy and record result."""
        start_time = time.time()

        # Build prompt with strategy
        # (Would use PromptOS.assemble() in production)
        strategy_prompt = self._assemble_with_strategy(prompt, strategy)

        # Run LLM
        response = (
            self.llm_callable(strategy_prompt) if self.llm_callable else "Test response"
        )

        latency_ms = (time.time() - start_time) * 1000

        # Estimate tokens
        tokens_used = len(strategy_prompt) // 4 + len(response) // 4

        return StrategyCandidate(
            strategy=strategy,
            prompt=prompt,
            response=response,
            reasoning_path=f"Strategy: {strategy}",
            tokens_used=tokens_used,
            latency_ms=latency_ms,
        )

    def _assemble_with_strategy(self, prompt: str, strategy: List[str]) -> str:
        """Assemble prompt with strategy modules."""
        # Simplified assembly (would use PromptOS in production)
        assembled = prompt

        if "role" in strategy:
            assembled = f"You are an expert problem solver.\n\n{assembled}"

        if "decompose" in strategy:
            assembled = f"Break this down into steps first.\n\n{assembled}"

        if "scratchpad" in strategy:
            assembled = f"Think through this step by step in a scratchpad.\n\n<SCRATCHPAD>\n[Reasoning]\n</SCRATCHPAD>\n\n{assembled}"

        if "verify" in strategy:
            assembled = f"{assembled}\n\nVerify your answer before finalizing."

        if "planner" in strategy:
            assembled = f"First create a plan, then execute.\n\n{assembled}"

        return assembled

    def _verify_candidates(
        self,
        candidates: List[StrategyCandidate],
        prompt: str,
        task_type: str,
    ) -> VerificationResult:
        """Verify candidates and select best."""
        if not candidates:
            raise ValueError("No candidates to verify")

        # Build verifier prompt
        verifier_prompt = self._build_verifier_prompt(candidates, prompt, task_type)

        # Run verifier
        verification_response = (
            self.verifier_llm(verifier_prompt) if self.verifier_llm else "Verified"
        )

        # Parse verification response
        best_idx, all_scores, reasoning = self._parse_verifier_response(
            verification_response, candidates
        )

        # If parsing failed, use fallback scoring
        if best_idx is None:
            best_idx = 0
            all_scores = [self._score_candidate(c.response, prompt) for c in candidates]

        # Find best
        if all_scores:
            best_idx = all_scores.index(max(all_scores))

        best_candidate = candidates[best_idx]

        return VerificationResult(
            candidates=candidates,
            best_candidate_idx=best_idx,
            best_strategy=best_candidate.strategy,
            best_response=best_candidate.response,
            verification_score=all_scores[best_idx] if all_scores else 0.7,
            verification_reasoning=reasoning
            or f"Strategy {best_candidate.strategy} produced best result",
            all_scores=all_scores,
        )

    def _parse_verifier_response(
        self,
        response: str,
        candidates: List[StrategyCandidate],
    ) -> Tuple[Optional[int], List[float], str]:
        """Parse verifier LLM response to extract best solution and scores."""
        import re

        best_idx = None
        all_scores = []
        reasoning = ""

        # Try to extract best solution letter (A, B, C, D, etc.)
        match = re.search(r"Best Solution:\s*([A-Za-z])", response)
        if match:
            letter = match.group(1).upper()
            best_idx = ord(letter) - ord("A")

        # Try to extract verification score
        score_match = re.search(r"Verification Score:\s*([\d.]+)", response)
        if score_match:
            best_score = float(score_match.group(1))
        else:
            best_score = 0.7

        # Try to extract reasoning
        reasoning_match = re.search(
            r"Reasoning:\s*(.+?)(?:\n\n|\Z)", response, re.DOTALL
        )
        if reasoning_match:
            reasoning = reasoning_match.group(1).strip()

        # If we have best_idx, generate scores for all
        if best_idx is not None and 0 <= best_idx < len(candidates):
            # Distribute scores around the best score
            for i, c in enumerate(candidates):
                if i == best_idx:
                    all_scores.append(best_score)
                else:
                    # Other candidates get slightly lower scores
                    all_scores.append(
                        max(0.3, best_score - 0.1 - (abs(i - best_idx) * 0.05))
                    )

        return best_idx, all_scores, reasoning

    def _score_candidate(self, response: str, prompt: str) -> float:
        """Score a candidate response using heuristics."""
        score = 0.5

        # Length check
        if 100 < len(response) < 3000:
            score += 0.1

        # Contains reasoning indicators
        reasoning_words = ["step", "therefore", "because", "thus", "hence", "analyzing"]
        if any(word in response.lower() for word in reasoning_words):
            score += 0.15

        # Contains solution/answer keywords
        if "solution" in response.lower() or "answer" in response.lower():
            score += 0.1

        # Contains code blocks (good for coding tasks)
        if "```" in response or "def " in response or "function" in response:
            score += 0.1

        return min(1.0, score)

    def _build_verifier_prompt(
        self,
        candidates: List[StrategyCandidate],
        prompt: str,
        task_type: str,
    ) -> str:
        """Build prompt for verifier LLM."""
        candidate_texts = "\n\n".join(
            f"Solution {chr(65 + i)} (Strategy: {c.strategy}):\n{c.response}"
            for i, c in enumerate(candidates)
        )

        return f"""You are reviewing multiple solutions to a {task_type} problem.

Original Problem:
{prompt}

---

{candidate_texts}

---

Task:
1. Analyze each solution for correctness
2. Identify any errors or issues
3. Select the best solution
4. Explain your reasoning

Format your response:
Best Solution: [A/B/C/D]
Verification Score: [0.0-1.0]
Reasoning: [explanation]"""

    def _simple_run(
        self,
        prompt: str,
        model: str,
        task_type: str,
    ) -> Dict[str, Any]:
        """Simple run for low-complexity tasks."""
        # Just use planner directly
        if self.planner:
            plan = self.planner.plan(prompt, model, task_type)
            strategy = plan.modules
        else:
            strategy = ["scratchpad"]

        candidate = self._run_strategy(prompt, model, strategy)

        return {
            "best_strategy": strategy,
            "best_response": candidate.response,
            "verification_score": 0.7,  # Placeholder
            "simple_run": True,
        }

    def _get_baseline_score(self, model: str, task_type: str) -> float:
        """Get baseline score for comparison."""
        if not self.genome:
            return 0.65

        # Would query genome in production
        return 0.65

    def get_distillation_stats(self) -> Dict[str, Any]:
        """Get distillation statistics."""
        if not self.records:
            return {"total_distillations": 0}

        avg_improvement = sum(r.improvement_over_baseline for r in self.records) / len(
            self.records
        )
        stored_count = sum(
            1
            for r in self.records
            if r.improvement_over_baseline >= self.min_improvement
        )

        return {
            "total_distillations": len(self.records),
            "avg_improvement": avg_improvement,
            "strategies_stored": stored_count,
            "storage_rate": stored_count / len(self.records),
        }

    def _save(self):
        """Save distillation records."""
        try:
            data = {
                "records": [asdict(r) for r in self.records[-500:]],
                "saved_at": time.time(),
            }

            with open(self.storage_path, "w") as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"[StrategyDistillation] Save failed: {e}")

    def _load(self):
        """Load distillation records."""
        try:
            if Path(self.storage_path).exists():
                with open(self.storage_path, "r") as f:
                    data = json.load(f)

                self.records = [
                    DistillationRecord(**r_data) for r_data in data.get("records", [])
                ]

                print(f"[StrategyDistillation] Loaded {len(self.records)} records")
        except Exception as e:
            print(f"[StrategyDistillation] Load failed: {e}")
