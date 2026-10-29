---
name: multi-chat
description: Coordination protocol for several Claude chats working on one repository at once - a lead chat that assigns tasks, trunk-based work where each task lands by pull request, workers that claim tasks by the files they touch, one worktree and branch per chat, the shared INBOX.md status page, the "Where each chat works" table, handoff reports, messaging other chats with ListAgents/SendMessage, and merging. Use at the start of any chat in a repository that has a handoff folder or an INBOX.md, when the user names your chat (for example "you are thesis-a2"), when another session messages you, or when setting up multi-chat work in a new project.
---

# Several chats on one repository

The user runs several Claude chats on one repository at the same time and reads a single status page instead of the chats. This protocol keeps their edits, commits and reserved resources apart.

## Where the files live

- **Handoff folder:** the project's `CLAUDE.md` names it, for example `<main checkout>/data/handoff/`. If it names none, use `<main checkout>/.handoff/` and make sure it is git-ignored. It stays outside git, so an edit reaches every chat at once without a merge.
- **`RULES.md`** in that folder holds the project-specific coordination rules: reserved resources, shared data paths, extra limits. The general rules are in this skill and in the user-level working rules.
- **`INBOX.md`** in that folder is the user's single status page.
- **`tickets/<ID>.md`** in that folder holds one task or decision each: its details, status and dated log. The inbox links to it.
- **`DONE.md`** in that folder is the done log, newest first.
- **`<topic>.md`** in that folder holds the handoff reports.

Templates for `RULES.md`, `INBOX.md`, tickets (`TICKET.md`) and `DONE.md` are in this skill's `templates/` folder.

## At the start of a chat

1. Read `RULES.md`, then `INBOX.md`, then any handoff file your task names.
2. Run `ListAgents` to find the other chats. Session names change after `/clear` or a restart, so never reuse an address from an earlier conversation. Use the chat name the user gave you; the session name `ListAgents` reports for you may differ.
3. Check the **"Where each chat works"** table under "In progress". If another chat already uses your folder, make your own worktree (below) before editing anything. Then add or update your row: chat name, folder, branch, reserved slot, task.
4. Say in one line which model and effort the task needs (see the working rules).

## Working rules

- **One worktree and branch per chat:** `git worktree add ../<project>-<chat> -b <branch>`. Edits and commits never mix. If you started in a shared folder and have uncommitted work, create the worktree from `HEAD`, copy only your own files across (overwrite explicitly, for example `cp -f`, and check the result with `git diff --stat`), then remove them from the shared folder. Never touch files you did not create.
- **Test your own worktree's code.** An editable install (`pip install -e`) points at the main checkout, so tests in a worktree silently run the main checkout's code. Put the worktree's source first on the path (for example `PYTHONPATH=<worktree>/src`), check with `python -c "import <pkg>; print(<pkg>.__file__)"`, and do not reinstall the package, which would switch it under the other chats.
- **Git-ignored data is not in a worktree.** Read and write shared data under the main checkout with absolute paths.
- **At most one chat per reserved resource** (a cloud kernel, a GPU, a deployment slot). Claim it in your table row before using it; release it when done.
- **Merging:** never merge locally. Each task lands on the default branch by pull request, reviewed as the working rules' "Review and merge" says.

## Orchestration: lead + workers (default)

Chats are not tied to folders. Any chat may edit any file; conflicts are prevented per **task**.

