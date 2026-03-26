"""
AutoDistiller
Mine PromptForge experiment history → fine-tuning datasets.

Quick start:
    from AutoDistiller import distill

    # From PromptForge DB → ChatML for LLaMA-3
    distill("promptforge.db", "dataset.jsonl", fmt="chatml", min_score=0.85)

    # From JSONL export → Alpaca format
    distill("runs.jsonl", "alpaca.jsonl", fmt="alpaca")

    # Generate an Ollama Modelfile
    distill("promptforge.db", "Modelfile", fmt="ollama", base_model="qwen2.5:7b")
"""
from .distiller import distill
from .miner import mine_from_promptforge_db, mine_from_jsonl, deduplicate
from .formatter import to_chatml, to_alpaca, to_sharegpt, to_ollama_modelfile_snippet

__version__ = "0.1.0"
__all__ = [
    "distill",
    "mine_from_promptforge_db",
    "mine_from_jsonl",
    "deduplicate",
    "to_chatml",
    "to_alpaca",
    "to_sharegpt",
    "to_ollama_modelfile_snippet",
]
