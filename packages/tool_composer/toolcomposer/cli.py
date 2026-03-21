#!/usr/bin/env python3
"""
Tool Composer CLI - Command Line Interface

Usage:
    python -m toolcomposer.cli run pipeline.json
    python -m toolcomposer.cli validate pipeline.json
    python -m toolcomposer.cli list
    python -m toolcomposer.cli create --type llm --name "My Node"
"""

import argparse
import json
import sys
from datetime import datetime


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="toolcomposer",
        description="Visual AI Workflow Builder - CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s run my_pipeline.json
  %(prog)s validate my_pipeline.json
  %(prog)s list
  %(prog)s create --type llm --name "Code Reviewer"
  %(prog)s execute-node pipeline.json node_1 --input '{"prompt": "test"}'
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run a pipeline")
    run_parser.add_argument("pipeline", help="Pipeline JSON file")
    run_parser.add_argument(
        "--input", "-i", default='{}', help="Initial input (JSON string)"
    )
    run_parser.add_argument(
        "--output", "-o", choices=["text", "json"], default="text", help="Output format"
    )

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate a pipeline")
    validate_parser.add_argument("pipeline", help="Pipeline JSON file")

    # List command
    subparsers.add_parser("list", help="List available node types")

    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new pipeline")
    create_parser.add_argument("--name", "-n", required=True, help="Pipeline name")
    create_parser.add_argument(
        "--description", "-d", default="", help="Pipeline description"
    )
    create_parser.add_argument(
        "--output", "-o", default=None, help="Output file (optional)"
    )

    # Execute-node command
    exec_parser = subparsers.add_parser("execute-node", help="Execute a single node")
    exec_parser.add_argument("pipeline", help="Pipeline JSON file")
    exec_parser.add_argument("node_id", help="Node ID to execute")
    exec_parser.add_argument(
        "--input", "-i", default='{}', help="Input for the node (JSON string)"
    )

    # Info command
    info_parser = subparsers.add_parser("info", help="Show pipeline information")
    info_parser.add_argument("pipeline", help="Pipeline JSON file")

    return parser


def cmd_run(args):
    """Run a pipeline command."""
    from toolcomposer.serializer import load_pipeline
    from toolcomposer.flow_engine import FlowEngine

    pipeline = load_pipeline(args.pipeline)
    if not pipeline:
        print(f"Error: Failed to load pipeline from {args.pipeline}")
        return 1

    try:
        inputs = json.loads(args.input)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}")
        return 1

    print(f"Running pipeline: {pipeline.name}")
    print(f"Nodes: {len(pipeline.nodes)}, Edges: {len(pipeline.edges)}")
    print("-" * 40)

    engine = FlowEngine(pipeline)
    result = engine.execute(inputs)

    if args.output == "json":
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(f"\nStatus: {'Success' if result.success else 'Failed'}")
        print(f"Duration: {result.duration_ms:.0f}ms")
        print(f"Nodes executed: {len(result.node_results)}")

        if result.error:
            print(f"Error: {result.error}")

        print("\nNode Results:")
        for node_result in result.node_results:
            status = "✓" if node_result.success else "✗"
            print(f"  {status} {node_result.node_id}: {node_result.status}")

        if result.final_output:
            print("\nFinal Output:")
            if isinstance(result.final_output, dict):
                print(json.dumps(result.final_output, indent=2))
            else:
                print(str(result.final_output)[:1000])

    return 0 if result.success else 1


def cmd_validate(args):
    """Validate a pipeline command."""
    from toolcomposer.serializer import load_pipeline, validate_pipeline

    pipeline = load_pipeline(args.pipeline)
    if not pipeline:
        print(f"Error: Failed to load pipeline from {args.pipeline}")
        return 1

    is_valid, errors = validate_pipeline(pipeline)

    if is_valid:
        print("✓ Pipeline is valid")
        return 0
    else:
        print("✗ Pipeline validation failed:")
        for error in errors:
            print(f"  - {error}")
        return 1


def cmd_list(args):
    """List available node types."""
    from toolcomposer.node_registry import get_available_nodes

    nodes = get_available_nodes()

    print("Available Node Types:")
    print("=" * 60)

    categories = {}
    for node in nodes:
        cat = node["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(node)

    for category, category_nodes in sorted(categories.items()):
        print(f"\n{category.upper()}")
        print("-" * 40)
        for node in category_nodes:
            print(f"  {node['type']:15} - {node.get('description', 'No description')}")
            print(f"                  Inputs: {', '.join(node['inputs'])}")
            print(f"                  Outputs: {', '.join(node['outputs'])}")

    return 0


def cmd_create(args):
    """Create a new pipeline command."""
    from toolcomposer.models import PipelineConfig
    from toolcomposer.serializer import PipelineSerializer

    pipeline = PipelineConfig(
        id="pipeline_" + datetime.now().strftime("%Y%m%d%H%M%S"),
        name=args.name,
        description=args.description,
    )

    serializer = PipelineSerializer()
    json_str = serializer.to_json(pipeline)

    if args.output:
        if serializer.save_to_file(pipeline, args.output):
            print(f"Pipeline saved to: {args.output}")
        else:
            print("Failed to save pipeline")
            return 1
    else:
        print(json_str)

    return 0


def cmd_execute_node(args):
    """Execute a single node command."""
    from toolcomposer.serializer import load_pipeline
    from toolcomposer.flow_engine import FlowEngine

    pipeline = load_pipeline(args.pipeline)
    if not pipeline:
        print(f"Error: Failed to load pipeline from {args.pipeline}")
        return 1

    try:
        inputs = json.loads(args.input)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}")
        return 1

    engine = FlowEngine(pipeline)

    print(f"Executing node: {args.node_id}")
    result = engine.execute_node(args.node_id, inputs)

    print(f"Status: {result.status}")
    if result.success:
        print(f"Output: {result.output}")
    else:
        print(f"Error: {result.error}")

    return 0 if result.success else 1


def cmd_info(args):
    """Show pipeline information command."""
    from toolcomposer.serializer import load_pipeline, PipelineSerializer

    pipeline = load_pipeline(args.pipeline)
    if not pipeline:
        print(f"Error: Failed to load pipeline from {args.pipeline}")
        return 1

    serializer = PipelineSerializer()
    summary = serializer.get_summary(pipeline)

    print(f"Pipeline: {summary['name']}")
    print(f"Description: {summary['description'] or '(none)'}")
    print(f"Version: {summary['version']}")
    print(f"Created: {summary.get('created_at', 'Unknown')}")
    print()
    print(f"Nodes: {summary['node_count']}")
    print(f"Edges: {summary['edge_count']}")
    print()
    print("Node Types:")
    for node_type, count in summary["node_types"].items():
        print(f"  {node_type}: {count}")

    return 0


def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    commands = {
        "run": cmd_run,
        "validate": cmd_validate,
        "list": cmd_list,
        "create": cmd_create,
        "execute-node": cmd_execute_node,
        "info": cmd_info,
    }

    handler = commands.get(args.command)
    if handler:
        return handler(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
