---
name: multi-chat
description: ALWAYS load this first, before any other work, when the repository has a handoff folder (.handoff/) or an INBOX.md, or when the project's CLAUDE.md names one. Coordination protocol for several Claude chats on one repository: chat table and claims, one worktree and branch per chat, the INBOX.md links page, tickets, DONE.md and handoff reports, messaging other chats with ListAgents/SendMessage, merging. Also use when the user names your chat (for example "you are thesis-a2"), when another session messages you, or when setting up multi-chat work in a new project.
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
2. Run `ListAgents` to find the other chats. A chat's `ListAgents` name and ID stay the same after `/clear` (tested 2026-10-31: ID and "started" time unchanged; the scratchpad folder and transcript file do change); a new window gives a new one. Never reuse an address from an earlier window. Your chat name is your own `ListAgents` ID (see "Chat names").
3. Write your table row ("Chat names" below). Then check who is working where: `gh issue list --label claimed`, `gh pr list --state open` and `git worktree list`. If another chat already uses your folder, make your own worktree (below) before editing anything. Then claim your issue (see "Claim rule") and re-read it (claim, then verify): if another chat's claim comment is also there, the one posted later backs off. Fill in your row's folder and branch.
4. Say in one line which model and effort the task needs (see the working rules).

## Chat names: the session ID (user's decision, 2026-10-31; replaces the `agent-N` registry names of 2026-10-30)

A chat's name is its `ListAgents` ID, the six characters in brackets (for example `f8ab79`). It survives `/clear`; a new window gives a new one. Use it in claims, signatures and your table row. There is no numbering, so there is no name to take or verify: `ListAgents` resolves an ID to the name to message and says whether it is alive (one source of truth).

The "Worktrees and machines" table in `INBOX.md` holds one row per active chat with **Session** (your ID), **Role** (`worker` or `talk`), **Folder**, **Branch**, **Machine** and **Last seen** (date and time) (standard: worker leases with heartbeats, as Kubernetes `Lease` objects; checked 2026-10-30). Write your row at the start of a chat and in a new window; `/clear` keeps your ID, so keep your row.

