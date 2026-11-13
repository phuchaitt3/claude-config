# One source of truth for a policy

- **Question:** How do rules written in prose and rules enforced in code stay in step?
- **Checked:** 2026-11-01

## Finding

- Practitioners agree on the idea: keep the rule in one place that enforcement reads, and let the documentation follow from it, so intent and implementation cannot drift apart.
- Policy-as-code tools block non-compliant changes, which stops new drift; they do not fix drift that already exists.
- One source suggests generating the documentation from the same source that enforcement reads.

Not from a source (the checker's own approach): where prose and code must both exist, a test that fails when the two lists differ catches divergence. No result gave a concrete recipe for this.

## Sources

- [OPA and policy automation (Scalr)](https://scalr.com/blog/opa-is-to-policy-automation-as-terraform-is-to-iac) (vendor blog).
- [Code gates should be as clear as the rules they enforce (hoop.dev)](https://hoop.dev/blog/code-gates-should-be-as-clear-as-the-rules-they-enforce) (vendor blog).

## Limits

Vendor and practitioner pages only; no formal standard found.
