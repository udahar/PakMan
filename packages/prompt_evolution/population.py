# Updated-On: 2026-03-08
# Updated-By: Codex
# PM-Ticket: UNTRACKED

"""
Prompt Population Management
Manage populations of prompts for evolution
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
import random


@dataclass
class Individual:
    """An individual prompt in the population."""

    prompt_id: str
    text: str
    fitness: float = 0.0
    generation: int = 0
    age: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __hash__(self):
        return hash(self.prompt_id)


class PromptPopulation:
    """
    Manage a population of prompts.

    Features:
    - Track individuals
    - Diversity scoring
    - Age-based selection
    - Family tree tracking
    """

    def __init__(self, max_size: int = 100, min_diversity: float = 0.3):
        self.max_size = max_size
        self.min_diversity = min_diversity
        self.individuals: Dict[str, Individual] = {}
        self.generation = 0
        self.family_tree: Dict[str, List[str]] = {}

    def add(self, individual: Individual):
        """Add individual to population."""
        self.individuals[individual.prompt_id] = individual

    def add_many(self, individuals: List[Individual]):
        """Add multiple individuals."""
        for ind in individuals:
            self.add(ind)

    def remove(self, prompt_id: str) -> bool:
        """Remove individual from population."""
        if prompt_id in self.individuals:
            del self.individuals[prompt_id]
            return True
        return False

    def get(self, prompt_id: str) -> Optional[Individual]:
        """Get individual by ID."""
        return self.individuals.get(prompt_id)

    def get_best(self, limit: int = 1) -> List[Individual]:
        """Get best individuals by fitness."""
        sorted_ind = sorted(
            self.individuals.values(), key=lambda x: x.fitness, reverse=True
        )
        return sorted_ind[:limit]

    def get_diverse(self, limit: int = 5) -> List[Individual]:
        """Get diverse set of individuals."""
        if not self.individuals:
            return []

        sorted_ind = sorted(
            self.individuals.values(), key=lambda x: x.fitness, reverse=True
        )

        selected = [sorted_ind[0]]
        selected_texts = [sorted_ind[0].text.lower()]

        for ind in sorted_ind[1:]:
            ind_text = ind.text.lower()

            is_diverse = True
            for sel_text in selected_texts:
                similarity = self._calculate_similarity(ind_text, sel_text)
                if similarity > (1 - self.min_diversity):
                    is_diverse = False
                    break

            if is_diverse:
                selected.append(ind)
                selected_texts.append(ind_text)

                if len(selected) >= limit:
                    break

        return selected

    def _calculate_similarity(self, text_a: str, text_b: str) -> float:
        """Calculate text similarity."""
        words_a = set(text_a.split())
        words_b = set(text_b.split())

        if not words_a or not words_b:
            return 0.0

        intersection = words_a & words_b
        union = words_a | words_b

        return len(intersection) / len(union)

    def select_parents(
        self, count: int, method: str = "tournament"
    ) -> List[Individual]:
        """Select parents for reproduction."""
        individuals = list(self.individuals.values())

        if method == "tournament":
            return self._tournament_select(count)
        elif method == "roulette":
            return self._roulette_select(count)
        elif method == "rank":
            return self._rank_select(count)
        else:
            return random.sample(individuals, min(count, len(individuals)))

    def _tournament_select(self, count: int) -> List[Individual]:
        """Tournament selection."""
        selected = []
        tournament_size = 3

        for _ in range(count):
            tournament = random.sample(
                list(self.individuals.values()),
                min(tournament_size, len(self.individuals)),
            )
            winner = max(tournament, key=lambda x: x.fitness)
            selected.append(winner)

        return selected

    def _roulette_select(self, count: int) -> List[Individual]:
        """Roulette wheel selection."""
        individuals = list(self.individuals.values())

        total_fitness = sum(ind.fitness for ind in individuals)
        if total_fitness == 0:
            return random.sample(individuals, min(count, len(individuals)))

        selected = []
        for _ in range(count):
            pick = random.uniform(0, total_fitness)
            current = 0

            for ind in individuals:
                current += ind.fitness
                if current >= pick:
                    selected.append(ind)
                    break

        return selected

    def _rank_select(self, count: int) -> List[Individual]:
        """Rank-based selection."""
        sorted_ind = sorted(
            self.individuals.values(), key=lambda x: x.fitness, reverse=True
        )

        n = len(sorted_ind)
        ranks = list(range(n, 0, -1))
        total_rank = sum(ranks)

        selected = []
        for _ in range(count):
            pick = random.uniform(0, total_rank)
            current = 0

            for i, ind in enumerate(sorted_ind):
                current += ranks[i]
                if current >= pick:
                    selected.append(ind)
                    break

        return selected

    def prune(self, keep_count: Optional[int] = None) -> int:
        """Remove weakest individuals."""
        keep_count = keep_count or self.max_size

        if len(self.individuals) <= keep_count:
            return 0

        sorted_ind = sorted(
            self.individuals.values(), key=lambda x: x.fitness, reverse=True
        )

        removed = 0
        for ind in sorted_ind[keep_count:]:
            self.remove(ind.prompt_id)
            removed += 1

        return removed

    def age_population(self):
        """Age all individuals."""
        for ind in self.individuals.values():
            ind.age += 1

    def get_stats(self) -> Dict[str, Any]:
        """Get population stats."""
        if not self.individuals:
            return {"size": 0, "generations": self.generation}

        fitnesses = [ind.fitness for ind in self.individuals.values()]

        return {
            "size": len(self.individuals),
            "max_fitness": max(fitnesses),
            "avg_fitness": sum(fitnesses) / len(fitnesses),
            "min_fitness": min(fitnesses),
            "generations": self.generation,
            "total_ever": len(self.individuals),
        }

    def export(self) -> List[Dict[str, Any]]:
        """Export population to dict."""
        return [
            {
                "prompt_id": ind.prompt_id,
                "text": ind.text,
                "fitness": ind.fitness,
                "generation": ind.generation,
                "age": ind.age,
                "metadata": ind.metadata,
            }
            for ind in self.individuals.values()
        ]

    def import_from(self, data: List[Dict[str, Any]]):
        """Import population from dict."""
        for item in data:
            ind = Individual(
                prompt_id=item["prompt_id"],
                text=item["text"],
                fitness=item.get("fitness", 0.0),
                generation=item.get("generation", 0),
                age=item.get("age", 0),
                metadata=item.get("metadata", {}),
            )
            self.add(ind)


def create_population(max_size: int = 100) -> PromptPopulation:
    """Factory function to create population."""
    return PromptPopulation(max_size=max_size)
