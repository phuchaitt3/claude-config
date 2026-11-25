---
topic: claude-code-vscode-terminal-clipboard-keys
area: Agent setup
question: In Claude Code running in the VS Code integrated terminal on Windows, what do Ctrl+A, Ctrl+X, Ctrl+C and Ctrl+V do, how are prompt text and output selected, cut, copied and pasted, and can these keys be remapped to the usual editor behaviour?
checked: 2026-11-22
review_months: 6
status: current
---

# Clipboard keys in Claude Code inside the VS Code terminal (Windows)

**Question:** select all, cut, copy and paste (Ctrl+A, Ctrl+X, Ctrl+C, Ctrl+V) in Claude Code's prompt in the VS Code integrated terminal on Windows.

**Finding:** Claude Code's prompt uses readline-style keys, not editor-style clipboard keys, so three of the four do something else.

| Key | In Claude Code's prompt | Source |
|---|---|---|
| Ctrl+A | Moves the cursor to the start of the current line. Not select-all; no select-all exists in the prompt. | Claude Code docs, interactive mode |
| Ctrl+X | Starts a two-key chord, not cut: Ctrl+X Ctrl+E opens the external editor, Ctrl+X Ctrl+K stops background subagents (twice within 3 s), Ctrl+X Ctrl+S sends queued messages. | Claude Code docs, interactive mode |
| Ctrl+C | Interrupts a running operation. When nothing runs, the first press clears the prompt and a second press exits; Up recovers the cleared draft. Ctrl+C is reserved and cannot be rebound in Claude Code. | Claude Code docs, interactive mode and keybindings |
| Ctrl+V | Claude Code binds it to image paste (`chat:imagePaste`); **on Windows and WSL image paste is Alt+V**. VS Code lists Ctrl+V as the terminal's paste on Windows, so text paste works. | Claude Code docs; VS Code terminal docs |

How to do the four actions instead:

- **Cut or clear text in the prompt:** Ctrl+U deletes from the cursor to the line start (repeat to clear across lines), Ctrl+K to the line end, Ctrl+W one word or path back; Ctrl+Y pastes the last deleted text and Alt+Y after it cycles older ones. These keys cannot be remapped (no keybinding actions exist for them). Esc Esc clears the whole draft and saves it to history. Ctrl+_ undoes the last edit. Whether Ctrl+Y's store is the system clipboard is not stated: Open.
- **Edit a long prompt with normal Ctrl+A/X/C/V:** Ctrl+G or Ctrl+X Ctrl+E opens the prompt in the external editor, but in the VS Code terminal VS Code takes both first; see "External editor" below.
- **Copy output:** in the VS Code terminal, select with the mouse; on Windows the default right-click "copies and drops the selection if there is one, otherwise pastes" (`terminal.integrated.rightClickBehavior`), and `terminal.integrated.copyOnSelection` copies on selection when enabled. With Claude Code's fullscreen rendering, its own `selection:copy` is Ctrl+Shift+C. The `/copy` command writes to the system clipboard (docs mention it for iTerm2 setup). Whether VS Code's Ctrl+C copies a selection on Windows instead of sending the interrupt is not stated in the VS Code docs page read: Open.
- **Select all terminal text:** VS Code's *Terminal: Select All* (`workbench.action.terminal.selectAll`) has no default key on Windows "as it may conflict with shell hotkeys"; the docs suggest `{"key": "ctrl+a", "command": "workbench.action.terminal.selectAll", "when": "terminalFocus && !isMac"}`. That selects the terminal buffer, not the prompt, and takes Ctrl+A away from Claude Code's line-start (inference: findings/claude-code-vscode-terminal-clipboard-keys).
- **Paste:** text with Ctrl+V or right-click; images with Alt+V. Pastes over 800 characters or three lines collapse to a `[Pasted text #1 +N lines]` placeholder but are sent in full. The VS Code terminal "can drop characters from very large pastes", so put very large text in a file.

