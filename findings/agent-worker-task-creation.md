# Whether a worker agent may create new tasks for itself or others

- **Question:** In an orchestrator and worker setup, is it standard for a worker (or the whole loop) to file new tasks, or does only the coordinator create work? What goes wrong when workers spawn work?

- **Finding:**
  - **The usual design: the coordinator (planner) makes and assigns tasks; workers do the task they were given.** Cursor's write-ups on long-running agent fleets describe a planner that "does no coding itself" and hands out targeted tasks. Their first design, agents of equal status coordinating through a shared file, made agents risk-averse: they avoided hard tasks and made small safe changes, and a planner/worker hierarchy fixed it (vendor posts). An AWS write-up has the orchestrator read the backlog, dispatch ready slices, and read only each worker's one-line result such as merge-ready or blocked (vendor post).
  - **A loop that files its own work exists, at the coordinator level.** One practitioner runs a self-scan pass (stale TODOs, uncovered code, flaky tests) whenever the queue is empty and warns that priority scoring needs a staleness term (single practitioner post). Guides for continuous task loops say to set an iteration cap and a token budget, because a backlog that never empties runs forever (practitioner guide).
  - **Workers spawning workers is a known cost hazard.** Claude Code issue reports say subagents have not been able to start subagents; a report says release 2.1.172 allows nesting up to 5 levels for some agent types, and another that general-purpose subagents still cannot (conflicting; not settled from the official docs). Separate bug reports describe unbounded recursive spawning, one with "3 requested, 24 ran, 80% of tokens wasted". The workaround reported is a custom agent whose tool list omits the Agent tool (user reports in a bug tracker, not official).
  - **Not found:** a source on a worker filing follow-up issues itself. The nearest pattern is the worker reporting open questions to the coordinator, who decides what becomes a task.
  - **Checker's inference:** keeping task creation in the loop chat (self-drive's "New issues", with duplicate search, priority label and checkable finish) and workers to one given issue, reporting open questions, matches the common design and avoids the recursion hazard. A worker should not get permission to file issues or spawn agents without a stated cap.

- **Evidence strength:** *common practice* for planner-creates and worker-executes, and for caps (several independent vendor and practitioner posts agree). *Anecdotal* for the self-scan pass. *Bug reports, not official* for the nesting limits and the recursion cost. Based on search result summaries; the pages were not read in full.

- **Sources:**
  - Scaling agents (Cursor blog): https://cursor.com/blog/scaling-agents
  - Self-driving codebases (Cursor blog): https://cursor.com/blog/self-driving-codebases
  - Autonomous epic delivery with orchestrator-worker agents (AWS Builder Center): https://builder.aws.com/content/3HpOSrEaFd2KMqEERg0aXUU156q/autonomous-epic-delivery-with-orchestrator-worker-agents
  - Continuous autonomous task loop (agentpatterns.ai): https://agentpatterns.ai/workflows/continuous-autonomous-task-loop/
  - How I taught my autonomous coding agent what to work on next (DEV Community): https://dev.to/yureki_lab/how-i-taught-my-autonomous-coding-agent-what-to-work-on-next-2dod
  - Sub-agents cannot spawn other sub-agents (Claude Code issue 61993): https://claudeissues.com/issue/61993-sub-agents-cannot-spawn-other-sub-agents-task-agent-primitive-not-exposed-in-nes
  - General-purpose subagents recursively spawn: 3 requested, 24 ran (Claude Code issue 82565): https://claudeissues.com/issue/82565-general-purpose-subagents-recursively-spawn-3-requested-24-ran-80-of-tokens-wast

- **Checked:** 2026-11-14.
