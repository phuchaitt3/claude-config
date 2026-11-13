# Stopping an unattended agent loop after repeated failures

- **Question:** In an unattended agent loop, should "the same task fails twice" end the whole loop, or only that task? Is a low failure count a sound stop rule?

- **Finding:**
  - **Breaker on the same failure is standard; stopping everything is not the usual outcome.** Loop tools and write-ups use a circuit breaker that opens after N repeated failures or no-progress iterations: three is the common default (one Ralph implementation, one agent-patterns article), with profiles from 2 (conservative) to 5 (aggressive). Counting repeats of the same error type is preferred to a bare step count, because a step cap misses an agent that keeps failing the same way.
  - **What happens when it opens varies.** In Ralph-style loops, which work one goal, the loop exits. For a backlog of independent tasks, the pattern found is to skip the stuck task, record it, and go on; one skill lists "skip to next task, return later" or escalate. A research-agent guide says the same: three errors on one source, note it, move to the next, no retry loop. No source tested for a backlog loop whether stop-all or skip-and-continue yields more merged work; this is design advice, not measurement.
  - **Too tight is a failure too.** One source warns an aggressive breaker "becomes the failure mode". A threshold of 2 is the conservative end of the range found.
  - **Enforce it in the harness.** A Claude Code feature request notes that prompt rules like "stop after 3 failures" are not reliably self-enforced by the model.
  - **Checker's inference:** for an overnight backlog of independent issues, halting the whole loop on one task's second CI failure wastes the night; the cheaper design is to park that task (draft PR, note in the summary, no retry) and take the next eligible task, and stop the loop only when the same failure hits several tasks in a row (a sign the cause is shared, such as a broken CI or a bad dependency) or no task is left. Two consecutive different tasks failing is a reasonable "stop all" trigger.

- **Evidence strength:** common practice for the circuit-breaker pattern and the threshold range (several independent blogs and tool docs agree); anecdotal for skip-and-continue; no data found on which policy gets more work done.

- **Sources:**
  - Circuit breakers for agent loops (agentpatterns.ai): https://agentpatterns.ai/observability/circuit-breakers/
  - Loop detection for AI agents (agentpatterns.ai): https://www.agentpatterns.ai/observability/loop-detection/
  - Ralph for Claude Code, circuit breaker (community post): https://dev.to/tumf/ralph-claude-code-the-technology-to-stop-ai-agents-how-the-circuit-breaker-pattern-prevents-3di4
  - Ralph for Claude Code, smart exit detection and thresholds (blog): https://yuv.ai/blog/ralph-claude-code
  - Loop termination architecture (community post): https://dev.to/thebrierfox/loop-termination-architecture-how-production-agents-know-when-to-stop-3n5b
  - Native circuit breaker request (Claude Code issue report): https://claudeissues.com/issue/38405-feature-native-circuit-breaker-auto-stop-after-repeated-identical-failures
  - Circuit-breaker skill with "skip to next task, return later" (community skill): https://skills.sh/pixel-process-ug/superkit-agents/circuit-breaker

- **Limits:** Two web searches; search summaries only, pages not read in full. All sources are blogs, community tools or issue reports; none is a standards body, and none measures outcomes. Mostly single-goal loops, not backlog loops.

- **Checked:** 2026-11-14
