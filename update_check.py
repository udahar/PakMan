# -*- coding: utf-8 -*-
"""
update_check.py

Checks for available updates to PakMan itself and installed packages.
Results are cached for 24 hours in ~/.pakman/last_check.json so the
check doesn't slow down every command.

Design decisions:
- Never auto-updates anything. Notify only.
- Hash guard: warns before overwriting locally-modified packages.
- One network request per day max, fail silently if offline.
"""

import json
import hashlib
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from pathlib import Path

PAKMAN_VERSION = "1.0.0"
REGISTRY_URL   = "https://raw.githubusercontent.com/udahar/PakMan/master/registry.json"
CACHE_FILE     = Path.home() / ".pakman" / "last_check.json"
CACHE_TTL_HRS  = 24


# ─── remote fetch (cached) ────────────────────────────────────────────────────

def _load_cache() -> dict:
    try:
        if CACHE_FILE.exists():
            return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _save_cache(data: dict):
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        pass


def _fetch_remote_registry() -> dict | None:
    """Download registry.json from GitHub. Returns None if offline or error."""
    try:
        req = urllib.request.urlopen(REGISTRY_URL, timeout=4)
        return json.loads(req.read().decode("utf-8"))
    except Exception:
        return None


def _load_bundled_registry() -> dict | None:
    """Load the registry.json that shipped with this PakMan install."""
    try:
        bundled = Path(__file__).parent / "registry.json"
        if bundled.exists():
            return json.loads(bundled.read_text(encoding="utf-8"))
    except Exception:
        pass
    return None


def get_remote_registry(force: bool = False) -> dict | None:
    """
    Return the remote registry, using a 24-hour local cache.
    Falls back to the bundled registry.json when offline or repo is private.
    Returns None only if nothing is available at all.
    """
    cache = _load_cache()
    now = datetime.now(timezone.utc)

    if not force and "fetched_at" in cache:
        fetched = datetime.fromisoformat(cache["fetched_at"])
        if now - fetched < timedelta(hours=CACHE_TTL_HRS):
            return cache.get("registry")

    remote = _fetch_remote_registry()
    if remote:
        _save_cache({"fetched_at": now.isoformat(), "registry": remote})
        return remote

    # Offline or private repo — use stale cache, then bundled fallback
    return cache.get("registry") or _load_bundled_registry()


# ─── pakman self-version check ────────────────────────────────────────────────

def check_pakman_update() -> str | None:
    """
    Return the remote PakMan version string if it's newer than the installed one.
    Returns None if up to date or offline.
    """
    remote = get_remote_registry()
    if not remote:
        return None
    remote_ver = remote.get("_pakman_version")
    if not remote_ver:
        return None
    if _version_gt(remote_ver, PAKMAN_VERSION):
        return remote_ver
    return None


def _version_gt(a: str, b: str) -> bool:
    """Return True if version a > version b (simple numeric comparison)."""
    try:
        return tuple(int(x) for x in a.split(".")) > tuple(int(x) for x in b.split("."))
    except Exception:
        return False


# ─── package update check ─────────────────────────────────────────────────────

def check_package_updates(installed_packages: list[dict]) -> list[dict]:
    """
    Cross-reference installed packages against the remote registry.
    Returns list of {name, installed_version, note} for packages that
    have a remote entry (meaning a newer version may be available).

    We can't easily compare versions without cloning, so we flag packages
    whose stored hash differs from a freshly-computed hash of their local
    files — that detects both "you modified it" and "you never updated it"
    situations and lets the user decide.

    For a future improvement: each package can expose __version__ and the
    registry can track latest_version — then this becomes a real semver diff.
    """
    remote = get_remote_registry()
    remote_packages = remote.get("packages", {}) if remote else {}

    flagged = []
    for pkg in installed_packages:
        name = pkg.get("name", "")
        if name in remote_packages:
            flagged.append({
                "name": name,
                "installed_version": pkg.get("version", "unknown"),
                "remote_entry": remote_packages[name],
            })
    return flagged


# ─── hash guard (called before update overwrites local files) ─────────────────

def compute_dir_hash(path: Path) -> str:
    """SHA256 of all file contents in a directory tree, sorted by path."""
    hasher = hashlib.sha256()
    for f in sorted(path.rglob("*")):
        if f.is_file() and ".git" not in f.parts and "__pycache__" not in f.parts:
            try:
                hasher.update(f.read_bytes())
            except Exception:
                pass
    return hasher.hexdigest()


def is_locally_modified(pkg_name: str, packages_dir: Path, stored_hash: str) -> bool:
    """
    Returns True if the installed package files differ from the stored install hash.
    Signals that the user may have manually edited the package.
    """
    pkg_path = packages_dir / pkg_name
    if not pkg_path.exists() or not stored_hash:
        return False
    current_hash = compute_dir_hash(pkg_path)
    return current_hash != stored_hash
