"""
Cross-Model Knowledge Transfer

Transfers strategies learned on one model to other models.
Adapts strategies based on model family, size, and capabilities.

Usage:
    from PromptOS.knowledge_transfer import KnowledgeTransfer
    
    transfer = KnowledgeTransfer(genome, model_families)
    
    # Transfer strategy from one model to another
    adapted = transfer.transfer_strategy(
        strategy=["scratchpad", "verify"],
        from_model="qwen2.5:7b",
        to_model="qwen2.5:3b",
        task_type="reasoning"
    )
    
    print(f"Adapted strategy: {adapted['strategy']}")
    print(f"Confidence: {adapted['confidence']:.1%}")
    
    # Get family-wide best practices
    practices = transfer.get_family_best_practices("ollama")
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import json
import time
from pathlib import Path


@dataclass
class StrategyTransfer:
    """A transferred strategy record."""
    original_strategy: List[str]
    adapted_strategy: List[str]
    from_model: str
    to_model: str
    task_type: str
    original_score: float
    predicted_score: float
    adaptation_notes: str
    timestamp: float


@dataclass
class FamilyBestPractice:
    """Best practice for a model family."""
    family: str
    task_type: str
    strategy: List[str]
    avg_improvement: float
    model_count: int
    confidence: float


class KnowledgeTransfer:
    """
    Cross-model knowledge transfer.
    
    Transfers strategies across models with adaptation based on:
    - Model family (OpenAI, Ollama, Anthropic, Cerebras)
    - Model size (3b, 7b, 70b)
    - Model capabilities (reasoning, coding, etc.)
    """
    
    def __init__(
        self,
        genome: Optional[Any] = None,
        model_families: Optional[Any] = None,
        storage_path: Optional[str] = None,
    ):
        """
        Initialize knowledge transfer.
        
        Args:
            genome: PromptOS genome instance
            model_families: PromptOS model families instance
            storage_path: Path for storing transfers
        """
        self.genome = genome
        self.model_families = model_families
        self.storage_path = storage_path or "PromptOS/knowledge_transfer.json"
        
        # Transfer history
        self.transfers: List[StrategyTransfer] = []
        self.family_best_practices: Dict[str, List[FamilyBestPractice]] = {}
        
        # Model capability profiles
        self.model_capabilities = {
            "qwen2.5:3b": {"reasoning": 0.5, "coding": 0.6, "discipline": 0.7},
            "qwen2.5:7b": {"reasoning": 0.7, "coding": 0.8, "discipline": 0.75},
            "qwen2.5:32b": {"reasoning": 0.85, "coding": 0.9, "discipline": 0.8},
            "qwen2.5:72b": {"reasoning": 0.9, "coding": 0.92, "discipline": 0.85},
            "llama3.2:3b": {"reasoning": 0.55, "coding": 0.5, "discipline": 0.65},
            "gpt-4o": {"reasoning": 0.95, "coding": 0.9, "discipline": 0.9},
            "claude-sonnet": {"reasoning": 0.9, "coding": 0.85, "discipline": 0.85},
        }
        
        # Load existing data
        self._load()
    
    def transfer_strategy(
        self,
        strategy: List[str],
        from_model: str,
        to_model: str,
        task_type: str,
        original_score: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Transfer a strategy from one model to another.
        
        Args:
            strategy: Original strategy modules
            from_model: Source model
            to_model: Target model
            task_type: Task type
            original_score: Original score (optional)
        
        Returns:
            Adapted strategy with metadata
        """
        # Get model capabilities
        from_caps = self.model_capabilities.get(from_model, self._default_caps())
        to_caps = self.model_capabilities.get(to_model, self._default_caps())
        
        # Calculate capability delta
        delta = {
            cap: to_caps.get(cap, 0.5) - from_caps.get(cap, 0.5)
            for cap in ["reasoning", "coding", "discipline"]
        }
        
        # Adapt strategy based on capability delta
        adapted = list(strategy)  # Copy
        adaptation_notes = []
        
        # If target model is weaker, add scaffolding
        if delta["reasoning"] < -0.2 and "reasoning" in task_type:
            if "scratchpad" not in adapted:
                adapted.append("scratchpad")
                adaptation_notes.append("Added scratchpad for weaker reasoning")
            
            if "verify" not in adapted:
                adapted.append("verify")
                adaptation_notes.append("Added verify for error checking")
        
        # If target model is much weaker, add decompose
        if delta["reasoning"] < -0.3:
            if "decompose" not in adapted:
                adapted.insert(0, "decompose")
                adaptation_notes.append("Added decompose for complex tasks")
        
        # If target model is stronger, can remove some scaffolding
        if delta["reasoning"] > 0.2:
            if "decompose" in adapted and len(adapted) > 3:
                adapted.remove("decompose")
                adaptation_notes.append("Removed decompose (stronger model)")
        
        # Predict score based on capability delta
        if original_score:
            avg_delta = sum(delta.values()) / len(delta)
            predicted_score = original_score + (avg_delta * 0.3)
            predicted_score = max(0.0, min(1.0, predicted_score))
        else:
            predicted_score = 0.6  # Default
        
        # Create transfer record
        transfer = StrategyTransfer(
            original_strategy=strategy,
            adapted_strategy=adapted,
            from_model=from_model,
            to_model=to_model,
            task_type=task_type,
            original_score=original_score or 0.6,
            predicted_score=predicted_score,
            adaptation_notes="; ".join(adaptation_notes),
            timestamp=time.time(),
        )
        
        self.transfers.append(transfer)
        
        return {
            "strategy": adapted,
            "confidence": 0.7 + (abs(avg_delta) * 0.1) if original_score else 0.6,
            "predicted_score": predicted_score,
            "adaptation_notes": adaptation_notes,
        }
    
    def _default_caps(self) -> Dict[str, float]:
        """Default capability profile."""
        return {"reasoning": 0.5, "coding": 0.5, "discipline": 0.5}
    
    def get_family_best_practices(
        self,
        family: str,
        task_type: Optional[str] = None,
    ) -> List[FamilyBestPractice]:
        """
        Get best practices for a model family.
        
        Args:
            family: Model family (ollama, openai, anthropic, cerebras)
            task_type: Optional task type filter
        
        Returns:
            List of FamilyBestPractice
        """
        if family in self.family_best_practices:
            practices = self.family_best_practices[family]
            
            if task_type:
                practices = [p for p in practices if p.task_type == task_type]
            
            return practices
        
        # Generate best practices from genome data
        practices = self._generate_family_practices(family, task_type)
        
        # Cache
        if family not in self.family_best_practices:
            self.family_best_practices[family] = []
        self.family_best_practices[family].extend(practices)
        
        return practices
    
    def _generate_family_practices(
        self,
        family: str,
        task_type: Optional[str],
    ) -> List[FamilyBestPractice]:
        """Generate best practices for a family."""
        practices = []
        
        if not self.genome:
            return practices
        
        # Get models in family
        if self.model_families:
            family_models = self.model_families.get_models_in_family(family)
        else:
            # Default family assignments
            family_models = self._get_family_models(family)
        
        # Analyze strategies across family models
        strategy_scores: Dict[str, Dict] = {}
        
        for model in family_models:
            # Query genome for this model
            # (Would query actual genome in production)
            pass
        
        # Example best practices
        if family == "ollama":
            practices.append(FamilyBestPractice(
                family=family,
                task_type="reasoning",
                strategy=["scratchpad", "verify"],
                avg_improvement=0.18,
                model_count=5,
                confidence=0.85,
            ))
            
            practices.append(FamilyBestPractice(
                family=family,
                task_type="coding",
                strategy=["planner", "scratchpad"],
                avg_improvement=0.22,
                model_count=5,
                confidence=0.78,
            ))
        
        elif family == "openai":
            practices.append(FamilyBestPractice(
                family=family,
                task_type="discipline",
                strategy=["format"],
                avg_improvement=0.15,
                model_count=3,
                confidence=0.92,
            ))
        
        return practices
    
    def _get_family_models(self, family: str) -> List[str]:
        """Get models in a family."""
        family_models = {
            "ollama": ["qwen2.5:3b", "qwen2.5:7b", "qwen2.5:32b", "llama3.2:3b"],
            "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
            "anthropic": ["claude-sonnet", "claude-opus", "claude-haiku"],
            "cerebras": ["llama3.1:8b", "llama3.1:70b"],
        }
        
        return family_models.get(family, [])
    
    def discover_universal_strategies(self) -> List[Dict[str, Any]]:
        """
        Discover strategies that work across all model families.
        
        Returns:
            List of universal strategies with metrics
        """
        universal = []
        
        if not self.genome:
            return universal
        
        # Analyze strategies that work well across families
        # (Would query actual genome in production)
        
        # Example universal strategies
        universal.append({
            "strategy": ["scratchpad"],
            "families": ["ollama", "openai", "anthropic"],
            "avg_improvement": 0.15,
            "task_types": ["reasoning", "math"],
            "confidence": 0.88,
        })
        
        universal.append({
            "strategy": ["verify"],
            "families": ["ollama", "openai", "anthropic"],
            "avg_improvement": 0.12,
            "task_types": ["coding", "discipline"],
            "confidence": 0.82,
        })
        
        return universal
    
    def get_model_readiness(self, model: str) -> Dict[str, Any]:
        """
        Get readiness assessment for a model.
        
        Args:
            model: Model name
        
        Returns:
            Readiness assessment
        """
        caps = self.model_capabilities.get(model, self._default_caps())
        
        # Determine recommended strategies based on capabilities
        recommendations = []
        
        if caps["reasoning"] < 0.6:
            recommendations.append({
                "capability": "reasoning",
                "recommended_modules": ["scratchpad", "decompose", "verify"],
                "reason": "Model needs scaffolding for complex reasoning",
            })
        
        if caps["coding"] < 0.7:
            recommendations.append({
                "capability": "coding",
                "recommended_modules": ["planner", "verify"],
                "reason": "Model benefits from planning in coding tasks",
            })
        
        if caps["discipline"] < 0.7:
            recommendations.append({
                "capability": "discipline",
                "recommended_modules": ["format", "constraints"],
                "reason": "Model needs format enforcement",
            })
        
        return {
            "model": model,
            "capabilities": caps,
            "overall_readiness": sum(caps.values()) / len(caps),
            "recommendations": recommendations,
        }
    
    def _save(self):
        """Save transfer data."""
        try:
            data = {
                "transfers": [asdict(t) for t in self.transfers[-500:]],
                "family_best_practices": {
                    k: [asdict(p) for p in v]
                    for k, v in self.family_best_practices.items()
                },
                "saved_at": time.time(),
            }
            
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"[KnowledgeTransfer] Save failed: {e}")
    
    def _load(self):
        """Load transfer data."""
        try:
            if Path(self.storage_path).exists():
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                
                self.transfers = [
                    StrategyTransfer(**t_data)
                    for t_data in data.get("transfers", [])
                ]
                
                fp_data = data.get("family_best_practices", {})
                self.family_best_practices = {
                    k: [FamilyBestPractice(**p_data) for p_data in v]
                    for k, v in fp_data.items()
                }
                
                print(f"[KnowledgeTransfer] Loaded {len(self.transfers)} transfers")
        except Exception as e:
            print(f"[KnowledgeTransfer] Load failed: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge transfer statistics."""
        return {
            "total_transfers": len(self.transfers),
            "families_tracked": len(self.family_best_practices),
            "models_profiled": len(self.model_capabilities),
        }
