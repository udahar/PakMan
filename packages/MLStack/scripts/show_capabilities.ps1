$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root ".venv312\\Scripts\\python.exe"
$script = Join-Path $root "scripts\\show_capabilities.py"

if (-not (Test-Path $python)) {
    throw "MLStack venv not found at $python"
}

$env:PYTHONPATH = $root
& $python $script
