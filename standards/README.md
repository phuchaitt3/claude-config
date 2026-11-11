# Industry-standard register

What agents checked against industry practice, kept so the next chat answers from it instead of searching the web again. Rule: `rules/working-rules.md`, "Industry practice".

The repository is public: an entry names no project and holds no private detail.

## How to use it

- Before a web search about an industry practice, look for the topic below. If an entry covers the question and is under 12 months old, answer from it and cite it as `standards/<topic>`.
- After a search that checks a practice, add or update the entry in the same turn, list it in the matching section of the index below with its Checked date (add a section only when no existing one fits), and tag the point where it is written: `(standard: standards/<topic>, checked YYYY-MM-DD)`, or `(departs from standard: <reason>)`.
- A hook (`tag_check.py` in the workflow plugin) refuses a commit in this repo that cites `standards/<topic>` with no `standards/<topic>.md`. It checks that the entry exists, not that it supports the claim.
- An entry older than 12 months, a source that has changed, or a new fact that contradicts it means check again and update the entry.

## Entry format

One file per topic, `standards/<topic>.md`:

- **Question:** what was asked, in one line.
- **Finding:** the answer in a few lines, as the sources say it. Mark what is the checker's own inference.
- **Sources:** links, each with its kind (official docs, standard body, vendor blog, community post).
- **Limits:** what the sources do not cover, and any source that is secondary or low quality.
- **Checked:** date.

## Index

Grouped by area so a lookup reads one section; the files stay flat, so a `standards/<topic>` tag never changes when an entry moves section (standard: standards/knowledge-register-layout, checked 2026-11-08).

### Software process

| Topic | Question | Checked |
|---|---|---|
| [code-owners-required-review](code-owners-required-review.md) | How does GitHub enforce a list of paths that only the owner may merge? | 2026-11-01 |
| [policy-single-source](policy-single-source.md) | How do rules in prose and in enforcement code stay in step? | 2026-11-01 |
| [secret-leak-prevention](secret-leak-prevention.md) | How is a secret kept out of a public repository, and how common are leaks? | 2026-11-01 |
| [private-repo-commit-checks](private-repo-commit-checks.md) | Can the secret and output checks before a commit be skipped in a private repository? | 2026-11-05 |
| [leaked-secret-response](leaked-secret-response.md) | What to do first when a secret has been pushed. | 2026-11-01 |
| [lockfile-review](lockfile-review.md) | How is a dependency lockfile change reviewed, and must the owner do it? | 2026-11-01 |
| [auto-merge-without-protection](auto-merge-without-protection.md) | Does `gh pr merge --auto` wait for CI on a private GitHub Free repository, and what replaces it? | 2026-11-05 |
| [solo-pr-or-trunk](solo-pr-or-trunk.md) | Should a solo developer running AI agents use pull requests or commit straight to main? | 2026-11-05 |
| [ml-ci-test-tiers](ml-ci-test-tiers.md) | How do machine-learning projects split tests between pull-request CI and heavier runs? | 2026-11-05 |
| [heavy-job-scheduling](heavy-job-scheduling.md) | How do teams run heavy tests and benchmarks without slowing people, and what scheduling tools exist for an agent on a laptop? | 2026-11-01 |
| [scaling-tests-on-a-budget](scaling-tests-on-a-budget.md) | How do teams learn how a system behaves at a much larger size or load without a production-size environment? | 2026-11-01 |
| [adr-length-and-scope](adr-length-and-scope.md) | How long should an ADR be, and what stays out of it? | 2026-11-01 |
| [adr-lifecycle](adr-lifecycle.md) | What statuses does an ADR have, and does a review block work? | 2026-11-01 |
| [bottleneck-tasks](bottleneck-tasks.md) | Do teams automatically find the tasks blocking other work and put them first? | 2026-11-01 |
| [worktree-hygiene](worktree-hygiene.md) | How do parallel agents keep a shared checkout current and clean, clean up worktrees, and where do worktrees live on disk? | 2026-11-01 |
| [project-path-portability](project-path-portability.md) | What should depend on a project's absolute path on disk, so that moving or renaming its folder stays cheap? | 2026-11-05 |
| [data-versioning-cadence](data-versioning-cadence.md) | Must every change to a DVC-tracked data folder be committed and pushed, and what do projects do instead? | 2026-11-08 |
| [docker-disk](docker-disk.md) | How do teams keep Docker Desktop's disk use under control on Windows (WSL 2), and how is the space given back? | 2026-11-01 |
| [knowledge-register-layout](knowledge-register-layout.md) | Should a practice register stay one flat folder as it grows, or use categories or subfolders? | 2026-11-08 |

