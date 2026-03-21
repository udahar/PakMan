# Updated-On: 2026-03-08
# Updated-By: Codex
# PM-Ticket: UNTRACKED

"""
Recursive LM Wrapper
Implements RLM-style processing using LiteLLM
Inspired by RLM paper (Recursive Language Models) - custom implementation
"""

import re
import os
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field

try:
    from langchain_ollama import ChatOllama
    from langchain_core.messages import HumanMessage, SystemMessage
except ImportError:
    ChatOllama = None


@dataclass
class RLMResponse:
    """Response from recursive LM."""

    answer: str
    iterations: int
    tokens_used: int
    success: bool
    error: Optional[str] = None
    steps: List[str] = field(default_factory=list)


class RecursiveLM:
    """
    Recursive Language Model for processing long contexts.

    Unlike traditional approaches that put context in the prompt,
    RLM stores context as a Python variable and lets the model
    explore it recursively using code execution.

    This is inspired by the RLM paper by Zhang & Khattab (MIT, 2025).
    """

    DEFAULT_BASE_URL = "http://127.0.0.1:11434"
    FINAL_PATTERN = re.compile(r"FINAL\((.*?)\)", re.DOTALL)

    SYSTEM_PROMPT = """You are a recursive language model that can explore context using Python code.

You have access to a variable called `context` that contains the full context.
You can explore it using Python code in a REPL environment.

Available operations:
- context[:1000] - Peek at first 1000 chars
- context[-1000:] - Peek at last 1000 chars  
- len(context) - Get context length
- re.findall(r'pattern', context) - Search with regex
- context.split('\\n') - Split into lines
- Any Python code to explore the context

When you have found the answer, respond with:
FINAL(your answer here)

Keep exploring until you find the answer. Be thorough."""

    def __init__(
        self,
        model: str = "qwen2.5:7b",
        base_url: str = DEFAULT_BASE_URL,
        temperature: float = 0.3,
        max_depth: int = 5,
        max_iterations: int = 20,
        chunk_size: int = 4000,
    ):
        self.model = model
        self.base_url = base_url
        self.temperature = temperature
        self.max_depth = max_depth
        self.max_iterations = max_iterations
        self.chunk_size = chunk_size

        self._llm = None
        self.context = ""

    def _get_llm(self):
        """Get or create LLM instance."""
        if self._llm is None:
            if ChatOllama is None:
                raise ImportError("langchain_ollama not installed")
            self._llm = ChatOllama(
                model=self.model, base_url=self.base_url, temperature=self.temperature
            )
        return self._llm

    def store_context(self, context: str, key: str = "default"):
        """Store context for recursive processing."""
        self.context = context
        return self

    def complete(self, query: str, context: Optional[str] = None) -> RLMResponse:
        """
        Complete a query using recursive context exploration.

        Args:
            query: The question to answer
            context: Optional context (if not stored)

        Returns:
            RLMResponse with answer and metadata
        """
        if context:
            self.store_context(context)

        if not self.context:
            return RLMResponse(
                answer="",
                iterations=0,
                tokens_used=0,
                success=False,
                error="No context provided",
            )

        steps = []
        current_query = query

        for iteration in range(self.max_iterations):
            steps.append(f"Iteration {iteration + 1}: Processing query")

            prompt = self._build_prompt(current_query)

            try:
                llm = self._get_llm()
                response = llm.invoke(prompt)
                content = (
                    response.content if hasattr(response, "content") else str(response)
                )

                steps.append(f"Response: {content[:200]}...")

                final_match = self.FINAL_PATTERN.search(content)
                if final_match:
                    answer = final_match.group(1).strip()
                    return RLMResponse(
                        answer=answer,
                        iterations=iteration + 1,
                        tokens_used=self._estimate_tokens(content),
                        success=True,
                        steps=steps,
                    )

                current_query = f"Previous response:\n{content}\n\nOriginal query: {query}\nContinue exploring if needed."

            except Exception as e:
                return RLMResponse(
                    answer="",
                    iterations=iteration + 1,
                    tokens_used=0,
                    success=False,
                    error=str(e),
                    steps=steps,
                )

        return RLMResponse(
            answer="Max iterations exceeded",
            iterations=self.max_iterations,
            tokens_used=0,
            success=False,
            error="Could not find answer within iteration limit",
            steps=steps,
        )

    def _build_prompt(self, query: str) -> str:
        """Build prompt with context as variable."""
        return f"""{self.SYSTEM_PROMPT}

Context (stored in variable `context`):
---
{self.context[: self.chunk_size]}
---

Query: {query}

Remember: Use Python code to explore the context. When ready, respond with FINAL(answer)."""

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimate."""
        return len(text) // 4

    async def acomplete(self, query: str, context: Optional[str] = None) -> RLMResponse:
        """Async version of complete."""
        return self.complete(query, context)

    def peek(self, start: int = 0, end: int = 1000) -> str:
        """Peek at a portion of context."""
        return self.context[start:end]

    def search(self, pattern: str) -> List[str]:
        """Search context with regex."""
        import re

        matches = re.findall(pattern, self.context)
        return matches

    def stats(self) -> Dict[str, Any]:
        """Get context statistics."""
        return {
            "context_length": len(self.context),
            "token_estimate": len(self.context) // 4,
            "line_count": len(self.context.split("\n")),
            "word_count": len(self.context.split()),
        }


def create_rlm(
    model: str = "qwen2.5:7b",
    base_url: str = "http://127.0.0.1:11434",
    temperature: float = 0.3,
) -> RecursiveLM:
    """Factory function to create RLM instance."""
    return RecursiveLM(model=model, base_url=base_url, temperature=temperature)
