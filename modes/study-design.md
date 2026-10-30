# study-design mode

**Goal:** the user learns system design by making the real decisions in the project.
**Who decides the architecture:** the user. Agents brief, implement and measure.

## What counts as an architecture decision

A new service, store, queue, protocol, data model, or a scaling or consistency choice. Implementation details inside an agreed design stay the agent's call.

## Agent steps

1. Write a design brief in the project's `docs/design/`: problem, requirements with numbers, 2-3 options with trade-offs, a recommendation, what to read.
2. File it as a GitHub issue labelled `needs-you`, assigned to the user, and keep working on everything else.
3. After the user's ADR, build it.
4. Where the decision rests on a performance claim, measure it and put the numbers in the ADR.

## User steps

Read the brief, choose, and write the decision and reasons in the ADR in your own words. The agent may correct facts, not the reasoning.

## ADRs

- The project keeps the template (`docs/adr/README.md`). Use every section for a choice that is costly to reverse; Context, Decision and Why are enough for a small one.
- Every ADR written before the mode was set is marked "agent-decided, not yet reviewed by the owner". Review them one at a time: one `needs-you` review issue open at once.

## Where things live

Process and templates live in the project (`docs/design/`, `docs/adr/`), not here, so the project makes sense on its own.
