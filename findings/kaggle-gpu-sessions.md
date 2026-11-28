---
topic: kaggle-gpu-sessions
area: ML systems
question: Can the Kaggle API or CLI show or cancel active kernel sessions, what happens when a kernel is pushed again while a version is active, and how do other systems treat a duplicate run? (Separate entry: the other Kaggle entries cover login and environment pinning, not sessions.)
checked: 2026-11-28
review_months: 6
status: current
---
# Kaggle GPU sessions: seeing, cancelling and re-pushing

**Question:** Can the API or CLI list or cancel active sessions, what does a second push do to the running version, and what is the usual handling of a duplicate run? (Separate from the other Kaggle entries, which cover login and environment pinning.)

**Finding:**
- Pushing again does not stop the version already running: one kernel was seen with version 2 RUNNING and version 3 QUEUED (CLI 2.2.5). The plain `kaggle kernels status <owner>/<kernel>` reports the latest version only.
- Status of an older version: CLI `.../<kernel>/<N>`; the API field is `version_label`, written `v<N>` (a bare number gives 404).
- The latest version number comes from `GetKernel` (`current_version_number`) in `kagglesdk`; the list call returned 0 for it, and `kaggle kernels list` shows no version.
- No call listing sessions was found in `kagglesdk` 0.1.38. `CancelKernelSession` exists but needs a session id that no public response returns, so a version can be stopped only in the web page. The maintainers said on 2026-11-24 that the back-end change needed is not planned. `kernels delete` removes the whole kernel, not one version.
- The quota call showed `timeReserved` 0s while a version was RUNNING, so it does not count sessions.
- No start time per version was found; `GetKernel` gave a last-run time three days old for a kernel with an active version.
- Why a second version waits is not documented. In the observed case all other readable kernels were COMPLETE and weekly quota was left, yet version 3 stayed QUEUED while version 2 ran. Community reports (search summaries only, pages not read) give a one-queued-commit-per-user policy (said about TPU), GPU shortage, and runs stuck in QUEUED. Checker's own inference: versions of one kernel may run one at a time while the waiting one still counts as a session.
- A new version is listed at once: on a private CPU script kernel, a check started right after `kernels push` returned saw version 1 RUNNING, and a second push started at the same moment, held back by a local lock, saw it too (end-to-end test of the push tool).
- Status calls are rate limited: about 100 within a few seconds drew "429 Too Many Requests" on some of them.
- Nearest practice for duplicate runs, GitHub Actions concurrency groups: by default the running run continues, one run may wait, and a newer waiting run replaces the older one; stopping the running one is opt-in (`cancel-in-progress`). Checker's own inference: without a cancel call, "replace the waiting run" is not possible on Kaggle, so the closest safe equivalent is to refuse a second push of a kernel that has an active version.

**Sources:**
- [GitHub, control workflow concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency) (official docs).
- [kaggle-cli issue #1169](https://github.com/Kaggle/kaggle-cli/issues/1169) and [PR #1255](https://github.com/Kaggle/kaggle-cli/pull/1255) (closed unmerged).
- [Kaggle forum, queuing a second commit](https://www.kaggle.com/discussions/product-feedback/276952) and [a project that re-pushes a stuck QUEUED notebook](https://github.com/eslam733/voicetut-kaggle/pull/3) (community; search summaries only).
- First-hand, 2026-11-28: read-only calls with CLI 2.2.5 and `kagglesdk` 0.1.38 on one account.

**Limits:** One account and one observation of two active versions of one kernel. That a QUEUED version counts against the 2-session limit is inferred from refused pushes, not documented. How many older versions can stay active, and whether CPU kernels behave the same, were not tested. No official Kaggle page on any of this was found.

**Checked:** 2026-11-28
