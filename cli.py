# -*- coding: utf-8 -*-
"""
pakman - command-line interface for PakMan package manager

Usage:
    pakman list                     # show installed packages
    pakman install <name|path|url>  # install a package
    pakman remove  <name>           # uninstall a package
    pakman update  [name]           # update one or all packages
    pakman info    <name>           # show package details
    pakman search  <query>          # search available and installed packages
    pakman wiki               [--port PORT]  # build and serve unified wiki from all packages
"""

import argparse
import json
import sys
from pathlib import Path

# Force UTF-8 output on Windows — prevents UnicodeEncodeError when emoji hits a
# CP1252 terminal, which would silently roll back installs mid-copy.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Allow running as `python cli.py` from the PakMan directory without install
sys.path.insert(0, str(Path(__file__).parent))

from package_manager import PackageManager
from update_check import (
    check_pakman_update,
    check_package_updates,
    is_locally_modified,
    PAKMAN_VERSION,
)

_pm = None
_registry = None

REGISTRY_FILE = Path(__file__).parent / "registry.json"


def _get_pm() -> PackageManager:
    global _pm
    if _pm is None:
        _pm = PackageManager()
    return _pm


def _get_registry() -> dict:
    """Load registry.json — maps short names to GitHub repos."""
    global _registry
    if _registry is None:
        if REGISTRY_FILE.exists():
            try:
                data = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
                _registry = data.get("packages", {})
            except Exception:
                _registry = {}
        else:
            _registry = {}
    return _registry


def _resolve_source(name: str) -> tuple[str, dict | None]:
    """
    Resolve a short package name to a GitHub source string via registry.json.
    Returns (resolved_source, registry_entry | None).

    Source format:
      - Full repo clone:         github.com/udahar/MyRepo
      - Monorepo subfolder:     github.com/udahar/PakMan#packages/PromptSKLib
      - Local path:             ./my_package  or  /abs/path
    """
    # Already a URL or local path — use as-is
    if (
        name.startswith("github.com/")
        or name.startswith("https://")
        or name.startswith("./")
        or name.startswith("/")
        or Path(name).exists()
    ):
        return name, None

    registry = _get_registry()
    entry = registry.get(name)
    if entry:
        repo = entry["repo"]
        path = entry.get("path")
        source = f"{repo}#{path}" if path else repo
        return source, entry

    # Not in registry — pass through and let the installer try it
    return name, None


# --- commands ---


def cmd_wiki(args):
    """Build and serve unified wiki from all PakMan packages.

    Requires: Zola static site generator (https://www.getzola.org/documentation/getting-started/installation/)
    Install: winget install getzola.zola  (Windows)
             brew install zola            (macOS)
             snap install zola --edge     (Linux)
    """
    import subprocess, os, shutil

    # Check Zola is available before doing any work
    if not shutil.which("zola"):
        print(
            "  Error: Zola is not installed or not on PATH.\n"
            "  pakman wiki requires Zola to render the documentation site.\n\n"
            "  Install Zola:\n"
            "    Windows : winget install getzola.zola\n"
            "    macOS   : brew install zola\n"
            "    Linux   : snap install zola --edge\n"
            "              or see https://www.getzola.org/documentation/getting-started/installation/",
            file=sys.stderr,
        )
        sys.exit(1)

    pakman_packages_dir = os.path.join(os.path.dirname(__file__), "packages")
    wiki_dir = os.path.join(os.path.dirname(__file__), "pakman_wiki")
    os.makedirs(wiki_dir, exist_ok=True)

    # Build wiki using wikipak
    try:
        subprocess.run(
            ["wikipak", "build", wiki_dir, pakman_packages_dir],
            check=True,
        )
        print(f"  Wiki built at {wiki_dir}")
    except subprocess.CalledProcessError as e:
        print(f"  Error building wiki: {e}", file=sys.stderr)
        return
    except FileNotFoundError:
        print(
            "  Error: wikipak command not found.\n"
            "  Run: pakman install WikiPak",
            file=sys.stderr,
        )
        return

    # Serve
    port = args.port or 1111
    print(f"  Serving wiki at http://127.0.0.1:{port}  (Ctrl+C to stop)")
    try:
        subprocess.run(
            ["zolapress", "serve", wiki_dir, "--port", str(port)],
            check=True,
        )
    except KeyboardInterrupt:
        print("\n  Wiki server stopped.")
    except subprocess.CalledProcessError as e:
        print(f"  Error: {e}", file=sys.stderr)


