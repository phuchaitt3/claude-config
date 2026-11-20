# Findings register

What agents checked outside this repository (industry practice, published research, hiring-market data, tool behaviour), kept so the next chat answers from it instead of searching the web again. An entry records a dated check and how strong its evidence is; it is not necessarily an established standard. Rule: `rules/working-rules.md`, "Industry practice".

The repository is public: an entry names no project and holds no private detail.

## How to use it

- Before a web search about an industry practice, look for the topic below. If a current entry covers the question and today is before its Review by date, answer from it and cite it as `findings/<topic>`. Do not answer from a superseded or archived entry.
- After a search that checks a practice, add or update the entry in the same turn, give it front matter (below), run `python scripts/build_findings_index.py` (it rewrites the index; never edit the index by hand), and tag the point where it is written: `(standard: findings/<topic>, checked YYYY-MM-DD)`, or `(departs from standard: <reason>)`.
- **Sourced lines versus inference (user's decision, 2026-11-15, after an agent wrote two opposite unsourced notes on one question within an hour):** a `(standard: findings/<topic>)` tag may cite only lines that name a source. A line that is the checker's own reasoning is tagged `(inference: findings/<topic>)` and is never cited as a standard. An inference is added or reversed only together with a new search; with none, the point is written as "Open". The register holds no project decisions; those go in the project's own ledger.
- **Unverified entries (user's decision, 2026-11-15):** an entry without an *Evidence strength* field has not been checked line by line and carries an "Unverified" note under its title. Before an agent cites it in a tag or relies on it for a decision, it re-reads the entry's listed sources (or searches), marks each line as sourced or inference, adds the field, removes the note and bumps `checked`. An entry nobody cites stays as it is.
- A hook (`tag_check.py` in the workflow plugin) refuses a commit in this repo that cites `findings/<topic>` with no `findings/<topic>.md`. It checks that the entry exists, not that it supports the claim.
- An entry past its Review by date, a source that has changed, or a new fact that contradicts it means check again and update the entry. A practice that no longer holds is set to `status: superseded` (replaced by a newer entry, named in its Finding) or `archived` (no longer relevant); the file stays so old `findings/<topic>` tags still resolve. Do not delete an entry.
- `python scripts/build_findings_index.py --check` exits 1 when the index is stale; run it before committing a change under `findings/`.

## Reddit and other sources the agent cannot read

The search and fetch tools cannot reach reddit.com (the search API rejects the domain, WebFetch refuses it, and a plain request gets 403); Blind returns 402. Searches show only third-party blogs that paraphrase Reddit. Tested 2026-11-19; the cause is on the tool side, not the user's DNS. So community evidence is a hand-off to the user:

1. Search the open web for the topic first (vendor docs, surveys, trade press) and read what is readable.
2. Give the user 3-5 Google queries of the form `site:reddit.com/r/<sub> <topic words>`. Subreddits by voice: r/recruiting and r/humanresources (recruiters and HR staff: the evidence); r/resumes, r/jobsearchhacks, r/recruitinghell (mostly job seekers: weak).
3. The user pastes the Google result list (titles and snippets). Pick 2-3 threads from the snippets: self-identified practitioners, on the exact question, not older than needed. Skip tool-product chat and translated copies.
4. The user opens each thread and pastes the top comments (above about 10 upvotes) plus the thread URL and date. A paste in any layout is readable; do not ask the user to clean it.
5. Record each thread in the entry as *anecdotal*: URL, subreddit, date or age, upvote counts, and a short paraphrase. No usernames (the register is public) and no long verbatim quotes. State the age of the comments and what the thread does not cover.
6. Raw cleaned text goes in the asking project's own private folder if it has one, never in this repository.

A single thread never overturns a sourced finding; it is an anecdote beside the surveys and vendor documentation. Worked example: `resume-keyword-stuffing`.

## Entry format

One file per topic, `findings/<topic>.md`, starting with front matter (the index is generated from it):

```
---
topic: <topic>            (same as the file name)
area: Software process | Agent setup | Research methods | ML systems | Career
question: <one line>
checked: YYYY-MM-DD
review_months: 12         (6: hiring-market or tool behaviour that changes fast; 12: default; 24: research method or slow-moving process)
status: current           (current | superseded | archived)
---
```

Then the body:

- **Question:** what was asked, in one line.
- **Finding:** the answer in a few lines, as the sources say it. Mark what is the checker's own inference.
- **Evidence strength:** one of: *official standard* (a standards body or the tool's own docs), *common practice* (several independent reputable sources agree), *vendor or single source* (one company or author), *sample or survey* (counts from a sample such as job postings; say its size and how it was drawn), *anecdotal* (blog or forum reports), *no data found*. Entries written before 2026-11-13 lack this field; add it when one is next touched.
- **Sources:** links, each with its kind (official docs, standard body, vendor blog, community post).
- **Limits:** what the sources do not cover, and any source that is secondary or low quality.
- **Checked:** date (the front matter `checked` is the one the index uses; keep both the same).

## Index

Grouped by area so a lookup reads one section; the files stay flat, so a `findings/<topic>` tag never changes when an entry moves section (standard: findings/knowledge-register-layout, checked 2026-11-08). The index is generated and sets Review by from `checked` plus `review_months` (standard: findings/knowledge-register-maintenance, checked 2026-11-15).

<!-- index:start -->
Generated by `scripts/build_findings_index.py` from each entry's front matter; never edit by hand.

### Software process

| Topic | Question | Checked | Review by |
|---|---|---|---|
| [adr-length-and-scope](adr-length-and-scope.md) | How long should an ADR be, and what stays out of it? | 2026-11-01 | 2028-11-01 |
| [adr-lifecycle](adr-lifecycle.md) | What statuses does an ADR have, and does a review block work? | 2026-11-01 | 2028-11-01 |
| [bottleneck-tasks](bottleneck-tasks.md) | Do teams automatically find the tasks blocking other work and put them first? | 2026-11-01 | 2027-11-01 |
| [code-owners-required-review](code-owners-required-review.md) | How does GitHub enforce a list of paths that only the owner may merge? | 2026-11-01 | 2027-05-01 |
| [docker-disk](docker-disk.md) | How do teams keep Docker Desktop's disk use under control on Windows (WSL 2), and how is the space given back? | 2026-11-01 | 2027-11-01 |
| [heavy-job-scheduling](heavy-job-scheduling.md) | How do teams run heavy tests and benchmarks without slowing people, and what scheduling tools exist for an agent on a laptop? | 2026-11-01 | 2027-11-01 |
| [leaked-secret-response](leaked-secret-response.md) | What to do first when a secret has been pushed. | 2026-11-01 | 2027-11-01 |
| [lockfile-review](lockfile-review.md) | How is a dependency lockfile change reviewed, and must the owner do it? | 2026-11-01 | 2027-11-01 |
| [policy-single-source](policy-single-source.md) | How do rules in prose and in enforcement code stay in step? | 2026-11-01 | 2028-11-01 |
| [scaling-tests-on-a-budget](scaling-tests-on-a-budget.md) | How do teams learn how a system behaves at a much larger size or load without a production-size environment? | 2026-11-01 | 2027-11-01 |
| [secret-leak-prevention](secret-leak-prevention.md) | How is a secret kept out of a public repository, and how common are leaks? | 2026-11-01 | 2027-11-01 |
| [worktree-hygiene](worktree-hygiene.md) | How do parallel agents keep a shared checkout current and clean, clean up worktrees, and where do worktrees live on disk? | 2026-11-01 | 2027-11-01 |
| [auto-merge-without-protection](auto-merge-without-protection.md) | Does `gh pr merge --auto` wait for CI on a private GitHub Free repository, and what replaces it? | 2026-11-05 | 2027-05-05 |
| [ml-ci-test-tiers](ml-ci-test-tiers.md) | How do machine-learning projects split tests between pull-request CI and heavier runs? | 2026-11-05 | 2027-11-05 |
| [private-repo-commit-checks](private-repo-commit-checks.md) | Can the secret and output checks before a commit be skipped in a private repository? | 2026-11-05 | 2027-11-05 |
| [project-path-portability](project-path-portability.md) | What should depend on a project's absolute path on disk, so that moving or renaming its folder stays cheap? | 2026-11-05 | 2027-11-05 |
| [solo-pr-or-trunk](solo-pr-or-trunk.md) | Should a solo developer running AI agents use pull requests or commit straight to main? | 2026-11-05 | 2027-11-05 |
| [data-versioning-cadence](data-versioning-cadence.md) | Must every change to a DVC-tracked data folder be committed and pushed, and what do projects do instead? | 2026-11-08 | 2027-11-08 |
| [knowledge-register-layout](knowledge-register-layout.md) | Should a practice register stay one flat folder as it grows, or use categories or subfolders? | 2026-11-08 | 2028-11-08 |
| [docker-run-timeout-cleanup](docker-run-timeout-cleanup.md) | Does `timeout docker run` stop the container, and how is a container run time-limited and always cleaned up? | 2026-11-13 | 2027-11-13 |
| [laptop-cpu-thermal-limit](laptop-cpu-thermal-limit.md) | Is a laptop CPU at 95-100 °C under load overheating or normal? | 2026-11-13 | 2027-11-13 |
| [shared-gpu-one-machine](shared-gpu-one-machine.md) | How is one GPU machine shared between several users or agents without collisions (jobs and long-running services such as model servers), and how is that checked afterwards? | 2026-11-13 | 2027-11-13 |
| [disk-space-alerting](disk-space-alerting.md) | At what free-space level should a machine warn about a filling drive, and is there a standard threshold? | 2026-11-14 | 2027-11-14 |
| [laptop-thermal-tiers](laptop-thermal-tiers.md) | Which GPU temperatures are normal or dangerous on a laptop, what wears it out, and is an 8-10 h nightly load wise? | 2026-11-14 | 2027-11-14 |
| [lenovo-legion-power-modes](lenovo-legion-power-modes.md) | How is the power mode switched on an older Legion when Fn+Q does nothing, and how can a script read CPU temperature without admin rights? | 2026-11-14 | 2027-05-14 |
| [run-outputs-with-worktrees](run-outputs-with-worktrees.md) | Is copying each worktree's git-ignored run outputs back to one DVC-tracked place normal, or is there a better way? | 2026-11-14 | 2027-11-14 |
| [cache-location-windows](cache-location-windows.md) | Should every cache (developer tools, apps such as a browser or music player) move to a second drive, and is that standard practice? | 2026-11-15 | 2027-11-15 |
| [disk-cleanup-windows](disk-cleanup-windows.md) | How do people quickly find and clean old, unused data on a full Windows drive, and should an agent scan the disk itself? | 2026-11-15 | 2027-11-15 |
| [knowledge-register-maintenance](knowledge-register-maintenance.md) | What keeps a register that gains entries constantly usable: owners, review dates, archiving, a generated index? | 2026-11-15 | 2027-11-15 |
| [uv-cache-management](uv-cache-management.md) | Is clearing the uv package cache on a schedule good practice, or how else is its size managed? | 2026-11-15 | 2027-11-15 |
| [laptop-cooling-baseline](laptop-cooling-baseline.md) | To track a laptop's cooling over time (dust, dried paste), must the repeat test be a hot stress test, or does a moderate fixed load work, and how is it kept comparable? | 2026-11-16 | 2027-11-16 |
| [laptop-heat-control-levers](laptop-heat-control-levers.md) | To keep a laptop running long unattended GPU jobs cooler, is "wait to cool before a job starts" a standard practice, and how does it compare with capping GPU power? | 2026-11-17 | 2027-11-17 |
| [monitoring-sample-interval](monitoring-sample-interval.md) | How often do standard tools sample hardware metrics such as GPU temperature, and is a 60-second always-on logger on a laptop light enough to leave running? | 2026-11-17 | 2027-11-17 |
| [backlog-label-lint](backlog-label-lint.md) | Do teams automatically check issue labels and links for consistency, and do those checks warn or block? | 2026-11-18 | 2027-11-18 |
| [backlog-ready-depth](backlog-ready-depth.md) | How far ahead of the work do teams check backlog items for readiness (dependencies, prerequisites), and is the depth fixed or set from throughput? | 2026-11-18 | 2027-11-18 |
| [gpu-benchmark-warmup-duration](gpu-benchmark-warmup-duration.md) | How long must a laptop GPU benchmark (speed, temperature, power at a given clock setting) run before the reading is trustworthy, is a fixed 10-20 minutes per setting standard, and how is steady state detected without thresholds tuned to one machine? | 2026-11-18 | 2027-11-18 |
| [priority-review-cadence](priority-review-cadence.md) | How often are business objectives and the backlog's priority labels reviewed in practice, and is re-triaging every 3-4 nights too often? | 2026-11-18 | 2027-11-18 |

### Agent setup

| Topic | Question | Checked | Review by |
|---|---|---|---|
| [agent-config-protection](agent-config-protection.md) | How are an AI agent's own config files (instructions, settings, hooks) protected from automated changes? | 2026-11-01 | 2027-11-01 |
| [agent-review-cost](agent-review-cost.md) | What does an AI code review of one PR cost, and is a second-agent review worth it on a small quota? | 2026-11-01 | 2027-05-01 |
| [multi-repo-agent-review](multi-repo-agent-review.md) | How are review requests routed when agents work across several repositories? | 2026-11-01 | 2027-11-01 |
| [agent-permission-enforcement](agent-permission-enforcement.md) | Which Claude Code mechanisms enforce a rule instead of asking the model to follow it? | 2026-11-05 | 2027-05-05 |
| [bot-repo-access](bot-repo-access.md) | Must a bot account be added to every repository one by one, and what do teams do instead? | 2026-11-08 | 2027-05-08 |
| [agent-state-freshness](agent-state-freshness.md) | When should a long-running agent re-check state others can change: every step, end of turn, on a timer, or before acting? | 2026-11-11 | 2027-11-11 |
| [keep-awake-long-jobs](keep-awake-long-jobs.md) | How do people keep a laptop awake while long (agent) jobs run without guessing their length, and how are never-ending processes handled? | 2026-11-11 | 2027-11-11 |
| [agent-process-and-resource-control](agent-process-and-resource-control.md) | How are runaway or orphaned shell processes from AI agents stopped, how are CPU and memory limited when several agents share one machine, and is that sharing normally hard? | 2026-11-12 | 2027-11-12 |
| [skill-context-cost](skill-context-cost.md) | What do installed skills cost in context at startup, and how are unused ones switched off (claude.ai and Claude Code)? | 2026-11-12 | 2027-05-12 |
| [claude-code-clear-vs-compact](claude-code-clear-vs-compact.md) | What is recommended about when to clear or compact a Claude Code chat? | 2026-11-13 | 2027-05-13 |
| [overnight-agent-runs](overnight-agent-runs.md) | Does running several coding agents overnight get more work out of a subscription, and what makes the morning result usable? | 2026-11-13 | 2027-05-13 |
| [agent-autonomy-tiers](agent-autonomy-tiers.md) | Is it standard to have speed-first modes that relax human review beside stricter ones, and how does dependent work proceed while a gated PR waits? Automate with stronger review, or gate? | 2026-11-14 | 2027-11-14 |
| [agent-delegation-choice](agent-delegation-choice.md) | Subagent or new session (background session, `claude -p`, another chat): which to hand a task to, and does that decide how many run at once? | 2026-11-14 | 2027-11-14 |
| [agent-loop-control-enforcement](agent-loop-control-enforcement.md) | In a long agent loop, does a text rule ("end each turn by scheduling the next") get skipped as context grows, and what enforces it instead? | 2026-11-14 | 2027-11-14 |
| [agent-loop-stop-on-repeated-failure](agent-loop-stop-on-repeated-failure.md) | In an unattended agent loop, should a task failing twice end the whole loop or only that task, and is a low count sound? | 2026-11-14 | 2027-11-14 |
| [agent-session-handoff-reset](agent-session-handoff-reset.md) | Is it standard for a long-running agent to end its session and start a fresh one with a written handoff, and is the trigger a context-size threshold? | 2026-11-14 | 2027-11-14 |
| [agent-worker-scope-and-verification](agent-worker-scope-and-verification.md) | Is it standard for a worker agent to do the whole task through opening the PR while the coordinator reads only a short report, and how is the result checked? | 2026-11-14 | 2027-11-14 |
| [agent-worker-task-creation](agent-worker-task-creation.md) | Is it standard for a worker agent to create new tasks, or only the coordinator, and what goes wrong when workers spawn work? | 2026-11-14 | 2027-11-14 |
| [claude-code-usage-limit-resume](claude-code-usage-limit-resume.md) | Does a Claude Code session or loop resume by itself after a usage limit resets, can an agent see its quota and pause first, and can resume be tested without using up the quota? | 2026-11-14 | 2027-05-14 |
| [long-agent-run-context](long-agent-run-context.md) | How does a long agent run (a loop or overnight run) keep its context, and token cost, from growing with every task: subagents, a fresh session per task, or other chats? | 2026-11-14 | 2027-11-14 |
| [agent-model-effort-selection](agent-model-effort-selection.md) | How reliable is an agent's own judgement of which model and effort a task needs, and what does the vendor advise for choosing between a smaller and a larger model? | 2026-11-15 | 2027-05-15 |
| [claude-code-plugin-reload-running-chat](claude-code-plugin-reload-running-chat.md) | Does a running Claude Code chat pick up a changed plugin skill, does `/reload-plugins` change that, and can an agent trigger a reload in another chat (no)? | 2026-11-15 | 2027-05-15 |
| [laptop-overnight-heavy-jobs](laptop-overnight-heavy-jobs.md) | Is running heavy agent jobs (GPU, all-core CPU) on a personal laptop every night unattended a common choice, and what are the risks beyond heat wear? | 2026-11-16 | 2027-11-16 |
| [claude-code-multi-repo-sessions](claude-code-multi-repo-sessions.md) | Should an agent session be started in each repository, or should one session work across several repositories? | 2026-11-17 | 2027-05-17 |
| [human-approval-queue-limits](human-approval-queue-limits.md) | Is there a standard size limit for a queue of items waiting on one human (approvals, decisions), and what do teams do when agents produce more than the human can clear? | 2026-11-17 | 2027-11-17 |
| [memory-admission-one-machine](memory-admission-one-machine.md) | How do schedulers decide whether a job fits in memory before starting it on one machine (a lock versus a memory budget), how do they cover long-running services, and how is a VM or container memory cap sized? | 2026-11-17 | 2027-11-17 |
| [heavy-task-tagging](heavy-task-tagging.md) | Do teams and agent tools tag work as "heavy" up front (a label or marker) to decide when it may start, or do they rely on declared resource requests and a check against live capacity? | 2026-11-18 | 2027-11-18 |
| [agent-era-bottleneck](agent-era-bottleneck.md) | With AI coding agents, is the bottleneck now token money rather than coding time, and is time spent on orchestration and permission prompts rather than review normal? | 2026-11-20 | 2027-05-20 |
| [claude-code-transcript-retention](claude-code-transcript-retention.md) | How long does Claude Code keep session transcripts (the .jsonl files under ~/.claude/projects) before deleting them, and how is that changed? | 2026-11-20 | 2027-05-20 |
| [claude-pro-usage-limits](claude-pro-usage-limits.md) | What are the 5-hour and weekly usage limits on the $20 Claude Pro plan, are token figures published, and can a user work out the size of the weekly limit? | 2026-11-20 | 2027-05-20 |
| [skim-and-approve-agent-prs](skim-and-approve-agent-prs.md) | Is approving an agent's pull request after skimming the agent's own summary (without reading the diff) a bad practice, and what do sources recommend instead? | 2026-11-20 | 2027-05-20 |

### Research methods

| Topic | Question | Checked | Review by |
|---|---|---|---|
| [research-held-out-tuning](research-held-out-tuning.md) | Can hyperparameters be chosen on the samples a result is reported on, and what does research practice do instead? | 2026-11-08 | 2028-11-08 |
| [llm-judge-vs-em-f1](llm-judge-vs-em-f1.md) | Does an LLM judge add anything over exact match and F1 when scoring QA or RAG answers? | 2026-11-09 | 2027-11-09 |
| [rag-hypothetical-question-indexing](rag-hypothetical-question-indexing.md) | Is indexing LLM-generated questions per chunk, instead of the chunk text, an established RAG practice? | 2026-11-09 | 2027-11-09 |
| [rag-retrieval-eval-without-benchmark](rag-retrieval-eval-without-benchmark.md) | With no benchmark that fits, how do teams evaluate RAG retrieval, and can LLM-generated test questions be trusted? | 2026-11-09 | 2027-11-09 |
| [rag-eval-confidence-intervals](rag-eval-confidence-intervals.md) | Do RAG and retrieval evaluations report bootstrap confidence intervals, and is it worth it on a small set? | 2026-11-10 | 2027-11-10 |
| [rag-hybrid-fusion](rag-hybrid-fusion.md) | How do hybrid search systems merge vector and keyword results; is RRF the default? | 2026-11-10 | 2027-11-10 |
| [rag-reranker-only-small-pool](rag-reranker-only-small-pool.md) | Is scoring every chunk with a cross-encoder, with no first-stage retriever, established practice, and when does it fit? | 2026-11-10 | 2027-11-10 |
| [rag-retrieval-relevance-without-llm](rag-retrieval-relevance-without-llm.md) | Without an LLM judge, how is a retrieved chunk labelled relevant (gold evidence, answer string, keyword recall), and how reliable is each? | 2026-11-10 | 2027-11-10 |
| [attention-steering-terminology](attention-steering-terminology.md) | Is "attention steering" or "attention intervention" the right term for an inference-time method that edits attention scores? | 2026-11-11 | 2027-11-11 |
| [research-improvement-size](research-improvement-size.md) | Is there a rule of thumb for how large an NLP/ML gain is good, and is a gain diluted by weak retrieval normal to report? | 2026-11-11 | 2028-11-11 |
| [research-baseline-design](research-baseline-design.md) | How is a research baseline built: same pipeline with the studied part switched off, or a separate plain version? | 2026-11-12 | 2028-11-12 |
| [rag-retrieval-metrics](rag-retrieval-metrics.md) | Which metric leads when reporting RAG retrieval: Hit@k, Recall@k, MRR or nDCG? | 2026-11-13 | 2027-11-13 |
| [rag-retrieval-score-ranges](rag-retrieval-score-ranges.md) | Is a top-5 hit rate near 100% normal, or a sign of evaluation bias? What drives retrieval scores up? | 2026-11-13 | 2027-11-13 |
| [rag-eval-offline-vs-app](rag-eval-offline-vs-app.md) | Should a RAG pipeline be evaluated in separate offline scripts or through the running application, and which result goes on a resume? | 2026-11-14 | 2027-11-14 |
| [eval-sample-size](eval-sample-size.md) | How many test questions or timed requests does an evaluation need, and is 30 or about 200 too small? | 2026-11-15 | 2028-11-15 |
| [llm-testset-cross-family-review](llm-testset-cross-family-review.md) | When an LLM writes an evaluation set, is it standard to have a model from another family review it and a person check a sample, and does the cross-family step reduce bias? | 2026-11-15 | 2027-11-15 |
| [attention-prefill-terminology](attention-prefill-terminology.md) | What do papers and docs call (a) the single last-position query that an inference-time method acts on, and (b) the fast built-in attention kernel the rest of the prompt runs through, and which wording avoids implying the custom part is slow? | 2026-11-19 | 2027-11-19 |
| [inference-time-vs-finetuning-gain](inference-time-vs-finetuning-gain.md) | Is it normal for a training-free inference-time method to give a smaller gain than fine-tuning, and is reporting it on top of a fine-tuned model standard practice? | 2026-11-19 | 2027-11-19 |

### ML systems

| Topic | Question | Checked | Review by |
|---|---|---|---|
| [llm-inference-memory-calibration](llm-inference-memory-calibration.md) | How do inference systems size the batch token budget, how is it calibrated, where does a bigger batch stop paying, and what must an inference benchmark report? | 2026-11-09 | 2027-11-09 |
| [benchmark-setup-consistency](benchmark-setup-consistency.md) | Must every benchmark run on the same hardware and configuration, or may results come from different setups? | 2026-11-11 | 2027-11-11 |
| [length-bucketed-batch-sizing](length-bucketed-batch-sizing.md) | When batches are sorted or bucketed by length, how is the batch size picked, and what sample should a timing sweep use? | 2026-11-11 | 2027-11-11 |
| [llm-batch-size-selection](llm-batch-size-selection.md) | How is the batch size for LLM inference chosen (search and pick rule): largest that fits, fastest, or the knee? | 2026-11-11 | 2027-11-11 |
| [vllm-custom-attention-bias](vllm-custom-attention-bias.md) | Can vLLM apply a custom, per-request bias to pre-softmax attention scores, and what would it take? | 2026-11-11 | 2027-05-11 |
| [benchmark-local-vs-shared-gpu](benchmark-local-vs-shared-gpu.md) | Is a personal laptop a worse place to time a benchmark than a free shared cloud GPU, and what keeps a timing number trustworthy on either? | 2026-11-12 | 2027-11-12 |
| [implementation-parity-testing](implementation-parity-testing.md) | When a model pipeline is re-implemented, how many samples and settings does a parity test need, and what counts as a match? | 2026-11-12 | 2027-11-12 |
| [kaggle-environment-pinning](kaggle-environment-pinning.md) | Can a Kaggle notebook be pinned to its original software environment, and from the command line? | 2026-11-12 | 2027-05-12 |
| [lora-vs-qlora](lora-vs-qlora.md) | For fine-tuning a small language model, 16-bit LoRA or QLoRA, and which is more in demand in research and hiring? | 2026-11-12 | 2027-05-12 |
| [precision-across-model-sizes](precision-across-model-sizes.md) | When comparing one model family at several sizes, is numeric precision (fp32, fp16, bf16) held fixed or chosen per model, and what if a model overflows in fp16? | 2026-11-12 | 2027-11-12 |
| [quantization-in-practice](quantization-in-practice.md) | In real research and applications, when is quantization the natural choice, and how often do LLM job postings ask for it? | 2026-11-12 | 2027-05-12 |
| [quantized-large-vs-small-model](quantized-large-vs-small-model.md) | At a fixed memory budget, is a larger 4-bit model better than a smaller 16-bit one, and is 4-bit nearly free below 1B parameters? | 2026-11-12 | 2027-11-12 |

### Career

| Topic | Question | Checked | Review by |
|---|---|---|---|
| [ats-resume-section-headings](ats-resume-section-headings.md) | Does an ATS look for the exact heading "Work Experience", and does a resume without it get rejected? | 2026-11-05 | 2027-11-05 |
| [thesis-as-research-experience](thesis-as-research-experience.md) | Can an undergraduate thesis be listed as "Research Experience" on a resume? | 2026-11-05 | 2027-11-05 |
| [resume-bullet-clarity](resume-bullet-clarity.md) | Should resume bullets be understandable in one read by someone new to the work, and what shape do guides recommend? | 2026-11-08 | 2027-11-08 |
| [resume-english-score-vietnam-it](resume-english-score-vietnam-it.md) | How much does an English test score (IELTS) matter in Vietnamese software hiring, and where does it go on a resume? | 2026-11-09 | 2027-05-09 |
| [resume-projects-as-experience](resume-projects-as-experience.md) | With no formal work history, should projects be formatted like jobs and carry job titles, and may a class project carry a lead title? | 2026-11-09 | 2027-11-09 |
| [resume-academic-honor-placement](resume-academic-honor-placement.md) | Where does a top academic honor (valedictorian, Latin honors) go so it is seen, and may it go in the summary? | 2026-11-10 | 2027-11-10 |
| [resume-dates-revisited-projects](resume-dates-revisited-projects.md) | Should a project revisited after a gap show "start -- Present" or its separate periods? | 2026-11-10 | 2027-11-10 |
| [resume-ml-model-names-and-baselines](resume-ml-model-names-and-baselines.md) | Should an ML bullet name the specific model (including an outdated one in an older project), and give a result against a baseline or alone? | 2026-11-10 | 2027-11-10 |
| [resume-project-stack-line](resume-project-stack-line.md) | How many technologies should a project's stack line list; is "at most 4–5" a rule? | 2026-11-10 | 2027-11-10 |
| [resume-summary-entry-level](resume-summary-entry-level.md) | Does an entry-level resume need a summary, what should it say, and may it restate the top entry? | 2026-11-10 | 2027-11-10 |
| [resume-tailoring-project-context](resume-tailoring-project-context.md) | When tailoring cuts bullets, does an entry lose what the project was, and is that accepted practice? | 2026-11-10 | 2027-11-10 |
| [ats-keyword-matching](ats-keyword-matching.md) | Does an ATS match only the posting's keywords, or also assumed skills (Git, Jupyter) the posting omits? | 2026-11-11 | 2027-05-11 |
| [resume-accuracy-vs-concision](resume-accuracy-vs-concision.md) | When shortening a line would make it read wider than the fact, does accuracy or brevity come first? | 2026-11-11 | 2027-11-11 |
| [resume-bullet-order](resume-bullet-order.md) | Are bullets inside one entry ordered by significance or by time, and must terms be introduced before use? | 2026-11-11 | 2027-11-11 |
| [resume-degree-name-abbreviation](resume-degree-name-abbreviation.md) | Must a resume spell out "Bachelor of Science in …" for ATS, or can it be abbreviated? | 2026-11-11 | 2027-11-11 |
| [resume-high-school-after-degree](resume-high-school-after-degree.md) | After a university degree, does a prestigious or selective high school stay on the resume? | 2026-11-11 | 2027-11-11 |
| [resume-llm-api-listing](resume-llm-api-listing.md) | Is naming a hosted LLM API (OpenAI, DeepSeek) on a resume worth it, and which APIs should be named? | 2026-11-11 | 2027-11-11 |
| [resume-skills-section-tailoring](resume-skills-section-tailoring.md) | When tailoring, should the skills section and stack lines keep every tool, or only relevant ones backed by bullets? | 2026-11-11 | 2027-11-11 |
| [resume-submission-readiness](resume-submission-readiness.md) | What are the final refinement steps, and how do you know a resume is ready to submit? | 2026-11-11 | 2027-11-11 |
| [resume-benchmark-range-reporting](resume-benchmark-range-reporting.md) | May a result measured on several setups be reported as a range, or only the best one? | 2026-11-12 | 2027-11-12 |
| [resume-matching-published-baseline](resume-matching-published-baseline.md) | Does a bullet that matches a paper's published baseline read as replication rather than engineering or research, and is it a red flag? | 2026-11-12 | 2027-11-12 |
| [resume-one-page-fill](resume-one-page-fill.md) | Must a one-page resume fill the page, or may it stay partly empty when no relevant bullets are left? | 2026-11-12 | 2027-11-12 |
| [entry-level-ai-engineer-market](entry-level-ai-engineer-market.md) | How hard is an entry-level AI engineer role to get, what are the common routes to a first job, and are most entry roles residencies or internships (no data)? | 2026-11-13 | 2027-05-13 |
| [leetcode-vietnam-hiring](leetcode-vietnam-hiring.md) | How often do companies in Vietnam use LeetCode-style coding tests for CS and software jobs? | 2026-11-13 | 2027-05-13 |
| [resume-master-subtractive-tailoring](resume-master-subtractive-tailoring.md) | Is cutting a master resume down to one page the best way to tailor, how long should it take, and should every posting get its own version? | 2026-11-13 | 2027-11-13 |
| [resume-technical-term-capitalization](resume-technical-term-capitalization.md) | Should generic method names in resume bullets and skills rows be capitalized or lowercase? | 2026-11-13 | 2027-11-13 |
| [interview-post-application-work](interview-post-application-work.md) | After submitting a resume, may a candidate talk about project upgrades made since, or must they stay within the resume, and is building more before the deadline worth it? | 2026-11-14 | 2027-11-14 |
| [interview-project-depth](interview-project-depth.md) | In an entry-level interview, does explaining an existing project in depth count for more than having more or newer projects? | 2026-11-14 | 2027-11-14 |
| [application-motivation-answers](application-motivation-answers.md) | How much weight does a "why do you want this job or programme" answer carry on an application form, and why do such answers read as hollow? | 2026-11-15 | 2027-11-15 |
| [resume-benchmark-context](resume-benchmark-context.md) | How much benchmark detail (sample size, batch size, hardware) does a resume bullet carry, and must all benchmark bullets list the same fields? | 2026-11-15 | 2027-11-15 |
| [resume-bold-text](resume-bold-text.md) | Is bold text recommended in a resume, where (headings, titles, keywords in bullets), and does it affect ATS parsing? | 2026-11-15 | 2027-11-15 |
| [resume-bullet-density](resume-bullet-density.md) | When a resume entry looks like a wall of text, is that acceptable for a one-page technical resume, or must bullets be trimmed or simplified? | 2026-11-15 | 2027-11-15 |
| [resume-bullet-standalone](resume-bullet-standalone.md) | Must each resume bullet make sense without the others in its entry, and does that make bullets too long? | 2026-11-15 | 2027-11-15 |
| [resume-personal-vs-academic-projects](resume-personal-vs-academic-projects.md) | Does a course (academic) project carry more weight on a new-grad resume than a personal project, and how is a solo rebuild of an old course project labelled and dated? | 2026-11-15 | 2027-11-15 |
| [resume-technique-tool-naming](resume-technique-tool-naming.md) | When a bullet names a method and the tool behind it, which form: "bge-m3 vector search", "vector search (bge-m3)" or "with bge-m3"? | 2026-11-15 | 2027-11-15 |
| [ai-engineer-skill-demand](ai-engineer-skill-demand.md) | How common is each skill family (RAG, fine-tuning, agents and MCP, evaluation, hallucination detection, serving) in AI-engineer job postings, and is any of them "core" for the role? | 2026-11-18 | 2027-05-18 |
| [effective-study-techniques](effective-study-techniques.md) | What study techniques does learning research support for remembering material for a test, and how should reviews be spaced? | 2026-11-18 | 2028-11-18 |
| [entry-level-ml-interview-emphasis](entry-level-ml-interview-emphasis.md) | In entry-level ML and AI engineer interviews and tests, are coding and CS fundamentals or ML theory asked more, and what ML basics recur? | 2026-11-18 | 2027-05-18 |
| [interview-prep-resources](interview-prep-resources.md) | Which resources do people most often use to prepare for coding and CS-fundamentals interviews, and how do they sequence them? | 2026-11-18 | 2027-05-18 |
| [study-error-log-pretest-review](study-error-log-pretest-review.md) | Does keeping a list of your own recurring quick-fix mistakes and rereading it just before a test help, and what does research say about correcting errors? | 2026-11-18 | 2028-11-18 |
| [rag-reranking-spelling](rag-reranking-spelling.md) | Is "reranking" or "re-ranking" the more standard spelling in RAG and retrieval writing? | 2026-11-19 | 2027-11-19 |
| [referral-skips-resume-screen](referral-skips-resume-screen.md) | Does an employee referral let a candidate skip the resume and ATS screening round, or does it only help the resume get read and raise the hire odds? | 2026-11-19 | 2027-05-19 |
| [resume-keyword-stuffing](resume-keyword-stuffing.md) | How much does keyword stuffing (repeating or padding in posting keywords) help a resume pass an ATS, and how relevant is keyword use at all? | 2026-11-19 | 2027-05-19 |
| [resume-skills-row-labels](resume-skills-row-labels.md) | What should the category labels of a skills section be for an AI/ML engineer resume (serving and infrastructure, retrieval and RAG), and may a row mix techniques with tools? | 2026-11-19 | 2027-11-19 |
| [resume-speed-vs-polish](resume-speed-vs-polish.md) | When a deadline or referral is near, should a candidate submit a good resume now or keep refining toward a perfect one, and does applying earlier help? | 2026-11-19 | 2027-05-19 |

<!-- index:end -->
