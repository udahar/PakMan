# OllamaGuard

Shared stuck-state recovery pieces for Ollama-backed apps.

Current scope:
- host-side restart bridge on `8772`
- launcher script with health checks
- bridge delegates restarts to `OllamaOps`

Design note:
- detection lives in the calling app
- restart/control lives here

