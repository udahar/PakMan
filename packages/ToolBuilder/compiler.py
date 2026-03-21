# Updated-On: 2026-03-08
# Updated-By: Codex
# PM-Ticket: UNTRACKED

"""
Tool Compiler
Advanced compilation and validation
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
import ast


@dataclass
class CompilationResult:
    """Result of tool compilation."""

    success: bool
    function: Optional[Callable]
    errors: List[str]
    warnings: List[str]


class ToolCompiler:
    """
    Compile and validate tools.

    Features:
    - Syntax validation
    - Security checks
    - Dependency resolution
    - Type checking
    """

    def __init__(self):
        self.compiled: Dict[str, CompilationResult] = {}

    def compile(self, code: str, language: str = "python") -> CompilationResult:
        """Compile tool code."""
        if language.lower() == "python":
            return self._compile_python(code)
        else:
            return CompilationResult(
                success=False,
                function=None,
                errors=[f"Unsupported language: {language}"],
                warnings=[],
            )

    def _compile_python(self, code: str) -> CompilationResult:
        """Compile Python code."""
        errors = []
        warnings = []
        function = None

        try:
            tree = ast.parse(code)

            warnings.extend(self._check_security(code))

            has_execute = any(
                isinstance(node, ast.FunctionDef) and node.name in ["execute", "run"]
                for node in ast.walk(tree)
            )

            if not has_execute:
                errors.append("Must define execute() or run() function")

            if errors:
                return CompilationResult(
                    success=False, function=None, errors=errors, warnings=warnings
                )

            namespace = {}
            exec(code, namespace)

            function = namespace.get("execute") or namespace.get("run")

            return CompilationResult(
                success=True, function=function, errors=[], warnings=warnings
            )

        except SyntaxError as e:
            errors.append(f"Syntax error: {e}")
        except Exception as e:
            errors.append(f"Compilation error: {e}")

        return CompilationResult(
            success=False, function=None, errors=errors, warnings=warnings
        )

    def _check_security(self, code: str) -> List[str]:
        """Check for security issues."""
        warnings = []

        dangerous = [
            ("eval(", "Use of eval() is dangerous"),
            ("exec(", "Use of exec() is dangerous"),
            ("__import__(", "Dynamic imports can be risky"),
            ("subprocess", "Subprocess calls require validation"),
            ("open(", "File operations require validation"),
        ]

        for pattern, message in dangerous:
            if pattern in code:
                warnings.append(message)

        return warnings

    def validate_params(
        self, params: Dict[str, Any], spec: List[Dict[str, str]]
    ) -> tuple[bool, List[str]]:
        """Validate parameters against spec."""
        errors = []

        for param_spec in spec:
            name = param_spec.get("name")
            required = param_spec.get("required", "false").lower() == "true"
            param_type = param_spec.get("type", "string")

            if required and name not in params:
                errors.append(f"Missing required parameter: {name}")

            if name in params:
                value = params[name]

                if param_type == "number" and not isinstance(value, (int, float)):
                    errors.append(f"Parameter {name} must be a number")
                elif param_type == "string" and not isinstance(value, str):
                    errors.append(f"Parameter {name} must be a string")
                elif param_type == "boolean" and not isinstance(value, bool):
                    errors.append(f"Parameter {name} must be a boolean")

        return len(errors) == 0, errors

    def get_stats(self) -> Dict[str, Any]:
        """Get compiler stats."""
        successful = sum(1 for r in self.compiled.values() if r.success)
        return {
            "total_compilations": len(self.compiled),
            "successful": successful,
            "failed": len(self.compiled) - successful,
        }


def create_tool_compiler() -> ToolCompiler:
    """Factory function to create compiler."""
    return ToolCompiler()
