---
name: dvc
description: Load before running or changing anything that touches DVC-tracked data (dvc add/commit/push/pull, a data/ folder with .dvc pointers), before removing a git worktree that may hold run outputs, or when setting up data versioning in a project. When to version, where run outputs are written, how pointers are committed, and what never goes in git.
---

# DVC data management (all repositories)

A project's `CLAUDE.md` names its tracked folders and remote; this skill holds the rules that are the same everywhere.

- **Versioning cadence:** run `dvc commit -f && dvc push`, then commit the `.dvc` pointers, once per milestone, not after every edit: a finished run's output, a data file a commit or doc depends on, and before switching machines (standard: findings/data-versioning-cadence, checked 2026-11-08). Small text that changes often (notes, coordination files) belongs in git, not DVC.
- **Run outputs go to one shared place, never a worktree's own `data/`:** `data/` is git-ignored, so a worktree's copy is lost when the worktree is removed. Point the run tool's output path at the main checkout (absolute path or an environment variable); do not copy outputs back afterwards (standard: findings/run-outputs-with-worktrees, checked 2026-11-14).
- **Before removing a worktree,** list its ignored files (`git status --porcelain --ignored`); anything beyond caches and build files must already exist in the main checkout or be rescued first (copy to a named folder under the main `data/`, `dvc commit`, `dvc push`).
- **Pointers land by pull request** from a task worktree: the main checkout stays clean, so run `dvc commit` there, copy the changed `.dvc` files into the worktree (`cp -f`), `git restore` them in main, and commit in the worktree.
- **Never `dvc add` inside a tracked folder** (it writes a pointer DVC cannot find); `dvc commit` updates the existing ones.
- **Never commit** run outputs, `data/`, or storage ids and credentials; never read or write credential files. Pushing to the user's own remote needs no asking; a remote in a third-party service does.
