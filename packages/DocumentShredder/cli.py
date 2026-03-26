"""
DocumentShredder - cli.py
Command-line interface.

Usage:
    python -m DocumentShredder.cli conversations.html
    python -m DocumentShredder.cli report.pdf --output out.jsonl --max-tokens 256
    python -m DocumentShredder.cli ./docs/ --folder --output all.jsonl
"""
import argparse
import sys
from pathlib import Path
from . import shred, shred_folder, to_markdown, to_jsonl


def main():
    parser = argparse.ArgumentParser(
        prog="shred",
        description="DocumentShredder — Convert any document into AI-ready chunks.",
    )
    parser.add_argument("input", help="File or folder path to shred.")
    parser.add_argument("--folder", action="store_true",
                        help="Shred all files in a folder.")
    parser.add_argument("--output", "-o", default=None,
                        help="Path to write output JSONL file.")
    parser.add_argument("--format", choices=["jsonl", "markdown"], default="jsonl",
                        help="Output format (default: jsonl).")
    parser.add_argument("--max-tokens", type=int, default=512,
                        help="Max tokens per chunk (default: 512).")

    args = parser.parse_args()

    try:
        if args.folder:
            result = shred_folder(args.input, output_jsonl=args.output,
                                  max_tokens=args.max_tokens)
        else:
            result = shred(args.input, max_tokens=args.max_tokens)

        if args.format == "markdown":
            out = to_markdown(result)
        else:
            out = to_jsonl(result, filepath=args.output)

        if not args.output:
            print(out)
        else:
            print(f"Written {len(result.chunks)} chunks "
                  f"({result.total_tokens} tokens) → {args.output}")

    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
