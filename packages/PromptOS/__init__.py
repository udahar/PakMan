#!/usr/bin/env python3
# Updated-On: 2026-03-07
# Updated-By: Codex
# PM-Ticket: UNTRACKED
#
"""
PromptOS - Modular Prompt Operating System

A self-optimizing prompt strategy system with:
- Modular strategy blocks
- DSPy integration for auto-optimization
- Bench integration with answer key scoring
- Strategy genome tracking
- Self-evolution based on ticket success/failure
- Template library for failure mode targeting
- Model behavior profiles
"""

from .core import PromptOS
from .modules import StrategyModule, STRATEGY_MODULES
from .stacks import StrategyStack, STRATEGY_STACKS
from .profiles import ModelProfile, MODEL_PROFILES
from .dspy_integration import DSPyOptimizer
from .bench import BenchIntegration
from .evolution import StrategyEvolution
from .genome import StrategyGenome
from .cache import ResponseCache
from .token_budget import TokenBudget
from .model_families import ModelFamilies
from .planner import StrategyPlanner, StrategyPlan
from .discovery import StrategyDiscovery, StrategyProposal, BenchmarkResult
from .strategy_embeddings import StrategyEmbeddings, StrategyExperience
from .strategy_research import StrategyResearchEngine, GenomePattern, StrategyHypothesis, HypothesisResult
from .self_modification import SelfModificationEngine, PerformanceAnalysis, SystemModification, ModificationResult
from .meta_learning import MetaLearningLoop, PerformancePattern, ImprovementProposal, MetaLearningReport
from .knowledge_transfer import KnowledgeTransfer, StrategyTransfer, FamilyBestPractice
from .strategy_distillation import StrategyDistillation, StrategyCandidate, VerificationResult, DistillationRecord
from .verifier import VerifierAgent, VerificationCriteria, CandidateEvaluation
from .templates.template_library import TemplateLibrary, PromptTemplate, get_template
from .model_behavior_profiles import ModelBehaviorProfiles, TestResult, StrategyImprovement
from .benchmark_helper import TwoModeBenchmark, TwoModeResult, benchmark_two_mode
from .knowledge_scraper import BenchmarkKnowledgeScraper, ScrapedExample

__all__ = [
    'PromptOS',
    'StrategyModule',
    'STRATEGY_MODULES',
    'StrategyStack',
    'STRATEGY_STACKS',
    'ModelProfile',
    'MODEL_PROFILES',
    'DSPyOptimizer',
    'BenchIntegration',
    'StrategyEvolution',
    'StrategyGenome',
    'ResponseCache',
    'TokenBudget',
    'ModelFamilies',
    'StrategyPlanner',
    'StrategyPlan',
    'StrategyDiscovery',
    'StrategyProposal',
    'BenchmarkResult',
    'StrategyEmbeddings',
    'StrategyExperience',
    'StrategyResearchEngine',
    'GenomePattern',
    'StrategyHypothesis',
    'HypothesisResult',
    'SelfModificationEngine',
    'PerformanceAnalysis',
    'SystemModification',
    'ModificationResult',
    'MetaLearningLoop',
    'PerformancePattern',
    'ImprovementProposal',
    'MetaLearningReport',
    'KnowledgeTransfer',
    'StrategyTransfer',
    'FamilyBestPractice',
    'StrategyDistillation',
    'StrategyCandidate',
    'VerificationResult',
    'DistillationRecord',
    'VerifierAgent',
    'VerificationCriteria',
    'CandidateEvaluation',
    'TemplateLibrary',
    'PromptTemplate',
    'get_template',
    'ModelBehaviorProfiles',
    'TestResult',
    'StrategyImprovement',
    'TwoModeBenchmark',
    'TwoModeResult',
    'benchmark_two_mode',
    'BenchmarkKnowledgeScraper',
    'ScrapedExample',
]

__version__ = '1.0.0'
