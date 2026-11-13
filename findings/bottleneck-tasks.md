# Bottleneck tasks

**Question:** Do teams build an automatic system that finds the tasks blocking other work and puts them first?

**Finding:**
- **Dependencies are data in the tracker, not prose.** GitHub issue dependencies (generally available 2025-08-21) mark an issue "blocked by" or "blocking" another, up to 50 each, with search filters `is:blocked`, `is:blocking`, `blocked-by:<n>`, `blocking:<n>`, and REST, GraphQL and webhook support. Forgejo and Gitea added the same in 2025; GitLab has blocking links. A "Blocked by #n" line in an issue body is invisible to these filters.
- **Unblocking comes before new work.** Kanban practice counts blocked items against the WIP limit and has the team work on unblocking them before pulling new items (Little's law: more work in progress means longer cycle time). A separate "Blocked" column is called an anti-pattern, because it invites pulling more work. The clock on cycle time keeps running while an item is blocked.
- **Measure, then act on the biggest cause.** Blocker clustering logs each block, groups them by cause, and ranks the groups by total blocked time. Work-item age and queues in front of a step show where the constraint is (Theory of Constraints). The constraint moves once it is fixed, so the check repeats.
- **Escalation by age.** A common written policy: the team tries to clear a blocker within 24 hours, then someone with more authority steps in.
- Checker's inference, not in the sources: ranking open issues by how many open issues they block (fan-out), and taking the top unblocked one first, is the small-team automation of these ideas. No source names a standard tool or formula for it.

**Sources:**
- GitHub changelog, "Dependencies on issues are now generally available" (official): https://github.blog/changelog/2025-08-21-dependencies-on-issues/
- ProKanban.org, "What's wrong with having a Blocked column?" (practitioner community): https://www.prokanban.org/blog/whats-wrong-with-having-a-blocked-column
- ProKanban.org, "Automating the impact of blocked work in Jira" (practitioner community): https://prokanban.org/blog/automating-the-impact-of-blocked-work-in-jira
- Kanbanize, "Block clustering" (vendor): https://www.kanbanize.com/kanban-resources/kanban-analytics/block-clustering
- InfoQ, "Blockers and defects for process improvement" (practitioner article): https://www.infoq.com/articles/blockers-defects-process-improvement
- Steve Fenton, "Two ways to reduce bottlenecks with the Theory of Constraints" (practitioner blog): https://dev.to/_steve_fenton_/two-ways-to-reduce-bottlenecks-with-the-theory-of-constraints-335b
- Visible Consulting, "My blocker playbook" (practitioner blog, source of the 24-hour tier): https://visibleconsulting.substack.com/p/my-blocker-playbook

**Limits:** Apart from the GitHub changelog, every source is a practitioner or vendor blog. None is a formal standard, and none was written for AI agents. The 24-hour tier comes from one blog. Which GitHub plans include dependencies was not stated on the changelog page. The REST endpoint paths were seen only in secondary sources (`/issues/{n}/dependencies/blocked_by`, taking the numeric issue ID); one call to it on a public repo returned an empty list without error.

**Checked:** 2026-11-01
