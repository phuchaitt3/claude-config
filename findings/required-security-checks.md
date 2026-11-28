---
topic: required-security-checks
area: Software process
question: Which security scans should block a merge on GitHub, and how is blocking on their findings set up? (Separate entry: no other entry covers security gates.)
checked: 2026-11-28
review_months: 12
status: current
---
# Security scans as merge gates

- **Question:** Which scans should be required, and how?
- **Evidence strength:** official GitHub docs for the mechanism; the choice of scans has only a few organisations' handbooks behind it.
- **Finding:**
  - Code-scanning findings are gated by the ruleset rule "Require code scanning results", per tool, with a security threshold (None, Critical, High or higher, Medium or higher, All) and an alert threshold (None, Errors, Errors and Warnings, All). This is separate from required status checks (GitHub docs).
  - Some organisations require CodeQL and Trivy and fail on high or critical findings (handbooks); no single standard set was found.
  - **Inference:** a CodeQL analysis job can succeed while reporting alerts, so requiring the job alone does not block findings. A scanner job that exits non-zero only on fixable critical vulnerabilities can be required as a status check; a newly published vulnerability can then block unrelated pull requests until the image is updated.
- **Sources:**
  - GitHub, code scanning merge protection (official docs): https://docs.github.com/en/code-security/code-scanning/managing-your-code-scanning-configuration/set-code-scanning-merge-protection
  - Handbooks (organisation docs, read as search summaries): https://department-of-veterans-affairs.github.io/github-handbook/required-status-checks , https://ministryofjustice.github.io/nvvs-devops/runbooks/static-code-analysis.html
- **Limits:** the docs page does not compare the two mechanisms in detail; dependency review was not researched.
- **Checked:** 2026-11-28
