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
> 3. **Then work.** Run `python <this skill's folder>/next_task.py` in the repository. It lists the startable issues bottleneck-first (multi-chat skill, "Bottlenecks first"); take the first one the rules below let you take, and make the `fix:` lines it prints (a missing dependency link or `priority:now` label) on the way. If it cannot reach GitHub, take `priority:now`, else the oldest unblocked `priority:next`, else the oldest unblocked `priority:later`. Claim it as the project says (label plus a comment listing the files), verify the claim, branch from the latest default branch in its own worktree, finish it, open the PR, then start the next round.
> 4. **Route or skip** an issue:
>    - needs an architecture or design choice: write a brief in the project's design folder, open it as a PR, move on;
>    - touches a path the project reserves for the user (workflow files, infra, deploy config, `CLAUDE.md`, `.claude/`, lockfiles unless the project's rule allows): do the work and open the PR with `needs-you` and the user as reviewer, while that queue is under the project's limit (default 3); the gate is the merge, not the work;
>    - skip (leave it, say nothing more) only when it: carries `needs-you`; needs a decision only the user can make; involves secrets; calls a paid API at scale; overlaps a file another chat has claimed; or needs a tool or large download the machine lacks.
> 5. **Stop** the loop (do not schedule another round) when: no issue is left that steps 3 and 4 can take; the project's limit on items waiting for the user is reached; CI fails twice on the same task; or you are unsure the task is yours. Never ask the user what to do next; say why it stopped in one line (user's decision, 2026-10-31; standard: bounded autonomy, where an agent escalates only at the edge of its authority and halts on explicit stop conditions, and Kanban pull of the next ready item; checked 2026-10-31).
> 6. Between rounds say nothing unless something blocks the user. When the loop stops, give one line: what was done (PR links) and why it stopped.

## Pacing

After opening a PR, start the next round at once in a new worktree; do not wait for its review or CI (user's decision, 2026-10-31; standard: Kanban pull with a WIP limit on review, about 1-2 items per reviewer, and background coding agents such as Copilot coding agent open a PR and move on; checked 2026-10-31). Wait only when:

- 2 of your own PRs are open with no review yet: review others' PRs, or schedule the next round in 5 to 10 minutes;
- the next eligible task depends on an open PR's change.

When nothing is eligible, stop rather than poll. Never schedule waits shorter than 60 seconds.

## Stopping

The user stops it by telling the chat to stop. The chat then ends the loop and finishes or parks its current task (commit as `wip:` on its own branch if unfinished).