- **Heartbeat:** update your Last seen each time you run the "check before each task" step. No timer. It matters only to peers on another machine (see Liveness).
- **Liveness** (user's decision, 2026-10-31): `ListAgents` is the source of truth for whether a chat on this machine is alive. A row on this machine whose Session `ListAgents` does not list is dead, whatever its Last seen says: do not message it, do not count it as a reviewer, and delete it the next time you write the table. `ListAgents` sees only this machine's sessions (plus cloud and Remote Control ones), so a row on another machine is alive while its Last seen is under 2 hours old. `idle` in `ListAgents` means only that the session is between prompts; work goes out through claims (see "Claim rule"), not to whoever looks idle.
- **Sign** every PR comment, review verdict, handoff line and message with your session ID, so author and reviewer are visible in the record. A review signed with the author's ID counts as no review.
- Remove your row when you end the chat for good; if you cannot (window closed), any chat deletes it once dead.

## Working rules

- **One worktree and branch per chat:** `git worktree add ../<project>-<task> -b <branch>`. Edits and commits never mix. If you started in a shared folder and have uncommitted work, create the worktree from `HEAD`, copy only your own files across (overwrite explicitly, for example `cp -f`, and check the result with `git diff --stat`), then remove them from the shared folder. Never touch files you did not create.
- **Test your own worktree's code.** An editable install (`pip install -e`) points at the main checkout, so tests in a worktree silently run the main checkout's code. Put the worktree's source first on the path (for example `PYTHONPATH=<worktree>/src`), check with `python -c "import <pkg>; print(<pkg>.__file__)"`, and do not reinstall the package, which would switch it under the other chats.
- **Git-ignored data is not in a worktree.** Read and write shared data under the main checkout with absolute paths.
- **At most one chat per reserved resource** (a cloud kernel, a GPU, a deployment slot). Claim it in your table row before using it; release it when done.
- **Merging:** never merge locally. Each task lands on the default branch by pull request, reviewed as the `workflow:pr-review` skill says.

## Orchestration: chats and claims (default; no lead, user's decision, 2026-10-31)

Chats are not tied to folders. Any chat may edit any file; conflicts are prevented per **task**.

- **Chats**: any chat turns the user's requests into GitHub issues (with a priority label, below). A chat claims an issue (see "Claim rule"), works on a branch named as the project's `CLAUDE.md` says (default `task/<ID>-<slug>`) in their own worktree, open the PR (its state is the status) and assign its reviewer (see Review queue).
- **Review queue (named reviewer, idle first; user's decision, 2026-10-31):** each PR gets one named reviewer, chosen by its author (standard: GitHub team review auto-assignment names one member instead of notifying the whole team; Google eng-practices make one business day the maximum for a first response and say to review at a break in focused work; checked 2026-10-31). Chats act only when prompted, so the author's message is what starts a review. When the PR opens, the author runs `ListAgents` and messages one non-author peer: an `idle` one first (if several, the one whose last review line in `DONE.md` is oldest), otherwise a busy one. If no peer is listed, the PR waits: the next chat that starts takes it under the backstop below, and if it is still unreviewed after one business day, the first chat that sees it adds the `needs-you` label with the user as reviewer. A reviewer takes the PR at its next task boundary (after its current commit, never in the middle of debugging) and before starting new work. It reviews (`/code-review`; risky paths also get `/security-review`), posts the result as a signed PR comment (the comment is the claim and the record; there is no queue table), files an issue for every finding not fixed in the PR and links it from the comment. When there is no blocking issue, the project's rules let agents merge and the PR is not a user-merge item, it enables auto-merge (`gh pr merge <n> --auto --squash`), so CI stays the final gate. An author never reviews its own work. Backstop: at each task boundary every chat also takes the oldest open PR with no review comment from a non-author chat, and an author whose PR is still unreviewed at its own next task boundary assigns it to another peer. The full pattern and its sources are in the `workflow:pr-review` skill.
- **Trunk-based:** the default branch is the integration branch; there is no `dev`. Branches live hours to a few days and land by pull request (standard: DORA trunk-based development, checked 2026-10-29). A project that supports several released versions may keep release branches; its `RULES.md` says so.
- **Claim rule** (user's decision, 2026-10-31): a task is a GitHub issue claimed with the one label `claimed` plus a comment `claimed by <session ID>` listing the files it touches. One shared label, because a per-chat label would leave a new label behind for every window. The latest claim comment names the owner. Do not start an issue whose files overlap another claimed issue; message its owner. If you need more files, comment them on the issue first. Remove the label when the PR opens.
- **Priority label** (user's decision, 2026-10-31; standard: Kubernetes issue triage guidelines, where a missing priority label means "not yet reviewed", and Cloudflare workers-sdk triage, where anyone triages against written criteria; checked 2026-10-31; departs from the Kanban practice that only an owner sets priority, because an owner gate delays chats that act only when prompted; the three level names are a default under test): each open issue carries exactly one of `priority:now` (unblocks other work, checks real behaviour, or is a security problem or a regression on the default branch), `priority:next` (do alongside features) or `priority:later` (wait until a feature needs it). The chat that files an issue sets the label and writes one line in the body saying why, plus what it blocks (`Blocked by #n`, or what it unblocks). Any chat may change a label it disagrees with, giving its reason in a comment. Before starting a `priority:now` issue it did not file, a chat checks the reason still holds. A chat picking work takes `priority:now` first, then the oldest unblocked `priority:next`. The chat that merges a milestone's last PR re-checks the labels of the next milestone. Order within a milestone only; milestones and `Blocked by` lines stay as they are.
- **Lifecycle** is GitHub's own state, never copied into handoff files: open issue → `claimed` label and claim comment → open PR (`Closes #n`) → merged, which closes the issue. Chats start every new task from the latest default branch.
- **Scaling:** about four chats; past that, split the work by milestone. New chat = one new worktree plus one worktree-table row.
- **Skip orchestration** (one chat, or two chats on clearly unrelated work) only when the user says so.

## The inbox and tickets

The split follows common practice: a tracker holds the details (one issue per item), and a status page gives one line per item (a standup note). Each item has one ID and lives in one place.

- **`INBOX.md`** fits on one screen (about 40 lines) and holds only what GitHub cannot: links to where status lives (issues, pull requests, the `needs-you` search), and the local worktree and machine table. It never copies issue or PR status, because a hand-kept copy goes stale (standard: single source of truth, status kept in the tracker; checked 2026-10-30). Sections, in order: **Where to look** (links), **Worktrees and machines** (session, folder, branch, machine), then a link to `DONE.md`. There is no Parked list (user's decision, 2026-10-31: unused; add one back if a real need appears).
- **Tickets** (`tickets/<ID>.md`): `T<n>` for a task, `D<n>` for a decision for the user; numbers are never reused. A ticket starts with title, status, owner, model tag, files it touches and acceptance check. A decision ticket adds the five fields from the working rules (what, why you, action, time, if you do nothing) and a recommended default. A dated **Log** section at the bottom records what happened, newest last. Longer results go in a handoff report that the ticket links to.
- **`DONE.md`**: one line per finished item, newest first, with the commit or PR and how to undo it. A "decide, then tell" choice gets a line here with its reason.
- When a ticket closes: set its status `done` and add its line to `DONE.md`. When a decision is answered, record the answer in the ticket's log the same way. Then check the working rules' "Context" section before taking the next ticket (a closed ticket is a task boundary).
- Edit only your own tickets and worktree rows. Exception: any chat deletes a dead row (see Liveness) and fixes a stale fact.
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
5. `ListAgents`, then `SendMessage` each peer the handoff path and its first task.
