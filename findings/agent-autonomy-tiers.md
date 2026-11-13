# Separate speed-first and oversight-first modes for agent work

- **Question:** Is it standard to have separate modes (or tiers) where some work favours speed and relaxes human-in-the-loop review, while other work keeps a human gate, and how do teams keep dependent work moving while a human-gated change waits?

- **Finding:**
  - **Yes, tiering human review by risk is common practice; one fixed level for all work is not.** No official standard exists for software-agent autonomy (one guide notes there is no SAE J3016-style standard for software engineering). Practitioner frameworks agree on the shape, though: autonomy is set per task or per action by how bad a mistake would be and how easily it is caught and undone. Examples: a ladder from "silent" through "notify after, with undo" and "confirm before" to "forbid" (LoopRails); four levels with human-in-the-loop kept for tasks that are hard to check (PostHog); "higher is not always better" (Swarmia, as cited by Tembo).
  - **The same idea predates AI agents.** Ship / Show / Ask (Rouan Wilsenach, on martinfowler.com, 2021) sorts each change into Ship (merge without review), Show (merge, then review after) or Ask (review before merging). Teams are "mostly Ship" or "mostly Ask", and the choice is made per change, not fixed per project.
  - **Review tools ship risk tiers.** Gitar rates PRs Low, Medium or High and can auto-merge only Low; CodeRabbit withholds its approval at Moderate risk or above, so humans must approve. Vercel reports that 58% of PRs in its largest monorepo merge without human review, with a classifier tuned to prefer false HIGHs over false LOWs, and HIGH-risk PRs still needing human approval (vendor posts; the Vercel post itself was not readable at check time). Common always-human classes: auth, secrets, payments, migrations, infrastructure, release automation. Sources stress that risk follows impact, not size: a 3-line change can be high risk.
  - **What the sources add to plain tiering:** measure both error directions (low-risk work that needed review, high-risk work that slipped through) and adjust the line with that evidence; make demotion to a stricter tier automatic on a risk signal rather than waiting for a human to notice; and keep a human as the owner of the policy even when an agent applies it.
  - **Dependent work while a gated PR waits: stacking.** Stacked PRs (each branch built on the one below, the bottom one targeting main) let the author, or the next agent session, keep building on unmerged work while it sits in review. GitHub has native stacked PRs (`gh stack`, public preview, 2026) and a Copilot tutorial on stacking agent work; a pattern note describes starting each agent session on the previous session's unmerged branch. Cost: when a lower PR changes in review, every branch above it must be rebased, which needs `--force-with-lease`.
  - **Checker's inference:** a project-level speed mode (merge on a light check) beside a stricter mode, with fixed always-human path lists, matches this practice. The documented refinement is to pick the tier per change by risk rather than per project, and to log the misses. For unattended runs where human-gated PRs would starve dependent tasks, the practices on offer are: auto-merge the low-risk tier, stack the dependent work on the gated branch, or both.

- **Evidence strength:** common practice (several independent practitioner frameworks, a long-standing branching strategy and several vendors agree on risk tiering); vendor or single source for the figures (Vercel 58%, LoopRails attack rates); official docs for GitHub stacked PRs, which are in preview.

- **Sources:**
  - Ship / Show / Ask (martinfowler.com, practitioner article, 2021): https://www.martinfowler.com/articles/ship-show-ask.html
  - How much can you delegate to agents? (PostHog newsletter, vendor): https://newsletter.posthog.com/p/agent-autonomy
  - AI agent autonomy levels, from logged to locked down (community post, LoopRails): https://dev.to/brennhill/ai-agent-autonomy-levels-from-logged-to-locked-down-45am
  - Autonomous engineering loop, no J3016 equivalent (vendor guide): https://www.augmentcode.com/guides/autonomous-engineering-loop
  - Autonomous coding agents in 2026, Swarmia levels cited (vendor blog): https://www.tembo.io/blog/autonomous-coding-agents
  - Risk Triage (Gitar / Sonar product docs, vendor): https://www.sonarsource.com/products/gitar/features/risk-triage/
  - Approval policies (CodeRabbit docs, vendor): https://docs.coderabbit.ai/pr-reviews/approval-policies
  - 58% of PRs in our largest monorepo merge without human review (Vercel blog, vendor; URL returned 404 when fetched, content from search snippet): https://vercel.com/blog/58-percent-of-prs-in-our-largest-monorepo-merge-without-human-review
  - Risk-based code review: tier rigor by blast radius (community post): https://dev.to/pyor/risk-based-code-review-tier-rigor-by-blast-radius-352j
  - Stack AI-generated code in pull requests (GitHub docs, official): https://docs.github.com/en/copilot/tutorials/stack-ai-generated-code-in-pull-requests
  - GitHub stacked pull requests (news report): https://infoq.com/news/2026/08/github-stacked-pull-requests
  - Stacked agent sessions on unmerged feature branches (pattern note): https://agentpatterns.ai/workflows/stacked-agent-sessions/

- **Limits:** No controlled study compares tiered and fixed review policies for defect or incident rates; the case numbers come from vendors that sell review or merge tools. The Vercel post could not be read directly. The autonomy-level frameworks are opinion pieces and use different level counts. GitHub stacked PRs are a public preview. No source addresses a solo developer whose AI agents also do the review; the frameworks assume a team.

- **Checked:** 2026-11-13
