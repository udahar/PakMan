"""WikiPak CLI - Command-line interface for WikiPak wiki generation."""

import sys
import argparse
import os
from .core import WikiPakBuilder, build_wiki, serve_wiki


def build_command(args):
    """Handle the 'build' command."""
    success = build_wiki(
        args.wiki_dir, args.pakman_packages_dir, args.output_dir, args.base_url
    )
    sys.exit(0 if success else 1)


def serve_command(args):
    """Handle the 'serve' command."""
    success = serve_wiki(
        args.wiki_dir, args.pakman_packages_dir, args.port, args.host, not args.no_build
    )
    sys.exit(0 if success else 1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="WikiPak - Generate a unified wiki from PakMan packages",
        prog="wikipak",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Build command
    build_parser = subparsers.add_parser("build", help="Build the WikiPak wiki")
    build_parser.add_argument("wiki_dir", help="Path to the WikiPak wiki directory")
    build_parser.add_argument(
        "pakman_packages_dir", help="Path to the PakMan packages directory"
    )
    build_parser.add_argument("--output-dir", help="Custom output directory")
    build_parser.add_argument("--base-url", help="Base URL for the site")
    build_parser.set_defaults(func=build_command)

    # Serve command
    serve_parser = subparsers.add_parser("serve", help="Serve the WikiPak wiki locally")
    serve_parser.add_argument("wiki_dir", help="Path to the WikiPak wiki directory")
    serve_parser.add_argument(
        "pakman_packages_dir", help="Path to the PakMan packages directory"
    )
    serve_parser.add_argument("--port", type=int, default=1111, help="Port to serve on")
    serve_parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    serve_parser.add_argument(
        "--no-build", action="store_true", help="Skip build before serving"
    )
    serve_parser.set_defaults(func=serve_command)

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
