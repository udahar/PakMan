"""
AutoDocGen - renderer.py
Converts ModuleDoc objects into professional Markdown documentation.
No LLM required for structured docs; LLM is optional for enriched descriptions.
"""
from pathlib import Path
from typing import Optional
from .extractor import ModuleDoc, FunctionDoc, ClassDoc


def render_module(doc: ModuleDoc, llm_callable=None) -> str:
    """
    Render a ModuleDoc as a Markdown string.

    Args:
        doc:          The parsed ModuleDoc.
        llm_callable: Optional fn(prompt) -> str for enhanced descriptions.
    """
    name = Path(doc.filepath).stem
    lines = [f"# `{name}`\n"]

    if doc.module_docstring:
        lines.append(f"{doc.module_docstring}\n")

    if doc.functions:
        lines.append("## Functions\n")
        for fn in doc.functions:
            lines.append(_render_function(fn, llm_callable))

    if doc.classes:
        lines.append("## Classes\n")
        for cls in doc.classes:
            lines.append(_render_class(cls, llm_callable))

    return "\n".join(lines)


def _render_function(fn: FunctionDoc, llm=None) -> str:
    sig_parts = []
    for p in fn.params:
        part = p.name
        if p.annotation:
            part += f": {p.annotation}"
        if p.default:
            part += f" = {p.default}"
        sig_parts.append(part)

    prefix = "async " if fn.is_async else ""
    returns = f" -> {fn.returns}" if fn.returns else ""
    sig = f"`{prefix}def {fn.name}({', '.join(sig_parts)}){returns}`"

    lines = [f"### {sig}\n"]

    if fn.docstring:
        lines.append(f"{fn.docstring}\n")
    elif llm:
        desc = _llm_describe_function(fn, llm)
        if desc:
            lines.append(f"{desc}\n")

    if fn.params:
        lines.append("**Parameters:**\n")
        for p in fn.params:
            ann = f" `{p.annotation}`" if p.annotation else ""
            dflt = f" *(default: `{p.default}`)*" if p.default else ""
            lines.append(f"- `{p.name}`{ann}{dflt}")
        lines.append("")

    if fn.returns:
        lines.append(f"**Returns:** `{fn.returns}`\n")

    return "\n".join(lines)


def _render_class(cls: ClassDoc, llm=None) -> str:
    bases = f"({', '.join(cls.bases)})" if cls.bases else ""
    lines = [f"### `class {cls.name}{bases}`\n"]

    if cls.docstring:
        lines.append(f"{cls.docstring}\n")

    if cls.methods:
        lines.append("**Methods:**\n")
        for m in cls.methods:
            lines.append(_render_function(m, llm))

    return "\n".join(lines)


def _llm_describe_function(fn: FunctionDoc, llm) -> str:
    """Ask the LLM to describe an undocumented function based on its signature."""
    sig_parts = ", ".join(p.name + (f": {p.annotation}" if p.annotation else "")
                          for p in fn.params)
    prompt = (
        f"Write a one-sentence docstring for this Python function: "
        f"`def {fn.name}({sig_parts})`"
    )
    try:
        return str(llm(prompt)).strip()
    except Exception:
        return ""
