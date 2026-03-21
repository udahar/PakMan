# Contributing to PakMan

There are two ways to contribute packages: **official packages** (in this repo, maintained by udahar) and **community packages** (your own repo, installed with `--community`).

---

## Community packages

The fastest path. Build your package in your own repo — PakMan can install it directly.

### Package structure

Any Python directory with these two files is a valid PakMan package:

```
my_package/
├── __init__.py       # export your public API
├── README.md         # required: what does this package add?
└── requirements.txt  # optional: pip dependencies
```

That's the minimum. Users install it with:

```bash
pakman install --community github.com/you/my_package
```

The `--community` flag is required for all non-udahar sources. It shows a warning and asks for confirmation before installing. This is intentional — it keeps users aware they are stepping outside the curated set.

### What makes a good package

- **Does one thing.** A package that does one thing well is composable. A package that does everything is an app.
- **Has a real README.** The README is what `pakman info` and `pakman wiki` surface. Write it for someone who has never seen your code.
- **Exports a clean `__init__.py`.** Other packages and apps import from your package. Keep the public surface intentional.
- **No hardcoded paths.** Use `Path.home() / ".pakman"` for any persistent state, not `./` relative paths.
- **No network calls on import.** Imports should be instant. Connect to things inside functions, not at module level.

### Listing in the community registry

If your package is stable and you want it discoverable via `pakman search`, open a pull request adding an entry to `community-registry.json`:

```json
"my_package": {
  "repo": "github.com/you/my_package",
  "description": "One sentence describing what this adds.",
  "category": "tools",
  "tags": ["your", "tags"],
  "status": "beta",
  "author": "your-github-username"
}
```

Community registry entries are reviewed before merging. The bar is: does it install cleanly, does it have a README, and is the description accurate? We don't evaluate the quality of the code — that's on the user to decide.

---

## Official packages

Official packages live in this repo under `packages/` and are installed without the `--community` flag. They are maintained by udahar.

To propose an official package, open an issue describing what it does and why it belongs in the core set. The bar is higher: it needs to be generally useful across the ecosystem, not just for one use case.

---

## Running the audit tool

Before any PR, run:

```bash
python sync_registry.py
```

This checks that every package has `__init__.py` and `README.md` and that the registry is in sync with the packages on disk. Fix any reported issues before opening a PR.

---

## Questions

Open an issue. No template required — just describe what you're trying to do.
