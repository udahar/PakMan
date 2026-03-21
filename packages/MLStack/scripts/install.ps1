$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$req  = Join-Path $root "requirements.txt"

# Shared ML venv — outside the repo, accessible to FieldBench and other consumers
$venv   = Join-Path $HOME ".pakman\venvs\ml"
$python = Join-Path $venv "Scripts\python.exe"

if (-not (Test-Path $req)) {
    throw "requirements.txt not found at $req"
}

Write-Host "[MLStack] Venv target: $venv"
Write-Host "[MLStack] Creating / refreshing Python 3.12 environment"
New-Item -ItemType Directory -Force -Path (Split-Path $venv) | Out-Null
py -3.12 -m venv $venv
& $python -m pip install --upgrade pip setuptools wheel
Write-Host "[MLStack] Installing Python dependencies from $req"
& $python -m pip install -r $req
Write-Host "[MLStack] Running smoke test"
& $python (Join-Path $PSScriptRoot "smoke_test.py")
Write-Host "[MLStack] Install complete. Venv at: $venv"
Write-Host "[MLStack] Add to FieldBench: set PAKMAN_ML_PYTHON=$python"
