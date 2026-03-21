"""
ModLib CLI - Module Library Command Line Interface

Usage:
    python -m ModLib                  # Show all modules
    python -m ModLib --status online  # Filter by status
    python -m ModLib --capabilities   # Show capabilities
    python -m ModLib --health         # Run health compliance checks
    python -m ModLib --check MODULE   # Check specific module
    python -m ModLib --json           # Output as JSON
    python -m ModLib wiki             # Build and serve unified wiki from all packages
"""

import argparse
import json
import sys
import subprocess
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from ModLib import get_registry, modules, status


def show_all(args):
    """Show all modules"""
    registry = get_registry()
    modules = registry.list_modules()
    health = registry.check_health()
    capabilities = registry.get_capabilities()

    print("📦 Frank AI Module Registry")
    print("=" * 60)
    print()
    print(f"Total: {len(modules)} modules")
    online = sum(1 for m in modules.values() if m.get("status") == "online")
    print(f"Online: {online}")
    print(f"Offline: {len(modules) - online}")
    print()

    if args.status:
        filtered = {k: v for k, v in modules.items() if v.get("status") == args.status}
        print(f"Modules with status '{args.status}':")
        for name, info in filtered.items():
            print(f"  {name}: {info.get('status', 'unknown')}")
        print()
    else:
        for name, info in modules.items():
            print(f"{name}: {info.get('status', 'unknown')}")
        print()


def show_capabilities(args):
    """Show module capabilities"""
    registry = get_registry()
    capabilities = registry.get_capabilities()

    print("🛠️  Module Capabilities")
    print("=" * 60)
    print()
    for module_name, caps in sorted(capabilities.items()):
        print(f"{module_name}:")
        for cap in caps:
            print(f"  • {cap}")
        print()


def show_health(args):
    """Run health compliance checks"""
    print("🔍 Running health compliance checks...")
    from ModLib.health import get_checker
    import asyncio

    async def run():
        checker = get_checker()
        await checker.run_all_checks()
        print(checker.get_compliance_report())

    asyncio.run(run())


def show_json(args):
    """Output as JSON"""
    registry = get_registry()
    data = {
        "modules": registry.list_modules(),
        "health": registry.check_health(),
        "capabilities": registry.get_capabilities(),
    }
    print(json.dumps(data, indent=2))


def check_module(args):
    """Check specific module"""
    print(f"🔍 Checking module: {args.module}")
    from ModLib.health import check_module
    import asyncio

    async def run():
        compliance = await check_module(args.module)
        print(f"Module: {compliance.module_name}")
        print(f"Status: {compliance.overall_status}")
        print(f"Score: {compliance.compliance_score * 100:.0f}%")
        print(f"Passed: {compliance.checks_passed}/{compliance.total_checks}")
        if compliance.blocking_issues:
            print("\nBlocking Issues:")
            for issue in compliance.blocking_issues:
                print(f"  ❌ {issue}")
        if compliance.warnings:
            print("\nWarnings:")
            for warning in compliance.warnings:
                print(f"  ⚠️  {warning}")

    asyncio.run(run())


def wiki_cmd(args):
    """Build and serve unified wiki from all PakMan packages."""
    print("📚 Building unified wiki from PakMan packages...")
    pakman_packages_dir = os.path.join(os.path.dirname(__file__), "packages")
    wiki_dir = os.path.join(os.path.dirname(__file__), "pakman_wiki")
    # Ensure wiki directory exists
    os.makedirs(wiki_dir, exist_ok=True)
    # Build wiki using wikipak
    try:
        subprocess.run(
            [sys.executable, "-m", "wikipak", "build", wiki_dir, pakman_packages_dir],
            check=True,
        )
        print(f"✅ Wiki built at {wiki_dir}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to build wiki: {e}")
        return
    # Serve wiki using zolapress
    port = args.port or 1111
    print(f"🚀 Serving wiki at http://127.0.0.1:{port} (press Ctrl+C to stop)")
    try:
        subprocess.run(
            [sys.executable, "-m", "zolapress", "serve", wiki_dir, "--port", str(port)],
            check=True,
        )
    except KeyboardInterrupt:
        print("\n🛑 Wiki server stopped.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to serve wiki: {e}")


def main():
    parser = argparse.ArgumentParser(description="ModLib - Module Library Registry")
    parser.add_argument(
        "--status",
        type=str,
        choices=["online", "offline", "degraded"],
        help="Filter by status",
    )
    parser.add_argument("--capabilities", action="store_true", help="Show capabilities")
    parser.add_argument(
        "--compliance", action="store_true", help="Run health compliance checks"
    )
    parser.add_argument(
        "--check", type=str, metavar="MODULE", help="Check specific module"
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument(
        "wiki",
        nargs="?",
        const=True,
        help="Build and serve unified wiki from all packages",
    )
    parser.add_argument(
        "--port", type=int, help="Port to serve the wiki on (default: 1111)"
    )
    args = parser.parse_args()

    if args.compliance:
        show_health(args)
    elif args.check:

        class ArgHolder:
            def __init__(self, module):
                self.module = module

        check_module(ArgHolder(args.check))
    elif args.json:
        show_json(args)
    elif args.capabilities:
        show_capabilities(args)
    elif args.status:
        show_all(args)
    elif args.wiki:
        wiki_cmd(args)
    else:
        show_all(args)


if __name__ == "__main__":
    main()
