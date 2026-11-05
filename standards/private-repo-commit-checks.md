# Commit checks in a private repository

- **Question:** Can the secret and output checks before a commit be skipped in a private repository that is never meant to be public?
- **Checked:** 2026-11-05

## Finding

- **Private repositories leak more, not less** (GitGuardian, 2025): about 35% of private repositories scanned held at least one plaintext secret, against about 4.6% of public ones. AWS IAM keys appeared in 8.17% of private repositories against 1.45% of public ones, and generic passwords in 24.1% against 8.94%. The vendor reads this as teams relaxing in private repositories, and advises scanning private repositories too.
- **GitHub push protection has gaps** for generic secrets and private repositories (same report), so a server-side check does not replace one before the commit.
- **Build and run outputs stay out of git by default** (community practice): they can be rebuilt from source, bloat history and cause merge conflicts that are hard to resolve. `.gitignore` does not remove a file already committed; `git rm --cached` does, but the file stays in history. Exceptions: files a framework says to commit, release snapshots, checked-in templates.

Not from a source (the checker's inference): "never public" is not a property git can enforce. A repository can be made public, shared or cloned later, and a committed secret stays in history until the history is rewritten. A check of a single diff by an agent takes seconds, so skipping it saves almost nothing.

## Sources

- [Secret leaks: private vs public repos (GitGuardian blog)](https://blog.gitguardian.com/secret-leaks-private-vs-public-repos) and [State of Secrets Sprawl 2025 press release](https://blog.gitguardian.com/the-state-of-secrets-sprawl-2025-pr) (vendor report).
- [CEO commentary (Cyber Defense Magazine)](https://www.cyberdefensemagazine.com/new-report-shows/) (vendor opinion).
- [Should you commit dist? (VibeReference)](https://vibereference.vercel.app/devops-and-tools/should-you-commit-dist-folder) and [.gitignore best practices (ITU Online)](https://www.ituonline.com/blogs/mastering-gitignore-files-best-practices-for-cleaner-safer-repositories/) (community guides).

## Limits

The secret figures come from one vendor that sells secret detection, and its blog and press release differ slightly on some numbers. The scanned private repositories are GitGuardian customers' repositories, not a random sample. The guidance on build outputs comes from blog posts and mailing lists, not from an official standard. Which secret-scanning features GitHub offers for personal private repositories was not checked.
