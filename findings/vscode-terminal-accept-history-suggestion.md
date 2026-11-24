---
topic: vscode-terminal-accept-history-suggestion
area: Agent setup
question: In the VS Code integrated terminal on Windows, how do you accept the grey inline suggestion of a previous command (history prediction), whole or one word at a time? Separate from claude-code-vscode-terminal-clipboard-keys because the keys belong to the shell (PSReadLine), not to Claude Code or VS Code.
checked: 2026-11-24
review_months: 6
status: current
---

# Accepting the inline "previous command" suggestion in the VS Code terminal (Windows)

**Question:** the grey text after the cursor that completes a command from history: which key takes it?

**Finding:** the grey text comes from the shell, not from VS Code, so the key is the shell's. In PowerShell it is PSReadLine's predictive IntelliSense (inline view).

- **Accept the whole suggestion: Right Arrow** (with the cursor at the end of the typed text). Microsoft's predictor docs say pressing RightArrow accepts an inline suggestion and that you can edit the line before running it; `AcceptSuggestion` is built into `ForwardChar`, which is bound to RightArrow. (official docs, via search summary of "Using predictors in PSReadLine"; the page itself was not read in full.)
- **Accept one word: no default key** in the function reference. `AcceptNextSuggestionWord` ("accept the next word of the inline or selected suggestion") and `AcceptSuggestion` are listed as "Function is unbound"; you bind a key yourself with `Set-PSReadLineKeyHandler`. Microsoft's sample profile has a `ForwardCharAndAcceptNextSuggestionWord` handler for this (DevBlogs, 2020, via search summary).
- **End key:** `End` is bound to `EndOfLine` (Windows mode); the reference does not say it accepts the suggestion. Treat it as untested. Same for Ctrl+Right Arrow (bound to `NextWord`, a cursor move).
- **Switch view: F2** (`SwitchPredictionView`) toggles between InlineView (grey text, default) and ListView (drop-down list, choose with Up/Down). `PredictionViewStyle` default is InlineView (Set-PSReadLineOption).
- **No suggestion appears?** `PredictionSource` default on the Set-PSReadLineOption pages (7.4, 7.6) is `None`; set `Set-PSReadLineOption -PredictionSource History` (or `HistoryAndPlugin`) in `$PROFILE`. A 2022 DevBlogs post titled "PSReadLine 2.2.6 enables Predictive Intellisense by default" says the opposite for PowerShell 7.3+, which ships 2.2.6; the two Microsoft sources disagree, so check with `Get-PSReadLineOption`. The Windows PowerShell 5.1 option page lists no prediction parameters at all, so use PowerShell 7 or a newer PSReadLine.
- **VS Code's own feature is different:** Terminal IntelliSense (a suggestion list) inserts with **Tab**; after navigating the list, **Enter** inserts; `terminal.integrated.suggest.runOnEnter` optionally runs the command on Enter; Ctrl+Space triggers it (`workbench.action.terminalTriggerSuggest`, VS Code shell-integration page dated 2026-11-18). The setting `terminal.integrated.suggest.inlineSuggestion` is described only as integrating with shell "ghost text"; the page names no accept key for it and gives no values or default: Open.
- **Claude Code's prompt:** its own grey prompt suggestion is a separate thing and does not use PSReadLine (see findings/claude-code-vscode-terminal-clipboard-keys for its keys).

**Evidence strength:** official docs for the setting defaults, F2 and unbound functions; the Right Arrow accept rests on a search summary of an official page plus a 2020 Microsoft blog, not a full read, and was not tested here.

**Sources:**

- Using predictors in PSReadLine: https://learn.microsoft.com/en-us/powershell/scripting/learn/shell/using-predictors (official docs)
- about_PSReadLine_Functions (AcceptSuggestion, AcceptNextSuggestionWord unbound; SwitchPredictionView F2; ForwardChar, EndOfLine): https://learn.microsoft.com/en-us/powershell/module/psreadline/about/about_psreadline_functions (official docs, ms.date 2026-01-18)
- Set-PSReadLineOption (PredictionSource default None, PredictionViewStyle default InlineView): https://learn.microsoft.com/en-us/powershell/module/psreadline/set-psreadlineoption (official docs, ms.date 2026-03-04)
- PSReadLine 2.2.6 enables Predictive Intellisense by default, 2022-06-27: https://devblogs.microsoft.com/powershell/psreadline-2-2-6-enables-predictive-intellisense-by-default (vendor blog)
- Announcing PSReadLine 2.1 with Predictive IntelliSense, 2020-11-10: https://devblogs.microsoft.com/powershell/announcing-psreadline-2-1-with-predictive-intellisense/ (vendor blog)
- VS Code Terminal Shell Integration: https://code.visualstudio.com/docs/terminal/shell-integration (official docs, dated 2026-11-18)

**Limits:** not tested on this machine; Right Arrow accepting and End/Ctrl+Right not accepting are unverified here (`Get-PSReadLineKeyHandler` lists the real bindings). Only PowerShell covered; other shells (Git Bash, zsh with autosuggestions, fish) differ. The default-on versus default-None conflict is unresolved. Review in 6 months.

**Checked:** 2026-11-24
