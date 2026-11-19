# Readiness pass: put prerequisites in place before an overnight run

(User's decision, 2026-11-18, after evenings went on ordering issues and preparing their prerequisites by hand.) One pass per repository, run by the overnight run before its first round (`SKILL.md`, "Readiness pass"), or earlier in the evening by `selfdrive.ps1 <repo> -ReadyOnly`, so the user sees what only they can do before bed. It does not change the ranking: `next_task.py` already ranks an issue's blockers ahead of it, so a prerequisite filed as a blocking issue is done first by the run itself.

## Who runs it

One worker subagent, Sonnet at medium effort (`workflow:subagents` applies), given the repository and this file's path. The loop chat reads back only the report. Run it after resume triage, since triage changes the order.

## How deep

Run `python <this skill's folder>/next_task.py --ready-depth` in the repository. It prints the depth N: the repository's merged PRs per run hour (mean over its last 7 runs with a merge, from `~/.claude/selfdrive-runs.jsonl`) times 8 hours, at least 5 (`--hours` for a shorter or longer night). Then read issues in the order `next_task.py --limit <3N>` prints, and stop once N of them are ready, or after 3N issues. Checking further ahead is waste and goes stale before the run gets there (standard: findings/backlog-ready-depth, checked 2026-11-18).

Skip an issue whose newest `Readiness:` comment is newer than its last change (a same-evening check by the `-ReadyOnly` pass), and count it as it was found.

## Ready means

An issue is ready when all of these hold:

1. No open blocker (`next_task.py` only lists unblocked issues, so this holds for each issue it prints).
2. Its finish is checkable: a test, a command, a file, a number. If not, write one into the issue body; that is an agent's job, not the user's.
3. Everything its finish needs is on the machine or can be had by the run without the user: tools, packages, data files, models, Docker images, a Kaggle dataset or runner, a design brief. Overnight rules allow free downloads that fit on disk (`SKILL.md`, step 4). List the tools each issue needs and sort them (user's decision, 2026-11-19, after a winget install raised a Windows admin prompt at 00:55 that nobody was awake to answer): an install that needs admin or elevation (a machine-wide installer, writing under Program Files, any UAC prompt) is done with the user present, or the issue leaves that night's queue and becomes a `needs-you` item; a per-user or unattended install (pip or uv into the project env, `ollama pull`, an official Docker image, winget with a per-user scope) is fine overnight.
4. No open decision that only the user can make.

## For each issue read

- **Ready:** comment `Readiness: ready.` and count it.
- **A prerequisite an agent can supply** (a download, a data upload to Kaggle, a runner, a script, a design brief, a missing finish line): file it as its own issue with a checkable finish and the issue's `priority:`, `resume:` and `gap:` labels, link it as blocking (`gh issue edit` or the GraphQL `addSubIssue`/dependency API the repo uses; a "Blocked by #n" line in the body alone is invisible to `next_task.py`), and count the issue as ready, since the run will do both. Search for an existing issue first (`gh issue list --search`).
- **A prerequisite only the user can supply** (a decision, a sign-in or credential, money, hardware the machine lacks): add `needs-you` with the user as assignee and a comment in the form of `SKILL.md` step 4 (what is blocked, the exact action, the time it takes, what happens if nothing is done; a paid step names an estimated cost). Do not count it.

Every comment ends with the session ID. In a public repository no private detail goes into an issue or comment ("private item; ask in chat").

## Never

Do the prerequisite work itself (the run does it, ranked by `next_task.py`); change `priority:` or `resume:` labels on existing issues; read credential files; or file a `needs-you` item for an issue below the depth.

## Report (at most 10 lines)

The depth N and how it was set, the rank of the last issue read, the count ready, the blocking issues filed (numbers), and the `needs-you` items (numbers, one line each with the action). The overnight run copies the depth and the last rank read into the morning summary, and the summary adds the deepest rank the night actually reached, so the depth can be tuned.
