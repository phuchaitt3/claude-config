<#
.SYNOPSIS
  Menu of saved self-drive runs (open issues labelled saved-run) across your repositories; starts one.
  No model is called until selfdrive.ps1 starts the run you pick.

.EXAMPLE
  selfdrive-queue.ps1                          # menu: type a number
  selfdrive-queue.ps1 -List                    # print the queue and stop
  selfdrive-queue.ps1 -Pick book-rag-app#12    # start that run without asking (a number works too)

.DESCRIPTION
  Issue body (workflow:self-drive, "Saved runs"):
      Issues: #273, #245, #285
      Machine: laptop            (optional: laptop, desktop or any)
      <blank line>
      <the brief, free text>
  A run is marked "cannot run here" when this machine has no checkout of its repository, the Machine
  line names the other kind of machine, the body cannot be read, or selfdrive.ps1 -DryRun refuses it
  (for example under 30 GB free); that message is shown as it is.
  Only issues from authors with write access are listed, because the brief becomes an agent's prompt.
  -Owner defaults to the owner of claude-config's origin. -DryRun is passed on to selfdrive.ps1.
  Tests only: SELFDRIVE_TEST_ISSUES (a JSON file in place of gh), SELFDRIVE_TEST_MACHINE.
#>
param(
    [string]$Pick,
    [switch]$List,
    [switch]$DryRun,
    [string]$Owner
)

$ErrorActionPreference = 'Stop'
$selfdrive = Join-Path $PSScriptRoot 'selfdrive.ps1'
$menu = -not $Pick -and -not $List
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch {}

# git writes to stderr for ordinary things; Windows PowerShell would turn that into an error.
function Get-Origin($path) {
    $ErrorActionPreference = 'SilentlyContinue'
    git -C $path remote get-url origin 2>$null
}

function Get-SavedRuns {
    if ($env:SELFDRIVE_TEST_ISSUES) {
        $json = Get-Content -LiteralPath $env:SELFDRIVE_TEST_ISSUES -Raw -Encoding UTF8
    } else {
        if (-not $Owner) {
            $url = Get-Origin $PSScriptRoot
            if ($url -notmatch '[:/]([^/:]+)/[^/]+?/?$') { throw 'Cannot tell your GitHub owner from claude-config; pass -Owner.' }
            $Owner = $Matches[1]
        }
        $json = gh search issues --owner $Owner --label saved-run --state open --limit 100 --json 'repository,number,title,body,createdAt,authorAssociation' | Out-String
        if ($LASTEXITCODE -ne 0) { throw 'gh search failed (gh signed in? network?).' }
    }
    $all = @($json | ConvertFrom-Json | ForEach-Object { $_ })
    $trusted = @($all | Where-Object { $_.authorAssociation -in 'OWNER', 'MEMBER', 'COLLABORATOR' })
    if ($trusted.Count -lt $all.Count) { Write-Host "Ignored $($all.Count - $trusted.Count) issue(s) from authors without write access." }
    $trusted | Sort-Object createdAt, number
}

# The header is the lines before the first blank line; the rest is the brief.
function Read-Body($body) {
    $parts = "$body".Replace("`r`n", "`n").Trim() -split "`n[ `t]*`n", 2
    $run = @{ Issues = @(); Machine = 'any'; Brief = ''; Problem = $null }
    if ($parts.Count -gt 1) { $run.Brief = $parts[1].Trim() }
    foreach ($line in $parts[0] -split "`n") {
        if ($line -match '^\s*Issues:\s*((#?\d+[,\s]*)+)$') {
            $run.Issues = @($Matches[1] -split '[,\s#]+' | Where-Object { $_ } | ForEach-Object { [int]$_ })
        } elseif ($line -match '^\s*Machine:\s*(laptop|desktop|any)\s*$') {
            $run.Machine = $Matches[1].ToLower()
        } else {
            $run.Problem = "cannot read this header line of the issue: $($line.Trim())"
        }
    }
    if (-not $run.Issues -and -not $run.Problem) { $run.Problem = "the issue has no 'Issues: #1, #2' line" }
    $run
}

