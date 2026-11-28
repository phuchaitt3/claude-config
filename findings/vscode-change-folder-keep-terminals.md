---
topic: vscode-change-folder-keep-terminals
area: Agent setup
question: Can one VS Code window switch to another repository while its integrated terminals, with Claude Code chats running in them, stay alive? (Separate from claude-code-host-without-ide, which is about moving chats out of the editor.)
checked: 2026-11-28
review_months: 6
status: current
---
# Changing the folder of a VS Code window without losing its terminals

**Question:** Can the open folder be swapped for another repository while the running terminals stay?

**Finding:**

- **The chat itself:** `/cd <path>` moves a running Claude Code session to another directory, keeping the conversation and loading that directory's `CLAUDE.md` and project settings. It does not change what the editor shows.
- **Editor, adding a folder:** File > Add Folder to Workspace shows a second folder in the same window; from a single-folder window this creates an untitled multi-root workspace. A folder can later be removed with Remove Folder from Workspace.
- **Terminals:** the pages read do not say whether terminals survive adding the first extra folder, removing the first folder, or File > Open Folder.
- **(inference: findings/vscode-change-folder-keep-terminals)** Adding the new repository as a second folder is the option to try for keeping one window; test it first in a spare window with a running terminal command.

**Evidence strength:** official vendor docs for the commands and workspace behaviour; nothing, official or tested, on terminal survival.

**Sources:**

- [Claude Code commands](https://code.claude.com/docs/en/commands), [permissions](https://code.claude.com/docs/en/permissions) (official docs, read 2026-11-28 through a fetch subagent)
- [Multi-root workspaces](https://code.visualstudio.com/docs/editing/workspaces/multi-root-workspaces), [Workspaces](https://code.visualstudio.com/docs/editing/workspaces/workspaces), [Terminal basics](https://code.visualstudio.com/docs/terminal/basics) (official docs, read 2026-11-28 through a fetch subagent; the last one only partly verbatim)

**Limits:** nothing was tested. The terminal advanced page, which covers persistent sessions, failed to load.

**Checked:** 2026-11-28
