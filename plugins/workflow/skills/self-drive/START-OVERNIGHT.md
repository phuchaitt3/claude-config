# Starting a self-drive overnight run (guide for the user)

Written 2026-11-14 for workflow 0.54.0. An agent asked "how do I start an overnight run" reads this file and walks the user through it. The rules the run follows are in `SKILL.md` ("Overnight mode"); this file only says how to start, watch and stop one. If `SKILL.md` and this file disagree, `SKILL.md` wins: fix this file.

## Before you start (about 2 minutes)

1. **Usage credits off** at claude.ai/settings/usage, so the 5-hour limit pauses the run instead of billing it. The agent cannot see this setting.
2. **Laptop plugged in**, lid open or set to stay awake with the lid shut. The `keep_awake` hook stops idle sleep while the run works; it cannot stop a closed lid or a dead battery.
3. **Free disk space** of at least 20 GB on the system drive if the run might pull models or images.
4. **One loop per repository.** Two loops in one repository claim the same issues. Several repositories at once is fine, but they share one 5-hour quota: on a Pro plan, run one repository a night, or at most two.

## Start it (one terminal per repository)

Start the loop as a background session from a terminal, not from the VS Code Claude panel. A background session keeps its scheduled wakeups across an editor reload or update, and runs the status line that feeds the quota pause (`SKILL.md` step 7b). The VS Code panel does neither (both tested 2026-11-14).

In PowerShell:

```powershell
# 1. Find the claude.exe bundled with the VS Code extension (its folder name changes with each update).
$c = (Get-ChildItem "$HOME\.vscode\extensions\anthropic.claude-code-*\resources\native-binary\claude.exe" | Select-Object -Last 1).FullName

# 2. Go to the repository's main checkout.
cd <path to the repository's main checkout>

# 3. Safety net: one fallback wakeup if a turn forgets to schedule the next round.
$env:CLAUDE_CODE_LOOP_KEEPALIVE = "1"

# 4. Start the loop in the background. Use today's date in the name.
& $c --bg -n selfdrive-<repo>-<yyyy-mm-dd> --permission-mode auto "Self-drive overnight in <repo> (main checkout, branch main). Load workflow:self-drive and follow Overnight mode."
```

Repeat steps 2 to 4 in a second terminal for a second repository (step 3 is per terminal).

If `claude` is on PATH on this machine, use `claude` instead of `& $c`.

## Check that it is running (1 minute)

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
- PRs labelled `resume-gap` are listed first; keep one by removing the label, or revert it.
- To review the run, ask an agent: "check how well the overnight run went in <repo>"; it reads the summary, the PRs and the transcripts' token use.
