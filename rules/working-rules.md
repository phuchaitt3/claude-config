# Working rules (all projects)

Loaded in every session through `~/.claude/CLAUDE.md`. A project's own `CLAUDE.md` adds to these and may make them stricter; nothing here relaxes a limit a project sets.

## Hard limits (a project may tighten, never loosen)

- Ask before anything destructive (deleting or overwriting data you did not create, rewriting git history) and anything outward-facing (push, opening a PR, publishing, uploading to any external service, spending money).
- Never read, write or delete credential files (`~/.kaggle`, `.env` files holding secrets, tokens, `~/.claude/.credentials.json`).
- Ask before a long paid or cloud job. The default threshold is 30 minutes; a project may set another.

## Decision rights

Asking is a cost: it stops the flow. Ask only when a wrong guess is expensive or only the user knows the answer. The test is **reversibility**: if a choice can be undone with a revert, a rerun or a file edit, make it.

**Decide and proceed, no asking:**
- Implementation choices: structure, naming, libraries already in the project, test design, refactors inside the task's files.
- Task order, parallelism, and which chat or subagent does a task.
- Commits on the current feature branch; merging a peer chat's branch when its checks pass, unless the diff weakens a safety limit.
- Defaults for open questions, documentation fixes, correcting stale claims, adding tests, lint and format fixes.
- Updating coordination files (inbox, handoff reports, status columns in design docs).

**Decide, then tell the user** (one line in the inbox or the reply, with the reason and how to undo it):
- A default taken on an open design question (hosting, frontend, scope of a milestone).
- Changing a pinned version, a preset value or a tolerance, together with the run that justifies it.
- Reordering or adding milestones.

**Ask first** (put it in the inbox under "Needs your decision" with a recommended default and a model tag, and keep working on everything else):
- Everything under "Hard limits".
- A choice whose cost of being wrong is high and that only the user can judge: claims in a thesis or paper, licensing, public content, a budget.
- Relaxing a limit in a project's `CLAUDE.md`.

When unsure which tier applies, take the lower-asking tier if the action is reversible, the asking tier if it is not. A question is one line with a recommended default and what happens if there is no answer. Do not ask for confirmation of something already requested, and do not ask which of two reversible options to take.

## Commits

You may commit on the current feature branch without asking. Never commit to `main`, and never push or open a PR unless asked.

- **One commit = one coherent change** (a feature, a fix, a tooling change, a doc update) with its tests and docs. Do not mix unrelated changes: stage with `git add <paths>`, not `git add -A`.
- **Commit when a unit is done and green**, not at the end of the session. Run the project's lint and tests first; never commit a half-working state or a failing test.
- **Message**: a short imperative subject, then a body explaining *why*, plus any known gap (for example "not yet run on real data"). Add the attribution trailer the harness specifies.
- **Never commit** run outputs, data, build artefacts, credentials or private identifiers. Check `git status` before adding.
- Never commit, stash or revert changes you did not make.

## Model and effort per task

The user picks the model (`/model`) and effort by hand. At the start of each task, say in one line which model and effort it needs; if the current model is a poor fit, say so before starting. Plan mode: yes only when the design is still open.

**Budget rule:** Sonnet is the default for everything. Opus costs much more and is reserved for tasks that are both hard and expensive to get wrong. Any task tag that names Opus must state the specific difficulty in a few words (for example "unexplained numeric drift after a Sonnet pass found nothing"). "New feature", "porting" or "important" are not reasons; an Opus tag without one is invalid. Prefer Sonnet at high effort first and escalate only if it fails or gets stuck.

| Task | Model | Effort |
|---|---|---|
| Inbox and handoff updates, commits, merges, routine runs, reading logs | Sonnet | low |
| Small, well-specified code or doc edits, tests for existing behaviour, lint fixes | Sonnet | medium |
| New features, ports, schema changes, writing docs and reports | Sonnet | high |
| Debugging, a mismatch or drift: first pass, narrowing down | Sonnet | high |
| **Opus only:** a bug still unexplained after a Sonnet pass; a bug that needs several components' behaviour held at once; an open design question with a costly wrong answer (use plan mode) | Opus | high (xhigh only if high failed) |
| Final wording of claims for a thesis, paper or public statement (the numbers come from Sonnet) | Opus | high |

Use `max` effort only when the user asks. Tags are written `[Sonnet, medium, no plan mode: reason]` and go on every open task, in-flight item, decision item and proposed next step.

## Subagents

Spawn subagents only when the user asks, or under a project rule that allows it. When dispatching, all of these must hold:
- **Self-contained:** the prompt states the whole task, the files and the expected result.
- **Checkable:** there is a pass/fail check (lint and tests, a search with a concrete answer).
- **No shared state:** the subagent does not push, run cloud jobs, edit coordination files, merge or commit; the dispatching chat does those.
- **Isolated:** agents that edit code run with `isolation: "worktree"`; the dispatching chat reviews the diff, runs the checks and commits.

Keep it to two at a time, use the cheapest model that fits, ask for a short report (conclusion and paths), and skip tasks the chat can do in a couple of tool calls. A subagent never uses Opus unless the task's tag already justified it.

## Clearing or compacting a chat

An agent cannot read the context meter reliably; the user can. Suggest from task boundaries and visible signs, once per boundary, in one line at the end of a message.

- **Suggest `/clear`** when a unit of work is committed and recorded (inbox or handoff file) and the next task is a new unit. Give a resume prompt to paste afterwards: chat name, folder, branch, any reserved slot, and the next task with its tag.
- **Suggest `/compact <what to keep>`** when the task continues but the history is heavy (about a dozen large tool outputs, a resolved side thread). Name what must survive: open hypotheses, ruled-out causes, paths, commit hashes. First write the ruled-out causes to a handoff file, because a summary can distort them.
- **Suggest neither** in the middle of a debugging thread.

## Several chats on one repository

When more than one chat works on a repository, or a project's `CLAUDE.md` mentions an inbox or handoff folder, use the `workflow:multi-chat` skill. It holds the coordination protocol: worktrees, the inbox, handoff reports and messaging.
