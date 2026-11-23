---
topic: multi-device-agent-orchestration
area: Agent setup
question: Is it normal to run Claude Code agents on several devices (for example a laptop and a desktop PC), and what is the standard setup for the devices?
checked: 2026-11-23
review_months: 6
status: current
---

# Running Claude Code agents on several devices

**Question:** Is it normal to orchestrate Claude agents across more than one device, and what is the standard device setup?

**Finding:**

- **Normal, but as independent sessions per machine, not one orchestrator driving all.** No source describes a standard in which one controller schedules agents across devices. What the sources describe is each machine running its own Claude Code sessions, with git and the vendor's remote features linking them.
- **Official building blocks (vendor docs):**
  - Remote Control: a session runs on one machine, and claude.ai/code or the phone app is a window into it. "Your computer has to stay on and the `claude` process has to keep running." The local session makes outbound HTTPS requests only and opens no inbound ports. It needs a claude.ai sign-in (Pro, Max, Team, Enterprise); API keys, Bedrock, Vertex, Foundry and custom base URLs are not supported. `claude remote-control` runs a server with `--capacity <N>` concurrent sessions (default 32) and `--spawn worktree` gives each session its own git worktree (default `same-dir` lets sessions conflict).
  - Cross-session messaging: a session connected to Remote Control can list and message "your sessions on other machines" through Anthropic's servers (`ListAgents`, `SendMessage`, `/list-agents`). Needs Claude Code 2.1.224 or later (2.1.234 or later on native Windows; 2.1.225 or later to start a conversation with another machine's session) and a claude.ai sign-in. A message to an offline session arrives when that machine reconnects. Cloud sessions cannot reply by `SendMessage`; some messages are one-way; long reply chains can be cut off. WSL 2 and containers cannot reach a native Windows session on the same computer.
  - Agent teams (experimental): documented as one local setup. Teams and mailboxes are stored locally (`~/.claude/teams/...`), one team per session, a team cannot be shared across sessions. The page never mentions several machines. A feature request for cross-machine teams over a LAN exists, which suggests it is not built (inference from the request's existence).
- **Remote Control on for every session (`/config` "Enable Remote Control for all sessions", `remoteControlAtStartup`), checked 2026-11-23:**
  - Cost and security (official docs, as summarised by search): no inbound ports, outbound HTTPS only, short-lived scoped credentials. Each session allows one remote connection at a time; starting an ultraplan session disconnects Remote Control. Setting `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` or `CLAUDE_CODE_DISABLE_FEATURE_FLAGS` makes it unavailable. Team and Enterprise: off until an admin enables it. A session offline about 10 minutes times out and the process exits. Docs and third-party guides treat the session URL or QR code as an access key (one guide notes no two-factor on session links). The docs state no token or quota cost for having it on; none found.
  - Reliability (community issue reports, anecdotal, several filed 2026): the link can drop silently while the local terminal keeps running and need `/remote-control` again; auto-reconnect after a network break or long idle is reported not to work in some cases; one report of duplicate messages. A permission prompt appears on the host and can stall a session nobody is watching (a blog's advice: pre-approve permissions first). Docs and issues disagree on how reliable reconnect is.
  - The always-on setting gives no hidden fee found; its costs are the extra network connection per session, exposure of every session to your claude.ai account (a stolen login or leaked link reaches all of them), and unreliable reconnects. Weighing these for a personal setup is the checker's inference.
- **Common community setup (individual blogs, anecdotal):** each machine holds a full clone of a git repository of notes, rules or config; a session-end hook or timer commits and pushes; one place is the source of truth ("one home per fact"); secrets stay out of the synced repository. One author uses the desktop by day and the laptop at night rather than splitting tasks. A reader comment names merge conflicts from concurrent edits on two machines as the main risk.
- **Coordination between machines (inference, not found stated for two machines):** the single-machine multi-agent advice transfers: one task, one branch, one worktree, one session; a shared task list or explicit claims for who owns what; serialised merges. Sources on parallel agents (several blogs) say git isolates files but a task list or claims is needed for work allocation. Nothing found covers splitting tasks across two computers.

**Evidence strength:** vendor documentation for the Remote Control, messaging and agent-teams facts (official standard for the tool's own behaviour); anecdotal for the sync setup; no data found on how common multi-device setups are or on a standard device split (heavy jobs on the stronger machine is the checker's inference).

**Sources:**

- [Remote Control](https://code.claude.com/docs/en/remote-control.md) (official docs)
- Community issue reports on Remote Control reconnects: [no auto-reconnect after network interruption](https://claudeissues.com/issue/79388-remote-control-does-not-auto-reconnect-after-a-network-interruption), [silent drop, no recovery](https://claudeissues.com/issue/34255-bug-remote-control-automatic-reconnection-doesnt-work-connection-drops-silently), [stability issues](https://claudeissues.com/issue/33205-remote-control-multiple-stability-and-usability-issues-make-autonomous-use-unrel) (seen in search results only, not opened)
- [Cross-session messaging](https://code.claude.com/docs/en/cross-session-messaging.md) (official docs)
- [Agent teams](https://code.claude.com/docs/en/agent-teams.md) (official docs)
- [Feature request: distributed agent teams over a LAN](https://claudeissues.com/issue/79507-feature-distributed-agent-teams-coordinate-claude-code-instances-across-machines) (community issue, seen in search results only, not opened)
- [Keeping Claude Code context alive across a desktop, a laptop and a VPS](https://dev.to/fillip_kosorukov/keeping-claude-code-context-alive-across-a-desktop-a-laptop-and-a-vps-2epa) (individual blog)
- [How to run coding agents across machines](https://www.mindstudio.ai/blog/how-to-run-coding-agents-across-machines) (vendor blog for a third-party terminal tool that works over SSH; not independent, not Claude-specific; 2026-11-08)
- Git worktree guides for parallel agents on one machine (several blogs, seen in search results only)

**Limits:** the docs were read through a summarising fetch tool, so exact wording is partly paraphrase; the Remote Control "Limitations" section was summarised only. Remote Control and messaging are research-preview or fast-changing features. Nothing found on cost or quota use across devices, or on two machines sharing one repository at the same moment beyond the blog comment above.

**Checked:** 2026-11-23
