---
topic: claude-code-resume-remote-control
area: Agent setup
question: Does `claude --resume` / `--continue` work for a Claude Code chat that ran with Remote Control, and is the remote link restored?
checked: 2026-11-23
review_months: 6
status: current
---

# Resuming a Claude Code chat that used Remote Control

- **Question:** Does `claude --resume` work for a chat started with Remote Control, and does the remote connection come back?
- **Finding:**
  - History: yes. A resumed session restores messages, tool calls and results; a tool call still running when the process ended is not rerun. The Remote Control page names `claude --continue` / `claude --resume` as the way to bring back a session started with `claude --remote-control` or `/remote-control`.
  - Remote link: the docs say "If Remote Control doesn't reconnect", see their troubleshooting section, so automatic reconnect is not guaranteed. Turn it on again with `/remote-control` (or `/rc`) in the session, `claude --remote-control` at launch, or always with `/config` "Enable Remote Control for all sessions" (`remoteControlAtStartup: true` in user settings; a `true` in project or local settings is ignored).
  - Folder: `--continue` and the picker look in the current folder and its git worktrees; `--resume <id>` works from any folder. Sessions from `claude -p`, the Agent SDK and `/loop` are left out of the picker and `--continue`.
  - Flags such as `--mcp-config`, `--plugin-dir`, `--add-dir`, `--settings` and tool allow/deny flags are not restored; pass them again.
  - Resuming in a second terminal while the first still has Remote Control on prints "Remote Control not started here"; run `/remote-control` there to move it.
  - Server mode (`claude remote-control --continue` / `--session-id`) brings sessions back for about four hours after the server stopped.
  - Remote Control needs a claude.ai login; not available on Bedrock, Vertex, Foundry, a custom `ANTHROPIC_BASE_URL`, or with Zero Data Retention.
- **Evidence strength:** official standard (the tool's own docs).
- **Sources:**
  - https://code.claude.com/docs/en/remote-control.md (official docs; "From an existing session", "Resume sessions after stopping the server", "Limitations")
  - https://code.claude.com/docs/en/sessions.md (official docs; "What a resumed session restores")
- **Limits:** the docs do not say whether `--remote-control` can be combined with `--resume`/`--continue` on one command line, whether auto-connect runs for a resumed conversation, or whether a resumed terminal chat keeps its old remote session or gets a new one. The CLI reference page was not read. Found by a documentation-guide subagent, not by running the commands.
- **Checked:** 2026-11-23
