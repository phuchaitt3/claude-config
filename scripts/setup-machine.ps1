# One command that makes this machine follow claude-config. Safe to run any number of times.
#   powershell -NoProfile -File "$HOME\claude-config\scripts\setup-machine.ps1"
# Does: git pull --ff-only on claude-config; registers the personal-config marketplace and installs
# or updates the workflow plugin (through the Claude Code command line); turns autoUpdate on in
# ~/.claude/settings.json (backup first, nothing else changed). After the first run nothing manual
# is needed again: the plugin pulls this repo at session start and updates itself.
# Needs git and python on PATH and the Claude Code CLI (on PATH, or the VS Code extension's copy).
$ErrorActionPreference = 'Continue'
$cfg = Join-Path $HOME 'claude-config'
function Step($m) { Write-Host "== $m" }

Step 'claude-config'
if (-not (Test-Path (Join-Path $cfg '.git'))) {
    Write-Host "No clone at $cfg. Run: git clone https://github.com/phuchaitt3/claude-config `"$cfg`""; exit 1
}
git -C $cfg pull --ff-only 2>&1 | Select-Object -Last 1 | Out-Host
if ($LASTEXITCODE -ne 0) { Write-Host 'PROBLEM  pull failed (local changes in claude-config?). Fix, then run this again.'; exit 1 }

Step 'Claude Code command line'
$claude = (Get-Command claude -ErrorAction SilentlyContinue).Source
if (-not $claude) {
    $claude = Get-ChildItem (Join-Path $HOME '.vscode\extensions') -Filter 'anthropic.claude-code-*' -Directory -ErrorAction SilentlyContinue |
        Sort-Object Name -Descending | ForEach-Object { Join-Path $_.FullName 'resources\native-binary\claude.exe' } |
        Where-Object { Test-Path $_ } | Select-Object -First 1
}
if (-not $claude) { Write-Host 'PROBLEM  no claude command line found (not on PATH, not in a VS Code extension). Install Claude Code first.'; exit 1 }
Write-Host "using $claude"

Step 'settings.json (autoUpdate)'
python (Join-Path $cfg 'scripts\merge_settings.py') --repo $cfg
if ($LASTEXITCODE -ne 0) { Write-Host 'PROBLEM  settings not updated (python missing, or settings.json is not valid JSON).'; exit 1 }

Step 'plugin'
$markets = & $claude plugin marketplace list 2>&1 | Out-String
if ($markets -notmatch 'personal-config') { & $claude plugin marketplace add $cfg 2>&1 | Select-Object -Last 2 | Out-Host }
else { & $claude plugin marketplace update personal-config 2>&1 | Select-Object -Last 1 | Out-Host }
$installed = & $claude plugin list 2>&1 | Out-String
if ($installed -notmatch 'workflow@personal-config') { & $claude plugin install workflow@personal-config 2>&1 | Select-Object -Last 2 | Out-Host }
else { & $claude plugin update workflow@personal-config 2>&1 | Select-Object -Last 1 | Out-Host }
& $claude plugin list 2>&1 | Select-String -Pattern 'workflow@personal-config|Version|Status' | Out-Host

Write-Host "`nDone. Restart Claude Code (close and reopen VS Code windows) to apply."
