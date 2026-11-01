---
name: adr
description: Load before writing, rewriting or editing an architecture decision record (ADR), before answering a review question on one, or when deciding whether a choice needs an ADR. How to keep an ADR short and decision-first, one decision per record, append-only once accepted, with teaching material, measurements and review Q&A kept out of it and linked.
---

# Writing an architecture decision record

User's decision, 2026-11-01, after ADR 0002 in book-rag-app grew to about 170 lines mixing a decision, a tutorial, a benchmark, a bug report and a Q&A log. A project's own template (usually `docs/adr/README.md`) wins on section names; these rules still apply.

## When to write one

For a choice that changes the system's structure or a key quality (a store, a queue, a service boundary, a protocol, a data model, a scaling or consistency choice) or is costly to reverse. Skip it for a choice that is small, temporary (a workaround, an experiment's toggle: see `workflow:experiment`) or already settled by a standard the project follows. (standard: Azure Well-Architected, "architecturally significant"; Henderson, when to skip an ADR; checked 2026-11-01)

## The rules

1. **One decision per record.** A decision with phases (now, at 100x, at 1000x) that will be decided at different times gets one record per phase; a later phase is a line under "Next steps" until it is decided. (standard: Henderson, "each ADR should be about one AD"; Azure Well-Architected; checked 2026-11-01)
2. **Decision first.** The title states the decision ("Postgres with pgvector, no separate vector store"), not the topic. The Decision section is one to three sentences and is readable without the rest.
3. **One or two pages.** About 800 words, the change log excluded. If it is longer, something below belongs in a linked note. (standard: Nygard 2011, "one or two pages long"; checked 2026-11-01)
4. **A record, not a design guide.** Keep out of the ADR, and link instead:
   - term explanations, background and deep dives: a study note or brief (in a study-design project, `docs/design/`);
   - benchmarks and query plans: a measurement note with the method and raw numbers; the ADR keeps one line with the result and the link;
   - known bugs and gaps: one line with the issue link.
   The decision must stand alone without the linked material. (standard: Azure Well-Architected, "avoid making decision records design guides… the decision must be clear and stand alone"; checked 2026-11-01)
5. **Neutral context, honest consequences.** Context states the forces (requirements with numbers, constraints) without arguing. Consequences list the bad and neutral ones too, and what follow-up decisions this one causes. (standard: Nygard 2011; checked 2026-11-01)
6. **Confidence and assumptions.** Say how sure the decision is and which assumptions it rests on, marking each number as measured or estimated, with the date. A low-confidence decision names what would change it. (standard: Azure Well-Architected, "record the confidence level"; Henderson, timestamps; checked 2026-11-01)
7. **Append-only once accepted.** Do not rewrite an accepted record's reasoning. A changed decision is a new ADR that supersedes the old one, and both link each other. A clarification, a corrected fact or a new measurement that leaves the decision unchanged is a dated line in the change log, plus the smallest edit to the body. (standard: Nygard 2011 and Azure Well-Architected, append-only and superseded; departs from standard by allowing small dated corrections, as Henderson's teams do: "mutability has worked better"; checked 2026-11-01)
8. **Full sentences, short paragraphs.** Bullets for lists of options or consequences, not as a replacement for reasoning. (standard: Nygard 2011; checked 2026-11-01)

## Review questions

Questions and answers stay in the review issue (or PR), not in the ADR. When an answer changes the ADR, add one dated line to its change log, for example `2026-10-31: defined "half-written" in Context (#35)`. An answer that only explains goes in the issue, or in the study note if it teaches something worth keeping.

## Default template (for a project without one)

```markdown
# NNNN: <the decision, in a few words>

**Status:** Proposed | Accepted | Superseded by NNNN | Rejected   **Date:** YYYY-MM-DD
**Decided by:** <who>   **Confidence:** high | medium | low   **Study note:** <link, if any>

## Context
The forces: the problem, requirements with numbers (measured or estimated), constraints.

## Options considered
Each real option in two to four lines: what it is, its main pro and con.

## Decision
One to three sentences.

## Why
Why this option beat the others, and the assumptions that would change the answer.

## Consequences
Good, bad and neutral; follow-up decisions; the next steps as load grows.

## Change log
Dated one-line entries, newest last.
```

## Sources

- Michael Nygard, Documenting Architecture Decisions: https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions
- Microsoft, Azure Well-Architected, Maintain an architecture decision record: https://learn.microsoft.com/en-us/azure/well-architected/architect-role/architecture-decision-record
- Joel Parker Henderson, Architecture decision record: https://github.com/joelparkerhenderson/architecture-decision-record
- MADR: https://adr.github.io/madr/
