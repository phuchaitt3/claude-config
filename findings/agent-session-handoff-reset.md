# A session that hands over to its own successor (context reset)

- **Question:** Is it a standard approach for a long-running agent to end its session and start a fresh one with a written handoff, rather than clear or compact in place? Is it triggered by a context-size threshold, and can an agent chain successors itself?

- **Finding:**
  - **Reset with a handoff is the documented pattern; the trigger is not a number.** Anthropic's long-running harness post runs each session in a new context window and carries continuity in files: a feature list with pass/fail state, a progress log and git history. Each new session reads them first. The post says compaction alone "isn't sufficient" (official engineering post; already in `findings/long-agent-run-context`). Secondary write-ups describe the same split: compaction shortens the context, a reset builds a new one, and external state keeps the checkable facts; they complement each other (practitioner posts, search summaries only).
  - **No source gives a token threshold for resetting.** Searches found only general statements (reset or compact when the window is used up). A threshold such as "about 120K tokens" is therefore the checker's own choice, to be tuned from transcripts; it is not a standard figure.
  - **Reset points are task boundaries in the sources.** The harness resets after one feature is finished and committed, not at a size. Mid-task resets rely on the progress file alone, which the post flags as lossy.
  - **An agent starting its own successor was not found as a described pattern.** The documented outer loop is a script or supervisor that starts the next session (the Ralph loop, a harness driver). Self-chaining (a session launches the next one, then stops) is the checker's inference. Its added risks are two loop sessions overlapping, and a successor that fails to start while the old one has already stopped; both need a check in the handoff step.

- **Evidence strength:** *vendor or single source* for the reset-with-handoff pattern (one Anthropic post, plus secondary summaries of it). *No data found* for a size threshold or for self-chained successors.

- **Sources:**
  - Effective harnesses for long-running agents (Anthropic engineering post): https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
  - Compaction is a lossy handoff (community post, search summary only): https://dev.to/tridaai/compaction-is-a-lossy-handoff-1omi
  - Amp retires compaction for a cleaner handoff (news summary, search summary only): https://tessl.io/blog/amp-retires-compaction-for-a-cleaner-handoff-in-the-coding-agent-context-race
  - When to clear the context instead of compacting it (practitioner post, search summary only): https://www.realaization.com/blog/when-to-clear-the-context-instead-of-compacting-it

- **Limits:** The Anthropic page appeared in this search only as a title and introduction; its content here rests on the earlier, fuller read in `findings/long-agent-run-context`. The other sources were seen as search summaries. No measurement of tokens per finished task for reset against no reset.

- **Checked:** 2026-11-14
