# Does a Claude Code session or loop resume by itself after a usage limit resets?

- **Question:** When a long-running interactive Claude Code session or a self-paced `/loop` hits the subscription usage limit overnight, does it resume on its own at the reset, and can this be tested without using up the quota?

- **Finding:**
  - **A built-in auto-continue exists but is unreliable.** From about Claude Code 2.1.234, an interactive session signed in with a claude.ai subscription waits in-process at a limit and sends a fixed continuation prompt at the reset. It is a `/config` toggle ("Continue automatically at usage limit"), on by default, and is not offered in `-p` runs, background sessions or API-key use. One guide says it does not start when the reset is more than 24 hours away, so it is unlikely to cover a weekly limit. These points come from a blog and issue reports; the official docs were not read (see Limits).
  - **Reported failures.** An issue reports a session with the toggle on that never retried after a five-hour reset and only moved when the user typed 8.5 hours later, with several sessions open. Another reports an overnight session that did resume with nobody present and silently used 66% of the next window. So both "does not resume" and "resumes and burns quota" are reported.
  - **Loops specifically.** No source says what a pending `ScheduleWakeup` does when it fires into a live limit. An issue says a loop's wakeups can be listed and cancelled only through the model, so a loop cannot be stopped while the limit blocks inference. A feature request asks for suspend-and-auto-resume at the reset because a session at the limit simply ends.
  - **External workarounds in use:** a tmux wrapper that waits for the reset and types "continue"; a scheduled-resume script; a status line plus a `StopFailure` hook that wakes the same session.
  - **Testing it:** no way was found to test resume without actually exhausting the quota; the only safe test is to watch a real limit event. Checker's inference: arm an external or second-session check for just after the reset (a watchdog that reads the session's last activity and sends "continue" if it is idle with no wakeup pending), and keep usage credits off so a stall costs time, not money.

- **Evidence strength:** anecdotal (GitHub issue reports and blogs, some secondhand); official docs not confirmed.

- **Sources:**
  - Suspend and auto-resume at limit reset (issue #79127): https://github.com/anthropics/claude-code/issues/79127
  - Loop wakeups cannot be stopped while rate-limited (issue #85292): https://github.com/anthropics/claude-code/issues/85292
  - Auto-continue disabled after five-hour reset with multiple sessions (issue #92418): https://github.com/anthropics/claude-code/issues/92418
  - Auto-resume after reset consumes session time silently (issue #92319): https://github.com/anthropics/claude-code/issues/92319
  - Auto-resume tasks after rate-limit reset (issue #26775): https://github.com/anthropics/claude-code/issues/26775
  - Usage limits, weekly limit, 5-hour window (blog): https://dev.to/alexcloudstar/claude-code-usage-limits-how-the-weekly-limit-5-hour-window-and-reset-times-work-2hp8
  - Auto-resume at usage limit reset (blog): https://www.getclaudeskills.com/blog/claude-code-auto-resume-usage-limit
  - Rate limits and fixes (guide, source of the `-p`/background exclusions): https://claudcod.com/blog/claude-code-rate-limits/

- **Limits:** Two web searches; summaries only. Issue status (open, closed, fixed) was not checked, the 2.1.234 changelog entry and the official docs page were not read, and the 24-hour claim is from one guide. Nothing covers a wakeup pending at the limit.

- **Checked:** 2026-11-14
