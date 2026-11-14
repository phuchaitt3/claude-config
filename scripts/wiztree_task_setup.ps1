<#
One-time setup, run in an ADMINISTRATOR PowerShell: lets agents run a fast WizTree scan (MFT read,
needs admin) with no UAC prompt, through a scheduled task they start with
`schtasks /Run /TN WizTreeExport`. Agents get only this one elevated action, nothing else.

Safety (an elevated task must not run or write anything a normal process can change):
- WizTree is copied to "C:\Program Files\WizTree", writable by administrators only; the task runs
  that copy, never the install folder (which may be user-writable).
- The output folder is re-created with an ACL that lets normal users read but not write, so no
  process can plant a link there for the elevated scan to overwrite.

Output: <OutDir>\<drive letter>.csv per drive (folders only, sorted by size). Re-run this script
after a WizTree update to refresh the copy. Remove: Unregister-ScheduledTask WizTreeExport.
Standard: findings/disk-cleanup-windows, checked 2026-11-15.
#>
param(
    [Parameter(Mandatory)] [string]$Source,                      # folder holding WizTree64.exe
    [string]$OutDir = "$env:ProgramData\WizTreeExport",
    [string[]]$Drives = @("C")
)
$ErrorActionPreference = "Stop"
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
        [Security.Principal.WindowsBuiltInRole]::Administrator)) { throw "Run this in an administrator PowerShell." }
if (-not (Test-Path (Join-Path $Source "WizTree64.exe"))) { throw "WizTree64.exe not found in $Source" }

$dest = "$env:ProgramFiles\WizTree"
New-Item -ItemType Directory -Force $dest | Out-Null
Copy-Item (Join-Path $Source "*") $dest -Recurse -Force   # Program Files inherits admin-only write

New-Item -ItemType Directory -Force $OutDir | Out-Null
icacls $OutDir /inheritance:r /grant:r "*S-1-5-32-544:(OI)(CI)F" "*S-1-5-18:(OI)(CI)F" "*S-1-5-32-545:(OI)(CI)RX" | Out-Null

$exe = Join-Path $dest "WizTree64.exe"
$actions = foreach ($d in $Drives) {
    New-ScheduledTaskAction -Execute $exe -Argument "`"$($d):`" /export=`"$OutDir\$d.csv`" /admin=1 /exportfiles=0 /exportfolders=1 /sortby=1"
}
$user = "$env:USERDOMAIN\$env:USERNAME"
$principal = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 15) -AllowStartIfOnBatteries
Register-ScheduledTask -TaskName "WizTreeExport" -Action $actions -Principal $principal -Settings $settings `
    -Description "Fast WizTree folder-size export for agents (no UAC prompt). Output: $OutDir" -Force | Out-Null
"Done. Agents run: schtasks /Run /TN WizTreeExport ; output: $OutDir\<drive>.csv"
