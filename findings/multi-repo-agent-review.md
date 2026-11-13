# Review and coordination when agents work across several repositories

**Question:** When several AI coding agents work across more than one repository, how do teams route review requests and keep each agent aware of work outside the repository it is in?

**Finding:**

- GitHub has no single review queue that spans repositories by repository. The queue is kept per **person**: `gh search prs --review-requested=@me --state=open` (no repository flag, so it searches every repository) and the web page `github.com/pulls/review-requested` list every pull request waiting on that account, wherever it is. `--review-requested` also matches team requests; the `user-review-requested:` search qualifier limits it to direct requests (only through `gh api`).
- Reviewer auto-assignment tools (GitHub Actions such as auto-assign and auto-request-review) are configured per repository. A tool that acts across repositories needs a token that can read them all, because the default `GITHUB_TOKEN` is scoped to the repository that ran it.
- Guidance for parallel agents (vendor and community, not a formal standard): one agent per branch and worktree; the reviewer is a separate session from the author; one review standard enforced at the pull request, not only in agent instruction files; cap the number of parallel agents at what the reviewer can absorb (one guide says 3 to 4, a rule of thumb); serialise git operations across worktrees.
- Claude Code's agent teams (experimental) coordinate teammates through one shared task list, but the sources describe a single codebase and do not say whether one list can span repositories.
- Checker's inference (not stated by the sources): when every agent acts as one bot account, "review requested from me" cannot tell agents apart, so the per-person queue maps to a per-owner query instead (`gh search prs --owner <owner> --state open`), with the named reviewer recorded on the pull request (a comment or label), not in the reviewer field.

**Sources:**

- GitHub CLI manual, [gh search prs](https://manpages.ubuntu.com/manpages/noble/man1/gh-search-prs.1.html) (official docs): `--review-requested`, no repository flag needed.
- [codegenes: find PRs where a user is a reviewer](https://www.codegenes.net/blog/github-find-prs-where-user-is-a-reviewer/) (community post): `github.com/pulls/review-requested`, `user-review-requested:`.
- [actions-automation/pull-request-responsibility](https://github.com/actions-automation/pull-request-responsibility) (project docs): `GITHUB_TOKEN` cannot reach other repositories.
- [kentaro-m auto-assign](https://github.com/80pctsols/auto-assign), [auto-request-review](https://github.com/witoldsleczkowski/auto-request-review) (project docs): per-repository configuration.
- [CodeRabbit: consistent review across coding agents](https://www.coderabbit.ai/guides/consistent-ai-code-review-across-coding-agents), [Augment: multi-agent coding workspace](https://www.augmentcode.com/guides/how-to-run-a-multi-agent-coding-workspace), [GitKraken: parallel AI coding across repos](https://gitkraken.com/blog/7-best-tools-for-parallel-ai-coding-across-repos-2026) (vendor blogs).
- [MindStudio: agent teams shared task list](https://mindstudio.ai/blog/claude-code-agent-teams-shared-task-list) (vendor blog; official docs not read).

**Limits:** no standard body or official guide covers several agents across several repositories; the agent guidance is vendor marketing and community practice. The agent-teams description comes from secondary sources. The single-account mapping is the checker's own inference.

**Checked:** 2026-11-01
