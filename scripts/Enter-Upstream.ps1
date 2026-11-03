# Dot-source from the project root: . .\scripts\Enter-Upstream.ps1
# Changes only the current PowerShell session; no system PATH/registry changes.
$projectRoot = Split-Path -Parent $PSScriptRoot
$physicalRoot = Join-Path $projectRoot 'local\wiz8-ws'
$compatibilityRoot = 'C:\dev\wiz8-ws'

if (-not (Test-Path -LiteralPath (Join-Path $physicalRoot '.git'))) {
    throw "Upstream checkout not found: $physicalRoot"
}
$compatibilityLink = Get-Item -LiteralPath $compatibilityRoot -Force -ErrorAction Stop
$junctionTarget = [string]@($compatibilityLink.Target)[0]
if ($compatibilityLink.LinkType -ne 'Junction' -or
    [IO.Path]::GetFullPath($junctionTarget).TrimEnd('\') -ne
    [IO.Path]::GetFullPath($physicalRoot).TrimEnd('\')) {
    throw "The upstream compatibility junction does not point at $physicalRoot"
}

Set-Location -LiteralPath $compatibilityRoot
. .\Tools\env.ps1
Write-Host "Upstream files: $physicalRoot"
Write-Host "Build entry:    $compatibilityRoot (junction to the same files)"
