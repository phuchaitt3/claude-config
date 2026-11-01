# GitHub code owners and required review

- **Question:** How does GitHub enforce a list of paths that only the owner may merge?
- **Checked:** 2026-11-01

## Finding

- A `CODEOWNERS` file only assigns owners. Enforcement is a separate setting: "Require review from Code Owners" in a branch protection rule or a ruleset.
- A pull request uses the `CODEOWNERS` file from its base branch, so a PR cannot change its own approval rules.
- The last matching pattern wins. An approval from any one listed owner meets the requirement.
- To protect fully, also make an owner for the `CODEOWNERS` file itself (GitHub suggests `.github/CODEOWNERS`).
- Paths are case sensitive. A file over 3 MB is not loaded, so owner checks silently stop.
- Rulesets are an alternative to branch protection rules.

Not from a source (the checker's own reasoning, not verified): with no bypass actors in the ruleset, an author cannot approve their own PR, so a solo owner who writes a PR touching an owned path needs "Repository admin" as a bypass actor.

## Sources

- [About code owners](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners) (official docs; several results were for older Enterprise Server versions, so UI labels may differ).
- [Kertos guide](https://docs.kertos.io/en/article/ensure-code-owner-approval-is-required-for-owned-code-changes) (third party): says admins can bypass unless "Include administrators" is on. Not checked against current GitHub docs.

## Limits

No source covered a solo-owner repository with a bot author, or how this interacts with auto-merge.
