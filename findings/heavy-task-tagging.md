---
topic: heavy-task-tagging
area: Agent setup
question: Do teams and agent tools tag work as "heavy" up front (a label or marker) to decide when it may start, or do they rely on declared resource requests and a check against live capacity?
checked: 2026-11-18
review_months: 12
status: current
---
# Tagging heavy work versus admitting it against live capacity

- **Question:** Is a "heavy" tag on a task (an issue label, a test marker) a common way to decide when it may start, or is the start decision made from declared resource requests and the machine's current state?

- **Finding:**
  - **Tags are common for tests, and they filter by cadence rather than gate by capacity.** Guides on pytest treat markers as labels: mark expensive tests `slow`, register the marker, run `-m "not slow"` locally, skip them in CI unless an environment variable asks, and run the full set nightly; a plugin (`pytest-skip-slow`) skips them by default. One reported PR cut CI time noticeably this way. The tag says when to run a test, not whether the machine has room right now.
  - **Bazel uses a tag and a size as scheduling hints.** Its test encyclopedia says a test's `size` also sets the assumed peak use of other resources such as RAM when run locally (default `medium`), and the `exclusive` tag forces a test to run with nothing else running. A third-party guide calls `exclusive` a scheduling escape hatch that should be rare, and says size drives how many tests run at once (secondary source, not in the official pages read).
  - **Schedulers pair a declared request with an admission check.** Slurm, HTCondor and Kubernetes take the job's declared memory request and start it only where capacity exists (details and sources in `findings/memory-admission-one-machine`); the declaration is an input, the start decision uses capacity.
  - **Local queues for agents on one machine follow the same shape.** `qex` (a local job queue for agents) holds a machine budget, starts a job when its claim fits and holds or rejects an oversized one; `AGCoord` (a local CI and merge queue for agents) has jobs declare CPU or memory and starts them when the machine has room. A research model of agent tasks as a dependency graph sends GPU tasks to a serialized GPU queue (preprint).
  - **No tool found tags an issue-tracker issue as heavy and skips it when the machine is busy.** The searches covered issue labels, polling and claiming and returned only the job-queue designs above, so a label-driven picker is not an established practice.
  - **Checker's inference:** a label is the human-written analogue of a resource request. It has the weakness a request has (nobody keeps it accurate; the triage labels here were already re-set after the fact), and in every system found the label is a hint and the start decision comes from the declared request plus a live check. For this setup that points to treating `heavy` as an optional hint, with the real gate being the live check at the moment a heavy command starts (already done by `gpu_run.py`) and heaviness learned from evidence (a worker that waited on a lock, or was killed for memory, marks its issue), not from a pass that labels every issue up front.

- **Sources:**
  - Markers as tags, `-m "not slow"`, CI gating by environment variable, nightly full runs (guide): https://oneuptime.com/blog/post/2026-02-02-pytest-markers-guide/markdown
  - `pytest-skip-slow`, skips `slow` by default, `--slow` to include: https://pypi.org/project/pytest-skip-slow
  - `pytest-explicit`, tests that run only on request: https://github.com/cryptaliagy/pytest-explicit
  - Bazel test encyclopedia, size and assumed resource use (official docs): https://bazel.build/reference/test-encyclopedia.md
  - Bazel tags, `exclusive` (Aspect docs) and its use as an escape hatch (third-party guide): https://docs.aspect.build/cli/help/tags and https://bazel.virtuslab.com/book/1~2~3/
  - qex, local job queue and machine budget for agents: https://docs.rs/crate/qex/0.25.0
  - AGCoord, local CI and merge queue for agents with declared resources: https://pypi.org/project/agcoord/
  - SAGA, workflow-atomic GPU scheduling for agent inference (arXiv preprint): https://arxiv.org/pdf/2605.00528
  - Admission against declared and live memory: `findings/memory-admission-one-machine`

- **Limits:** One standard search per angle (test markers, Bazel, agent task queues), results summarised from snippets, not full pages. The pytest evidence is guides and plugin pages, not pytest's own docs. The Bazel concurrency claim comes from a third-party page that may be machine-generated. qex and AGCoord are small projects whose docs were read through search summaries, and the SAGA paper is an unreviewed preprint. Absence of an issue-label picker is a negative result from one search, not proof that none exists.

- **Checked:** 2026-11-18
