# Keeping secrets out of a public repository

- **Question:** How is a secret kept out of a public repository, and how common are leaks?
- **Checked:** 2026-11-01

## Finding

- **Push protection** (GitHub) refuses a push that contains a known token type, before the push is accepted. It supports only high-confidence token formats, so a generic password or an unusual key is not caught. Bypasses are logged. For public repositories, secret scanning is free on all plans and push protection for users is on by default for supported secrets. GitHub now groups these under "Secret Protection".
- **A client-side scanner** (for example gitleaks) in pre-commit and CI is the usual second layer; GitLab's own issue on push scanning treats pre-commit scanning as a separate option.
- **Secrets live in a store, not in code:** OWASP's guidance (read here through secondary summaries) covers the whole lifecycle: creation, storage, access, rotation, revocation, auditing; prefer short-lived credentials.
- **Scale** (GitGuardian): 23.8M secrets leaked on public GitHub in 2024, and 70% of those leaked in 2022 were still valid two years later; the 2026 edition reports 29M new hardcoded secrets in 2025 (read through secondary coverage). The older "over 90% still valid after 5 days" figure is from the 2024 report (2023 data), not current.

Not from a source (the checker's advice): set a spending cap on any paid API key so a leaked key has a ceiling on cost.

## Sources

- [Push protection (GitHub blog)](https://github.blog/news-insights/product-news/push-protection-github-advanced-security) (official).
- [Server-side push scanning (GitLab issue)](https://gitlab.com/gitlab-org/gitlab/-/issues/422574).
- [OWASP secrets management summary (Infisical)](https://infisical.com/blog/owasp-secrets-management-cheat-sheet) (vendor summary; the OWASP cheat sheet itself was not read).
- [State of Secrets Sprawl 2025 (GitGuardian)](https://blog.gitguardian.com/the-state-of-secrets-sprawl-2025/) and [2026 coverage (The Hacker News)](https://thehackernews.com/2026/03/the-state-of-secrets-sprawl-2026-9.html) (vendor report; secondary coverage).

## Limits

The OWASP cheat sheet itself (cheatsheetseries.owasp.org) was not read; read it for authoritative detail. Some search results were low-quality copies and were ignored.
