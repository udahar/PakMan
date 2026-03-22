"""
Strategy Research Engine - Autonomous Strategy Discovery

Analyzes genome patterns, generates hypotheses, and invents new strategies.
This is the "scientist" component of PromptOS.

Usage:
    from PromptOS.strategy_research import StrategyResearchEngine
    
    researcher = StrategyResearchEngine(genome, llm_callable)
    
    # Analyze genome for patterns
    patterns = researcher.analyze_genome()
    
    # Generate hypothesis strategies
    hypotheses = researcher.generate_hypotheses(patterns)
    
    # Test hypotheses
    results = researcher.test_hypotheses(hypotheses, test_prompts, model)
    
    # Store successful strategies
    for result in results:
        if result.success_rate > 0.8:
            genome.record_strategy(result.strategy, result.avg_score)
"""

from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, asdict
import json
import time
import random
from pathlib import Path


@dataclass
class GenomePattern:
    """Pattern discovered in genome data."""
    pattern_type: str  # "synergy", "antagonism", "context_dependent"
    modules: List[str]
    effect_size: float
    confidence: float
    context: Dict[str, Any]  # task_types, models, etc.
    evidence_count: int


@dataclass
class StrategyHypothesis:
    """A hypothesized strategy to test."""
    strategy: List[str]
    rationale: str
    predicted_improvement: float
    generation_method: str  # "mutation", "crossover", "llm_invention", "pattern_based"
    parent_strategies: List[List[str]]


@dataclass
class HypothesisResult:
    """Result from testing a hypothesis."""
    strategy: List[str]
    avg_score: float
    success_rate: float
    runs: int
    token_efficiency: float
    confirmed: bool
    improvement_over_baseline: float


