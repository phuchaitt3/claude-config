# study-design mode

**Goal:** the user learns system design by studying and questioning the decisions agents make in the project (user's decision, 2026-10-31; replaces "the user makes the decisions").
**Who decides the architecture:** agents, with the full reasoning written out. The user reviews from outside the loop: asks why, challenges assumptions, and may overrule. Work does not wait for the review; overruling a decision means a follow-up change.

## What counts as an architecture decision

A new service, store, queue, protocol, data model, or a scaling or consistency choice. Implementation details inside an agreed design stay the agent's call.

## Agent steps

1. Write the ADR as `workflow:adr` says, in the project's template. Put the study material in a linked study note in `docs/design/`, not in the ADR: each term explained for a reader new to system design, requirements with numbers, each option's trade-offs in depth, what breaks at 1000x the load, and 2-4 sources to read.
2. Open a review issue labelled `adr-review`, assigned to the user, linking the ADR. Build the decision without waiting for the review.
3. Answer the user's questions in that issue. When a question exposes a wrong call, write a new ADR that supersedes the old one; when it exposes unclear wording, clarify it with the smallest edit and a dated change-log line. The question and answer stay in the issue.
4. Where the decision rests on a performance claim, measure it. The method and numbers go in a measurement note; the ADR gets one line with the result and a link.

## User steps

Read the ADR and question it as an outsider: why this and not X, what was assumed, what breaks first. An ADR counts as reviewed when your questions are answered. You may overrule any decision.

## ADRs

- **An accepted ADR is frozen** (user's decision, 2026-11-13, after agents re-edited one ADR five times to keep it current; standard: Nygard 2011 and Azure Well-Architected, accepted records are append-only and a changed decision supersedes the old one, checked 2026-11-01). It records what was decided, when, and on which assumptions; it is not edited because the code moved on or a later ADR touched the same area. The only edits are a typo or broken link, the `Superseded by NNNN` status line, and a dated clarification of wording that was unclear when written. Current state lives in the code, issues and study notes. An agent citing an ADR checks that it is not superseded and that the code still matches; where they disagree, the code and the newest ADR win, and the agent says so in the issue or PR.
- Follow `workflow:adr`. The project's template (`docs/adr/README.md`) ends with a change log, not a Review section.
- ADRs written before 2026-11-01 are rewritten by agents: the decision stays unchanged, the study material moves to a linked note, and the Q&A stays in the review issue with one change-log line per change.

## Where things live

Process and templates live in the project (`docs/design/`, `docs/adr/`), not here, so the project makes sense on its own.
