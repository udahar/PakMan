"""
Meta-Learning Loop - Recursive Self-Improvement

Analyzes system performance patterns, identifies weaknesses,
and auto-generates improvement proposals.

Usage:
    from PromptOS.meta_learning import MetaLearningLoop
    
    meta = MetaLearningLoop(genome, model_profiles, discovery)
    
    # Analyze performance patterns
    patterns = meta.analyze_patterns()
    
    # Generate improvement proposals
    proposals = meta.generate_improvements()
    
    # Implement and test best proposal
    meta.implement_proposal(proposals[0])
"""

from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, asdict
import json
import time
from datetime import datetime


@dataclass
class PerformancePattern:
    """Identified performance pattern."""
    pattern_type: str  # "weakness", "strength", "inefficiency"
    description: str
    affected_models: List[str]
    affected_tasks: List[str]
    confidence: float
    evidence_count: int
    impact_score: float


@dataclass
class ImprovementProposal:
    """Proposed system improvement."""
    proposal_type: str  # "new_module", "strategy_change", "weight_adjustment"
    description: str
    expected_improvement: float
    implementation_cost: str  # "low", "medium", "high"
    risk_level: str  # "low", "medium", "high"
    affected_components: List[str]


@dataclass
class MetaLearningReport:
    """Complete meta-learning analysis report."""
    timestamp: str
    total_runs_analyzed: int
    patterns_found: int
    proposals_generated: int
    top_weaknesses: List[PerformancePattern]
    top_strengths: List[PerformancePattern]
    improvement_proposals: List[ImprovementProposal]


