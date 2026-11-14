<#
.SYNOPSIS
  Start a self-drive overnight run as a background session (workflow:self-drive, "Overnight mode").

.EXAMPLE
  selfdrive.ps1 book-rag-app
  selfdrive.ps1 thesis -ResumeFirst
  selfdrive.ps1 C:\path\to\repo\main -Name selfdrive-custom

.DESCRIPTION
  Does what plugins/workflow/skills/self-drive/START-OVERNIGHT.md says to type by hand:
  finds the extension's bundled claude.exe, goes to the repository's main checkout, sets
  CLAUDE_CODE_LOOP_KEEPALIVE=1 and starts `claude --bg`.

  <Repo> is either a path, or a folder name under $env:SELFDRIVE_ROOT (checkout at
  <root>\<name>\main). Set SELFDRIVE_ROOT once, e.g.
  [Environment]::SetEnvironmentVariable('SELFDRIVE_ROOT', '<your projects folder>', 'User')
  -ResumeFirst adds one line to the brief: take resume-gap items before existing open issues.
  One loop per repository: the script refuses to start a second session for the same repo and date.
#>
param(
    [Parameter(Mandatory, Position = 0)][string]$Repo,
    [switch]$ResumeFirst,
    [string]$Name
)

$ErrorActionPreference = 'Stop'

# 1. The claude.exe bundled with the VS Code extension (the folder name changes with each update).
$c = Get-ChildItem "$HOME\.vscode\extensions\anthropic.claude-code-*\resources\native-binary\claude.exe" -ErrorAction SilentlyContinue |
    Sort-Object { $_.Directory.Parent.Parent.Name } | Select-Object -Last 1
if (-not $c) {
    $onPath = Get-Command claude -ErrorAction SilentlyContinue
    if ($onPath) { $c = $onPath.Source } else { throw 'claude.exe not found (VS Code extension or PATH).' }
} else { $c = $c.FullName }

# 2. The repository's main checkout. A terminal opened by an app started before SELFDRIVE_ROOT
# was set does not see it, so fall back to the stored user value.
if (-not $env:SELFDRIVE_ROOT) { $env:SELFDRIVE_ROOT = [Environment]::GetEnvironmentVariable('SELFDRIVE_ROOT', 'User') }
if (Test-Path -LiteralPath $Repo) {
    $dir = (Resolve-Path -LiteralPath $Repo).Path
} elseif ($env:SELFDRIVE_ROOT -and (Test-Path -LiteralPath (Join-Path $env:SELFDRIVE_ROOT "$Repo\main"))) {
    $dir = (Resolve-Path -LiteralPath (Join-Path $env:SELFDRIVE_ROOT "$Repo\main")).Path
} else {
    throw "No such path, and SELFDRIVE_ROOT\$Repo\main not found (SELFDRIVE_ROOT='$env:SELFDRIVE_ROOT')."
}
if (-not (Test-Path -LiteralPath (Join-Path $dir '.git'))) { throw "$dir is not a git checkout." }
$repoName = if ((Split-Path $dir -Leaf) -eq 'main') { Split-Path (Split-Path $dir -Parent) -Leaf } else { Split-Path $dir -Leaf }
if (-not $Name) { $Name = "selfdrive-$repoName-$(Get-Date -Format 'yyyy-MM-dd')" }

# One loop per repository: refuse if a session with this name is already listed.
$existing = & $c agents --json 2>$null | Out-String
if ($existing -match [regex]::Escape($Name)) { throw "A session named $Name already exists. Attach to it (claude attach $Name) or stop it first." }

# 3 and 4. Safety-net wakeup, then start the background session.
$env:CLAUDE_CODE_LOOP_KEEPALIVE = '1'
$brief = "Self-drive overnight in $repoName (main checkout, branch main). Load workflow:self-drive and follow Overnight mode."
if ($ResumeFirst) { $brief += ' Tonight, take resume-gap items from ~/.claude/resume-gaps.md before existing open issues.' }

Push-Location $dir
try { & $c --bg -n $Name --permission-mode auto $brief } finally { Pop-Location }
Write-Host "Started $Name in $dir. Check: claude logs $Name"
