---
name: experiment
description: Load before trying a new implementation of something that already works (a new database, store, library, model or algorithm), when the user asks "should we replace X with Y", or when adding a feature flag or an experimental mode. How to run the new path beside the old one, measure it against exit criteria set in advance, and then promote it or remove it, with the ADR lifecycle that records the outcome.
---

# Trying a replacement: experiment first, replace on evidence

User's decision, 2026-10-31. Applies when a new option might replace a working, accepted one. A brand-new feature with nothing to replace needs only the toggle steps (2 and 6).

## Steps

1. **Exit criteria first.** Before any code, write down what the new path must show to win (quality, latency, cost, operations), with numbers, and the date by which it is decided. In a project with ADRs this is a new ADR with status **Proposed**; the accepted ADR stays as it is. Criteria set after the results are in do not count. (standard: Nygard, "Documenting Architecture Decisions", statuses proposed/accepted/superseded, checked 2026-10-31)
2. **Behind the existing interface, behind a setting.** Build the new implementation behind the interface the old one already uses (add the interface first if there is none), selected by a setting whose default is the old path. Never fork the callers. (standard: Fowler, Branch by Abstraction, checked 2026-10-31)
3. **The toggle is debt.** When the setting is added, file its removal issue in the same PR, with an expiry date. Keep at most one experimental toggle per component. (standard: Hodgson, "Feature Toggles", release and experiment toggles are short-lived inventory, checked 2026-10-31)
4. **Shadow before switch.** Where both paths can run on the same input, run both, return the old path's result, and log the differences and timings of the new one; errors in the new path are logged, never shown. (standard: parallel run with reconciliation, Thoughtworks Radar; GitHub Scientist, checked 2026-10-31)
5. **Measure against the criteria,** on the same inputs, load and data for both paths. Say which numbers are measured and which are estimates.
6. **Decide and clean up, both ways.**
   - Wins: a new ADR that supersedes the old one (or the part of it that changed), switch the default, then delete the old path and the toggle. The old ADR stays, marked **Superseded by** the new one.
   - Loses or is inconclusive by the date: mark the experiment ADR **Rejected** with the numbers, delete the new path and the toggle. What was learned stays in the ADR.
   - Either way the toggle does not outlive its expiry.

## What not to do

- Replace an accepted design because the new option looks better on paper or is newer: that is the "measured, not assumed" failure this skill exists to prevent.
- Edit an accepted ADR into a different decision. Supersede it.
- Leave both paths running with no date: a permanent second path is a second system to maintain.

## Sources

- Michael Nygard, Documenting Architecture Decisions: https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions
- Martin Fowler, Branch By Abstraction: https://martinfowler.com/bliki/BranchByAbstraction.html
- Pete Hodgson, Feature Toggles (aka Feature Flags): https://martinfowler.com/articles/feature-toggles.html
- Thoughtworks Technology Radar, Parallel run with reconciliation: https://www.thoughtworks.com/radar/techniques/parallel-run-with-reconciliation