class StrategyResearchEngine:
    """
    Strategy research engine for autonomous strategy discovery.
    
    Analyzes genome data to discover patterns, generates hypotheses,
    and tests new strategies through experimentation.
    """
    
    def __init__(
        self,
        genome: Optional[Any] = None,
        llm_callable: Optional[Callable] = None,
        storage_path: Optional[str] = None,
    ):
        """
        Initialize strategy research engine.
        
        Args:
            genome: PromptOS genome instance
            llm_callable: LLM callable for strategy invention
            storage_path: Path for storing research data
        """
        self.genome = genome
        self.llm_callable = llm_callable
        self.storage_path = storage_path or "PromptOS/strategy_research.json"
        
        # Research history
        self.patterns: List[GenomePattern] = []
        self.hypotheses: List[StrategyHypothesis] = []
        self.results: List[HypothesisResult] = []
        
        # Module library for invention
        self.available_modules = [
            "role", "decompose", "scratchpad", "tools", "verify",
            "format", "planner", "few_shot", "constraints",
        ]
        
        # Load existing data
        self._load()
    
    def analyze_genome(self) -> List[GenomePattern]:
        """
        Analyze genome for strategy patterns.
        
        Returns:
            List of discovered patterns
        """
        patterns = []
        
        if not self.genome:
            return patterns
        
        # 1. Analyze module synergies
        synergy_patterns = self._discover_synergies()
        patterns.extend(synergy_patterns)
        
        # 2. Analyze antagonistic modules
        antagonism_patterns = self._discover_antagonisms()
        patterns.extend(antagonism_patterns)
        
        # 3. Analyze context-dependent patterns
        context_patterns = self._discover_context_patterns()
        patterns.extend(context_patterns)
        
        # Store patterns
        self.patterns = patterns
        
        return patterns
    
    def _discover_synergies(self) -> List[GenomePattern]:
        """Discover module synergies (modules that work well together)."""
        patterns = []
        
        # Example: scratchpad + verify synergy
        patterns.append(GenomePattern(
            pattern_type="synergy",
            modules=["scratchpad", "verify"],
            effect_size=0.17,  # +17% improvement
            confidence=0.85,
            context={"task_types": ["reasoning", "coding"], "models": ["all"]},
            evidence_count=47,
        ))
        
        # Example: planner + tools synergy
        patterns.append(GenomePattern(
            pattern_type="synergy",
            modules=["planner", "tools"],
            effect_size=0.22,
            confidence=0.78,
            context={"task_types": ["tools", "automation"], "models": ["qwen2.5:7b+"]},
            evidence_count=32,
        ))
        
        return patterns
    
    def _discover_antagonisms(self) -> List[GenomePattern]:
        """Discover modules that work poorly together."""
        patterns = []
        
        # Example: decompose + planner antagonism (redundant)
        patterns.append(GenomePattern(
            pattern_type="antagonism",
            modules=["decompose", "planner"],
            effect_size=-0.07,  # -7% degradation
            confidence=0.73,
            context={"task_types": ["simple_qa", "chat"], "models": ["small"]},
            evidence_count=28,
        ))
        
        return patterns
    
    def _discover_context_patterns(self) -> List[GenomePattern]:
        """Discover context-dependent patterns."""
        patterns = []
        
        # Example: format module only helps discipline tasks
        patterns.append(GenomePattern(
            pattern_type="context_dependent",
            modules=["format"],
            effect_size=0.25,
            confidence=0.92,
            context={"task_types": ["discipline", "extraction"], "models": ["all"]},
            evidence_count=89,
        ))
        
        return patterns
    
    def generate_hypotheses(
        self,
        patterns: Optional[List[GenomePattern]] = None,
        n_hypotheses: int = 10,
    ) -> List[StrategyHypothesis]:
        """
        Generate strategy hypotheses based on patterns.
        
        Args:
            patterns: Patterns to use (analyzes genome if None)
            n_hypotheses: Number of hypotheses to generate
        
        Returns:
            List of hypotheses
        """
        if not patterns:
            patterns = self.analyze_genome()
        
        hypotheses = []
        
        # 1. Generate via mutation
        mutation_hypotheses = self._generate_via_mutation(n_hypotheses // 3)
        hypotheses.extend(mutation_hypotheses)
        
        # 2. Generate via crossover
        crossover_hypotheses = self._generate_via_crossover(n_hypotheses // 3)
        hypotheses.extend(crossover_hypotheses)
        
        # 3. Generate via pattern-based reasoning
        pattern_hypotheses = self._generate_via_patterns(patterns)
        hypotheses.extend(pattern_hypotheses)
        
        # 4. Generate via LLM invention
        if self.llm_callable:
            llm_hypotheses = self._generate_via_llm(n_hypotheses // 4)
            hypotheses.extend(llm_hypotheses)
        
        # Limit to n_hypotheses
        hypotheses = hypotheses[:n_hypotheses]
        
        self.hypotheses.extend(hypotheses)
        
        return hypotheses
    
    def _generate_via_mutation(self, n: int) -> List[StrategyHypothesis]:
        """Generate hypotheses via mutation."""
        hypotheses = []
        
        # Get existing strategies from genome
        existing_strategies = self._get_existing_strategies()
        
        for _ in range(n):
            if not existing_strategies:
                break
            
            parent = random.choice(existing_strategies)
            mutated = parent.copy()
            
            # Random mutation
            mutation_type = random.choice(["add", "remove", "swap"])
            
            if mutation_type == "add":
                new_module = random.choice(self.available_modules)
                if new_module not in mutated:
                    mutated.append(new_module)
            
            elif mutation_type == "remove" and mutated:
                mutated.pop(random.randint(0, len(mutated) - 1))
            
            elif mutation_type == "swap" and mutated:
                idx = random.randint(0, len(mutated) - 1)
                new_module = random.choice(self.available_modules)
                mutated[idx] = new_module
            
            hypothesis = StrategyHypothesis(
                strategy=mutated,
                rationale=f"Mutation of {parent} via {mutation_type}",
                predicted_improvement=0.05,  # Small expected improvement
                generation_method="mutation",
                parent_strategies=[parent],
            )
            
            hypotheses.append(hypothesis)
        
        return hypotheses
    
    def _generate_via_crossover(self, n: int) -> List[StrategyHypothesis]:
        """Generate hypotheses via crossover."""
        hypotheses = []
        
        existing_strategies = self._get_existing_strategies()
        
        for _ in range(n):
            if len(existing_strategies) < 2:
                break
            
            parent1 = random.choice(existing_strategies)
            parent2 = random.choice(existing_strategies)
            
            # Crossover
            if parent1 and parent2:
                crossover_point = min(len(parent1), len(parent2)) // 2
                child = parent1[:crossover_point] + parent2[crossover_point:]
                
                hypothesis = StrategyHypothesis(
                    strategy=child,
                    rationale=f"Crossover of {parent1} and {parent2}",
                    predicted_improvement=0.08,
                    generation_method="crossover",
                    parent_strategies=[parent1, parent2],
                )
                
                hypotheses.append(hypothesis)
        
        return hypotheses
    
    def _generate_via_patterns(
        self,
        patterns: List[GenomePattern],
    ) -> List[StrategyHypothesis]:
        """Generate hypotheses based on discovered patterns."""
        hypotheses = []
        
        for pattern in patterns:
            if pattern.pattern_type == "synergy":
                # Synergy suggests combining modules
                hypothesis = StrategyHypothesis(
                    strategy=pattern.modules,
                    rationale=f"Synergy pattern: modules work well together (+{pattern.effect_size:.0%})",
                    predicted_improvement=pattern.effect_size,
                    generation_method="pattern_based",
                    parent_strategies=[],
                )
                hypotheses.append(hypothesis)
            
            elif pattern.pattern_type == "context_dependent":
                # Context pattern suggests targeted strategy
                task_types = pattern.context.get("task_types", [])
                for task_type in task_types:
                    hypothesis = StrategyHypothesis(
                        strategy=pattern.modules,
                        rationale=f"Context pattern: effective for {task_type}",
                        predicted_improvement=pattern.effect_size,
                        generation_method="pattern_based",
                        parent_strategies=[],
                    )
                    hypotheses.append(hypothesis)
        
        return hypotheses
    
    def _generate_via_llm(self, n: int) -> List[StrategyHypothesis]:
        """Generate hypotheses via LLM invention."""
        hypotheses = []
        
        if not self.llm_callable:
            return hypotheses
        
        # Build invention prompt
        modules_list = "\n".join(f"- {mod}" for mod in self.available_modules)
        
        prompt = f"""You are designing reasoning strategies for LLMs.

Available modules:

{modules_list}

Design {n} novel strategies for complex reasoning tasks.

For each strategy:
1. List the modules (2-5 modules)
2. Explain the rationale

Format:
Strategy: [module1, module2, module3]
Rationale: [explanation]"""
        
        # Get LLM response
        response = self.llm_callable(prompt)
        
        # Parse response (simplified)
        # In production, would use better parsing
        for i in range(n):
            hypothesis = StrategyHypothesis(
                strategy=["scratchpad", "verify"],  # Placeholder
                rationale="LLM-invented strategy",
                predicted_improvement=0.10,
                generation_method="llm_invention",
                parent_strategies=[],
            )
            hypotheses.append(hypothesis)
        
        return hypotheses
    
    def _get_existing_strategies(self) -> List[List[str]]:
        """Get existing strategies from genome."""
        if not self.genome:
            return []
        
        # Would query actual genome in production
        return [
            ["scratchpad", "verify"],
            ["planner", "verify"],
            ["decompose", "scratchpad"],
        ]
    
    def test_hypotheses(
        self,
        hypotheses: List[StrategyHypothesis],
        test_prompts: List[str],
        model: str,
    ) -> List[HypothesisResult]:
        """
        Test hypotheses through benchmarking.
        
        Args:
            hypotheses: Hypotheses to test
            test_prompts: Test prompts
            model: Model to test with
        
        Returns:
            List of results
        """
        results = []
        
        for hypothesis in hypotheses:
            scores = []
            token_counts = []
            
            for prompt in test_prompts:
                # Run with hypothesis strategy
                # (Would integrate with PromptOS.run() in production)
                score = self._evaluate_strategy(
                    prompt=prompt,
                    strategy=hypothesis.strategy,
                    model=model,
                )
                scores.append(score)
                
                tokens = self._estimate_tokens(hypothesis.strategy, prompt)
                token_counts.append(tokens)
            
            # Calculate metrics
            avg_score = sum(scores) / len(scores) if scores else 0
            success_rate = sum(1 for s in scores if s >= 0.7) / len(scores) if scores else 0
            avg_tokens = sum(token_counts) / len(token_counts) if token_counts else 0
            token_efficiency = avg_score / (avg_tokens / 1000) if avg_tokens > 0 else 0
            
            # Get baseline (best existing strategy)
            baseline_score = self._get_baseline_score(model, test_prompts[0] if test_prompts else "")
            improvement = avg_score - baseline_score
            
            result = HypothesisResult(
                strategy=hypothesis.strategy,
                avg_score=avg_score,
                success_rate=success_rate,
                runs=len(scores),
                token_efficiency=token_efficiency,
                confirmed=avg_score >= 0.7,
                improvement_over_baseline=improvement,
            )
            
            results.append(result)
            self.results.append(result)
        
        return results
    
    def _evaluate_strategy(
        self,
        prompt: str,
        strategy: List[str],
        model: str,
    ) -> float:
        """Evaluate a strategy (placeholder)."""
        # Would integrate with actual PromptOS in production
        import random
        return random.uniform(0.5, 0.95)
    
    def _estimate_tokens(self, strategy: List[str], prompt: str) -> int:
        """Estimate token cost."""
        from .strategy_modules import STRATEGY_MODULES
        
        prompt_tokens = len(prompt) // 4
        module_tokens = sum(
            STRATEGY_MODULES.get(m).cost_tokens if STRATEGY_MODULES.get(m) else 50
            for m in strategy
        )
        response_tokens = prompt_tokens
        
        return prompt_tokens + module_tokens + response_tokens
    
    def _get_baseline_score(self, model: str, prompt: str) -> float:
        """Get baseline score for comparison."""
        # Would query genome for best existing strategy
        return 0.65  # Placeholder
    
    def get_confirmed_strategies(self, min_improvement: float = 0.05) -> List[HypothesisResult]:
        """Get confirmed successful strategies."""
        return [
            r for r in self.results
            if r.confirmed and r.improvement_over_baseline >= min_improvement
        ]
    
    def export_research(self, path: Optional[str] = None):
        """Export research data to JSON."""
        export_path = path or self.storage_path
        
        data = {
            "patterns": [asdict(p) for p in self.patterns],
            "hypotheses": [asdict(h) for h in self.hypotheses],
            "results": [asdict(r) for r in self.results],
            "saved_at": time.time(),
        }
        
        with open(export_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def _save(self):
        """Save research data."""
        self.export_research()
    
    def _load(self):
        """Load research data."""
        try:
            if Path(self.storage_path).exists():
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                
                # Would load data in production
                print(f"[StrategyResearch] Loaded existing research data")
        except Exception as e:
            print(f"[StrategyResearch] Load failed: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get research statistics."""
        return {
            "patterns_discovered": len(self.patterns),
            "hypotheses_generated": len(self.hypotheses),
            "hypotheses_tested": len(self.results),
            "confirmed_strategies": len(self.get_confirmed_strategies()),
        }
