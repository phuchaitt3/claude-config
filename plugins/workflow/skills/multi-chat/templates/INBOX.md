# INBOX: <project>                 updated YYYY-MM-DD by <chat>

Rules: `workflow:multi-chat` skill + RULES.md. Details: tickets/. History: DONE.md.
Answer decisions by ID, for example "D1: yes".

## Needs you (most urgent first)
| ID | What | Time | If ignored |
|---|---|---|---|
| [D1](tickets/D1.md) | Decision in plain words | 5 min | the default |

## In progress
| Chat | Role | Folder | Branch | Slot | Ticket | Status |
|---|---|---|---|---|---|---|
| chat-name | lead (+ worker) | `<path>` | `<branch>` | none | — | idle |
| chat-name | worker | `<path>` | `<branch>` | none | [T1](tickets/T1.md) | in progress |
| (integration) | merges only | `<path>-integration` | `dev` | n/a | — | — |

## Review queue
| PR | Author | Reviewer | Status |
|---|---|---|---|
| #1 | chat-name | (open) | waiting |

## Up next
- [T2](tickets/T2.md) task in plain words: blocked by D1

Statuses: `open` → `assigned` / `in progress` → `review` → `done`.

Done: [DONE.md](DONE.md)
