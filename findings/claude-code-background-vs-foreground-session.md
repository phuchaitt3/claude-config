---
topic: claude-code-background-vs-foreground-session
area: Agent setup
question: Why does a Claude Code chat open in fullscreen (no terminal scrollback) although the tui setting says default, how does a chat become a background session without the user asking for it, and how is a foreground session started again?
checked: 2026-11-25
review_months: 6
status: current
---
# Claude Code: background sessions force fullscreen, and how to get a foreground session

- **Question:** Why does a chat open in fullscreen although `tui` is `default`, how does it become a background session, and how is a foreground session started again?
- **Finding:**
  - *Why fullscreen (docs).* "Attached sessions always render in fullscreen mode, regardless of your `tui` setting, because a background session has no terminal scrollback to append to." `CLAUDE_CODE_DISABLE_ALTERNATE_SCREEN` does not apply to them either. So `/tui default` cannot fix an attached background session; only a foreground session uses the setting.
  - *How a chat becomes a background session (docs):* `←` on an empty prompt (sends the open foreground session to the background and opens agent view); `/bg`; `claude --bg`; a prompt typed inside agent view (`claude agents`) starts a new background session.
  - *Also observed (v2.1.332, Windows, one machine):* a foreground chat that used `/resume` to open a chat running in the background was itself moved to the background. `~/.claude/daemon.log` records the source of each background session: `slash` (backgrounded from an open chat), `fleet` (agent view), `shell` (`--bg`), `spare` (pre-started). The meaning of these labels is inferred from matching log times, not documented.
  - *Getting a foreground session:* run `claude` in the shell, not in agent view. To keep an existing conversation, `claude stop <id>` (the short ID) in the shell, then `claude --resume <full session id>`: CLI help for `stop` says "`claude --resume` works once it is stopped". While it runs, `--resume` attaches to it instead. Whether the resumed chat then draws in the classic renderer is untested here.
  - *Safe listing:* `claude agents --json` lists sessions without opening agent view. `"kind"` tells background from foreground.
  - *Prevention:* the `leftArrowOpensAgents` setting (in `/config`, default on) turns off the `←` shortcut for foreground sessions; `defaultToAgentsView` controls whether bare `claude` opens agent view; `disableAgentView` (or `CLAUDE_CODE_DISABLE_AGENT_VIEW`) turns off background sessions and agent view entirely.
  - *Wheel walks the prompt history in fullscreen:* not explained in the docs. Wheel scrolling there needs the terminal to forward mouse events; a terminal that sends arrow keys instead would recall history (inference: findings/claude-code-background-vs-foreground-session). Scroll keys: findings/claude-code-vscode-terminal-clipboard-keys, "Scrolling in fullscreen rendering".
- **Evidence strength:** *official standard* for the fullscreen rule, the `←` shortcut and the settings; *anecdotal* for the `/resume` case and the log labels (one machine, one day).
- **Sources:**
  - Claude Code docs, agent view: https://code.claude.com/docs/en/agent-view (official docs)
  - Claude Code docs, fullscreen rendering: https://code.claude.com/docs/en/fullscreen (official docs)
  - `claude --help`, v2.1.332 (installed CLI)
- **Limits:** Read through a fetch subagent: the first 40,000 characters of the agent-view page verbatim, most of the rest as a summary (`disableAgentView`, `--bg` details), its last 6,500 characters not at all. The stop-then-resume result is untested. Shortcuts change between releases.
- **Checked:** 2026-11-25
