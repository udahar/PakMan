# Unified Ollama Instance Manager
# Purpose: Single source of truth for spawning/stopping Ollama instances
# Used by: Benchmark, FieldBench, manual startup
# Updated: 2026-02-22

param(
    [ValidateSet('start','stop','status','restart')]
    [string]$Action = 'status',

    [int[]]$Ports = @(11434, 11436, 11437),

    [switch]$Force,

    [switch]$Json
)

$ErrorActionPreference = "Stop"
$lockDir = "$env:USERPROFILE\.ollama_locks"

if (-not (Test-Path $lockDir)) {
    New-Item -ItemType Directory -Path $lockDir -Force | Out-Null
}

function Get-PortPid {
    param([int]$Port)
    try {
        $line = netstat -ano -p tcp | Select-String -Pattern "^\s*TCP\s+\S+:$Port\s+\S+\s+LISTENING\s+(\d+)\s*$" | Select-Object -First 1
        if ($line -and $line.Matches.Count -gt 0) {
            return [int]$line.Matches[0].Groups[1].Value
        }
    } catch {}
    return $null
}

function Test-OllamaAlive {
    param([int]$Port)
    try {
        $null = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/api/tags" -TimeoutSec 2
        return $true
    } catch {
        return $false
    }
}

function Get-StatusData {
    $items = @()
    foreach ($port in $Ports) {
        $lockFile = Join-Path $lockDir "ollama_$Port.lock"
        $lockPid = $null
        if (Test-Path $lockFile) {
            $lockPid = [int](Get-Content $lockFile -ErrorAction SilentlyContinue | Select-Object -First 1)
        }
        $portPid = Get-PortPid -Port $port
        $alive = Test-OllamaAlive -Port $port
        $items += [PSCustomObject]@{
            port = $port
            alive = [bool]$alive
            pid = $portPid
            lock_pid = $lockPid
            status = if ($alive) { "alive" } else { "down" }
        }
    }
    return $items
}

function Stop-OllamaInstance {
    param([int]$Port)
    $lockFile = Join-Path $lockDir "ollama_$Port.lock"

    # Try lock file first
    if (Test-Path $lockFile) {
        try {
            $lockPid = [int](Get-Content $lockFile -ErrorAction SilentlyContinue | Select-Object -First 1)
            if ($lockPid -gt 0) {
                Write-Host "  Stopping Ollama PID $lockPid (port $Port via lock file)..." -ForegroundColor Yellow
                try {
                    Stop-Process -Id $lockPid -Force -ErrorAction Stop
                } catch {
                    taskkill /F /T /PID $lockPid | Out-Null
                }
                Remove-Item $lockFile -Force -ErrorAction SilentlyContinue
                Start-Sleep -Seconds 2
                return
            }
        } catch {}
    }

    # Fallback: port scan
    $targetPid = Get-PortPid -Port $Port
    if ($targetPid -and $targetPid -gt 0) {
        Write-Host "  Stopping Ollama PID $targetPid (port $Port via netstat)..." -ForegroundColor Yellow
        try {
            Stop-Process -Id $targetPid -Force -ErrorAction Stop
        } catch {
            taskkill /F /T /PID $targetPid | Out-Null
        }
        Start-Sleep -Seconds 2
    }
}

