#!/usr/bin/env python3
"""Windows host bridge for Ollama restart and health actions."""

from __future__ import annotations

import json
import os
import socket
import subprocess
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


HOST = os.environ.get("OLLAMA_GUARD_HOST", "0.0.0.0")
PORT = int(os.environ.get("OLLAMA_GUARD_PORT", "8772"))
OLLAMA_EXE = os.environ.get(
    "OLLAMA_EXE",
    r"C:\Users\Richard\AppData\Local\Programs\Ollama\ollama.exe",
)
OLLAMA_PORTS = [11434, 11436, 11437]
OLLAMA_MANAGER = str(
    Path(__file__).resolve().parents[1] / "OllamaOps" / "ollama_manager.ps1"
)
LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_FILE = LOG_DIR / "ollama_guard_bridge.log"
_LAST_RESTART_TS = 0.0


def _log(message: str) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}"
    print(line, flush=True)
    try:
        with LOG_FILE.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
    except Exception:
        pass


def _port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def _list_ollama_pids() -> list[int]:
    try:
        out = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq ollama.exe", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except Exception:
        return []
    pids: list[int] = []
    for line in (out.stdout or "").splitlines():
        if not line or "No tasks are running" in line:
            continue
        parts = [part.strip('"') for part in line.split('","')]
        if len(parts) < 2:
            continue
        try:
            pids.append(int(parts[1]))
        except Exception:
            continue
    return pids


def _run_manager(action: str) -> dict[str, object]:
    if not Path(OLLAMA_MANAGER).exists():
        return {"ok": False, "error": f"missing_ollama_manager:{OLLAMA_MANAGER}"}
    ps_exe = r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
    script = (
        f"& '{OLLAMA_MANAGER}' "
        f"-Action {action} "
        "-Ports @(11434,11436,11437) "
        "-Json"
    )
    cmd = [
        ps_exe,
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        script,
    ]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except Exception as exc:
        return {"ok": False, "error": f"manager_exec_failed:{type(exc).__name__}:{exc}"}

    stdout = (proc.stdout or "").strip()
    stderr = (proc.stderr or "").strip()
    payload: dict[str, object] = {
        "returncode": int(proc.returncode),
        "stdout": stdout[-4000:],
        "stderr": stderr[-4000:],
    }
    if stdout:
        try:
            payload["json"] = json.loads(stdout)
        except Exception:
            pass
    payload["ok"] = proc.returncode == 0
    return payload


def _wait_for_ports(timeout_s: int = 30) -> dict[str, object]:
    start = time.time()
    while time.time() - start < timeout_s:
        open_ports = [port for port in OLLAMA_PORTS if _port_open(port)]
        if 11434 in open_ports:
            return {"ok": True, "ports": open_ports, "elapsed_s": round(time.time() - start, 2)}
        time.sleep(0.5)
    return {"ok": False, "ports": [port for port in OLLAMA_PORTS if _port_open(port)], "elapsed_s": round(time.time() - start, 2)}


def restart_ollama(reason: str = "", cooldown_s: int = 120) -> dict[str, object]:
    global _LAST_RESTART_TS
    now = time.time()
    age = now - float(_LAST_RESTART_TS or 0.0)
    if age < cooldown_s:
        return {
            "ok": False,
            "skipped": True,
            "reason": "cooldown_active",
            "cooldown_s": cooldown_s,
            "age_s": round(age, 2),
            "ports": [port for port in OLLAMA_PORTS if _port_open(port)],
        }

    _log(f"Restarting Ollama (reason={reason or 'unspecified'})")
    before = _run_manager("status")
    restarted = _run_manager("restart")
    waited = _wait_for_ports(timeout_s=40)
    if restarted.get("ok") and waited.get("ok"):
        _LAST_RESTART_TS = time.time()
    result = {
        "ok": bool(restarted.get("ok")) and bool(waited.get("ok")),
        "reason": reason,
        "before": before,
        "restart": restarted,
        "waited": waited,
        "ports": [port for port in OLLAMA_PORTS if _port_open(port)],
        "last_restart_ts": int(_LAST_RESTART_TS or 0),
    }
    _log(f"Restart result: {result}")
    return result


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, payload: dict[str, object]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._send_json(
                200,
                {
                    "status": "ok",
                    "ports": [port for port in OLLAMA_PORTS if _port_open(port)],
                    "last_restart_ts": int(_LAST_RESTART_TS or 0),
                    "manager_script": OLLAMA_MANAGER,
                },
            )
            return
        self._send_json(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/ollama/restart":
            self._send_json(404, {"error": "not_found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            reason = str(payload.get("reason") or "").strip()
            cooldown_s = max(30, min(int(payload.get("cooldown_s") or 120), 3600))
            result = restart_ollama(reason=reason, cooldown_s=cooldown_s)
            self._send_json(200, result)
        except Exception as exc:
            self._send_json(500, {"ok": False, "error": f"bridge_error:{exc}"})


if __name__ == "__main__":
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    _log(f"ollama guard bridge listening on http://{HOST}:{PORT}")
    server.serve_forever()
