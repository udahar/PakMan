param(
    [switch]$CheckOnly
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$logs = Join-Path $root "logs"
$scriptPath = Join-Path $root "bridge.py"
$healthUrl = "http://127.0.0.1:8772/health"
$pidFile = Join-Path $root ".ollama_guard_bridge.pid"

if (-not (Test-Path $logs)) {
    New-Item -ItemType Directory -Path $logs -Force | Out-Null
}

function Test-WebReady {
    param([string]$Url, [int]$TimeoutSec = 2)
    try {
        $resp = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec $TimeoutSec -ErrorAction Stop
        return ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 400)
    } catch {
        return $false
    }
}

function Get-BridgePids {
    $matches = netstat -ano -p tcp | Select-String -Pattern "^\s*TCP\s+\S+:8772\s+\S+\s+LISTENING\s+(\d+)\s*$"
    $ids = @()
    foreach ($line in $matches) {
        if ($line.Matches.Count -gt 0) {
            $ids += [int]$line.Matches[0].Groups[1].Value
        }
    }
    return @($ids | Sort-Object -Unique)
}

if (Test-WebReady -Url $healthUrl -TimeoutSec 2) {
    Write-Output "healthy"
    exit 0
}

if ($CheckOnly) {
    Write-Output "down"
    exit 1
}

foreach ($existingPid in Get-BridgePids) {
    try {
        Stop-Process -Id $existingPid -Force -ErrorAction SilentlyContinue
    } catch {}
    try {
        taskkill /F /T /PID $existingPid | Out-Null
    } catch {}
}
Start-Sleep -Seconds 1

$pythonCmd = Get-Command pythonw.exe -ErrorAction SilentlyContinue
if (-not $pythonCmd) { $pythonCmd = Get-Command python.exe -ErrorAction SilentlyContinue }
if (-not $pythonCmd) { $pythonCmd = Get-Command python -ErrorAction SilentlyContinue }
if (-not $pythonCmd) {
    throw "Python not found"
}

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$stdoutLog = Join-Path $logs "ollama_guard_stdout_$stamp.log"
$stderrLog = Join-Path $logs "ollama_guard_stderr_$stamp.log"

$proc = Start-Process -FilePath $pythonCmd.Source `
    -ArgumentList @($scriptPath) `
    -WorkingDirectory $root `
    -WindowStyle Hidden `
    -PassThru `
    -RedirectStandardOutput $stdoutLog `
    -RedirectStandardError $stderrLog

$proc.Id | Set-Content -Path $pidFile

for ($i = 0; $i -lt 15; $i++) {
    Start-Sleep -Seconds 1
    if (Test-WebReady -Url $healthUrl -TimeoutSec 2) {
        Write-Output "started"
        exit 0
    }
    if (-not (Get-Process -Id $proc.Id -ErrorAction SilentlyContinue)) {
        break
    }
}

Write-Output "failed"
exit 1
