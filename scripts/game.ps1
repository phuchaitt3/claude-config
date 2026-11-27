<#
.SYNOPSIS
  Game mode: lift every laptop cap (CPU turbo on, GPU clock cap off).
.DESCRIPTION
  Max processor state 100% on AC (turbo on) and `gpu_run.py cap off`.
  Needs no administrator rights. Undo with night.ps1.
  Source of the settings: personal-notes machine/laptop-legion-y540.md.
#>
$ErrorActionPreference = 'Stop'

# Lenovo power mode through Lenovo Legion Toolkit (starts it if it is not running).
function Set-LenovoMode([string]$Mode) {
    $dir = Join-Path $env:LOCALAPPDATA 'Programs\LenovoLegionToolkit'
    $llt = Join-Path $dir 'llt.exe'
    if (-not (Test-Path $llt)) { Write-Warning 'Lenovo Legion Toolkit not found; set the Lenovo mode by hand.'; return }
    if (-not (Get-Process -Name 'Lenovo Legion Toolkit' -ErrorAction SilentlyContinue)) {
        Start-Process (Join-Path $dir 'Lenovo Legion Toolkit.exe') -ArgumentList '--minimized'
        Start-Sleep 6
    }
    & $llt feature set power-mode $Mode
    if ($LASTEXITCODE -ne 0) { Write-Warning "Lenovo mode NOT changed to $Mode (llt failed); the other settings still apply."; return }
    Write-Host "Lenovo mode now: $(& $llt feature get power-mode)"
}
powercfg /setacvalueindex SCHEME_CURRENT SUB_PROCESSOR PROCTHROTTLEMAX 100
powercfg /setactive SCHEME_CURRENT
python (Join-Path $PSScriptRoot 'gpu_run.py') cap off
Set-LenovoMode 'performance'
Write-Host 'GAME mode: CPU turbo ON (100%), GPU cap OFF. Lenovo mode: see above.'
