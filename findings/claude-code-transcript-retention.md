---
topic: claude-code-transcript-retention
area: Agent setup
question: How long does Claude Code keep session transcripts (the .jsonl files under ~/.claude/projects) before deleting them, and how is that changed?
checked: 2026-11-20
review_months: 6
status: current
---
# How long Claude Code keeps session transcripts

- **Question:** How long does Claude Code keep its session transcripts, and what does a tool that reads old transcripts (token or cost reports) have to do about it?

- **Finding:**
  - **Default 30 days (vendor docs as quoted by secondary sources, many issue reports).** At startup Claude Code deletes transcripts under `~/.claude/projects/` whose last modification is older than `cleanupPeriodDays` (default 30). The setting lives in `~/.claude/settings.json`. Anthropic is reported to have chosen 30 days for privacy, since transcripts can hold code and secrets.
  - **Raising it:** users set a large value (for example 3650). One issue reports deletions continuing at 36500, tied to reopening an editor, so a large value is not a guarantee. Behaviour of `0` is reported differently by different sources (a validation error, or no transcripts written at all); do not set it.
  - **Scope notes:** Desktop and Cowork session transcripts are kept at any age unless `desktopSessionCleanupPeriodDays` is set (Claude Code 2.1.248 or later); older versions delete them under `cleanupPeriodDays`. Deleting a transcript does not remove the sidebar's metadata for it.
  - **Consequence for tools:** anything computed later from old transcripts (tokens per run, calibration of the quota) has a 30-day horizon unless the figures are saved when they are produced.
  - **This machine (checker's own reading):** `~/.claude/settings.json` has no `cleanupPeriodDays`, so the default applies; the oldest transcript present on 2026-11-20 was dated 2026-10-27 (24 days old), consistent with the 30-day rule. Not verified by waiting for a deletion.

- **Evidence strength:** *common practice* on the default (many issue reports and write-ups agree); the official settings page itself was not read in this check, only quoted by secondary sources; *anecdotal* for the 36500 report and the behaviour of `0`.

- **Sources:**
  - Claude Code silently deletes conversation transcripts after 30 days by default (GitHub issue report): https://claudeissues.com/issue/62476-bug-claude-code-silently-deletes-conversation-transcripts-after-30-days-by-defau
  - Default 30-day auto cleanup deletes chat transcripts (GitHub issue report): https://claudeissues.com/issue/64999-default-30-day-auto-cleanup-silently-and-irreversibly-deletes-chat-transcripts-n
  - `cleanupPeriodDays: 0` disables transcript persistence (GitHub issue report): https://claudeissues.com/issue/23710-cleanupperioddays-0-silently-disables-all-transcript-persistence-docs-say-it-dis
  - Storage location and retention period investigated (blog): https://dev.classmethod.jp/en/articles/claude-code-conversation-history-retention/
  - Claude Code deletes conversation history after 30 days by default (trade press): https://itdaily.com/news/cloud/claude-code-deletes-conversation-history-after-30-days-by-default/
  - The .claude directory (official docs, scope of desktop transcripts): https://code.claude.com/docs/en/claude-directory

- **Limits:** The official settings reference was not read; the default comes from secondary sources and issue reports that agree with each other. Whether a version-specific change to the default happened after those reports was not checked.

- **Checked:** 2026-11-20