function Start-OllamaInstance {
    param(
        [int]$Port,
        [string]$KeepAlive = '5m'
    )

    $lockFile = Join-Path $lockDir "ollama_$Port.lock"

    # Check lock file
    if ((Test-Path $lockFile) -and -not $Force) {
        $lockPid = [int](Get-Content $lockFile -ErrorAction SilentlyContinue | Select-Object -First 1)
        if ($lockPid -gt 0) {
            try {
                $proc = Get-Process -Id $lockPid -ErrorAction SilentlyContinue
                if ($proc -and (Test-OllamaAlive -Port $Port)) {
                    Write-Host "  Port $Port already running (PID $lockPid) ✅" -ForegroundColor Green
                    return
                }
            } catch {}
        }
        Remove-Item $lockFile -Force -ErrorAction SilentlyContinue
    }

    # Check port
    if ((Test-OllamaAlive -Port $Port) -and -not $Force) {
        $alivePid = Get-PortPid -Port $Port
        Write-Host "  Port $Port already alive (PID $alivePid) ✅" -ForegroundColor Green
        if ($alivePid) { Set-Content -Path $lockFile -Value $alivePid }
        return
    }

    # Kill stale process
    $stalePid = Get-PortPid -Port $Port
    if ($stalePid) {
        Write-Host "  Killing stale process on port $Port (PID $stalePid)..." -ForegroundColor Yellow
        try {
            Stop-Process -Id $stalePid -Force -ErrorAction Stop
        } catch {
            taskkill /F /T /PID $stalePid | Out-Null
        }
        Start-Sleep -Seconds 2
    }

    # Start fresh instance
    Write-Host "  Starting Ollama on port $Port (keep_alive=$KeepAlive)..." -ForegroundColor Cyan

    $env:OLLAMA_HOST = "127.0.0.1:$Port"
    $env:OLLAMA_KEEP_ALIVE = $KeepAlive
    $env:NO_PROXY = "127.0.0.1,localhost,ollama.com,.ollama.com"

    $ollamaExe = "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"
    if (-not (Test-Path $ollamaExe)) {
        throw "Ollama not found at $ollamaExe"
    }

    $proc = Start-Process -FilePath $ollamaExe -ArgumentList 'serve' -WindowStyle Hidden -PassThru
    Set-Content -Path $lockFile -Value $proc.Id

    # Wait for readiness
    $maxWait = 15
    $waited = 0
    while ($waited -lt $maxWait) {
        Start-Sleep -Seconds 1
        $waited += 1
        if (Test-OllamaAlive -Port $Port) {
            Write-Host "    ✅ Ready (PID $($proc.Id))" -ForegroundColor Green
            return
        }
    }

    Write-Host "    ⚠️ Started but not responding yet (PID $($proc.Id))" -ForegroundColor Yellow
}

function Show-Status {
    $statusData = Get-StatusData
    if ($Json) {
        [PSCustomObject]@{
            action = $Action
            ports = $statusData
        } | ConvertTo-Json -Depth 4
        return
    }

    Write-Host "`n=== Ollama Instance Status ===" -ForegroundColor Cyan
    foreach ($item in $statusData) {
        $status = if ($item.alive) { "✅ ALIVE" } else { "❌ DOWN" }
        $pidInfo = if ($item.pid) { "PID $($item.pid)" } elseif ($item.lock_pid) { "Lock PID $($item.lock_pid) (stale)" } else { "No PID" }
        Write-Host "  Port $($item.port) : $status ($pidInfo)"
    }
    Write-Host ""
}

# Main logic
switch ($Action) {
    'start' {
        Write-Host "`n=== Starting Ollama Instances ===" -ForegroundColor Green
        foreach ($port in $Ports) {
            $keepAlive = if ($port -eq 11437) { '5s' } else { '5m' }
            Start-OllamaInstance -Port $port -KeepAlive $keepAlive
        }
        Show-Status
    }

    'stop' {
        Write-Host "`n=== Stopping Ollama Instances ===" -ForegroundColor Red
        foreach ($port in $Ports) {
            Stop-OllamaInstance -Port $port
        }
        Show-Status
    }

    'restart' {
        Write-Host "`n=== Restarting Ollama Instances ===" -ForegroundColor Yellow
        foreach ($port in $Ports) {
            Stop-OllamaInstance -Port $port
        }
        Start-Sleep -Seconds 3
        foreach ($port in $Ports) {
            $keepAlive = if ($port -eq 11437) { '5s' } else { '5m' }
            Start-OllamaInstance -Port $port -KeepAlive $keepAlive
        }
        Show-Status
    }

    'status' {
        Show-Status
    }
}

exit 0
