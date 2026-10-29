---
name: multi-chat
description: Coordination protocol for several Claude chats working on one repository at once - a lead chat that assigns tasks and merges into a dev branch, workers that claim tasks by the files they touch, one worktree and branch per chat, the shared INBOX.md status page, the "Where each chat works" table, handoff reports, messaging other chats with ListAgents/SendMessage, and merging. Use at the start of any chat in a repository that has a handoff folder or an INBOX.md, when the user names your chat (for example "you are thesis-a2"), when another session messages you, or when setting up multi-chat work in a new project.
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

## Orchestration: lead + workers (default)

Chats are not tied to folders. Any chat may edit any file; conflicts are prevented per **task**.

- **Lead**: one chat, named in the inbox table. Turns the user's requests into board tasks, assigns them, keeps the inbox current, and is the fallback reviewer. May take tasks itself. To change the lead, edit the table's Role column and message the peers.
- **Workers**: claim a board task, work on `task/<ID>-<slug>` in their own worktree, set status `review`, add a row to the review queue, message the idle chats.
- **Review queue (pool, not a dedicated reviewer):** the industry pattern is GitHub's team review auto-assignment (round robin or load balance across members), not one reviewer. Any chat other than the author claims the oldest unclaimed row before starting new work, reviews (`/code-review`), and merges on green when the review finds no blocking issue and the project's rules let agents merge. An author never reviews its own work. The lead takes rows nobody claimed within a session. Chats act only when prompted, so the author's `SendMessage` to idle peers (or a peer's `/loop`) is what starts a review.
- **`dev`** is the integration branch, checked out in its own worktree (`../<project>-integration`) where only the lead merges. `dev` reaches `main` only with the user's approval.
- **Claim rule:** each board row lists the files it touches. Do not start a task whose files overlap another `in progress` task; message its owner or the lead. If you need more files, add them to the row first.
- **Lifecycle:** `open` → `assigned` / `in progress` → `review` → `done`. Workers start every new task from the latest `dev`.
- **Scaling:** one lead plus about three workers; past that, split the board by milestone. New chat = one new worktree plus one table row.
- **Skip orchestration** (one chat, or two chats on clearly unrelated work) only when the user says so.

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

Quick setup (about five minutes; do it all without asking, these steps are reversible):

1. Create `.handoff/` in the main checkout and add it to `.git/info/exclude` (not `.gitignore`, so no tracked file changes).
2. Create the integration branch and worktree: `git branch dev <default branch>` then `git worktree add ../<project>-integration dev`.
3. Create one worktree per chat: `git worktree add ../<project>-<chat> -b <chat>/work dev`. The first chat may keep the main checkout, on its own branch (never on `main`).
4. Copy `templates/INBOX.md` and `templates/RULES.md` into `.handoff/` and fill in paths, chat names and the lead.
5. Add `CLAUDE.md` to `dev` (commit it there) with the project's hard limits and a short "Working in several chats" section that names the handoff folder and says to use this skill. Hard limits live in `CLAUDE.md`, in git, so no handoff file can relax them.
6. `ListAgents`, then `SendMessage` each peer the handoff path, the lead's name and its first task.