Customising: `/keybindings` edits `~/.claude/keybindings.json` (reloads without restart); contexts include `Chat`, `Global`, `Scroll`, `Select`. Reserved, not rebindable: Ctrl+C, Ctrl+D, Ctrl+M, Ctrl+[, Ctrl+I, Ctrl+H.

**Remapping to editor-style keys (checked 2026-11-22):**

- **Inside Claude Code: not possible for these four.** `~/.claude/keybindings.json` maps a key to an *action* only (format `{"bindings": [{"context": "Chat", "bindings": {"ctrl+e": "chat:externalEditor", "ctrl+s": null}}]}`, `null` unbinds, hot-reloaded); it cannot make one key send another. The Chat context has no select-all, cut or copy action, the line-editing keys (Ctrl+A/E/K/U/W/Y) have no actions so cannot be moved, and Ctrl+C is reserved. Ctrl+L (`chat:clearInput`) only redraws the screen despite its name. Rebindable actions that help: `chat:externalEditor` (Ctrl+G, Ctrl+X Ctrl+E), `chat:undo` (Ctrl+_), `chat:imagePaste`. Source: Claude Code docs, keybindings.
- **In VS Code's `keybindings.json` (catches keys before the terminal):** Ctrl+A → `workbench.action.terminal.selectAll` with `"when": "terminalFocus && !isMac"` (VS Code docs) selects the terminal screen, not the prompt. Ctrl+C → `workbench.action.terminal.copySelection` with `"when": "terminalFocus && terminalProcessSupported && terminalTextSelected"` copies when text is selected and leaves Ctrl+C as interrupt otherwise (community: Stack Overflow answer, Cursor forum, a blog; not in VS Code's docs). A rule is disabled by repeating it with a leading `-` on the command. Neither gives a cut or select-all inside the prompt line.
- **Use the graphical panel instead of the terminal:** the Claude Code VS Code extension's panel is a normal prompt box where pasted text and images go in directly; `claudeCode.useTerminal` (default `false`) chooses terminal mode. The docs list what the panel lacks against the CLI: a subset of commands and skills, no `!` Bash shortcut, no Tab completion. That the panel's box takes the standard Ctrl+A/X/C/V is not stated in the page read: Open, though it is a VS Code text input (inference: findings/claude-code-vscode-terminal-clipboard-keys).
- **External editor for long prompts (corrected twice 2026-11-22):** Claude Code binds `chat:externalEditor` to Ctrl+G and Ctrl+X Ctrl+E, but **in the VS Code terminal neither reaches Claude Code**. Ctrl+G is VS Code's terminal command *Go to Recent Directory…* (`workbench.action.terminal.goToRecentDirectory`, a shell-integration quick pick), bound to Ctrl+G when the terminal has focus; checked in the installed VS Code's `workbench.desktop.main.js` (`keybinding:{primary:2085,when:<terminal focus>}`, 2085 = Ctrl+G), 2026-11-22. It is not Go to Line: removing `workbench.action.gotoLine` from `commandsToSkipShell` did not help (user test, 2026-11-22). Ctrl+X Ctrl+E fails too: VS Code takes Ctrl+E for its file search (Go to File; user observation, 2026-11-22).
  **Fix that targets the real binding:** remove VS Code's Ctrl+G terminal binding in VS Code's `keybindings.json` (Command Palette → *Preferences: Open Keyboard Shortcuts (JSON)*): `{"key": "ctrl+g", "command": "-workbench.action.terminal.goToRecentDirectory"}`, or in the Keyboard Shortcuts editor search "Go to Recent Directory" and choose *Remove Keybinding*. A key with no VS Code command left then goes to the shell (inference from VS Code docs, terminal advanced: only commands with keys are intercepted). Untested at the time of writing. The older notes below on `commandsToSkipShell` describe the general mechanism. VS Code decides this with `terminal.integrated.commandsToSkipShell`, a hard-coded list of commands whose keys "skip the shell"; a command is removed from it with a leading `-` (the docs' example is `"-workbench.action.quickOpen"`), and `terminal.integrated.sendKeybindingsToShell` sends most keys to the shell but disables keys such as Ctrl+F find (VS Code docs, terminal advanced). Whether `workbench.action.gotoLine` is named in that list was not confirmed from the docs page. Three ways round it:
  Alternative to the fix above (not needed with it): bind `chat:externalEditor` to another key in `~/.claude/keybindings.json` (`{"bindings": [{"context": "Chat", "bindings": {"<key>": "chat:externalEditor"}}]}`; Claude Code docs, keybindings). The key must be one VS Code leaves to the terminal; which keys those are was not checked. Superseded advice, kept for the record: pressing Ctrl+X Ctrl+E (fails, Ctrl+E is taken) and removing `workbench.action.gotoLine` from `commandsToSkipShell` (wrong command).
- **Which editor opens:** the official docs say only "your default text editor". A Claude Code collaborator's issue reply (seen through search snippets of issues #16342 / #18990 on a mirror site, not read in full) says Ctrl+G reads `VISUAL` first, then `EDITOR`, and suggests `VISUAL="code --wait"` either in the shell profile or in the `env` block of Claude Code's `settings.json` so it applies only to Claude Code. An unofficial copy of the source suggests Notepad as the Windows fallback when neither is set. Several Windows issues report problems with terminal editors (nvim, Helix) under Ctrl+G; a GUI editor such as `code --wait` avoids those (inference). Evidence for this bullet: anecdotal.

**Community fixes (anecdotal):** one blog (May 2026) unbinds VS Code's Ctrl+V terminal paste so the keypress reaches the CLI, moving text paste to Ctrl+Shift+V (`"-workbench.action.terminal.paste"` on `ctrl+v`, `when: terminalFocus && terminalProcessSupported`). A dev.to post (Claude Code v2.1.71) says image paste in the Windows terminal is Alt+V, which the official docs now confirm, so the Alt+V route is the one to use. A GitHub issue where Ctrl+C and Esc did not reach Claude Code in the VS Code terminal on Windows (#38766, Mar 2026) was fixed in v2.1.85.

**Evidence strength:** official standard for the key table, the cut/paste alternatives and the VS Code settings (Claude Code and VS Code docs); anecdotal for the community fixes.

**Sources:**

- Claude Code docs, interactive mode (keyboard shortcuts): https://code.claude.com/docs/en/interactive-mode (official docs)
- Claude Code docs, keybindings: https://code.claude.com/docs/en/keybindings (official docs)
- Claude Code docs, terminal config: https://code.claude.com/docs/en/terminal-config (official docs)
- VS Code docs, Terminal Basics (copy and paste, right-click behavior, select all): https://code.visualstudio.com/docs/terminal/basics (official docs)
- Claude Code docs, VS Code extension: https://code.claude.com/docs/en/vs-code (official docs)
- VS Code docs, keyboard shortcuts (keybindings.json, `-` removal, live reload): https://code.visualstudio.com/docs/configure/keybindings (official docs)
- VS Code docs, terminal advanced ("Keyboard shortcuts and the shell", page dated 2026-11-18): https://code.visualstudio.com/docs/terminal/advanced (official docs)
- Claude Code issues on the Ctrl+G editor choice, #16342 and #18990, via mirror https://claudeissues.com/issue/16342-feature-request-add-configurable-editor-option-for-ctrl-g-shortcut (issue tracker mirror; seen only in search snippets, the site failed to load)
- Ctrl+C copy-when-selected binding: https://forum.cursor.com/t/ctrl-c-will-not-copy/70657 and https://www.codegenes.net/blog/make-ctrl-c-copy-and-ctrl-shift-c-interrupt-in-vscode-terminal/ (community forum, blog)
- Enable image paste in the VS Code terminal, 2026-05-11: https://www.vincentschmalbach.com/enable-image-paste-claude-code-codex-cli-vscode-terminal/ (personal blog)
- Claude Code Ctrl+V not working on Windows: https://dev.to/akari_iku/claude-code-ctrlv-not-working-on-windows-fixes-for-common-gotchas-3mc9 (community post)
- anthropics/claude-code issue #38766: https://github.com/anthropics/claude-code/issues/38766 (issue tracker)
- Claude Code docs, fullscreen rendering (read in full 2026-11-25): https://code.claude.com/docs/en/fullscreen (official docs)

**Scrolling in fullscreen rendering (added 2026-11-25; standard: findings/claude-code-vscode-terminal-clipboard-keys, checked 2026-11-25):** in fullscreen mode Claude Code draws on the terminal's alternate screen, so the VS Code terminal's own scrollback and mouse-wheel scrolling do not hold the conversation. Scrolling happens inside Claude Code: `PgUp`/`PgDn` (half a screen), `Ctrl+Home`/`Ctrl+End` (start, latest), the mouse wheel (needs the terminal to forward mouse events), `Ctrl+o` then `/` to search or `[` to write the conversation to the terminal scrollback. `/scroll-speed` or `CLAUDE_CODE_SCROLL_SPEED` sets the wheel speed (the VS Code terminal sends one event per notch). `/tui default` returns to the classic renderer, `/tui fullscreen` switches back; the choice is saved as the `tui` setting. Which renderer a session starts in depends on the setting, the `CLAUDE_CODE_NO_FLICKER` variable and when the user first used Claude Code (table on the docs page).

**Limits:** the second half of the Claude Code interactive-mode page and the end of the VS Code page were read only through a fetch summary; the key tables were in the verbatim part. Not tested on this machine. The fullscreen-rendering page was read in full on 2026-11-25 (scrolling only; the mouse-selection parts were not tested). VS Code's Windows Ctrl+C copy-versus-interrupt behaviour is Open. Shortcuts change between Claude Code releases; review in 6 months.

**Checked:** 2026-11-22
