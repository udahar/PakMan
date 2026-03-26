"""
WebHooker - server.py
Lightweight HTTP server that receives webhooks and emits normalized events.
Uses only stdlib (http.server). No Flask/FastAPI required.

Usage:
    from WebHooker import WebHooker
    hooker = WebHooker(port=9000)
    hooker.on("github", lambda event: print(event.to_ticket()))
    hooker.start()   # Blocking — use start_background() for non-blocking
"""
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Callable, Dict, List, Optional

from .models import WebhookEvent
from .normalizers import normalize


HandlerFn = Callable[[WebhookEvent], None]


class _RequestHandler(BaseHTTPRequestHandler):
    """Internal HTTP handler — routes POST /webhook/<source> to normalizer."""

    router: Dict[str, List[HandlerFn]] = {}
    default_handlers: List[HandlerFn] = []

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            payload = json.loads(body or b"{}")
        except Exception:
            self._respond(400, {"error": "invalid_json"})
            return

        parts = self.path.strip("/").split("/")
        source = parts[1] if len(parts) >= 2 else "custom"
        headers = dict(self.headers)

        try:
            event = normalize(source, payload, headers=headers)
        except Exception as e:
            self._respond(500, {"error": str(e)})
            return

        self._dispatch(source, event)
        self._respond(200, {"id": event.id, "status": "received"})

    def _dispatch(self, source: str, event: WebhookEvent):
        handlers = self.router.get(source, []) + self.router.get("*", [])
        for h in handlers + self.default_handlers:
            try:
                h(event)
            except Exception as e:
                print(f"[WebHooker] Handler error for {source}: {e}")

    def _respond(self, code: int, body: dict):
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):
        print(f"[WebHooker] {self.address_string()} — {fmt % args}")


class WebHooker:
    """
    Inbound webhook server. Listens on a local port, normalizes payloads,
    and calls registered handler callbacks.

    Routes:
        POST /webhook/<source>   (e.g. /webhook/github, /webhook/stripe)
        POST /webhook/           (hits "*" handlers)

    Args:
        port:    Port to listen on (default: 9000).
        host:    Bind address (default: 0.0.0.0).
        secret:  Optional shared secret for HMAC verification (future).
    """

    def __init__(self, port: int = 9000, host: str = "0.0.0.0"):
        self.port = port
        self.host = host
        self._router: Dict[str, List[HandlerFn]] = {}
        self._server: Optional[HTTPServer] = None
        self._thread: Optional[threading.Thread] = None

    def on(self, source: str, handler: HandlerFn) -> "WebHooker":
        """
        Register a handler for a specific source (e.g. "github", "stripe").
        Use source="*" to handle all events.

        Returns self for chaining.
        """
        self._router.setdefault(source, []).append(handler)
        return self

    def start(self) -> None:
        """Start server (blocking). Press Ctrl+C to stop."""
        self._boot()
        print(f"[WebHooker] Listening on {self.host}:{self.port}")
        try:
            self._server.serve_forever()
        except KeyboardInterrupt:
            self.stop()

    def start_background(self) -> threading.Thread:
        """Start server in a daemon thread (non-blocking)."""
        self._boot()
        self._thread = threading.Thread(
            target=self._server.serve_forever, daemon=True, name="WebHooker"
        )
        self._thread.start()
        print(f"[WebHooker] Running in background on {self.host}:{self.port}")
        return self._thread

    def stop(self) -> None:
        if self._server:
            self._server.shutdown()
            print("[WebHooker] Stopped.")

    def _boot(self) -> None:
        handler_cls = type("Handler", (_RequestHandler,), {
            "router": self._router,
            "default_handlers": [],
        })
        self._server = HTTPServer((self.host, self.port), handler_cls)
