# Updated-On: 2026-03-08
# Updated-By: Codex
# PM-Ticket: UNTRACKED
from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List

import requests

try:
    from .router import rank_cards
except Exception:
    from router import rank_cards


def _get_json(url: str, timeout: int = 20) -> Dict[str, Any]:
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    return r.json()


def fetch_model_names(api_base: str) -> List[str]:
    payload = _get_json(f"{api_base}/benchmark/models")
    names: List[str] = []
    for row in payload if isinstance(payload, list) else []:
        name = str((row or {}).get("model_name") or "").strip()
        if name:
            names.append(name)
    return names


def fetch_model_cards(api_base: str, model_names: List[str]) -> List[Dict[str, Any]]:
    cards: List[Dict[str, Any]] = []
    for model in model_names:
        try:
            card = _get_json(f"{api_base}/benchmark/models/card?model_name={model}")
            cards.append(card)
        except Exception:
            continue
    return cards


def main() -> int:
    parser = argparse.ArgumentParser(description="PromptRouter experimental ranking")
    parser.add_argument("--prompt", required=True, help="Prompt text used to infer routing profile")
    parser.add_argument("--api-base", default="http://localhost:3001/api", help="Benchmark API base")
    parser.add_argument("--models", default="", help="Comma-separated model list (optional)")
    parser.add_argument("--top-k", type=int, default=5, help="How many ranked results to return")
    parser.add_argument("--json", action="store_true", help="Emit JSON only")
    args = parser.parse_args()

    model_names = [m.strip() for m in str(args.models).split(",") if m.strip()]
    if not model_names:
        model_names = fetch_model_names(args.api_base)
    if not model_names:
        print("No model names available for routing.", file=sys.stderr)
        return 2

    cards = fetch_model_cards(args.api_base, model_names)
    ranked = rank_cards(cards, prompt=args.prompt, top_k=int(args.top_k))

    if args.json:
        print(json.dumps({"success": True, "ranked": ranked}, indent=2))
        return 0

    print(f"PromptRouter ranked {len(ranked)} model(s):")
    for i, row in enumerate(ranked, start=1):
        readiness = (row.get("raw") or {}).get("route_readiness") or "unknown"
        print(
            f"{i}. {row['model_name']} | score={row['score']:.4f} "
            f"| quality={row['signals']['quality']:.3f} rel={row['signals']['reliability']:.3f} "
            f"speed={row['signals']['speed']:.3f} cost={row['signals']['cost']:.3f} "
            f"clutch={row['signals']['clutch']:.3f} readiness={readiness}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
