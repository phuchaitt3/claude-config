# Runs a command line and keeps Windows from sleeping while it runs (SetThreadExecutionState).
# Usage: pwsh -NoProfile -File keepawake.ps1 -Run 'uv run python scripts/long_job.py --chunks 500000'
# Sleep is blocked only while the command runs. The power plan is not changed, and a closed lid
# still sleeps unless the lid action is "do nothing". The exit code of the command is returned.
param([Parameter(Mandatory)][string]$Run)

Add-Type -Namespace Win -Name Power -MemberDefinition '[DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint flags);'
$continuous = [uint32]2147483648     # ES_CONTINUOUS
$systemRequired = [uint32]1          # ES_SYSTEM_REQUIRED
[void][Win.Power]::SetThreadExecutionState($continuous -bor $systemRequired)
try {
    Invoke-Expression $Run
    $code = if ($null -ne $LASTEXITCODE) { $LASTEXITCODE } else { 0 }
} finally {
    [void][Win.Power]::SetThreadExecutionState($continuous)   # release
}
exit $code
