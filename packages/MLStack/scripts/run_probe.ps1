$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root ".venv312\\Scripts\\python.exe"
$probe = Join-Path $root "probes\\ml_stack_probe.py"

if (-not (Test-Path $python)) {
    throw "MLStack venv not found at $python"
}

& $python $probe
