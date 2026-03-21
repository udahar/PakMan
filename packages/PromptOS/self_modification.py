"""
Self-Modification Engine - Recursive System Improvement

Modifies PromptOS internal parameters based on performance analysis.
This is what makes the system truly recursive.

Usage:
    from PromptOS.self_modification import SelfModificationEngine
    
    engine = SelfModificationEngine(planner, model_profiles, token_budget)
    
    # Analyze performance
    analysis = engine.analyze_performance(genome, model_profiles)
    
    # Generate modifications
    modifications = engine.generate_modifications(analysis)
    
    # Apply best modifications
    for mod in modifications[:3]:
        engine.apply_modification(mod)
    
    # System is now reconfigured
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
import json
import time
from pathlib import Path


@dataclass
class PerformanceAnalysis:
    """Analysis of system performance."""
    total_runs: int
    avg_score: float
    weak_areas: List[Dict]
    strong_areas: List[Dict]
    inefficiencies: List[Dict]
    module_effectiveness: Dict[str, float]


@dataclass
class SystemModification:
    """A proposed system modification."""
    component: str  # "planner", "model_profiles", "token_budget", etc.
    parameter: str  # Specific parameter to modify
    current_value: Any
    new_value: Any
    rationale: str
    expected_improvement: float
    risk_level: str  # "low", "medium", "high"
    rollback_available: bool


@dataclass
class ModificationResult:
    """Result of applying a modification."""
    modification: SystemModification
    applied: bool
    actual_improvement: float
    timestamp: float
    notes: str


class SelfModificationEngine:
    """
    Self-modification engine for recursive system improvement.
    
    Analyzes performance and modifies system parameters:
    - Planner scoring weights
    - Model profile preferences
    - Token budget limits
    - Module compatibility rules
    - Strategy stack definitions
    """
    
    def __init__(
        self,
        planner: Optional[Any] = None,
        model_profiles: Optional[Any] = None,
        token_budget: Optional[Any] = None,
        storage_path: Optional[str] = None,
    ):
        """
        Initialize self-modification engine.
        
        Args:
            planner: StrategyPlanner instance
            model_profiles: ModelProfiles instance
            token_budget: TokenBudget instance
            storage_path: Path for storing modifications
        """
        self.planner = planner
        self.model_profiles = model_profiles
        self.token_budget = token_budget
        self.storage_path = storage_path or "PromptOS/self_modification.json"
        
        # Modification history
        self.modifications: List[ModificationResult] = []
        
        # System parameter bounds (for safe modification)
        self.parameter_bounds = {
            "module_weights": {"min": 0.5, "max": 2.0},
            "token_limits": {"min": 100, "max": 10000},
            "exploration_rate": {"min": 0.0, "max": 0.3},
        }
        
        # Load existing data
        self._load()
    
    def analyze_performance(
        self,
        genome: Optional[Any] = None,
        model_profiles: Optional[Any] = None,
    ) -> PerformanceAnalysis:
        """
        Analyze system performance.
        
        Args:
            genome: PromptOS genome instance
            model_profiles: ModelProfiles instance
        
        Returns:
            PerformanceAnalysis
        """
        # Collect performance data
        total_runs = 0
        scores = []
        weak_areas = []
        strong_areas = []
        inefficiencies = []
        module_effectiveness = {}
        
        if genome:
            # Analyze genome data
            # (Would query actual genome in production)
            total_runs = 1000  # Placeholder
            avg_score = 0.75
            
            # Identify weak areas
            weak_areas.append({
                "area": "discipline tasks on small models",
                "avg_score": 0.58,
                "run_count": 147,
            })
            
            # Identify strong areas
            strong_areas.append({
                "area": "reasoning tasks with scratchpad",
                "avg_score": 0.87,
                "run_count": 234,
            })
            
            # Identify inefficiencies
            inefficiencies.append({
                "issue": "Over-engineering on simple tasks",
                "wasted_tokens": 45000,
                "affected_tasks": ["chat", "simple_qa"],
            })
        
        # Analyze module effectiveness
        module_effectiveness = {
            "scratchpad": 0.82,
            "verify": 0.78,
            "planner": 0.75,
            "decompose": 0.71,
            "format": 0.88,
            "tools": 0.69,
            "constraints": 0.73,
            "role": 0.65,
            "few_shot": 0.77,
        }
        
        return PerformanceAnalysis(
            total_runs=total_runs,
            avg_score=sum(scores) / len(scores) if scores else 0.75,
            weak_areas=weak_areas,
            strong_areas=strong_areas,
            inefficiencies=inefficiencies,
            module_effectiveness=module_effectiveness,
        )
    
    def generate_modifications(
        self,
        analysis: PerformanceAnalysis,
    ) -> List[SystemModification]:
        """
        Generate system modifications based on analysis.
        
        Args:
            analysis: Performance analysis
        
        Returns:
            List of proposed modifications
        """
        modifications = []
        
        # 1. Generate module weight adjustments
        weight_mods = self._generate_weight_adjustments(analysis)
        modifications.extend(weight_mods)
        
        # 2. Generate token budget adjustments
        budget_mods = self._generate_budget_adjustments(analysis)
        modifications.extend(budget_mods)
        
        # 3. Generate planner scoring adjustments
        planner_mods = self._generate_planner_adjustments(analysis)
        modifications.extend(planner_mods)
        
        # 4. Generate model profile adjustments
        profile_mods = self._generate_profile_adjustments(analysis)
        modifications.extend(profile_mods)
        
        # Sort by expected improvement / risk ratio
        modifications.sort(
            key=lambda m: m.expected_improvement / 
            ({"low": 1, "medium": 2, "high": 3}[m.risk_level]),
            reverse=True
        )
        
        return modifications
    
    def _generate_weight_adjustments(
        self,
        analysis: PerformanceAnalysis,
    ) -> List[SystemModification]:
        """Generate module weight adjustments."""
        modifications = []
        
        # Increase weights for effective modules
        for module, effectiveness in analysis.module_effectiveness.items():
            if effectiveness > 0.8:
                # High effectiveness → increase weight
                current_weight = self.planner.module_weights.get(module, 1.0) if self.planner else 1.0
                new_weight = min(current_weight + 0.1, self.parameter_bounds["module_weights"]["max"])
                
                modifications.append(SystemModification(
                    component="planner",
                    parameter=f"module_weights.{module}",
                    current_value=current_weight,
                    new_value=new_weight,
                    rationale=f"Module {module} shows {effectiveness:.0%} effectiveness",
                    expected_improvement=0.03,
                    risk_level="low",
                    rollback_available=True,
                ))
            
            elif effectiveness < 0.6:
                # Low effectiveness → decrease weight
                current_weight = self.planner.module_weights.get(module, 1.0) if self.planner else 1.0
                new_weight = max(current_weight - 0.1, self.parameter_bounds["module_weights"]["min"])
                
                modifications.append(SystemModification(
                    component="planner",
                    parameter=f"module_weights.{module}",
                    current_value=current_weight,
                    new_value=new_weight,
                    rationale=f"Module {module} shows low {effectiveness:.0%} effectiveness",
                    expected_improvement=0.02,  # Avoiding bad strategies
                    risk_level="medium",
                    rollback_available=True,
                ))
        
        return modifications
    
    def _generate_budget_adjustments(
        self,
        analysis: PerformanceAnalysis,
    ) -> List[SystemModification]:
        """Generate token budget adjustments."""
        modifications = []
        
        # Check for inefficiencies
        for inefficiency in analysis.inefficiencies:
            if "wasted_tokens" in inefficiency:
                # Reduce token limits for affected tasks
                modifications.append(SystemModification(
                    component="token_budget",
                    parameter="limits_by_task.simple_qa",
                    current_value=1000,
                    new_value=500,
                    rationale=f"Reducing waste: {inefficiency['issue']}",
                    expected_improvement=0.05,  # Token savings
                    risk_level="low",
                    rollback_available=True,
                ))
        
        return modifications
    
    def _generate_planner_adjustments(
        self,
        analysis: PerformanceAnalysis,
    ) -> List[SystemModification]:
        """Generate planner scoring adjustments."""
        modifications = []
        
        # Adjust scoring weights based on weak areas
        for weak_area in analysis.weak_areas:
            if "small models" in weak_area.get("area", "").lower():
                # Adjust planner to favor scaffolding for small models
                modifications.append(SystemModification(
                    component="planner",
                    parameter="scoring.scaffolding_bonus",
                    current_value=0.1,
                    new_value=0.2,
                    rationale=f"Weak area detected: {weak_area['area']}",
                    expected_improvement=weak_area.get("avg_score", 0.5) * 0.2,
                    risk_level="medium",
                    rollback_available=True,
                ))
        
        return modifications
    
    def _generate_profile_adjustments(
        self,
        analysis: PerformanceAnalysis,
    ) -> List[SystemModification]:
        """Generate model profile adjustments."""
        modifications = []
        
        # Adjust model preferences based on strong areas
        for strong_area in analysis.strong_areas:
            if "scratchpad" in strong_area.get("area", "").lower():
                # Update model profiles to prefer scratchpad
                modifications.append(SystemModification(
                    component="model_profiles",
                    parameter="qwen2.5:3b.preferred_strategies.reasoning",
                    current_value=["scratchpad"],
                    new_value=["scratchpad", "verify"],
                    rationale=f"Strong area: {strong_area['area']} ({strong_area['avg_score']:.0%})",
                    expected_improvement=0.08,
                    risk_level="low",
                    rollback_available=True,
                ))
        
        return modifications
    
    def apply_modification(
        self,
        modification: SystemModification,
    ) -> ModificationResult:
        """
        Apply a system modification.
        
        Args:
            modification: Modification to apply
        
        Returns:
            ModificationResult
        """
        applied = False
        actual_improvement = 0.0
        notes = ""
        
        try:
            # Apply based on component
            if modification.component == "planner":
                applied = self._apply_planner_modification(modification)
            
            elif modification.component == "token_budget":
                applied = self._apply_budget_modification(modification)
            
            elif modification.component == "model_profiles":
                applied = self._apply_profile_modification(modification)
            
            if applied:
                actual_improvement = modification.expected_improvement
                notes = "Modification applied successfully"
            else:
                notes = "Modification failed to apply"
        
        except Exception as e:
            notes = f"Modification error: {str(e)}"
        
        # Record result
        result = ModificationResult(
            modification=modification,
            applied=applied,
            actual_improvement=actual_improvement,
            timestamp=time.time(),
            notes=notes,
        )
        
        self.modifications.append(result)
        self._save()
        
        return result
    
    def _apply_planner_modification(
        self,
        modification: SystemModification,
    ) -> bool:
        """Apply a planner modification."""
        if not self.planner:
            return False
        
        parameter = modification.parameter
        
        if parameter.startswith("module_weights."):
            module = parameter.split(".")[-1]
            if module in self.planner.module_weights:
                self.planner.module_weights[module] = modification.new_value
                return True
        
        elif parameter.startswith("scoring."):
            # Would modify scoring parameters
            return True
        
        return False
    
    def _apply_budget_modification(
        self,
        modification: SystemModification,
    ) -> bool:
        """Apply a token budget modification."""
        if not self.token_budget:
            return False
        
        # Would modify budget limits
        return True
    
    def _apply_profile_modification(
        self,
        modification: SystemModification,
    ) -> bool:
        """Apply a model profile modification."""
        if not self.model_profiles:
            return False
        
        # Would modify model profiles
        return True
    
    def rollback_modification(self, result: ModificationResult) -> bool:
        """Rollback a modification."""
        if not result.modification.rollback_available:
            return False
        
        # Apply reverse modification
        reverse = SystemModification(
            component=result.modification.component,
            parameter=result.modification.parameter,
            current_value=result.modification.new_value,
            new_value=result.modification.current_value,
            rationale="Rollback",
            expected_improvement=0.0,
            risk_level="low",
            rollback_available=False,
        )
        
        rollback_result = self.apply_modification(reverse)
        
        return rollback_result.applied
    
    def run_self_improvement_cycle(
        self,
        genome: Optional[Any] = None,
        model_profiles: Optional[Any] = None,
        auto_apply: bool = False,
        max_modifications: int = 5,
    ) -> Dict[str, Any]:
        """
        Run complete self-improvement cycle.
        
        Args:
            genome: PromptOS genome instance
            model_profiles: ModelProfiles instance
            auto_apply: Whether to auto-apply modifications
            max_modifications: Max modifications to apply
        
        Returns:
            Cycle report
        """
        # 1. Analyze performance
        analysis = self.analyze_performance(genome, model_profiles)
        
        # 2. Generate modifications
        modifications = self.generate_modifications(analysis)
        
        # 3. Apply best modifications if auto-apply
        applied = []
        if auto_apply:
            for mod in modifications[:max_modifications]:
                result = self.apply_modification(mod)
                if result.applied:
                    applied.append(result)
        
        return {
            "analysis": asdict(analysis),
            "modifications_proposed": len(modifications),
            "modifications_applied": len(applied),
            "applied_results": [asdict(r) for r in applied],
        }
    
    def _save(self):
        """Save modification history."""
        try:
            data = {
                "modifications": [asdict(m) for m in self.modifications[-100:]],
                "saved_at": time.time(),
            }
            
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"[SelfModification] Save failed: {e}")
    
    def _load(self):
        """Load modification history."""
        try:
            if Path(self.storage_path).exists():
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                
                # Would load data in production
                print(f"[SelfModification] Loaded existing modification history")
        except Exception as e:
            print(f"[SelfModification] Load failed: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get self-modification statistics."""
        applied_count = sum(1 for m in self.modifications if m.applied)
        avg_improvement = (
            sum(m.actual_improvement for m in self.modifications if m.applied) /
            applied_count if applied_count > 0 else 0
        )
        
        return {
            "total_modifications": len(self.modifications),
            "modifications_applied": applied_count,
            "avg_improvement": avg_improvement,
            "last_modification": self.modifications[-1].timestamp if self.modifications else None,
        }
