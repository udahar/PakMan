"""
Model Behavior Profiles

Tracks how models perform across different capabilities and strategies.
Discovers patterns like "Model X improves 35% with strategy Y for capability Z".

Usage:
    from PromptOS.profiles import ModelBehaviorProfiles
    
    profiles = ModelBehaviorProfiles()
    
    # Record test result
    profiles.record_test_result(
        model="qwen2.5:7b",
        test="json_formatting",
        capability="discipline",
        strategy="baseline",
        score=0.64
    )
    
    # Record strategy improvement
    profiles.record_strategy_improvement(
        model="qwen2.5:7b",
        test="json_formatting",
        baseline_strategy="baseline",
        baseline_score=0.64,
        improved_strategy="strict_json",
        improved_score=0.93
    )
    
    # Get model profile
    profile = profiles.get_model_profile("qwen2.5:7b")
    
    # Get strategy recommendation
    recommendation = profiles.get_best_strategy("qwen2.5:7b", "discipline")
"""

import json
import time
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict, field
from datetime import datetime


@dataclass
class TestResult:
    """Result from a single test run."""
    model: str
    test_name: str
    capability: str
    strategy: str
    score: float
    timestamp: float
    ticket_id: Optional[str] = None
    failure_mode: Optional[str] = None


@dataclass
class StrategyImprovement:
    """Record of strategy improvement."""
    model: str
    test_name: str
    capability: str
    baseline_strategy: str
    baseline_score: float
    improved_strategy: str
    improved_score: float
    improvement_pct: float
    timestamp: float


@dataclass
class ModelCapabilityProfile:
    """Profile for a model's capability."""
    capability: str
    avg_score: float
    test_count: int
    weak_areas: List[str]
    strong_areas: List[str]
    best_strategy: Optional[str]
    improvement_potential: float


@dataclass
class ModelProfile:
    """Complete profile for a model."""
    model: str
    overall_avg: float
    total_tests: int
    capabilities: Dict[str, ModelCapabilityProfile]
    best_strategies: Dict[str, str]  # capability → best strategy
    improvement_opportunities: List[Dict]
    last_updated: float


