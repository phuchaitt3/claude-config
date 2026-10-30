---
name: subagents
description: Rules for dispatching subagents in the user's projects - only when the user asks or a project rule allows, self-contained and checkable briefs, no pushes or commits or coordination edits by the subagent, worktree isolation for code edits, at most two at a time, and keeping cost down (tight brief, cheapest model, short report, skip tiny tasks, fork when context matters). Use before spawning any subagent or fork.
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
