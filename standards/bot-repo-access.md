# Giving a bot account access to many repositories

- **Question:** Must a bot (machine user) be added as a collaborator on every repository one by one? What do teams do instead?

- **Finding:**
  - **Personal accounts:** a repository owned by a personal account has only two roles, owner and collaborator. Access is granted per repository, by invitation, and GitHub suggests moving to an organization for finer control. On a personal account there is no setting that gives one user access to all repositories, so per-repository invites are how GitHub works there rather than a chosen practice.
  - **Organizations:** base permissions give every member a default role "across the organization's repositories". So a bot that is an org member with base permission Write reaches each new repository with no extra step. A higher role set on one repository overrides the base. Outside collaborators are not covered.
  - **GitHub Apps:** GitHub recommends a GitHub App over a user account or personal token for long-lived automation:
    - an app has its own identity and uses no seat;
    - it stays installed when the person who installed it leaves;
    - the installer picks "All repositories" or "Only select repositories".

    The install page does not say whether "All repositories" includes repositories created later; it says only that repositories the app itself creates are added.
  - **Checker's inference:**
    - At a few repositories, per-repository invites are normal and cheap.
    - Past that, the usual moves are an organization with base permissions, or a GitHub App.
    - An app's short-lived installation tokens take more setup for command-line agents than a machine user does.

- **Sources:**
  - GitHub Docs, permission levels for a personal account repository (official): https://docs.github.com/en/account-and-profile/reference/permission-levels-for-a-personal-account-repository
  - GitHub Docs, setting base permissions for an organization (official): https://docs.github.com/en/organizations/managing-user-access-to-your-organizations-repositories/managing-repository-roles/setting-base-permissions-for-an-organization
  - GitHub Docs, deciding when to build a GitHub App (official): https://docs.github.com/en/apps/creating-github-apps/about-creating-github-apps/deciding-when-to-build-a-github-app
  - GitHub Docs, installing your own GitHub App (official): https://docs.github.com/en/apps/using-github-apps/installing-your-own-github-app

- **Limits:**
  - The pages fetched do not cover organization pricing, or whether rulesets on private repositories need a paid plan in an organization as they do on a personal account.
  - Whether a GitHub App's "All repositories" covers repositories created later is not stated on the pages fetched.

- **Checked:** 2026-11-08
