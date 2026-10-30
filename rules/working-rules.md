# Working rules (all projects)

Loaded in every session through `~/.claude/CLAUDE.md`. This file holds only what applies to every task; procedures for specific situations live in the `workflow` plugin's skills and load when needed (standard: keep always-loaded instructions short and move task-specific detail to on-demand skills, since compliance falls as the instruction count rises, IFScale arXiv 2507.11538; checked 2026-10-30). A project's `CLAUDE.md` adds to these and may make them stricter; nothing here relaxes a limit a project sets.

## Hard limits (a project may tighten, never loosen, except through the exceptions named here)

- Ask before anything destructive (deleting or overwriting data you did not create, rewriting git history, force-pushing) and anything outward-facing (merging a PR, pushing to `main` or to a public repository, publishing, uploading to any external service, spending money). Exceptions: pushing your own feature branch and opening its PR ("Git"); merges in a confirmed solo-fast project (`workflow:pr-review`); the config repo ("Git").
- Never read, write or delete credential files (`~/.kaggle`, `.env` files holding secrets, tokens, `~/.claude/.credentials.json`). Read and update `.env.example` instead.
- Ask before a long paid or cloud job. The default threshold is 30 minutes; a project may set another.

## Decision rights

The test is reversibility: if a choice can be undone with a revert, a rerun or a file edit, make it. Asking stops the flow, so ask only when a wrong guess is expensive or only the user knows the answer.

- **Decide and proceed:** implementation choices, task order, which chat or subagent does a task, commits on your feature branch, defaults for open questions, doc fixes, stale facts, tests, lint and format, coordination files.
- **Decide, then tell** (one line in the reply or the project's DONE.md, with the reason and the undo): a default on an open design question; a changed pinned version, preset or tolerance, with the run that justifies it; reordered or added milestones.
- **Ask first:** everything under Hard limits; choices only the user can judge (thesis or paper claims, licensing, public content, a budget); relaxing a project's limit; **adding or changing any rule** (user's decision, 2026-10-29): load `workflow:rule-change` before proposing one.

When unsure, take the lower-asking tier if the action is reversible. Do not ask for confirmation of something already requested, or which of two reversible options to take.

**How to ask:** a choice among 2–4 options goes through `AskUserQuestion`, recommended option first and marked "(Recommended)", one self-contained question per decision. Plain text only for open questions or when the tool is unavailable. Decisions that can wait become `needs-you` issues ("Replies").

**Unclear requests** (user's decision, 2026-10-30): ask one clarifying question first only when the request has two plausible readings, they lead to substantially different work, and the conversation, code and project files do not settle it; a term that fits two things in context (two hooks, two PRs) counts. Otherwise state "Reading X as Y" in one line and proceed.

## Replies and items for the user

- **Push only what blocks the task in hand.** End a turn with at most 3 lines: the step that blocks the current task (plain words, a link, the time it takes); "N new in [INBOX.md](…)" only if the inbox gained an item this turn; a `/clear` or `/compact` suggestion only when "Context" says so. Say nothing when nothing blocks. Never end with a bare list of IDs.
- **Items for the user live on GitHub** (user's decision, 2026-10-30): a PR or issue labelled `needs-you`, with the user as reviewer or assignee. The body says what it is, why it needs the user, the exact action, the time it takes, and what happens if nothing is done. In a public repo, private content stays in a local ticket and the issue says only "private item; ask in chat". Handoff files are the agents' notes; never ask the user to read them.
- **Status comes from `gh` in the same turn**, never from memory or a handoff file (user's decision, 2026-10-30).
- **Markdown** (user's decision, 2026-10-30): in chat replies, no `#` headings; a heading is a line of its own as `==Heading==`. Files keep normal `#` headings and never use `==`.

## Git

- **Tasks:** one GitHub issue per task; its PR says `Closes #n` (user's decision, 2026-10-30). A repo without a GitHub remote keeps tickets in files.
- **Commit** on the current feature branch without asking; never on `main` (except the config repo). One commit is one coherent change with its tests and docs, staged with `git add <paths>`, committed once the project's lint and tests pass. Never commit run outputs, data, build artefacts, credentials, private identifiers, or changes you did not make. Message: imperative subject, a body with the why and known gaps, the harness's attribution trailer.
- **Push** your own feature branch (`git push -u origin <branch>`, never `--force`) when it is green and the repo is private, or public with the user's standing approval in the project's `CLAUDE.md` and secret-scanning push protection on; otherwise ask. Push at a natural boundary. Once its PR has merged, follow-ups go on a new branch off the default branch (the `push_guard` hook refuses a push to a merged PR's branch).
- **Switching machines** (user's decision, 2026-10-30): unfinished work may be committed as `wip: …` and pushed to your own feature branch; keep committing on top of it, never amend or reset it.
- **GitHub identity:** agents write to GitHub as `phuchai-bot`. Check `gh auth status` before a write; never `gh auth switch`, `login` or `logout` yourself; if the bot is not active, ask.
- **Config repo `~/claude-config`** (authorised by the user): commit and push to `main` after every change, without asking. It is public: check `git diff` for credentials, private paths and private-project identifiers first, and stop and ask if there are any. No force-push, no history rewrite. It keeps pushing as the user.

## Model and effort

The user picks the model and effort. At the start of each task, say in one line which it needs, tagged `[Sonnet, medium, no plan mode: reason]`, and say so if the current model is a poor fit; the same tag goes on every proposed next step and decision item. Sonnet is the default; prefer Sonnet at high effort before Opus. An Opus tag must name the specific difficulty (for example "bug unexplained after a Sonnet pass"); "new feature" or "important" is not a reason. `max` effort only when the user asks. Plan mode only when the design is still open.

| Task | Model, effort |
|---|---|
| Inbox and handoff updates, commits, merges, routine runs, logs | Sonnet, low |
| Small well-specified edits, tests for existing behaviour, lint | Sonnet, medium |
| New features, ports, schema changes, docs and reports; first-pass debugging | Sonnet, high |
| Bug unexplained after a Sonnet pass; bug needing several components held at once; open design question with a costly wrong answer (plan mode) | Opus, high (xhigh only if high failed) |
| Final wording of thesis, paper or public claims | Opus, high |

## Context

The user sees the context meter in the status line; you do not. Suggest once per task boundary (work committed and recorded; opening, reviewing or merging a PR counts), in one line at the end of the message, never in the middle of a debugging thread:

- `/clear` with a resume prompt (chat name, folder, branch, next task with its tag) when the next task is unrelated and this chat did more than about 15 tool calls, when the chat passed about 40 tool calls, or when quality is slipping (the same correction twice). Do not start the next task in that turn.
- `/compact <what to keep>` only when the task continues and its state cannot be written to files yet; write ruled-out causes to a file first, because a summary can distort them.

## Skills to load (the `workflow` plugin)

- `workflow:pr-review`: before opening, reviewing or merging a pull request, or deferring work out of one.
- `workflow:new-project`: at the start of a project (tier, mode, one-time GitHub setup, the bot's push config), or when adding environment settings or a `.env`.
- `workflow:multi-chat`: when several chats share a repository, or the project's `CLAUDE.md` names an inbox or handoff folder.
- `workflow:rule-change`: before proposing or editing any rule, here or in a project, and for any proposal with more than about five items.
- `workflow:subagents`: before dispatching a subagent (only when the user asks or a project rule allows).
- A project whose recorded mode is not **build**: read `~/claude-config/modes/<mode>.md` before starting work.
