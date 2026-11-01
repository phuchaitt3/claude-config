# Responding to a leaked secret

- **Question:** What to do first when a secret has been pushed.
- **Checked:** 2026-11-01

## Finding

- Revoke or rotate the credential first. Deleting the file or rewriting history does not undo the exposure: a pushed secret stays in git history, forks, local clones, logs and screenshots, and the gap before someone uses it can be minutes.
- Then check whether GitHub or the provider already acted. For some providers GitHub forwards tokens found in public repositories so they can be revoked; that does not replace your own rotation.
- Then remove the secret from the code and, if it is in history, from history, after rotating.
- Push protection catches new pushes only; it does not make a past leak safe.

## Sources

- [Command line push protection (GitHub docs, Enterprise Server 3.17)](https://docs.github.com/en/enterprise-server@3.17/code-security/concepts/secret-security/command-line-push-protection) (official; an older Enterprise Server page, wording may differ on github.com).
- [DS 013 (Microsoft Zero Trust assessment, DevSecOps)](https://microsoft.github.io/zerotrustassessment/docs/workshop-guidance/devsecops/DS_013).

## Limits

The GitHub page is for an Enterprise Server version that is being discontinued. No source gave provider-specific rotation steps.
