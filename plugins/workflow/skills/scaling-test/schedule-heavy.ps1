# Schedules a heavy local job for a time the owner chose (Windows Task Scheduler).
# Usage: pwsh -NoProfile -File schedule-heavy.ps1 -Name qdrant-scale -At '2026-11-02 23:00' `
#            -Run 'uv run python scripts/qdrant_scale.py qdrant ...' -WorkDir 'D:\work' -Log 'D:\work\scale.log'
# The job runs through keepawake.ps1 (no sleep while it runs), wakes the computer if it is asleep
# (needs "allow wake timers" in the power plan, which this script does not change), starts only on
# AC power and is stopped if the charger is pulled (Task Scheduler defaults, kept on purpose), runs
# as the signed-in user, stops after -MaxHours, and deletes its own task when it ends.
# The log gets "== started" and "== finished ... exit=<code>" lines for the next session to read.
# Show a task: Get-ScheduledTask -TaskName <name>.  Remove it: Unregister-ScheduledTask -TaskName <name> -Confirm:$false
param(
    [Parameter(Mandatory)][string]$Name,
    [Parameter(Mandatory)][datetime]$At,
    [Parameter(Mandatory)][string]$Run,
    [Parameter(Mandatory)][string]$WorkDir,
    [Parameter(Mandatory)][string]$Log,
    [int]$MaxHours = 4
)

if ($At -le (Get-Date)) { throw "-At must be in the future" }
$keepAwake = Join-Path $PSScriptRoot 'keepawake.ps1'
$full = "Set-Location -LiteralPath '$WorkDir'; $Run; Unregister-ScheduledTask -TaskName '$Name' -Confirm:`$false"
$encoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($full))
$pwsh = (Get-Command pwsh).Source
$action = New-ScheduledTaskAction -Execute $pwsh -WorkingDirectory $WorkDir `
    -Argument "-NoProfile -File `"$keepAwake`" -RunEncoded $encoded -Log `"$Log`""
$trigger = New-ScheduledTaskTrigger -Once -At $At
$settings = New-ScheduledTaskSettingsSet -WakeToRun -ExecutionTimeLimit (New-TimeSpan -Hours $MaxHours) `
    -StartWhenAvailable -MultipleInstances IgnoreNew
$principal = New-ScheduledTaskPrincipal -UserId ([Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive
Register-ScheduledTask -TaskName $Name -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description 'Heavy job scheduled by an agent (workflow:scaling-test)' | Out-Null
$task = Get-ScheduledTask -TaskName $Name
"scheduled '$Name' for $($At.ToString('s')); log: $Log; state: $($task.State)"