# Checkouts on this machine: <SELFDRIVE_ROOT>\<name>\main (or <name>), and claude-config.
function Find-Checkout($slug) {
    if (-not $env:SELFDRIVE_ROOT) { $env:SELFDRIVE_ROOT = [Environment]::GetEnvironmentVariable('SELFDRIVE_ROOT', 'User') }
    if ($null -eq $script:checkouts) {
        $paths = @()
        if ($env:SELFDRIVE_ROOT -and (Test-Path -LiteralPath $env:SELFDRIVE_ROOT)) {
            $paths = @(Get-ChildItem -LiteralPath $env:SELFDRIVE_ROOT -Directory | ForEach-Object { Join-Path $_.FullName 'main'; $_.FullName })
        }
        $paths += Join-Path $HOME 'claude-config'
        $script:checkouts = @($paths | Where-Object { Test-Path -LiteralPath (Join-Path $_ '.git') } |
            ForEach-Object { @{ Path = $_; Url = "$(Get-Origin $_)" } })
    }
    $pattern = "[:/]$([regex]::Escape($slug))(\.git)?/?$"
    ($script:checkouts | Where-Object { $_.Url -match $pattern } | Select-Object -First 1).Path
}

function Get-ThisMachine {
    if ($env:SELFDRIVE_TEST_MACHINE) { return $env:SELFDRIVE_TEST_MACHINE }
    if (Get-CimInstance Win32_Battery -ErrorAction SilentlyContinue) { 'laptop' } else { 'desktop' }
}

# Why this machine cannot do the run, or $null.
function Get-Blocker($run, $machine) {
    if ($run.Problem) { return $run.Problem }
    if (-not $run.Path) { return "no checkout of $($run.Slug) on this machine" }
    if ($run.Machine -ne 'any' -and $run.Machine -ne $machine) { return "needs the $($run.Machine); this is a $machine" }
    try { & $selfdrive $run.Path -DryRun | Out-Null } catch { return $_.Exception.Message }
}

function Start-Run($run) {
    $text = "This is saved run $($run.Slug)#$($run.Number): when the run stops, close or update that issue (workflow:self-drive, `"Saved runs`").`n$($run.Brief)"
    # Windows PowerShell does not escape double quotes inside a native argument.
    if ($PSVersionTable.PSVersion.Major -lt 6) { $text = $text.Replace('"', "'") }
    $file = Join-Path ([IO.Path]::GetTempPath()) "saved-run-$($run.Number).md"
    Set-Content -LiteralPath $file -Value $text -Encoding UTF8
    try { & $selfdrive $run.Path -Issues $run.Issues -Brief $file -DryRun:$DryRun }
    finally { Remove-Item -LiteralPath $file -ErrorAction SilentlyContinue }
}

$code = 0
try {
    $machine = Get-ThisMachine
    Write-Host 'Reading saved runs from GitHub...'
    $runs = @(Get-SavedRuns | ForEach-Object {
        $run = Read-Body $_.body
        $run.Slug = $_.repository.nameWithOwner
        $run.Repo = $_.repository.name
        $run.Number = [int]$_.number
        $run.Title = $_.title
        $run.Saved = ([datetime]$_.createdAt).ToLocalTime().ToString('yyyy-MM-dd')
        $run.Path = Find-Checkout $run.Slug
        $run.Blocker = Get-Blocker $run $machine
        $run
    })
    if (-not $runs) {
        Write-Host 'The queue is empty. In a chat, say "save this to my queue".'
    } else {
        Write-Host "`nSaved runs (this machine: $machine)`n"
        for ($i = 0; $i -lt $runs.Count; $i++) {
            $r = $runs[$i]
            $issues = ($r.Issues | ForEach-Object { "#$_" }) -join ' '
            Write-Host "$($i + 1)) $($r.Repo)#$($r.Number)  saved $($r.Saved)  issues: $issues"
            Write-Host "     $($r.Title)"
            if ($r.Blocker) { Write-Host "     CANNOT RUN HERE: $($r.Blocker)" -ForegroundColor Yellow }
        }
    }
    if ($runs -and -not $List) {
        if (-not $Pick) { $Pick = "$(Read-Host "`nNumber to start (Enter to quit)")".Trim() }
        if ($Pick) {
            $chosen = if ($Pick -match '^\d+$') {
                if ([int]$Pick -ge 1 -and [int]$Pick -le $runs.Count) { $runs[[int]$Pick - 1] }
            } else {
                $runs | Where-Object { $Pick -in "$($_.Repo)#$($_.Number)", "$($_.Slug)#$($_.Number)" }
            }
            if (@($chosen).Count -ne 1 -or -not $chosen) { throw "No single saved run matches '$Pick'." }
            if ($chosen.Blocker) { throw "Cannot run $($chosen.Repo)#$($chosen.Number) here: $($chosen.Blocker)" }
            Start-Run $chosen
        }
    }
} catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    $code = 1
}
# The desktop shortcut's window closes when the script ends.
if ($menu) { Read-Host "`nPress Enter to close" | Out-Null }
exit $code
