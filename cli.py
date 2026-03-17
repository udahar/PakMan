"""
pakman - command-line interface for PakMan package manager

Usage:
    pakman list                     # show installed packages
    pakman install <name|path|url>  # install a package
    pakman remove  <name>           # uninstall a package
    pakman update  [name]           # update one or all packages
    pakman info    <name>           # show package details
    pakman search  <query>          # search available packages
"""

import argparse
import sys
from pathlib import Path

# Allow running as `python cli.py` from the PakMan directory without install
sys.path.insert(0, str(Path(__file__).parent))

from package_manager import PackageManager

_pm = None


def _get_pm() -> PackageManager:
    global _pm
    if _pm is None:
        _pm = PackageManager()
    return _pm


# ─── commands ────────────────────────────────────────────────────────────────

def cmd_list(args):
    pm = _get_pm()
    packages = pm.list_packages()
    if not packages:
        print("No packages installed.")
        return
    print(f"{'Package':<28} {'Version':<10} {'Status':<12} Source")
    print("─" * 72)
    for p in packages:
        name    = p.get("name", "?")
        version = p.get("version", "─")
        status  = p.get("status", "installed")
        source  = p.get("source", "local")
        print(f"{name:<28} {version:<10} {status:<12} {source}")
    print(f"\n{len(packages)} package(s) installed.")


def cmd_install(args):
    pm = _get_pm()
    source = args.package
    print(f"Installing {source} ...")
    try:
        result = pm.install(source, upgrade=args.upgrade, verify=not args.no_verify)
        if result:
            print(f"  Installed: {result.get('name', source)}")
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
    name = args.package or None
    target = name or "all packages"
    print(f"Updating {target} ...")
    try:
        pm.update(name, auto_confirm=True)
        print("  Done.")
    except Exception as e:
        print(f"  Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_info(args):
    pm = _get_pm()
    packages = pm.list_packages()
    match = [p for p in packages if p.get("name") == args.package]
    if not match:
        # Also check packages/ dir for unregistered packages
        pkg_dir = pm.packages_dir / args.package
        if pkg_dir.is_dir():
            print(f"Package: {args.package}")
            print(f"Path:    {pkg_dir}")
            print("Status:  present (not registered)")
            return
        print(f"Package '{args.package}' not found.", file=sys.stderr)
        sys.exit(1)
    p = match[0]
    for k, v in p.items():
        print(f"{k:<16} {v}")


def cmd_search(args):
    pm = _get_pm()
    try:
        results = pm.search(args.query)
    except Exception:
        results = []

    # Also scan packages dir for unregistered packages
    q = args.query.lower()
    registered = {r.get("name") for r in results}
    for p in pm.packages_dir.iterdir():
        if p.is_dir() and q in p.name.lower() and p.name not in registered:
            results.append({"name": p.name, "source": "local (unregistered)"})
    if not results:
        print(f"No packages matching '{args.query}'.")
        return
    for r in results:
        name   = r.get("name", "?")
        source = r.get("source", "local")
        print(f"  {name:<28} {source}")


# ─── main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog="pakman",
        description="PakMan — AI productivity package manager",
    )
    sub = parser.add_subparsers(dest="command", metavar="<command>")
    sub.required = True

    # list
    p_list = sub.add_parser("list", help="show installed packages")
    p_list.set_defaults(func=cmd_list)

    # install
    p_install = sub.add_parser("install", help="install a package")
    p_install.add_argument("package", help="package name, local path, or github URL")
    p_install.add_argument("--upgrade", "-u", action="store_true", help="upgrade if already installed")
    p_install.add_argument("--no-verify", action="store_true", help="skip hash verification")
    p_install.set_defaults(func=cmd_install)

    # remove
    p_remove = sub.add_parser("remove", help="remove a package")
    p_remove.add_argument("package", help="package name")
    p_remove.set_defaults(func=cmd_remove)

    # update
    p_update = sub.add_parser("update", help="update packages")
    p_update.add_argument("package", nargs="?", help="package name (omit for all)")
    p_update.set_defaults(func=cmd_update)

    # info
    p_info = sub.add_parser("info", help="show package details")
    p_info.add_argument("package", help="package name")
    p_info.set_defaults(func=cmd_info)

    # search
    p_search = sub.add_parser("search", help="search available packages")
    p_search.add_argument("query", help="search term")
    p_search.set_defaults(func=cmd_search)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
