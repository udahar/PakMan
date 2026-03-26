"""
AutoDocGen - patcher.py
Surgically patches an existing README.md by replacing the API section
without overwriting narrative content.
"""
import re
from pathlib import Path
from typing import Optional


API_SECTION_HEADER = "## API Reference"
_START_MARKER = "<!-- autodocgen:start -->"
_END_MARKER = "<!-- autodocgen:end -->"


def patch_readme(
    readme_path: str,
    new_api_section: str,
    create_if_missing: bool = True,
) -> bool:
    """
    Surgically replace the AutoDocGen section in a README.

    If markers are present (<!-- autodocgen:start/end -->), content between them
    is replaced. Otherwise the section is appended.

    Args:
        readme_path:       Path to the README.md file.
        new_api_section:   Rendered Markdown to inject.
        create_if_missing: Create the README if it doesn't exist.

    Returns:
        True if the file was modified.
    """
    path = Path(readme_path)

    if not path.exists():
        if create_if_missing:
            path.write_text(
                f"{_START_MARKER}\n{new_api_section}\n{_END_MARKER}\n",
                encoding="utf-8"
            )
            return True
        return False

    content = path.read_text(encoding="utf-8")

    if _START_MARKER in content and _END_MARKER in content:
        # Replace between markers
        pattern = re.compile(
            re.escape(_START_MARKER) + r".*?" + re.escape(_END_MARKER),
            re.DOTALL
        )
        updated = pattern.sub(
            f"{_START_MARKER}\n{new_api_section}\n{_END_MARKER}",
            content
        )
    else:
        # Append a new section
        updated = content.rstrip() + f"\n\n{_START_MARKER}\n{new_api_section}\n{_END_MARKER}\n"

    if updated == content:
        return False

    path.write_text(updated, encoding="utf-8")
    return True
