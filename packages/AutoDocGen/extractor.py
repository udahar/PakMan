"""
AutoDocGen - extractor.py
AST-based code analyzer. Extracts functions, classes, types, and docstrings
from Python source files without executing any code.
"""
import ast
import inspect
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class ParamInfo:
    name: str
    annotation: str = ""
    default: str = ""


@dataclass
class FunctionDoc:
    name: str
    params: List[ParamInfo] = field(default_factory=list)
    returns: str = ""
    docstring: str = ""
    is_async: bool = False
    is_method: bool = False
    decorators: List[str] = field(default_factory=list)
    lineno: int = 0


@dataclass
class ClassDoc:
    name: str
    bases: List[str] = field(default_factory=list)
    docstring: str = ""
    methods: List[FunctionDoc] = field(default_factory=list)
    lineno: int = 0


@dataclass
class ModuleDoc:
    filepath: str
    module_docstring: str = ""
    functions: List[FunctionDoc] = field(default_factory=list)
    classes: List[ClassDoc] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)


def extract(filepath: str) -> ModuleDoc:
    """
    Parse a Python file and extract all documentation-relevant information.

    Args:
        filepath: Absolute or relative path to the .py file.

    Returns:
        ModuleDoc with all functions, classes, docstrings, and type hints.
    """
    source = Path(filepath).read_text(encoding="utf-8", errors="replace")
    try:
        tree = ast.parse(source, filename=filepath)
    except SyntaxError as e:
        return ModuleDoc(filepath=filepath, module_docstring=f"Parse error: {e}")

    doc = ModuleDoc(filepath=filepath)
    doc.module_docstring = ast.get_docstring(tree) or ""

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            doc.imports.append(ast.unparse(node) if hasattr(ast, "unparse") else "")

    for node in tree.body:
        if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            doc.functions.append(_parse_function(node))
        elif isinstance(node, ast.ClassDef):
            doc.classes.append(_parse_class(node))

    return doc


def _parse_function(node) -> FunctionDoc:
    params = []
    args = node.args
    all_args = args.args + getattr(args, "posonlyargs", []) + getattr(args, "kwonlyargs", [])
    defaults = [None] * (len(all_args) - len(args.defaults)) + list(args.defaults)

    for arg, default in zip(all_args, defaults):
        ann = ast.unparse(arg.annotation) if (hasattr(ast, "unparse") and arg.annotation) else ""
        dflt = ast.unparse(default) if (hasattr(ast, "unparse") and default) else ""
        params.append(ParamInfo(name=arg.arg, annotation=ann, default=dflt))

    returns = ""
    if hasattr(ast, "unparse") and node.returns:
        returns = ast.unparse(node.returns)

    return FunctionDoc(
        name=node.name,
        params=params,
        returns=returns,
        docstring=ast.get_docstring(node) or "",
        is_async=isinstance(node, ast.AsyncFunctionDef),
        decorators=[ast.unparse(d) if hasattr(ast, "unparse") else "" for d in node.decorator_list],
        lineno=node.lineno,
    )


def _parse_class(node) -> ClassDoc:
    bases = [ast.unparse(b) if hasattr(ast, "unparse") else "" for b in node.bases]
    methods = []
    for item in node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            m = _parse_function(item)
            m.is_method = True
            methods.append(m)
    return ClassDoc(
        name=node.name,
        bases=bases,
        docstring=ast.get_docstring(node) or "",
        methods=methods,
        lineno=node.lineno,
    )
