param(
    [string]$ExePath = "dist\\VideoToMP3.exe",
    [int]$LaunchTimeoutSeconds = 10
)

$ErrorActionPreference = "Stop"

function Add-Result {
    param(
        [string]$Name,
        [bool]$Ok,
        [string]$Detail
    )
    [PSCustomObject]@{
        Check = $Name
        Status = if ($Ok) { "OK" } else { "FAIL" }
        Detail = $Detail
    }
}

$results = @()

$fullExePath = Resolve-Path -Path $ExePath -ErrorAction SilentlyContinue
if (-not $fullExePath) {
    $results += Add-Result -Name "EXE exists" -Ok $false -Detail "No se encontro: $ExePath"
    $results | Format-Table -AutoSize
    exit 1
}

$results += Add-Result -Name "EXE exists" -Ok $true -Detail $fullExePath.Path

$appDataDir = Join-Path $env:APPDATA "video-to-mp3"
if (-not (Test-Path $appDataDir)) {
    New-Item -ItemType Directory -Path $appDataDir -Force | Out-Null
}

$results += Add-Result -Name "APPDATA folder writable" -Ok (Test-Path $appDataDir) -Detail $appDataDir

$proc = $null
try {
    $proc = Start-Process -FilePath $fullExePath.Path -PassThru
    $ended = Wait-Process -Id $proc.Id -Timeout $LaunchTimeoutSeconds -ErrorAction SilentlyContinue
    if ($ended) {
        $results += Add-Result -Name "App launch" -Ok $false -Detail "El proceso termino antes de $LaunchTimeoutSeconds s."
    }
    else {
        $results += Add-Result -Name "App launch" -Ok $true -Detail "El proceso sigue vivo tras $LaunchTimeoutSeconds s."
    }
}
catch {
    $results += Add-Result -Name "App launch" -Ok $false -Detail $_.Exception.Message
}
finally {
    if ($proc -and -not $proc.HasExited) {
        Stop-Process -Id $proc.Id -Force
    }
}

$historyFile = Join-Path $appDataDir "history.json"
$results += Add-Result -Name "History path" -Ok $true -Detail $historyFile

$reportPath = Join-Path (Get-Location).Path "vm-smoke-report.txt"
$timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
"VM Smoke Test - $timestamp" | Out-File -FilePath $reportPath -Encoding utf8
$results | Format-Table -AutoSize | Out-String | Out-File -FilePath $reportPath -Append -Encoding utf8

$results | Format-Table -AutoSize
Write-Host "Reporte: $reportPath"

if ($results.Status -contains "FAIL") {
    exit 1
}

exit 0
