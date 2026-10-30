# claude-config

My Claude Code setup, shared between machines through git.

| Part | What it is | How it loads |
|---|---|---|
| `rules/working-rules.md` | Always-on rules: hard limits, decision rights, commits, model/effort, subagents, clearing | imported by `~/.claude/CLAUDE.md` in every session |
| `plugins/workflow/` | Plugin with the `workflow:multi-chat` skill (worktrees, inbox, handoff reports) and its templates | installed from this repo as a local marketplace |
| `hooks/github_state.py` | UserPromptSubmit hook that keeps a chat in sync with GitHub: when open PRs, `needs-you` items or merges changed since the chat last heard, it adds one line (plus the "after a merge" steps, and a warning when the checked-out branch's PR is already merged). Silent otherwise. Tests: `hooks/test_github_state.py` | add to `~/.claude/settings.json` under `hooks.UserPromptSubmit`, once per machine: `{"type":"command","command":"python \"C:/Users/<you>/claude-config/hooks/github_state.py\"","timeout":5}` |
| `CLAUDE.user.md` | The stub to copy to `~/.claude/CLAUDE.md` | copied once per machine |

Project-specific rules stay in each project's own `CLAUDE.md`, together with its hard limits, which these rules never relax.

## Set up a machine (once)

1. Clone this repo to `~/claude-config`, which is `C:\Users\<you>\claude-config` on Windows. The import path in the stub assumes that location.
2. Copy `CLAUDE.user.md` to `~/.claude/CLAUDE.md`, or add its import line to an existing one.
3. In a Claude Code session:
   ```
   /plugin marketplace add ~/claude-config
   /plugin install workflow@personal-config
   ```
   Choose user scope. Check with `/plugin` (Installed tab) and `/memory`, which lists the loaded instruction files.

## Change something

Edit here, commit, push; on the other machine, `git pull`. A local-path marketplace reads the plugin straight from this folder, so changes apply at the next session start or after `/reload-plugins`, with no version bump.
