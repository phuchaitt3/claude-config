---
topic: required-security-checks
area: Software process
question: Which security scans should block a merge on GitHub, how is blocking set up, is dependency review worth enabling, and how is a gate kept from blocking unrelated pull requests? (Separate entry: no other entry covers security gates.)
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
- **Dependency review (added 2026-11-28):**
  - The action is available for all public repositories, and private ones with GitHub Code Security or Advanced Security; it needs the dependency graph (GitHub docs, action README).
  - It looks at vulnerable versions *introduced by the pull request's package changes*, not the whole tree (GitHub docs). `fail-on-severity` defaults to `low` (action README).
  - **Inference:** worth enabling on a public repository: it is free there, and because it judges only the PR's changes it cannot block an unrelated pull request. Set the threshold to match the code-scanning gate (for example `high`) instead of the default.
- **Newly published CVEs and unrelated pull requests (added 2026-11-28):**
  - Gating only on newly introduced vulnerabilities, with existing ones reported elsewhere, is used by at least one organisation (Camunda) and described by vendor guides; scheduled rescans catch CVEs published after a build, and are suggested to raise alerts rather than fail pull requests (vendor guide).
  - Skipping unfixed vulnerabilities avoids a red build nobody can act on (vendor guide; Trivy `ignore-unfixed`).
  - Docker: rebuild images regularly (`--pull`); tags are mutable; a digest pin opts out of automatic fixes, so pair it with Dependabot `package-ecosystem: "docker"` (Docker docs).
  - Trivy exceptions can expire: `expired_at` in `.trivyignore.yaml` (experimental), or `exp:YYYY-MM-DD` after the ID in `.trivyignore` (Trivy docs).
  - **Inference:** to stop a newly published CVE blocking unrelated work, run the failing gate only when the pull request changes what goes into the image (Dockerfiles, dependency manifests and lockfiles) and keep the scheduled run as the alarm. The cost: other pull requests merge while a known fixable critical is still in the image.
- **Sources:**
  - GitHub, about dependency review (official docs): https://docs.github.com/en/code-security/concepts/supply-chain-security/about-dependency-review
  - dependency-review-action README (official): https://github.com/actions/dependency-review-action
  - Docker, build best practices (official docs): https://docs.docker.com/build/building/best-practices/
  - Trivy, filtering (official docs): https://trivy.dev/latest/docs/configuration/filtering/
  - Camunda, dependency vulnerability gate (organisation docs, search summary): https://camunda.github.io/camunda/dependency-vulnerability-gate/
  - Safeguard, scanning images in CI (vendor blog, search summary): https://www.safeguard.sh/resources/blog/scanning-docker-images-in-ci-cd
  - GitHub, code scanning merge protection (official docs): https://docs.github.com/en/code-security/code-scanning/managing-your-code-scanning-configuration/set-code-scanning-merge-protection
  - Handbooks (organisation docs, read as search summaries): https://department-of-veterans-affairs.github.io/github-handbook/required-status-checks , https://ministryofjustice.github.io/nvvs-devops/runbooks/static-code-analysis.html
- **Limits:** the docs page does not compare the two mechanisms in detail; no source says how a team should choose between blocking all pull requests and only image-changing ones; no standard for how to introduce a new required check was found (searched 2026-11-28).
- **Checked:** 2026-11-28
