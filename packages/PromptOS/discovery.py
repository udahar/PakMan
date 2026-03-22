"""
Strategy Discovery Engine

Lets the LLM invent new strategies by proposing module combinations.
Benchmarks proposals and stores successful ones in genome.

Usage:
    from PromptOS.discovery import StrategyDiscovery
    
    discovery = StrategyDiscovery(llm_callable=llm, genome=genome)
    
    # Ask LLM to propose strategies
    proposals = discovery.propose_strategies(
        task_type="debugging",
        n_proposals=5
    )
    
    # Benchmark proposals
    results = discovery.benchmark_proposals(
        proposals=proposals,
        test_prompts=test_prompts,
        model="qwen2.5:7b"
    )
    
    # Store successful strategies in genome
    for result in results:
        if result.score > 0.8:
            genome.record_strategy(result.strategy, result.score)
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
import json
import time


@dataclass
class StrategyProposal:
    """A proposed strategy from LLM."""
    modules: List[str]
    reasoning: str
    proposed_by: str
    task_type: str
    timestamp: float


@dataclass
class BenchmarkResult:
    """Result from benchmarking a proposal."""
    strategy: List[str]
    avg_score: float
    success_rate: float
    runs: int
    token_efficiency: float


class StrategyDiscovery:
    """
    Strategy discovery engine.
    
    Uses LLM to propose new strategy combinations, then benchmarks them.
    Successful strategies are stored in genome.
    """
    
    def __init__(
        self,
        llm_callable: Callable,
        genome: Optional[Any] = None,
    ):
        """
        Initialize strategy discovery.
        
        Args:
            llm_callable: LLM callable function
            genome: PromptOS genome instance
        """
        self.llm_callable = llm_callable
        self.genome = genome
        
        # Available modules for proposals
        self.available_modules = [
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
        
        # Module descriptions (for LLM prompting)
        self.module_descriptions = {
            "role": "Assigns a role to the model (e.g., 'senior engineer')",
            "decompose": "Breaks problem into smaller steps before solving",
            "scratchpad": "Hidden reasoning space for step-by-step thinking",
            "tools": "Plans tool usage before execution",
            "verify": "Self-correction and verification before finalizing",
            "format": "Enforces strict output formatting",
            "planner": "Plan-then-solve pattern for complex tasks",
            "few_shot": "Includes examples of desired output",
            "constraints": "Explicit constraints and requirements",
        }
        
        # Discovery history
        self.proposals: List[StrategyProposal] = []
        self.benchmark_results: List[BenchmarkResult] = []
    
    def propose_strategies(
        self,
        task_type: str,
        n_proposals: int = 5,
    ) -> List[StrategyProposal]:
        """
        Ask LLM to propose new strategies for a task type.
        
        Args:
            task_type: Task type (debugging, coding, reasoning, etc.)
            n_proposals: Number of proposals to generate
        
        Returns:
            List of StrategyProposal
        """
        # Build prompt for LLM
        prompt = self._build_discovery_prompt(task_type, n_proposals)
        
        # Get LLM response
        response = self.llm_callable(prompt)
        
        # Parse proposals from response
        proposals = self._parse_proposals(response, task_type)
        
        # Store proposals
        self.proposals.extend(proposals)
        
        return proposals
    
    def _build_discovery_prompt(self, task_type: str, n_proposals: int) -> str:
        """Build prompt for strategy discovery."""
        modules_list = "\n".join(
            f"- {mod}: {self.module_descriptions[mod]}"
            for mod in self.available_modules
        )
        
        prompt = f"""You are designing reasoning strategies for LLMs.

Available modules:

{modules_list}

Task Type: {task_type}

Design {n_proposals} different strategies for {task_type} tasks.

For each strategy:
1. List the modules (2-5 modules recommended)
2. Explain why this combination works for {task_type}
3. Explain the order modules should be applied

Format your response as:

Strategy 1:
Modules: [module1, module2, module3]
Reasoning: [explanation]

Strategy 2:
...

