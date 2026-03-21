"""ZolaPress - Documentation and site generation package."""

__version__ = "0.1.0"
__author__ = "Richard"
__email__ = "richard@example.com"

# Public API exports
from .core import ZolaPressBuilder, build_site, serve_site
from .cli import main

__all__ = [
    "ZolaPressBuilder",
    "build_site",
    "serve_site",
    "main",
]
