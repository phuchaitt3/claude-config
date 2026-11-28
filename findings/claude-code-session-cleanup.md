---
topic: claude-code-session-cleanup
area: Agent setup
question: How are old or no longer needed Claude Code sessions ended and cleaned up, so that later sessions do not have to check them?
checked: 2026-11-28
review_months: 6
status: current
---
# Ending and cleaning up Claude Code sessions

**Question:** What is the documented or common way to end a session quickly and to clear old ones?

**Finding:**

- **Interactive session (official docs, read through a fetch tool):** Ctrl+D twice (the second within 800 ms) exits; Ctrl+C twice with nothing running also exits. The pages read do not say what happens to an interactive session's process when its terminal is closed or killed.
- **Orphaned processes are a reported problem (issue reports, anecdotal):** several reports, mostly on Windows with the VS Code integrated terminal or extension, say `claude` processes stay alive after the window, tab or panel is closed. The reported workaround is listing `claude` processes and ending the stale ones.
- **Background sessions (official docs):** `claude stop <id>` stops one; `claude rm <id>` removes it from the list and keeps the transcript (`claude --resume` still opens it). In agent view, Ctrl+X stops and a second Ctrl+X deletes, which also ends the process when the stop failed. A finished or idle background session left unattached for about an hour has its process stopped automatically (summarised, not verbatim). If the background service does not respond, `claude daemon stop --any --keep-workers` and then `claude agents` starts a fresh one (summarised).
- **Offline Remote Control sessions (official docs):** they appear in the session listing with status `offline`. No page read says how to remove them or that they expire.
- **Old data (official docs):** transcripts are kept 30 days by default (`cleanupPeriodDays`).
- **Observed on one machine (2026-11-28, one case):** two interactive sessions the user had meant to close with the VS Code terminal's Kill button were still running about a day later, and their shell processes were also still alive, so the kill had not reached them. Cause not established.
- **(inference: findings/claude-code-session-cleanup)** The quickest reliable habit is to exit from inside the session (Ctrl+D twice) before closing its terminal, because the exit does not depend on the editor ending the process. A live-process listing (`claude agents --json`) is the check; offline listing entries cost a few lines of context and need no action.

**Evidence strength:** official vendor docs for the commands; anecdotal for orphaned processes; one observation for the editor case. No source describes an established team practice for session hygiene.

**Sources:**

- [Interactive mode](https://code.claude.com/docs/en/interactive-mode), [Sessions](https://code.claude.com/docs/en/sessions), [Agent view](https://code.claude.com/docs/en/agent-view), [Remote Control](https://code.claude.com/docs/en/remote-control), [Cross-session messaging](https://code.claude.com/docs/en/cross-session-messaging), [CLI reference](https://code.claude.com/docs/en/cli-reference) (official docs)
- Issue mirrors, seen in search results only: [process stays after terminal closes](https://claudeissues.com/issue/20596-bug), [VS Code extension does not reap child processes](https://claudeissues.com/issue/57557-vs-code-extension-does-not-reap-orphan-child-claude-processes), [leak when closing tabs (WSL2)](https://claudeissues.com/issue/26987-vs-code-extension-leaks-claude-processes-when-closing-tabs-panels-wsl2)

**Limits:** long pages were partly read as model summaries; the VS Code terminal page could not be read; the issue reports were not opened and their upstream numbers and status were not checked.

**Checked:** 2026-11-28
