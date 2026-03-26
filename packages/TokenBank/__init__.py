"""
TokenBank
Local token budget enforcement for AI agents. Zero external dependencies.

Quick start:
    from TokenBank import TokenBank

    bank = TokenBank()
    bank.open("research_project", budget=100_000)

    # Wrap your LLM
    safe_llm = bank.guard("research_project", llm)
    response = safe_llm(prompt, model="gpt-4o")

    # Check balance
    print(bank.remaining("research_project"))
    bank.print_summary()

    # Budget exceeded? BudgetExceeded is raised automatically.
    from TokenBank import BudgetExceeded
    try:
        response = safe_llm(very_long_prompt)
    except BudgetExceeded as e:
        print(f"Agent cut off: {e}")
"""
from .guard import TokenBank
from .ledger import Ledger, Account, LedgerEntry, BudgetExceeded

__version__ = "0.1.0"
__all__ = [
    "TokenBank",
    "Ledger",
    "Account",
    "LedgerEntry",
    "BudgetExceeded",
]
