# RULES: project-specific coordination

The general protocol is the `workflow:multi-chat` skill and the user-level working rules. This file adds only what is specific to this project. It is not in git, so an edit reaches every chat at once. After changing it, message the running chats and add one line under "Done" in `INBOX.md`.

## Shared paths

- Main checkout: `<path>`
- Shared data (git-ignored, absolute paths from worktrees): `<path>/data/`
- Testing a worktree's code: `PYTHONPATH=<worktree>/<src path>`

## Reserved resources

| Slot | What it is | Rule |
|---|---|---|
| `<name>` | for example a cloud kernel or GPU | one chat at a time; claim it in the inbox table |

## Extra rules for this project

- (anything that holds only here: run-time thresholds, data that must never leave the machine, per-run caveats)