### Agent setup

| Topic | Question | Checked |
|---|---|---|
| [agent-config-protection](agent-config-protection.md) | How are an AI agent's own config files (instructions, settings, hooks) protected from automated changes? | 2026-11-01 |
| [agent-permission-enforcement](agent-permission-enforcement.md) | Which Claude Code mechanisms enforce a rule instead of asking the model to follow it? | 2026-11-05 |
| [bot-repo-access](bot-repo-access.md) | Must a bot account be added to every repository one by one, and what do teams do instead? | 2026-11-08 |
| [multi-repo-agent-review](multi-repo-agent-review.md) | How are review requests routed when agents work across several repositories? | 2026-11-01 |
| [agent-review-cost](agent-review-cost.md) | What does an AI code review of one PR cost, and is a second-agent review worth it on a small quota? | 2026-11-01 |
| [keep-awake-long-jobs](keep-awake-long-jobs.md) | How do people keep a laptop awake while long (agent) jobs run without guessing their length, and how are never-ending processes handled? | 2026-11-11 |
| [agent-state-freshness](agent-state-freshness.md) | When should a long-running agent re-check state others can change: every step, end of turn, on a timer, or before acting? | 2026-11-11 |

### Research methods

| Topic | Question | Checked |
|---|---|---|
| [attention-steering-terminology](attention-steering-terminology.md) | Is "attention steering" or "attention intervention" the right term for an inference-time method that edits attention scores? | 2026-11-11 |
| [research-improvement-size](research-improvement-size.md) | Is there a rule of thumb for how large an NLP/ML gain is good, and is a gain diluted by weak retrieval normal to report? | 2026-11-11 |
| [research-held-out-tuning](research-held-out-tuning.md) | Can hyperparameters be chosen on the samples a result is reported on, and what does research practice do instead? | 2026-11-08 |
| [rag-hypothetical-question-indexing](rag-hypothetical-question-indexing.md) | Is indexing LLM-generated questions per chunk, instead of the chunk text, an established RAG practice? | 2026-11-09 |
| [rag-eval-confidence-intervals](rag-eval-confidence-intervals.md) | Do RAG and retrieval evaluations report bootstrap confidence intervals, and is it worth it on a small set? | 2026-11-10 |
| [rag-hybrid-fusion](rag-hybrid-fusion.md) | How do hybrid search systems merge vector and keyword results; is RRF the default? | 2026-11-10 |
| [rag-reranker-only-small-pool](rag-reranker-only-small-pool.md) | Is scoring every chunk with a cross-encoder, with no first-stage retriever, established practice, and when does it fit? | 2026-11-10 |
| [rag-retrieval-metrics](rag-retrieval-metrics.md) | Which metric leads when reporting RAG retrieval: Hit@k, Recall@k, MRR or nDCG? | 2026-11-10 |
| [rag-retrieval-relevance-without-llm](rag-retrieval-relevance-without-llm.md) | Without an LLM judge, how is a retrieved chunk labelled relevant (gold evidence, answer string, keyword recall), and how reliable is each? | 2026-11-10 |
| [rag-retrieval-eval-without-benchmark](rag-retrieval-eval-without-benchmark.md) | With no benchmark that fits, how do teams evaluate RAG retrieval, and can LLM-generated test questions be trusted? | 2026-11-09 |
| [llm-judge-vs-em-f1](llm-judge-vs-em-f1.md) | Does an LLM judge add anything over exact match and F1 when scoring QA or RAG answers? | 2026-11-09 |

### ML systems

