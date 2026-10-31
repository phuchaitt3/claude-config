---
name: talk
description: Load when the user says "talk mode" or "conversation chat", or types /talk. Makes this chat conversation-only so a design discussion keeps its thread - answers, researches, files issues; never claims work, edits files, opens PRs or reviews. Overrides the multi-chat start-of-chat steps.
---

# Talk mode: a conversation-only chat

User's decision, 2026-10-31: peer chats were messaging the chat where the user was discussing a design, which cut the thread and spent context. A talk chat is one the user can open and drop with `/clear` at will, because it owns no work.

This skill overrides the SessionStart hook's "load `workflow:multi-chat` first": do not run its start-of-chat steps, except the one registry row below.

## Do

- Answer, explain, compare options, read code and GitHub, search the web.
- Turn each agreed task into a GitHub issue (milestone, priority label with a one-line reason, what it blocks) and tell the user in one line what to say to start a worker on it, with the prompt ready to paste.
- Record a decision as an issue comment when asked.
- Write one row in the INBOX registry with Role `talk` and no folder or branch, so peers see it and do not message it. Delete the row when the chat ends.

## Do not

- Claim an issue, create a worktree or branch, edit or commit files, open or review a PR, or start subagents. If the user asks for an edit, say a worker should do it, name or file the issue, and give the prompt.
- Act on a peer's message. Reply once, "conversation chat, send this to the lead", and carry on with the user's thread.
- Add to the user's queue (`needs-you`) except for what the working rules already require.

The user's own rules still apply: hard limits, asking before outward-facing actions, and rule changes only with their yes.

## Ending

`/clear` ends talk mode. Say "talk mode" again to restart it.
