# Updated-On: 2026-03-08
# Updated-By: Codex
# PM-Ticket: UNTRACKED

"""
Multi-Objective Evolution
Optimize prompts across multiple objectives (quality, speed, cost)
"""

from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import random
import hashlib


@dataclass
class Objective:
    """An optimization objective."""

    name: str
    weight: float
    higher_is_better: bool = True
    target: Optional[float] = None


@dataclass
class MultiObjectiveResult:
    """Result from multi-objective optimization."""

    prompt_id: str
    text: str
    scores: Dict[str, float]
    objectives: Dict[str, float]
    generation: int
    pareto_rank: int = 0


class MultiObjectiveEvolver:
    """
    Evolve prompts optimizing multiple objectives simultaneously.

    Objectives can include:
    - Quality score
    - Length (shorter preferred)
    - Speed of execution
    - Cost efficiency
    - Creativity
    - Accuracy
    """

    def __init__(self):
        self.population: List[MultiObjectiveResult] = []
        self.pareto_front: List[MultiObjectiveResult] = []
        self.generation = 0
        self.objectives: List[Objective] = []

    def add_objective(
        self,
        name: str,
        weight: float = 1.0,
        higher_is_better: bool = True,
        target: Optional[float] = None,
    ):
        """Add an optimization objective."""
        obj = Objective(name, weight, higher_is_better, target)
        self.objectives.append(obj)

    def evaluate(
        self, prompt: str, fitness_fn: Callable[[str], float]
    ) -> MultiObjectiveResult:
        """Evaluate a prompt across all objectives."""
        scores = {}
        base_score = fitness_fn(prompt)

        scores["quality"] = base_score
        scores["length"] = 1.0 / (len(prompt.split()) + 1)
        scores["simplicity"] = 1.0 if len(prompt) < 200 else 0.5

        objectives = {}
        for obj in self.objectives:
            if obj.name in scores:
                raw = scores[obj.name]
                if obj.higher_is_better:
                    normalized = raw
                else:
                    normalized = 1.0 - raw
                objectives[obj.name] = normalized * obj.weight

        return MultiObjectiveResult(
            prompt_id=hashlib.md5(prompt.encode()).hexdigest()[:8],
            text=prompt,
            scores=scores,
            objectives=objectives,
            generation=self.generation,
        )

    def dominates(self, a: MultiObjectiveResult, b: MultiObjectiveResult) -> bool:
        """Check if solution a dominates solution b (Pareto)."""
        better_in_any = False

        for obj_name, weight in [(o.name, o.weight) for o in self.objectives]:
            score_a = a.objectives.get(obj_name, 0)
            score_b = b.objectives.get(obj_name, 0)

            if obj_name in a.scores and obj_name in b.scores:
                obj = next((o for o in self.objectives if o.name == obj_name), None)
                if obj and not obj.higher_is_better:
                    score_a, score_b = score_b, score_a

            if score_a > score_b:
                better_in_any = True
            elif score_a < score_b:
                return False

        return better_in_any

    def fast_non_dominated_sort(
        self, population: List[MultiObjectiveResult]
    ) -> List[List[MultiObjectiveResult]]:
        """Fast non-dominated sorting (NSGA-II)."""
        fronts = [[]]
        domination_count = {i: 0 for i in range(len(population))}
        dominated_solutions = {i: [] for i in range(len(population))}

        for i, p1 in enumerate(population):
            for j, p2 in enumerate(population):
                if i != j:
                    if self.dominates(p1, p2):
                        dominated_solutions[i].append(j)
                    elif self.dominates(p2, p1):
                        domination_count[i] += 1

            if domination_count[i] == 0:
                p1.pareto_rank = 0
                fronts[0].append(p1)

        k = 0
        while fronts[k]:
            next_front = []
            for p1 in fronts[k]:
                for j in dominated_solutions[population.index(p1)]:
                    domination_count[j] -= 1
                    if domination_count[j] == 0:
                        population[j].pareto_rank = k + 1
                        next_front.append(population[j])
            k += 1
            fronts.append(next_front)

        return fronts[:-1]

    def crowding_distance(self, front: List[MultiObjectiveResult]) -> Dict[int, float]:
        """Calculate crowding distance for diversity."""
        if len(front) <= 2:
            return {i: float("inf") for i in range(len(front))}

        distances = {i: 0.0 for i in range(len(front))}

        for obj in self.objectives:
            sorted_front = sorted(
                enumerate(front), key=lambda x: x[1].objectives.get(obj.name, 0)
            )

            distances[sorted_front[0][0]] = float("inf")
            distances[sorted_front[-1][0]] = float("inf")

            obj_range = sorted_front[-1][1].objectives.get(obj.name, 0) - sorted_front[
                0
            ][1].objectives.get(obj.name, 0)

            if obj_range == 0:
                continue

            for i in range(1, len(sorted_front) - 1):
                idx = sorted_front[i][0]
                next_score = sorted_front[i + 1][1].objectives.get(obj.name, 0)
                prev_score = sorted_front[i - 1][1].objectives.get(obj.name, 0)
                distances[idx] += (next_score - prev_score) / obj_range

        return distances

    def select_parents(
        self, population: List[MultiObjectiveResult], count: int
    ) -> List[MultiObjectiveResult]:
        """Select parents using tournament based on rank and crowding."""
        selected = []

        for _ in range(count):
            candidates = random.sample(population, 2)

            if candidates[0].pareto_rank < candidates[1].pareto_rank:
                selected.append(candidates[0])
            elif candidates[0].pareto_rank > candidates[1].pareto_rank:
                selected.append(candidates[1])
            else:
                fronts = self.fast_non_dominated_sort(population)
                all_with_rank = [p for f in fronts for p in f]
                distances = self.crowding_distance(all_with_rank)

                idx1 = population.index(candidates[0])
                idx2 = population.index(candidates[1])

                if distances.get(idx1, 0) > distances.get(idx2, 0):
                    selected.append(candidates[0])
                else:
                    selected.append(candidates[1])

        return selected

    def evolve_generation(
        self,
        base_prompts: List[str],
        fitness_fn: Callable[[str], float],
        population_size: int = 20,
    ) -> List[MultiObjectiveResult]:
        """Evolve one generation."""
        if not self.population:
            self.population = [
                self.evaluate(p, fitness_fn) for p in base_prompts[:population_size]
            ]

        fronts = self.fast_non_dominated_sort(self.population)
        self.pareto_front = fronts[0] if fronts else []

        parents = self.select_parents(self.population, population_size // 2)

        offspring = []
        for i in range(0, len(parents) - 1, 2):
            child1_text = parents[i].text
            child2_text = parents[i + 1].text

            if random.random() < 0.7:
                words1 = child1_text.split()
                words2 = child2_text.split()
                if words1 and words2:
                    split1 = random.randint(1, len(words1) - 1)
                    split2 = random.randint(1, len(words2) - 1)
                    child_text = " ".join(words1[:split1] + words2[split2:])
                else:
                    child_text = child1_text
            else:
                child_text = child1_text

            if random.random() < 0.1:
                prefixes = ["Carefully: ", "Specifically: ", "Remember: "]
                child_text = random.choice(prefixes) + child_text

            offspring.append(self.evaluate(child_text, fitness_fn))

        self.population = sorted(
            self.population + offspring,
            key=lambda x: (x.pareto_rank, -x.objectives.get("quality", 0)),
            reverse=False,
        )[:population_size]

        self.generation += 1

        return self.population

    def get_pareto_front(self) -> List[MultiObjectiveResult]:
        """Get current Pareto front."""
        return self.pareto_front

    def get_best_for_objective(
        self, objective_name: str, limit: int = 5
    ) -> List[MultiObjectiveResult]:
        """Get best prompts for specific objective."""
        sorted_pop = sorted(
            self.population,
            key=lambda x: x.objectives.get(objective_name, 0),
            reverse=True,
        )
        return sorted_pop[:limit]

    def get_stats(self) -> Dict[str, Any]:
        """Get evolution stats."""
        return {
            "generation": self.generation,
            "population_size": len(self.population),
            "pareto_front_size": len(self.pareto_front),
            "objectives": [
                {"name": o.name, "weight": o.weight} for o in self.objectives
            ],
        }


def create_multi_objective_evolver() -> MultiObjectiveEvolver:
    """Factory function to create multi-objective evolver."""
    return MultiObjectiveEvolver()
