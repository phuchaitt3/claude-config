---
topic: human-approval-queue-limits
area: Agent setup
question: Is there a standard size limit for a queue of items waiting on one human (approvals, decisions), and what do teams do when agents produce more than the human can clear?
checked: 2026-11-17
review_months: 12
status: current
---
# Size limits for a human approval queue

- **Question:** Is a fixed cap (for example 3 items) a standard for the queue of decisions that autonomous agents hand to one person? What is done instead?

- **Finding:**
  - **No published numeric standard.** The searches found no accepted maximum queue depth for human approvals. A number has to come from the arrival rate, the time one decision takes and the reviewer's capacity (practitioner blogs; no primary research).
  - **The established idea is a WIP limit set from capacity, not a fixed count.** Kanban limits every column, including review, because work piling up in review means the bottleneck has moved; Little's Law (average time in queue = items in queue / throughput; proved by Little, 1961) says a bigger queue at fixed throughput means longer waits. Starting heuristics differ (team size, or team size plus one) and are tuned from observed cycle time (practitioner write-ups). The backlog itself is not capped.
  - **Agent-approval sources prefer cutting arrivals to capping the queue:** tiered routing (auto-approve low risk, escalate high risk), confidence thresholds, and gating only expensive, irreversible or external actions; high-volume reversible work is covered by audit logs (vendor and practitioner blogs).
  - **Overload shows as approval fatigue:** review time per item falls while the approval rate stays high (one vendor blog: 96%). One person can read about ten items an hour, not two hundred (practitioner blog, anecdotal).
  - **Batching is a workload tool, not a fix**, and expired requests should not be silently cleared: return them to the agent with a signal that the window was missed, so it retries or drops them (practitioner blogs).
  - **Checker's inference (not stated by the sources):** a fixed cap per repository does not scale with the number of repositories or with the user's real capacity. A better shape is one limit on what the user reads in a sitting, with items ranked by priority, and overflow collected in one digest (a single list of waiting decisions) instead of being left unflagged. Skipping an item without any flag is the failure the sources warn about (silent expiry).

- **Departure: no limit on items waiting for the user (user's decision, 2026-11-17; standard: WIP limit on the review step, departed from).** Reasons:
  1. **The standard's origin differs.** WIP limits and Little's Law come from Kanban and lean manufacturing (Little, 1961), written for human teams whose review step is a bottleneck that also stops the next work. The agent-approval blogs only borrow them.
  2. **The limit buys nothing here.** Its benefit is a shorter wait, which needs new work to pause while the queue is full. In the self-drive loop other issues are independent of a `needs-you` item, so a cap only stops useful work. The loop used to stop when the queue reached its limit; a stopped overnight run produces nothing and shortens no wait.
  3. **The reviewer is not one person reading alone.** The user's agents help review (summaries, diffs, self-review modes), so the fatigue problem the sources describe (a person can read about ten items an hour) is much smaller.
  4. **Hidden skips cost more than a long queue.** The failure seen in practice was the opposite of overload: top-ranked user-blocked issues were skipped for two nights with only a line in a summary file. Every flagged item is visible in GitHub; an unflagged one is invisible (the silent expiry the sources warn about).
  5. **The one real risk stays covered without a cap:** stale items and work built on unreviewed work. Gap-list PRs are contained by the `resume-gap` label, parked items are re-checked and flagged after 2 days, and the morning summary lists every open `needs-you` item oldest first with its age, one `gh` query per repository, so it scales with the number of projects.
  6. **How to reverse:** if the queue grows past what the user can clear and items go stale, add a cap on the review step back in the self-drive skill (step 5) or lower-priority items to a digest; the evidence to watch is item age in the morning summary.

- **Evidence strength:** common practice for WIP limits and Little's Law (many independent sources); anecdotal for agent-approval numbers (vendor and practitioner blogs); no data found for a numeric cap.

- **Sources:**
  - Approval queue as critical path (practitioner blog): https://tianpan.co/blog/2026-06-01-the-approval-queue-that-became-your-critical-path
  - HITL queue dynamics and approver fatigue (practitioner blog): https://tianpan.co/blog/2026/04/23/hitl-queue-dynamics-approver-fatigue
  - Approval fatigue policy fix (vendor blog): https://waxell.ai/blog/human-in-the-loop-approval-fatigue-policy-fix
  - When to add an approval gate (practitioner blog): https://alejandrorioja.com/human-in-the-loop-ai-agents-when-to-build-an-approval-gate/
  - What teams get wrong with human approval for every agent action (vendor FAQ): https://nhimg.org/faq/what-do-teams-get-wrong-when-they-rely-on-human-approval-for-every-agent-action/
  - WIP limits, Kanban guide (practitioner): https://notes.devcloudsoftware.com/blog/wip-limits-kanban-guide
  - Queuing theory and Kanban (tool vendor): https://kanbantool.com/kanban-guide/queuing-theory
  - Little's Law and delivery speed (community post): https://dev.to/mdenda/littles-law-the-math-that-explains-why-your-team-delivers-slowly-31j3

- **Limits:** Mostly vendor and practitioner blogs; the 14,000-item and 96% figures are single anecdotes. Nothing studied a single-person, multi-repository setup. Related: `findings/overnight-agent-runs` (morning review capacity).

- **Checked:** 2026-11-17
