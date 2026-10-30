---
name: multi-chat
description: ALWAYS load this first, before any other work, when the repository has a handoff folder (.handoff/) or an INBOX.md, or when the project's CLAUDE.md names one. Coordination protocol for several Claude chats on one repository: chat registry and claimed: labels, one worktree and branch per chat, the INBOX.md links page, tickets, DONE.md and handoff reports, lead and workers, messaging other chats with ListAgents/SendMessage, merging. Also use when the user names your chat (for example "you are thesis-a2"), when another session messages you, or when setting up multi-chat work in a new project.
---

# Several chats on one repository

The user runs several Claude chats on one repository at the same time and reads a single status page instead of the chats. This protocol keeps their edits, commits and reserved resources apart.

## Where the files live

- **Handoff folder:** the project's `CLAUDE.md` names it, for example `<main checkout>/data/handoff/`. If it names none, use `<main checkout>/.handoff/` and make sure it is git-ignored. It stays outside the project's repository, so an edit reaches every chat at once without a merge.
- **When the handoff folder is its own git repo** (a private one, so the notes follow the user between machines): start a session with `git -C <handoff> pull --rebase`; at the end of a session, and before any machine move, commit, `pull --rebase` and push your changes there. Never put `.env*` or other secrets in it. If the folder is not a git repo, skip this.
- **`RULES.md`** in that folder holds the project-specific coordination rules: reserved resources, shared data paths, extra limits. The general rules are in this skill and in the user-level working rules.
- **`INBOX.md`** in that folder is the agents' status page. The user's own queue is on GitHub (label `needs-you`, see the working rules, "Replies and items for the user").
- **`tickets/<ID>.md`** in that folder holds one task or decision each: its details, status and dated log. The inbox links to it.
- **`DONE.md`** in that folder is the done log, newest first.
- **`<topic>.md`** in that folder holds the handoff reports.

Templates for `RULES.md`, `INBOX.md`, tickets (`TICKET.md`) and `DONE.md` are in this skill's `templates/` folder.

## At the start of a chat

1. Read `RULES.md`, then `INBOX.md`, then any handoff file your task names.
2. Run `ListAgents` to find the other chats. Session names change after `/clear` or a restart, so never reuse an address from an earlier conversation. Use the chat name the user gave you; the session name `ListAgents` reports for you may differ.
3. Take your name from the registry ("Chat names" below) and write your row. Then check who is working where: `gh issue list --label 'claimed:*'`, `gh pr list --state open` and `git worktree list`. If another chat already uses your folder, make your own worktree (below) before editing anything. Then claim your issue with the label `claimed:<chat>` and re-read it (claim, then verify): if another chat's claim is also there, the one whose label was added later backs off. Fill in your row's folder and branch.
4. Say in one line which model and effort the task needs (see the working rules).

## Chat names: the registry (user's decision, 2026-10-30; standard: worker leases with heartbeats, as Kubernetes `Lease` objects; checked 2026-10-30)

The user opens chats without naming them, so chats name themselves. The "Worktrees and machines" table in `INBOX.md` is the registry: one row per active chat with **Chat** (`agent-N`), **Session** (the ID `ListAgents` shows, for example `4e6cdd`), **Role**, **Folder**, **Branch**, **Machine** and **Last seen** (date and time).

- **Take a name** at the start of a chat and after every `/clear` (the session ID changes): run `ListAgents`, then take the lowest `agent-N` whose row is free. A row is free when its session is not in `ListAgents` and its Last seen is more than 2 hours old. A name the user gives is used if it is free. Write your row, then re-read the table (claim, then verify): if another session wrote the same name, the one written later takes the next number.
- **Heartbeat:** update your Last seen each time you run the "check before each task" step. No timer.
- **Sign** every PR comment, review verdict, handoff line and message as `agent-N (session)`, so author and reviewer are visible in the record. A review signed with the author's name or session counts as no review.
- **Lead:** the Role column names it. If the lead's row is free (lease expired), the lowest-numbered active chat becomes lead and adds a line to `DONE.md`.
- Remove your row when you end the chat for good; otherwise it expires on its own.

## Working rules

- **One worktree and branch per chat:** `git worktree add ../<project>-<chat> -b <branch>`. Edits and commits never mix. If you started in a shared folder and have uncommitted work, create the worktree from `HEAD`, copy only your own files across (overwrite explicitly, for example `cp -f`, and check the result with `git diff --stat`), then remove them from the shared folder. Never touch files you did not create.
- **Test your own worktree's code.** An editable install (`pip install -e`) points at the main checkout, so tests in a worktree silently run the main checkout's code. Put the worktree's source first on the path (for example `PYTHONPATH=<worktree>/src`), check with `python -c "import <pkg>; print(<pkg>.__file__)"`, and do not reinstall the package, which would switch it under the other chats.
- **Git-ignored data is not in a worktree.** Read and write shared data under the main checkout with absolute paths.
- **At most one chat per reserved resource** (a cloud kernel, a GPU, a deployment slot). Claim it in your table row before using it; release it when done.
- **Merging:** never merge locally. Each task lands on the default branch by pull request, reviewed as the `workflow:pr-review` skill says.

## Orchestration: lead + workers (default)

