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
  - **On Android the palette and menus close as soon as they open** (user, 2026-11-26, Unexpected Keyboard, phone browser): the on-screen keyboard opening or closing resizes the page and the open palette or ☰ / ⋯ menu disappears. Likely cause the page resize; not confirmed. So the command and menu routes above could not be tested on that phone.
  - **Keyboard keys instead of menus (Android, not tested):** Unexpected Keyboard does have Shift: the ⇧ key left of Z on the default QWERTY layout (`latn_qwerty_us.xml`); its docs list `shift`, `ctrl`, `alt` as modifiers "sent to the app", and `up`/`down`/`left`/`right` and `selectAll`, `copy`, `cut`, `paste` as keys sent to the app, which the "Add keys to the keyboard" setting can add. The docs do not say whether Shift held with an arrow selects text, and Android's own guidance says apps should not rely on key events from a soft keyboard, so whether Monaco receives them is unknown. Next to try: Shift + arrow, then the added `selectAll` and `copy` keys.
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
  - Unexpected Keyboard README (corner swipes, settings): https://github.com/Julow/Unexpected-Keyboard ; key values and modifiers: https://github.com/Julow/Unexpected-Keyboard/blob/master/doc/Possible-key-values.md ; default US layout (Shift left of Z): https://github.com/Julow/Unexpected-Keyboard/blob/master/srcs/layouts/latn_qwerty_us.xml
  - Android developers, "Handle keyboard actions" (Shift+arrow selects; apps should not rely on key events from a soft input method): https://developer.android.com/develop/ui/compose/touch-input/keyboard-input/commands
- **Limits:** no source is about vscode.dev itself; all describe Monaco embedded in other products, which may set it up differently. Issue 246 could not be read, so its current state is unknown. The snapshot dates of the GitLab pages are not shown. None of the workarounds above was tried on a phone.
