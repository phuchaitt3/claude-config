<#
.SYNOPSIS
  Game mode: lift every laptop cap (CPU turbo on, GPU clock cap off).
.DESCRIPTION
  Max processor state 100% on AC (turbo on) and `gpu_run.py cap off`.
  Needs no administrator rights. Undo with night.ps1.
  Source of the settings: personal-notes machine/laptop-legion-y540.md.
#>
$ErrorActionPreference = 'Stop'
powercfg /setacvalueindex SCHEME_CURRENT SUB_PROCESSOR PROCTHROTTLEMAX 100
powercfg /setactive SCHEME_CURRENT
python (Join-Path $PSScriptRoot 'gpu_run.py') cap off
Write-Host 'GAME mode: CPU turbo ON (100%), GPU cap OFF. Set Lenovo mode to Performance by hand if you want it.'
