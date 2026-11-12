# Stopping runaway agent processes and sharing one machine's resources

- **Question:** How do tools and teams stop shell commands started by AI coding agents from outliving their call (orphaned `find`, `grep`, `yes`), and how do they limit CPU and memory when several agents share one machine?

- **Finding:**
  - **The failure is common and documented.** Bug reports against coding agents describe a shell tool call that timed out or was stopped while its child kept running: an orphaned `grep` that reached about 20 GB of memory, 39 background `yes` processes pegging about 7 cores for 8 h 42 m, a stopped task whose `rm -rf` kept deleting for 20 minutes, and agent shells that survive the editor closing. The cause in each: killing the shell does not kill its children. On Windows this is the default, because child processes are not tied to their parent's lifetime.
  - **Fix 1, kill the tree, not the shell.** On Unix: start each command in its own session or process group, send SIGTERM, wait briefly, then SIGKILL the whole group. On Windows: put the shell and its descendants in a Job Object with `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`, so closing the last handle terminates every process in the job. A PostgreSQL patch proposal and several libraries use this and report children dying within about 100-200 ms. Caveats: the flag must be set explicitly, and a job that allows breakaway (`SILENT_BREAKAWAY_OK`, `CREATE_BREAKAWAY_FROM_JOB`) lets children escape.
  - **Fix 2, a timeout on every command.** Orchestrators force-kill the group when a deadline passes. Agents that have no timeout rely on the user pressing Ctrl-C. This matches the backstop pattern in `standards/keep-awake-long-jobs`: a timeout is a generous limit against hangs.
  - **Fix 3, resource ceilings as a second backstop.** A proposed mitigation for the 20 GB case is `ulimit -v` / `RLIMIT_AS` on the tool's children, so a runaway allocation dies by itself. On Linux, cgroup v2 gives memory caps and CPU bandwidth limits; guides suggest one parent cgroup per agent session and tighter child cgroups per tool call, with headroom above the average because tool calls spike.
  - **Fix 4, reaping and a watchdog.** Process-guard style tools scan for stray processes by name, age and CPU time and kill them; the agent session's teardown should reap what it started.
  - **Memory, not CPU, limits how many agents fit.** An academic study (AgentCgroup, Feb 2026) measured sandboxed coding agents at 2-4 GB peak memory each with low CPU, so memory runs out first. Its authors say plain cgroups handle bursty agent workloads poorly and propose an eBPF controller (29% lower P95 latency for high-priority work in their replays).
  - **Worktrees isolate files, not processes.** Parallel-agent guides say a worktree per agent does not isolate RAM, ports or the GPU. The practical advice is to serialize only the heavy steps (type-check, build, benchmark) and keep the rest parallel; one guide calls 5-7 concurrent agents comfortable on a modern laptop.
  - **The checker's own inference** (not stated by one source): a layered design fits a shared laptop: (1) per-command timeout, (2) tree kill through a Job Object or process group, (3) a lock for heavy jobs (see `standards/shared-gpu-one-machine`, `standards/heavy-job-scheduling`), (4) a periodic check for strays, (5) a guard that refuses a whole-drive search before it starts. Search itself should use the agent's indexed Glob/Grep tools or a scoped path, not `find /`.

- **Sources:**
  - Orphaned grep after a bash tool timeout, 20 GB RSS (issue report): https://claudeissues.com/issue/84647-bash-tool-timeout-does-not-kill-the-child-an-orphaned-grep-reached-20-gb-rss-and
  - Background jobs orphaned, 39 `yes` processes for 8 h 42 m (issue report): https://claudeissues.com/issue/93794-background-jobs-in-a-bash-tool-call-are-orphaned-not-reaped-39-yes-processes-peg
  - TaskStop does not kill the process tree (issue report): https://claudeissues.com/issue/85200-bug-taskstop-does-not-kill-the-process-tree-orphaned-rm-rf-c-deleted-user-data-f
  - Agent shell commands survive after the editor closes (forum report): https://forum.cursor.com/t/agent-shell-commands-survive-after-cursor-closes-leaving-orphaned-high-cpu-processes-in-wsl/161340
  - Stop is a process-tree operation (vendor blog): https://docs.connectonion.com/blog/stop-is-a-process-tree-operation
  - Why kill -9 is not enough for a runaway agent (article, secondary): https://groundy.com/articles/stopping-a-runaway-coding-agent-why-kill-9-is-not-enough/
  - Job Objects (Microsoft docs, archived copy): https://msdn.microsoft.com/library/ms684161(v=VS.85).aspx
  - Fix orphaned backend processes on Windows using Job Objects (PostgreSQL mailing list): https://hackorum.dev/topics/52587
  - AgentCgroup: OS resources of AI agents (arXiv preprint): https://arxiv.org/html/2602.09345v2
  - When worktrees share RAM (community post): https://dev.to/koenvg/when-worktrees-share-ram-gba
  - Parallel coding agents guide (vendor blog, secondary): https://superset.sh/blog/parallel-coding-agents-guide

- **Limits:** Most agent-side evidence is user-filed bug reports and blog posts, not controlled studies; counts of how often it happens are not available. The Microsoft Job Objects page is an old archived copy; current docs were not re-read. No source tested Git Bash (MSYS) on Windows specifically, so whether its `timeout` or `kill` reaches a native `find.exe` child is the checker's inference. Quota numbers (2 GB, 2 cores, 5-7 agents) come from guides, not benchmarks. The AgentCgroup study used Linux sandboxes, not a Windows laptop.

- **Checked:** 2026-11-12
