"""WikiPak - Package for generating a unified wiki from PakMan packages."""

import os

__version__ = "0.1.0"
__author__ = os.environ.get("PACKAGE_AUTHOR", "Richard")
__email__ = os.environ.get("PACKAGE_AUTHOR_EMAIL", "author@packages.example.com")

try:
    from .core import WikiPakBuilder, build_wiki, serve_wiki
    from .cli import main
    __all__ = [
        "WikiPakBuilder",
        "build_wiki",
        "serve_wiki",
        "main",
    ]
except ImportError:
    __all__ = []
