"""ZolaPress Core - Site generation and management utilities."""

import os
import subprocess
import json
import toml
from pathlib import Path
from typing import Dict, Any, Optional, List
import shutil


class ZolaPressBuilder:
    """ZolaPress site builder and manager."""

    def __init__(self, site_dir: str):
        """Initialize ZolaPress builder.

        Args:
            site_dir: Path to the ZolaPress site directory
        """
        self.site_dir = Path(site_dir).resolve()
        if not self.site_dir.exists():
            raise ValueError(f"Site directory does not exist: {site_dir}")
        if not (self.site_dir / "config.toml").exists():
            raise ValueError(
                f"Not a valid ZolaPress site (missing config.toml): {site_dir}"
            )

    def build(
        self, output_dir: Optional[str] = None, base_url: Optional[str] = None
    ) -> bool:
        """Build the ZolaPress site.

        Args:
            output_dir: Custom output directory (defaults to site_dir/public)
            base_url: Base URL for the site (overrides config.toml)

        Returns:
            True if build successful, False otherwise
        """
        cmd = ["zola", "build"]

        if output_dir:
            cmd.extend(["--output-dir", output_dir])

        if base_url:
            cmd.extend(["--base-url", base_url])

        try:
            result = subprocess.run(
                cmd, cwd=self.site_dir, capture_output=True, text=True, check=True
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"Build failed: {e.stderr}")
            return False
        except FileNotFoundError:
            print("Error: zola command not found. Please install ZolaPress.")
            return False

    def serve(
        self, port: int = 1111, host: str = "127.0.0.1", build_first: bool = True
    ) -> bool:
        """Serve the ZolaPress site locally.

        Args:
            port: Port to serve on
            host: Host to bind to
            build_first: Whether to build before serving

        Returns:
            True if serve started successfully, False otherwise
        """
        if build_first:
            if not self.build():
                return False

        cmd = ["zola", "serve", "--port", str(port), "--host", host]

        try:
            # This will run until interrupted
            subprocess.run(cmd, cwd=self.site_dir, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Serve failed: {e.stderr}")
            return False
        except FileNotFoundError:
            print("Error: zola command not found. Please install ZolaPress.")
            return False
        except KeyboardInterrupt:
            print("\nServing stopped.")
            return True

    def check(self) -> bool:
        """Check the site for errors.

        Returns:
            True if check passes, False otherwise
        """
        try:
            result = subprocess.run(
                ["zola", "check"],
                cwd=self.site_dir,
                capture_output=True,
                text=True,
                check=True,
            )
            print("Site check passed!")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Site check failed: {e.stderr}")
            return False
        except FileNotFoundError:
            print("Error: zola command not found. Please install ZolaPress.")
            return False

    def init(self, theme: Optional[str] = None) -> bool:
        """Initialize a new ZolaPress site.

        Args:
            theme: Optional theme to initialize with

        Returns:
            True if initialization successful, False otherwise
        """
        cmd = ["zola", "init"]

        if theme:
            cmd.extend(["--theme", theme])

        try:
            # Note: zola init is interactive, so we'll just run the basic command
            # For full automation, we'd need to handle the prompts
            result = subprocess.run(
                cmd,
                cwd=self.site_dir.parent,
                capture_output=True,
                text=True,
                check=True,
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"Init failed: {e.stderr}")
            return False
        except FileNotFoundError:
            print("Error: zola command not found. Please install ZolaPress.")
            return False

    def get_config(self) -> Dict[str, Any]:
        """Get the site configuration.

        Returns:
            Dictionary containing site configuration
        """
        config_path = self.site_dir / "config.toml"
        with open(config_path, "r", encoding="utf-8") as f:
            return toml.load(f)

    def update_config(self, updates: Dict[str, Any]) -> bool:
        """Update the site configuration.

        Args:
            updates: Dictionary of configuration updates

        Returns:
            True if update successful, False otherwise
        """
        try:
            config = self.get_config()

            # Deep update the config
            def deep_update(d, u):
                for k, v in u.items():
                    if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                        deep_update(d[k], v)
                    else:
                        d[k] = v

            deep_update(config, updates)

            config_path = self.site_dir / "config.toml"
            with open(config_path, "w", encoding="utf-8") as f:
                toml.dump(config, f)

            return True
        except Exception as e:
            print(f"Failed to update config: {e}")
            return False

    def list_content(self) -> List[Dict[str, Any]]:
        """List all content files in the site.

        Returns:
            List of content file information
        """
        content_dir = self.site_dir / "content"
        if not content_dir.exists():
            return []

        content_files = []
        for md_file in content_dir.rglob("*.md"):
            rel_path = md_file.relative_to(content_dir)
            content_files.append(
                {
                    "path": str(rel_path),
                    "full_path": str(md_file),
                    "name": md_file.stem,
                    "modified": md_file.stat().st_mtime,
                }
            )

        return sorted(content_files, key=lambda x: x["path"])

    def create_content(
        self,
        path: str,
        front_matter: Optional[Dict[str, Any]] = None,
        content: str = "",
    ) -> bool:
        """Create a new content file.

        Args:
            path: Relative path from content directory (e.g., "blog/post.md")
            front_matter: Optional front matter dictionary
            content: Optional content string

        Returns:
            True if creation successful, False otherwise
        """
        try:
            content_dir = self.site_dir / "content"
            file_path = content_dir / path

            # Create parent directories if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Prepare front matter
            fm_content = ""
            if front_matter:
                fm_content = "---\n"
                fm_content += toml.dumps(front_matter)
                fm_content += "---\n\n"

            # Write file
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(fm_content + content)

            return True
        except Exception as e:
            print(f"Failed to create content: {e}")
            return False


# Convenience functions
def build_site(
    site_dir: str, output_dir: Optional[str] = None, base_url: Optional[str] = None
) -> bool:
    """Build a ZolaPress site (convenience function).

    Args:
        site_dir: Path to the ZolaPress site directory
        output_dir: Custom output directory
        base_url: Base URL for the site

    Returns:
        True if build successful, False otherwise
    """
    builder = ZolaPressBuilder(site_dir)
    return builder.build(output_dir, base_url)


def serve_site(
    site_dir: str, port: int = 1111, host: str = "127.0.0.1", build_first: bool = True
) -> bool:
    """Serve a ZolaPress site locally (convenience function).

    Args:
        site_dir: Path to the ZolaPress site directory
        port: Port to serve on
        host: Host to bind to
        build_first: Whether to build before serving

    Returns:
        True if serve started successfully, False otherwise
    """
    builder = ZolaPressBuilder(site_dir)
    return builder.serve(port, host, build_first)


def check_site(site_dir: str) -> bool:
    """Check a ZolaPress site for errors (convenience function).

    Args:
        site_dir: Path to the ZolaPress site directory

    Returns:
        True if check passes, False otherwise
    """
    builder = ZolaPressBuilder(site_dir)
    return builder.check()


def init_site(site_dir: str, theme: Optional[str] = None) -> bool:
    """Initialize a new ZolaPress site (convenience function).

    Args:
        site_dir: Path where to create the site
        theme: Optional theme to initialize with

    Returns:
        True if initialization successful, False otherwise
    """
    # Create directory if it doesn't exist
    Path(site_dir).mkdir(parents=True, exist_ok=True)
    builder = ZolaPressBuilder(site_dir)
    return builder.init(theme)
