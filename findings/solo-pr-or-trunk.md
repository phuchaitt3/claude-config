# Pull requests or direct commits for a solo developer with agents

- **Question:** Should a solo developer running AI agents use pull requests or commit straight to the main branch?
- **Checked:** 2026-11-05

## Finding

- **Trunk-based development allows both.** Some teams commit directly to the main branch, others use short-lived branches merged through lightweight pull requests (vendor guide).
- **Branches should be short-lived:** hours to two days at most, and never long enough to diverge meaningfully from the trunk (practitioner posts).
- **CI is the gate, and it has to be fast.** A slow gate pushes people back to batching work into large, risky changes (practitioner posts).
- **Long branches hurt agents most**, because an agent writes against a branch state that main has since left. One project gives each agent its own worktree and draft pull request, so agents run in parallel and merge independently (practitioner posts).

Not from a source (the checker's inference): with one agent at a time, direct commits lose little. With several in parallel, per-task branches avoid collisions on one branch, and a pull request is the only place CI runs before the code lands. The value of that checkpoint depends on what CI covers.

## Sources

- [What is trunk-based development (Flagsmith)](https://flagsmith.com/blog/trunk-based-development) (vendor guide).
- [Trunk-based development with short-lived branches](https://dev.to/tacoda/trunk-based-development-with-short-lived-branches-5f74), [Trunk-based development: from chaos to flow](https://dev.to/codecraft_diary_3d13677fb/trunk-based-development-from-chaos-to-flow-4mkg), [Agentic git workflow](https://dev.to/igor_grieder/agentic-git-workflow-hig) (community posts).
- [What is trunk-based development (Hyrax)](https://hyrax.dev/learn/what-is-trunk-based-development), [AutoGit development philosophy](https://autogit-docs.pages.dev/guides/philosophy) (vendor docs).

## Limits

No source addresses solo developers directly, and none measures outcomes for agents. Everything here is practitioner opinion read through search summaries, weaker than the DORA research behind trunk-based development in general. It does not settle the choice.
