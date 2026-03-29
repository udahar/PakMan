param()

$ErrorActionPreference = "Stop"

function Stop-PortListener {
    param([int]$Port)
    $lines = netstat -ano -p tcp | Select-String -Pattern "^\s*TCP\s+\S+:$Port\s+\S+\s+LISTENING\s+(\d+)\s*$"
    foreach ($line in $lines) {
        if ($line.Matches.Count -gt 0) {
            $portPid = [int]$line.Matches[0].Groups[1].Value
            try { Stop-Process -Id $portPid -Force -ErrorAction SilentlyContinue } catch {}
            try { taskkill /F /T /PID $portPid | Out-Null } catch {}
        }
    }
}

Get-CimInstance Win32_Process | Where-Object {
    $_.Name -match 'powershell' -and (
        $_.CommandLine -like '*OllamaBotApp*watchdog.ps1*' -or
        $_.CommandLine -like '*OllamaBot*ollama-watchdog.ps1*'
    )
} | ForEach-Object {
    try { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue } catch {}
}

$line = netstat -ano -p tcp | Select-String -Pattern "^\s*TCP\s+\S+:11435\s+\S+\s+LISTENING\s+(\d+)\s*$" | Select-Object -First 1
if ($line -and $line.Matches.Count -gt 0) {
    $proxyProcId = [int]$line.Matches[0].Groups[1].Value
    Stop-Process -Id $proxyProcId -Force -ErrorAction SilentlyContinue
}

Stop-PortListener -Port 8772
Stop-PortListener -Port 11434
Stop-PortListener -Port 11436
Stop-PortListener -Port 11437
Stop-PortListener -Port 11435
exit 0
