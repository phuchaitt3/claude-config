---
topic: agent-era-bottleneck
area: Agent setup
question: With AI coding agents, is the bottleneck now token money rather than coding time, and is time spent on orchestration and permission prompts rather than review normal?
checked: 2026-11-20
review_months: 6
status: current
---
# Is the bottleneck in the agent era token money?

- **Question:** With AI coding agents, is the limiting factor no longer manual coding time but the money spent on token usage?

- **Finding:**
  - **Half true.** Writing code is no longer the scarce step. The sources that measured anything place the new constraint at review and verification, not at token spend.
  - **Review is the constraint (firm level).** Secondary coverage of a Harvard/Jellyfish study (720,542 engineers, 655 companies) reports pull requests per engineer up 35.7%, resolved Jira issues up 13.7% (not quite significant), and pull-request review time up 56.1%. Figures differ between write-ups; the working paper was not read.
  - **Review costs tokens too.** A paper cited by a community post ("Tokenomics", arXiv 2601.14470) reports an automated pipeline spending 59% of tokens on review and 2% on design. LoLBench (arXiv) reports code verification at 26.4% of non-cached input tokens against 19.8% for editing. So token spend is real, and much of it goes to checking, not writing.
  - **Tokens are a minor share of total cost in one vendor's model.** Sonar (Nov 4, 2026) says tokens are under 10% of total agentic-development cost (6.8% and 8.4% in its two workflows); the larger costs are review, CI cycles, rework and escaped defects. This is an illustrative worked example with assumed inputs, not measured data, and Sonar sells code-quality tools.
  - **A team's own telemetry:** one consultancy's eight weeks of agent sessions split spend as writing 39%, review 23%, shipping (CI, rebases, merge conflicts) 13%, planning 10%, investigating 7%, other 8%; in one week review plus shipping was 46% against 25% for writing. Single company, own classifier, sells cost-analysis services.
  - **Where money does bind:** on a flat-rate plan the limit is the 5-hour and weekly quota, not dollars (see `findings/claude-pro-usage-limits`, `findings/overnight-agent-runs`). For an individual on a small plan, tokens are the binding limit; for a team paying per token, the sources put engineer review time and rework ahead of token bills.
  - **Orchestration and permission prompts are part of the same constraint (added 2026-11-20).** Practitioner sources describe the human's limit as attention across agents, not code reading alone: every agent stalls on a permission prompt, a clarifying question or a finished task waiting for review. OpenAI's Symphony write-up says most people manage about three to five interactive sessions before switching becomes painful (an observation, not a study). A blog cites about 3-4 items of working memory and "up to 40%" of time lost to task switching; that figure is a repeated secondary citation, not checked against the original paper. So spending most time on orchestration and permissions is the common experience, not a sign of doing it wrong. Review figures in the Harvard coverage measure reviewer time in a team, a different thing from one person running several agents.
  - **Documented ways to cut permission prompts (official docs and community guides):** auto mode (a classifier approves routine commands; the built-in starting mode in interactive sessions from Claude Code v2.1.283); sandbox auto-allow for Bash (a host outside the allowlist still prompts; Read, Edit and WebFetch are not sandboxed); static allow rules, and the `/fewer-permission-prompts` skill, which reads the last 50 sessions, keeps read-only commands approved at least three times and proposes up to 20 rules to review; bypass mode only inside a container. Prompts that still remain after these are a sign to widen the allowlist or sandbox, per these guides.
  - **Documented ways to cut orchestration load:** hand work through an issue tracker so agents run until a ticket reaches a review state (Symphony); a few lead agents instead of many subagents (Osmani); a coordinator that filters interruptions.
  - **Checker's inference on "am I doing something wrong":** not by itself. It would be a problem if prompts for the same read-only commands recur (fixable with rules), or if more agents are running than can be handled (the cited ceiling is three to five), or if review is being skipped because attention ran out; the last one is what the Harvard figures warn about. Time spent on orchestration still counts as the scarce human resource named above.
  - **Checker's inference:** "time versus money" is the wrong split. Both are spent on verification; the scarce resource is a human's attention to check agent output, with token quota a second, plan-dependent limit.

- **Evidence strength:** sample or survey (Harvard/Jellyfish figures, seen only through secondary coverage); vendor or single source for the cost split (Sonar, consultancy); no independent measurement of tokens against human time found.

- **Sources:**
  - Agentic Development Economics (Sonar, vendor, 2026-11-04): https://www.sonarsource.com/resources/library/economics-of-agentic-development/
  - The tokenomics of software development: checking AI-written code now costs as much as writing it (community post by a consultancy, Nov 17): https://dev.to/cloudexmachina/the-tokenomics-of-software-development-checking-ai-written-code-now-costs-as-much-as-writing-it-2lak
  - Harvard researchers find AI coding agents shifted the bottleneck to code review (aggregator): https://daily.dev/posts/harvard-researchers-find-ai-coding-agents-shifted-the-bottleneck-to-code-review-aeapqg8jp
  - AI Coding Agents Lift Pull Requests 35.7%, Harvard Study Finds (trade press): https://www.beri.net/article/harvard-jellyfish-study-ai-coding-agents-code-review-bottleneck-output-employment-engineering-org-design
  - Configure permissions; Choose a permission mode; Sandboxed Bash tool (official docs): https://code.claude.com/docs/en/permissions ; https://code.claude.com/docs/en/permission-modes ; https://code.claude.com/docs/en/sandboxing
  - Stop Claude Code asking for permission, without losing control (community guide): https://wmedia.es/en/writing/claude-code-stop-asking-for-permission
  - An open-source spec for Codex orchestration: Symphony (OpenAI, vendor): https://openai.com/index/open-source-codex-orchestration-symphony/
  - The Code Agent Orchestra (Addy Osmani, practitioner): https://addyosmani.com/blog/code-agent-orchestra/
  - More agents, same human brain (practitioner blog): https://codeaholicguy.substack.com/p/more-agents-same-human-brain
  - The Attention Bottleneck: Managing 10 AI Coding Agents at Once (vendor blog; source of the 3-4 items and 40% figures): https://voxos.ai/blog/terminal-focus-routing-multiplexer/
  - Beyond Code Generation: Reliability, Verification, and Cost Economics in the Agentic SDLC (arXiv, not read in full): https://arxiv.org/pdf/2609.04681
  - Where AI Coding Tools Move the Engineering Bottleneck (vendor blog): https://larridin.com/blog/where-ai-coding-tools-move-engineering-bottleneck

- **Limits:** The original Harvard paper, the Tokenomics paper and LoLBench were not opened; numbers come from search summaries and two pages read in full (Sonar, the consultancy post). Most sources sell review or cost tools. No source compares token cost with the engineer time saved in dollars, which is what "money is the bottleneck" would need. Nothing here covers solo users on flat-rate plans except the quota entries linked above. Searches for 2026 METR or DORA results found none. The orchestration and permission-prompt points rest on search summaries of official docs and practitioner blogs; no study measured how a single developer's time splits between review, orchestration and permission handling.

- **Checked:** 2026-11-20
