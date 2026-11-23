---
topic: sonnet-effort-medium-vs-high
area: Agent setup
question: For Sonnet 5.5 in Claude Code, when is high effort worth using over the default medium, according to the vendor and to community practice on Reddit?
checked: 2026-11-24
review_months: 6
status: current
---

# Sonnet 5.5: medium or high effort

- **Question:** When should a task run on Sonnet 5.5 at `high` instead of the default `medium`? (Separate from `agent-model-effort-selection`, which covers model choice and vendor defaults; this one adds Sonnet-specific community practice on Reddit.)
- **Finding:**
  - **Vendor (Claude Code model-config docs, read 2026-11-15; see `findings/agent-model-effort-selection`):** Sonnet 5.5 defaults to `medium`, which "fits day-to-day engineering work with a clear scope". `high` is for "work where verification matters or edge cases are likely". `max` "may show diminishing returns and is prone to overthinking". Anthropic calls effort "a general preference rather than a task-by-task decision".
  - **Independent measurement already in `agent-model-effort-selection`:** on 4 small tasks in one repository, Sonnet 5.5 at `high` (14.3 s median API time) gained nothing over `medium` (single blog benchmark).
  - **Community practice (Reddit), *anecdotal*, read 2026-11-24** with the user's `webx` (official API search plus thread reads). About ten threads in r/ClaudeCode and r/ClaudeAI, Aug to Nov 2026; comment scores were not available, so nothing is weighted by votes; no usernames kept.
    - **"Medium is the ceiling" camp.** Two Sept 2026 threads in r/ClaudeCode, posted the day Sonnet 5.5 came out, argued Sonnet 5.5 is only worth it at low or medium, because Opus 5.5 at low or medium sits at a similar price. Replies: one poster put Sonnet High against Opus High on easy and medium tasks and found Sonnet faster and cheaper but with more bugs and missed items; having Opus review Sonnet's work cost more than Opus doing it alone. Others said Opus overthinks simple mechanical work and Sonnet does it faster and cheaper. Several replies pointed out the threads were written within hours of the release.
    - **"High is fine for implementation" camp.** An Oct 2026 post  (r/ClaudeCode) ran 25 real tasks (C++, Rust, GDScript) with Opus 5.5 medium and Sonnet 5.5 high as implementers, blind-graded by an Opus reviewer with one fix round allowed. Results were near equal (0.80 vs 0.96 fix rounds per task), so the poster switched to Sonnet high. A further 15 tasks on Sonnet medium produced about twice as many serious findings, so the poster judged medium "probably not worth it" for implementation. The poster says 25 tasks is too few for solid conclusions. A reply reported the opposite on their own work: three Sonnet 5.5 high handoffs kept failing a task that Opus 5.5 medium solved in one.
    - **Opus-for-hard-work split.** Replies in the second of those threads: Sonnet medium as the everyday workhorse, Opus low or medium for hard problems, higher Opus only when something is on fire; one commenter said they move a problem to Opus rather than push Sonnet to high, except when Sonnet already understands the repository and just needs to think harder without a model switch.
    - **A vendor-adjacent eval (Oct 2026, r/ClaudeCode)** by someone building a commercial agent-eval service (the poster says to weigh it accordingly): 8 real tasks from 5 codebases, graded by hidden tests. Sonnet 5.5 at low solved 88% at about $0.31 a run. Across models, `high` roughly doubled the lines changed (126 to 281 for solved runs), which means more to review. `max` did worse than `high` on the hardest bug.
    - **A daily-use thread  (Aug 2026, r/ClaudeAI, about Sonnet 5, not 5.5):** most replies use medium for nearly everything, with `high` for work needing full accuracy; one said medium handles about 90% of tasks; one reply said to use the default because defaults are not arbitrary.
  - **Pattern across them (inference: findings/sonnet-effort-medium-vs-high):** nobody argues for `max` on Sonnet; the disagreement is only `medium` against `high`. People who build and review code in a pipeline with a fix round (so mistakes are caught) report `high` roughly matching a more expensive model and `medium` leaving more serious findings; people doing quick or mechanical work report `medium` or even `low` as enough. None of the threads measured the cost difference between `medium` and `high` on Sonnet directly.
  - **Rule of thumb (inference: findings/sonnet-effort-medium-vs-high):** `medium` for mechanical, well-scoped edits (rename, format, copy a pattern, run a known command); `high` when the output is a quality-sensitive artifact that other work builds on (a benchmark or test set, a design brief, a reviewed implementation of non-trivial logic) or when a missed edge case is expensive to find later; neither `max`. This matches the vendor's "verification matters or edge cases are likely".
- **Evidence strength:** *vendor docs* for defaults and the `high` guidance. *Anecdotal* for everything from Reddit; the threads disagree, the samples are small and mostly self-run (25 tasks, 8 tasks), and two of the main ones were written on release day.
- **Sources:**
  - https://code.claude.com/docs/en/model-config.md (official docs, via `findings/agent-model-effort-selection`)
  - https://www.reddit.com/r/ClaudeCode/comments/1wsqfzk/(2026-09-28)
  - https://www.reddit.com/r/ClaudeCode/comments/1wsso74/ (2026-09-28)
  - https://www.reddit.com/r/ClaudeCode/comments/1x7a5v9/ (2026-10-16, 25-task implementer test)
  - https://www.reddit.com/r/ClaudeCode/comments/1xjl3dv/ (2026-10-30, 8-task eval, commercial interest disclosed)
  - https://www.reddit.com/r/ClaudeCode/comments/1wss302/ (2026-09-28, subagent workers)
  - https://www.reddit.com/r/ClaudeAI/comments/1vwdbhy/ (2026-08-23, Sonnet 5, daily use)
- **Limits:** only six of about thirty matching threads were read in full; comment scores were not available; the largest thread by listed comments (Nov 2026, medium, high and max, mixed models) was not read; the search API's comment counts looked unreliable (a thread with many replies was listed with 0), so none are quoted. Model behaviour changes with each release, hence the 6-month review. No source measures the cost of `high` against `medium` on Sonnet 5.5 for the same task set.
- **Checked:** 2026-11-24
