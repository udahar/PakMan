"""ZolaPress - Documentation and site generation package."""

import os

__version__ = "0.1.0"
__author__ = os.environ.get("PACKAGE_AUTHOR", "Richard")
__email__ = os.environ.get("PACKAGE_AUTHOR_EMAIL", "author@packages.example.com")

try:
    from .core import ZolaPressBuilder, build_site, serve_site
    from .cli import main
    __all__ = [
        "ZolaPressBuilder",
        "build_site",
        "serve_site",
        "main",
    ]
except ImportError:
    __all__ = []
