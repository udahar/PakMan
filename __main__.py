"""
ModLib CLI - Module Library Command Line Interface

Usage:
    python -m ModLib                  # Show all modules
    python -m ModLib --status online  # Filter by status
    python -m ModLib --capabilities   # Show capabilities
    python -m ModLib --health         # Health compliance check
    python -m ModLib --check MODULE   # Check specific module
"""

import argparse
import json
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from ModLib import get_registry, modules, status


def show_all(args):
    """Show all modules"""
    registry = get_registry()

    print("📦 Frank AI Module Registry")
    print("=" * 60)
    print()
    print(status())
    print()
    print(f"Total: {len(registry.modules)} modules")

    online = sum(1 for m in registry.modules.values() if m.status == "online")
    print(f"Online: {online}")
    print(f"Offline: {len(registry.modules) - online}")


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
    """Show health status"""
    registry = get_registry()
    health = registry.check_health()

    print("💚 Module Health")
    print("=" * 60)
    print()

    for module_name, score in sorted(health.items(), key=lambda x: x[1], reverse=True):
        icon = "🟢" if score > 0.8 else "🟡" if score > 0.5 else "🔴"
        bar = "█" * int(score * 10) + "░" * (10 - int(score * 10))
        print(f"{icon} {module_name:30} [{bar}] {score*100:.0f}%")


def show_json(args):
    """Show as JSON"""
    registry = get_registry()

    data = {
        "modules": registry.list_modules(),
        "health": registry.check_health(),
        "capabilities": registry.get_capabilities()
    }

    print(json.dumps(data, indent=2))


async def run_health_checks_cmd():
    """Run health compliance checks"""
    from ModLib.health import get_checker

    print("🔍 Running health compliance checks...")
    print()

    checker = get_checker()
    await checker.run_all_checks()

    print(checker.get_compliance_report())


async def check_module_cmd(module_name: str):
    """Check specific module"""
    from ModLib.health import check_module

    print(f"🔍 Checking module: {module_name}")
    print()

    compliance = await check_module(module_name)

    print(f"Module: {compliance.module_name}")
    print(f"Status: {compliance.overall_status}")
    print(f"Score: {compliance.compliance_score*100:.0f}%")
    print(f"Passed: {compliance.checks_passed}/{compliance.total_checks}")

    if compliance.blocking_issues:
        print(f"\nBlocking Issues:")
        for issue in compliance.blocking_issues:
            print(f"  ❌ {issue}")

    if compliance.warnings:
        print(f"\nWarnings:")
        for warning in compliance.warnings:
            print(f"  ⚠️  {warning}")


def main():
    parser = argparse.ArgumentParser(
        description="ModLib - Module Library Registry"
    )

    parser.add_argument(
        "--status",
        type=str,
        choices=["online", "offline", "degraded"],
        help="Filter by status"
    )

    parser.add_argument(
        "--capabilities",
        action="store_true",
        help="Show capabilities"
    )

    parser.add_argument(
        "--compliance",
        action="store_true",
        help="Run health compliance checks"
    )

    parser.add_argument(
        "--check",
        type=str,
        metavar="MODULE",
        help="Check specific module"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )

    args = parser.parse_args()

    if args.compliance:
        asyncio.run(run_health_checks_cmd())
    elif args.check:
        asyncio.run(check_module_cmd(args.check))
    elif args.json:
        show_json(args)
    elif args.capabilities:
        show_capabilities(args)
    elif args.status:
        show_all(args)  # Could filter by status
    else:
        show_all(args)


if __name__ == "__main__":
    main()
