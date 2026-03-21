# Updated-On: 2026-03-08
# Updated-By: Codex
# PM-Ticket: UNTRACKED
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional


def _clip01(v: float) -> float:
    return max(0.0, min(1.0, v))


@dataclass
class TaskProfile:
    speed_bias: float = 0.0
    cost_bias: float = 0.0
    hard_task_bias: float = 0.0
    category_targets: List[str] = None  # type: ignore[assignment]


@dataclass
class RouterWeights:
    quality: float = 0.30
    reliability: float = 0.30
    speed: float = 0.20
    cost: float = 0.10
    clutch: float = 0.10
    determinism: float = 0.10
    category_fit: float = 0.10
    readiness: float = 0.08
    weakness_penalty: float = 0.10
    failure_penalty: float = 0.12


def infer_task_profile(prompt: str) -> TaskProfile:
    p = (prompt or "").lower()
    speed_bias = 0.25 if any(k in p for k in ["quick", "fast", "short", "brief"]) else 0.0
    cost_bias = 0.30 if any(k in p for k in ["cheap", "cost", "budget", "low cost"]) else 0.0
    hard_bias = 0.35 if any(k in p for k in ["reason", "proof", "architecture", "complex", "hard"]) else 0.0
    cat_map = {
        "code": "Coding",
        "python": "Coding",
        "bug": "Debugging",
        "debug": "Debugging",
        "math": "Math",
        "sql": "SQL",
        "query": "SQL",
        "analysis": "Reasoning",
        "reason": "Reasoning",
        "summarize": "Summarization",
        "summary": "Summarization",
    }
    targets: List[str] = []
    for key, category in cat_map.items():
        if key in p and category not in targets:
            targets.append(category)
    return TaskProfile(
        speed_bias=speed_bias,
        cost_bias=cost_bias,
        hard_task_bias=hard_bias,
        category_targets=targets,
    )


def is_embedding_task(prompt: str) -> bool:
    p = (prompt or "").lower()
    keys = ["embedding", "embed", "vector", "retrieval", "semantic search", "rerank"]
    return any(k in p for k in keys)


def _norm_latency_ms(ms: Optional[float]) -> float:
    if ms is None or ms <= 0:
        return 0.5
    # ~0.5 around 2s, approaches 0 as latency increases
    return _clip01(1.0 / (1.0 + (ms / 2000.0)))


def _norm_cost_usd(cost: Optional[float]) -> float:
    if cost is None:
        return 1.0  # local/unknown cost treated as favorable until explicit pricing exists
    if cost <= 0:
        return 1.0
    # 1.0 at zero, ~0.5 near $0.01/task, lower after
    return _clip01(1.0 / (1.0 + (cost / 0.01)))


def _readiness_value(readiness: Optional[str]) -> float:
    r = str(readiness or "").strip().lower()
    if r == "safe_for_prod":
        return 1.0
    if r == "needs_guardrails":
        return 0.65
    if r == "experimental":
        return 0.25
    return 0.40


def _category_fit_score(card: Dict[str, Any], targets: List[str]) -> float:
    vec = card.get("category_fit_vector") or []
    if not isinstance(vec, list) or not vec:
        return 0.5
    if not targets:
        top_fit = float((vec[0] or {}).get("fit_score") or 0.0)
        return _clip01(top_fit / 100.0)
    best = 0.0
    for row in vec:
        category = str((row or {}).get("category") or "").strip().lower()
        if category in {t.lower() for t in targets}:
            best = max(best, float((row or {}).get("fit_score") or 0.0))
    if best <= 0:
        return 0.45
    return _clip01(best / 100.0)


