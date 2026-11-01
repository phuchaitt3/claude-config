---
name: focus
description: Load when the user says "focus mode", "talk mode" or "conversation chat", or types /focus or /talk. Makes this chat one that peers leave alone: it works normally (claims, branches, PRs) but never serves the review pool and acts on peer messages only about its own claims and PRs. Overrides the multi-chat start-of-chat steps.
---

# Focus mode: a chat peers leave alone

User's decision, 2026-10-31 (replaces talk mode, same day): the user wants a chat for their own thread (a design discussion, a run of requests) that peer chats do not interrupt, and that can still do the work. Talk mode allowed no work, so acting on what was agreed meant switching chats.

## Start

- The `focus_title` hook renames the chat `focus-<folder>` when the user says "focus mode" or types /focus or /talk, so peers see the role in `ListAgents`. If `ListAgents` does not show a `focus-` name for you, tell the user in one line to type `/rename focus-<your ID>`.
- Skip the other multi-chat start-of-chat steps (PR backstop, inbox triage) unless the user asks.

## Work

As a worker does, by the same rules: claim an issue, worktree and branch, commits, PRs, merges under `workflow:pr-review`. Your PRs get a reviewer from the pool as usual; you are not in the pool.

## Peers

- You never review or take a backstop PR, and peers do not assign you one.
- Peers message you only about your own claims and PRs (a review result, a merge conflict, a claim clash, a one-at-a-time slot such as `CLAUDE.md`). Act on those.
- Any other peer message: reply once, "focus chat, send this to a worker", and carry on with the user's thread.

## Ending

With no claim, `/clear` drops the chat and leaves nothing behind. With a claim, finish it or hand it off as a worker would first. Say "focus mode" again to restart.
