---
topic: backlog-label-lint
area: Software process
question: Do teams automatically check issue labels and links for consistency, and do those checks warn or block?
checked: 2026-11-18
review_months: 12
status: current
---
# Linting issue labels and links: advisory or blocking

- **Question:** Is it common to run an automatic check that finds issues with missing or inconsistent labels or dependencies, and is the result a warning or a block?

- **Finding:**
  - **Label checks exist as GitHub Actions, aimed at new or edited items.** `required-labels-action` takes `required_any` and `required_all` lists; one example workflow fails when an `area:` prefix is missing; the Triage Issues action checks that issues carry expected labels and re-checks on a `/triaged` comment; Issue Label Enforcer fails a workflow when a label requirement is not met. These act when an item is opened or edited.
  - **No ready-made sweep of an existing backlog was found.** The search returned no scheduled job that scans open issues for label inconsistencies; a cron workflow over the GitHub API would be needed.
  - **Advisory checks are the common pattern in Jira guidance.** One vendor guide recommends a sprint-start rule that finds items missing required fields and comments or notifies the owner, and argues hard gates belong at key workflow transitions. A script project runs over a Jira project, finds issues that break hygiene rules, then comments or fixes. FlowAnalyzer's missing-labels rule carries a default severity of medium, a graded warning.
  - **Hidden dependencies are a known gap.** A community post says dependencies are invisible until you open the item and proposes automation that flags blocked and blocking work.
  - **Checker's inference (not stated by the sources):** a script that prints fix-ups beside a ranking, without skipping or blocking any issue, matches the advisory pattern. A keyword match between issue text and a label is a heuristic and will raise false alarms; a `heavy` keyword lint in particular repeats the up-front labelling that `findings/heavy-task-tagging` advises against, so it is left out of this setup.

- **Evidence strength:** *common practice* for advisory warnings over hard blocks (several vendor and practitioner pages agree); *vendor or single source* for each named tool.

- **Sources:**
  - required-labels-action, `required_any` and `required_all` (project listing): https://awesome.ecosyste.ms/projects/github.com%2Fsugarshin%2Frequired-labels-action
  - Triage Issues, checks expected labels (Marketplace): https://github.com/marketplace/actions/triage-issues
  - Issue Label Enforcer (Marketplace news post): https://devops-actions.github.io/github-actions-marketplace-news/blog/2026/05/02/issue-label-enforcer/
  - Issue and PR hygiene workflow with `area:` prefix check (example workflow): https://glama.ai/mcp/servers/@kesslerio/attio-mcp-server/blob/fd518a3faa56a694a312ba9a00998b91542d3ad7/.github/workflows/issue-hygiene.yml
  - Jira hygiene best practices, sprint-start check, gates at transitions (vendor blog): https://www.hivel.ai/blog/jira-hygiene-best-practices-claude-automation-fix
  - JIRA-Hygiene script (project page): https://www.github.com/Roming22/JIRA-Hygiene
  - FlowAnalyzer missing-labels rule, default severity medium (vendor docs): https://flowanalyzer.scrumdesk.com/rules/DV-08
  - Auto-flagging blocked and blocking work (Atlassian community post): https://community.atlassian.com/forums/discussion/3281980/no-more-hidden-dependencies-auto-flagging-blocked-and-blocking-work-with-jira-automation

- **Limits:** Two standard searches, read as result summaries, no page opened in full. All sources are vendor, marketplace or community pages; none is a standard, and none concerns an AI agent's task picker. The advisory-versus-blocking point comes from Jira guidance, not from GitHub.

- **Checked:** 2026-11-18
