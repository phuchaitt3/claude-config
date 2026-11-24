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

**Why it shows up only sometimes, and how to toggle it (added 2026-11-24).** Three different features draw grey text in this terminal; which one you see depends on what runs in the terminal:

1. **PSReadLine history prediction (PowerShell prompt).** Needs PSReadLine 2.1 or newer plus `PredictionSource` set to History/HistoryAndPlugin (default per Set-PSReadLineOption: `None`; per the 2022 blog: on from 2.2.6). **On this machine (measured 2026-11-24): `pwsh` is not installed, Windows PowerShell 5.1 runs PSReadLine 2.0.0, `PredictionSource` and `PredictionViewStyle` are empty and `RightArrow` is plain `ForwardChar`; there is no `$PROFILE` file.** So no PowerShell prediction exists here at all; grey text on this machine's PowerShell prompt is not from PSReadLine. Where it exists, it shows only when the typed text is the start of a history entry and the cursor is at the end of the line, and a PSReadLine 2.4.5 regression on PowerShell 7.6.0 shows none (GitHub PSReadLine #5116, seen in a search snippet, status unconfirmed). Toggle: `Set-PSReadLineOption -PredictionSource None` (off) or `History` (on), put in `$PROFILE` to persist; F2 switches inline/list view. A one-key toggle is not documented; a custom `Set-PSReadLineKeyHandler` that flips `PredictionSource` is possible (inference, untested).
2. **Claude Code's own prompt suggestion (inside the `claude` prompt).** Grey example prompt at session start (taken from the project's git history) and a suggested next prompt after a reply. Accept: **Tab or Right Arrow** places it in the input, Enter then submits; typing dismisses it (Claude Code docs, interactive mode, verbatim). It is skipped when the prompt cache is cold, after the first turn in some sessions, after an error, and per the docs' summary near the usage limit and in plan mode; in interactive mode the docs say it is off by default in sessions that do not fetch feature flags and in the first session after an install or upgrade, which also hides the `/config` toggle. That varying availability is the likeliest reason it appears "sometimes". Toggle: `/config` → Prompt suggestions, or `"promptSuggestionEnabled": false` in settings (named in the settings reference), or env `CLAUDE_CODE_ENABLE_PROMPT_SUGGESTION=false` (env name and precedence from a fetch summary, not verbatim).
3. **VS Code Terminal IntelliSense (suggestion list/ghost text from VS Code).** Needs shell integration active (auto-injected for pwsh and Git Bash launched from VS Code; on Windows it needs permission to run PowerShell scripts, the page recommends the CurrentUser policy `RemoteSigned`); not active in sub-shells, plain ssh or after `terminal.integrated.shellIntegration.enabled` is false. Toggle: `terminal.integrated.suggest.enabled`; defaults not stated on the page. Tab inserts; Ctrl+Space triggers it. Windows PowerShell 5.1 is not in the page's supported list (only pwsh and Git Bash), consistent with this machine showing nothing there (inference).

To find out which one you saw: the grey text with the prompt `PS C:\...>` and no `claude` running is 1 or 3; grey text inside the `claude` input box is 2. Open: not tested which one the user saw.

**Evidence strength:** official docs for the setting defaults, F2 and unbound functions; the Right Arrow accept rests on a search summary of an official page plus a 2020 Microsoft blog, not a full read, and was not tested here.

**Sources:**

- Using predictors in PSReadLine: https://learn.microsoft.com/en-us/powershell/scripting/learn/shell/using-predictors (official docs)
- about_PSReadLine_Functions (AcceptSuggestion, AcceptNextSuggestionWord unbound; SwitchPredictionView F2; ForwardChar, EndOfLine): https://learn.microsoft.com/en-us/powershell/module/psreadline/about/about_psreadline_functions (official docs, ms.date 2026-01-18)
- Set-PSReadLineOption (PredictionSource default None, PredictionViewStyle default InlineView): https://learn.microsoft.com/en-us/powershell/module/psreadline/set-psreadlineoption (official docs, ms.date 2026-03-04)
- PSReadLine 2.2.6 enables Predictive Intellisense by default, 2022-06-27: https://devblogs.microsoft.com/powershell/psreadline-2-2-6-enables-predictive-intellisense-by-default (vendor blog)
- Announcing PSReadLine 2.1 with Predictive IntelliSense, 2020-11-10: https://devblogs.microsoft.com/powershell/announcing-psreadline-2-1-with-predictive-intellisense/ (vendor blog)
- VS Code Terminal Shell Integration: https://code.visualstudio.com/docs/terminal/shell-integration (official docs, dated 2026-11-18)
- Claude Code docs, interactive mode, "Prompt suggestions": https://code.claude.com/docs/en/interactive-mode (official docs; second half via fetch summary)
- Claude Code settings reference (`promptSuggestionEnabled`): https://code.claude.com/docs/en/settings-reference (official docs; default not read)
- PSReadLine #5116, no inline prediction in 2.4.5 on PowerShell 7.6.0: https://github.com/PowerShell/PSReadLine/issues/5116 (issue tracker; seen through a mirror snippet)
- Disable PSReadLine predictions during demos, 2026-03-15: https://markgzero.github.io/2026/03/15/disable-psreadline-predictions-during-demos.html (personal blog; title only, not read)

**Limits:** not tested on this machine; Right Arrow accepting and End/Ctrl+Right not accepting are unverified here (`Get-PSReadLineKeyHandler` lists the real bindings). Only PowerShell covered; other shells (Git Bash, zsh with autosuggestions, fish) differ. The default-on versus default-None conflict is unresolved. Review in 6 months.

**Checked:** 2026-11-24
