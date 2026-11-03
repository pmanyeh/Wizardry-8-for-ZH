param(
    [Parameter(Mandatory)][ValidateSet('alpha', 'text', 'off')][string]$Phase,
    [string]$CaptureDirectory = ''
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$upstreamRoot = Join-Path $projectRoot 'local\wiz8-ws'
$gameDirectory = Join-Path $upstreamRoot 'games\work'
if (Get-Process Wiz8 -ErrorAction SilentlyContinue) {
    throw 'Close the existing test game before installing a new Hybrid pair.'
}
if (Test-Path -LiteralPath (Join-Path $upstreamRoot 'build\hybrid\GUARD_FAILED')) {
    throw 'The latest Hybrid build did not pass its guard; do not install stale outputs.'
}
if (-not $CaptureDirectory) {
    $phaseDirectory = switch ($Phase) {
        'alpha' { 'p1a-alpha' }
        'text' { 'p1b-hires-text' }
        'off' { 'p1b-feature-off' }
    }
    $CaptureDirectory = Join-Path $projectRoot "artifacts\$phaseDirectory"
}
$CaptureDirectory = [IO.Path]::GetFullPath($CaptureDirectory)
New-Item -ItemType Directory -Force -Path $CaptureDirectory | Out-Null
Copy-Item -LiteralPath (Join-Path $upstreamRoot 'build\version.dll') -Destination $gameDirectory -Force
foreach ($name in 'wiz8hy.dll', 'wiz8hy_hooks.txt') {
    Copy-Item -LiteralPath (Join-Path $upstreamRoot "build\hybrid\$name") -Destination $gameDirectory -Force
    if ((Get-FileHash -LiteralPath (Join-Path $upstreamRoot "build\hybrid\$name")).Hash -ne
        (Get-FileHash -LiteralPath (Join-Path $gameDirectory $name)).Hash) {
        throw "Installed pair hash differs: $name"
    }
}
$enabled = if ($Phase -eq 'off') { 0 } else { 1 }
[IO.File]::WriteAllText((Join-Path $gameDirectory 'wiz8zhtw.ini'), "[ZH-TW]`r`nEnabled=$enabled`r`n", [Text.Encoding]::ASCII)
$env:WIZ8_ZHTW_CAPTURE_DIR = $CaptureDirectory
$env:WIZ8_ZHTW_POC_PHASE = $Phase
$gameProcess = Start-Process -FilePath (Join-Path $gameDirectory 'Wiz8.exe') -WorkingDirectory $gameDirectory -WindowStyle Normal -PassThru
[ordered]@{
    phase = $Phase
    process_id = $gameProcess.Id
    game_directory = $gameDirectory
    capture_directory = $CaptureDirectory
    source_revision = (& git -C (Join-Path $upstreamRoot 'decomp') rev-parse HEAD)
    hybrid_sha256 = (Get-FileHash -LiteralPath (Join-Path $gameDirectory 'wiz8hy.dll')).Hash
    hooks_sha256 = (Get-FileHash -LiteralPath (Join-Path $gameDirectory 'wiz8hy_hooks.txt')).Hash
} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $CaptureDirectory 'run-info.json') -Encoding UTF8
"Started $Phase proof (PID $($gameProcess.Id)); capture directory: $CaptureDirectory"
