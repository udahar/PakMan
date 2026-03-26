"""
AutoDistiller - distiller.py
High-level pipeline: mine → deduplicate → format → write.

Usage:
    from AutoDistiller import distill

    distill(
        source="promptforge.db",
        output="dataset.jsonl",
        format="chatml",
        min_score=0.85,
    )
"""
from pathlib import Path
from typing import Literal, Optional

from .miner import mine_from_promptforge_db, mine_from_jsonl, deduplicate
from .formatter import to_chatml, to_alpaca, to_sharegpt, write_jsonl, to_ollama_modelfile_snippet

Format = Literal["chatml", "alpaca", "sharegpt", "ollama"]


def distill(
    source: str,
    output: str,
    fmt: Format = "chatml",
    min_score: float = 0.8,
    system_prompt: str = "",
    base_model: str = "llama3:8b",
    dedup: bool = True,
    max_examples: int = 5000,
) -> int:
    """
    Full distillation pipeline.

    Args:
        source:       Path to a PromptForge SQLite DB or JSONL export.
        output:       Output file path for the dataset.
        fmt:          One of "chatml", "alpaca", "sharegpt", "ollama".
        min_score:    Minimum quality score filter (0–1).
        system_prompt: Optional system prompt for ChatML/Ollama formats.
        base_model:   Base model name (for Ollama Modelfile only).
        dedup:        Remove near-duplicate examples.
        max_examples: Hard cap on training examples.

    Returns:
        Number of examples written.
    """
    # 1. Mine
    src = str(source)
    if src.endswith(".db"):
        examples = mine_from_promptforge_db(src, min_score=min_score)
    else:
        examples = mine_from_jsonl(src, min_score=min_score)

    print(f"[AutoDistiller] Mined {len(examples)} examples (score ≥ {min_score})")

    # 2. Deduplicate
    if dedup:
        examples = deduplicate(examples)
        print(f"[AutoDistiller] After dedup: {len(examples)} examples")

    # 3. Cap
    examples = examples[:max_examples]

    # 4. Format
    out_path = str(output)

    if fmt == "chatml":
        rows = to_chatml(examples, system_prompt=system_prompt)
    elif fmt == "alpaca":
        rows = to_alpaca(examples)
    elif fmt == "sharegpt":
        rows = to_sharegpt(examples)
    elif fmt == "ollama":
        to_ollama_modelfile_snippet(examples, base_model, system_prompt, out_path)
        print(f"[AutoDistiller] Ollama Modelfile → {out_path}")
        return len(examples)
    else:
        raise ValueError(f"Unknown format: {fmt!r}")

    # 5. Write
    count = write_jsonl(rows, out_path)
    print(f"[AutoDistiller] Wrote {count} examples → {out_path}")
    return count
