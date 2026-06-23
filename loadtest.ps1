# loadtest.ps1
# Stress test for GCP Load Balancer -> MIG autoscaling demo
#
# NOTE: PowerShell's ThreadJob pool defaults to a small number of threads
# (tied to CPU core count). With high -Concurrency values, most jobs sit
# in "NotStarted" forever waiting for a free pool thread. We raise the
# .NET ThreadPool minimum explicitly below to fix this.

param(
    [string]$Url = "http://34.8.223.80/",
    [int]$Concurrency = 50,
    [int]$DurationMinutes = 8
)

# Raise the .NET ThreadPool minimum so all $Concurrency threads can actually start
[System.Threading.ThreadPool]::SetMinThreads($Concurrency + 10, $Concurrency + 10) | Out-Null

Write-Host "=================================================="
Write-Host " GCP Load Balancer Stress Test"
Write-Host " Target:       $Url"
Write-Host " Concurrency:  $Concurrency"
Write-Host " Duration:     $DurationMinutes minute(s)"
Write-Host "=================================================="
Write-Host ""

$startTime = Get-Date
$endTime = $startTime.AddMinutes($DurationMinutes)

# Thread-safe counter object
$sync = [hashtable]::Synchronized(@{ Count = 0 })

$jobs = 1..$Concurrency | ForEach-Object {
    Start-ThreadJob -ThrottleLimit ($Concurrency + 10) -ScriptBlock {
        param($u, $endTime, $sync)
        while ((Get-Date) -lt $endTime) {
            try {
                Invoke-WebRequest -Uri $u -UseBasicParsing -TimeoutSec 5 | Out-Null
                $sync.Count = $sync.Count + 1
            } catch {}
        }
    } -ArgumentList $Url, $endTime, $sync
}

Write-Host "Load test running... press Ctrl+C to stop early."
Write-Host ""

while ((Get-Date) -lt $endTime) {
    Start-Sleep -Seconds 5
    $total = $sync.Count
    $elapsed = [math]::Round(((Get-Date) - $startTime).TotalSeconds)
    $rps = if ($elapsed -gt 0) { [math]::Round($total / $elapsed, 1) } else { 0 }
    $running = (Get-Job | Where-Object { $_.State -eq 'Running' }).Count
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Requests: $total  |  Elapsed: ${elapsed}s  |  ~$rps req/sec  |  Active workers: $running/$Concurrency"
}

Write-Host ""
Write-Host "Duration reached. Stopping workers..."
$jobs | Stop-Job -ErrorAction SilentlyContinue
$jobs | Remove-Job -ErrorAction SilentlyContinue
Write-Host "Total requests sent: $($sync.Count)"
Write-Host "Done."
