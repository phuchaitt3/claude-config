# Run outputs and git worktrees

- **Question:** When ML run outputs (logs, per-sample results, large files) are git-ignored and versioned with DVC, and runs happen in several git worktrees, is it normal to copy each worktree's output back to one place and `dvc push`? Is there a better way?

- **Finding:**
  - **Git ignores are per worktree.** Worktrees share the object database but not the working directory; ignored files (data, build output, environments) are not carried into a new worktree and are lost when it is removed. Git refuses `git worktree remove` on a worktree with untracked files but not on one holding only ignored files, so ignored outputs vanish silently.
  - **Common remedy: keep large ignored data in one place and link it in**, not copy it out later. Community tools do this with symlinks (`git worksync`, a `.worktreeinclude` file with a `@symlink` entry for large read-mostly assets). Known gotchas: a directory symlink is not matched by a trailing-slash ignore rule and shows in `git status`; a change in one worktree changes all; symlinked directories have broken automatic worktree cleanup in at least one reported case.
  - **DVC side:** the DVC cache can be shared on a shared machine (`dvc cache dir`, `cache.type symlink`), and `dvc exp run --temp` runs an experiment outside the workspace. A third-party guide advises pruning old experiments (`dvc exp gc`). No source describes worktree handling of large outputs, and DVC's own advice on organising many experiments is described as still evolving.
  - **Checker's inference** (no source states it as a rule): the copy-and-push step is the symptom of outputs having been written inside a throwaway worktree. Cheaper than rescuing outputs afterwards is to point the run tool's output path at the shared main checkout's data folder (an absolute path or environment variable), so a worktree never holds run data and removing it loses nothing. Rescue-copy is a one-off for outputs already stranded.

- **Evidence strength:** common practice for the symlink pattern (several community tools and guides agree); anecdotal for the cleanup gotcha (one issue report); no data found for DVC with worktrees.

- **Sources:**
  - workmux, Git worktree caveats (community guide): https://workmux.raine.dev/guide/git-worktree-caveats/
  - git-worksync (community tool): https://awesome.ecosyste.ms/projects/github.com%2Fatusy%2Fgit-worksync
  - `.worktreeinclude` convention (community tool): https://awesome.ecosyste.ms/projects/github.com%2Fbastos%2Fdot-worktreeinclude
  - GitWorktree.org, gitignore guide (community guide): https://gitworktree-org.pages.dev/guides/gitignore
  - Issue report, `symlinkDirectories` breaking worktree cleanup (issue tracker): https://claudeissues.com/issue/40259-symlinkdirectories-causes-silent-worktree-cleanup-failure
  - DVC experiments guide, `--temp`, queue, shared cache (third-party tutorial, mirrors DVC docs): https://www.mintlify.com/treeverse/dvc/guide/running-experiments
  - DVC data versioning how-to, `dvc cache dir`, `exp gc` (third-party tutorial): https://oneuptime.com/blog/post/2026-01-25-dvc-data-versioning/view

- **Limits:** two standard searches; most hits are community posts or tutorial mirrors, not DVC's own docs, which were not read directly. Nothing found on keeping run outputs of several worktrees in one DVC-tracked folder. See also [data-versioning-cadence](data-versioning-cadence.md) and [worktree-hygiene](worktree-hygiene.md).

- **Checked:** 2026-11-14
