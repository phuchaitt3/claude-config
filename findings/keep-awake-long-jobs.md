# Keeping a machine awake while long jobs run

- **Question:** How do people keep a laptop from sleeping while a long job (or an AI agent's job) runs, without guessing how long it takes, and how are processes that never end handled?

- **Finding:**
  - **Operating-system tools tie the hold to the job's process, with no time limit.** `systemd-inhibit` takes the lock before the command runs and releases it when the command ends. Its default `block` mode applies "without time limit". macOS `caffeinate -i <cmd>` holds while the command runs, and `caffeinate -w <pid>` holds until that process exits. Neither asks for an estimate of the job's length.
  - **Windows:** `SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)` holds until the same thread clears it. Microsoft's docs do not say what happens when the thread or process exits. Wine releases the hold on thread exit, and PowerToys Awake binds its hold to a process ID and exits when that process ends. No official source says the OS clears the hold when the holding process dies, but a local test confirmed it on Windows 11 (2026-11-11): a `pwsh` holder appeared under `SYSTEM` in `powercfg /requests`, and its entry was gone right after `Stop-Process -Force`.
  - **No API stops the user's own sleep.** Microsoft: the function "cannot be used to prevent the user from putting the computer to sleep", and applications should respect what the user expects when closing the lid. macOS guides likewise say an assertion cannot override sleep on lid close on battery.
  - **Keep-awake tools built for AI agents tie the hold to the agent's turn.** One Claude Code plugin (caffeinate-claude) starts `caffeinate` on `UserPromptSubmit` and stops it on `Stop`, with a 1-hour default timeout. Its opt-in session mode reference-counts sessions. agentawake writes a token per turn, and a reconcile loop every ~60 s removes tokens from dead turns, using a process-liveness check plus a max-age cap. In these tools the cap is a backstop for a release step that never fires (crash, interrupted turn), not an estimate of the job's length. A turn-scoped hold does not cover a background job that outlives the turn (the checker's inference from the designs described).
  - **Finite jobs and long-lived services are treated differently in CI and orchestration.** A Kubernetes Job may carry `activeDeadlineSeconds` and is marked failed when it runs past it. GitHub Actions jobs default to a 360-minute `timeout-minutes`, and guides advise setting explicit timeouts to catch hangs. Long-lived services (Kubernetes Deployments) have no run deadline and are handled by health checks instead (the checker's own knowledge; not in the search results). The pattern: a timeout is a generous backstop against hangs, set well above normal run time, and services are a separate kind with no run deadline.

- **Sources:**
  - systemd-inhibit(1) man page (official docs): https://www.freedesktop.org/software/systemd/man/systemd-inhibit.html
  - caffeinate(1) man page mirror (official man text): https://www.sudo.is/docs/macos/man_caffeinate.html
  - SetThreadExecutionState (Microsoft Learn, official docs): https://learn.microsoft.com/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate
  - Wine patch discussion on execution-state counting (project mailing list): https://www.winehq.org/pipermail/wine-devel/2019-August/149614.html
  - PowerToys Awake, process binding (third-party docs mirror): https://www.mintlify.com/microsoft/powertoys/utilities/awake
  - caffeinate-claude (community plugin README): https://github.com/bmoeskau/caffeinate-claude
  - agentawake (community tool README): https://github.com/meshulga/agentawake
  - Keeping a Mac awake for overnight agent runs (vendor blog): https://blog.openreplay.com/mac-awake-overnight-agent-runs-caffeinate/
  - GitHub Actions timeouts (training notes, secondary): https://notes.kodekloud.com/docs/GitHub-Actions/GitHub-Actions-Core-Concepts/Timeout-for-Jobs-and-Steps
  - Kubernetes Jobs and deadlines (vendor blog, secondary): https://plural.sh/blog/kubernetes-jobs

- **Limits:** No official source says whether Windows releases an execution-state hold when its process dies. A single local test on one Windows 11 machine confirmed that it does (a forced kill, not a crash inside the holder). The agent keep-awake tools are small community projects, read from their READMEs, not their code. Neither publishes its max-age value. The GitHub Actions and Kubernetes points come from secondary sources, and the jobs-versus-services split is the checker's synthesis.

- **Checked:** 2026-11-11
