---
topic: backlog-ready-depth
area: Software process
question: How far ahead of the work do teams check backlog items for readiness (dependencies, prerequisites), and is the depth fixed or set from throughput?
checked: 2026-11-18
review_months: 12
status: current
---
# How deep to keep the backlog "ready"

- **Question:** Before work is pulled, how many items do teams prepare (dependencies found, prerequisites in place), and do they fix that number or derive it from throughput?

- **Finding:**
  - **One to two cycles of ready work is the usual target.** Scrum.org recommends one to two Sprints' worth of "Ready" items; Scrum Alliance says the items for the next one or two sprints need to be ready. Others say two to three sprints in detail, with the wider backlog (three to six sprints) only roughly ordered.
  - **Depth is measured in throughput, not a fixed count.** Scrum.org's "ready story forecast" counts how many sprints of ready work exist from average throughput. A Kanban guide suggests a threshold trigger (replenish when the ready queue drops below N) and sets cadence by throughput, without saying how to pick N.
  - **Refining too far ahead is waste.** Scrum.org calls over-refinement lean waste; another guide says detailing items 10+ sprints away is usually wasted.
  - **Dependencies are found before commitment.** Kanban replenishment guidance identifies dependencies and risks of newly replenished work before it starts; a "Ready" state means dependencies and size are understood well enough to start.
  - **Definition of Ready is not in the Scrum Guide**; one source warns it should be a guide, not a gate.
  - **Checker's inference (not stated by the sources):** for an agent's overnight run, one "cycle" is one night, so a ready depth of about two nights' merged PRs, recomputed from the run log, is the closest match to this practice.

- **Evidence strength:** *common practice* for one to two cycles and for throughput-based depth (several Scrum bodies and practitioner pages agree); *vendor or single source* for the Kanban threshold trigger.

- **Sources:**
  - Product backlog refinement, how far is too far (Scrum.org blog): https://www.scrum.org/resources/blog/product-backlog-refinement-how-far-too-far
  - Optimizing product backlog refinement, ready story forecast (Scrum.org blog): https://www.scrum.org/resources/blog/optimizing-product-backlog-refinement
  - Product backlog refinement first principles, three to six sprints (Scrum.org blog): https://www.scrum.org/resources/blog/product-backlog-refinement-how-succeed-scrum-team
  - 5 practical ways to optimize backlog refinement (Scrum Alliance): https://resources.scrumalliance.org/Article/5-practical-ways-help-optimize-backlog-refinement
  - Backlog refinement, next 2-3 sprints (Rework): https://resources.rework.com/libraries/project-management/backlog-refinement
  - Kanban replenishment, dependencies before starting (Businessmap): https://businessmap.io/kanban-resources/getting-started/kanban-replenishment
  - Replenishment meeting, throughput-set cadence and threshold trigger (practitioner blog): https://www.resumelens.org/blog/kanban/replenishment-meeting-kanban

- **Limits:** Two standard searches, read as result summaries, no page opened in full. All sources concern human teams with sprints or Kanban boards, not an AI agent's overnight loop; the mapping of a sprint to one night is the checker's. No source gives a formula for the ready depth.

- **Checked:** 2026-11-18
