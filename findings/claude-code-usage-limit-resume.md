# Does a Claude Code session or loop resume by itself after a usage limit resets?

- **Question:** When a long-running interactive Claude Code session or a self-paced `/loop` hits the subscription usage limit overnight, does it resume on its own at the reset? Can an agent see how close it is to the limit and pause before it, and can resume be tested without using up the quota?

- **Finding:**
  - **Built-in auto-continue (official).** The hooks reference documents three `Notification` types, from v2.1.234: `quota_auto_resume_fired` (Claude Code continues the task after a claude.ai usage limit paused it, at the reset or sooner if usage becomes available), `quota_auto_resume_stale` (the limit reset while the computer slept for more than about 30 minutes; it then waits for `Enter` instead of continuing), and `quota_auto_resume_disabled` (the wait ends without continuing: `autoContinueAtUsageLimit` off, the reset moved more than 24 hours away during a wait it started itself, **the continued task kept hitting the limit**, or the continuation was blocked before reaching the model). `idle_prompt` does not fire during the wait. A third-party guide says the setting is on by default and re-arms at most twice in a row; the docs read do not state the default.
  - **Why a run can still stall (checker's inference from the official list).** Two documented causes fit an overnight loop: the machine sleeping more than 30 minutes during the wait (stale, waits for Enter), and repeated limit hits (disabled). A pending `ScheduleWakeup` or a background worker's report that fires into the live limit is a likely source of repeated hits; no source confirms that a wakeup counts as one.
  - **The agent can know its quota (official).** The status line script receives `rate_limits.five_hour.used_percentage` and `rate_limits.seven_day.used_percentage` (0 to 100) and `rate_limits.<window>.resets_at` (Unix seconds). The status line re-runs on events, when a window reaches `resets_at`, and every `refreshInterval` seconds if set; it can go quiet while a coordinator waits on background work unless `refreshInterval` is set. No hook input carries these fields, so the model sees them only if a status line script writes them somewhere a hook or the model reads.
  - **`StopFailure` hook (official):** fires when a turn ends on an API error, with matcher values including `rate_limit`; its output and exit code are ignored (apart from `terminalSequence`), so it can log or notify but cannot continue or wake the session.
  - **General API practice (official, Claude API):** responses carry remaining and reset headers (`anthropic-ratelimit-*-remaining`, `-reset`) and 429s may carry `retry-after`; clients wait that long, hold traffic where requests succeed, and spread scheduled or bulk jobs rather than retrying into the limit. Pausing on the provider's reset time instead of retrying into the wall is the standard pattern; it applies here by analogy, since subscription limits are a different mechanism.
  - **External workarounds in use (community):** a pty wrapper that parses the reset time and types "continue"; scheduled-resume shell scripts; a status line plus a `StopFailure` hook that wakes the same session.
  - **Testing it:** no way was found to test resume without exhausting the quota; only a real limit event shows it. Keep usage credits off so a stall costs time, not money.

- **Evidence strength:** official docs for the notification types, the status line `rate_limits` fields, `StopFailure` and API headers; vendor or single source for the setting's default and the "twice" re-arm count; anecdotal for the issue reports.

- **Sources:**
  - Hooks reference, `Notification` matchers `quota_auto_resume_*` and `StopFailure` (official docs): https://code.claude.com/docs/en/hooks
  - Status line, `rate_limits` fields and update triggers (official docs): https://code.claude.com/docs/en/statusline
  - Claude API rate limits, response headers and `retry-after` (official docs): https://platform.claude.com/docs/en/api/rate-limits
  - What's new 2026 week 33, desktop "Auto-continue when limits reset" (official digest): https://code.claude.com/docs/en/whats-new/2026-w33
  - Suspend and auto-resume at limit reset (issue #79127): https://github.com/anthropics/claude-code/issues/79127
  - Loop wakeups cannot be stopped while rate-limited (issue #85292): https://github.com/anthropics/claude-code/issues/85292
  - Auto-continue disabled after five-hour reset with multiple sessions (issue #92418): https://github.com/anthropics/claude-code/issues/92418
  - Auto-resume after reset consumes session time silently (issue #92319): https://github.com/anthropics/claude-code/issues/92319
  - Continue at usage limit, `autoContinueAtUsageLimit` default and re-arm count (blog): https://www.memorylake.ai/en/blogs/claude-code-continue-at-usage-limit
  - claude-auto-continue pty wrapper (community tool): https://github.com/oguztecimer/claude-auto-continue

- **Limits:** The `StopFailure` input schema was not read (truncated page). The setting's default and the re-arm count come from one blog. Nothing official says whether a loop wakeup or a background worker's report firing into the limit counts as a repeated hit. Background sessions' behaviour at the limit was not found in the docs.

- **Checked:** 2026-11-14 (re-checked the same day against the official hooks, status line and API pages)
