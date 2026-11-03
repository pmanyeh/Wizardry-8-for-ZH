# The test module consumes this request and writes its own renderer readback.
$projectRoot = Split-Path -Parent $PSScriptRoot
$gameDirectory = Join-Path $projectRoot 'local\wiz8-ws\games\work'
New-Item -ItemType File -Force -Path (Join-Path $gameDirectory 'zhtwshot.req') | Out-Null
