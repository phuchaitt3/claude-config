# study-design mode

**Goal:** the user learns system design by studying and questioning the decisions agents make in the project (user's decision, 2026-10-31; replaces "the user makes the decisions").
**Who decides the architecture:** agents, with the full reasoning written out. The user reviews from outside the loop: asks why, challenges assumptions, and may overrule. Work does not wait for the review; overruling a decision means a follow-up change.

## What counts as an architecture decision

A new service, store, queue, protocol, data model, or a scaling or consistency choice. Implementation details inside an agreed design stay the agent's call.

## Agent steps

1. Write the ADR in the project's template, every section for a choice that is costly to reverse: requirements with numbers, each real option with its trade-offs, why the others lost, consequences, what breaks at 1000x the load, and 2-4 sources to read. Write for a reader new to system design: explain each term on first use.
2. Open a review issue labelled `adr-review`, assigned to the user, linking the ADR. Build the decision without waiting for the review.
3. Answer the user's questions in that issue. When a question exposes a gap or a wrong call, fix the ADR or supersede it, and record the question and answer in the ADR's "Review" section.
4. Where the decision rests on a performance claim, measure it and put the numbers in the ADR.

## User steps

Read the ADR and question it as an outsider: why this and not X, what was assumed, what breaks first. An ADR counts as reviewed when your questions are answered. You may overrule any decision.

## ADRs

- The project keeps the template (`docs/adr/README.md`), which ends with a "Review" section (questions and answers). Use every section for a choice that is costly to reverse; Context, Decision and Why are enough for a small one.
- ADRs written before this version are rewritten by agents to the full template, then reviewed like any other.

## Where things live

Process and templates live in the project (`docs/design/`, `docs/adr/`), not here, so the project makes sense on its own.
