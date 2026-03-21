#!/usr/bin/env python3
"""
sync_registry.py — Audit PakMan packages vs registry.json

Scans packages/ directory and reports:
  - Packages on disk but missing from registry (need to be added)
  - Registry entries with no package folder (stale)
  - Packages missing required files (__init__.py, README.md)

Run before any publish/commit to catch gaps.
Usage: python sync_registry.py [--fix]
  --fix   Adds missing registry stubs for unregistered packages (review before committing)
"""

import json
import sys
import os
from pathlib import Path

ROOT = Path(__file__).parent
PACKAGES_DIR = ROOT / "packages"
REGISTRY_FILE = ROOT / "registry.json"

# Packages that are not Python — skip __init__.py check
NON_PYTHON_PACKAGES = {"Alfred.rust"}

# Items in packages/ that are not packages (files, not dirs handled by iterdir already)
# but also skip these names even if they somehow appear as dirs
SKIP_NAMES = {"damagereport.md"}

CATEGORY_HINTS = {
    "prompt": "prompting", "skill": "prompting", "forge": "prompting",
    "context": "context", "memory": "memory", "graph": "memory",
    "router": "routing", "routing": "routing", "cost": "routing", "model": "routing",
    "eval": "evaluation", "bench": "evaluation", "gap": "evaluation",
    "agent": "agents", "council": "agents", "court": "agents",
    "tool": "tools", "composer": "tools",
    "schedule": "infrastructure", "ticket": "infrastructure", "autocode": "infrastructure",
    "kernel": "infrastructure", "alfred": "infrastructure", "apikey": "infrastructure",
    "wiki": "knowledge", "pak": "infrastructure", "health": "infrastructure",
    "zola": "cms", "browser": "knowledge", "linkedin": "knowledge",
    "lora": "ml", "mlstack": "ml", "stock": "finance", "rom": "entertainment",
    "sup": "productivity", "proj": "productivity",
}

def guess_category(name: str) -> str:
    lower = name.lower()
    for hint, cat in CATEGORY_HINTS.items():
        if hint in lower:
            return cat
    return "tools"

def check_package(pkg_dir: Path) -> list[str]:
    issues = []
    if pkg_dir.name not in NON_PYTHON_PACKAGES:
        if not (pkg_dir / "__init__.py").exists():
            issues.append("missing __init__.py")
    if not (pkg_dir / "README.md").exists():
        issues.append("missing README.md")
    return issues

def main():
    fix_mode = "--fix" in sys.argv

    with open(REGISTRY_FILE) as f:
        registry = json.load(f)

    # External packages live in separate repos — exclude from disk checks
    external_packages = {k for k, v in registry["packages"].items() if v.get("external")}
    reg_packages = set(registry["packages"].keys())
    disk_packages = {d.name for d in PACKAGES_DIR.iterdir() if d.is_dir() and d.name not in SKIP_NAMES}

    missing_from_registry = sorted(disk_packages - reg_packages)
    stale_in_registry = sorted((reg_packages - disk_packages) - external_packages)

    print(f"Registry entries : {len(reg_packages)}")
    print(f"Packages on disk : {len(disk_packages)}")
    print()

    if stale_in_registry:
        print(f"STALE (in registry, no folder):")
        for name in stale_in_registry:
            print(f"  STALE  {name}")
        print()

    if missing_from_registry:
        print(f"UNREGISTERED (folder exists, not in registry):")
        for name in missing_from_registry:
            issues = check_package(PACKAGES_DIR / name)
            issue_str = f"  [{', '.join(issues)}]" if issues else ""
            print(f"  +  {name}{issue_str}")
        print()

    # Check all registered packages for required files
    print("REGISTERED PACKAGES — file check:")
    all_ok = True
    for name in sorted(reg_packages):
        pkg_dir = PACKAGES_DIR / name
        if not pkg_dir.exists():
            continue
        issues = check_package(pkg_dir)
        if issues:
            print(f"  FAIL  {name}: {', '.join(issues)}")
            all_ok = False
    if all_ok:
        print("  OK  All registered packages have __init__.py and README.md")
    print()

    if fix_mode and missing_from_registry:
        print("--fix: Adding registry stubs for unregistered packages...")
        for name in missing_from_registry:
            category = guess_category(name)
            registry["packages"][name] = {
                "repo": "github.com/udahar/PakMan",
                "description": f"{name} package",
                "category": category,
                "tags": [category],
                "status": "beta",
                "path": f"packages/{name}"
            }
            print(f"  ADDED stub: {name} (category: {category})")

        with open(REGISTRY_FILE, "w") as f:
            json.dump(registry, f, indent=2)
        print(f"\nRegistry updated. Review registry.json before committing.")
        print("Edit descriptions and tags — the stubs are placeholders only.")
    elif missing_from_registry and not fix_mode:
        print(f"Run with --fix to add registry stubs for the {len(missing_from_registry)} unregistered packages.")

if __name__ == "__main__":
    main()
