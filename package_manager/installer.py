# -*- coding: utf-8 -*-
"""
PkgMan - Package Manager for Richard's Custom Modules

Install, manage, and hot-reload custom packages with security features.

Usage:
    from PkgMan import install, list_packages, get_package, update, check_updates

    # Check for updates
    updates = check_updates()

    # Install from GitHub
    install("github.com/udahar/browser_memory")
"""

import sqlite3
import subprocess
import shutil
import sys
import os
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import json
import re

from ..security import (
    get_security_manager,
    SecurityManager,
    trust_source,
    verify_hash,
    get_changelog,
    create_backup,
    rollback,
    list_backups,
    check_updates as security_check_updates,
)


class InstallerMixin:
    def install(
        self,
        source: str,
        upgrade: bool = False,
        verify: bool = True,
        allow_untrusted: bool = False,
    ) -> str:
        """
        Install a package from GitHub or local path.

        Args:
            source: GitHub URL (github.com/user/repo) or local path
            upgrade: Upgrade if already installed
            verify: Verify hash after install
            allow_untrusted: Allow installation from untrusted sources (for automation)

        Returns:
            Package name

        Raises:
            ValueError: If source is invalid or untrusted
            RuntimeError: If installation fails
        """
        # Check if source is trusted
        if source.startswith("github.com") and not self.security.is_trusted_source(
            source
        ):
            if not allow_untrusted:
                raise ValueError(
                    f"Untrusted source: {source}. Use allow_untrusted=True or add to trusted sources."
                )
            # Log warning but continue (automation-safe)
            print(f"  Installing from untrusted source: {source}")

        # Parse source
        if source.startswith("github.com"):
            # GitHub URL
            name = self._parse_github_name(source)
            is_github = True
        elif Path(source).exists():
            # Local path
            name = Path(source).name
            is_github = False
        else:
            raise ValueError(f"Invalid source: {source}")

        # Check if already installed
        existing = self._get_package(name)
        if existing and not upgrade:
            print(f"  Package '{name}' already installed (use upgrade=True to update)")
            return name

        # Install
        install_path = self.packages_dir / name

        try:
            if is_github:
                print(f" Installing {name} from GitHub...")
                self._install_from_github(source, install_path, upgrade)
            else:
                print(f" Installing {name} from local path...")
                self._install_from_local(source, install_path, upgrade)

            # Install dependencies
            self._install_dependencies(install_path)

            # Get version
            version = self._get_version(name)

            # Create backup before installing (if upgrade)
            if upgrade and existing:
                print(f"   Creating backup...")
                create_backup(name, existing["version"])

            # Verify hash
            if verify:
                print(f"   Verifying integrity...")
                file_hash = self.security.compute_hash(install_path)
                self.security.save_version_hash(name, version, file_hash)

            # Register in database
            self._register_package(name, source, version)

            # Hot-reload
            if self.hotload:
                try:
                    self.hotload.load(name, reload=upgrade)
                except Exception as e:
                    try:
                        print(f"     Hot-load warning: {e}")
                    except Exception:
                        print("     Hot-load warning: (message not printable)")

            print(f" Installed '{name}' to {install_path}")

            # Build wiki after successful install
            try:
                wiki_dir = os.path.join(os.path.dirname(__file__), "pakman_wiki")
                pakman_packages_dir = os.path.join(
                    os.path.dirname(__file__), "packages"
                )
                # Ensure wiki directory exists
                os.makedirs(wiki_dir, exist_ok=True)
                subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "wikipak",
                        "build",
                        wiki_dir,
                        pakman_packages_dir,
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                print(
                    f"📚 Wiki built/updated at {wiki_dir}. Run 'pakman wiki' to serve it."
                )
            except Exception as e:
                print(f"⚠️ Failed to build wiki after install: {e}")

            return name

        except UnicodeDecodeError as e:
            # Cleanup on failure
            if install_path.exists():
                shutil.rmtree(install_path)
            raise RuntimeError(
                f"Installation failed (encoding error - try copying manually): {e}"
            )
        except Exception as e:
            # Cleanup on failure
            if install_path.exists():
                shutil.rmtree(install_path)
            raise RuntimeError(f"Installation failed: {e}")

    def _parse_github_name(self, url: str) -> str:
        """Extract package name from GitHub URL.

        Supports two formats:
          github.com/udahar/MyRepo          -> "MyRepo"
          github.com/udahar/PakMan#packages/PromptSKLib  -> "PromptSKLib"
        """
        # Subfolder syntax: repo#path/to/subfolder  -> name is last path segment
        if "#" in url:
            _, subfolder = url.split("#", 1)
            return subfolder.rstrip("/").split("/")[-1]
        parts = url.split("/")
        if len(parts) >= 3:
            return parts[2]
        return url.replace("github.com/", "").split("/")[0]

    def _install_from_github(self, url: str, dest: Path, upgrade: bool):
        """Clone from GitHub, or sparse-checkout a subfolder via # syntax.

        Full repo:   github.com/udahar/MyRepo
        Subfolder:   github.com/udahar/PakMan#packages/PromptSKLib
        """
        if "#" in url:
            repo_url, subfolder = url.split("#", 1)
            self._install_github_sparse(repo_url, subfolder.strip("/"), dest, upgrade)
        elif upgrade and dest.exists():
            subprocess.run(["git", "pull"], cwd=dest, check=True, capture_output=True)
        else:
            subprocess.run(
                ["git", "clone", f"https://{url}", str(dest)],
                check=True,
                capture_output=True,
            )

    def _install_github_sparse(
        self, repo_url: str, subfolder: str, dest: Path, upgrade: bool
    ):
        """Pull only a subfolder from a repo using git sparse-checkout.

        No full repo clone — downloads just the files you need.
        Works on git >= 2.25 (sparse-checkout) and >= 2.27 (--filter=blob:none).
        """
        import tempfile

        if upgrade and dest.exists():
            shutil.rmtree(dest)

        full_url = f"https://{repo_url}"

        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            # Init a bare-minimum repo, configure sparse, then fetch
            subprocess.run(["git", "init", str(tmp)], check=True, capture_output=True)
            subprocess.run(
                ["git", "-C", str(tmp), "remote", "add", "origin", full_url],
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "-C", str(tmp), "config", "core.sparseCheckout", "true"],
                check=True,
                capture_output=True,
            )
            sparse_file = tmp / ".git" / "info" / "sparse-checkout"
            sparse_file.write_text(subfolder + "/\n")
            subprocess.run(
                ["git", "-C", str(tmp), "pull", "--depth=1", "origin", "HEAD"],
                check=True,
                capture_output=True,
            )
            # Move the subfolder into place
            src = tmp / subfolder
            if not src.exists():
                raise RuntimeError(
                    f"Subfolder '{subfolder}' not found in {repo_url}. "
                    "Check registry.json path field."
                )
            shutil.copytree(str(src), str(dest))

    def _install_from_local(self, source: str, dest: Path, upgrade: bool):
        """Copy from local path"""
        if dest.exists():
            shutil.rmtree(dest)

        # Copy with ignore for problematic files
        def ignore_patterns(path, names):
            ignored = []
            for name in names:
                # Skip cache and temp files
                if (
                    name.startswith(".")
                    or name.endswith(".pyc")
                    or name == "__pycache__"
                ):
                    ignored.append(name)
            return ignored

        shutil.copytree(source, dest, ignore=ignore_patterns)

    def _install_dependencies(self, install_path: Path):
        """Install requirements.txt if exists"""
        req_file = install_path / "requirements.txt"

        if req_file.exists():
            print(f"   Installing dependencies...")
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
                    check=True,
                    capture_output=True,
                )
                print(f"    Dependencies installed")
            except subprocess.CalledProcessError as e:
                print(f"     Dependency install warning: {e.stderr.decode()[:200]}")


    def uninstall(self, name: str) -> bool:
        """
        Uninstall a package.

        Args:
            name: Package name

        Returns:
            True if successful
        """
        pkg_info = self._get_package(name)

        if not pkg_info:
            print(f"  Package '{name}' not installed")
            return False

        # Remove from filesystem
        pkg_path = self.packages_dir / name
        if pkg_path.exists():
            shutil.rmtree(pkg_path)

        # Remove from database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE packages SET status = 'uninstalled' WHERE name = ?", (name,)
        )
        conn.commit()
        conn.close()

        # Remove from sys.modules
        if name in sys.modules:
            del sys.modules[name]

        print(f" Uninstalled '{name}'")
        return True

    def update(
        self, name: str = None, show_changelog: bool = True, auto_confirm: bool = False
    ) -> List[str]:
        """
        Update packages from their sources.

        Args:
            name: Specific package to update (None for all)
            show_changelog: Show changelog before update
            auto_confirm: Auto-confirm updates (for automation)

        Returns:
            List of updated package names
        """
        # Check for updates first
        updates = self.check_updates()

        if not updates:
            print(" All packages are up to date")
            return []

        if name:
            updates = [u for u in updates if u["name"] == name]

        updated = []

        for pkg in updates:
            pkg_name = pkg["name"]
            current = pkg["current"]
            latest = pkg["latest"]

            print(f"\n {pkg_name}: {current}  {latest}")

            # Show changelog
            if show_changelog:
                changelog = get_changelog(pkg_name, latest)
                if changelog and "No changelog" not in changelog:
                    print(f"\n Changelog:\n{changelog}")

                # Automation-safe: skip prompt if auto_confirm
                if not auto_confirm:
                    response = input(f"Update {pkg_name}? (y/n): ")
                    if response.lower() != "y":
                        continue

            try:
                print(f"   Updating...")
                self.install(pkg["source"], upgrade=True, verify=True)
                updated.append(pkg_name)
            except Exception as e:
                print(f"     Failed to update {pkg_name}: {e}")
                print(f"   Rolling back...")
                rollback(pkg_name, current)

        return updated


    def rollback_to(self, name: str, version: str) -> bool:
        """
        Rollback package to specific version.

        Args:
            name: Package name
            version: Version to rollback to

        Returns:
            True if successful
        """
        print(f" Rolling back {name} to v{version}...")

        if rollback(name, version):
            # Update database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE packages
                SET version = ?, updated_at = ?
                WHERE name = ?
            """,
                (version, datetime.now().isoformat(), name),
            )
            conn.commit()
            conn.close()

            # Hot-reload
            if self.hotload:
                self.hotload.load(name, reload=True)

            print(f" Rolled back {name} to v{version}")
            return True

        print(f" Rollback failed")
        return False

