---
topic: claude-code-auto-mode-trust
area: Agent setup
question: Which repositories does the Claude Code auto mode classifier trust, how is that changed, and how is a block diagnosed? (Separate from agent-permission-enforcement, which covers deny, ask and hooks.)
checked: 2026-11-28
review_months: 6
status: current
---
# Auto mode: trusted repositories and blocked pushes

**Question:** Which repositories does the classifier trust, how is that changed, and how is a block diagnosed?

**Finding:**
- By default only the working directory and that repository's remotes are trusted. The built-in "Git Push Destination" exception covers any branch of the session's repository, the default branch included, and no other repository.
- `autoMode.environment`, `allow`, `soft_deny` and `hard_deny` are prose rules, not patterns. A list should contain `"$defaults"`, or it replaces the built-in entries of that section.
- `autoMode` is read from user settings, managed settings and `--settings`, not from project settings. So an `environment` written for one project in user settings applies to every project.
- Explicit user intent that names the action can clear a soft block, not a `hard_deny`.
- Narrow `permissions.allow` Bash rules stay in effect in auto mode and skip the classifier; broad ones are dropped.
- Diagnosis: `/permissions`, "Recently blocked" tab; `claude auto-mode config` (effective rules), `claude auto-mode defaults` (built-in rules), `claude auto-mode reset` (removes `autoMode` from user settings only).
- Observed once: a compound command that committed and pushed to the `main` of a repository other than the session's was blocked as "Destructive or Unwanted Actions"; a shorter commit and push that the user typed into the chat then ran. Which rule fired was not shown. Later the same session, after the user said they wanted to push, a commit and then a push to that repository's `main` as separate commands both ran, with the settings unchanged.

**Sources:**
- [Auto mode configuration](https://code.claude.com/docs/en/auto-mode-config) and [permission modes](https://code.claude.com/docs/en/permission-modes) (official docs; the second was only partly read).
- First-hand: `claude auto-mode defaults`, Claude Code 2.1.332.

**Limits:** Vendor documentation, read through a fetch summary; behaviour may change between versions. The cause of the observed block was not reproduced.

**Checked:** 2026-11-28
