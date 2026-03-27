# OllamaProxy

Shared Ollama reverse-proxy and queue server extracted from OllamaBot.

Current behavior:
- priority queueing
- strict per-upstream serialization
- stable info endpoints
- local/cloud/embed routing

Explicitly not re-enabled:
- old broken `*5` style load-balancer fan-out