def cmd_list(args):
    pm = _get_pm()
    packages = pm.list_packages()
    if not packages:
        print("No packages installed.")
        _print_update_notices([])
        return
    print(f"{'Package':<28} {'Version':<10} {'Status':<12} Source")
    print("-" * 72)
    for p in packages:
        name = p.get("name", "?")
        version = p.get("version", "-")
        status = p.get("status", "installed")
        source = p.get("source", "local")
        print(f"{name:<28} {version:<10} {status:<12} {source}")
    print(f"\n{len(packages)} package(s) installed.")
    _print_update_notices(packages)


def _print_update_notices(packages: list):
    """Quietly check for updates (cached 24h) and print a one-line notice if any."""
    try:
        # PakMan self-update
        newer_pakman = check_pakman_update()
        if newer_pakman:
            print(
                f"\n  [pakman] New version available: {PAKMAN_VERSION} -> {newer_pakman}"
            )
            print(
                "           Run: pip install --upgrade git+https://github.com/udahar/PakMan.git"
            )

        # Package updates (packages that exist in the remote registry)
        if packages:
            available = check_package_updates(packages)
            if available:
                names = ", ".join(p["name"] for p in available[:5])
                extra = f" (+{len(available) - 5} more)" if len(available) > 5 else ""
                print(f"\n  [packages] Updates may be available for: {names}{extra}")
                print("             Run: pakman update")
    except Exception:
        pass  # Never let the update check crash the main command


