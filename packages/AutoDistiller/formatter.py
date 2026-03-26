"""
AutoDistiller - formatter.py
Converts raw mining results into standard fine-tuning dataset formats.

Supports:
  - ChatML (Mistral, LLaMA-3, Qwen)
  - Alpaca (instruction/input/output)
  - ShareGPT (multi-turn conversations)
  - Ollama Modelfile snippet
"""
import json
from pathlib import Path
from typing import List, Optional


Example = dict  # {"prompt": str, "response": str, "task_type": str, "score": float}


def to_chatml(examples: List[Example], system_prompt: str = "") -> List[dict]:
    """
    ChatML format — the most widely supported fine-tuning format.
    Compatible with: Mistral, LLaMA-3, Qwen, Phi.

    Output per example:
        {"messages": [{"role": "system", ...}, {"role": "user", ...}, {"role": "assistant", ...}]}
    """
    rows = []
    for ex in examples:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": ex["prompt"]})
        messages.append({"role": "assistant", "content": ex["response"]})
        rows.append({"messages": messages})
    return rows


def to_alpaca(examples: List[Example]) -> List[dict]:
    """
    Alpaca instruction format.
    Output: {"instruction": str, "input": "", "output": str}
    """
    return [
        {
            "instruction": ex["prompt"],
            "input": "",
            "output": ex["response"],
        }
        for ex in examples
    ]


def to_sharegpt(examples: List[Example]) -> List[dict]:
    """
    ShareGPT format for multi-turn datasets.
    Output: {"conversations": [{"from": "human", "value": ...}, ...]}
    """
    return [
        {
            "conversations": [
                {"from": "human", "value": ex["prompt"]},
                {"from": "gpt", "value": ex["response"]},
            ]
        }
        for ex in examples
    ]


def to_ollama_modelfile_snippet(
    examples: List[Example],
    base_model: str,
    system_prompt: str = "",
    output_path: Optional[str] = None,
) -> str:
    """
    Generates an Ollama Modelfile that embeds examples as MESSAGE pairs.
    Suitable for `ollama create my-model -f Modelfile`.

    Note: Ollama MESSAGE blocks are for seeding behavior, not true fine-tuning.
    Use ChatML JSONL + Unsloth for actual weight updates.
    """
    lines = [f"FROM {base_model}"]
    if system_prompt:
        lines.append(f'\nSYSTEM """{system_prompt}"""')
    for ex in examples[:20]:  # Ollama limits context size
        lines.append(f'\nMESSAGE user "{ex["prompt"]}"')
        lines.append(f'MESSAGE assistant "{ex["response"]}"')

    content = "\n".join(lines)
    if output_path:
        Path(output_path).write_text(content, encoding="utf-8")
    return content


def write_jsonl(
    rows: List[dict],
    output_path: str,
    indent: bool = False,
) -> int:
    """Write formatted examples to a JSONL file. Returns count written."""
    lines = [
        json.dumps(r, ensure_ascii=False, indent=2 if indent else None)
        for r in rows
    ]
    Path(output_path).write_text("\n".join(lines), encoding="utf-8")
    return len(lines)
