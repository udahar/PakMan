"""
ContextCompressor - compressor.py
Token-aware context window manager. Keeps conversation context within
a model's token budget using prioritized truncation and summarization.

Strategies (applied in order when budget is exceeded):
  1. Drop oldest low-priority messages
  2. Truncate long assistant messages
  3. Summarize via LLM (if provided)
  4. Hard truncate as last resort
"""
import re
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Literal, Optional

Role = Literal["system", "user", "assistant", "tool"]

# Priority for truncation — lower = dropped first
_ROLE_PRIORITY = {"tool": 0, "assistant": 1, "user": 2, "system": 9}


def _estimate_tokens(text: str) -> int:
    """~4 chars per token heuristic. Good to ±10% for English."""
    return max(1, len(str(text)) // 4)


@dataclass
class Message:
    role: Role
    content: str
    pinned: bool = False          # Pinned messages are never dropped
    priority: int = field(init=False)

    def __post_init__(self):
        self.priority = _ROLE_PRIORITY.get(self.role, 1)

    @property
    def tokens(self) -> int:
        return _estimate_tokens(self.content)

    def to_dict(self) -> dict:
        return {"role": self.role, "content": self.content}


class ContextCompressor:
    """
    Manages a message list within a fixed token budget.

    Usage:
        cc = ContextCompressor(max_tokens=4096)
        cc.add("system", "You are a helpful assistant.", pin=True)
        cc.add("user", very_long_document)
        cc.add("assistant", response)

        # Fit within budget before next API call
        messages = cc.fit()   # → list of {"role": ..., "content": ...}
        response = llm(messages)

    Args:
        max_tokens:     Hard budget (prompt + completion headroom).
        reserve_tokens: Tokens to reserve for model response (default: 512).
        llm:            Optional fn(prompt)->str for summarization.
    """

    def __init__(
        self,
        max_tokens: int = 4096,
        reserve_tokens: int = 512,
        llm: Optional[Callable] = None,
    ):
        self.max_tokens = max_tokens
        self.reserve = reserve_tokens
        self.llm = llm
        self._messages: List[Message] = []

    @property
    def budget(self) -> int:
        return self.max_tokens - self.reserve

    @property
    def current_tokens(self) -> int:
        return sum(m.tokens for m in self._messages)

    def add(self, role: Role, content: str, pin: bool = False) -> "ContextCompressor":
        self._messages.append(Message(role=role, content=content, pinned=pin))
        return self

    def clear(self) -> None:
        self._messages = [m for m in self._messages if m.pinned]

    def fit(self) -> List[dict]:
        """
        Return messages trimmed to fit within the token budget.
        Applies compression strategies in order of least destruction.
        """
        msgs = list(self._messages)

        # Step 1: Drop oldest unpinned low-priority messages
        while _total_tokens(msgs) > self.budget and len(msgs) > 1:
            unpinned = [m for m in msgs if not m.pinned]
            if not unpinned:
                break
            # Drop the oldest lowest-priority message
            target = min(unpinned, key=lambda m: (m.priority, msgs.index(m)))
            msgs.remove(target)

        # Step 2: Truncate long assistant messages to 50% of their content
        if _total_tokens(msgs) > self.budget:
            for m in msgs:
                if m.role == "assistant" and not m.pinned:
                    half = len(m.content) // 2
                    m.content = m.content[:half] + "\n[...truncated...]"
                if _total_tokens(msgs) <= self.budget:
                    break

        # Step 3: LLM summary of oldest conversation block
        if self.llm and _total_tokens(msgs) > self.budget:
            msgs = self._summarize_block(msgs)

        # Step 4: Hard truncate oldest non-system message
        while _total_tokens(msgs) > self.budget and len(msgs) > 1:
            for i, m in enumerate(msgs):
                if not m.pinned and m.role != "system":
                    msgs.pop(i)
                    break

        return [m.to_dict() for m in msgs]

    def _summarize_block(self, msgs: List[Message]) -> List[Message]:
        """Summarize the oldest non-pinned block via LLM."""
        non_pinned = [m for m in msgs if not m.pinned]
        if len(non_pinned) < 3:
            return msgs

        # Summarize first third of non-pinned messages
        chunk = non_pinned[: len(non_pinned) // 3]
        text = "\n".join(f"{m.role}: {m.content[:400]}" for m in chunk)
        prompt = (
            f"Summarize the following conversation excerpt in 3-5 sentences. "
            f"Preserve key facts, decisions, and outcomes:\n\n{text}"
        )
        try:
            summary = str(self.llm(prompt)).strip()
            summary_msg = Message(role="assistant", content=f"[Summary] {summary}")
            for m in chunk:
                msgs.remove(m)
            # Insert summary at the start of non-pinned area
            insert_at = next(
                (i for i, m in enumerate(msgs) if not m.pinned), 0
            )
            msgs.insert(insert_at, summary_msg)
        except Exception as e:
            print(f"[ContextCompressor] Summarization failed: {e}")
        return msgs

    def stats(self) -> dict:
        return {
            "messages": len(self._messages),
            "current_tokens": self.current_tokens,
            "budget": self.budget,
            "utilization_pct": round(self.current_tokens / max(self.budget, 1) * 100, 1),
        }


def _total_tokens(msgs: List[Message]) -> int:
    return sum(m.tokens for m in msgs)
