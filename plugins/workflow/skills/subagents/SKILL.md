---
name: subagents
description: ALWAYS load this before spawning any subagent or fork. Rules for dispatching subagents in the user's projects: only when the user asks or a project rule allows, self-contained and checkable briefs, no pushes or commits or coordination edits by the subagent, worktree isolation for code edits, at most two at a time, keeping cost down (tight brief, cheapest model, short report, skip tiny tasks, fork when context matters), and handing off a whole task (check first, a worker that opens its own PR, a background session for a long task).
---

# Dispatching subagents

Moved out of the working rules (`~/claude-config/rules/working-rules.md`) on 2026-10-30 so it loads only when needed; the text is unchanged.

Spawn subagents only when the user asks, or under a project rule that allows it. When dispatching, all of these must hold:
- **Self-contained:** the prompt states the whole task, the files and the expected result.
- **Checkable:** there is a pass/fail check (lint and tests, a search with a concrete answer).
- **No shared state:** the subagent does not push, run cloud jobs, edit coordination files, merge or commit; the dispatching chat does those.
- **Isolated:** agents that edit code run with `isolation: "worktree"`; the dispatching chat reviews the diff, runs the checks and commits.

Keep it to two at a time, and do not dispatch work that is blocked on a long job or a user decision. A subagent starts cold, so its cost scales with how much it reads, not with the task's importance. To keep that small:
1. **Tight brief:** name the exact files, the goal and the check, so it does not explore.
2. **Cheapest model that fits:** a mechanical task on Haiku or Sonnet often costs less than doing it in an Opus chat.
3. **Short report:** ask for the conclusion and file paths, not file dumps.
4. **Skip tiny tasks:** if the chat can do it in a couple of tool calls, the cold start costs more.
5. **Fork when context matters:** a fork inherits the chat's context but runs on the chat's model, so it saves time, not money.

A subagent never uses Opus unless the task's tag already justified it.

## Handing off a whole task

Applies to any dispatch of a task with a checkable finish (user's decision, 2026-11-14, moved here from `workflow:self-drive`).

- **Check first.** Before dispatching, look at `main`, the issue and open PRs for existing work (a design brief, code, a ticked box). A task already done is closed out, not redone (after three workers were routed to work that already existed).
- **Report.** At most 10 lines: PR link or paths, files changed, checks with results, open questions.
- **Worker that opens its own PR.** This departs from "No shared state" above and is allowed only under a self-drive loop (`workflow:self-drive`) or a project rule that says so. The worker runs lint and tests, commits, pushes its own branch and opens the PR with `Closes #n`; it never merges, edits coordination files, files issues or starts agents of its own (standard: findings/agent-worker-task-creation, checked 2026-11-14). The dispatching chat does not read the diff or a log. It verifies from sources the worker did not write: `gh pr checks`, `gh pr diff --stat` (the file list matches the brief; no user-merge path is touched unless intended) and the PR body's closing line. It reads the diff itself on a user-merge path, or when the report and `--stat` disagree (standard: findings/agent-worker-scope-and-verification, checked 2026-11-14; vendor or single source for the worker opening the PR).
- **Long task (about an hour or more).** Use a background session, not a subagent: `claude --bg -n <issue>-<slug> "<brief>"` from the main checkout (on a machine without `claude` on PATH, the VS Code extension's bundled `claude.exe`). It works in its own worktree and opens its own PR; the dispatcher reads only the PR and `claude agents --json`. The brief says: create the worktree with `git worktree add ../<ID>-<slug>` (never `EnterWorktree` or `--worktree`), pass the PR body as `--body-file` (never `--body -`), and finish with `gh pr view <n> --json closingIssuesReferences`. When it is done, the dispatcher checks the PR body has `Closes #n` (fixing it if not), runs `claude rm <id>`, and checks `git worktree list` for a stray worktree under `main/.claude/worktrees` (first real run, 2026-11-14, hit all three; standard: findings/agent-delegation-choice, checked 2026-11-14).
