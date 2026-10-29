# RULES: orchestration for <project>

The general protocol is the `workflow:multi-chat` skill and the user-level working rules; hard limits are in the repo's `CLAUDE.md`. This file adds only what is specific to this project. It is not in git, so an edit reaches every chat at once. After changing it, message the running chats and add one line to `DONE.md`.

## Roles

Lead: `<chat-name>`. Workers: see the "Where each chat works" table in `INBOX.md`. Task lifecycle, claim rule and merge flow: see the skill.

## Shared paths

- Main checkout: `<path>` (stays on the default branch, nobody commits here; holds git-ignored data and secrets; other worktrees reach them by absolute path, read-only)
- Task worktrees: `<path>-<name>`, branched from the default branch
- Handoff folder: `<path>/.handoff/`
- Testing a worktree's code: `PYTHONPATH=<worktree>/<src path>`; never `pip install -e` into a shared environment.

## Reserved resources

| Slot | What it is | Rule |
|---|---|---|
| `<name>` | for example a cloud kernel, GPU, shared venv, paid API | one chat at a time; claim it in the inbox table |

## Extra rules for this project

- (anything that holds only here: run-time thresholds, data that must never leave the machine, per-run caveats)
