#!/usr/bin/env python3
"""
AutoCode CLI - Command Line Interface

Usage:
    python -m autocode.cli "Build a REST API"
    python -m autocode.cli --workflow iterative "Create a calculator"
    python -m autocode.cli --stats
"""

import argparse
import json
import sys
from datetime import datetime


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="autocode",
        description="Multi-Agent Code Generation System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "Build a REST API for todo list"
  %(prog)s --workflow iterative "Create a calculator module"
  %(prog)s --model llama3.2 "Build a web scraper"
  %(prog)s --stats
  %(prog)s --agents
        """,
    )

    parser.add_argument(
        "task",
        nargs="?",
        help="Task description for the agents",
    )

    parser.add_argument(
        "--workflow",
        "-w",
        choices=["linear", "iterative"],
        default="linear",
        help="Workflow type (default: linear)",
    )

    parser.add_argument(
        "--model",
        "-m",
        default="qwen2.5:7b",
        help="Ollama model to use (default: qwen2.5:7b)",
    )

    parser.add_argument(
        "--output",
        "-o",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show system statistics",
    )

    parser.add_argument(
        "--agents",
        action="store_true",
        help="List available agents",
    )

    parser.add_argument(
        "--output-dir",
        "-d",
        help="Directory to save results",
    )

    return parser


def print_result(result: dict, verbose: bool = False):
    """Print collaboration results in text format."""
    sections = [
        ("DESIGN", "design"),
        ("IMPLEMENTATION", "implementation"),
        ("REVIEW", "review"),
        ("TESTS", "tests"),
    ]

    for title, key in sections:
        content = result.get(key, "")
        if content:
            print(f"\n{'=' * 60}")
            print(f"  {title}")
            print("=" * 60)

            if verbose or len(content) <= 1000:
                print(content)
            else:
                print(content[:1000] + "\n... (truncated)")

    print(f"\n{'=' * 60}")
    print("  SUMMARY")
    print("=" * 60)

    summary = result.get("summary", {})
    for agent, stats in summary.items():
        if isinstance(stats, dict) and "success" in stats:
            status = "OK" if stats["success"] else "FAILED"
            duration = stats.get("duration", 0)
            print(f"  {agent}: {status} ({duration:.2f}s)")

    print(f"\nTotal agents: {summary.get('total_agents', 0)}")
    print(f"Successful: {summary.get('successful', 0)}")


def show_stats(zoo):
    """Show system statistics."""
    stats = zoo.get_full_stats()

    print("\n" + "=" * 60)
    print("  AGENT STATISTICS")
    print("=" * 60)

    for agent, info in stats.get("agents", {}).items():
        print(f"  {agent}:")
        print(f"    Role: {info.get('role', 'N/A')}")
        print(f"    Tasks: {info.get('tasks_processed', 0)}")

    print("\n" + "=" * 60)
    print("  MESSAGE BUS")
    print("=" * 60)

    msg_stats = stats.get("messages", {})
    print(f"  Registered agents: {msg_stats.get('registered_agents', 0)}")
    print(f"  Messages in history: {msg_stats.get('messages_in_history', 0)}")
    print(f"  Topics: {msg_stats.get('topics', [])}")

    print("\n" + "=" * 60)
    print("  WORKFLOW ENGINE")
    print("=" * 60)

    wf_stats = stats.get("workflows", {})
    print(f"  Registered workflows: {wf_stats.get('registered_workflows', 0)}")
    print(f"  Active workflows: {wf_stats.get('active_workflows', 0)}")
    print(f"  Completed workflows: {wf_stats.get('completed_workflows', 0)}")


def show_agents():
    """List available agents."""
    from autocode.models import AgentRole

    print("\n" + "=" * 60)
    print("  AVAILABLE AGENTS")
    print("=" * 60)

    agents = [
        ("architect", AgentRole.ARCHITECT, "System design and architecture"),
        ("coder", AgentRole.CODER, "Code implementation"),
        ("reviewer", AgentRole.REVIEWER, "Code review and quality"),
        ("tester", AgentRole.TESTER, "Test creation"),
    ]

    for name, role, description in agents:
        print(f"\n  {name.upper()}")
        print(f"    Role: {role.value}")
        print(f"    Description: {description}")


def save_results(result: dict, output_dir: str):
    """Save results to files."""
    import os

    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    files = {
        "design.md": result.get("design", ""),
        "implementation.md": result.get("implementation", ""),
        "review.md": result.get("review", ""),
        "tests.md": result.get("tests", ""),
        "summary.json": json.dumps(result.get("summary", {}), indent=2),
    }

    for filename, content in files.items():
        if content:
            filepath = os.path.join(output_dir, filename)
            with open(filepath, "w") as f:
                f.write(content)
            print(f"  Saved: {filepath}")


def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if args.agents:
        show_agents()
        return 0

    if not args.task and not args.stats:
        parser.print_help()
        return 1

    if args.stats:
        from autocode.zoo_keeper import ZooKeeper

        zoo = ZooKeeper()
        show_stats(zoo)
        return 0

    print(f"Task: {args.task}")
    print(f"Workflow: {args.workflow}")
    print(f"Model: {args.model}")
    print("-" * 40)

    try:
        from autocode.zoo_keeper import ZooKeeper

        zoo = ZooKeeper(
            model=args.model,
            log_level="DEBUG" if args.verbose else "INFO",
            workflow_type=args.workflow,
        )

        result = zoo.collaborate(args.task)

        if args.output == "json":
            print(json.dumps(result, indent=2))
        else:
            print_result(result, verbose=args.verbose)

        if args.output_dir:
            save_results(result, args.output_dir)

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
