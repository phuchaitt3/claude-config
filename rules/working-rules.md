# Working rules (all projects)

Loaded in every session through `~/.claude/CLAUDE.md`. A project's own `CLAUDE.md` adds to these and may make them stricter; nothing here relaxes a limit a project sets.

## Hard limits (a project may tighten, never loosen)

- Ask before anything destructive (deleting or overwriting data you did not create, rewriting git history, force-pushing) and anything outward-facing (merging a PR, pushing to `main` or to a public repository, publishing, uploading to any external service, spending money). Pushing your own feature branch to a private remote and opening a PR for it are allowed (a PR changes nothing until merged and can be closed), and the config repo `~/claude-config` is committed and pushed to `main` after every change; see "Commits".
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

**How to ask:** when the user is present and the answer is a choice among 2–4 options (yes/no, approve/hold, A/B/C), ask with the `AskUserQuestion` tool, recommended option first and marked "(Recommended)", one question per decision, each self-contained (it may be read without the rest of the reply). Use plain text only for open-ended questions or when the tool is unavailable (subagents, background runs). Decisions that can wait go in the project's inbox under "Needs your decision" instead.

**Asking the user for something: notification short, ticket complete** (industry pattern: a short notification points to a self-contained ticket). The user cannot be expected to remember earlier turns.
- **Chat turn ending:** at most 3 lines. Line 1: the one thing that needs the user now, in plain words with a link and the time it takes. Line 2: how many other items wait and where (the inbox "Needs your decision" section). Say nothing when nothing new needs the user. Never end a turn with a bare list of IDs ("D6, #9, D5").
- **Only what changed:** mention an item in chat when it first appears or turns urgent, not every turn.
- **Ticket (inbox item or issue):** every item stands alone, with five fields: what it is (plain words), why it needs the user, the exact action (link or click path), the time it takes, and what happens if the user does nothing. Most urgent first. List only what blocks work.

## Project tiers (proposed by the agent, confirmed by the user)

At the start of a new project, propose a tier in one line with the reason; the user confirms once, then record it at the top of the project's `CLAUDE.md`. Never pick or change a tier without that confirmation. A confirmed **solo-fast** tier is the user's standing exception to the Hard limits' "ask before merging a PR"; nothing else in the Hard limits is relaxed by any tier.

| Tier | When | Pull requests |
|---|---|---|
| **solo-fast** | personal project, no users, no money, no private data | agents open PRs freely; any chat other than the author reviews and enables auto-merge (see "Review and merge"); the user merges only PRs touching `CLAUDE.md`, `.github/`, infra/deploy, lockfiles, secrets, money or public positioning |
| **standard** (default) | shared repo, collaborators, or anything others depend on | agents push branches; the user opens and merges PRs |
| **strict** | thesis/paper claims, client work, production with users | as standard, plus the user reviews every diff before merge |

Hard limits (credentials, force-push, paid jobs over the threshold, publishing) apply in every tier. solo-fast needs the permission rules `Bash(gh pr create:*)`, `Bash(gh pr comment:*)` and `Bash(gh pr merge:*)` in the project's `.claude/settings.local.json`; the user adds them. An allow rule matches only a command that starts with it, so run these commands plain (`gh pr create --repo … --body-file …`), never chained after `cd … &&` or with `$(…)`; a chained call falls to the auto-mode classifier and is denied.

## Review and merge (industry pattern, checked 2026-10-29)

Sources: GitHub's rules for required approvals and for Copilot-agent PRs, GitHub team review auto-assignment, Google/Chromium OWNERS review, and published guidance on agent approval authority.