Be creative! Try combinations that haven't been tried before."""

        return prompt
    
    def _parse_proposals(
        self,
        response: str,
        task_type: str,
    ) -> List[StrategyProposal]:
        """Parse strategy proposals from LLM response."""
        proposals = []
        
        # Simple parsing (can be improved)
        lines = response.split("\n")
        current_modules = []
        current_reasoning = ""
        
        for line in lines:
            line = line.strip()
            
            if line.startswith("Modules:"):
                # Parse modules list
                try:
                    modules_str = line.replace("Modules:", "").strip()
                    # Handle both "[a, b]" and "a, b" formats
                    modules_str = modules_str.strip("[]")
                    current_modules = [
                        m.strip().strip('"').strip("'")
                        for m in modules_str.split(",")
                        if m.strip()
                    ]
                except Exception:
                    current_modules = []
            
            elif line.startswith("Reasoning:"):
                current_reasoning = line.replace("Reasoning:", "").strip()
                
                # If we have both modules and reasoning, create proposal
                if current_modules:
                    # Validate proposal
                    if self._validate_strategy(current_modules):
                        proposal = StrategyProposal(
                            modules=current_modules,
                            reasoning=current_reasoning,
                            proposed_by="llm",
                            task_type=task_type,
                            timestamp=time.time(),
                        )
                        proposals.append(proposal)
                    
                    # Reset for next proposal
                    current_modules = []
                    current_reasoning = ""
        
        return proposals
    
    def _validate_strategy(self, strategy: List[str]) -> bool:
        """
        Validate a strategy proposal.
        
        Rules:
        - Max 5 modules
        - No incompatible pairs
        - All modules must exist
        - Task compatibility
        """
        # Rule 1: Max modules
        if len(strategy) > 5:
            return False
        
        # Rule 2: All modules must exist
        from .strategy_modules import STRATEGY_MODULES
        for module in strategy:
            if module not in STRATEGY_MODULES:
                return False
        
        # Rule 3: No incompatible pairs
        incompatible_pairs = [
            ("format", "hidden_scratchpad"),
            ("decompose", "planner"),  # Redundant
        ]
        
        for mod_a, mod_b in incompatible_pairs:
            if mod_a in strategy and mod_b in strategy:
                return False
        
        # Rule 4: No duplicates
        if len(strategy) != len(set(strategy)):
            return False
        
        return True
    
    def benchmark_proposals(
        self,
        proposals: List[StrategyProposal],
        test_prompts: List[str],
        model: str,
        task_type: Optional[str] = None,
    ) -> List[BenchmarkResult]:
        """
        Benchmark proposed strategies.
        
        Args:
            proposals: List of proposals to benchmark
            test_prompts: Test prompts to run
            model: Model to test with
            task_type: Task type (auto-detected if None)
        
        Returns:
            List of BenchmarkResult
        """
        results = []
        
        for proposal in proposals:
            scores = []
            token_counts = []
            
            for prompt in test_prompts:
                # Run with proposed strategy
                # (This would integrate with PromptOS.run())
                # For now, simplified
                score = self._evaluate_strategy(
                    prompt=prompt,
                    strategy=proposal.modules,
                    model=model,
                )
                scores.append(score)
                
                # Estimate tokens
                tokens = self._estimate_tokens(proposal.modules, prompt)
                token_counts.append(tokens)
            
            # Calculate metrics
            avg_score = sum(scores) / len(scores) if scores else 0
            success_rate = sum(1 for s in scores if s >= 0.7) / len(scores) if scores else 0
            avg_tokens = sum(token_counts) / len(token_counts) if token_counts else 0
            token_efficiency = avg_score / (avg_tokens / 1000) if avg_tokens > 0 else 0
            
            result = BenchmarkResult(
                strategy=proposal.modules,
                avg_score=avg_score,
                success_rate=success_rate,
                runs=len(scores),
                token_efficiency=token_efficiency,
            )
            
            results.append(result)
            self.benchmark_results.append(result)
        
        return results
    
    def _evaluate_strategy(
        self,
        prompt: str,
        strategy: List[str],
        model: str,
    ) -> float:
        """
        Evaluate a strategy (placeholder).
        
        In production, this would:
        1. Assemble prompt with strategy
        2. Run LLM
        3. Score with Bench
        """
        # Placeholder - would integrate with actual PromptOS
        import random
        return random.uniform(0.5, 0.9)
    
    def _estimate_tokens(self, strategy: List[str], prompt: str) -> int:
        """Estimate token cost for a strategy."""
        from .strategy_modules import STRATEGY_MODULES
        
        prompt_tokens = len(prompt) // 4
        module_tokens = sum(
            STRATEGY_MODULES.get(m, type("obj", (object,), {"cost_tokens": 50})()).cost_tokens
            for m in strategy
        )
        response_tokens = prompt_tokens
        
        return prompt_tokens + module_tokens + response_tokens
    
    def get_best_proposals(
        self,
        task_type: str,
        min_score: float = 0.7,
    ) -> List[BenchmarkResult]:
        """
        Get best proposals for a task type.
        
        Args:
            task_type: Task type
            min_score: Minimum score threshold
        
        Returns:
            List of successful BenchmarkResult
        """
        # Filter by task type and score
        successful = [
            r for r in self.benchmark_results
            if r.avg_score >= min_score
        ]
        
        # Sort by score
        return sorted(successful, key=lambda r: r.avg_score, reverse=True)
    
    def export_discoveries(self, path: str):
        """Export discoveries to JSON file."""
        data = {
            "proposals": [
                {
                    "modules": p.modules,
                    "reasoning": p.reasoning,
                    "task_type": p.task_type,
                    "timestamp": p.timestamp,
                }
                for p in self.proposals
            ],
            "benchmark_results": [
                {
                    "strategy": r.strategy,
                    "avg_score": r.avg_score,
                    "success_rate": r.success_rate,
                    "runs": r.runs,
                    "token_efficiency": r.token_efficiency,
                }
                for r in self.benchmark_results
            ],
        }
        
        with open(path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def import_discoveries(self, path: str):
        """Import discoveries from JSON file."""
        with open(path, 'r') as f:
            data = json.load(f)
        
        # Load proposals
        for p_data in data.get("proposals", []):
            proposal = StrategyProposal(
                modules=p_data["modules"],
                reasoning=p_data.get("reasoning", ""),
                proposed_by=p_data.get("proposed_by", "imported"),
                task_type=p_data.get("task_type", "unknown"),
                timestamp=p_data.get("timestamp", time.time()),
            )
            self.proposals.append(proposal)
        
        # Load benchmark results
        for r_data in data.get("benchmark_results", []):
            result = BenchmarkResult(
                strategy=r_data["strategy"],
                avg_score=r_data["avg_score"],
                success_rate=r_data["success_rate"],
                runs=r_data["runs"],
                token_efficiency=r_data.get("token_efficiency", 0),
            )
            self.benchmark_results.append(result)
        
        print(f"[StrategyDiscovery] Imported {len(self.proposals)} proposals")
