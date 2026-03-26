"""
GapMan - Complete Software Evolution Engine

Combines: PatternMiner (pattern mining), Mutation (mutation), SanityFilter (quality gate),
SpecGenerator (spec generation), Autocoder (code gen), Bench (evaluation).

All-in-one evolution engine.

Usage:
    from GapMan import evolve_toolkit
    
    # Mine patterns, mutate, filter, spec, code, evaluate
    results = evolve_toolkit(repos, max_candidates=10)
"""

# === 1. PatternMiner - Pattern Mining ===
try:
    from PatternMiner import (
        mine_patterns,
        DesignFragment,
        categorize_fragments,
        filter_fragments,
    )
except ImportError:
    mine_patterns = None
    DesignFragment = None
    categorize_fragments = None
    filter_fragments = None

# === 2. Mutation - Mutation Engine ===
try:
    from Mutation import (
        mutate_fragments,
        score_candidate,
        filter_candidates,
        rank_candidates,
        PackageCandidate,
    )
except ImportError:
    mutate_fragments = None
    score_candidate = None
    filter_candidates = None
    rank_candidates = None
    PackageCandidate = None

# === 3. SanityFilter - Quality Gate ===
try:
    from SanityFilter import (
        sanity_filter,
        get_top_candidates,
    )
except ImportError:
    sanity_filter = None
    get_top_candidates = None

# === 4. SpecGenerator - Spec Generator ===
try:
    from SpecGenerator import (
        generate_build_spec,
        create_projman_ticket,
        BuildSpec,
    )
except ImportError:
    generate_build_spec = None
    create_projman_ticket = None
    BuildSpec = None

# === 5. Autocoder - Code Generation ===
try:
    from Autocoder import (
        generate_code,
        generate_package,
    )
except ImportError:
    generate_code = None
    generate_package = None

# === 6. Bench - Evaluation ===
try:
    from Bench import (
        evaluate_package,
        fitness_test,
    )
except ImportError:
    evaluate_package = None
    fitness_test = None

# === Main Orchestrator ===
from .orchestrator import (
    evolve_toolkit,
    EvolutionEngine,
)


__all__ = [
    # PatternMiner
    "mine_patterns",
    "DesignFragment",
    "categorize_fragments",
    "filter_fragments",
    
    # Mutation
    "mutate_fragments",
    "score_candidate",
    "filter_candidates",
    "rank_candidates",
    "PackageCandidate",
    
    # SanityFilter
    "sanity_filter",
    "get_top_candidates",
    
    # SpecGenerator
    "generate_build_spec",
    "create_projman_ticket",
    "BuildSpec",
    
    # Autocoder
    "generate_code",
    "generate_package",
    
    # Bench
    "evaluate_package",
    "fitness_test",
    
    # Orchestrator
    "evolve_toolkit",
    "EvolutionEngine",
]

__version__ = "1.0.0"
