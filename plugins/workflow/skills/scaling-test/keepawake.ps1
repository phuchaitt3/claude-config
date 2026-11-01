# Runs a command line and keeps Windows from sleeping while it runs (SetThreadExecutionState).
# Usage: pwsh -NoProfile -File keepawake.ps1 -Run 'uv run python scripts/long_job.py --chunks 500000' [-Log run.log]
# -RunEncoded takes the command as base64 of its UTF-16LE text (schedule-heavy.ps1 uses it, so no
# quoting is needed). With -Log, output is appended to the file and a final line records the exit
# code and time, so a later session can see that the run finished.
# Sleep is blocked only while the command runs. The power plan is not changed, and a closed lid
# still sleeps unless the lid action is "do nothing". The exit code of the command is returned.
param([string]$Run, [string]$RunEncoded, [string]$Log)

if ($RunEncoded) { $Run = [Text.Encoding]::Unicode.GetString([Convert]::FromBase64String($RunEncoded)) }
if (-not $Run) { throw 'give -Run or -RunEncoded' }

Add-Type -Namespace Win -Name Power -MemberDefinition '[DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint flags);'
$continuous = [uint32]2147483648     # ES_CONTINUOUS
$systemRequired = [uint32]1          # ES_SYSTEM_REQUIRED
[void][Win.Power]::SetThreadExecutionState($continuous -bor $systemRequired)
try {
    if ($Log) { Add-Content -Path $Log -Value "== started $(Get-Date -Format s): $Run" }
    $global:LASTEXITCODE = $null
    if ($Log) { Invoke-Expression $Run *>> $Log } else { Invoke-Expression $Run }
    $code = if ($null -ne $LASTEXITCODE) { $LASTEXITCODE } else { 0 }
    if ($Log) { Add-Content -Path $Log -Value "== finished $(Get-Date -Format s) exit=$code" }
} finally {
    [void][Win.Power]::SetThreadExecutionState($continuous)   # release
}
exit $code
