# Updated-On: 2026-03-08
# Updated-By: Codex
# PM-Ticket: UNTRACKED
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import requests
from fastapi import FastAPI
from pydantic import BaseModel, Field

try:
    from .router import rank_cards
except Exception:
    from router import rank_cards

app = FastAPI(title="PromptRouter API", version="0.1.0")


class RouteRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
    api_base: Optional[str] = None
    models: List[str] = Field(default_factory=list)


def _benchmark_api_base(override: Optional[str]) -> str:
    if override:
        return str(override).rstrip("/")
    return os.environ.get("PROMPTROUTER_BENCHMARK_API_BASE", "http://127.0.0.1:8765/api").rstrip("/")


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


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"ok": True, "service": "promptrouter", "version": "0.1.0"}


@app.post("/route")
def route(req: RouteRequest) -> Dict[str, Any]:
    api_base = _benchmark_api_base(req.api_base)
    model_names = [str(m).strip() for m in req.models if str(m).strip()]
    if not model_names:
        model_names = fetch_model_names(api_base)

    cards = fetch_model_cards(api_base, model_names)
    ranked = rank_cards(cards, prompt=req.prompt, top_k=req.top_k)
    return {
        "success": True,
        "api_base": api_base,
        "models_considered": len(model_names),
        "cards_loaded": len(cards),
        "ranked": ranked,
    }
