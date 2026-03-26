"""
AutoDocGen
AI-powered self-maintaining documentation generator.

Quick start:
    from AutoDocGen import AutoDocGen

    doc = AutoDocGen()

    # Document a single file
    doc.document_file("mypackage/core.py", readme="mypackage/README.md")

    # Document a whole package
    doc.document_package("mypackage/")

    # With LLM enrichment for undocumented functions
    from AutoDocGen import AutoDocGen
    doc = AutoDocGen(llm_callable=my_llm)
    doc.document_package("mypackage/")
"""
from pathlib import Path
from typing import Callable, List, Optional

from .extractor import extract, ModuleDoc
from .renderer import render_module
from .patcher import patch_readme


class AutoDocGen:
    """
    Orchestrator: extract → render → patch README.

    Args:
        llm_callable: Optional fn(prompt) -> str added descriptions
                      for undocumented functions.
    """

    def __init__(self, llm_callable: Optional[Callable] = None):
        self.llm = llm_callable

    def document_file(
        self,
        filepath: str,
        readme: Optional[str] = None,
    ) -> str:
        """
        Document a single Python file and optionally patch a README.

        Returns:
            Rendered Markdown string.
        """
        module_doc = extract(filepath)
        md = render_module(module_doc, llm_callable=self.llm)

        if readme:
            patched = patch_readme(readme, md)
            status = "patched" if patched else "unchanged"
            print(f"[AutoDocGen] {Path(filepath).name} → {readme} ({status})")

        return md

    def document_package(
        self,
        package_dir: str,
        readme: Optional[str] = None,
        glob: str = "**/*.py",
    ) -> List[str]:
        """
        Document all Python files in a package directory.

        Returns:
            List of rendered Markdown strings (one per file).
        """
        base = Path(package_dir)
        files = sorted(base.glob(glob))
        results = []

        combined_md = f"# API Reference — `{base.name}`\n\n"

        for py_file in files:
            if py_file.name.startswith("_"):
                continue
            module_doc = extract(str(py_file))
            md = render_module(module_doc, llm_callable=self.llm)
            combined_md += md + "\n---\n\n"
            results.append(md)
            print(f"[AutoDocGen] Documented: {py_file.name}")

        target_readme = readme or str(base / "README.md")
        patch_readme(target_readme, combined_md)
        print(f"[AutoDocGen] Patched README: {target_readme}")

        return results


__version__ = "0.1.0"
__all__ = ["AutoDocGen", "extract", "render_module", "patch_readme"]
