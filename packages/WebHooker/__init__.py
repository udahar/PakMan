"""
WebHooker
Zero-dependency inbound webhook server → normalized AiOS events.

Quick start:
    from WebHooker import WebHooker

    hooker = WebHooker(port=9000)

    # Handle GitHub events
    @hooker.on("github")
    def on_github(event):
        print(event.summary)
        ticket = event.to_ticket()
        # Pass ticket to AiOSKernel...

    # Handle Stripe payments
    hooker.on("stripe", lambda e: print(f"Payment: {e.summary}"))

    # Catch everything
    hooker.on("*", lambda e: log_all(e))

    # Non-blocking (integrates with existing app)
    hooker.start_background()

    # Blocking (standalone)
    hooker.start()

Supported routes:
    POST /webhook/github
    POST /webhook/stripe
    POST /webhook/slack
    POST /webhook/<anything>   → custom normalizer
"""
from .server import WebHooker
from .models import WebhookEvent
from .normalizers import normalize, NORMALIZERS

__version__ = "0.1.0"
__all__ = [
    "WebHooker",
    "WebhookEvent",
    "normalize",
    "NORMALIZERS",
]
