# Project path portability

**Question:** What should depend on a project's absolute path on disk, so that moving or renaming its folder stays cheap?

**Finding:**

- Python: a virtual environment is "not considered as movable or copyable"; it is "disposable", and if a parent directory moves "you should recreate the environment in its new location". Scripts in it hold absolute interpreter paths. The official answer to a move is a rebuild from a requirements or lock file, not a path fix-up. The same goes for an editable install, which lives inside the environment.
- Git: `git worktree move` cannot move the main worktree. After moving it by hand, `git worktree repair` run in the main worktree reconnects the linked worktrees; if the linked worktrees moved too, pass their new paths to `repair`. `worktree.useRelativePaths` stores relative links for setups that move, but it is off by default and turns on `extensions.relativeWorktrees`, which older git versions cannot read.
- Tracked content: the twelve-factor app separates config, meaning whatever varies between deploys, strictly from code, and keeps it in the environment. Reproducible-research guidance says the same at small scale: no absolute paths in a project; where one cannot be avoided, define it once at the top rather than scattering it. Paths resolve from the script or the project root.
- DVC: `.dvc/config.local` is a git-ignored file with the highest priority, the place for machine-specific settings. A path setting such as `cache.dir` may be absolute or relative to the config file.
- Claude Code: auto memory sits at `~/.claude/projects/<project>/memory/`, with `<project>` derived from the git repository, so worktrees share it. It is machine-local. `autoMemoryDirectory`, read from any settings scope, stores it elsewhere. Issue reports say sessions are keyed by the absolute path too, so after a move the old data stays on disk in the old folder and a new empty one is used. Requests for a stable project ID and a migrate command are open as far as checked; community tools (`claude-mv`, `claude-repath`) rewrite the state.
- Layout: no source says a container folder per repository (`<repo>/main` plus `<repo>/<task>`) is cheaper to move than a checkout beside a `<repo>.worktrees` folder. Guides on the bare-repository variant report that some tools expect a normal clone as the project root; a normal clone in `main/` avoids that (see [worktree-hygiene](worktree-hygiene.md) for the layouts).
- Checker's inference (not stated by the sources): sort everything that holds a path into three groups. Rebuildable (environments, editable installs, build caches): recreate, never patch. Tracked (code, docs, agent instructions): keep relative, so a move changes nothing. Machine-local (a data root, a remote, per-machine settings): one git-ignored place per machine. Moving a project then costs one rebuild and one local edit, whatever the layout.

**Observed locally (2026-11-05):** renaming a parent folder left a Python environment's editable install and `activate` script on the old path, so the import failed until a rebuild, and nothing reported it. It also left two Claude Code project folders for one repository. Across five repositories, absolute paths in tracked files were rare: three files in one repository, one of them a remote outside the repository that a move does not affect. Handoff notes held more.

**Sources:**

- Python, [venv documentation](https://docs.python.org/3/library/venv.html) (official docs).
- Git, [git-worktree documentation](https://git-scm.com/docs/git-worktree) (official docs).
- [The Twelve-Factor App: Config](https://12factor.net/config) (widely cited methodology, written for deployed services).
- Karl Broman, [Knitr with R: reproducibility](https://kbroman.org/knitr_knutshell/pages/reproducible.html) (academic guide); [scriptloc vignette](https://erised.las.iastate.edu/CRAN/web/packages/scriptloc/vignettes/scriptloc.html) (package docs, CRAN mirror: paths from the script's location).
- DVC, [Configuration](https://doc.dvc.org/user-guide/project-structure/configuration) (official docs).
- Claude Code docs, [How Claude remembers your project](https://code.claude.com/docs/en/memory) (official docs).
- Claude Code issues [54791](https://github.com/anthropics/claude-code/issues/54791) and [33636](https://github.com/anthropics/claude-code/issues/33636) (user reports and feature requests); [claude-mv](https://awesome.ecosyste.ms/projects/github.com%2Fjustinstimatze%2Fclaude-mv), [claude-repath](https://pypi.org/project/claude-repath/) (community tools, not tested here).
- [GitWorktree.org: bare repository guide](https://gitworktree-org.pages.dev/guides/bare-repo), [bare-repository worktree workflow](https://xoofee.github.io/posts/2026/04/git_worktree_bare_repo_workflow/) (community guides).

**Limits:** no source covers a developer's folder layout as a whole; the three groups are an inference from per-tool documentation. Twelve-factor is about deployed services, applied here by analogy. The Claude Code session behaviour comes from issue reports, not from documentation, and may change between versions. `autoMemoryDirectory` moves memory only, not session transcripts, and was not tested here. `worktree.useRelativePaths` was not tested: git 2.42 on the test machine does not offer it, and the page gives no version.

**Checked:** 2026-11-05
