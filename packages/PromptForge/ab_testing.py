"""
A/B Testing Engine - Parallel Strategy Experimentation

Runs multiple strategies in parallel, determines statistical significance,
and identifies winners with confidence intervals.
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import statistics
import math


@dataclass
class ABTestResult:
    """Result from a single A/B test run."""

    strategy: List[str]
    response: str
    score: float
    tokens_used: int
    latency_ms: float
    success: bool
    timestamp: str


@dataclass
class ABTestReport:
    """Complete A/B test report with statistics."""

    prompt: str
    model: str
    task_type: str
    strategies_tested: int
    total_runs: int
    winner: Optional[Dict]
    analysis: Dict[str, Any]
    statistical_significance: float
    confidence_level: float
    timestamp: str


class ABTestingEngine:
    """
    A/B testing engine for strategy experimentation.

    Features:
    - Parallel execution
    - Statistical significance testing
    - Confidence intervals
    - Winner determination
    """

    def __init__(
        self,
        llm_callable: Optional[Callable] = None,
        bench_callback: Optional[Callable] = None,
    ):
        """
        Initialize A/B testing engine.

        Args:
            llm_callable: LLM callable function
            bench_callback: Bench scoring callback
        """
        self.llm_callable = llm_callable
        self.bench_callback = bench_callback

        # Test history
        self.tests: List[ABTestReport] = []

        # Statistical parameters
        self.confidence_level = 0.95
        self.min_runs = 3

    def ab_test(
        self,
        prompt: str,
        model: str,
        strategies: List[List[str]],
        task_type: Optional[str] = None,
        n_runs: int = 5,
        timeout_seconds: int = 60,
        parallel: bool = True,
    ) -> Dict[str, Any]:
        """
        Run A/B test of multiple strategies.

        Args:
            prompt: Test prompt
            model: Model to test with
            strategies: List of strategy combinations
            task_type: Task type
            n_runs: Number of runs per strategy
            timeout_seconds: Timeout per run
            parallel: Run tests in parallel

        Returns:
            Test results with statistical analysis
        """
        # Detect task type if not provided
        if task_type is None:
            task_type = self._detect_task_type(prompt)

        # Run tests
        all_results = []

        if parallel:
            # Run all tests in parallel
            all_results = self._run_parallel_tests(
                prompt=prompt,
                model=model,
                strategies=strategies,
                n_runs=n_runs,
                timeout_seconds=timeout_seconds,
            )
        else:
            # Sequential execution
            for strategy in strategies:
                strategy_results = []

                for i in range(n_runs):
                    result = self._run_single_test(
                        prompt=prompt,
                        model=model,
                        strategy=strategy,
                        timeout_seconds=timeout_seconds,
                    )
                    strategy_results.append(result)

                all_results.append(
                    {
                        "strategy": strategy,
                        "results": strategy_results,
                    }
                )

        # Analyze results
        analysis = self._analyze_results(all_results)

        # Determine winner
        winner = self._determine_winner(analysis)

        # Calculate statistical significance (real t-test)
        significance = self._calculate_significance(analysis)

        # Build report
        report = {
            "prompt": prompt,
            "model": model,
            "task_type": task_type,
            "strategies_tested": len(strategies),
            "total_runs": len(strategies) * n_runs,
            "winner": winner,
            "analysis": analysis,
            "statistical_significance": significance,
            "confidence_level": self.confidence_level,
            "timestamp": datetime.now().isoformat(),
            "results": all_results,
        }

        # Store test
        self.tests.append(report)

        return report

    def _run_parallel_tests(
        self,
        prompt: str,
        model: str,
        strategies: List[List[str]],
        n_runs: int,
        timeout_seconds: int,
    ) -> List[Dict]:
        """Run all tests in parallel using asyncio."""

        async def run_all():
            tasks = []

            for strategy in strategies:
                for i in range(n_runs):
                    task = asyncio.get_event_loop().run_in_executor(
                        None,
                        self._run_single_test,
                        prompt,
                        model,
                        strategy,
                        timeout_seconds,
                    )
                    tasks.append((strategy, task))

            # Run all tasks concurrently
            results = await asyncio.gather(
                *[t[1] for t in tasks], return_exceptions=True
            )

            # Group by strategy
            by_strategy = {}
            for i, (strategy, _) in enumerate(tasks):
                strategy_key = ",".join(sorted(strategy))
                if strategy_key not in by_strategy:
                    by_strategy[strategy_key] = []

                result = results[i]
                if isinstance(result, Exception):
                    # Handle exception
                    result = ABTestResult(
                        strategy=strategy,
                        response=f"Error: {str(result)}",
                        score=0.0,
                        tokens_used=0,
                        latency_ms=0,
                        success=False,
                        timestamp=datetime.now().isoformat(),
                    )

                by_strategy[strategy_key].append(result)

            return [
                {"strategy": by_strategy[strategy_key][0].strategy, "results": results}
                for strategy_key, results in by_strategy.items()
            ]

        # Run async event loop
        try:
            import nest_asyncio

            nest_asyncio.apply()
        except ImportError:
            pass

        # Use new asyncio.run() instead of deprecated get_event_loop()
        try:
            return asyncio.run(run_all())
        except RuntimeError:
            # Fallback for environments where asyncio.run is not available
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(run_all())
            finally:
                loop.close()

    def _run_single_test(
        self,
        prompt: str,
        model: str,
        strategy: List[str],
        timeout_seconds: int,
    ) -> ABTestResult:
        """Run a single test."""
        start_time = time.time()

        try:
            # Build prompt with strategy
            strategy_prompt = self._assemble_with_strategy(prompt, strategy)

            # Run LLM with timeout
            if self.llm_callable:
                response = self.llm_callable(strategy_prompt)
            else:
                response = "Test response"

            latency_ms = (time.time() - start_time) * 1000

            # Score response
            score = self._score_response(response, prompt)

            # Estimate tokens
            tokens_used = len(strategy_prompt) // 4 + len(response) // 4

            success = score >= 0.7

            return ABTestResult(
                strategy=strategy,
                response=response,
                score=score,
                tokens_used=tokens_used,
                latency_ms=latency_ms,
                success=success,
                timestamp=datetime.now().isoformat(),
            )

        except Exception as e:
            return ABTestResult(
                strategy=strategy,
                response=f"Error: {str(e)}",
                score=0.0,
                tokens_used=0,
                latency_ms=(time.time() - start_time) * 1000,
                success=False,
                timestamp=datetime.now().isoformat(),
            )

    def _assemble_with_strategy(self, prompt: str, strategy: List[str]) -> str:
        """Assemble prompt with strategy modules."""
        assembled = prompt

        if "role" in strategy:
            assembled = f"You are an expert problem solver.\n\n{assembled}"

        if "decompose" in strategy:
            assembled = f"Break this down into steps first.\n\n{assembled}"

        if "scratchpad" in strategy:
            assembled = f"Think through this step by step.\n\n<SCRATCHPAD>\n[Reasoning]\n</SCRATCHPAD>\n\n{assembled}"

        if "verify" in strategy:
            assembled = f"{assembled}\n\nVerify your answer before finalizing."

        if "planner" in strategy:
            assembled = f"First create a plan, then execute.\n\n{assembled}"

        return assembled

    def _score_response(self, response: str, prompt: str) -> float:
        """Score a response."""
        if self.bench_callback:
            return self.bench_callback(response, prompt)

        # Fallback: simple heuristics
        score = 0.5

        # Length bonus (not too short, not too long)
        if 100 < len(response) < 2000:
            score += 0.2

        # Contains reasoning indicators
        reasoning_words = ["step", "therefore", "because", "thus", "hence"]
        if any(word in response.lower() for word in reasoning_words):
            score += 0.2

        # Contains conclusion
        if "answer" in response.lower() or "solution" in response.lower():
            score += 0.1

        return min(1.0, score)

    def _detect_task_type(self, prompt: str) -> str:
        """Detect task type from prompt."""
        prompt_lower = prompt.lower()

        if any(kw in prompt_lower for kw in ["write", "code", "function", "implement"]):
            return "coding"
        elif any(kw in prompt_lower for kw in ["fix", "debug", "error", "bug"]):
            return "debugging"
        elif any(kw in prompt_lower for kw in ["explain", "analyze", "why", "how"]):
            return "reasoning"
        elif any(kw in prompt_lower for kw in ["json", "format", "schema"]):
            return "discipline"
        else:
            return "general"

    def _analyze_results(self, all_results: List[Dict]) -> Dict[str, Any]:
        """Analyze A/B test results."""
        by_strategy = {}

        for strategy_data in all_results:
            strategy_key = ",".join(sorted(strategy_data["strategy"]))
            results = strategy_data["results"]

            scores = [r.score for r in results]
            latencies = [r.latency_ms for r in results]
            tokens = [r.tokens_used for r in results]

            by_strategy[strategy_key] = {
                "strategy": strategy_data["strategy"],
                "scores": scores,
                "avg_score": statistics.mean(scores) if scores else 0,
                "std_score": statistics.stdev(scores) if len(scores) > 1 else 0,
                "success_rate": sum(1 for r in results if r.success) / len(results)
                if results
                else 0,
                "avg_latency": statistics.mean(latencies) if latencies else 0,
                "avg_tokens": statistics.mean(tokens) if tokens else 0,
                "runs": len(results),
            }

        # Calculate fitness scores
        for strategy_key, data in by_strategy.items():
            # Fitness = score * success_rate - token_penalty
            token_penalty = data["avg_tokens"] / 10000
            data["fitness"] = data["avg_score"] * data["success_rate"] - token_penalty

        return {"by_strategy": by_strategy}

    def _determine_winner(self, analysis: Dict) -> Optional[Dict]:
        """Determine winning strategy."""
        by_strategy = analysis.get("by_strategy", {})

        if not by_strategy:
            return None

        # Find highest fitness
        winner_key = max(by_strategy, key=lambda k: by_strategy[k]["fitness"])
        winner = by_strategy[winner_key].copy()
        winner["strategy_key"] = winner_key

        return winner

    def _calculate_significance(self, analysis: Dict) -> float:
        """Calculate statistical significance using manual t-test."""
        by_strategy = analysis.get("by_strategy", {})

        if len(by_strategy) < 2:
            return 1.0

        # Get scores for top 2 strategies
        strategies = sorted(
            by_strategy.values(), key=lambda x: x["avg_score"], reverse=True
        )[:2]

        if len(strategies) < 2:
            return 0.5

        scores_a = strategies[0]["scores"]
        scores_b = strategies[1]["scores"]

        if len(scores_a) < 2 or len(scores_b) < 2:
            return 0.5

        # Manual t-test implementation
        try:
            # Calculate means
            mean_a = sum(scores_a) / len(scores_a)
            mean_b = sum(scores_b) / len(scores_b)

            # Calculate variances
            var_a = sum((x - mean_a) ** 2 for x in scores_a) / (len(scores_a) - 1)
            var_b = sum((x - mean_b) ** 2 for x in scores_b) / (len(scores_b) - 1)

            # Calculate t-statistic
            pooled_se = math.sqrt(var_a / len(scores_a) + var_b / len(scores_b))
            if pooled_se == 0:
                return 0.5

            t_stat = (mean_a - mean_b) / pooled_se

            # Convert t to p-value (approximation for two-tailed test)
            # Using normal approximation for simplicity
            df = len(scores_a) + len(scores_b) - 2
            p_value = self._t_cdf(abs(t_stat), df)
            significance = 1 - p_value

            return max(0.0, min(1.0, significance))
        except Exception:
            return 0.5

    def _t_cdf(self, t: float, df: int) -> float:
        """Approximate t-distribution CDF using normal approximation."""
        # For large df, t converges to normal distribution
        # Use Abramowitz and Stegun approximation for normal CDF
        if df > 30:
            return self._normal_cdf(t)

        # For smaller df, use a simpler approximation
        x = df / (df + t * t)
        return 1 - 0.5 * (1 - self._normal_cdf(t)) * (1 - x)

    def _normal_cdf(self, z: float) -> float:
        """Standard normal CDF using Abramowitz and Stegun approximation."""
        if z < 0:
            return 1 - self._normal_cdf(-z)

        # Constants for approximation
        p = 0.2316419
        b1 = 0.319381530
        b2 = -0.356563782
        b3 = 1.781477937
        b4 = -1.821255978
        b5 = 1.330274429

        t = 1 / (1 + p * z)
        cdf = 1 - (1 / math.sqrt(2 * math.pi)) * math.exp(-z * z / 2) * (
            b1 * t
            + b2 * t * t
            + b3 * t * t * t
            + b4 * t * t * t * t
            + b5 * t * t * t * t * t
        )

        return min(1.0, max(0.0, cdf))

        scores_a = strategies[0]["scores"]
        scores_b = strategies[1]["scores"]

        if len(scores_a) < 2 or len(scores_b) < 2:
            return 0.5

        # Perform t-test
        try:
            stat, p_value = ttest_ind(scores_a, scores_b)
            significance = 1 - p_value
            return max(0.0, min(1.0, significance))
        except Exception:
            return 0.5

    def get_stats(self) -> Dict[str, Any]:
        """Get A/B testing statistics."""
        return {
            "total_tests": len(self.tests),
            "avg_strategies_per_test": statistics.mean(
                [t["strategies_tested"] for t in self.tests]
            )
            if self.tests
            else 0,
            "avg_runs_per_test": statistics.mean([t["total_runs"] for t in self.tests])
            if self.tests
            else 0,
        }

    def generate_mutated_strategies(
        self,
        base_strategies: List[List[str]],
        n_mutations: int = 5,
    ) -> List[List[str]]:
        """
        Generate mutated strategy variants.

        Args:
            base_strategies: Base strategies to mutate
            n_mutations: Number of mutations to generate

        Returns:
            List of mutated strategies
        """
        import random

        available_modules = [
            "role",
            "decompose",
            "scratchpad",
            "tools",
            "verify",
            "format",
            "planner",
            "few_shot",
            "constraints",
        ]

        mutations = []

        for _ in range(n_mutations):
            # Pick random base strategy
            base = random.choice(base_strategies).copy()

            # Apply random mutation
            mutation_type = random.choice(["add", "remove", "swap"])

            if mutation_type == "add" and len(base) < 5:
                new_module = random.choice(available_modules)
                if new_module not in base:
                    base.append(new_module)

            elif mutation_type == "remove" and len(base) > 1:
                base.pop(random.randint(0, len(base) - 1))

            elif mutation_type == "swap" and base:
                idx = random.randint(0, len(base) - 1)
                new_module = random.choice(available_modules)
                base[idx] = new_module

            # Validate (max 5, no duplicates)
            base = list(set(base))[:5]

            if base and base not in mutations:
                mutations.append(base)

        return mutations
