"""
Skill Composer - Chain Skills Together
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
import asyncio


@dataclass
class SkillResult:
    """Result from executing a skill."""

    skill_name: str
    success: bool
    output: Any
    error: Optional[str] = None


class SkillChain:
    """A chain of skills to execute in sequence."""

    def __init__(self, name: str, skills: List[str]):
        self.name = name
        self.skills = skills

    def execute(
        self, input_data: Any, executor_fn: Callable = None
    ) -> Dict[str, SkillResult]:
        """Execute chain in sequence."""
        results = {}
        current_input = input_data

        for skill_name in self.skills:
            try:
                if executor_fn:
                    output = executor_fn(skill_name, current_input)
                else:
                    output = f"Skill '{skill_name}' would execute with input: {current_input}"

                results[skill_name] = SkillResult(
                    skill_name=skill_name, success=True, output=output
                )

                current_input = output

            except Exception as e:
                results[skill_name] = SkillResult(
                    skill_name=skill_name, success=False, output=None, error=str(e)
                )
                break

        return results

    def __repr__(self):
        return f"SkillChain({self.name}: {' -> '.join(self.skills)})"


class ParallelChain:
    """Execute skills in parallel."""

    def __init__(self, name: str, skills: List[str]):
        self.name = name
        self.skills = skills

    def execute(
        self, input_data: Any, executor_fn: Callable = None
    ) -> Dict[str, SkillResult]:
        """Execute all skills in parallel."""
        results = {}

        for skill_name in self.skills:
            try:
                if executor_fn:
                    output = executor_fn(skill_name, input_data)
                else:
                    output = (
                        f"Skill '{skill_name}' would execute with input: {input_data}"
                    )

                results[skill_name] = SkillResult(
                    skill_name=skill_name, success=True, output=output
                )
            except Exception as e:
                results[skill_name] = SkillResult(
                    skill_name=skill_name, success=False, output=None, error=str(e)
                )

        return results


class ConditionalChain:
    """Execute skills conditionally (if A fails, try B)."""

    def __init__(self, name: str, skills: List[str]):
        self.name = name
        self.skills = skills

    def execute(
        self, input_data: Any, executor_fn: Callable = None
    ) -> Dict[str, SkillResult]:
        """Execute with fallback on failure."""
        results = {}
        current_input = input_data

        for skill_name in self.skills:
            try:
                if executor_fn:
                    output = executor_fn(skill_name, current_input)
                else:
                    output = f"Skill '{skill_name}' would execute with input: {current_input}"

                results[skill_name] = SkillResult(
                    skill_name=skill_name, success=True, output=output
                )

                if output:
                    current_input = output

            except Exception as e:
                results[skill_name] = SkillResult(
                    skill_name=skill_name, success=False, output=None, error=str(e)
                )

        return results


class ChainLibrary:
    """Library of saved skill chains."""

    def __init__(self):
        self.chains: Dict[str, SkillChain] = {}
        self.parallel_chains: Dict[str, ParallelChain] = {}
        self.conditional_chains: Dict[str, ConditionalChain] = {}

    def save_chain(self, chain: SkillChain):
        """Save a chain."""
        self.chains[chain.name] = chain

    def save_parallel(self, chain: ParallelChain):
        """Save a parallel chain."""
        self.parallel_chains[chain.name] = chain

    def save_conditional(self, chain: ConditionalChain):
        """Save a conditional chain."""
        self.conditional_chains[chain.name] = chain

    def get(self, name: str) -> Optional[SkillChain]:
        """Get a chain."""
        return self.chains.get(name)

    def list_chains(self) -> List[str]:
        """List all chains."""
        return list(self.chains.keys())


class Composer:
    """
    Compose skills into chains.

    Usage:
        composer = Composer()

        # Sequential chain
        chain = composer.chain("inquiry", "coding", "review")

        # Parallel execution
        parallel = composer.parallel("search", "analyze", "report")

        # Conditional (fallback)
        fallback = composer.fallback("gpt4", "claude", "local")
    """

    def __init__(self):
        self.library = ChainLibrary()

    def chain(self, *skills: str) -> SkillChain:
        """Create sequential skill chain."""
        name = "_".join(skills)
        chain = SkillChain(name, list(skills))
        self.library.save_chain(chain)
        return chain

    def parallel(self, *skills: str) -> ParallelChain:
        """Create parallel execution chain."""
        name = f"parallel_{'_'.join(skills)}"
        chain = ParallelChain(name, list(skills))
        self.library.save_parallel(chain)
        return chain

    def fallback(self, *skills: str) -> ConditionalChain:
        """Create conditional (fallback) chain."""
        name = f"fallback_{'_'.join(skills)}"
        chain = ConditionalChain(name, list(skills))
        self.library.save_conditional(chain)
        return chain

    def execute(
        self, chain_name: str, input_data: Any, executor_fn: Callable = None
    ) -> Dict:
        """Execute a saved chain."""
        chain = self.library.get(chain_name)
        if chain:
            return chain.execute(input_data, executor_fn)

        for pc in self.library.parallel_chains.values():
            if pc.name == chain_name:
                return pc.execute(input_data, executor_fn)

        for cc in self.library.conditional_chains.values():
            if cc.name == chain_name:
                return cc.execute(input_data, executor_fn)

        return {"error": f"Chain '{chain_name}' not found"}


def create_composer() -> Composer:
    """Factory function."""
    return Composer()