class ModelBehaviorProfiles:
    """
    Model behavior profile tracking.
    
    Features:
    - Track performance by capability
    - Record strategy improvements
    - Discover model-specific patterns
    - Generate recommendations
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize model behavior profiles.
        
        Args:
            storage_path: Path for persistent storage
        """
        self.storage_path = storage_path or "PromptOS/model_profiles.json"
        
        # Data storage
        self.test_results: List[TestResult] = []
        self.strategy_improvements: List[StrategyImprovement] = []
        
        # Cached profiles
        self._model_profiles: Dict[str, ModelProfile] = {}
        
        # Capability categories
        self.capability_categories = {
            "discipline": ["json_formatting", "schema_compliance", "format_adherence", "constraint_following"],
            "reasoning": ["logic", "math", "complex_reasoning", "multi_step"],
            "tool_use": ["tool_selection", "tool_execution", "error_handling"],
            "communication": ["verbosity_control", "explanation_suppression", "clarity"],
            "coding": ["code_quality", "testing", "debugging", "implementation"],
        }
        
        # Load existing data
        self._load()
    
    def record_test_result(
        self,
        model: str,
        test_name: str,
        capability: str,
        strategy: str,
        score: float,
        ticket_id: Optional[str] = None,
        failure_mode: Optional[str] = None,
    ):
        """
        Record a test result.
        
        Args:
            model: Model name
            test_name: Test name
            capability: Capability category
            strategy: Strategy used
            score: Test score (0-1)
            ticket_id: Optional ticket ID
            failure_mode: Optional failure mode
        """
        result = TestResult(
            model=model,
            test_name=test_name,
            capability=capability,
            strategy=strategy,
            score=score,
            timestamp=time.time(),
            ticket_id=ticket_id,
            failure_mode=failure_mode,
        )
        
        self.test_results.append(result)
        
        # Invalidate cached profile
        if model in self._model_profiles:
            del self._model_profiles[model]
        
        # Auto-save
        if len(self.test_results) % 100 == 0:
            self._save()
    
    def record_strategy_improvement(
        self,
        model: str,
        test_name: str,
        capability: str,
        baseline_strategy: str,
        baseline_score: float,
        improved_strategy: str,
        improved_score: float,
    ):
        """
        Record a strategy improvement.
        
        Args:
            model: Model name
            test_name: Test name
            capability: Capability category
            baseline_strategy: Baseline strategy
            baseline_score: Baseline score
            improved_strategy: Improved strategy
            improved_score: Improved score
        """
        improvement_pct = ((improved_score - baseline_score) / baseline_score) * 100 if baseline_score > 0 else 0
        
        record = StrategyImprovement(
            model=model,
            test_name=test_name,
            capability=capability,
            baseline_strategy=baseline_strategy,
            baseline_score=baseline_score,
            improved_strategy=improved_strategy,
            improved_score=improved_score,
            improvement_pct=improvement_pct,
            timestamp=time.time(),
        )
        
        self.strategy_improvements.append(record)
        
        # Auto-save
        if len(self.strategy_improvements) % 50 == 0:
            self._save()
    
    def get_model_profile(self, model: str) -> Optional[ModelProfile]:
        """
        Get complete profile for a model.
        
        Args:
            model: Model name
        
        Returns:
            Model profile or None
        """
        # Return cached if available
        if model in self._model_profiles:
            return self._model_profiles[model]
        
        # Build profile from data
        model_results = [r for r in self.test_results if r.model == model]
        
        if not model_results:
            return None
        
        # Calculate overall average
        overall_avg = sum(r.score for r in model_results) / len(model_results)
        
        # Group by capability
        by_capability: Dict[str, List[TestResult]] = {}
        for result in model_results:
            if result.capability not in by_capability:
                by_capability[result.capability] = []
            by_capability[result.capability].append(result)
        
        # Build capability profiles
        capabilities = {}
        best_strategies = {}
        
        for cap, results in by_capability.items():
            avg_score = sum(r.score for r in results) / len(results)
            
            # Find weak and strong areas (specific tests)
            by_test: Dict[str, List[TestResult]] = {}
            for r in results:
                if r.test_name not in by_test:
                    by_test[r.test_name] = []
                by_test[r.test_name].append(r)
            
            weak_areas = []
            strong_areas = []
            
            for test_name, test_results in by_test.items():
                test_avg = sum(r.score for r in test_results) / len(test_results)
                if test_avg < 0.7:
                    weak_areas.append(test_name)
                elif test_avg > 0.9:
                    strong_areas.append(test_name)
            
            # Find best strategy for this capability
            strategy_scores: Dict[str, List[float]] = {}
            for r in results:
                if r.strategy not in strategy_scores:
                    strategy_scores[r.strategy] = []
                strategy_scores[r.strategy].append(r.score)
            
            best_strategy = None
            best_avg = 0
            
            for strategy, scores in strategy_scores.items():
                avg = sum(scores) / len(scores)
                if avg > best_avg:
                    best_avg = avg
                    best_strategy = strategy
            
            best_strategies[cap] = best_strategy
            
            # Calculate improvement potential
            if strategy_scores:
                max_possible = max(sum(scores) / len(scores) for scores in strategy_scores.values())
                improvement_potential = max_possible - avg_score
            else:
                improvement_potential = 0
            
            capabilities[cap] = ModelCapabilityProfile(
                capability=cap,
                avg_score=avg_score,
                test_count=len(results),
                weak_areas=weak_areas,
                strong_areas=strong_areas,
                best_strategy=best_strategy,
                improvement_potential=improvement_potential,
            )
        
        # Find improvement opportunities
        improvement_opportunities = []
        
        for improvement in self.strategy_improvements:
            if improvement.model == model and improvement.improvement_pct > 20:
                improvement_opportunities.append({
                    "capability": improvement.capability,
                    "test": improvement.test_name,
                    "from_strategy": improvement.baseline_strategy,
                    "to_strategy": improvement.improved_strategy,
                    "improvement_pct": improvement.improvement_pct,
                })
        
        profile = ModelProfile(
            model=model,
            overall_avg=overall_avg,
            total_tests=len(model_results),
            capabilities=capabilities,
            best_strategies=best_strategies,
            improvement_opportunities=improvement_opportunities,
            last_updated=time.time(),
        )
        
        # Cache and return
        self._model_profiles[model] = profile
        return profile
    
    def get_best_strategy(self, model: str, capability: str) -> Optional[str]:
        """
        Get best strategy for a model/capability combination.
        
        Args:
            model: Model name
            capability: Capability category
        
        Returns:
            Best strategy or None
        """
        profile = self.get_model_profile(model)
        
        if not profile:
            return None
        
        return profile.best_strategies.get(capability)
    
    def get_improvement_potential(self, model: str, capability: str) -> float:
        """
        Get improvement potential for a model/capability.
        
        Args:
            model: Model name
            capability: Capability category
        
        Returns:
            Improvement potential (0-1)
        """
        profile = self.get_model_profile(model)
        
        if not profile or capability not in profile.capabilities:
            return 0.0
        
        return profile.capabilities[capability].improvement_potential
    
    def get_weak_areas(self, model: str) -> Dict[str, List[str]]:
        """
        Get weak areas for a model.
        
        Args:
            model: Model name
        
        Returns:
            Dict mapping capability → list of weak test names
        """
        profile = self.get_model_profile(model)
        
        if not profile:
            return {}
        
        return {
            cap: prof.weak_areas
            for cap, prof in profile.capabilities.items()
            if prof.weak_areas
        }
    
    def get_strategy_recommendations(self, model: str) -> List[Dict[str, Any]]:
        """
        Get strategy recommendations for a model.
        
        Args:
            model: Model name
        
        Returns:
            List of recommendations
        """
        profile = self.get_model_profile(model)
        
        if not profile:
            return []
        
        recommendations = []
        
        # Recommend strategies for weak areas
        for capability, cap_profile in profile.capabilities.items():
            if cap_profile.weak_areas and cap_profile.best_strategy:
                recommendations.append({
                    "capability": capability,
                    "weak_areas": cap_profile.weak_areas,
                    "recommendation": f"Use '{cap_profile.best_strategy}' strategy",
                    "expected_improvement": cap_profile.improvement_potential,
                })
        
        # Add historical improvements
        for opp in profile.improvement_opportunities:
            recommendations.append({
                "capability": opp["capability"],
                "recommendation": f"Switch from '{opp['from_strategy']}' to '{opp['to_strategy']}'",
                "expected_improvement": opp["improvement_pct"] / 100,
                "based_on": "historical data",
            })
        
        return recommendations
    
    def compare_models(self, models: List[str]) -> Dict[str, Any]:
        """
        Compare multiple models.
        
        Args:
            models: List of model names
        
        Returns:
            Comparison data
        """
        profiles = {m: self.get_model_profile(m) for m in models}
        
        return {
            "models": models,
            "profiles": {m: asdict(p) if p else None for m, p in profiles.items()},
            "ranking": sorted(
                [(m, p.overall_avg if p else 0) for m, p in profiles.items()],
                key=lambda x: x[1],
                reverse=True,
            ),
        }
    
    def get_capability_leaders(self, capability: str) -> List[Tuple[str, float]]:
        """
        Get top models for a capability.
        
        Args:
            capability: Capability category
        
        Returns:
            List of (model, score) tuples
        """
        leaders = []
        
        for model in set(r.model for r in self.test_results):
            profile = self.get_model_profile(model)
            
            if profile and capability in profile.capabilities:
                leaders.append((model, profile.capabilities[capability].avg_score))
        
        return sorted(leaders, key=lambda x: x[1], reverse=True)
    
    def _save(self):
        """Save profiles to storage."""
        try:
            data = {
                "test_results": [asdict(r) for r in self.test_results[-2000:]],
                "strategy_improvements": [asdict(r) for r in self.strategy_improvements[-500:]],
                "saved_at": time.time(),
            }
            
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"[ModelProfiles] Save failed: {e}")
    
    def _load(self):
        """Load profiles from storage."""
        try:
            if Path(self.storage_path).exists():
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                
                self.test_results = [TestResult(**r) for r in data.get("test_results", [])]
                self.strategy_improvements = [StrategyImprovement(**r) for r in data.get("strategy_improvements", [])]
                
                print(f"[ModelProfiles] Loaded {len(self.test_results)} test results")
        except Exception as e:
            print(f"[ModelProfiles] Load failed: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get profile statistics."""
        return {
            "total_test_results": len(self.test_results),
            "total_improvements": len(self.strategy_improvements),
            "models_tracked": len(set(r.model for r in self.test_results)),
            "capabilities_tracked": len(set(r.capability for r in self.test_results)),
        }
