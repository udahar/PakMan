$ErrorActionPreference = "Stop"

$root   = Split-Path -Parent $PSScriptRoot
$venv   = Join-Path $HOME ".pakman\venvs\ml"
$python = Join-Path $venv "Scripts\python.exe"
$probe  = Join-Path $root "probes\ml_stack_probe.py"

if (-not (Test-Path $python)) {
    throw "ML venv not found. Run: packages\MLStack\scripts\install.ps1"
}

& $python $probe
