#!/usr/bin/env python3
"""
Agent Zoo - Multi-Agent Simulation Framework
Starter implementation
"""

from dataclasses import dataclass
from typing import list, Callable
from langchain_ollama import ChatOllama


@dataclass
class AgentConfig:
    name: str
    system_prompt: str
    model: str = "qwen2.5:7b"


class Agent:
    def __init__(self, config: AgentConfig):
        self.config = config
        self.llm = ChatOllama(model=config.model)

    def think(self, context: str) -> str:
        messages = [
            {"role": "system", "content": self.config.system_prompt},
            {"role": "user", "content": context},
        ]
        return self.llm.invoke(messages).content


ARCHITECT = AgentConfig(
    name="Architect",
    system_prompt="""You are a senior software architect. You think in systems, 
patterns, and tradeoffs. Always ask: 'What's the best way to structure this?'
Consider: maintainability, scalability, simplicity.""",
)

CODER = AgentConfig(
    name="Coder",
    system_prompt="""You are an expert programmer. Write clean, efficient code.
Follow best practices. Ask: 'How do I implement this correctly?'""",
)

REVIEWER = AgentConfig(
    name="Reviewer",
    system_prompt="""You are a meticulous code reviewer. Find bugs, security 
issues, and code smells. Ask: 'What could go wrong here?'
Be thorough and constructive.""",
)

TESTER = AgentConfig(
    name="Tester",
    system_prompt="""You are a QA engineer. Write tests that verify correctness.
Think about edge cases and failure modes. Ask: 'What could break?'""",
)


class ZooKeeper:
    def __init__(self):
        self.agents = {
            "architect": Agent(ARCHITECT),
            "coder": Agent(CODER),
            "reviewer": Agent(REVIEWER),
            "tester": Agent(TESTER),
        }

    def collaborate(self, task: str) -> dict:
        # Step 1: Architect designs
        design = self.agents["architect"].think(f"Design an approach for: {task}")

        # Step 2: Coder implements
        implementation = self.agents["coder"].think(
            f"Implement: {task}\n\nDesign: {design}"
        )

        # Step 3: Reviewer critiques
        review = self.agents["reviewer"].think(f"Review this code:\n{implementation}")

        # Step 4: Tester verifies
        tests = self.agents["tester"].think(f"Write tests for:\n{implementation}")

        return {
            "design": design,
            "implementation": implementation,
            "review": review,
            "tests": tests,
        }


if __name__ == "__main__":
    zoo = ZooKeeper()
    result = zoo.collaborate("Build a REST API for todo list")

    print("=== DESIGN ===")
    print(result["design"])
    print("\n=== IMPLEMENTATION ===")
    print(result["implementation"])
    print("\n=== REVIEW ===")
    print(result["review"])
    print("\n=== TESTS ===")
    print(result["tests"])