def score_card(card: Dict[str, Any], profile: TaskProfile, base: RouterWeights | None = None) -> Dict[str, Any]:
    w = base or RouterWeights()
    weights = RouterWeights(
        quality=w.quality,
        reliability=w.reliability,
        speed=w.speed + profile.speed_bias,
        cost=w.cost + profile.cost_bias,
        clutch=w.clutch + profile.hard_task_bias,
        determinism=w.determinism,
        category_fit=w.category_fit,
        readiness=w.readiness,
        weakness_penalty=w.weakness_penalty,
        failure_penalty=w.failure_penalty,
    )

    s = card.get("summary") or {}
    rs = card.get("routing_signals") or {}
    clutch = card.get("clutch") or {}

    quality = _clip01(float(rs.get("quality_score", s.get("avg_score", 0.0)) or 0.0) / 100.0)
    reliability = _clip01(float(rs.get("reliability_score", s.get("reliability_score", 0.0)) or 0.0) / 100.0)
    speed = _norm_latency_ms(rs.get("latency_ms", s.get("avg_latency_ms")))
    cost = _norm_cost_usd(rs.get("cost_per_task_usd", s.get("avg_cost_per_task_usd")))
    clutch_score = _clip01(float(rs.get("clutch_score", clutch.get("score", 0.0)) or 0.0) / 100.0)
    determinism = _clip01(float(rs.get("determinism_score", 0.0) or 0.0) / 100.0)
    category_fit = _category_fit_score(card, profile.category_targets or [])
    readiness = _readiness_value(rs.get("route_readiness") or card.get("route_readiness"))
    weakness_count = float(rs.get("weakness_count", 0.0) or 0.0)
    weakness_norm = _clip01(weakness_count / 10.0)
    format_err = _clip01(float(rs.get("format_error_rate", 0.0) or 0.0) / 100.0)
    transport_err = _clip01(float(rs.get("transport_error_rate", 0.0) or 0.0) / 100.0)
    logic_err = _clip01(float(rs.get("logic_error_rate", 0.0) or 0.0) / 100.0)
    failure_penalty = _clip01((0.4 * format_err) + (0.3 * transport_err) + (0.3 * logic_err))

    score = (
        weights.quality * quality
        + weights.reliability * reliability
        + weights.speed * speed
        + weights.cost * cost
        + weights.clutch * clutch_score
        + weights.determinism * determinism
        + weights.category_fit * category_fit
        + weights.readiness * readiness
        - weights.weakness_penalty * weakness_norm
        - weights.failure_penalty * failure_penalty
    )

    return {
        "model_name": card.get("model_name"),
        "score": round(score, 4),
        "signals": {
            "quality": round(quality, 4),
            "reliability": round(reliability, 4),
            "speed": round(speed, 4),
            "cost": round(cost, 4),
            "clutch": round(clutch_score, 4),
            "determinism": round(determinism, 4),
            "category_fit": round(category_fit, 4),
            "readiness": round(readiness, 4),
            "weakness_penalty": round(weakness_norm, 4),
            "failure_penalty": round(failure_penalty, 4),
        },
        "raw": {
            "avg_score": s.get("avg_score"),
            "reliability_score": s.get("reliability_score"),
            "avg_latency_ms": s.get("avg_latency_ms"),
            "avg_cost_per_task_usd": s.get("avg_cost_per_task_usd"),
            "clutch_score": clutch.get("score"),
            "weakness_count": rs.get("weakness_count"),
            "route_readiness": rs.get("route_readiness") or card.get("route_readiness"),
            "specialist_titles": card.get("specialist_titles") or [],
        },
    }


def rank_cards(cards: Iterable[Dict[str, Any]], prompt: str, top_k: int = 5) -> List[Dict[str, Any]]:
    profile = infer_task_profile(prompt)
    embedding_mode = is_embedding_task(prompt)
    selected: List[Dict[str, Any]] = []
    for c in cards:
        if not c.get("success"):
            continue
        tags = set((c.get("profile") or {}).get("tags") or [])
        is_embed = "embedding" in tags
        if embedding_mode and not is_embed:
            continue
        if not embedding_mode and is_embed:
            continue
        selected.append(c)

    ranked = [score_card(c, profile) for c in selected]
    ranked.sort(key=lambda r: (-float(r["score"]), str(r.get("model_name") or "")))
    return ranked[: max(1, top_k)]
