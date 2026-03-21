# PakMan

**Package manager for AI-native apps.**

Install a package once. Every app that understands PakMan gains the capability automatically — no wiring, no config, no restarts required.

```bash
pip install git+https://github.com/udahar/PakMan.git

pakman install PromptSKLib
pakman install context_distiller
pakman list
```

---

## The idea

Every AI tool ships with skills baked in. Nobody ships the layer that makes them composable.

PakMan is that layer. It's a package manager built specifically for AI capability — prompting strategies, context management, routing logic, memory modules, evaluation harnesses. You install a package once into `~/.pakman/`, and every PakMan-aware app on your machine finds it automatically on startup.

The design is intentionally minimal. No daemon. No service. No registry server. A folder, a database, and a CLI.

---

## Install

```bash
pip install git+https://github.com/udahar/PakMan.git
```

> **Want it isolated?**
> ```bash
> python -m venv .venv
> .venv/Scripts/activate      # Windows
> source .venv/bin/activate   # macOS / Linux
> pip install git+https://github.com/udahar/PakMan.git
> ```
> The `~/.pakman/` data folder is shared across all your environments regardless.

---

## CLI

```bash
# Install a package (sparse-checkout — downloads only that package, not the whole repo)
pakman install PromptSKLib
pakman install context_distiller
pakman install cost_optimizer

# Upgrade
pakman install PromptSKLib --upgrade

# Install from a local folder (dev/testing)
pakman install ./my_package

# Install from any udahar repo
pakman install github.com/udahar/Guardian

# See what's installed
pakman list

# Browse available packages
pakman search prompt
pakman search context
pakman search routing

# Package details
pakman info PromptSKLib

# Update
pakman update              # everything
pakman update PromptSKLib  # one package

# Remove
pakman remove PromptSKLib

# Build and serve a unified wiki from all installed packages
pakman wiki
pakman wiki --port 8080
```

---

## Where files go

```
~/.pakman/
  packages/      ← installed packages live here
  pakman.db      ← installation records (SQLite)
  hashes/        ← SHA256 per-package integrity store
```

Nothing is written to your current directory. Clean install, clean uninstall.

```bash
# Move the home directory (e.g. shared team install)
PAKMAN_HOME=/data/shared/pakman pakman list
```

---

## How installs work

All packages live under `packages/` in this repo. When you run `pakman install PromptSKLib`, PakMan uses **git sparse-checkout** to pull only `packages/PromptSKLib/` — not the entire repository. A few KB, not the whole tree.

If a package outgrows this repo and moves to its own repository, the registry entry is updated to point there. The install command stays the same.

---

## How auto-discovery works

PakMan-aware apps call `hotload()` on startup. It scans `~/.pakman/packages/`, imports whatever it finds, and makes the capabilities available — no manual registration required.

```
pakman install PromptSKLib
        ↓
~/.pakman/packages/PromptSKLib/ created
        ↓
App starts → scans ~/.pakman/packages/ → loads PromptSKLib
        ↓
Prompting strategies now available to the app. No config touched.
```

The hotload system also supports **live reload** — it watches package files for changes and reloads modules without restarting the host app. Useful during development.

---

## Security

- Only packages from `github.com/udahar/` are trusted. This is hard-coded in `security.py` and is not user-configurable. It prevents supply-chain attacks through forked registries.
- Every install computes and stores a SHA256 hash. Integrity is verified on load.
- Local installs (`./my_package`) bypass the trusted-source check and are flagged as local.

---

## Package health

```bash
# Check all installed packages for import errors and missing dependencies
pakman health

# Check one package
pakman health PromptSKLib
```

The health system (`health.py`) loads each package in isolation, checks required dependencies, and reports degraded or broken packages before they cause runtime failures.

---

## Writing a package

Any directory with an `__init__.py` is a valid PakMan package:

```
my_package/
├── __init__.py       # export your public API
├── README.md         # required: what does this add?
└── requirements.txt  # optional: pip dependencies
```

```bash
pakman install ./my_package
```

That's it. Any app that calls `hotload()` will find it.

---

## Available packages

47 packages across 15 categories. Run `pakman search` to browse. Quick index:

