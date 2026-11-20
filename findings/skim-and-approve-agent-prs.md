---
topic: skim-and-approve-agent-prs
area: Agent setup
question: Is approving an agent's pull request after skimming the agent's own summary (without reading the diff) a bad practice, and what do sources recommend instead?
checked: 2026-11-20
review_months: 6
status: current
---
# Approving agent PRs by skimming the agent's summary

- **Question:** A solo developer merges agent PRs by reading the summary the agent wrote and clicking approve, without reading the code. Is that a bad practice, and is a human merge step then worth keeping?

- **Finding:**
  - **The pattern has a name.** Practitioner sources call it the rubber-stamp effect: approving large agent-written PRs with little scrutiny, using passing tests and lint as a stand-in for review. One blog says the reviewer's real choice with a large diff is a superficial approval or an honest "I can't review this in reasonable time" (practitioner blogs).
  - **What a summary-skim cannot catch.** Green tests do not establish correctness; maintainers rejected about half of SWE-bench-passing PRs (secondhand, unverified here). A blog citing a study of 567 agent PRs reports correctness, documentation or style problems in 45.1% of merged agent PRs; another cites enterprise data of about 1.7x more issues in AI-assisted PRs (both secondhand). A solo developer's account says an agent merged a stranger's PR and nobody noticed for three weeks (anecdote).
  - **The agent's own report is the agent's claim, not evidence.** Sources say reviewers want supporting evidence (tests, traces, diffs) and treat missing evidence as a reason to delay a merge (an interview-based arXiv paper, "Plausible Is Not Enough"). Earlier register entries make the same point: an agent checks code against itself, not against intent (`findings/agent-autonomy-tiers`).
  - **What sources recommend instead of a skim:** (1) deterministic gates that do not fade with habit (types, lint, tests, scanners, a rule that the branch may not have fewer tests than main); (2) risk routing: low-risk changes merge on those gates, and human reading goes where a wrong merge is costly (auth, money, data, public claims); (3) post-merge review and revert as the backstop (Ship / Show / Ask; Vercel reported no measurable difference in revert rate, 0.39%, between light-review and no-review low-risk PRs; vendor figure). A solo-developer merge-gate post notes such a gate blocks harmless changes and lets through bugs the tests cannot see. Sources disagree on whether routine low-risk changes need any human review.
  - **So is it bad practice?** Reading only the agent's summary is the pattern the sources warn about, but the sources do not say a human skim is worse than merging on checks alone. They say it adds delay without adding independent evidence, so it is not a good use of the scarce human step.
  - **Checker's inference (not stated by any source):** for this setup, an approve click that does not read the diff is better replaced by an honest rule: merge on deterministic checks for low-risk changes, and spend human time only on a short list where the checks cannot verify the claim (numbers and claims in public text, results labelled as held-out, `.github/`, permission or secret handling), reading the evidence (diff, run output), not the summary. A periodic random sample of merged PRs, read in full, would measure how often the checks miss something.

- **Evidence strength:** anecdotal and vendor (practitioner blogs, vendor posts); one interview-based arXiv paper; the quoted study figures are secondhand and were not checked against the originals. No controlled study compares skim-approval with no human approval.

- **Sources:**
  - How to review AI-generated code without rubber-stamping it (community post): https://dev.to/alisa_hester_1/how-to-review-ai-generated-code-without-rubber-stamping-it-4a8c
  - The Rubber-Stamp Collapse: why AI-authored PRs are hollowing out code review (practitioner blog): https://tianpan.co/blog/2026/04/23/rubber-stamp-collapse-ai-authored-prs
  - How to review AI-generated pull requests (SpecStory, vendor): https://specstory.com/learning/code-review/reviewing-agent-pull-requests
  - Plausible Is Not Enough: trust and evidence in AI-authored PR review (arXiv, interviews; summary only): https://arxiv.org/pdf/2610.21144
  - Risk-gated AI pull request approval with Copilot (vendor blog): https://keyholesoftware.com/ai-pull-request-approval-copilot/
  - A free-tier merge gate for the solo developer (community post): https://dev.to/devgo_5325/a-free-tier-merge-gate-for-the-solo-developer-33jl
  - My AI agent merged a stranger's pull request, and I didn't notice for three weeks (community post, anecdote): https://dev.to/anton_shubin_f26b3cb5a572/my-ai-agent-merged-a-strangers-pull-request-and-i-didnt-notice-for-three-weeks-4mb8
  - Nothing should merge on an AI's word (community post, title only): https://dev.to/aicodeops_dev/nothing-should-merge-on-an-ais-word-23b8
  - AI-assisted development playbook (GitLab handbook): https://handbook.gitlab.com/handbook/engineering/workflow/ai-assisted-development

- **Limits:** Everything was read through search summaries, not the full pages. The statistics come from blogs citing studies, not from the studies. No source addresses a solo developer whose agents also write the summary; the frameworks assume a team. Related: `findings/agent-autonomy-tiers`, `findings/agent-era-bottleneck`, `findings/human-approval-queue-limits`.

- **Checked:** 2026-11-20
