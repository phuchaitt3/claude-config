---
name: self-drive
description: Load this when the user asks a chat to "self-drive", "loop", "pick tasks on its own" or "work without prompts", or types /self-drive. Starts a /loop in which this one chat reviews open PRs, then takes eligible issues without being prompted, and says when to skip an issue and when to stop. Never starts on its own; only the user starts it, per chat.
---

# Self-driving chat

(User's decision, 2026-10-31: per chat, started by the user's prompt only; saved globally so any project can use it. Standard: Kanban pull system, where a worker takes the next ready item when it has capacity, with a WIP limit; checked 2026-10-31.)

A chat never starts this by itself. The user starts it in a chat by asking, and it lasts until that chat ends or the user says stop. It does not change any project limit: a project's `CLAUDE.md` hard limits, user-merge paths and queue limits all still apply.

## Start

Run `/loop` with no interval (the model paces itself) and this brief. If the project uses the `workflow:multi-chat` protocol, load that skill first and follow its claim rules.

> Each round:
> 1. Sync: if the project has a handoff repo, `git -C <handoff> pull --rebase`. Run `gh pr list --state open`, `gh issue list --label claimed`, `git worktree list`.
> 2. **Review first.** Take the oldest open PR with no review comment from a chat other than its author and review it as `workflow:pr-review` says. Never review your own PR.
> 3. **Then work.** Take the first eligible issue: `priority:now`, else the oldest unblocked `priority:next`, else stop. Claim it as the project says (label plus a comment listing the files), verify the claim, branch from the latest default branch in its own worktree, finish it, open the PR, then start the next round.
> 4. **Skip** an issue (leave it, say nothing more) when it: needs an architecture or design choice (write a brief if the project has a design folder, then move on); carries `needs-you`; needs a decision only the user can make; touches a path the project reserves for the user (workflow files, infra, deploy config, `CLAUDE.md`, lockfiles unless the project's rule allows, secrets); calls a paid API at scale; overlaps a file another chat has claimed.
> 5. **Stop** the loop (do not schedule another round) when: nothing eligible is left; the project's limit on items waiting for the user is reached; CI fails twice on the same task; or you are unsure the task is yours. Say why in one line.
> 6. Between rounds say nothing unless something blocks the user. When the loop stops, give one line: what was done (PR links) and why it stopped.

## Pacing

If a round ended with a PR waiting on CI, schedule the next round for 5 to 10 minutes; if it ended with nothing to do, stop rather than polling. Never schedule waits shorter than 60 seconds.

## Stopping

The user stops it by telling the chat to stop. The chat then ends the loop and finishes or parks its current task (commit as `wip:` on its own branch if unfinished).
