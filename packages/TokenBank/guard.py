"""
TokenBank - guard.py
Wraps LLM calls with budget enforcement.
Drop-in wrapper: replace llm(...) with guarded_llm(...).

Usage:
    from TokenBank import TokenBank

    bank = TokenBank()
    bank.open("my_project", budget=50_000)

    # Wrap your LLM callable
    safe_llm = bank.guard("my_project", llm)
    response = safe_llm(prompt, model="gpt-4o")  # Raises BudgetExceeded if over limit
"""
import os
from typing import Callable, Optional
from .ledger import Ledger, BudgetExceeded, Account


def _estimate_tokens(text: str) -> int:
    """Fast estimation: ~4 chars per token."""
    return max(1, len(str(text)) // 4)


class TokenBank:
    """
    High-level API for token budget management.

    Create named accounts, then wrap LLM callables to auto-enforce limits.
    """

    def __init__(self):
        self._ledger = Ledger()

    def open(self, name: str, budget: int) -> Account:
        """Open a new budget account."""
        print(f"[TokenBank] Account '{name}' opened. Budget: {budget:,} tokens")
        return self._ledger.open_account(name, budget)

    def spend(
        self,
        account: str,
        description: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
    ) -> None:
        """Manually record token usage against an account."""
        self._ledger.record(account, description, prompt_tokens, completion_tokens)

    def remaining(self, account: str) -> int:
        acct = self._ledger.get(account)
        return acct.remaining if acct else 0

    def is_blocked(self, account: str) -> bool:
        acct = self._ledger.get(account)
        return acct.blocked if acct else False

    def reset(self, account: str) -> None:
        """Reset an account's spend back to zero."""
        self._ledger.reset_account(account)
        print(f"[TokenBank] Account '{account}' reset.")

    def summary(self) -> list:
        return self._ledger.summary()

    def print_summary(self) -> None:
        rows = self.summary()
        print(f"\n{'='*58}")
        print(f"{'TOKENBANK LEDGER':^58}")
        print(f"{'='*58}")
        print(f"{'Account':<22} {'Budget':>8} {'Spent':>8} {'Remain':>8} {'%':>6} {'Blocked'}")
        print(f"{'-'*58}")
        for r in rows:
            print(
                f"{r['name']:<22} {r['budget']:>8,} {r['spent']:>8,} "
                f"{r['remaining']:>8,} {r['utilization_pct']:>5.1f}% "
                f"{'⛔' if r['blocked'] else '✓'}"
            )
        print(f"{'='*58}\n")

    def guard(self, account: str, llm_callable: Callable) -> Callable:
        """
        Wrap an LLM callable with budget enforcement.

        The wrapped function:
          1. Checks the account is not already blocked
          2. Estimates prompt tokens from the prompt argument
          3. Calls the original LLM
          4. Records estimated completion tokens from the response
          5. Raises BudgetExceeded if over limit

        Args:
            account:      Account name to charge usage to.
            llm_callable: The original fn(prompt, **kwargs) -> str.

        Returns:
            Wrapped callable with identical signature.
        """
        bank = self

        def guarded(prompt: str, **kwargs) -> str:
            if bank.is_blocked(account):
                raise BudgetExceeded(bank._ledger.get(account))

            prompt_toks = _estimate_tokens(prompt)
            response = llm_callable(prompt, **kwargs)
            completion_toks = _estimate_tokens(response or "")

            model = kwargs.get("model", "unknown")
            bank._ledger.record(
                account,
                description=f"llm({model})",
                prompt_tokens=prompt_toks,
                completion_tokens=completion_toks,
            )
            return response

        guarded.__name__ = getattr(llm_callable, "__name__", "llm")
        return guarded
