# PakMan

**Package manager for AI-native apps. Install a package, and every app that knows about PakMan gains the capability automatically.**

```bash
pip install git+https://github.com/udahar/PakMan.git
pakman install PromptSKLib
pakman list
```

---

## What It Is

PakMan is a lightweight package manager layer for a growing ecosystem of AI productivity tools. The core idea is simple:

- You install **PakMan** once.
- You install **packages** individually — only what you need.
- Any **app** in the ecosystem that hooks into PakMan auto-discovers your installed packages and expands its own capabilities without any extra wiring.

Think of it like a plugin bus. The packages are the plugins. The apps are the hosts. PakMan is the registry that connects them.

---

## The Ecosystem

### Apps (hosts)

Apps hook into PakMan on startup and discover whatever packages are installed. Installing a package extends **all** compatible apps at once.

| App | What it does |
|-----|-------------|
| **Claw** | AI coding and automation layer |
| **ZolaPress** | AI-native CMS |
| **[Browser]** | Semantic web intelligence *(name TBD)* |

### Packages (capabilities)

Each package lives in its own repo and is installed individually.

| Package | What it adds |
|---------|-------------|
| `PromptSKLib` | 26 reusable AI reasoning skills and strategy scaffolds |
| `PromptForge` | A/B prompt testing and prompt evolution pipeline |
| `PromptOS` | Prompt runtime with memory, routing, and state |
| `context_distiller` | Passage-based summarization for long documents |
| `cost_optimizer` | Model routing by price/quality tradeoff |
| `model_router` | Task-type → model strategy selection |
| `GapMan` | Gap analysis and hard test generation |
| `eval_framework` | Evaluation harness for model outputs |
| *(more coming)* | |

---

## Install

### 1. Install PakMan

```bash
pip install git+https://github.com/udahar/PakMan.git
```

This gives you the `pakman` command. No packages are installed yet.

### 2. Install only what you need

```bash
pakman install PromptSKLib      # pull just this package
pakman install context_distiller
pakman install cost_optimizer
```

Each `install` pulls only the requested package from its own repo. You don't get the whole ecosystem — just what you asked for.

### 3. See what's installed

```bash
pakman list
```

---

## CLI Reference

```bash
pakman install <name>       # install a package by name
pakman install <name> -u    # upgrade if already installed
pakman list                 # show installed packages
pakman remove <name>        # uninstall
pakman update [name]        # update one or all packages
pakman info <name>          # show package details
pakman search <query>       # search available packages
```

---

## How Packages Auto-Wire Into Apps

When you install a package, it lands in PakMan's `packages/` directory. Every PakMan-aware app checks this directory on startup (or via hot-reload) and loads what's there.

```
User installs PromptSKLib
       ↓
pakman downloads udahar/PromptSKLib → packages/PromptSKLib/
       ↓
Claw starts up → scans packages/ → finds PromptSKLib
       ↓
Claw's task briefs now include PromptSKLib strategy scaffolds automatically
       ↓
No config. No wiring. Just works.
```

The same PromptSKLib install also wires into ZolaPress, the Browser, and any other PakMan-aware app running on the same machine.

---

## How App Authors Hook In

Apps discover PakMan packages by scanning the install directory:

```python
from package_manager import PackageManager

pm = PackageManager()
installed = pm.list_packages()

for pkg in installed:
    # load and use pkg["name"]
    module = pm.get_package(pkg["name"])
    # expand app capabilities with module
```

Or via the hot-load watcher — apps can subscribe to package install/remove events and update themselves live without a restart.

---

## Package Registry

PakMan resolves short names (e.g. `PromptSKLib`) to GitHub repos via a registry file. When you run `pakman install PromptSKLib`, it looks up the registry, finds the repo URL, and clones just that package.

```json
{
  "PromptSKLib":       "github.com/udahar/PromptSKLib",
  "PromptForge":       "github.com/udahar/PromptForge",
  "context_distiller": "github.com/udahar/context_distiller",
  "cost_optimizer":    "github.com/udahar/cost_optimizer"
}
```

You can also install directly by URL:

```bash
pakman install github.com/udahar/PromptSKLib
pakman install ./my_local_package
```

---

## Philosophy

- **Base is small.** Installing PakMan gives you the manager, nothing else.
- **Packages are optional.** Install only what your use case needs.
- **No manual wiring.** Apps auto-expand when you install a package.
- **Each package is independent.** Separate repos, separate versioning, separate changelog.
- **Read the manual.** Each package has its own README describing what it adds and how to get the most out of it.

---

## Security

- Packages from `github.com/udahar/*` are trusted by default.
- All installs compute and store a SHA256 hash for integrity verification.
- Rollback to any previous version at any time.
- Changelog is displayed before upgrades.

```bash
pakman update PromptSKLib     # shows changelog, then upgrades
```

---

## Status

**Implemented:**
- `pakman` CLI (install / list / remove / update / info / search)
- pip-installable via `pip install git+https://...`
- GitHub install, local install, upgrade, rollback
- SHA256 hash verification
- Hot-reload (load packages without app restart)
- SQLite package registry

**Coming:**
- Public package registry JSON (short-name → repo URL resolution)
- Per-package `pakman.toml` manifest standard
- Dependency resolution between packages
- Private repo support (GitHub token)
- `pakman publish` to register a new package

---

## Writing a Package

Any directory with an `__init__.py` and a `README.md` is a valid PakMan package.

```
my_package/
├── __init__.py          # export your API
├── README.md            # required — what does this package add?
├── pakman.toml          # optional — name, version, deps, compatible apps
└── requirements.txt     # optional — pip dependencies
```

```toml
# pakman.toml
[package]
name = "my_package"
version = "1.0.0"
description = "What this adds to the ecosystem"
compatible_apps = ["Claw", "ZolaPress"]
```

Publish it to GitHub and it's installable by anyone:

```bash
pakman install github.com/you/my_package
```

---

**Author:** udahar
**License:** MIT *(coming — currently private)*
