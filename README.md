# PakMan

**Package manager for AI-native apps.**

Install a package once. Every app that understands PakMan gains the capability automatically — no wiring, no config. Restart the app and the new package is live.

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

# Install a community package (non-udahar — shows warning, requires confirmation)
pakman install --community github.com/someone/their_package

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
# Requires: Zola (https://www.getzola.org) + pakman install WikiPak
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
App restarts → scans ~/.pakman/packages/ → loads PromptSKLib
        ↓
Prompting strategies now available. No config touched.
```

**Hotload during install:** `pakman install` calls `hotload.load()` immediately after writing the package — so the PakMan process itself has the package available right away.

**Live reload for development:** The hotload watcher monitors already-loaded package files for changes and reloads them without restarting the host app. Useful when developing a package locally. A newly installed package in a *running* app is picked up on next restart, not injected live.

---

## Security and trust

Official packages (everything in `registry.json`) come from `github.com/udahar/` only. That trust boundary is hard-coded in `security.py` — not user-configurable. It prevents supply-chain attacks where a forked registry points users at malicious packages.

Every install computes and stores a SHA256 hash. Integrity is verified on load. Local installs (`./my_package`) are flagged as local and bypass the remote trust check.

### Community packages

Community packages from other GitHub users are supported, but require an explicit opt-in flag:

```bash
pakman install --community github.com/someone/their_package
```

The `--community` flag triggers a warning and requires typing `y` before anything is downloaded. PakMan still computes and stores a hash after install. There is no silent community install — the friction is intentional.

Community packages can be listed in `community-registry.json` (in this repo) to make them discoverable via `pakman search`. See [CONTRIBUTING.md](CONTRIBUTING.md) for how to submit one.

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

### Claw / PakClaw

Claw is the first PakMan-aware AI agent — and the reference implementation of the PakClaw design: an agent with **no built-in skills**, where all capability comes from installed packages.

```bash
pakman install Claw
pakman install PromptSKLib
pakman install council
pakman install cost_optimizer

# With Alfred running on localhost:5001:
claw ask "summarize my benchmark results"
claw models
claw bench --suite code
```

Install a package, restart Claw, the capability is there. Uninstall it, restart, it's gone. No hardcoded skill list. The packages are the product.

> **Requires Alfred running locally.** See [Alfred.py](https://github.com/udahar/Alfred.py) for setup. Without Alfred, Claw will report a connection error on startup — it won't silently fail.

```python
from Claw import ClawClient

client = ClawClient(alfred_url="http://localhost:5001")
task_id = client.submit_task("ask", {"prompt": "Hello"})
result  = client.wait_for_result(task_id)
```

The long-term goal is a standalone `pakclaw` that ships without Alfred as a dependency — a self-contained agent runtime where PakMan packages provide everything. The architecture is specified. The standalone runtime is not yet released.

### ZolaPress *(private — open-source release planned)*

AI-native CMS built on Zola static generation + FastAPI + PostgreSQL. PakMan packages extend the editorial and automation layer.


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