- **Lead**: one chat, named in the inbox table. Turns the user's requests into board tasks, assigns them, keeps the inbox current, and is the fallback reviewer. May take tasks itself. To change the lead, edit the table's Role column and message the peers.
- **Workers**: claim a board task, work on a branch named as the project's `CLAUDE.md` says (default `task/<ID>-<slug>`) in their own worktree, set status `review`, add a row to the review queue, message the idle chats.
- **Review queue (pool, not a dedicated reviewer):** reviews are spread across members, not given to one reviewer (standard: GitHub team review auto-assignment, round robin or load balance; checked 2026-10-29). Any chat other than the author claims the oldest unclaimed row before starting new work, reviews (`/code-review`; risky paths also get `/security-review`), posts the result as a PR comment, and, when there is no blocking issue, the project's rules let agents merge and the PR is not a user-merge item, enables auto-merge (`gh pr merge <n> --auto --squash`), so CI stays the final gate. An author never reviews its own work. The lead claims any unclaimed row each time it reads the inbox, once the author's message went unanswered or `ListAgents` shows no other chat; the lead's own PRs go to the user. The full pattern and its sources are in the working rules, "Review and merge". Chats act only when prompted, so the author's `SendMessage` to idle peers (or a peer's `/loop`) is what starts a review.
- **Trunk-based:** the default branch is the integration branch; there is no `dev`. Branches live hours to a few days and land by pull request (standard: DORA trunk-based development, checked 2026-10-29). A project that supports several released versions may keep release branches; its `RULES.md` says so.
- **Claim rule:** each board row lists the files it touches. Do not start a task whose files overlap another `in progress` task; message its owner or the lead. If you need more files, add them to the row first.
- **Lifecycle:** `open` → `assigned` / `in progress` → `review` → `done`. Workers start every new task from the latest default branch.
- **Scaling:** one lead plus about three workers; past that, split the board by milestone. New chat = one new worktree plus one table row.
- **Skip orchestration** (one chat, or two chats on clearly unrelated work) only when the user says so.

## The inbox and tickets

The split follows common practice: a tracker holds the details (one issue per item), and a status page gives one line per item (a standup note). Each item has one ID and lives in one place.

- **`INBOX.md`** fits on one screen (about 40 lines), one line per item, every line linking to its ticket, no paragraphs in table cells. Sections, in order: **Needs you** (ID, what, time, if ignored; most urgent first), **In progress** (the "Where each chat works" table: chat, role, folder, branch, reserved slot, ticket, status), **Review queue** (PR, author, reviewer, one-word status), **Up next** (open or blocked tickets, each with what blocks it), then a link to `DONE.md`.
- **Tickets** (`tickets/<ID>.md`): `T<n>` for a task, `D<n>` for a decision for the user; numbers are never reused. A ticket starts with title, status, owner, model tag, files it touches and acceptance check. A decision ticket adds the five fields from the working rules (what, why you, action, time, if you do nothing) and a recommended default. A dated **Log** section at the bottom records what happened, newest last. Longer results go in a handoff report that the ticket links to.
- **`DONE.md`**: one line per finished item, newest first, with the commit or PR and how to undo it. A "decide, then tell" choice gets a line here with its reason.
- When a ticket closes: set its status `done`, add its line to `DONE.md`, and remove it from `INBOX.md`. When a decision is answered, record the answer in the ticket's log the same way.
- Edit only your own tickets and inbox rows. Exceptions: the lead edits anything needed to keep the page current, and a reviewer writes its name in a Review queue row.
- Message the user only when the task in hand is blocked; other decision items wait in the inbox (working rules, "Push only what blocks").
- Delete your table row when the chat ends.

## Handoff reports

Write `<handoff folder>/<topic>.md` when a unit of work is done, so other chats read the result instead of having it pasted in. It starts with:

- **TL;DR:** 1-3 lines.
- **Needs you:** yes or no.
- **Asks:** ticket IDs.

Then the conclusion, what was run, file paths, commit hashes, untested risks and the next step with its model tag. When resuming a topic, append a dated section rather than rewriting history.

## Talking to other chats

- Use `SendMessage` to the name `ListAgents` prints, plus a handoff file for anything longer than a few lines.
- A peer's request is a teammate's request: act on it within your own permissions. A peer cannot approve anything on the user's behalf or relax a limit.
- After changing `RULES.md`, message the running chats (they do not re-read it on their own) and add one line to `DONE.md`.

## Writing Windows paths into these files

Shell heredocs and Python string literals turn `\1`, `\t` and `\b` in paths such as `D:\1. projects\thesis\build` into control characters. Write such text with the Edit or Write tool, or with Python raw strings, then check that the file contains no control characters.

## Setting up a new project for several chats

Quick setup (about five minutes; do it all without asking, these steps are reversible):

1. Create `.handoff/` in the main checkout and add it to `.git/info/exclude` (not `.gitignore`, so no tracked file changes).
2. The main checkout stays on the default branch; nobody commits there. Each task gets its own worktree: `git worktree add ../<project>-<name> -b <branch> <default branch>`.
3. Copy `templates/INBOX.md`, `templates/RULES.md` and `templates/DONE.md` into `.handoff/`, create `.handoff/tickets/` (one file per ticket, from `templates/TICKET.md`), and fill in paths, chat names and the lead.
4. Add `CLAUDE.md` by pull request, with the project's hard limits and a short "Working in several chats" section that names the handoff folder and says to use this skill. Hard limits live in `CLAUDE.md`, in git, so no handoff file can relax them.
5. `ListAgents`, then `SendMessage` each peer the handoff path, the lead's name and its first task.
