# Auto-merge on a repository without branch protection

- **Question:** Does `gh pr merge --auto` wait for CI on a private repository under GitHub Free, and what replaces it where it cannot?
- **Checked:** 2026-11-05

## Finding

- **Auto-merge waits only for required checks.** It "merges a pull request automatically after all required reviews and status checks pass", and the repository must have it enabled first (GitHub docs). A check that is not required does not hold it back.
- **The option needs a pending requirement.** GitHub offers it only on pull requests that cannot merge immediately, for example when branch protection requires reviews or checks. The peter-evans action lists the same conditions: "Allow auto-merge" on, a branch protection rule with at least one requirement, and requirements not yet satisfied. If the pull request can already be merged, that action merges at once.
- **Protected branches, code owners and required reviewers in private repositories are listed as paid-plan tools** (GitHub Pro and above); Free's private repositories have "a limited feature set". GitHub's API answers a rulesets call on a Free private repository with 403, "Upgrade to GitHub Pro or make this repository public".
- **The workaround seen in practice** (community examples): check the status yourself, then merge plainly, with `gh pr checks <n> --watch` followed by `gh pr merge <n> --squash --delete-branch`. `--delete-branch` deletes the local and remote branch after the merge (gh manual).

Not from a source (the checker's inference): with no required checks, `--auto` cannot be a CI gate, because either the option is refused or nothing makes it wait. On such a repository the gate must be an explicit check before the merge, and it is enforced by the agent's rule or a hook, not by GitHub.

## Sources

- [Automatically merging a pull request](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/incorporating-changes-from-a-pull-request/automatically-merging-a-pull-request) (official docs).
- [Managing auto-merge in a repository](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-auto-merge-for-pull-requests-in-your-repository) (official docs).
- [GitHub's plans](https://docs.github.com/en/get-started/learning-about-github/githubs-plans) (official docs).
- [gh pr merge manual](https://cli.github.com/manual/gh_pr_merge) (official docs).
- [enable-pull-request-automerge](https://github.com/peter-evans/enable-pull-request-automerge) (community action, widely used).
- [Auto-merge after GitHub Actions pass](https://www.zonca.dev/posts/2025-10-20-github-actions-auto-merge), [Set up auto-merge in GitHub Actions](https://oneuptime.com/blog/post/2025-12-20-github-actions-auto-merge/markdown) (community posts, found by search; read only through search summaries).

## Limits

No official page reached says which plans include auto-merge itself, so its availability on Free private repositories is unconfirmed, as is whether Pro alone enables it. The claim that `--auto` merges at once with no requirements comes from community sources and a third-party action, and was not tested. The 403 text was observed directly on one repository.
