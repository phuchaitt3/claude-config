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
- Diagnosis: `/permissions`, "Recently blocked" tab; `claude auto-mode config` (effective rules), `claude auto-mode defaults` (built-in rules), `claude auto-mode reset --yes` (removes `autoMode` from user settings only; without `--yes` it asks, and aborts when run with no input). `--debug-file` logs only `Auto mode classifier blocked action`, with no rule named.
- `/auto-mode-setup`, run inside one project, writes an `autoMode.environment` describing that project into user settings, without `"$defaults"`, so it replaces the default entries for every project. Seen on two machines.
- Observed: a compound command that committed and pushed to the `main` of a repository other than the session's was blocked as "Destructive or Unwanted Actions"; later pushes in the same session, after the user had asked for them, ran.
- Reproduced with throwaway repositories and a local bare remote (headless sessions, `--permission-mode auto`, one Bash call of add, commit, fetch, rebase, `push origin HEAD:main`, then pull in another checkout). The verdict is not deterministic: identical input was both allowed and denied.
- Push not asked for: denied 2 of 8 (project-specific `environment` in user settings), 0 of 8 (same text passed by `--settings` after the reset), 4 of 9 (default settings). A push on its own in a separate call was also denied (1 of 3 runs), so a compound command is not required.
- Push asked for in the user's words ("I want this fix committed and pushed to main"): denied 0 of 3 (old settings) and 0 of 8 (default settings). Without fetch, rebase and pull, and not asked for: 0 of 3.
- So the misplaced `environment` is not needed for the block. When a push to another repository is wanted, asking for it in the prompt avoided the block in every run; no permission rule was added.

**Sources:**
- [Auto mode configuration](https://code.claude.com/docs/en/auto-mode-config) and [permission modes](https://code.claude.com/docs/en/permission-modes) (official docs; the second was only partly read).
- First-hand: `claude auto-mode defaults` and the trials above, Claude Code 2.1.332, Sonnet 5.5, 2026-11-28.

**Limits:** Vendor documentation, read through a fetch summary; behaviour may change between versions. Small samples: the 0 of 8 against 4 of 9 gap between settings may be chance, and asked (0 of 8) against not asked (4 of 9) on default settings is only suggestive. Not tested: a GitHub remote, a push to the session's own repository, other models. Which rule fired is unknown.

**Checked:** 2026-11-28
