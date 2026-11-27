<#
.SYNOPSIS
  Overnight mode: put every laptop cap on (CPU turbo off, GPU clock 1000-1350 MHz).
.DESCRIPTION
  Max processor state 99% on AC (turbo off) and `gpu_run.py cap on`.
  Needs no administrator rights. Undo with game.ps1.
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
powercfg /setacvalueindex SCHEME_CURRENT SUB_PROCESSOR PROCTHROTTLEMAX 99
powercfg /setactive SCHEME_CURRENT
python (Join-Path $PSScriptRoot 'gpu_run.py') cap on
Set-LenovoMode 'quiet'
Write-Host 'NIGHT mode: CPU turbo OFF (99%), GPU cap ON (1350 MHz). Lenovo mode: see above.'
