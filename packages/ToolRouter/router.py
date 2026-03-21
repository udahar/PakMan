"""
ToolRouter — semantic tool name resolution.

Given a tool name a model naturally reaches for (e.g. "snapshot_repo",
"vector_search", "audit_log"), resolves it to the actual tool name used in
your system (e.g. "bridge.read", "qdrant:similarity", "postgres:events").

Resolution order:
  1. Exact match in alias map
  2. Model-family-specific lookup (Codex family, Mistral family, etc.)
  3. Fuzzy / prefix match across all consensus terms
  4. Optional: Qdrant semantic fallback (if qdrant_client available)
"""

from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Optional

_DATA_FILE = Path(__file__).parent / "data" / "semantic_tools_map.json"

# Model name prefix → family tag (matches the family field in the map)
_FAMILY_PREFIXES = {
    "codex": "openai", "gpt": "openai", "opencode": "openai_family",
    "cerebras": "cerebras", "nemotron": "nvidia",
    "devstral": "mistral", "ministral": "mistral", "mistral": "mistral",
    "qwen": "alibaba", "deepseek": "deepseek",
    "llama": "meta", "gemma": "google", "glm": "zhipu",
    "kimi": "moonshot", "granite": "ibm", "aya": "cohere",
    "smollm": "huggingface",
}


def _load_map() -> dict:
    with open(_DATA_FILE, encoding="utf-8") as f:
        return json.load(f)


def _model_family(model_name: str) -> Optional[str]:
    base = model_name.split(":")[0].split("/")[0].lower()
    for prefix, family in _FAMILY_PREFIXES.items():
        if base.startswith(prefix):
            return family
    return None


def _normalize(s: str) -> str:
    return re.sub(r"[^a-z0-9_.]", "_", s.lower()).strip("_")


class ToolRouter:
    """
    Resolve natural model vocabulary to your actual tool names.

    Usage:
        router = ToolRouter()
        actual = router.resolve("snapshot_repo", model="codex/gpt-5.3-codex")
        # → "bridge.read"

        # Or just get the intent cluster without a specific model
        intent = router.intent_for("vector_search")
        # → "semantic_pattern_search"
    """

    def __init__(self, map_path: Optional[Path] = None):
        data = _load_map() if map_path is None else json.loads(Path(map_path).read_text())
        self._intents: dict = data["intents"]
        self._index = self._build_index()

    def _build_index(self) -> dict[str, tuple[str, str]]:
        """
        Returns {alias_term: (intent_name, your_name)} for fast lookup.
        Covers both consensus terms and per-model terms.
        """
        index: dict[str, tuple[str, str]] = {}
        for intent, d in self._intents.items():
            your_name = d["your_name"]
            for term in d["top_consensus_terms"]:
                key = _normalize(term)
                if key and key not in index:
                    index[key] = (intent, your_name)
            for model_data in d["by_model"].values():
                for term in model_data["terms"]:
                    key = _normalize(term)
                    if key and key not in index:
                        index[key] = (intent, your_name)
        return index

    def resolve(self, tool_name: str, model: Optional[str] = None) -> Optional[str]:
        """
        Resolve a model's natural tool name to your actual tool name.
        Returns your_name string (e.g. "bridge.read") or None if no match.
        """
        key = _normalize(tool_name)

        # 1. Model-specific lookup first (highest confidence)
        if model:
            family = _model_family(model)
            for intent, d in self._intents.items():
                for m, mdata in d["by_model"].items():
                    if m == model or (family and _model_family(m) == family):
                        if any(_normalize(t) == key for t in mdata["terms"]):
                            return d["your_name"]

        # 2. Exact match in global index
        if key in self._index:
            return self._index[key][1]

        # 3. Prefix / substring match
        for index_key, (intent, your_name) in self._index.items():
            if index_key.startswith(key) or key.startswith(index_key):
                return your_name

        return None

    def intent_for(self, tool_name: str) -> Optional[str]:
        """Return the intent cluster name for a given tool term."""
        key = _normalize(tool_name)
        if key in self._index:
            return self._index[key][0]
        for index_key, (intent, _) in self._index.items():
            if index_key.startswith(key) or key.startswith(index_key):
                return intent
        return None

    def aliases_for_intent(self, intent: str) -> dict:
        """Return all known aliases for an intent, grouped by model family."""
        d = self._intents.get(intent)
        if not d:
            return {}
        by_family: dict[str, list[str]] = {}
        for model, mdata in d["by_model"].items():
            fam = mdata.get("family", "unknown")
            by_family.setdefault(fam, [])
            by_family[fam].extend(mdata["terms"])
        # deduplicate
        return {fam: sorted(set(terms)) for fam, terms in by_family.items()}

    def all_intents(self) -> list[str]:
        return list(self._intents.keys())

    def summary(self) -> dict:
        return {
            intent: {
                "your_name": d["your_name"],
                "models_sampled": d["model_count"],
                "top_terms": d["top_consensus_terms"][:8],
            }
            for intent, d in self._intents.items()
        }
