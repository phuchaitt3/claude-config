---
topic: vscode-tunnel-mobile-text-selection
area: Agent setup
question: Can text be selected (and copied) in the VS Code editor opened from a phone through a VS Code tunnel (vscode.dev/tunnel), and what works instead?
checked: 2026-11-26
review_months: 6
status: current
---

# VS Code tunnel on a phone: text selection

- **Question:** A VS Code tunnel (`code tunnel`) opened in a phone browser at `vscode.dev/tunnel/<machine>/<folder>` shows the files and allows typing, but long-press or drag does not select text. Is this a known limit, and what works instead? Separate from the other VS Code entries because those cover the desktop editor and terminal.
- **Short answer:** a known limit, not a setting. The editor in vscode.dev is Monaco, and Monaco's own FAQ says it is not supported in mobile browsers. Other products that embed Monaco (GitLab, Node-RED, Babylon.js, Home Assistant) report the same thing on iOS and Android: blocks of text cannot be selected, copy and paste fails or half-works, and long-press is broken. No source found says this has been fixed. The user saw the same on 2026-11-26 (tunnel from VS Code 1.148.0, phone browser).
- **What to try instead (none tested on a phone):**
  - Read in the **Markdown preview** (rendered tab or `Markdown: Open Preview`). The preview is an HTML page in a webview, not Monaco, so the phone's own selection may work there. (inference: findings/vscode-tunnel-mobile-text-selection)
  - Use keyboard-style selection from the command palette: `Select All` (Ctrl+A), `Expand Selection`, `Copy Line Down`. These are editor commands, not touch gestures. Whether the phone keyboard and clipboard then copy the selection was not checked.
  - Select with Shift+arrows on an external keyboard. A GitLab issue reports that external keyboard keys do not work in Monaco on iOS (Chrome, Safari), so this may fail on an iPhone.
  - For a passage to quote or move, ask a Claude Code Remote Control session on the same machine to copy or edit it: the chat text in the Claude app is selectable.
  - The file viewer on github.com renders Markdown as normal HTML, which a phone can select; it shows the last pushed version, not unsynced local edits.
- **Sources:**
  - Monaco FAQ, "Is the editor supported in mobile browsers or mobile web app frameworks? No.": https://github.com/microsoft/monaco-editor (README, FAQ section); quoted in GitLab issue 229159, "Web Editor not working on mobile", which also says the maintainers had no plan to add mobile support and points to monaco-editor issue 246: https://gitlab.com/gitlab-org/gitlab/-/issues/229159
  - GitLab issue 32163, "Selecting/copying/pasting in Editor does not work on mobile devices" (iOS and Android): https://gitlab.com/gitlab-org/gitlab/-/issues/32163
  - GitLab issue 24063, "External keyboard keys don't work on iOS (Chrome, Safari)": https://gitlab.com/gitlab-org/gitlab/-/issues/24063
  - Node-RED forum, "Cannot select/copy/paste with monaco editor on iPad/Safari": https://discourse.nodered.org/t/cannot-select-copy-paste-with-monaco-editor-on-ipad-safari/77844
  - Babylon.js forum, "[Android] Playground doesn't handle long-press anymore" (calls it a Monaco problem): https://forum.babylonjs.com/t/android-playground-doesnt-handle-long-press-anymore/57574
  - Home Assistant forum, "Monaco editor IPad": https://community.home-assistant.io/t/monaco-editor-ipad/463861
  - code-server issue 7556 (iPad selection and copy problems, a workaround of selecting begin to end): https://github.com/coder/code-server/issues/7556
- **Limits:** no source is about vscode.dev itself; all describe Monaco embedded in other products, which may set it up differently. Issue 246 could not be read, so its current state is unknown. The snapshot dates of the GitLab pages are not shown. None of the workarounds above was tried on a phone.
