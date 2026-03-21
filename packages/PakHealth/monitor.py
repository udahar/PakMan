"""
Health Monitor - Core Monitoring System
"""

import importlib
import socket
from typing import Dict, List, Any, Optional
from datetime import datetime


class Monitor:
    """
    Monitor health of packages and services.

    Usage:
        monitor = Monitor()
        health = monitor.check_all()
        print(health)
    """

    DEFAULT_PORTS = {
        "postgres": 5432,
        "qdrant": 6333,
        "redis": 6379,
        "ollama": 11434,
    }

    PACKAGE_CHECKS = {
        "PkgMan": "PkgMan",
        "StockAI": "StockAI",
        "AiOSKernel": "AiOSKernel",
        "PromptRouter": "PromptRouter",
    }

    def __init__(self, pkg_root: str = None):
        self.pkg_root = pkg_root
        self.last_check: Optional[datetime] = None

    def check_all(self) -> Dict[str, Dict]:
        """Check all systems."""
        self.last_check = datetime.now()

        results = {
            "packages": self.check_packages(),
            "ports": self.check_ports(),
            "imports": self.check_imports(),
        }

        results["summary"] = self._summarize(results)

        return results

    def check_packages(self) -> Dict[str, Dict]:
        """Check if packages can be imported."""
        results = {}

        for pkg_name in self.PACKAGE_CHECKS:
            results[pkg_name] = self.check_import(pkg_name)

        return results

    def check_import(self, package_name: str) -> Dict[str, Any]:
        """Check if a package can be imported."""
        try:
            mod = importlib.import_module(package_name)
            return {
                "ok": True,
                "status": "online",
                "module": str(mod),
                "message": f"Successfully imported {package_name}",
            }
        except ImportError as e:
            return {
                "ok": False,
                "status": "offline",
                "error": str(e),
                "message": f"Failed to import {package_name}",
            }
        except Exception as e:
            return {
                "ok": False,
                "status": "error",
                "error": str(e),
                "message": f"Error importing {package_name}",
            }

    def check_ports(self, ports: Dict[str, int] = None) -> Dict[str, Dict]:
        """Check if services are running on ports."""
        ports_to_check = ports or self.DEFAULT_PORTS

        results = {}

        for service, port in ports_to_check.items():
            results[service] = self._check_port("localhost", port)

        return results

    def _check_port(self, host: str, port: int) -> Dict[str, Any]:
        """Check if a port is open."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)

        try:
            result = sock.connect_ex((host, port))
            sock.close()

            if result == 0:
                return {
                    "ok": True,
                    "status": "online",
                    "port": port,
                    "message": f"Port {port} is open",
                }
            else:
                return {
                    "ok": False,
                    "status": "offline",
                    "port": port,
                    "message": f"Port {port} is closed",
                }
        except Exception as e:
            return {
                "ok": False,
                "status": "error",
                "port": port,
                "error": str(e),
                "message": f"Error checking port {port}",
            }

    def check_imports(self) -> Dict[str, Dict]:
        """Check critical imports."""
        critical = [
            "yaml",
            "psycopg2",
            "sqlalchemy",
            "qdrant_client",
            "pandas",
            "numpy",
        ]

        results = {}

        for module in critical:
            results[module] = self._check_module_import(module)

        return results

    def _check_module_import(self, module_name: str) -> Dict[str, Any]:
        """Check if a module can be imported."""
        try:
            importlib.import_module(module_name)
            return {"ok": True, "status": "installed"}
        except ImportError:
            return {"ok": False, "status": "missing"}

    def check_venv(self) -> Dict[str, Any]:
        """Check virtual environment info."""
        import sys
        import os

        return {
            "python_version": sys.version,
            "python_executable": sys.executable,
            "path": sys.path[:3],
        }

    def _summarize(self, results: Dict) -> Dict:
        """Generate summary of all checks."""
        package_online = sum(1 for p in results["packages"].values() if p.get("ok"))
        package_total = len(results["packages"])

        ports_online = sum(1 for p in results["ports"].values() if p.get("ok"))
        ports_total = len(results["ports"])

        imports_ok = sum(1 for p in results["imports"].values() if p.get("ok"))
        imports_total = len(results["imports"])

        overall_ok = all(
            [
                package_online == package_total,
                ports_online > 0,
                imports_ok == imports_total,
            ]
        )

        return {
            "packages_online": f"{package_online}/{package_total}",
            "ports_online": f"{ports_online}/{ports_total}",
            "imports_ok": f"{imports_ok}/{imports_total}",
            "overall": "healthy" if overall_ok else "degraded",
            "checked_at": self.last_check.isoformat() if self.last_check else None,
        }

    def get_dashboard(self) -> Dict:
        """Get health dashboard data."""
        all_checks = self.check_all()

        return {
            "summary": all_checks["summary"],
            "details": {
                "packages": all_checks["packages"],
                "services": all_checks["ports"],
                "dependencies": all_checks["imports"],
            },
        }
