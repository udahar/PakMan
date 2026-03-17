# PakMan

**Package manager for AI-native apps.**
Install a package once — every app that knows about PakMan gains the capability automatically.

```bash
pip install git+https://github.com/udahar/PakMan.git

pakman install PromptSKLib
pakman list
```

---

## Where files go

When you install PakMan, it creates **one folder in your home directory** and nothing else:

```
~/.pakman/
  packages/      ← installed packages live here
  pakman.db      ← tracks what's installed (SQLite)
```

The `pip install` itself goes into your active Python environment (system Python or venv — whichever is active). The `pakman` command is added to that environment's `Scripts/` or `bin/`. **No files are scattered around your current directory.** Clean install, clean uninstall.

> **Tip for new users:** If you want to keep it isolated, create a venv first:
> ```bash
> python -m venv .venv
> .venv/Scripts/activate   # Windows
> source .venv/bin/activate  # Mac/Linux
> pip install git+https://github.com/udahar/PakMan.git
> ```
> The `~/.pakman/` data folder is shared across all your environments regardless.

---

## CLI Reference

```bash
# See what's installed
pakman list

# Browse what's available
pakman search <query>
pakman search prompt
pakman search context
pakman search routing

# Get details on a specific package
pakman info PromptSKLib
pakman info cost_optimizer

# Install a package (downloads only that package — not the whole repo)
pakman install PromptSKLib
pakman install context_distiller
pakman install cost_optimizer

# Upgrade an installed package
pakman install PromptSKLib --upgrade
pakman install PromptSKLib -u

# Install from a local folder
pakman install ./my_package

# Install directly from any udahar GitHub repo
pakman install github.com/udahar/SomeRepo

# Remove a package
pakman remove PromptSKLib

# Update packages
pakman update              # update everything
pakman update PromptSKLib  # update one package
```

---

## Available Packages

Run `pakman search` to browse everything. Quick overview by category:

| Category | Packages |
|----------|---------|
| **Prompting** | `PromptSKLib` `PromptForge` `PromptOS` `prompt_library` `prompt_evolution` `prompt_version_control` `skills_framework` `skills_registry` |
| **Context** | `context_distiller` `recursive_context` `context_cache` |
| **Routing** | `cost_optimizer` `model_router` `multi_model_orchestrator` |
| **Evaluation** | `GapMan` `eval_framework` `benchmark_arena` |
| **Memory** | `memory_graph` `browser_memory` |
| **Agents** | `council` `courtroom` |
| **Tools** | `tool_builder` `tool_composer` |
| **Infrastructure** | `scheduler` `tickets` `Alfred.rust` `AutoCode` `AiOSKernel` `apikey` |
| **Templates** | `blueprints` |

---

## How it works

### Install is lightweight — one subfolder, not the whole repo

All packages live in this PakMan repo under `packages/`. When you run:

```bash
pakman install PromptSKLib
```

PakMan uses **git sparse-checkout** to pull only `packages/PromptSKLib/` from the remote. You download a few KB of files, not the entire repository. The registry maps each package name to its subfolder.

If a package ever grows into its own standalone repo, the registry entry is updated to point there instead. The command stays the same.

### Apps auto-expand when you install a package

Apps in the ecosystem (Claw, ZolaPress, and others) scan `~/.pakman/packages/` on startup. Installing a package makes it available to every PakMan-aware app on your machine without any manual wiring.

```
pakman install PromptSKLib
        ↓
Downloads packages/PromptSKLib → ~/.pakman/packages/PromptSKLib/
        ↓
Claw starts → scans ~/.pakman/packages/ → finds PromptSKLib
        ↓
Task briefs now include PromptSKLib strategy scaffolds. No config needed.
```

### Security

- Only packages from `github.com/udahar/` can be installed. This is hard-coded and not user-configurable. It prevents anyone from pointing you at an untrusted source through a forked registry.
- Every install computes a SHA256 hash stored in `~/.pakman/`.
- Rollback to any prior version: `pakman update PromptSKLib` (shows changelog before applying).

---

## Writing your own package

Any directory with an `__init__.py` is a valid PakMan package:

```
my_package/
├── __init__.py       # export your API
├── README.md         # required — what does this add?
└── requirements.txt  # optional — pip dependencies
```

Install from a local folder:

```bash
pakman install ./my_package
```

---

## Environment variable

```bash
# Change where packages and the database are stored (default: ~/.pakman/)
PAKMAN_HOME=/data/shared/pakman pakman list
```

---

## The ecosystem

PakMan is the package layer for a family of AI-native apps. Each app discovers installed packages on startup and expands its capabilities automatically.

| App | What it is |
|-----|-----------|
| **Claw** | AI coding and automation |
| **ZolaPress** | AI-native CMS |
| **[Browser]** | Semantic web intelligence *(name TBD)* |

---

**Author:** udahar
**License:** MIT *(repository currently private — open-source release planned)*
