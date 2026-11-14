# How much a worker agent does, and how the coordinator checks it

- **Question:** In an orchestrator and worker setup for coding, is it standard for the worker to do the whole task (tests, commit, push, open the PR) while the coordinator reads only a short report? What checking of the worker's result is standard?

- **Finding:**
  - **Thin coordinator is the common design.** Sources on the orchestrator-worker pattern say the worker does the heavy reading and returns a compact summary or writes its full output to a file; if the coordinator re-reads full worker output, the isolation, and its benefit, is lost (vendor and practitioner posts). This agrees with the Claude Code docs on subagents (see `findings/long-agent-run-context`).
  - **Workers doing the whole path to a pull request is described, thinly.** Pipelines are described in which developer agents work on isolated branches, deterministic steps run the full tests, and the pull request is opened afterwards, with a human reviewing the PR (cloud vendor and product docs). No source describes exactly "worker commits and opens the PR, coordinator reads only the report"; that combination is an inference from the pattern.
  - **Checking the worker is standard, and it is not done by trusting the report.** Several designs treat a worker's "done" as a trigger for checking: a separate reviewer re-reads the spec, inspects the diff and runs the tests, or the coordinator compares the diff with the expected scope and merges only verified results (vendor and open-source write-ups). The check is cheap and mechanical where it can be: CI status, a diff size and file list, the exit codes of tests. No measurement of how often workers report success falsely was found; the designs assume it.
  - **The check needs to be independent of the worker's own account.** A reviewed pull request in one project found a "worker started" check that always returned true; verification code has its own bugs (single community example).
  - **Checker's inference for a loop that keeps the coordinator thin:** let the worker run lint and tests, commit, push and open the PR, and have it report a few lines (PR link, files changed, check results, open questions). The coordinator then verifies from sources that are small and not written by the worker: `gh pr checks`, `gh pr diff --stat`, the PR body's closing-issue line. A full read of the diff stays with whoever the project's review mode names (a second worker, or the coordinator when the diff is small). Skipping the diff read trades review depth for context, so it fits low-risk paths and not paths the project reserves for the user.

- **Evidence strength:** *common practice* for a thin coordinator and for independent verification of worker output (several reputable vendor and practitioner sources agree). *Vendor or single source* for workers opening the PR. *No data found* on false completion reports.

- **Sources:**
  - One agent thinks, many agents work: a better pattern for coding agents (community post): https://hackernoon.com/one-agent-thinks-many-agents-work-a-better-pattern-for-coding-agents
  - Orchestrator-workers pattern (vendor blog): https://vantaige.io/blog/orchestrator-workers-multi-agent-pattern-2026
  - Autonomous epic delivery with orchestrator-worker agents (cloud vendor builder post): https://builder.aws.com/content/3HpOSrEaFd2KMqEERg0aXUU156q/autonomous-epic-delivery-with-orchestrator-worker-agents
  - Multi-agent verification (vendor blog): https://zencoder.ai/blog/multi-agent-verification-the-new-standard-for-ai-code-quality
  - Persistent dev orchestrator, zero-trust verification of reports (vendor guide): https://claudemarket.ai/blog/openclaw-persistent-dev-orchestrator-guide
  - Implement a verify-fix loop in multi-agent systems (vendor blog): https://www.mindstudio.ai/blog/implement-verify-fix-loop-multi-agent-ai-systems

- **Limits:** All sources were seen as search summaries, and nearly all are vendor or practitioner posts, not studies. The one academic-style preprint found (arXiv 2605.25233, validation gates between agents) was not read. Nothing measured tokens or review quality for "worker opens the PR" against "coordinator opens it".

- **Checked:** 2026-11-14
