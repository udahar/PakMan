"""WikiPak Core - Build a unified wiki from PakMan packages."""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional


class WikiPakBuilder:
    """WikiPak site builder and manager."""

    def __init__(self, wiki_dir: str):
        """Initialize WikiPak builder.

        Args:
            wiki_dir: Path to the WikiPak wiki directory (where content will be built)
        """
        self.wiki_dir = Path(wiki_dir).resolve()
        self.wiki_dir.mkdir(parents=True, exist_ok=True)
        self.content_dir = self.wiki_dir / "content"
        self.content_dir.mkdir(parents=True, exist_ok=True)

    def collect_package_docs(self, pakman_packages_dir: str) -> None:
        """Collect documentation from all PakMan packages and copy to wiki content directory.

        Args:
            pakman_packages_dir: Path to the PakMan packages directory
        """
        pakman_path = Path(pakman_packages_dir)
        if not pakman_path.exists():
            raise ValueError(
                f"PakMan packages directory does not exist: {pakman_packages_dir}"
            )

        # Clear existing content in wiki content directory (except maybe _index.md?)
        for item in self.content_dir.iterdir():
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)

        # Iterate over each package directory
        for package_dir in pakman_path.iterdir():
            if not package_dir.is_dir():
                continue
            package_name = package_dir.name
            # Skip the WikiPak package itself to avoid recursion
            if package_name == "WikiPak":
                continue
            # Look for content directory in the package
            pkg_content_dir = package_dir / "content"
            if pkg_content_dir.exists() and pkg_content_dir.is_dir():
                # Combine all markdown files in the package's content into one file.
                combined_content = ""
                # Read all markdown files in the package's content directory
                for md_file in pkg_content_dir.glob("*.md"):
                    try:
                        with open(md_file, "r", encoding="utf-8") as f:
                            content = f.read()
                        # If the file has frontmatter, we can extract it and merge? For simplicity, we just append.
                        combined_content += f"\n\n## {md_file.stem}\n\n{content}"
                    except Exception as e:
                        print(f"Warning: Could not read {md_file}: {e}")
                # If there's no content, we can still create a placeholder.
                if not combined_content.strip():
                    combined_content = (
                        f"# {package_name}\n\nNo documentation available."
                    )
                else:
                    combined_content = f"# {package_name}\n\n" + combined_content

                # Write to wiki content directory as package_name.md with frontmatter
                wiki_md_file = self.content_dir / f"{package_name}.md"
                frontmatter_content = f"---\ntitle: {package_name}\npackage: {package_name}\n---\n{combined_content}"
                with open(wiki_md_file, "w", encoding="utf-8") as f:
                    f.write(frontmatter_content)
            else:
                # If the package has no content directory, create a placeholder
                wiki_md_file = self.content_dir / f"{package_name}.md"
                frontmatter_content = f"---\ntitle: {package_name}\npackage: {package_name}\n---\n# {package_name}\n\nNo content directory found."
                with open(wiki_md_file, "w", encoding="utf-8") as f:
                    f.write(frontmatter_content)

    def build(
        self, output_dir: Optional[str] = None, base_url: Optional[str] = None
    ) -> bool:
        """Build the WikiPak site using ZolaPress CLI.

        Args:
            output_dir: Custom output directory (defaults to wiki_dir/public)
            base_url: Base URL for the site (overrides config.toml)

        Returns:
            True if build successful, False otherwise
        """
        # We assume that the wiki_dir is a valid Zola site (with config.toml, etc.)
        # For now, we just copy the content and let the user run zola build via WikiPak CLI or ZolaPress.
        # We (re)write a basic config.toml each time to ensure correct format.
        config_path = self.wiki_dir / "config.toml"
        default_config = f"""base_url = "{base_url or "http://127.0.0.1:1111"}"
title = "PakMan Wiki"
description = "Unified documentation for all PakMan packages"

[taxonomies]
tag = [ "tags" ]

[extra]
author = "Richard"
version = "0.1.0"
"""
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(default_config)

        # Now, we can use ZolaPress to build the site via subprocess.
        cmd = ["zolapress", "build"]
        if output_dir:
            cmd.extend(["--output-dir", output_dir])
        if base_url:
            cmd.extend(["--base-url", base_url])
        cmd.append(str(self.wiki_dir))
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            return True
        except Exception as e:
            print(f"ZolaPress build failed: {e}")
            return False

    def serve(
        self, port: int = 1111, host: str = "127.0.0.1", build_first: bool = True
    ) -> bool:
        """Serve the WikiPak site locally using ZolaPress.

        Args:
            port: Port to serve on
            host: Host to bind to
            build_first: Whether to build before serving

        Returns:
            True if serve started successfully, False otherwise
        """
        # Build first if requested
        if build_first:
            if not self.build():
                return False
        # Serve using zolapress
        cmd = ["zolapress", "serve", "--port", str(port), "--host", host]
        try:
            # This will run until interrupted (Ctrl+C)
            subprocess.run(cmd, cwd=str(self.wiki_dir), check=True)
            return True
        except Exception as e:
            print(f"ZolaPress serve failed: {e}")
            return False
        except KeyboardInterrupt:
            print("\nServe stopped by user.")
            return True


# Convenience functions
def build_wiki(
    wiki_dir: str,
    pakman_packages_dir: str,
    output_dir: Optional[str] = None,
    base_url: Optional[str] = None,
) -> bool:
    """Build a WikiPak wiki (convenience function).

    Args:
        wiki_dir: Path to the WikiPak wiki directory
        pakman_packages_dir: Path to the PakMan packages directory
        output_dir: Custom output directory
        base_url: Base URL for the site

    Returns:
        True if build successful, False otherwise
    """
    builder = WikiPakBuilder(wiki_dir)
    builder.collect_package_docs(pakman_packages_dir)
    return builder.build(output_dir, base_url)


def serve_wiki(
    wiki_dir: str,
    pakman_packages_dir: str,
    port: int = 1111,
    host: str = "127.0.0.1",
    build_first: bool = True,
) -> bool:
    """Serve a WikiPak wiki locally (convenience function).

    Args:
        wiki_dir: Path to the WikiPak wiki directory
        pakman_packages_dir: Path to the PakMan packages directory
        port: Port to serve on
        host: Host to bind to
        build_first: Whether to build before serving

    Returns:
        True if serve started successfully, False otherwise
    """
    builder = WikiPakBuilder(wiki_dir)
    builder.collect_package_docs(pakman_packages_dir)
    return builder.serve(port, host, build_first)
