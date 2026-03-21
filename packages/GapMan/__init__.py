"""
GapMan - Complete Software Evolution Engine

Combines: Frank (pattern mining), GapMan (mutation), SanityFilter (quality gate),
ProjManSpec (spec generation), Autocoder (code gen), Bench (evaluation).

All-in-one evolution engine.

Usage:
    from GapMan import evolve_toolkit
    
    # Mine patterns, mutate, filter, spec, code, evaluate
    results = evolve_toolkit(repos, max_candidates=10)
"""

# === 1. Frank - Pattern Mining ===
from .frank import (
    mine_patterns,
    DesignFragment,
    categorize_fragments,
    filter_fragments,
)

# === 2. GapMan - Mutation Engine ===
from .mutation import (
    mutate_fragments,
    score_candidate,
    filter_candidates,
    rank_candidates,
    PackageCandidate,
)

# === 3. Sanity Filter - Quality Gate ===
from .sanity import (
    sanity_filter,
    get_top_candidates,
)

# === 4. ProjMan Spec - Spec Generator ===
from .spec import (
    generate_build_spec,
    create_projman_ticket,
    BuildSpec,
)

# === 5. Autocoder - Code Generation ===
from .autocoder import (
    generate_code,
    generate_package,
)

# === 6. Bench - Evaluation ===
from .bench import (
    evaluate_package,
    fitness_test,
)

# === Main Orchestrator ===
from .orchestrator import (
    evolve_toolkit,
    EvolutionEngine,
)


__all__ = [
    # Frank
    "mine_patterns",
    "DesignFragment",
    "categorize_fragments",
    "filter_fragments",
    
    # GapMan Mutation
    "mutate_fragments",
    "score_candidate",
    "filter_candidates",
    "rank_candidates",
    "PackageCandidate",
    
    # Sanity
    "sanity_filter",
    "get_top_candidates",
    
    # Spec
    "generate_build_spec",
    "create_projman_ticket",
    "BuildSpec",
    
    # Code
    "generate_code",
    "generate_package",
    
    # Bench
    "evaluate_package",
    "fitness_test",
    
    # Orchestrator
    "evolve_toolkit",
    "EvolutionEngine",
]
