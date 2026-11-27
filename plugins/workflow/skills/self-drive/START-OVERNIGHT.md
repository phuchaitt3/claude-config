# Starting a self-drive overnight run (guide for the user)

The same start works at any hour (one self-drive mode, 2026-11-27). Written 2026-11-14 for workflow 0.54.0. An agent asked "how do I start an overnight run" reads this file and walks the user through it. The rules the run follows are in `SKILL.md` ("Overnight mode"); this file only says how to start, watch and stop one. If `SKILL.md` and this file disagree, `SKILL.md` wins: fix this file.

## Before you start (about 2 minutes)

1. **Usage credits off** at claude.ai/settings/usage, so the 5-hour limit pauses the run instead of billing it. The agent cannot see this setting.
2. **Machine stays on.** Laptop: plugged in, lid open or set to stay awake with the lid shut. PC: nothing to do beyond not turning it off or logging out. The `keep_awake` hook stops idle sleep while the run works; it cannot stop a closed lid, a dead battery or a shutdown. The run detects which machine it is on and skips the laptop-only steps (cooling check, clock cap, cap benchmark) on a desktop (`SKILL.md`, "Which machine").
3. **Installs that need admin.** A tool an issue needs that asks for administrator rights (a machine-wide installer, a write under Program Files) is installed now, while you are at the machine, or its issue is left out tonight. The readiness pass lists them; an overnight run cannot answer a UAC prompt (user's decision, 2026-11-19).
4. **Free disk space** of at least 20 GB on the system drive if the run might pull models or images.
5. **One loop per repository.** Two loops in one repository claim the same issues. Several repositories at once is fine, but they share one 5-hour quota: on a Pro plan, run one repository a night, or at most two.

## Start it (one terminal per repository)

Start the loop as a background session from a terminal, not from the VS Code Claude panel. A background session keeps its scheduled wakeups across an editor reload or update, and runs the status line that feeds the quota pause (`SKILL.md` step 7b). The VS Code panel does neither (both tested 2026-11-14).

In PowerShell, the short way (added 2026-11-15): one command does steps 1 to 4 below, and refuses a second session for the same repository and date.

```powershell
& "$HOME\claude-config\scripts\selfdrive.ps1" <repo name or path>              # e.g. thesis
& "$HOME\claude-config\scripts\selfdrive.ps1" <repo name or path> -ResumeFirst # resume-gap items before existing open issues
& "$HOME\claude-config\scripts\selfdrive.ps1" <repo name or path> -ReadyOnly   # earlier in the evening: readiness pass only (READY.md)
& "$HOME\claude-config\scripts\selfdrive.ps1" <repo name or path> -Issues 285,245 -Brief <file> # only these issues, in this order; -Brief appends a file to the prompt
```

The `-ReadyOnly` run (optional, about 10 to 20 minutes) files each missing prerequisite an agent can supply as a blocking issue and turns each one only you can supply into a `needs-you` item, so you can clear those before bed. You do not need to order issues or prepare prerequisites by hand; the overnight run repeats the pass itself if you skip it.

A name is looked up as `<SELFDRIVE_ROOT>\<name>\main`; set `SELFDRIVE_ROOT` once as a user environment variable (the script reads the stored value even in a terminal opened before it was set). Local scripts run under the machine's `RemoteSigned` policy, so no execution-policy change is needed.

The long way, by hand:

```powershell
# 1. Find the claude.exe bundled with the VS Code extension (its folder name changes with each update).
$c = (Get-ChildItem "$HOME\.vscode\extensions\anthropic.claude-code-*\resources\native-binary\claude.exe" | Select-Object -Last 1).FullName

# 2. Go to the repository's main checkout.
cd <path to the repository's main checkout>

# 3. Safety net: one fallback wakeup if a turn forgets to schedule the next round.
$env:CLAUDE_CODE_LOOP_KEEPALIVE = "1"

# 4. Start the loop in the background. Use today's date in the name.
& $c --bg -n selfdrive-<repo>-<yyyy-mm-dd> --model sonnet --permission-mode auto "Self-drive overnight in <repo> (main checkout, branch main). Load workflow:self-drive and follow Overnight mode."
```

Repeat steps 2 to 4 in a second terminal for a second repository (step 3 is per terminal).

If `claude` is on PATH on this machine, use `claude` instead of `& $c`.

## Check that it is running (1 minute)

- **A chat that started a short session for you** (the `-ReadyOnly` pass, a worker) starts a background Bash poll on `claude agents --json` until that session ends, in the same turn, so the harness re-invokes it and it reports; starting a session does not notify the starter (2026-11-23: a readiness pass ended after 2 minutes and the user heard 20 minutes later). The overnight loop runs all night and needs no poll.

- `& $c agents` lists sessions; the `selfdrive-...` one should be there and working.
- `& $c attach selfdrive-<repo>-<date>` opens it, so you can read its first message. It names anything you must do (for example, no keep-awake hold seen). Detach and leave it running.
- `Get-Content $HOME\.claude\hook-cache\quota.json` should show a recent `written_at` and the 5-hour percentage. If the file is missing or stale, the quota pause cannot work: say so to an agent.

## While it runs

- **The quota pause:** at 90% of the 5-hour limit the loop starts no new work, sleeps until 2 minutes after the reset, then goes on. Nothing to do.
- **Peek without disturbing it:** `& $c logs selfdrive-<repo>-<date>`, or the PR list on GitHub.
- **GPU and RAM jobs** from several loops queue behind one machine-wide lock; a second repository's measurement waits for the first.

## Stop it

- Attach (`& $c attach selfdrive-<repo>-<date>`) and type "stop the self-driving overnight". It finishes or parks its current task, writes the morning summary and the cost log, and ends.
- Hard stop, only if it does not respond: `& $c stop selfdrive-<repo>-<date>`, then `& $c rm selfdrive-<repo>-<date>`. A hard stop skips the morning summary; ask an agent to write it from the PRs.

## In the morning

- The summary is `overnight-<date>.md` in the project's handoff folder (or the session's final message if the project has none): PRs merged or waiting, decisions, what was skipped, quota pauses, the starting commit of `main`, and how to undo the night.
- First step of the review: `python ~/claude-config/scripts/night_timeline.py` prints one merged timeline of the night (daemon spawns and retirements with their reasons such as `[low memory]`, lock start/end, `low_memory` rows and the lowest free memory with its biggest users, harness low-memory kills, each session's final state). Add `--since`/`--until` for another window. The daemon itself retires idle workers under low memory and exits when none remain, so a `stop` after that fails with "service may be restarting".
- PRs labelled `resume-gap` are listed first; keep one by removing the label, or revert it.
- To review the run, ask an agent: "check how well the overnight run went in <repo>"; it reads the summary, the PRs and the transcripts' token use.
