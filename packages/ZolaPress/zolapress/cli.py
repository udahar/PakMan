"""ZolaPress CLI - Command-line interface for ZolaPress site management."""

# Standard library imports
import sys
import argparse
import json
import os

# Local imports
from .core import ZolaPressBuilder, build_site, serve_site, check_site, init_site


def build_command(args):
    """Handle the 'build' command."""
    success = build_site(args.site_dir, args.output_dir, args.base_url)
    sys.exit(0 if success else 1)


def serve_command(args):
    """Handle the 'serve' command."""
    success = serve_site(args.site_dir, args.port, args.host, not args.no_build)
    sys.exit(0 if success else 1)


def check_command(args):
    """Handle the 'check' command."""
    success = check_site(args.site_dir)
    sys.exit(0 if success else 1)


def init_command(args):
    """Handle the 'init' command."""
    success = init_site(args.site_dir, args.theme)
    sys.exit(0 if success else 1)


def config_command(args):
    """Handle the 'config' command."""
    builder = ZolaPressBuilder(args.site_dir)

    if args.get:
        config = builder.get_config()
        if args.key:
            # Navigate nested keys
            keys = args.key.split(".")
            value = config
            try:
                for key in keys:
                    value = value[key]
                print(value)
            except (KeyError, TypeError):
                print(f"Error: Key '{args.key}' not found in configuration")
                sys.exit(1)
        else:
            # Print full config
            print(json.dumps(config, indent=2))

    elif args.set:
        # Parse key=value format
        try:
            key, value_str = args.set.split("=", 1)
            # Try to parse value as JSON for proper types
            try:
                parsed_value = json.loads(value_str)
            except json.JSONDecodeError:
                # Keep as string if not valid JSON
                parsed_value = value_str

            success = builder.update_config({key: parsed_value})
            if success:
                print(f"Configuration updated: {key} = {parsed_value}")
            else:
                print("Failed to update configuration")
                sys.exit(1)
        except ValueError:
            print("Error: Invalid format for --set. Use KEY=VALUE")
            sys.exit(1)

    else:
        print("Error: Must specify either --get or --set")
        sys.exit(1)


def content_command(args):
    """Handle the 'content' command."""
    builder = ZolaPressBuilder(args.site_dir)

    if args.list:
        content_files = builder.list_content()
        if not content_files:
            print("No content files found.")
        else:
            print("Content files:")
            for cf in content_files:
                print(f"  {cf['path']}")

    elif args.create:
        front_matter = {}
        if args.title:
            front_matter["title"] = args.title
        if args.date:
            front_matter["date"] = args.date
        if args.tags:
            front_matter["tags"] = args.tags.split(",")

        success = builder.create_content(args.create, front_matter, args.content or "")
        if success:
            print(f"Content created: {args.create}")
        else:
            print("Failed to create content")
            sys.exit(1)

    else:
        print("Error: Must specify either --list or --create")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="ZolaPress - Site generation and management utilities",
        prog="zolapress",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Build command
    build_parser = subparsers.add_parser("build", help="Build the ZolaPress site")
    build_parser.add_argument("site_dir", help="Path to the ZolaPress site directory")
    build_parser.add_argument("--output-dir", help="Custom output directory")
    build_parser.add_argument("--base-url", help="Base URL for the site")
    build_parser.set_defaults(func=build_command)

    # Serve command
    serve_parser = subparsers.add_parser(
        "serve", help="Serve the ZolaPress site locally"
    )
    serve_parser.add_argument("site_dir", help="Path to the ZolaPress site directory")
    serve_parser.add_argument("--port", type=int, default=1111, help="Port to serve on")
    serve_parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    serve_parser.add_argument(
        "--no-build", action="store_true", help="Skip build before serving"
    )
    serve_parser.set_defaults(func=serve_command)

    # Check command
    check_parser = subparsers.add_parser("check", help="Check the site for errors")
    check_parser.add_argument("site_dir", help="Path to the ZolaPress site directory")
    check_parser.set_defaults(func=check_command)

    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize a new ZolaPress site")
    init_parser.add_argument("site_dir", help="Path where to create the site")
    init_parser.add_argument("--theme", help="Optional theme to initialize with")
    init_parser.set_defaults(func=init_command)

    # Config command
    config_parser = subparsers.add_parser("config", help="Manage site configuration")
    config_parser.add_argument("site_dir", help="Path to the ZolaPress site directory")
    config_group = config_parser.add_mutually_exclusive_group(required=True)
    config_group.add_argument(
        "--get", action="store_true", help="Get configuration values"
    )
    config_group.add_argument("--set", help="Set configuration value (KEY=VALUE)")
    config_parser.add_argument(
        "--key", help="Specific key to get (supports dot notation)"
    )
    config_parser.set_defaults(func=config_command)

    # Content command
    content_parser = subparsers.add_parser("content", help="Manage site content")
    content_parser.add_argument("site_dir", help="Path to the ZolaPress site directory")
    content_group = content_parser.add_mutually_exclusive_group(required=True)
    content_group.add_argument(
        "--list", action="store_true", help="List all content files"
    )
    content_group.add_argument(
        "--create", help="Create new content file (path from content dir)"
    )
    content_parser.add_argument("--title", help="Title for new content")
    content_parser.add_argument("--date", help="Date for new content (YYYY-MM-DD)")
    content_parser.add_argument("--tags", help="Tags for new content (comma-separated)")
    content_parser.add_argument("--content", help="Content for new file")
    content_parser.set_defaults(func=content_command)

    # Parse arguments
    args = parser.parse_args()

    # Handle command
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
