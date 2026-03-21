"""WikiPak — Generate a unified wiki from installed PakMan packages."""

from .wikipak import WikiPakBuilder, build_wiki, serve_wiki

__all__ = ["WikiPakBuilder", "build_wiki", "serve_wiki"]