- **Author ≠ approver.** This is the one fixed rule everywhere: GitHub does not count an author's own approval, and whoever assigned a Copilot agent cannot approve its PR. A chat never reviews or merges its own PR, and an agent-authored PR that an agent approved counts as unreviewed by anyone independent.
- **General review comes from a pool, not a dedicated reviewer.** This matches GitHub's team auto-assignment (round robin or load balance) and Google's LGTM, which any engineer can give. Chats of the same model with the same `/code-review` recipe gain nothing from a "reviewer" role. What gives a review its value is independence (a fresh context without the author's assumptions), and a dedicated reviewer chat becomes a bottleneck that idles until prompted.
- **Specialize by risk, not by agent.** Industry practice puts named owners on risky paths (CODEOWNERS, Google OWNERS and readability). Here the user is that owner: risky paths (`.github/` risk items, `infra/`, auth, secrets, lockfiles, money, public content) get a deeper review (`/security-review` or `/code-review high`), and the user merges them. Everything else gets `/code-review medium`.
- **Merge authority follows the gate, not the person.** On GitHub anyone with write access may merge once the ruleset is satisfied. So the reviewer does not merge by hand: when the review finds no blocking issue and the PR is not a user-merge item, it runs `gh pr merge <n> --auto --squash`, and GitHub merges when the required checks pass. Restricting merges to the lead adds no safety when every chat is the same model under the same account; it only adds a queue.
- **All chats act as the user's GitHub account**, so GitHub cannot tell author from reviewer, and a required-approvals count cannot enforce author ≠ approver. The inbox rule enforces it. The hard gates are required CI checks and the user-merge list.
- **Fallback:** an unclaimed PR goes to the lead, except a PR the lead wrote. That one goes to the user, never to its author.
- **Invest in checks over review.** Studies find agent-only review catches less than human review, and review attention fades with habit. Tests, typing, evaluation jobs and merge queues do not fade, so each one added is worth more than another review pass.
- **Post the review** as a PR comment (`gh pr comment <n> --body-file …`) stating the verdict, what was checked, findings dropped after checking, and for a `.github/` change, that no user-merge item is touched.

## Commits

You may commit on the current feature branch without asking. Never commit to `main`, except in the config repo (next section).

**Why `main` is protected:** in project repositories (several chats, collaborators, reviewable history) the usual practice is a protected default branch plus review, so agents work on branches and a human or lead merges. A single-owner config repo has no reviewer, so a branch-and-merge step there adds friction and no safety.

### The config repo (`~/claude-config`) — exception, authorised by the user

This repo is synced between machines, so a change that is not pushed is lost to the other machine. For this repo only, commit and push to `main` yourself after every change to it, without asking. The remote is **public**, so every push publishes: before committing, run `git diff` and check that nothing is a credential, token, private path or identifier from a private project. If anything is, stop and ask. Other limits still hold: no force-push, no history rewrite, no other repository.

**Pushing** follows the usual practice for coding agents (GitHub Copilot's coding agent, the Claude Code GitHub Action): the agent pushes its own branch, a human reviews and merges. So you may push your feature branch without asking (`git push -u origin <branch>`), after the branch is green, when all of these hold:

- the remote already exists and the repository is **private** (check once, for example `gh repo view --json visibility`, or ask if you cannot tell); pushing to a public repository publishes, so ask first;
- the branch is not `main` or the default branch, and the push is not a force push (no `--force` or `--force-with-lease`), so nothing on the remote is overwritten;
- `git status` shows nothing staged or committed that the project keeps out of git (data, run outputs, credentials, identifiers).

Still ask first: merging a PR, pushing to `main`, force-pushing, deleting a remote branch, creating a repository or changing its visibility. Push at a natural boundary (a unit committed, end of a session), not after every commit.

- **One commit = one coherent change** (a feature, a fix, a tooling change, a doc update) with its tests and docs. Do not mix unrelated changes: stage with `git add <paths>`, not `git add -A`.
- **Commit when a unit is done and green**, not at the end of the session. Run the project's lint and tests first; never commit a half-working state or a failing test.
- **Message**: a short imperative subject, then a body explaining *why*, plus any known gap (for example "not yet run on real data"). Add the attribution trailer the harness specifies.
- **Never commit** run outputs, data, build artefacts, credentials or private identifiers. Check `git status` before adding.
- Never commit, stash or revert changes you did not make.

## Model and effort per task

The user picks the model (`/model`) and effort by hand. At the start of each task, say in one line which model and effort it needs; if the current model is a poor fit, say so before starting. Plan mode: yes only when the design is still open.

**Budget rule:** Sonnet is the default for everything. Opus costs much more and is reserved for tasks that are both hard and expensive to get wrong. Any task tag that names Opus must state the specific difficulty in a few words (for example "unexplained numeric drift after a Sonnet pass found nothing"). "New feature", "porting" or "important" are not reasons; an Opus tag without one is invalid. Before proposing Opus, say what a Sonnet attempt would miss. Prefer Sonnet at high effort first and escalate only if it fails or gets stuck; say in the handoff what was tried.

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

Keep it to two at a time, and do not dispatch work that is blocked on a long job or a user decision. A subagent starts cold, so its cost scales with how much it reads, not with the task's importance. To keep that small:
1. **Tight brief:** name the exact files, the goal and the check, so it does not explore.
2. **Cheapest model that fits:** a mechanical task on Haiku or Sonnet often costs less than doing it in an Opus chat.
3. **Short report:** ask for the conclusion and file paths, not file dumps.
4. **Skip tiny tasks:** if the chat can do it in a couple of tool calls, the cold start costs more.
5. **Fork when context matters:** a fork inherits the chat's context but runs on the chat's model, so it saves time, not money.

A subagent never uses Opus unless the task's tag already justified it.

## Clearing or compacting a chat

An agent cannot read the context meter reliably; the user can. Suggest from task boundaries and visible signs, once per boundary, in one line at the end of a message. Do not wait for auto-compaction at the limit: long contexts get worse before they fill.

- **Suggest `/clear`** when a unit of work is committed and recorded (inbox or handoff file) and the next task is a new unit. Give a resume prompt to paste afterwards: chat name, folder, branch, any reserved slot, and the next task with its tag.
- **Suggest `/compact <what to keep>`** when the task continues but the history is heavy (about a dozen large tool outputs, a resolved side thread, or the user says the context is over half full). Name what must survive: open hypotheses, ruled-out causes, paths, commit hashes. First write the ruled-out causes to a handoff file, because a summary can distort them.
- **Suggest neither** in the middle of a debugging thread.

## Several chats on one repository

When more than one chat works on a repository, or a project's `CLAUDE.md` mentions an inbox or handoff folder, use the `workflow:multi-chat` skill. It holds the coordination protocol: worktrees, the inbox, handoff reports and messaging.
