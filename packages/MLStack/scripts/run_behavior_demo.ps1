$ErrorActionPreference = "Stop"

$root   = Split-Path -Parent $PSScriptRoot
$venv   = Join-Path $HOME ".pakman\venvs\ml"
$python = Join-Path $venv "Scripts\python.exe"
$script = Join-Path $root "scripts\demo_behavior_profile.py"

if (-not (Test-Path $python)) {
    throw "ML venv not found. Run: packages\MLStack\scripts\install.ps1"
}

$env:PYTHONPATH = $root
& $python $script