def cmd_install(args):
    pm = _get_pm()
    source, entry = _resolve_source(args.package)
    community = getattr(args, "community", False)

    # Community install: explicit opt-in required for non-udahar sources
    if source.startswith("github.com") and not source.startswith("github.com/udahar"):
        if not community:
            print(
                f"  Error: '{source}' is not an official PakMan package.\n"
                "  Community packages require explicit opt-in:\n"
                f"    pakman install --community {args.package}\n"
                "  Only install community packages from authors you trust.",
                file=sys.stderr,
            )
            sys.exit(1)
        # Community warning — must confirm
        print("  *** COMMUNITY PACKAGE ***")
        print(f"  Source : {source}")
        print("  This package is NOT maintained by udahar.")
        print("  Only continue if you trust this source.")
        answer = input("  Install anyway? [y/N] ").strip().lower()
        if answer != "y":
            print("  Aborted.")
            return

    if entry:
        print(f"  {entry['description']}")
        print(f"  Source: {source}")

    print(f"Installing {args.package} ...")
    try:
        result = pm.install(
            source,
            upgrade=args.upgrade,
            verify=not args.no_verify,
            allow_untrusted=community,
        )
        if result:
            print(f"  Installed: {result}")
        else:
            print("  Already up to date.")
    except Exception as e:
        print(f"  Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_remove(args):
    pm = _get_pm()
    print(f"Removing {args.package} ...")
    try:
        pm.uninstall(args.package)
        print(f"  Removed: {args.package}")
    except Exception as e:
        print(f"  Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_update(args):
    pm = _get_pm()
    packages = pm.list_packages()

    # Determine which packages to update
    targets = [p for p in packages if not args.package or p["name"] == args.package]
    if not targets:
        print(
            f"Package '{args.package}' not installed."
            if args.package
            else "No packages installed."
        )
        return

    # Hash guard: warn about locally-modified packages before overwriting
    modified = []
    for p in targets:
        if is_locally_modified(p["name"], pm.packages_dir, p.get("hash", "")):
            modified.append(p["name"])

    if modified and not args.yes:
        print("  Warning: these packages have been modified locally:")
        for m in modified:
            print(f"    - {m}")
        print("  Updating will overwrite your local changes.")
        answer = input("  Continue? [y/N] ").strip().lower()
        if answer != "y":
            print("  Aborted.")
            return

    target_label = args.package or "all packages"
    print(f"Updating {target_label} ...")
    try:
        pm.update(args.package, auto_confirm=True)
        print("  Done.")
    except Exception as e:
        print(f"  Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_info(args):
    pm = _get_pm()

    # Check registry for metadata even if not installed
    registry = _get_registry()
    reg_entry = registry.get(args.package)

    packages = pm.list_packages()
    installed = next((p for p in packages if p.get("name") == args.package), None)

    if not installed:
        # Check packages/ dir for unregistered local presence
        pkg_dir = pm.packages_dir / args.package
        local_present = pkg_dir.is_dir()
        if not local_present and not reg_entry:
            print(f"Package '{args.package}' not found.", file=sys.stderr)
            sys.exit(1)

    if reg_entry:
        print(f"{'name':<16} {args.package}")
        print(f"{'description':<16} {reg_entry.get('description', '-')}")
        print(f"{'category':<16} {reg_entry.get('category', '-')}")
        print(f"{'tags':<16} {', '.join(reg_entry.get('tags', []))}")
        print(f"{'repo':<16} {reg_entry.get('repo', '-')}")
        print(f"{'status':<16} {reg_entry.get('status', '-')}")

    if installed:
        print(f"{'installed':<16} yes (v{installed.get('version', '?')})")
        print(f"{'local_source':<16} {installed.get('source', '-')}")
    else:
        print(f"{'installed':<16} no")


def cmd_search(args):
    pm = _get_pm()
    q = args.query.lower()

    # Search registry (available packages)
    registry = _get_registry()
    reg_matches = {
        name: entry
        for name, entry in registry.items()
        if q in name.lower()
        or q in entry.get("description", "").lower()
        or any(q in t for t in entry.get("tags", []))
    }

    # Search installed packages
    try:
        installed = {p["name"]: p for p in pm.search(args.query)}
    except Exception:
        installed = {}

    # Union: show registry entries, annotate installed ones
    all_names = sorted(set(reg_matches) | set(installed))

    if not all_names:
        print(f"No packages matching '{args.query}'.")
        return

    print(f"{'Package':<28} {'Status':<14} Description")
    print("-" * 72)
    for name in all_names:
        entry = reg_matches.get(name, {})
        is_installed = name in installed
        status = "installed" if is_installed else "available"
        desc = entry.get("description", installed.get(name, {}).get("source", ""))
        # Truncate description for display
        desc = desc[:42] + "..." if len(desc) > 45 else desc
        print(f"  {name:<26} {status:<14} {desc}")


# --- main ---


def main():
    parser = argparse.ArgumentParser(
        prog="pakman",
        description="PakMan — AI productivity package manager",
    )
    parser.add_argument(
        "--version", "-V", action="version", version=f"pakman {PAKMAN_VERSION}"
    )
    sub = parser.add_subparsers(dest="command", metavar="<command>")
    sub.required = True

    # list
    p_list = sub.add_parser("list", help="show installed packages")
    p_list.set_defaults(func=cmd_list)

    # install
    p_install = sub.add_parser("install", help="install a package")
    p_install.add_argument("package", help="package name, local path, or github URL")
    p_install.add_argument(
        "--upgrade", "-u", action="store_true", help="upgrade if already installed"
    )
    p_install.add_argument(
        "--no-verify", action="store_true", help="skip hash verification"
    )
    p_install.add_argument(
        "--community",
        action="store_true",
        help="allow installing from non-udahar GitHub sources (shows warning, requires confirmation)",
    )
    p_install.set_defaults(func=cmd_install)

    # remove
    p_remove = sub.add_parser("remove", help="remove a package")
    p_remove.add_argument("package", help="package name")
    p_remove.set_defaults(func=cmd_remove)

    # update
    p_update = sub.add_parser("update", help="update packages")
    p_update.add_argument("package", nargs="?", help="package name (omit for all)")
    p_update.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="skip modified-file warning (CI/automation)",
    )
    p_update.set_defaults(func=cmd_update)

    # info
    p_info = sub.add_parser("info", help="show package details")
    p_info.add_argument("package", help="package name")
    p_info.set_defaults(func=cmd_info)

    # search
    p_search = sub.add_parser("search", help="search available packages")
    p_search.add_argument("query", help="search term")
    p_search.set_defaults(func=cmd_search)

    # wiki
    p_wiki = sub.add_parser(
        "wiki", help="build and serve unified wiki from all packages"
    )
    p_wiki.add_argument(
        "--port", type=int, help="Port to serve the wiki on (default: 1111)"
    )
    p_wiki.set_defaults(func=cmd_wiki)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
