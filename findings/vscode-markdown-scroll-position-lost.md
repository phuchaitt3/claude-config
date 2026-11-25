---
topic: vscode-markdown-scroll-position-lost
area: Agent setup
question: In VS Code, why can a Markdown file jump back to the top after switching to another file and returning, and which settings control restoring the scroll position?
checked: 2026-11-25
review_months: 6
status: current
---

# VS Code: Markdown file jumps to the top after switching files

- **Question:** Opening another file and returning to a `.md` file puts the view at the top instead of where it was. Is there a fix, and which settings apply? Separate from the other VS Code entries because those cover the terminal, not the editor.
- **Finding:**
  - The text editor remembers scroll position and cursor by default: `workbench.editor.restoreViewState` is `true`. The state is stored per editor group and discarded when the group closes. `workbench.editor.sharedViewState` (default `false`) reuses the most recent state across groups when a group has none. (standard: findings/vscode-markdown-scroll-position-lost, checked 2026-11-25; source: VS Code source, `workbench.contribution.ts`.)
  - `workbench.editor.enablePreview` (default `true`) replaces an italic-titled preview tab with the next file opened. The setting text says only that the contents are replaced. Whether a replaced tab still gets its scroll back depends on the view-state setting above; the sources do not say. (inference: findings/vscode-markdown-scroll-position-lost)
  - The Markdown preview (the rendered view) is a separate case. VS Code issue 63690 ("markdown files preview does not save scroll position", 2018) was closed as fixed in 2021 by a maintainer. A commenter on the same day said the release-notes preview still lost its position, and the issue gives no later confirmation either way. The preview-as-custom-editor work (issues 84520 and 138040) says scroll position is synced between preview and editor only when both are not visible at once.
  - A VS Code fork's forum (Cursor) reports the same symptom for Markdown files in 2026 and says a fix covered one tab, not switching between files. That is a fork, not VS Code.
  - No source found that gives a fix for the plain text editor on current VS Code (tested version here: 1.147.0). No bug report matching the symptom was found for the text editor on 1.147.
- **Evidence strength:** *official standard* for the settings (the tool's own source); *anecdotal* for the bug reports; *no data found* for a fix on current builds.
- **Sources:**
  - VS Code source, setting descriptions: https://github.com/microsoft/vscode/blob/main/src/vs/workbench/browser/workbench.contribution.ts (official source)
  - https://github.com/microsoft/vscode/issues/63690 (issue tracker, closed 2021-10-07)
  - https://github.com/microsoft/vscode/issues/84520 and https://github.com/microsoft/vscode/issues/138040 (issue tracker, preview as custom editor)
  - https://github.com/microsoft/vscode/issues/102485 (issue tracker, origin of `sharedViewState`)
  - https://forum.cursor.com/t/markdown-file-scrolls-back-up-unexpectedly/168821 (fork's forum, anecdotal)
- **Limits:** Two web searches plus the issue tracker through `gh`; the official docs page for the setting did not come up in search, so the wording comes from the source file. The sources do not separate "text editor" from "preview" for the user's symptom; which one it is has to be asked.
- **Checked:** 2026-11-25
