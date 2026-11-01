# Reviewing dependency lockfile changes

- **Question:** How is a dependency lockfile change reviewed, and must the repository owner do it?
- **Checked:** 2026-11-01

## Finding

- Sources treat a lockfile diff as security-relevant and say a reviewer should be able to explain every change in it. None of the sources read says the owner must be the one who merges it.
- The raw diff is mostly hash and resolved-URL churn, so practice is to summarise it: list the packages added, removed or bumped (name, old to new version). The "added" list matters most, because it includes transitive packages nobody asked for.
- Tooling that does this: a CLI summary (locksift), a pull-request comment with a table of changes (Private Packagist Update Review), and a CI tripwire that flags a lockfile change with no change to the manifest (lockfile-integrity; a tripwire, not an audit).
- Snyk's write-up on npm lockfiles recommends a lint of the lockfile (lockfile-lint: allowed hosts, https) and accepting lockfile changes only from trusted maintainers.

Not from a source (the checker's inference): drawing the line by risk (new package or minor or patch bump from the default registry with hashes kept, versus a major bump, new registry or git source, or removed hashes) is a reasonable policy built on the above, not a published standard.

## Sources

- [locksift](https://pypi.org/project/locksift/) and [the dev.to post on unreadable lockfile diffs](https://dev.to/_06a3df6b50aec966668fb/your-package-lockjson-diff-is-unreadable-thats-a-supply-chain-problem-30hm) (tool page; community post).
- [Private Packagist, Update Review](https://blog.packagist.com/introducing-update-review/) (vendor blog).
- [lockfile-integrity](https://awesome.ecosyste.ms/projects/github.com%2Ftartinerlabs%2Flockfile-integrity) (project listing).
- [Snyk, npm lockfiles as a security blindspot](https://snyk.io/jp/blog/why-npm-lockfiles-can-be-a-security-blindspot-for-injecting-malicious-modules/) (vendor blog).
- [Vulert, pull request security review checklist](https://vulert.com/blog/?p=5379) (vendor blog).

## Limits

All sources are vendor or community posts and tool pages; no standards body or official ecosystem document (npm, PyPI, OpenSSF) was read. Tool quality was not evaluated.
