# study-design mode

**Goal:** the user learns system design by studying and questioning the decisions agents make in the project (user's decision, 2026-10-31; replaces "the user makes the decisions").
**Who decides the architecture:** agents, with the full reasoning written out. The user reviews from outside the loop: asks why, challenges assumptions, and may overrule. Work does not wait for the review; overruling a decision means a follow-up change.

## What counts as an architecture decision

A new service, store, queue, protocol, data model, or a scaling or consistency choice. Implementation details inside an agreed design stay the agent's call.

## Agent steps

1. Write the ADR as `workflow:adr` says, in the project's template. Put the study material in a linked study note in `docs/design/`, not in the ADR: each term explained for a reader new to system design, requirements with numbers, each option's trade-offs in depth, what breaks at 1000x the load, and 2-4 sources to read.
2. Open a review issue labelled `adr-review`, assigned to the user, linking the ADR. Build the decision without waiting for the review.
3. Answer the user's questions in that issue. When a question exposes a gap or a wrong call, fix the ADR or supersede it, as `workflow:adr` says, and add a dated line to its change log. The question and answer stay in the issue.
4. Where the decision rests on a performance claim, measure it. The method and numbers go in a measurement note; the ADR gets one line with the result and a link.

## User steps

Read the ADR and question it as an outsider: why this and not X, what was assumed, what breaks first. An ADR counts as reviewed when your questions are answered. You may overrule any decision.

## ADRs

- Follow `workflow:adr`. The project's template (`docs/adr/README.md`) ends with a change log, not a Review section.
- ADRs written before 2026-11-01 are rewritten by agents: the decision stays unchanged, the study material moves to a linked note, and the Q&A stays in the review issue with one change-log line per change.

## Where things live

Process and templates live in the project (`docs/design/`, `docs/adr/`), not here, so the project makes sense on its own.
