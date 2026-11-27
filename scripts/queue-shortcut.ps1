# Creates or refreshes the desktop shortcut "Self-drive queue" (runs selfdrive-queue.ps1).
# Called by setup-machine.ps1; safe to run any number of times. -Desktop is for the test.
param([string]$Desktop = [Environment]::GetFolderPath('Desktop'))
$ErrorActionPreference = 'Stop'
$shell = (Get-Command pwsh -ErrorAction SilentlyContinue).Source
if (-not $shell) { $shell = (Get-Command powershell).Source }
$path = Join-Path $Desktop 'Self-drive queue.lnk'
$link = (New-Object -ComObject WScript.Shell).CreateShortcut($path)
$link.TargetPath = $shell
$link.Arguments = "-NoProfile -File `"$(Join-Path $PSScriptRoot 'selfdrive-queue.ps1')`""
$link.WorkingDirectory = $HOME
$link.Description = 'Start a saved self-drive run'
$link.Save()
Write-Host "shortcut: $path"
