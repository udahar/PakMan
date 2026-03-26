"""
TraceLog - renderer.py
Human-readable trace timeline and summary reports.
No external dependencies; renders to plain text or Markdown.
"""
from typing import List
from .spans import Trace, Span

BAR_WIDTH = 40


def render_timeline(trace: Trace, fmt: str = "text") -> str:
    """
    Render a waterfall-style timeline of spans in a trace.

    Args:
        trace: The completed Trace object.
        fmt:   "text" for plain terminal output, "md" for Markdown.
    """
    spans = sorted(trace.spans, key=lambda s: s.start_time)
    if not spans:
        return f"[TraceLog] Trace {trace.trace_id} has no spans."

    root_start = spans[0].start_time
    total_ms = trace.total_duration_ms() or 1.0

    lines = []

    if fmt == "md":
        lines.append(f"## 🔍 Trace: `{trace.name}` — `{trace.trace_id}`\n")
        lines.append(f"**Total:** {total_ms:.1f}ms | **Spans:** {len(spans)} | **Errors:** {len(trace.errors())}\n")
        lines.append("```")
    else:
        lines.append(f"\n{'='*60}")
        lines.append(f"TRACE: {trace.name}  [{trace.trace_id}]")
        lines.append(f"Total: {total_ms:.1f}ms | Spans: {len(spans)} | Errors: {len(trace.errors())}")
        lines.append(f"{'='*60}")

    for span in spans:
        indent = "  " if span.parent_id else ""
        offset_ms = (span.start_time - root_start) * 1000
        dur = span.duration_ms or 0
        bar_len = max(1, int((dur / total_ms) * BAR_WIDTH))
        bar = "█" * bar_len

        status_icon = {"ok": "✓", "error": "✗", "timeout": "⏰"}.get(span.status, "?")
        line = f"{indent}{status_icon} {span.name:<30} {bar:<{BAR_WIDTH}} {dur:>7.1f}ms"

        if span.error:
            line += f"  ← {span.error[:50]}"
        if span.attributes:
            attrs = ", ".join(f"{k}={v}" for k, v in list(span.attributes.items())[:3])
            line += f"  [{attrs}]"

        lines.append(line)

    if fmt == "md":
        lines.append("```")

    return "\n".join(lines)


def render_summary(traces: List[dict], fmt: str = "md") -> str:
    """Render a summary table of recent traces."""
    if not traces:
        return "No traces recorded."

    rows = [
        f"| {t.get('name','?'):<28} | {t.get('total_duration_ms') or '?':>8} ms "
        f"| {t.get('span_count',0):>5} | {t.get('error_count',0):>6} |"
        for t in traces
    ]

    header = (
        "| Trace Name                   | Duration     | Spans | Errors |\n"
        "|------------------------------|--------------|-------|--------|"
    )
    return "## Recent Traces\n\n" + header + "\n" + "\n".join(rows)