| Topic | Question | Checked |
|---|---|---|
| [llm-inference-memory-calibration](llm-inference-memory-calibration.md) | How do inference systems size the batch token budget, how is it calibrated, where does a bigger batch stop paying, and what must an inference benchmark report? | 2026-11-09 |
| [benchmark-setup-consistency](benchmark-setup-consistency.md) | Must every benchmark run on the same hardware and configuration, or may results come from different setups? | 2026-11-11 |
| [llm-batch-size-selection](llm-batch-size-selection.md) | How is the batch size for LLM inference chosen (search and pick rule): largest that fits, fastest, or the knee? | 2026-11-11 |
| [length-bucketed-batch-sizing](length-bucketed-batch-sizing.md) | When batches are sorted or bucketed by length, how is the batch size picked, and what sample should a timing sweep use? | 2026-11-11 |
| [vllm-custom-attention-bias](vllm-custom-attention-bias.md) | Can vLLM apply a custom, per-request bias to pre-softmax attention scores, and what would it take? | 2026-11-11 |

### Career

| Topic | Question | Checked |
|---|---|---|
| [ats-resume-section-headings](ats-resume-section-headings.md) | Does an ATS look for the exact heading "Work Experience", and does a resume without it get rejected? | 2026-11-05 |
| [resume-projects-as-experience](resume-projects-as-experience.md) | With no formal work history, should projects be formatted like jobs and carry job titles, and may a class project carry a lead title? | 2026-11-09 |
| [thesis-as-research-experience](thesis-as-research-experience.md) | Can an undergraduate thesis be listed as "Research Experience" on a resume? | 2026-11-05 |
| [resume-bullet-clarity](resume-bullet-clarity.md) | Should resume bullets be understandable in one read by someone new to the work, and what shape do guides recommend? | 2026-11-08 |
| [resume-dates-revisited-projects](resume-dates-revisited-projects.md) | Should a project revisited after a gap show "start -- Present" or its separate periods? | 2026-11-10 |
| [resume-ml-model-names-and-baselines](resume-ml-model-names-and-baselines.md) | Should an ML bullet name the specific model (including an outdated one in an older project), and give a result against a baseline or alone? | 2026-11-10 |
| [resume-project-stack-line](resume-project-stack-line.md) | How many technologies should a project's stack line list; is "at most 4–5" a rule? | 2026-11-10 |
| [resume-llm-api-listing](resume-llm-api-listing.md) | Is naming a hosted LLM API (OpenAI, DeepSeek) on a resume worth it, and which APIs should be named? | 2026-11-11 |
| [resume-skills-section-tailoring](resume-skills-section-tailoring.md) | When tailoring, should the skills section and stack lines keep every tool, or only relevant ones backed by bullets? | 2026-11-11 |
| [resume-tailoring-project-context](resume-tailoring-project-context.md) | When tailoring cuts bullets, does an entry lose what the project was, and is that accepted practice? | 2026-11-10 |
| [resume-summary-entry-level](resume-summary-entry-level.md) | Does an entry-level resume need a summary, what should it say, and may it restate the top entry? | 2026-11-10 |
| [ats-keyword-matching](ats-keyword-matching.md) | Does an ATS match only the posting's keywords, or also assumed skills (Git, Jupyter) the posting omits? | 2026-11-11 |
| [resume-high-school-after-degree](resume-high-school-after-degree.md) | After a university degree, does a prestigious or selective high school stay on the resume? | 2026-11-11 |
| [resume-academic-honor-placement](resume-academic-honor-placement.md) | Where does a top academic honor (valedictorian, Latin honors) go so it is seen, and may it go in the summary? | 2026-11-10 |
| [resume-accuracy-vs-concision](resume-accuracy-vs-concision.md) | When shortening a line would make it read wider than the fact, does accuracy or brevity come first? | 2026-11-11 |
| [resume-submission-readiness](resume-submission-readiness.md) | What are the final refinement steps, and how do you know a resume is ready to submit? | 2026-11-11 |
| [resume-degree-name-abbreviation](resume-degree-name-abbreviation.md) | Must a resume spell out "Bachelor of Science in …" for ATS, or can it be abbreviated? | 2026-11-11 |
| [resume-english-score-vietnam-it](resume-english-score-vietnam-it.md) | How much does an English test score (IELTS) matter in Vietnamese software hiring, and where does it go on a resume? | 2026-11-09 |
| [resume-bullet-order](resume-bullet-order.md) | Are bullets inside one entry ordered by significance or by time, and must terms be introduced before use? | 2026-11-11 |
