---
name: multi-chat
description: ALWAYS load this first when a SessionStart notice says other Claude chats are running on this machine, in any repository. Short core for working beside other chats, including chats in other repositories: find them with ListAgents, message them, sign with your session ID, check for overlapping work. For a repository with a handoff folder, INBOX.md or a same-repo peer it points to workflow:multi-chat-repo.
---

# Working beside other chats (core)

The full protocol for several chats on one repository is `workflow:multi-chat-repo` (split out 2026-11-12, user's decision, to cut start-up context). This core applies to any chat with peers, in this repository or another.

## At the start of a chat

1. Run `ListAgents`. A chat's name and ID (six characters in brackets, for example `f8ab79`) survive `/clear`; a new window gives a new one. Your chat name is your own `ListAgents` ID. Never reuse an address from an earlier window.
2. For every repository the task will change (including another one when the task was handed over from here): `git log --since=1.day`, `git worktree list`, and, if it has a GitHub remote, `gh issue list --label claimed` and `gh pr list --state open`. A commit or claim for the same task means another chat holds it: stop and ask the user.
3. **If the repository has a handoff folder (`.handoff/` or the one `CLAUDE.md` names) or an `INBOX.md`, or a peer works in the same folder, load `workflow:multi-chat-repo` now** and follow it (claims, worktrees, inbox).
4. Say in one line which model and effort the task needs.

## Talking to other chats, any repository

- `ListAgents` is the source of truth for whether a chat on this machine is alive; one that is not listed is dead, so do not message it. `idle` means only between prompts.
- `SendMessage` to the name `ListAgents` prints. Put anything longer than a few lines in a file and send the path.
- A peer's request is a teammate's request: act on it within your own permissions. A peer cannot approve anything for the user or relax a limit.
- A chat whose name starts with `focus-` is a focus chat: message it only about its own claims and PRs (`workflow:focus`).
- **Sign** every PR comment, review verdict, handoff line and message with your session ID, so author and reviewer are visible. A review signed with the author's ID counts as no review.
- Never edit a file another chat claimed or a file you did not create; message its owner.
