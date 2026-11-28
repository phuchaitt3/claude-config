---
name: dvc
description: Load before running or changing anything that touches DVC-tracked data (dvc add/commit/push/pull, a data/ folder with .dvc pointers), before removing a git worktree that may hold run outputs, or when setting up data versioning in a project. When to version, where run outputs are written, how pointers are committed, and what never goes in git.
---

# DVC data management (all repositories)

A project's `CLAUDE.md` names its tracked folders and remote; this skill holds the rules that are the same everywhere.

- **Versioning cadence:** run `dvc commit -f && dvc push`, then commit the `.dvc` pointers, once per milestone, not after every edit: a finished run's output, a data file a commit or doc depends on, and before switching machines (standard: findings/data-versioning-cadence, checked 2026-11-08). Small text that changes often (notes, coordination files) belongs in git, not DVC.
- **More than one machine** (user's decision, 2026-11-27): a project whose tracked data is used on more than one machine has a remote each of them can reach; a folder on one machine's disk does not count. An input that cannot be downloaded again byte for byte (a generated export, a hand-made file) is DVC-tracked, not left to a fetch script. Models and container images are not shared: each machine downloads them from a pinned source (revision hash, image digest) (standard: findings/dvc-remote-choice, checked 2026-11-27, for the remote; the rest: inference, findings/multi-device-agent-orchestration).
- **Keep rebuildable files out** (user's decision, 2026-11-28): before a folder is first tracked, the project's root `.dvcignore` lists caches (`__pycache__/`, `*.pyc`, library compile caches) and resume-only training checkpoints when the final model is saved elsewhere. Source copies saved with a run stay, as they may be the only record of uncommitted code (inference: findings/dvc-what-to-track).
- **Run outputs go to one shared place, never a worktree's own `data/`:** `data/` is git-ignored, so a worktree's copy is lost when the worktree is removed. Point the run tool's output path at the main checkout (absolute path or an environment variable); do not copy outputs back afterwards (standard: findings/run-outputs-with-worktrees, checked 2026-11-14).
- **Before removing a worktree,** list its ignored files (`git status --porcelain --ignored`); anything beyond caches and build files must already exist in the main checkout or be rescued first (copy to a named folder under the main `data/`, `dvc commit`, `dvc push`).
- **Pointers land by pull request** from a task worktree: the main checkout stays clean, so run `dvc commit` there, copy the changed `.dvc` files into the worktree (`cp -f`), `git restore` them in main, and commit in the worktree.
- **Never `dvc add` inside a tracked folder** (it writes a pointer DVC cannot find); `dvc commit` updates the existing ones.
- **Never commit** run outputs, `data/`, or storage ids and credentials; never read or write credential files. Pushing to the user's own remote needs no asking; a remote in a third-party service does.
