# Updated-On: 2026-03-08
# Updated-By: Codex
# PM-Ticket: UNTRACKED

"""
Prompt Evolver
Genetic algorithm for evolving better prompts
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
import random
import hashlib


@dataclass
class EvolutionConfig:
    """Configuration for evolution."""

    population_size: int = 10
    generations: int = 5
    mutation_rate: float = 0.1
    crossover_rate: float = 0.7
    elite_count: int = 2
    tournament_size: int = 3


@dataclass
class EvolvedPrompt:
    """A prompt after evolution."""

    prompt_id: str
    text: str
    fitness: float
    generation: int
    parent_ids: List[str] = field(default_factory=list)
    mutations: List[str] = field(default_factory=list)


class PromptEvolver:
    """
    Evolve prompts using genetic algorithm.

    Operations:
    - Mutation: Modify prompt slightly
    - Crossover: Combine two prompts
    - Selection: Choose best prompts
    - Elitism: Keep top performers
    """

    def __init__(self, config: Optional[EvolutionConfig] = None):
        self.config = config or EvolutionConfig()
        self.history: List[EvolvedPrompt] = []
        self.generation = 0

    def create_initial_population(
        self, base_prompt: str, template_variations: Optional[List[str]] = None
    ) -> List[str]:
        """Create initial population from base prompt."""
        population = [base_prompt]

        variations = template_variations or [
            f"Think carefully: {base_prompt}",
            f"Step by step: {base_prompt}",
            f"You are an expert. {base_prompt}",
            f"Analyze this: {base_prompt}",
            f"Be precise: {base_prompt}",
            f"Consider all aspects: {base_prompt}",
            f"First, think about: {base_prompt}",
            f"Your task is to: {base_prompt}",
            f"Help me with: {base_prompt}",
            f"Complete this: {base_prompt}",
        ]

        population.extend(variations[: self.config.population_size - 1])

        return population[: self.config.population_size]

    def mutate(self, prompt: str) -> str:
        """Mutate a prompt."""
        mutations = [
            lambda p: f"Think step by step. {p}",
            lambda p: f"Be very careful: {p}",
            lambda p: f"Analyze thoroughly: {p}",
            lambda p: f"Your goal: {p}",
            lambda p: f"Consider this carefully: {p}",
            lambda p: p.replace(".", "?").replace("?", ".")
            if "?" in p or "." in p
            else p,
            lambda p: p + " Provide detailed explanation.",
            lambda p: " ".join(p.split()[: len(p.split()) // 2])
            + ". "
            + " ".join(p.split()[len(p.split()) // 2 :]),
        ]

        if random.random() < self.config.mutation_rate:
            mutator = random.choice(mutations)
            prompt = mutator(prompt)

        return prompt

    def crossover(self, prompt_a: str, prompt_b: str) -> str:
        """Crossover two prompts."""
        if random.random() > self.config.crossover_rate:
            return prompt_a

        words_a = prompt_a.split()
        words_b = prompt_b.split()

        if len(words_a) < 2 or len(words_b) < 2:
            return prompt_a

        split_a = random.randint(1, len(words_a) - 1)
        split_b = random.randint(1, len(words_b) - 1)

        child = " ".join(words_a[:split_a] + words_b[split_b:])

        return child

    def select_parent(
        self, population: List[tuple[str, float]], tournament_size: Optional[int] = None
    ) -> str:
        """Tournament selection."""
        size = tournament_size or self.config.tournament_size
        size = min(size, len(population))

        tournament = random.sample(population, size)
        tournament.sort(key=lambda x: x[1], reverse=True)

        return tournament[0][0]

    def evolve(
        self, population: List[str], fitness_fn: Callable[[str], float]
    ) -> List[EvolvedPrompt]:
        """Run one generation of evolution."""

        evaluated = [(p, fitness_fn(p)) for p in population]
        evaluated.sort(key=lambda x: x[1], reverse=True)

        new_population = []

        for i in range(self.config.elite_count):
            new_population.append(evaluated[i][0])

        while len(new_population) < self.config.population_size:
            parent_a = self.select_parent(evaluated)
            parent_b = self.select_parent(evaluated)

            child_text = self.crossover(parent_a, parent_b)
            child_text = self.mutate(child_text)

            new_population.append(child_text)

        self.generation += 1

        results = []
        for i, (text, fitness) in enumerate(evaluated[: self.config.population_size]):
            results.append(
                EvolvedPrompt(
                    prompt_id=hashlib.md5(text.encode()).hexdigest()[:8],
                    text=text,
                    fitness=fitness,
                    generation=self.generation,
                    parent_ids=[
                        hashlib.md5(p.encode()).hexdigest()[:8]
                        for p in [parent_a, parent_b]
                    ],
                )
            )

        self.history.extend(results)

        return results

    def run_evolution(
        self,
        base_prompt: str,
        fitness_fn: Callable[[str], float],
        template_variations: Optional[List[str]] = None,
    ) -> EvolvedPrompt:
        """Run full evolution."""
        population = self.create_initial_population(base_prompt, template_variations)

        best = None

        for gen in range(self.config.generations):
            results = self.evolve(population, fitness_fn)

            best = max(results, key=lambda x: x.fitness)

            population = [r.text for r in results]

        return best

    def get_best_prompts(self, limit: int = 5) -> List[EvolvedPrompt]:
        """Get best prompts from history."""
        sorted_history = sorted(self.history, key=lambda x: x.fitness, reverse=True)
        return sorted_history[:limit]

    def get_stats(self) -> Dict[str, Any]:
        """Get evolution stats."""
        if not self.history:
            return {"generations": 0}

        return {
            "generations": self.generation,
            "total_individuals": len(self.history),
            "best_fitness": max(h.fitness for h in self.history),
            "avg_fitness": sum(h.fitness for h in self.history) / len(self.history),
        }


def create_prompt_evolver(config: Optional[EvolutionConfig] = None) -> PromptEvolver:
    """Factory function to create evolver."""
    return PromptEvolver(config)
