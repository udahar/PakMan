"""
Strategy Planner - Dynamic Reasoning Orchestration

Replaces static strategy stacks with dynamic planning.
Analyzes task, model, and history to generate optimal module sequences.

Usage:
    from PromptOS.planner import StrategyPlanner
    
    planner = StrategyPlanner(genome, model_profiles)
    
    # Plan strategy for task
    plan = planner.plan(
        prompt="Debug this crash",
        model="qwen2.5:7b",
        task_type="debugging"
    )
    
    print(f"Strategy: {plan.modules}")
    print(f"Predicted success: {plan.predicted_success:.1%}")
    print(f"Token cost: {plan.estimated_tokens}")
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import random
import math

from .modules import STRATEGY_MODULES, StrategyModule


@dataclass
class StrategyPlan:
    """A planned strategy sequence."""
    modules: List[str]
    predicted_success: float
    estimated_tokens: int
    confidence: float
    reasoning: str
    alternatives: List[List[str]] = field(default_factory=list)
    
    def to_strategy_key(self) -> str:
        """Convert to strategy key string."""
        return ",".join(sorted(self.modules))


@dataclass
class ModuleInteraction:
    """Records interaction effect between two modules."""
    module_a: str
    module_b: str
    avg_score_delta: float
    occurrences: int


class StrategyPlanner:
    """
    Dynamic strategy planner.
    
    Instead of static stacks, generates optimal module sequences based on:
    - Task type and complexity
    - Model profile and preferences
    - Genome historical data
    - Module interaction effects
    - Token budget constraints
    """
    
    def __init__(
        self,
        genome: Optional[Any] = None,
        model_profiles: Optional[Any] = None,
        token_budget: Optional[Any] = None,
    ):
        """
        Initialize strategy planner.
        
        Args:
            genome: PromptOS genome instance (for historical data)
            model_profiles: PromptOS model profiles instance
            token_budget: PromptOS token budget instance
        """
        self.genome = genome
        self.model_profiles = model_profiles
        self.token_budget = token_budget
        
        # Module interaction tracking
        self.interactions: Dict[str, ModuleInteraction] = {}
        
        # Module weights (for reinforcement learning)
        self.module_weights: Dict[str, float] = {
            name: 1.0 for name in STRATEGY_MODULES
        }
        
        # Task complexity cache
        self.complexity_cache: Dict[str, float] = {}
        
        # Exploration tracking (prevents strategy collapse)
        self.strategy_usage: Dict[str, int] = {}  # strategy_key → usage count
        self.exploration_bonus: float = 0.1  # Bonus for underused strategies
    
    def plan(
        self,
        prompt: str,
        model: str,
        task_type: str,
        token_limit: Optional[int] = None,
    ) -> StrategyPlan:
        """
        Plan optimal strategy for a task.
        
        Args:
            prompt: Input prompt
            model: Model name
            task_type: Task type
            token_limit: Optional token limit
        
        Returns:
            StrategyPlan with module sequence
        """
        # 1. Classify task complexity
        complexity = self._classify_complexity(prompt)
        
        # 2. Get model profile
        model_profile = self._get_model_profile(model)
        
        # 3. Get genome best strategies
        genome_strategies = self._get_genome_strategies(model, task_type)
        
        # 4. Generate candidate strategies
        candidates = self._generate_candidates(
            model=model,
            task_type=task_type,
            complexity=complexity,
            model_profile=model_profile,
            genome_strategies=genome_strategies,
        )
        
        # 5. Score candidates
        scored = []
        
        for candidate in candidates:
            # Check token budget
            if token_limit:
                estimated_tokens = self._estimate_tokens(candidate, prompt)
                if estimated_tokens > token_limit:
                    continue  # Skip if over budget
            
            score = self._score_candidate(
                modules=candidate,
                model=model,
                task_type=task_type,
                complexity=complexity,
            )
            scored.append((candidate, score))
        
        # 6. Choose best
        if not scored:
            # Fallback to simple strategy
            return self._fallback_plan(task_type)
        
        best_candidate, best_score = max(scored, key=lambda x: x[1]["predicted_success"])

        # 7. Track strategy usage (for exploration bonus)
        strategy_key = ",".join(sorted(best_candidate))
        self.strategy_usage[strategy_key] = self.strategy_usage.get(strategy_key, 0) + 1

        # 8. Generate alternatives
        alternatives = [c for c, s in scored[:3] if c != best_candidate]
        
        # 8. Build plan
        plan = StrategyPlan(
            modules=best_candidate,
            predicted_success=best_score["predicted_success"],
            estimated_tokens=self._estimate_tokens(best_candidate, prompt),
            confidence=best_score["confidence"],
            reasoning=best_score["reasoning"],
            alternatives=alternatives,
        )
        
        return plan
    
    def _classify_complexity(self, prompt: str) -> float:
        """
        Classify prompt complexity (0-1).
        
        Factors:
        - Length
        - Number of requirements
        - Presence of code
        - Presence of constraints
        """
        # Check cache
        if prompt in self.complexity_cache:
            return self.complexity_cache[prompt]
        
        # Length score (0-0.3)
        length_score = min(len(prompt) / 1000, 0.3)
        
        # Requirements score (0-0.3)
        requirement_keywords = ["must", "should", "require", "need", "constraint"]
        req_count = sum(1 for kw in requirement_keywords if kw in prompt.lower())
        req_score = min(req_count * 0.1, 0.3)
        
        # Code presence (0-0.2)
        code_indicators = ["```", "def ", "function", "import ", "class "]
        code_score = 0.2 if any(ind in prompt for ind in code_indicators) else 0
        
        # Constraints (0-0.2)
        constraint_keywords = ["only", "exactly", "strict", "no ", "without"]
        constraint_count = sum(1 for kw in constraint_keywords if kw in prompt.lower())
        constraint_score = min(constraint_count * 0.05, 0.2)
        
        complexity = length_score + req_score + code_score + constraint_score
        
        # Cache
        self.complexity_cache[prompt] = complexity
        
        return complexity
    
    def _get_model_profile(self, model: str) -> Optional[Dict]:
        """Get model profile if available."""
        if not self.model_profiles:
            return None
        
        # ModelFamilies has methods, not dict access
        if hasattr(self.model_profiles, 'get_model_readiness'):
            return self.model_profiles.get_model_readiness(model)
        
        return None
    
    def _get_genome_strategies(self, model: str, task_type: str) -> List[Dict]:
        """Get best strategies from genome."""
        if not self.genome:
            return []
        
        # Query genome for best strategies
        best = self.genome.query_best(model, task_type)
        
        if not best or best.get("trials", 0) < 3:
            return []
        
        return [best]
    
    def _generate_candidates(
        self,
        model: str,
        task_type: str,
        complexity: float,
        model_profile: Optional[Dict],
        genome_strategies: List[Dict],
    ) -> List[List[str]]:
        """Generate candidate strategy sequences."""
        candidates = []
        
        # 1. Add model's preferred strategies
        if model_profile and task_type in model_profile.get("preferred_strategies", {}):
            preferred = model_profile["preferred_strategies"][task_type]
            if isinstance(preferred, list):
                candidates.append(preferred)
        
        # 2. Add genome best strategies
        for genome_strat in genome_strategies:
            if "strategy" in genome_strat:
                candidates.append(genome_strat["strategy"])
        
        # 3. Add complexity-based strategies
        if complexity > 0.7:
            # High complexity → more scaffolding
            candidates.append(["role", "decompose", "scratchpad", "verify"])
            candidates.append(["planner", "scratchpad", "verify"])
        elif complexity > 0.4:
            # Medium complexity → moderate scaffolding
            candidates.append(["scratchpad", "verify"])
            candidates.append(["decompose", "verify"])
        else:
            # Low complexity → minimal scaffolding
            candidates.append([])
            candidates.append(["scratchpad"])
        
        # 4. Add task-specific strategies
        task_strategies = self._get_task_strategies(task_type)
        candidates.extend(task_strategies)
        
        # 5. Add mutated strategies (exploration)
        if candidates:
            for _ in range(3):
                base = random.choice(candidates)
                mutated = self._mutate_strategy(base)
                if mutated not in candidates:
                    candidates.append(mutated)
        
        # Deduplicate
        unique = []
        seen = set()
        
        for candidate in candidates:
            key = tuple(sorted(candidate))
            if key not in seen:
                seen.add(key)
                unique.append(candidate)
        
        return unique
    
    def _get_task_strategies(self, task_type: str) -> List[List[str]]:
        """Get strategies specific to a task type."""
        task_strategies = {
            "coding": [
                ["planner"],
                ["scratchpad", "verify"],
                ["role", "planner", "verify"],
            ],
            "debugging": [
                ["scratchpad", "verify"],
                ["decompose", "scratchpad", "verify"],
                ["role", "decompose", "verify"],
            ],
            "reasoning": [
                ["scratchpad"],
                ["scratchpad", "verify"],
                ["decompose", "scratchpad"],
            ],
            "discipline": [
                ["format"],
                ["constraints", "format"],
                ["role", "constraints"],
            ],
            "tools": [
                ["tools"],
                ["scratchpad", "tools"],
                ["planner", "tools"],
            ],
        }
        
        return task_strategies.get(task_type, [[]])
    
    def _mutate_strategy(self, strategy: List[str]) -> List[str]:
        """Mutate a strategy (for exploration)."""
        mutated = strategy.copy()
        
        # Random mutation
        mutation_type = random.choice(["add", "remove", "swap"])
        
        available_modules = list(STRATEGY_MODULES.keys())
        
        if mutation_type == "add" and available_modules:
            # Add random module
            new_module = random.choice(available_modules)
            if new_module not in mutated:
                mutated.append(new_module)
        
        elif mutation_type == "remove" and mutated:
            # Remove random module
            mutated.pop(random.randint(0, len(mutated) - 1))
        
        elif mutation_type == "swap" and mutated and available_modules:
            # Swap random module
            idx = random.randint(0, len(mutated) - 1)
            new_module = random.choice(available_modules)
            mutated[idx] = new_module
        
        return mutated
    
    def _score_candidate(
        self,
        modules: List[str],
        model: str,
        task_type: str,
        complexity: float,
    ) -> Dict[str, Any]:
        """
        Score a candidate strategy.

        Returns dict with:
        - predicted_success (0-1)
        - confidence (0-1)
        - reasoning (explanation)
        """
        score = 0.5  # Base score
        confidence = 0.5
        reasoning_parts = []

        # 1. Model preference bonus
        model_profile = self._get_model_profile(model)
        if model_profile:
            preferred = model_profile.get("preferred_strategies", {}).get(task_type)
            if preferred and set(modules) == set(preferred):
                score += 0.2
                reasoning_parts.append("Matches model preference")
                confidence += 0.2
        
        # 2. Genome success bonus
        if self.genome:
            genome_best = self.genome.query_best(model, task_type)
            if genome_best and genome_best.get("strategy"):
                if set(modules) == set(genome_best["strategy"]):
                    genome_score = genome_best.get("avg_score", 0.5)
                    score += genome_score * 0.3
                    reasoning_parts.append(f"Genome success: {genome_score:.2f}")
                    confidence += 0.3
        
        # 3. Module weight bonus
        module_weight_bonus = sum(
            self.module_weights.get(m, 1.0) for m in modules
        ) / max(len(modules), 1)
        
        score += (module_weight_bonus - 1.0) * 0.1
        reasoning_parts.append(f"Module weights: {module_weight_bonus:.2f}")
        
        # 4. Module interaction bonus/penalty
        interaction_bonus = self._get_interaction_bonus(modules)
        score += interaction_bonus * 0.1
        if interaction_bonus > 0:
            reasoning_parts.append(f"Positive interactions: {interaction_bonus:.2f}")
        elif interaction_bonus < 0:
            reasoning_parts.append(f"Negative interactions: {interaction_bonus:.2f}")
        
        # 5. Complexity matching
        if complexity > 0.7 and len(modules) >= 3:
            score += 0.1
            reasoning_parts.append("Good for high complexity")
        elif complexity < 0.3 and len(modules) <= 1:
            score += 0.1
            reasoning_parts.append("Efficient for low complexity")
        
        # 6. Task-specific bonuses
        if task_type == "discipline" and "format" in modules:
            score += 0.15
            reasoning_parts.append("Format module for discipline task")
        
        if task_type == "reasoning" and "scratchpad" in modules:
            score += 0.1
            reasoning_parts.append("Scratchpad for reasoning task")
        
        # 7. EXPLORATION BONUS (prevents strategy collapse)
        strategy_key = ",".join(sorted(modules))
        usage_count = self.strategy_usage.get(strategy_key, 0)
        
        if usage_count < 3:
            # Underused strategy gets exploration bonus
            exploration_bonus = self.exploration_bonus * (3 - usage_count) / 3
            score += exploration_bonus
            reasoning_parts.append(f"Exploration bonus: +{exploration_bonus:.2f}")
        
        # Clamp scores
        score = max(0.0, min(1.0, score))
        confidence = max(0.0, min(1.0, confidence))
        
        return {
            "predicted_success": score,
            "confidence": confidence,
            "reasoning": "; ".join(reasoning_parts),
        }
    
    def _get_interaction_bonus(self, modules: List[str]) -> float:
        """Get bonus/penalty for module interactions."""
        if len(modules) < 2:
            return 0.0
        
        bonus = 0.0
        
        for i, mod_a in enumerate(modules):
            for mod_b in modules[i+1:]:
                key = f"{mod_a}:{mod_b}"
                if key in self.interactions:
                    interaction = self.interactions[key]
                    bonus += interaction.avg_score_delta
        
        return bonus
    
    def _estimate_tokens(self, modules: List[str], prompt: str) -> int:
        """Estimate token cost for a strategy."""
        if not self.token_budget:
            # Fallback estimation
            prompt_tokens = len(prompt) // 4
            module_tokens = sum(
                STRATEGY_MODULES.get(m).cost_tokens if STRATEGY_MODULES.get(m) else 50
                for m in modules
            )
            response_tokens = prompt_tokens  # Rough estimate
            return prompt_tokens + module_tokens + response_tokens
        
        # Use token budget estimator
        _, total = self.token_budget.estimate_tokens(
            prompt, "unknown", modules
        )
        return total
    
    def _fallback_plan(self, task_type: str) -> StrategyPlan:
        """Generate fallback plan when planning fails."""
        fallback_strategies = {
            "coding": ["scratchpad", "verify"],
            "debugging": ["scratchpad", "verify"],
            "reasoning": ["scratchpad"],
            "discipline": ["format"],
            "tools": ["tools"],
            "chat": [],
        }
        
        modules = fallback_strategies.get(task_type, [])
        
        return StrategyPlan(
            modules=modules,
            predicted_success=0.5,
            estimated_tokens=200,
            confidence=0.3,
            reasoning="Fallback strategy",
        )
    
    def update_module_weight(self, module: str, success: bool, score: float):
        """
        Update module weight based on performance (reinforcement learning).
        
        Args:
            module: Module name
            success: Whether strategy succeeded
            score: Performance score
        """
        if module not in self.module_weights:
            self.module_weights[module] = 1.0
        
        # Reinforcement update
        if success:
            self.module_weights[module] += 0.02 * score
        else:
            self.module_weights[module] -= 0.02 * (1 - score)
        
        # Clamp
        self.module_weights[module] = max(0.5, min(2.0, self.module_weights[module]))
    
    def record_interaction(
        self,
        module_a: str,
        module_b: str,
        score_delta: float,
    ):
        """
        Record interaction effect between two modules.
        
        Args:
            module_a: First module
            module_b: Second module
            score_delta: Score impact of interaction
        """
        key = f"{module_a}:{module_b}"
        
        if key not in self.interactions:
            self.interactions[key] = ModuleInteraction(
                module_a=module_a,
                module_b=module_b,
                avg_score_delta=score_delta,
                occurrences=0,
            )
        else:
            interaction = self.interactions[key]
            # Running average
            interaction.avg_score_delta = (
                interaction.avg_score_delta * interaction.occurrences + score_delta
            ) / (interaction.occurrences + 1)
            interaction.occurrences += 1