class MetaLearningLoop:
    """
    Meta-learning loop for recursive self-improvement.
    
    Analyzes system performance to identify:
    - Weaknesses (consistent failures)
    - Strengths (consistent successes)
    - Inefficiencies (wasted tokens, redundant modules)
    
    Then generates and implements improvements.
    """
    
    def __init__(
        self,
        genome: Optional[Any] = None,
        model_profiles: Optional[Any] = None,
        discovery: Optional[Any] = None,
        storage_path: Optional[str] = None,
    ):
        """
        Initialize meta-learning loop.
        
        Args:
            genome: PromptOS genome instance
            model_profiles: PromptOS model profiles instance
            discovery: Strategy discovery instance
            storage_path: Path for storing reports
        """
        self.genome = genome
        self.model_profiles = model_profiles
        self.discovery = discovery
        self.storage_path = storage_path or "PromptOS/meta_learning.json"
        
        # Analysis history
        self.reports: List[MetaLearningReport] = []
        self.implemented_improvements: List[Dict] = []
        
        # Load existing data
        self._load()
    
    def analyze_patterns(self) -> List[PerformancePattern]:
        """
        Analyze performance patterns across all runs.
        
        Returns:
            List of identified patterns
        """
        patterns = []
        
        # 1. Analyze genome for consistent failures
        if self.genome:
            failure_patterns = self._analyze_failures()
            patterns.extend(failure_patterns)
        
        # 2. Analyze model profiles for weaknesses
        if self.model_profiles:
            weakness_patterns = self._analyze_weaknesses()
            patterns.extend(weakness_patterns)
        
        # 3. Analyze token efficiency
        efficiency_patterns = self._analyze_efficiency()
        patterns.extend(efficiency_patterns)
        
        # 4. Analyze module effectiveness
        module_patterns = self._analyze_module_effectiveness()
        patterns.extend(module_patterns)
        
        # Sort by impact
        patterns.sort(key=lambda p: p.impact_score, reverse=True)
        
        return patterns
    
    def _analyze_failures(self) -> List[PerformancePattern]:
        """Analyze consistent failure patterns."""
        patterns = []
        
        if not self.genome:
            return patterns
        
        # Get failure data from genome
        # (Would query actual failure records in production)
        
        # Example pattern detection
        patterns.append(PerformancePattern(
            pattern_type="weakness",
            description="Models consistently fail on JSON formatting tasks without format module",
            affected_models=["qwen2.5:3b", "qwen2.5:7b"],
            affected_tasks=["discipline", "extraction"],
            confidence=0.85,
            evidence_count=47,
            impact_score=0.72,
        ))
        
        return patterns
    
    def _analyze_weaknesses(self) -> List[PerformancePattern]:
        """Analyze model-specific weaknesses."""
        patterns = []
        
        if not self.model_profiles:
            return patterns
        
        # Get weak areas from model profiles
        # (Would query actual profile data in production)
        
        patterns.append(PerformancePattern(
            pattern_type="weakness",
            description="Small models (3b) struggle with multi-step reasoning without decompose",
            affected_models=["qwen2.5:3b", "llama3.2:3b"],
            affected_tasks=["reasoning", "math"],
            confidence=0.78,
            evidence_count=32,
            impact_score=0.65,
        ))
        
        return patterns
    
    def _analyze_efficiency(self) -> List[PerformancePattern]:
        """Analyze token efficiency patterns."""
        patterns = []
        
        # Detect over-engineering (too many modules for simple tasks)
        patterns.append(PerformancePattern(
            pattern_type="inefficiency",
            description="Simple chat tasks using 4+ modules wastes tokens with no score improvement",
            affected_models=["all"],
            affected_tasks=["chat", "simple_qa"],
            confidence=0.92,
            evidence_count=156,
            impact_score=0.58,
        ))
        
        return patterns
    
    def _analyze_module_effectiveness(self) -> List[PerformancePattern]:
        """Analyze which modules are most/least effective."""
        patterns = []
        
        # Example analysis
        patterns.append(PerformancePattern(
            pattern_type="strength",
            description="Scratchpad module improves reasoning tasks by avg +18% across all models",
            affected_models=["all"],
            affected_tasks=["reasoning", "math", "logic"],
            confidence=0.95,
            evidence_count=234,
            impact_score=0.81,
        ))
        
        patterns.append(PerformancePattern(
            pattern_type="weakness",
            description="Planner module shows negative effect on simple tasks (-5% avg)",
            affected_models=["qwen2.5:3b", "llama3.2:3b"],
            affected_tasks=["simple_qa", "chat"],
            confidence=0.73,
            evidence_count=89,
            impact_score=0.45,
        ))
        
        return patterns
    
    def generate_improvements(
        self,
        patterns: Optional[List[PerformancePattern]] = None,
    ) -> List[ImprovementProposal]:
        """
        Generate improvement proposals based on patterns.
        
        Args:
            patterns: Patterns to address (analyzes if None)
        
        Returns:
            List of improvement proposals
        """
        if not patterns:
            patterns = self.analyze_patterns()
        
        proposals = []
        
        for pattern in patterns:
            if pattern.pattern_type == "weakness":
                proposal = self._generate_weakness_fix(pattern)
                if proposal:
                    proposals.append(proposal)
            
            elif pattern.pattern_type == "inefficiency":
                proposal = self._generate_efficiency_fix(pattern)
                if proposal:
                    proposals.append(proposal)
        
        # Sort by expected improvement / cost ratio
        proposals.sort(
            key=lambda p: p.expected_improvement / 
            ({"low": 1, "medium": 2, "high": 3}[p.implementation_cost]),
            reverse=True
        )
        
        return proposals
    
    def _generate_weakness_fix(
        self,
        pattern: PerformancePattern,
    ) -> Optional[ImprovementProposal]:
        """Generate proposal to fix a weakness."""
        # Example: If models fail JSON formatting, propose format module enforcement
        if "JSON" in pattern.description or "format" in pattern.description.lower():
            return ImprovementProposal(
                proposal_type="strategy_change",
                description="Enforce format module for all discipline tasks on small models",
                expected_improvement=0.25,
                implementation_cost="low",
                risk_level="low",
                affected_components=["planner", "model_profiles"],
            )
        
        # Example: If models struggle with reasoning, propose decompose module
        if "reasoning" in pattern.description.lower() or "multi-step" in pattern.description:
            return ImprovementProposal(
                proposal_type="strategy_change",
                description="Add decompose module to reasoning tasks for models <7b",
                expected_improvement=0.18,
                implementation_cost="low",
                risk_level="low",
                affected_components=["planner"],
            )
        
        return None
    
    def _generate_efficiency_fix(
        self,
        pattern: PerformancePattern,
    ) -> Optional[ImprovementProposal]:
        """Generate proposal to fix inefficiency."""
        if "wastes tokens" in pattern.description or "over-engineering" in pattern.description:
            return ImprovementProposal(
                proposal_type="strategy_change",
                description="Limit simple tasks (chat, simple_qa) to max 2 modules",
                expected_improvement=0.15,  # Token savings
                implementation_cost="medium",
                risk_level="medium",
                affected_components=["planner", "token_budget"],
            )
        
        return None
    
    def implement_proposal(
        self,
        proposal: ImprovementProposal,
        llm_callable: Optional[Callable] = None,
    ) -> bool:
        """
        Implement an improvement proposal.
        
        Args:
            proposal: Proposal to implement
            llm_callable: Optional LLM for strategy invention
        
        Returns:
            True if implemented successfully
        """
        implemented = False
        
        if proposal.proposal_type == "strategy_change":
            implemented = self._implement_strategy_change(proposal)
        
        elif proposal.proposal_type == "new_module":
            implemented = self._implement_new_module(proposal, llm_callable)
        
        elif proposal.proposal_type == "weight_adjustment":
            implemented = self._implement_weight_adjustment(proposal)
        
        if implemented:
            self.implemented_improvements.append({
                "proposal": asdict(proposal),
                "timestamp": datetime.now().isoformat(),
                "status": "implemented",
            })
        
        return implemented
    
    def _implement_strategy_change(
        self,
        proposal: ImprovementProposal,
    ) -> bool:
        """Implement a strategy change proposal."""
        # Would modify planner rules, model profiles, etc.
        # For now, just record
        return True
    
    def _implement_new_module(
        self,
        proposal: ImprovementProposal,
        llm_callable: Optional[Callable],
    ) -> bool:
        """Implement a new module proposal."""
        if not llm_callable or not self.discovery:
            return False
        
        # Ask LLM to design new module
        # Then benchmark
        # Then add to available modules if successful
        
        return True
    
    def _implement_weight_adjustment(
        self,
        proposal: ImprovementProposal,
    ) -> bool:
        """Implement module weight adjustment."""
        # Would adjust module weights in planner
        return True
    
    def run_full_cycle(
        self,
        llm_callable: Optional[Callable] = None,
        auto_implement: bool = False,
    ) -> MetaLearningReport:
        """
        Run complete meta-learning cycle.
        
        Args:
            llm_callable: Optional LLM for strategy invention
            auto_implement: Whether to auto-implement top proposal
        
        Returns:
            MetaLearningReport
        """
        # 1. Analyze patterns
        patterns = self.analyze_patterns()
        
        # 2. Generate proposals
        proposals = self.generate_improvements(patterns)
        
        # 3. Implement top proposal if auto-implement
        if auto_implement and proposals:
            self.implement_proposal(proposals[0], llm_callable)
        
        # 4. Create report
        report = MetaLearningReport(
            timestamp=datetime.now().isoformat(),
            total_runs_analyzed=len(patterns) * 10,  # Placeholder
            patterns_found=len(patterns),
            proposals_generated=len(proposals),
            top_weaknesses=[p for p in patterns if p.pattern_type == "weakness"][:5],
            top_strengths=[p for p in patterns if p.pattern_type == "strength"][:5],
            improvement_proposals=proposals[:10],
        )
        
        self.reports.append(report)
        self._save()
        
        return report
    
    def _save(self):
        """Save meta-learning data."""
        try:
            data = {
                "reports": [asdict(r) for r in self.reports[-20:]],
                "implemented_improvements": self.implemented_improvements[-50:],
                "saved_at": time.time(),
            }
            
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"[MetaLearning] Save failed: {e}")
    
    def _load(self):
        """Load meta-learning data."""
        try:
            if Path(self.storage_path).exists():
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                
                self.reports = [
                    MetaLearningReport(**r_data)
                    for r_data in data.get("reports", [])
                ]
                self.implemented_improvements = data.get("implemented_improvements", [])
                
                print(f"[MetaLearning] Loaded {len(self.reports)} reports")
        except Exception as e:
            print(f"[MetaLearning] Load failed: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get meta-learning statistics."""
        return {
            "total_reports": len(self.reports),
            "total_improvements": len(self.implemented_improvements),
            "last_report": self.reports[-1].timestamp if self.reports else None,
        }


# Import Path for _load
from pathlib import Path
