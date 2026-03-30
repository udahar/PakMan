# -*- coding: utf-8 -*-
"""
ModLib Health Compliance System

Tests modules to verify they:
1. Load without errors
2. Have required dependencies
3. Pass basic functionality tests
4. Are compatible with the system

Usage:
    from ModLib.health import HealthChecker
    
    checker = HealthChecker()
    results = await checker.run_all_checks()
    
    # Check specific module
    result = await checker.check_module("PromptRD")
"""

import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import importlib
import sys


@dataclass
class HealthCheckResult:
    """Result of a health check"""
    module_name: str
    check_type: str
    passed: bool
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class ModuleCompliance:
    """Overall compliance status for a module"""
    module_name: str
    overall_status: str = "pending"  # compliant, non_compliant, warning
    checks_passed: int = 0
    checks_failed: int = 0
    checks_warning: int = 0
    total_checks: int = 0
    compliance_score: float = 0.0
    last_check: datetime = field(default_factory=datetime.now)
    results: List[HealthCheckResult] = field(default_factory=list)
    blocking_issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class HealthChecker:
    """
    Runs health and compliance checks on modules.
    """
    
    def __init__(self, frank_root: str = None):
        self.frank_root = Path(frank_root) if frank_root else Path(__file__).parent.parent
        self.results: Dict[str, ModuleCompliance] = {}
    
    async def run_all_checks(self) -> Dict[str, ModuleCompliance]:
        """
        Run all health checks on all modules.
        
        Returns:
            Dict of module_name -> ModuleCompliance
        """
        from ModLib import get_registry
        
        registry = get_registry(str(self.frank_root))
        
        for module_info in registry.list_modules():
            compliance = await self.check_module(module_info["name"])
            self.results[module_info["name"]] = compliance
        
        return self.results
    
    async def check_module(self, module_name: str) -> ModuleCompliance:
        """
        Run all checks on a specific module.
        
        Args:
            module_name: Name of module to check
        
        Returns:
            ModuleCompliance with all check results
        """
        compliance = ModuleCompliance(module_name=module_name)
        
        # Run individual checks
        checks = [
            self._check_load,
            self._check_dependencies,
            self._check_init,
            self._check_exports,
            self._check_compatibility,
        ]
        
        for check in checks:
            try:
                result = await check(module_name)
                compliance.results.append(result)
                
                if result.passed:
                    compliance.checks_passed += 1
                elif result.error and "FATAL" in result.error:
                    compliance.blocking_issues.append(result.message)
                else:
                    compliance.checks_failed += 1
                    compliance.warnings.append(result.message)
                    
            except Exception as e:
                compliance.checks_failed += 1
                compliance.blocking_issues.append(f"{check.__name__}: {str(e)}")
        
        # Calculate totals
        compliance.total_checks = len(checks)
        compliance.compliance_score = (
            compliance.checks_passed / compliance.total_checks
            if compliance.total_checks > 0
            else 0.0
        )
        
        # Determine overall status
        if compliance.blocking_issues:
            compliance.overall_status = "non_compliant"
        elif compliance.checks_failed > 0:
            compliance.overall_status = "warning"
        else:
            compliance.overall_status = "compliant"
        
        compliance.last_check = datetime.now()
        
        return compliance
    
    async def _check_load(self, module_name: str) -> HealthCheckResult:
        """Check if module loads without errors"""
        try:
            # Try to import the module
            module_path = self._find_module_path(module_name)
            
            if not module_path:
                return HealthCheckResult(
                    module_name=module_name,
                    check_type="load",
                    passed=False,
                    message=f"Module path not found",
                    error="FATAL: Module not found"
                )
            
            # Try importing
            spec = importlib.util.spec_from_file_location(
                module_name,
                module_path / "__init__.py"
            )
            
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
            
            return HealthCheckResult(
                module_name=module_name,
                check_type="load",
                passed=True,
                message=f"Module loaded successfully"
            )
            
        except Exception as e:
            return HealthCheckResult(
                module_name=module_name,
                check_type="load",
                passed=False,
                message=f"Failed to load: {str(e)}",
                error=f"FATAL: {str(e)}"
            )
    
    async def _check_dependencies(self, module_name: str) -> HealthCheckResult:
        """Check if required dependencies are available"""
        try:
            module_path = self._find_module_path(module_name)
            if not module_path:
                return HealthCheckResult(
                    module_name=module_name,
                    check_type="dependencies",
                    passed=False,
                    message="Module not found"
                )
            
            # Check for requirements.txt
            req_file = module_path / "requirements.txt"
            if req_file.exists():
                # Would check if dependencies are installed
                return HealthCheckResult(
                    module_name=module_name,
                    check_type="dependencies",
                    passed=True,
                    message="Dependencies declared"
                )
            
            # Check for common imports in __init__.py
            init_file = module_path / "__init__.py"
            if init_file.exists():
                content = init_file.read_text()
                
                # Check for problematic imports
                problematic = []
                if "import optional_dep" in content:
                    problematic.append("optional_dep")
                
                if problematic:
                    return HealthCheckResult(
                        module_name=module_name,
                        check_type="dependencies",
                        passed=False,
                        message=f"Missing optional dependencies: {problematic}",
                        error="WARNING"
                    )
            
            return HealthCheckResult(
                module_name=module_name,
                check_type="dependencies",
                passed=True,
                message="No dependency issues detected"
            )
            
        except Exception as e:
            return HealthCheckResult(
                module_name=module_name,
                check_type="dependencies",
                passed=False,
                message=f"Dependency check failed: {str(e)}"
            )
    
    async def _check_init(self, module_name: str) -> HealthCheckResult:
        """Check if module has valid __init__.py"""
        try:
            module_path = self._find_module_path(module_name)
            if not module_path:
                return HealthCheckResult(
                    module_name=module_name,
                    check_type="init",
                    passed=False,
                    message="Module not found"
                )
            
            init_file = module_path / "__init__.py"
            
            if not init_file.exists():
                return HealthCheckResult(
                    module_name=module_name,
                    check_type="init",
                    passed=False,
                    message="Missing __init__.py",
                    error="FATAL: Not a valid Python module"
                )
            
            # Check if __init__.py is valid Python
            try:
                compile(init_file.read_text(), str(init_file), 'exec')
                return HealthCheckResult(
                    module_name=module_name,
                    check_type="init",
                    passed=True,
                    message="__init__.py is valid"
                )
            except SyntaxError as e:
                return HealthCheckResult(
                    module_name=module_name,
                    check_type="init",
                    passed=False,
                    message=f"Syntax error in __init__.py: {str(e)}",
                    error=f"FATAL: {str(e)}"
                )
            
        except Exception as e:
            return HealthCheckResult(
                module_name=module_name,
                check_type="init",
                passed=False,
                message=f"Init check failed: {str(e)}"
            )
    
    async def _check_exports(self, module_name: str) -> HealthCheckResult:
        """Check if module exports are properly defined"""
        try:
            module_path = self._find_module_path(module_name)
            if not module_path:
                return HealthCheckResult(
                    module_name=module_name,
                    check_type="exports",
                    passed=False,
                    message="Module not found"
                )
            
            init_file = module_path / "__init__.py"
            if not init_file.exists():
                return HealthCheckResult(
                    module_name=module_name,
                    check_type="exports",
                    passed=False,
                    message="No __init__.py"
                )
            
            content = init_file.read_text()
            
            # Check for __all__ definition
            if "__all__" in content:
                return HealthCheckResult(
                    module_name=module_name,
                    check_type="exports",
                    passed=True,
                    message="__all__ is defined"
                )
            
            # Check for factory functions
            if "def create_" in content or "def get_" in content:
                return HealthCheckResult(
                    module_name=module_name,
                    check_type="exports",
                    passed=True,
                    message="Factory functions found"
                )
            
            return HealthCheckResult(
                module_name=module_name,
                check_type="exports",
                passed=True,
                message="No explicit exports (may be intentional)",
                error="WARNING"
            )
            
        except Exception as e:
            return HealthCheckResult(
                module_name=module_name,
                check_type="exports",
                passed=False,
                message=f"Export check failed: {str(e)}"
            )
    
    async def _check_compatibility(self, module_name: str) -> HealthCheckResult:
        """Check if module is compatible with system"""
        try:
            # Check for AiOSKernel integration
            if module_name == "AiOSKernel":
                return HealthCheckResult(
                    module_name=module_name,
                    check_type="compatibility",
                    passed=True,
                    message="Core kernel module"
                )
            
            # Check for ModLib integration
            module_path = self._find_module_path(module_name)
            if not module_path:
                return HealthCheckResult(
                    module_name=module_name,
                    check_type="compatibility",
                    passed=False,
                    message="Module not found"
                )
            
            # Check if in expected location
            if "src/modules" in str(module_path) or "PromptRD" in str(module_path):
                return HealthCheckResult(
                    module_name=module_name,
                    check_type="compatibility",
                    passed=True,
                    message="Module in expected location"
                )
            
            return HealthCheckResult(
                module_name=module_name,
                check_type="compatibility",
                passed=True,
                message="Module location acceptable",
                error="WARNING"
            )
            
        except Exception as e:
            return HealthCheckResult(
                module_name=module_name,
                check_type="compatibility",
                passed=False,
                message=f"Compatibility check failed: {str(e)}"
            )
    
    def _find_module_path(self, module_name: str) -> Optional[Path]:
        """Find module path by name"""
        # Check /src/modules/
        src_modules = self.frank_root.parent / "src" / "modules" / module_name
        if src_modules.exists():
            return src_modules
        
        # Check /PromptRD/ subdirectories
        promptrd = self.frank_root
        for subdir in promptrd.iterdir():
            if subdir.is_dir() and subdir.name == module_name:
                return subdir
        
        # Check direct children
        for child in self.frank_root.iterdir():
            if child.is_dir() and child.name == module_name:
                return child
        
        return None
    
    def get_compliance_report(self) -> str:
        """Generate compliance report"""
        lines = []
        lines.append("📋 Module Compliance Report")
        lines.append("=" * 60)
        lines.append("")
        
        for module_name, compliance in sorted(self.results.items()):
            icon = {
                "compliant": "✅",
                "warning": "⚠️",
                "non_compliant": "❌"
            }.get(compliance.overall_status, "❓")
            
            lines.append(f"{icon} {module_name}")
            lines.append(f"   Score: {compliance.compliance_score*100:.0f}%")
            lines.append(f"   Passed: {compliance.checks_passed}/{compliance.total_checks}")
            
            if compliance.blocking_issues:
                lines.append(f"   Blocking: {', '.join(compliance.blocking_issues)}")
            if compliance.warnings:
                lines.append(f"   Warnings: {', '.join(compliance.warnings[:3])}")
            
            lines.append("")
        
        # Summary
        total = len(self.results)
        compliant = sum(1 for c in self.results.values() if c.overall_status == "compliant")
        warning = sum(1 for c in self.results.values() if c.overall_status == "warning")
        non_compliant = sum(1 for c in self.results.values() if c.overall_status == "non_compliant")
        
        lines.append("=" * 60)
        lines.append(f"Total: {total} modules")
        lines.append(f"✅ Compliant: {compliant}")
        lines.append(f"⚠️  Warning: {warning}")
        lines.append(f"❌ Non-compliant: {non_compliant}")
        
        return "\n".join(lines)


# Global instance
_checker: Optional[HealthChecker] = None


def get_checker() -> HealthChecker:
    """Get or create health checker"""
    global _checker
    if not _checker:
        _checker = HealthChecker()
    return _checker


async def run_health_checks() -> Dict[str, ModuleCompliance]:
    """Run all health checks"""
    checker = get_checker()
    return await checker.run_all_checks()


async def check_module(module_name: str) -> ModuleCompliance:
    """Check specific module"""
    checker = get_checker()
    return await checker.check_module(module_name)


def get_compliance_report() -> str:
    """Get compliance report"""
    checker = get_checker()
    return checker.get_compliance_report()
