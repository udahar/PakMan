"""
WebHooker - normalizers.py
Source-specific payload normalizers.
Each normalizer takes the raw JSON dict and returns a WebhookEvent.
"""
from typing import Any, Dict
from .models import WebhookEvent


def normalize_github(payload: Dict[str, Any], headers: dict = None) -> WebhookEvent:
    """
    Normalize a GitHub webhook payload.
    Supports: push, pull_request, issues, pull_request_review, release.
    """
    event_header = (headers or {}).get("X-GitHub-Event", "unknown")
    action = payload.get("action", "")
    event_type = f"github.{event_header}" + (f".{action}" if action else "")

    # Build a human summary
    repo = payload.get("repository", {}).get("full_name", "unknown/repo")
    sender = payload.get("sender", {}).get("login", "unknown")

    if event_header == "pull_request":
        pr = payload.get("pull_request", {})
        summary = f"GitHub PR #{pr.get('number')} {action} by {sender}: {pr.get('title','')}"
    elif event_header == "push":
        ref = payload.get("ref", "").replace("refs/heads/", "")
        commits = len(payload.get("commits", []))
        summary = f"GitHub push to {repo}/{ref} — {commits} commit(s) by {sender}"
    elif event_header == "issues":
        issue = payload.get("issue", {})
        summary = f"GitHub issue #{issue.get('number')} {action}: {issue.get('title','')}"
    elif event_header == "release":
        rel = payload.get("release", {})
        summary = f"GitHub release {rel.get('tag_name','')} {action} on {repo}"
    else:
        summary = f"GitHub {event_type} on {repo} by {sender}"

    return WebhookEvent(
        source="github",
        event_type=event_type,
        payload=payload,
        summary=summary,
        metadata={"repo": repo, "sender": sender},
    )


def normalize_stripe(payload: Dict[str, Any], headers: dict = None) -> WebhookEvent:
    """Normalize a Stripe webhook payload."""
    evt_type = payload.get("type", "stripe.unknown")
    data = payload.get("data", {}).get("object", {})

    amount = data.get("amount", 0)
    currency = data.get("currency", "usd").upper()
    customer = data.get("customer", "unknown")
    amount_fmt = f"{amount/100:.2f} {currency}" if amount else "?"

    summary = f"Stripe {evt_type}: {amount_fmt} from {customer}"

    return WebhookEvent(
        source="stripe",
        event_type=evt_type,
        payload=payload,
        summary=summary,
        metadata={"amount": amount, "currency": currency, "customer": customer},
    )


def normalize_slack(payload: Dict[str, Any], headers: dict = None) -> WebhookEvent:
    """Normalize a Slack event API payload."""
    evt = payload.get("event", payload)
    evt_type = f"slack.{evt.get('type', 'unknown')}"
    user = evt.get("user", "unknown")
    text = evt.get("text", "")[:120]
    channel = evt.get("channel", "?")

    summary = f"Slack {evt_type} in #{channel} from {user}: {text}"

    return WebhookEvent(
        source="slack",
        event_type=evt_type,
        payload=payload,
        summary=summary,
        metadata={"user": user, "channel": channel},
    )


def normalize_custom(
    payload: Dict[str, Any],
    source: str = "custom",
    headers: dict = None,
) -> WebhookEvent:
    """
    Generic fallback normalizer for any custom webhook.
    Tries to extract event_type from common field names.
    """
    event_type = (
        payload.get("event_type")
        or payload.get("type")
        or payload.get("event")
        or "custom.unknown"
    )
    summary = (
        payload.get("summary")
        or payload.get("message")
        or payload.get("description")
        or str(event_type)
    )
    return WebhookEvent(
        source=source,
        event_type=str(event_type),
        payload=payload,
        summary=str(summary)[:200],
    )


# Registry — maps source name → normalizer fn
NORMALIZERS = {
    "github": normalize_github,
    "stripe": normalize_stripe,
    "slack": normalize_slack,
}


def normalize(source: str, payload: dict, headers: dict = None) -> WebhookEvent:
    """Route a payload to the correct normalizer by source name."""
    fn = NORMALIZERS.get(source.lower(), normalize_custom)
    if fn is normalize_custom:
        return normalize_custom(payload, source=source, headers=headers)
    return fn(payload, headers=headers)
