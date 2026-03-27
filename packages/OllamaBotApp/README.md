# OllamaBotApp

Composition package for the full OllamaBot stack.

This package is the parent bundle. It does not own the core logic.

It wires together:
- `OllamaOps`
- `OllamaGuard`
- `OllamaProxy`

What it provides:
- app-frame scaffolding
- stack start/stop helpers
- health checks
- a reproducible way to rebuild the app from packages

What it does not include:
- secrets
- provider tokens
- the old broken `*5` load-balancer fan-out

Typical flow:

```powershell
pakman install OllamaBotApp
powershell -File .\scripts\scaffold_frame.ps1 -TargetDir C:\Apps\OllamaBot
powershell -File .\scripts\start_stack.ps1 -AppRoot C:\Apps\OllamaBot
```

