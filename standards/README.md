# Industry-standard register

What agents checked against industry practice, kept so the next chat answers from it instead of searching the web again. Rule: `rules/working-rules.md`, "Industry practice".

The repository is public: an entry names no project and holds no private detail.

## How to use it

- Before a web search about an industry practice, look for the topic below. If an entry covers the question and is under 12 months old, answer from it and cite it as `standards/<topic>`.
- After a search that checks a practice, add or update the entry in the same turn, and tag the point where it is written: `(standard: standards/<topic>, checked YYYY-MM-DD)`, or `(departs from standard: <reason>)`.
- A hook (`tag_check.py` in the workflow plugin) refuses a commit in this repo that cites `standards/<topic>` with no `standards/<topic>.md`. It checks that the entry exists, not that it supports the claim.
- An entry older than 12 months, a source that has changed, or a new fact that contradicts it means check again and update the entry.

## Entry format

One file per topic, `standards/<topic>.md`:

- **Question:** what was asked, in one line.
- **Finding:** the answer in a few lines, as the sources say it. Mark what is the checker's own inference.
- **Sources:** links, each with its kind (official docs, standard body, vendor blog, community post).
- **Limits:** what the sources do not cover, and any source that is secondary or low quality.
- **Checked:** date.

## Index

| Topic | Question |
|---|---|
| [code-owners-required-review](code-owners-required-review.md) | How does GitHub enforce a list of paths that only the owner may merge? |
| [policy-single-source](policy-single-source.md) | How do rules in prose and in enforcement code stay in step? |
| [agent-config-protection](agent-config-protection.md) | How are an AI agent's own config files (instructions, settings, hooks) protected from automated changes? |
| [secret-leak-prevention](secret-leak-prevention.md) | How is a secret kept out of a public repository, and how common are leaks? |
| [private-repo-commit-checks](private-repo-commit-checks.md) | Can the secret and output checks before a commit be skipped in a private repository? |
| [leaked-secret-response](leaked-secret-response.md) | What to do first when a secret has been pushed. |
| [heavy-job-scheduling](heavy-job-scheduling.md) | How do teams run heavy tests and benchmarks without slowing people, and what scheduling tools exist for an agent on a laptop? |
| [scaling-tests-on-a-budget](scaling-tests-on-a-budget.md) | How do teams learn how a system behaves at a much larger size or load without a production-size environment? |
| [lockfile-review](lockfile-review.md) | How is a dependency lockfile change reviewed, and must the owner do it? |
| [adr-length-and-scope](adr-length-and-scope.md) | How long should an ADR be, and what stays out of it? |
| [adr-lifecycle](adr-lifecycle.md) | What statuses does an ADR have, and does a review block work? |
| [bottleneck-tasks](bottleneck-tasks.md) | Do teams automatically find the tasks blocking other work and put them first? |
| [worktree-hygiene](worktree-hygiene.md) | How do parallel agents keep a shared checkout current and clean, clean up worktrees, and where do worktrees live on disk? |
| [project-path-portability](project-path-portability.md) | What should depend on a project's absolute path on disk, so that moving or renaming its folder stays cheap? |
| [docker-disk](docker-disk.md) | How do teams keep Docker Desktop's disk use under control on Windows (WSL 2), and how is the space given back? |
| [multi-repo-agent-review](multi-repo-agent-review.md) | How are review requests routed when agents work across several repositories? |
| [agent-review-cost](agent-review-cost.md) | What does an AI code review of one PR cost, and is a second-agent review worth it on a small quota? |
| [auto-merge-without-protection](auto-merge-without-protection.md) | Does `gh pr merge --auto` wait for CI on a private GitHub Free repository, and what replaces it? |
| [ml-ci-test-tiers](ml-ci-test-tiers.md) | How do machine-learning projects split tests between pull-request CI and heavier runs? |
| [solo-pr-or-trunk](solo-pr-or-trunk.md) | Should a solo developer running AI agents use pull requests or commit straight to main? |
| [agent-permission-enforcement](agent-permission-enforcement.md) | Which Claude Code mechanisms enforce a rule instead of asking the model to follow it? |
