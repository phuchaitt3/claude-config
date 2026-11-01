# Scheduling heavy test and benchmark jobs

- **Question:** How do teams run heavy tests and benchmarks without slowing the people working, and what scheduling tools exist for an agent on a laptop?
- **Checked:** 2026-11-01

## Finding

- Heavy benchmarks usually run on a nightly schedule (a cron trigger in CI), while pull requests get only quick checks. Examples: one graph-database project runs its "heavy" benchmark workflow at 02:00 UTC every night; a Python project template documents a nightly benchmark job that compares the latest main with the previous day; another project runs a daily performance regression test next to its pull-request triggers.
- The usual pattern around the nightly run: compare with the previous run or a stored baseline, and open an issue when a regression is flagged, checking first that one is not already open. Schedules in CI are written in UTC.
- Claude Code scheduling (official docs): `CronCreate` and `/loop` tasks are session-scoped and fire only while Claude Code is running and idle, in local time, up to 50 per session. Desktop scheduled tasks need the machine powered on. Cloud scheduled tasks (`/schedule`) run without the computer, but cannot reach a local machine. For unattended work the docs point to a GitHub Actions workflow with a `schedule` trigger.
- Windows Task Scheduler (official docs) can run a job on a local machine: `WakeToRun` wakes the computer from sleep; tasks do not start on battery by default (`DisallowStartIfOnBatteries`) and stop when the machine goes onto battery (`StopIfGoingOnBatteries`); an idle-triggered task is stopped when idleness ends unless `DontStopOnIdleEnd` is set; battery saver holds back idle-triggered tasks.
- Checker's inference (not stated by the sources): a job that needs a large local machine (more RAM or disk than a hosted CI runner, local models, Docker) cannot use a CI schedule or a cloud task, so on a laptop the choices are a Windows scheduled task with wake-to-run, or running the job when the owner says they are away.

## Sources

- [Nightly heavy benchmark workflow, 02:00 UTC with regression issues (example project, source)](https://docs.rs/crate/minigraf/0.19.0/source/.github/workflows/bench.yml) (community project).
- [Continuous integration benchmarking, nightly job (project template docs)](https://lincc-ppt.readthedocs.io/en/stable/practices/ci_benchmarking.html) (community docs).
- [Claude Code scheduled tasks](https://code.claude.com/docs/en/scheduled-tasks) (official docs).
- [Task Scheduler settings, wake and battery options](https://learn.microsoft.com/windows/win32/taskschd/tasksettings) and [idle conditions](https://learn.microsoft.com/en-ie/Windows/Win32/taskschd/task-idle-conditions) (official docs).

## Limits

No authoritative guide to "when to run heavy jobs"; the nightly pattern comes from example repositories, not a standard body. Third-party pages about Claude Code scheduling disagree with the official docs in places; the docs were used. The Task Scheduler interactions are described one setting at a time, so a setup should be tested on the target machine.
