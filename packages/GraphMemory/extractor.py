"""
GraphMemory - extractor.py
Extracts entities and relationships from text.

Two modes:
  1. Heuristic (no LLM) — fast, regex + NLP patterns, works offline.
  2. LLM-assisted — richer extractions, uses a simple structured prompt.
"""
import re
from typing import Callable, List, Optional, Tuple

from .models import Edge, Node

# ── Kind heuristics ──────────────────────────────────────────────────────────

_TOOL_PATTERNS = re.compile(
    r"\b(PromptForge|PromptOS|AiOSKernel|SafetySentry|StockAI|PromptRouter|"
    r"GraphMemory|TraceLog|TokenBank|WebHooker|SwarmProtocol|ApprovalGate|"
    r"AutoDistiller|FeedbackLoop|AutoDocGen|TerminalObserver|PakMan|Frank|Alfred)\b"
)
_PERSON_CAPS = re.compile(r"\b([A-Z][a-z]{2,15})\b")
_RELATION_MAP = {
    "worked on": "worked_on", "working on": "worked_on",
    "created": "created", "built": "created", "wrote": "created",
    "broke": "broke", "introduced bug": "broke",
    "fixed": "fixed", "resolved": "fixed", "patched": "fixed",
    "discussed": "discussed", "talking about": "discussed",
    "depends on": "depends_on", "uses": "depends_on", "imports": "depends_on",
    "found in": "found_in", "bug in": "found_in",
    "deployed": "deployed", "released": "deployed",
}

_STOPWORDS = {
    "The", "This", "That", "These", "Those", "What", "When", "Where",
    "Then", "Also", "Just", "Here", "Now", "Yes", "No", "Not",
}


def extract_heuristic(text: str) -> Tuple[List[Node], List[Edge]]:
    """
    Fast heuristic extraction. No LLM required.
    Finds known tools and capitalized words as entities,
    and verb phrases as relationships.

    Returns:
        (nodes, edges)
    """
    nodes: dict[str, Node] = {}
    edges: List[Edge] = []

    def get_or_create(label: str, kind: str = "entity") -> Node:
        key = label.lower()
        if key not in nodes:
            nodes[key] = Node(label=label, kind=kind)
        else:
            nodes[key].mentions += 1
        return nodes[key]

    # Extract known tools
    for match in _TOOL_PATTERNS.finditer(text):
        get_or_create(match.group(), kind="tool")

    # Extract capitalized words as potential entities
    for match in _PERSON_CAPS.finditer(text):
        word = match.group()
        if word not in _STOPWORDS and not _TOOL_PATTERNS.match(word):
            get_or_create(word, kind="entity")

    # Extract relationships from sentences
    sentences = re.split(r"[.!?\n]", text)
    for sent in sentences:
        sent_lower = sent.lower()
        for phrase, rel in _RELATION_MAP.items():
            if phrase in sent_lower:
                # Find entities in this sentence
                ents = [n for n in nodes.values()
                        if n.label.lower() in sent_lower]
                if len(ents) >= 2:
                    edges.append(Edge(
                        src_id=ents[0].id,
                        rel=rel,
                        dst_id=ents[1].id,
                        context=sent.strip()[:200],
                    ))
                    break

    return list(nodes.values()), edges


def extract_with_llm(
    text: str,
    llm: Callable,
) -> Tuple[List[Node], List[Edge]]:
    """
    LLM-assisted extraction. Produces richer, more accurate results.

    Sends a structured prompt and parses a simple line-delimited response.
    Falls back to heuristic on any error.
    """
    prompt = (
        "Extract entities and relationships from the following text.\n"
        "Format each entity as: ENTITY:<name>:<type> "
        "(type = person|tool|project|concept|issue)\n"
        "Format each relation as: REL:<subject>:<verb>:<object>\n"
        "Only extract factual relationships. Text:\n\n"
        f"{text[:1200]}\n\n"
        "Output (one per line):"
    )
    try:
        response = str(llm(prompt))
    except Exception:
        return extract_heuristic(text)

    nodes: dict[str, Node] = {}
    edges: List[Edge] = []

    def get_or_create(label: str, kind: str = "entity") -> Node:
        key = label.lower().strip()
        if key not in nodes:
            nodes[key] = Node(label=label.strip(), kind=kind)
        return nodes[key]

    for line in response.splitlines():
        line = line.strip()
        if line.startswith("ENTITY:"):
            parts = line.split(":")
            if len(parts) >= 2:
                label = parts[1].strip()
                kind = parts[2].strip() if len(parts) > 2 else "entity"
                if label:
                    get_or_create(label, kind)
        elif line.startswith("REL:"):
            parts = line.split(":")
            if len(parts) >= 4:
                subj = parts[1].strip()
                verb = parts[2].strip().lower().replace(" ", "_")
                obj = parts[3].strip()
                src = get_or_create(subj)
                dst = get_or_create(obj)
                if src and dst:
                    edges.append(Edge(
                        src_id=src.id,
                        rel=verb,
                        dst_id=dst.id,
                        context=line,
                    ))

    # Fallback if LLM returned nothing useful
    if not nodes:
        return extract_heuristic(text)

    return list(nodes.values()), edges
