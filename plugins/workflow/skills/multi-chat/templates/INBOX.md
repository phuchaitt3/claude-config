# INBOX: read this, not the chats

Rules for agents: the `workflow:multi-chat` skill, plus `RULES.md` in this folder for this project.

User: give new work to the lead (or any chat; it lands on this board). Answer decisions by ID (for example "A1: yes, option 2"). Newest items first in each section.

---

## Review queue (any chat except the author claims the oldest open row)

| PR / branch | Author | Touches | Reviewer | Status |
|---|---|---|---|---|
| #1 title | chat-name | `path/globs` | (open) | waiting |

## Needs your decision

- **A1** [chat-name] Question in one line. *Default if no answer:* what happens. [Sonnet, medium, no plan mode: reason]

## In flight

**Where each chat works** (each chat keeps its own row current):

| Chat | Role | Folder | Branch | Reserved slot | Current task |
|---|---|---|---|---|---|
| chat-name | lead (+ worker) | `<path>` | `<branch>` | none | none |
| chat-name | worker | `<path>` | `<branch>` | none | none |
| (integration) | merges only | `<path>-integration` | `dev` | n/a | n/a |

**Task board**

| ID | Goal | Files it touches | Acceptance check | Owner | Status | Model |
|---|---|---|---|---|---|---|
| T1 | Task description | `path/globs` | how the lead verifies it | chat-name | open | [Sonnet, medium, no plan mode: reason] |

Statuses: `open` → `assigned` / `in progress` → `review` → `done`.

## Done (newest first)

- YYYY-MM-DD [chat-name] What was done (`commit`). To undo: how.