| Category | Packages |
|----------|---------|
| **Prompting** | `PromptSKLib` `PromptForge` `PromptOS` `PromptRouter` `prompt_library` `prompt_evolution` `prompt_version_control` `skill_composer` `skill_evolver` `skills_framework` `skills_registry` |
| **Context** | `context_distiller` `context_manager` `recursive_context` `context_cache` |
| **Routing** | `cost_optimizer` `model_router` `multi_model_orchestrator` |
| **Evaluation** | `GapMan` `eval_framework` `benchmark_arena` |
| **Memory** | `memory_graph` `browser_memory` |
| **Agents** | `council` `courtroom` |
| **Tools** | `tool_builder` `tool_composer` |
| **Infrastructure** | `scheduler` `tickets` `AutoCode` `AiOSKernel` `apikey` `RomAI` `PakHealth` |
| **ML** | `MLStack` `LoRA` |
| **Knowledge** | `WikiPak` `LinkedIn_Export` `browser_memory` |
| **CMS** | `ZolaPress` |
| **Finance** | `StockAI` |
| **Productivity** | `ProjMan` `SupDoc` |
| **Entertainment** | `RomAI` |
| **Rust utilities** | `Alfred.rust` |

---

## The wiki builder

```bash
pakman wiki
```

Reads every installed package's `README.md`, builds a [Zola](https://www.getzola.org/) static site, and serves it locally. One command gives you a browsable, searchable documentation site across everything installed on your machine.

Source: `packages/WikiPak/`

---

## The ecosystem

PakMan is the package layer for a family of AI-native tools. Each app discovers installed packages at startup and expands its capabilities without any manual wiring.

### Claw *(available now)*

Claw is a thin CLI and Python client for the [Alfred](https://github.com/udahar/Alfred.py) AI platform. It was the first app built to be PakMan-aware — install a prompting package, restart Claw, and the new strategies are live.

```bash
pakman install Claw

# Then, with Alfred running on localhost:5001:
claw ask "summarize my benchmark results"
claw models
claw bench --suite code
```

> **Requires Alfred running locally.** See [Alfred.py](https://github.com/udahar/Alfred.py) for setup. Without Alfred, Claw will connect but get a connection error — it won't silently fail.

```python
from Claw import ClawClient

client = ClawClient(alfred_url="http://localhost:5001")
task_id = client.submit_task("ask", {"prompt": "Hello"})
result  = client.wait_for_result(task_id)
```

### ZolaPress *(private — open-source release planned)*

AI-native CMS built on Zola static generation + FastAPI + PostgreSQL. PakMan packages extend the editorial and automation layer.

### PakClaw *(design stage)*

> This section describes a planned system, not a released one. The architecture is specified. The implementation is not yet public.

The natural endpoint of PakMan: a standalone AI agent that ships with **zero built-in skills** and gains all capability purely by installing packages.

```bash
pip install pakclaw
pakman install PromptSKLib
pakman install council
pakman install cost_optimizer
pakclaw start
```

At startup, PakClaw scans `~/.pakman/packages/`, loads whatever it finds, and assembles its own capability surface from the installed set. Uninstall a package, restart, the capability is gone. Install a new one, restart, it's there.

The design separates the agent runtime (PakClaw) from the capability library (PakMan packages) completely. The runtime itself stays small. The packages do the work.

This is the direction Claw is being developed toward.

---

## Guardian *(companion project)*

[Guardian](https://github.com/udahar/Guardian) is a continuous Windows + WSL system health monitor — resource tracking, auto-heal, disk cleanup, crash analysis, Telegram alerts. Built to keep an 80-model local LLM cluster stable. It is registered in the PakMan registry as an installable package.

```bash
pakman install Guardian
```

---

## sync_registry.py

```bash
# Audit packages/ against registry.json before committing
python sync_registry.py

# Auto-add registry stubs for unregistered packages
python sync_registry.py --fix
```

Run this before any publish. It catches missing `__init__.py`, missing `README.md`, stale registry entries, and unregistered packages. The `--fix` flag adds placeholder entries — review and edit descriptions before committing.

---

## License

MIT — [udahar](https://github.com/udahar)
