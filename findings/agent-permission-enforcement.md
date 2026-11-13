# Enforcing rules on a coding agent

- **Question:** Which Claude Code mechanisms enforce a rule instead of asking the model to follow it, and how strong is each?
- **Checked:** 2026-11-05

## Finding

- **Permission rules are enforced by Claude Code, not by the model.** Instructions in a prompt or `CLAUDE.md` shape what the model tries to do, not what Claude Code allows.
- **Order is deny, then ask, then allow.** An allow rule cannot carve an exception out of a deny rule.
- **Modes.** Deny rules block in every mode, including `bypassPermissions`. Explicit ask rules still force a prompt in auto mode and do not go to the classifier.
- **Bash patterns match command text.** Deny and ask rules apply to any subcommand of a compound command, but a rule "isn't a security boundary around the program", and patterns that constrain arguments are "fragile". For arguments, the docs recommend a `PreToolUse` hook.
- **Read deny rules** cover the built-in file tools, file commands Claude Code recognises in Bash (`cat`, `head`, `sed`) and redirections, not "arbitrary subprocesses", such as a Python script that opens the file itself. For limits that do not depend on command text, the docs point to sandboxing.

Not from a source (the checker's inference): order the layers by who enforces them: the server (rulesets), missing access, the harness (deny, ask, hooks, sandbox), checks after the fact, then text. For an agent making mistakes, the harness is usually enough; against a hostile agent on a machine holding the owner's tokens, only the server and the sandbox count.

## Sources

- [Configure permissions](https://code.claude.com/docs/en/permissions) (official docs).
- [Permission modes](https://code.claude.com/docs/en/permission-modes) (official docs; the last part of the page was not read).

## Limits

Claude Code's own documentation, not an independent standard, and behaviour may change between versions. The permission-modes page does not state directly that `PreToolUse` hooks run in auto mode; in practice the hooks fired in auto-mode sessions.