Chats are not tied to folders. Any chat may edit any file; conflicts are prevented per **task**.

- **Lead**: one chat, named in the registry's Role column (see "Chat names"). Turns the user's requests into board tasks, assigns them, keeps the inbox current, and is the fallback reviewer. May take tasks itself. To change the lead, edit the table's Role column and message the peers.
- **Workers**: claim a GitHub issue (label `claimed:<chat>`), work on a branch named as the project's `CLAUDE.md` says (default `task/<ID>-<slug>`) in their own worktree, open the PR (its state is the status) and message the idle chats.
- **Review queue (pool, not a dedicated reviewer):** reviews are spread across members, not given to one reviewer (standard: GitHub team review auto-assignment, round robin or load balance; checked 2026-10-29). Any chat other than the author takes the oldest unclaimed open PR (one with no review comment from a non-author chat) before starting new work, reviews (`/code-review`; risky paths also get `/security-review`), posts the result as a PR comment (the comment is the claim and the record; there is no queue table) and files an issue for every finding not fixed in the PR, linked from the comment, and, when there is no blocking issue, the project's rules let agents merge and the PR is not a user-merge item, enables auto-merge (`gh pr merge <n> --auto --squash`), so CI stays the final gate. An author never reviews its own work. The lead takes any unclaimed PR each time it checks, once the author's message went unanswered or `ListAgents` shows no other chat; the lead's own PRs go to the user. The full pattern and its sources are in the `workflow:pr-review` skill. Chats act only when prompted, so the author's `SendMessage` to idle peers (or a peer's `/loop`) is what starts a review.
- **Trunk-based:** the default branch is the integration branch; there is no `dev`. Branches live hours to a few days and land by pull request (standard: DORA trunk-based development, checked 2026-10-29). A project that supports several released versions may keep release branches; its `RULES.md` says so.
- **Claim rule:** a task is a GitHub issue claimed with the label `claimed:<chat>` plus a comment listing the files it touches. Do not start an issue whose files overlap another claimed issue; message its owner or the lead. If you need more files, comment them on the issue first. Remove the label when the PR opens.
- **Lifecycle** is GitHub's own state, never copied into handoff files: open issue → `claimed:<chat>` label → open PR (`Closes #n`) → merged, which closes the issue. Workers start every new task from the latest default branch.
- **Scaling:** one lead plus about three workers; past that, split the work by milestone. New chat = one new worktree plus one worktree-table row.
- **Skip orchestration** (one chat, or two chats on clearly unrelated work) only when the user says so.

## The inbox and tickets

The split follows common practice: a tracker holds the details (one issue per item), and a status page gives one line per item (a standup note). Each item has one ID and lives in one place.

- **`INBOX.md`** fits on one screen (about 40 lines) and holds only what GitHub cannot: links to where status lives (issues, pull requests, the `needs-you` search), the local worktree and machine table, and parked or private notes. It never copies issue or PR status, because a hand-kept copy goes stale (standard: single source of truth, status kept in the tracker; checked 2026-10-30). Sections, in order: **Where to look** (links), **Worktrees and machines** (chat, folder, branch, machine), **Parked** (private or process tickets, one line each), then a link to `DONE.md`.
- **Tickets** (`tickets/<ID>.md`): `T<n>` for a task, `D<n>` for a decision for the user; numbers are never reused. A ticket starts with title, status, owner, model tag, files it touches and acceptance check. A decision ticket adds the five fields from the working rules (what, why you, action, time, if you do nothing) and a recommended default. A dated **Log** section at the bottom records what happened, newest last. Longer results go in a handoff report that the ticket links to.
- **`DONE.md`**: one line per finished item, newest first, with the commit or PR and how to undo it. A "decide, then tell" choice gets a line here with its reason.
- When a ticket closes: set its status `done`, add its line to `DONE.md`, and take it off the Parked list. When a decision is answered, record the answer in the ticket's log the same way. Then check the working rules' "Context" section before taking the next ticket (a closed ticket is a task boundary).
- Edit only your own tickets and worktree rows. Exception: the lead edits anything needed to keep the page correct.
- Message the user only when the task in hand is blocked; other decision items wait in the inbox (working rules, "Push only what blocks"). The one exception is the daily digest below.

### Keeping the user's queue short

A pull-only inbox with no limit piles up unseen. These practices keep it readable (standard: DORA "Streamlining change approval" and Kanban WIP limits, checked 2026-10-29). **The numbers are defaults under test, not standards**: no source gives the right limit, so a project measures its own queue (does it stay within the limit, how long do items wait) and changes them in its `RULES.md` with the user's yes.

- **Limit:** "Needs you" holds at most **3** items (default). When full, no chat adds a user item or starts work that will end in one; it finishes or unblocks existing items, or parks the new one as "Not blocking".
- **Batch:** each PR waiting for the user's merge carries the `needs-you` label and a review request; no batch row is needed.
- **Age:** each "Needs you" row shows the date added; an item older than **2 days** (default) moves to the top.
- **Daily digest** (default on): the first reply a chat gives the user each day starts with one line, "N items wait for you on GitHub (label needs-you), oldest since <date>", and says nothing when the queue is empty.
- **Gate less, check more:** before adding an item for the user, check whether an automated check (CI, a hook, a required status) could replace the approval.
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
