"""WikiPak - Package for generating a unified wiki from PakMan packages."""

__version__ = "0.1.0"
__author__ = "Richard"
__email__ = "richard@example.com"

# Public API exports
from .core import WikiPakBuilder, build_wiki, serve_wiki
from .cli import main

__all__ = [
    "WikiPakBuilder",
    "build_wiki",
    "serve_wiki",
    "main",
]
