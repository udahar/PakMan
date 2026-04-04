# -*- coding: utf-8 -*-
import sys as _sys
from pathlib import Path as _Path
_pkg_root = str(_Path(__file__).parent.parent)
if _pkg_root not in _sys.path:
    _sys.path.insert(0, _pkg_root)

from .core import (
    PackageManager,
    get_package_manager,
    install,
    uninstall,
    list_packages,
    get_package,
    update,
    check_updates,
    rollback_to,
    list_versions,
    get_changelog,
    search,
    get_stats
)
from security import SecurityManager, trust_source

__all__ = [
    "PackageManager",
    "SecurityManager",
    "get_package_manager",
    "install",
    "uninstall",
    "list_packages",
    "get_package",
    "update",
    "check_updates",
    "rollback_to",
    "list_versions",
    "get_changelog",
    "search",
    "get_stats",
    "trust_source",
]
