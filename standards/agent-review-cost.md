# What an AI code review of a pull request costs

**Question:** How much does an AI code review of one pull request cost, and is a second-agent review worth it on a small subscription quota?

**Finding:**

- Anthropic's managed Code Review is billed on token use through usage credits, separate from a plan's included usage; Anthropic gives no fixed price, and secondary sources quote an average of $15 to $25 per review, rising with PR size and review depth. Some sources say it is limited to Team and Enterprise plans.
- Review bots that call a model API directly report about 2,400 to 3,200 input tokens and 400 to 800 output tokens per review (cents per PR). Per-seat tools (for example about $19 a seat a month) charge a flat fee instead.
- Several guides argue the measure is cost per *useful* review on the PRs that matter, not cost per review.
- Checker's own measurement (one project, 14 local `/code-review` reviews in Claude Code chat transcripts, 2026-11-01): from the `/code-review` call to the posted review comment, a median of 1.3M input tokens (p90 1.6M; nearly all cache reads of the reviewing chat's context), 7k output tokens and 7 API calls. A whole chat there was a median of 5.5M input tokens, so one review is about a quarter of a chat. The cost follows the reviewing chat's context size times its number of calls, not the size of the diff.

**Sources:**

- [Claude Code docs: code review costs](https://code.claude.com/docs/en/code-review-costs) (official docs): billed by token use, separate from plan usage.
- [Codacy: AI code review cost per pull request](https://blog.codacy.com/ai-code-review-cost-per-pull-request-what-engineering-teams-actually-pay-in-2026) (vendor blog).
- [CodeAnt: Anthropic Claude Code Review](https://www.codeant.ai/blogs/anthropic-claude-code-review), [Emelia: $25 per review](https://emelia.io/hub/claude-code-review-test) (vendor blogs): $15 to $25 per review.
- [DEV: cutting AI code review costs](https://dev.to/bolddeck/how-i-cut-ai-code-review-costs-by-65-a-2026-data-dive-37kp), [DEV: a 50-line GitHub Action](https://dev.to/_2b847605e5fbe8a8c9e26/i-replaced-our-300month-code-review-tool-with-a-50-line-github-action-g39) (community posts): tokens per review for API bots.
- [Unblocked: cost per merged PR](https://getunblocked.com/blog/cost-per-merged-pr) (vendor blog).

**Limits:** no source says how the local `/code-review` command or cache reads count against a Pro plan's limits; the per-review figures are vendor and community numbers, not independent studies; no independent data on how many real bugs an agent review of an agent's PR catches for a solo developer. The transcript measurement is one project and the checker's own.

**Checked:** 2026-11-01
