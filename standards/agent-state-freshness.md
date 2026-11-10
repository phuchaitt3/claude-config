# When an agent re-checks external state

- **Question:** When should a long-running agent re-check state that others can change (a PR's status, a file, a branch): on every step, at the end of each turn, on a timer, or just before it acts on it?
- **Checked:** 2026-11-11

## Finding

- **Check at the point of use, not on a schedule.** Practitioner guidance for coding agents puts the check right before a consequential action: a write, a patch, a PR, a merge. Its wording is "re-read immediately before the write", and the check is "mandatory" for side effects. A fingerprint (a version, a commit, a digest) taken at read time and compared before acting turns the check into one cheap call.
- **Refreshing everything on every step is called a mistake.** It "burns tokens, slows the run, and teaches teams to disable the check when deadlines hit." Checks should be cheap and targeted at the state the next action depends on.
- **Cached state expires.** Each piece of external state carries a TTL (one source suggests 5 to 15 minutes for an active repository, and different TTLs for stable and volatile data). After the TTL, the agent re-fetches before acting on it.
- **Events beat polling** where the platform offers them.
- **Databases settled the same question long ago.** Optimistic concurrency folds the check into the write (version or ETag conditions, Redis WATCH): a separate check-then-act leaves a time-of-check to time-of-use gap.

The checker's inference, not from a source: a report to the user ("PR #n waits for your merge") is an action on state like a write. It is the place to re-check that one item, with one call, and nothing else needs refreshing. An end-of-turn hook that compares the whole state costs one command per turn, not per step. It adds no tokens unless something changed, so it does not slow the main work. It does catch the problem only after the reply is written, though, so it can flag a stale claim but cannot prevent it.

## Sources

- [Freshness guards for long-running AI coding agents](https://negiadventures.github.io/blog/freshness-guards-long-running-ai-coding-agents.html) (practitioner blog).
- [The stale world model problem in long-running agents](https://tianpan.co/blog/2026-04-10-stale-world-model-long-running-agents) (practitioner blog).
- [CORVUS: context optimization for LLM coding agents](https://www.alphaxiv.org/abs/2607.22711) (preprint; measures stale and redundant re-reads).
- [Optimistic concurrency control](https://en.wikipedia.org/wiki/Optimistic_concurrency_control) (encyclopedia); [PynamoDB optimistic locking](https://pynamodb.readthedocs.io/en/stable/optimistic_locking.html) (official docs).
- On Stop-hook cost: [Claude Code Stop hooks](https://amitkoth.com/claude-code-stop-hooks) (community post): a command hook costs no tokens and seconds of wall time, while an LLM-judged hook adds seconds per turn.

## Limits

No official vendor or standards-body guidance for AI agents was found; the agent-specific sources are blogs and one preprint. The TTL numbers are one author's suggestion. The Stop-hook cost figures are community claims, not measured here.
