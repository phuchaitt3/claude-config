---
topic: claude-code-host-without-ide
area: Agent setup
question: When no IDE is needed, where is the best place to run Claude Code chats (VS Code terminal, Windows Terminal, plain console, background session, desktop app), and how is a running chat moved to another terminal? (Separate from the background-session and clipboard entries, which cover behaviour inside one host.)
checked: 2026-11-28
review_months: 6
status: current
---
# Claude Code without an IDE: where to run it, and moving a running chat

**Question:** With no code editing in VS Code, should chats be moved out of it to save RAM, where to, and how?

**Finding:**

- **Terms:** the terminal app (VS Code panel, Windows Terminal, the classic console) draws the window; the shell (PowerShell) runs commands; Claude Code is a program started from the shell. "CLI or PowerShell" is not a choice: the CLI runs inside PowerShell.
- **Official docs:** they name no preferred Windows terminal. Supported shells include PowerShell and CMD; Git for Windows is recommended so the Bash tool exists. Windows Terminal 1.25 or later takes Shift+Enter without setup; older ones use Ctrl+J. No page read compares memory use of terminal, IDE and desktop app.
- **Moving a chat:** history is on disk, so exit it (`/exit`, or Ctrl+D twice) and run `claude --resume <session id>` in the other terminal (`claude agents --json` lists the IDs). Exit first: resuming a still-running session attaches to it or conflicts instead of moving it. Launch flags are not restored, and a command still running at exit is not rerun (findings/claude-code-resume-remote-control). `/desktop` moves a CLI session into the desktop app (x64 Windows and macOS, subscription login).
- **Background sessions (`/bg`)** keep running with no terminal open and survive sleep, not shutdown; an idle unattached one has its process stopped after about an hour. Reopen with `claude attach <id>`. They always render fullscreen and one machine saw scrolling trouble in them (findings/claude-code-background-vs-foreground-session).
- **Memory, observed (the desktop PC, 16 GB, 2026-11-28, v2.1.332, Windows 10; the laptop was not measured):** with three idle or light chats in VS Code terminals, the 14 `Code.exe` processes held about 2.3 GB private memory; the three `claude.exe` processes about 1.5 GB (330 to 370 MB resident each). Moving the chats keeps the `claude` cost and removes the editor's.
- **Memory, other terminals:** a 2024 Windows 10 benchmark measured 6.5 MB private at start-up for the classic console host against 74 MB for Windows Terminal; both are small next to the editor. User reports of Windows Terminal above 1 GB exist, cause not established.
- **Desktop app:** user reports on the issue tracker describe several hundred MB to over 1 GB for the app itself, and more with its virtual machine; no official or controlled comparison was found.
- **(inference: findings/claude-code-host-without-ide)** To save RAM with no IDE need: foreground sessions in Windows Terminal (tabs, newer keys), or plain PowerShell windows if installing nothing. Use `/bg` only for a chat that should outlive its terminal. Not the desktop app for this purpose.

**Evidence strength:** official vendor docs for the commands and terminal notes; one observation for memory with VS Code; one third-party benchmark and anecdotal reports for the rest. No established team practice was found.

**Sources:**

- [Agent view](https://code.claude.com/docs/en/agent-view), [Terminal configuration](https://code.claude.com/docs/en/terminal-config), [Advanced setup](https://code.claude.com/docs/en/getting-started), [Desktop application](https://code.claude.com/docs/en/desktop) (official docs, read 2026-11-28 through a fetch subagent)
- [Terminal latency on Windows](https://chadaustin.me/2024/02/windows-terminal-latency/) (third-party benchmark, 2024; search summary only)
- [claude-code issue 40633](https://github.com/anthropics/claude-code/issues/40633), [issue 96299](https://github.com/anthropics/claude-code/issues/96299) (user reports; search summary only)

**Limits:** the saving after closing VS Code was not measured, only what VS Code held before; private memory is not all returned as free RAM. VS Code's figure depends on its extensions and open windows. The move was not tested end to end from VS Code to Windows Terminal. Agent view is a research preview.

**Checked:** 2026-11-28
