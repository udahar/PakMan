import random

# ========== STRATEGY MUTATION ENGINE ==========
AVAILABLE_MODULES = [
    "role",
    "decompose",
    "scratchpad",
    "tools",
    "verify",
    "format",
    "planner",
    "few_shot",
    "constraints",
    "chain",
    "branch",
]


def mutate_strategy(strategy: list, mutation_rate: float = 0.4) -> list:
    """Mutate a strategy to create new variations."""
    if not strategy:
        strategy = ["scratchpad"]

    mutated = strategy.copy()

    # Mutation types:
    # 1. Add module (40%)
    if random.random() < mutation_rate:
        available = [m for m in AVAILABLE_MODULES if m not in mutated]
        if available:
            mutated.append(random.choice(available))

    # 2. Remove module (20%)
    if random.random() < mutation_rate * 0.5 and len(mutated) > 1:
        to_remove = random.choice(mutated)
        mutated.remove(to_remove)

    # 3. Swap module (20%)
    if random.random() < mutation_rate * 0.5 and len(mutated) > 0:
        idx = random.randint(0, len(mutated) - 1)
        available = [m for m in AVAILABLE_MODULES if m not in mutated]
        if available:
            mutated[idx] = random.choice(available)

    # 4. Reorder (20%)
    if random.random() < mutation_rate * 0.5 and len(mutated) > 1:
        random.shuffle(mutated)

    return list(set(mutated))  # Dedup


def generate_strategy_variations(base_strategy: list, n: int = 4) -> list:
    """Generate n variations of a base strategy."""
    variations = [base_strategy]  # Keep original

    for _ in range(n - 1):
        variation = mutate_strategy(base_strategy)
        if variation not in variations:
            variations.append(variation)

    return variations[:n]


