<#
.SYNOPSIS
  Overnight mode: put every laptop cap on (CPU turbo off, GPU clock 1000-1350 MHz).
.DESCRIPTION
  Max processor state 99% on AC (turbo off) and `gpu_run.py cap on`.
  Needs no administrator rights. Undo with game.ps1.
  Source of the settings: personal-notes machine/laptop-legion-y540.md.
#>
$ErrorActionPreference = 'Stop'
powercfg /setacvalueindex SCHEME_CURRENT SUB_PROCESSOR PROCTHROTTLEMAX 99
powercfg /setactive SCHEME_CURRENT
python (Join-Path $PSScriptRoot 'gpu_run.py') cap on
Write-Host 'NIGHT mode: CPU turbo OFF (99%), GPU cap ON (1350 MHz). Set Lenovo mode back to Quiet by hand if you changed it.'
