# Architecture decision record lifecycle

- **Question:** What statuses does an ADR have, and does a review block the work?
- **Checked:** 2026-11-01

## Finding

- Fowler: an ADR is "proposed" while under discussion, "accepted" once the team adopts it, and "superseded" once significantly changed or replaced, with a link to the replacement. An accepted record is not reopened or edited; a change makes a new record that supersedes it.
- GDS Way: no status is needed while a record is first drafted; the pull request's state tracks it until acceptance. A superseded record is marked with a status line under its heading and links to the new one.
- Other sources add "rejected" or "deprecated"; they are common variants, not part of the core lifecycle.
- None of the sources read says a pending review blocks work built on a proposed record. That reading (merge of the pull request is the acceptance gate; later questions lead to a superseding record) is the checker's inference.

## Sources

- [Fowler, Architecture Decision Record](https://www.martinfowler.com/bliki/ArchitectureDecisionRecord.html) (practitioner article).
- [GDS Way, architecture decisions](https://gds-way.digital.cabinet-office.gov.uk/standards/architecture-decisions.html) (government service standard; its page says it is for internal use by that community; last reviewed 2026-03-05).
- Several ADR templates (Ministry of Justice and others) for the "rejected" and "deprecated" variants, seen in search results only.

## Limits

Search excerpts only for Fowler and the GDS Way; Nygard's original article does not define these statuses in the pages read.
