# claude-config

My Claude Code setup, shared between machines through git.

| Part | What it is | How it loads |
|---|---|---|
| `rules/working-rules.md` | Always-on rules: hard limits, decision rights, commits, model/effort, subagents, clearing | imported by `~/.claude/CLAUDE.md` in every session |
| `plugins/workflow/` | Plugin with the `workflow:multi-chat` skill (worktrees, inbox, handoff reports) and its templates, and two hooks (`hooks/hooks.json`) that keep chats in sync with GitHub: `github_state.py` (UserPromptSubmit: when open PRs, `needs-you` items or merges changed since the chat last heard, it adds one line, plus the "after a merge" steps and a warning when the checked-out branch's PR is already merged; silent otherwise) and `push_guard.py` (PreToolUse: refuses `git push` to a branch whose PR is already merged). Tests: `hooks/test_*.py` | installed from this repo as a local marketplace. **A plugin is a cached copy: after each change, bump `version` in `.claude-plugin/plugin.json`, push, and on every machine run `/plugin update workflow@personal-config` and restart.** |
| `CLAUDE.user.md` | The stub to copy to `~/.claude/CLAUDE.md` | copied once per machine |

Project-specific rules stay in each project's own `CLAUDE.md`, together with its hard limits, which these rules never relax.

## Set up or repair a machine: one command

After cloning this repo to `~/claude-config` (step 1 below), everything else is one command, safe to run any number of times (it pulls this repo, installs or updates the `workflow` plugin through the Claude Code command line, and turns `autoUpdate` on in `~/.claude/settings.json` with a backup):

```
powershell -NoProfile -File "$HOME\claude-config\scripts\setup-machine.ps1"
```

Needs git, python and Claude Code. Run it once on a machine that is behind; after that the plugin keeps the machine current by itself. The numbered steps below are what it automates (and the manual fallback). Tests: `scripts/test_merge_settings.py`.

## Set up a machine (once)

1. Clone this repo to `~/claude-config`, which is `C:\Users\<you>\claude-config` on Windows. The import path in the stub assumes that location.
2. Copy `CLAUDE.user.md` to `~/.claude/CLAUDE.md`, or add its import line to an existing one.
3. In a Claude Code session:
   ```
   /plugin marketplace add ~/claude-config
   /plugin install workflow@personal-config
   ```
   Choose user scope. Check with `/plugin` (Installed tab) and `/memory`, which lists the loaded instruction files.
   Where `/plugin` is not available (the VS Code extension), use the bundled command line instead: `claude.exe` sits in `%USERPROFILE%\.vscode\extensions\anthropic.claude-code-*\resources\native-binary\`. Run `claude.exe plugin marketplace add %USERPROFILE%\claude-config`, then `claude.exe plugin install workflow@personal-config`. To update by hand: `claude.exe plugin marketplace update personal-config`, then `claude.exe plugin update workflow@personal-config`, then restart.
4. Turn on automatic plugin updates: in `~/.claude/settings.json`, under `extraKnownMarketplaces` > `personal-config`, add `"autoUpdate": true` (sibling of `source`). The plugin then updates itself at startup whenever its `version` in `plugin.json` is newer; a plugin change without a version bump is not picked up. The plugin's `pull_config.py` (SessionStart) runs `git pull --ff-only` on `~/claude-config` at most every 30 minutes, silently, so the repo follows too; a machine is current after one or two restarts.

## Change something

Edit here, commit, push; on the other machine, `git pull`. A local-path marketplace reads the plugin straight from this folder, so changes apply at the next session start or after `/reload-plugins`, with no version bump.
