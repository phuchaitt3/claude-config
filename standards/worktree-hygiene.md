# Worktree hygiene for parallel agents

**Question:** When several agents work in git worktrees of one repository, how do teams keep the shared checkout from going stale or being dirtied, and how are worktrees cleaned up?

**Finding:**

- Claude Code's built-in worktrees (`claude --worktree`, the `EnterWorktree` tool, subagent `isolation: worktree`) handle three of these by default. New worktrees branch from the remote default branch (`worktree.baseRef: "fresh"`), fetching it first when the repository has not been fetched in 24 hours. While a session is in a worktree, Claude Code blocks edits, commands and git redirects that target the main checkout. A periodic sweep removes worktrees Claude created for subagents and background sessions once they hold no work; a reopened clean worktree whose PR merged resets to the default branch. Worktrees made by hand with `git worktree add` get none of this: the sweep never removes them and the isolation checks do not apply.
- Nothing updates a checkout's files automatically. `git maintenance`'s `prefetch` task fetches hourly into `refs/prefetch/`, not into remote-tracking branches, and moves no branch. Keeping a checkout current is a `git fetch` plus `git merge --ff-only` that someone runs.
- Refusing local commits on the default branch is commonly done with the pre-commit framework's `no-commit-to-branch` hook (blocks `main`/`master` by default; `--branch`, `--pattern`). It is a local guard, bypassed by `--no-verify` or uninstalling, so it is paired with server-side branch protection. A branch-name check does not catch a detached HEAD.
- Community guidance for parallel agents: one task, one branch, one worktree, one agent, each branched fresh from main; remove worktrees when done, since they pile up (removing one does not delete its branch). An alternative layout is a bare repository with every branch as a sibling worktree, so there is no privileged main checkout to dirty.
- Checker's inference (not stated by the sources): an agent that reads files from a shared checkout can answer from stale content; reading from `origin/<default>` after a fetch, or working only in fresh worktrees, avoids it.

**Sources:**

- Claude Code docs, [Run parallel sessions with worktrees](https://code.claude.com/docs/en/worktrees) (official docs): base branch, fetch, isolation checks, sweep, manual worktrees.
- Git, [git-maintenance documentation](https://github.com/git/git/blob/d166e8c1d4cb35dec960c4f69ccc23d2fedb322a/Documentation/git-maintenance.txt) (official docs): the `prefetch` task writes to `refs/prefetch/`.
- pre-commit-hooks, [README for no-commit-to-branch](https://cobalt.googlesource.com/pre-commit-hooks/+/202ec6b8f5caebaa97c5f6db0c2a7723df592ed9%5E%21/README.md) (project docs, mirror).
- alexwlchan, [A hook to stop committing to main](https://alexwlchan.net/2026/no-main-hook/) (community post).
- [Git worktrees for parallel AI coding agents](https://recca0120.github.io/en/2026/04/14/git-worktree-parallel-work/), [OpenReplay](https://blog.openreplay.com/git-worktrees-ai-agents/), [MindStudio](https://www.mindstudio.ai/blog/git-worktrees-parallel-ai-coding-agents) (community posts: one worktree per agent, cleanup, bare-repo layout).

**Limits:** no official source says how to keep a shared main checkout clean or current; that guidance is community practice. The Claude Code behaviour is version-dependent and documented for its own worktree location (`.claude/worktrees/`). No source measures how often stale reads happen.

**Checked:** 2026-11-01
