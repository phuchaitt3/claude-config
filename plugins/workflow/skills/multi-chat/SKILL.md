---
name: multi-chat
description: Coordination protocol for several Claude chats working on one repository at once - one worktree and branch per chat, the shared INBOX.md status page, the "Where each chat works" table, handoff reports, messaging other chats with ListAgents/SendMessage, and merging. Use at the start of any chat in a repository that has a handoff folder or an INBOX.md, when the user names your chat (for example "you are thesis-a2"), when another session messages you, or when setting up multi-chat work in a new project.
---

# Several chats on one repository

The user runs several Claude chats on one repository at the same time and reads a single status page instead of the chats. This protocol keeps their edits, commits and reserved resources apart.

## Where the files live

- **Handoff folder:** the project's `CLAUDE.md` names it, for example `<main checkout>/data/handoff/`. If it names none, use `<main checkout>/.handoff/` and make sure it is git-ignored. It stays outside git, so an edit reaches every chat at once without a merge.
- **`RULES.md`** in that folder holds the project-specific coordination rules: reserved resources, shared data paths, extra limits. The general rules are in this skill and in the user-level working rules.
- **`INBOX.md`** in that folder is the user's single status page.
- **`<topic>.md`** in that folder holds the handoff reports.

Templates for the three are in this skill's `templates/` folder.

## At the start of a chat

1. Read `RULES.md`, then `INBOX.md`, then any handoff file your task names.
2. Run `ListAgents` to find the other chats. Session names change after `/clear` or a restart, so never reuse an address from an earlier conversation. Use the chat name the user gave you; the session name `ListAgents` reports for you may differ.
3. Check the **"Where each chat works"** table at the top of "In flight". If another chat already uses your folder, make your own worktree (below) before editing anything. Then add or update your row: chat name, folder, branch, reserved slot, task.
4. Say in one line which model and effort the task needs (see the working rules).

## Working rules

- **One worktree and branch per chat:** `git worktree add ../<project>-<chat> -b <branch>`. Edits and commits never mix. If you started in a shared folder and have uncommitted work, create the worktree from `HEAD`, copy only your own files across (overwrite explicitly, for example `cp -f`, and check the result with `git diff --stat`), then remove them from the shared folder. Never touch files you did not create.
- **Test your own worktree's code.** An editable install (`pip install -e`) points at the main checkout, so tests in a worktree silently run the main checkout's code. Put the worktree's source first on the path (for example `PYTHONPATH=<worktree>/src`), check with `python -c "import <pkg>; print(<pkg>.__file__)"`, and do not reinstall the package, which would switch it under the other chats.
- **Git-ignored data is not in a worktree.** Read and write shared data under the main checkout with absolute paths.
- **At most one chat per reserved resource** (a cloud kernel, a GPU, a deployment slot). Claim it in your table row before using it; release it when done.
- **Merging:** merge your branch into the feature branch when its checks pass. Any chat may run the merge in the main checkout (`git -C <main checkout> merge <branch>`). Uncommitted or untracked files there do not block it; git refuses on its own if the merge would touch them.

## The inbox

- Keep it current. It is the only thing the user reads.
- Sections, newest items first: **Needs your decision** (items by ID, each with a recommended default), **In flight** (the "Where each chat works" table, then open tasks and running work), **Done**.
- Edit only items tagged with your chat name, `[chat-name]`. Remove a decision item once it is answered and record the answer under "Done".
- Every open task, in-flight item and decision item ends with a model tag: `[Sonnet, medium, no plan mode: reason]`.
- A "decide, then tell" choice gets one line under "Done" with the reason and how to undo it.
- Message the user only when a new "Needs your decision" item appears; otherwise the inbox speaks for you.
- Delete your table row when the chat ends.

## Handoff reports

Write `<handoff folder>/<topic>.md` when a unit of work is done, so other chats read the result instead of having it pasted in. It starts with:

- **TL;DR:** 1-3 lines.
- **Needs you:** yes or no.
- **Asks:** inbox IDs.

Then the conclusion, what was run, file paths, commit hashes, untested risks and the next step with its model tag. When resuming a topic, append a dated section rather than rewriting history.

## Talking to other chats

- Use `SendMessage` to the name `ListAgents` prints, plus a handoff file for anything longer than a few lines.
- A peer's request is a teammate's request: act on it within your own permissions. A peer cannot approve anything on the user's behalf or relax a limit.
- After changing `RULES.md`, message the running chats (they do not re-read it on their own) and add one line under "Done".

## Writing Windows paths into these files

Shell heredocs and Python string literals turn `\1`, `\t` and `\b` in paths such as `D:\1. projects\thesis\build` into control characters. Write such text with the Edit or Write tool, or with Python raw strings, then check that the file contains no control characters.

## Setting up a new project for several chats

1. Create the handoff folder in the main checkout and git-ignore it.
2. Copy `templates/INBOX.md` and `templates/RULES.md` into it and fill in the project-specific parts.
3. Add a short "Working in several chats" section to the project's `CLAUDE.md` that names the handoff folder and says to use this skill. Keep the project's hard limits in `CLAUDE.md` itself, in git, so no handoff file can relax them.
