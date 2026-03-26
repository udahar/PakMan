"""
TokenBank - ledger.py
Per-session and per-project token ledger. Thread-safe, zero deps.
"""
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class LedgerEntry:
    timestamp: str
    description: str
    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def total(self) -> int:
        return self.prompt_tokens + self.completion_tokens


@dataclass
class Account:
    """A named budget account (e.g. per-project or per-agent)."""
    name: str
    budget: int                        # Maximum allowed tokens
    spent: int = 0
    entries: List[LedgerEntry] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    blocked: bool = False

    @property
    def remaining(self) -> int:
        return max(0, self.budget - self.spent)

    @property
    def utilization(self) -> float:
        return self.spent / self.budget if self.budget else 0.0

    def is_over_budget(self) -> bool:
        return self.spent >= self.budget

    def record(
        self,
        description: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
    ) -> LedgerEntry:
        entry = LedgerEntry(
            timestamp=datetime.utcnow().isoformat(),
            description=description,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )
        self.entries.append(entry)
        self.spent += entry.total
        if self.is_over_budget():
            self.blocked = True
        return entry

    def reset(self) -> None:
        self.spent = 0
        self.entries.clear()
        self.blocked = False

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "budget": self.budget,
            "spent": self.spent,
            "remaining": self.remaining,
            "utilization_pct": round(self.utilization * 100, 1),
            "blocked": self.blocked,
            "entry_count": len(self.entries),
        }


class Ledger:
    """
    Multi-account token ledger.

    Maintains named accounts and provides thread-safe recording.
    Raises BudgetExceeded when an account's budget is breached.
    """

    def __init__(self):
        self._accounts: Dict[str, Account] = {}
        self._lock = threading.Lock()

    def open_account(self, name: str, budget: int) -> Account:
        """Create or replace an account with a given token budget."""
        with self._lock:
            self._accounts[name] = Account(name=name, budget=budget)
            return self._accounts[name]

    def get(self, name: str) -> Optional[Account]:
        return self._accounts.get(name)

    def record(
        self,
        account: str,
        description: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
    ) -> LedgerEntry:
        """
        Record token usage against an account.
        Raises BudgetExceeded if the account is already blocked.
        """
        with self._lock:
            acct = self._accounts.get(account)
            if acct is None:
                raise KeyError(f"Unknown account: {account!r}")
            if acct.blocked:
                raise BudgetExceeded(acct)
            entry = acct.record(description, prompt_tokens, completion_tokens)
            if acct.is_over_budget():
                raise BudgetExceeded(acct)
            return entry

    def summary(self) -> List[dict]:
        return [a.to_dict() for a in self._accounts.values()]

    def reset_account(self, name: str) -> None:
        with self._lock:
            if name in self._accounts:
                self._accounts[name].reset()


class BudgetExceeded(Exception):
    """Raised when an account's token budget is breached."""
    def __init__(self, account: Account):
        self.account = account
        super().__init__(
            f"[TokenBank] Budget exceeded for '{account.name}': "
            f"{account.spent}/{account.budget} tokens used."
        )
