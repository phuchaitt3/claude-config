# How long an architecture decision record is, and what stays out

- **Question:** How long should an ADR be, and may it carry teaching material?
- **Checked:** 2026-11-01

## Finding

- Nygard (2011, the original ADR article) says the whole record "should be one or two pages long", written as a conversation with a future developer, in full sentences; bullets are for visual style only.
- Microsoft's Azure Well-Architected guide says the log is append-only, uses a consistent template (problem, options considered, decision with trade-offs), and that records should not become design guides: supporting material is linked, and the decision must stand on its own.
- A Microsoft engineering-playbook page adds that low-confidence decisions should be recorded as such.

Not from a source (the checker's inference): putting teaching notes in a separate linked document follows from "link supporting material"; no source prescribes that exact split.

## Sources

- [Nygard, Documenting Architecture Decisions](https://www.cognitect.com/blog/2011/11/15/documenting-architecture-decisions) (original article, read directly).
- [Azure Well-Architected, Architecture decision record](https://learn.microsoft.com/en-gb/azure/well-architected/architect-role/architecture-decision-record) (official docs; read through search excerpts, not the full page).
- [Microsoft code-with-engineering playbook, ADR](https://playbook.microsoft.com/code-with-engineering/design/design-reviews/decision-log/doc/adr/0001-record-architecture-decisions/) (vendor playbook).

## Limits

The Azure page was read only as excerpts. "One or two pages" is Nygard's own advice, not a standards-body rule.
