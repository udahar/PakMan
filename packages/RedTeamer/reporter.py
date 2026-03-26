"""
RedTeamer - reporter.py
Formats attack results as readable reports and JSONL vulnerability logs.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import List
from .runner import AttackResult


_SEVERITY_ICON = {
    "critical": "🔴",
    "high": "🟠",
    "medium": "🟡",
    "low": "🟢",
}


def print_report(results: List[AttackResult], summary: dict) -> None:
    """Print colorized attack summary to stdout."""
    print(f"\n{'='*60}")
    print(f"  RED TEAM REPORT — {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*60}")
    print(f"  Total attacks: {summary['total_attacks']}")
    print(f"  Bypassed:      {summary['bypassed']}  ({summary['bypass_rate']}%)")
    print(f"  Blocked:       {summary['blocked']}")

    bypassed = [r for r in results if r.bypassed]
    if bypassed:
        print(f"\n  ⚠️  VULNERABILITIES FOUND:")
        for r in bypassed:
            icon = _SEVERITY_ICON.get(r.severity, "?")
            print(f"    {icon} [{r.severity.upper()}] {r.attack_id}")
            print(f"       {r.notes}")
    else:
        print(f"\n  ✅  No successful bypasses detected.")

    if summary.get("bypassed_by_category"):
        print(f"\n  Bypassed by category:")
        for cat, ids in summary["bypassed_by_category"].items():
            print(f"    • {cat}: {', '.join(ids)}")

    print(f"{'='*60}\n")


def to_jsonl(results: List[AttackResult], path: str) -> int:
    """Write all results to a JSONL vulnerability log. Returns count written."""
    lines = [json.dumps(r.to_dict(), ensure_ascii=False) for r in results]
    Path(path).write_text("\n".join(lines), encoding="utf-8")
    return len(lines)


def to_markdown(results: List[AttackResult], summary: dict) -> str:
    """Render results as a Markdown report."""
    lines = [
        "# Red Team Report\n",
        f"**Date:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        f"**Bypass Rate:** {summary['bypass_rate']}% "
        f"({summary['bypassed']}/{summary['total_attacks']})\n",
        "## Vulnerabilities\n",
    ]
    bypassed = [r for r in results if r.bypassed]
    if bypassed:
        lines.append("| ID | Category | Severity | Notes |")
        lines.append("|---|---|---|---|")
        for r in bypassed:
            icon = _SEVERITY_ICON.get(r.severity, "?")
            lines.append(f"| `{r.attack_id}` | {r.category} | {icon} {r.severity} | {r.notes} |")
    else:
        lines.append("✅ No successful bypasses detected.")

    return "\n".join(lines)
